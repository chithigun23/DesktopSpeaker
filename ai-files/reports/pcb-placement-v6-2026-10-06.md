# PCB placement v6 (2026-10-06): denser cells, packer on a 0.25 mm raster. Placement only, no routing

Board `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` (311 footprints + 4 PTH GND M3 holes). Pipeline `ai-files/helpers/run_v6.sh [seeds]` (`build_pcb_v6.py` -> `fp_pack_v6.py` -> `fp_spec_v6.py` -> board; `TRIALS=200 HMIN=118` with 8 seeds takes about 8 min). Checks: `pcb_check.sh`, `dist_v6.sh`, `decap_list_v6.py`, `pcb_sep_v6.py` (needs `--filesystem=/tmp`), `pcb_gap_check.py`. Renders `ai-files/pcb/layout-v6-top.png`, `layout-3d-top.png`.

## Changes v5 -> v6
- Cells: front amp jacks beside U6 (zone bottom -11.6), inductor row 1.5 mm lower (`LV` 14.5), U7 cell narrowed, tighter anchor pitch for fuel gauge / mux / codec rail / charger FETs, greedy passive pull to the cell centre (`HINTW` 0.02 -> 0.6). Cell box sum 12,300 -> about 11,000 mm2. A simulated-annealing compaction (`SA=` env, existing `anneal`) was tried: 190 s, 16 violators legalised outside their cells, cell boxes blew up; left off.
- Tiles: title strip 1.9 -> 1.2 mm (title text 0.7 mm, 0.12 thick; project `min_text_height` 0.6). Tile sum 15,000 -> 12,700 mm2 (+ four 8 x 8 hole tiles).
- Packer: occupancy raster 1 mm -> 0.25 mm, 0.5 mm candidate step, H step 1 mm, base cell order with noise or area/height orders, per-trial heuristic mix, BATIO free along the right edge, mounting-hole tiles free (28 mm apart), BM83 3V8 buck (BTSUP) >= 10 mm from analogue cells (new; the unconstrained 134 mm result had L3 4.2 mm from C224).
- **Deliberate decision (flagged): class-D/analogue minimum 20.4 -> 15.4 mm** in the packer (rules doc `pcb-layout-rules-audio.md`/v2 report: 20 mm, 10 mm absolute with a GND via fence). Not binding in the final result (47.9 mm achieved), so no fence is needed for it; if the rule is used later, add a GND via fence row between the zones.

## v3 vs v5 vs v6
| | v3 | v5 | v6 |
|---|---|---|---|
| Board | 116 x 112 | 116 x 152 | **116 x 138** |
| Area mm2 | 12,992 | 17,632 | **16,008** (-9 % vs v5, +23 % vs v3) |
| Enclosure depth (Y) | 180 | 220 | **206** |
| Woofer chamber net | 0.625 L | 0.525 L | 0.525 L (auto) |
| 0402 caps near ICs: n / mean / max / >3 mm (same metric, dist json) | - | 80 / 3.10 / 9.4 / 30 | 80 / 3.23 / 10.1 / 32 |
| U6 / U24 / U4 / U25 passive mean | 5.88 / 6.41 / 5.98 / 4.38 | 5.22 / 4.48 / 4.82 / 4.44 | 5.59 / 4.79 / 5.05 / 4.42 |
| U7 / U22 / U23 / U2 / U3 / U10 passive mean | 3.14 / 4.63 / 3.10 / 5.97 / 5.10 / - | 2.15 / 2.25 / 2.31 / 3.64 / 3.23 / 2.68 | 2.23 / 2.25 / 2.31 / 3.67 / 2.92 / 2.73 |

Separations (mm, required): BM83 to analogue 20.2 (15); BM83 to class-D 84.6, boost 69.9, L1/U4 77.2 (25); class-D to analogue ICs 47.9 / all parts 45.1 (15.4 used, 20 in the doc); boost to analogue 34.2 / 30.5 (20); L2/U14 27.1 (20); L1/U4 15.7 (14); U15/L3 to analogue 24.2 (10, new).

## Checks
DRC (`pcb_check.sh`): courtyards_overlap / overlap / outline / copper_edge / shorting / pth_inside_courtyard 0; remaining 28 are inherited kinds (hole_clearance 2, drill_out_of_range 8, silk_edge 5, silk_over_copper 9) plus silk_overlap 4 (reference labels C214/C217, C214/C222, C231/C238, C231/C241); unconnected 499 (not routed). `pcb_gap_check`: 100 courtyard gaps < 0.45 mm (min 0.32; same as v5), text over courtyard 0. CAD: outer 163 x 100 x 206 mm, 0 unintended overlaps (6 intended connector pairs), woofer chamber net 0.525 L.

## Unmet targets and causes
1. **Area 16,008 mm2 (target <= 13,000) and enclosure depth 206 mm (target <= 190, needs board <= 122 mm).** Tiles (12.7k + holes) fill 84 % of the board; filling to 13,000 needs 95 % with fixed rows. Cell boxes are still ~40 % courtyard; passives are greedily ring-packed. 8 seeds x 200 trials x 20 heights plateau at 134-138 mm (134 mm without the BTSUP rule). Next levers: rotated tiles (needs rotatable cells), true row/column cell layouts (aligned passive rows), a working compaction pass (the SA is too slow/unstable), or the 2-board split.
2. **Decaps**: critical 0402 not improved (mean 3.23 vs 3.10; U6 BST/OUT 4-10 mm, U24 8 caps > 3 mm, U4 5.9 mm). The tile compaction (`HINTW`) acts on unlocked passives only; locked decaps are unchanged, differences come from the new cell shapes. Not at the 2.5 mm target (41 of 80 above 2.5 mm).
3. Label overlaps 4 (silk_overlap) and 100 courtyard gaps < 0.45 mm remain. Mounting holes are on the left/right edges, not corners (BM83, USB-C, amp row and battery connector own the corners).
