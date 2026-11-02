# RT-7: remaining connections and release checks (2026-11-02)

Agent "RT-7 remaining connections and release checks". Input `ai-files/pcb/work-route6/RT-6.*` (204/283 connections, DRC 0, 95 unconnected). Work folder `ai-files/pcb/work-route7/` only. Result `ai-files/pcb/work-route7/RT-7.kicad_pcb/.kicad_pro/.kicad_dru`. Nothing in `DesktopSpeaker-kicad/`, earlier work folders or `helpers/route_oct*.py` was edited. All board edits are text edits (`scripts/edit.py`, plans by coordinates in `scripts/mkplan.py`); every build refilled in a separate pcbnew process with the pristine `.kicad_pro` and the RT-6 rule file beside it (`scripts/cycle.sh`). Not committed; nothing published.

**Bottom line: the goal (0 unconnected) was not reached.** RT-7 closes 31 of the 95 unconnected items: all 15 inherited power items that could be closed (3V_AO at the MCU, GND around U3/J7, LDO_3V3) and 16 routing connections. **64 remain** (1 inherited 3V_AO, 63 routing), every one of them a sealed pin pocket or a corridor that needs a placement or copper redesign beyond the 3-iteration budget; section 6 lists each with cause and remedy. No release-todo file was written (the brief asks for it only at 0 unconnected).

## 1. Result

| gate | RT-6 | RT-7 |
|---|---|---|
| kicad-cli DRC `--severity-all --all-track-errors` (RT-6 rules, project library) | 0 | **0** |
| DRC unconnected | 95 (79 routing + 16 inherited) | **64** (63 routing + 1 inherited 3V_AO to R241) |
| connections closed | | 31: 3V_AO 7, GND 7, LDO_3V3 1, U24-VINR1, U24-XO, U25-FB, U25-MODE, U10-INL-, U11-FAULT, U12-EN (pin link), BT_FORCE_PWM, BT_PWR_EN (R152-U15), USB_CC2 (D5-J1), I2S_LRCK (U6), AUD_SDA (U6), BT_UART_RX, CE_N, 5V_LOGIC_EN (U3-U14), CTRL_SDA (U4-15 -> TP15) |
| footprints moved | | **C212** 0.35 mm W (VINR1 lane), **R209** 0.011 mm (HA8 compensation); 358 others unchanged |
| pad nets of 360 footprints (1194 pads) vs RT-6 | | **unchanged** (gates4 `pad_net_diff []`) |
| rule files | `.kicad_dru` ce43baa1..., `.kicad_pro` aa88e8c9... | **identical to RT-6** (no new rule, no exemption) |
| sentinel (I2S_CLK width >= 5 mm appended on a copy) | FIRES | **FIRES** |
| locked copper (RT-6 items untouched) | | 2939 of 2972; 33 removed/changed, all in the edit reports, 0 unexpected; SHA-256 `899de752...a4797e4b4df9c745` |
| new copper exact 0/45/90 (gates4, own text parse) | | **188 segments, 520.4 mm, 0 not exact** |
| pour check (route_oct_pourcheck, RT-6 -> RT-7) | | **OK**, foreign unconnected 62 -> 55 |
| parcheck (< 0.4 mm over > 3 mm) | 0 pairs | sensitive pairs **0**; 1 non-sensitive pair BT_RST_N / BT_UART_RX B.Cu 4.35 mm at 0.25 mm (both slow UART/reset lines; the only shift was blocked by a PDCTRL_SCL via) |
| sensitive vias / farther than 1.5 mm from GND | | 17 / **0** (worst 1.425 mm, LRCK hub via, inherited) |
| r7 joints < 80 / < 30 deg | 19 / 7 | **19 / 7** (all inherited power copper); exact segments >= 5 mm 1646 -> 1853 mm |
| r7 BM83 F.Cu inside module | GND 2.3, SYS_PWR 2.0 | **unchanged** (0 mm new copper) |
| r7 switch proximity | | unchanged entries; new copper adds none below RT-6's minimum (TS_SENSE F 1.88 mm, the moved TS via) |
| HA8 failing pairs | 122 | **122**: new C215-C212 (0.14 of 0.4 mm, the VINR1 lane), gone H2-R209 (was 0.399 of 0.4) |
| BAT_INT U4-22/23 -> Q103 (copper_path 6 A, 20 C) | 2.889 mOhm | **2.889 mOhm** (104.0 mW, unchanged; no BAT_INT-area copper touched) |
| length / octilinear minimum (route_oct_check, touched nets, complete) | | median **1.155**, p95 **2.98** (n 16); above 1.5: CE_N 2.95 and U11-FAULT 2.98 (slow enable/status, <= 3.5 by decision 1), U24-AVDD 1.86 (inherited B.Cu feed; only its pin stub was redone) |
| silkscreen (silk_tile.py + gate G1-G6) | ALL PASS | section 7 |
| teardrops | | edit.py removed the teardrop zones next to edited copper (section 9); **no headless teardrop API** in the AppImage pcbnew (`dir(pcbnew)` has no teardrop symbol): regeneration is a GUI step for the owner |

## 2. Inherited power items (closed 15 of 16)

Finding: the MCU supply was never routed. U3-6/7/8 (VBAT, VREF+, VDD on 3V_AO) had no copper, and U3-9, C160-2, C161-2, C162-2, R259-2, R160-2 and J7-5 (GND) had no via to the planes.
- **U3 3V_AO**: pins 6-8 joined by a 0.25 mm bar at their pad tips (y 82.85), pin 8 straight down to C160-1 (x 127.75), C160-1 -> C161-1 below the PD_PLUG_EVENT/CHG_INT vias (y 85.3), C161-1 -> R106-1 (y 85.2).
- **Source**: R106-1 -> via (123.3, 86.0) -> **In2** 0.4 mm (PWR_3V is allowed on In2 by rule 11) diagonal to via (117.2, 79.15), F.Cu into U12-5 (LDO output). 14.7 mm, ratio 1.17. The In2 run stays north of the 5V_LOGIC In2 trunk.
- **J7-1 (TC2030 VTref)**: escape east between the J7 NPTH holes at y 63.13 (0.30/0.31 mm to the hole edges), then F.Cu -> In2 -> F.Cu to C123-1, 22.5 mm (1.49).
- **GND**: one via per pad by `scripts/gvia.py` (nearest legal octilinear spot, In1+In2 GND under the land): C160-2, C162-2, R259-2, C161-2, R160-2, J7-5; U3-9 straight down into C160-2.
- **LDO_3V3**: C6/via cluster joined to U11-1 along y 54.8 (0.25 mm; neck_u11 0.15 mm applies, 0.177 mm to U11-2).
- **Not closed: 3V_AO R241-1 (188.42, 39.0)**, 69.5 mm from the nearest 3V_AO copper (AUX_DET pull-up in the headphone block). A long hr7 run (F/B/In2, 4 million nodes, 17 min) found no path; remedy otherwise: feed R241 from a local 3V_AO via on In2 from J7/U3 (about 65 mm of In2) or re-source the pull-up in the schematic (owner decision; not done, every net stays as drawn).

## 3. Task groups

### 3.1 U4 group (decision 3)
- **TS_SENSE via moved** from (152.87, 125.285) to (153.42, 125.6), straight below U4-16, B.Cu (153.42, 125.6)-(153.42, 127.235)-(153.17, 127.485). This frees the column under pins 12-15. TS to SW2 distance: B 1.31 mm (unchanged), F 1.88 mm.
- **CE_N**: U4-13 stub straightened into R103-2 (x 151.77 then east). CE_N R103-2 -> Q100-3 routed by hr7 around the west of U4 and north of L1/L2: 62.8 mm, 6 vias, ratio 2.95 (slow enable, inside 3.5 x). Closed.
- **CTRL_SDA / CTRL_SCL**: only one B.Cu lane exists west of the U4 south pins (between the GND via (150.77, 124.65), the VBUS_PD via cluster x 147.65-148.6 and the REGN via (148.79, 122.58)). Either net routes alone (SDA 45.4 mm, SCL 44.1 mm, ratio about 1.3); the second is then sealed. **SDA routed** (U4-15 -> TP15, closes one of RT-6's two CTRL_SDA items); **SCL open**. Remedy: drop one 0.6 mm VBUS_PD via of the five (charger input current check needed) or move the REGN via north by 0.6 mm, then route SCL beside SDA.
- **QON** (U4-12): pin pocket. The only via site below the pin (x 151.37) is 0.05-0.15 mm short of clearance between the U4-10/11 GND stub (x 150.65) and CE_N (x 151.77); below y 127 the REGN trunk (x 151.52-152.22) blocks. Remedy: move R103 (CE_N pull-up) 1 mm south-west so CE_N can drop to B.Cu at once, freeing x 151.4-151.9 for a QON fine via.
- **ILIM_HIZ**: R108-2 is boxed (C110, R108-1, ILIM stub); a path from the Q101 side exists (52.3 mm, 1.62) but is over the sense limit (ILIM is the SP3 victim and an analog programming node). Not closed.
- **CHG_INT** (U4-21): **sealed by a hard rule.** Pin 21 sits between the BAT_INT finger (north/east, zone outline x - y = 32.515) and the PROG/BTST2/BATP fan (south). A 0.5/0.2 via at the pin is 0.05 mm from PROG and would carve the thinned BAT finger; BAT_INT is at 2.889 of 2.9 mOhm (0.011 margin). hr7 found no exit. **Recommendation (design change, owner decision): read the charger status by I2C polling (BQ25792 status/fault registers) and leave U4-21 unconnected on the board, or accept a BAT_INT re-plan (wider SYS/BAT finger elsewhere) before a CHG_INT via is placed.** The schematic net is unchanged and still reported as unconnected.
- **CHG_ENABLE, CHG_SYS_ENABLE, Q101-G x2**: Q101-G is split by the AUD_SCL F.Cu detour that runs between Q102-3, Q101-1 and R110-2 (y 106-110.7); remedy: re-route that AUD_SCL stretch north of Q102 at y 104.3 after moving the LRCK stitch via (180.91, 103.87). CHG_ENABLE / CHG_SYS_ENABLE start at U3-38/42, see 3.6.

### 3.2 I2S hub to U6/U7 (decision 4)
- **U6 five-track fan built** (F.Cu, verticals out of the pins, 45-degree NE runs at x + y = 228.74 (AUD_SCL), 229.74 (AUD_SDA), 230.98 (SDATA), 232.19 (BCK lane, reserved), 233.40 (LRCK)). The I2C verticals jog 0.43/0.33 mm west inside NECK_U6 so the I2C-to-I2S gap outside the neck is 0.655 mm. The fan passes the C280-2 GND corner at 0.226 mm. The old AUD_SCL and SDATA escapes were removed.
- **Closed**: I2S_LRCK U6-12 (29.7 mm from the fan end, 0 vias, E along y 117 then NE x + y = 245.15 south-east of TP17, joining the y 103.8 LRCK branch), AUD_SDA U6-15 (29.3 mm, one via + GND stitch at (133.997, 103.539)); AUD_SCL rejoined its run at (124.205, 107.995); SDATA rejoined at (118.905, 114.595).
- **BCK (U6-13, U7-13) not closed, and why**: the BCK hub copper (R207-2, TP12) sits in a box walled by LRCK (x 142.895 vertical and its NW diagonal) and SDATA (x 148.55). On In2 the whole hub column x 141.5-149.5 is the VBUS_PD island (mapped in `t/`), so a B.Cu hop for an I2S net there violates section 14.1 (zero I2S B.Cu over an island). The 4-million-node hr7 search confirms no F-only path. Remedy (hub redesign): move the LRCK R208 -> TP14 wall west to about x 140.0 (over In2 GND), so BCK can hop on B.Cu at x <= 141.2 with a GND stitch and enter the TP12 box on F.Cu; then route U7-13 to the same node. Not attempted (budget).
- **AUD_SDA U7-15, AMP_FAULT_N x4, AMP_PDN, U7-PDN**: U6-9 (FAULT) is boxed by the LRCK fan on the west and R262-1 (3V3_AUDIO) on the north of R262-2, with PVDD vias (116.2, 124.6) on the only east lane; U3-25 is sealed (3.6). Remedy: rotate/move R262 0.8 mm south and re-route the C282 GND stub.

### 3.3 U24 codec block
- **VINR1 closed**: C212 moved 0.35 mm west (152.45 -> 152.1); its GND via moved (151.85, 79.0) -> (151.75, 78.75) off the lane; VINL1's diagonal moved 0.13 mm SE (x + y = 233.72); VINR1 = U24-4 north on x 152.745, NE (x + y = 232.59), east into the R201-2/C207-1 node. 5.6 mm.
- **XO closed**: Y200-2's GND via (150.9, 78.05) and stub removed (Y200-2/Y200-4 GND re-tied to C214-2 by a new 0.3 mm track, C214-2 has its own via); U24-9 -> north -> NE -> x 150.9 -> NW into Y200-3, 6.5 mm (1.02). The U24-8 AVDD stub was redrawn at 0.3 mm (old 0.6 mm stub was 0.18 mm from XO).
- **HA8**: C212 now 0.14 mm from C215 (0.4 tier). Compensated by R209 (0.011 mm, H2-R209 had 0.399 of 0.4); the count stays 122 but C215-C212 is a real tweezers-access item at the VREF/AVDD pair. Alternative that keeps 0.4 mm: move C215 0.26 mm west, which needs XO moved 0.2 mm west and is blocked by XI.
- Not closed: C204/C205/C233/C235-Pad2, USB_AUDIO_L/R, U2-VOUTL (feeds into the input block; pads boxed by their own RC partners, for example R229-1 is enclosed by its sibling NO2 loop).

### 3.4 Headphone mux U8/U9/U10
- **U10-INL- closed** (decision 2 item): hr route U10-1 -> via -> B.Cu -> via -> C239-2, with the last F.Cu diagonal ended inside the pad at (187.2675, 61.2) so it keeps 0.5 mm audio_clear from the 3V3_AUDIO track (y 60.35). 9.0 mm, ratio 1.0, both vias within 1.5 mm of GND.
- Not closed (12): COM1/COM2/NC1/NC2 (0.5 mm pin pitch; a via beside a pin stub is 0.075 mm short), HP_L (walled by the U9-8 3V3_AUDIO feed at x 184.29 and the 3V3 track at y 60.35), HP_SEL_A/B (pins 1 boxed by the NO1/NO2 escapes), HP_G0, HP_EN, HP_OUTL, AUX_L, AUX_DET. Remedy: feed U9-8 from a via north of the pin on In2 (removes the x 184.29 wall), and re-place R226/R227/R229 next to their pins.

### 3.5 USB-C/PD, regulators, gauge
- **Closed**: U11-FAULT (8.4 mm, 2.98, slow fault), U25-FB (manual, 0.2 mm, U25-17 -> E -> NE parallel to COMP at 0.25 mm -> R251-1 from below; 2.0 mm+ from SW), U25-MODE (manual, between U25-12 and C314-2), U12-EN pin link (U12-1 via -> U12-3, 2.4 mm), BT_FORCE_PWM (1.62), BT_PWR_EN R152-1 -> U15-1 (3.25), USB_CC2 D5-2 -> J1-B5 (18.6 mm, 2.12; CC is a 300 kbit/s config line, not USB data).
- **Not closed**: U14-FB (R140-2 boxed by C141/C142 5V_LOGIC, the L2 switch track 0.5 mm away would break switch_sensitive for a via; the only router path puts a via in the R140-2 pad: rejected, hand assembly), 5V_LOGIC_EN R142-1 -> U14-1 (the FB loop around R142 walls it), U11-ADC4, R18, PD_PLUG_EVENT, PD_SINK_EN, PDCTRL_SCL (U11 fine-pitch pockets, VIN_LOW diagonal over pins 36-38), USB_CC1, USB_CC2 C183-1 -> D5-2, U12-EN B-track -> F track (17 mm), GAUGE_ISO_N.

### 3.6 MCU U3 escapes (the dominant cause)
14 remaining long nets start at U3 pins that have no legal exit: east pins 24/25 are fenced by the ADC_INT escape diagonal (U3-26 -> via (136.2, 77.2) crosses in front of them with 0.37 mm room), and the north row (U3-36/38/42/45/46/47) is covered by the PDCTRL/NRST/SWCLK/ENC fan. hr7 with fine vias and In2 (rule 11 nets) still found no exit (`exp 0..8`). Closed: BT_UART_RX (65.5 mm, 1.21, 8 vias) and 5V_LOGIC_EN (55.9 mm, 1.14, U3-18 -> U14-1). Remedy: a U3 escape redesign (one via per pin to In2 just outside the pin row, re-route ADC_INT and the north fan), which is the precondition for AMP_BOOST_EN, AMP_FAULT_N, BT_PWR_EN (U3-36), CHG_ENABLE, CHG_SYS_ENABLE, HP_EN, HP_SEL_A/B, HP_G0, AUX_DET, SWDIO, SWCLK, NRST.

## 4. Task 5 review items
- **BATP vs BTST2/SW2**: the 0.20 mm BTST2 gap is the U4-18/19 pin pitch over the 0.8 mm fan-out and cannot be widened. The 0.325 mm gap to the SW2 via V2 (155.6, 126.2): moving V2 0.57 mm NE gives 0.83 mm, but then V2 is outside NECK_U4 and DRC applies switch_critical 2.0 mm (2 violations, build C0 iteration 1). The neck relaxation is what makes the current geometry legal, so **V2 stays**; a real fix moves the BATP/TS lanes 0.4 mm south together with the SYS_RAW via row y 129.0 (not done).
- **BAT_INT**: 2.889 mOhm, unchanged; no BAT_INT-area copper was edited (the TS via move is outside the finger).

## 5. Clean-up (S4-S6 style)
- Colinear splits merged: 5 pairs (AUD_SDA, AUD_SCL x2, I2S_SDATA, TS_SENSE); checker colinear_splits 0.
- Stitching: every new sensitive via has a GND via within 1.5 mm (parcheck 17 vias, 0 over 1.5). `route_oct_stitch.py` needs a continuation manifest (C0 lock) and was not run on these hand-edited boards; the only new sensitive B.Cu runs are U10-INL- (4.8 mm, two vias stitched) and the AUD_SDA hop (1.65 mm).
- r7 joints < 80 degrees: 19 (all inherited power/In2 copper; none on new copper). New-copper hygiene (route_oct_check on the touched nets): T-junctions 3 (LRCK and AUD_SDA join existing runs mid-segment; VINR1 joins its node), 90-degree joints away from pads 3, short pad exits 12 and bend-spacing 13 (mostly fine-pitch pins and inherited LDO_3V3 In2 copper), dangling-end flags 8 (track ends inside pads off the pad centre and the inherited R241/LDO_3V3 ends; DRC reports no dangling track).
- Teardrops: not regenerated (no headless method; owner GUI step). edit.py removed 35 teardrop zones next to edited copper over the seven builds (listed per build in `t/editlog.md`).

## 6. Remaining open connections (64)

| group | conns | nets | cause / remedy |
|---|---|---|---|
| MCU U3 pin escapes | 16 | AMP_BOOST_EN, AMP_FAULT_N (U3), BT_PWR_EN (U3-36), CHG_ENABLE, CHG_SYS_ENABLE, HP_EN, HP_SEL_A x2, HP_SEL_B x2, HP_G0 x2, AUX_DET, SWDIO x2, SWCLK | 3.6: U3 escape redesign (In2 vias per pin, re-route ADC_INT and the north fan) |
| U4 charger | 6 | CTRL_SCL, QON, ILIM_HIZ, CHG_INT, Q101-G x2 | 3.1; CHG_INT sealed by the BAT_INT budget: I2C polling recommended |
| I2S / AUD I2C / amp control | 9 | I2S_BCK x2, AUD_SDA (U7, U24), AUD_SCL (U24 side), AMP_FAULT_N x3, AMP_PDN, U7-PDN | 3.2: hub LRCK wall to x 140, R262 move |
| U24 inputs / USB audio | 9 | C204/C205/C233-Pad2, C235-Pad2 x2, USB_AUDIO_L, USB_AUDIO_R x2, U2-VOUTL | 3.3: input-block re-place (R229, R225, C235) |
| headphone mux | 9 | U8-COM1/COM2/NC1/NC2, HP_L, HP_OUTL, AUX_L | 3.4: U9-8 feed to In2, re-place R226/R227 |
| USB-C / PD / regulators / gauge | 12 | U11-ADC4, R18, PD_PLUG_EVENT, PD_SINK_EN, PDCTRL_SCL, USB_CC1, USB_CC2 (C183), U14-FB, 5V_LOGIC_EN (R142), U12-EN (B->F), GAUGE_ISO_N, CTRL_SDA (98.8,74.2 -> 123.9,78.8) | 3.5 |
| BT / debug | 3 | BT_RST_M, BT_SYS_CFG, NRST (J6) | BM83 keep-out plus the U3 north fan |
| inherited power | 1 | 3V_AO R241 | 2 |

## 7. Gate record (RT-7)

From `t/RT-7.gates.txt` (independent of the editing tools; RT-7 = G1 + silk_tile):
- kicad-cli DRC: **0 violations, 64 unconnected** (RT-6 rules beside the board, project footprint library).
- gates4 vs RT-6: 360 footprints, 1194 pads, moved C212 and R209 only (both allowed), **pad_net_diff []**; base copper 2972 items, 33 removed/changed (all listed in the edit reports, 0 unexpected), **locked 2939 items, SHA-256 `899de752eff497f356f98f71b6fd26ae7c19b2f3ad2e5982a4797e4b4df9c745`**; 234 items added, 188 new segments, 520.4 mm, **0 not exact 0/45/90**.
- Rule hashes: `.kicad_dru` ce43baa1... and `.kicad_pro` aa88e8c9... = RT-6 (no exemption added). Sentinel FIRES (81 items).
- Pour check RT-6 -> RT-7: OK (foreign unconnected 62 -> 55).
- parcheck: sensitive pairs 0; sensitive vias 17, 0 farther than 1.5 mm from GND; BM83 new F.Cu 0 mm.
- r7: joints < 80 / < 30 deg 19 / 7 (RT-6 19 / 7); exact segments >= 5 mm 1853 mm (RT-6 1646); BM83 GND 2.3, SYS_PWR 2.0 (unchanged); switch proximity unchanged except TS_SENSE F 1.88 mm (new via position).
- HA8: 122 failing pairs (new C215-C212, gone H2-R209).
- BAT_INT: 104.0 mW at 6 A = **2.889 mOhm**.
- Silk: `silk_tile_gate.py` G1-G6 **ALL PASS** (`RT-7.silkgate.json`).
- Length (route_oct_check, 24 touched nets, 16 complete): median 1.155, p95 2.98, max 2.98; nets above 1.4: BT_FORCE_PWM 1.42, CE_N 2.95, U11-FAULT 2.98, U24-AVDD 1.86 (reasons in section 1).

## 8. Iterations (AG13) and log

- Power (A): A1 build 1, DRC 0. Iteration count 1.
- Regional hr7 runs (B): W/N/S on A1 (5 accepted by the length policy: U11-FAULT, BT_FORCE_PWM, BT_PWR_EN, USB_CC2, U10-INL-; rejected U14-FB 1.96 sense, U8-NC2 5.48 audio). B1 build 1 duplicated A1 vias (wrong base plan, 11 violations), build 2 DRC 0.
- U24/U25 (C0): build 1 (SW2 via move: switch_critical x2, crystal GND island), build 2 (dangling crystal GND link), build 3 DRC 0. Three builds.
- U4 pocket: hr7 run 1 (CTRL_SDA routed under the U4 body: rejected; IC-body keep-out added to hr7), run 2 (stale TS via in the model: hr7 now applies via deletions from base plans), run 3 (SCL), retry SDA with large window (sealed), both I2C orders on E1 (one of two each). CE_N on F1 in both orders (closed). Three iterations plus the order test.
- U6 fan (E1): build 1 (CTRL_SDA conflicts, BCK dangling stub), build 2 DRC 0.
- Long nets: 6 parallel workers (24 jobs) + 3 U3 workers (13 jobs) + 3V_AO R241: 2 closed (BT_UART_RX, 5V_LOGIC_EN), rest `no exit`/`no path` logged.
- Final: G1 (CE_N, 5V_LOGIC_EN, merges, R209) DRC 0 -> RT-7 (silk).
- Logs: `t/j*.json` (jobs), `t/j*.log` (hr7 output), `t/*.hrlog.json`, plans `t/plan*.json`, edit reports `A1/B1/C0/D0/E1/F1/G1.edit.json`.

## 9. Edit log

Full table in `ai-files/pcb/work-route7/t/editlog.md` (generated from the edit reports by `scripts/editlog.py`: every deleted/changed/added segment and via with net, layer, width and coordinates, footprint moves and removed teardrops per build). Part moves:

| ref | old | new | mm | reason |
|---|---|---|---|---|
| C212 | (152.45, 80.2) rot 90 | (152.10, 80.2) rot 90 | 0.35 | VINR1 lane at U24-4 (decision 2) |
| R209 | (152.95, 91.95) rot 90 | (152.94, 91.945) rot 90 | 0.011 | HA8 compensation (H2-R209 0.399 -> >= 0.4) |

HF decoupling: C212 (VREF) moved 0.35 mm towards U24-6 in x; its pad stays within 1.5 mm of the pin. No other decoupling cap moved. Regenerate position/CPL files and stencil for C212 and R209.

## 10. Files (`ai-files/pcb/work-route7/`)

- Result `RT-7.kicad_pcb/.kicad_pro/.kicad_dru` (= G1 + silk_tile). Gate files `RT-7.drc.json`, `RT-7.gates.json`, `RT-7.check.json/.txt`, `RT-7.r7.json/.txt`, `RT-7.par.json/.txt`, `RT-7.rulehash.txt`, `t/RT-7.gates.txt`, `t/RT-7.ha8.json`, `t/RT-7.cp.json`, sentinel in `sentinel/`.
- Evidence `evidence/rt7-F.png`, `evidence/rt7-B.png` (+ .svg), crops `evidence/u3pwr.png`, `u6fan.png`, `u24.png`, `u4s.png`, `u25.png`.
- Scripts (`scripts/`): RT-6 set plus `hr7.py` (hr.py + In2 layer for rule-11 nets, IC-body keep-out, island-via option, via deletions from base plans, 0.5/0.2 fine vias only inside necks), `gvia.py`, `accept.py` (length policy), `mkjobs.py`, `merge.py`, `colmerge.py`, `editlog.py`, `gates7.sh`, plan builders `planP1/U4S/U24/T5/U25/U6/E1.py`.
- Build chain: RT-6 = R0 -> A1 (power) -> B1 (regional hr7) -> C0 (U24, U25) -> D0 (CTRL_SDA, TS move, INL-, U12-EN) -> E1 (U6 fan) -> F1 (CTRL_SDA, BT_UART_RX) -> G1 (CE_N, 5V_LOGIC_EN, merges, R209) -> RT-7 (silk_tile).
- Work folder size: intermediate boards and geo exports; do not commit them.
