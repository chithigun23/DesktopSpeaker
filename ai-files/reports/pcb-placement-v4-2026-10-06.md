# PCB placement v4 (2026-10-06): functional cells in a tiled floorplan. Placement only: no routing, no zones except the BM83 rule area

File `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` (311 footprints + 4 PTH GND holes). Generator `ai-files/helpers/build_pcb_v4.sh` (about 12 s, deterministic: PYTHONHASHSEED=0; replaces the 10 min annealer). Pipeline: (1) `build_pcb_v4.py` places each of 20 cells (IC heads + inductors/connectors anchored, all R/C by pin-attracted ring search, critical 0402 decaps first) in isolation on a far-apart canvas and writes `ai-files/pcb/cells-v4.json` (cell sizes); (2) `fp_pack_v4.py` (run with the KiCad python for numpy) packs the cell tiles with hard separation rules, edge-flush rows (rear: BM83|WAKE|JACKS|PDIN, front: AMP6/AMP7) and corner/edge holes; (3) `fp_spec_v4.py` writes `ai-files/pcb/floorplan-v4.json`; (4) `build_pcb_v4.sh` again builds the board (tiles stretched to abut, silk rectangle + centred title per tile, titles at the bottom for rear-edge tiles). Tools: `fp_search_v4.py`/`fp_hand_v4.py` were abandoned experiments. Checks: `pcb_check.sh`, `pcb_dist_check.py` (`dist-v4.txt/.json`), `pcb_sep_v4.py`.

## Result
- Board **117.5 x 176 mm = 20,680 mm2** (v3 116 x 112 = 12,992 mm2): **larger, not smaller** (+59 %). Reasons: 20 isolated cells (sum of cell boxes 13,200 mm2, courtyard sum only 4,800) plus tile margins and the hard separation rules (BM83 15/25 mm, class-D/boost 20 mm from analogue) cost more than the v3 interleaved zones; the 117.5 mm width is needed for the rear row (BM83 34.8 + WAKE + jacks + USB-C), 1.5 mm over the 116 mm roof limit.
- Looks like the reference board: tiled grid of boxed sections with centred titles (Bluetooth, Wake, Headphone / aux jacks, USB-C connector + ESD, USB-C + PD input, Fuel gauge + low-current power, 3V AO, MCU + SWD, USB audio codec, ADC, Source mux + headphone, 5V codec rail, Charger FETs, Charger, BT supply, Boost, 5V logic, Connectors (battery), Amplifier front (U6) + output filters, Amplifier woofer (U7) + filters). Holes: H3 right edge, H4 and H1 left edge, H2 front-right corner (not four corners: BM83 antenna, USB-C and amp rows own the other corners). Renders `ai-files/pcb/layout-v4-top.png`, `layout-3d-top.png`, `layout-top.pdf`.
- Not as in the reference: passives inside a cell are ring-packed around the IC, not in neat aligned rows; test-point/LED strips not added (no test points in the netlist).

## DRC (`pcb_check.sh`)
courtyards_overlap / overlap / outline / copper_edge / shorting / pth_inside_courtyard **0**; remaining 25: hole_clearance 2 (SW100), drill_out_of_range 8 (TPS25730D thermal vias), silk_edge_clearance 7 (J1/U1 flush parts, tile rim), silk_over_copper 8 (J2/J3 and tile lines); unconnected 499 (nothing routed); parity 0. All inherited kinds; v3 had 35.

## Separations (courtyard/bbox gaps, `pcb_sep_v4.py`)
| Rule | Required | v3 | v4 |
|---|---|---|---|
| BM83 to analogue ICs/jacks/passives | 15 | 16.1 | **27.0** (U1-D200); the two BT-audio coupling parts R223/C233 belong to the BM83 cell (2.5 mm, as the RF-side network) |
| BM83 to class-D / boost / L1 / L2 | 25 | 56.2 / 105.5 / 72.0 | **98.9 / 101.7 / 132.0 / 149.0** |
| BM83 to its own U15/L3 | 25 | 33.6 | **76.4** |
| Class-D to analogue ICs / all parts | 20 | 24.0 / 20.8 | **41.0 / 32.4** |
| Boost to analogue ICs / all parts | 20 | - / 50.9 | **37.2 / 30.5** |
| L2/U14, L1/U4 to analogue (all parts) | 20 / 15 | 31.0 / 14.1 | **77.8 / 52.6** |
| U15/L3 to analogue passives | (none) | 11.0 | 6.3 (L3-R234) |
All hard rules met with margin: the packer used the rules with 0.4-1 mm safety and the achieved gaps are larger than needed (room to compact further by hand).

## Decoupling distance, v3 -> v4 (pad centre to nearest pad of the net on the IC; mean mm; `dist-v3.txt`, `dist-v4.txt`)
| IC | v3 | v4 | IC | v3 | v4 |
|---|---|---|---|---|---|
| U6 TAS5825M | 5.88 | **7.70** (worse: 10 bulk PVDD and 4 inductors share the ring) | U7 TAS5825M | 3.14 | **2.48** (max 4.69) |
| U4 BQ25792 | 5.98 | 5.85 | U25 TPS61088 | 4.38 | **4.98** (worse) |
| U24 PCM1862 | 6.41 | 5.63 | U2 PCM2902C | 5.97 | **3.86** |
| U3 MCU | 5.10 | **3.46** | U11 TPS25730D | 3.42 | 3.76 |
| U22 / U23 LDO | 4.63 / 3.10 | **2.25 / 2.31** | U14 / U15 / U10 | 4.71 / 4.16 / 3.89 | 3.15 / 4.03 / 3.32 |
All 230 passives: mean 5.42 -> 4.66, max 28.4 -> 14.8. 0402 HF decaps: mean 3.45 -> **3.25**, max 8.5 -> 7.9, above 3 mm 31 -> 32 of 62. Bulk 0805: mean 6.85 -> 6.13. Caps with a GND pad: mean 5.03 -> 4.59, above 3 mm 78 -> 80.
**Unmet: every critical cap <= 2.5 mm.** Only the small, lightly loaded cells (U7, U22, U23, U2, U3, U14, U8/U9 muxes) get there; U6 (26 passives), U4, U25 and U24 still have 3-10 mm caps (U6 3V3 C293 13.8 mm, PVDD bulk 7-11 mm, U4 SYS 8.5-8.9 mm, U24 AVDD/LDO 8-9 mm). Limit: ring capacity (3 parts per QFN side with 0.8 mm labels + 0.5 mm gaps) and the greedy order; the 0805 PVDD/SYS bulk caps push the 0402s out. Next: nudge the 12 worst caps by hand, or labels of first-ring caps to a fab layer / 0201 HF caps (see rules section 8). U25 FB/COMP parts: R251 4.7 mm from FB, nearest SW pad 4.6 mm (rule: away from SW; v3 5.8).

## Enclosure/CAD (`ai-files/cad`, rebuilt from `layout.json`)
Outer 163 x 100 x **244** mm (v3 180 deep), **0 unintended overlaps** (6 intended connector-in-PCB pairs). **Woofer chamber net 1.003 L (target 0.45-0.60; v3 0.625)** and main chamber 2.10 L, because the chamber runs to the lid: the deeper board breaks the acoustic design unless `ch_y0` in `build_speaker_cad.py` is moved rearwards or the board is made shorter. External volume 3.98 L.

## Open items
1. Board is 59 % larger than v3: decide between this layout (clear sections, easy to debug) and a denser cell compaction pass (cells fill only about 36 % of their box) or relaxing the rules to their stated minimums (class-D/analogue 10 mm with a ground fence).
2. Decoupling <= 2.5 mm unmet for U6, U4, U25, U24 (above).
3. Woofer chamber 1.003 L and enclosure depth 244 mm.
4. Width 117.5 mm vs 116 mm roof limit (check against the rocker body, CAD shows no overlap).
5. Inherited: footprint issues (SW100 hole clearance, TPS25730D via drill), TPS61088 datasheet missing, no test points/LED strip.
