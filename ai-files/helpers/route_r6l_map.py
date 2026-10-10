"""flatpak: route_r6l_map.py BOARD x0 y0 x1 y1 LAYER(F|2|B) OUT.svg [grid_mm]
Net-coloured SVG of one copper layer in a box: zone fills, tracks, arcs, vias, pads (pads on the layer), with net-name labels on
pads/vias/zones and an optional coordinate grid. Convert with: node route_p1_png.mjs OUT.svg OUT.png 1600"""
import sys, hashlib, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1]); x0, y0, x1, y1 = map(float, sys.argv[2:6]); LN = sys.argv[6]; out = sys.argv[7]
grid = float(sys.argv[8]) if len(sys.argv) > 8 else 0.5
L = {'F': pcbnew.F_Cu, '1': pcbnew.In1_Cu, '2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}[LN]
S = 100.0  # px per mm
def X(x): return (x - x0) * S
def Y(y): return (y - y0) * S
def col(n):
    if n == 'GND': return '#9a9a9a'
    if n == '': return '#ffffff'
    h = hashlib.md5(n.encode()).digest(); return '#%02x%02x%02x' % (60 + h[0] % 170, 60 + h[1] % 170, 60 + h[2] % 170)
def short(n): return n.split('/')[-1].replace('Battery_Charger', '').replace('Net-(', '').replace(')', '')
o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (X(x1), Y(y1), X(x1), Y(y1)), '<rect width="100%" height="100%" fill="#fff"/>']
def poly(ps, fill, op=0.55, stroke='none'):
    for k in range(ps.OutlineCount()):
        d = ''
        ol = ps.Outline(k)
        d += 'M' + ' L'.join('%.1f,%.1f' % (X(ol.CPoint(i).x / MM), Y(ol.CPoint(i).y / MM)) for i in range(ol.PointCount())) + ' Z '
        for h in range(ps.HoleCount(k)):
            hl = ps.Hole(k, h); d += 'M' + ' L'.join('%.1f,%.1f' % (X(hl.CPoint(i).x / MM), Y(hl.CPoint(i).y / MM)) for i in range(hl.PointCount())) + ' Z '
        o.append('<path d="%s" fill="%s" fill-opacity="%.2f" fill-rule="evenodd" stroke="%s" stroke-width="1"/>' % (d, fill, op, stroke))
labels = []
box = pcbnew.BOX2I(pcbnew.VECTOR2I(int(x0 * MM), int(y0 * MM)), pcbnew.VECTOR2I(int((x1 - x0) * MM), int((y1 - y0) * MM)))
for z in b.Zones():
    if z.GetIsRuleArea():
        if z.IsOnLayer(L) and z.GetBoundingBox().Intersects(box):
            ol = z.Outline()
            pts = ' '.join('%.1f,%.1f' % (X(ol.CVertex(i).x / MM), Y(ol.CVertex(i).y / MM)) for i in range(ol.TotalVertices()))
            o.append('<polygon points="%s" fill="none" stroke="#c0f" stroke-dasharray="8,6" stroke-width="2"/>' % pts)
        continue
    if not z.IsOnLayer(L) or not z.HasFilledPolysForLayer(L) or not z.GetBoundingBox().Intersects(box): continue
    n = str(z.GetNetname()); fp = z.GetFilledPolysList(L); poly(fp, col(n), 0.45 if n == 'GND' else 0.6)
    ol = z.Outline(); pts = ' '.join('%.1f,%.1f' % (X(ol.CVertex(i).x / MM), Y(ol.CVertex(i).y / MM)) for i in range(ol.TotalVertices()))
    o.append('<polygon points="%s" fill="none" stroke="%s" stroke-dasharray="4,4" stroke-width="1"/>' % (pts, col(n)))
    if n != 'GND':
        bb = fp.BBox(); labels.append(((bb.GetLeft() + bb.GetRight()) / 2 / MM, (bb.GetTop() + bb.GetBottom()) / 2 / MM, z.GetZoneName() or short(n), 14, '#000'))
for t in b.GetTracks():
    if not t.GetBoundingBox().Intersects(box): continue
    n = str(t.GetNetname())
    if t.GetClass() == 'PCB_VIA':
        r = t.GetWidth(pcbnew.F_Cu) / MM / 2; dr = t.GetDrillValue() / MM / 2
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="#000" stroke-width="1"/><circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff"/>' % (X(t.GetX() / MM), Y(t.GetY() / MM), r * S, col(n), X(t.GetX() / MM), Y(t.GetY() / MM), dr * S))
        if n != 'GND': labels.append((t.GetX() / MM, t.GetY() / MM + r + 0.08, short(n), 9, '#00f'))
        continue
    if t.GetLayer() != L: continue
    w = t.GetWidth() / MM * S
    if t.GetClass() == 'PCB_ARC':
        sh = t.GetEffectiveShape(L); ps = pcbnew.SHAPE_POLY_SET(); t.TransformShapeToPolygon(ps, L, 0, 5000, pcbnew.ERROR_INSIDE); poly(ps, col(n), 0.9, '#000')
        continue
    a, c = t.GetStart(), t.GetEnd()
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%.1f" stroke-linecap="round" stroke-opacity="0.9"/>' % (X(a.x / MM), Y(a.y / MM), X(c.x / MM), Y(c.y / MM), col(n), w))
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#000" stroke-width="0.8"/>' % (X(a.x / MM), Y(a.y / MM), X(c.x / MM), Y(c.y / MM)))
    if (a.x - c.x) ** 2 + (a.y - c.y) ** 2 > (0.8 * MM) ** 2: labels.append(((a.x + c.x) / 2 / MM, (a.y + c.y) / 2 / MM, '%s %.2f' % (short(n), t.GetWidth() / MM), 8, '#600'))
for f in b.GetFootprints():
    if not f.GetBoundingBox().Intersects(box): continue
    for p in f.Pads():
        if not p.IsOnLayer(L): continue
        n = str(p.GetNetname()); ps = p.GetEffectivePolygon(L); poly(ps, col(n), 0.95, '#000')
        labels.append((p.GetX() / MM, p.GetY() / MM, '%s.%s' % (f.GetReference(), p.GetNumber()), 9, '#000'))
    labels.append((f.GetX() / MM, f.GetY() / MM - 0.15, f.GetReference(), 12, '#a00'))
g = grid
xx = int(x0 / g) * g
while xx <= x1:
    o.append('<line x1="%.1f" y1="0" x2="%.1f" y2="%.1f" stroke="#08f" stroke-opacity="%.2f" stroke-width="0.6"/>' % (X(xx), X(xx), Y(y1), 0.5 if abs(xx - round(xx)) < 1e-6 else 0.18))
    if abs(xx - round(xx)) < 1e-6: o.append('<text x="%.1f" y="12" font-size="12" fill="#08f">%g</text>' % (X(xx) + 2, xx))
    xx += g
yy = int(y0 / g) * g
while yy <= y1:
    o.append('<line x1="0" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#08f" stroke-opacity="%.2f" stroke-width="0.6"/>' % (Y(yy), X(x1), Y(yy), 0.5 if abs(yy - round(yy)) < 1e-6 else 0.18))
    if abs(yy - round(yy)) < 1e-6: o.append('<text x="2" y="%.1f" font-size="12" fill="#08f">%g</text>' % (Y(yy) - 2, yy))
    yy += g
for x, y, s, fs, c in labels:
    if x0 <= x <= x1 and y0 <= y <= y1: o.append('<text x="%.1f" y="%.1f" font-size="%d" fill="%s" text-anchor="middle" font-family="sans-serif">%s</text>' % (X(x), Y(y) + fs / 3, fs, c, s.replace('&', '&amp;').replace('<', '&lt;')))
o.append('</svg>'); open(out, 'w').write('\n'.join(o)); print('wrote', out)
