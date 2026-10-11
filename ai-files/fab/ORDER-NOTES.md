# JLCPCB order notes (draft 2026-10-12, before the final teardrop pass)

Final gerber/drill/position files are produced by `ai-files/helpers/fab_export.sh DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb ai-files/fab/out R7` after the teardrop pass and the DRC/gate re-run. The notes below are the order options; they do not change with teardrops.

## Board
| Option | Value | Why |
|---|---|---|
| Layers | 4 | stackup JLC04161H-7628 (F.Cu 35 um / 7628 prepreg 0.2104 / In1 / 1.065 core / In2 / 7628 / B.Cu 35 um), as set in the board stackup block |
| Thickness | 1.6 mm | stackup |
| Outer copper | 1 oz | power pours on F/B |
| Inner copper | 0.5 oz | design assumption (15 K rise accepted for the 8 A paths with In2 pours in parallel with F.Cu); 1 oz inner is an allowed upgrade, no re-route needed |
| Surface finish | ENIG | fine-pitch QFN/VQFN (TAS5825M, BQ25792, TPS25730D, PCM1862) and the BM83 module; HASL acceptable only if ENIG is unavailable |
| Impedance control | No | USB is full speed (12 Mbit/s), pair kept at 0.25 / 0.15 mm (about 92 ohm by calculation); accepted by the user (USB FS waiver in `DesktopSpeaker.kicad_dru`) |
| Via covering | Tented (solder mask over vias) | default; the 43 fine vias 0.5/0.2 mm in neck areas and 3 vias in SMD pads (R10.2, R224.1, C215.1, user-accepted) stay tented; the via-in-pad ones may wick a little solder, inspect after assembly |
| Min drill | 0.2 mm | 43 fine vias (0.5/0.2) and 8 x 0.2 mm PTH in the U11 footprint thermal pad; JLC 4-layer standard allows 0.2 mm |
| Min track / clearance | 0.15 / 0.15 mm class, used only in neck areas; general 0.2 mm+ | rules file |
| Solder mask / silk colour | user choice (green/white is cheapest) | silk is on F and B |
| Mark on PCB / order number | "Remove" or specify location; there is an Orwellian logo on the back, do not let JLC place the order number on the front silk | cosmetic |
| Gold fingers / castellations | none | |
| Board outline | 127.6 x 137.7 mm, 3 mm corner radius; 11 M3 mounting holes (3.2 mm PTH, GND), 4 x 2.375 mm NPTH for J7 Tag-Connect legs | from Edge.Cuts |
| Panel | single piece | |

## Assembly (if JLC SMT is used)
- BOM: `ai-files/bom/DesktopSpeaker_JLC_BOM.csv` (90 lines, 318 placements), notes in `ai-files/bom/jlc-assembly-notes.md`.
- CPL: `<TAG>-pos-jlc.csv` from `fab_export.sh`; all parts top side; 27 test points appear in the CPL but have no BOM line (JLC will flag them, ignore).
- Through-hole: J4, J6, J8 headers; J5 Micro-Fit; J9-J11 JST VH; C275 electrolytic; SW102 encoder; J2/J3 jacks; J1 USB-C hybrid pins. Either JLC THT assembly or hand soldering.
- Not assembled: SW101 panel rocker CW GRB112B802BR1 (Digi-Key, wired), R256 (DNP, fit 0R at the bench for forced PWM on U25), J7 (Tag-Connect footprint only).
- Stock risk at 2026-10-10: BM83SM1-00TA (U1) stock 1, SW102 now EC11E18244AU C202365 (398 in stock 2026-10-12), SW101 now a Digi-Key part. Re-check every line at order time.

## Before ordering (checklist)
1. Teardrop pass in the GUI, refill, save; coordinator gates (DRC 0/0, strict, sliver, islands, corners).
2. `fab_export.sh` on the saved board; view every gerber layer in the KiCad gerber viewer (or JLC's preview): copper, mask, paste, silk, edge, drill maps.
3. JLC preview: check rotations of polarised parts (D*, C275, U1 pin 1, J1, SW100, U4/U6/U7 pin 1) and fix in the CPL if needed.
4. Confirm stock and the price per line; the starter BOM subtotals are partial, not product cost.
