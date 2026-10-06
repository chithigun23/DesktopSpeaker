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

## Decap snap (added 2026-10-06, same board 116 x 138 mm, cell/tile positions unchanged)
Cause of the poor decoupling distance: every passive carried a silk reference slot and a >= 0.45 mm courtyard gap, so only about 3 caps fitted along a QFN side. **Policy now: reference designators of all 0402 R/C/FB are on F.Fab (visible, 0.6 mm, so they remain in the assembly layer, the placement CSV/report and the 3D/fab prints); silk labels stay on ICs, connectors, inductors, switches, diodes/transistors and on 0805 caps when a clean slot exists (otherwise F.Fab).** Courtyard gap 0.25 mm (0402/0402), 0.3 mm (other passives), 0.15 mm to ICs, 0.5 mm to tall parts; pad-to-pad >= 0.2 mm to every other footprint (hand-solder iron access remains from the outside).
Stage `ai-files/helpers/snap_v6.py` (called from `build_pcb_v6.py` after the floorplan shift, `SNAP=0` disables; `run_v6.sh`/`build_pcb_v6.sh` unchanged for the user): all 250 passives with an IC pin on a signal net are lifted and re-placed deterministically on a 0.1 mm raster (0.2/0.3 mm farther out), cost = pad-to-nearest-IC-pin distance on the served net (same cell first) + 0.08 x GND-pad distance to the IC GND pads + 0.03 x displacement; all four rotations; staying inside the tile (cell box + 0.3 mm, so no box growth, no board growth). Priority: critical-IC caps (U6, U7, U4, U25, U24, U3, U1, U15, U22, U23, U2, U14, U11; 0402 first, smaller value first), other 0402 caps with a GND pad, other 0402, then 0805/bulk. A eviction pass for far critical caps found no legal swap (0 moves). 6 passives had no legal closer spot and keep their v6 position (R101, R113, C200, R176, R180, R181).

| IC | passives n | mean before | mean after | max before | max after | 0402 caps > 2.5 mm before / after |
|---|---|---|---|---|---|---|
| U6 TAS5825M | 26 | 5.59 | 3.39 | 10.13 | 6.87 | 7 / 4 |
| U7 TAS5825M | 9 | 2.23 | 1.58 | 3.10 | 2.51 | 3 / 1 |
| U4 BQ25792 | 16 | 5.05 | 3.67 | 7.42 | 6.06 | 2 / 0 |
| U25 TPS61088 | 17 | 4.42 | 4.14 | 8.53 | 8.53 (C275, 0805/1210 bulk) | 2 / 1 |
| U24 PCM1862 | 32 | 4.79 | 3.15 | 8.50 | 4.92 | 10 / 8 |
| U3 STM32 | 6 | 2.92 | 2.74 | 3.58 | 4.81 (R160 SWD) | 0 / 0 |
| U1 BM83 | 12 | 3.48 | 2.80 | 5.55 | 3.81 | 1 / 1 |
| U15 / U22 / U23 | 9 / 2 / 3 | 3.97 / 2.25 / 2.31 | 2.77 / 1.54 / 1.58 | 5.00 / 2.50 / 2.50 | 3.93 / 1.58 / 1.70 | 0 / 0 / 0 |
| U2 PCM2902C | 14 | 3.67 | 2.84 | 5.09 | 4.40 | 5 / 2 |
| U14 / U11 | 6 / 13 | 3.35 / 3.19 | 2.65 / 2.39 | 4.40 / 4.95 | 3.34 / 3.85 | 0 / 0 |

0402 caps near ICs (80): mean 3.23 -> 2.07 mm; the 62 HF decaps (0402 with GND pad): mean 2.05, max 3.87, 9 > 3 mm. Other passives (150): mean 3.32. All 230 passives with an IC pin: mean 2.88 (v6 about 3.4). 0805+ bulk caps (54): mean 3.93, 37 > 3 mm.
**Targets met:** HF mean <= 2.2, other passives <= 3.5, board size unchanged. **Not met:** every critical decap <= 2.0 (2.5 hard): 24 0402 caps remain between 2.5 and 3.9 mm, mostly U24 (8: VREF C212 3.87, 3V3_AUDIO C219/C220/C222, AVDD C215, LDO C213, VINR1/2 C207/C209), U6 (C284 AVDD 2.9, BST C287/C288, C294 2.5), U2 (C173/C174), U10/J3/D201 audio parts; the 20-caps-plus-13-resistors crowd around the TSSOP U24 and the 0.65 mm pitch limit what fits within 3 mm. Bulk 0805 at U6 PVDD (C270/C272/C277/C279/C292) and U4 PMID/SYS (C101/C104/C107) stay 3-7 mm (bulk: acceptable, HF 0402 PVDD caps are close). Next lever if needed: let the cell packer reserve decap rings around U24/U6 (bigger cells) or swap the 0805 PVDD caps to 0603.
Checks after the snap: DRC courtyards_overlap / overlap / outline / copper_edge / shorting / pth_inside_courtyard 0; no new clearance or solder-mask-bridge types; remaining are the inherited hole_clearance 2, drill_out_of_range 8, silk_edge 5, silk_over_copper 9 plus 1 silk_overlap (board title text vs a tile line; the four C214/C217/C222/C231/C238/C241 reference overlaps are gone, tile titles shortened to 'Jacks' / 'Battery I/O' removed two more); text_height 0 (`min_text_height` = 0.6 in `DesktopSpeaker.kicad_pro`; **pcbnew `SaveBoard` in the build resets it to 0.8, now restored by the last line of `build_pcb_v6.sh`**); unconnected 499 (not routed). `pcb_gap_check`: 359 courtyard gaps < 0.45 mm (by design, min about 0.15 to ICs, 0.25 between 0402), separations unchanged (BM83-analogue 20.2, class-D-analogue 45.4, boost-analogue 30.7, L1/U4-analogue 15.8 mm). CAD not rebuilt: board, tile and all tall/IC/connector positions are unchanged (only passives moved). Before-snap board and metrics: `ai-files/pcb/before-snap/`.
