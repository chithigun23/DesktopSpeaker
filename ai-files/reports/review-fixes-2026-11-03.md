# Review fixes: documents, BOM and RFQ (2026-11-03)

Agent "BOM, RFQ and document consistency fixes". Owner instruction: "make the fixes and address the issues you discovered. use judgment" (firmware later). Basis: `project-review-cad-completeness-2026-11-03.md` (the review), `fastener-schedule-2026-11-03.md` + `cad/fastener-schedule.json`, coordinator decisions of 2026-11-03. Scope of this agent: documents and BOM only. CAD v16 (`ai-files/cad/v16/`) is built by another agent and the website by a third; neither was touched here, nor any KiCad or board file. Nothing was committed.

Status legend: **fixed in docs/BOM** (done here) · **CAD v16 (pending)** (decided, the CAD agent implements it) · **owner action** · **deferred** (firmware or next board revision).

## 1. Decisions recorded (coordinator, 2026-11-03; applied in the documents)

| # | Decision | Where recorded |
|---|---|---|
| D1 | **Encoder dish becomes a separate printed knob cup** (review M1 option b): 42 mm top-wall opening, cup with a 46 mm flange in a 1 mm recess, 4 x countersunk post-Torx M3x10 into 4 inserts, foam ring seal. The PCB slides in under the top wall; the encoder stays on the board (SW102, no board change); H8 is reached from above with the cup out | `cad/mechanical-bom.md`, HANDOVER |
| D2 | **Woofer-chamber insert screwed with a gasket (removable)** (M2): 4 x countersunk post-Torx M3x10 from below into 4 inserts, 1.5 mm closed-cell foam gasket in the floor grooves instead of the Sikaflex bond. Service order: lid, PCB, woofer, insert, battery or drivers | same |
| D3 | **SW100 printed plunger**, three nub lengths (0.4 / 0.6 / 0.8 mm), lid counterbore 7.4 x 1.0 (M3) | same |
| D4 | **Cable anchoring**: printed tie bridges (or adhesive mounts) at 9 positions, 2.5 x 100 ties, driver leads tied at the tabs, foam tape where a lead crosses a basket (M4); harness cut lengths per S9 | same, buy list rows 55-56 |
| D5 | **Pack secondary protection**: 15 A fuse in PACK+ and an about 85 C thermal cut-off, supplied by the pack vendor (RFQ item 2); per-cell fusible links kept; thickness limit 22.3 mm; inline 15 A mini-blade holder only as a fallback (M5, S5) | RFQ, buy list rows 31, 60-62 |
| D6 | **Seals and vents**: 2 mm sponge cord in the lid groove (S4), 2 mm foam on the connector faces (S1a), 3 mm foam encoder washer (S1b), 1.5 mm foam at the knob cup flange and insert floor, 0.5 mm drilled vents (woofer and main chamber) with a cloth/felt dot (S3), lid screws in the woofer loop sealed with foam washers or butyl (S2) | mechanical-bom, buy list rows 50-53, 65-66 |
| D7 | **Damping**: 6-8 g polyfill in the woofer chamber, 10 mm open-cell foam lining in the main chamber (S11) | buy list rows 3, 54 |
| D8 | **Nylon at H9** (nearest metal to the BM83 antenna): nylon M3 standoff and nylon M3x10 screw (N1) | buy list rows 47-48 |
| D9 | **No status LED in v1** (S15): BM83 voice prompts / phone battery reporting; revisit at the next board revision | HANDOVER |
| D10 | **Fasteners per the schedule**: lid 11 + drivers 8 + knob cup 4 + insert 4 = 27 countersunk post-Torx T10 M3x10 (22CPTS310); drivers on 6g cup washers (71CS6); PCB 10 x Wurth 971100321 M/F standoffs + button post-Torx M3x10 (22BPTS310), H9 nylon; woofer 4 x button M3x20 (22BPTS320); 46 inserts; T10 post-Torx bits x2, L-keys x2 (one cut short), 1/4 in bit extension >= 200 mm; ball-end keys not usable; nylon washers and socket-head rows superseded; >= 10 % spares | buy list rows 15-22, 40-49 |

Judgement calls made by this agent (also recorded in the buy list notes):

- **Driver gaskets 3 mm** (coordinator's figure), although the v15 pad recess is 0.5 mm and the review suggested 0.8-1.0 mm: CAD v16 must set the recess or stand-off for 3 mm foam. The woofer keeps its factory 3.3 mm gasket; a ring is cut from the 3 mm sheet only if the sample has none.
- **Feet**: the Wurth 971120321 stud stays; a screw-in rubber foot with an M3 male stud goes into the stud's female end. The floor gap becomes 12 mm + foot height (CAD v16 updates the woofer gap and the tipping check).
- **Wire**: thin-wall 18 AWG (row 57) for both the rocker leads (2 x about 150 mm with a 60-80 mm service loop) and a J5 service lead; the silicone 18 AWG pack (row 13) becomes optional.
- **Quantities**: PCB steel standoffs and button screws ordered as 12 (10 needed + 10 % + one so H9 can fall back to steel if the nylon parts disappoint); countersunk M3x10 ordered as 30 (27 + 10 %; the 30+ price tier is AUD 0.63).
- **Prices**: the T10 bit and L-key use the verified standalone 2+ prices (AUD 7.00 / 6.00), not the bundle prices whose quantity rule is unverified.
- **Knob:** Kilo DDS-90-4-7 (true 6.00 mm bore, knurled, 31.75 mm skirt, 15.88 mm tall) replaces the Jaycar HK7011 (6.35 bore). It is taller than the 14 mm stand-in: CAD v16 re-checks the top height.
- **Encoder washer** OD 12 instead of 14: the verified 3 mm closed-cell neoprene comes as a 12 mm wide self-adhesive tape (still 1.75 mm overlap beyond the 8.5 mm shaft hole).
- **H9 nylon standoff** Wurth 971100365 has an 8 mm stud (no 6 mm nylon version found): trim it to 6 mm (pilot floor 6.7 below the insert top).
- **RFQ refinements from sourcing:** the 15 A fuse must have an interrupting rating above the pack short-circuit current (the example NANO2 453 breaks only 50 A at rated voltage; the 456 series has no 15 A part), and the TCO must hold at least 10 A at 45 C (bimetal mini-breakers such as the NR85AB0 also trip on self-heating).
- **Feet:** no 12-16 mm buffer with an M3 stud exists in catalogues. Listed: an 8 x 8 mm M3 buffer on the kept stud (UNVERIFIED); alternative M4 inserts with a 15 x 13 mm M4 buffer and no stud. Left to the owner and the CAD agent.
- The review items S7 (wider USB-C/jack openings), S14 (lid labels), S16 (roof ribs), S5 stop ribs and S13 grille enlargement are geometry: left to the CAD agent and marked "CAD v16 (pending)".

## 2. Finding-by-finding status

### 2.1 Top findings (review section 1)

| # | Finding | Status | What was done / remains |
|---|---|---|---|
| 1 | PCB cannot be installed (SW102 shaft vs dish floor) | CAD v16 (pending) | D1 knob cup; mechanical-bom rows; 4 CSK screws + 4 inserts added to the buy list |
| 2 | Pack and drivers captive once the insert is bonded | CAD v16 (pending) | D2 removable insert; +4 CSK, +4 inserts, 1.5 mm foam sheet (row 53); Sikaflex row limited to grilles/grommet |
| 3 | Main chamber not sealed (about 214 mm2 of leaks) | CAD v16 (pending) + fixed in docs/BOM | foam rows 51-53, encoder washer row 66, plunger row 71, vents (drill row 65); CAD v16 adds the counterbores and the face-seal geometry |
| 4 | SW100 has no actuator | CAD v16 (pending) | D3; printed part row 71 |
| 5 | Nothing holds the wiring | CAD v16 (pending) + fixed in docs/BOM | D4; ties and mounts rows 55-56; anchor list in mechanical-bom |
| 6 | No fuse in the battery path | fixed in docs/BOM | RFQ item 2 (15 A fuse + about 85 C TCO, part numbers requested), rows 60-62; starter BOM PACK note synced |
| 7 | CAD, BOM and RFQ disagree | fixed in docs/BOM (CAD items: v16) | see 2.4 |
| 8 | Project status (no firmware, 9 open connections, pack not quoted, reprint needed) | owner action / deferred | plan.md and HANDOVER summaries refreshed; firmware deferred by the owner |

### 2.2 MUST items (review section 2)

| # | Item | Status | Notes |
|---|---|---|---|
| M1 | Encoder/knob installation path | CAD v16 (pending) | option (b) chosen (D1); the panel-mount encoder option (a) is not pursued, so no new encoder is bought |
| M2 | Insert retention and serviceability | CAD v16 (pending) | D2 |
| M3 | SW100 lid plunger | CAD v16 (pending) | D3; three variants printed |
| M4 | Cable management and anti-rattle | CAD v16 (pending) + fixed in docs/BOM | D4; `wire_check.py` re-run with anchor waypoints is CAD-agent scope |
| M5 | Pack fuse and thermal cut-off | fixed in docs/BOM | D5; vendor answer pending (owner action: send the RFQ) |
| M6 | Drivers before the insert; L1 needs an L-key | fixed in docs/BOM + CAD v16 (pending) | L-keys x2 (row 45), bit extension (row 49); with the removable insert the order is reversible; the CAD v16 tool-access check confirms L1 |

### 2.3 SHOULD and NICE items

| # | Item | Status | Notes |
|---|---|---|---|
| S1 | Seal main-chamber openings | CAD v16 (pending) + fixed in docs/BOM | 2 mm face foam (row 51), encoder washer (row 66) |
| S2 | Seal the 4 lid screws in the woofer loop | CAD v16 (pending) | nylon washers removed (row 22); foam washers from the 1.5 mm sheet in boss counterbores, or a butyl dab |
| S3 | Pressure-equalisation vent | fixed in docs/BOM | 0.5 mm drilled holes, drill row 65, cloth dot; CAD v16 may mark the positions |
| S4 | Lid gasket gland overfill | fixed in docs/BOM | 2 mm cord (row 50) replaces 3 mm (row 25) |
| S5 | Pack retention, cushioning, 22.3 mm | fixed in docs/BOM (RFQ) + CAD v16 (pending) | RFQ thickness 22.3; stop ribs and cradle re-cut from the vendor drawing are CAD scope |
| S6 | Knob usability | fixed in docs/BOM | new knob row 64 (true 6 mm bore, grip); raising the knob is not possible with the board-mounted 20 mm shaft (deferred) |
| S7 | Rear-lid openings for real plugs | CAD v16 (pending) | CAD-agent decision |
| S8 | Rocker SW101 leads | fixed in docs/BOM + CAD v16 (pending) | thin-wall 18 AWG (row 57), service loop, lamp tab insulated (row 7); CAD models the leads |
| S9 | Harness slack | fixed in docs/BOM | cut lengths in mechanical-bom and row 12 |
| S10 | Driver and woofer gaskets | fixed in docs/BOM + owner action | 3 mm sheet (row 52); owner checks the factory woofer gasket on the sample |
| S11 | Acoustic damping | fixed in docs/BOM + CAD v16 (pending) | polyfill 6-8 g (row 3), 10 mm foam (row 54); CAD lining placeholder |
| S12 | Feet | fixed in docs/BOM + CAD v16 (pending) | screw-in rubber feet (row 63) replace the glued Bumpon (row 21) |
| S13 | Woofer grille dust | fixed in docs/BOM | cloth behind the woofer grille (row 4); optional perforation enlargement is CAD scope |
| S14 | Labels | CAD v16 (pending) / deferred | lid deboss is CAD scope; J8/J4 silkscreen pin names deferred to the next board revision |
| S15 | Status indicator | decided (no LED in v1) | D9 |
| S16 | Insert roof stiffness | CAD v16 (pending) + owner action | ribs or a 5 mm roof; tap test after the first print |
| N1 | Nylon at H9 | fixed in docs/BOM + owner action | rows 47-48; owner runs an RSSI front/rear test |
| N2 | Field updates need the lid off | owner action | flash MCU and BM83 on the bench before installation; right-angle Dupont for J6; check the TC2030-CTX fit |
| N3 | Magnetic grille | no action | |
| N4 | EMI ferrites | no action | |
| N5 | Thermal | owner action / deferred (firmware) | log the pack NTC during the first charges; JEITA pause at 45 C is firmware policy |
| N6 | Tamper resistance | no action | post-Torx already |

### 2.4 Inconsistencies (review section 3.2)

| # | Conflict | Status | Fix |
|---|---|---|---|
| 1 | Woofer M3x20 screws missing from the buy list | fixed in docs/BOM | row 44 (button post-Torx M3x20) |
| 2 | Nylon lid washers still qty 11 and priced | fixed in docs/BOM | row 22 quantity 0, superseded |
| 3 | mechanical-bom woofer bolt circle 77 | fixed in docs/BOM | current table: 96.52 bolt circle, 68.25 square, square 82.55 frame; history kept |
| 4 | Woofer gasket recess vs factory gasket | fixed in docs/BOM | aligned on the CAD (factory 3.3 mm gasket, no recess); ring only if missing |
| 5 | Grommet hole 6.0 / web 1.6 vs Heyco 2000 | fixed in docs/BOM; CAD v16 (pending) | buy list and mechanical-bom state 6.35 / 1.5 |
| 6 | Rocker body about 11 vs 22.4 | fixed in docs/BOM + owner action | 22.4 (CAD stand-in) stated; measure the real GRB112B802BR1 |
| 7 | RFQ 23.0 vs cradle | fixed in docs/BOM | RFQ, buy list row 31 and mechanical-bom say 22.3 |
| 8 | mechanical-bom brick/PCM/title stale | fixed in docs/BOM | 86.85 x 74.47 x 21.75, PCM 60 x 18 x 1.6, new title |
| 9 | Strap placeholder 300 mm too short | owner action | row 24 unchanged (estimate): order >= 350 mm or the 20 mm VELCRO roll |
| 10 | Woofer row cites the v11.2 conflict | fixed in docs/BOM | row 2 notes |
| 11 | Consumables absent | fixed in docs/BOM | rows 50-59, 65-66 |
| 12 | Lead 180 vs routed 131 | fixed in docs/BOM | slack kept, tie point on the J5 path (anchor list) |
| 13 | CAD mass with steel grilles vs FR4 | CAD v16 (pending) | buy list keeps FR4 |
| 14 | plan.md and HANDOVER headers stale | fixed in docs/BOM | plan.md "Current status (2026-11-03)", HANDOVER "Current state (2026-11-03)" |
| 15 | release-todo still 12 open and 2P/3P/4P | fixed in docs/BOM | marked superseded for status at its top |

### 2.5 Top-10 risks (review section 4)

| # | Risk | Status |
|---|---|---|
| 1 | Enclosure cannot be assembled | CAD v16 (pending), plus its scripted insertion-path check |
| 2 | No firmware | deferred (owner: "firmware later") |
| 3 | First power-up damage | owner action (bench order in HANDOVER) |
| 4 | Hand-assembly yield | owner action (stencil, staged assembly) |
| 5 | Pack not ordered | owner action: send the RFQ (ready) |
| 6 | Long-lead silicon | owner action: BM83, PCM2902C, U19 from Digi-Key/Mouser |
| 7 | TAS5825M PBTL mis-configuration | deferred (firmware) |
| 8 | Leaks and rattles | CAD v16 (pending) + BOM rows done |
| 9 | Woofer dimensions are photo estimates | owner action: caliper the sample |
| 10 | SW100 plunger tolerance | CAD v16 (pending): three variants |

## 3. Owner action list

Quantities are for one unit with at least 10 % spares. Prices are 2026-11-03 snapshots, not quotes; shipping, duty and GST differences are excluded. **Every subtotal below is partial and is not a product cost** (no pack, PCB/stencil, electronics BOM, drivers, filament or the earlier buy-list lines).

### 3.1 Purchases added or changed by the review fixes (delta order)

| Store | Item (buy-list row) | Qty | Approx. cost | Status |
|---|---|---|---|---|
| Bolt and Nut (AUD inc GST) | Countersunk post-Torx M3x10 22CPTS310 (40) | 30 | 18.90 | VERIFIED |
| | Button post-Torx M3x10 22BPTS310 (43) | 12 | 12.00 | VERIFIED |
| | Button post-Torx M3x20 22BPTS320 (44) | 5 | 8.00 | VERIFIED |
| | Cup washer 6g 71CS6 (42) | 10 | 6.40 | VERIFIED |
| | T10 post-Torx bit 25 mm 11PT1025A (41) | 2 | 14.00 (6.00 if the bundle price applies) | VERIFIED |
| | T10 post-Torx L-key 11PTK10H (45) | 2 | 12.00 (10.00 bundle) | VERIFIED |
| | *Bolt and Nut partial* | | **A$71.30** (A$59.30 with bundles) | |
| Digi-Key AU (AUD ex GST) | Nylon standoff Wurth 971100365 (47) | 2 | 2.66 | VERIFIED |
| | Nylon screw Wurth 97791003111 (48) | 2 | 0.76 | VERIFIED |
| | Knob Kilo DDS-90-4-7 (64) | 1 | 26.82 | VERIFIED (26 in stock) |
| | Thin-wall 18 AWG TE 55A0111-18-0 / -18-2 (57) | 2 ft + 2 ft | 10.40 | VERIFIED |
| | Heyco 2000 (23, re-checked) | 2 | 0.30 | VERIFIED |
| Digi-Key (USD) | Wurth 971100321 M/F standoff (46) | 12 | USD 3.96 | VERIFIED (thread depth UNVERIFIED) |
| | *Digi-Key partial* | | **about A$46.9** (A$40.94 + USD 3.96 at an assumed 1.50) | |
| Altronics (AUD inc GST) | Cable ties 2.5 x 100 H4031A (55) | 100 | 4.55 | VERIFIED |
| | Adhesive tie mounts 21 mm H4110A (56) | 25 | 9.15 | VERIFIED |
| | Heat-shrink assortment W0886 (58) | 160 pcs | 22.95 | VERIFIED |
| | Polyimide tape 12 mm T2972A (59) | 1 roll | 14.50 | VERIFIED |
| | PCB drill set 0.3-1.2 mm T2329 (65) | 1 set | 16.95 | VERIFIED (carbide unstated) |
| | *Altronics partial* | | **A$68.10** | |
| Bunnings | Kango 300 mm 1/4 in magnetic bit holder (49) | 1 | 19.99 | VERIFIED |
| Clark Rubber | Neoprene self-adhesive tape 12 x 3 mm 15471P (52) | 2 m | 11.00 | VERIFIED price |
| Polymax (UK) | EPDM sponge cord 2 mm 2004200 (50) | 2 m | GBP 7.10 + freight (about A$14 at an assumed 2.00) | price VERIFIED; closed-cell and AU freight UNVERIFIED |
| Clark Rubber or Foam Sales (store) | Closed-cell adhesive foam 2 mm (51) and 1.5 mm (53) | about 150 x 100 and 200 x 150 mm | TBD | UNVERIFIED (no sheet source verified) |
| Jaycar | Acoustic lining AX3694 (54), or Monacor MDM-3002 10 mm | 1 sheet | TBD | UNVERIFIED |
| RS Australia | Rubber buffer M3 x 6 male, 8 x 8 RS PRO 196-1356 (63), after the feet decision | 5 | TBD | UNVERIFIED |
| element14 / Core | Hook-and-loop strap >= 350 mm or VELCRO ONE-WRAP 20 mm roll (24) | 1 | TBD | unsourced (unchanged) |
| Altronics / Jaycar (optional) | Inline mini-blade holder S6035 + 15 A fuse SF1915 (62), only if the pack vendor declines the fuse | 0 (1) | 9.25 | holder VERIFIED |

**Partial subtotal of the priced delta: about A$231** (71.30 + 46.9 + 68.10 + 19.99 + 11.00 + about 14), shipping excluded. TBD lines are not in it. The rendered buy list (`bom/hardware-buy-list.md`) now totals about **A$651** confirmed for unit 1 (A$411 build + A$240 one-off tools) plus about A$82 of estimates; also partial.

No longer bought (superseded, quantity 0): M3x16 socket pack (A$7.68), F/F spacers (USD 3.19), nylon lid washers (USD 1.10), Bumpon feet (A$1.40), 3 mm lid cord (A$9.52), Jaycar HK7011 knob (A$10.95), unsourced 0.5-1 mm foam sheet and 8 x 1.6 cup washers.

### 3.2 Owner actions without a purchase

1. **Send the pack RFQ** (`battery-pack-rfq.md`): 15 A PACK+ fuse (interrupting rating stated), about 85 C TCO (hold current >= 10 A at 45 C), max 22.3 mm, thin-wall 18 AWG leads about 180 mm, drawing, UN38.3.
2. **Feet decision:** keep the Wurth stud with an 8 x 8 mm M3 buffer (gap 20 mm), or change the 4 foot inserts to M4 and use a 15 x 13 mm M4 buffer without the stud (gap 13 mm). No 12-16 mm M3-stud buffer was found.
3. **Caliper the woofer sample** (frame, factory gasket, hole pattern, termination) before the shell prints; check the ND65 tab polarity; measure the rocker depth behind the panel.
4. Confirm on the parts: Wurth 971100321 female thread depth >= 8.5 mm (else button M3x8 22BPTS38), Heyco 2000 ID 3.56 mm (the J11 pair needs it), the 2 mm cord is closed-cell, trim the nylon standoff stud to 6 mm.
5. Route the 9 RT-15H connections in the GUI, then `regen_final.sh` (agent adopts the board afterwards); order BM83, PCM2902C and U19 from Digi-Key/Mouser.
6. After the first print: tap-test the insert roof, check the lid gasket with a paper strip, measure the front-driver impedance in the box (one peak = sealed), RSSI front vs rear, log the pack NTC during the first charges.
7. Flash the MCU and BM83 on the bench before installation (field updates need the lid off).

## 4. Sourcing evidence for the new lines

Full JSON from the sourcing agent: `/tmp/claude-1000/.../scratchpad/sourcing-review-fixes.json` (session scratchpad, not kept in the repo); the relevant data is copied into the buy-list rows 47-65 (source, MPN, price, stock, read date, URL, VERIFIED/UNVERIFIED in the notes). Blocked sites: RS AU, Jaycar, Littelfuse and Essentra returned 403; smallparts.com.au returned 429; element14 AU timed out: nothing from them is marked VERIFIED. Digi-Key AU prices are ex GST; Australian store prices inc GST.

Findings worth keeping:
- **Knob:** the ideal Same Sky SAK-002 (28.9 x 12 mm, 6 mm D bore) is non-stocked with an MOQ of 2268. Kilo DDS-90-4-7 (6.00 mm bore, skirt 31.75) is the in-stock choice.
- **Encoder:** SW102 = Alps EC11E18244AU: flat (D) metal shaft, 20 mm actuator length (Alps product list in `ai-files/datasheets/Alps_EC11E.pdf`) [V]; 6 mm shaft diameter from the EC11 family / CAD stand-in [D].
- **Nylon M/F standoffs** (Wurth 971100365) come with an 8 mm stud only: trim to 6 mm.
- **Feet:** catalogue M3 male buffers are 8 mm diameter; 12-16 mm buffers are M4.
- **Fuse:** the Littelfuse 456 series starts at 20 A (no 15 A part); the NANO2 453 15 A part breaks 50 A at rated voltage, which may be low for a 4P short: the RFQ now asks the vendor for the interrupting rating.
- **TCO:** the Bourns NR85AB0 also trips on self-heating (about 13 A at room temperature, less when warm): the RFQ now asks for a hold current of at least 10 A at 45 C.
- **Bolt and Nut** showed no nylon M3 screws or standoffs (partial read); it has nylon flat washers.

## 5. Files changed by this agent

- `ai-files/bom/hardware-buy-list.csv`: rows 2, 3, 4, 12, 13, 14, 15, 16, 17, 19, 21, 22, 23, 25, 26, 27, 30, 31, 40, 41, 42 updated in place (superseded rows at quantity 0 with dated notes); rows 43-71 appended. Applied by the one-shot `ai-files/helpers/buylist_review_fixes_20261103.py` with data in `buylist_review_fixes_20261103_rows.py`.
- `ai-files/bom/hardware-buy-list.md`: now rendered from the CSV by `ai-files/helpers/render_hardware_buylist_md.py` (re-run after every CSV edit; recomputes the partial subtotals).
- `ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv`, `.xlsx`, `.xlsx.inspect.ndjson`: one sentence added to the PACK note (fuse, TCO, 22.3 mm) by the one-shot `ai-files/helpers/bom_sync_pack_fuse_tco.py` (modelled on `bom_sync_pack_1s4p.py`; backups `ai-files/backups/*.pre-packfuse`; the xlsx zip re-tested OK).
- `ai-files/reports/battery-pack-rfq.md`: secondary protection (fuse + TCO, with interrupting rating and hold current), 22.3 mm, thin-wall leads, documents; dated change note; 1S2P history kept.
- `ai-files/cad/mechanical-bom.md`: new current-design table; the previous table kept under "History".
- `ai-files/cad/mechanical-parts.md`: dated current-design pointer and superseded marks (history kept).
- `plan.md`: header date, "Current status (2026-11-03)" section, dated notes on the stale PCB/CAD/battery lines.
- `ai-files/HANDOVER.md`: top "Current state (2026-11-03)" summary (the 2026-10-10 summary kept as history) and the section "Review fixes 2026-11-03".
- `ai-files/reports/release-todo-2026-11-03.md`: marked superseded for status.
- This report.
- Backups of every edited document: `ai-files/backups/*.pre-reviewfix-20261103` (git-ignored).
- Not touched: `ai-files/cad/` other than the two Markdown files, `ai-files/website/`, KiCad and board files. `build_site_data.py` not run (it writes the website data; the coordinator runs it). The firmware spec mentions the 20 Ah pack already; not edited.
