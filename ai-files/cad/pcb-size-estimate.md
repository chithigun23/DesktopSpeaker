# PCB size estimate (2026-10-06) - ESTIMATE, no PCB layout exists

Method (script `pcb_estimate.py`, input `work/net.xml` = `kicad-cli sch export netlist` of the root sheet):
1. All 322 netlist components were mapped to their assigned footprint in `DesktopSpeaker-kicad/kicad-library/footprint`.
2. Each footprint's F.CrtYd bounding box (W x H) was summed (all 322 have a courtyard): **sum = 5 679 mm2** (details: `work/pcb_estimate.json`).
3. SW101 (panel-mounted rocker, courtyard 20 x 20 = 400 mm2) is wired to the rear lid, not on the board: **5 279 mm2** for 321 parts.
   Largest contributors: 6 x output inductors MWSA1265S 15 x 13.1 (1 179 mm2, 22 %), BM83 15.9 x 32 (508), STM32G071 13.4 sq. (180), 2 x PJ-307 jacks (341), J5 Micro-Fit (149).
4. Placement/routing/keepout factor 2.0 (courtyard area x 2.0 = 10 558 mm2 of copper area needed), two-sided assembly assumed to halve it: 5 279 mm2 of board.
5. + about 15 % for the board edge, 4 corner M3 holes, antenna keep-out and connector overhang: **about 6 100 mm2**.
6. Proposed outline: **100 x 66 mm = 6 600 mm2, 1.6 mm FR4**, M3 holes (3.2 mm) at 4 points 47.0 mm x 29.5 mm from the centre (6 mm pad, 3 mm from edges). 8 % spare over the estimate.

Assumptions and weak points: the 2.0 factor is a rule of thumb (a 4-layer, dense, two-sided board could be 1.6, a hand-routed board 2.5); the PA-class parts (TAS5825M, boost, 6 inductors) need PGND copper zone; underside parts are not modelled. Treat +-25 % (5 000 - 8 000 mm2) as the uncertainty; the chamber roof carries a board up to about 115 x 66 without changing the enclosure.

3D models on the board: only parts with a STEP in the library and area >= ~14 mm2 or edge function are placed (U1 BM83, J1 USB-C, J2/J3 jacks, U3, U2, U24, U4, U11, U6/U7, U25, L1-L3, L200, L201-L206, C275 and J4/J6/J8). **Skipped small parts:** about 280 resistors/capacitors (the 14 PD_C_1210 caps, 0603/0402 passives), SOT/DFN ICs, crystals, diodes, J7 Tag-Connect (pads only). Box stand-ins (no STEP): J5 Micro-Fit, J9-J11 JST B2P-VH, SW100 tact switch (plunger through the lid). SW101 rocker is a panel stand-in on the lid.

Zones (u = across, v = front to rear): rear edge = USB-C J1, jacks J2/J3, SW100 facing the lid cutouts; rear-left = BM83 with its antenna end overhanging the left board edge by 8 mm over empty cabinet air (no battery, magnet or rocker nearby); front = 6 output inductors in two rows with U6/U7 behind them (PGND zone) and the JST speaker connectors on the left; right = boost U25/L200/C275, charger L1-L3/U4/U11, J5 at the right edge, pin headers; centre = MCU, USB audio codec, ADC.
