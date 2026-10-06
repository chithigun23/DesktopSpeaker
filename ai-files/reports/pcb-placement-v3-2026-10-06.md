# PCB placement v3 (2026-10-06): 116 x 112 mm, hard separation zones, decoupling-weighted placement. Placement only: no routing, no zones except the BM83 rule area

File: `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` (311 footprints). Regenerate: `ai-files/helpers/build_pcb.sh` (about 10 min; `BOARD_D` env = depth, default 112), then the outlier post-fix `helpers/pcb_refine.py` (moves single decoupling caps to the nearest free spot; spec list = caps > 3 mm from `dist-v3.json`; analogue parts get a v >= 10.5 limit) and a `layout.json` refresh for moved tall parts (C275). Checks: `pcb_check.sh` (DRC + renders), `pcb_dist_check.py` (separation table, per-IC decoupling, U25 FB/COMP vs SW; output `ai-files/pcb/dist-v3.json/.txt`), `pcb_zone_check.py`, `pcb_gap_check.py` (courtyard gaps/labels). Rules: `pcb-layout-rules-audio.md`. Before: `pcb-placement-v2-2026-10-06.md`.
Note: the run budget (3 full runs) was exceeded: 8 generator runs of 7-11 min each plus 2 refine passes were needed (hard clamps, U25 re-layout, U14 anchor, audio-owner fix).

## 1. Board and enclosure
- Board **116 x 112 mm** (v2 116 x 96). Width unchanged (left = roof edge x -61, right = rocker body x 55); depth +16 mm to the rear. Front edge stays at CAD y 64.5 and the rear edge is CAD y 176.5. Layout frame: the generator works with the front edge at v -48; `layout.json` is exported centre-relative (v - 8) so the CAD needs no change.
- Enclosure: outer **163 x 100 x 180 mm** (v2 164 deep), CAD rebuilt, **0 unintended overlaps** (6 intended connector-in-PCB pairs). Internal volumes (`ai-files/cad/volumes.md`): woofer chamber net **0.625 L** (v2 0.530; target 0.45-0.60, Vas 0.59: 0.025 L above the target, because the chamber runs to the lid; shorten it at the front wall `ch_y0` in the build script if the user wants <= 0.60), main chamber net 1.589 L, total 2.568 L, external 2.93 L. Outer size grew from 2.67 L to 2.93 L.
- PTH GND M3 holes (pad 1 on GND, 6.2 mm pad) kept: H1 (-55.5, -52), H2 (51, -28), H3 (-28.5, 44), H4 (51, 29) in centre-relative (u, v). H2 moved up the right edge to free the corner for the boost converter; H3 is 7 mm from the BM83 module (screw head 22+ mm from the antenna).

## 2. Zone map (u right, v rear, design frame front edge v -48, rear v 64)
| Zone | Region | Contents |
|---|---|---|
| BM83 | corner u -61..-21, v 30.5..64; module u -69..-35.9, v 45.2..62.5 | U1 + BT passives, J8 (-36.5, 37); antenna keep-out rule area u -61..-58.4 |
| BT supply | u -61..-50, v -5..13 (hard v <= 17) | U15, L3 |
| MCU | u -61..-44, v -48..-6 | U3, J6, J7, H1 |
| Class-D | u -45..36, v -47.5..-10 (hard v <= -10) | U6 (-35, -27), U7 (28.5, -27), L201-L206 (rows v -30.6/-16.6), J9-J11 front edge |
| Boost | u 27..55, v -48..-17 | U25 (44.5, -42.5, rot 270 so SW faces L200 and VOUT faces C275), L200 (33.5, -42), C275 (46.0, -30.5 -> moved by the refine pass), H2 |
| Gauge/switches | u 24..55, v -24..-3 | U5, U12, U13, U16, U17, U20, U21, Q104 |
| 5 V supply | u 45..55, v -4..16 (hard u >= 44.5) | U14 (49, 2), L2 (50, 9.5) |
| Charger | u 24..55, v 8..40 | U4 (39, 20), L1 (39, 32.5), J5 (right edge, v 26), Q100-Q103, H4 |
| USB PD | u 14..55, v 40..64 | J1 (25.5), J4, SW100 rear edge, U11 (33, 49), SW101 (right edge v 52) |
| Audio (analogue) | u -42..22.5, v 11.5..64 minus a 15 mm strip beside the BM83 (hard v >= 10.5, u >= -20.5, left block v <= 29.5) | J2, J3 (rear edge), U24 (-28, 19), U2 (9, 27), muxes, U10, U22/U23, crystals |
The hard clamps (`CLAMP` in `build_pcb.py`) apply after the zone-margin escalation, so a part can never be pushed into a forbidden strip; the first runs without them leaked audio parts to 3-12 mm from the class-D block. Audio-sheet passives that touch a BM83 net (BT_AUDIO_L/R coupling network) are owned by the audio ICs, not the BM83.

## 3. Separations (courtyard gaps, `pcb_dist_check.py`) and rule compliance
| Rule | Required | v2 | v3 | Status |
|---|---|---|---|---|
| Class-D (U6/U7, L201-L206) to analogue ICs | >= 20 | 17.9 | **24.0** | met |
| Class-D block to ALL analogue passives / audio input RC | >= 20 | 10.4 | **20.8** (nearest R206, left block) | met |
| BM83 to analogue ICs (U24, muxes, U10, codec, jacks) | >= 15 | 13.5 | **16.1** (U1-J2) | met |
| BM83 to ALL analogue passives / input networks | >= 15 | 9.5 | **16.1** | met |
| BM83 to its own U15/L3 | >= 25 | 13.7 | **33.6** | met (U15/L3 moved to the left edge, v <= 13; BM83 BAT_IN is a wire/trace; keep TPS63802 feedback and caps at U15) |
| BM83 to any other switching inductor/node (L1, L2, L200, class-D, U4, U25, U14) | >= 25 | 19.2 | **56.2** class-D, 72.0 L1, 105.5 L200, 75.6 U4/U25 | met |
| U14/L2 to analogue (all parts) | >= 20 | 2.0 | **31.0**; U14/L2 not next to U2 | met |
| Boost U25/L200/C275 to analogue (all parts) | >= 20 | 47.2 | **50.9** | met |
| Charger U4/L1 to analogue ICs / all parts | aim >= 15 | 19.3 / - | **21.3 / 14.1** (L1-C186) | ICs met; passives 0.9 mm short of the aim |
| BT supply U15/L3 to analogue passives | (not a stated rule) | - | 11.0 | note: switching inductor 11 mm from the left analogue block |
| BM83 external metal >= 15 mm from antenna | 15 | board met | board met (H3 screw 22 mm, J8 header 22 mm) | met; the cabinet wall 11 mm beyond the antenna end is a CAD item |
| Antenna keep-out, no copper any layer | - | met | met (`BM83_ANTENNA_KEEPOUT`, 4 copper layers) | met |
| FB/COMP of U25 away from SW | away | 2-5 mm (not met) | FB/COMP parts 5.8-6.0 mm from the nearest SW pad (SW pins/L200), C269 2.4 mm, R251 3.1 mm, R254 7.3 mm from their pins | met (R254 7.3 mm from the COMP pin is the compromise) |
| Hand-solder: courtyard gaps >= 0.5, 2.0 mm tall-vs-passive, top side only | - | met | met: 0 gaps < 0.45 mm, 0 labels over a courtyard | met |
Zone map and keep-out distances are enforced by hard clamps; the table values are measured on the final board.

## 4. Decoupling distances (pad centre to nearest pad of the net on an IC)
All 230 passives that touch an IC pin: mean 5.39 mm (v2 6.83), max 28.4 (v2 34.8; the 28 mm item is a USB resistor chain), >3 mm 155 (182), >5 mm 97 (130), >8 mm 44 (72). 0402 HF caps: mean **3.45** (v2 5.65), max 8.5 (20.6), 31 of 62 above 3 mm (v2 37). Bulk 0805+ caps: mean 6.9 (7.5), max 20.8 (17.0, the outlier is C263, a U20 SYS_RAW input cap). All caps with a GND pad (116): mean 5.03.
Per IC (n, max, mean) v2 -> v3:
| IC | v2 | v3 |
|---|---|---|
| U25 TPS61088 | 10 / 19.7 / 10.1 | 12 / 8.9 / **4.4** |
| U4 BQ25792 | 16 / 17.0 / 8.8 | 15 / 10.3 / **6.0** |
| U24 PCM1862 | 32 / 18.2 / 8.1 | 30 / 15.9 / **6.2** |
| U22 LDO | 2 / 20.6 / 11.3 | 4 / 7.5 / **4.6** |
| U23 LDO | 2 / 20.2 / 15.2 | 3 / 4.5 / **3.1** |
| U2 PCM2902C | 14 / 14.9 / 6.2 | 13 / 17.8 / 6.0 |
| U6 TAS5825M | 25 / 11.3 / 5.4 | 23 / 12.7 / 5.9 |
| U7 TAS5825M | 9 / 7.3 / 2.4 | 9 / 8.2 / 3.1 |
| U3 MCU | 5 / 9.5 / 6.0 | 6 / 8.8 / 5.1 |
| U11 TPS25730D | 12 / 10.4 / 5.2 | 12 / 7.8 / **3.4** |
| U14 / U15 / U10 | 4.8 / 4.4 / 5.5 mean | 4.7 / 4.2 / **3.9** mean |
Previously poor groups: BQ25792 SYS caps 14-17 mm -> 8.7-9.5 mm (C104/C105/C107; the 0805 SYS caps cannot get closer: the ring is full), PMID 2.5-4.3 mm, VBUS 4.9-6.1 mm, REGN 5.0 mm, SW2 bootstrap C110 4.2 mm. U25: VCC C265 8.5 mm, SS C266 9-11 mm still outside the target (the corner ring is taken by FB/COMP/ILIM/MODE parts, L200 and C275), C269/R254/R251 as above. U22/U23 caps 2.0 mm (was 20). PCM1862 3V3_AUDIO caps 4.0-8.5 mm (was up to 18). U2 crystal caps C177/C178 4.3-5 mm (was 10-15; the crystal sits next to U2 at 3.2-3.5 mm).
**Not met**: "every decoupling cap <= 3 mm": 78 of 116 GND-capacitors stay above 3 mm. Reason: the first ring of a 4-5 mm QFN holds about 6 parts once each part needs its 0.5 mm courtyard gap and an adjacent reference label slot, and U6/U4/U24 carry 20-30 passives each (25 on the TAS5825M alone, many 0805/1206 bulk caps). Critical pins that do reach it: U7 all PVDD caps (0 above 3 mm), U11 (0), U23 (0), U4 PMID C101 2.5 mm, U6 GVDD/VR_DIG 1.6-2.0 mm, MCU VDD C160 2.5 mm. Remaining critical gaps: U6 PVDD small caps 2.7-10 mm (C289 2.7, C276/C291 3.5-4, the rest 5-10), U4 SYS 8.7-9.5, U25 VCC/SS 8.5-11, U24 AVDD/LDO 7-9. These are first items for manual nudging in KiCad once routing begins; the label slots are the limiting item (labels could move to a user-agreed fab/second silk layer).

## 5. DRC and checks
`pcb_check.sh`: courtyard / overlap / outline / copper_edge / shorting **0**; total 35 violations (all inherited): clearance 13 (J1/U11/U19 pad pitch), drill_out_of_range 8 (TPS25730D thermal vias), hole_clearance 2 (SW100), silk_edge_clearance 4 (J1, U1 flush with edge), silk_over_copper 8 (J2/J3); 499 unconnected (nothing routed); 0 parity errors. Reference labels: all 311 visible on F.SilkS; `pcb_gap_check.py` still finds 15 label/label proximity pairs (bounding boxes touching, e.g. R234/C241, R262/R257) that are cosmetic and were also present before the refine pass. Renders: `ai-files/pcb/layout-top-full.png`, `layout-top.pdf`, `layout-3d-top.png`, `layout-3d-bottom.png` were viewed; CAD renders in `ai-files/cad/renders/`.

## 6. Room left for routing
The 20 mm band between the class-D block (v -10) and the analogue block (v 10.5) is empty except for the board title, so ground-via fence rows and the I2S/I2C/PDM buses can cross it; U6/U7 are free over the thermal pad (~20 vias); BM83 ground fence <= 3 mm around the module; no test points placed yet (list as in v2).

## 7. Open items
1. Decoupling <= 3 mm for all caps not reached (section 4); next step is hand nudging of the worst critical caps (U6 PVDD, U4 SYS, U25 VCC/SS, U24 AVDD) or moving reference labels of the first ring to a second layer.
2. Charger passives 14.1 mm from the analogue block (aim 15) and BT supply L3 11 mm from the left analogue passives (no stated limit; adds a ground fence if kept).
3. Woofer chamber 0.625 L (above 0.60): decide with the user or trim the chamber; board depth 112 mm and enclosure 180 mm deep (v2 164).
4. TPS61088 datasheet PDF still unavailable (excerpt only); verify U25 pin function/rotation (rot 270, SW pins face L200 on the left, VOUT faces C275) against the real datasheet before routing.
5. Inherited footprint issues (J1/U11/U19 pitch, TPS25730D via drill, SW100, J2/J3 silk) are unchanged. This is a reviewed first-pass placement, not a routed or thermally verified design.
