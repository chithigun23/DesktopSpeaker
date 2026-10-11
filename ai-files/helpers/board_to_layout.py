#!/usr/bin/env python3
"""Routed .kicad_pcb -> CAD layout JSON (schema of ai-files/pcb/work-v10d/layout-v10d.json).

Run with KiCad's python (pcbnew), e.g.
  flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --filesystem=/tmp --command=python3 org.kicad.KiCad \
      ai-files/helpers/board_to_layout.py BOARD.kicad_pcb OUT.json [REFERENCE_LAYOUT.json]

Frame: u = x_board - U_ORIGIN, v = V_ORIGIN - y_board (mm; KiCad y points down, v points to the rear edge).
The origin is the board outline centre in u-design terms: U_ORIGIN = 147.25 (layout frame u = 0 at the
enclosure centre line as the v10 generator placed it), V_ORIGIN = outline centre y (88.8 for the routed board).
board.rear_edge_cad_y = FRONT_CAD_Y + d (front board edge fixed at CAD y 64.5, as build_pcb_v10d.py).
Holes: footprints H<n> / HA<n>.  Part rect = front/back courtyard bounding box (falls back to the
footprint bounding box without text); cy_u/cy_v = rect centre; origin_u/origin_v = footprint origin.
The optional reference JSON supplies the 'owner' map (generator-only data, not on the board).
"""
import sys, re, json
import pcbnew

MM = 1e6
U_ORIGIN = 147.25
FRONT_CAD_Y = 64.5
CORNER_R_DEFAULT = 3.0


def main(board_path, out_path, ref_path=None):
    b = pcbnew.LoadBoard(board_path)
    # ---- outline from Edge.Cuts
    xs, ys, arcs = [], [], []
    for d in b.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        sb = d.GetBoundingBox()
        xs += [sb.GetX() / MM, sb.GetRight() / MM]
        ys += [sb.GetY() / MM, sb.GetBottom() / MM]
        if d.GetShape() == pcbnew.SHAPE_T_ARC:
            arcs.append(d.GetRadius() / MM)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    # arc bounding boxes include the line width; snap to the line end points
    lx, ly = [], []
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            for p in (d.GetStart(), d.GetEnd()):
                lx.append(p.x / MM); ly.append(p.y / MM)
    x0, x1, y0, y1 = min(lx), max(lx), min(ly), max(ly)
    V_ORIGIN = round((y0 + y1) / 2, 4)
    uv = lambda x, y: (x - U_ORIGIN, V_ORIGIN - y)
    w, dd = round(x1 - x0, 4), round(y1 - y0, 4)
    board = dict(w=w, d=dd, u0=round(x0 - U_ORIGIN, 4), u1=round(x1 - U_ORIGIN, 4), v0=-dd / 2, v1=dd / 2,
                 corner_r=round(max(arcs), 3) if arcs else CORNER_R_DEFAULT,
                 rear_edge_cad_y=round(FRONT_CAD_Y + dd, 4), centre_cad_y=round(FRONT_CAD_Y + dd / 2, 4),
                 v_design_offset=-dd / 2)
    holes, parts, sheets = [], {}, {}
    for f in sorted(b.GetFootprints(), key=lambda f: (re.sub(r'\d+', '', f.GetReference()), int(re.sub(r'\D', '', f.GetReference()) or 0))):
        ref = f.GetReference()
        p = f.GetPosition()
        ou, ov = uv(p.x / MM, p.y / MM)
        if re.match(r'^HA?\d+$', ref):
            holes.append(dict(name=ref, u=round(ou, 4), v=round(ov, 4)))
            continue
        try:
            sheets[ref] = f.GetSheetname() if f.GetSheetname() != 'Root' else ''
        except Exception:
            sheets[ref] = ''
        f.BuildCourtyardCaches()
        cy = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
        if cy.OutlineCount() > 0:
            bb = cy.BBox()
            bx0, by0, bx1, by1 = bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM
        else:
            bb = f.GetBoundingBox(False, False)
            bx0, by0, bx1, by1 = bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM
        ru0, rv1 = uv(bx0, by0); ru1, rv0 = uv(bx1, by1)
        rot = round(f.GetOrientationDegrees()) % 360
        parts[ref] = dict(origin_u=round(ou, 3), origin_v=round(ov, 3), rot=rot,
                          cy_u=round((ru0 + ru1) / 2, 3), cy_v=round((rv0 + rv1) / 2, 3),
                          rect=[round(ru0, 3), round(rv0, 3), round(ru1, 3), round(rv1, 3)],
                          side='B' if f.IsFlipped() else 'F', fpid=f.GetFPIDAsString())
    holes.sort(key=lambda h: (h['name'].startswith('HA'), int(re.sub(r'\D', '', h['name']))))
    ant = None
    for z in b.Zones():
        if z.GetIsRuleArea() and 'ANTENNA' in z.GetZoneName().upper():
            zb = z.GetBoundingBox()
            a0, a1 = uv(zb.GetX() / MM, zb.GetBottom() / MM), uv(zb.GetRight() / MM, zb.GetY() / MM)
            ant = dict(u0=round(a0[0], 4), u1=round(a1[0], 4), v0=round(a0[1], 4), v1=round(a1[1], 4))
    owner = {}
    if ref_path:
        owner = json.load(open(ref_path)).get('owner', {})
    out = dict(board=board, holes=holes, parts=parts, sheets=sheets, owner=owner, antenna=ant, failed=[], noslot=[],
               source=dict(board=board_path, frame='u = x - %.2f, v = %.4f - y (mm)' % (U_ORIGIN, V_ORIGIN), generator='board_to_layout.py'))
    json.dump(out, open(out_path, 'w'), indent=1)
    print('board', board); print('holes', len(holes), 'parts', len(parts), 'antenna', ant)


if __name__ == '__main__':
    main(*sys.argv[1:4])
