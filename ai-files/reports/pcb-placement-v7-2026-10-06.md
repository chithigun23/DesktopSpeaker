# PCB placement v7 (2026-10-06): bigger section labels, 10 M3 support holes, CAD standoffs. Placement only, not committed

Pipeline: `helpers/run_v7.sh` (`WS="127 129 131 133" SEEDS="1 2 3 4" TRIALS=250 HMIN=124`) -> `build_pcb_v7.py`, `fp_pack_v7.py`, `fp_spec_v7.py`, `floorplan_v7.py`, `snap_v6.py` (unchanged); plate model `helpers/plate_v7.py`. Run `build_pcb_v7.sh` alone to regenerate the board from `pcb/floorplan-v7.json`. Renders `pcb/layout-v7-top.png`, `layout-3d-top.png`. The v6 board is in git HEAD (`git checkout` restores it).

## v6 vs v7
| | v6 | v7 |
|---|---|---|
| Board | 116 x 138 | **129 x 138** |
| Area | 16,008 mm2 | **17,802 mm2 (+11 %, target <= 13,000 NOT met)** |
| Enclosure depth | 206 mm | 206 mm (target <= 125 board depth NOT met) |
| Tile strip / label | 1.2 mm, text 0.7 / 0.12 | **2.3 mm, text 1.7 mm, 0.22 thick**, centred in strip, F.Silkscreen |
| Mounting holes | 4 (edges) | **10**: H1-H6 free tiles, HA1-HA4 inside the amp inductor row |
| HF 0402 decaps (62) mean / max / >3 mm | 2.05 / 3.87 / 9 | 2.05 / 3.87 / 9 (snap unchanged) |
| Separations (BM83-analogue / class-D-analogue / boost-analogue / L1-analogue) | 20.2 / 45.4 / 30.7 / 15.8 | 20.2 / 47.3 / 30.2 / 28.0 (rules 15 / 20.4 / 20 / 14 all met) |
| DRC | courtyard/overlap/outline/shorting 0 | same 0; silk_overlap 5 (3 title vs tile line, Charger/L1, BT supply/L3), silk_over_copper 13, silk_edge 8, hole_clearance 2, drill_out_of_range 8 (inherited), unconnected 499 |
| CAD | 0 unintended | **6 unintended** (SW101 stand-in and J5 harness vs the PCB/J1/J4/shell; the board is 13 mm wider and the BATIO column moved, not yet re-fitted), woofer chamber 0.525 L, main 2.06 L |

## Why area went UP (targets unmet)
The tile sum is 14.7k mm2 (v6: 12.7k): +2k from the 2.3 mm title strip (+1.1 mm on 20 tiles), the amp tiles widened by 24 mm / 8 mm to hold four holes in the inductor row (86.9 + 39.1 mm), and 6 free 7.6 mm hole tiles. The greedy packer fills 80 % at best; the AMP6/AMP7 front row is 128 mm wide so the board is >= 129 mm and the cells above it lose the 20.4 mm class-D/analogue band (all analogue cells sit in the upper two thirds). Gaps that exist only because of rules: the 20.4 mm band between the amp/boost row and MUX/ADC/USB-codec/Jacks; the 25 mm BM83-to-switcher zone (BM83 corner, Charger/BT supply/5V logic far right); the antenna keep-out left of BM83. Visible voids (view: mid-left beside Charger FETs/Boost, centre column, under the amp row ends) are packer and tile-shape waste, not rules. A real fix needs non-rectangular (L-shaped) tiles/rotation or a 2-D packer with simulated annealing; the 13,000 mm2 target is out of reach with rectangular tiles of 14.7k mm2 total. Not done: tile rotation/mirroring (cells are generated in a fixed orientation), reordering via annealing.

## Mounting screws and plate model
Masses (estimates; Sunlord MWSA1265S-220MT mass not published in the lookup, volume 13.45 x 12.6 x 6.5 mm x ~4.5 g/cm3 x 0.85 = about 4.5 g each, UNVERIFIED): L201-L206 6 x 4.5 g = 27 g; L200 3, L1 3, C275 2, J9-J11 2 each, J5 3, J1 2, J2/J3 3 each, U1 1.5, SW101 5 g (guesses); FR4 129 x 138 x 1.6 mm about 54 g; small parts about 35 g. Board assembly about 150 g (about 3.5 g/cm2 of heavy-part loading is negligible, one 4.5 g inductor on 1.6 mm FR4 deflects micrometres even at 40 mm span).
Model (`plate_v7.py`): Ritz, 14 x 14 cosine basis, free edges, point supports as stiff springs, E 18 GPa, nu 0.17, h 1.6 mm, uniform + point masses. Approximate (truncated basis, upper-bound trend). Results f1 / f2 / f3: 4 corner holes **131 / 210 / 226 Hz** (inside the 60-300 Hz woofer band: resonance risk); v7 10 holes **426 / 478 / 575 Hz** (1.4x above 300 Hz); removing the three front-row holes drops f1 to 114 Hz. Closed form check: simply supported 50 x 50 mm panel 1.1 kHz, 100 mm panel 340 Hz.
Support geometry: heavy part to nearest hole centre L201-L206 11.8-12.4 mm (met, <= 15), L1 10.3, C275 18.5, L200 21.1, J5 17.4, J1 21.9, J11 22.8, J9/J10 26.1 mm, U1 27.4 mm. Unmet: max distance board point to a hole 40 mm (target span <= 45-50 mm needs <= 25-30; the packer could only place holes in free gaps at RCOV 40; spans between holes are about 50-60 mm), L200 and C275 (18-21 mm), J9/J10/J11/J1 (22-26 mm). Remedy: second pass placing holes into leftover voids (several exist beside Boost/Charger FETs) or one more hole beside L200/C275.
Acoustic: woofer chamber below the board (inner 116 mm wide, 98 mm long); holes within the roof footprint sit on 3 mm roof + 4.5 mm boss; holes outside it (HA4 at u=62.8 and any hole in front of the chamber or beyond |x| 61) get an 8 mm printed post from the main-cavity floor (CAD `s['post']`), which keeps the chamber sealed. The board is 129 mm wide vs the 116 mm chamber: both side overhangs are unsupported by the roof but covered by posts/holes.
Screw check: M3x10 with 5 mm standoff + 1.6 mm PCB only engages 3.4 mm in the 5.7 mm insert (< 1.5 d): **M3x10 is wrong for the PCB, use M3x12** (5.4 mm engagement, tip stays inside the 5.7 mm insert; pilot 6.5 deep leaves 1.0 mm of the roof above the chamber ceiling, so the chamber stays sealed). CAD updated; the 6 lid/driver/woofer screws stay M3x10.

## Parts count (mechanical-bom.md)
M3x10: 19 (8 drivers + 4 woofer + 7 lid); M3x12: 10 (PCB); heat-set inserts 33; PCB standoffs M3 F/F 5 mm: 10; posts as above; board mass about 150 g.
