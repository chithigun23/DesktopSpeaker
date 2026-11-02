# RT-14: recipes for the last 15 connections (2026-11-03)

Agent "RT-14 recipes for last 15 connections".
- **Input:** `ai-files/pcb/work-route13/RT-13P.*` (RT-13 + AMP_PDN; DRC 0, 15 unconnected, B.Cu over In2 void 273.9 mm).
- **Work folder:** `ai-files/pcb/work-route14/` only. Nothing in `DesktopSpeaker-kicad/`, earlier work folders or `helpers/route_oct*.py` was edited. Nothing committed or published.
- **Result:** `ai-files/pcb/work-route14/RT-14.kicad_pcb` / `.kicad_pro` (= base) / `.kicad_dru` (= RT-13P, byte-identical, SHA-256 c47d6aed...).
- **Method:** text-level edits (`scripts/edit.py`, `mkplan.py`), every build refilled in a separate pcbnew process with the pristine `base.kicad_pro` + `RT-14.kicad_dru` beside it (`scripts/cycle14.sh`). Router `scripts/hr14.py` = hr13 reading `RT-14.kicad_dru` (no code change). Clean build chain RT-13P -> C1 -> C2 -> C3 -> C4 -> C5 -> C6 -> silk tiling -> RT-14 (`scripts/final14.sh`).
- **Not reached:** 0 unconnected. 12 remain; section 5 is the connection-by-connection GUI table. The release material (proposed-project.kicad_dru, release-todo) was therefore **not** written (condition: at most 3).

## Bottom line

- Unconnected (kicad-cli DRC) **15 -> 12**: 3 closures (AMP_FAULT_N at R262/U6-9, AMP_FAULT_N at TP20, U4-QON), **no connection lost** (per-net counts only decrease). DRC **0 violations**.
- Parts moved: **TP20 only** (see 1; the move is longer than the 8 mm figure in the brief, it follows the brief's example location). R262 did not need to move. R242 was moved in a trial and reverted (HA8).
- Rules: `RT-14.kicad_dru` = RT-13P byte-identical. **No rule-21 addition was needed** (AMP_FAULT_N and Net-(U4-QON) are rule-11 nets).
- **B.Cu over In2 void 273.9 -> 284.5 mm** (gate <= 285 met). All 10.6 mm added belong to slow nets (QON 7.3 mm own, side effects on SWDIO / HP_G0 / NRST In2 crossings). **Sensitive nets: 0.0 mm added** (r7 sensitive list byte-identical to RT-13P).
- HA8 failing pairs **121 -> 121** (none new, none tighter). BAT_INT 17.3 mV / 104.0 mW unchanged.

## 1. Parts moved

| ref | RT-13P (x, y, rot) | RT-14 (x, y, rot) | moved | why |
|---|---|---|---|---|
| TP20 | (110.155, 149.645, 0) | (123.900, 111.250, 0) | 40.8 mm | AMP_FAULT_N test point. Within 8 mm of its old spot (south of BKO_U6, between L202/L204/TP10) no lane exists (RT-13 2.6 M nodes). The brief's example "near (112.5, 112.5)" is 37 mm away, so the coordinator decision was read as "relocate north of BKO_U6". New spot is the empty F.Cu field between the AUD_SDA y 108.9 run and the SDATA y 114.6 run, centred on the new AMP_FAULT_N F diagonal (no stub needed). Courtyard clear (SW102 ends y 108.03, L201 starts y 119.06). **Coordinator: confirm the distance.** |

Tried and reverted: **R242** rot 90 at (188.42, 35.0) (2.39 mm) between the J2/J3 courtyards to free R242-2 (AUX_DET): HA8 new pair J2-R242 0.235 mm and R242-J3 tighter (1.295 -> 0.245); AUX_DET did not route anyway (see 5, row 12). R262: the RT-13 target (113.6, 119.8) lies exactly on the LRCK diagonal (x + y = 233.4); not needed (see 2).

gates4: moved ['TP20'], moved_not_allowed [] (allow list TP20), pad_net_diff [] (360 footprints, 1194 pads).
Silk: `scripts/silk_tile13.py` (no data change); `silk_tile_gate` G1-G6 **ALL PASS** (`t/RT-14.silkgate.json`).

## 2. Edits (`t/C1.edit.json` ... `t/C6.edit.json`)

- **C1 - QON fan-out (RT-13 recipe row 14):** GND via (150.77, 124.65) -> (150.72, 124.65); U4-11 GND stub redrawn exact (150.97, 124.085) -> (150.97, 124.25) -> (150.82, 124.4); GND F run at C313-2 shortened to (150.65, 124.4)-(150.65, 125.3), its C111 diagonal (150.65, 127.95)-(149.57, 129.07) deleted (C111-2 keeps its 2 vias; no connection lost); QON pin 12 F w0.2 (151.37, 124.085) -> (151.37, 125.73) -> 0.5/0.2 via (150.95, 126.15) in NECK_U4.
- **C2 - AMP_FAULT_N escape at U6 (hand-drawn, F, w0.2):** R262-2 (111.505, 124.947) -> (112.005, 124.947) -> (112.505, 124.447) -> E y 124.447 -> (115.105, 124.447) -> N x 115.105 between C280 and C271 (pad gap 0.64 mm, 0.22 mm each side) -> (115.105, 120.82) -> NE -> (117.425, 118.5) -> E y 118.5 -> (125.5, 118.5) (out of BKO_U6). Why: the whole U6-9 / R262 group sits in a pocket closed by the LRCK diagonal (W, N) and C280/C271/L201 (E); the only exit is this 0.64 mm pad gap, which the router's sweep margin rejects (needs 0.672). No 3V3_AUDIO, GND or part change.
- **C3 - AMP_FAULT_N to the U3-25 -> U7-9 run (router, void cost 12, via cost 6) + TP20 move:** (125.5, 118.5) via -> In2 x 125.5 -> via (125.5, 112.85) -> F diagonal through the TP20 pad -> via (122.45, 109.8) -> In2 -> via (122.45, 107.0) -> F x 122.45 -> (124.6, 93.65) via -> B y 94.15 -> joins the AMP_FAULT_N B run at (133.545, 93.055). 36.6 mm, 5 vias. The In2 legs pass under the I2S bundle (F, In1 reference unchanged); no via inside the RT-13 BCK corridor (x + y = 242.45 / y 115.8).
- **C4 - QON route (router, void cost 200, In2 shadow 25):** via (150.95, 126.15) -> B/F/In2 north along x 143-157 -> In2 x 156.1 -> F y 22.8 -> QON network at (137.3, 24.6). Hand fix of the router's In2 retrace at the 5V_CODEC In2 trunk: In2 (156.7, 70.95) -> (156.7, 68.5) -> (154.4, 66.2) replaces the In2 run that lay under its own B hop (void -3.6 mm).
- **C5/C6:** exact end joints (AMP_FAULT_N B end onto the x 133.545 run; QON diagonal (139.095, 22.8)-(137.295, 24.6) onto the existing end point) so no new dangling end.

**New copper:** 81 segments, 245.0 mm, **0 not exact 0/45/90** (gates4). New vias 0.6/0.3; one 0.5/0.2 inside NECK_U4.

## 3. Gates (independent of the editing tools; `t/RT-14.gates.txt`)

| gate | RT-13P | RT-14 |
|---|---|---|
| kicad-cli DRC (project library, RT-14 = RT-13P rules) | 0 / 15 unconnected | **0 / 12** |
| connections lost | - | **none** (per-net: AMP_FAULT_N 2 -> 0, U4-QON 1 -> 0, all others equal) |
| footprints / pad nets (360 fp, 1194 pads) | - | TP20 moved only / **pad_net_diff []** |
| locked copper | - | 3776 of 3780 RT-13P items untouched; 4 changed/removed, all in the edit reports (0 unexpected). SHA-256 `5463fd7f6e900e47cdfc148b5ed7db407364d1958a71e26a813c8458796cb9dc` (`t/RT-14.gates.json`) |
| new copper exact 0/45/90 | - | 81 seg, 245.0 mm, **0 not exact** |
| route_oct_check | joints < 90: 0, dangling 63, T 23, exact 100 % | joints < 90 **0**, dangling **63** (none new), T 25, exact **100 %** |
| r7 B.Cu over In2 void | 273.9 | **284.5** (gate <= 285; all added length on slow nets) |
| r7 sensitive B over void | (12 nets, see t/RT-13P.r7.json) | **identical** (0 mm added) |
| r7 BM83 F.Cu in module | GND 2.3, SYS_PWR 2.0 | unchanged; antenna keep-out DRC 0 |
| parcheck (sensitive / slow pairs) | 1 / 9 | 1 / **11**: new slow-slow pairs QON / NRST In2 6.9 mm at 0.203 mm, QON / AMP_PDN B 6.0 mm at 0.279 mm |
| GND stitch distance | 2 over 1.5 mm | unchanged (AUX_L hop 2.77 mm, USB_DP 1.86 mm) |
| pour check | OK | **OK**; non-GND islands: every count unchanged; PVDD_C271_F 4.4 -> 4.2 mm2 (AMP_FAULT neck), VBUS_PD_IN2_G 81.1 -> 81.0 |
| GND islands | In2 59, B 5 | In2 62, B 7; every new piece holds GND vias (`scripts/islanddiff.py`: smallest 1.8 mm2 with 1 via). No floating copper. |
| HA8 | 121 | **121** (0 new, 0 tighter) |
| BAT_INT 6 A | 17.3 mV / 104.0 mW | **unchanged** |
| route_oct sentinel / rule-21 sentinel | fires (81) / PASS | **fires (81)** / **PASS** |
| silk_tile_gate | - | **ALL PASS** |

**Length report** (route_oct_check, whole net):

| net | mm | ratio | vias | note |
|---|---|---|---|---|
| AMP_FAULT_N (whole net, 5 pads) | 162.4 | 1.19 | 11 | complete; was 3 groups |
| Net-(U4-QON) | 199.3 | 1.75 | 12 | slow push-button line (limit 4x) |
| I2S_LRCK / I2S_SDATA | 133.8 / 126.4 | 1.20 / 1.11 | 4 / 0 | unchanged |

## 4. AG13 iteration log (max 3 per task group)

**Group 1 (AMP_FAULT_N, R262/TP20):** 1. router from R262-2: FAIL in 1145 nodes (pocket); free map + debug map show the only exit is the C280/C271 gap at 0.64 mm. 2. hand escape (C2) + router to the net: 32.4 mm / 7 vias, then via cost 6: 36.6 mm / 5 vias (taken). 3. TP20 first placed on the y 118.5 run: courtyard overlap with L201 -> moved onto the C3 diagonal (C3). Done.

**Group 2 (U4: QON, ILIM_HIZ):** 1. QON from the fan-out via: 185.4 mm / 11 vias, void +15.2 (289.8). 2. void cost 40 / 200: 185.9 / 186.6 mm, void 289.0 / 289.3. 3. hand fix of the In2 retrace (C4): 284.5. ILIM_HIZ: router Q101-3 -> U4 group FAIL (2.5 M nodes); analysis in 5, row 5.

**Group 3 (U3 long nets: HP_EN, HP_SEL_B, AUX_DET):** 1. probes from the U3 pins: HP_EN FAIL (0.93 M nodes, region exhausted), HP_SEL_B FAIL (2341 s), AUX_DET from the jack side (R242 trial move + via) FAIL (18.4 M nodes). 2. reverse/debug maps from U3-47 and U3-29: the U3 region is sealed (5, rows 10-12). 3. R242 trial reverted (HA8).

**Group 4 (jack/U24 RC block: C204, C205, USB_AUDIO_L/R, AUD_SCL hook):** 1. hook deleted (A3) + TP18 feed along y 104.5-105.5: FAIL (FB 0.18 M, FBI 0.51 M nodes); USB L/R FAIL (0.8-1.2 M) even with the BT_AUDIO_R T-branch removed. 2. partial hook re-route (B x 163-166 south of BKO_ADC) + C204/C205/USB/BT_R in sequence: with B over In2 GND only, USB_R/L and C205 FAIL; with halo 0.5 and B allowed anywhere, C204 (83.1 mm) and C205 (78.1 mm) route but put **25.4 mm of audio B.Cu over In2 void** (C205 15.3, C204 10.1) -> rejected. 3. USB_R/USB_L with B anywhere route (24.8 / 36.1 mm, 2 vias each) but only after the AUD_SCL hook is gone, which leaves AUD_SCL without a feed -> not integrated.

**Group 5 (AUD_SDA, BCK):** 1. AUD_SDA U24-23 on A3: FAIL (2.5 k nodes, boxed in the BKO_ADC notch). 2. with the RT-13 recipe 3V3_AUDIO via move (150.3, 90.5) -> (150.0, 90.6) and In2 branch at y 90.3: FAIL (5.7 k nodes; the notch B lane west runs over the VBUS_PD In2 trunk, AUD_SDA is sensitive). BCK: analysis only (the recipe needs the VBUS_PD GND windows plus the re-spaced U7 bundle; no copper).

**Group 6 (void gate):** void2in2r found 0.9 mm only; the gate was met by the QON hand fix (above).

## 5. Remaining open connections (12) and GUI actions

Owner routes by hand in 45-degree steps. Audio 0.3 mm / 0.5 mm clearance, B only over In2 GND with a stitch within 1.5 mm; I2S 0.6 mm spacing; slow nets may use In2 (rules 11/21, 0.3 mm from islands). Rows 1-4 and 6-9 are the RT-13 rows, re-verified on RT-14 (unchanged copper there).

| # | from | to | net | verified cause (RT-14) | suggested layer / corridor |
|---|---|---|---|---|---|
| 1 | TP12-1 (146.35, 95.40) | U6-13 (109.50, 126.39) | I2S_BCK | TP12 pocket (LRCK x 142.9 / SDATA x 148.55); In2 under the hub = VBUS_PD trunk | RT-13 row 1 recipe stands: GND window in VBUS_PD_IN2 and _G (x 141.0-145.2, y 95.0-97.8), B hop y 96.6 with stitches, SW on x + y = 238.5, cross SDATA at (136.5-137.5, 101.5-104), corridor x + y = 242.45 -> W y 115.8 -> SW x + y = 232.19 -> U6-13. The new AMP_FAULT_N copper stays clear of it (In2 under the bundle only; vias at (125.5, 117.95) and (122.45, 107.0-109.8) are outside the corridor). |
| 2 | U7-13 (192.29, 126.39) | BCK stub (147.15, 93.75) | I2S_BCK | CHG_ENABLE / CHG_SYS_ENABLE B y 93.4 / 94.2 and VBUS_PD trunk close the lane east of R207; U7 bundle 0.92 mm | RT-13 row 2 recipe (CHG_* B to y 92.6 / 91.8, trunk window x 147.4-149.3, B hop, re-spaced U7 diagonals, AMP_FAULT diagonal to x - y = 82.2). |
| 3 | U24-23 (150.75, 88.28) | AUD_SDA (139.05, 81.00) | AUD_SDA | boxed in the BKO_ADC notch; with the 3V3 via moved per recipe the notch B lane west runs over the VBUS_PD In2 trunk (not GND) | via (150.75, 91.3) in the notch after the 3V3 via move, then **In2** (rule 11 allows AUD_SDA on In2) west under the hub to a via at the AUD_SDA run (136.2, 89-100) - or open a GND window in VBUS_PD_IN2 along the B path (as BCK row 1) and stitch. |
| 4 | U7-15 (191.29, 126.39) | U24-23 | AUD_SDA | needs row 3; 60 mm through the U7 bundle | F parallel to the AUD_SCL U7 branch at 0.6 mm, inside the re-spaced bundle of row 2. |
| 5 | Q101-3 (180.96, 110.73) | U4-17 group (153.42, 123.39) / R108-2 | ILIM_HIZ | pin 17 is between TS_SENSE (16) and BATP (18), whose B pair runs together to x 164-172 (edge gaps 0.585 at y 127, 0.45 at y 116); F around the group is closed by SW2 (1.0 mm switch rule, C110-2 and via (155.6, 126.2)) and R108-1/REGN; In2 under U4 = BAT_INT/SYS_RAW/VBUS_PD islands; router FAIL 2.5 M nodes | Re-route the **TS_SENSE B section** off the pair: from R100-2 a new via south of the SYS_RAW via rows, B y ~131.6 under H3's south side to x 172.4, north on x 172.4 to (172.4, 116.05) (existing TS run), delete the old pair section (153.47..172.4). Then ILIM: 0.5/0.2 via at (154.05, 124.9) (NECK_U4), B x 154.1 south to y ~130.7, east south of the SYS_RAW vias, via up east of H3 into the free F field (x 163-183, y 123-131), F north to Q101-3. TS_SENSE is a sense net: keep its new B run over In2 GND (check r7). |
| 6 | R204-1 (156.35, 90.73) | C204-2 (191.14, 40.17) | C204-Pad2 | R204-1 boxed by the AUD_SCL hook (F x 158.025 / y 91.8 run inside BKO_ADC, no B allowed there) | Hook must go: re-route the AUD_SCL south part on B east of BKO_ADC (via (163.025, 79.85) -> B (166.0, 82.85)-(166.0, 88.45)-(159.9, 94.6) -> F/B to via (156.5, 92.8); router found it, 26.2 mm, 4 vias, plan `t/p4/p_v1.json`). C204/C205 then cross it on F, but their only routes found put 10-15 mm of audio on B over In2 void: the owner must either open GND under the hops (In2 5V_CODEC trunk x + y = 238.25 region) or route them F-only NE between the mux and the jack (move slow HP_SEL_A / HP_G0 / HP_G1 F runs at y 66-69 to In2 locally first). |
| 7 | R205-1 (156.95, 89.28) | C205-2 (192.89, 42.37) | C205-Pad2 | as 6 | parallel to 6 at 0.6 mm. |
| 8 | C200-1 (162.02, 79.00) | USB_AUDIO_L (174.55, 60.88) | USB_AUDIO_L | sealed by the AUD_SCL hook (y 71.75 run, B x 163.0) and the BT_AUDIO_R T-branch (165.53, 75.6-77.47) / BT_AUDIO_L F y 69.92 walls; with B over GND only no path (1.2 M nodes) | Only after row 6's hook re-route. Then delete the BT_AUDIO_R T-branch to C203 and route USB_R, USB_L, BT_R as nested bands (router found USB_R 24.8 mm / USB_L 36.1 mm / BT_R 8.3 mm, `t/p3/p_rlb3.json`, with B hops at x 161.5 and x 164-172.8 that need In2 GND under them: check and stitch). |
| 9 | C201-1 (162.02, 77.65) | USB_AUDIO_R (168.75, 56.43) | USB_AUDIO_R | as 8 | as 8 (innermost band). |
| 10 | U3-47 (124.75, 70.83) | U10-13 (197.04, 63.78) | HP_EN | U3 is sealed on the NE by a 3-layer diagonal wall at x + y = 199-206: F PD_PLUG_EVENT (202.6), SWDIO (203.8), BT_AUDIO_L (205.8); B PDCTRL_SDA (200.9), PD_SINK_EN (203.5), HP_DET (204.9); In2 5V_LOGIC 2.0 mm (198.9), HP_SEL_A (207.3); the router exhausts the U3-side region at 0.93 M nodes | Move PD_SINK_EN and HP_DET B (rule-11 slow nets) to In2 or F locally around (134-136, 66-70) to open a 1.3 mm via channel, then HP_EN: U3-47 F south under the body to a via at about (124.9, 73.5) (yellow via site in the free map), In2 east through the opened channel, then the 3V_AO corridor (In2 north of the USB_VBUS block y 44.5-45.5, B over the USB_VBUS column y 55-58) to U10-13. |
| 11 | U3-51 (122.33, 73.75) | R235-1 (183.40, 58.70) | HP_SEL_B | as 10 (router FAIL, 2341 s) | parallel to 10 at 0.6 mm; U3-51 west-column exit under the body (BT_TX_IND takes the west lane). |
| 12 | U3-29 (133.68, 74.25) | R242-2 (189.82, 36.30) | AUX_DET | both ends sealed: U3-29 sits between AUD_SCL F y 73.75 and HP_DET F y 74.75 (0.5 mm pitch, 0.725 mm free) with AMP_BOOST_EN B x 134.37 beside it, no via site; R242-2 is inside the AUX_TIPSW loop | U3 end: escape west under the U3 body to a via, then as 10. Jack end: R242 rot 90 between J2/J3 frees R242-2 but gives an HA8 pair at 0.235 mm; instead move R242 2.8 mm west as RT-13 row 16 only after re-placing the 3V_AO via (187.72, 38.65) (the column between HP_OUTR and the AUX_TIPSW vertical has no legal via site: audio 0.5 mm on both sides). |

## 6. Coordinator quality items (brief item 5)

- CTRL_SCL / CTRL_SDA 0.20 mm (NECK_U4 fan-out) and 3V_AO / HP_DET 0.25 mm: **unchanged** (not cheap: the U4 fan-out is pin-pitch limited; 3V_AO shares the jack corridor that rows 10-12 need).
- AUX_L hop via without a stitch within 1.5 mm: **unchanged**; checked sites north of R224 (best 1.63 mm) and south (VMID F at 0.11 mm) - no legal site.
- CC2 8 vias, HP_R ratio 1.83, ADC_INT 35.6 mm: **unchanged** (not touched this round).

## 7. Hand-assembly note

C215-C212 are 0.14 mm apart (unchanged). Place C215 and C212 first, before U24 and Y200. TP20 now sits at (123.9, 111.25) on F with no neighbour closer than its courtyard.

## 8. Files (`ai-files/pcb/work-route14/`)

- **Result:** `RT-14.kicad_pcb`, `RT-14.kicad_pro` (= base), `RT-14.kicad_dru` (= RT-13P), `RT-14.drc.json`, `RT-14.geo.json`.
- **Gates:** `t/RT-14.gates.txt`, `t/RT-14.gates.json` (locked manifest, new-copper list), `t/RT-14.check.json/.txt`, `t/RT-14.r7.json`, `t/RT-14.par.json`, `t/RT-14.ha8.json`, `t/RT-14.cp.json`, `t/RT-14.rulehash.txt`, `t/RT-14.silkgate.json`, `sentinel/`; baseline `t/RT-13P.*`.
- **Build chain:** `t/b1/b1.json` (C1), `t/a2/a2.json` (C2), `t/a4/a4.json` (C3), `t/c4/c4.json` (C4), `t/c5`, `t/c6`; edit reports `t/C1.edit.json` ... `t/C6.edit.json`.
- **Probes and logs:** `t/p1` ... `t/p6` (router jobs, logs, debug maps `t/p1/dbg_fault.png`, `t/p2/dbg_hpen.png`, `t/p2/dbg_aux.png`, `t/p3/dbg_sda.png`); trial builds A1-A6, A3b, A5*, X1 (not results).
- **Scripts (new/changed copies):** `cycle14.sh`, `gates14.sh` (baseline RT-13P), `final14.sh`, `hr14.py` (= hr13, reads RT-14.kicad_dru), `sentinel21_14.sh`, `render14.sh`, `crops14.sh`.
- **Evidence:** `evidence/rt14-F.png`, `rt14-B.png`; crops `rt13p-` / `rt14-fault.png`, `-u4qon.png`, `rt14-qon.png`.
- **Size:** trial boards and geo exports (about 0.33 GB); do not commit them.
