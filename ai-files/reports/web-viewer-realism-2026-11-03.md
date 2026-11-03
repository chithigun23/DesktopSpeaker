# Web CAD viewer: realistic PCB, newest board, snapping view cube (2026-11-03)

Site: `ai-files/website/desktopSpeaker-site/` (not deployed; the coordinator copies it to the share). Nothing outside the
site folder was changed except the new helpers `ai-files/helpers/make_pcb_textures.{sh,py}`, this report and its
screenshot folder `ai-files/reports/web-viewer-realism-2026-11-03/`. The CAD export files (`cad/meta.json`,
`cad/pcb.glb`, `cad/pcb_copper.glb`, `cad/enclosure.glb`, `cad/renders/*` of v15) are untouched.

## 1 Owner feedback and what changed

| Feedback | Change |
| --- | --- |
| PCB looks neither good nor realistic, silkscreen hard to see | Board faces dressed with textures made from the real layers of the board: green mask with the copper faintly visible under it (lighter green over copper, slight bump), ENIG gold pads and annular rings (metallic, roughness 0.32), white silkscreen (clipped off mask openings as the fab does), dark drills, tented vias as small dimples, FR4/mask edge. Parts get finishes from their colours (black epoxy with a sheen, tin/steel, gold pins, tan ceramics, cream nylon). Generated studio environment light (PMREM, no download), ACES filmic tone mapping, sRGB output, static 2048 px contact-shadow map, anisotropy 12. |
| "The PCB render is old, missing a bunch of stuff" | The viewer now loads a new board model exported from the current board **RT-15H** (`ai-files/pcb/gui-finish/DesktopSpeaker-RT15H.kicad_pcb`, sha256 3f1e6cae...) instead of RT-14 (CAD v15). Tracks, zones, pads, vias, silkscreen, section boxes and the logo are in the texture, so they are visible by default (before, copper existed only in the optional copper file). The optional copper layer is now the RT-15H copper as geometry. The gallery leads with three new KiCad raytraced renders of RT-15H; the RT-14 `cad/renders/pcb.png` is skipped. |
| View cube lost its edges and corners | Chamfered cube ported from the cabinet viewer: 26 buttons (6 faces, 12 edge strips, 8 corner facets), hover shading per kind, click or tap swings the camera (400 ms ease) round the current target at the current distance: face = orthogonal, edge = 45 degrees, corner = isometric. Labels FRONT/BACK/LEFT/RIGHT/TOP/BOTTOM from meta (front = +z, up = +y, right = +x). ISO button and XYZ axes kept; the "Side" view button is now "Right". |

## 2 Files

| File | What |
| --- | --- |
| `site/app.js` | environment, tone mapping, shadow light; `cad/pcb_textures/textures.json` override of the PCB files; `realPcb()` (split Board_body into top/bottom/edge, UVs from board XY, hide KiCad mask/silk/pad-top meshes, keep plated barrels as gold geometry, part finishes, shadow casting); `updateShadow()` (on load, explode, group visibility); chamfered view cube (`buildCube`, `cubePiece`, `lookAlong`), `swing()` animation (with a fix for exactly opposite views); gallery: new board renders first, the 14 CAD v11 renders (old R6q board) folded behind a button |
| `site/style.css` | cube faces `.f`, edges `.e`, corners `.k`, hover colours (light and dark theme), `.gal.hide-old` |
| `site/index.html` | cube title, "Right" view button |
| `site/CAD_SCHEMA.md` | `pcb_textures/textures.json` section |
| `site/cad/pcb_rt15h.glb` (15.4 MB) | RT-15H board + parts, same export options and placement as CAD v15 (`--subst-models --include-pads --include-soldermask --include-silkscreen --user-origin 147.25x88.8mm`, repacked with `glb_repack.py --scale 1000 --translate -3.5 67.0 -133.3`, root `PCB_RT-15H`, parts named by reference) |
| `site/cad/pcb_copper_rt15h.glb` (25.4 MB, optional) | RT-15H tracks and zones as geometry |
| `site/cad/pcb_textures/` (5.5 MB) | `top_albedo.jpg` 4096 px (32 x 30 px/mm), `top_albedo_2k.jpg` (small screens), `top_rmb.jpg`, `bottom_albedo.jpg`, `bottom_rmb.jpg` (2048 px), `textures.json` |
| `site/cad/renders/pcb_real_{iso,top,bottom}.png` (3.2 MB) | KiCad 10.0.7 `pcb render --quality high` (iso with `--floor --perspective`), downscaled to 1600 px |
| `ai-files/helpers/make_pcb_textures.sh` / `.py` | regeneration (below) |

Page load: the PCB glb replaces the old one (same size); textures add 4.6 MB on desktop (3.1 MB on phones). Texture
memory about 150 MB (top albedo 4096 with mips about 89 MB, three 2048 maps about 64 MB) plus the 2048 shadow map
(16 MB). Draw cost: PCB-only view 246k triangles (415k before: the KiCad mask, silk and pad-top meshes are hidden);
measured frame time in headless swiftshader 6 ms against 3 to 4 ms before (no runaway cost); the shadow map is
redrawn only on load, explode and visibility changes.

## 3 Regenerate

```
ai-files/helpers/make_pcb_textures.sh [BOARD.kicad_pcb] [WORKDIR]        # default board: gui-finish RT-15H
```
Copies the board (+ .kicad_pro/.kicad_dru/fp-lib-table, kicad-library link) to WORKDIR (default a fresh /tmp folder,
never inside DesktopSpeaker-kicad/), applies the models-v13 links, exports and repacks both glb files, dumps outline
and drills with pcbnew (`~/Applications/kicad.AppImage python3.11 make_pcb_textures.py dump ...`), exports
F/B.Cu, Mask, SilkS as SVG with kicad-cli, rasterises them with cairosvg over the exact outline box (127.5 x 137.6 mm
at x 86.25, y 20.0) and composites the textures (`make_pcb_textures.py build ...`, numpy + pillow + cairosvg in
`PYVENV`), then makes the three hero renders. Env `TAG` (file suffix, default RT15H) and `PCB_T` (placement, default
the CAD v15 values). Run it again for the final board (after the 9 GUI connections and teardrops) and for the final
mask colour (constants `MASK_GREEN*`, `SILK` at the top of the .py). Time: about 2 minutes.

## 4 Verification (headless Chrome + swiftshader WebGL, 1400 x 1000 and 390 x 844)

Screenshots in `ai-files/reports/web-viewer-realism-2026-11-03/`:
`before_after_full_top_oblique.jpg`, `before_after_bottom_mcu_amp.jpg`, `before_after_enclosure_iso.jpg`,
`after_pcb_{top,bottom,oblique,mcu_close,amp_close,bm83_close}.jpg`, `after_full_iso_dark.jpg`,
`after_copper_geometry_layer_on.jpg`, `after_hover_label.jpg`, `cube_hover_face_edge_corner_dark_tap.jpg`,
`cube_snapped_views.jpg`, `mobile_390px_light_dark.jpg`, `mobile_gallery.jpg`.

- Alignment: texture pads, holes and silk sit under the matching 3D parts (MCU U3, U24, BM83 U1, U6/U7 amplifiers,
  inductors, test points, encoder); text reads correctly from the top; the bottom view matches the KiCad geometry
  orientation of the old silkscreen mesh (logo and "Desktop Speaker Rev A" in the same place). No z-fighting: the
  board top/bottom faces of Board_body are replaced, not overlaid.
- View cube: all 26 pieces clicked programmatically; every resulting view direction matched (faces (0,0,1) etc.,
  edges 0.71, corners 0.58), distance (548 mm) and target unchanged; opposite jumps (for example bottom-back-right to
  top-front-left) correct after the half-turn fix; real mouse hover shows face, edge and corner shading (light and
  dark); a CDP touch tap on RIGHT snapped to (1,0,0).
- Hover names still work (`SW102 · EC11E`, `L201 · 22uH`); explode, reset, groups, optional copper layer work.
- Console: no messages or exceptions in any run (desktop, mobile, dark theme).
- Components: all 346 footprints with a 3D model have a node in `pcb_rt15h.glb` (including J1, J2, J3, J5, J9-J11,
  SW100, SW102, TP1-TP27, U1). The 14 footprints without a model (H1-H9 and HA1-HA2 mounting holes, J7 TC2030 pads,
  LOGO1, SW101 wire pads) are now visible in the texture: gold rings with real holes, the TC2030 pad/hole pattern,
  the logo in bottom silkscreen and the three gold oval wire pads. Nothing modelled is absent.

## 5 Limits and owner decisions

- **Mask colour**: `fab/ORDER-NOTES.md` leaves mask/silk colour to the owner ("green/white is cheapest"); the textures
  use JLC green with white silk. Another colour (black, blue, matte) is a one-line change plus a rerun.
- Vias are drawn tented (ORDER-NOTES: tented); the 3 accepted via-in-pad holes show as open drills in their pads.
- RT-15H still has 9 open connections and no teardrops: the picture shows that state. Rerun the script on the final board.
- The enclosure CAD renders of v15 (and the folded v11 images in `img/`) were not regenerated with RT-15H: that needs
  the full FreeCAD rebuild (`ai-files/cad/v15/scripts/rebuild_cad.sh`), which writes `cad/meta.json`, the enclosure
  and the v15 renders (outside this task's write scope). At enclosure scale the RT-14 to RT-15H change (TP17 moved,
  copper) is not visible. `build_site_data.py` still copies the v11 renders to `img/`; the page now folds them behind
  "Show the 14 older CAD v11 renders" while the v15 renders exist.
- `cad/meta.json` still names RT-14 as the CAD board; the viewer foot note says which board is shown. The next CAD
  rebuild should run `make_pcb_textures.sh` afterwards (or the override keeps showing RT-15H).
- Contact shadows come from one fixed light at about 45 degrees and are short; there is no screen-space AO.
- Component models keep KiCad's colours; finishes are inferred from colour (models without any colour, for example
  SW102 and J2/J3, are shown grey metal as in KiCad).
