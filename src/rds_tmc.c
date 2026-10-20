/*
    PiFmRds - FM/RDS transmitter for the Raspberry Pi
    Copyright (C) 2014 Christophe Jacquet, F8FTK

    Modified for TMC (Traffic Message Channel) support

    See https://github.com/ChristopheJacquet/PiFmRds

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <stdlib.h>

#include "rds_strings.h"
#include "waveforms.h"

#define RT_LENGTH 64
#define PS_LENGTH 8
#define GROUP_LENGTH 4

/* TMC Configuration - using codes from car dump
 * loc=17602, event_1=807 from trafficevents_A.txt
 */
#define TMC_LOCATION_CODE   17602   // From dump: loc=17602
#define TMC_EVENT_CODE      807     // From dump: event_1=807
#define TMC_EXTENT          1       // Event spans 1 location point
#define TMC_DIRECTION       1       // Positive direction
#define TMC_DIVERSION       0       // No diversion advised
#define TMC_DURATION        0       // Not specified (0 = use default)
#define TMC_LTN             10      // Location Table Number: UK
#define TMC_CC              12      // Country Code: UK

struct {
    uint16_t pi;
    int ta;
    char ps[PS_LENGTH];
    char rt[RT_LENGTH];
} rds_params = { 0 };

/* TMC parameters - hardcoded for now, can be extended for runtime control */
struct {
    uint16_t location_code;   // 16-bit ALERT-C location code
    uint16_t event_code;      // 11-bit ALERT-C event code
    uint8_t extent;           // Extent (0-7, 3 bits)
    uint8_t direction;        // Direction (0=both, 1=pos, 2=neg, 3=undefined)
    uint8_t diversion;        // Diversion advice (1 bit)
    uint8_t duration;         // Duration/persistence (3 bits)
    int enabled;              // TMC enabled flag
} tmc_params = {
    TMC_LOCATION_CODE,
    TMC_EVENT_CODE,
    TMC_EXTENT,
    TMC_DIRECTION,
    TMC_DIVERSION,
    TMC_DURATION,
    1  /* enabled by default */
};

/* Here, the first member of the struct must be a scalar to avoid a
   warning on -Wmissing-braces with GCC < 4.8.3
   (bug: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=53119)
*/

/* The RDS error-detection code generator polynomial is
   x^10 + x^8 + x^7 + x^5 + x^4 + x^3 + x^0
*/
#define POLY 0x1B9
#define POLY_DEG 10
#define MSB_BIT 0x8000
#define BLOCK_SIZE 16

#define BITS_PER_GROUP (GROUP_LENGTH * (BLOCK_SIZE+POLY_DEG))
#define SAMPLES_PER_BIT 192
#define FILTER_SIZE (sizeof(waveform_biphase)/sizeof(float))
#define SAMPLE_BUFFER_SIZE (SAMPLES_PER_BIT + FILTER_SIZE)


uint16_t offset_words[] = {0x0FC, 0x198, 0x168, 0x1B4};
// We don't handle offset word C' here for the sake of simplicity

/* Classical CRC computation */
uint16_t crc(uint16_t block) {
    uint16_t crc = 0;

    for(int j=0; j<BLOCK_SIZE; j++) {
        int bit = (block & MSB_BIT) != 0;
        block <<= 1;

        int msb = (crc >> (POLY_DEG-1)) & 1;
        crc <<= 1;
        if((msb ^ bit) != 0) {
            crc = crc ^ POLY;
        }
    }

    return crc;
}

/* TMC 3A ODA (Open Data Application) Group Generator
 * ODA ID 0xCD46 = TMC
 * Announces that 8A groups contain TMC data
 *
 * 3A group structure:
 * Block 1: PI code
 * Block 2: 3A specific (ODA group type, 0xCD46 high byte)
 * Block 3: 0xCD46 low byte + ODA application ID high
 * Block 4: ODA application ID low + 8A (group type for TMC)
 */
void get_tmc_3a_group(uint16_t *blocks) {
    blocks[0] = rds_params.pi;

    // Block 2: 3A group type with ODA high byte
    // bit 15 = 0 (group A), bits 14-11 = 3 (3A), bit 10-8 = 0 (reserved)
    // bits 7-0 = 0xCD (high byte of ODA ID 0xCD46)
    blocks[1] = 0x3A00 | 0x00CD;  // Actually: 0b00111010 00000000 | 0xCD

    // For 3A, the group type is 3, so bits 14-11 = 3 = 0x3
    // PI is in block 0
    // Block 1: 0x0C00 | (group << 11) | (version << 8) where version A = 0
    // Actually: 0x0C00 | (3 << 11) = 0x0C00 | 0x6000 = 0x6C00
    blocks[1] = 0x6C00 | 0x00CD;  // 3A + ODA high byte

    // Block 3: ODA ID low (0x46) + AID high byte (0x8 for 8A)
    // Actually: ODA ID is 0xCD46, and we announce group 8A as the application
    // So block 3 = 0x468A (46 = low byte of ODA, 8A = group type)
    blocks[2] = 0x468A;

    // Block 4: For ODA, this is the data field - we'll use 0 for now
    // Could contain tuning info variant in future
    blocks[3] = 0x0000;
}

/* TMC 8A User Message Group Generator
 *
 * 8A group structure (ALERT-C):
 * Block 1: PI code
 * Block 2: 8A specific + SI (service indicator) + DP (diversion)
 * Block 3: Location code (16 bits)
 * Block 4: Event code (11 bits) + extent (3 bits) + direction (2 bits)
 *
 * Detailed bit layout in block 4:
 * - bits 15-5: Event code (11 bits)
 * - bits 4-2: Extent (3 bits)
 * - bits 1-0: Direction (2 bits): 00=both, 01=positive, 10=negative, 11=undefined
 *
 * Block 2 layout:
 * - bits 15-11: Group type = 8 (8A)
 * - bit 10: Version (0 = A)
 * - bit 9: TP (Traffic Program)
 * - bit 8: TA (Traffic Announcement)
 * - bits 7-5: Duration/persistence (3 bits)
 * - bit 4: Diversion advice (1 bit)
 * - bits 3-0: Continuation flag (0 = last/first in sequence)
 */
void get_tmc_8a_group(uint16_t *blocks) {
    // Block 1: PI code
    blocks[0] = rds_params.pi;

    // Block 2: 8A group + TP + TA + duration + diversion
    // Group 8A: 0b1000 = 8, so bits 15-11 = 8
    // Version A = 0 (bit 10)
    // TP from rds_params (bit 9), TA from rds_params (bit 8)
    uint16_t block2 = 0x8000;  // 8A group type
    block2 |= (tmc_params.duration & 0x07) << 5;  // Duration (3 bits)
    block2 |= (tmc_params.diversion & 0x01) << 4;  // Diversion (1 bit)
    if(rds_params.ta) block2 |= 0x0100;  // TA flag
    // TP would be set from the radio's TP flag - default to 1 for traffic info
    block2 |= 0x0200;  // TP = 1
    blocks[1] = block2;

    // Block 3: 16-bit location code (little-endian in the message)
    blocks[2] = tmc_params.location_code;

    // Block 4: Event code (11 bits) + extent (3 bits) + direction (2 bits)
    // Event code in bits 15-5 (11 bits)
    // Extent in bits 4-2 (3 bits)
    // Direction in bits 1-0 (2 bits)
    uint16_t event = tmc_params.event_code & 0x7FF;  // 11-bit event
    uint16_t extent = tmc_params.extent & 0x07;       // 3-bit extent
    uint16_t direction = tmc_params.direction & 0x03; // 2-bit direction

    blocks[3] = (event << 5) | (extent << 2) | direction;
}

/* Possibly generates a CT (clock time) group if the minute has just changed
   Returns 1 if the CT group was generated, 0 otherwise
*/
int get_rds_ct_group(uint16_t *blocks) {
    static int latest_minutes = -1;

    // Check time
    time_t now;
    struct tm *utc;

    now = time (NULL);
    utc = gmtime (&now);

    if(utc->tm_min != latest_minutes) {
        // Generate CT group
        latest_minutes = utc->tm_min;

        int l = utc->tm_mon <= 1 ? 1 : 0;
        int mjd = 14956 + utc->tm_mday +
                        (int)((utc->tm_year - l) * 365.25) +
                        (int)((utc->tm_mon + 2 + l*12) * 30.6001);

        blocks[1] = 0x4400 | (mjd>>15);
        blocks[2] = (mjd<<1) | (utc->tm_hour>>4);
        blocks[3] = (utc->tm_hour & 0xF)<<12 | utc->tm_min<<6;

        utc = localtime(&now);

        int offset = utc->tm_gmtoff / (30 * 60);
        blocks[3] |= abs(offset);
        if(offset < 0) blocks[3] |= 0x20;

        //printf("Generated CT: %04X %04X %04X\n", blocks[1], blocks[2], blocks[3]);
        return 1;
    } else return 0;
}

/* Creates an RDS group. This generates sequences of the form 0A, 0A, 0A, 0A, 2A, etc.
   The pattern is of length 5, the variable 'state' keeps track of where we are in the
   pattern. 'ps_state' and 'rt_state' keep track of where we are in the PS (0A) sequence
   or RT (2A) sequence, respectively.
*/
void get_rds_group(int *buffer) {
    /* Group cycle with TMC:
     * State 0-3: 0A (PS) - 4 groups
     * State 4:   3A (TMC ODA announcement)
     * State 5:   8A (TMC user message)
     * State 6:   2A (RadioText)
     *
     * Total cycle: 7 groups, TMC appears every ~1.3 seconds at 4 groups/second
     */
    static int state = 0;
    static int ps_state = 0;
    static int rt_state = 0;
    uint16_t blocks[GROUP_LENGTH] = {rds_params.pi, 0, 0, 0};

    // Generate block content
    if(! get_rds_ct_group(blocks)) { // CT (clock time) has priority
        if(state < 4) {
            // 0A: Program Service name
            blocks[1] = 0x0400 | ps_state;
            if(rds_params.ta) blocks[1] |= 0x0010;
            blocks[2] = 0xCDCD;     // no AF
            blocks[3] = rds_params.ps[ps_state*2]<<8 | rds_params.ps[ps_state*2+1];
            ps_state++;
            if(ps_state >= 4) ps_state = 0;
        } else if (state == 4) {
            // 3A: TMC ODA announcement (ODA ID 0xCD46 = TMC)
            get_tmc_3a_group(blocks);
        } else if (state == 5) {
            // 8A: TMC user message
            get_tmc_8a_group(blocks);
        } else { // state == 6
            // 2A: RadioText
            blocks[1] = 0x2400 | rt_state;
            blocks[2] = rds_params.rt[rt_state*4+0]<<8 | rds_params.rt[rt_state*4+1];
            blocks[3] = rds_params.rt[rt_state*4+2]<<8 | rds_params.rt[rt_state*4+3];
            rt_state++;
            if(rt_state >= 16) rt_state = 0;
        }

        state++;
        if(state >= 7) state = 0;
    }

    // Calculate the checkword for each block and emit the bits
    for(int i=0; i<GROUP_LENGTH; i++) {
        uint16_t block = blocks[i];
        uint16_t check = crc(block) ^ offset_words[i];
        for(int j=0; j<BLOCK_SIZE; j++) {
            *buffer++ = ((block & (1<<(BLOCK_SIZE-1))) != 0);
            block <<= 1;
        }
        for(int j=0; j<POLY_DEG; j++) {
            *buffer++= ((check & (1<<(POLY_DEG-1))) != 0);
            check <<= 1;
        }
    }
}

/* Get a number of RDS samples. This generates the envelope of the waveform using
   pre-generated elementary waveform samples, and then it amplitude-modulates the
   envelope with a 57 kHz carrier, which is very efficient as 57 kHz is 4 times the
   sample frequency we are working at (228 kHz).
 */
void get_rds_samples(float *buffer, int count) {
    static int bit_buffer[BITS_PER_GROUP];
    static int bit_pos = BITS_PER_GROUP;
    static float sample_buffer[SAMPLE_BUFFER_SIZE] = {0};

    static int prev_output = 0;
    static int cur_output = 0;
    static int cur_bit = 0;
    static int sample_count = SAMPLES_PER_BIT;
    static int inverting = 0;
    static int phase = 0;

    static int in_sample_index = 0;
    static int out_sample_index = SAMPLE_BUFFER_SIZE-1;

    for(int i=0; i<count; i++) {
        if(sample_count >= SAMPLES_PER_BIT) {
            if(bit_pos >= BITS_PER_GROUP) {
                get_rds_group(bit_buffer);
                bit_pos = 0;
            }

            // do differential encoding
            cur_bit = bit_buffer[bit_pos];
            prev_output = cur_output;
            cur_output = prev_output ^ cur_bit;

            inverting = (cur_output == 1);

            float *src = waveform_biphase;
            int idx = in_sample_index;

            for(int j=0; j<FILTER_SIZE; j++) {
                float val = (*src++);
                if(inverting) val = -val;
                sample_buffer[idx++] += val;
                if(idx >= SAMPLE_BUFFER_SIZE) idx = 0;
            }

            in_sample_index += SAMPLES_PER_BIT;
            if(in_sample_index >= SAMPLE_BUFFER_SIZE) in_sample_index -= SAMPLE_BUFFER_SIZE;

            bit_pos++;
            sample_count = 0;
        }

        float sample = sample_buffer[out_sample_index];
        sample_buffer[out_sample_index] = 0;
        out_sample_index++;
        if(out_sample_index >= SAMPLE_BUFFER_SIZE) out_sample_index = 0;


        // modulate at 57 kHz
        // use phase for this
        switch(phase) {
            case 0:
            case 2: sample = 0; break;
            case 1: break;
            case 3: sample = -sample; break;
        }
        phase++;
        if(phase >= 4) phase = 0;

        *buffer++ = sample;
        sample_count++;
    }
}

void set_rds_pi(uint16_t pi_code) {
    rds_params.pi = pi_code;
}

void set_rds_rt(char *rt) {
    fill_rds_string(rds_params.rt, rt, 64);
}

void set_rds_ps(char *ps) {
    fill_rds_string(rds_params.ps, ps, 8);
}

void set_rds_ta(int ta) {
    rds_params.ta = ta;
}