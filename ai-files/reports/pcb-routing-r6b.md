# Routing R6b (2026-10-08): signals and GND on R6a-final (work in progress)

Work copies only: `ai-files/pcb/work-r6/R6b-*`. R6a power copper is locked and unchanged.

## Progress notes
- R6b-base = R6a-final + B.Cu keep-out rule areas BKO_U6 (900 mm²), BKO_U7 (870 mm²), BKO_BM83, BKO_ADC, BKO_CODEC, BKO_MUX (`route_r6b_base.py`). Enforced by DRC rules `bko_tracks`/`bko_vias` in `R6b.kicad_dru`. Power and GND classes are exempt; Net-(U7-BST_B+) and Net-(U25-BOOT) are explicit exceptions. Base DRC: no new items. Open edges 471 (Default 137, AUDIO 85, I2C 24, I2S 22, USB 9, PWR_LOCAL 3, GND 191).
- Router: `route_r6b_route.py` (route_p2 A* on F.Cu+B.Cu; SW copper 1.0 mm / 2.0 mm for BATP-FB-COMP-ILIM; BKO_* on B.Cu; sub-floor widths only in NECK areas; no signal via inside any non-GND In2 island; 0.5/0.2 vias only in NECK; GND via beside each AUDIO/I2S via). GND: `route_r6b_gnd.py` (dogbones) + `route_r6b_gnd2.py` (A* track to the nearest legal via spot). `route_r6b_widen.py`, `route_r6b_rip.py` for clean-up.
- Pass 1 (crystals → AUDIO → I2S → I2C → Default → PWR_LOCAL, shortest first) + GND dogbones: 471 → 177 open edges.
- Found blockers (R6a copper, not modified):
  - Y200 XI/XO: enclosed by the R6a 3V3_AUDIO loop (C219 → y 79.0 → via 150.0,81.2) and the U24-AVDD loop. Both crystal-to-U24 links are cut off.
  - U24 VINL1-3/VINR1-3 and VREF side: the R6a U24-AVDD track runs down x ≈ 154.7 beside the top pin row, and its bottom loop walls the pins off from C206-C211/R205.
  - U2 VOUTL/VOUTR/VCOM: walled off by the R6a VCCP1I/VCCP2I and VCCCI loops.
- USB D+/D- (placement): J1 pin order and D1 put DP on the right-hand side of the pair. R171 (DP) sits above R172 (DN) beside U2, so the pair must cross once. Every island-free via spot on the path is taken: the In2 USB_VBUS island covers 135.5-153.5 × 27.4-54.6, VBUS_PD covers x 141-149.3 from y 55.2, and the R6a 5V_LOGIC via sits at (150.1, 61.3).

## Final (R6b-final, continuation by Sonnet)
- Starting point R6b-c12 (128 DRC unconnected). Extra full pass over every remaining non-GND net (`R6b-d1`, 69 nets, A* with all tiers): 0 nets completed, so no gain; combined with the earlier 12 rounds the stop criterion is met. d1 not adopted.
- `route_r6b_final.py`: removed 5 dangling vias (U4-BATP, U8-COM1/COM2, HP_L, PD_PLUG_EVENT) and widened the VMID_HP 0.2 stub to 0.25. Output `work-r6/R6b-final.kicad_pcb/.kicad_pro/.kicad_dru`; renders `route-r6b-top.png`, `route-r6b-bottom.png`.
- DRC: clearance 0, shorts 0, dangling 0, isolated_copper 0, track_width 0. Remaining: 2 hole_clearance (SW100 pad 1/pad 3 vs its NPTH, 0.175 < 0.25; footprint/placement issue, not routing), silk-only items (20 silk_over_copper, 8 silk_edge, 4 silk_overlap).
- Open edges: 123 (GND 27, Default 41, AUDIO 23, I2C 10, I2S_CLK 10, USB 9, PWR_LOCAL 3).
- Vias: 581 total (signal 361, GND 220). I2S: BCK 112.6 mm (0 vias), LRCK 3.3 mm (partial), SDATA 62.0 mm (3 vias). USB D+/D-: not routed, so no skew to record. Via-in-pad script, EP/via-field counts and antenna keep-out were not re-run in this continuation (only DRC and open edges).

## Why the remaining edges are impossible without changes (R6a copper not modified)
- Y200 XI/XO, U24 VINL/VINR/VREF: enclosed by the R6a 3V3_AUDIO loop and U24-AVDD track (x about 154.7 and its bottom loop). Need: reroute/open the U24-AVDD and 3V3_AUDIO loops (e.g. feed AVDD from the pad side with a short stub and move the 3V3_AUDIO return to In2/B.Cu).
- U2 VOUTL/VOUTR/VCOM: walled off by R6a VCCP1I/VCCP2I/VCCCI loops. Need those loops shortened or put on B.Cu.
- USB D+/D-: pair must cross once; every island-free via spot is taken (In2 USB_VBUS island 135.5-153.5 x 27.4-54.6, VBUS_PD from y 55.2, R6a 5V_LOGIC via at 150.1,61.3). Need: swap R171/R172 (or J1 DP/DN order) so no crossing, or shrink the In2 USB_VBUS island.
- U24 LDO x2, U10 CPP (PWR_LOCAL): same R6a enclosure; need the R6a loop changes above.
- Remaining Default/I2C/GND edges are in the same walled-in zones or need vias inside non-GND In2 islands; not retried by hand in this pass (no hand routing was done in the continuation).
