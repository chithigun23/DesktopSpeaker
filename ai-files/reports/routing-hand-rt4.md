# RT-4: charge copper, hand templates and hand closures (2026-11-02)

Agent "Hand templates and nudges RT-4". Input `ai-files/pcb/work-route3/RT-3.*` (RT-2 routing + silkscreen). Work folder `ai-files/pcb/work-route4/` only. Result `ai-files/pcb/work-route4/RT-4.kicad_pcb/.kicad_pro/.kicad_dru`. Nothing in `DesktopSpeaker-kicad/`, earlier work folders, `helpers/route_oct*.py` or `work-oct3/` was edited (helpers used read-only; `route_oct_rules.py` snapshotted as `scripts/rules_snap.py`, SHA-256 3eab4ddd…). All copper edits are text edits (`scripts/edit.py`, extended with `fp_move`); zones refilled in a separate pcbnew process with the pristine project `.kicad_pro/.kicad_dru` beside the board. Not committed; nothing published.

## 1. Result

| gate | RT-3 | RT-4 |
|---|---|---|
| kicad-cli DRC `--severity-all --all-track-errors`, violations | 0 | **0** (no USB gap/skew/uncoupled items) |
| DRC unconnected | 152 | **108** (44 closed, 0 new; the 16 inherited power items 3V_AO/GND/LDO_3V3 unchanged) |
| router-scope open connections (RT-2 list 136 + 2 XTO) | 138 | **92** |
| BAT_INT path U4-22/23 -> Q103-1..3 (copper_path_solve, 20 C) | 3.320 mOhm | **2.845 mOhm** (target <= 2.9) |
| footprints moved / pad nets changed (360 fp, 1192 pads) | | **R102 only** / **0** |
| rule files vs project (dru 102fbee4…, pro aa88e8c9…) | equal | **equal**, no exemption used |
| sentinel (I2S_CLK width >= 5 mm appended on a copy) | | **FIRES** (73 items) |
| locked copper: RT-3 items unchanged | | 2740 of 2752 (12 intentional: 9 segments, 2 vias, 1 zone outline); SHA-256 of the locked set `2b581bed57f4f44e82f5ad0d04ea4f449cefb28c46ff4ef893e61eaee5da3d10`; 0 unexpected removals |
| new copper exact 0/45/90 (gates4.py, own text parse) | | **162 segments, 298.1 mm, 0 not exact** |
| pour check (route_oct_pourcheck) | | **OK** (foreign unconnected 86 -> 86) |
| r7 joints < 80 / < 30 deg | 19 / 7 | 20 / 8 (+1: NRST at U3-12, see 6.3) |
| r7 sensitive vias / worst GND-via distance of new vias | 36 | 40 / none above 1.5 mm |
| r7 BM83 F.Cu / vias inside | GND 2.3, SYS_PWR 2.0 | unchanged (no new copper under BM83) |
| r7 near-parallel (all pairs) | 19 | 21: new U13-NC/U16-NC 1.4 mm @ 0.228, USB_CC1/CC2 0.6 mm @ 0.25 (both < 3 mm) |
| parcheck (< 0.4 mm over > 3 mm) on the 40 touched nets | | 0 pairs |

Gate files (work-route4): `RT-4.drc.json`, `RT-4.gates.json/.txt`, `RT-4.check.json/.txt`, `RT-4.r7.json`, `RT-3.r7.json`, `RT-4.par.json`, `RT-4.pour.txt`, `RT-4.sentinel.txt` (+ `sentinel/`), `RT-4.rulehash.txt`, `RT-4.nets.txt`.

## 2. Task 1: charge copper

Edits (board T1, full coordinates in section 7):
- **REGN B.Cu** under the U4 east pin row moved 0.45 mm west (x 153.43-153.57 -> x 153.0, exact 0/45/90, 0.4/0.5 mm kept). Frees B.Cu under U4-20…24 for a future escape via.
- **BTST2** (U4-19 -> C110-1) redrawn to turn SE at x 154.07 (0.3 mm beyond the toe) instead of 154.55: 3.4 -> 3.0 mm, frees the U4-20/21 SE lanes.
- **BAT_U4PIN_F** outline (11 -> 11 vertices): finger 0.6 mm only to x 154.05 (0.28 mm beyond the pad toe), then 1.32-1.44 mm (x 154.05-154.55, north edge fixed at 0.2 mm from SYS_U4PIN_F), 1.70 mm at x 154.8, 2.53 mm at x 155.3, south edge a 45-degree line (x - y = 33.04) that keeps 0.2 mm (neck) to the reserved CHG_INT lane; the old SE lobe (x 155-156.6, y 122.8-123.2) removed for the same lanes.
- **R102 (PROG) nudge**: (160.000, 122.640) -> (159.300, 123.950), 1.49 mm. Its GND via (159.9, 124.35) and the C106-2 GND via (158.3, 124.178) replaced by vias at (159.897, 124.75) and (157.5, 124.75). The BAT_INT_F strip is now **3.45 mm everywhere from x 155.3 to 164** (was 2.64-2.89 at x 159-161).
- Measured BAT_INT width (fill, F.Cu): x 154.05 1.32, 154.55 1.44, 154.8 1.70, 155.05 1.95, 155.3 2.53, 156-163 3.45 mm.
- Resistance (helpers/copper_path_export.py + copper_path_solve.py, 0.05 mm cells, 6 A): **3.320 -> 2.845 mOhm** (loss at 6 A 119.5 -> 102.4 mW; F.Cu hotspot now the 0.28 mm pin neck at x 154.07).
- Shortfall vs the report targets: 1.6 mm by x 154.05 is limited by SYS_U4PIN_F (0.2 mm), 2.5 mm by x 154.8 by the CHG_INT/PROG lanes. Target resistance met anyway.
- **U4-24 / U4-20 / U4-21 / U4-18 escapes: not routed (structural).** Tried: a 0.5/0.2 neck via at (153.708, 120.31) with a NE stub (fits after the REGN move, DRC ok). The B.Cu pocket it lands in is closed by the SW2 bootstrap track (L1-2 via (153.0, 115.2) -> (154.3, 120) -> (155.6, 122.8) -> C110-2 via (156.55, 125.57)) on the east and REGN on the west, the SYS_COL_B pour, the SYS via rows and H3; F.Cu above is SYS/BAT pour. The hand-route search exhausted the pocket (60 k states, `t/dbg1.png`). Q103-G, BATP, PROG and CHG_INT all start in this pocket; a switch_critical exemption for U4-18 would not help. The stub/via were removed again (no dangling via). Remedy: reroute the C110-2 SW2 B.Cu track (e.g. a shorter BTST2/SW2 arrangement next to U4-26) or move C110, then the four nets get their escape via at the U4 east toe.
- **U4-26/28 fan-out (Fix 4): not done.** SW1_F/SW2_F already fill the space between the PMID (x <= 150.84) and SYS feeds and the U4-27 GND pin at the 0.2 mm neck clearance; widening needs the PMID/SYS feeds reshaped.

## 3. Task 2: placement nudges

Only one nudge applied (R102, task 1). The others were evaluated against what they would open:
- R252: not needed. U25-3 FSW closed by one straight 0.2 mm segment (150.3, 145.945)-(151.458, 145.945) inside NECK_U25 (lattice-offset issue of the search, not a blocked exit).
- C239: does not open HP_L. U9-10 is walled off by the 3V3_AUDIO feed U9-8 -> C237-1 -> via (187.8, 60.35) and the VMID_HP B.Cu run; needs a 3V3_AUDIO/C237 rework, not a 1.5 mm move.
- C210/C212: U24-30 (VINR3) and U24-6 (VREF) closed without moving them.
- C226: the open XO connection (Y200-3 -> U24-9) is blocked by the Y200-2 GND via (150.85, 78.0) and the XI/AVDD copper, not by C226; candidate fix: remove that GND via (Y200-2 is tied to Y200-4 on F.Cu) and route XO east of Y200-2. Not done (budget).
- C173, R226, C124/C125, C141/C142, C283/C294/C296, R182/TP22: not applied. U2-VOUTR, U7-ADR, U6-PDN, U12-EN (U20-7 -> U20-2), U20-PR1, BT_RXD_M closed without nudges; the rest remain (section 5).
- HA8: R102 moved into free board (no new neighbour within 0.4 mm, checked on the render); a full HA8 re-run (`work-r8/scripts/r8b_ha8.py`) was not done: open item.

## 4. Task 3 / 4: hand templates and hand closures

Method: `scripts/hr.py` drafts each connection (local exact-octilinear lattice search anchored at the start pad, 45-degree bends only, run >= 0.75 mm after a bend with 0.4 mm fallback, pad exits >= 0.3 mm straight, class widths, rule-file clearances with the neck_ic value inside neck areas, hole 0.25 / edge 0.5, BKO / BM83 / antenna / J7 keep-outs, 0.6 mm halo for AUDIO/I2S/USB/AUD I2C, sensitive B.Cu only over In2 GND, GND stitch via within 1.5 mm of every sensitive via). Results were accepted only if (a) DRC 0 and (b) length <= 1.5 x octilinear minimum + 1 mm; 13 drafts were rejected for detours (U25-FSW 3.6x, U11-FAULT 3.0x, BT_FORCE_PWM 2.4-2.8x, U14-FB 2.3x, U8-NC2 5.5-6.3x, U6-PDN 2.2x (then closed directly in batch E at 0.98x), BT_PWR_EN 3.5x, USB_CC2 D5-2 -> J1-B5 2.1x) and 1 for DRC (U10-INL- vs the inherited 3V3_AUDIO diagonal, audio_clear 0.42 mm).

Iterations (AG13): task 1: 2 builds (T1: annular ring of a 0.45 via, dangling via -> T1 final). Templates (A): 2 builds (hole clearance 0.248 at J7 NPTH, then DRC 0). Closures: B2 (1 DRC fix by dropping), E (1 DRC fix by dropping). All logged in `t/*.log` and `T*.edit.json`.

Templates (task 3):
| item | result |
|---|---|
| (a) I2S BCK/LRCK at U6/U7 | **not closed.** U6-12/13 have no legal exit at the 0.4 mm clock clearance + 0.6 mm halo inside BKO_U6 (search starts blocked); U7-13 is 53 mm from the hub (outside the search cap). Needs the swap of TP12/TP14 or a placement change near U6 |
| (b) AUD I2C crossing | **not closed** (U24-23 and U6-15 pockets; AUD_SCL TP18 leg) |
| (c) fan-outs | U25: SS, ILIM, COMP, FSW closed; FB/MODE open. U24: VINR3, VINL3, VREF closed; VINL1/VINL2/VINR1/VINR2 open (the C206-C209 / R200-R203 pads are boxed by the 0.5 mm audio clearance). U4: CE_N (U4-13 -> R103-2) and ILIM_HIZ (U4-17 -> R108-2) closed; U4-12/14/15/16/18/20/21/24 open (pocket, section 2). U6/U7: U6-PDN, U7-ADR closed; U7-PDN, AMP_FAULT_N open |
| (d) J7 TC2030 | SWCLK J7-4 closed (diagonal escape, B.Cu hop, 8.47 mm); NRST J7-3 closed to U3-12 (27.3 mm, 4 vias, 1.35x); SWDIO open. **No rule area added**: the board hole clearance is already 0.25 mm and DRC passes with it; assumption: JLC minimum hole-to-copper 0.2 mm (not re-verified on the JLC site) |
| (e) U4-18 BATP stub | **not done**, no exemption added: structurally blocked (section 2) |
| (f) J1 CC | CC1 J1-A5 -> D5-1 with a B.Cu hop (vias (150.23, 25.255) and (154.23, 27.905); 9.69 mm, 1.73x, accepted as the requested hop); U11-28 -> C182-1 and U11-29 -> C183-1 escapes. CC2 J1-B5 -> D5-2 only found as a 2.1x detour (rejected); D5-1 -> C182-1 and D5-2 -> C183-1 (about 25 mm) open |
| (g) XTO | R174-2 and C178-1 joined to the template (4.52 and 1.80 mm): **XTO complete** |

Closed connections (44, by net): AMP_BOOST_EN 1, BT_AUDIO_L 1, BT_AUDIO_R 1, BT_UART_TX 1, CE_N 1, ILIM_HIZ 1, BT_RXD_M 2, CHG_SYS_ENABLE 1, CTRL_SCL 1, CTRL_SDA 1, HP_EN 1, HP_SEL_A 1, HP_SEL_B 1, NRST 2, SWCLK 1, PDCTRL_SCL 1, PD_SINK_EN 1, USB_CC1 2, USB_CC2 1, C231-Pad2 1, U1-AOHPL 1, U12-EN 1, U15-FB 1, U16-NC 1, U2-SEL0 3, U2-VOUTR 1, U2-XTO 2, U20-PR1 1, U24-VINL3 1, U24-VINR3 1, U24-VREF 1, U25-COMP 1, U25-FSW 1, U25-ILIM 1, U25-SS 1, U4-QON 1 (SW100 pin stack joined under the switch), U6-PDN 1, U7-ADR 1.

By importance group: power-adjacent control 19, clocks/USB CC/XTO 5, analog audio 9, control 11. Hand edits: 44 accepted connections + the task-1 copper set (about 50 edits).

## 5. Remaining open (92 router-scope + 16 inherited power)

| cause | connections | examples / remedy |
|---|---|---|
| U4 east/south pocket (SW2 bootstrap B.Cu wall + REGN + power pours) | 9 | Q103-G, BATP, PROG, CHG_INT, TS_SENSE, CTRL_SDA/SCL at U4-14/15, QON U4-12 leg, CE_N Q100 leg: reroute C110-2 SW2 / move C110 |
| U24 VIN coupling block + C200-C205/C230-C235 block (0.5 mm audio clearance, halo) | 16 | spread the block 0.5-1 mm (placement round) |
| I2S hub / AUD I2C at U6/U7/U24 | 8 | TP12/TP14 swap or B.Cu hop sites outside BKO_U6/U7 (placement) |
| U11 fine pitch (ADC4, R18-36, PLUG_EVENT, FAULT) and U25 FB/MODE, U14 5V_LOGIC_EN | 8 | FAULT, U14-FB found only as > 2x detours; R18/U11-36 footprint-bound |
| U8/U9 3V3_AUDIO feed (COM1/COM2/NC1/NC2, HP_L, U10-INL-) | 6 | 3V3_AUDIO/C237 rework (C239 nudge alone does not open it) |
| long control nets > 30-45 mm (search cap) | about 20 | HP_G0, AUX_DET, CHG_ENABLE, AMP_FAULT_N, AMP_PDN, BT_UART_RX, HP_OUTL, AUX_L, SWDIO, CC1/CC2 D5 -> C18x legs, BT_RST/TXD/SYS_CFG M |
| other pockets / detours rejected | about 25 | BT_PWR_EN, BT_FORCE_PWM, Q101-G, GAUGE_ISO_N, U12-EN U12-3 leg, U2-VOUTL, U7-PDN, XO |

None of the remaining ones can be closed within the allowed nudges (<= 1.5 mm) and the 1.5x length rule without one of the placement or power-copper changes above.

## 6. Open problems

1. **U4 pocket** (section 2): blocks 9 charger/MCU connections and the U4-18 template. Needs an owner decision on the BTST2/SW2 bootstrap path or the C110 position.
2. **Length / hygiene items on new copper** (route_oct_check on the 40 touched nets): 7 "dangling" ends are T-joins into the middle of existing same-net tracks (BT_AUDIO_L/R, CTRL_SCL, SWCLK, PDCTRL_SCL; KiCad connects them, DRC counts them connected) plus 2 inherited REGN items; 5 bend-spacing-short and 6 pad-exit-short items (0.4 mm fallback runs at fine-pitch pins); ratio p95 1.53, max 1.62 (U20-PR1, U2-SEL0).
3. **NRST 0-degree joint at U3-12**: two NRST connections leave the same pad on the same stub (r7 +1 acute). Electrically fine (inside pad copper), violates the "no joint < 90" rule; merge the two stubs.
4. **Switch proximity (r7 sw, new)**: ILIM_HIZ 0.84 mm from SW2 at the U4-17 escape (pin-pitch limited, inside NECK_U4); U15-FB 1.43/1.68 mm from U15-L2/L1 (pin geometry, same as RT-2's U14-FB note).
5. **Sensitive B.Cu over In2 void**: BT_AUDIO_L 0.8 -> 1.7 mm, BT_AUDIO_R 1.8 -> 2.6 mm (via antipads of the new hops).
6. **HA8 re-check for R102** and position files after the R102 move are not regenerated.
7. Teardrops still absent near edited copper (edit.py removes teardrops within 0.8 mm of edits).
8. The CC1 hop is 1.73x its octilinear minimum (requested template); CC2 hop not found within 1.5x.

## 7. Files (`ai-files/pcb/work-route4/`)

- Result: `RT-4.kicad_pcb/.kicad_pro/.kicad_dru` (= T5), gates listed in section 1, evidence `evidence/rt4-F.png`, `evidence/rt4-B.png` (+ .svg, top view), `evidence/rt4-u4-charge-F.png`, `evidence/u4-before.png`, `evidence/u4-before-B.png`, `evidence/rt4-j7.png`, `evidence/rt4-j1-cc.png`.
- Build chain: RT-3 -> T1 (`t1.plan.json`) -> T2 (`t/pA.json`) -> T3 (`t/pB_f.json`) -> T4 (`t/pM.json`) -> T5 (`t/pE_f.json`); each `T*.edit.json` lists every change with old/new coordinates; `T*.drc.json`, `T*.geo.json`.
- Scripts (`scripts/`): `hr.py` (hand-route drafting), `gen_jobs.py`, `plan_from_log.py`, `ratio2.py`, `edit.py` (+fp_move), `pcbtext.py`, `cycle.sh`, `gates4.py`, `fplib.py`, `crop.py`, `q.py`, `render.sh`, `drcsum.py`, `uncdiff.py`, `rules_snap.py`.
- Scratch: `t/` (job files, logs, debug PNGs, copper-path exports `t/RT-3.cp.json`, `t/T1.cp.json`).

## 8. Edit log (net, layer, coordinates)

### T1: Task 1 charge copper (t1.plan.json on RT-3)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg del 178c1c3c | /Battery_Charger/REGN | B.Cu | 0.4 | (153.4000, 119.6000)-(153.4329, 120.4000) |
| seg del b8f2d724 | /Battery_Charger/REGN | B.Cu | 0.5 | (153.4329, 120.4000)-(153.4830, 121.6170) |
| seg del cbc9536d | /Battery_Charger/REGN | B.Cu | 0.5 | (153.5667, 123.6333)-(153.4833, 121.6167) |
| seg del 7f90c54d | /Battery_Charger/BTST2 | F.Cu | 0.2 | (153.4300, 122.5850)-(154.5500, 122.5850) |
| seg del cca0b769 | /Battery_Charger/BTST2 | F.Cu | 0.2 | (154.5500, 122.5850)-(155.9500, 123.9850) |
| seg del 7f936668 | /Battery_Charger/BTST2 | F.Cu | 0.2 | (155.9500, 123.9850)-(155.9500, 124.3000) |
| seg del 47938bfb | GND | F.Cu | 0.6 | (157.5000, 124.1780)-(158.3000, 124.1780) |
| seg del 91438164 | GND | F.Cu | 0.3 | (160.5975, 122.6400)-(159.9000, 123.3375) |
| seg del da259741 | GND | F.Cu | 0.3 | (159.9000, 123.3375)-(159.9000, 124.3500) |
| via del 23287786 | GND | F-B | 0.6/0.3 | (158.3000, 124.1780) |
| via del 99689be8 | GND | F-B | 0.6/0.3 | (159.9000, 124.3500) |
| footprint move | R102 | F | - | (160.000, 122.640) -> (159.300, 123.950) |
| zone outline BAT_U4PIN_F | /Battery_Charger/BAT_INT | F.Cu | - | 11 -> 11 vertices: (153.3,120.885) (154.05,120.885) (154.05,120.05) (155.3,120.05) (155.3,119.6) (156.6,119.6) (156.6,123) (156.055,123) (154.555,121.5) (154.54,121.485) (153.3,121.485) |
| seg add | /Battery_Charger/REGN | B.Cu | 0.4 | (153.4000, 119.6000)-(153.0000, 120.0000) |
| seg add | /Battery_Charger/REGN | B.Cu | 0.5 | (153.0000, 120.0000)-(153.0000, 123.0667) |
| seg add | /Battery_Charger/REGN | B.Cu | 0.5 | (153.0000, 123.0667)-(153.5667, 123.6333) |
| seg add | /Battery_Charger/BTST2 | F.Cu | 0.2 | (153.4300, 122.5850)-(154.0700, 122.5850) |
| seg add | /Battery_Charger/BTST2 | F.Cu | 0.2 | (154.0700, 122.5850)-(155.7500, 124.2650) |
| seg add | GND | F.Cu | 0.6 | (157.5000, 124.1780)-(157.5000, 124.7500) |
| seg add | GND | F.Cu | 0.3 | (159.8970, 123.9500)-(159.8970, 124.7500) |
| via add | GND | F-B | 0.6/0.3 | (157.5000, 124.7500) |
| via add | GND | F-B | 0.6/0.3 | (159.8970, 124.7500) |

### T2: Task 3 templates: J1 CC1 hop, U11 CC1/CC2 escapes, XTO extension, J7 SWCLK (t/pA.json)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg add | /USB_CC1 | F.Cu | 0.25 | (150.2300, 26.3550)-(150.2300, 25.2550) |
| seg add | /USB_CC1 | B.Cu | 0.25 | (150.2300, 25.2550)-(152.1300, 27.1550) |
| seg add | /USB_CC1 | B.Cu | 0.25 | (152.1300, 27.1550)-(153.4800, 27.1550) |
| seg add | /USB_CC1 | B.Cu | 0.25 | (153.4800, 27.1550)-(154.2300, 27.9050) |
| seg add | /USB_CC1 | F.Cu | 0.25 | (154.2300, 27.9050)-(153.0300, 29.1050) |
| seg add | /USB_CC1 | F.Cu | 0.25 | (153.0300, 29.1050)-(153.0300, 30.9050) |
| seg add | /USB_CC1 | F.Cu | 0.15 | (139.0000, 53.8750)-(139.0000, 53.2750) |
| seg add | /USB_CC1 | F.Cu | 0.25 | (139.0000, 53.2750)-(139.5500, 52.7250) |
| seg add | /USB_CC2 | F.Cu | 0.15 | (138.6000, 53.8750)-(138.6000, 53.2750) |
| seg add | /USB_CC2 | F.Cu | 0.15 | (138.6000, 53.2750)-(138.0500, 52.7250) |
| seg add | Net-(U2-XTO) | F.Cu | 0.25 | (159.2600, 51.1275)-(157.4600, 51.1275) |
| seg add | Net-(U2-XTO) | F.Cu | 0.25 | (153.3075, 49.9100)-(155.7075, 49.9100) |
| seg add | Net-(U2-XTO) | F.Cu | 0.25 | (155.7075, 49.9100)-(157.2075, 51.4100) |
| seg add | /MCU/SWCLK | F.Cu | 0.25 | (122.1000, 64.6850)-(122.9500, 65.5350) |
| seg add | /MCU/SWCLK | B.Cu | 0.25 | (122.9500, 65.5350)-(123.5000, 64.9850) |
| seg add | /MCU/SWCLK | B.Cu | 0.25 | (123.5000, 64.9850)-(125.4000, 64.9850) |
| seg add | /MCU/SWCLK | F.Cu | 0.25 | (125.4000, 64.9850)-(126.2500, 65.8350) |
| seg add | /MCU/SWCLK | F.Cu | 0.25 | (126.2500, 65.8350)-(126.2500, 67.3850) |
| seg add | /MCU/SWCLK | F.Cu | 0.25 | (126.2500, 67.3850)-(124.9500, 68.6850) |
| via add | /USB_CC1 | F-B | 0.6/0.3 | (150.2300, 25.2550) |
| via add | /USB_CC1 | F-B | 0.6/0.3 | (154.2300, 27.9050) |
| via add | /MCU/SWCLK | F-B | 0.6/0.3 | (122.9500, 65.5350) |
| via add | /MCU/SWCLK | F-B | 0.6/0.3 | (125.4000, 64.9850) |

### T3: Task 4 batch B2 (t/pB_f.json)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg add | Net-(U12-EN) | F.Cu | 0.25 | (93.3500, 73.9775)-(91.8500, 73.9775) |
| seg add | Net-(U20-PR1) | F.Cu | 0.25 | (91.8700, 74.9775)-(90.7700, 76.0775) |
| seg add | Net-(U25-SS) | F.Cu | 0.25 | (151.6900, 150.8125)-(151.6900, 150.1125) |
| seg add | Net-(U25-SS) | F.Cu | 0.25 | (151.6900, 150.1125)-(152.4400, 149.3625) |
| seg add | /CHG_SYS_ENABLE | F.Cu | 0.25 | (180.0375, 105.3475)-(180.5875, 104.7975) |
| seg add | /CHG_SYS_ENABLE | F.Cu | 0.25 | (180.5875, 104.7975)-(181.6875, 104.7975) |
| seg add | Net-(U25-ILIM) | F.Cu | 0.25 | (154.9122, 145.4450)-(155.5622, 144.7950) |
| seg add | Net-(U25-ILIM) | F.Cu | 0.25 | (155.5622, 144.7950)-(155.5622, 143.5950) |
| seg add | Net-(U15-FB) | F.Cu | 0.25 | (116.1650, 37.0650)-(115.3150, 37.0650) |
| seg add | Net-(U15-FB) | F.Cu | 0.25 | (115.3150, 37.0650)-(114.7650, 37.6150) |
| seg add | Net-(U15-FB) | F.Cu | 0.25 | (114.7650, 37.6150)-(114.7650, 38.3650) |
| seg add | Net-(U15-FB) | F.Cu | 0.25 | (114.7650, 38.3650)-(114.0150, 39.1150) |
| seg add | Net-(U4-QON) | F.Cu | 0.25 | (137.5700, 25.1950)-(137.5700, 23.9950) |
| seg add | Net-(U4-QON) | F.Cu | 0.25 | (137.5700, 23.9950)-(137.0200, 23.4450) |
| seg add | Net-(U4-QON) | F.Cu | 0.25 | (137.0200, 23.4450)-(135.7700, 23.4450) |
| seg add | Net-(U4-QON) | F.Cu | 0.25 | (135.7700, 23.4450)-(134.8200, 24.3950) |
| seg add | Net-(U25-COMP) | F.Cu | 0.25 | (154.9122, 145.9450)-(155.6122, 145.9450) |
| seg add | Net-(U25-COMP) | F.Cu | 0.25 | (155.6122, 145.9450)-(156.7122, 144.8450) |
| seg add | Net-(U25-COMP) | F.Cu | 0.25 | (156.7122, 144.8450)-(156.7122, 143.5950) |
| seg add | /AMP_BOOST_EN | F.Cu | 0.25 | (149.0600, 140.4375)-(150.7100, 140.4375) |
| seg add | /AMP_BOOST_EN | F.Cu | 0.25 | (150.7100, 140.4375)-(152.0600, 141.7875) |
| seg add | /AMP_BOOST_EN | F.Cu | 0.25 | (152.0600, 141.7875)-(152.0600, 143.9375) |
| seg add | /AMP_BOOST_EN | F.Cu | 0.25 | (152.0600, 143.9375)-(151.5100, 144.4875) |
| seg add | /AMP_BOOST_EN | F.Cu | 0.2 | (151.5100, 144.4875)-(151.5100, 145.4375) |
| seg add | /PD_SINK_EN | F.Cu | 0.25 | (122.3250, 79.7500)-(123.8250, 79.7500) |
| seg add | /PD_SINK_EN | F.Cu | 0.25 | (123.8250, 79.7500)-(129.5750, 74.0000) |
| seg add | /PD_SINK_EN | B.Cu | 0.25 | (129.5750, 74.0000)-(130.9750, 75.4000) |
| seg add | /PD_SINK_EN | B.Cu | 0.25 | (130.9750, 75.4000)-(137.5750, 75.4000) |
| seg add | /PD_SINK_EN | B.Cu | 0.25 | (137.5750, 75.4000)-(139.5250, 73.4500) |
| seg add | /PD_SINK_EN | B.Cu | 0.25 | (139.5250, 73.4500)-(139.5250, 69.8000) |
| seg add | /PD_SINK_EN | B.Cu | 0.25 | (139.5250, 69.8000)-(138.7750, 69.0500) |
| seg add | /PD_SINK_EN | B.Cu | 0.25 | (138.7750, 69.0500)-(138.7750, 66.7000) |
| seg add | /PD_SINK_EN | B.Cu | 0.25 | (138.7750, 66.7000)-(139.3250, 66.1500) |
| seg add | /PD_SINK_EN | B.Cu | 0.25 | (139.3250, 66.1500)-(139.3250, 64.6000) |
| seg add | /PD_SINK_EN | B.Cu | 0.25 | (139.3250, 64.6000)-(137.1250, 62.4000) |
| seg add | /PD_SINK_EN | F.Cu | 0.25 | (137.1250, 62.4000)-(138.0750, 62.4000) |
| seg add | /PD_SINK_EN | F.Cu | 0.25 | (138.0750, 62.4000)-(138.8750, 61.6000) |
| seg add | Net-(U24-VINR3) | F.Cu | 0.3 | (154.2450, 88.2800)-(155.6450, 88.2800) |
| seg add | Net-(U24-VINL3) | F.Cu | 0.3 | (155.1525, 90.7300)-(154.4525, 90.7300) |
| seg add | Net-(U24-VINL3) | F.Cu | 0.3 | (154.4525, 90.7300)-(153.7025, 89.9800) |
| seg add | Net-(C231-Pad2) | F.Cu | 0.3 | (174.5900, 64.3675)-(175.6900, 63.2675) |
| seg add | Net-(U1-AOHPL) | F.Cu | 0.3 | (96.1975, 44.5700)-(97.0475, 43.7200) |
| seg add | Net-(U1-AOHPL) | F.Cu | 0.3 | (97.0475, 43.7200)-(97.0475, 42.8700) |
| seg add | Net-(U1-AOHPL) | F.Cu | 0.3 | (97.0475, 42.8700)-(96.1475, 41.9700) |
| seg add | Net-(U2-VOUTR) | F.Cu | 0.3 | (159.1150, 55.6550)-(160.1650, 54.6050) |
| seg add | Net-(U2-VOUTR) | F.Cu | 0.3 | (160.1650, 54.6050)-(162.2650, 54.6050) |
| seg add | Net-(U2-VOUTR) | F.Cu | 0.3 | (162.2650, 54.6050)-(163.3650, 53.5050) |
| seg add | /BT_AUDIO_R | F.Cu | 0.3 | (174.5175, 70.4000)-(174.5175, 71.0500) |
| seg add | /BT_AUDIO_R | B.Cu | 0.3 | (174.5175, 71.0500)-(169.9675, 75.6000) |
| seg add | /BT_AUDIO_R | B.Cu | 0.3 | (169.9675, 75.6000)-(167.3675, 75.6000) |
| seg add | /BT_AUDIO_R | F.Cu | 0.3 | (167.3675, 75.6000)-(165.6175, 75.6000) |
| seg add | /BT_AUDIO_L | F.Cu | 0.3 | (162.0175, 81.6500)-(162.8175, 80.8500) |
| seg add | /BT_AUDIO_L | F.Cu | 0.3 | (162.8175, 80.8500)-(163.5675, 80.8500) |
| seg add | /BT_AUDIO_L | F.Cu | 0.3 | (163.5675, 80.8500)-(165.5175, 78.9000) |
| seg add | /BT_AUDIO_L | B.Cu | 0.3 | (165.5175, 78.9000)-(165.5175, 76.1500) |
| seg add | /BT_AUDIO_L | B.Cu | 0.3 | (165.5175, 76.1500)-(168.1175, 73.5500) |
| seg add | /BT_AUDIO_L | F.Cu | 0.3 | (168.1175, 73.5500)-(169.1175, 72.5500) |
| seg add | Net-(U2-SEL0) | F.Cu | 0.25 | (155.2150, 62.5750)-(155.8650, 62.5750) |
| seg add | /HP_SEL_B | F.Cu | 0.25 | (183.2950, 67.3875)-(181.9950, 67.3875) |
| seg add | /HP_SEL_A | F.Cu | 0.25 | (173.2950, 67.3875)-(174.6450, 66.0375) |
| seg add | Net-(U2-SEL0) | F.Cu | 0.25 | (156.2425, 64.4800)-(155.3925, 63.6300) |
| seg add | Net-(U2-SEL0) | F.Cu | 0.25 | (155.3925, 63.6300)-(155.3925, 62.8800) |
| seg add | Net-(U2-SEL0) | F.Cu | 0.25 | (155.3925, 62.8800)-(155.9425, 62.3300) |
| seg add | /HP_EN | F.Cu | 0.25 | (197.0450, 63.7775)-(197.6450, 63.1775) |
| seg add | /HP_EN | F.Cu | 0.25 | (197.6450, 63.1775)-(199.3450, 63.1775) |
| seg add | /PDCTRL_SCL | F.Cu | 0.3 | (126.7500, 70.8250)-(126.7500, 73.2250) |
| seg add | /MCU/NRST | F.Cu | 0.25 | (129.7500, 82.1750)-(129.7500, 84.4250) |
| seg add | Net-(U7-ADR) | F.Cu | 0.25 | (194.9550, 127.0550)-(194.9550, 124.9050) |
| seg add | Net-(U7-ADR) | F.Cu | 0.25 | (194.9550, 124.9050)-(195.9550, 123.9050) |
| seg add | /Bluetooth/BT_RXD_M | B.Cu | 0.25 | (107.8825, 50.8650)-(107.8825, 48.4150) |
| seg add | /Bluetooth/BT_RXD_M | B.Cu | 0.25 | (107.8825, 48.4150)-(109.5325, 46.7650) |
| seg add | /Bluetooth/BT_RXD_M | F.Cu | 0.25 | (109.5325, 46.7650)-(108.8825, 46.1150) |
| seg add | /CTRL_SCL | F.Cu | 0.3 | (122.3250, 78.2500)-(121.1750, 78.2500) |
| seg add | /CTRL_SCL | B.Cu | 0.3 | (121.1750, 78.2500)-(120.2250, 79.2000) |
| seg add | /CTRL_SCL | F.Cu | 0.3 | (120.2250, 79.2000)-(117.8750, 81.5500) |
| seg add | Net-(U2-SEL0) | F.Cu | 0.25 | (155.2150, 62.5750)-(155.2150, 60.8250) |
| seg add | Net-(U2-SEL0) | F.Cu | 0.25 | (155.2150, 60.8250)-(152.6650, 58.2750) |
| seg add | Net-(U2-SEL0) | F.Cu | 0.25 | (152.6650, 58.2750)-(151.9150, 58.2750) |
| seg add | Net-(U2-SEL0) | F.Cu | 0.25 | (151.9150, 58.2750)-(151.3650, 57.7250) |
| seg add | Net-(U2-SEL0) | F.Cu | 0.25 | (151.3650, 57.7250)-(151.3650, 55.6750) |
| seg add | /BT_UART_TX | F.Cu | 0.25 | (122.3250, 75.7500)-(123.4250, 75.7500) |
| seg add | /BT_UART_TX | F.Cu | 0.25 | (123.4250, 75.7500)-(124.8750, 74.3000) |
| seg add | /BT_UART_TX | B.Cu | 0.25 | (124.8750, 74.3000)-(117.8750, 67.3000) |
| seg add | /BT_UART_TX | B.Cu | 0.25 | (117.8750, 67.3000)-(116.8250, 67.3000) |
| seg add | /BT_UART_TX | F.Cu | 0.25 | (116.8250, 67.3000)-(115.8250, 68.3000) |
| seg add | /Bluetooth/BT_RXD_M | F.Cu | 0.25 | (109.0025, 46.0000)-(110.9525, 44.0500) |
| seg add | /Bluetooth/BT_RXD_M | B.Cu | 0.25 | (110.9525, 44.0500)-(111.5025, 43.5000) |
| seg add | /Bluetooth/BT_RXD_M | B.Cu | 0.25 | (111.5025, 43.5000)-(111.5025, 34.3500) |
| seg add | /Bluetooth/BT_RXD_M | B.Cu | 0.25 | (111.5025, 34.3500)-(112.4025, 33.4500) |
| seg add | /Bluetooth/BT_RXD_M | B.Cu | 0.25 | (112.4025, 33.4500)-(112.4025, 32.7000) |
| seg add | /Bluetooth/BT_RXD_M | B.Cu | 0.25 | (112.4025, 32.7000)-(111.8525, 32.1500) |
| seg add | /Bluetooth/BT_RXD_M | F.Cu | 0.25 | (111.8525, 32.1500)-(111.8525, 31.0500) |
| seg add | /Bluetooth/BT_RXD_M | F.Cu | 0.25 | (111.8525, 31.0500)-(110.9025, 30.1000) |
| seg add | /MCU/NRST | F.Cu | 0.25 | (129.7500, 82.1750)-(129.7500, 83.3250) |
| seg add | /MCU/NRST | B.Cu | 0.25 | (129.7500, 83.3250)-(129.7500, 79.9250) |
| seg add | /MCU/NRST | F.Cu | 0.25 | (129.7500, 79.9250)-(127.6500, 77.8250) |
| seg add | /MCU/NRST | B.Cu | 0.25 | (127.6500, 77.8250)-(127.0500, 77.2250) |
| seg add | /MCU/NRST | B.Cu | 0.25 | (127.0500, 77.2250)-(127.0500, 71.0750) |
| seg add | /MCU/NRST | B.Cu | 0.25 | (127.0500, 71.0750)-(125.6000, 69.6250) |
| seg add | /MCU/NRST | B.Cu | 0.25 | (125.6000, 69.6250)-(125.6000, 67.9250) |
| seg add | /MCU/NRST | B.Cu | 0.25 | (125.6000, 67.9250)-(126.2500, 67.2750) |
| seg add | /MCU/NRST | B.Cu | 0.25 | (126.2500, 67.2750)-(126.2500, 64.3750) |
| seg add | /MCU/NRST | B.Cu | 0.25 | (126.2500, 64.3750)-(125.0000, 63.1250) |
| seg add | /MCU/NRST | B.Cu | 0.25 | (125.0000, 63.1250)-(123.5000, 63.1250) |
| seg add | /MCU/NRST | B.Cu | 0.25 | (123.5000, 63.1250)-(122.9500, 62.5750) |
| seg add | /MCU/NRST | F.Cu | 0.25 | (122.9500, 62.5750)-(122.1000, 63.4250) |
| seg add | /CTRL_SDA | F.Cu | 0.3 | (138.0000, 97.0000)-(138.0000, 94.8000) |
| seg add | /CTRL_SDA | B.Cu | 0.3 | (138.0000, 94.8000)-(135.3000, 94.8000) |
| seg add | /CTRL_SDA | F.Cu | 0.3 | (135.3000, 94.8000)-(129.6000, 89.1000) |
| seg add | /CTRL_SDA | B.Cu | 0.3 | (129.6000, 89.1000)-(125.8500, 85.3500) |
| seg add | /CTRL_SDA | B.Cu | 0.3 | (125.8500, 85.3500)-(123.5500, 85.3500) |
| seg add | /CTRL_SDA | B.Cu | 0.3 | (123.5500, 85.3500)-(123.0000, 84.8000) |
| seg add | /CTRL_SDA | B.Cu | 0.3 | (123.0000, 84.8000)-(123.0000, 83.6500) |
| seg add | /CTRL_SDA | B.Cu | 0.3 | (123.0000, 83.6500)-(125.5000, 81.1500) |
| seg add | /CTRL_SDA | B.Cu | 0.3 | (125.5000, 81.1500)-(125.5000, 80.4000) |
| seg add | /CTRL_SDA | B.Cu | 0.3 | (125.5000, 80.4000)-(123.8500, 78.7500) |
| seg add | /CTRL_SDA | F.Cu | 0.3 | (123.8500, 78.7500)-(122.3000, 78.7500) |
| via add | /PD_SINK_EN | F-B | 0.6/0.3 | (129.5750, 74.0000) |
| via add | /PD_SINK_EN | F-B | 0.6/0.3 | (137.1250, 62.4000) |
| via add | /BT_AUDIO_R | F-B | 0.6/0.3 | (174.5175, 71.0500) |
| via add | /BT_AUDIO_R | F-B | 0.6/0.3 | (167.3675, 75.6000) |
| via add | GND | F-B | 0.6/0.3 | (167.8850, 76.2740) |
| via add | /BT_AUDIO_L | F-B | 0.6/0.3 | (165.5175, 78.9000) |
| via add | /BT_AUDIO_L | F-B | 0.6/0.3 | (168.1175, 73.5500) |
| via add | GND | F-B | 0.6/0.3 | (168.9600, 73.6610) |
| via add | /Bluetooth/BT_RXD_M | F-B | 0.6/0.3 | (109.5325, 46.7650) |
| via add | /CTRL_SCL | F-B | 0.6/0.3 | (121.1750, 78.2500) |
| via add | /CTRL_SCL | F-B | 0.6/0.3 | (120.2250, 79.2000) |
| via add | /BT_UART_TX | F-B | 0.6/0.3 | (124.8750, 74.3000) |
| via add | /BT_UART_TX | F-B | 0.6/0.3 | (116.8250, 67.3000) |
| via add | /Bluetooth/BT_RXD_M | F-B | 0.6/0.3 | (110.9525, 44.0500) |
| via add | /Bluetooth/BT_RXD_M | F-B | 0.6/0.3 | (111.8525, 32.1500) |
| via add | /MCU/NRST | F-B | 0.6/0.3 | (129.7500, 83.3250) |
| via add | /MCU/NRST | F-B | 0.6/0.3 | (129.7500, 79.9250) |
| via add | /MCU/NRST | F-B | 0.6/0.3 | (127.6500, 77.8250) |
| via add | /MCU/NRST | F-B | 0.6/0.3 | (122.9500, 62.5750) |
| via add | /CTRL_SDA | F-B | 0.6/0.3 | (138.0000, 94.8000) |
| via add | /CTRL_SDA | F-B | 0.6/0.3 | (135.3000, 94.8000) |
| via add | /CTRL_SDA | F-B | 0.6/0.3 | (129.6000, 89.1000) |
| via add | /CTRL_SDA | F-B | 0.6/0.3 | (123.8500, 78.7500) |

### T4: Task 3 manual: U25 FSW (t/pM.json)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg add | Net-(U25-FSW) | F.Cu | 0.2 | (150.3000, 145.9450)-(151.4580, 145.9450) |

### T5: Task 4 batch E (t/pE_f.json)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg add | /Battery_Charger/CE_N | F.Cu | 0.2 | (151.7700, 124.0850)-(151.7700, 125.6350) |
| seg add | /Battery_Charger/CE_N | F.Cu | 0.25 | (151.7700, 125.6350)-(152.3700, 126.2350) |
| seg add | /Battery_Charger/ILIM_HIZ | F.Cu | 0.2 | (153.4200, 123.3850)-(154.0700, 123.3850) |
| seg add | /Battery_Charger/ILIM_HIZ | F.Cu | 0.25 | (154.0700, 123.3850)-(154.6200, 123.9350) |
| seg add | /Battery_Charger/ILIM_HIZ | F.Cu | 0.2 | (154.6200, 123.9350)-(154.6200, 125.4350) |
| seg add | /Battery_Charger/ILIM_HIZ | F.Cu | 0.2 | (154.6200, 125.4350)-(154.0200, 126.0350) |
| seg add | Net-(U24-VREF) | F.Cu | 0.3 | (151.7450, 82.5550)-(151.7450, 81.5050) |
| seg add | Net-(U24-VREF) | F.Cu | 0.3 | (151.7450, 81.5050)-(152.4450, 80.8050) |
| seg add | Net-(U6-~{PDN}) | F.Cu | 0.25 | (107.3450, 127.0550)-(106.9450, 126.6550) |
| seg add | Net-(U6-~{PDN}) | F.Cu | 0.25 | (106.9450, 126.6550)-(106.9450, 122.4050) |
| seg add | Net-(U16-NC) | F.Cu | 0.2 | (99.8600, 87.7875)-(99.8600, 87.0875) |
| seg add | Net-(U16-NC) | F.Cu | 0.2 | (99.8600, 87.0875)-(99.0600, 86.2875) |
| seg add | Net-(U16-NC) | F.Cu | 0.25 | (99.0600, 86.2875)-(99.0600, 84.0375) |
| seg add | Net-(U16-NC) | B.Cu | 0.25 | (99.0600, 84.0375)-(99.0600, 80.8375) |
| seg add | Net-(U16-NC) | B.Cu | 0.25 | (99.0600, 80.8375)-(104.6100, 75.2875) |
| seg add | Net-(U16-NC) | B.Cu | 0.25 | (104.6100, 75.2875)-(104.6100, 74.2375) |
| seg add | Net-(U16-NC) | B.Cu | 0.25 | (104.6100, 74.2375)-(105.3100, 73.5375) |
| seg add | Net-(U16-NC) | F.Cu | 0.25 | (105.3100, 73.5375)-(106.3100, 73.5375) |
| via add | Net-(U16-NC) | F-B | 0.6/0.3 | (99.0600, 84.0375) |
| via add | Net-(U16-NC) | F-B | 0.6/0.3 | (105.3100, 73.5375) |
