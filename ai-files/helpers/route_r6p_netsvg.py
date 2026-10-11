"""flatpak: route_r6p_netsvg.py BOARD OUT.svg NET1,NET2 [x0 y0 x1 y1] : SVG of the board with all copper faint and the given nets
highlighted (F.Cu red, In2 green, B.Cu blue, vias black ring, the nets' pads orange). Grid every 5 mm (labels). Convert: node route_p1_png.mjs."""
import sys, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1]); out = sys.argv[2]; HL = set(sys.argv[3].split(','))
bb = b.GetBoardEdgesBoundingBox()
x0, y0, x1, y1 = (map(float, sys.argv[4:8]) if len(sys.argv) > 7 else (bb.GetX() / MM - 1, bb.GetY() / MM - 1, bb.GetRight() / MM + 1, bb.GetBottom() / MM + 1))
COL = {pcbnew.F_Cu: '#d01010', pcbnew.In2_Cu: '#10a020', pcbnew.B_Cu: '#1040e0', pcbnew.In1_Cu: '#999999'}
FA = {pcbnew.F_Cu: '#e8c0c0', pcbnew.In2_Cu: '#c0e0c0', pcbnew.B_Cu: '#c0c8f0', pcbnew.In1_Cu: '#dddddd'}
o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="%g %g %g %g" width="%gmm" height="%gmm"><rect x="%g" y="%g" width="%g" height="%g" fill="white"/>' % (x0, y0, x1 - x0, y1 - y0, x1 - x0, y1 - y0, x0, y0, x1 - x0, y1 - y0)]
import math
g = 5 * math.floor(x0 / 5)
while g <= x1: o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#eeeeee" stroke-width="0.05"/><text x="%g" y="%g" font-size="1.2" fill="#aaaaaa">%g</text>' % (g, y0, g, y1, g + 0.2, y0 + 1.5, g)); g += 5
g = 5 * math.floor(y0 / 5)
while g <= y1: o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#eeeeee" stroke-width="0.05"/><text x="%g" y="%g" font-size="1.2" fill="#aaaaaa">%g</text>' % (x0, g, x1, g, x0 + 0.2, g - 0.2, g)); g += 5
def poly(ps, fill, op=1):
    for k in range(ps.OutlineCount()):
        ol = ps.Outline(k); pts = ' '.join('%.3f,%.3f' % (ol.CPoint(i).x / MM, ol.CPoint(i).y / MM) for i in range(ol.PointCount()))
        o.append('<polygon points="%s" fill="%s" fill-opacity="%g"/>' % (pts, fill, op))
ps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ps, True)
for k in range(ps.OutlineCount()):
    ol = ps.Outline(k); o.append('<polygon points="%s" fill="none" stroke="#444" stroke-width="0.15"/>' % ' '.join('%.3f,%.3f' % (ol.CPoint(i).x / MM, ol.CPoint(i).y / MM) for i in range(ol.PointCount())))
for z in b.Zones():
    if z.GetIsRuleArea() or z.IsTeardropArea(): continue
    for L in (pcbnew.B_Cu, pcbnew.In2_Cu, pcbnew.F_Cu):
        if z.IsOnLayer(L) and z.HasFilledPolysForLayer(L) and str(z.GetNetname()) != 'GND': poly(z.GetFilledPolysList(L), FA[L], 0.5)
def seg(t, col, w, op=1):
    o.append('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" stroke="%s" stroke-width="%.3f" stroke-linecap="round" stroke-opacity="%g"/>' % (t.GetStart().x / MM, t.GetStart().y / MM, t.GetEnd().x / MM, t.GetEnd().y / MM, col, w, op))
def arc(t, col, w, op=1):
    s, m, e = t.GetStart(), t.GetMid(), t.GetEnd(); r = t.GetRadius() / MM
    cr = (m.x - s.x) * (e.y - m.y) - (m.y - s.y) * (e.x - m.x)
    o.append('<path d="M %.3f %.3f A %.3f %.3f 0 0 %d %.3f %.3f" fill="none" stroke="%s" stroke-width="%.3f" stroke-opacity="%g"/>' % (s.x / MM, s.y / MM, r, r, 1 if cr > 0 else 0, e.x / MM, e.y / MM, col, w, op))
for f in b.GetFootprints():
    for p in f.Pads():
        L = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        poly(p.GetEffectivePolygon(L), '#ff9900' if str(p.GetNetname()) in HL else '#bbbbbb', 1 if str(p.GetNetname()) in HL else 0.6)
for L in (pcbnew.B_Cu, pcbnew.In2_Cu, pcbnew.F_Cu):
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA' or t.GetLayer() != L or str(t.GetNetname()) in HL: continue
        (arc if t.GetClass() == 'PCB_ARC' else seg)(t, FA[L], t.GetWidth() / MM, 0.9)
for L in (pcbnew.B_Cu, pcbnew.In2_Cu, pcbnew.F_Cu):
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA' or t.GetLayer() != L or str(t.GetNetname()) not in HL: continue
        (arc if t.GetClass() == 'PCB_ARC' else seg)(t, COL[L], max(t.GetWidth() / MM, 0.35))
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        hl = str(t.GetNetname()) in HL
        o.append('<circle cx="%.3f" cy="%.3f" r="%.3f" fill="%s" stroke="%s" stroke-width="%.2f"/>' % (t.GetX() / MM, t.GetY() / MM, t.GetWidth(pcbnew.F_Cu) / MM / 2, 'white' if hl else '#cccccc', 'black' if hl else '#aaaaaa', 0.15 if hl else 0.05))
for f in b.GetFootprints():
    if any(str(p.GetNetname()) in HL for p in f.Pads()):
        o.append('<text x="%.2f" y="%.2f" font-size="1.4" fill="black">%s</text>' % (f.GetX() / MM + 1, f.GetY() / MM - 1, f.GetReference()))
o.append('</svg>'); open(out, 'w').write('\n'.join(o))
