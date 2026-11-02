# Schematic patches P1, P4, P5 applied and board synced (RT-9p, 2026-11-02)

Agent "Apply schematic patches P1 P4 P5 and sync board".
- **Input:** `DesktopSpeaker-kicad/*.kicad_sch` and `ai-files/pcb/work-route9/RT-9.*` (DRC 0, 53 unconnected).
- **Proposals:** P1 is in `pcb/work-route8/schematic-patch.md`; P4 and P5 are in `pcb/work-route9/schematic-patch.md`.
- **Not applied:** P2 (3V_AO to R241), which is a layout lane, not a schematic change.
- **Result:** `ai-files/pcb/work-route9p/RT-9p.kicad_pcb/.kicad_pro/.kicad_dru`.
- **Not done:** not committed, nothing published.

**Bottom line.**
- **ERC:** 240 violations before and after, the identical set; **0 new**.
- **Netlist:** exactly 6 pin-net changes, all intended.
- **Board:**
  - DRC **0 violations**;
  - unconnected **53 → 50**: the CHG_INT and J7-3 NRST connections no longer exist, and PDCTRL_SDA is routed;
  - schematic parity **0 new** (243 inherited, the identical set RT-9 had against the old schematic);
  - no part moved; rule files byte-identical; HA8 and BAT_INT unchanged.

## 1. Schematic edits (text-level; uuids of untouched items kept)

| Item | File | Edit |
|---|---|---|
| P1 | `Battery_Charger.kicad_sch` | Deleted the U4-21 wire stub (`88dd1b25`) and the label `CHG_INT` (`0eff06d6`). Added a no-connect flag at U4 pin 21 (201.93, 139.7). |
| P1 | `Battery_Charger.kicad_sch`, root, `MCU.kicad_sch` | Renamed `CHG_INT` to `PC15_SPARE` on: the R106-2 label (`e08209f6`), the remote label (`0cbd59ef`), the hierarchical label (`a4c33d60`), both root sheet pins and both root labels (`a56b147c`, `b421e170`), and the MCU hierarchical label (`01baa7fc`). No position changed. |
| P4 | `MCU.kicad_sch` | The PDCTRL_SDA wire (`f175bd7a`) and hierarchical label (`a14198fc`) moved from the pin-44 row (y 97.79) to the pin-33 row (y 143.51), same x. Added a no-connect flag at pin 44 (165.1, 97.79). Deleted the pin-33 no-connect (`f3943f9b`) and the text "LED_R (reserved)" (`cae13aa4`), which sat on the new wire. Sheet note `c2a1b93a`: "PA12/PA11" became "PB13/PA11". |
| P5 | `MCU.kicad_sch` | Deleted the J7-3 wire (`d68ff8a5`) and the NRST label (`ba99af15`). Added a no-connect flag at J7 pin 3 (185.42, 66.04). |

No symbol moved and no other label changed. The ground symbols and the junctions are untouched.

**Deviation from the P1 text: the label chain is renamed, not removed.**
- R106 (the 10 k pull-up to 3V_AO, via CHG_VIO_3V0) sits on the **Battery_Charger** sheet, not on the MCU sheet as P1 assumed.
- A local label alone therefore cannot keep R106 on U3-5. The hierarchical link must stay to keep R106 on PC15 and the RT-9 copper R106-2 → U3-5.
- The link is renamed `PC15_SPARE` end to end. Removing it would split R106-2 from U3-5 and short two nets on the board.
- The CHG_INT text is gone from every sheet.

**PB13 check (DS12232 Table 12 and the AF tables).**
- PB13 is an **FT_f** I/O, the same type as PA12:
  - it is 5 V tolerant, so the R14 pull-up to LDO_3V3 is fine;
  - it has no `_d` UCPD dead-battery pull-down;
  - its AF6 is I2C2_SCL, but I2C2 runs on PB10/PB11 and the PD bus is bit-banged GPIO, so no alternate function is needed.
- **Soft conflict:** PB13 carried the *reservation* LED_R (TIM1_CH1N) for the proposed RGB status LED. No LED hardware exists.
  - The LED_R proposal moves to **PA2** (19): FT_a, TIM2_CH3 AF2 or TIM15_CH1 AF5. This is recorded in `mcu-pin-allocation.md` and the firmware spec. The sheet carries no LED_R text now.
  - The P4 alternatives (pins 34, 35, 37, 40, 41) have no routable exit (RT-9 probes), so PB13 is the only option.

**ERC** (kicad-cli 10.0.7, `--severity-all`): 240 before and 240 after, identical by type, sheet and items. They are all inherited:
- 238 `lib_symbol_issues` warnings;
- 1 `power_pin_not_driven` error;
- 1 `same_local_global_label` warning.

**Netlist diff by physical pin** (`sch export netlist`, 1130 pins before and after):

| Pin | Before | After |
|---|---|---|
| U4-21 | /CHG_INT | unconnected-(U4-~{INT}-Pad21) |
| U3-5 | /CHG_INT | /PC15_SPARE |
| R106-2 | /CHG_INT | /PC15_SPARE |
| U3-44 | /PDCTRL_SDA | unconnected-(U3-PA12[PA10]-Pad44) |
| U3-33 | unconnected-(U3-PB13-Pad33) | /PDCTRL_SDA (with J4-3, R14-2, U11-8) |
| J7-3 | /MCU/NRST | unconnected-(J7-Pin_3-Pad3) (NRST keeps C162-1, J6-3, TP19-1, U3-12) |

**Render:** the MCU, Battery_Charger and root sheets were checked as PNG crops of the exported PDF and read cleanly. `ai-files/DesktopSpeaker-preview.pdf` is refreshed.

## 2. Board sync (`work-route9p/scripts/sync.py`, text edits only)

- **Pads:** the 6 pad net lines above, with the names taken from the exported netlist. KiCad 10 boards carry no net codes or net table, so nets are by name. The "no net" pads use KiCad's own `unconnected-(…)` names, exactly as an update from the schematic would write them.
- **Copper:** the 5 `/CHG_INT` items (R106-2 → U3-5 stub: 3 segments, 2 vias) were renamed `/PC15_SPARE` with their geometry unchanged.
- **No copper removed:**
  - no CHG_INT copper reached U4-21;
  - no NRST copper reached J7-3;
  - no PDCTRL_SDA copper reached U3-44.
- **Diff:** RT-9 → `S1-raw` is exactly 11 changed net lines.
- **Refill:** done in a separate pcbnew process (python3.11 via the AppImage) with the pristine `.kicad_pro`/`.kicad_dru` beside the board.
- **Parity check** (`kicad-cli pcb drc --schematic-parity` against the project schematic, board copy in the scratchpad):
  - 243 items: 199 field mismatches, 29 attribute mismatches and 15 net conflicts (6 are U11 stacked pins with "no pad found", 9 are `/` versus `{slash}` name escaping);
  - this is the identical set RT-9 gives against the old schematic;
  - RT-9 against the new schematic would add exactly the 6 pad conflicts, and the sync clears all of them.
- **In2 rule:** `RT-9p.kicad_dru` (byte-identical) still names `/CHG_INT` in the in2_power_only exception list. This is a dead clause; `/PC15_SPARE` has no In2 copper.

## 3. PDCTRL_SDA route (U3-33 → U11-8)

The verified plan `work-route9/t/pSDA33.json` was applied first (build S2: DRC 0). Its end overlapped the existing SDA copper:
- the last F.Cu piece (135.4, 58.775)-(135.4, 58.025) lies colinear over the existing segment (135.4, 58.325)-(135.4, 57.725);
- this gave 2 T-junctions, and the new via sat 0.32 mm from the existing SDA diagonal.

**Adopted variant** (`t/pSDA33b.json`, second and final iteration): the In2 leg ends at the existing through via of the SDA tree, (134.7, 59.025), with one more 45° piece. The fourth via and the F.Cu stub are dropped.

| layer | segments (0.3 mm) |
|---|---|
| F.Cu | (131.75, 70.825)-(132.15, 70.425)-(132.15, 68.725) |
| B.Cu | (132.15, 68.725)-(134.5, 66.375) |
| F.Cu | (134.5, 66.375)-(134.5, 64.825)-(133.95, 64.275) |
| In2.Cu | (133.95, 64.275)-(135.4, 62.825)-(135.4, 59.725)-(134.7, 59.025) (PDCTRL_SDA is allowed on In2 by rule 11) |

- **Size:** 14.06 mm and 3 new vias: 0.5/0.2 at (132.15, 68.725), 0.6/0.3 at (134.5, 66.375) and (133.95, 64.275).
- **Geometry:** all exact 0/45/90; SDA T-junctions 0; the net ratio is 1.83.
- **Clearances:** checked by kicad-cli DRC, 0 violations. No GND stitching was added (slow digital line).

## 4. Gates (independent of the editing tools; `work-route9p/t/RT-9p.gates.txt`)

| Gate | RT-9 | RT-9p |
|---|---|---|
| kicad-cli DRC `--severity-all --all-track-errors`, project library | 0 | **0** |
| Unconnected | 53 | **50** (CHG_INT 1→0, NRST 1→0, PDCTRL_SDA 1→0; all other nets identical) |
| Schematic parity (new schematic) | +6 net conflicts | **0 new** (243 inherited) |
| Footprints moved / pad nets (360 fp, 1194 pads) | | **none moved**; pad diff = U4-21, U3-5, R106-2, U3-33, U3-44, J7-3 only |
| Locked copper vs RT-9 | 3421 items | 3416 untouched (SHA-256 `de2e53ae…a05e`). The 5 changed are the renamed CHG_INT items, with geometry identical (vs the synced S1-raw: 0 removed, locked SHA `806411a6…`) |
| Added copper | | 8 segments 14.057 mm + 3 vias; 0 not exact |
| Rule files | dru `ce43baa1…`, pro `aa88e8c9…` | **byte-identical**; sentinel FIRES (81) |
| HA8 failing pairs | 122 | **122** (none new, none tighter) |
| BAT_INT U4-22/23 → Q103, 6 A | 17.3 mV, 104.0 mW (2.889 mΩ) | **17.3 mV, 104.0 mW (2.889 mΩ)** |
| r7 B.Cu over In2 void | 267.7 mm | 269.5 mm (+1.8: the SDA B leg and the new In2 SDA leg under HP_DET B.Cu, HP_DET 6.2 → 7.1 mm) |
| r7 F.Cu over In1 void | 150.7 mm | 152.5 mm (+1.8, around the new vias) |
| r7 sensitive B.Cu over void, joints < 80° / < 30°, BM83 | | **unchanged** (19 / 7) |
| Parallel pairs < 0.4 mm over > 3 mm (r7 and parcheck, same net file) | | unchanged (CHG_INT/PD_PLUG_EVENT 1.5 mm pair renamed PC15_SPARE) |
| Pour check | | OK |

Teardrops: no teardrop zone was removed, and the new SDA copper has none. Teardrops remain a GUI step at the end, as in RT-9.

## 5. Open items
- **LED_R:** the reservation now proposes PA2. Mark it on the MCU sheet when an RGB LED is captured.
- **Remaining open connections (50):** see `reports/routing-rt9.md` section 4, minus CHG_INT, PDCTRL_SDA and NRST J7-3. P2 (3V_AO to R241) is still a layout task.
- **Dead rule clause:** `/CHG_INT` in rule 11 of the frozen `.kicad_dru` can be cleaned up at the next authorised rule change.

## 6. Files
- **Schematic:**
  - `DesktopSpeaker-kicad/MCU.kicad_sch`, `Battery_Charger.kicad_sch`, `DesktopSpeaker.kicad_sch`;
  - `ai-files/DesktopSpeaker-preview.pdf`.
- **Board** (`ai-files/pcb/work-route9p/`):
  - result `RT-9p.kicad_pcb/.kicad_pro/.kicad_dru`, `RT-9p.drc.json`;
  - sync-only board `S1-raw.kicad_pcb` (input of the copper-lock gate) and `S1.drc.json`.
- **Scripts:** `scripts/sync.py`, `refill_drc.sh`, `parity.sh`, `gates9p.sh`.
- **Plans, reports and gate outputs:**
  - `t/pSDA33.json`, `t/pSDA33b.json`;
  - `t/S1.sync.json`, `t/RT-9p.edit.json`;
  - `t/RT-9p.gates.txt`, `t/RT-9p.parity.json`, `t/RT-9-oldsch.parity.json`;
  - `t/RT-9p.{check,r7,par,ha8,cp}.*`, `t/RT-9base.{check,par}.*` (RT-9 with the same net file).
- **Evidence:** `evidence/rt9p-sda33.png`.
- **Docs updated:**
  - `reports/mcu-pin-allocation.md`;
  - `reports/firmware-system-spec-2026-11-01.md` (BQ25792 polling every 250 ms / 2 s; PDCTRL_SDA on PB13; J7 without NRST);
  - `reports/charge-policy-2026-11-02.md` (one note);
  - `plan.md` (MCU line);
  - `HANDOVER.md`.
- **Do not commit:** `RT-9p.geo.json` (7 MB) and `sentinel/` (a board copy) are regenerable.
