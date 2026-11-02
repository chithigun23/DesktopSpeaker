#!/usr/bin/env python3
"""silk_tile_gate.py - independent gates for a silk_tile.py result.

Run headless with the KiCad AppImage interpreter (needs pcbnew):
  ~/Applications/kicad.AppImage python3.11 silk_tile_gate.py BASE.kicad_pcb NEW.kicad_pcb \
      --drc-base BASE.drc.json --drc-new NEW.drc.json [--json OUT.json]
(DRC files: kicad-cli pcb drc --severity-all --all-track-errors --format json, project rules beside each board.)

Gates (all must pass):
  G1  every board item except F.SilkS gr_* graphics is byte-identical (text with F.SilkS gr_* blocks removed)
  G2  footprints: same set, same position/orientation/side (pcbnew), and every footprint block byte-identical (G1)
  G3  DRC: violation count of NEW == BASE and unconnected count of NEW == BASE
  G4  box lines (F.SilkS gr_line, width W): every segment end is shared by exactly 2 or 3 segment ends, or lies on the
      tiled-region boundary; no end lies inside another segment; no overlapping collinear segments; axis-aligned only
  G5  tiling: the box lines cut the tiled region into faces; every face holds exactly one section title, every
      title lies in its own face, face areas sum to the region area (rectangle cells, so no overlap and no gap)
  G6  clearances: no box line within 0.2 mm of an exposed pad (F.Cu pad with F.Mask or a hole), none crosses a
      footprint courtyard, footprint silkscreen, footprint text, a board text, or a mounting-hole square (0.4 mm line)
"""
import re, sys, json, argparse
import pcbnew

ap = argparse.ArgumentParser()
ap.add_argument('base'); ap.add_argument('new')
ap.add_argument('--drc-base'); ap.add_argument('--drc-new')
ap.add_argument('--width', type=float, default=0.15)
ap.add_argument('--region', default='86.65,20.4,213.35,157.2')
ap.add_argument('--pad-clear', type=float, default=0.2)
ap.add_argument('--text-pad', type=float, default=0.15, help='KiCad text bbox padding above/below the ink, ignored for line-vs-board-text tests')
ap.add_argument('--json')
a = ap.parse_args()
RX0, RY0, RX1, RY1 = map(float, a.region.split(','))
res = {}; ok_all = True
def gate(name, ok, detail):
    global ok_all
    ok_all &= bool(ok)
    res[name] = {'pass': bool(ok), 'detail': detail}
    print('%-3s %s  %s' % (name, 'PASS' if ok else 'FAIL', json.dumps(detail)[:600]))

# ---------- G1 text identity outside F.SilkS gr_*
def strip_fsilk(t):
    out = []; pos = 0; n = 0
    for m in re.finditer(r'^\t\(gr_\w+', t, re.M):
        s = m.start(); depth = 0; i = s; ins = False
        while True:
            c = t[i]
            if ins:
                if c == '\\': i += 1
                elif c == '"': ins = False
            elif c == '"': ins = True
            elif c == '(': depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0: break
            i += 1
        e = i + 2 if t[i + 1:i + 2] == '\n' else i + 1
        blk = t[s:e]
        if '(layer "F.SilkS")' in blk:
            out.append(t[pos:s]); pos = e; n += 1
    out.append(t[pos:])
    return ''.join(out), n
tb, nb = strip_fsilk(open(a.base).read()); tn, nn = strip_fsilk(open(a.new).read())
gate('G1', tb == tn, {'base_fsilk_gr_items': nb, 'new_fsilk_gr_items': nn, 'rest_identical': tb == tn,
                      'rest_bytes': len(tb)})

# ---------- G2 footprints
M = 1e6
def fpdump(path):
    b = pcbnew.LoadBoard(path)
    return b, {f.GetReference() + '|' + str(f.m_Uuid.AsString()): (f.GetPosition().x, f.GetPosition().y, round(f.GetOrientationDegrees(), 4), f.IsFlipped()) for f in b.GetFootprints()}
bb, fb = fpdump(a.base); bn, fn = fpdump(a.new)
moved = [k for k in fb if fb.get(k) != fn.get(k)]
gate('G2', not moved and set(fb) == set(fn), {'footprints': len(fn), 'moved_or_missing': moved[:20]})

# ---------- G3 DRC
if a.drc_base and a.drc_new:
    db = json.load(open(a.drc_base)); dn = json.load(open(a.drc_new))
    vb, vn = len(db['violations']), len(dn['violations']); ub, un = len(db['unconnected_items']), len(dn['unconnected_items'])
    from collections import Counter
    gate('G3', vb == vn and ub == un, {'violations_base': vb, 'violations_new': vn, 'unconnected_base': ub, 'unconnected_new': un,
                                       'new_types': dict(Counter(v['type'] for v in dn['violations']))})
else:
    gate('G3', False, 'no DRC files given')

# ---------- collect box lines from the NEW board (pcbnew)
W = int(round(a.width * M))
segs = []
for g in bn.GetDrawings():
    if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() == 'PCB_SHAPE' and g.GetWidth() == W:
        if g.GetShape() != pcbnew.SHAPE_T_SEGMENT:
            segs.append(None); continue
        s, e = g.GetStart(), g.GetEnd()
        segs.append(((s.x, s.y), (e.x, e.y)))
nonseg = sum(1 for s in segs if s is None); segs = [s for s in segs if s]
def on_boundary(p):
    x, y = p[0] / M, p[1] / M
    return abs(x - RX0) < 1e-4 or abs(x - RX1) < 1e-4 or abs(y - RY0) < 1e-4 or abs(y - RY1) < 1e-4
cnt = {}
for s in segs:
    for p in s: cnt[p] = cnt.get(p, 0) + 1
bad_deg = [(p[0] / M, p[1] / M, c) for p, c in cnt.items() if not (c in (2, 3) or (c == 1 and on_boundary(p)))]
diag = [s for s in segs if s[0][0] != s[1][0] and s[0][1] != s[1][1]]
def inside(p, s):
    (x1, y1), (x2, y2) = s
    if x1 == x2 == p[0]: return min(y1, y2) < p[1] < max(y1, y2)
    if y1 == y2 == p[1]: return min(x1, x2) < p[0] < max(x1, x2)
    return False
t_unsplit = [(p[0] / M, p[1] / M) for p in cnt for s in segs if inside(p, s)]
overl = 0
for i, s in enumerate(segs):
    for t in segs[i + 1:]:
        if s[0][0] == s[1][0] == t[0][0] == t[1][0]:
            lo, hi = sorted((s[0][1], s[1][1])); lo2, hi2 = sorted((t[0][1], t[1][1]))
            if min(hi, hi2) > max(lo, lo2): overl += 1
        elif s[0][1] == s[1][1] == t[0][1] == t[1][1]:
            lo, hi = sorted((s[0][0], s[1][0])); lo2, hi2 = sorted((t[0][0], t[1][0]))
            if min(hi, hi2) > max(lo, lo2): overl += 1
outside = [s for s in segs if any(not (RX0 * M - 1 <= p[0] <= RX1 * M + 1 and RY0 * M - 1 <= p[1] <= RY1 * M + 1) for p in s)]
deg = {}
for c in cnt.values(): deg[c] = deg.get(c, 0) + 1
gate('G4', not (bad_deg or diag or t_unsplit or overl or nonseg or outside),
     {'segments': len(segs), 'end_multiplicity': deg, 'dangling_or_4way': bad_deg, 'diagonal': len(diag),
      'unsplit_T': t_unsplit[:10], 'overlaps': overl, 'arcs_or_other': nonseg, 'outside_region': len(outside)})

# ---------- G5 faces (cell union-find on the line grid)
xs = sorted({RX0 * M, RX1 * M} | {p[0] for s in segs for p in s}); xs = [int(round(v)) for v in xs]
ys = sorted({RY0 * M, RY1 * M} | {p[1] for s in segs for p in s}); ys = [int(round(v)) for v in ys]
xs = sorted(set(xs)); ys = sorted(set(ys))
hcut = set(); vcut = set()   # blocked cell borders
for (p, q) in segs:
    if p[1] == q[1]:
        j = ys.index(p[1]); lo, hi = sorted((p[0], q[0]))
        for i in range(len(xs) - 1):
            if xs[i] >= lo and xs[i + 1] <= hi: hcut.add((i, j))     # border between cell row j-1 and j at column i
    else:
        i = xs.index(p[0]); lo, hi = sorted((p[1], q[1]))
        for j in range(len(ys) - 1):
            if ys[j] >= lo and ys[j + 1] <= hi: vcut.add((i, j))     # border between cell col i-1 and i at row j
par = {}
def f(c):
    while par.setdefault(c, c) != c:
        par[c] = par[par[c]]; c = par[c]
    return c
nx, ny = len(xs) - 1, len(ys) - 1
for i in range(nx):
    for j in range(ny):
        f((i, j))
        if i + 1 < nx and (i + 1, j) not in vcut: par[f((i, j))] = f((i + 1, j))
        if j + 1 < ny and (i, j + 1) not in hcut: par[f((i, j))] = f((i, j + 1))
faces = {}
for i in range(nx):
    for j in range(ny):
        faces.setdefault(f((i, j)), []).append((i, j))
area = {k: sum((xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j]) for i, j in v) / M / M for k, v in faces.items()}
def bbox(k):
    v = faces[k]
    return (xs[min(i for i, _ in v)] / M, ys[min(j for _, j in v)] / M, xs[max(i for i, _ in v) + 1] / M, ys[max(j for _, j in v) + 1] / M)
def face_of(x, y):
    i = max(k for k in range(nx) if xs[k] <= x * M); j = max(k for k in range(ny) if ys[k] <= y * M)
    return f((min(i, nx - 1), min(j, ny - 1)))
# titles: F.SilkS gr_text of height >= 0.9 mm that are not net labels (listed in silk_tile.TITLES when importable)
try:
    sys.path.insert(0, __file__.rsplit('/', 1)[0]); import silk_tile as ST; tnames = set(ST.TITLES)
except Exception:
    tnames = None
titles = []
for g in bn.GetDrawings():
    if g.GetClass() == 'PCB_TEXT' and g.GetLayer() == pcbnew.F_SilkS:
        if (tnames is not None and g.GetText() in tnames) or (tnames is None and g.GetTextHeight() >= 1.0 * M):
            r = g.GetBoundingBox()
            titles.append((g.GetText(), r.GetLeft() / M, r.GetTop() / M, r.GetRight() / M, r.GetBottom() / M))
per_face = {}
bad_t = []
for t in titles:
    c = face_of((t[1] + t[3]) / 2, (t[2] + t[4]) / 2)
    corners = {face_of(t[1] + 0.01, t[2] + 0.26), face_of(t[3] - 0.01, t[2] + 0.26), face_of(t[1] + 0.01, t[4] - 0.26), face_of(t[3] - 0.01, t[4] - 0.26)}
    if corners != {c}: bad_t.append(t[0])
    per_face.setdefault(c, []).append(t[0])
fails = {str([round(v, 2) for v in bbox(k)]): per_face.get(k, []) for k in faces if len(per_face.get(k, [])) != 1}
region_area = (RX1 - RX0) * (RY1 - RY0)
rect_faces = sum(1 for k in faces if abs(area[k] - (bbox(k)[2] - bbox(k)[0]) * (bbox(k)[3] - bbox(k)[1])) < 1e-6)
facelist = sorted(([per_face.get(k, ['?'])[0], [round(v, 2) for v in bbox(k)], round(area[k], 2),
                    'rect' if abs(area[k] - (bbox(k)[2] - bbox(k)[0]) * (bbox(k)[3] - bbox(k)[1])) < 1e-6 else 'rectilinear']
                   for k in faces), key=lambda r: (r[1][1], r[1][0]))
gate('G5', not fails and not bad_t and abs(sum(area.values()) - region_area) < 1e-6,
     {'faces': len(faces), 'titles': len(titles), 'rectangular_faces': rect_faces, 'faces_without_exactly_one_title': fails,
      'titles_crossing_lines': bad_t, 'area_sum': round(sum(area.values()), 4), 'region_area': round(region_area, 4)})
res['faces'] = facelist

# ---------- G6 clearances
def seg_box_dist(s, r):
    """distance between axis-aligned segment s (mm) and box r=(x0,y0,x1,y1); 0 if they intersect"""
    (x1, y1), (x2, y2) = s
    lo_x, hi_x = min(x1, x2), max(x1, x2); lo_y, hi_y = min(y1, y2), max(y1, y2)
    dx = max(r[0] - hi_x, lo_x - r[2], 0); dy = max(r[1] - hi_y, lo_y - r[3], 0)
    return (dx * dx + dy * dy) ** 0.5
def seg_seg_dist(s, t):
    import math
    def pd(p, a, b):
        ax, ay = a; bx, by = b; px, py = p
        L = (bx - ax) ** 2 + (by - ay) ** 2
        u = 0 if L == 0 else max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / L))
        return math.hypot(px - ax - u * (bx - ax), py - ay - u * (by - ay))
    def inter(a, b, c, d):
        def o(p, q, r): return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0
    if inter(s[0], s[1], t[0], t[1]): return 0.0
    return min(pd(s[0], *t), pd(s[1], *t), pd(t[0], *s), pd(t[1], *s))
S = [((p[0] / M, p[1] / M), (q[0] / M, q[1] / M)) for p, q in segs]
hw = a.width / 2
viol = []
def box_of(r): return (r.GetLeft() / M, r.GetTop() / M, r.GetRight() / M, r.GetBottom() / M)
for fp in bn.GetFootprints():
    if fp.IsFlipped(): continue
    ref = fp.GetReference()
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    crt_polys = []
    for oi in range(cy.OutlineCount()):
        o = cy.Outline(oi); pts = [(o.CPoint(i).x / M, o.CPoint(i).y / M) for i in range(o.PointCount())]
        crt_polys.append(pts)
    for p in fp.Pads():
        ls = p.GetLayerSet()
        if not (ls.Contains(pcbnew.F_Cu) and (ls.Contains(pcbnew.F_Mask) or p.GetDrillSize().x > 0)): continue
        poly = p.GetEffectivePolygon(pcbnew.F_Cu, pcbnew.ERROR_INSIDE)
        for oi in range(poly.OutlineCount()):
            o = poly.Outline(oi); pts = [(o.CPoint(i).x / M, o.CPoint(i).y / M) for i in range(o.PointCount())]
            edges = list(zip(pts, pts[1:] + pts[:1]))
            bx = (min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts), max(y for _, y in pts))
            for s in S:
                if seg_box_dist(s, bx) - hw > a.pad_clear + 0.5: continue
                d = min(seg_seg_dist(s, e) for e in edges) - hw
                if d < a.pad_clear - 1e-6: viol.append(('pad', ref, p.GetNumber(), s, round(d, 3)))
    for pts in crt_polys:
        edges = list(zip(pts, pts[1:] + pts[:1]))
        for s in S:
            d = min(seg_seg_dist(s, e) for e in edges) - hw
            if d < 0: viol.append(('courtyard', ref, s, round(d, 3)))
    for g in list(fp.GraphicalItems()) + [fp.Reference(), fp.Value()]:
        if g.GetLayer() != pcbnew.F_SilkS: continue
        if g.GetClass() == 'PCB_FIELD' and not g.IsVisible(): continue
        r = box_of(g.GetBoundingBox())   # footprint silk and footprint text: full bbox (DRC silk_overlap uses 0 clearance)
        for s in S:
            if seg_box_dist(s, r) - hw < 0: viol.append(('fp_silk', ref, g.GetClass(), s))
for g in bn.GetDrawings():
    if g.GetLayer() != pcbnew.F_SilkS: continue
    if g.GetClass() == 'PCB_TEXT':
        r = box_of(g.GetBoundingBox()); r = (r[0], r[1] + a.text_pad, r[2], r[3] - a.text_pad)
        for s in S:
            if seg_box_dist(s, r) - hw < 0:
                viol.append(('text', g.GetText(), s, round(seg_box_dist(s, r) - hw, 3)))
    elif g.GetClass() == 'PCB_SHAPE' and g.GetWidth() != W:
        t = ((g.GetStart().x / M, g.GetStart().y / M), (g.GetEnd().x / M, g.GetEnd().y / M))
        for s in S:
            d = seg_seg_dist(s, t) - hw - g.GetWidth() / M / 2
            if d < 0.1: viol.append(('silk_graphic w%.2f' % (g.GetWidth() / M), t, s, round(d, 3)))
gate('G6', not viol, {'violations': len(viol), 'first': [str(v) for v in viol[:15]], 'pad_clearance_mm': a.pad_clear})
print('ALL PASS' if ok_all else 'GATES FAILED')
if a.json:
    json.dump(res, open(a.json, 'w'), indent=1)
sys.exit(0 if ok_all else 1)
