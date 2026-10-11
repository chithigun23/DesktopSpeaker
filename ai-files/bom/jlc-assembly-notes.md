# JLC assembly BOM notes (2026-10-12)

- `DesktopSpeaker_JLC_BOM.csv`: 90 lines, 318 placements, generated from the schematic fields (LCSC / LCSC Part, MPN, Manufacturer) with `kicad-cli sch export bom`, grouped by LCSC code + footprint (the Comment is the most common value string; value spellings differ in the schematic). All lines carry an LCSC code; codes match `DesktopSpeaker_LCSC_Starter_BOM.csv` reference for reference.
- Excluded: R256 (DNP), SW101 (panel-mount rocker, wired to the board; not assembled). J7 (Tag-Connect footprint, no part) and the 27 test points are not BOM items; mounting holes H1-H9/HA1/HA2 and the logo have no placement.
- Position file: `helpers/fab_export.sh` writes `<TAG>-pos-jlc.csv` (Designator, Mid X, Mid Y, Layer, Rotation, mm) from the board; it lists 347 placements = 318 BOM placements + 27 test points. All parts are on the top side (single-side assembly).
- Rotation: JLC's footprint zero may differ from KiCad's for some packages (connectors, SOT-23, polarised caps); check the JLC preview before confirming the order and fix rotations in the CPL, not in the board.
- Through-hole parts (J4/J6/J8 headers, J5 Micro-Fit, J9-J11 JST VH, C275 electrolytic, SW102 encoder, J2/J3 jacks, J1 USB-C hybrid) need JLC's THT/extended assembly option or hand soldering.
- Stock caveats from the sourcing pass still apply: SW102 EC11E15244G1 (C370970) and SW101 had zero LCSC stock on 2026-10-10 (in-stock alternatives EC11E18244A5/AU are 36 detent / 18 pulse); BM83 stock 1; re-check every line at order time.
