# RT-6: U4 east route, U24 block, I2S hub, continuation (2026-11-02)

Agent "RT-6 U4 east route, audio block, I2S, continuation". Input `ai-files/pcb/work-route5/RT-5.*`. Work folder `ai-files/pcb/work-route6/` only. Result `ai-files/pcb/work-route6/RT-6.kicad_pcb/.kicad_pro/.kicad_dru`. Nothing in `DesktopSpeaker-kicad/`, earlier work folders or `helpers/route_oct*.py` was edited. Board edits are text edits (`scripts/edit.py` from RT-5, plans built by coordinate lookup in `scripts/mkplan.py`); zones refilled in a separate pcbnew process with the pristine `.kicad_pro` and the RT-5 rule file beside the board. The footprint library is the project library (`kicad-library/footprint` is a link to `DesktopSpeaker-kicad/kicad-library/footprint`, which already holds the RT-5 fixes). Not committed; nothing published.

## 1. Result

| gate | RT-5 | RT-6 |
|---|---|---|
| kicad-cli DRC `--severity-all --all-track-errors` (RT-6 rules, project library) | 0 | **0** |
| DRC unconnected | 107 | **95** (12 closed, 0 new; 79 router scope + the 16 inherited 3V_AO/GND/LDO_3V3 items) |
| closures | | Q103-G 1, BATP 1, TS_SENSE 1, U24-VINL1 2, VINR2 2, VINL2 1, VINR1 1 (RC link), I2S_LRCK 1 (TP14), ADC_INT 1, BT_TXD_M 1 (router) |
| BAT_INT U4-22/23 -> Q103-1..3 (copper_path, 0.05 mm, 6 A, 20 C) | 2.652 mOhm | **2.889 mOhm** (limit 2.9; 104 mW at 6 A) |
| BAT_INT via field (x 163.9-170.9, y 120.6-123.9) | 22 vias | **18** (8 removed for the lane, 4 added on row y 120.6; >= 16) |
| footprints moved | | C110, R102, C106, TP2, TP12, TP14 (section 6); all other 354 unchanged |
| pad nets of 360 footprints (1194 pads) vs RT-5 | | **unchanged** (gates4 `pad_net_diff []`) |
| rule files | `.kicad_dru` ce43baa1..., `.kicad_pro` aa88e8c9... | **identical to RT-5** (no new rule, no exemption) |
| sentinel (I2S_CLK width >= 5 mm appended on a copy) | FIRES | **FIRES** (71 items) |
| locked copper (RT-5 items untouched) | | 2853 of 2929; 76 removed/changed, all listed in the edit reports, 0 unexpected; SHA-256 `793c7e782e8c703e59229880d28599782c27a35401d8246e9e0e8aedabd4a54b` |
| new copper exact 0/45/90 (gates4, own text parse) | | **95 segments, 248 mm, 0 not exact** |
| pour check (route_oct_pourcheck, RT-5 -> RT-6) | | **OK** (foreign unconnected 90 -> 90) |
| parcheck (< 0.4 mm over > 3 mm, touched nets) | 0 pairs | **0 pairs**; sensitive vias 4, 0 > 1.5 mm from GND; BM83 new F.Cu 0 mm |
| r7 joints < 80 / < 30 deg | 19 / 7 | **19 / 7**; exact length >= 5 mm segments 1521 -> 1646 mm |
| r7 BM83 F.Cu inside module | GND 2.3, SYS_PWR 2.0 | **unchanged** (0 mm new copper) |
| r7 switch proximity (U4) | ILIM_HIZ 0.36, TS_SENSE 0.99, PROG 1.28 mm from SW2 | ILIM_HIZ **1.23**, TS_SENSE **1.15** (B) / 1.93 (F), PROG 1.42 mm |
| HA8 failing pairs (r8b_ha8) | 122 | **122** (0 new, 0 gone, 0 tighter) |
| silkscreen (silk_tile.py + silk_tile_gate.py G1-G6) | | **ALL PASS**; RT-6 = the silk version of F4 |

Gate files (work-route6): `RT-6.drc.json`, `RT-6.gates.json` (gates4), `RT-6.check.json/.txt`, `RT-6.r7.json/.txt` (+ `t/RT-5.r7.json`), `RT-6.par.json/.txt`, `RT-6.rulehash.txt`, `RT-6.silkgate.json`, `sentinel/RT-6_sentinel.*`, `t/RT-6.gates.txt` (full gate log), `t/RT-6.ha8.json`, `t/RT-5.ha8.json`, `t/RT-6.cp.json` + `t/map_RT-6_*.png` (resistance maps).

## 2. Task 1: U4 east route (BATP, Q103-G, CE_N, TS_SENSE, CHG_INT)

**Finding (root cause, deeper than the via field).** The pins U4-20..25 sat inside the SW2 bootstrap loop (U4-26 -> SW2_F -> via (153,115.2) -> B.Cu leg x 156.3 -> via (155.13,125.8) -> C110 -> BTST2 -> U4-19), and the REGN B.Cu trunk to R110 ran through the same pocket (x 153.0), closing it on B.Cu to the north and south. Thinning the field alone opens nothing until the loop and REGN are moved. Pins 16-18 and 20-24 lie on opposite sides of BTST2 (pin 19), so one loop shape cannot leave both groups free: the loop was made compact so that 20-24 are outside it on B.Cu and 16-18 leave on F.Cu across it.

Edits (full coordinates in section 9):
- **REGN**: the pocket section (7 B.Cu segments, (152.19,115.62) .. via (155.45,127.6)) is removed. The trunk to R110 is fed by a new west hook, B.Cu 0.4 mm (152.19,115.62) -> (149.5,118.31) -> (149.5,121.87) -> via (148.79,122.58) on the U4-5 REGN track: 8.4 mm instead of 13 mm. R108-1's via moved (155.45,127.6) -> (155.45,128.9) with a 45-degree F.Cu feed, out of the new lanes.
- **SW2 bootstrap loop**: old B.Cu leg (3 segments), its vias (153,115.2) and (155.13,125.8) and the C110-2 stub removed. New: V1 0.5/0.2 at (151.9,119.45) on the U4-26 stub, B.Cu leg 0.3 mm under the U4 east pin row (151.9,119.45)-(151.9,120.1)-(152.87,121.07)-(152.87,122.7)-(155.6,122.7)-(155.6,126.2), V2 at (155.6,126.2), F.Cu stub to C110-2. The loop now encloses only the BTST2/C110 sliver; the whole loop lies inside NECK_U4.
- **Fan-out at the east toe** (all 0.2 mm, inside NECK_U4): BTST2 E to x 154.655 then SE (x-y = 32.07) to C110-1; PROG E to 154.845 then SE (32.66) to R102-1; BATP E to 154.275, SE to a 0.5/0.2 via (154.64,123.35) between BTST2 and ILIM_HIZ. C110, R102 moved (section 6).
- **Q103-G**: U4-24 -> NE to via (154.12,120.16) -> B.Cu north x 154.12, east y 115.1 (between the GND via row y 114.3 and SYS_COL_B), NE to y 114.35, east to x 170.425, NE, north to via (170.975,112.75) -> Q103-4. 25.0 mm, octilinear minimum 21.2 mm (1.18).
- **BATP**: via (154.64,123.35) -> B.Cu south x 154.64, lane y 126.95 under SYS_COL_B, NE (x+y 288.95) into the thinned field, column x 164.0 north, east y 115.9, NE into via (170.47,115.2) -> R112-2. Connection 31.6 mm vs 20.7 mm octilinear (1.53, inside 1.5 x min + 1 mm).
- **TS_SENSE**: from the existing via (153.17,127.485), lane y 127.785, NE (x+y 289.9), column x 164.9, east y 116.6, north x 172.4 (between the Q103 field and BAT_PACK_B), east y 108.35, NE straight onto the J5-2 B.Cu pad. 70 mm vs 60.6 mm (1.16). BATP/TS keep >= 0.4 mm edge gap everywhere (parcheck 0 pairs).
- **Via field**: removed (164.3,120.6), (165.1,120.6), (164.4,121.7/122.8/123.9), (165.5,121.7/122.8/123.9); added (167.7/168.8/169.9/170.9, 120.6). 18 vias remain.
- **SYS_RAW stitching row** y 128.2 (7 vias, x 156.9-161.7) moved to y 129.8 (same x) to give the TS lane its 0.4 mm POWER_HI clearance.
- **R102/C106 GND**: shared via (157.0,124.8975) -> (156.95,125.95); R102-2 and C106-2 joined by one 45-degree track.

Switch-critical clearance (BATP 2.0 mm): DRC passes without an exemption because every place where BATP is closer than 2.0 mm to SW2/BTST2 copper involves an item inside NECK_U4 (neck_ic 0.2 mm is the last matching rule). Measured: BATP to BTST2 0.20 mm over 0.8 mm (fan-out, unavoidable at the 0.4 mm pin pitch), to the C110-1 pad 0.21 mm, to V2 (SW2 via) 0.325 mm where the lane passes under it; >= 9 mm wherever both items are outside the neck. No exemption rule was added; the deviation from the 2.0 mm intent is local (about 2 mm of track) and is recorded here. BATP is a DC sense through R112.

BAT_INT resistance by build: RT-5 2.652, A2 2.872 (PROG shift narrows the finger's south edge; Q103-G via carve at the finger's NW corner), F3 2.914 (field thinned further; over the limit), **F4 2.889** (one via restored and one added). Margin to 2.9 is 0.011 mOhm: any further BAT_INT-area edit must be re-measured.

**Not closed in task 1** (11 connections in the U4 group):
- CE_N (Q100 leg) and ILIM_HIZ (to Q101-3/R109): their copper starts south of U4; to reach the lane they would cross the BATP descent (x 154.64). Remedy: a second lane south of the SYS rows (move the y 129.0 row as well) and an F.Cu crossing under R108/R100 (R108 cannot move: HA8 to R100/C110).
- CHG_INT: its via would sit east of the Q103-G B.Cu run while the MCU is north-west, so it must cross Q103-G or the REGN trunk on F.Cu north of U4 (SW2_F/SYS pours). Remedy: an F.Cu hop north of U4 after a C104/SW2_F reshape, or firmware polling of the charger status over I2C.
- CTRL_SDA x2, CTRL_SCL, QON (U4-12..15 south pins), CHG_ENABLE, CHG_SYS_ENABLE, Q101-G x2: long control nets / pockets (unchanged from RT-5).

## 3. Task 2: HP_G1 out of the U24 block, then the VIN block

- **HP_G1** (U3-21 -> U10-7): the 25 segments and 2 vias between U3-21 and via (161.025,75.45) are replaced by an hr.py draft north of the codec block: U3-21 F.Cu -> via (135.075,78.25) -> B.Cu y 76.0 -> via (151.025,76.0) -> F.Cu y 73.9 -> via (158.375,73.9) -> B.Cu to the existing B.Cu run. 30.6 mm for this part (the old detour went down to y 93.35 and under U24). The redundant via (161.025,75.45) and the old F stub were removed in B2/B3.
- **VIN links** (AUDIO, 0.25 mm): C206-1 -> U24-3, C209-1 -> U24-2, U24-1 -> VINL2 node (155.3825,81.63) as 45-degree fans with >= 0.85 mm perpendicular pitch on the diagonals; RC nodes R201-2/R200-2/R203-2 -> C207-1/C206-1/C209-1 in the 0.7 mm gaps between the C20x GND pads and vias (0.225 mm each side).
- **ADC_INT** U24-21 -> R211-1 closed (hr.py, 6.98 mm vs 5.22 mm): possible now that HP_G1 no longer runs under U24.
- **Not closed**: U24-4 (VINR1 pin link): C212 (VREF decoupling) occupies the pin-4 entry column (pads x 152.14-152.76) and VINR1 cannot reach pin 4 from the east without crossing the other three VIN entries. Remedy: move C212 and C215 0.35 mm west (needs HA8 room at C219) or rotate C212. U24-9 XO: C215 and the Y200-2 GND stub/via fill the only lane east of Y200 (remedy as RT-4: C215 0.6 mm east, Y200-2 via removed). C204/C205/C233/C235-Pad2, USB_AUDIO_L/R, U2-VOUTL: long feeds to the audio input block (40-50 mm), not attempted.

## 4. Task 3: I2S / AUD I2C

- **TP12 <-> TP14 swap** (positions exchanged: TP12 BCK now (146.35,95.4), TP14 LRCK (146.35,98.5); same footprint and rotation, HA8 unchanged). BCK's tail around the west of the hub (5 segments) is replaced by one 0.9 mm stub from R207's track into TP12; LRCK gets a 45-degree stub from its corner (142.895,97.047) into TP14. Closes the LRCK -> TP14 connection that was blocked by the BCK tail.
- **Not closed** (BCK U6-13 and U7-13, LRCK U6-12, AUD_SDA x3, AUD_SCL, AMP_FAULT_N x4 and related). hr.py drafts (`t/jC1.log`) fail on all seven, and the router reports "no exit at U6-13 / U7-13". Cause: at U6 the pin order is AUD_SCL(16) AUD_SDA(15) SDATA(14) BCK(13) LRCK(12). SDATA's escape turns NE immediately over pins 13/12, and AUD_SCL/SDATA leave only a 0.62 mm gap for AUD_SDA. At the hub the TPs are ordered top to bottom BCK, LRCK, SDATA, with SDATA approaching from the west at y 102.6. BCK and LRCK therefore have to cross SDATA between U6 and the hub. Remedy (not attempted, budget): (1) redraw the U6 escapes as a 5-track fan (pitch 1.2 on x+y: AUD_SCL 230.95, AUD_SDA 232.15, SDATA 233.35, BCK 234.55, LRCK 235.75) with SDATA straight north to y 124.5 first; (2) B.Cu hops for BCK/LRCK across SDATA at x > 125 or y < 114 (outside BKO_U6), each with a GND stitch via within 1.5 mm; (3) then equalise the I2S lengths to within 2 mm at the hub.

## 5. Task 4 and task 5

- **ILIM_HIZ**: 0.36 mm -> 1.23 mm from SW2 (C110 and V2 moved east), no reroute needed. TS_SENSE 0.99 -> 1.15/1.93 mm.
- **SW1/SW2 45-degree fan-out (Fix 4)**: not done. The freed space is on B.Cu; the fan-out needs the F.Cu PMID/SYS feed outlines reshaped (as RT-5).
- **Router continuation** (`scripts/run_cont.sh`, `helpers/route_oct_stage.sh`, project rule file beside the input as the router requires; net file `cont-nets.txt` from work-oct3):
  - KT (trial on RT-5, before the hand edits): 1/91.
  - **R1** on B3 (after tasks 1-2) with `--cont-drc --first-refs U1,J8 (S3) --detour 2.5 --via-cost 1.5 --pair-avoid 1 --hweight 1 --max-exp 3e7`: S1 0/5, S2 0/22, S3 1/55. **Closed BT_TXD_M** (8 segments, 1 via, connection ratio 1.08, no detour). Accepted (all gates).
  - R2 on R1-3 (iteration 2: `--margins 4,12,40,80 --tap-pen-mid 30 --pad-pen 0`): 0/82. The remaining connections are "no exit" (sealed pad stubs) or "no path" in under 0.1 s: the same picture as work-oct3.
- **hr.py closures** (`t/jE.json`, 32 connections with pad distance < 9 mm, on R1-3): 8 drafts, accepted only if length <= 1.5 x octilinear minimum + 1 mm: **ADC_INT accepted** (1.34). U10-INL- (1.00) was accepted by length but failed DRC (audio_clear 0.42 mm to the 3V3_AUDIO track at (187.8,60.35)) and was dropped. Rejected for detour: U12-EN 2.65, U11-FAULT 2.98, BT_FORCE_PWM 2.59, U14-FB 2.33, USB_CC2 2.12, U8-NC2 5.48. The 30-45 mm control nets were not hand-routed (budget).

## 6. Part moves (old -> new; all within 4 mm)

| ref | old | new | mm | reason |
|---|---|---|---|---|
| C110 | (154.73, 124.28) rot -90 | (155.6, 124.75) rot -90 | 0.99 | BATP via between BTST2 and ILIM_HIZ; HA8 to R108 (bootstrap loop still inside NECK_U4) |
| R102 | (156.05, 124.3) rot -90 | (156.95, 124.457) rot -90 | 0.91 | room for C110; PROG one 45-degree run |
| C106 | (157.9, 122.84) | (158.85, 122.84) | 0.95 | HA8 0.4 mm tier to R102 (BAT 10 uF bulk cap, now 5.4 mm from U4-22/23, was 4.4) |
| TP2 | (159.07, 126.485) | (159.97, 126.485) | 0.90 | HA8 0.4 mm tier to R102 |
| TP12 | (146.35, 98.5) | (146.35, 95.4) | 3.10 | TP12/TP14 swap (task 3) |
| TP14 | (146.35, 95.4) | (146.35, 98.5) | 3.10 | TP12/TP14 swap (task 3) |

HF decoupling: C110-1 (bootstrap) pad centre is 2.7 mm from U4-19 (RT-5: 1.7 mm); BTST2 is 3.2 mm long (RT-5 2.05 mm). No HF decoupling cap moved otherwise. Regenerate the position/CPL files, the stencil and the fab output for these six parts.

## 7. Iterations (AG13) and log

- Task 1: A1 (3 annular-width errors from 0.45/0.2 fine vias, 1 courtyard overlap TP2/R102, HA8 +4) -> A2 (0.5/0.2 vias, C110/R102/C106/TP2 placement: DRC 0, HA8 122, 2.872 mOhm) -> F3 = iteration 3 (parcheck TS/BATP 17.3 mm at 0.245 mm; mitres and exact joints). A V1 move inside F3 cut the U4-28 SW1 stub off SW1_F (dangling, +1 unconnected), so it was rolled back to the A2 V1. One corrective build, F4, followed because F3 measured 2.914 mOhm: restore/add 2 field vias, 2.889 mOhm. This is one build over the 3-iteration budget, for a gate failure only.
- Task 2: B1 (dangling old HP_G1 F stub) -> B2 (via left with B.Cu only) -> B3 (DRC 0).
- Task 3: hr drafts C1 (0/7); TP swap applied in F1/F2.
- Task 5: router R1, R2 (2 of 3); hr closures 1 run; F1 (U10-INL- audio_clear) -> F2 (dropped).
- Logs: `t/*.cycle` outputs in the shell transcripts, `t/R1.log`, `t/R2.log`, `t/KT.log`, `t/jB1.json`, `t/jC1.log`, `t/jE.log`, `t/pE.hrlog.json`, the plans `t/planA.json`, `t/planB.json`, `t/planF.json`, `t/planG.json`, `t/planH.json`, and the edit reports `A1/A2/B1/B2/B3/F1/F2/F3/F4.edit.json`.

## 8. Remaining open connections (95 = 79 router scope + 16 inherited), by cause and remedy

| group | conns | nets | cause / remedy |
|---|---|---|---|
| U4 charger pocket / east | 11 | CE_N, ILIM_HIZ, CHG_INT, CTRL_SDA 2, CTRL_SCL, QON, CHG_ENABLE, CHG_SYS_ENABLE, Q101-G 2 | section 2; second lane + F.Cu crossing at R108/R100; CHG_INT hop north of U4 or I2C polling; long nets via the MCU placement |
| I2S / AUD I2C / amp control U6/U7 | 14 | I2S_BCK 2, I2S_LRCK 1, AUD_SDA 3, AUD_SCL 1, AMP_FAULT_N 4, AMP_PDN, AMP_BOOST_EN, U7-PDN | section 4: U6 5-track fan + B.Cu hops outside BKO_U6 with GND stitches; AMP_FAULT_N is boxed by the LRCK escape at U6-9 |
| U24 codec block, audio feeds | 11 | U24-VINR1, U24-XO, C204/C205/C233-Pad2, C235-Pad2 2, USB_AUDIO_L, USB_AUDIO_R 2, U2-VOUTL | section 3: C212/C215 shuffle; long feeds need a placement pass of the input block |
| headphone mux/amp U8/U9/U10 | 16 | U8-COM1/COM2/NC1/NC2, HP_L, U10-INL-, HP_SEL_A 2, HP_SEL_B 2, HP_G0 2, HP_EN, HP_OUTL, AUX_L, AUX_DET | 3V3_AUDIO/C237 feed walls U9-10 and the mux lanes (RT-4); U10-INL- found at ratio 1.0 but 0.08 mm short of audio_clear: nudge the 3V3_AUDIO diagonal at (187.8,60.35) |
| USB-C / PD U11 | 9 | U11-FAULT, U11-ADC4, R18, PD_PLUG_EVENT, PD_SINK_EN, PDCTRL_SCL, USB_CC1, USB_CC2 2 | fine-pitch pockets; only detours 2.1-3.0x found |
| regulator control, gauge | 11 | U12-EN 2, U14-FB, 5V_LOGIC_EN 2, U25-FB, U25-MODE, BT_PWR_EN 2, BT_FORCE_PWM, GAUGE_ISO_N | only detours 2.3-2.7x found; need 0.5-1 mm part nudges at U12/U14/U15/U25 |
| MCU debug / BT UART | 7 | SWDIO 2, SWCLK, NRST (to J6), BT_UART_RX, BT_RST_M, BT_SYS_CFG | long nets (30-45 mm), BM83 keep-out; hand-route with the fewest vias in a later pass |
| inherited power | 16 | 3V_AO 8, GND 7, LDO_3V3 1 | unchanged from RT-2..RT-5 (outside router scope) |

## 9. Other open items and notes

1. **BAT_INT margin** 0.011 mOhm (2.889 of 2.9). The remaining F.Cu hotspot is still the 0.28 mm pin neck at U4-23 (13.9 A/mm at 6 A).
2. **Hygiene items on touched nets** (route_oct_check):
   - Dangling ends: REGN hook end (152.19,115.62) and its via (148.79,122.58) are off the inherited node coordinates by < 2 um (DRC connected). V1 (151.9,119.45) sits on the U4-26 stub mid-segment because the stub end is too close to the SYS via. REGN (151.87,127.58) and the via (176.35,106.75) are inherited.
   - 90-degree joints away from pads: 6 (VIN RC links 0.35 mm from the C20x pads, 2 corners of the SW2 leg).
   - T-junctions: LRCK TP14 stub at a corner and VINL2 joining its node (intended), plus 1 inherited REGN.
   - Pad exits < 0.3 mm: BTST2, PROG and VINL2 at 0.4-0.5 mm pitch pins; 5 inherited REGN.
3. **B.Cu reference**: BATP, TS_SENSE and Q103-G run about 130 mm on B.Cu over In2 power islands (SYS_IN2, BAT_INT_IN2, PVDD), not over GND. These are slow DC/gate nets; In1 under F.Cu is unchanged. Sensitive-net B.Cu is unchanged (5.1 mm).
4. **TS_SENSE ends on the J5-2 THT pad on B.Cu**: no via near J5.
5. **Regenerate**: position/CPL files (6 parts), stencil (C110, R102, C106, TP2, TP12, TP14), teardrops near edits (edit.py removed 5 teardrop zones: A2 2, B3 2, F2 1), Gerber/drill, board STEP.
6. **Work folder size**: intermediate boards (A1..F4, K0/K1, KT/R1/R2 stages) and geo exports, about 400 MB; do not commit them.

## 10. Files (`ai-files/pcb/work-route6/`)

- Result: `RT-6.kicad_pcb/.kicad_pro/.kicad_dru` (= F4 + silk_tile). Evidence: `evidence/rt6-F.png`, `evidence/rt6-B.png` (+ .svg), `evidence/u4-east-B.png`, `evidence/u4-fanout-F.png`, `evidence/hp-g1-u24.png`, `evidence/i2s-hub-F.png`.
- Build chain: RT-5 = `R0` -> `A2` (`scripts/planA.py`) -> `B3` (`t/planB.json`) -> router `R1-1..3` -> `F2` (`scripts/planC.py` + `t/planE.json`) -> `F3` (`scripts/planG.py`) -> `F4` (`t/planH.json`) -> `RT-6` (silk_tile).
- Scripts (`scripts/`): RT-5 set, plus:
  - `mkplan.py` (plans by coordinates);
  - `pchk.py` (pre-DRC clearance aid);
  - `planA.py`, `planC.py`, `planG.py`;
  - `run_cont.sh` (continuation wrapper);
  - `ha8.sh`, `gates6.sh` (gate suite).

## 11. Edit log (net, layer, coordinates)

Router stage R1-S3 (BT_TXD_M, 8 segments + 1 via) is listed in `R1-manifest.json` (`added_items`) and `R1-3.route.json`.

### A2: task 1 U4 east (R0=RT-5 -> A2)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg del c05c6f04 | /Battery_Charger/REGN | B.Cu | 0.6 | (152.7952, 117.6094)-(152.1905, 115.6187) |
| seg del 5b2f5d77 | /Battery_Charger/REGN | B.Cu | 0.4 | (153.4000, 119.6000)-(152.7952, 117.6094) |
| seg del cdc7a7ea | /Battery_Charger/REGN | B.Cu | 0.4 | (153.4000, 119.6000)-(153.0000, 120.0000) |
| seg del bf528583 | /Battery_Charger/REGN | B.Cu | 0.5 | (153.0000, 120.0000)-(153.0000, 123.0667) |
| seg del 1a0ab8f3 | /Battery_Charger/REGN | B.Cu | 0.5 | (153.0000, 123.0667)-(153.5667, 123.6333) |
| seg del da627d5a | /Battery_Charger/REGN | B.Cu | 0.4 | (153.6500, 125.6500)-(153.5667, 123.6333) |
| seg del 0ec96bd7 | /Battery_Charger/REGN | B.Cu | 0.4 | (155.2500, 127.4000)-(153.6500, 125.6500) |
| seg del bb9478a4 | /Battery_Charger/REGN | F.Cu | 0.6 | (155.3300, 127.4800)-(155.4500, 127.6000) |
| seg del b3bf740d | /Battery_Charger/SW2 | B.Cu | 0.4 | (153.0000, 115.2000)-(156.3000, 118.5000) |
| seg del b38f5d65 | /Battery_Charger/SW2 | B.Cu | 0.4 | (156.3000, 118.5000)-(156.3000, 124.6300) |
| seg del 70dea569 | /Battery_Charger/SW2 | B.Cu | 0.4 | (156.3000, 124.6300)-(155.1300, 125.8000) |
| seg del 0d54ffa2 | /Battery_Charger/SW2 | F.Cu | 0.4 | (154.7300, 124.8475)-(154.7300, 125.4000) |
| seg del cc8720ed | /Battery_Charger/SW2 | F.Cu | 0.4 | (154.7300, 125.4000)-(155.1300, 125.8000) |
| seg del 34096a07 | /Battery_Charger/BTST2 | F.Cu | 0.2 | (153.4300, 122.5850)-(154.0700, 122.5850) |
| seg del b0ec7802 | /Battery_Charger/BTST2 | F.Cu | 0.2 | (154.0700, 122.5850)-(154.7300, 123.2450) |
| seg del 287ca498 | /Battery_Charger/BTST2 | F.Cu | 0.2 | (154.7300, 123.2450)-(154.7300, 123.7125) |
| seg del e2c67ab4 | /Battery_Charger/PROG | F.Cu | 0.2 | (153.4700, 122.1850)-(154.3050, 122.1850) |
| seg del 0847b3c3 | /Battery_Charger/PROG | F.Cu | 0.2 | (154.3050, 122.1850)-(156.0500, 123.9300) |
| seg del de1ae19e | GND | F.Cu | 0.3 | (156.0500, 124.8975)-(157.0000, 124.8975) |
| seg del a9f988c7 | GND | F.Cu | 0.4 | (157.9000, 123.9975)-(157.0000, 124.8975) |
| seg del 2a996590 | GND | F.Cu | 0.4 | (157.9000, 123.8770)-(157.9000, 123.9975) |
| seg set 80574cb6 | /Battery_Charger/REGN | B.Cu | 0.6 | (155.4500, 127.6000)-(155.4500, 130.7000) -> (155.4500, 128.9000)-(155.4500, 130.7000) |
| seg set 6fdf0db7 | /Battery_Charger/REGN | F.Cu | 0.6 | (154.2700, 127.4800)-(155.3300, 127.4800) -> (154.2700, 127.4800)-(154.8300, 127.4800) |
| via del 55258782 | /Battery_Charger/SW2 | F-B | 0.6/0.3 | (155.1300, 125.8000) |
| via del 6c0dd744 | /Battery_Charger/SW2 | F-B | 0.6/0.3 | (153.0000, 115.2000) |
| via del 71cb0e6b | GND | F-B | 0.6/0.3 | (157.0000, 124.8975) |
| via del 66040038 | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (164.3000, 120.6000) |
| via del 797450d7 | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (165.1000, 120.6000) |
| via del 05888709 | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (164.4000, 121.7000) |
| via del 823b8556 | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (164.4000, 122.8000) |
| via del cef017f7 | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (164.4000, 123.9000) |
| via move 99ffb6ba | /Battery_Charger/REGN | F-B | - | (155.4500, 127.6000) -> (155.4500, 128.9000) |
| via move a069ec40 | /SYS_RAW | F-B | - | (156.9000, 128.2000) -> (156.9000, 129.8000) |
| via move c0b8f219 | /SYS_RAW | F-B | - | (157.7000, 128.2000) -> (157.7000, 129.8000) |
| via move f0930c16 | /SYS_RAW | F-B | - | (158.5000, 128.2000) -> (158.5000, 129.8000) |
| via move 72ff93fe | /SYS_RAW | F-B | - | (159.3000, 128.2000) -> (159.3000, 129.8000) |
| via move c8389ed4 | /SYS_RAW | F-B | - | (160.1000, 128.2000) -> (160.1000, 129.8000) |
| via move d202078d | /SYS_RAW | F-B | - | (160.9000, 128.2000) -> (160.9000, 129.8000) |
| via move 93f7a467 | /SYS_RAW | F-B | - | (161.7000, 128.2000) -> (161.7000, 129.8000) |
| footprint move C110 | - | F | - | (154.73, 124.28) -> (155.6, 124.75, -90) |
| footprint move R102 | - | F | - | (156.05, 124.3) -> (156.95, 124.457, -90) |
| footprint move C106 | - | F | - | (157.9, 122.84) -> (158.85, 122.84) |
| footprint move TP2 | - | F | - | (159.07, 126.485) -> (159.97, 126.485) |
| seg add | /Battery_Charger/REGN | B.Cu | 0.4 | (152.1900, 115.6200)-(149.5000, 118.3100) |
| seg add | /Battery_Charger/REGN | B.Cu | 0.4 | (149.5000, 118.3100)-(149.5000, 121.8700) |
| seg add | /Battery_Charger/REGN | B.Cu | 0.4 | (149.5000, 121.8700)-(148.8000, 122.5700) |
| seg add | /Battery_Charger/REGN | F.Cu | 0.6 | (154.8300, 127.4800)-(155.4500, 128.1000) |
| seg add | /Battery_Charger/REGN | F.Cu | 0.6 | (155.4500, 128.1000)-(155.4500, 128.9000) |
| seg add | /Battery_Charger/SW2 | B.Cu | 0.3 | (151.9000, 119.4500)-(151.9000, 120.1000) |
| seg add | /Battery_Charger/SW2 | B.Cu | 0.3 | (151.9000, 120.1000)-(152.8700, 121.0700) |
| seg add | /Battery_Charger/SW2 | B.Cu | 0.3 | (152.8700, 121.0700)-(152.8700, 122.7000) |
| seg add | /Battery_Charger/SW2 | B.Cu | 0.3 | (152.8700, 122.7000)-(155.6000, 122.7000) |
| seg add | /Battery_Charger/SW2 | B.Cu | 0.3 | (155.6000, 122.7000)-(155.6000, 126.2000) |
| seg add | /Battery_Charger/SW2 | F.Cu | 0.4 | (155.6000, 125.3170)-(155.6000, 126.2000) |
| seg add | /Battery_Charger/BTST2 | F.Cu | 0.2 | (153.4300, 122.5850)-(154.6550, 122.5850) |
| seg add | /Battery_Charger/BTST2 | F.Cu | 0.2 | (154.6550, 122.5850)-(155.6000, 123.5300) |
| seg add | /Battery_Charger/BTST2 | F.Cu | 0.2 | (155.6000, 123.5300)-(155.6000, 124.1820) |
| seg add | /Battery_Charger/PROG | F.Cu | 0.2 | (153.4700, 122.1850)-(154.8450, 122.1850) |
| seg add | /Battery_Charger/PROG | F.Cu | 0.2 | (154.8450, 122.1850)-(156.5200, 123.8600) |
| seg add | /Battery_Charger/PROG | F.Cu | 0.2 | (156.5200, 123.8600)-(156.9500, 123.8600) |
| seg add | GND | F.Cu | 0.3 | (156.9500, 125.0540)-(156.9500, 125.9500) |
| seg add | GND | F.Cu | 0.4 | (158.8500, 123.9770)-(158.8500, 124.2540) |
| seg add | GND | F.Cu | 0.4 | (158.8500, 124.2540)-(158.0500, 125.0540) |
| seg add | GND | F.Cu | 0.4 | (158.0500, 125.0540)-(156.9500, 125.0540) |
| seg add | Net-(U4-BATP) | F.Cu | 0.2 | (153.4450, 122.9850)-(154.2750, 122.9850) |
| seg add | Net-(U4-BATP) | F.Cu | 0.2 | (154.2750, 122.9850)-(154.6400, 123.3500) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (154.6400, 123.3500)-(154.6400, 126.6000) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (154.6400, 126.6000)-(154.9900, 126.9500) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (154.9900, 126.9500)-(162.0500, 126.9500) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (162.0500, 126.9500)-(164.0000, 125.0000) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (164.0000, 125.0000)-(164.0000, 115.9000) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (164.0000, 115.9000)-(170.4700, 115.9000) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (170.4700, 115.9000)-(170.4700, 115.2000) |
| seg add | Net-(U4-BATP) | F.Cu | 0.25 | (170.4700, 115.2000)-(170.4700, 114.2100) |
| seg add | Net-(Q103-G) | F.Cu | 0.2 | (153.6950, 120.5850)-(154.1200, 120.1600) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (154.1200, 120.1600)-(154.1200, 115.4500) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (154.1200, 115.4500)-(154.4700, 115.1000) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (154.4700, 115.1000)-(163.1000, 115.1000) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (163.1000, 115.1000)-(163.8500, 114.3500) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (163.8500, 114.3500)-(170.6250, 114.3500) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (170.6250, 114.3500)-(170.9750, 114.0000) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (170.9750, 114.0000)-(170.9750, 112.7500) |
| seg add | Net-(Q103-G) | F.Cu | 0.25 | (170.9750, 112.7500)-(170.9750, 111.7100) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (153.1700, 127.4850)-(153.3100, 127.6250) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (153.3100, 127.6250)-(162.0750, 127.6250) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (162.0750, 127.6250)-(164.5000, 125.2000) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (164.5000, 125.2000)-(164.5000, 116.4000) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (164.5000, 116.4000)-(172.4000, 116.4000) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (172.4000, 116.4000)-(172.4000, 108.3500) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (172.4000, 108.3500)-(199.0000, 108.3500) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (199.0000, 108.3500)-(202.7450, 104.6050) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (202.7450, 104.6050)-(204.2850, 104.6050) |
| via add | /Battery_Charger/REGN | F-B | 0.6/0.3 | (148.8000, 122.5700) |
| via add | /Battery_Charger/SW2 | F-B | 0.5/0.2 | (151.9000, 119.4500) |
| via add | /Battery_Charger/SW2 | F-B | 0.6/0.3 | (155.6000, 126.2000) |
| via add | GND | F-B | 0.6/0.3 | (156.9500, 125.9500) |
| via add | Net-(U4-BATP) | F-B | 0.5/0.2 | (154.6400, 123.3500) |
| via add | Net-(U4-BATP) | F-B | 0.6/0.3 | (170.4700, 115.2000) |
| via add | Net-(Q103-G) | F-B | 0.5/0.2 | (154.1200, 120.1600) |
| via add | Net-(Q103-G) | F-B | 0.6/0.3 | (170.9750, 112.7500) |
| teardrops removed near edits | | | | 2 |

### B3: task 2 HP_G1 + U24 VIN links (A2 -> B3)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg del 148c85ad | /HP_G1 | F.Cu | 0.25 | (142.3250, 93.3500)-(144.5250, 91.1500) |
| seg del 224b774a | /HP_G1 | F.Cu | 0.25 | (154.7750, 83.4000)-(154.7750, 81.7000) |
| seg del 2d7cb059 | /HP_G1 | F.Cu | 0.25 | (148.0250, 86.1000)-(150.6250, 86.1000) |
| seg del 32b2cb16 | /HP_G1 | F.Cu | 0.25 | (137.1250, 90.5000)-(139.9750, 93.3500) |
| seg del 32c6e1cd | /HP_G1 | F.Cu | 0.25 | (154.2250, 77.1000)-(155.0250, 76.3000) |
| seg del 33a4442f | /HP_G1 | F.Cu | 0.25 | (139.9750, 93.3500)-(142.3250, 93.3500) |
| seg del 33c0f003 | /HP_G1 | F.Cu | 0.25 | (146.5750, 87.5500)-(148.0250, 86.1000) |
| seg del 34ed79de | /HP_G1 | F.Cu | 0.25 | (146.5750, 89.3000)-(146.5750, 87.5500) |
| seg del 3bbe4a35 | /HP_G1 | F.Cu | 0.25 | (145.0750, 89.8500)-(146.0250, 89.8500) |
| seg del 474c0d0d | /HP_G1 | F.Cu | 0.25 | (154.7750, 81.7000)-(154.2250, 81.1500) |
| seg del 4aaa39be | /HP_G1 | F.Cu | 0.25 | (155.0250, 76.3000)-(159.1750, 76.3000) |
| seg del 4dd777d9 | /HP_G1 | F.Cu | 0.25 | (159.1750, 76.3000)-(160.0250, 75.4500) |
| seg del 6113d497 | /HP_G1 | F.Cu | 0.25 | (144.5250, 91.1500)-(144.5250, 90.4000) |
| seg del 6d4c7fba | /HP_G1 | F.Cu | 0.25 | (137.1250, 89.5500)-(137.1250, 90.5000) |
| seg del 7a0e0877 | /HP_G1 | F.Cu | 0.25 | (144.5250, 90.4000)-(145.0750, 89.8500) |
| seg del 880cf410 | /HP_G1 | F.Cu | 0.25 | (133.6750, 78.2500)-(134.7750, 78.2500) |
| seg del 9bb26afd | /HP_G1 | F.Cu | 0.25 | (152.7750, 83.9500)-(154.2250, 83.9500) |
| seg del a947b4ea | /HP_G1 | F.Cu | 0.25 | (154.2250, 83.9500)-(154.7750, 83.4000) |
| seg del bb4298f2 | /HP_G1 | F.Cu | 0.25 | (146.0250, 89.8500)-(146.5750, 89.3000) |
| seg del c11e8204 | /HP_G1 | F.Cu | 0.25 | (154.2250, 81.1500)-(154.2250, 77.1000) |
| seg del d08b0880 | /HP_G1 | F.Cu | 0.25 | (134.7750, 78.2500)-(135.3250, 78.8000) |
| seg del f32d7f61 | /HP_G1 | F.Cu | 0.25 | (135.3250, 78.8000)-(135.3250, 79.8500) |
| seg del fcb59bfe | /HP_G1 | F.Cu | 0.25 | (150.6250, 86.1000)-(152.7750, 83.9500) |
| seg del a4f53c19 | /HP_G1 | B.Cu | 0.25 | (135.3250, 79.8500)-(137.1250, 81.6500) |
| seg del bcb684fe | /HP_G1 | B.Cu | 0.25 | (137.1250, 81.6500)-(137.1250, 89.5500) |
| seg del bc8b23a6 | /HP_G1 | F.Cu | 0.25 | (160.0250, 75.4500)-(161.0250, 75.4500) |
| via del 0cb811c6 | /HP_G1 | F-B | 0.6/0.3 | (137.1250, 89.5500) |
| via del 25a1293f | /HP_G1 | F-B | 0.6/0.3 | (135.3250, 79.8500) |
| via del ca13b881 | /HP_G1 | F-B | 0.6/0.3 | (161.0250, 75.4500) |
| seg add | /HP_G1 | F.Cu | 0.25 | (133.6750, 78.2500)-(135.0750, 78.2500) |
| seg add | /HP_G1 | B.Cu | 0.25 | (135.0750, 78.2500)-(135.0750, 77.5000) |
| seg add | /HP_G1 | B.Cu | 0.2 | (135.0750, 77.5000)-(136.5750, 76.0000) |
| seg add | /HP_G1 | B.Cu | 0.25 | (136.5750, 76.0000)-(151.0250, 76.0000) |
| seg add | /HP_G1 | F.Cu | 0.25 | (151.0250, 76.0000)-(153.1250, 73.9000) |
| seg add | /HP_G1 | F.Cu | 0.25 | (153.1250, 73.9000)-(158.3750, 73.9000) |
| seg add | /HP_G1 | B.Cu | 0.25 | (158.3750, 73.9000)-(158.3750, 74.6500) |
| seg add | /HP_G1 | B.Cu | 0.25 | (158.3750, 74.6500)-(159.1750, 75.4500) |
| seg add | /HP_G1 | B.Cu | 0.25 | (159.1750, 75.4500)-(161.0250, 75.4500) |
| seg add | Net-(U24-VINL1) | F.Cu | 0.25 | (155.3800, 78.3500)-(155.2000, 78.3500) |
| seg add | Net-(U24-VINL1) | F.Cu | 0.25 | (155.2000, 78.3500)-(153.2500, 80.3000) |
| seg add | Net-(U24-VINL1) | F.Cu | 0.25 | (153.2500, 80.3000)-(153.2500, 82.5600) |
| seg add | Net-(U24-VINR2) | F.Cu | 0.25 | (155.3800, 79.6500)-(155.3000, 79.6500) |
| seg add | Net-(U24-VINR2) | F.Cu | 0.25 | (155.3000, 79.6500)-(153.7500, 81.2000) |
| seg add | Net-(U24-VINR2) | F.Cu | 0.25 | (153.7500, 81.2000)-(153.7500, 82.5600) |
| seg add | Net-(U24-VINL2) | F.Cu | 0.25 | (154.2400, 82.5600)-(154.2400, 81.6100) |
| seg add | Net-(U24-VINL2) | F.Cu | 0.25 | (154.2400, 81.6100)-(155.3700, 81.6100) |
| seg add | Net-(U24-VINR1) | F.Cu | 0.25 | (158.4000, 77.7000)-(155.3800, 77.7000) |
| seg add | Net-(U24-VINL1) | F.Cu | 0.25 | (158.4000, 79.0000)-(155.3800, 79.0000) |
| seg add | Net-(U24-VINL1) | F.Cu | 0.25 | (155.3800, 79.0000)-(155.3800, 78.3500) |
| seg add | Net-(U24-VINR2) | F.Cu | 0.25 | (158.4000, 80.3000)-(155.3800, 80.3000) |
| seg add | Net-(U24-VINR2) | F.Cu | 0.25 | (155.3800, 80.3000)-(155.3800, 79.6500) |
| seg add | Net-(U24-VINR1) | F.Cu | 0.25 | (155.3800, 77.7000)-(155.3800, 77.0500) |
| via add | /HP_G1 | F-B | 0.6/0.3 | (135.0750, 78.2500) |
| via add | /HP_G1 | F-B | 0.6/0.3 | (151.0250, 76.0000) |
| via add | /HP_G1 | F-B | 0.6/0.3 | (158.3750, 73.9000) |
| teardrops removed near edits | | | | 2 |

### F2: task 3 TP swap + hr closure ADC_INT (R1-3 -> F2)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg del d24da899 | /I2S_BCK | F.Cu | 0.25 | (144.5000, 93.7500)-(147.1500, 93.7500) |
| seg del 140e27f5 | /I2S_BCK | F.Cu | 0.25 | (143.8000, 94.4500)-(144.5000, 93.7500) |
| seg del 3761a114 | /I2S_BCK | F.Cu | 0.25 | (143.8000, 97.9500)-(143.8000, 94.4500) |
| seg del 08cb832b | /I2S_BCK | F.Cu | 0.25 | (144.3500, 98.5000)-(143.8000, 97.9500) |
| seg del f38cea4f | /I2S_BCK | F.Cu | 0.25 | (146.3500, 98.5000)-(144.3500, 98.5000) |
| footprint move TP12 | - | F | - | (146.35, 98.5) -> (146.35, 95.4) |
| footprint move TP14 | - | F | - | (146.35, 95.4) -> (146.35, 98.5) |
| seg add | /I2S_BCK | F.Cu | 0.25 | (147.1500, 93.7500)-(147.1500, 94.6500) |
| seg add | /I2S_LRCK | F.Cu | 0.25 | (142.8950, 97.0470)-(143.6000, 97.7520) |
| seg add | /I2S_LRCK | F.Cu | 0.25 | (143.6000, 97.7520)-(144.8000, 97.7520) |
| seg add | /ADC_INT | F.Cu | 0.25 | (149.7450, 88.2800)-(149.7450, 87.2300) |
| seg add | /ADC_INT | F.Cu | 0.25 | (149.7450, 87.2300)-(149.1950, 86.6800) |
| seg add | /ADC_INT | F.Cu | 0.25 | (149.1950, 86.6800)-(146.8450, 86.6800) |
| seg add | /ADC_INT | F.Cu | 0.25 | (146.8450, 86.6800)-(146.1950, 87.3300) |
| seg add | /ADC_INT | F.Cu | 0.2 | (146.1950, 87.3300)-(145.4450, 87.3300) |
| seg add | /ADC_INT | F.Cu | 0.2 | (145.4450, 87.3300)-(144.6450, 88.1300) |
| teardrops removed near edits | | | | 1 |

### F3: task 1 iteration 3 hygiene/parcheck (F2 -> F3)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| seg del 7d8a43fd | /Battery_Charger/REGN | B.Cu | 0.4 | (152.1900, 115.6200)-(149.5000, 118.3100) |
| seg del a6cc99c7 | /Battery_Charger/REGN | B.Cu | 0.4 | (149.5000, 118.3100)-(149.5000, 121.8700) |
| seg del 5f73f5fa | /Battery_Charger/REGN | B.Cu | 0.4 | (149.5000, 121.8700)-(148.8000, 122.5700) |
| seg del 5dc33c3b | Net-(U24-VINL2) | F.Cu | 0.25 | (154.2400, 82.5600)-(154.2400, 81.6100) |
| seg del 8a93ffb3 | Net-(U24-VINL2) | F.Cu | 0.25 | (154.2400, 81.6100)-(155.3700, 81.6100) |
| seg del 1b1a2d6a | Net-(Q103-G) | B.Cu | 0.25 | (154.1200, 120.1600)-(154.1200, 115.4500) |
| seg del baf44343 | Net-(Q103-G) | B.Cu | 0.25 | (154.1200, 115.4500)-(154.4700, 115.1000) |
| seg del 2bc025ec | Net-(Q103-G) | B.Cu | 0.25 | (154.4700, 115.1000)-(163.1000, 115.1000) |
| seg del 3cbed461 | Net-(Q103-G) | B.Cu | 0.25 | (163.8500, 114.3500)-(170.6250, 114.3500) |
| seg del f2c2b74d | Net-(Q103-G) | B.Cu | 0.25 | (170.6250, 114.3500)-(170.9750, 114.0000) |
| seg del 8e9dc757 | Net-(Q103-G) | B.Cu | 0.25 | (170.9750, 114.0000)-(170.9750, 112.7500) |
| seg del 2083bedf | Net-(U4-BATP) | B.Cu | 0.25 | (154.6400, 123.3500)-(154.6400, 126.6000) |
| seg del a6165771 | Net-(U4-BATP) | B.Cu | 0.25 | (154.6400, 126.6000)-(154.9900, 126.9500) |
| seg del 30d6ce39 | Net-(U4-BATP) | B.Cu | 0.25 | (154.9900, 126.9500)-(162.0500, 126.9500) |
| seg del ecab0837 | Net-(U4-BATP) | B.Cu | 0.25 | (162.0500, 126.9500)-(164.0000, 125.0000) |
| seg del 9f478f77 | Net-(U4-BATP) | B.Cu | 0.25 | (164.0000, 125.0000)-(164.0000, 115.9000) |
| seg del f1cb9ee3 | Net-(U4-BATP) | B.Cu | 0.25 | (164.0000, 115.9000)-(170.4700, 115.9000) |
| seg del 2d729a43 | Net-(U4-BATP) | B.Cu | 0.25 | (170.4700, 115.9000)-(170.4700, 115.2000) |
| seg del 5df7b419 | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (153.1700, 127.4850)-(153.3100, 127.6250) |
| seg del 0b63ca89 | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (153.3100, 127.6250)-(162.0750, 127.6250) |
| seg del 898c3b17 | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (162.0750, 127.6250)-(164.5000, 125.2000) |
| seg del c29bfcd0 | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (164.5000, 125.2000)-(164.5000, 116.4000) |
| seg del d2f0ef91 | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (164.5000, 116.4000)-(172.4000, 116.4000) |
| seg del 272cedc2 | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (172.4000, 116.4000)-(172.4000, 108.3500) |
| seg del 10f0f113 | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (172.4000, 108.3500)-(199.0000, 108.3500) |
| seg del 495343c9 | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (199.0000, 108.3500)-(202.7450, 104.6050) |
| seg del 13e277ab | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (202.7450, 104.6050)-(204.2850, 104.6050) |
| via del 668298e5 | /Battery_Charger/REGN | F-B | 0.6/0.3 | (148.8000, 122.5700) |
| via del a3c776a7 | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (165.5000, 121.7000) |
| via del e02bce19 | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (165.5000, 122.8000) |
| via del 0a8868da | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (165.5000, 123.9000) |
| via del 57c8d59f | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (165.9000, 120.6000) |
| seg add | /Battery_Charger/REGN | B.Cu | 0.4 | (152.1905, 115.6187)-(149.5000, 118.3092) |
| seg add | /Battery_Charger/REGN | B.Cu | 0.4 | (149.5000, 118.3092)-(149.5000, 121.8720) |
| seg add | /Battery_Charger/REGN | B.Cu | 0.4 | (149.5000, 121.8720)-(148.7940, 122.5780) |
| seg add | Net-(U24-VINL2) | F.Cu | 0.25 | (154.2450, 82.5550)-(154.2450, 81.6300) |
| seg add | Net-(U24-VINL2) | F.Cu | 0.25 | (154.2450, 81.6300)-(155.3825, 81.6300) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (154.1200, 120.1600)-(154.1200, 115.6500) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (154.1200, 115.6500)-(154.6700, 115.1000) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (154.6700, 115.1000)-(163.1000, 115.1000) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (163.8500, 114.3500)-(170.4250, 114.3500) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (170.4250, 114.3500)-(170.9750, 113.8000) |
| seg add | Net-(Q103-G) | B.Cu | 0.25 | (170.9750, 113.8000)-(170.9750, 112.7500) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (154.6400, 123.3500)-(154.6400, 126.4000) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (154.6400, 126.4000)-(155.1900, 126.9500) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (155.1900, 126.9500)-(162.0000, 126.9500) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (162.0000, 126.9500)-(164.0000, 124.9500) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (164.0000, 124.9500)-(164.0000, 116.4500) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (164.0000, 116.4500)-(164.5500, 115.9000) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (164.5500, 115.9000)-(169.7700, 115.9000) |
| seg add | Net-(U4-BATP) | B.Cu | 0.25 | (169.7700, 115.9000)-(170.4700, 115.2000) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (153.1700, 127.4850)-(153.4700, 127.7850) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (153.4700, 127.7850)-(162.1150, 127.7850) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (162.1150, 127.7850)-(164.9000, 125.0000) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (164.9000, 125.0000)-(164.9000, 117.1500) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (164.9000, 117.1500)-(165.4500, 116.6000) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (165.4500, 116.6000)-(171.8500, 116.6000) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (171.8500, 116.6000)-(172.4000, 116.0500) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (172.4000, 116.0500)-(172.4000, 108.9000) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (172.4000, 108.9000)-(172.9500, 108.3500) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (172.9500, 108.3500)-(199.0000, 108.3500) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (199.0000, 108.3500)-(202.7450, 104.6050) |
| seg add | /Battery_Charger/TS_SENSE | B.Cu | 0.25 | (202.7450, 104.6050)-(204.2850, 104.6050) |
| via add | /Battery_Charger/REGN | F-B | 0.6/0.3 | (148.7940, 122.5780) |
| via add | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (167.7000, 120.6000) |
| via add | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (168.8000, 120.6000) |
| via add | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (169.9000, 120.6000) |
| teardrops removed near edits | | | | 0 |

### F4: BAT_INT via restore (F3 -> F4)

| op | net | layer | w / size | geometry |
|---|---|---|---|---|
| via add | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (165.9000, 120.6000) |
| via add | /Battery_Charger/BAT_INT | F-B | 0.8/0.4 | (170.9000, 120.6000) |
| teardrops removed near edits | | | | 0 |

