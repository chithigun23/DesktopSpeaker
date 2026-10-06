# PCB placement v2 (2026-10-06): noise zoning, PTH GND mounting holes, 116 x 96 mm. Placement only: no routing, no zones except the BM83 rule area

File: `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` (311 footprints = current schematic netlist, the 11 deleted parts are gone, U6 pin 8 ADR is on GND). Regenerate: `ai-files/helpers/build_pcb.sh` (about 15 min: greedy start, then two soft-constraint annealing passes and a legaliser, all inside `build_pcb.py`; edit ANCHORS / SATELLITES / ZONES, rerun overwrites the board). Checks: `ai-files/helpers/pcb_check.sh` (DRC + renders in `ai-files/pcb/`), `ai-files/helpers/pcb_dist_check.py` (passive-to-IC pin distances and zone separations; results `ai-files/pcb/dist-v2.json`, before `dist-v1-before.json`).
Rule set: `pcb-layout-rules-audio.md`. Previous placement: `pcb-placement-2026-10-06.md` (v1).

## 0. TPS61088 datasheet
Not obtainable as a PDF: `ti.com/lit/ds/symlink/tps61088.pdf` and `/lit/gpn/tps61088` return a 404 HTML page, the mouser.lt mirror also returned HTML (3 attempts, nothing kept). Only the TI document-viewer layout text could be fetched; verbatim excerpt in `ai-files/datasheets/tps61088-layout-excerpt.txt`: minimise length/area of all SW traces and put a ground plane under the regulator; input capacitor close to VIN and GND (0.1 uF bypass as close as possible to VIN); thermal pad soldered to a large ground plate with thermal vias. The inductor/output-cap/FB/COMP/SS wording was not retrievable (general boost rules applied, marked unverified in the excerpt). Gap: the real PDF is still to be fetched manually.
Result for U25: L200 adjacent (U25-L200 courtyard gap 1.1 mm) but the FB divider (R250/R251) is only 3.0-5.2 mm and the COMP network (R254, C269) 2.2-3.4 mm from the SW pins, and C265 (VCC) 10 mm, C266 (SS) 9 mm from their pins: FB/COMP separation from SW is NOT met and U25 passives are not tight (see section 5).

## 1. Board, holes, enclosure
- Outline **116 x 96 mm** (was 114 x 92), corner radius 3. Left edge u -61 (roof edge), right edge u 55 (rocker), rear edge CAD y 160.5, front edge CAD y 64.5 (unchanged). Enclosure depth 160 -> **164 mm** (`build_speaker_cad.py` now reads `rear_edge_cad_y` from `layout.json`: D = rear edge + 3.5; plunger/USB/jack plane constants follow it). CAD rebuilt and checked: **0 unintended overlaps**, outer 163 x 100 x 164, woofer chamber net **0.530 L** (was 0.506, target 0.45-0.60), main chamber net 1.461 L. Larger than 116 x 96 is not possible without moving the rocker or the chamber/driver geometry (front edge is limited by the chamber wall y 59-62 and the ND65 magnets, left by the roof edge x -61, right by the rocker body x 66).
- **Mounting holes**: new footprint `MountingHole_3.2mm_M3_PTH_GND` (3.2 mm drill, 6.2 mm round copper pad on all layers, pad number 1 on net GND, zone connect solid so the L2 GND plane / L4 pour join it, 3.75 mm radius courtyard for the screw head), the old `MountingHole_3.2mm_M3` file is removed. Positions (u, v) = CAD x, y - 112.5: H1 (-55.5, -44.0), H2 (51.0, -44.0), H3 (-28.5, 41.0), H4 (51.0, 16.5); copper-to-edge 0.9 mm (copper_edge DRC clean). H3 moved from the rear-left corner to between BM83 and the audio jacks (corner is BM83; a GND screw next to the antenna is not acceptable; it also supports the rear edge near the jacks). CAD standoffs follow the layout holes. Open: a screw head and standoff are metal on GND: keep them >= 15 mm from the antenna (H3 is 22+ mm away); the PTH hole pads are GND: there is no isolation from the chassis screws (cabinet is printed plastic).
- SW101: its library courtyard was the panel (23 x 23); reduced to the wire-pad row (20 x 6.4) so the courtyard stays on the board; pads vertical along the right edge (u 51.5, v 26..46).

## 2. Zone map (u right, v rear; board u -61..55, v -48..48)
| Zone | Region (u0..u1, v0..v1) | Contents |
|---|---|---|
| BM83 corner | -61..-22, 4..48 (module u -69..-35.7, v 29.3..46.7, antenna 8 mm over the left edge) | U1, BT passives, J8 (-36.5, 22.3), H3, keep-out under the antenna u -61..-58.4, v 30..46 on all layers |
| BT supply | -61..-47, -2..20 | U15 (-52, 8), L3 (-51.5, 13.3) |
| MCU | -61..-44, -48..-6 | U3 (-51, -27), J7 TC2030 front edge (-46.5), J6 SWD left edge (-59.2, -12), H1 |
| Audio (analogue) | -19.5..24, 2.5..48 and -46..-19.5, 2.5..16 | J2 (-13.7), J3 (-0.2) on the rear edge; U10, U8/U9 muxes, U22/U23, U2 PCM2902C (9, 19) + Y170, U24 PCM1862 (-28, 12) + Y200, FB200, D200/D201, ~106 passives |
| Class-D | -44..23, -48..-12 | U6 (-35, -22) left of 2 x 3 inductor block L201-L206 (columns -17.5 / -1.6 / 14.3, rows v -30.6 / -16.6), U7 (28.5, -22), J9/J10/J11 on the front edge (-22.5 / -2.5 / 17.5), output caps between them |
| Boost | 31..55, -48..-17 | U25 (44, -43), L200 (36, -42.5), C275 (48.5, -32), H2 |
| Charger | 18..55, -9..27 | U4 (37, 7), L1 (37, 19.5), Q100-Q103, J5 right edge (49.5, 4), H4 |
| Gauge/switches | 34..55, -22..0 | U5, U12, U13, U16, U17, U20, U21, Q104 |
| 5 V logic supply | 12..30, 0..22 | U14 (18, 8), L2 (18.5, 13.3) |
| USB PD | 14..55, 24..48 | J1 (25.5), J4 (16.5), SW100 (10.5), U11 (31, 34), U19, D1/D5/D6/D7, SW101 pads (51.5, 36) |
Signal flow: jacks (rear) -> muxes -> U24 -> I2S -> amps (front); USB-C at the rear right, speaker connectors at the front.
Connector courtyards (u0, v0, u1, v1): J1 20.4..30.6 x 40.7..49.2 (shell 1.2 mm past the rear edge), J2 -19.9..-7.5 x 33.4..47.7, J3 -6.4..6.0 x 33.4..47.7, SW100 7.7..13.3 x 40.5..48.0, J4 14.7..18.3 x 36.8..48.0, J5 44.0..55.0 x -2.9..10.9, J9 -27..-18, J10 -7..2, J11 13..22 (all v -47.6..-38.0), J7 -50.5..-42.5 x -47.6..-39, J6 -61..-57.4 x -17.6..-6.4, J8 -38.3..-34.7 x 15.4..29.2, SW101 48.3..54.7 x 26..46. CAD cutouts follow these (`layout.json`).

## 3. Separation results and rule compliance
Distances are courtyard-box gaps (`pcb_dist_check.py`); "ICs" = the named parts only, "all parts" = every passive of the audio sheets (Source_Select_ADC, Headphone_Aux, USB_Audio) against the noisy block.
| Rule | Required | v1 (before) | v2 achieved | Status |
|---|---|---|---|---|
| BM83 to class-D inductors/U6/U7 | >= 25 mm | 19.2 | **40.7** | met |
| BM83 to boost U25/L200 | >= 25 | 77.7 | **95.6** | met |
| BM83 to charger L1/U4 (SW1/SW2) | >= 25 | 58.4 | **69.7** | met |
| BM83 to its own supply U15/L3 | >= 25 | - | 13.7 (L3 top v 15.6 vs module bottom v 29.3) | NOT met by design: the module supply regulator must sit by the module; mitigate with ground fence, ferrite |
| BM83 to analogue audio ICs | >= 15 | 1.0 | **13.5** (U24); 16.1 for jacks/others | marginally missed (U24); move U24 3 mm lower-left to fix |
| BM83 to ALL analogue passives | >= 15 | 1.0 | 9.5 (some audio passives spilled next to J8) | NOT met for passives |
| Class-D (U6/U7, L201-L206) to analogue ICs | >= 20 (10 absolute with fence) | 1.8 | **17.9** | missed by 2 mm, above the 10 mm minimum |
| Class-D block to ALL analogue passives | >= 20 | 0.5 | 10.4 | at the absolute minimum: needs a GND via fence between the zones |
| Boost U25/L200/C275 to analogue (all parts) | >= 20 | 29.3 | **47.2** | met |
| Charger L1/U4 to analogue ICs | (aim >= 15) | 27.5 | 19.3 | met |
| 5 V supply U14/L2 to ADC/analogue | >= 10 | 1.2 | 2.0 (L2 beside U2) | NOT met: U14/L2 should leave the audio zone |
| BM83 external metal >= 15 mm from the antenna | 15 | - | nearest metal: H3 screw 22 mm, J8 header 22 mm; cabinet wall 11 mm beyond the antenna end (CAD) | board met; enclosure wall 11 mm is a CAD item |
| BM83 antenna keep-out | no copper any layer | - | rule area `BM83_ANTENNA_KEEPOUT` u -61..-58.4, v 30..46 (F.Cu, In1, In2, B.Cu); courtyard of U1 2.5 mm inside the rear edge | met |
| Hand-solder gaps 0.5 mm, tall parts 2.0 mm to small passives | - | - | enforced in placement; DRC courtyards 0 | met |
**Why 20 mm class-D to analogue and 25 mm BM83 to its supply cannot all be met on one board**: courtyard areas total 4 821 mm2 (about 7 000 mm2 with reference text and moats) on an 11 136 mm2 board; the analogue block needs about 2 100 mm2, the class-D block (6 inductors 15.1 x 13.2 + U6/U7 + 3 JST + 60 passives) about 2 300 mm2 and cannot be shorter than 38 mm (connector row 9.6 + two inductor rows 26.4), so 96 mm depth minus 38 (class-D) minus 20 (gap) leaves 38 mm for the analogue block, which also holds the 14.3 mm deep jacks. A single board that meets every number needs about 105 mm depth (needs more than 4 mm extra enclosure depth plus the CAD front edge) or the split below.
**Two-board split recommendation (unchanged, now stronger)**: Board P (power/amp: USB_PD, Battery_Charger, Fuel_Gauge_Power, Amplifiers incl. boost, MCU) and Board A (BM83 + PCM1862 + PCM2902C + muxes + TPA6132A2 + jacks), B2B 2 x 20 connector, as in `pcb-layout-rules-audio.md` section 3. The 20 mm class-D and BM83 >= 25 mm numbers then hold by construction. Triggers remain as in that report.

## 4. Passive-to-pin distances (pad centre to nearest pad of the net on a non-passive part)
Method: `pcb_dist_check.py`. All 230 passives that touch an IC pin:
| | v1 (322 parts, before) | v2 |
|---|---|---|
| mean / max (mm) | 10.83 / 51.05 | **6.83 / 34.8** |
| passives > 3 / > 5 / > 8 mm | 217 / 182 / 138 | 182 / 130 / 72 |
| 0402 HF decaps (cap with a GND pad) n, mean, max | 71, 7.22, 18.3 | 62, **5.65**, 20.6 |
| 0805+ bulk caps n, mean, max | 55, 8.67, 25.0 | 54, 7.51, 17.0 |
Per IC (n passives, max, mean in mm): 
| IC | v1 n | v1 max | v1 mean | v2 n | v2 max | v2 mean |
|---|---|---|---|---|---|---|
| U24 | 28 | 19.75 | 10.26 | 32 | 18.21 | 8.07 |
| U6 | 15 | 16.6 | 8.64 | 25 | 11.25 | 5.38 |
| U4 | 25 | 20.51 | 9.94 | 16 | 17.01 | 8.75 |
| U2 | 14 | 41.37 | 13.38 | 14 | 14.87 | 6.16 |
| U11 | 10 | 11.26 | 7.48 | 12 | 10.4 | 5.23 |
| U10 | 4 | 10.27 | 9.01 | 11 | 10.06 | 5.47 |
| U25 | 13 | 51.05 | 14.03 | 10 | 19.74 | 10.08 |
| U15 | 10 | 9.23 | 5.59 | 9 | 6.23 | 4.4 |
| U7 | 17 | 31.41 | 9.81 | 9 | 7.3 | 2.37 |
| U1 | 11 | 23.84 | 7.86 | 9 | 25.18 | 7.39 |
| U14 | 7 | 24.4 | 16.58 | 7 | 8.37 | 4.75 |
| L200 | 2 | 12.72 | 11.23 | 6 | 13.5 | 9.43 |
| D201 | 5 | 24.67 | 10.63 | 6 | 8.61 | 4.74 |
| U20 | 5 | 18.16 | 11.89 | 5 | 13.53 | 5.57 |
| U3 | 15 | 49.86 | 15.56 | 5 | 9.45 | 5.99 |
| U9 | 3 | 28.66 | 20.43 | 5 | 13.41 | 6.71 |
| U8 | 8 | 28.23 | 19.39 | 5 | 20.34 | 9.88 |
| U12 | 6 | 33.98 | 12.17 | 5 | 4.11 | 2.88 |
| Q103 | 2 | 5.58 | 4.31 | 4 | 5.29 | 3.61 |
| J3 | 4 | 22.94 | 18.38 | 3 | 34.8 | 28.28 |

**Not met**: the 2-3 mm decoupling target (only 25 of 62 0402 decaps are within 3 mm). Ring capacity around the QFNs (U6 has 25 passives, U4 16, U24 32 around a TSSOP) and the 0.5 mm courtyard + reference-text slot per part limit the first ring to about 12 caps. Good: U7 (mean 2.4, all PVDD/BST/GVDD within 3 mm), U12/U13/U16/U17 (<= 4 mm), U6 critical caps (GVDD C283 2.0, AVDD C284 2.0, BST/VR_D 3-5). Poor and needing a second pass: BQ25792 SYS/PMID/VBUS caps (7-17 mm: C105/C107 SYS 14-17 mm), U25 (VCC/SS/COMP caps 9-17 mm), U22/U23 LDO caps C224/C225 (20 mm), PCM1862 3V3_AUDIO caps (up to 18 mm), U2 crystal caps (C177/C178 10-15 mm), J3 series/filter parts R242 (34.8 mm). These are the first items to fix by hand once the layout is accepted (give each of those ICs a free 8 x 8 mm ring: move U22/U23 and Y170 out of the crowded rear audio strip, move J5 or L1 away from U4).
Passives with no IC pin on their nets (21, e.g. second elements of RC chains) are excluded.

## 5. DRC (kicad-cli, no routing)
Courtyard / overlap / outline / copper_edge / shorting: **0**. Total 35 violations + 499 unconnected (nothing routed), 0 parity errors:
| Type | Count | Cause |
|---|---|---|
| unconnected_items | 499 | no routing |
| clearance | 13 | J1 / U11 / U19 footprint pad pitch below 0.2 mm (inherited) |
| drill_out_of_range | 8 | TPS25730D thermal-via drill 0.2 mm (inherited) |
| hole_clearance | 2 | SW100 draft footprint pad 1 vs its NPTH (inherited) |
| silk_edge_clearance | 4 | J1 outline flush with the edge, U1 outline over the left edge/corner |
| silk_over_copper | 8 | J2/J3 silk over their NPTH pads (inherited) |
Reference texts: all 311 visible on F.SilkS (0.8 / 0.12 mm), no hidden refs (v1 had 5); L203 is labelled on the body centre because no free slot touches it. Board title `DesktopSpeaker rev A` on top silk at (-17, -2.5). Text is mostly horizontal; some vertical labels remain in tight gaps. Row alignment/grids were not enforced beyond the 0.25 mm placement snap. Hole labels were removed (they collided with parts).

## 6. Room left for routing (suggestions only)
- TAS5825M U6/U7 thermal pad via field (about 20 vias 0.3 mm at 1.0-1.2 mm pitch in columns) needs the pad area clear on top: U6/U7 are free on all four sides within about 2 mm only at the pads; do not move bypass caps over the pad. QFN pin fan-out at 0.5 mm pitch needs the first-ring caps pulled 0.5 mm outward when routing.
- BM83 ground via fence <= 3 mm near the module; GND via fence between the audio zone and the amp block (v about -5), both sides of the USB D+/D- pair.
- Test points to add when routing (not placed): PVDD_AMP (near C275 and U6), 3V_AO, 3V3_AUDIO, 5V_LOGIC, 3V8_BT, SYS_RAW/BAT_INT, VBUS_PD, I2S BCLK/LRCK/DATA (near U24), SDA/SCL, AMP_FAULT_N, 3 GND points (one per zone corner), SWD via J6/J7 already.

## 7. Open items
1. 20 mm class-D/boost-to-analogue is not reached for the class-D block (17.9 mm ICs, 10.4 mm passives); decision needed: two-board split or accept a GND fence plus a larger enclosure depth (about +9 mm).
2. BM83 to its own U15/L3 supply (13.7 mm) and to U24 (13.5 mm) are below the targets; 5 V supply U14/L2 sits in the audio zone.
3. Decoupling distances (section 4) not at the 2-3 mm target; a second pass or hand moves around U4/U25/U22/U23/U24/U2 are needed.
4. FB/COMP of U25 are within 2-5 mm of the SW pins (against the boost layout rule); fetch the TPS61088 datasheet and re-place the FB divider (R250/R251) and COMP (R254/C269) on the far side of U25 from L200.
5. Verify the enclosure change (depth 164 mm, woofer chamber 0.530 L) with the user; the printed housing and lid cutouts moved with the connectors (cutouts: USB-C, jacks, SW100 plunger follow the layout).
6. Inherited footprint issues (J1/U11/U19 pitch, TPS25730D via drill, SW100, J2/J3 silk) and the stackup/net classes are unchanged. This is a reviewed first-pass placement, not a routed or thermally verified design.
