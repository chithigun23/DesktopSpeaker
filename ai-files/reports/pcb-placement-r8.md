# PCB placement R8: wire-length pass (2026-11-01)

Stage PL of the routing restart. Input: project board `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` (commit 2858f93, R6q routing), copied to `ai-files/pcb/work-r8/R8-0.*`. Output: `ai-files/pcb/work-r8/R8-placement.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru` unchanged project rules). Nothing in `DesktopSpeaker-kicad/` or the schematics was edited. No net, value, footprint or side changes. Headless only (KiCad 10.0.7 AppImage `kicad-cli` and `python3.11`).

Files: poses `work-r8/r8-poses.json`; strip/move log `work-r8/r8-apply-report.json`; scripts `work-r8/scripts/` (`dump.py` board to JSON, `run_u3c.py` placer, `apply.py` move + copper strip + silk + refill, `final_metrics.py` gates, `crop.sh` renders); evidence `work-r8/evidence/` (metrics JSON, DRC and parity JSON before/after, renders `r8-mcu.png`, `r8-old.png`, `r8-full.png`).

## Summary
- **One cluster moved: the MCU U3 with its decoupling, NRST, SWCLK pull-down, two pull-ups/downs, the Tag-Connect J7 and six bus test points (14 parts).** U3 went from (186.0, 88.3) to (128.0, 76.5) at 90 degrees, into the empty area between the 3V AO, PD and ADC tiles.
- Score (sum over each IC of octilinear distances from its own pins to every foreign pad on its signal nets; rails and GND excluded): **ICs 12,075 -> 10,679 (-11.6 %)**; with the J4/J6/J7/J8 headers 12,853 -> 11,791 (-8.3 %). U3 alone 4,918 -> 4,010 (-18.5 %), which equals its unconstrained optimum on the baseline board (4,014 at (153, 82), occupied by the ADC).
- Signal-net octilinear MST total 4,937 -> 4,434 mm (-10.2 %); all nets 6,859 -> 6,332 mm. Nets with MST > 100 mm: 20 -> 14 (signal nets 14 -> 8; the remaining 8 are bounded by fixed parts, see the net section).
- Gates: courtyard overlaps 0; DRC with the project rules, all severities: **0 violations** (clearance, courtyard, edge, hole, silk all 0), 294 unconnected items (expected: signal copper stripped); schematic parity identical to the baseline board (243 pre-existing warnings, 0 new); pad-net comparison 0 differences; decoupling: no IC worse; U3 escape corridors clear on all four sides; analog-to-switch-node minimum 16.5 mm (unchanged).
- Hand-assembly gates (coordinator message): all moved parts meet the 1.0 / 0.5 / 2 / 3 mm spacing rules; U3 has 3.41 mm to the nearest unrelated part (2.38 before). Board-wide, 317 parts still miss the 1.0 mm courtyard rule (330 before): this is a whole-board density finding, not fixable by a few moves (question 3).

## Fixed parts and evidence
| Part(s) | Reason / evidence |
|---|---|
| J1, J2, J3, J5, J9, J10, J11, SW100, SW101, SW102, U1, U6, U7, all H*/HA*, board outline | User decision 2026-11-01 (brief) |
| J1, J2, J3, SW100, SW101 | Rear-lid cutouts are cut to these positions (`cad/README.md` v11/v11.2, `interference.md` lid table) |
| J11 | Woofer leads run from J11 to the grommet at CAD X 40 (`cad/README.md` v11 "Woofer leads") |
| J5 | Pack harness route J5 -> right side pocket (`cad/README.md` v11 "Battery") |
| SW102 + knob dish | Dish axis derived from the SW102 shaft (board 116.1, 100.9); dish 36 mm + 3 mm wall, floor z 82.09 = **13.5 mm above the board top** inside a 21 mm radius. Used as a height limit: the moved parts under it are at most about 2 mm tall (LQFP, 0402/0805, Keystone 5015 SMD loops) |
| U4 (BQ25792), U25 (TPS61088) + L200 + C275, U14/U15 (TPS63802), U11 (TPS25730D) | Vendor hot loops, kept exactly (brief). C275 is 20.7 mm below the top wall (`cad-v11-print-ready.md`), no position constraint found |
| J4 (PD service header) | **Unclear**: sits at the rear edge beside J1 but has no lid cutout; kept and asked (question 2) |
| J6 (SWD 1x4 header) | No CAD constraint found. Kept because no legal spot exists near the new MCU (see rejected alternatives); asked (question 1) |
| J7, test points, J8 | No CAD constraint found (`cad/*.md`, `check_cad.py` only model J1/J2/J3/SW100/SW101 cutouts, the dish, battery, harness and inserts). J7 and six TPs moved; J8 not moved (no gain) |
| H6/H*/HA* screw bosses and lid screws | Lid screws enter the insert rim below the board (z < 57) and do not touch the board; the PCB screws are the fixed holes |

## Scores per IC and header (before / after)
Score = sum over the part's signal nets (Default, I2C, AUDIO, I2S_CLK, USB) of the octilinear distance (max(dx,dy) + 0.414 min(dx,dy)) from its nearest own pin on the net to every foreign pad on the net. The "unconstrained optimum" is a 2 mm grid search over the whole board ignoring collisions, holding all other parts fixed.

| Part | Score before | Score after | Change | Unconstrained optimum (x, y, rot) and its score, baseline board | Status |
|---|---|---|---|---|---|
| J4 | 316.6 | 283.8 | -32.8 | (139, 60, -90) 146.2 | kept (question) |
| J6 | 158.1 | 420.4 | +262.3 | (185, 90, -90) 85.8 | kept (no legal spot) |
| J7 | 149.3 | 254.1 | +104.8 | (179, 88, 0) 94.4 | moved |
| J8 | 153.5 | 153.5 | +0.0 | (103, 28, 90) 41.5 | kept |
| U1 | 138.2 | 138.2 | +0.0 | (101, 38, 90) 131.3 | fixed (antenna edge) |
| U2 | 53.2 | 53.2 | +0.0 | (155, 56, 0) 43.4 | not moved |
| U3 | 4918.0 | 4010.2 | -907.8 | (153, 82, 0) 4014.2 | moved |
| U4 | 1180.0 | 1151.7 | -28.3 | (171, 96, -90) 973.0 | hot loop kept |
| U5 | 44.2 | 44.2 | +0.0 | (97, 74, -90) 18.8 | not moved |
| U6 | 1549.8 | 1330.6 | -219.2 | (153, 96, 90) 759.0 | fixed (beside J9/J10) |
| U7 | 1451.0 | 1645.1 | +194.1 | (145, 96, 90) 802.4 | fixed (beside J11) |
| U8 | 60.6 | 81.6 | +21.0 | (175, 66, 0) 56.7 | not moved |
| U9 | 54.8 | 101.7 | +46.9 | (184.3, 65.3, 0) 54.8 | not moved |
| U10 | 271.1 | 397.1 | +126.0 | (189, 62, 0) 255.1 | not moved |
| U11 | 483.6 | 331.1 | -152.5 | (139, 54, 0) 480.9 | hot loop kept |
| U12 | 42.3 | 42.3 | +0.0 | (95, 76, -90) 19.8 | not moved |
| U13 | 297.1 | 196.3 | -100.8 | (109, 82, 180) 266.9 | not moved |
| U14 | 103.1 | 59.9 | -43.2 | (93, 98, 0) 101.0 | hot loop kept |
| U15 | 204.5 | 98.7 | -105.8 | (119, 36, -90) 201.9 | hot loop kept |
| U16 | 293.8 | 181.6 | -112.2 | (107, 80, 180) 266.9 | not moved |
| U17 | 167.4 | 114.7 | -52.7 | (103, 78, 90) 122.8 | not moved |
| U19 | 0.0 | 0.0 | +0.0 | (149, 37.5, 0) 0.0 | not moved |
| U20 | 63.1 | 63.1 | +0.0 | (111, 76, 0) 41.8 | not moved |
| U21 | 17.2 | 17.2 | +0.0 | (107, 80, 0) 2.2 | not moved |
| U22 | 0.0 | 0.0 | +0.0 | (172.8, 51.8, 0) 0.0 | not moved |
| U23 | 40.9 | 65.1 | +24.2 | (187, 56, 0) 37.9 | not moved |
| U24 | 543.6 | 447.7 | -95.9 | (153, 86, -90) 534.0 | not moved |
| U25 | 97.8 | 108.1 | +10.3 | (155, 146, -90) 91.2 | hot loop kept |
| **Total (U only)** | 12075.3 | 10679.4 | -1395.9 | | |
| **Total (U + J4/J6/J7/J8)** | 12852.8 | 11791.2 | -1061.6 | | |

## Move log
| Ref | Old (x, y, rot) | New (x, y, rot) | Reason |
|---|---|---|---|
| U3 | 186.015, 88.305, 0 | 128.000, 76.500, 90 | Wire-length optimum within the free area under the 3 mm hand-rework ring (search: 0.5 mm grid, 4 rotations, all fixed courtyards with the coordinator's gap rules). Rot 90 chosen over rot 0 (score 3,693 vs 3,623 at the same spot) because 11 instead of 14 signal pins face away from their far ends, SWD pins face the free area for J7, and the PDCTRL/BT/CTRL/AUD buses leave toward U11 (up), U1/U13/U16 (left) and U24 (right) |
| C160 100 nF | 178.200, 87.650, -90 | 128.000, 84.650, 0 | VDD/VSS pins 8/9 (bottom row): 3V_AO pad under pin 8, GND pad under pin 9, outside the 1 mm escape band |
| C162 100 nF (NRST) | 177.540, 90.450, -90 | 131.200, 84.650, 0 | NRST pin 12 |
| C161 4.7 uF | 176.940, 84.250, 90 | 124.900, 86.100, -90 | Bulk beside C160, VDD side |
| R106 10k (CHG_INT pull-up) | 177.540, 92.900, 90 | 122.400, 84.500, 90 | Pin 5 |
| R160 100k (SWCLK/BOOT0 pull-down) | 192.290, 80.150, 90 | 120.700, 70.300, 180 | Pin 46 / J7 SWCLK |
| R259 100k (AMP_PDN pull-down) | 184.770, 96.380, -90 | 136.000, 83.000, -90 | Pin 23, toward both amplifier branches |
| J7 Tag-Connect TC2030 | 170.765, 95.305, 0 | 121.750, 64.500, 180 | SWD pins 45/46 face it; NPTH legs clear of In2 power tracks |
| TP19 NRST | 180.340, 97.055, 0 | 133.000, 87.500, 0 | NRST in line below C162 |
| TP21 BT_UART_TX | 194.760, 83.480, 90 | 115.500, 68.000, 90 | UART TX path toward U1 |
| TP15 CTRL_SDA | 183.765, 77.635, 0 | 138.000, 97.000, 90 | CTRL bus path toward U4 (down) |
| TP16 CTRL_SCL | 189.265, 79.135, 0 | 133.750, 96.250, 90 | same |
| TP17 AUD_SDA | 194.765, 93.985, 90 | 137.000, 106.250, 0 | AUD bus path toward U6/U7 (down), >= 5 mm from switch pads (L1 9.2 mm) |
| TP18 AUD_SCL | 194.765, 88.985, 90 | 134.250, 102.000, 0 | same |
| NECK_U3 rule area | around old U3 | translated/rotated with U3 | Rule area follows its IC (brief) |

Silkscreen edits (needed for DRC 0 and correct documentation; board graphics only): the TP net-name labels of the moved TPs moved with them (centre justified); the ADC tile's left edge moved from x 131.45 to x 137.0 (y 69.1-93.3) so the MCU sits in its own tile; the empty strip x 87.25-126.29, y 55.9-66.9 plus the free area form the new tile titled "MCU"; the old tile keeps J6 and TP25 and is retitled "SWD Header"; the TP26 "GND" label moved above TP26 (it crossed the new tile edge). A full silk pass is still due after routing.

Renders (top, F.Cu + silk + courtyards): `evidence/r8-mcu.png` (new MCU cluster), `evidence/r8-old.png` (old MCU tile, now J6 + TP25), `evidence/r8-full.png`. Looked at once each: the cluster sits inside its tile, U3 corridors are open, labels are readable and do not overlap; the old tile is nearly empty.

## Copper handled for the restart
- Removed: every track and via of the signal classes (Default, I2C, AUDIO, I2S_CLK, USB; all <= 0.25 mm): 1,474 tracks, 335 vias. Plus the copper attached to moved pads (flood over tracks/vias from each moved pad, stopping at pads of unmoved parts).
- **Power nets whose copper was touched: `/3V_AO` (57 of 90 tracks, 158.6 mm; 7 of 11 vias) and `GND` (8 tracks, 8.8 mm; 7 vias, all attached to moved caps/TPs).** No other power net, no power pour, no power via of an unmoved part was touched.
- Kept: all zones (refilled after the moves), 288 GND tracks, 265 GND vias, all POWER_HI/PVDD/SWITCH/BOOT/SPK_OUT/PWR_5V/PWR_LOCAL copper, the remaining PWR_3V copper.
- 1,179 teardrop areas that no longer touched a same-net track or via were deleted (regenerate after routing).

## Gates
| Gate | Result |
|---|---|
| Courtyard overlaps | 0 (own check and DRC) |
| DRC, project rules, `--severity-all` (`evidence/drc-R8-placement.json`) | 0 violations: clearance 0, courtyard 0, edge 0, hole 0, shorting 0, silk 0. 294 unconnected items (signal copper stripped; expected). Baseline R8-0: 0 / 0 |
| Schematic parity (kicad-cli on a scratch copy of the schematics next to the board) | 243 items, identical item by item to the baseline board (199 field mismatches, 29 footprint/symbol attribute mismatches, 15 net-name escaping/pin-stack warnings, all pre-existing). 0 new |
| Pad nets / values / footprints / sides vs baseline | 0 / 0 / 0 / 0 differences |
| Rotations | all parts at multiples of 90 degrees |
| Decoupling (cap pad edge to nearest same-net IC pad), all 24 ICs | No IC worse by more than 0.5 mm; only U3 changed: 3V_AO C160 1.06 -> 1.39 mm (+0.33, now outside the 1 mm escape band), NRST C162 1.72 -> 1.50 mm |
| Escape corridor (1 mm in front of every pin row) | U3: 0 foreign and 0 own pads in all four bands (before: R259 in the bottom band). Other fine-pitch ICs unchanged (table below) |
| Analog (AUDIO-class pads) to switch-node pads | minimum 16.5 mm (R204), unchanged; no analog part within 5 mm of a switch node |
| Analog to I2S/crystal clock pads | unchanged; 10 pre-existing parts within 5 mm, all at their own IC's crystal or clock pins (C186 0.96 mm at U2 XTI/XO, U24 own pins, C212, R175, U2, C187, C210, C207, C208, C206) |
| Moved parts to switch nodes | >= 9.2 mm (TP17 to L1); U3 27.6 mm |
| Retained vias within 0.5 mm of a moved part's SMD pad | 0 |

### Hand-assembly gates (coordinator message, 2026-11-01)
Rules used: courtyard gap >= 1.0 mm between neighbours; 0.5 mm for 0402-0402 on a shared net; >= 3 mm between a QFN/LQFP/fine-pitch IC (U2-U11, U14, U15, U19, U20, U24, U25, Q103) and any part that shares no non-GND net with it (its own decoupling/support parts use the 1.0 mm rule, otherwise the HF-cap-within-3 mm rule cannot be met); >= 2 mm between a tall part (L*, C275, J*, SW*) and a small passive or fine-pitch IC; mounting holes use 1.0 mm.
| Gate | Before | After |
|---|---|---|
| 1. SMD parts on the bottom | 0 (only LOGO1 graphic) | 0 |
| 2. Parts with any spacing violation (board-wide) | 330 of 359 | 317 |
| 2. Violating pairs by rule: 1.0 / 0.5 / 2.0 tall / 3.0 rework | 333 / 40 / 57 / 13 | 321 / 40 / 57 / 12 |
| 2. Violating pairs involving a moved part | 13 (U3 in 7 of them) | **0** |
| 2. U3 nearest unrelated part (rework ring) | 2.38 mm (TP25) | 3.41 mm (TP6) |
| 3. Orientation | same-type ICs consistent (U6/U7 180, U8/U9, U13/U16/U17, U14/U15 0); mixed pre-existing: D200 180 vs D201 0 (PESD5V0S2BT), Q102 -90 vs Q100/Q101/Q104 0 | unchanged (not moved). U3 is the only LQFP; its pin-1 chamfer and silk mark stay 1.0 mm clear of C160/C161 |
| 4. Via edge < 0.5 mm from an SMD pad (incl. touching) | 681 | 499 (all remaining are power/GND vias of unmoved parts) |
| 4. Via centre in a non-thermal SMD pad | 3 (C215 U24-AVDD, R10 U11-ADC4, R224) | 1 (C215; its PWR_LOCAL via was kept because U24 did not move; dogbone it in routing) |
| 5. Heat-sensitive/plastic parts moved | - | none (J7 is a footprint without a part; the TPs are metal loops) |
| 6. Moved TPs to the nearest tall part | - | >= 6.75 mm (none under a tall part); all are top-side SMD loops |
Per-part minimum gaps of the moved parts are in the table below; the per-part values for the whole board are in `evidence/gaps_before.json` and `evidence/final_metrics.json`.

### Moved parts: minimum courtyard gap
| Moved part | Min courtyard gap before (mm, neighbour, required) | After | Rule violations before | After |
|---|---|---|---|---|
| TP17 | 0.71 TP18 (1.0) | 1.56 TP18 (1.0) | 2 | 0 |
| TP18 | 0.71 TP17 (1.0) | 1.53 TP15 (1.0) | 2 | 0 |
| TP21 | 0.67 R160 (1.0) | 1.16 J7 (1.0) | 2 | 0 |
| TP16 | 0.41 R160 (1.0) | 1.56 TP15 (1.0) | 1 | 0 |
| C161 | 0.44 C160 (1.0) | 1.03 U3 (1.0) | 1 | 0 |
| J7 | 1.38 TP8 (1.0) | 1.06 U3 (1.0) | 0 | 0 |
| R106 | 0.26 C162 (1.0) | 1.01 U3 (1.0) | 1 | 0 |
| U3 | 0.28 R259 (1.0) | 1.00 C162 (1.0) | 7 | 0 |
| C162 | 0.26 R106 (1.0) | 1.00 U3 (1.0) | 2 | 0 |
| TP19 | 0.71 U3 (1.0) | 1.05 C162 (1.0) | 1 | 0 |
| TP15 | 1.11 TP25 (1.0) | 1.53 TP18 (1.0) | 0 | 0 |
| R259 | 0.28 U3 (1.0) | 1.51 U3 (1.0) | 1 | 0 |
| R160 | 0.41 TP16 (1.0) | 1.07 U3 (1.0) | 2 | 0 |
| C160 | 0.44 C161 (1.0) | 1.00 U3 (1.0) | 3 | 0 |

### Escape corridors of the fine-pitch ICs
"Own support" = a part that shares a non-GND net with the IC (decoupling, bootstrap, filter), placed by the vendor layout order.

| Fine-pitch IC | Side: pins, foreign pads in the 1 mm band (before -> after) | Own support parts in band (after) |
|---|---|---|
| U2 | (no pin rows detected) | - |
| U3 | L 16: 0 -> 0; R 16: 0 -> 0; T 16: 0 -> 0; B 16: 0 -> 0 | - |
| U4 | L 8: 0 -> 0; R 9: 0 -> 0; T 5: 0 -> 0; B 7: 0 -> 0 | L: C103.1,C102.1; B: C313.1,C313.2 |
| U5 | B 4: 0 -> 0 | B: C120.1,C120.2 |
| U6 | L 8: 0 -> 0; R 8: 0 -> 0; T 8: 0 -> 0; B 8: 0 -> 0 | - |
| U7 | L 8: 0 -> 0; R 8: 0 -> 0; T 8: 0 -> 0; B 8: 0 -> 0 | - |
| U8 | T 3: 0 -> 0; B 5: 0 -> 0 | B: R228.2 |
| U9 | T 3: 0 -> 0; B 5: 0 -> 0 | - |
| U10 | L 4: 0 -> 0; R 4: 0 -> 0; T 4: 0 -> 0; B 4: 0 -> 0 | R: C243.1 |
| U11 | L 6: 0 -> 0; T 8: 0 -> 0; B 13: 0 -> 0 | L: C181.1; T: C182.1,C183.1 |
| U14 | L 4: 0 -> 0; R 4: 0 -> 0 | - |
| U15 | L 4: 0 -> 0; R 4: 0 -> 0 | - |
| U19 | L 3: 0 -> 0; R 3: 0 -> 0 | L: C5.1; R: C316.1 |
| U20 | L 3: 0 -> 0; R 3: 0 -> 0 | L: C124.1,C124.2; R: C125.1,C125.2 |
| U24 | T 13: 0 -> 0; B 15: 0 -> 0 | T: C215.1,C212.1,C213.1; B: R206.1,C210.1,C210.2,R207.1 |
| U25 | L 8: 0 -> 0; R 8: 0 -> 0 | L: R252.1,R252.2; R: C314.1,C314.2 |


## Decoupling distances, all ICs (before / after)
| IC | Rail / local net | Nearest cap before (mm, ref) | After (mm, ref) |
|---|---|---|---|
| U1 | 3V8_BT | 0.57 C191 | 0.57 C191 |
| U1 | Net-(U1-SYS_PWR) | 1.82 C193 | 1.82 C193 |
| U1 | Net-(U1-VDD_IO) | 0.57 C192 | 0.57 C192 |
| U2 | Net-(U2-VBUS) | 0.59 C170 | 0.59 C170 |
| U2 | Net-(U2-VCCCI) | 2.08 C175 | 2.08 C175 |
| U2 | Net-(U2-VCCP1I) | 2.40 C174 | 2.40 C174 |
| U2 | Net-(U2-VCCP2I) | 2.36 C173 | 2.36 C173 |
| U2 | Net-(U2-VCCXI) | 0.61 C172 | 0.61 C172 |
| U2 | Net-(U2-VCOM) | 1.19 C176 | 1.19 C176 |
| U3 | 3V_AO | 1.06 C160 | 1.39 C160 |
| U4 | BAT_INT | 2.73 C106 | 2.73 C106 |
| U4 | PMID | 0.77 C312 | 0.77 C312 |
| U4 | REGN | 0.94 C102 | 0.94 C102 |
| U4 | VBUS_PD | 0.71 C313 | 0.71 C313 |
| U4 | SYS_RAW | 0.77 C311 | 0.77 C311 |
| U5 | BAT_PACK | 0.56 C120 | 0.56 C120 |
| U6 | 3V3_AUDIO | 1.29 C281 | 1.29 C281 |
| U6 | PVDD_AMP | 1.34 C276 | 1.34 C276 |
| U6 | Net-(U6-AVDD) | 1.18 C284 | 1.18 C284 |
| U6 | Net-(U6-GVDD) | 1.18 C283 | 1.18 C283 |
| U6 | Net-(U6-VR_DIG) | 2.00 C282 | 2.00 C282 |
| U7 | 3V3_AUDIO | 1.29 C294 | 1.29 C294 |
| U7 | PVDD_AMP | 1.34 C289 | 1.34 C289 |
| U7 | Net-(U7-AVDD) | 1.18 C297 | 1.18 C297 |
| U7 | Net-(U7-GVDD) | 1.18 C296 | 1.18 C296 |
| U7 | Net-(U7-VR_DIG) | 2.01 C295 | 2.01 C295 |
| U8 | 3V3_AUDIO | 2.84 C238 | 2.84 C238 |
| U9 | 3V3_AUDIO | 1.61 C237 | 1.61 C237 |
| U10 | 3V3_AUDIO | 1.89 C241 | 1.89 C241 |
| U10 | Net-(U10-HPVDD) | 0.38 C243 | 0.38 C243 |
| U10 | Net-(U10-HPVSS) | 0.73 C244 | 0.73 C244 |
| U11 | VBUS_PD | 1.66 C315 | 1.66 C315 |
| U11 | LDO_1V5 | 0.80 C181 | 0.80 C181 |
| U11 | LDO_3V3 | 1.79 C6 | 1.79 C6 |
| U11 | USB_VBUS | 0.92 C2 | 0.92 C2 |
| U12 | 3V_AO | 0.84 C123 | 0.84 C123 |
| U13 | 3V_AO | 0.64 C130 | 0.64 C130 |
| U14 | 5V_LOGIC | 2.05 C141 | 2.05 C141 |
| U14 | SYS_RAW | 1.57 C140 | 1.57 C140 |
| U15 | 3V8_BT | 1.14 C152 | 1.14 C152 |
| U15 | SYS_RAW | 1.25 C150 | 1.25 C150 |
| U16 | 3V_AO | 4.77 C123 | 4.77 C123 |
| U17 | 3V_AO | 0.62 C131 | 0.62 C131 |
| U19 | USB_AUX_5V | 0.78 C5 | 0.78 C5 |
| U19 | USB_VBUS | 0.64 C316 | 0.64 C316 |
| U20 | USB_AUX_5V | 0.67 C124 | 0.67 C124 |
| U20 | SYS_RAW | 0.66 C125 | 0.66 C125 |
| U21 | BAT_PACK | 0.56 C126 | 0.56 C126 |
| U22 | 3V3_AUDIO | 0.53 C222 | 0.53 C222 |
| U22 | 5V_LOGIC | 0.86 C224 | 0.86 C224 |
| U23 | 5V_CODEC | 0.84 C225 | 0.84 C225 |
| U23 | 5V_LOGIC | 12.09 C221 | 12.09 C221 |
| U24 | 3V3_AUDIO | 1.44 C217 | 1.44 C217 |
| U24 | Net-(U24-AVDD) | 0.54 C215 | 0.54 C215 |
| U24 | Net-(U24-LDO) | 1.14 C213 | 1.14 C213 |
| U24 | Net-(U24-VREF) | 0.55 C212 | 0.55 C212 |
| U25 | PVDD_AMP | 0.63 C314 | 0.63 C314 |
| U25 | SYS_RAW | 1.47 C260 | 1.47 C260 |
| U25 | Net-(U25-VCC) | 1.07 C265 | 1.07 C265 |

## Net lengths: 30 longest nets before, with the after value
| # | Net (30 longest before) | Class | Octilinear MST before mm | After mm |
|---|---|---|---|---|
| 1 | /3V3_AUDIO | PWR_3V | 242.8 | 242.8 |
| 2 | /SYS_RAW | POWER_HI | 215.6 | 215.6 |
| 3 | /3V_AO | PWR_3V | 177.1 | 152.6 |
| 4 | /Amplifiers/PVDD_AMP | PVDD | 157.4 | 157.4 |
| 5 | /AUD_SDA | I2C | 152.0 | 140.4 |
| 6 | /AMP_FAULT_N | Default | 142.3 | 164.2 |
| 7 | /Fuel_Gauge_Power/BAT_PACK | POWER_HI | 141.2 | 141.2 |
| 8 | /AUD_SCL | I2C | 141.1 | 138.8 |
| 9 | /CTRL_SDA | I2C | 136.4 | 85.8 |
| 10 | /CTRL_SCL | I2C | 132.2 | 78.0 |
| 11 | /5V_LOGIC | PWR_5V | 123.4 | 123.4 |
| 12 | /PDCTRL_SCL | I2C | 114.7 | 58.8 |
| 13 | /I2S_LRCK | I2S_CLK | 113.9 | 113.9 |
| 14 | /I2S_BCK | I2S_CLK | 113.4 | 113.4 |
| 15 | /BT_TX_IND | Default | 113.3 | 66.5 |
| 16 | /I2S_SDATA | I2S_CLK | 113.2 | 113.2 |
| 17 | Net-(U4-QON) | Default | 110.7 | 110.7 |
| 18 | /PDCTRL_SDA | I2C | 110.7 | 56.0 |
| 19 | /BT_RST_N | Default | 109.4 | 62.1 |
| 20 | /BT_UART_TX | Default | 100.1 | 34.8 |
| 21 | /BT_PWR_EN | Default | 100.0 | 45.1 |
| 22 | /BT_AUDIO_L | AUDIO | 99.0 | 99.0 |
| 23 | /BT_UART_RX | Default | 98.9 | 57.9 |
| 24 | /GAUGE_ALRT_N | Default | 98.6 | 44.5 |
| 25 | /BT_AUDIO_R | AUDIO | 97.3 | 97.3 |
| 26 | /AMP_PDN | Default | 96.7 | 114.8 |
| 27 | /BT_FORCE_PWM | Default | 95.1 | 46.5 |
| 28 | /5V_LOGIC_EN | Default | 94.6 | 51.4 |
| 29 | /BT_MFB | Default | 93.2 | 49.2 |
| 30 | /MCU/ENC_B | Default | 92.5 | 39.6 |

## Net lengths: 30 longest nets after
| # | Net (30 longest after) | Class | Before mm | After mm |
|---|---|---|---|---|
| 1 | /3V3_AUDIO | PWR_3V | 242.8 | 242.8 |
| 2 | /SYS_RAW | POWER_HI | 215.6 | 215.6 |
| 3 | /AMP_FAULT_N | Default | 142.3 | 164.2 |
| 4 | /Amplifiers/PVDD_AMP | PVDD | 157.4 | 157.4 |
| 5 | /3V_AO | PWR_3V | 177.1 | 152.6 |
| 6 | /Fuel_Gauge_Power/BAT_PACK | POWER_HI | 141.2 | 141.2 |
| 7 | /AUD_SDA | I2C | 152.0 | 140.4 |
| 8 | /AUD_SCL | I2C | 141.1 | 138.8 |
| 9 | /5V_LOGIC | PWR_5V | 123.4 | 123.4 |
| 10 | /AMP_PDN | Default | 96.7 | 114.8 |
| 11 | /I2S_LRCK | I2S_CLK | 113.9 | 113.9 |
| 12 | /I2S_BCK | I2S_CLK | 113.4 | 113.4 |
| 13 | /I2S_SDATA | I2S_CLK | 113.2 | 113.2 |
| 14 | Net-(U4-QON) | Default | 110.7 | 110.7 |
| 15 | /BT_AUDIO_L | AUDIO | 99.0 | 99.0 |
| 16 | /BT_AUDIO_R | AUDIO | 97.3 | 97.3 |
| 17 | /CTRL_SDA | I2C | 136.4 | 85.8 |
| 18 | /CTRL_SCL | I2C | 132.2 | 78.0 |
| 19 | /HP_EN | Default | 26.0 | 77.7 |
| 20 | /Battery_Charger/VBUS_PD | POWER_HI | 76.9 | 76.9 |
| 21 | /AMP_BOOST_EN | Default | 67.7 | 76.1 |
| 22 | /Fuel_Gauge_Power/USB_AUX_5V | PWR_5V | 75.2 | 75.2 |
| 23 | /5V_CODEC | PWR_5V | 73.0 | 73.0 |
| 24 | /AUX_DET | Default | 58.4 | 71.9 |
| 25 | /HP_G0 | Default | 31.8 | 70.7 |
| 26 | /HP_G1 | Default | 32.3 | 68.9 |
| 27 | /CHG_SYS_ENABLE | Default | 23.4 | 68.6 |
| 28 | /BT_TX_IND | Default | 113.3 | 66.5 |
| 29 | /HP_SEL_B | Default | 20.0 | 65.6 |
| 30 | /USB_PD/LDO_3V3 | PWR_3V | 65.0 | 65.0 |

## Nets over 100 mm after placement (signal classes)
| Net | MST mm | Reason it stays |
|---|---|---|
| /AMP_FAULT_N | 164.2 (142.3 before) | Shared fault line of U6 and U7, which are fixed 83 mm apart beside their connectors; TP20 sits in the front-edge probe group with TP10/TP24. Rises because U3 moved left (away from U7) |
| /AUD_SDA, /AUD_SCL | 140.4, 138.8 (152.0, 141.1) | Bus spans U6, U7 (fixed, 83 mm apart), U24 and U3 |
| /AMP_PDN | 114.8 (96.7) | U6 and U7 enable branches (R257/R258 at the amplifiers) |
| /I2S_BCK, /I2S_LRCK, /I2S_SDATA | 113.4, 113.9, 113.2 (unchanged) | ADC U24 to both fixed amplifiers |
| Net-(U4-QON) | 110.7 (unchanged) | U4 (hot loop, kept) to SW100 (rear-edge switch, fixed) |
Fixed by this pass (were > 100 mm): CTRL_SDA 136 -> 86, CTRL_SCL 132 -> 78, PDCTRL_SCL 115 -> 59, PDCTRL_SDA 111 -> 56, BT_TX_IND 113 -> 67, BT_RST_N 109 -> 62, BT_UART_TX 100 -> 35. Power nets over 100 mm (3V3_AUDIO 243, SYS_RAW 216, PVDD_AMP 157, 3V_AO 153, BAT_PACK 141, 5V_LOGIC 123) are rails with many loads; the rail topology belongs to the routing stage (review R6).
SWD after the move: SWDIO/SWCLK/NRST reach J7 within about 10 mm of U3, but J6 stays at (168.3, 80.0), so each SWD net carries a 40-45 mm branch to J6.

## Rejected alternatives
- **U3 at its unconstrained optimum (151.5-153, 82)**: occupied by the ADC U24, its crystal Y200 and input filter (sensitive analog); would mean moving the ADC block. Score gain over the chosen spot only about 100.
- **U3 in the empty area (125-145, 90-108)**: score 3,750-3,990 (worse than 3,693), straddles the I2S trunk from U24 to U6, 7 mm from the charger inductor L1 (SW node), and leaves no room for the test points.
- **U3 at 0 degrees, same spot**: 70 lower score, but 14 pins face away (11 at 90 degrees) and the SWD side would face the ADC tile.
- **Gauge / low-power cluster (U5, U12, U13, U16, U17, U20, U21)**: after the U3 move their pull is small (best unconstrained positions are 2-6 mm shifts inside the same tile, gain 20-50 each); moving them would rip BAT_PACK, SYS_RAW, USB_AUX_5V and 3V_AO power copper. U13/U16/U17 already improved by 50-112 each from the U3 move. Not moved.
- **J6 with the MCU**: no legal position in the new tile or the free area south of it. Blocked by retained In2 power tracks (SYS_RAW, USB_AUX_5V, 3V3_AUDIO, BAT_PACK cross the free area; a THT pin would short them, which the first trial showed as 4 DRC shorts), the 2 mm tall-part rule and the silk tiles. Kept at its old position (question 1).
- **J4 next to U11 (139, 60)** would save about 140 score: not done (unclear constraint, question 2).
- **TP25 (GND loop) with the MCU**: no room under the rules; the TP26 GND loop is 2.3 mm from TP15 and serves the new cluster. Kept.
- U19, U22: no signal nets (score 0). J8: optimum inside the BM83 body. U2, U10, U14, U15, U23: gains below 40 each, not worth the rip-up.
- U3 corridor vs decoupling: placing C160 closer (1.06 mm, as before) would put it inside the 1 mm escape band; 1.39 mm keeps both rules.

## Open questions for the user
1. **J6 (SWD 1x4 header)**: it could not follow the MCU. Options: (a) keep it where it is (current file: 40-45 mm SWD/NRST branches; SWD at a few MHz tolerates this); (b) let the routing stage move the In2 power tracks (SYS_RAW, USB_AUX_5V) out of the strip at x 96-112, y 57-66 so J6 can sit 15 mm from U3; (c) fit only J7 (Tag-Connect) and leave J6 unplaced/DNP (a BOM decision).
2. **J4 (PD service header)**: is the rear-edge position needed for access? There is no lid cutout for it. If not, J4 near U11 at about (139, 60) shortens PDCTRL by about 35 mm per line.
3. **Hand-assembly spacing board-wide**: 317 parts are still below the 1.0 mm courtyard gap (321 pairs at 1.0, 57 tall-part pairs, 12 rework-ring pairs), mostly 0402 decoupling clusters placed in vendor order. Treat vendor decoupling clusters as an exception (they reflow with the IC), or plan a full re-placement with a larger board?
4. **TP13/TP14 labels**: TP13 has value/label "I2S_LRCK" but is on net /I2S_SDATA; TP14 "I2S_SDATA" is on /I2S_LRCK (pre-existing, also flagged by parity as a value mismatch). Check the schematic.
5. **Silk tiles**: the MCU now has its own tile ("MCU"), the old tile is "SWD Header". Confirm the names before the final silk pass.
