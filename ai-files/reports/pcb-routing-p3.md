# Routing P3 (2026-10-07): bootstrap caps + remaining signals - DRAFT, not complete

Work only in `ai-files/pcb/work-p3/` (start `work-p2/R4-final`). Final board `work-p3/R5-final.kicad_pcb` (+ `.kicad_pro` = P1/P2 project, `.kicad_dru` = identical to R4: no new rule relaxations; `switch_clear` 0.3 mm and `neck_exempt` 0.2 mm from P2 only). Renders: `ai-files/pcb/route-p3-top.png`, `route-p3-bottom.png`. DRC/open lists: `R5-final.drc.json`, `R5-final.open2.json`. `DesktopSpeaker-kicad/` untouched, no build script run, no commit.

## 1. Result (KiCad unconnected items, R4 -> R5)
Board wide 243 -> 67. By class (R4 P1-oracle -> R5 KiCad): SWITCH 2->0, BOOT 3->0, SPK_OUT 0->0, POWER_HI 0->0, PVDD 0->2 (C274.1 to the B.Cu PVDD run, plus one F.Cu pour fragment `L1_PVDD_AMP_1`), AUDIO 16->1, USB 7->3, I2S_CLK 11->4, I2C 23->8, SIGNAL 42->20, PWR_LOCAL 12->4, PWR_3V 52->7, PWR_5V 16->1, GND 75->17.
DRC (project rules): clearance 0, shorting_items 0, track_dangling 0, via_dangling 0, isolated_copper 0, items_not_allowed 0, courtyards_overlap 0. Inherited: hole_clearance 2 (SW100), drill_out_of_range 8, silk_* 43, lib_footprint_issues 199, skew_out_of_range 3 + diff_pair_uncoupled 1 (USB pair still open). **track_width 199 (unchanged from R4)**. Copper: F.Cu 1640, B.Cu 255, In2 215 segments, 489 vias (R4: 1880/123/163, 265).

## 2. Bootstrap caps (step 1) - done
C299/C301 (U7) moved up 2.5 mm (y 132.45/132.49 -> 129.95/129.99). U6: C286 -> (117.597, 131.0), C288 -> (119.467, 129.7) (1.7 / 2.1 mm outward, hand-placed so the pin fan-out OUT_A-, BST_A-, BST_B-, OUT_B- (0.5 mm pitch) squeezes to 0.4 mm centres past C285 and fans out without crossings; `helpers/route_p3_hand4.py`). U6 BST_A-, BST_B-, OUT_A-, OUT_B- and U7 BST/OUT are all connected on F.Cu, no relaxation. U6 OUT_A+ (pin 2 -> C285.2 -> L201) was routed after fixing the router (below) using one via at (116.0, 131.7).

## 3. Router fixes (helpers/route_p2_core.py, route_p2_lib.py are edited in place; scripts `route_p3_*`)
- `route_net` no longer gives up on the closest pair; tries up to 6 pairs, 80 joins per call.
- NPTH holes (0.27 mm) are now respected by track simplification/width fit and the raster (R4 had unchecked hole_clearance growth); footprint rule areas with track/via keep-out (J7) are obstacles; vias are checked against all layers after emit (snap-to-pad-centre had dropped a via onto an In2 track).
- Bug found late: a first edit treated every board rule area (`SW_NOPOUR_*`, pour-only keep-outs) as a routing obstacle; fixed (only track/via keep-outs count). Early P3 rounds (to B3) ran with it; rounds F/G did not.
- `route_p3_gnd.py`: strips via-less GND stubs and re-attaches GND pads (GND 75 -> 17); `route_p3_cycle.sh` = DRC-driven rip/re-route.

## 4. Not routed (67 edges) - why
Rounds E2 -> F1 -> H8 -> G1 -> G2: 93 -> 69 -> 67 -> 67 -> 67 (two rounds without gain). The rest need placement or via-size changes, not more search: pad escapes of 0.5 mm-pitch ICs (U3 MCU, U6/U7, U4, U10, U11, J1/J7) are boxed in by 0402 neighbours and 0.6 mm minimum vias.
- GND 17: 16 SMD GND pads (U10.2/3/15, U9.3, U4.27, U6.20, U7.5/20, U2.26, U11.31, U24.7, C296.2, U5.4, R180.2, U14.3/8) have no legal via within 6 mm; not in a pour.
- I2C/SIGNAL (28): AUD_SCL/SDA (U6, U7, U3), PDCTRL_SDA, CTRL_SCL, AMP_PDN/BOOST_EN/FAULT_N, MCU SWDIO/SWCLK/NRST (J7 via keep-out), CHG_INT, HP_G1, REGN, PROG, Q103.G, FSW, SS, R18.1, U10.CPP, C233.2.
- Power rails: /3V3_AUDIO 5, /3V_AO 1, /3V8_BT 1, U6/U7 AVDD, U24 AVDD; I2S_CLK 4 (SDATA, BCK to U6/U7), AUDIO 1 (U24 VINL), PWR_5V 1.
- USB: DP 2 edges (J1.A6 to R171, track to J1), DN 1 (J1 to R172): pair not completed, so skew not measurable (DRC skew 3 inherited). CC2 2.
- Rule relaxations: none. Neck exemptions: unchanged (199 track_width items, all 0.2 mm pad-pitch necks).

## 5. Next
Placement nudges at U6/U7 (left column C276/C289 vs pin 1-2 corridor), U3/J7, U4/U11, U10; GND vias via-in-pad decision; then a short re-run of `route_p3_run.py` (no `--only`), `route_p2_fix.py`/`route_p3_gnd.py`, `route_p3_cycle.sh`. Runs are not bit-reproducible; `R5-final` is the checked state.
