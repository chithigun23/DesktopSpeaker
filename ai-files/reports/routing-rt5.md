# RT-5: footprint fixes, U4 bootstrap/PROG rework, BAT finger (2026-11-02)

Agent "RT-5 blocked areas and footprint fixes". Input `ai-files/pcb/work-route4/RT-4.*`. Work folder `ai-files/pcb/work-route5/` only. Result `ai-files/pcb/work-route5/RT-5.kicad_pcb/.kicad_pro/.kicad_dru`. Nothing in `DesktopSpeaker-kicad/`, earlier work folders, `helpers/route_oct*.py` or `work-oct3/` was edited. All board edits are text edits (`scripts/fpfix.py` for footprints, `scripts/edit.py` for copper/moves, extended with a rotation-aware `fp_move`); zones refilled in a separate pcbnew process with the pristine `.kicad_pro` and the RT-5 rule file beside the board. Not committed; nothing published.

## 1. Result

| gate | RT-4 | RT-5 |
|---|---|---|
| kicad-cli DRC `--severity-all --all-track-errors` (RT-5 rules, library = project library + `lib-proposed/`) | 0 | **0** (no USB items, no lib-footprint warnings) |
| same board, **project** rule file | 0 | 4 hole_clearance, all SW100 peg hole vs own pad (the documented exemption, section 4) |
| DRC unconnected | 108 | **107** (PROG closed; no new opens; per-net counts otherwise identical, `scripts/uncnet.py`) |
| router-scope open connections | 92 | **91** (+16 inherited 3V_AO/GND/LDO_3V3, unchanged) |
| BAT_INT U4-22/23 -> Q103-1..3 (copper_path, 0.05 mm, 6 A, 20 C) | 2.845 mOhm | **2.652 mOhm** (target 2.6: 0.05 short, see 3.2) |
| footprints moved | R102 | SW100, C110, R102, C106, R113, TP2 (all listed, section 5) |
| pad nets of 360 footprints vs RT-4 | | unchanged by (ref, pad number); SW100 gains 2 net-less bracket tabs (pad index order changed, nets identical) |
| rule files | project | `.kicad_pro` = project (aa88e8c9...); `.kicad_dru` = project + one appended exemption (ce43baa1...), `RT-5.rulehash.txt` |
| sentinel (I2S_CLK width >= 5 mm appended on a copy) | | **FIRES** (73 items), `RT-5.sentinel.txt`, `sentinel/` |
| locked copper (RT-4 items untouched) | | 2901 of 2934; 33 removed/changed, all listed in the edit reports, 0 unexpected; SHA-256 `76ff5ca7da42effd4d77352a19685a9fc6fb4d60b6313f068b8c1bc643834389` (`RT-5.gates.json`) |
| new copper exact 0/45/90 (gates4, own text parse) | | **23 segments, 36.8 mm, 0 not exact** |
| pour check (route_oct_pourcheck, touched nets) | | **OK** (foreign unconnected 97 -> 97) |
| parcheck (< 0.4 mm over > 3 mm, touched nets) | | 0 pairs |
| r7 joints < 80 / < 30 deg | 20 / 8 | **19 / 7** (NRST 0-degree joint at U3-12 removed) |
| r7 BM83 F.Cu inside module | GND 2.3, SYS_PWR 2.0 | **unchanged** (0 mm new copper; the pad-56 GND stub/via were moved with the pad, same length) |
| HA8 failing pairs (r8b_ha8, strict tiers) | 124 (R10 baseline 123 + RT-4's R102) | **122**; 0 new, 0 tighter; gone: C106-C110, C106-R102 |
| silkscreen (silk_tile.py + silk_tile_gate.py G1-G6) | | **ALL PASS**; RT-5 = the silk version |

Gate files (work-route5): `RT-5.drc.json`, `RT-5.gates.json`, `RT-5.r7.json` (+ `t/RT-4.r7.json`), `RT-5.par.json`, `RT-5.check.json`, `C1s.silkgate.json`, `RT-5.sentinel.txt`, `RT-5.rulehash.txt`, `t/RT-4.ha8.json`, `t/B1b.ha8.json`, `t/*.cp.json` + `t/map_*.png` (resistance maps).

## 2. Task A: footprint fixes (board only; library patch in `work-route5/footprint-fixes.md`, files in `work-route5/lib-proposed/`)

Each fix was verified against the drawing before editing:
- **J2/J3 PJ-307**: front NPTH pegs local x -5.75 -> -4.75 (HOOYA layout: pegs 1.0 and 3.5 from the body front, pin 1 at 3.1; the footprint's own Cmts.User circles already sat at -4.75). No copper near the new holes; DRC clean.
- **U1 BM83 pad 56**: local (1.40, -0.03) -> (4.77, -0.03) (DS70005402D p.56 Fig. 8-2: X 12.27, Y 10.47; mapping checked against pad 57 and pad 1). Board position (99.825, 32.465) -> (99.825, 29.095). Its GND stub and via were moved with it (track f304dfae and via 49662455, same 1.34 mm length), so the copper under the module is unchanged in amount (r7 BM83 metric identical); the pad stays on GND, In1/B GND planes reached through the via.
- **SW100 TE 1977066-1**: redrawn from TE drawing C1 p.1 (measured from the vector PDF): pad "1" 0.75 x 1.8 at +-1.225, pad "2" 0.6 x 1.8, NPTH d0.9 at (+-2.125, -0.9) on the actuator side, two net-less bracket tabs 1.3 x **0.9** at (+-1.85, -1.95), TE no-track keep-out between the tabs (footprint rule area). The brief's "1.2 x 1.3" tab is the 1.2 mm keep-out height in the drawing; the tab itself is 0.90 tall. Origin = terminal-pad row; actuator tip at local y -2.95. Footprint moved (136.07, 25.245) -> (136.07, 22.95) so the tip sits on the board edge (y 20.0); before, the tip was 2.30 mm inside. Lid inner face at edge + 0.5, outer at edge + 4.5 (cad/v13 meta): the lid plunger bridges 4.5 mm. Courtyard 5.5 x 4.35 (x 133.32-138.82): J1 courtyard 5.7 mm away; R113 nudged 0.08 mm west for the HA8 tall-part tier (1.5 mm). QON/GND copper redrawn: GND pad 2 -> new GND via (136.07, 24.25); pin-1 stack joined behind the pads at y 25.0; R113-1 -> left pad one 45-degree run.
- **C275**: CP_Elec_8x10 land -> CP_Elec_6.3x7.7 (pads 3.5 x 1.6 at +-2.7, KiCad library geometry, model unchanged). PVDD pour and the GND stub reconnect (stub end inside the new pad).
- 3D models: `models-v13/apply.py --map apply-map.json --board` applied (36 footprints; second run reports 0 changes).

## 3. Task B

### 3.1 B1, U4 pocket (decision and edits)

Finding: the pocket is not one blocker but three.
1. The SW2 bootstrap loop (U4-26 -> SW2_F -> B.Cu leg -> C110 -> BTST2 -> U4-19) necessarily encloses U4-20..25; those pins can only leave by crossing the loop on the other layer.
2. With C110 at (155.75, 125.0) the B.Cu SW2 via and the REGN B.Cu diagonal leave no lane south of the pocket at the switch_sensitive 1.0 mm rule (only one 0.25 mm lane between the SW2 via and the SYS via row at y 128.2).
3. **East corridor**: BATP, Q103-G, CE_N and TS_SENSE go north-east/east (R112, Q103, Q100, J5). On B.Cu the BAT_INT 24-via field (x 163.9-170.3, y 120.4-124.5), H3 (r 3.06 at 166.4, 128.3), SYS_COL_B and its via rows close the band y 115.7-131. On F.Cu the BAT/SYS pours fill it. This is not openable with <= 4 mm part nudges.

Decision (power first, safe and reliable): make the bootstrap loop compact, give PROG (essential: charger default configuration) a direct F.Cu lane, widen the BAT finger, and leave the east-bound nets for an owner-level corridor decision (section 6).

Edits (full coordinates in section 7):
- **C110** (155.75, 125.0) -> (154.73, 124.28), same rotation. BTST2 U4-19 -> C110-1 is now 2.05 mm (was 3.0): east 0.64, 45 degrees to x 154.73, straight down into the pad.
- **SW2**: C110-2 -> F.Cu stub (0.4) -> via (155.13, 125.8) -> B.Cu leg (0.4) (155.13, 125.8)-(156.3, 124.63)-(156.3, 118.5)-(153.0, 115.2) to the existing SW2_F via. That is 11.9 mm, against 11.7 mm before, and it now runs east of the pocket instead of through it. Old leg, stub and via (156.55, 125.57) removed.
- **R102 (PROG)** (159.3, 123.95) rot 0 -> (156.05, 124.3) rot -90. Its GND goes by F.Cu to a new GND via (157.0, 124.8975), shared with C106-2. The old vias (159.897, 124.75) and (157.5, 124.75) were removed.
- **C106** (157.2, 122.84) -> (157.9, 122.84), and **TP2** (158.97, 126.485) -> (159.07, 126.485), for HA8 (0.4 mm tier).
- **PROG closed**: U4-20 -> E 0.835 -> 45 degrees -> R102-1, 3.30 mm, which is 1.03 x its octilinear minimum.
- **ILIM_HIZ** rerouted: U4-17 -> E to x 154.07 -> straight down into R108-2. That is 3.37 mm, against 3.56 mm before, and it frees the C110 site.
- **BAT_U4PIN_F** outline: 10 vertices, north edge from x 153.75 (was 154.05), south edge a 45-degree line x - y = 32.515 down to y 123.0 (0.2 mm neck to PROG). Measured: **2.845 -> 2.652 mOhm**, loss at 6 A 102.4 -> 95.5 mW. Experiments: lane-free finger 2.575 (F3; blocks PROG, rejected), north-only 2.647 (F2). The remaining hotspot is the 0.28 mm pin neck at x 153.78 (pins 0.2 mm wide, unavoidable). Width at x 154.05 is still limited by SYS_U4PIN_F (0.2 mm), so 1.6 mm there is not met; the >= 2.5 mm width at x 154.8 is met.
- U4-26/28 45-degree fan-out (Fix 4): not done. SW1_F/SW2_F still fill the gap between the PMID/SYS feeds and U4-27 at the neck clearance; widening needs the PMID/SYS feed outlines reshaped (not attempted, budget).
- BATP, Q103-G, CHG_INT: not routed (east corridor, and U4-18 is boxed by BTST2/ILIM/C110 on F.Cu). No switch_critical exemption was added: it would not create the corridor.

Iterations (AG13): B1 build 1 (shorting ILIM vs U4-16 corner pad, courtyard C106/R102), build 2 (DRC 0, HA8 +3), build 3 (TP2/R102 HA8, DRC 0), final. Logged in `t/planB1.json`, `B1.edit.json`, `t/B1.cycle.log`.

### 3.2 B2-B4 (not closed)

`scripts/hr.py` was re-run on all 88 open jobs (`t/j1.json`, log `t/j1.log`, stopped after 22 jobs at about 45 min). It reproduced only RT-4's rejected detours, all over 1.5 x octmin + 1 mm: U12-EN 5.0 mm vs 1.9 mm, U11-FAULT 8.4/2.6, BT_PWR_EN 14.0/3.8, U14-FB 10.5/4.5, BT_FORCE_PWM 13.0/5.5. **0 accepted.** New root-cause findings:
- **B2, U24 VIN block (16)**: the long control net **HP_G1** (U3-21 -> U10-7/R238) runs straight through the block. It goes F.Cu x 154.225 from y 77.1 to 81.15, then x 154.775 to 83.4, then under the U24 body to (146.6, 87.6). That walls off U24-1..4 from C206-C209. In addition each RC node R20x-2 -> C20x-1 has to pass between the C20x-2 GND pads and their GND vias (0.68 mm gaps: one 0.25 mm AUDIO track fits at 0.215 mm). Remedy: reroute HP_G1 around the north of the codec block (y about 76.3 west to x 146), then hand-place the four RC links at 0.25 mm. This is HP_G1 copper work, not a placement nudge.
- **B3, I2S/AUD I2C at U6/U7 (8)**: unchanged from RT-4 (U6-12/13 have no legal exit at 0.4 mm plus the 0.6 mm halo inside BKO_U6). Needs the TP12/TP14 swap or hop sites outside BKO_U6/U7.
- **B4, U11/U25/U14 and the long control nets (about 28)**: as RT-4. The NRST 0-degree joint at U3-12 is fixed: the long stub was split at the via (129.75, 83.325), giving one straight run.

## 4. Rule-file exemption (documented, sentinel-tested)

Appended to the project rule file as rule 20 `rt5_sw100_te_land`: hole clearance 0.05 mm, only between SW100's own items (`A.Parent == 'SW100' && B.Parent == 'SW100'`). TE's land pattern puts the peg holes 0.075 mm from the terminal lands and 0.15 mm from the bracket tabs.
- Proof it is narrow: RT-5 with the project rule file gives exactly 4 hole_clearance items, all SW100-own (`sentinel/C1_noexempt.drc.json`).
- Sentinel: an appended I2S_CLK width >= 5 mm rule fires (73 items).
- Fab note: a 0.075 mm web to an NPTH is below JLC's usual NPTH-to-copper figure, and the drill may nick the pad corner. The alternative is trimming the outer lands to 0.65 at +-1.175 (0.175 mm), as noted in `footprint-fixes.md`.

## 5. Part moves (old -> new; all <= 4 mm except none)

| ref | old | new | mm | reason |
|---|---|---|---|---|
| SW100 | (136.07, 25.245) | (136.07, 22.95) | 2.30 | actuator tip onto the board edge (task A, fixed part: axis x unchanged) |
| C110 | (155.75, 125.0) rot -90 | (154.73, 124.28) rot -90 | 1.25 | compact BTST2/SW2 loop, frees PROG lane |
| R102 | (159.3, 123.95) rot 0 | (156.05, 124.3) rot -90 | 3.27 | PROG resistor on a direct lane |
| C106 | (157.2, 122.84) | (157.9, 122.84) | 0.70 | HA8 0.4 tier to R102/C110 |
| R113 | (131.42, 24.745) | (131.34, 24.745) | 0.08 | HA8 tier c to the new SW100 courtyard |
| TP2 | (158.97, 126.485) | (159.07, 126.485) | 0.10 | HA8 0.4 tier to R102 |

HF decoupling: C110 (bootstrap) is 1.3 mm from U4-19 (was 2.3); C106 (BAT 10 uF) moved 0.7 mm away from U4-22/23 (still inside the BAT strip, 4.4 mm from the pins); no other decoupling cap moved.

## 6. Open problems

1. **East corridor from U4 (BATP, Q103-G, CE_N Q100 leg, TS_SENSE, plus CHG_INT)**: owner decision needed. Options: thin the BAT_INT 24-via field to open a B.Cu lane at y about 125-126 west of H3; route these slow nets on In2 through the SYS_IN2 island (needs a coordinator exception to rule 19's intent); or move Q103/R112 closer. U4-18 BATP is also boxed on F.Cu by BTST2/ILIM/C110; its 2.0 mm switch_critical rule then has to be met outside NECK_U4.
2. **Switch proximity, new (all inside NECK_U4, DRC-legal)**:
   - ILIM_HIZ is 0.36 mm from the SW2 stub/pad over about 0.6 mm (RT-4: 0.84 at the escape).
   - TS_SENSE is 0.99 mm and PROG 1.28 mm from SW2.
   - BTST2/PROG run parallel at 0.2 mm for 1.5 mm.
   - ILIM_HIZ is an analog input: watch the IINDPM readback at bring-up.
3. BAT_INT 2.652 mOhm is 0.05 above the 2.6 target; the remaining gain needs SYS_U4PIN_F reshaped (north edge) or the PROG lane routed differently.
4. The library must take `lib-proposed/` (5 files) and the C275 symbol footprint field, or DRC on the project library will show 4 lib_footprint_mismatch + 1 lib_footprint_issues warnings.
5. B2 HP_G1 reroute, B3 I2S hop sites/TP swap, B4 long nets: as section 3.2.

## 7. Regenerated-outputs TODO (not done here)

- Position/CPL files: 6 parts moved, and SW100, C275 and U1 have new footprints.
- JLC/stencil data: C275 and SW100 paste layers changed, and U1 pad 56 moved.
- Teardrops: edit.py removed 5 teardrop zones near edited copper (A1 4, B1 1); regenerate them.
- Fab outputs: Gerber/drill (the J2/J3 NPTH and SW100 holes changed), plus BOM footprint text for C275.
- Board STEP: re-export for the enclosure build (SW100 position; the lid plunger is 4.5 mm).
- Library: copy in `lib-proposed/`; schematic C275 footprint field.

## 8. Files (`ai-files/pcb/work-route5/`)

- Result: `RT-5.kicad_pcb/.kicad_pro/.kicad_dru` (= `C1s`). Evidence: `evidence/rt5-F.png`, `evidence/rt5-B.png` (+ .svg), `evidence/a-sw100.png`, `evidence/b1-u4-F.png`, `evidence/b1-u4-B.png`.
- Build chain:
  - RT-4 -> `A0` (`scripts/fpfix.py`, `t/A0.fpfix.json`)
  - -> `A1` (`t/planA.json`, `A1.edit.json`)
  - -> `A2` (v13 models)
  - -> `B1` (`t/planB1.json`, `B1.edit.json`)
  - -> `C1` (`t/planN.json`, `C1.edit.json`)
  - -> `C1s` (silk_tile).
- Library proposal: `footprint-fixes.md`, `lib-proposed/*.kicad_mod`; `kicad-library/` is a local copy, project footprints + proposals, with 3d linked to the project.
- Scripts (`scripts/`): copies of the RT-4 set plus `fpfix.py`, `fpshow.py`, `uncnet.py`, `ha8diff.py`, `runA.sh`.

## 9. Edit log (net, layer, coordinates)

Footprint-internal edits (A0, `t/A0.fpfix.json`): J2/J3 NPTH `(at -5.75 +-5 270)` -> `(at -4.75 +-5 270)`; U1 pad 56 `(at 1.4 -0.03 90)` -> `(at 4.77 -0.03 90)`; C275 lib id, pads (+-2.7, 3.5 x 1.6, rratio 0.15625) and 34 graphic blocks replaced by the KiCad CP_Elec_6.3x7.7 graphics; SW100 8 blocks replaced (section 2) and footprint origin moved.

### A1 (task A copper: SW100 QON/GND, U1 pad-56 GND)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg del db0fc233 | Net-(U4-QON) | F.Cu | 0.25 | (132.1700, 25.3425)-(132.7200, 24.7925) |
| seg del 8026fecc | Net-(U4-QON) | F.Cu | 0.25 | (132.7200, 24.7925)-(132.7200, 24.0425) |
| seg del 934667da | Net-(U4-QON) | F.Cu | 0.25 | (132.7200, 24.0425)-(133.2700, 23.4925) |
| seg del 6baa6190 | Net-(U4-QON) | F.Cu | 0.25 | (133.2700, 23.4925)-(134.0200, 23.4925) |
| seg del fe390e2d | Net-(U4-QON) | F.Cu | 0.25 | (134.0200, 23.4925)-(134.5700, 24.0425) |
| seg del 2f7a1d93 | Net-(U4-QON) | F.Cu | 0.25 | (134.5700, 24.0425)-(134.5700, 25.1950) |
| seg del 019109bb | Net-(U4-QON) | F.Cu | 0.25 | (137.5700, 25.1950)-(137.5700, 23.9950) |
| seg del ea07d7a2 | Net-(U4-QON) | F.Cu | 0.25 | (137.5700, 23.9950)-(137.0200, 23.4450) |
| seg del 026257b1 | Net-(U4-QON) | F.Cu | 0.25 | (137.0200, 23.4450)-(135.7700, 23.4450) |
| seg del f2669c5e | Net-(U4-QON) | F.Cu | 0.25 | (135.7700, 23.4450)-(134.8200, 24.3950) |
| seg del b6f59aff | GND | F.Cu | 0.3 | (136.0700, 25.2450)-(136.0700, 26.9000) |
| seg del 9c285f85 | GND | F.Cu | 0.3 | (136.0700, 26.9000)-(136.8700, 27.7000) |
| seg del 7365ec5c | GND | F.Cu | 0.3 | (136.8700, 27.7000)-(138.9700, 27.7000) |
| seg del 6f845e4f | GND | F.Cu | 0.3 | (138.9700, 27.7000)-(140.0700, 26.6000) |
| seg set f304dfae | GND | F.Cu | 0.3 | (99.8250, 32.4650)-(101.1650, 32.4650) -> (99.8250, 29.0950)-(101.1650, 29.0950) |
| via move 49662455 | GND | F-B | - | (101.1650, 32.4650) -> (101.1650, 29.0950) |
| seg add | GND | F.Cu | 0.3 | (136.0700, 22.9500)-(136.0700, 24.2500) |
| seg add | Net-(U4-QON) | F.Cu | 0.25 | (132.1700, 25.3425)-(134.5625, 22.9500) |
| seg add | Net-(U4-QON) | F.Cu | 0.25 | (134.5625, 22.9500)-(134.8450, 22.9500) |
| seg add | Net-(U4-QON) | F.Cu | 0.25 | (134.8450, 22.9500)-(134.8450, 24.6000) |
| seg add | Net-(U4-QON) | F.Cu | 0.25 | (134.8450, 24.6000)-(135.2450, 25.0000) |
| seg add | Net-(U4-QON) | F.Cu | 0.25 | (135.2450, 25.0000)-(136.8950, 25.0000) |
| seg add | Net-(U4-QON) | F.Cu | 0.25 | (136.8950, 25.0000)-(137.2950, 24.6000) |
| seg add | Net-(U4-QON) | F.Cu | 0.25 | (137.2950, 24.6000)-(137.2950, 22.9500) |
| via add | GND | F-B | 0.6/0.3 | (136.0700, 24.2500) |
| teardrops removed near edits | | | | 4 |

### B1 (task B1: U4 bootstrap/PROG/ILIM/BAT finger, part nudges)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg del 9b5d2fd2 | /Battery_Charger/BTST2 | F.Cu | 0.2 | (154.0700, 122.5850)-(155.7500, 124.2650) |
| seg del f78dc4d4 | /Battery_Charger/SW2 | F.Cu | 0.4 | (155.7500, 125.5700)-(156.5500, 125.5700) |
| seg del a9617583 | /Battery_Charger/SW2 | B.Cu | 0.4 | (153.0000, 115.2000)-(154.3000, 120.0000) |
| seg del 430c55b1 | /Battery_Charger/SW2 | B.Cu | 0.4 | (154.3000, 120.0000)-(155.6000, 122.8000) |
| seg del cc9b7c7e | /Battery_Charger/SW2 | B.Cu | 0.4 | (155.6000, 122.8000)-(156.4000, 124.0000) |
| seg del 9fcea13e | /Battery_Charger/SW2 | B.Cu | 0.4 | (156.5500, 125.5700)-(156.4000, 124.0000) |
| seg del 01f82768 | /Battery_Charger/ILIM_HIZ | F.Cu | 0.2 | (153.4200, 123.3850)-(154.0700, 123.3850) |
| seg del bc436704 | /Battery_Charger/ILIM_HIZ | F.Cu | 0.25 | (154.0700, 123.3850)-(154.6200, 123.9350) |
| seg del b0c8ce56 | /Battery_Charger/ILIM_HIZ | F.Cu | 0.2 | (154.6200, 123.9350)-(154.6200, 125.4350) |
| seg del 68d95b81 | /Battery_Charger/ILIM_HIZ | F.Cu | 0.2 | (154.6200, 125.4350)-(154.0200, 126.0350) |
| seg del 48d4aef7 | GND | F.Cu | 0.3 | (159.8970, 123.9500)-(159.8970, 124.7500) |
| seg del 55073cc6 | GND | F.Cu | 0.6 | (157.2000, 123.8780)-(157.5000, 124.1780) |
| seg del f9d66e35 | GND | F.Cu | 0.6 | (157.5000, 124.1780)-(157.5000, 124.7500) |
| via del 22688bb2 | /Battery_Charger/SW2 | F-B | 0.6/0.3 | (156.5500, 125.5700) |
| via del 0557b591 | GND | F-B | 0.6/0.3 | (159.8970, 124.7500) |
| via del 0c769a49 | GND | F-B | 0.6/0.3 | (157.5000, 124.7500) |
| zone outline BAT_U4PIN_F | /Battery_Charger/BAT_INT | F.Cu | - | 11 -> 10 vertices: (153.3,120.885) (153.75,120.885) (153.75,120.05) (155.3,120.05) (155.3,119.6) (156.6,119.6) (156.6,123) (155.515,123) (154,121.485) (153.3,121.485) |
| footprint move C110 | - | F | - | (155.75, 125) -> (154.73, 124.28, -90) |
| footprint move R102 | - | F | - | (159.3, 123.95) -> (156.05, 124.3, -90) |
| footprint move C106 | - | F | - | (157.2, 122.84) -> (157.9, 122.84) |
| footprint move R113 | - | F | - | (131.42, 24.745) -> (131.34, 24.745) |
| footprint move TP2 | - | F | - | (158.97, 126.485) -> (159.07, 126.485) |
| seg add | /Battery_Charger/BTST2 | F.Cu | 0.2 | (154.0700, 122.5850)-(154.7300, 123.2450) |
| seg add | /Battery_Charger/BTST2 | F.Cu | 0.2 | (154.7300, 123.2450)-(154.7300, 123.7125) |
| seg add | /Battery_Charger/SW2 | F.Cu | 0.4 | (154.7300, 124.8475)-(154.7300, 125.4000) |
| seg add | /Battery_Charger/SW2 | F.Cu | 0.4 | (154.7300, 125.4000)-(155.1300, 125.8000) |
| seg add | /Battery_Charger/SW2 | B.Cu | 0.4 | (153.0000, 115.2000)-(156.3000, 118.5000) |
| seg add | /Battery_Charger/SW2 | B.Cu | 0.4 | (156.3000, 118.5000)-(156.3000, 124.6300) |
| seg add | /Battery_Charger/SW2 | B.Cu | 0.4 | (156.3000, 124.6300)-(155.1300, 125.8000) |
| seg add | /Battery_Charger/PROG | F.Cu | 0.2 | (153.4700, 122.1850)-(154.3050, 122.1850) |
| seg add | /Battery_Charger/PROG | F.Cu | 0.2 | (154.3050, 122.1850)-(156.0500, 123.9300) |
| seg add | GND | F.Cu | 0.3 | (156.0500, 124.8975)-(157.0000, 124.8975) |
| seg add | GND | F.Cu | 0.4 | (157.9000, 123.8770)-(157.9000, 123.9975) |
| seg add | GND | F.Cu | 0.4 | (157.9000, 123.9975)-(157.0000, 124.8975) |
| seg add | /Battery_Charger/ILIM_HIZ | F.Cu | 0.2 | (153.4200, 123.3850)-(154.0700, 123.3850) |
| seg add | /Battery_Charger/ILIM_HIZ | F.Cu | 0.2 | (154.0700, 123.3850)-(154.0700, 126.1000) |
| via add | /Battery_Charger/SW2 | F-B | 0.6/0.3 | (155.1300, 125.8000) |
| via add | GND | F-B | 0.6/0.3 | (157.0000, 124.8975) |
| teardrops removed near edits | | | | 1 |

### C1 (NRST joint at U3-12)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg set 3cfc3845 | /MCU/NRST | F.Cu | 0.25 | (129.7500, 82.1750)-(129.7500, 84.4250) -> (129.7500, 83.3250)-(129.7500, 84.4250) |
| teardrops removed near edits | | | | 0 |

