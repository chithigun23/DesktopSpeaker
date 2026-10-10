# Whole-project review (Fable, 2026-10-10): schematic, R6m board, adoption, manufacturing, bring-up

Read-only. Verified on scratch copies in the session scratchpad with KiCad 10.0.6 (`kicad-cli`): ERC and netlist export of the
current schematic, `pcb drc --schematic-parity --severity-all` of `work-r6/R6m-final.kicad_pcb` placed beside the current
schematic, semantic diff of the project `.kicad_pro`/`.kicad_dru` against the R6m copies, pad-net checks of the pin swaps and new
parts in R6m, BOM CSV scan, SW100 footprint comparison, datasheet text (TPA6132A2, BQ25792), git status. Nothing was modified.

## Verdict: NOT FAB-READY, but the circuit and the routing are release-candidate quality

ERC is 0 at default severities (1 documented exclusion, U11 VIN_3V3). R6m-final is DRC-clean apart from the 4 USB items already
argued as a full-speed waiver; strict DRC, islands, slivers and In2 hygiene were re-verified in the R6l/R6m rounds. Parity between
the current schematic (after the MCU pin swaps, C311-C316, TP26/27, J1 regrid) and R6m: **0 pad-net conflicts** (the 15
`net_conflict` rows are 6 documented U11 merged pads and 9 `{slash}` name-encoding artefacts), so no re-routing is needed.
What blocks fabrication is packaging and decisions: the project board is still placement v9b, nothing from R6 is committed,
teardrops do not exist, no fab outputs exist, and the BOM cannot be ordered as it stands.

## BLOCKERS (ranked)

| # | Where | Why | Smallest fix | Who |
|---|---|---|---|---|
| B1 | `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` (v9b: 377 footprints, 200 segments, no zones) vs `work-r6/R6m-final.kicad_pcb` (385 fp, 2586 segments, 30 arcs, 958 vias, 83 zones); project `.kicad_dru` is the old 13-rule file (3 017 B) while R6m uses the R6a rule set (10 297 B: switch_power/sensitive/critical, in2_power_only, neck_ic) | The project does not hold the reviewed board; opening the project board with its old rules gives a different DRC than every R6 gate | Copy `R6m-final.kicad_pcb` to the project board, copy `R6m-final.kicad_dru` to the project `.kicad_dru`, **keep the project `.kicad_pro`** (it is a superset: same 15 classes and 111 patterns plus the `SIGNAL *` catch-all and the ERC exclusion; R6m's copy lacks both, harmless for routing because Default and SIGNAL have identical values, but copying it would drop the ERC exclusion). Then GUI "Update PCB from Schematic": 244 parity items are fields (199), attributes (30: TP exclude-from-BOM, R256 DNP, TP13/TP14 value) and net-name encoding (9); no track changes | me |
| B2 | git: `ai-files/pcb/work-r6/` entirely untracked (R6a..R6m), the schematic pin swaps and ERC cleanup, HANDOVER/plan edits all uncommitted (`git status`: 11 modified, ~1 500 untracked) | One wrong rebuild or disk problem loses the routing; AGENTS.md asks for checkpoints at reviewed milestones | Commit the schematic changes, `R6m-final.*` + gate JSONs + `r6m/` logs, the R6 reports, renders and helpers; leave the intermediate 5 MB boards and `work-p1/*.ses` out (or add `work-r6/R6[a-l]*` to .gitignore) | me |
| B3 | R6m has 0 teardrop zones; plan sec. 5 requires teardrops on every pad/via joint; KiCad 10 has no CLI generator | Mandated step not done; it changes copper, so the sliver/strict gates must be re-run afterwards | GUI: Edit > Teardrops (project parameters already set: 0.5/1.0/2.0 mm, 5 points; use 0.6 mm max on 0402 pads), zone refill, save; then re-run `route_r6m_eval.sh`-style gates and DRC | USER (GUI), me (re-check) |
| B4 | No fab outputs anywhere under `ai-files/` (no gerber/drill/pos/CPL exports); no DRC exclusions recorded for the 4 USB errors (`drc_exclusions` empty); JLC impedance calculator never run (plan sec. 1/8, handover line 513) | Cannot order; a board with 4 DRC errors and 2 unconnected items is not a release | After B1-B3: record the USB waiver as DRC exclusions with text (as done for ERC), export gerbers (JLC 4-layer naming), Excellon drill, position file, 3D/gerber review; stackup note: JLC04161H-7628, 1.6 mm, ENIG, 1 oz outer / 0.5 oz inner (matches the R6m stackup block: 0.035/0.2104/0.0152/1.065/0.0152/0.2104/0.035) | me (outputs), USER (order options) |
| B5 | `ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv`: 99 rows, **49 without an LCSC code**, 64 flagged unverified; the `.xlsx` is dated 2026-10-06 while the CSV is 2026-10-08 (C311-C316, TP26/27 rows only in the CSV); open: PACK (2P 21700 + PCM + 10k NTC not sourced), J4, L200 (XAL7070-222MEC not at LCSC; needs an Isat >= 12 A alternative), L201-L206 MWSA1265S-220MT, C275 polymer, SW102, J5 mating housing/crimps, and about 35 0402 Murata/Yageo/Samsung rows that only need code lookups | Not orderable; cost is a partial subtotal | Sourcing pass with the 8-lookup discipline (subagent), regenerate the XLSX from the CSV, report the two inductor substitutes for approval | me (sourcing), USER (pack, inductor substitutes) |

## MAJORS (ranked)

| # | Where | Why | Smallest fix | Who |
|---|---|---|---|---|
| M1 | `Headphone_Aux.kicad_sch` U10 TPA6132A2 VDD: 1 uF only (C242 100 nF was removed in the low-risk cuts) | Datasheet sec. 9.1: "Place a 2.2 uF capacitor within 5 mm of the VDD pin" (the application figure shows 1 uF; 9.1 is the stronger statement) | Change the VDD 1 uF (C240/C241, whichever is on VDD, both CL05A105KO5NNNC) to 2.2 uF CL05A225KP5NNNC, already in the BOM, same 0402 pad: no layout change | me |
| M2 | U4 BQ25792 PGND pin 27: 2 x 0.5/0.2 vias + F bridge (R6m sec. 2); about 1.0 A per 0.2 mm via at 3 A charge from 9 V, below the project 0.7 A/via rule, inside IPC 1.5 A | Decision pending since R6l m-L1; no further copper room | Record a firmware ICHG ceiling of 3 A (0.3 C of the 2P 21700 pack, matching the handover's 2-3 A default) and close the item; or accept by IPC | USER |
| M3 | Standing user decisions from the R6k/R6l reviews not recorded in `HANDOVER.md` (grep finds none): A1 BAT_INT <= 6 A RMS continuous / 8 A for <= 1 s (BQ BATFET rating), v10d accepted deviation (U6/U7-left 100 nF 2-3 mm from the pins), USB full-speed waiver (17.3 mm uncoupled, DN 2 fine vias), 3 via-in-pad (R10.2, R224.1, C215.1 = U24 AVDD HF cap; solder wicking on hand-soldered 0402), m-R1 PMID bulk GND via 2.5 mm | Decisions exist only in review files; the handover is the single record | One "PCB release decisions" paragraph in the handover after the user answers | USER decides, me records |
| M4 | `MCU.kicad_sch` J7 TC2030 duplicates J6; J7 pads 3/4 (NRST, SWCLK) unrouted: the 2 DRC unconnected items | A release board cannot carry "unconnected" without a documented acceptance | Delete J7 from the schematic and board (J7 is not in the BOM, J6 + TP19 carry the signals), or route the two short nets to J7 | USER |
| M5 | `HANDOVER.md` lines 9-22 ("Active ... STUSB4500/BQ25895", "MCU/audio blocks remain unconnected; noPCB"), line 98, the "Final open-items list" (pre-routing); `plan.md` line 14 "No PCB layout is authorized yet" | Anyone continuing from the summary starts from a state three weeks old | Rewrite the continuation summary (<= 20 lines) and the open-items list to the R6m state; fix plan.md line 14 | me |
| M6 | SW100 `TE_1977066-1_Tact_RA_SMD`: board copy pad 1 = 0.9 x 1.7 mm at y -0.05 (both pads 1), library file still 0.9 x 1.8 at y 0 -> DRC `lib_footprint_mismatch`; the land pattern is a DRAFT from the TE drawing | "Update footprints from library" would revert the fix and bring back the 2 hole_clearance errors | Edit the library `.kicad_mod` to the board geometry; check the pad/hole geometry once against the TE drawing in `ai-files/datasheets/TE_1977066-1_datasheet.pdf` | me |
| M7 | USB DRC: 3 skew (-2.9 mm via-height artefact, two post-resistor net artefacts) + 1 uncoupled 17.3 mm against `usb_diff` max 6 mm | Errors remain in every DRC run; the waiver was recommended in R6k but never applied | DRC exclusions in the project `.kicad_pro` with the waiver text (after M3) | me after USER confirms |
| M8 | Amplifier thermal/EMI (R6j part-specific): U6/U7 thermal pad 16 vias each (plan 20), B.Cu GND under the amps in pieces; TAS5825M RthJA 24-30 K/W; OUT_x to inductor 8-10 mm (placement) | Accepted in reviews but never measured; first-bring-up risk | Keep; add "amp case temperature at 2 x 10 W, 10 min" to the bench list; add 4 EP vias only if the GUI teardrop/refill pass touches U6/U7 anyway | USER/bench |

## MINORS

- R256 DNP on U25 MODE: consistent with TI SLVSCM8D (MODE floating = PFM, grounded = forced PWM); keep DNP, fit 0R at the bench if
  PFM bursts are audible. The symbol's datasheet link `TPS61088_zh.pdf` is dangling (only `tps61088-layout-excerpt.txt` exists): store the PDF.
- `CHG_VIO_3V0` dangling port still present (root 1, Battery_Charger 2 occurrences); remove or annotate.
- MCU sheet (page 7) never visually inspected after the redraw and the pin swaps; render and look once (text/wire overlaps).
- Inherited routing minors, unchanged: 3V3_AUDIO 0.3 mm In2 trunk, 8 audio vias without a GND via within 1.2 mm, I2S trio at 0.2 mm gap
  for 30 mm, SYS_COL_B 0.18 mm tip, 7 corner hits, m-L4 (U15 L1 0.206 mm to SYS pad, U14 L2 0.777 mm to FB), 36 silk warnings (J2/J3 silk
  over pads: the fab clips it), I2S 125-128 mm with 2-4 vias, 17 pre-R6i foreign vias in In2 islands.
- Project `.kicad_pro` teardrop `td_curve_segcount` 5 vs R6m 1: keep 5 (B1 keeps the project file).
- TP13/TP14 footprint Value shows the reference, symbol value is the net name (parity, fixed by B1's update).
- BOM: J5 mating housing 43645-0300 and crimps, woofer/driver wiring, grommets are not in any BOM.
- SW101 rocker rated 10 A @ 12 VDC, LCSC stock 0, terminal mapping unverified by continuity: service disconnect only.

## First bring-up risks (e)

1. **Cold start / USB only, no battery:** U19 -> U20 -> U12 powers the MCU before any charger conversion; BQ25792 ILIM_HIZ is held low at POR
   (100 mA clamp cached), EN_EXTILIM/IINDPM must be written and read back before releasing CHG_SYS_ENABLE; REG14 SFET_PRESENT = 1 before any
   ship-mode command; watchdog/REG_RST policies (contract report). A battery-absent codec on SYS can deadlock the 100 mA budget.
2. **USB-PD dead battery:** TPS25730D sinks on dead battery (AlwaysEnableSink, 5 mA LDO_3V3 budget, pin 36, ADCIN2 code 7 = 20 V): verify the
   contract and the 20 V VBUS waveform; TVS2200 clamp maximum exceeds the controller's 28 V absolute maximum (surge immunity unproven).
3. **Boost U25:** compensation calculated only; ILIM 150k caps the output to about 15-18 W at low pack voltage by design; PFM acoustics (R256).
4. **Pack path:** boost switch peak up to about 9 A plus loads against BQ IBAT_OCP 9.3 A / 6 A RMS; Q103 and SW101 ratings; charge <= 3 A (M2).
5. **BM83:** MFB polarity/levels, 10 uF/100 nF/1 uF cap values vs the Microchip hardware guide, host-mode UART baud/TX_IND, power-off ordering
   (RST_N low before SYS_PWR < 2.7 V, > 640 us ramp-down), RF/antenna keep-out with the enclosure.
6. **Amplifiers:** write DAMP_PBTL on U7 before leaving Hi-Z (pairing verified from Fig. 159), AMP_PDN only after 3V3_AUDIO, FAULTZ wired-OR,
   case temperature (M8), click/pop on source change and HP_DET mute (firmware only).
7. **Gauge/AO domain:** TS5A3167 isolation at pack collapse, 2N7002 gates at 3.0 V, ADC reference sagging with 3V_AO.
Bench order: (a) USB only, no pack: rails, 3V_AO, MCU alive, PD contract readback at 5/9/15/20 V, VBUS waveform at attach; (b) pack only:
QON wake, ship mode entry/exit, SW101; (c) both: charger register sequence, IINDPM readback, ICHG 1 A, thermal of U4/L1; (d) 5V_LOGIC,
3V3_AUDIO, 5V_CODEC enables and ripple; (e) PVDD boost no load / 1 A / 2 A, PFM audibility; (f) U6 BTL then U7 PBTL into dummy loads,
thermal; (g) codec USB enumeration at 100 mA, PCM1862 I2S clocks; (h) BM83 power sequence, pairing, DAC level; (i) headphone/aux
detection and TPA6132A2 pop; (j) standby/ship current.

## Recommended ordered action plan to a fab-ready release

1. Adopt R6m into the project (B1): board + dru, keep pro, Update PCB from Schematic, DRC = same 4 USB + 2 J7 items. [autonomous]
2. Commit and push the checkpoint (B2). [autonomous, user asked for checkpoints]
3. User decision batch (one message): M2 ICHG cap, M3 records (A1, v10d, USB waiver, via-in-pad, m-R1), M4 J7 delete vs route,
   B4 order options (no impedance control for FS USB vs paid control; ENIG; 0.5 oz inner), B5 pack and the two inductor substitutes. [USER]
4. Schematic fixes: M1 U10 2.2 uF, CHG_VIO_3V0, SW100 library (M6), TPS61088 datasheet file, J7 per decision; ERC 0; netlist compare;
   Update PCB again; render page 7 and page 11. [autonomous]
5. Teardrops + zone refill in the GUI (B3), then re-run DRC, strict/sliver/island gates. [USER then autonomous]
6. DRC exclusions for the USB waiver with text (M7); final DRC 0 errors / 0 unconnected. [autonomous after 3]
7. BOM sourcing pass, XLSX regeneration, orderable cost (B5). [autonomous sourcing, user approval of substitutes]
8. Fab outputs: gerbers, drill, pos, BOM export, 3D/gerber review, stackup/order note (B4). [autonomous]
9. Handover/plan refresh (M5) with the release decisions, bring-up list and bench order; commit and push. [autonomous]
10. Order. [USER]

## Already good

- ERC 0 with a single, well-documented exclusion; netlist byte-identical through the grid fix (348 components, 311 nets, 1 130 pins).
- Schematic-to-PCB parity after the pin swaps: 0 pad-net conflicts; C311-C316, TP26/27, SW102 and the swapped U3 pads (18/47/55/56) are in R6m.
- R6m: DRC 0 clearance/short/width/dangling, 0 floating GND pieces, 0 copper slivers under 0.15/0.12 mm, 1 outline per island, no audio,
  I2S, USB or clock copper on In2, rule set unchanged since R6k, every change traceable by uuid; stackup block matches JLC04161H-7628.
- Power path capacity documented with numbers (SYS >= 9 A series minimum, BAT_INT 6.5 A at 15 K, VBUS_PD 3.6 A, PVDD arrays).
- Design records are unusually complete: per-round reviews, gate JSONs, reproducible helper scripts, datasheet-backed decisions
  (PBTL pairing from the rendered figure, BQ25792 ILIM/POR review, TPS25730 capacitance table), hardware default-off gates on every enable.
- Hand-solder footprint policy applied consistently (0402/0805 HandSolder), test points on every rail, antenna keep-out verified empty.
