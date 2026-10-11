# CAD v11: rebuilt from the routed board, print-ready enclosure (2026-10-12)

Scope: `ai-files/cad/` (model, checks, renders, STL), `ai-files/helpers/board_to_layout.py`, `ai-files/pcb/layout.json` (+ `layout-v9b.json` backup). Nothing under `DesktopSpeaker-kicad/` was changed. Board: committed R6o `DesktopSpeaker.kicad_pcb` (e526e7d), copied to the scratchpad for the STEP export. Elapsed time: about 32 min (01:28-02:00).

## 1. Rebuilt from the board

| Item | Source now | Before |
|---|---|---|
| `pcb/layout.json` | `helpers/board_to_layout.py` (pcbnew) on the routed board: Edge.Cuts outline, H1-H9/HA1/HA2 footprints, F/B courtyard bbox per part, BM83 antenna rule area | v9b generator output (stale: 136.9 x 127.8, 10 holes) |
| PCB body + components | `cad/parts/DesktopSpeaker-board.step` (kicad-cli 10.0.6 `pcb export step --subst-models --user-origin 147.25x88.8mm`, 21.8 MB, 686 solids); solids assigned to references by courtyard; the STEP origin is the layout frame (x = u, y = v, z = 0 board bottom) | per-footprint library STEP models placed at layout coordinates |
| Stand-ins kept | J5 Micro-Fit, J9-J11 JST VH, SW100 (+ plunger), SW101 rocker, PCM board (no models) | same + any part without a model |

Frame: u = x_board - 147.25, v = 88.8 - y_board; CAD X = u - 3.5, CAD Y = 133.3 + v, board front edge at CAD Y 64.5, rear edge 202.1, lid inner face 202.6.

### Differences vs the v10d sandbox (`pcb/work-v10d/layout-v10d.json`, `work-v10d/cad`)
- Board outline (127.5 x 137.6, R3), all 11 hole positions and the antenna keep-out: identical (< 0.001 mm).
- Part origins: identical for all 103 v10d parts except **C106** (moved 1.24 mm in routing). Courtyard rects differ by up to 2.0 mm (U2 1.97, U8/U9 1.58, U1 1.18, J1 1.07, C275 1.05 mm): v10d stored generator rects, v11 stores the real courtyards. 246 more footprints are listed (all parts; v10d listed only tall/anchor/non-passive parts). New keys `side`, `fpid`, `source`; `owner` copied from v10d (generator-only data).
- CAD, DETAIL=0 (v10 enclosure logic, real board): woofer net 0.525 L, main net 2.057 L (v10d 0.525 / 2.055), 0 unintended overlaps, 2 intended (J2/J3 pins in the board; v10d had 7 because the stand-in board had no holes for THT pins).
- Findings from the real board, all handled in the CAD:
  - **BM83 (U1) STEP floats 5.41 mm** above the board and **XFL4015 (L2, L3) STEP sits 1.40 mm inside the board** (rotate 90 about X with the wrong pivot). Corrected in the CAD only; the library model offsets should be fixed by the coordinator (`BM83SM1-00TA.kicad_mod` offset z -5.41, `Coilcraft_XFL4015-471MEC.kicad_mod` offset z +1.40 or fix the pivot).
  - BM83 overhangs the board left edge by 8.0 mm (courtyard to u -69): CAD X -72.9, 5.6 mm from the inner wall. OK.
  - USB-C receptacle protrudes 1.22 mm past the board edge (0.72 mm into the lid); the v10 10.2 x 5 lid cut left only 0.55 mm radial margin.
  - 3.5 mm jack noses (dia 6.0) end 0.84 mm in front of the lid inner face.
  - H1, H3 (Y 93.8) and HA1, HA2 (Y 82.5) lie in front of the woofer chamber: v10 used 58 mm printed posts from the floor, which cannot be printed baffle-down (replaced, see 2).
  - **SW100 is only 8.9 mm from J1** (centres): a 12 mm USB-C plug clearance and a 5 mm plunger bore leave a 0.41 mm web.
  - **SW102 encoder shaft top is 3.9 mm below the top wall** (z 93.1 vs 97.0): the knob cannot be reached (unchanged from v10, now confirmed on the real model).

## 2. Print-ready detailing (DETAIL=1, default)

| Body | STL (binary, print orientation) | Size X x Y x Z on the bed (mm) | Volume | Orientation | Supports |
|---|---|---|---|---|---|
| Main shell (baffle, walls, driver pads with gasket recesses, woofer ring pad + flange recess + aperture, 9 lid bosses with webs and 45 deg lead-ins, 4 feet bosses, battery cradle, strap anchors, insert floor grooves) | `print/DesktopSpeaker_shell.stl` | 163.0 x 100.0 x 202.6 | 384 cm3 | front baffle on the bed (enclosure +Y up) | none; needs about 205 mm Z. Minor horizontal overhangs: woofer ring pad 5.5 mm and feet bosses 4.5 mm (unsupported, acceptable), woofer aperture 70 mm arch |
| Woofer chamber insert (partition, side walls, roof, forward PCB shelf with three 45 deg gussets, 11 PCB bosses under the roof/shelf, 2 lid bosses, grommet boss) | `print/DesktopSpeaker_woofer_chamber_insert.stl` | 122.0 x 126.6 x 55.0 | 101 cm3 | roof on the bed (upside down) | none |
| Rear lid 4 mm (cutouts, chamfers, gasket groove, counterbores, 11 screw holes) | `print/DesktopSpeaker_lid.stl` | 163.0 x 100.0 x 4.0 | 60 cm3 | outer face on the bed | none (jack counterbore floors bridge 1.25 mm) |

FDM 0.4 nozzle, PETG or ASA, walls 3 mm, bosses 8 mm OD, heat-set pilots 4.0 mm x (5.7 + 1) for M3 x 5.7 inserts (now modelled; insert/pilot overlap is reported as intended).

Design choices:
- **Three bodies.** Printed baffle-down, a one-piece shell would have an unsupported 116 x 54 mm partition, a roof and chamber walls starting in mid-air, and 58 mm cantilever posts. The chamber is a separate insert printed roof-down; it drops 1 mm into floor grooves (0.2 mm clearance per side) and is bonded and sealed there (epoxy or PU). Its roof extends forward as a 3 mm PCB shelf to Y 76, so the four front holes need no posts.
- **Lid seal: foam groove, not tongue-and-groove.** A 2 x 1.5 groove in the lid (lid now 4 mm, 2.5 mm left under the groove): an outer loop on the 3 mm wall land plus an inverted U on the insert rim that joins the floor run. A tongue-and-groove lip needs a groove in the 3 mm wall (not possible) or a tongue inside the opening, which would collide with the board rear edge (0.5 mm), the USB-C receptacle (0.72 mm into the lid) and the bonded insert rim. Foam also tolerates the insert position. 11 lid screws (4 corners, top centre, 2 floor screws inside the chamber, 2 side-pocket screws, 2 into the insert roof bosses) with nylon sealing washers, because the screw holes lie inside the gasket loops.
- **PCB stack (11 real holes).** Flat insert roof/shelf top z 57.0, then a 10 mm hex spacer, PCB 1.6 mm, M3x16 with 4.4 mm thread in the 5.7 mm insert. The pilots are 6.7 mm deep in bosses under the roof, 1.0 mm skin to the chamber air. Bosses at H5/H9 merge into the chamber side walls (clipped at the wall outer face). The PCB sits 0.5 mm higher than in v10 (bottom z 67.0).
- **Drivers:** 0.5 mm gasket recess on each pad rear face: 63 mm square (inside the 64 mm flange), minus the 59.5 aperture and 7 mm around each screw. **Woofer:** the ring pad is now 5.5 mm with an 83.4 x 1.0 flange locating recess, so the flange seat stays at z 7.5. Woofer screws keep 6.0 mm engagement and a 1 mm skin.
- **Woofer leads:** J11 (WOOFER) goes down in front of the board edge (Y 60) to a 6.0 mm grommet hole in a 14 mm boss on the partition front face at X 40, Z 40. A 10 mm counterbore leaves a 1.6 mm web for a snap grommet.
- **Pack:** the cradle is printed in the shell floor. Two ribs at X -31 and +22: front lip, falling arc, then a 45 deg rising flank, so they print along +Y without support. End stops sit 1 mm from the cells and the PCM. Front and rear strap anchors have 22 x 2.5 tunnels for a 20 mm hook-and-loop strap. Harness: J5, then the right side pocket (X 70), then along the floor at z 17.85 to the PCM end. It does not cross the sealed chamber: 10 mm from the chamber air, 7 mm from the insert.
- **Fillets and chamfers.** 2 mm fillets on the shell front vertical edges and on the lid outer vertical edges, 1 mm on the 8 cavity edges, 0.5 x 45 deg chamfers on every lid cutout rim (including the screw holes). The rear vertical edges of the shell stay sharp where the lid meets them. `makeChamfer` on the lid failed (StdFail_NotDone, all edges and single edges), so the chamfers are built as cone/loft cut tools instead. Not attempted: fillets on bosses, pads, ribs, gussets and insert edges.
- **Rear-lid cutouts** come from the STEP connector geometry: USB-C 12 x 7 R2 around the receptacle section, jacks 8.5 mm with 11 x 2.5 outside counterbores (the plug body reaches 0.84 + 1.5 mm from the jack face), SW100 5.0 mm, rocker 20.2 mm with a 25 mm inside counterbore for a 2.0 mm panel. **J1/SW100 web 0.41 mm (unprintable): the two openings are joined into one keyhole.** The joining edges are not chamfered. Moving SW100 at least 3 mm away from J1 on the board would restore a 3.4 mm web (coordinator decision). Drawing: `renders/rear_lid_drawing.png`.

## 3. Results after detailing

### Interference (`cad/interference.md`)
164 solids, pairwise, threshold 0.5 mm3: **0 unintended overlaps**. 40 intended: 38 heat-set inserts in 4.0 mm pilots, plus J2/J3 THT pins in the board.

### Volumes (`cad/volumes.md`)
| Chamber | Gross L | Displaced L | Net L | Target | v11 DETAIL=0 | v10d |
|---|---|---|---|---|---|---|
| Woofer (sealed) | 0.581 | 0.060 | **0.521** | 0.45-0.60 | 0.525 | 0.525 |
| Main | 2.279 | 0.235 | **2.044** | >= 0.80 | 2.057 | 2.055 |
Outer 163 x 100 x 206.6 mm (lid +1 mm). Detailing costs 0.004 L in the woofer chamber (bosses under the roof, lid bosses, recess) and 0.013 L in the main chamber (cradle, shelf, gussets, bosses). The gaskets do not change the gross volumes. Wall inner fillets (r1) are not subtracted (< 0.001 L).

### Clearances
| Check | Result | Required |
|---|---|---|
| Cells / PCM to the ND65 magnets and baskets | min 5.49 mm (PCM to right driver), cells 6.98 mm | >= 3 |
| Cells / PCM to the PCB underside | >= 44 mm | >= 3 |
| Pack harness to the sealed chamber air / insert | 10.0 / 7.0 mm | no contact |
| USB-C J1 | 12 x 7 cut, body section 9.10 x 3.36, radial 1.45, wall clearance in the lid 1.53 | >= 1 |
| Jacks J2/J3 | 8.5 bore, nose 6.0, radial 1.25 (nose does not enter the lid) | >= 1 |
| SW100 plunger (stand-in) | 5.0 bore, radial 1.25 | >= 1 |
| SW101 rocker | 20.2 panel hole for a 19.6 body (panel fit by design) | n/a |
| Tall parts to the top wall | SW102 3.9 mm, JST VH stand-ins 17.5, J4/J6/J8 headers 19.9, C275 20.7, inductors >= 21.4 | - |
| Screw engagement | drivers 9.25, woofer 6.0, lid 6.0, PCB 4.4 (insert 5.7) | >= 3.5 |

## 4. Open assumptions
- **Woofer** (Tang Band W3-2052SC): no maker drawing or STEP. Flange 82.6 x 4, aperture 70, 4 x 3.5 holes on a 77 mm circle, magnet 40 and the frustum are all assumed. The flange recess (83.4 x 1.0) and the screw circle must be checked against the drawing.
- **Rocker** SW101 (Shou Han KCD1-201-R, D20): body, depth (22) and snap-in panel thickness (2.0 assumed, set by the 25 mm inside counterbore) are unverified. The lid position (X 66, Z 80) is a free choice; the board footprint carries wire pads only.
- **Pack**: 2P Samsung 50S with PCM (3 x 43.4 x 18 box, at the +X end), 10k NTC, strap length and the PCM current rating are not sourced. The cradle assumes bare cells with a 0.3 mm gap; wrapped cells or a holder need a larger gap (`cradle_gap`).
- **Grommet**: a 6 mm hole and 1.6 mm panel snap grommet with ID >= 3.4 is not selected; leads assumed 2 x 0.5 mm2 (3.0 mm bundle).
- **SW100** (TE 1977066-1): no STEP; plunger 2.5 mm dia at PCB top + 1.75, 2.5 mm proud of the board edge (assumed). The tip ends 2.0 mm below the lid outer face, so it is a pin-press (paperclip) button.
- J5, J9-J11 bodies are courtyard boxes. Plug bodies are assumed to be USB-C overmold <= 12 x 7 and 3.5 mm plug <= 11 mm dia in the counterbore. The foam cord (3 mm closed cell) and the sealing washers are not sourced.
- Library STEP offsets for BM83 and XFL4015 were wrong; fixed in the library and the board on 2026-10-12 (commit 6052ec2, offsets z -5.41 and z 1.5, verified by STEP re-export). The CAD-side correction is now redundant and should be removed on the next rebuild.

## 5. Not finished / known gaps
- SW102 encoder: solved by the knob dish (v11.1).
- **J1/SW100 spacing**: the keyhole is a workaround. A board revision with SW100 >= 3 mm further from J1 is preferred.
- Fillets on internal bosses, pads, ribs and the insert were not attempted. There is no draft. Print renders show the bodies alone, without a bed: the painter's-algorithm renderer drew the bed over the parts.
- Insert-to-shell joint: a bonded seam is assumed (no screws). Cable retention clips in the side pocket are not modelled.
- The mesh deflection is 0.03 mm linear and 0.2 rad. Re-slice check (wall thickness, first-layer area) was not done in a slicer.

## Files changed
- `ai-files/helpers/board_to_layout.py` (new), `ai-files/pcb/layout.json` (regenerated), `ai-files/pcb/layout-v9b.json` (copy of the stale file)
- `ai-files/cad/build_speaker_cad.py`, `check_cad.py`, `render_cad.py`, `README.md` (v11 section), `volumes.md`, `interference.md`, `mechanical-bom.md`
- `ai-files/cad/parts/DesktopSpeaker-board.step` (new, 21.8 MB), `DesktopSpeaker_internal.FCStd` (4.6 MB) / `.step` (36 MB, was about 20 MB), `work/` (regenerated: `work/brep` is cleared each build, so 47 tracked v10 brep files are deleted and 69 new ones added)
- `ai-files/cad/print/DesktopSpeaker_{shell,lid,woofer_chamber_insert}.stl` (new)
- `ai-files/cad/renders/*.png` (same names overwritten) + `print_shell.png`, `print_insert.png`, `print_lid.png`, `rear_lid_drawing.png`

## v11.1: knob dish (2026-10-12)
- **Library fix taken over.** Board STEP and `layout.json` were re-exported from the committed board (b635b6e; BM83/XFL4015 3D offsets fixed in 6052ec2). The CAD-side Z correction is removed. The build now only reports floating or sunk models, and found none (U1 and L2/L3 start at z 1.6).
- **Dish position, derived (not hard-coded).** The axis comes from the SW102 solids in the board STEP: the top 1 mm of the shaft, with the axis placed 3.0 mm from the round side of the D-shaft.
  - Result: CAD X -34.68, Y 121.16, shaft top z 93.09.
  - The coordinator's estimate (X -41.4, Y 123.7) is the footprint origin (pin A). It is 6.7 mm off the shaft axis.
- **Geometry** (parameters `dish_*`):
  - Dish 36 mm, well wall 3 mm, floor 3 mm (z 82.09-85.09) with an 8.5 mm hole (7.5 + 1). Exposed shaft 8.0 mm. 2 mm 45 deg lead-in on the top rim.
  - The well is horizontal when the shell prints baffle-down. It is therefore a teardrop: its outer wall has a 45 deg point toward the baffle, and the pocket a 45 deg point toward the rear truncated to a 9 mm bridge. This keeps the shell support-free. Cosmetic cost: the dish has a pointed rear end seen from above (`dish_teardrop=False` gives a round dish that needs support).
  - The well does not merge with the 1 mm cavity fillets or the 2 mm outer fillets: it is 44 mm from the side walls and 70 mm from the baffle.
- **Knob stand-in.** D30 x 14 with a 6.0 mm bore (round; the D flat is not modelled). It sits 0.75 mm above the floor, at z 85.84-99.84 (0.16 mm below the top surface), with 3 mm radial gap to the dish wall. The shaft goes 7.25 mm into the knob. Knob/shaft is listed as an intended overlap (fit).
- **Checks.** 165 solids: 0 unintended overlaps, 41 intended (38 inserts, J2/J3 pins, knob on shaft).
  - Envelope clearances: L201 7.0 mm, L203 7.6, L202 7.7, H8/H4 screw heads 10.5. The left ND65, the battery, the lid bosses and the board's other tall parts are all > 15 mm away.
  - The encoder body top (about z 75.1) is 7 mm below the floor. The shaft passes the 8.5 hole with 1.25 mm radial clearance.
- **Volumes.** Woofer 0.521 L (unchanged). Main gross 2.255 L, net **2.021 L** (was 2.044). The loss is 0.0235 L: well material plus dish air.
- **Assembly note.** The well floor covers PCB screw H8 (10.5 mm above its head). Drive H8, and the other PCB screws, with a ball-end hex key through the rear opening before the lid goes on.
- **Files.** `cad/build_speaker_cad.py`, `check_cad.py`, `README.md`, `volumes.md`, `interference.md`, `parts/DesktopSpeaker-board.step`, `pcb/layout.json`, `print/*.stl`, `renders/*` (all re-rendered), `work/dish_envelope.brep` (new).

## v11.2: R6q board, woofer cutout 76.2, GRB112 rocker (2026-10-12)
- **Board.** R6q (cfea017) was re-exported to the board STEP and `layout.json`: SW100 moved to u -11.18 and R113 to u -15.68; outline and holes unchanged. **Lid web J1/SW100 is 4.41 mm**: separate openings, both chamfered 0.5 mm; no keyhole.
- **3D offset regression.** cfea017 carries the old offsets: BM83 model offset z 0 (6052ec2 had -5.41) and XFL4015 z 0.1 (6052ec2 had 1.5). As instructed, the CAD now uses the STEP unmodified. U1 floats 5.41 mm and L2/L3 sit 1.40 mm in the board, which shows as 24.3 mm3 board/part overlaps for each. These are listed as intended, but they are a board-file error. **Action for the coordinator:** re-apply the 6052ec2 offsets on the R6q board.
- **Woofer ring land** (aperture r 38.1, flange recess wall r 41.7, flange edge r 41.275, assumed bolt circle r 38.5, holes 3.5, pilots 4.0):
  - Total land between aperture and recess wall: 3.6 mm.
  - Hole inner edge to aperture: -1.35 mm (**the holes break into the aperture**). Pilot to aperture: -1.6 mm.
  - Hole outer edge to recess wall: 1.45 mm; to flange edge: 1.02 mm.
  - With a 76.2 cutout and an 82.55 flange, no circle can hold a 3.5 hole with land on both sides: the land is 3.2 mm at the flange edge. Either the real flange has ears/scallops, or the holes sit on about 79.5 mm and breach the flange edge.
  - **Proposed fix, not applied:** (1) get the maker drawing (hole size and circle). (2) If the holes are on about 79.5 mm, use M2.5 screws with M2.5 x 4 inserts (pilot 3.2): pilot edges r 38.15-41.35, 0.05 from the aperture, which still needs the drawing. (3) Recommended fallback: drop screws through the flange. Clamp the flange with a printed 4 mm ring (ID 74, OD 96) screwed on a 90 mm circle into a ring pad enlarged to OD 100. The insert pilots then sit at r 45, clear of the aperture and the flange.
  - The model keeps the 77 circle so the conflict stays visible.
- **Rocker** GRB112B802BR1:
  - Position and lid cuts: X 63, Z 80. 20.2 hole + 2.2 x 1.0 key notch at the top. 28 mm inside pocket to a 2.0 panel; snap-in range 1.5-2.5. The 25 mm outside flange seat is flat with a 0.5 chamfer on the hole only.
  - Stand-in: flange 25 x 2, body 19.8 x 7, 3 fastons 4.8 x 0.8 x 4 (11 mm behind the panel).
  - The coordinator's 30 mm pocket does not fit: at X 63 it would leave the J3 counterbore web at -0.36 mm. At the old X 66 it would break the groove (x 81 vs groove inner edge 79) and the (74, 92.5) screw boss.
  - The top-right lid screw moved to (76.5, 94.0).
  - Clearances: pocket to groove side band 2.0 mm, to top band 3.5 mm, to LidScrew_4 boss footprint 1.45 mm, to J3 outside counterbore 0.64 mm laterally. The jack counterbores are now 2.0 deep (was 2.5): 2.0 + 2.0 = the 4 mm lid, so no depth band is shared. A plug now reaches 2.84 mm from the lid face to the jack.
  - Rocker body bottom is 1.5 mm above the board top; fastons are clear of the board (check: 0 overlaps).
- **Results.** 165 solids: **0 unintended overlaps**, 43 intended (38 inserts, J2/J3 pins, knob on shaft, L2/L3 in board from the offset regression).
  - Woofer chamber net **0.525 L** (gross 0.581; the larger aperture displaces less ring).
  - Main chamber net **2.025 L** (gross 2.255).
  - Dish unchanged at X -34.68, Y 121.16; clearances as in v11.1.
- **Files.** `cad/build_speaker_cad.py`, `render_cad.py`, `README.md`, `volumes.md`, `interference.md`, `mechanical-bom.md`, `parts/DesktopSpeaker-board.step`, `DesktopSpeaker_internal.FCStd/.step`, `print/*.stl`, `renders/*` (incl. `rear_lid_drawing.png`), `work/`, `pcb/layout.json`, this report.
- **Update (2c1eecc).** The board offsets are restored and the STEP and `layout.json` were re-exported from the current board. `zfix` is empty: U1 and L2/L3 start at z 1.6.
  - **0 unintended overlaps, 41 intended** (38 inserts, J2/J3 pins, knob on shaft). The L2/L3 board overlaps are gone.
  - Woofer chamber net 0.525 L, main chamber net 2.025 L, J1/SW100 web 4.41 mm; rocker pocket gaps unchanged.
  - The woofer bolt circle of 77 mm is still UNVERIFIED. The clamp-ring proposal remains the fallback.
