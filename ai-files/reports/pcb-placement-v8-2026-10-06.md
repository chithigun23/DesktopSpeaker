# PCB placement v8 (2026-10-06): sequence-pair compaction, 10 support holes. Placement only, not committed

Pipeline: `helpers/build_pcb_v8.sh` (cells -> `pcb/cells-v8.json`, board from `pcb/floorplan-v8.json`), `fp_sp_v8.py seed iters NH` (sequence-pair SA, raw files `pcb/floorplan-v8-raw<seed>_<NH>.json`), `fp_spec_v8.py raw.json`, `eval_holes_v8.py` + `plate_v7.py` (plate model). Chosen: `floorplan-v8-raw8_9.json` (24 seeds x 1.2 M iterations, NH 7/8/9). Render `pcb/layout-v8-top.png`.

## Method note
The continuous slide annealer (`fp_anneal_v8.py`, v6 start, shift/slide/swap moves) stayed at 16.4-18k mm2. The sequence-pair annealer (always overlap-free, longest-path compaction, separation minima as edge weights, walls by sliding) reached 14.6k for tiles only and about 15.4-15.6k with 8-9 support holes. Rotation/mirroring of tiles was NOT done (cells are generated in fixed orientation; rebuilding them rotated would need generator work).

## v6 / v7 / v8
| | v6 | v7 | v8 |
|---|---|---|---|
| Board | 116 x 138 | 129 x 138 | **121.1 x 127.4** |
| Area | 16,008 | 17,802 | **15,428 mm2** (target <= 14,000 NOT met) |
| Board depth | 138 | 138 | 127.4 (target <= 135 met) |
| Enclosure | 163 x 100 x 206 | 163 x 100 x 206 | **163 x 100 x 195** |
| Title strip / text | 1.2 / 0.7 mm | 2.3 / 1.7 | 2.3 / 1.7, abutting tiles share one wall |
| Holes | 4 | 10 | **10** (H1-H9 free 7.8 mm tiles, HA1 inside the AMP6 inductor row, row widened only +8 mm) |
| Plate f1/f2/f3 | 140/236/247 Hz (4 corners) | 426/478/575 | **387/437/450 Hz** (>= 350 met; removing 3 holes: 191 Hz) |
| 0402 caps near ICs (80): mean / max / >3 mm | 2.07 / 3.87 / 10 | same | same (2.07 / 3.87 / 10; snap unchanged) |
| BM83-analogue / class-D-analogue / boost-analogue / L1-analogue | 20.2/45.4/30.7/15.8 | 20.2/47.3/30.2/28.0 | 38.0 / 26.0 (all parts, 30.5 ICs) / 34.6 / 48.0; L2-analogue 28.3, U15/L3-analogue 10.2 (rule 10); all rules met (class-D 20.4 used) |
| DRC | courtyard/overlap/outline/shorting 0 | same, silk_overlap 5 | same 0; 28 violations = inherited hole_clearance 2, drill_out_of_range 8, silk_edge 4, silk_over_copper 9, silk_overlap 5; unconnected 499 |
| CAD | 0 unintended | 6 | **0 unintended** (SW101 rocker stand-in raised z 75 -> 78; it clipped the board corner), woofer chamber net 0.525 L, main 1.917 L |

## Holes (board-centred u, v mm) and distances
H1 (27.8, 16.5), H2 (46.9, -49.3), H3 (21.4, 59.8), H4 (2.2, 59.8), H5 (21.3, -24.2), H6 (4.5, -24.2), H7 (-57.1, -24.5), H8 (-57.1, 8.5), H9 (-57.1, 23.5), HA1 (-25.1, -37.5, inside the AMP6 row between L202 and L204).
Heavy part to nearest hole centre (mm): L201 13.6, L202 12.0, L203 13.4, L204 12.0, L205 13.5, L206 16.8, L200 17.7, L1 11.9, C275 10.4, J1 15.8, J5 14.4, J11 12.9; unmet: J9/J10 26.1 mm (targets <= 15), L200 17.7, L206 16.8; max board point to a hole 42.6 mm (target span <= 50 between supports met, <= 35 covering radius not). Corner holes were not possible: corners belong to BM83/antenna, amp row and connectors.
Masses are the v7 estimates (inductor 4.5 g each, unverified). Screws: PCB M3x12 on 5 mm standoffs (5.4 mm engagement in the 5.7 mm insert); M3x10 stays for drivers/lid/grille: **M3x10 for the PCB engages only 3.4 mm, flagged**. Board about 140 g.

## Why the 14,000 mm2 target is unmet
Tile sum is 12.9k mm2 (+ 9 hole tiles 0.55k) = 13.5k, so 14,000 would need 96 % fill. The annealer reaches 87.5 % (tile-only 14.6k = 88 %). Voids exist only because of rules: the 25.4 mm BM83-to-switcher/class-D zone, the 20.4 mm class-D/boost-to-analogue band (analogue tiles JACKS/MUX/ADC/USBAUD/CODSUP sit away from the amp row and boost), the 14 mm charger-analogue and 10 mm BT-buck-analogue gaps, the antenna keep-out at BM83, and the hole proximity/coverage targets (about +0.8k mm2 versus tiles-only). Visible voids: beside 3V AO / USB-C PD, right of the MCU tile, under the Wake tile. Remedies not tried: rotated/mirrored cells, relaxing the 20.4 class-D rule to the 15.4 used in v6 (not used here), L-shaped tiles.
Builder warnings 'cells too close' for 3 abutting tile pairs (BTSUP/LOG5V, MCU/BOOST, USBAUD/PDIN) are exact-1.0 mm content gaps by design; DRC courtyards 0.
