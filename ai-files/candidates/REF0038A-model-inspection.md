# TPS25730DREFR REF0038A STEP inspection

**Source:** TI WEBENCH CAD endpoint [`REF0038A.stp`](https://webench.ti.com/cad/dlbxl.cgi/newstep/REF0038A.stp), retrieved 2026-10-05. Original downloaded model is `ai-files/candidates/REF0038A.stp` (STEP assembly contains products `REF0038A_ASM`, `BODY-QFN`, `FRAME-REF0038A`, and `PIN1-ID`).

## Mechanical measurements

FreeCAD 1.0.0 STEP import produced a valid shape (38 solids, 484 faces). Overall bounds are **6.00 × 4.00 × 0.80 mm**, X/Y from −3.00…+3.00 and −2.00…+2.00 mm, Z from 0.00…+0.80 mm. Z=0 is the seating plane; the model body rises to 0.80 mm. This agrees with the official KiCad REF0038A footprint/body outline dimensions and lead arrangement. Pin-1 orientation is checked against the perimeter-lead pattern: STEP lead geometry at approximately x=−3.0…−2.65 mm, y=−1.1…−0.9 mm aligns footprint pad 1 at (−2.925,−1.0) mm under the KiCad model Y-axis convention. The 39 large exposed surface is on the left and its corner chamfer is at the pin-1 side; the smaller pad 40 surface is on the right. The fit/orientation also matches the official footprint model declaration (zero offset, scale 1, rotation 0).

The footprint exposes separate `39` GND and `40` DRAIN copper islands:

- Pad 39 is centered at (−0.965, 0) mm, 2.72 × 2.65 mm.
- Pad 40 is centered at (+1.560, 0) mm, 1.53 × 2.65 mm.
- Their land gap is 0.40 mm.

The underside view clearly depicts two separate exposed surfaces and the correct large-pad chamfer. The central `FRAME-REF0038A` is encoded as one closed STEP solid spanning X −2.5…+2.5, Y −1.5…+1.5, Z 0…0.2 mm; point-in-solid sampling crosses the gap between exposed surfaces at z=0.1 mm. This is an internal lead-frame simplification in the vendor mechanical CAD, not evidence that the physical GND and DRAIN pads are electrically connected. TI assigns pad 39 to GND and pad 40 to DRAIN, and the KiCad footprint retains separate copper pad areas/numbers. Use the exact STEP for mechanical visualization only; do not interpret its internal solid topology as electrical connectivity. KiCad 10 PCB top/bottom 3D renders using the copied footprint at zero model offset/rotation verify the lead/pad placement under KiCad's Y convention and show two separate underside pad surfaces.

## Inspection outputs

- `REF0038A_inspection.json` — dimensions, volume and solid bounds.
- `REF0038A_topology.json` and `REF0038A_center_section.json` — shell and cross-section counts.
- `REF0038A_center_samples.json` — bridge sampling results.
- `REF0038A_iso.png`, `REF0038A_top.png`, `REF0038A_bottom.png` — FreeCAD review views.

The exact TI STEP is linked with zero offset, unit scale, zero rotation for mechanical visualization. Its merged internal frame is documented above and must not be interpreted electrically.
