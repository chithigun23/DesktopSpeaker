# Routing R6c (2026-10-08): local R6a rework at U24/Y200 and U2, partial signal routing

Work copies only (`ai-files/pcb/work-r6/R6c-*`). Final board `R6c-final.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`). Renders `ai-files/pcb/route-r6c-top.png`, `route-r6c-bottom.png`. Nothing in `DesktopSpeaker-kicad/` was touched. No commit.

## Result
- Open edges (fragment-aware, `route_p2_open2.py`): **123 -> 105**. Default 37, GND 26, AUDIO 16, I2C 10, USB 9, I2S_CLK 4, PWR_LOCAL 3 (U24-LDO x2, U10-CPP, inherited from R6a, unchanged). All other power classes are at 0, same as R6a-final.
- DRC: clearance 0, shorting 0, track_width 0, dangling 0, isolated_copper 0, hole_clearance 0 (SW100 gone). Remaining: silk only (silk_over_copper 20, silk_edge 8, silk_overlap 4) and 1 `lib_footprint_mismatch` for SW100 (board copy differs from the library until mirrored).
- Closed 18 edges: U24 XI, XO, VINL1-3, VINR2 (one of two), LRCK, DOUT; U2 VCOM, XTO; AMP_PDN; BT_RST_N; PROG; C230 net; 1 GND.
- Round 2 (all remaining nets, margins 10/30/70 mm) was stopped after 7 nets with 0 gain (about 40 s per net), so the "two rounds without gain" criterion is only partly met.

## R6a copper changed (local, power connectivity kept; power opens identical to R6a)
- Removed and re-routed: all copper of Net-(U24-AVDD), VCCP1I, VCCP2I, VCCCI; 3V3_AUDIO F.Cu tracks in x 139.5-151.5 / y 72.5-86, via (150.0,81.25) and the two short In2 links beside it (In2 trunk 150.35,81.55-152.7,77.55 now comes from the A* re-route).
- AVDD: pin 8 stub 0.2 mm to C215, then via + B.Cu 0.3-0.4 mm to FB200 and C216 (PWR_LOCAL B.Cu). VCCCI: via + B.Cu 0.4 mm (U2 pin 10 to C175, via moved to (156.5,61.35)/(156.5,65.95)). VCCP2I 0.2 mm (below the 0.25 plan value, neck-style). VCCP1I via A*.
- 3V3_AUDIO U24 pins 13/14 now leave north then west on y 81.48 (0.2 mm) to the C217/C219 group; the GND wall (C213.2/C226.2 to pin 15) was removed and those two pads tied by a short track; one A* GND attach used.
- C206-C209 GND stubs narrowed 0.6 -> 0.3 mm (opens the VIN corridor). 3V3_AUDIO bend near R226 moved 0.2 mm (audio clearance).
- DRC rule exceptions: `bko_tracks`/`bko_vias` now also exempt Net-(U24-AVDD), VCCCI, VCCP1I, VCCP2I (power links on B.Cu).

## SW100 (board copy only; mirror in the library)
Pads 1 (two pads, 0.9 x 1.8 mm at x=138.57 / 141.57, y=25.245) were 0.175 mm from the NPTH holes (0.9 mm at 137.945/142.195, y=26.745). Changed to 0.9 x 1.7 mm with the centre moved up 0.05 mm (y 25.195), so the pad bottom stays 0.7 mm from the hole centre (0.27 mm gap).

## Router changes
`route_r6c_route.py` adds `R6C_M` (grid margin, 0.012 passes the 0.7 mm gaps between the 1.3 mm-pitch GND vias in the VIN filter column; DRC confirmed no clearance errors), an exception list for power B.Cu links and `--verb`. Findings: failures in a batch were mostly order dependence (XO routed first blocks XI; the A* has no 0.2 mm neck clearance for I2S_CLK neighbours), so XI was hand-routed (pin 10 north on x=149.745, then diagonal to Y200.1, 0.2 mm). Helpers: `route_r6c_hand.py` (explicit tracks/vias), `route_r6c_rip.py`, `route_r6c_setw.py`, `route_r6c_dbg.py` (obstacle map PNG), `route_r6c_gates.py`, `route_r6c_eval.sh`.

## Remaining open edges and reasons
- USB (9: DP 4, DN 3, U2-D+/D- 2): not routed, so no skew value. The pair must run about 30 mm from J1 to U2. BT_MFB is a long F.Cu run at y~41.8 (x 133.5-154.2) across the corridor and signal vias are barred in the In2 USB_VBUS island (135.5-153.5 x 27.4-54.6). Needed: move that BT_MFB run to B.Cu with vias west of the island (e.g. at about (128.8,37.05), clear of the In2 USB_AUX_5V diagonal) and hand-route the pair (R171/R172 do not need swapping at U2: D+ is the left pin and the upper resistor). Not done.
- AUDIO 16: U24 VINR1/VINR2/VINR3 (the VIN column still walled by cap/GND via columns and B.Cu BKO_ADC), U2 VOUTL (surrounded by VCCP1I/VCCP2I/XTO pin neighbours), U10 INL-/INR-, U8 COM1/COM2, U9 NO2, BT_AUDIO_L/R, C205 net, HP_L, USB_AUDIO_R: A* finds no path (pad enclosed); needs hand work.
- I2S_CLK 4: U24 BCK, I2S_LRCK x2, I2S_SDATA: BCK/LRCK are enclosed at the U24 bottom row, LRCK/SDATA are long runs with no free corridor under the 0.4 mm clearance.
- I2C 10 (AUD_SCL/SDA, CTRL_SCL/SDA): long runs across the board, no window found; AUD_SDA blocked at U24 bottom.
- Default 37 and GND 26: same enclosures or long cross-board routes (for example 5V_LOGIC_EN about 90 mm); GND needs vias in positions blocked by In2 islands or pads. Not retried by hand.
- PWR_LOCAL 3: U24-LDO (C213 is boxed in by the 3V3 pins, pin 11 crosses the 3V3 link), U10-CPP: as in R6a.

## Gate numbers (R6c-final)
- Vias 594 (GND 221, signal 373; R6b 581). EP arrays: U6 16, U7 16, U25 8 (U11 8 via footprint, not counted by the script). Antenna keep-out: no new copper (one inherited GND track at 89.4,26.4 touches the bbox). Via-in-pad script: 51 hits = 48 EP array vias + inherited signal vias (R152, R10, C204, C234, R224, J7, TP19, R242, R15, R185) + 1 new: C215.1 AVDD via at (151.15,80.7) (C212 sits 0.6 mm away, no free spot). C175 via was moved off the pad.
- I2S lengths: BCK 112.6 mm (0 vias, partial), LRCK 3.3 mm (partial), SDATA 62.0 mm (3 vias), U24-LRCK 2.0 mm. USB skew: not applicable (not routed).
