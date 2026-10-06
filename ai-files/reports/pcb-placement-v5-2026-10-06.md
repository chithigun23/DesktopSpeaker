# PCB placement v5 (2026-10-06): denser cells, minimum separations, auto woofer-chamber volume. Placement only, no routing

Board `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` (311 footprints + 4 PTH GND M3 holes). Pipeline `ai-files/helpers/run_v5.sh [seeds]` (cells `build_pcb_v5.py` -> `fp_pack_v5.py` -> `fp_spec_v5.py` -> board, about 1 min). Checks: `pcb_check.sh`, `dist_v5.sh` + `decap_list_v5.py`, `pcb_sep_v5.py` (run with `--filesystem=/tmp`), `pcb_gap_check.py`. Renders `ai-files/pcb/layout-v5-top.png`, `layout-3d-top.png`.

## Changes v4 -> v5
- Reference text 0.6 mm (thickness 0.1), project `min_text_height` lowered 0.8 -> 0.6 (otherwise 199 text_height warnings); tile margin 0.5 mm, title strip 1.9 mm, courtyard gaps 0.3 (R-R), 0.35 (cap to its own IC), pad slot gap 0.12.
- Decoupling: for critical ICs the rail 0402 caps are placed first and without needing a free label slot (label moves to the nearest slot afterwards); QFN gap rule uses the owner IC, so own caps sit 0.35 mm from the IC courtyard; bulk 0805s follow on the outer ring.
- Class-D inductors in one row of 4 (2 for U7) above the amp, 16 mm above its origin so the OUT/BST caps fit; SWG cell compacted; R223/C233 moved to the ADC cell (analogue side, 20.2 mm from BM83).
- Packer: Euclidean separations at the stated minimums (BM83 25 mm to charger/5V logic/boost/amps, 15.2 to analogue; amps/boost 20.4 to analogue, charger 14), max-contact placement, front row AMP6|AMP7|BATIO, BT supply (BM83's own 3V8 buck) allowed 12 mm from the BM83.
- CAD: `build_speaker_cad.py` sets the woofer chamber length from `CH_NET_L` (0.525 L net): `ch_y0`, `woof_cy` derived; woofer moves to the chamber.

## v3 vs v4 vs v5
| | v3 | v4 | v5 |
|---|---|---|---|
| Board | 116 x 112 | 117.5 x 176 | **116 x 152** |
| Area mm2 | 12,992 | 20,680 | **17,632** (-15 % vs v4, +36 % vs v3) |
| Enclosure depth (Y) | 180 | 244 | **220** |
| Woofer chamber net | 0.625 L | 1.003 L | **0.525 L** (auto) |
| Main chamber net | 1.436 | 2.100 | 2.283 |
| 0402 HF decaps mean / max / >3 mm | 3.45 / 8.5 / 31 | 3.25 / 7.9 / 32 | **2.84 / 7.45 / 21** |
| All passives mean / max | 5.42 / 28.4 | 4.66 / 14.8 | **3.86 / 9.4** |
| Bulk 0805 mean | 6.85 | 6.13 | 4.94 |
| Caps with GND pad, >3 mm | 78 | 80 | 61 |

Mean passive-to-pin distance per IC (v3 / v4 / v5): U6 5.88 / 7.70 / **5.22**; U25 4.38 / 4.98 / **4.44**; U4 5.98 / 5.85 / **4.82**; U24 6.41 / 5.63 / **4.48**; U7 3.14 / 2.48 / 2.15; U2 5.97 / 3.86 / 3.64; U3 5.10 / 3.46 / 3.23; U11 3.42 / 3.76 / **3.15**; U22 / U23 4.63 / 3.10 -> 2.25 / 2.31; U14 / U15 / U10 4.71 / 4.16 / 3.89 -> 2.93 / 3.66 / 2.68.

## Separations (mm; required)
BM83 to analogue ICs/jacks/passives (15) **20.2**; BM83 to class-D inductors (25) **87.6**, boost **91.7**, L1/U4 **70.8**, L2/U14 **72.2**; BM83 to its own U15/L3 12 required (no rule), 68.5 achieved; class-D to analogue ICs (20) 40.8 / all parts 38.0; boost to analogue ICs 39.0 / all 36.9; L2/U14 to analogue 21.4 (20); L1/U4 25.3 (15). Hard rules all met. The measured gaps are larger than the minimums because the analogue block must sit between the BM83/jack rear row and the amp row (see unmet).

## DRC (`pcb_check.sh`)
courtyards_overlap / overlap / outline / copper_edge / shorting / pth_inside_courtyard 0. Remaining 26 (inherited kinds): hole_clearance 2 (SW100), drill_out_of_range 8 (TPS25730D thermal vias), silk_edge_clearance 6, silk_over_copper 10 (J2/J3 pins, bottom-silk title over J7 NPTH); text_height 0 after the rule change; unconnected 499 (not routed); parity 0. `pcb_gap_check`: 100 courtyard gaps < 0.45 mm (min 0.31, intended by the denser rules, DRC clean); 3 label-label overlaps (C214/C220, C214/C217, C287/C291).

## CAD (`ai-files/cad`)
Outer 163 x 100 x **220** mm, external 3.59 L, cavity 3.158 L; woofer chamber gross 0.581 / net **0.525 L**; 0 unintended overlaps (6 intended connector-in-PCB pairs). Renders refreshed by `render_cad.py`.

## Unmet targets and causes
1. **Area 17,632 mm2 (target <= 13,000 / ideally 11,000) and depth 220 mm (target <= 185).** Tile sum is already 15,000 mm2 (cells 12,300 mm2 + margins) against 4,800 mm2 of courtyards, and the separation chain forces depth: BM83 and the jack/USB row at the rear, the analogue block (ADC, USB codec, mux, rail: 2 rows, about 48 mm) below, then 20 mm clear, then the 45 mm amp row. 150 packer trials (8 seeds, 3 heuristics) all plateau at 152 mm. Reaching v3 needs interleaved (non-tile) placement as in v3, a 2x2 inductor layout with jacks beside the IC (about -8 mm), or relaxing class-D to analogue spacing with a ground fence. Board width 116 mm meets the roof limit.
2. **Decaps <= 2.5 mm for every critical cap not met**: 0402 mean 2.84, 21 of 62 above 3 mm. U6 (20 caps, 26 passives), U24 (18) and U4 (10) still have 3-8 mm caps (U6 BST/OUT caps 5-9 mm, U24 3V3/AVDD 4-8 mm, U4 BTST/SW 4-6 mm); several listed 0402 are crystal/coupling/filter caps rather than supply decaps. Pad-centre to IC-pad distance has a floor around 2 mm on these QFNs. U7, U22, U23, U11, U14 meet it.
3. Holes: 4 PTH holes at edges (left x2, right x2), not four corners (BM83 antenna, USB-C and the front amp/connector row own the corners).
4. Cell bboxes are about 50 % full; passives are ring-packed, not in aligned rows like the BSPD reference (only the labels were reduced).
