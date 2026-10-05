# PCB placement (2026-10-06): placement only, no routing, no copper zones

File: `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` (322 schematic footprints with nets, 3D models linked, 4 board-only mounting holes). Regenerate: `ai-files/helpers/build_pcb.sh` (netlist export + `build_pcb.py` in the flatpak KiCad python; edit the ANCHORS/SATELLITES tables, re-running overwrites the board). Check/renders: `ai-files/helpers/pcb_check.sh` -> `ai-files/pcb/` (drc.json, layout-top.pdf/.svg/-full.png, layout-3d-top/bottom.png, layout.json = positions used by the CAD).

## Outline and stack
- **114 x 92 mm**, 1.6 mm, 4 copper layers declared (stackup default, not designed), corner radius 3. Was 100 x 66 (estimate). Reason: top-only placement with 0.5 mm courtyard gaps, 2 mm moats around tall parts and a reference text slot per part needs about 9 000 mm2; 110 x 84 failed to fit all parts. Limits used from the CAD: roof carries the board x -61..61 (left edge -59), rear edge fixed at y 156.5, front edge y 64.5 (chamber wall y 59-62, ND65 magnet rear y 55.8), right edge u 55 because the rocker body (x 66, r 9.8, z 65-85) would hit the PCB (z 66.5-68.1).
- Frame: u = CAD X, v = rear (CAD Y - 111.5). Rear edge is at the top of the KiCad sheet. Origin of the sheet frame: board centre (150, 100) mm.
- 4 x M3 NPTH 3.2 (footprint `MountingHole_3.2mm_M3`, new file in the footprint folder, board-only, 3.75 mm square keepout, labels H1-H4 on silk): (-55.5, +-42.5), (51.5, -42.5), (51.5, 18.5) (u, v). The fourth hole is not at the rear-right corner because the rocker wire pads are there. CAD standoffs/inserts/screws follow these (asymmetric list). No ground pad (plain NPTH; standoffs are isolated).

## Zone map (u from left -59 to right 55, v from front -46 to rear +46)
| Zone | Where | Contents |
|---|---|---|
| Rear edge | v +46 | J8 BM83 header (u -48), J2 (-30) and J3 (-12) jacks, SW100 tact (-1), J1 USB-C (20), J4 PD service header (33), SW101 rocker wire pads (52) |
| BM83 | left edge, v 9..27 | U1 rotated 90, antenna end 8 mm past the left edge over cabinet air; BT parts right of it; U15/L3 BT supply below it |
| USB PD | rear right, u 8..40, v 14..46 | U11, U19, D1/D5/D6/D7 around J1, PD passives |
| Charger/power | right, v -20..14 | U4, L1 next to U7, Q100-Q102, J5 on the right edge (u 55, v -9) with Q103 beside it, gauge/switch ICs U5/U12/U13/U16/U17/U20/U21/Q104 in a column at u 36..40 |
| Boost | front right | U25, L200, C275 (polymer 8x10) |
| Amplifiers | front centre | L201-L206 as 2 x 3 block (2.4 mm gaps between columns), U6/U7 behind, J9-J11 on the front edge under their column, output caps beside the inductors |
| MCU | front left | U3, J6 SWD header and J7 TC2030 on the front edge |
| Audio | centre/rear | U2+Y170, U24+Y200, U22/U23, U14+L2, headphone amp U10 and muxes U8/U9 close to J2/J3, D200/D201 at the jacks |

## Connectors vs CAD cutouts (CAD rebuilt from layout.json; 0 unintended overlaps, `ai-files/cad/interference.md`)
Origin / courtyard centre in CAD X (u) and edge handling: J1 origin x 20.0, shell tab pads end 0.5 mm inside the edge, body 1.25 mm past it (was 2.03: copper_edge DRC); J2 x -30.0, J3 x -12.0 (bore to the rear, 0.3 mm inside the edge, silk clearance); SW100 x -1.0 plunger to the rear (lid hole dia 5); J5 mating face to +X at the right edge (harness to the pack now starts outside the board); SW101 pads at x 52 v 36.5 (rocker panel body is at x 66, z 75, wired by flying leads; its 23 x 23 courtyard overhangs the rear and right edges); J9-J11 at the front edge (x -19, -1.5, 16); J6/J7 front edge x -37/-45.8; J8 rear edge x -48. CAD lid cutouts follow the placed positions (previous x -18/-2/14/30 changed). Jack/USB opening plug clearances still unverified.

## Rules applied
- Top side only; all 322 parts on F.Cu. Passives 0/90/180/270 (2-pin parts pick the orientation that puts the right pad toward its net), ICs fixed orientation.
- Courtyard gaps: passive-passive 0.5 mm; IC-IC and IC-passive 0.6 mm; exposed-pad ICs (BQ25792, TAS5825M x2, TPA6132, TPS25730D, TPS7B8450, TPS61088, CSD17579, TPS63802 x2, PCM1862, BM83) 1.0 mm to everything except passives sharing a net with them (0.6, decoupling caps adjacent); tall parts (inductors, C275, connectors, switches) 2.0 mm to small passives and 1.0 mm to ICs (iron access). Courtyards are the union of the library courtyard and the pad extents + 0.2 (several library courtyards are smaller than their pads, e.g. U2, U8).
- Greedy ring search per part minimising pad-to-pad distance to already placed pins on the same nets (same sheet first), decoupling caps first; satellites with hints; GND ignored for attraction.
- Reference text: 0.8 mm / 0.12 mm silk, to the right of passives (else left/below/above, rotated 90 deg in tight gaps), below ICs and connectors; never over pads (checked against pad-union rects). Values on F.Fab, hidden. 5 refs (R232, R241, R243, R244, C268) found no silk slot and are hidden on silk (only on the assembly layer); give them a slot after routing. Board name/revision on bottom silk (top has no free 26 x 1.4 mm area); H1-H4 labels on the ring.
- Keep-outs: BM83 antenna rule area `BM83_ANTENNA_KEEPOUT` (F.Cu, In1, In2, B.Cu; no tracks/vias/pour) over the board strip under the antenna (u -59..-56.4, v 10..26); placement keeps all parts 3 mm from the antenna end/sides. The module itself sits partly in the area, so the footprint restriction flag is off. No keepout under the inductors (MWSA1265S and XFL are shielded; add one under L200/XAL7070 if the datasheet asks).
- Polarity/pin 1 are left to the footprints (C275 has a + mark, J1/IC pin 1 marks visible in the render; D7, Q and ICs not re-verified against datasheets).

## DRC (kicad-cli pcb drc, no routing)
Courtyard/overlap/outline errors: **0**. Total 36 violations + 499 unconnected items (expected, nothing routed), 0 parity errors.
| Type | Count | Cause |
|---|---|---|
| unconnected_items | 499 | no routing |
| clearance | 13 | footprint pad pitch below the 0.2 mm default: J1 (A4B9 vs neighbours 0.10-0.15), U19 (0.19), U11 (0.125-0.175); inherited, set a fine-pitch rule or tune footprints |
| drill_out_of_range | 8 | TPS25730D footprint thermal-via drill 0.2 mm (min 0.3 default) |
| hole_clearance | 2 | SW100 draft footprint pad 1 to its NPTH |
| silk_edge_clearance | 4 | connector outlines flush at the edge (J1, J2/J3 partly) and BM83 outline crossing the edge |
| silk_over_copper | 8 | jack NPTH pads under J2/J3 silk |
| silk_overlap | 1 | Y170 reference near U10 silk |

## Open concerns
- Thermal: U6/U7 exposed pads and U25 need via arrays into inner ground; U6/U7 sit under the 2.4 mm columns; the 4 layer stackup is not defined. TAS5825M pair is 25 mm apart, boost 35-45 mm from them: PVDD_AMP needs a wide path or plane; put the bulk caps at U6/U7 (done by placement) and C275 at the boost.
- Loops: L1 beside U4 with SW/PMID caps nearby; U25/L200 loop depends on pin orientation (not inspected, L200 3 mm from U25: check at routing); L201-206 front row connects to U6/U7 through the back row (layer change). Output caps are 2 mm from the inductors (iron-access rule), so loops are longer than minimal.
- High current: J5 -> Q103 -> L1/SYS -> boost input -> U25 -> PVDD (several A, 12 V): pours/planes needed; J9-J11 3 A+ per wire.
- Charger and boost switching nodes (right half) are 40+ mm from the codec/ADC (left centre) but U6/U7 and the inductor block are adjacent to U24, U2 and the headphone amp: shield with ground plane and keep the I2S/clock lines short.
- BM83 antenna at the left edge, 8 mm over air: wire harness/battery must stay away; the left wall is 11 mm beyond.
- Test points wanted (none placed): PVDD_AMP, 3V_AO, 3V3_AUDIO, 5V_LOGIC, 3V8_BT, SYS/BAT_INT, VBUS, GND, I2S BCK/LRCK/DATA, SDA/SCL, AMP_FAULT_N.
- Footprint issues to settle: SW100 and TPS61088/TPS25730D land patterns (draft), J1/U11/U19 clearance, no 3D for J5/J9-J11/SW100/SW101.
- The rocker pads corner uses a 290 mm2 courtyard region that is otherwise empty; the board could shrink 3-4 mm if SW101 is replaced by a 3-pin wire header footprint.
- `DesktopSpeaker.kicad_pro` was rewritten by KiCad (board design-settings block added); no rules were changed.
