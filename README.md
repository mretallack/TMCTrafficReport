# TrafficReport — a DIY RDS-TMC transmitter for in-car satnav routing

**Goal:** build a transmitter that sends **machine-coded traffic data** (not audio) that a
car satnav can ingest and use for **routing / re-routing** — e.g. broadcast "A31 closed" and
have the satnav route around it.

This is a sibling project to the RDS experiments in the parent `TMS/` workspace, which
already proved an end-to-end FM-RDS chain (Pi transmitter → RTL-SDR → `redsea` decode) with
PS / RadioText / TA all round-tripping cleanly. This project extends that chain to the one
piece PiFmRds does **not** implement: **TMC**.

> **Status:** TMC encoding is implemented and the current MediaNav OSM
> CC=12/LTN=10 member-0 location index has been decoded to reproducible
> road-record coordinates. See `docs/17-CURRENT-UK-TMC-INDEX-EXTRACTION.md`.

## Repository layout

| Path | Contents |
|---|---|
| `data/exports/` | Authoritative reproducible CSV exports and their hash manifest |
| `analysis/ghidra-scripts/` | Lightweight headless Ghidra scripts used to recover the formats |
| `docs/` | Investigation reports and exact runtime/format evidence |
| `tools/` | Reusable FBL/TMC extraction and correlation tools |
| `src/` | RDS-TMC transmitter implementation |
| `dump/` | Small historical traffic samples; large map files are ignored |
| `tmp/` | Local probes, firmware, Ghidra projects and generated intermediates; ignored |

Large map/firmware inputs and license/key material are deliberately not stored
in Git.

---

## 1. What this technology is called

The service is **RDS-TMC** — *Radio Data System – Traffic Message Channel* — using the
**ALERT-C** protocol, standardised as **ISO 14819** (parts 1/2/3):

- **ISO 14819-1** — ALERT-C protocol & message structure.
- **ISO 14819-2** — the **Events List** (11-bit event codes: accident, queue, closure…).
- **ISO 14819-3** — location referencing / location table rules.

TMC is carried on the **57 kHz RDS subcarrier** of an ordinary FM broadcast, in **type 8A**
RDS groups, announced via a **3A** ODA group (Open Data Application id **`0xCD46`**). It is
*silent* — the radio need not be tuned to it audibly — and when wired into the navigation
engine the events feed route calculation. This is exactly the feature described in car
manuals as "RDS-TMC traffic" (VAG, Toyota, Jaguar/Land Rover, TomTom, etc.).

TMC is **not** RadioText. RadioText is human-readable free text; TMC is densely bit-packed
references into reference databases. "A31 closed" must become *event code X at location
code Y, direction, extent, duration* — and the receiver must hold the same location table
to turn code Y back into "the A31".

## 2. Why it's needed in the UK (the problem)

The UK's public RDS-TMC service has been **switched off**. Confirmed from multiple sources:

- The UK service ran under Ofcom's single national **Additional Services Licence (AS/1)**,
  operated by **Trafficmaster / ITIS**, broadcast piggybacked on **Classic FM**. (Ofcom
  AS/1 consultation documents; car-owner forums.)
- It **ceased during 2023**. Owners of VAG (Audi/VW), Toyota, and other cars report their
  built-in satnav now shows "no traffic messages available" and dynamic re-routing stopped.
- The only remaining UK traffic-data provider is **Inrix**, in a *different* format, so
  there is no drop-in replacement for devices built around the Trafficmaster RDS-TMC feed.

So cars with RDS-TMC hardware now have a dead input. This project aims to feed that input
locally (on a bench, legally — see §7) from our own data source.

## 3. Prior art (yes, people have done this)

TMC transmission/injection is well-trodden ground. Key references:

| Work | What it is | Relevance |
|------|-----------|-----------|
| **Barisani & Bianco, "Injecting RDS-TMC Traffic Information Signals" (2007, CanSecWest/hack.lu)** | The canonical demonstration — injected crafted TMC into real satnavs with a low-power FM transmitter and made them display/act on fake events | Proves the concept end-to-end against real devices; documents message layout & gotchas |
| **D. Symeonidis, "RDS-TMC Spoofing using GNU Radio"** | Academic reproduction using SDR | Encoding reference |
| **gr-rds** (`bastibl/gr-rds`, `TuxCoder/gr-rds`) | GNU Radio FM **RDS/TMC** transceiver | Working open-source TMC encoder to compare against |
| **mueschel/TmcDecoder** | Dedicated RDS-TMC decoder | Second independent decoder for cross-checking |
| **redsea** (`windytan/redsea`) | RDS decoder **with a full `src/tmc/` subsystem** | **Already built in `../redsea`** — our primary test receiver |
| **Anthony96922/MiniRDS** | Feature-rich software RDS encoder | Reference for group scheduling / RDS2 |

Takeaway: the **encoding** is a solved problem we can reproduce. The **data** (location
tables) is the hard part — see §6.

## 4. The two hard problems (be honest up front)

1. **Location Code List (LCL).** Location codes are 16-bit indices into a *national* table.
   The transmitter and the satnav must share the **same** table for a code to map to a real
   road. National LCLs are maintained by official bodies and are frequently **licensed, not
   freely distributable**. A satnav ships with its vendor's table baked into the map data.
   **To make a *specific* car react to "A31 closed", we must emit the location code that
   that car's map uses for the A31.** This is the single biggest blocker and is addressed
   as its own phase.

2. **Receiver acceptance.** Real head units may expect a particular provider/PI, may expect
   the service to be **encrypted** (some European public TMC is scrambled), may be
   **region-locked**, and will ignore codes outside the LCL they hold. Behaviour is highly
   device-specific. This is why we iterate against **one specific target receiver**.

Everything else (the DSP, CRC, biphase coding, 57 kHz modulation) is **already working** in
PiFmRds and is reused unchanged.

## 5. What we have to build, and in what order

The guiding principle: **prove each layer with a decoder before moving on.** We never
"build it all then test" — every phase has an explicit pass/fail test, most of them using
`redsea` (which we already trust from the parent project) and, where possible, a second
independent decoder (`TmcDecoder`) for cross-validation.

Work happens in a **copy** of PiFmRds's `rds.c` so the original mono/stereo/RDS paths stay
intact. The generic machinery to reuse without change: `crc()`, `offset_words[]`, the
differential/biphase encoder in `get_rds_samples()`. The only thing we extend is
**which groups `get_rds_group()` emits**.

### Phase 0 — Toolchain & baseline (no new encoding yet)
**Build:** nothing new — confirm the parent chain still works from inside this project.
**Why:** a known-good reference so any later failure is clearly *our* TMC code, not the link.
**Test / pass criteria:**
- Transmit a plain PS/RT/TA message from the Pi, decode with `redsea`, confirm fields match
  (this is exactly what the parent project does). If green → the RF link and decoder are
  trustworthy and we can attribute any TMC failure to our encoding.

### Phase 1 — Emit a single hard-coded 8A TMC message + 3A ODA announcement
**Build:** in the copied `rds.c`:
- Add a **3A** group declaring the TMC ODA (`0xCD46`) and the Application Group Type (8A).
- Add a single hard-coded **8A** single-group user message with known fields
  (duration, diversion, direction, extent, 11-bit **event code**, 16-bit **location code**).
- Inject these into the group cycle alongside the existing 0A/2A with steady repetition.
**Why first:** this is the smallest unit that is "real TMC". If `redsea` decodes the exact
event/location codes we put in, our bit-packing and block framing are correct.
**Test / pass criteria:**
- `redsea -p` (and its TMC output) prints a TMC message whose **event code** and
  **location code** equal what we encoded. Cross-check the same capture with
  `mueschel/TmcDecoder`. Both must agree. Measure block-error rate (`redsea -E`) to confirm
  a clean link. **No LCL needed yet** — we verify the *numbers*, not their road meaning.

### Phase 2 — Correct service signalling (tuning info + repetition discipline)
**Build:**
- **8A tuning-information** variants (provider name, Location Table Number / LTN, service
  identifiers, PI).
- Proper 3A/8A **repetition cadence** (TMC is re-sent continuously so a newly-tuned receiver
  catches the service quickly).
**Why:** a decoder will show raw 8A groups without this, but a *navigation device* generally
won't treat the stream as a usable TMC service until it sees the ODA announcement + tuning
info + consistent repetition.
**Test / pass criteria:**
- `redsea` reports the service correctly (ODA `0xCD46`, LTN, provider). The stream is
  self-describing: a decoder started mid-stream locks onto the service within a few seconds.

### Phase 3 — Runtime control: inject messages on demand
**Build:** extend the existing `-ctl` FIFO with a command such as
`TMC <event> <location> <direction> <extent> <duration>` so messages can be added/cleared
without restarting the transmitter. Support cancellation messages (clearing an event).
**Why:** a real feed is dynamic; we must set/update/clear events live.
**Test / pass criteria:**
- Send a `TMC …` command over the FIFO; confirm `redsea` starts reporting the new message
  within the expected repetition window, and that a cancel removes it.

### Phase 4 — The LCL problem: make codes mean real roads (for a test area)
**Build / obtain:**
- A **location table** covering a small test area (e.g. a few roads around home, including
  the A31), plus the standard event list.
- A mapping layer: *human description → (event code, location code, direction, extent,
  duration)*.
**Why:** this is what turns "event 401 at location 12345" into "A31 closed" **for a receiver
that holds the same table.** This is the crux and the riskiest part (licensing/availability
of a UK LCL; may require constructing a minimal custom table and a matching receiver map, or
targeting a device whose table we can inspect).
**Test / pass criteria:**
- In `redsea`/`TmcDecoder` configured with our test location table, the decoded message
  resolves to the intended human-readable road + event ("A31, closed"). Semantics verified,
  still on the bench — no car required yet.

### Phase 5 — Feed integration
**Build:** an ingestion layer that pulls real incidents (e.g. an open traffic data source)
and geocodes each to the nearest LCL location + event code, then drives the FIFO.
**Why:** turns the transmitter into an actual service rather than a static demo.
**Test / pass criteria:**
- A real incident from the feed appears, correctly coded, in the decoder within seconds of
  ingestion; stale incidents are cancelled.

### Phase 6 — Real satnav acceptance (the goal, not guaranteed)
**Build:** nothing new — tune PI code, tuning info, repetition, encryption expectations, and
**LCL matching** to a **specific target head unit**.
**Why:** decoding our own stream proves correctness; a car acting on it proves usefulness.
**Test / pass criteria:**
- The target satnav lists our injected event and/or re-routes around it. Iterate per device.
  Treat success as device-specific, not universal (older/aftermarket PND units tend to be
  more permissive than built-in head units).

## 6. Dependencies & tooling

| Need | Source | Status |
|------|--------|--------|
| FM-RDS transmitter with reusable DSP | `../PiFmRds` (built on the Pi) | ✅ available |
| Primary TMC decoder (test receiver) | `../redsea` (`src/tmc/`) | ✅ built |
| RTL-SDR receiver | this PC (RTL2838UHIDIR / R820T) | ✅ working |
| TMC encoding (rds_tmc.c) | `src/rds_tmc.c` | ✅ Phase 1+ implemented |
| Location codes from car dump | `docs/01-LOCATION-CODES-DUMP.md` | ✅ Found in trafficevents |
| Second independent TMC decoder | `mueschel/TmcDecoder` | ⬜ optional |
| Open-source TMC encoder (reference) | `gr-rds` | ⬜ optional |
| Live traffic event codes | `dump/trafficevents_A.txt` | ✅ extracted |

## 7. Legal & safety — read before transmitting

- Transmitting on the FM band **without a licence is illegal** in the UK and most countries.
  As in the parent project: **shielded cable straight into the receiver's antenna input,
  NO antenna.** PiFmRds's square-wave carrier is harmonic-rich.
- **Broadcasting fake traffic data that a navigation device acts on has obvious real-world
  safety implications.** This stays strictly on a **bench** with a wired receiver. It must
  **never** be transmitted anywhere a real vehicle in live traffic could receive it.
- `redsea` is explicitly **not** safety-certified; the same caution applies to *generating*
  TMC. Nothing here is for real navigation use.
- This is an experiment for a dead service against our **own** equipment, at our own risk.

## 8. Immediate next steps

**Status:** Phase 1 encoding implemented (2026-10-19)

1. ✅ Created `src/rds_tmc.c` based on PiFmRds `rds.c`
2. ✅ Added 3A ODA group (ODA id 0xCD46) announcing TMC service
3. ✅ Added 8A TMC user message using **real codes from car dump**:
   - Location: `17602` (from dump: `loc=17602`)
   - Event: `807` (from dump: `event_1=807`)
4. ⬜ **Next:** Build and test on the Pi, verify with `redsea` decode

### How to test

1. Copy `src/rds_tmc.c` and related files to PiFmRds on the Raspberry Pi
2. Build and run: `sudo ./pi_fm_rds -freq 107.9 -pi C1C1 -ps TMC -rt "TMC test"`
3. On this PC: capture with `rtl_fm | redsea -r 171000 -p`
4. Verify redsea shows TMC groups with loc=17602, event=807

## 9. References

- ISO 14819-1/-2/-3 — RDS-TMC ALERT-C protocol, Events List, location referencing.
- Barisani & Bianco — "Injecting RDS-TMC Traffic Information Signals" (2007).
- D. Symeonidis — "RDS-TMC Spoofing using GNU Radio".
- redsea — https://github.com/windytan/redsea (`src/tmc/`).
- gr-rds — https://github.com/bastibl/gr-rds .
- mueschel/TmcDecoder — https://github.com/mueschel/TmcDecoder .
- Wikipedia: Traffic message channel (ALERT-C overview, 16-bit location code history).
- Ofcom AS/1 Additional Services Licence consultation (UK RDS-TMC licensing background).
- Parent project: `../README.md` §6 (TMC research & feasibility).

---

## 10. Found the TMC location codes! (dump findings, 2026-10-19)

A MediaNav filesystem dump (`/home/markretallack/buildhome/dacia/`) + USB disk backup revealed:

### The actual TMC data lives in `trafficevents_A.txt` / `trafficevents_B.txt`

These are **live traffic events** stored on the device (not fetched from the internet —
updates are via USB only). Example from the dump:

```
EVENT htmc=1 loc=17602 extent=1 dir=1 bidi=0 age=59 cc=12 ltn=10 new=1 tmc_source=0 sid=10 qdecoded=1 snd_id=0 event_1=807  loaded=1
EVENT htmc=2 loc=10024 extent=1 dir=1 bidi=0 age=59 cc=12 ltn=10 new=1 tmc_source=0 sid=10 qdecoded=1 snd_id=0 event_1=806  loaded=1
```

Key fields:
- `loc=17602`, `loc=10024` — **16-bit ALERT-C location codes** for UK roads
- `event_1=807`, `event_1=806` — **11-bit event codes** (ISO 14819-2)
- `ltn=10` — Location Table Number = 10 (UK)
- `cc=12` — Country Code 12 = United Kingdom (ISO 3166-1)
- `extent=1`, `dir=1` — extent and direction

### What this means

**We don't need to build or find a UK LCL.** The car already has TMC location codes
stored in its `trafficevents` files — these are the exact codes the navigation system
understands. We can use these same codes in our transmitter:

- Location code **17602** → the road segment the car knows as "X"
- Location code **10024** → another road segment
- Event code **807** / **806** → traffic event types (e.g., queue, stationary traffic)

The `.tmc.stm` files in the dump are just shadow containers; the actual data is in
`trafficevents_A/B.txt` which the device reads at runtime.

### Path forward

1. **Phase 1 (TMC encoding):** Use these exact codes (or similar ones from the dump)
   in our 8A transmission. No LCL needed for testing — we use the car's own codes.
2. **Verify with the car:** If the car accepts these codes over FM RDS-TMC, we've solved it.
3. **Extend:** Add more location codes by reading other `trafficevents` entries or
   extracting from a fresh USB sync.
