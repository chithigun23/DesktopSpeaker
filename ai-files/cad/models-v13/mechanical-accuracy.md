# Enclosure-level accuracy: real parts vs the CAD (models-v13, 2026-11-02)

This compares the CAD inputs in `ai-files/cad/build_speaker_cad.py` (v11.2 parameters `P`) with the real-part data found in this audit. OK means a deviation under 0.5 mm. FIX means 0.5 mm or more, or a geometry conflict. UNVERIFIED means no drawing could be found, so a measurement is needed.

Nothing in `ai-files/cad/` was changed. The new models are in `3d/` (see `MODELS.md`).

## Summary table

| Item | CAD v11.2 value | Real part (source) | Deviation | Verdict |
|---|---|---|---|---|
| ND65-4 flange | Maker STEP: 64.0 x 64.9 x 0.75 | Dayton spec 64 x 64 | 0.9 (one side of the scan) | OK for clearance; the scan is 0.9 wider in y |
| ND65-4 holes | STEP: Ø4.32 on a 66.3 bolt circle (46.8 sq) | Spec: Ø4.2 on a 66 bolt circle | 0.12 / 0.3 | OK. The STEP's hole pattern is 0.35 off the cone axis in y: confirm on the part |
| ND65-4 depth | 48.0 (3.25 + 44.75 behind the flange) | Spec 48 | 0 | OK |
| ND65-4 rear-mount aperture | 59.5 | Surround OD in the STEP 58.4 | | OK, 0.55 per side |
| **W3-2052SC flange shape** | Round Ø82.55 x 4.0 | **Square, 82.55 across, R ~4 corners** (PE photos ALT_1, HR_0) | Corners reach r 56.7 vs 41.3 | **FIX**: the corners do not fit the Ø83.4 round recess or the Ø86 ring pad |
| **W3-2052SC bolt pattern** | 4 x Ø3.5 on a 77 bolt circle | **4 holes on a 96.52 bolt circle = 68.25 square** (PE item JSON `custitem_pe_bolt_circle_diameter` 3.8 in). The photo measures 67.3 sq (±1) | 19.5 on diameter | **FIX**: holes at r 48.3, outside the current ring pad (r 43) |
| W3-2052SC hole Ø | 3.5 | ~3.4 with a ~7.3 counterbore on the front (photo) | ~0.1 | UNVERIFIED: an M3 fits; check the counterbore for screw heads |
| W3-2052SC cutout | 76.2 | 76.2 (PE). The frame opening in the photo is ~73.7 | 0 | OK (seller value) |
| W3-2052SC factory gasket | Not modelled. The CAD adds a 1.0 recess for a 0.5-1 foam ring | **3.3 black foam gasket already fitted on the front face** (photo ALT_2) | +3.3 stack | **FIX**: remove the CAD gasket and recess, and allow ~3 mm compressed gasket height |
| W3-2052SC frame thickness | 4.0 | ~13.3 solid frame block (photo) | 9.3 | FIX for screw length: M3 through 13.3 + gasket needs ~M3x20 into an insert |
| W3-2052SC depth | 44.45 | 44.45 PE (photo: 43.7 + 3.3 gasket) | 0 / gasket +3.3 | OK. Treat 44.45 as frame front to magnet, plus the gasket |
| W3-2052SC magnet | Ø40 (assumed) | ~Ø35.5 x 14.5 (photo) | -4.5 | OK (the CAD is conservative) |
| W3-2052SC terminals | None | 2-pin JST-PH-style plug on a ~100 mm twisted pigtail from a frame rib; no frame tabs | | Note: J11 needs a PH-to-VH adapter lead, or re-terminate the pigtail |
| Cells 2P | Ø21.7 x 70.2 | Samsung 50S max Ø21.25 x 70.62; Molicel P45B max Ø21.55 x 70.15 | Ø +0.45 / +0.15; length -0.42 / +0.05 | OK, but the 50S max length is 0.42 longer than the CAD. Raise `cell_l` to 70.7 for margin |
| Cell holder | Printed cradle (CAD-defined) | Custom | | OK (made to the CAD) |
| PCM/protection board | 3 mm slab placeholder | **Not sourced** | | UNVERIFIED |
| Rocker GRB112B802BR1 | Bore 20.2, notch 2.2 x 1.0, panel 2.0, flange 25 x 2.0, body stand-in Ø19.6 x 22 | Drawing: cutout Ø20.2 (+0.2/-0.1), notch 2.2 wide to 11.0 from the centre (= 0.9 past the hole edge), panel 1.5-2.5, bezel Ø25 ±1, 22.4 ±1 behind the panel to the terminal tips, rocker 11.5 ±1 above the panel, body ~17.5 sq at the clips | ≤ 0.4 | OK. The new model adds the rocker cap above the panel (11.5) and the clips and terminals |
| Heat-set inserts | OD 4.6, L 5.7, pilot 4.0 | Ruthex RX-M3x5.7: OD 4.6, L 5.7, hole 4.0 (retailer table) | 0 | OK. Maker drawing not obtained |
| Screws ISO 4762 M3x10 / M3x16 | Head Ø5.5 x 3.0 | Standard | 0 | OK |
| PCB spacer | 10 mm hex 5.5 AF | Würth 970100321, M3 F/F 10 mm, 5.5 AF | 0 | OK (Würth datasheet 403; distributor data) |
| Feet stud | 12 body + 6 stud | Würth 971120321, M/F 12 + 6, 5.5 AF | 0 | OK |
| Rubber feet | Ø12 x 3 | Not selected | | UNVERIFIED |
| Gaskets | Lid 3 mm foam cord in a 2 x 1.5 groove; driver 0.5 recess | Material not selected | | UNVERIFIED. Woofer: see above |
| Grilles | 0.8 plate, Ø2.0 holes / 3.0 pitch | Custom | | OK (made to the CAD) |
| Encoder knob | Ø30 x 14 stand-in | **Not selected** | | UNVERIFIED |

## Rear-lid cutouts vs corrected board-part models

The cutouts are derived from the board STEP. With the v13 models:
- **J1 (USB-C).** The mating face is 2.60 in front of the front leg slots, so 2.13 mm past the drawing's PCB-edge line. The opening is 8.34 x 2.56 (stadium) centred 1.68 above the board top; the old model was 1.65, so the change is +0.03. The shell outer is 8.94 x 3.16. The lid cut of 12 x 7 R2 leaves 1.5 / 1.9 mm around the shell. USB-IF allows plug overmolds up to 12.35 x 6.5, so some plugs will not enter a 12.0 wide hole. If the lid is thicker than the receptacle's overhang, use 12.6 x 7.
- **J2/J3 (PJ-307).** The model is unchanged and correct: nose Ø6.0 at 2.5 above the board, bore Ø3.6, nose 3.3 long. The nose bottom is 0.5 below the board top surface, so the nose must overhang the board edge. **The footprint front pegs are wrong by 1.0 mm** (see the report).
- **SW100 (TE 1977066-1).** The actuator is Ø2.0, centred 1.70 above the board top, with its tip 2.95 in front of the terminal-pad row. The board side is valid only after the footprint is corrected (see the report). The lid opening of 5.0 gives 1.5 per side around the actuator.

## Caliper checklist for the owner

Measure in mm to 0.1. Mark any item you cannot measure.

**Tang Band W3-2052SC** (highest priority: the woofer mounting is a FIX in the enclosure):
1. Frame outer width, x ___ y ___ ; corner radius ___
2. Hole centre-to-centre, x ___ y ___ diagonal ___
3. Hole Ø ___ ; front counterbore Ø ___ depth ___
4. Frame block thickness without the gasket ___ ; factory gasket thickness, free ___ compressed ___
5. Front opening Ø ___ ; surround outer Ø ___
6. Overall depth, frame front (without gasket) to magnet back ___
7. Magnet cup Ø ___ height ___ ; basket max Ø ___
8. Pigtail exit: rib angle from a hole ___, length ___, connector type ___

**CW GRB112B802BR1 rocker:**
9. Bezel Ø ___ thickness ___ ; rocker height above the panel, high side ___ low side ___
10. Body width behind the panel at the clips ___ ; clip span ___ ; panel-face to terminal tip ___

**Cells**, when bought: Ø ___ length ___ ; positive button Ø ___ height ___ (Samsung 50S / Molicel P45B)

**PCM board:** L ___ W ___ H ___ ; wire and strip exit positions ___

**Keystone 5010-5014 test points:** body Ø ___ body height ___ overall height ___ pin Ø ___

**Micro-Fit J5**, the delivered part (genuine Molex or LXW): housing L ___ depth ___ height ___ lock height ___

**ND65-4:** hole centre-to-centre x ___ y ___ ; hole-pattern centre vs cone centre offset ___

**Encoder knob**, once selected: OD ___ height ___ bore depth ___ skirt ___

**Ruthex insert:** OD ___ length ___
