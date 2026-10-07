# Routing P1 (2026-10-07): Freerouting diagnosis and chunked routing - DRAFT for coordinator adoption

Everything is a copy in `ai-files/pcb/work-p1/`. Final board: `R3-final.kicad_pcb` (+ `.kicad_pro/.kicad_dru`, the project files with the netclass-pattern fix). Nothing in `DesktopSpeaker-kicad/` was touched. Renders: `ai-files/pcb/route-p1-top.png`, `route-p1-bottom.png`, plots `route-p1-plot-F.Cu/B.Cu/In2.Cu.png`.

## 1. Diagnosis: why phase 0 left so many nets open
1. **Class widths (main cause).** Freerouting routes at the class width (0.25-0.5 mm); 0.4 mm-pitch QFN pads (0.2 wide) and 0402 escapes cannot be left at that width. Isolated test of 3 trivial nets: width 0.25 -> 0/3 routed, width 0.2 -> 2/3. Fix: route at 0.2 mm (0.25 on AUDIO/I2S/USB), widen afterwards segment by segment where room allows (`route_p1_widen.py`).
2. **P0 GND stubs/vias** (203 vias) as protected obstacles: pass-1 unrouted 99 -> 74 when removed. Fix: strip P0 vias before routing (`nowire.kicad_pcb`), re-add GND/rail vias afterwards in free space (`route_p1_vias.py`) and let Freerouting fan the rest out to the In1 plane (dedicated GND run).
3. **Measurement bug:** `kicad-cli drc` JSON caps `unconnected_items` at 499, so P0 "open" numbers were lower bounds. Real oracle: `route_p1_open.py` (own union-find incl. zones). Real baseline (non-GND): 208 nets / 504 edges open.
4. **Project bug (30 nets):** KiCad netclass patterns do not support `[..]`: Net-(C20[0-5]-Pad2), C23x, U10-IN[LR]-, U24-VIN.., U2-VOUT[LR], U1-AOHP[LR] (AUDIO) and the 6 SPK_OUT filter nets were class SIGNAL, so audio_clear/width_audio/pvdd_clear did not apply. Fixed in the project .kicad_pro (coordinator); DRC below uses the fixed file.
5. **Freerouting facts:** `-mp` = passes; the SES holds the LAST pass and passes oscillate (74 -> 126 -> ...): use `-mp 1` per chunk. SES import into a board with tracks drops tracks of nets not in the SES: use `route_p1_post.py merge`. Wires of nets not in the DSN network make Freerouting hang on the SES write ("net not found"): all foreign copper is converted to netless keepout paths/circles (audio/I2S/USB copper inflated by a 0.5/0.4 mm halo). Not causes: B.Cu GND plane, F.Cu pours/keepouts, In2 planes (each about +-10 unrouted), clearance 0.2 vs 0.15.
6. The DSN needs the antenna keep-out on F.Cu (the P0 filter deleted it) and an edge frame: one run laid a 22 mm audio track along the edge through the BM83 keep-out. Both are re-added in `route_p1_dsn.py`.

## 2. Method (stage 2/3)
- DSN rules via `route_p1_dsn.py` (config json): width 0.2 (AUDIO/I2S/USB 0.25), clearance 0.21 for all classes (so DRC 0.2 holds), AUDIO/I2S/USB on F.Cu only (no vias), In1 power, In2 planes kept, B.Cu GND plane and F.Cu pours dropped. SWITCH/POWER_HI/PVDD/SPK_OUT not routed.
- The plan clearances 0.5/0.4 as router class clearance collapse routing (audio 0.5: 52 of 53 open; critical nets routed last: 21 of 27 open). Working method: critical nets first at 0.21; later runs see them as keepouts with the 0.5/0.4 halo; DRC (audio_clear, clk_clear, edge, rf_keepout, shorts, dangling) then removes the lower-class net (whole net) and it is rerouted (`route_p1_fix.py`, `route_p1_cycle.sh`, `route_p1_rounds.py`).
- Order: AUDIO/I2S/USB first, then SIGNAL/I2C/PWR_*/BOOT in chunks of 10-15 nets, shortest span first, failed nets pruned (no dangling copper). Rounds repeated until no gain; managed-class edges plateau at about 105-170 because each DRC cleanup reopens some nets.

## 3. Result (R3-final)
Open edges (union-find), start (P0 board) -> R3-final:
AUDIO 85 -> 17 | I2S_CLK 22 -> 11 | USB 9 -> 7 | SIGNAL 143 -> 35 | I2C 24 -> 23 | PWR_LOCAL 23 -> 12 | PWR_3V 69 -> 52 | PWR_5V 25 -> 14 | BOOT 11 -> 2 | GND 274 -> 79. Untouched: SWITCH 30, POWER_HI 35, PVDD 17, SPK_OUT 12 (94).
Managed classes without GND: 440 -> 173 edges (61 % routed); 88 nets still open in total.
- DRC (project rules): clearance 0, shorting 0, via_dangling 0, track_dangling 0, hole_to_hole 0, edge 0, rf_keepout 0; track_width 45 (pin necks: PWR_5V 34, I2S 7, AUDIO 4); isolated_copper 12 (In2 island fragments SYS_RAW/VBUS/3V3_AUDIO without a via: power work); inherited: silk 3 types, drill_out_of_range 8, hole_clearance 2; skew_out_of_range 3 (USB pair unrouted).
- Copper: F.Cu 1673 segments, B.Cu 76, In2.Cu 174; vias 221 (210 x 0.6/0.3, 11 x 0.8/0.4; GND 96). Antenna keep-out: 0 hits. I2S_LRCK 2.4 mm, USB D+/D- (U2 side) 2.4/4.0 mm; USB_DP removed (a 167 mm detour), so no pair skew data.
- Widths widened to class preference where clearance allowed (SIGNAL 0.25, I2C 0.3, PWR_3V 0.5, PWR_5V up to 1.0, AUDIO 0.3).

## 4. Still open (manual), by block and why
- **AUDIO (17):** VMID_HP (4), USB_AUDIO_L/R (4), U24 VINR1/VINR2 (4), BT_AUDIO_L/R, C200/C204 nets, U8-COM2: F.Cu-only without vias around U24/U8/U9 (a test with vias routed 24 of 34).
- **I2S/USB (18):** I2S_BCK/LRCK/SDATA U2 -> U24, U24 LRCK/XO, USB_DP/DN J1 -> U11 -> U2: long F.Cu-only runs through dense areas.
- **I2C (23) / control (35):** AUD/CTRL/PDCTRL I2C, SWD/NRST, HP_SEL/G/EN, ADC_INT, BT_PWR_EN, PD_SINK_EN, USB_CC1/2, U4 QON/PROG, U25 SS, U2 SEL0: long cross-board nets from U3 and fine-pitch U4/U11 pins.
- **Rails (PWR_3V 52, PWR_5V 14, LOCAL 12):** 3V_AO (19), 3V3_AUDIO (27), 5V_LOGIC (9), 5V_CODEC, LDO_3V3/1V5, REGN; local nets U6/U7/U24/U10/U25 (AVDD, VCC, CPP/CPN/HPVSS). Many decap pads, no free space for island vias: manual pour/tracks.
- **BOOT (2):** U6/U7 BST_B-. **GND (79):** pads without room for a via (U2, U4, U6, U7, U10, U11, U24, connectors).
- Untouched: SWITCH, POWER_HI, PVDD, SPK_OUT (94 edges); nothing intentionally routed in the U25/L200, U6/U7-L201..L206, U4/L1 corridors.

## 5. Risks / notes
- 174 In2 signal segments sit among the 21 power islands: review or move before the power pours are finalised.
- 45 width-floor items are pin escapes (PWR_5V 0.2 vs floor 0.4): widen by hand or accept.
- No teardrops; GND zone clearance 0.4 as P0. Full pipeline about 60 min.
- Scripts in `ai-files/helpers/`: route_p1_dsn.py, _chunks.py, _rounds.py, _cycle.sh, _fix.py, _post.py (import/merge/refill), _open.py, _stat.sh, _vias.py, _widen.py, _metrics.py, _strip.py, _prune_nets.py, _dedupe.py, _fr.sh, _view.sh/_png.mjs. Never use `pkill -f` (it kills the own shell).
