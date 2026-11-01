# PCB placement R8b: tiered hand-assembly spacing, J4, J6 check (2026-11-01)

Stage PL of the routing restart, continuing `pcb-placement-r8.md`. Input `ai-files/pcb/work-r8/R8-placement.kicad_pcb`. Output `ai-files/pcb/work-r8/R8b-placement.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`, both unchanged copies of the R8 project files). Nothing in `DesktopSpeaker-kicad/` or the schematics was edited; no DRC rule or net class changed; headless only (KiCad 10.0.7 `kicad-cli` and `python3.11`). Nothing committed.

Files: plan (moves, dragged copper, J4 pose, field positions) `work-r8/r8b-plan.json`; apply log `work-r8/r8b-apply-report.json`; scripts `work-r8/scripts/r8b_*.py` (`r8b_ha8.py` tiered check, `r8b_place.py` greedy placer, `r8b_hdr.py` header search, `r8b_apply.py` board writer, `r8b_metrics.py` gates, `r8b_fpsilk.py`, `r8b_setpose.py`, `r8b_drc.sh`); evidence `work-r8/evidence/r8b/` (DRC JSON R8 rerun and R8b, `r8b_metrics.json`, `ha8_before.json`, `ha8_remaining.json`, before/after crops `r8b-clusters-1..4.png`).

## Summary (revision 2, after the coordinator decision of 2026-11-01)
The first R8b board is kept as `R8b-0.kicad_pcb` (+ `.pro`, `.dru`, plan `r8b-0-plan.json`). Revision 2 applies: (1) hot-loop pairs inside the vendor clusters of U4, U6, U7, U11, U14, U15, U25 are an HA8 exception with a 0.2 mm floor, fixed by micro-moves (<= 0.3 mm, decoupling no worse than +0.25 mm); (2) rule AG3: no failing pair may be tighter than in R8; (3) TP13/TP14 left untouched.
- **HA8 failing pairs (strict tiers): 203 -> 123** (tier a 0.40: 112 -> 63; a 0.25: 44 -> 29; b 1.5: 7 -> 3; c 1.5: 40 -> 28); parts involved 222 -> 130; literal F.CrtYd only: 181 -> 109. Revision 1 had 115, but 9 of its pairs had become tighter than R8; the parts were reverted and re-placed under AG3, which costs 8 pairs.
- **AG3: 0 pairs tighter than R8.** No new failing pair.
- Of the 123: **62 hot-loop exception pairs** (19 still under 0.2 mm, list below; 4 of the 23 under 0.2 mm were fixed: U15-C153 0.165 -> 0.201, C152-C153 0.15 -> 0.35, C297-C296 0.14 -> 0.24, C267-U25 0.115 -> 0.215); **3 ESD diodes at fixed connectors** (D1/J1 1.14, D200/J2 0.83, D201/J3 1.31 mm, all above the 0.25 floor); **58 involve a movable part with no legal move**. 27 non-exception pairs are under 0.25 mm; all are pre-existing and none is tighter than in R8.
- 84 parts moved: 41 R, 32 C, 9 TP, J7, J4; 5 of them are hot-loop micro-moves (C106 0.3, C150 0.2, C153 0.2, C267 0.1, C296 0.1 mm). Passive/TP moves are translations of 0.05-1.75 mm, no rotation change. Retained power/GND copper on moved pads was dragged with octilinear 45/90 degree jogs, not ripped.
- **J4 moved** to (133.5, 42.5, 90): J4 score 283.8 -> 137.2; PDCTRL_SCL MST 58.8 -> 32.7 mm, PDCTRL_SDA 56.0 -> 33.4 mm (23-26 mm shorter each). No enclosure constraint in `ai-files/cad/`.
- **J6 stays**: the only spot near U3, (116.0, 64.75, 180), is blocked by the In2 `/Fuel_Gauge_Power/USB_AUX_5V` track (127.33, 45.76)-(111.0, 61.52), 2.0 mm wide (TP21 would also move).
- **TP13/TP14**: the board nets match the schematic (TP13 = /I2S_SDATA, TP14 = /I2S_LRCK). The board values and silk labels are stale and swapped. Not edited (coordinator handles them).
- Gates: courtyard overlaps 0 (DRC and own F.CrtYd check); DRC 0 violations, 295 unconnected (294 + J4 pin 1 LDO_3V3, expected); schematic parity identical to R8 (243); pad-net / value-footprint / side differences 0; rotations all on 90 degrees; decoupling: 3 nearest-cap distances worse, max +0.25 mm (U24 VREF C212 0.55 -> 0.80), every moved cap within +0.25 mm of its R8 distance; escape corridors unchanged; analog-to-switch minimum 16.43 mm (16.48). IC scores 10,679.4 -> 10,584.2; with headers 11,791.2 -> 11,550.6.

## HA8 method
Rule (brief, rulebook HA8): (a) any two courtyards >= 0.4 mm; 0.25 mm for two 0402s sharing a non-GND net and for an IC with its own support part; (b) QFN/LQFP/fine-pitch IC >= 1.5 mm to any part that is not its own support part; (c) part taller than 3 mm >= 1.5 mm from small passives/discretes and fine-pitch ICs. The governing (largest) requirement of a pair decides its tier.
- Courtyards: union of the footprint's F.CrtYd outlines (KiCad `GetCourtyard`). **All 359 top-side parts have F.CrtYd; the pad-box + 0.25 mm fallback was needed for none** (LOGO1 is on B.Cu, no pads). 13 footprints have pads that stick out of their own F.CrtYd: J1, J2, J3, U1, U2, U5, U6, U7, U8, U9, U10, D1, SW100; for these the pad outline + 0.25 mm was added to the courtyard ("F.CrtYd + pad overhang"); the other 346 use F.CrtYd as drawn. Loose courtyards (> 3x the pad box): J9, J10, J11 (JST VH bodies, genuine).
- Support part: a C, R, FB, L, D, Q or Y that shares a non-GND net with the IC (test points and other ICs are not support parts). Same-net 0402 test ignores GND (stricter).
- Fine-pitch set (as R8): U2-U11, U14, U15, U19, U20, U24, U25, Q103. SOT-23/SOT-5 ICs (U12, U13, U16, U17, U21-U23) use tier a.
- Tall (> 3 mm), heights from the STEP models: MWSA1265S 6.5, XAL7070 7.0, SRN6045 4.33, CP 8x10 (C275) 10.0, PJ-307 5.5, pin headers J4/J6/J8 8.65, EC11E 24.5; no STEP, treated as tall: J1 USB-C, J5, J9-J11, SW100, SW101, Keystone 5010 THT loops (TP23-TP27). XFL4015 (L3) is 1.5 mm, so not tall. J7 is pads only.

## HA8 failures before / after by tier
| Tier (required) | R8 | R8b-0 (rev 1) | R8b (rev 2) | rev 2: hot-loop exception (under 0.2 mm) | rev 2: ESD diode at fixed connector | rev 2: movable part, no legal move |
|---|---|---|---|---|---|---|
| a, 0.40 mm | 112 | 59 | 63 | 33 (13) | 0 | 30 |
| a, 0.25 mm | 44 | 28 | 29 | 13 (5) | 0 | 16 |
| b, 1.5 mm | 7 | 1 | 3 | 0 | 0 | 3 |
| c, 1.5 mm | 40 | 27 | 28 | 16 (1) | 3 | 9 |
| **Total pairs** | **203** | **115** | **123** | 62 (19) | 3 | 58 |
| Parts involved | 222 | 128 | 130 | | | |
| Literal F.CrtYd only (pairs) | 181 | 101 | 109 | | | |
| Pairs tighter than R8 (AG3) | - | 9 | **0** | | | |

Hot-loop exception pairs still under 0.2 mm (19; micro-moves blocked by retained power vias within 0.5 mm of the pads (HA6), pour membership, the next cap in the row, or the U15/U4 decoupling limit): U15-C190 0.115, U15-C152 0.165, C152-C190 0.15, C190-C154 0.14, C191-U1 0.17 (C191 is a U15 cap next to the BM83, not an own-IC pair), C280-C271 0.14, L201-C271 0.124, C284-C283 0.14, C284-C278 0.15, C274-C291 0.13, C314-C270 0.11, C270-C290 0.14, C277-C292 0.14, R252-U25 0.125, U4-C103 0.14, C100-C103 0.15, C100-C312 0.19, C103-C102 0.155, C106-C110 0.02 mm. Fixing these needs a joint move of two or three caps of a row with their vias (a hot-loop copper edit), which this pass does not do.

The 3 tier-b pairs are pre-existing (C192/C193 to U15 1.465 mm, U10-C236 1.03 mm), not tighter than R8. U10-C243 stays at 0.0 (touching through the U10 pad overhang; C243 is the HPVDD cap at 0.38 mm and has no legal move).

## How moves were chosen
Greedy pass over the failing pairs, worst deficit first; only C, R, FB, TP and J7 move (not in a hot loop, not fixed). For each candidate part: 0.05 mm grid, radius 0.3/0.6/1.0/1.5/2.0 mm, translation only. A move is accepted only if: no new failing pair and fewer failures (or a lower total deficit) for that part; courtyard inside the board and outside the BM83 keep-out; no new pad in a 1 mm escape band of any fine-pitch IC; decoupling: a cap may not move more than 0.25 mm further from any same-net IC pin than in R8; analog parts keep >= 5 mm from switch pads; a pad inside a same-net pour stays inside it; no new silkscreen contact (board silk, other footprints' silk, TP labels) or silk on pads; HA6: a pad never comes closer than 0.5 mm to a via that does not move with it, unless it already was (then no closer); approximate project clearances for the pad and every dragged track (0.25 base, 1.0 switch-to-signal, 2.0 critical nets, 0.4 POWER_HI tracks, 0.55 audio). AG3 (revision 2): no pair that fails the strict HA8 may end tighter than in R8; hot-loop parts move at most 0.3 mm. Among legal moves the smallest wire-score increase, then the smallest displacement wins. Final DRC is the judge.
- Wire score: of the 83 passive/TP/J7 moves, 57 left the summed IC score unchanged or shorter (best -0.25), 26 lengthened it (at most +2.05 mm, most under +0.5; per-move values of the last move step in the move log).
- Copper: retained copper on a moved pad is dragged: 85 track segments edited, 73 jog segments added (octilinear, 45 or 90 degree bends), 2 vias moved with their pads (R209, TP3, both already at the pad). Dragged by class: GND 40, PWR_3V 18, POWER_HI 9, PWR_LOCAL 6, PWR_5V 4, SPK_OUT 4, PVDD 2, BOOT 1, SWITCH 1 (C267 boot cap, 0.1 mm). Nothing ripped except the old J4 branch of `/USB_PD/LDO_3V3` (10 tracks, 38.1 mm, dangling after J4 moved; LDO_3V3 MST 65.0 -> 35.5 mm). 114 teardrop zones next to moved copper were removed (regenerate after routing). Zones refilled.
- Silk: TP net-name labels follow their TPs (8 labels); C305 and J4 reference fields were placed explicitly to keep them off the tile lines (C305 field kept at its old absolute position, J4 field left of pin 1).

## Task 3: J4 (PD service header)
- Enclosure check: `cad/build_speaker_cad.py` cuts rear-lid openings only for J1, J2, J3 (and the SW100 plunger / SW101 rocker); `cad/check_cad.py` checks only those; `interference.md` has no J4 entry; J4 is modelled only as a board part (1x04 header STEP, `mechanical-parts.md` row 62). The harnesses (J5 to the right side pocket, J11 woofer leads) and the knob dish (r 21 mm around SW102 at 116.1, 100.9) are far from the new spot. **Confirmed: no enclosure constraint.** Note: at the rear edge J4 could be reached with only the rear lid off; at the new spot it is about 20 mm further in (still reachable from the rear opening, 8.65 mm tall header).
- Search (`r8b_hdr.py`, 0.25 mm grid, 4 rotations, after the passive moves): all HA8 tiers, courtyards, silk, escape bands, THT pads against every retained track/via on all layers.
  - The R8 suggestion (139, 60) and the score optimum near (135.75, 68.0, 90) (score 83) need TP23 (GND THT loop) moved; TP23 has no legal spot within 6 mm. Rejected.
  - Spots west of U11 (125, 57) score 82-85 but sit on the In2 USB_AUX_5V track. Rejected.
  - **Chosen (133.5, 42.5, 90)**: fully legal, in the strip above the "USB-C PD" title (pins at x 133.5-141.1, y 42.5). y 42.5 keeps the header outline 0.3 mm off the tile line at y 44.26 (y 43.0 scored 4 lower but its outline touched the line). Reference field placed left of pin 1.
- Result: J4 score 283.8 -> 137.2; PDCTRL_SCL 58.8 -> 32.7 mm, PDCTRL_SDA 56.0 -> 33.4 mm (octilinear MST); U11 score 331.1 -> 282.3. J4-D5 tier-c failure gone. The old J4 LDO_3V3 branch (38.1 mm, In2 1.5 mm track) was pruned; J4 pin 1 to LDO_3V3 is now one unconnected item for the routing stage (5 mA service supply).

## Task 4: J6 (SWD header) near the MCU
Search within 16 mm of U3 (128.0, 76.5), rotations 0/180 (pin labels stay readable), J6 tall (8.65 mm), all other rules hard:
- **No position without an inner-layer conflict.** Best spot (116.0, 64.75, 180), west of J7 and about 5 mm from the U3 courtyard: J6 score 420 -> about 152. It needs:
  - In2 track `/Fuel_Gauge_Power/USB_AUX_5V` from (127.33, 45.76) to (111.0, 61.52), 2.0 mm wide, moved (a THT pin would short it);
  - TP21 (BT_UART_TX loop) moved about 2 mm.
- Everywhere else within 16 mm fails the tall-part rule against U3's own decoupling/TPs, the U3 1.5 mm ring, other ICs, tile silk or the In2 BAT_PACK tracks ((124.0, 95.3)-(128.0, 96.53) 2.0 mm and (128.0, 96.53)-(136.0, 98.99) 1.0 mm south of U3).
- **J6 left at (168.265, 79.995)** (score 420.4 -> 419.9). Options as in R8 question 1: let routing move the USB_AUX_5V In2 trunk, or rely on J7.

## Task 5: TP13 / TP14 labels (report only)
| | Schematic (`Source_Select_ADC.kicad_sch`) | Board R8/R8b |
|---|---|---|
| TP13 | Value I2S_SDATA, label I2S_SDATA | pad net /I2S_SDATA, footprint value "I2S_LRCK", silk label "I2S_LRCK" at (144.56, 95.5) |
| TP14 | Value I2S_LRCK, label I2S_LRCK | pad net /I2S_LRCK, footprint value "I2S_SDATA", silk label "I2S_SDATA" at (144.56, 101.5) |

The nets agree with the HANDOVER (TP13 = I2S_SDATA, TP14 = I2S_LRCK after the r6e swap). The board values were never updated from the schematic (parity reports it) and the two silk labels are swapped. Not edited in R8b (coordinator handles the labels). Both TPs moved 0.1 mm to clear TP12; their labels moved with them.

## Gates (revision 2)
| Gate | R8 | R8b |
|---|---|---|
| Courtyard overlaps, DRC and own check on F.CrtYd | 0 | 0 |
| Courtyard overlaps with the pad-overhang correction | 1 (U10-C243) | 1 (same, unchanged) |
| DRC, project rules, `--severity-all` | 0 violations, 294 unconnected | **0 violations**, 295 unconnected (+1: J4 pin 1 LDO_3V3) |
| Schematic parity | 243 | 243, identical items |
| Pad-net / value-footprint / side differences vs R8 | - | 0 / 0 / 0 |
| Rotations off 90 degrees; SMD on bottom | 0; 0 | 0; 0 |
| HA8 failing pairs (strict tiers) | 203 | 123 |
| HA8 pairs tighter than R8 (AG3) | - | 0 |
| Hot-loop exception pairs under 0.2 mm | 23 | 19 |
| Decoupling worse than R8 | - | 3 nearest-cap values, max +0.25 mm (U24 VREF C212); none > 0.25 |
| Escape corridors (foreign / own pads in 1 mm bands) | as R8 | unchanged for every fine-pitch IC |
| Analog (AUDIO pads) to switch pads, minimum | 16.48 mm | 16.43 mm; none < 5 mm |
| Moved pads closer than 0.5 mm to a via that stays | - | 0 (R209 and TP3 carry their own via) |
| Signal-net octilinear MST total | 4,433.9 mm | 4,389.1 mm |
| All nets MST | 6,332.0 mm | 6,262.9 mm |

## Per-IC and header scores (octilinear, as R8)
| Part | Score R8 | Score R8b | Change |
|---|---|---|---|
| J4 | 283.8 | 137.2 | -146.6 |
| J6 | 420.4 | 419.9 | -0.5 |
| J7 | 254.1 | 255.7 | +1.6 |
| J8 | 153.5 | 153.6 | +0.1 |
| U1 | 138.2 | 138.1 | -0.1 |
| U2 | 53.2 | 53.4 | +0.2 |
| U3 | 4010.2 | 3962.3 | -47.9 |
| U4 | 1151.7 | 1152.0 | +0.3 |
| U5 | 44.2 | 44.2 | +0.0 |
| U6 | 1330.6 | 1330.6 | +0.0 |
| U7 | 1645.1 | 1645.0 | -0.1 |
| U8 | 81.6 | 81.5 | -0.1 |
| U9 | 101.7 | 101.8 | +0.1 |
| U10 | 397.1 | 397.4 | +0.3 |
| U11 | 331.1 | 282.3 | -48.8 |
| U12 | 42.3 | 42.4 | +0.1 |
| U13 | 196.3 | 196.3 | +0.0 |
| U14 | 59.9 | 59.9 | +0.0 |
| U15 | 98.7 | 98.7 | +0.0 |
| U16 | 181.6 | 181.6 | +0.0 |
| U17 | 114.7 | 114.7 | +0.0 |
| U19 | 0.0 | 0.0 | +0.0 |
| U20 | 63.1 | 62.9 | -0.2 |
| U21 | 17.2 | 17.3 | +0.1 |
| U22 | 0.0 | 0.0 | +0.0 |
| U23 | 65.1 | 65.1 | +0.0 |
| U24 | 447.7 | 447.9 | +0.2 |
| U25 | 108.1 | 108.8 | +0.7 |
| **Total U** | 10679.4 | 10584.2 | -95.2 |
| **Total U + J4/J6/J7/J8** | 11791.2 | 11550.6 | -240.6 |

## Decoupling distances, all ICs (cap pad edge to nearest same-net IC pad)
| IC | Rail / local net | Nearest cap R8 (mm, ref) | R8b (mm, ref) |
|---|---|---|---|
| U15 | /3V8_BT | 1.14 C152 | 1.14 C152 |
| U15 | /SYS_RAW | 1.25 C150 | 1.25 C150 |
| U16 | /3V_AO | 4.77 C123 | 4.77 C123 |
| U6 | /3V3_AUDIO | 1.29 C281 | 1.29 C281 |
| U6 | /Amplifiers/PVDD_AMP | 1.34 C276 | 1.34 C276 |
| U6 | Net-(U6-AVDD) | 1.18 C284 | 1.18 C284 |
| U6 | Net-(U6-GVDD) | 1.18 C283 | 1.18 C283 |
| U6 | Net-(U6-VR_DIG) | 2.00 C282 | 2.00 C282 |
| U14 | /5V_LOGIC | 2.05 C141 | 2.05 C141 |
| U14 | /SYS_RAW | 1.57 C140 | 1.57 C140 |
| U20 | /Fuel_Gauge_Power/USB_AUX_5V | 0.67 C124 | 0.67 C124 |
| U20 | /SYS_RAW | 0.66 C125 | 0.66 C125 |
| U4 | /Battery_Charger/BAT_INT | 2.73 C106 | 2.71 C106 |
| U4 | /Battery_Charger/PMID | 0.77 C312 | 0.77 C312 |
| U4 | /Battery_Charger/REGN | 0.94 C102 | 0.94 C102 |
| U4 | /Battery_Charger/VBUS_PD | 0.71 C313 | 0.71 C313 |
| U4 | /SYS_RAW | 0.77 C311 | 0.77 C311 |
| U22 | /3V3_AUDIO | 0.53 C222 | 0.53 C222 |
| U22 | /5V_LOGIC | 0.86 C224 | 0.86 C224 |
| U19 | /Fuel_Gauge_Power/USB_AUX_5V | 0.78 C5 | 0.78 C5 |
| U19 | /USB_VBUS | 0.64 C316 | 0.64 C316 |
| U9 | /3V3_AUDIO | 1.61 C237 | 1.61 C237 |
| U3 | /3V_AO | 1.39 C160 | 1.39 C160 |
| U8 | /3V3_AUDIO | 2.84 C238 | 2.84 C238 |
| U11 | /Battery_Charger/VBUS_PD | 1.66 C315 | 1.66 C315 |
| U11 | /USB_PD/LDO_1V5 | 0.80 C181 | 0.80 C181 |
| U11 | /USB_PD/LDO_3V3 | 1.79 C6 | 1.79 C6 |
| U11 | /USB_VBUS | 0.92 C2 | 0.92 C2 |
| U13 | /3V_AO | 0.64 C130 | 0.64 C130 |
| U10 | /3V3_AUDIO | 1.89 C241 | 1.89 C241 |
| U10 | Net-(U10-HPVDD) | 0.38 C243 | 0.38 C243 |
| U10 | Net-(U10-HPVSS) | 0.73 C244 | 0.82 C244 **(+0.09)** |
| U23 | /5V_CODEC | 0.84 C225 | 0.84 C225 |
| U23 | /5V_LOGIC | 12.09 C221 | 12.09 C221 |
| U21 | /Fuel_Gauge_Power/BAT_PACK | 0.56 C126 | 0.66 C126 **(+0.10)** |
| U2 | Net-(U2-VBUS) | 0.59 C170 | 0.59 C170 |
| U2 | Net-(U2-VCCCI) | 2.08 C175 | 2.08 C175 |
| U2 | Net-(U2-VCCP1I) | 2.40 C174 | 2.40 C174 |
| U2 | Net-(U2-VCCP2I) | 2.36 C173 | 2.36 C173 |
| U2 | Net-(U2-VCCXI) | 0.61 C172 | 0.61 C172 |
| U2 | Net-(U2-VCOM) | 1.19 C176 | 1.19 C176 |
| U5 | /Fuel_Gauge_Power/BAT_PACK | 0.56 C120 | 0.56 C120 |
| U25 | /Amplifiers/PVDD_AMP | 0.63 C314 | 0.63 C314 |
| U25 | /SYS_RAW | 1.47 C260 | 1.47 C260 |
| U25 | Net-(U25-VCC) | 1.07 C265 | 1.07 C265 |
| U7 | /3V3_AUDIO | 1.29 C294 | 1.29 C294 |
| U7 | /Amplifiers/PVDD_AMP | 1.34 C289 | 1.34 C289 |
| U7 | Net-(U7-AVDD) | 1.18 C297 | 1.18 C297 |
| U7 | Net-(U7-GVDD) | 1.18 C296 | 1.18 C296 |
| U7 | Net-(U7-VR_DIG) | 2.01 C295 | 2.01 C295 |
| U1 | /3V8_BT | 0.57 C191 | 0.57 C191 |
| U1 | Net-(U1-SYS_PWR) | 1.82 C193 | 1.82 C193 |
| U1 | Net-(U1-VDD_IO) | 0.57 C192 | 0.57 C192 |
| U17 | /3V_AO | 0.62 C131 | 0.62 C131 |
| U12 | /3V_AO | 0.84 C123 | 0.84 C123 |
| U24 | /3V3_AUDIO | 1.44 C217 | 1.44 C217 |
| U24 | Net-(U24-AVDD) | 0.54 C215 | 0.54 C215 |
| U24 | Net-(U24-LDO) | 1.14 C213 | 1.14 C213 |
| U24 | Net-(U24-VREF) | 0.55 C212 | 0.80 C212 **(+0.25)** |

## Rejected alternatives
- Revision 1 (`R8b-0`): 115 pairs, but 9 pairs tighter than R8 (C246-J3 0.625 -> 0.175 worst); replaced by revision 2 under AG3.
- Hot-loop micro-moves beyond 0.3 mm (C106 0.82 mm was found first): rejected, limit 0.3 mm.
- Moving D/Q/Y discretes (ESD diodes at J1-J3, Q100-Q102, Y170/Y200): not passives; their neighbours were moved instead where possible. D1, D200, D201 stay at their connectors (ESD close to the pin), 3 tier-c pairs remain.
- Earlier trial plans (not delivered): one put C262's GND pad over its own via and moved several pads to within 0.0-0.3 mm of vias (via-in-pad), another put TP27 and C305 silk on tile lines; the via-to-pad and footprint-silk checks were added and those moves redone. J4 at (133.0-133.25, 43.0): header outline touched the y 44.26 tile line (DRC silk), moved to y 42.5.

## Open questions for the owner
1. **Hot-loop pairs under 0.2 mm** (19): accept, or allow joint moves of cap rows together with their power vias (a hot-loop copper edit)?
2. **Tall inductors (tier c)**: the LC-filter and output caps beside L200-L206 and L1 cannot reach 1.5 mm without lengthening the loops. Is 1.5 mm needed for parts that are reflowed before the inductors (or are the inductors reflowed too)?
3. **J6**: keep at the old tile, or let routing move the In2 USB_AUX_5V trunk so J6 can go to (116.0, 64.75)?
4. **J4 access**: the new spot is about 20 mm in from the rear edge. Fine for a service header used with the rear lid off?

## Move log (84 parts)
"HA8 failures before -> after" are the partner parts failing with this part at the last move step. Wire delta = change of the summed IC/header octilinear score from that step.

| Ref | Old (x, y, rot) | New (x, y, rot) | Move mm | HA8 partners failing before -> after (last step) | Wire delta | Dragged tracks / vias |
|---|---|---|---|---|---|---|
| C106 | 157.200, 123.140, -90 | 157.200, 122.840, -90 | 0.30 | 2 (C110, TP2) -> 1 (C110) [hot-loop micro-move, 0.2 mm floor] | +0.00 | 1 / 0 |
| C122 | 112.560, 74.780, 0 | 112.410, 74.780, 0 | 0.15 | 1 (C123) -> 0 | -0.09 | 1 / 0 |
| C126 | 102.650, 81.700, 90 | 102.750, 81.700, 90 | 0.10 | 1 (U21) -> 0 | +0.00 | 3 / 0 |
| C150 | 116.820, 33.460, 180 | 116.620, 33.460, 180 | 0.20 | 1 (R152) -> 0 [hot-loop micro-move, 0.2 mm floor] | +0.00 | 2 / 0 |
| C153 | 119.650, 40.450, -90 | 119.850, 40.450, -90 | 0.20 | 2 (C152, U15) -> 0 [hot-loop micro-move, 0.2 mm floor] | +0.00 | 2 / 0 |
| C177 | 153.460, 51.860, 90 | 153.360, 51.810, 90 | 0.11 | 2 (C172, Y170) -> 0 | +0.09 | 1 / 0 |
| C178 | 159.160, 50.560, 90 | 159.260, 50.560, 90 | 0.10 | 1 (Y170) -> 1 (Y170) | +0.04 | 1 / 0 |
| C183 | 138.400, 52.100, 90 | 138.250, 52.100, 90 | 0.15 | 2 (C182, U11) -> 2 (C182, U11) | +0.06 | 2 / 0 |
| C200 | 161.350, 79.000, 180 | 161.450, 79.000, 180 | 0.10 | 2 (C203, R200) -> 1 (C203) | +0.00 | 0 / 0 |
| C201 | 161.350, 77.700, 180 | 161.450, 77.650, 180 | 0.11 | 2 (C200, R201) -> 0 | +0.00 | 0 / 0 |
| C202 | 161.350, 81.600, 180 | 161.450, 81.650, 180 | 0.11 | 2 (C203, R202) -> 0 | +0.00 | 0 / 0 |
| C203 | 161.350, 80.300, 180 | 161.450, 80.300, 180 | 0.10 | 2 (C200, R203) -> 1 (C200) | +0.00 | 0 / 0 |
| C204 | 191.190, 39.600, -90 | 191.140, 39.600, -90 | 0.05 | 3 (C205, C234, R224) -> 1 (R224) | +0.00 | 0 / 0 |
| C208 | 155.950, 80.950, 0 | 155.950, 81.000, 0 | 0.05 | 1 (C209) -> 0 | -0.05 | 1 / 0 |
| C212 | 152.100, 80.350, 90 | 152.450, 80.200, 90 | 0.38 | 2 (C215, U24) -> 0 | +0.29 | 2 / 0 |
| C214 | 145.400, 76.950, 90 | 145.150, 76.100, 90 | 0.89 | 1 (Y200) -> 0 | +0.00 | 2 / 0 |
| C230 | 171.590, 59.100, 0 | 171.340, 59.100, 0 | 0.25 | 1 (C238) -> 0 | +0.00 | 0 / 0 |
| C231 | 175.890, 62.870, -90 | 175.890, 62.920, -90 | 0.05 | 1 (R220) -> 0 | +0.00 | 0 / 0 |
| C233 | 174.200, 70.200, 180 | 173.950, 70.400, 180 | 0.32 | 1 (U8) -> 0 | +0.00 | 0 / 0 |
| C234 | 192.490, 38.800, -90 | 192.340, 38.800, -90 | 0.15 | 1 (D201) -> 0 | +0.00 | 0 / 0 |
| C236 | 192.140, 62.980, -90 | 191.690, 62.980, -90 | 0.45 | 1 (U10) -> 1 (U10) | +0.00 | 1 / 0 |
| C244 | 198.440, 68.080, 0 | 198.440, 68.180, 0 | 0.10 | 1 (U10) -> 0 | +0.00 | 2 / 0 |
| C245 | 200.390, 65.930, -90 | 200.390, 66.130, -90 | 0.20 | 1 (C243) -> 0 | +0.00 | 2 / 0 |
| C266 | 151.640, 151.380, -90 | 151.690, 151.380, -90 | 0.05 | 1 (C260) -> 0 | -0.02 | 1 / 0 |
| C267 | 150.550, 143.200, 90 | 150.550, 143.100, 90 | 0.10 | 1 (U25) -> 0 [hot-loop micro-move, 0.2 mm floor] | +0.00 | 2 / 0 |
| C269 | 158.150, 142.900, 90 | 158.150, 143.100, 90 | 0.20 | 2 (C268, R251) -> 1 (R251) | -0.08 | 1 / 0 |
| C279 | 161.960, 145.700, -90 | 162.210, 145.650, -90 | 0.25 | 1 (C290) -> 0 | +0.00 | 2 / 0 |
| C296 | 187.690, 127.250, 180 | 187.690, 127.150, 180 | 0.10 | 1 (C297) -> 0 [hot-loop micro-move, 0.2 mm floor] | +0.00 | 2 / 0 |
| C304 | 88.540, 134.900, -90 | 87.790, 135.050, -90 | 0.76 | 2 (L203, L204) -> 2 (L203, L204) | +0.00 | 2 / 0 |
| C305 | 88.480, 139.200, 90 | 87.730, 139.200, 90 | 0.75 | 1 (L204) -> 0 | +0.00 | 2 / 0 |
| C306 | 208.120, 131.200, 180 | 208.120, 130.550, 180 | 0.65 | 1 (L205) -> 0 | +0.00 | 2 / 0 |
| C307 | 176.970, 131.200, 0 | 176.970, 130.550, 0 | 0.65 | 1 (L206) -> 0 | +0.00 | 2 / 0 |
| J4 | 158.580, 23.093, 0 | 133.500, 42.500, 90 | 31.71 | J4 re-posed (task 3) | J4 283.8 -> 137.2 | old LDO_3V3 branch pruned |
| J7 | 121.750, 64.500, 180 | 122.100, 64.050, 180 | 0.57 | 1 (U3) -> 0 | +2.05 | 0 / 0 |
| R15 | 131.970, 61.400, 90 | 131.970, 61.250, 90 | 0.15 | 1 (TP5) -> 0 | -0.06 | 2 / 0 |
| R17 | 138.270, 61.600, 0 | 138.320, 61.600, 0 | 0.05 | 1 (R11) -> 0 | -0.00 | 2 / 0 |
| R100 | 153.370, 129.080, 0 | 153.370, 128.930, 0 | 0.15 | 1 (TP11) -> 0 | -0.15 | 1 / 0 |
| R102 | 159.400, 123.140, 0 | 160.000, 122.640, 0 | 0.78 | 1 (C106) -> 0 | +0.39 | 1 / 0 |
| R107 | 164.690, 108.290, 0 | 164.690, 108.140, 0 | 0.15 | 1 (Q100) -> 0 | -0.15 | 1 / 0 |
| R108 | 154.670, 126.780, 90 | 154.270, 126.880, 90 | 0.41 | 1 (C110) -> 0 | -0.07 | 1 / 0 |
| R109 | 182.760, 111.340, -90 | 182.860, 111.340, -90 | 0.10 | 1 (Q101) -> 0 | +0.10 | 1 / 0 |
| R111 | 181.540, 105.850, -90 | 181.690, 105.600, -90 | 0.29 | 1 (Q102) -> 0 | +0.05 | 1 / 0 |
| R113 | 131.570, 24.745, 90 | 131.420, 24.745, 90 | 0.15 | 1 (SW100) -> 0 | +0.00 | 0 / 0 |
| R127 | 106.070, 79.780, 180 | 106.070, 79.630, 180 | 0.15 | 1 (Q104) -> 0 | +0.06 | 1 / 0 |
| R142 | 91.930, 97.470, 180 | 91.930, 97.420, 180 | 0.05 | 1 (R141) -> 0 | +0.03 | 1 / 0 |
| R154 | 118.020, 48.660, 0 | 118.020, 48.810, 0 | 0.15 | 1 (TP9) -> 0 | +0.00 | 2 / 0 |
| R170 | 150.550, 65.180, 90 | 150.500, 65.230, 90 | 0.07 | 1 (U2) -> 0 | +0.00 | 3 / 0 |
| R171 | 149.050, 59.580, -90 | 149.050, 59.730, -90 | 0.15 | 2 (R172, R173) -> 1 (R172) | -0.15 | 0 / 0 |
| R172 | 149.000, 62.180, -90 | 148.900, 62.380, -90 | 0.22 | 1 (R171) -> 0 | +0.18 | 0 / 0 |
| R174 | 152.860, 49.860, 0 | 152.710, 49.910, 0 | 0.16 | 1 (Y170) -> 0 | +0.02 | 0 / 0 |
| R185 | 99.300, 24.460, 180 | 99.300, 24.360, 180 | 0.10 | 1 (U1) -> 0 | +0.24 | 0 / 0 |
| R187 | 93.400, 24.460, 0 | 93.200, 24.360, 0 | 0.22 | 1 (U1) -> 0 | +0.02 | 0 / 0 |
| R202 | 159.000, 81.600, 180 | 159.000, 81.650, 180 | 0.05 | 1 (R203) -> 0 | -0.02 | 0 / 0 |
| R204 | 155.750, 90.680, 180 | 155.750, 90.730, 180 | 0.05 | 1 (C211) -> 0 | +0.05 | 0 / 0 |
| R206 | 149.045, 90.668, -90 | 149.095, 90.618, -90 | 0.07 | 2 (R207, R211) -> 1 (R211) | +0.01 | 0 / 0 |
| R208 | 146.445, 90.668, -90 | 146.395, 90.668, -90 | 0.05 | 1 (R207) -> 0 | +0.02 | 0 / 0 |
| R209 | 152.900, 92.000, 90 | 152.950, 91.950, 90 | 0.07 | 1 (H2) -> 1 (H2) | +0.04 | 2 / 1 |
| R210 | 139.850, 79.350, -90 | 139.850, 79.600, -90 | 0.25 | 1 (TP6) -> 0 | -0.21 | 2 / 0 |
| R211 | 150.600, 92.450, 0 | 150.400, 92.600, 0 | 0.25 | 1 (R206) -> 0 | +0.13 | 1 / 0 |
| R225 | 189.890, 39.670, 90 | 189.740, 40.370, 90 | 0.72 | 1 (C204) -> 0 | +0.00 | 0 / 0 |
| R226 | 172.490, 60.400, 180 | 172.290, 60.650, 180 | 0.32 | 1 (C238) -> 0 | -0.25 | 0 / 0 |
| R228 | 170.990, 69.790, 90 | 170.940, 69.840, 90 | 0.07 | 1 (U8) -> 0 | +0.07 | 0 / 0 |
| R230 | 186.590, 65.890, -90 | 186.690, 65.940, -90 | 0.11 | 1 (C240) -> 0 | +0.08 | 0 / 0 |
| R236 | 199.240, 62.480, 90 | 199.340, 62.380, 90 | 0.14 | 1 (C243) -> 1 (C243) | +0.28 | 2 / 0 |
| R237 | 194.040, 68.080, 180 | 193.790, 67.980, 180 | 0.27 | 1 (U10) -> 0 | +0.00 | 1 / 0 |
| R239 | 178.220, 37.050, 90 | 178.170, 37.150, 90 | 0.11 | 1 (J2) -> 0 | +0.00 | 2 / 0 |
| R240 | 179.820, 36.450, -90 | 180.020, 37.150, -90 | 0.73 | 1 (J2) -> 0 | -0.09 | 0 / 0 |
| R242 | 190.420, 36.250, 180 | 190.420, 36.300, 180 | 0.05 | 1 (J3) -> 1 (J3) | -0.02 | 0 / 0 |
| R243 | 197.790, 37.400, -90 | 197.940, 37.400, -90 | 0.15 | 1 (D201) -> 0 | +0.00 | 1 / 0 |
| R250 | 160.350, 142.900, -90 | 160.400, 142.300, -90 | 0.60 | 2 (C279, R251) -> 1 (R251) | +0.30 | 1 / 0 |
| R253 | 155.950, 142.900, 90 | 155.800, 143.000, 90 | 0.18 | 2 (C268, R254) -> 1 (R254) | -0.16 | 1 / 0 |
| R254 | 157.050, 142.900, 90 | 156.950, 143.000, 90 | 0.14 | 3 (C268, C269, R253) -> 1 (R253) | -0.14 | 0 / 0 |
| R255 | 149.060, 140.640, 90 | 149.060, 139.840, 90 | 0.80 | 1 (L200) -> 0 | +0.00 | 1 / 0 |
| R261 | 196.860, 124.000, 180 | 196.510, 123.900, 180 | 0.36 | 1 (C295) -> 0 | -0.04 | 3 / 0 |
| R262 | 116.100, 127.190, 90 | 116.000, 127.340, 90 | 0.18 | 1 (L201) -> 1 (L201) | +0.32 | 1 / 0 |
| TP3 | 103.547, 87.228, 90 | 104.097, 87.228, 90 | 0.55 | 1 (U5) -> 0 | +0.00 | 6 / 1 |
| TP4 | 95.978, 86.210, 0 | 95.278, 86.210, 0 | 0.70 | 1 (U5) -> 0 | +0.00 | 1 / 0 |
| TP6 | 140.245, 76.555, 0 | 140.245, 76.705, 0 | 0.15 | 2 (C218, R210) -> 1 (R210) | +0.00 | 2 / 0 |
| TP9 | 115.815, 46.565, 0 | 116.615, 46.565, 0 | 0.80 | 1 (C154) -> 0 | +0.00 | 2 / 0 |
| TP13 | 147.000, 95.500, 0 | 147.000, 95.400, 0 | 0.10 | 1 (TP12) -> 0 | +0.08 | 0 / 0 |
| TP14 | 147.000, 101.500, 0 | 147.000, 101.600, 0 | 0.10 | 1 (TP12) -> 0 | -0.08 | 0 / 0 |
| TP20 | 110.005, 149.395, 0 | 110.155, 149.645, 0 | 0.29 | 1 (TP10) -> 0 | +0.33 | 0 / 0 |
| TP23 | 137.399, 65.300, 0 | 137.399, 65.600, 0 | 0.30 | 2 (R11, R17) -> 0 | +0.00 | 0 / 0 |
| TP27 | 146.000, 132.000, 0 | 144.250, 132.050, 0 | 1.75 | 1 (C109) -> 0 | +0.00 | 0 / 0 |

## Remaining HA8 failures (123 pairs)
| Category | Tier | Required mm | Part A (role) | Part B (role) | Gap R8b mm |
|---|---|---|---|---|---|
| ESD diode at fixed connector | c | 1.50 | D201  | J3  | 1.310 |
| ESD diode at fixed connector | c | 1.50 | J1  | D1  | 1.140 |
| ESD diode at fixed connector | c | 1.50 | J2  | D200  | 0.830 |
| hot-loop exception | a | 0.40 | C100 (U4 in/out cap) | C312 (U4 in/out cap) | 0.190 **< 0.2** |
| hot-loop exception | a | 0.40 | C100 (U4 in/out cap) | C103 (U4 sw/boot) | 0.150 **< 0.2** |
| hot-loop exception | a | 0.40 | C103 (U4 sw/boot) | C102 (U4 in/out cap) | 0.155 **< 0.2** |
| hot-loop exception | a | 0.40 | C104 (U4 in/out cap) | C311 (U4 in/out cap) | 0.210 |
| hot-loop exception | a | 0.40 | C106 (U4 in/out cap) | C110 (U4 sw/boot) | 0.020 **< 0.2** |
| hot-loop exception | a | 0.40 | C141 (U14 in/out cap) | C142 (U14 in/out cap) | 0.280 |
| hot-loop exception | a | 0.40 | C152 (U15 in/out cap) | C190 (U15 in/out cap) | 0.150 **< 0.2** |
| hot-loop exception | a | 0.40 | C152 (U15 in/out cap) | C153 (U15 in/out cap) | 0.350 |
| hot-loop exception | a | 0.40 | C190 (U15 in/out cap) | C154 (U15 in/out cap) | 0.140 **< 0.2** |
| hot-loop exception | a | 0.25 | C191 (U15 in/out cap) | U1  | 0.170 **< 0.2** |
| hot-loop exception | a | 0.25 | C267 (U25 sw/boot) | U25  | 0.215 |
| hot-loop exception | a | 0.40 | C270 (U25 in/out cap) | C290 (U25 in/out cap) | 0.140 **< 0.2** |
| hot-loop exception | a | 0.40 | C271 (U6 in/out cap) | C282 (U6 in/out cap) | 0.321 |
| hot-loop exception | a | 0.40 | C274 (U7 in/out cap) | C296 (U7 in/out cap) | 0.336 |
| hot-loop exception | a | 0.40 | C274 (U7 in/out cap) | C297 (U7 in/out cap) | 0.290 |
| hot-loop exception | a | 0.40 | C274 (U7 in/out cap) | C291 (U7 in/out cap) | 0.130 **< 0.2** |
| hot-loop exception | a | 0.40 | C277 (U25 in/out cap) | C290 (U25 in/out cap) | 0.354 |
| hot-loop exception | a | 0.40 | C277 (U25 in/out cap) | C292 (U25 in/out cap) | 0.140 **< 0.2** |
| hot-loop exception | a | 0.40 | C277 (U25 in/out cap) | C270 (U25 in/out cap) | 0.250 |
| hot-loop exception | a | 0.40 | C277 (U25 in/out cap) | C261 (U25 in/out cap) | 0.320 |
| hot-loop exception | a | 0.40 | C277 (U25 in/out cap) | C264 (U25 in/out cap) | 0.320 |
| hot-loop exception | a | 0.40 | C280 (U6 in/out cap) | C271 (U6 in/out cap) | 0.140 **< 0.2** |
| hot-loop exception | a | 0.40 | C282 (U6 in/out cap) | C281 (U6 in/out cap) | 0.390 |
| hot-loop exception | a | 0.40 | C284 (U6 in/out cap) | C283 (U6 in/out cap) | 0.140 **< 0.2** |
| hot-loop exception | a | 0.40 | C284 (U6 in/out cap) | C278 (U6 in/out cap) | 0.150 **< 0.2** |
| hot-loop exception | a | 0.40 | C286 (U6 sw/boot) | C288 (U6 sw/boot) | 0.390 |
| hot-loop exception | a | 0.40 | C291 (U7 in/out cap) | C300 (U7 sw/boot) | 0.260 |
| hot-loop exception | a | 0.40 | C292 (U25 in/out cap) | C290 (U25 in/out cap) | 0.250 |
| hot-loop exception | a | 0.40 | C292 (U25 in/out cap) | C270 (U25 in/out cap) | 0.252 |
| hot-loop exception | a | 0.40 | C294 (U7 in/out cap) | C295 (U7 in/out cap) | 0.390 |
| hot-loop exception | a | 0.25 | C294 (U7 in/out cap) | U7  | 0.238 |
| hot-loop exception | a | 0.40 | C297 (U7 in/out cap) | C296 (U7 in/out cap) | 0.240 |
| hot-loop exception | a | 0.40 | C301 (U7 sw/boot) | C299 (U7 sw/boot) | 0.390 |
| hot-loop exception | a | 0.40 | C312 (U4 in/out cap) | C101 (U4 in/out cap) | 0.210 |
| hot-loop exception | a | 0.40 | C314 (U25 in/out cap) | C270 (U25 in/out cap) | 0.110 **< 0.2** |
| hot-loop exception | a | 0.40 | L3 (U15 sw/boot) | C153 (U15 in/out cap) | 0.220 |
| hot-loop exception | a | 0.25 | R252 (U25 sw/boot) | U25  | 0.125 **< 0.2** |
| hot-loop exception | a | 0.25 | U15  | C190 (U15 in/out cap) | 0.115 **< 0.2** |
| hot-loop exception | a | 0.25 | U15  | C152 (U15 in/out cap) | 0.165 **< 0.2** |
| hot-loop exception | a | 0.25 | U15  | C153 (U15 in/out cap) | 0.201 |
| hot-loop exception | a | 0.25 | U4  | C312 (U4 in/out cap) | 0.215 |
| hot-loop exception | a | 0.25 | U4  | C103 (U4 sw/boot) | 0.140 **< 0.2** |
| hot-loop exception | a | 0.25 | U4  | C311 (U4 in/out cap) | 0.215 |
| hot-loop exception | a | 0.25 | U4  | C313 (U4 in/out cap) | 0.215 |
| hot-loop exception | a | 0.25 | U6  | C281 (U6 in/out cap) | 0.227 |
| hot-loop exception | a | 0.25 | U7  | C298 (U7 sw/boot) | 0.230 |
| hot-loop exception | c | 1.50 | C104 (U4 in/out cap) | L1 (U4 sw/boot) | 1.380 |
| hot-loop exception | c | 1.50 | C273 (U7 in/out cap) | L205 (U7 sw/boot) | 1.235 |
| hot-loop exception | c | 1.50 | C275  | C290 (U25 in/out cap) | 0.650 |
| hot-loop exception | c | 1.50 | C287 (U6 sw/boot) | L204 (U6 sw/boot) | 0.355 |
| hot-loop exception | c | 1.50 | C292 (U25 in/out cap) | C275  | 0.760 |
| hot-loop exception | c | 1.50 | C298 (U7 sw/boot) | L205 (U7 sw/boot) | 0.736 |
| hot-loop exception | c | 1.50 | L1 (U4 sw/boot) | C101 (U4 in/out cap) | 1.380 |
| hot-loop exception | c | 1.50 | L200 (U25 sw/boot) | C267 (U25 sw/boot) | 0.815 |
| hot-loop exception | c | 1.50 | L200 (U25 sw/boot) | R252 (U25 sw/boot) | 0.555 |
| hot-loop exception | c | 1.50 | L200 (U25 sw/boot) | C260 (U25 in/out cap) | 0.625 |
| hot-loop exception | c | 1.50 | L201 (U6 sw/boot) | C271 (U6 in/out cap) | 0.124 **< 0.2** |
| hot-loop exception | c | 1.50 | L202 (U6 sw/boot) | C285 (U6 sw/boot) | 1.405 |
| hot-loop exception | c | 1.50 | L203 (U6 sw/boot) | C272 (U6 in/out cap) | 0.264 |
| hot-loop exception | c | 1.50 | L203 (U6 sw/boot) | C278 (U6 in/out cap) | 0.724 |
| hot-loop exception | c | 1.50 | L203 (U6 sw/boot) | C287 (U6 sw/boot) | 1.174 |
| hot-loop exception | c | 1.50 | L206 (U7 sw/boot) | C300 (U7 sw/boot) | 0.355 |
| movable, no legal move | a | 0.25 | C120  | U5  | 0.165 |
| movable, no legal move | a | 0.25 | C171  | U2  | 0.196 |
| movable, no legal move | a | 0.40 | C172  | Y170  | 0.276 |
| movable, no legal move | a | 0.25 | C172  | U2  | 0.186 |
| movable, no legal move | a | 0.40 | C173  | Y170  | 0.304 |
| movable, no legal move | a | 0.25 | C173  | U2  | 0.156 |
| movable, no legal move | a | 0.40 | C178  | Y170  | 0.354 |
| movable, no legal move | a | 0.40 | C182  | C183  | 0.340 |
| movable, no legal move | a | 0.25 | C182  | U11  | 0.170 |
| movable, no legal move | a | 0.40 | C190 (U15 in/out cap) | R151  | 0.100 |
| movable, no legal move | a | 0.40 | C190 (U15 in/out cap) | R150  | 0.170 |
| movable, no legal move | a | 0.40 | C191 (U15 in/out cap) | C193  | 0.390 |
| movable, no legal move | a | 0.25 | C192  | U1  | 0.170 |
| movable, no legal move | a | 0.40 | C193  | R151  | 0.380 |
| movable, no legal move | a | 0.25 | C193  | U1  | 0.170 |
| movable, no legal move | a | 0.40 | C203  | C200  | 0.390 |
| movable, no legal move | a | 0.40 | C206  | C207  | 0.390 |
| movable, no legal move | a | 0.40 | C206  | C209  | 0.390 |
| movable, no legal move | a | 0.25 | C215  | U24  | 0.138 |
| movable, no legal move | a | 0.40 | C219  | C213  | 0.360 |
| movable, no legal move | a | 0.40 | C226  | C213  | 0.190 |
| movable, no legal move | a | 0.40 | C246  | R224  | 0.370 |
| movable, no legal move | a | 0.40 | C246  | C234  | 0.380 |
| movable, no legal move | a | 0.40 | C269  | R251  | 0.180 |
| movable, no legal move | a | 0.25 | C316  | U19  | 0.150 |
| movable, no legal move | a | 0.40 | D201  | C246  | 0.325 |
| movable, no legal move | a | 0.40 | H2  | R209  | 0.399 |
| movable, no legal move | a | 0.40 | R140  | C142 (U14 in/out cap) | 0.140 |
| movable, no legal move | a | 0.25 | R151  | R150  | 0.160 |
| movable, no legal move | a | 0.40 | R152  | L3 (U15 sw/boot) | 0.180 |
| movable, no legal move | a | 0.40 | R200  | R203  | 0.370 |
| movable, no legal move | a | 0.40 | R201  | R200  | 0.370 |
| movable, no legal move | a | 0.40 | R224  | C204  | 0.380 |
| movable, no legal move | a | 0.40 | R236  | C243  | 0.210 |
| movable, no legal move | a | 0.25 | R250  | R251  | 0.220 |
| movable, no legal move | a | 0.40 | R253  | R254  | 0.220 |
| movable, no legal move | a | 0.25 | R256  | U25  | 0.105 |
| movable, no legal move | a | 0.40 | R256  | C270 (U25 in/out cap) | 0.250 |
| movable, no legal move | a | 0.40 | R256  | C261 (U25 in/out cap) | 0.110 |
| movable, no legal move | a | 0.40 | R256  | C277 (U25 in/out cap) | 0.140 |
| movable, no legal move | a | 0.25 | U10  | C243  | 0.000 |
| movable, no legal move | a | 0.25 | U11  | C183  | 0.170 |
| movable, no legal move | a | 0.25 | U2  | C170  | 0.196 |
| movable, no legal move | a | 0.25 | U22  | C222  | 0.138 |
| movable, no legal move | a | 0.40 | Y200  | C226  | 0.350 |
| movable, no legal move | a | 0.40 | Y200  | C215  | 0.320 |
| movable, no legal move | b | 1.50 | U10  | C236  | 1.480 |
| movable, no legal move | b | 1.50 | U15  | C192  | 1.465 |
| movable, no legal move | b | 1.50 | U15  | C193  | 1.465 |
| movable, no legal move | c | 1.50 | C246  | J3  | 0.625 |
| movable, no legal move | c | 1.50 | C262  | L200 (U25 sw/boot) | 0.185 |
| movable, no legal move | c | 1.50 | C302  | L201 (U6 sw/boot) | 0.880 |
| movable, no legal move | c | 1.50 | C304  | L203 (U6 sw/boot) | 1.030 |
| movable, no legal move | c | 1.50 | C304  | L204 (U6 sw/boot) | 1.445 |
| movable, no legal move | c | 1.50 | L201 (U6 sw/boot) | R262  | 0.784 |
| movable, no legal move | c | 1.50 | L202 (U6 sw/boot) | C302  | 0.695 |
| movable, no legal move | c | 1.50 | L202 (U6 sw/boot) | C303  | 0.755 |
| movable, no legal move | c | 1.50 | R242  | J3  | 1.295 |
