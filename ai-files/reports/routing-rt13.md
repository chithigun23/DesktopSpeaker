# RT-13: final automated routing round (2026-11-03)

Agent "RT-13 final automated routing round".
- **Input:** `ai-files/pcb/work-route12/RT-12.*` (DRC 0, 26 unconnected).
- **Work folder:** `ai-files/pcb/work-route13/` only. Nothing in `DesktopSpeaker-kicad/`, earlier work folders or `helpers/route_oct*.py` was edited. Nothing committed or published.
- **Result:** `ai-files/pcb/work-route13/RT-13.kicad_pcb` / `.kicad_pro` (= base) / `.kicad_dru` (= RT-12, byte-identical).
- **Method:** text-level edits (`scripts/edit.py`), every build refilled in a separate pcbnew process with the pristine `base.kicad_pro` + `RT-13.kicad_dru` beside it (`scripts/cycle13.sh`). Router `scripts/hr13.py` = hr12 reading `RT-13.kicad_dru` (no code change); probes used its existing `island_via` / `block` / `void_cost` options. New helper scripts in section 7.
- **Not reached:** 0 unconnected. 16 remain; section 5 is the connection-by-connection GUI table. The release material was therefore **not** written (16 is not "a handful"); `schematic-patch.md` holds the proposals the brief allows.

## Bottom line

- Unconnected (kicad-cli DRC) **26 -> 16**: 10 closures, **no connection lost** (per-net counts only decrease). DRC **0 violations**.
- Closed: 5V_LOGIC_EN (R142), Q101-G, USB_CC1, USB_CC2, CTRL_SCL (U4-14), AUX_L, C235-Pad2 x2, AMP_FAULT_N (U3-25 <-> U7-9), 3V_AO (R241).
- Parts moved (2, both in the allowed list): R142 2.42 mm, R225 5.79 mm. HA8 failing pairs **121 -> 121** (none new, none tighter).
- Rules: `RT-13.kicad_dru` = RT-12 byte-identical (SHA-256 c47d6aed...). **No rule-21 addition was needed**: every In2 use is by rule-11 nets (CTRL_SCL, CTRL_SDA, AMP_FAULT_N, AUD_SCL/SDA, BT_*, CHG_*, HP_*, PD*, ENC_*, TS_SENSE, GAUGE_ALRT_N) or rule-21 nets (HP_G0, U12-EN) or the PWR_3V class (3V_AO).
- **B.Cu over In2 void 264.7 -> 264.7 mm** (gate <= 265 met exactly). The 10 new routes added about 24 mm; it was paid back by moving 40 B.Cu segments (via-to-via chains of 22 slow rule-11/21 nets) onto In2 on the same polyline (`scripts/void2in2r.py`, connectivity- and island-checked, section 2 D1).
- **Variant with AMP_PDN (owner's choice):** `RT-13P.kicad_pcb` = RT-13 + a router AMP_PDN route R258-1 -> AMP_PDN (99.2 mm, 10 vias, F 37.6 / B 34.3 / In2 27.3 mm). DRC 0, **15 unconnected**, same moves, gates4 clean, but B.Cu over In2 void **273.9 mm (gate missed by 8.9 mm**: 6.6 mm own via antipads and B legs, 2.6 mm side effect of its In2 run under CTRL_SDA/AMP_BOOST_EN). Not the delivered result; no In2 move was left to repay it (only 1.8 mm).
- **Release material:** not produced (condition not met). C215-C212 (0.14 mm) remains the hand-assembly item (section 6).

## 1. Parts moved

| ref | RT-12 (x, y, rot) | RT-13 (x, y, rot) | moved | why |
|---|---|---|---|---|
| R142 | (91.930, 97.420, 180) | (91.900, 95.000, 180) | 2.42 mm | R142-1 was enclosed by the U14-FB loop. North of the loop pin 1 runs F (92.50, 95.0) -> (93.975, 95.0) -> (93.975, 98.2) onto the 5V_LOGIC_EN run; pin 2 to a new GND via (90.30, 95.0) in the In2 GND pour west of the SYS_RAW trunk. Placed 0.4 mm north of first trial to keep the board text "5V_LOGIC" clear (silk DRC). |
| R225 | (189.740, 40.370, 90) | (194.400, 43.800, 180) | 5.79 mm | R225-1 was sealed by the VMID F loop. New spot: pin 1 straight under C235-2 (F x 195.0), pin 2 joins VMID_HP on its diagonal (x - y = 147.0575) by a 2.1 mm stub. |

gates4: moved ['R142', 'R225'], moved_not_allowed [], pad_net_diff [] (360 footprints, 1194 pads).
Silk: `scripts/silk_tile13.py` = `silk_tile12.py` (no data change); `silk_tile_gate` G1-G6 **ALL PASS** (`t/RT-13.silkgate.json`).

## 2. Edits (build chain RT-12 -> A1 -> A2 -> A3 -> A4 -> A5 -> B0 -> B1 -> C2 -> C3 -> C4 -> D0 -> D1 -> RT-13)

Edit reports `t/<stem>.edit.json`; plans in `t/a1` ... `t/d1` (`base.py` / `base.json`).

- **A1:** R142 move + 5V_LOGIC_EN (above). **Q101-G:** Q102-3 -> F (180.4, 107.222) -> via -> B x 180.4 under AUD_SCL -> via (180.4, 109.785) -> F -> Q101-1 (7.5 mm, ratio 1.44). TS_SENSE B y 108.35 jogs to y 110.6 between x 176.6 and 184.2 (same In2 BAT_PACK under it) to let the hop pass.
- **A2: U4 bottom row fan-out** in NECK_U4 (0.2 mm rules, 0.5/0.2 vias): CTRL_SDA pin 15 now jogs SE to a via (152.85, 124.95) and runs B north-west under the pin row along y 124.0 into its old diagonal; CTRL_SCL pin 14 drops to a via (152.33, 125.55). (A QON fan-out was also built here and reverted in D0, see 5.)
- **A3 / B1: CC1, CC2, CTRL_SCL** by the router (`island_via`: vias may pass the In2 USB_VBUS island; BAT_INT, VBUS_PD, SYS_RAW stay forbidden). CC1 31.5 mm / CC2 36.3 mm for the new legs (B hops under the caps and under the USB DP/DN pair at x 143.4-145.75, In2 GND there); CTRL_SCL 54.2 mm, 5 vias, south of U4 then F/B north-west to TP16.
- **A4:** ILIM_HIZ via + TS_SENSE shift (both reverted in D0, see row 9 of section 5).
- **A5: jack east half.** AUX_R: the redundant F loops around C235-2 (11 segments) removed; D201-2 keeps its x 196.04 run to the J3-2 via, the C235-1/C205-1 B pair is tied to D201-2 by a 0.83 mm F stub. R225 move. C235-Pad2: C235-2 -> R225-1 (F x 195.0), R225-1 -> F x 195.4 south (outside VMID) -> B y 55.5 under VMID / HP_OUTL / HP_OUTR / C234-Pad2 -> F -> R231-1 (25.9 mm net, ratio 1.29), GND stitches (196.3, 55.5), (192.6, 56.4), (186.3, 54.4). AUX_L: router B hop C204-1 -> D201-1 (6.2 mm leg).
- **B0/B1:** CC/SCL re-run with a high void cost (same CC result; SCL kept from A2 router run).
- **C2: AMP_FAULT_N U3-25 -> U7-9**, router 105.7 mm (ratio ~1.30), 6 vias, F/B/In2, run with a block box over the I2S hub (x 138.5-150.5, y 93-99) so the planned BCK B hop stays free (section 5 row 6).
- **C3/C4: 3V_AO** in two legs (single searches exhausted 8-12 M nodes): R241-1 -> F/B west along y 39.5 -> B diagonal to (149.5, 55.2) and from there B/F north of the In2 USB_VBUS block (B y 45.15) -> In2 west of U3 -> 3V_AO network at (117.05, 72.25). About 111 mm, 7 vias, w 0.25 (pull-up supply).
- **D0:** exact-end fixes (AUX_R ends on the J3-2 via and the D201-2 diagonal end; 3V_AO legs joined end to end); QON and ILIM preparations reverted (vias + TS shift + GND tweaks restored byte-identical).
- **D1 (void repair):** 40 B.Cu segments (via-to-via chains, 22 rule-11/21 nets) moved to In2 on the same polyline where In2 is free (0.22 mm to In2 tracks/vias, 0.33 to non-GND islands). Excluded after checking: chains with a T-branch, chains whose end via would lose its F link, one BT_UART_TX chain that cut a GND island (ENC_A void +4.9) and the AUD_SCL x 163.0 chain (SWCLK void +1.7).

**New copper:** 156 segments, 511.4 mm, **0 not exact 0/45/90** (gates4). New vias 0.6/0.3, 0.5/0.2 inside NECK_U4 only.

## 3. Gates (independent of the editing tools; `t/RT-13.gates.txt`)

| gate | RT-12 | RT-13 |
|---|---|---|
| kicad-cli DRC (project library, RT-13 = RT-12 rules) | 0 / 26 unconnected | **0 / 16** |
| connections lost | - | **none** (per-net: only decreases) |
| footprints / pad nets (360 fp, 1194 pads) | - | R142, R225 moved only / **pad_net_diff []** |
| locked copper | - | 3540 of 3595 RT-12 items untouched; 55 removed/changed, all in the edit reports (0 unexpected). SHA-256 `926f43de8afc8dc5826e1194fc5a1a0b21d01bba32d243a529c3c05fc1ac71fa` (`t/RT-13.gates.json`) |
| new copper exact 0/45/90 | - | 156 seg, 511.4 mm, **0 not exact** |
| route_oct_check | joints < 90: 0, dangling 63, T 21, exact 100 % | joints < 90 **0**, dangling **63** (none new), T 23, bend-short 45, pad-exit-short 17, exact **100 %** |
| r7 B.Cu over In2 void | 264.7 | **264.7** (gate <= 265) |
| r7 sensitive B over void | AUD_SCL 3.4, AUD_SDA 3.5, AUX_L 1.8 | AUD_SCL 1.6, AUD_SDA 2.7, AUX_L 2.7 (new hop), others unchanged |
| r7 BM83 F.Cu in module | GND 2.3, SYS_PWR 2.0 | unchanged; antenna keep-out DRC 0 |
| parcheck (sensitive / slow pairs) | 1 / 7 | **1 / 9**: new slow pairs CTRL_SCL/CTRL_SDA 3.1 mm at 0.20 (inside NECK_U4 fan-out) and 3V_AO/HP_DET 3.2 mm at 0.25 |
| GND stitch distance | | 2 vias over 1.5 mm: AUX_L hop via (190.59, 38.48) 2.77 mm (no stitch site in the jack cluster; the D201 end has stitches at 0.88/1.25 mm) and USB_DP (unchanged) |
| pour check | OK | **OK**; non-GND islands: every island count unchanged; USB_VBUS area 289.0 -> 285.5 mm2 (CC via antipads), BAT_PACK 826.7 -> 824.4 |
| GND islands | GND_IN2_BG 54 | 58; every new/changed piece holds GND vias (`scripts/islanddiff.py`; smallest 0.3 mm2 ring with 1 via). No floating copper. |
| HA8 | 121 | **121** (0 new, 0 tighter) |
| BAT_INT 6 A | 17.3 mV / 104.0 mW | **unchanged** |
| route_oct sentinel / rule-21 sentinel | fires (81) / PASS | **fires (81)** / **PASS** (`scripts/sentinel21_13.sh`) |
| silk_tile_gate | ALL PASS | **ALL PASS** |

**Length report** (route_oct_check, whole net; ratio = length / octilinear minimum):

| net | mm | ratio | vias | note |
|---|---|---|---|---|
| 5V_LOGIC_EN | 61.1 | 1.16 | 2 | |
| Q101-G | 7.5 | 1.44 | 2 | |
| USB_CC1 / USB_CC2 | 42.6 / 56.3 | 1.24 / 1.56 | 6 / 8 | Default class, B hops over In2 GND under DP/DN |
| CTRL_SCL / CTRL_SDA | 110.3 / 109.4 | 1.41 / 1.27 | 12 / 12 | |
| AUX_L | 22.1 | 1.48 | 3 | audio, B hop 2.9 mm over In2 GND |
| C235-Pad2 | 25.9 | 1.29 | 2 | audio, B 9.5 mm over In2 GND, 3 stitches |
| VMID_HP | 75.5 | 1.20 | 8 | R225 stub |
| AMP_FAULT_N (U3-25 -> U7-9 leg) | 105.7 | about 1.30 | 6 | net still incomplete (R262/U6, TP20) |
| 3V_AO (R241 leg) | about 111 | about 1.3 | 7 | slow pull-up supply |
| TS_SENSE | 80.6 | 1.25 | 2 | +1.9 mm jog under Q101 |
| HP_R / ADC_INT | 13.7 / 35.6 | 1.83 / 1.61 | 2 / 2 | unchanged (blocked by the same I2S/hub knot as BCK) |

## 4. AG13 iteration log (max 3 per task group)

**Group 1 (local closures: R142, Q101-G, AUX_L, C235):** 1 build each (A1, A5), 1 silk fix (R142 y 95.4 -> 95.0). Done.

**Group 2 (U4 charger: CTRL_SCL, QON, ILIM_HIZ):**
1. Fan-out A2 (0.45 vias rejected by the 0.15 annular rule, rebuilt with 0.5/0.2). SCL routed.
2. QON: 139.9 mm / 10 vias, then (void cost 12) 143.5 mm / 12 vias adding 11.7 mm B over void; (U3-west B blocked, void cost 25) 206.6 mm / 15 vias. Not integrated: the void gate cannot absorb it. Fan-out reverted.
3. ILIM_HIZ: via between TS_SENSE and BATP + TS shift (A4); router exp 10 k: the only exit is the 0.8 mm lane between BATP and TS, which does not survive their turn north at x 164 (0.9 mm apart). Reverted.

**Group 3 (U3 long nets: AMP_FAULT_N x3, AMP_PDN, HP_EN, HP_SEL_B, AUX_DET):**
1. Probes on A2 (8 M nodes): only U7-9 -> U3-25 succeeded (27 min).
2. Re-run with the hub blocked (C2, 16 M): AMP_FAULT U3-U7 integrated. R262-2 analysed by hand (no lane, section 5 row 5); TP20 2.6 M nodes.
3. Final runs on C2/C3/D1 (16-25 M nodes, U3 body open): AMP_PDN OK twice (84.5 mm / +10.1 mm void; void cost 30: 99.2 mm / +9.2 mm void) -> variant RT-13P only; HP_EN FAIL (18.9 M nodes, mux -> U3-47); HP_SEL_B FAIL (15.3 M, R235 -> U3-51); AUX_DET FAIL (0.77 M, R242-2 sealed).

**Group 4 (jack cluster: AUX_L, C235 x2, C204, C205, 3V_AO, AUX_DET):** 1. A5 (AUX_R clean-up, R225, C235, AUX_L). 2. Escape probes after A5: C204/C205/3V_AO leave the cluster; AUX_DET still sealed (exp 6). 3. 3V_AO in two legs (C3/C4). C204/C205 are sealed at the U24 end (R204-1/R205-1 inside BKO_ADC, boxed by AUD_SCL), not at the jack.

**Group 5 (I2S BCK, AUD_SDA, USB_AUDIO):** analysis only (section 5): all are blocked by the same two knots (the I2S hub and the AUD_SCL hook around the U24 input RC block); no copper.

**Group 6 (void gate):** 3 rounds: In2 moves (void2in2), safety pass (T-branch / F-link / island side effects), exclusion of 2 moves with side effects. 289.1 -> 264.7.

## 5. Remaining open connections (16) and GUI actions

Owner routes by hand in 45-degree steps. Audio 0.3 mm, 0.5 mm clearance, B only over In2 GND, stitch within 1.5 mm. I2S 0.6 mm spacing. Slow nets may use In2 (rules 11/21, 0.3 mm from islands).

| # | from | to | net | verified cause | suggested layer / corridor |
|---|---|---|---|---|---|
| 1 | TP12-1 (146.35, 95.40) | U6-13 (109.50, 126.39) | I2S_BCK | TP12 pocket boxed by LRCK (x 142.9) / SDATA (x 148.55); In2 under the hub is the VBUS_PD trunk; then the lane NW of SDATA is taken by AUD_SDA (x + y = 238.5) and the SDATA/LRCK/AUD_SDA hop knot at (136-139, 100-105) | (a) Cut a GND window in VBUS_PD_IN2 **and** VBUS_PD_IN2_G east edge: x 141.0-145.2, y 95.0-97.8 (trunk keeps x 145.2-149.3). (b) F (144.8, 96.0) -> (144.2, 96.6) via, B y 96.6 to via (141.6, 96.6), stitches (143.7, 95.5), (141.6, 95.6). (c) F S to (141.6, 96.9), SW on x + y = 238.5 (0.51 mm from TP15, 0.77 from LRCK). (d) Cross SDATA at about (136.5-137.5, 101.5-104): move GND stitch (136.899, 101.801), re-do the AUD_SDA B hop 0.6 mm west. (e) F on x + y = 242.45 (mid-corridor between SDATA 239.75 and LRCK 245.15) to (126.65, 115.8), W y 115.8 to 116.39, SW x + y = 232.19 to (109.505, 122.685), S into U6-13 (0.6 mm to SDATA and LRCK at the pins). Length-match LRCK/SDATA +-2 mm. |
| 2 | U7-13 (192.29, 126.39) | BCK stub (147.15, 93.75) | I2S_BCK | Hub east: CHG_ENABLE / CHG_SYS_ENABLE B runs at y 93.4 / 94.2 (x 135-154) and the VBUS_PD trunk close the B lane east of R207; U7 bundle SDATA/LRCK 0.92 mm apart | Move CHG_ENABLE/CHG_SYS_ENABLE B (rule-11 nets) to y 92.6 / 91.8 locally; second trunk window x 147.4-149.3, y 92.8-94.0; B hop from a via on the BCK stub corner (147.15, 93.75) to (150.6, 93.75). East along SDATA's y 93.7 run, then re-space the bundle: diagonals SDATA x - y = 78.4, BCK 79.6, LRCK 80.8 (LRCK B-hop via to (182.7, 101.9)); **also move the new AMP_FAULT diagonal from x - y = 80.95 to 82.2** and its vertical to x 194.4. |
| 3 | U24-23 (150.75, 88.28) | AUD_SDA (139.05, 81.00) | AUD_SDA | U24-23 under the 3V3_AUDIO via (150.30, 90.50) and AUD_SCL; freevia 0 sites | Move the 3V3 via to (150.0, 90.6) and its In2 east branch to y 90.3 (In2 (150.0, 90.6) -> (150.3, 90.3) -> (152.8, 90.3) -> (153.4, 90.9)); AUD_SDA F x 150.745 down to a 0.6/0.3 via (150.75, 91.3) in the BKO_ADC notch; B over In2 GND west to the AUD_SDA network. |
| 4 | U7-15 (191.29, 126.39) | U24-23 | AUD_SDA | needs row 3 first; 60 mm, U7 bundle | F parallel to AUD_SCL (its route via (157.3, 92.75) -> (166.85, 102.3) -> y 106.0 -> U7) at 0.6 mm; vertical x 190.75 into U7-15 within the re-spaced bundle of row 2. |
| 5 | R262-2 (111.50, 124.95) | AMP_FAULT_N B (138.54, 99.05) | AMP_FAULT_N | R262 boxed: a lane between the LRCK diagonal and R262-1 needs x + y >= 234.32 and <= 234.12 (none); R262 not movable in RT-13 | Move R262 about 2.5 mm NE to (113.6, 119.8) (schematic-patch P2), then F north-east to y 113.5 (out of BKO_U6), via, In2/B to the U3-U7 AMP_FAULT run at (129.75, 87.25). |
| 6 | TP20-1 (110.16, 149.65) | AMP_FAULT_N (111.50, 124.95) | AMP_FAULT_N | south of BKO_U6, between L202/L204 and TP10, In2 PVDD | Delete TP20 or move it north of BKO_U6 (schematic-patch P1). |
| 7 | R258-1 (185.60, 113.00) | AMP_PDN (137.47, 78.00) | AMP_PDN | routable (RT-13P, plan `t/e1/p_pdn2.json`) but +9.2 mm B over void breaks the 265 mm gate | Take the RT-13P copper and repay about 9 mm of void elsewhere (e.g. move the SWCLK B diagonal (157.7, 74.7)-(162.1, 79.1), 5 mm over void, to F after re-routing HP_G1 locally), or accept the gate overrun. |
| 8 | U3-47 (124.75, 70.83) | U10-13 (197.04, 63.78) | HP_EN | router 18.9 M nodes, no path (mux side to U3 top row) | As 3V_AO: In2 north of the USB_VBUS block (y 44.5-45.5, x 131-146) and B over the USB_VBUS column at y 55-58 to x 152, then F north of BKO_MUX along y 56-57 to R236/U10-13. U3 side: top-row escape north under the U3 body (LQFP, F allowed). |
| 9 | Q101-3 (180.96, 110.73) | U4-17 track (154.07, 123.39) | ILIM_HIZ | ILIM pin column fenced by SW2 (1.0 mm switch rule), BTST2/PROG, and the TS_SENSE/BATP B pair (0.85-1.05 mm apart to x 164) | Re-route TS_SENSE from U4-16 west of R103 (F to R100, B south of the SYS_RAW via row y 129.8) so the BATP/TS pair separates; then via (154.0, 124.9) (0.5/0.2, NECK_U4), B x 154.0 south, east along y 127.5 to x 165.5, north outside the BATP run to (173.0, 116.0), east of the BAT_PACK via array (x >= 177.4) to via (181.0, 111.8), F into Q101-3. Alternative: schematic-patch P3. |
| 10 | R204-1 (156.35, 90.73) | C204-2 (191.14, 40.17) | C204-Pad2 | R204-1 inside BKO_ADC, boxed by the AUD_SCL hook (163.0, 82.3) -> (158.0, 87.3) -> (156.9, 91.8) | Re-route AUD_SCL: delete the hook from (140.075, 71.75) to (158.0, 90.7) and feed U24/U7 from TP18 (134.25, 102.0) along y 104.5-105.5 (between LRCK y 103.8 and SYS_RAW y 106.0, B under LRCK x 139.1); then C204/C205/USB_AUDIO leave the RC block to the north-east on F (jack leg probes: `t/p2/p2.json`, `p3.json`). |
| 11 | R205-1 (156.95, 89.28) | C205-2 (192.89, 42.37) | C205-Pad2 | as 10 | parallel to 10 at 0.6 mm |
| 12 | C200-1 (162.02, 79.00) | USB_AUDIO_L (174.55, 60.88) | USB_AUDIO_L | AUD_SCL hook + BT_AUDIO_R wall (162.7, 80.3) -> (165.5, 77.5) -> (165.5, 73.8) -> via (162.63, 70.87) | after row 10: rip BT_AUDIO_R/BT_AUDIO_L RC-to-mux runs and re-route the four RC outputs as nested bands NE (USB_R innermost), F only, In2 5V_CODEC trunk (x + y = 238.25) under them is F-only territory |
| 13 | C201-1 (162.02, 77.65) | USB_AUDIO_R (168.75, 56.43) | USB_AUDIO_R | as 12 | as 12 |
| 14 | U4-12 (151.37, 124.08) | QON (135.25, 25.00) | U4-QON | routable but costs 11.7 mm B over void (gate) | Fan-out: GND via (150.77, 124.65) -> (150.72, 124.65), shorten the GND F run at C313-2 (C111-2 keeps its 2 vias), pin 12 F to a 0.5/0.2 via (150.95, 126.15); then mostly In2 west of the VBUS_PD trunk (router plan `t/b1/pQ.json`, 143.5 mm). Repay the void (e.g. In2 moves with via deletion, `scripts/void2in2v.py`). |
| 15 | U3-51 (122.33, 73.75) | R235-1 (183.40, 58.70) | HP_SEL_B | router 15.3 M nodes, no path; U3-51 west-column exit taken by BT_TX_IND (RT-12) | parallel to row 8 at 0.6 mm (In2), U3 west-column exit under the body. |
| 16 | U3-29 (133.68, 74.25) | R242-2 (189.82, 36.30) | AUX_DET | R242-2 sealed by the AUX_TIPSW loop | Move R242 2.8 mm to (187.6, 36.2) rot -90 (pin 1 to the AUX_TIPSW corner (188.42, 35.953)); AUX_DET F down x 187.6 to a via at (187.75, 39.75) (0.53 mm to R241-1, 0.575 to HP_OUTR), then the 3V_AO corridor (B y 38.65 / F y 39.5 / B diagonal) at 0.6 mm, and In2 to U3-29. |

## 6. Hand-assembly note

C215-C212 are 0.14 mm apart (unchanged). Place C215 and C212 first, before U24 and Y200.

## 7. Files (`ai-files/pcb/work-route13/`)

- **Result:** `RT-13.kicad_pcb`, `RT-13.kicad_pro` (= base), `RT-13.kicad_dru` (= RT-12).
- **Variant:** `RT-13P.kicad_pcb` / `.drc.json` (+ AMP_PDN, void gate missed), `t/RT-13P.gates.json`, `t/RT-13P.r7.json`.
- **Gates:** `t/RT-13.gates.txt`, `RT-13.drc.json`, `t/RT-13.gates.json` (locked manifest, new-copper list), `t/RT-13.check.json/.txt`, `t/RT-13.r7.json`, `t/RT-13.par.json`, `t/RT-13.ha8.json`, `t/RT-13.cp.json`, `t/RT-13.rulehash.txt`, `t/RT-13.silkgate.json`, `sentinel/RT-13_sentinel.*`, `sentinel/S21*`.
- **Proposals:** `schematic-patch.md` (TP20, R262, ILIM_HIZ).
- **Plans and logs:** `t/a1` ... `t/d1`, `t/<stem>.edit.json`; probes `t/p1` ... `t/p5`, `t/a2`, `t/b1`, `t/c2`, `t/c3`.
- **Scripts (new):** `cycle13.sh`, `gates13.sh`, `final13.sh`, `hr13.py` (= hr12, reads RT-13.kicad_dru), `probe13.py`, `void2in2.py` / `void2in2r.py` / `void2in2v.py`, `void2f.py`, `voidtop.py`, `lengths13.py`, `crops13.sh`, `render13.sh`, `sentinel21_13.sh`, `silk_tile13.py` (= silk_tile12).
- **Evidence:** `evidence/rt13-F.png`, `rt13-B.png`; before/after crops `rt12-` / `rt13-r142.png`, `-q101.png`, `-u4.png`, `-cc.png`, `-jack.png`.
- **Size:** intermediate boards and geo exports (about 0.3 GB); do not commit them.
