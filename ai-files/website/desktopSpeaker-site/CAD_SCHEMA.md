# What the 3D viewer reads from cad/

The viewer (`app.js`, part 2) loads `cad/meta.json`, `cad/cad_status.json` and the glTF files named in
`meta.files`. Every key is optional; when `meta.json` is missing it tries `cad/enclosure.glb` and
`cad/pcb.glb`, and when no model file exists it shows "CAD files not available yet" and the static renders.
The CAD export v12 (2026-11-02) uses the keys marked (v12).

## meta.json

| Key | Used for |
| --- | --- |
| `version`, `date` or `generated`, `title` or `description` (v12) | Side panel, CAD notes |
| `units` (v12 `mm`) | Model frame is millimetres; explode vectors and section planes are in mm |
| `up_axis` (v12 `+Y`) | `Y` (glTF default), `Z` or `X`; a Z-up frame is rotated to three.js Y-up |
| `frame` (v12) | Text shown in the CAD notes; `front` direction defaults to +Z for Y-up, -Y for Z-up; `views.{front,top,...}: [x,y,z]` overrides |
| `files` (v12) | Object `key -> {file, units, up_axis, transform, optional, group}` or a list. Keys containing `pcb`/`board` are the PCB. `units` may carry a note after the unit word ("mm (root node ...)"). `optional: true` files get an on-demand checkbox. `files.renders` (list of paths) adds images to the gallery |
| `files.<key>.transform` or `pcb_transform` | `{position_mm, rotation_deg, order}` or `{matrix: [16]}` in the model frame. Skipped when `applied: true` or its `note` says "already applied" (v12) |
| `groups` (v12) | List of `{key|id, label, description, color, explode_mm, nodes[], visible}` or an object keyed by id. Colours: `#rrggbb` or `[r,g,b]` in 0-1 or 0-255 |
| `pcb_group` (v12) | Group used for the PCB file (`key`, `explode_mm`, `components_without_model`) |
| `nodes` (v12) | List of `{name, group, color, explode_mm, model_source, accuracy}` or an object `name -> group/object`. Named nodes become the hover/explode parts; without `nodes`, the children of the first non-trivial node are the parts, and the PCB file is one part |
| `pcb_nodes` (v12) | `{ref, model_source, accuracy}`: shown when hovering a PCB part |
| node `extras` (glTF userData) | `group`, `explode_mm`, `model_source`, `accuracy` are read when `meta.nodes` lacks them |
| `section_planes` (v12) | Presets `{name, normal, constant}`: three.js plane convention, keeps `normal . p + constant >= 0` |
| `key_dimensions` (v12) | Side panel: outer size, board size, chamber volumes |
| `fit_findings` (v12) | Verification table (`severity` ok -> PASS) |
| `assumptions`, `open_items` (v12) | CAD notes and the Open items table (strings or `{item, detail}`) |
| `downloads` | List of files; otherwise `cad/downloads/SHA256SUMS` lists them |

Explode: a part's own vector replaces its group's vector (so nothing moves twice); groups with no vector at
all get an automatic direction away from the model centre, noted under the viewer.

## cad_status.json

`version`, `date`, `board`, `verdict`, `solids`, `unintended_overlaps`, `intended_overlaps`, `problems[]`
(v12) feed the side panel, CAD notes and Verification; an optional `checks[]` of `{check, result, detail}`
is listed in Verification as well.

## pcb_textures/textures.json (realistic board, 2026-11-03)

Optional. Written by `ai-files/helpers/make_pcb_textures.sh`. When present, `glb` and `copper_glb` (files in `cad/`)
replace the PCB file and the optional copper file of `meta.files` (the board can be newer than the CAD export), and
the viewer dresses the board: the Board_body top/bottom faces get `sides.{top,bottom}.albedo` (sRGB) and `rmb`
(R bump, G roughness, B metalness) mapped by `box_mm` / `origin_mm` (u along board x, v along board y, image row 0 =
`box.y`, bottom image not mirrored); the KiCad mask, silkscreen and pad-top meshes are hidden (plated barrels stay);
the parts get finishes from their colours and cast a static 2048 px shadow map. `renders` lead the gallery and replace
the export's `renders/pcb.png`. `top_albedo_2k` is used on small screens or GPUs below 4096 px textures.

## Hover names

The part name is the nearest named node that looks like a reference designator (KiCad names component nodes
`R238`, `U4`), else the nearest named node, skipping KiCad shape nodes (`=>[0:1:1:3]`). PCB references are
looked up in `data/bom.json` for value, function, MPN and LCSC code.
