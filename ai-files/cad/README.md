# DesktopSpeaker internal CAD (v11 2026-10-12; first version 2026-10-06)

**Current entry point and state: see the v11 section at the end.** The sections in between are the v3-v10 history.

Parametric FreeCAD model of the enclosure, drivers, 2P 21700 pack, estimated PCB with real KiCad STEP parts, and hardware.
Only the PCB size is an estimate (`pcb-size-estimate.md`). Nothing in the KiCad project folders was touched; no PCB layout was made.

## Rebuild (v3-v10, historical; v11 commands are in the v11 section)
v3-v10 read the schematic netlist (`work/net.xml`) and placed per-footprint KiCad models from `layout.json`; v11 uses the routed-board STEP instead.
All parameters are in the dict `P` at the top of the build script. Axes: X = long side, Y = depth (0 = front outer face), Z = up (0 = outer bottom of the box; feet go to -15). Layout and sites are in the script (LAYOUT, `sites`).

## Result
- **Placement v5 update: outer 163 x 100 x 220 mm (depth follows the 116 x 152 mm board), woofer chamber net 0.525 L (auto from `CH_NET_L`, gross 0.581 L), main chamber net 2.283 L, 0 unintended overlaps; see volumes.md. The v3 figures below are historical.**
- Outer **163 x 100 x 180 mm** (W x H x D incl. 3 mm lid; 2.93 L; depth follows the 116 x 112 mm PCB of placement v3: D = PCB rear edge + 3.5, set by `layout.json`), +15 mm feet gap, overall height 115. Wall 3 mm. Larger than the 163 x 156 x 82 starting box: the ND65 is 48 mm deep, the woofer is 44.5 mm deep and 82.6 mm in diameter, the 2P 21700 pack is 73 x 43 x 22 mm.
- Front long side 163: two ND65-4 at x = +-41 on raised 11 mm pads. Battery sits under the drivers (z 4 - 26). A sealed woofer chamber occupies the rear lower half (x +-58, y 62-157, z 3-54); its roof carries the PCB on 5 mm standoffs; the rear lid is the chamber's rear wall. The woofer fires down through a 70 mm hole with a ring pad and a 90 mm grille; side pockets of the main chamber carry the harness and the rocker.
- **Volumes** (`volumes.md`): woofer chamber gross 0.680 L, **net 0.625 L** (placement v3; was 0.506 at depth 160) (target 0.45-0.60; Vas 0.59). Main chamber (both ND65, battery, PCB) gross 1.627 L, **net 1.436 L** (target >= 0.8; larger than needed: height is set by the 64 mm driver + 27 mm battery layer, depth by the 90 mm woofer ring; the main chamber could be trimmed, but the woofer chamber footprint then stays). Total cavity 2.273 L.
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
- PCB size, enclosure depth and the positions of the modelled parts now come from the KiCad placement (`ai-files/pcb/layout.json`, 116 x 138 mm, placement v6 (`helpers/run_v6.sh`); v is exported centre-relative); rerun `helpers/build_pcb.sh` before this build when the board changes.
- **Tang Band W3-2052SC**: no maker drawing or STEP. Flange 82.6 x 4 mm, aperture 70, hole pattern 4 x 3.5 on a 77 mm circle, magnet 40 dia, cone/basket frustum are all assumptions. Request the drawing before cutting.
- ND65 depth 48 mm (44.75 behind the flange) drives the 160 mm depth; the maker STEP is dated 2025-11-20.
- **Pack**: 2P 21700 (2 x Samsung 50S 5 Ah) with a protection board is chosen; PCM/protection board (4-5 A+ continuous, ideally 10+ A for headroom), 10k NTC, holder/cradle, and the Samsung datasheet (50S rated about 9.8 A continuous per cell, from memory, verify) are not sourced. Cells are cylinders; wrap and PCM allowance = 3 mm PCM + 1 mm gaps. J5 stays (Micro-Fit 3 pin; harness drawn schematically from J5 to the PCM end).
- Not modelled: wires (speaker leads, battery harness), cell holder, gaskets, foam, acoustic stuffing, wire grommets through the chamber roof (needed for the woofer cable and the pack harness must not pass through the sealed chamber), fillets, print draft. Cabinet sealing relies on the printed seams and a lid gasket.
- Stand-ins without STEP: J5 Micro-Fit, J9-J11 JST B2P-VH, SW100, SW101 (D20 round assumed from the footprint name), PCM board, rubber discs, standoffs, inserts, screws (all parametric).
- Rear cutouts: USB-C 10.2 x 5, jacks dia 8.4, SW100 dia 5, rocker dia 20.2, all aligned to the placed connectors; plug clearances are not verified against real plug bodies.

## Files
`build_speaker_cad.py`, `check_cad.py`, `render_cad.py`, `pcb_estimate.py`, `DesktopSpeaker_internal.FCStd`, `DesktopSpeaker_internal.step` (named solids), `renders/`, `interference.md`, `volumes.md`, `mechanical-bom.md`, `pcb-size-estimate.md`, `mechanical-parts.md` (sourcing), `parts/` (ND65 files), `work/` (netlist, brep dumps, probes; regenerable).

## v8 (2026-10-06)
PCB holes now 10 (`layout.json` holes); holes outside the woofer chamber roof get printed 8 mm posts from the main floor; PCB screws are M3x12. Board 121.1 x 127.4 mm, outer 163 x 100 x 195 mm, woofer chamber net 0.525 L, main 1.917 L; rocker stand-in raised to z 78 (was overlapping the board corner); check_cad: 0 unintended overlaps. See reports/pcb-placement-v8-2026-10-06.md.

## v11 (2026-10-12): built from the routed board, print-ready

### Rebuild (from the project root; one entry point = `build_speaker_cad.py`)
```
K="flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp"
# 1. layout frame from the routed board (outline, 11 holes, courtyard rects, antenna keep-out)
$K --command=python3 org.kicad.KiCad ai-files/helpers/board_to_layout.py BOARD.kicad_pcb ai-files/pcb/layout.json ai-files/pcb/work-v10d/layout-v10d.json
# 2. board STEP in the layout frame (copy the board next to DesktopSpeaker.kicad_pro + fp-lib-table + a kicad-library symlink so ${KIPRJMOD} resolves)
$K --command=kicad-cli org.kicad.KiCad pcb export step --force --subst-models --user-origin 147.25x88.8mm \
   --output ai-files/cad/parts/DesktopSpeaker-board.step COPY/DesktopSpeaker.kicad_pcb
# 3. model, checks, renders
freecadcmd ai-files/cad/build_speaker_cad.py   # DETAIL=1 (default): print-ready; DETAIL=0: v10 enclosure logic on the real board (about 20 s)
freecadcmd ai-files/cad/check_cad.py           # interference.md, volumes.md, clearances, lid cutout check (about 1 min)
freecadcmd ai-files/cad/render_cad.py          # renders/*.png incl. print_*.png and rear_lid_drawing.png (about 2.5 min)
```
Outputs: `DesktopSpeaker_internal.FCStd/.step` (named solids, assembly), `print/DesktopSpeaker_{shell,lid,woofer_chamber_insert}.stl` (binary, in print orientation), `work/meta.json` (sites, cutouts, prints, skipped operations).
Frame: layout u = x_board - 147.25, v = 88.8 - y_board; CAD X = u - 3.5 (`pcb_cx`), CAD Y = 133.3 + v (board front edge fixed at CAD y 64.5), PCB bottom z 67.0 (DETAIL=1; 66.5 for DETAIL=0).

### What comes from the board
- `ai-files/pcb/layout.json` is now generated from the routed board (`helpers/board_to_layout.py`; stale v9b kept as `pcb/layout-v9b.json`). Same schema as `work-v10d/layout-v10d.json`, plus `side`/`fpid` per part and all 349 footprints (v10d listed 103). Outline 127.5 x 137.6, 11 holes and the antenna keep-out are identical to v10d; part origins identical except C106 (moved 1.24 mm by routing); courtyard rects differ by up to 2 mm (v10d rects were generator rects, now real courtyards).
- PCB body and all modelled components come from `parts/DesktopSpeaker-board.step` (686 solids, assigned to references by courtyard). Large parts are separate objects; small passives are grouped per sheet (`PCB_smallparts_<sheet>`). Stand-ins remain for J5, J9-J11, SW100 (+ plunger), SW101 and the PCM board (no models).
- Library model faults found and corrected in the CAD only (library not touched): BM83 (U1) STEP floats 5.41 mm above the board; Coilcraft XFL4015 (L2, L3) STEP sits 1.40 mm inside the board (rotate 90 about X, wrong pivot).

### Print-ready detailing (DETAIL=1)
- **Bodies**: main shell (163 x 100 x 202.6, front baffle on the bed), woofer chamber insert (122 x 126.6 x 55, roof on the bed), rear lid (163 x 100 x 4, outer face on the bed). No supports for any body. FDM 0.4 nozzle, PETG or ASA, 3 mm walls, 8 mm bosses, heat-set pilots 4.0 x (insert + 1 mm) for M3 x 5.7.
- **Why three bodies**: printed baffle-down, the v10 one-piece shell had an unsupported 116 x 54 mm partition, a roof that starts in mid-air and 58 mm cantilever posts under H1/H3/HA1/HA2. The chamber (partition, side walls, roof) is now a separate insert printed roof-down; its roof is extended forward as a 3 mm shelf with three 45 deg gussets that carries the four front PCB holes, so no posts are needed. The insert drops 1 mm into 0.2 mm-clearance grooves in the shell floor and is bonded/sealed there; its rear rim seals on the lid gasket.
- **Lid seal**: foam gasket groove 2 x 1.5 in the lid (outer loop on the wall land + inverted U on the insert rim, joining the floor run), chosen over tongue-and-groove because the 3 mm walls cannot take a groove, a tongue would collide with the board rear edge (0.5 mm) and the USB-C receptacle (0.72 mm into the lid), and foam tolerates the bonded insert position. 11 lid screws (7 corner/edge + 2 side pockets + 2 into the insert roof); use nylon sealing washers.
- **PCB stack**: insert roof/shelf top z 57.0 (flat) -> 10 mm hex spacer -> PCB 1.6 -> M3x16 (4.4 mm in a 5.7 insert); pilots 6.7 deep end 1.0 mm above the chamber air in bosses below the roof.
- **Drivers**: 0.5 mm gasket recess on the pad rear faces (63 mm square inside the 64 mm flange, minus the aperture and 7 mm around each screw). Woofer: ring pad 5.5 with an 83.4 x 1.0 flange recess (flange seat unchanged at z 7.5).
- **Woofer leads**: J11 -> in front of the board edge -> 6 mm grommet hole in a 14 mm boss on the partition front face (10 mm counterbore leaves a 1.6 mm web for a snap grommet) at X 40, Z 40.
- **Battery**: printed cradle in the shell: two ribs (front lip, falling arc, 45 deg rising flank so they print along +Y), two end stops (1 mm from the cells/PCM), front and rear strap anchors with 22 x 2.5 tunnels for a 20 mm strap. Pack harness J5 -> right side pocket (X 70) -> along the floor at z 17.85 -> PCM end; 7 mm from the insert, 10 mm from the chamber air.
- **Fillets/chamfers**: 2 mm on the shell front vertical edges and the lid outer vertical edges, 1 mm on the 8 cavity edges, 0.5 mm x 45 deg on all lid cutout rims (cut tools: `makeChamfer` fails on this lid). Not attempted: fillets on bosses, pads, ribs and the insert.
- **Rear-lid cutouts** from the board STEP: USB-C 12 x 7 R2 (receptacle section 9.1 x 3.36, margin 1.45), jacks 8.5 (nose 6.0, margin 1.25) with 11 x 2.5 outside counterbores so plug bodies reach the jacks (jack face 0.84 mm behind the lid), SW100 5.0 (plunger 2.5 stand-in), rocker 20.2 with a 25 mm inside counterbore (2.0 mm panel). **SW100 is only 8.9 mm from J1**: the web would be 0.41 mm, so both openings are joined into one keyhole. Drawing: `renders/rear_lid_drawing.png`.
- Results (`volumes.md`, `interference.md`): see the tables there and `ai-files/reports/cad-v11-print-ready.md`.

### Open
- SW102 encoder shaft top is 3.9 mm below the top wall (z 93.1 vs 97.0): no knob access through the enclosure. Needs a longer shaft or an extension and a top-wall bore (not modelled).
- Woofer (no drawing), rocker (panel thickness, body), PCM size/position, grommet part, SW100 plunger height (no STEP), J5/J9-J11 bodies, plug body sizes: assumptions as listed in the report.
