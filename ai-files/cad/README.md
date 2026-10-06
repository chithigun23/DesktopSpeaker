# DesktopSpeaker internal CAD (2026-10-06)

Parametric FreeCAD model of the enclosure, drivers, 2P 21700 pack, estimated PCB with real KiCad STEP parts, and hardware.
Only the PCB size is an estimate (`pcb-size-estimate.md`). Nothing in the KiCad project folders was touched; no PCB layout was made.

## Rebuild (from the project root)
```
PATH=/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/bin:$PATH
kicad-cli sch export netlist --format kicadxml -o ai-files/cad/work/net.xml DesktopSpeaker-kicad/DesktopSpeaker.kicad_sch
python3 ai-files/cad/pcb_estimate.py            # courtyard sum -> work/pcb_estimate.json
freecadcmd ai-files/cad/build_speaker_cad.py    # model -> DesktopSpeaker_internal.FCStd/.step, work/brep, work/meta.json (about 10 s)
freecadcmd ai-files/cad/check_cad.py            # interference.md, volumes.md
freecadcmd ai-files/cad/render_cad.py           # renders/*.png (about 2 min; FreeCAD tessellation + matplotlib)
```
All parameters are in the dict `P` at the top of the build script. Axes: X = long side, Y = depth (0 = front outer face), Z = up (0 = outer bottom of the box; feet go to -15). Layout and sites are in the script (LAYOUT, `sites`).

## Result
- Outer **163 x 100 x 164 mm** (W x H x D incl. 3 mm lid; 2.67 L; depth follows the 116 x 96 mm PCB: D = PCB rear edge + 3.5, set by `layout.json`), +15 mm feet gap, overall height 115. Wall 3 mm. Larger than the 163 x 156 x 82 starting box: the ND65 is 48 mm deep, the woofer is 44.5 mm deep and 82.6 mm in diameter, the 2P 21700 pack is 73 x 43 x 22 mm.
- Front long side 163: two ND65-4 at x = +-41 on raised 11 mm pads. Battery sits under the drivers (z 4 - 26). A sealed woofer chamber occupies the rear lower half (x +-58, y 62-157, z 3-54); its roof carries the PCB on 5 mm standoffs; the rear lid is the chamber's rear wall. The woofer fires down through a 70 mm hole with a ring pad and a 90 mm grille; side pockets of the main chamber carry the harness and the rocker.
- **Volumes** (`volumes.md`): woofer chamber gross 0.562 L, **net 0.506 L** (target 0.45-0.60; Vas 0.59). Main chamber (both ND65, battery, PCB) gross 1.627 L, **net 1.436 L** (target >= 0.8; larger than needed: height is set by the 64 mm driver + 27 mm battery layer, depth by the 90 mm woofer ring; the main chamber could be trimmed, but the woofer chamber footprint then stays). Total cavity 2.273 L.
- **Interference** (`interference.md`): 107 solids, all pairs, threshold 0.5 mm3: **0 unintended overlaps**; 6 intended pairs = connector body/pins sitting in the PCB model (through-hole pins, mid-mount USB-C).
- Renders in `renders/`: assembled (front/right, rear/left, underside), open top view, sections x = -41, x = 0, z = 15, z = 75, exploded (two views). Section faces are red.

## Screws M3x10 - where 10 mm works (all checked in the model, tip positions)
| Site | Stack | Thread into insert/boss | Verdict |
|---|---|---|---|
| ND65 mounting (x8, holes 4.3 in the STEP) | head, flange **0.75 mm** (STEP), then pad | 9.25 mm; pad 11 mm thick with 10 mm pilot, 1 mm skin to the front face, insert 5.7 | works only because the baffle is locally thickened to 11 mm (3 + 8 raised pads). **10 mm is too long for a normal 3 mm baffle**: use M3x6 and 3 mm walls to remove the pads (gain 0.1 L) |
| Woofer (x4) | head, flange 4 mm (assumed), ring pad 4.5 + floor 3 | 6 mm; pilot 6.5, 1 mm skin outside, insert 5.7 | works for flange >= 3.5 mm; if the real flange is thinner the tip bottoms in the pilot: check the drawing |
| PCB (x4) | head, PCB 1.6, 5 mm standoff | 3.4 mm in the insert (insert top z 61.5, pilot floor 1 mm above the chamber air) | works with a 5 mm standoff; **6 mm standoff gives only 2.4 mm (too short)**; 4 mm is better |
| Lid (x7) | head, lid 3 | 7 mm; insert 5.7, pilot 8 | works; tip is 1.3 mm past the insert inside the boss; M3x8 would be ideal |
| Feet (x4, stud from outside) | M3 male stud 6 mm (Wurth 1768061, length assumed) | 6 mm in insert 5.7, pilot 6.5, 1 mm skin to the cabinet air | marginal 1 mm skin (print the floor boss 8 mm if possible) |
| Front grille | not screwed | - | **M3x10 is unsuitable** (0.8 mm plate, 3 mm baffle): grille is bonded/clipped; use 4 x M3x5 or adhesive |
Pilot holes are modelled at 4.6 mm (= insert OD) so inserts show no overlap; real pilot 4.0-4.2 (heat-set).

## Findings on the real parts
- ND65-4 STEP orientation: front = -Z, flange plane z = -22.75 (flange only 0.75 mm thick), cone/surround outer diameter 58.4 mm stands 3.25 mm proud of the flange, magnet rear z = +22. The maker's 48 mm total = 3.25 + 44.75 behind the flange. A rear-mounted driver therefore needs a **59.5 mm aperture** (not the 52 mm datasheet cutout, which is for a different mounting) - modelled so.
- USB-C: opening is the +Y end of the STEP; jack bore at the -X end (PJ-307). BM83 STEP floats 5.4 mm above its origin (shifted to the board; module height 2.5).
- KiCad STEP positions: footprint model offset/rotation were applied; models were then re-centred in the layout. Connector rear-edge overhang (USB-C 2 mm past the board edge, jacks flush) is an assumption.

## Assumptions and unresolved
- PCB size, enclosure depth and the positions of the modelled parts now come from the KiCad placement (`ai-files/pcb/layout.json`, 116 x 96 mm, placement v2); rerun `helpers/build_pcb.sh` before this build when the board changes.
- **Tang Band W3-2052SC**: no maker drawing or STEP. Flange 82.6 x 4 mm, aperture 70, hole pattern 4 x 3.5 on a 77 mm circle, magnet 40 dia, cone/basket frustum are all assumptions. Request the drawing before cutting.
- ND65 depth 48 mm (44.75 behind the flange) drives the 160 mm depth; the maker STEP is dated 2025-11-20.
- **Pack**: 2P 21700 (2 x Samsung 50S 5 Ah) with a protection board is chosen; PCM/protection board (4-5 A+ continuous, ideally 10+ A for headroom), 10k NTC, holder/cradle, and the Samsung datasheet (50S rated about 9.8 A continuous per cell, from memory, verify) are not sourced. Cells are cylinders; wrap and PCM allowance = 3 mm PCM + 1 mm gaps. J5 stays (Micro-Fit 3 pin; harness drawn schematically from J5 to the PCM end).
- Not modelled: wires (speaker leads, battery harness), cell holder, gaskets, foam, acoustic stuffing, wire grommets through the chamber roof (needed for the woofer cable and the pack harness must not pass through the sealed chamber), fillets, print draft. Cabinet sealing relies on the printed seams and a lid gasket.
- Stand-ins without STEP: J5 Micro-Fit, J9-J11 JST B2P-VH, SW100, SW101 (D20 round assumed from the footprint name), PCM board, rubber discs, standoffs, inserts, screws (all parametric).
- Rear cutouts: USB-C 10.2 x 5, jacks dia 8.4, SW100 dia 5, rocker dia 20.2, all aligned to the placed connectors; plug clearances are not verified against real plug bodies.

## Files
`build_speaker_cad.py`, `check_cad.py`, `render_cad.py`, `pcb_estimate.py`, `DesktopSpeaker_internal.FCStd`, `DesktopSpeaker_internal.step` (named solids), `renders/`, `interference.md`, `volumes.md`, `mechanical-bom.md`, `pcb-size-estimate.md`, `mechanical-parts.md` (sourcing), `parts/` (ND65 files), `work/` (netlist, brep dumps, probes; regenerable).
