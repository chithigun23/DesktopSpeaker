# RT-5 footprint fixes: library patch for the coordinator (2026-11-02)

The board `RT-5.kicad_pcb` already carries these fixes (embedded footprints). The project library in
`DesktopSpeaker-kicad/kicad-library/footprint/` was **not** edited. Ready-made replacement files are in
`ai-files/pcb/work-route5/lib-proposed/`; copy them flat into the project footprint folder (no subfolders).
With these five files in a copy of the library (`work-route5/kicad-library/footprint/`), kicad-cli DRC reports
0 `lib_footprint_mismatch` / `lib_footprint_issues` for RT-5, so board and library agree.

| File | Change | Source (verified in this run) |
|---|---|---|
| `PJ-307.kicad_mod` (J2, J3) | Lines 30-31: front NPTH pegs `(at -5.75 -5.00)` / `(at -5.75 5.00)` -> `(at -4.75 -5.00)` / `(at -4.75 5.00)`. Nothing else. | `datasheets/PJ-307.pdf` PCB layout: pegs 1.0 and 3.5 from the body front, pin 1 at 3.1, pins 2-5 at 8.4. The body front is x -5.75 (pin 1 at -2.65), so the pegs are at -4.75 and -2.25. The footprint's own Cmts.User circles already mark (-4.75, +-5); only the NPTH pads were wrong. |
| `BM83SM1-00TA.kicad_mod` (U1) | Line 86: `(pad 56 smd rect (at 1.400 -0.030) ...)` -> `(at 4.770 -0.030)`. Nothing else. | DS70005402D p.56 Fig. 8-2 (top view): pad 56 (1.78 sq) at X 12.27 from the module's left edge, Y 10.47 from the bottom. Footprint frame: x = X - 7.5 (pad 57: 4.21 -> -3.29, matches), y = 10.44 - Y (pad 57: 20.58 -> -10.14, matches) -> (4.77, -0.03). The audit's "(+4.77, +0.03)" is the same point in the y-up 3D frame. |
| `TE_1977066-1_Tact_RA_SMD.kicad_mod` (SW100) | Replaced (DRAFT removed). Origin = terminal-pad row centre, actuator toward -y. Pads: "1" 0.75 x 1.8 at (+-1.225, 0) (terminals 1 and 3), "2" 0.6 x 1.8 at (0, 0); NPTH d0.9 at (+-2.125, -0.9); two net-less bracket tabs "" 1.3 x 0.9 at (+-1.85, -1.95); F.Cu keep-out (tracks, vias, pour) x -1..1, y -2.4..-1.2 (TE "prohibited area of copper tracks"). Courtyard -2.75..2.75 x -3.2..1.15; Fab: case 4.0 x 2.55 (front face y -2.1), actuator 2.0 wide to the tip at y -2.95. Model `TE_1977066-1.step` (models-v13) unchanged, offset 0. | TE drawing 1977066 rev C1 p.1, land pattern measured at 117.8 px/mm from the vector PDF: pads 1.80 tall; outer pads 0.75 (3.20 outer / 1.70 inner span); centre pad 0.60; holes 4.25 apart, centre on the pad-row edge line (0.9 from the pad centre) on the actuator side; bracket tabs 1.30 wide (5.00 / 2.40 spans) and **0.90 tall** (the 1.20 dimension is the hatched keep-out height, not the tab); tabs end 1.50 below the pad row edge. Side view: tip -> peg centre 2.05, peg 0.9 in front of the terminal row, so the tip is 2.95 from the pad-row centre. **Note:** the brief and the CAD audit said "bracket pads 1.2 x 1.3"; the drawing gives 1.3 x 0.9 (the 1.2 is the keep-out). |
| `CP_Elec_6.3x7.7.kicad_mod` (C275) | **New file**: copy of KiCad `Capacitor_SMD.pretty/CP_Elec_6.3x7.7.kicad_mod` with the model path changed to `${KIPRJMOD}/kicad-library/3d/CP_Elec_6.3x7.7.step` (the model C275 already used). Pads 3.5 x 1.6 at +-2.7. The C275 symbol's footprint field must change from `DesktopSpeaker:CP_Elec_8x10` to `DesktopSpeaker:CP_Elec_6.3x7.7` (schematic edit, coordinator). `CP_Elec_8x10.kicad_mod` can stay (unused after the change). | EEHZA1E101XP is case D8 (6.3 x 7.7) per the Panasonic EEH-ZA sheet; the 8x10 land left only 2.4 of 3.0 mm terminal overlap. |

## Rule-file exemption needed with the TE footprint

The TE land pattern puts the peg holes 0.075 mm from the terminal lands and 0.15 mm from the bracket tabs (by TE's design).
The board hole-clearance setting is 0.25 mm. `RT-5.kicad_dru` = project rule file + this appended rule (sentinel-tested, see the report):

```
# 20. RT-5 (documented additive exemption, sentinel-tested): TE 1977066-1 land pattern (TE drawing C1 p.1) puts the two d0.9 locating-peg
#     holes 0.075 mm from the terminal lands and 0.15 mm from the bracket tabs by design. Hole clearance 0.05 mm between SW100's own items only.
(rule rt5_sw100_te_land
  (condition "A.Parent == 'SW100' && B.Parent == 'SW100'")
  (constraint hole_clearance (min 0.05mm)))
```
Fabrication note: a 0.075 mm copper web to an NPTH edge is below JLC's usual NPTH-to-copper figure; the drill may nick the pad corner.
That is acceptable for a locating peg (the solder joint is on the pad body), but say so in the fab notes, or trim the outer pads to the
terminal width (0.65 at +-1.175) to get 0.175 mm.

## Placement consequence (board only, recorded in the RT-5 report)

SW100 moved (136.07, 25.245) -> (136.07, 22.95) so the actuator tip sits on the board edge (y 20.0); previously the tip was 2.30 mm
inside the edge. Lid: inner face edge + 0.5, outer face edge + 4.5 (cad/v13 meta `sw100`), so the lid button/plunger must bridge
0.5 + 4.0 mm. QON/GND copper at SW100 was redrawn (report section A).
