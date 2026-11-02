# CAD component accuracy audit (2026-11-02)

**Request (owner):** "lets really try making the cad accurate down to less than 0.5mm. use as detailed of a model as you can find for each components and where you cant make them".

**Scope:** every footprint on `ai-files/pcb/work-route3/RT-3.kicad_pcb` (360) plus the enclosure-level parts.

**Staging:** everything is staged in `ai-files/cad/models-v13/`. Nothing in `DesktopSpeaker-kicad/` or the `ai-files/cad/` originals was changed. Nothing was committed.

## Result in numbers

The 360 footprints are 346 physical parts plus 14 N/A: 11 mounting holes, the J7 Tag-Connect pads, LOGO1, and the SW101 wire pads (the rocker is panel-mounted).

| | Before (RT-3 as is) | After (`apply-map.json` applied to a scratch copy) |
|---|---|---|
| Parts with a 3D model | 314 / 346 | 346 / 346 |
| Model within 0.5 mm of the datasheet (L, W, H) | 311 | 340 |
| FIX (≥ 0.5 mm, wrong detail, or no model) | 34 = 32 without a model (J5, J9-J11, SW100, TP1-TP27) + U24 (TSSOP-30 model 0.5 too high) + J1 (box-level USB-C, opening corners 0.53) | 0 |
| UNVERIFIED (no drawing obtainable) | 1 (L200 XAL7070) | 6 (L200; TP23-TP27 Keystone 5010-5014: built from distributor data) |
| Lead/pad mismatch > 0.1 mm | 3 (J2, J3, U1) | 4 (J2, J3, U1, SW100). **All four are footprint errors, not model errors** |

**Coverage of verified models after the change:** 340 / 346 = 98.3 %.

**What "verified" means here:**
- **Passives:** checked at class level. The 0402 and 0805 MLCC/resistor thickness codes were taken from the MPN datasheets or the family datasheets.
- **ICs:** the model body envelope was checked against the TI, ST or maker package drawing (nominal values).
- **Leads:** checked by slicing at board level against the pads, with a 0.1 mm tolerance. Where the vendor model fuses the terminals with the body underside, lead checking is not possible and is marked n/a.

No part is claimed below 0.5 mm unless a drawing was compared.

**Models:**
- **Downloaded:** 0. All manufacturer and distributor STEP routes failed; about 50 attempts are logged in `ai-files/cad/models-v13/downloads/SOURCING-LOG.md`. TE, Coilcraft, Bourns, Microchip, Keystone and Würth returned 403. Molex and Alps did not respond. JST is form-gated. EasyEDA gives OBJ only.
- **Built for the board:** 8 parametric models from drawings, plus 1 offset correction:
  - JST B2P-VH
  - Micro-Fit 43650-0300 (from the LXW equivalent drawing)
  - TE 1977066-1
  - Keystone 5015
  - Keystone 5010-5014 (envelope only)
  - TI TSSOP-30 DBT for U24
  - TI SSOP-28 DB for U2: it was 0.2 above the max height; now nominal
  - Detailed HRO TYPE-C-31-M-12 for J1
  - BM83 offset correction: y -0.427
- **Built for the enclosure:** 11 parametric models:
  - Tang Band W3-2052SC
  - Samsung 50S cell
  - Molicel P45B cell
  - CW GRB112 rocker
  - ISO 4762 screws, M3x10 and M3x16
  - Ruthex insert
  - Würth spacer
  - Würth stud
  - Rubber foot
  - Knob stand-in

## Critical findings (board, not CAD): footprint errors exposed by the accurate models

1. **J2/J3 PJ-307: the front locating pegs miss their holes by 1.0 mm.**
   - In the HOOYA drawing (`datasheets/PJ-307.pdf`, PCB layout), the pegs are 1.0 and 3.5 from the body front. Pin 1 is at 3.1 and pins 2-5 at 8.4.
   - The footprint has the front NPTH pair at 0.0 from the body front: local x -5.75, which should be -4.75.
   - The model, which matches the drawing, agrees with the drawing.
   - The jack cannot seat as drawn. Fix: move both front NPTH (±5.0) from x -5.75 to x -4.75 in `PJ-307.kicad_mod` and on the board.
2. **U1 BM83: GND pad 56 is misplaced by 3.37 mm.**
   - Datasheet DS70005402D p.56 Fig. 8-2 places pad 56 (1.78 sq) at 12.27 from the module's left edge and 10.47 from the bottom edge, which is footprint-local (+4.77, +0.03) in 3D.
   - The footprint has it at x +1.40. Pad 57 (x 4.21) is correct.
   - Separately, the module 3D model sat 0.43 mm off the footprint pad pattern. That is fixed by the offset in `apply-map.json`.
3. **SW100 TE 1977066-1: the footprint (marked "DRAFT") does not match the TE drawing** (C1 p.1).
   - Outer terminal pads are at ±1.50 / 0.9 wide; the terminals are at ±1.175 / 0.65 and the TE lands are 0.75 wide at ±1.225.
   - The peg holes are 1.5 from the pad row on the side away from the board edge. TE puts them 0.9 from the pad row, on the actuator side.
   - The two bracket solder pads (1.2 x 1.3 at x ±1.2..2.5) are missing.
   - As built, the switch would sit with its actuator pointing into the board, or its pegs would miss.
   - The v13 model follows the drawing with the actuator toward the board edge, as the courtyard intends.
4. **C275 (EEHZA1E101XP, case D8 6.3 x 7.7) sits on a CP_Elec_8x10 land.** The model is correct. The terminals overlap the pads by only 2.4 of 3.0 mm. Consider the CP_Elec_6.3x7.7 land.

## Enclosure findings (`ai-files/cad/models-v13/mechanical-accuracy.md`)

- **Tang Band W3-2052SC: the CAD is wrong.**
  - The frame is square (82.55, R ~4), not round.
  - The 4 holes are on a 96.52 bolt circle (68.25 sq; seller JSON). The CAD assumed 77.
  - The frame block is ~13.3 thick, not 4.
  - A 3.3 mm foam gasket is already fitted.
  - The leads are a JST-PH-style pigtail.
  - The ring pad and recess have to be redesigned: square seat, screws at r 48.3, about M3x20 into inserts.
  - This supersedes the v11.2 clamp-ring fallback analysis that was based on the 77 bolt circle.
- **Cells:** the CAD length of 70.2 is 0.42 shorter than the Samsung 50S max (70.62). Raise it to 70.7.
- **Rocker, inserts, spacers, studs, screws:** within 0.4 of the drawing or standard values.
- **ND65 maker STEP:** within spec, but the hole pattern is 0.35 off the cone axis in the scan.

## What is still assumed

- **XAL7070 L200:** the Coilcraft drawing is blocked, so the KiCad library model is unverified.
- **MWSA1265S:** checked only against a third-party copy of the Sunlord sheet.
- **Keystone 5010-5014:** no maker drawing.
- **Micro-Fit J5:** the drawing is an LXW equivalent, not genuine Molex.
- **Woofer:** hole Ø, frame thickness, magnet, basket and opening come from photos (±1.5).
- **Not selected or sourced:** knob, rubber feet, PCM board and gaskets.
- **Cell caps:** cap/button geometry is assumed.
- **Passives:** the model is the nominal body; real parts vary by ±0.1-0.2.
- **J1 contacts:** contact count and position are cosmetic.

## Owner actions

1. Fix the three footprints above (J2/J3, U1 pad 56, SW100) before fabrication. The coordinator owns `DesktopSpeaker-kicad/`.
2. Fill in the caliper checklist in `mechanical-accuracy.md` (the woofer first), or supply a Tang Band drawing.
3. Select the knob, rubber feet, PCM board and gasket materials so they can be modelled.

## Files

All paths are under `ai-files/cad/models-v13/`:
- **Models:** `3d/*.step` (19 models: 8 board, 11 enclosure).
- **Generators:** `gen/build_parts_a.py`, `gen/build_mech.py`, `gen/m13lib.py`.
- **Checks:** `gen/measure.py`, `gen/inventory.py`, `gen/table.py`, `gen/showcase.py`.
- **Notes and tables:** `MODELS.md`, `accuracy-table.csv`, `accuracy-table.md`, `mechanical-accuracy.md`.
- **Apply script:** `apply.py` with `apply-map.json`.
- **Renders:** `renders/before_g*.png`, `renders/after_g*.png`, `renders/after_front_*.png`, `renders/after_rear_*.png`, `renders/mech_*.png`.
- **Sourcing:** `downloads/` holds the sourcing log, the drawings and the EasyEDA OBJ files used for comparison.

**Applying (coordinator, after the v12 agent finishes):**
```
cd ai-files/cad/models-v13
python3 apply.py --dry-run --footprints ../../../DesktopSpeaker-kicad/kicad-library/footprint \
   --board BOARD.kicad_pcb --models-dir ../../../DesktopSpeaker-kicad/kicad-library/3d --allow-project
```
- **What it does:** it copies the 8 new STEP files flat into the 3d folder. It replaces the model block of 9 footprints, and of the 36 board footprints that use them: J1, J5, J9-J11, SW100, TP1-TP27, U1, U2, U24.
- **Tested:** it was run on a scratch copy of RT-3 and the library. The second run reports no change, so it is idempotent. It refuses to touch `DesktopSpeaker-kicad/` without `--allow-project`.
- **After applying:** re-export the board STEP for the enclosure build.

**Regenerating the checks:**
- `python3 gen/inventory.py BOARD work/inventory.json`
- `M13_INV=... M13_LIB3D=... M13_OUT=... freecadcmd gen/measure.py`
- `python3 gen/table.py`
