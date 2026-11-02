#!/usr/bin/env python3
"""freemap.py GEO.json X0 Y0 X1 Y1 OUT.png --net NET [--w 0.25] [--plan PLAN.json] [--px 1600] [--mark x,y;...]
RT-9 helper (venv python, shapely). Draws, for net NET, where a track CENTRE line of width w may lie on F, B and In2
(green = free) and where a 0.6 mm via centre may lie (yellow dots = free through all layers). Clearances: 0.2 default,
0.5 to AUDIO tracks/vias, 0.4 to I2S_CLK and POWER_HI tracks/vias, 0.3 PVDD, 1.0 SWITCH, 0.25 to holes, 0.6 halo to
sensitive tracks (AUDIO/I2S/USB, AUD_SDA/SCL); GND pours yield on F/B; on In2 GND yields, other zones 0.3.
--plan applies seg_del (uuid prefixes) and seg_add/via_add of an edit plan to the model (deleted vias by via_del_xy)."""
import sys, json, argparse, subprocess, os
import shapely
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

ap = argparse.ArgumentParser()
ap.add_argument('geo'); ap.add_argument('x0', type=float); ap.add_argument('y0', type=float); ap.add_argument('x1', type=float); ap.add_argument('y1', type=float)
ap.add_argument('out'); ap.add_argument('--net', required=True); ap.add_argument('--w', type=float, default=0.25)
ap.add_argument('--plan'); ap.add_argument('--px', type=int, default=1600); ap.add_argument('--mark', default='')
ap.add_argument('--sens', action='store_true', help='net is sensitive (halo vs all signal tracks)')
ap.add_argument('--only', default='F,B,In2')
a = ap.parse_args()
D = json.load(open(a.geo))
X0, Y0, X1, Y1 = a.x0, a.y0, a.x1, a.y1
WIN = box(X0 - 2, Y0 - 2, X1 + 2, Y1 + 2)
SENS = {'AUDIO', 'I2S_CLK', 'USB'}; SN = {'/AUD_SDA', '/AUD_SCL'}
SIG = {'Default', 'SIGNAL', 'I2C', 'AUDIO', 'I2S_CLK', 'USB'}


def clr(cls, typ):
    if typ == 'Pad': return 0.2 if cls != 'SWITCH' else 1.0
    return {'AUDIO': 0.5, 'I2S_CLK': 0.4, 'POWER_HI': 0.4, 'PVDD': 0.3, 'SPK_OUT': 0.3, 'SWITCH': 1.0}.get(cls, 0.2)


def mk(plist):
    out = []
    for rings in plist:
        if len(rings[0]) < 3: continue
        p = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 3])
        if not p.is_valid: p = p.buffer(0)
        out.append(p)
    return unary_union(out) if out else None


tracks = [t for t in D['tracks']]
vias = [v for v in D['vias']]
if a.plan:
    P = json.load(open(a.plan))
    dl = P.get('seg_del', [])
    tracks = [t for t in tracks if not any(t['uuid'].startswith(u) for u in dl)]
    gone = [tuple(v) for v in P.get('via_del_xy', [])]
    vias = [v for v in vias if not any(abs(v['x'] - x) < 1e-3 and abs(v['y'] - y) < 1e-3 for x, y in gone)]
    ncls = {}
    for p in D['pads']: ncls[p['net']] = p['cls']
    for t in D['tracks']: ncls[t['net']] = t['cls']
    for s in P.get('seg_add', []):
        tracks.append(dict(x1=s[3], y1=s[4], x2=s[5], y2=s[6], w=s[2], layer=s[0], net=s[1], cls=ncls.get(s[1], 'Default'), arc=False, poly=None, uuid='new'))
    for v in P.get('via_add', []):
        vias.append(dict(x=v[1], y=v[2], d=v[3], drill=v[4], net=v[0], cls=ncls.get(v[0], 'Default')))
w = a.w; NET = a.net
LAY = ['F.Cu', 'B.Cu', 'In2.Cu']
blk = {L: [] for L in LAY}; vblk = []
holes = []
for p in D['pads']:
    if not WIN.intersects(Point(p['x'], p['y']).buffer(4)): continue
    for L, pl in p['poly'].items():
        g = mk(pl)
        if g is None: continue
        if L in LAY and p['net'] != NET:
            blk[L].append(g.buffer(clr(p['cls'], 'Pad') + w / 2))
        if p['net'] != NET and L in ('F.Cu', 'B.Cu', 'In1.Cu', 'In2.Cu'): vblk.append(g.buffer(0.2 + 0.3))
    if p['drill']:
        holes.append(Point(p['x'], p['y']).buffer(max(p['drill']) / 2))
for t in tracks:
    if t['layer'] not in LAY and t['layer'] != 'In1.Cu': continue
    g = mk(t['poly']) if t['arc'] and t['poly'] else LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]).buffer(t['w'] / 2, 8)
    if not WIN.intersects(g) or t['net'] == NET: continue
    c = clr(t['cls'], 'Track')
    if t['layer'] in LAY:
        blk[t['layer']].append(g.buffer(c + w / 2))
        sens_o = t['cls'] in SENS or t['net'] in SN
        if (not a.sens and sens_o) or (a.sens and t['cls'] in SIG):
            blk[t['layer']].append(g.buffer(0.6 + w / 2))
    vblk.append(g.buffer(c + 0.3))
for v in vias:
    g = Point(v['x'], v['y']).buffer(v['d'] / 2, 12)
    if not WIN.intersects(g): continue
    holes.append(Point(v['x'], v['y']).buffer(v['drill'] / 2))
    if v['net'] == NET: continue
    c = clr(v['cls'], 'Via')
    for L in LAY: blk[L].append(g.buffer(c + w / 2))
    vblk.append(g.buffer(c + 0.3))
for z in D['zones']:
    if z['net'] in (NET, 'GND', '') : continue
    for L, pls in z['fills'].items():
        if L not in LAY and L != 'In1.Cu': continue
        g = mk(pls)
        if g is None or not WIN.intersects(g): continue
        c = 0.3 if L == 'In2.Cu' else clr(z['cls'], 'Zone')
        if L in LAY: blk[L].append(g.buffer(c + w / 2))
        vblk.append(g.buffer(c + 0.3))
for h in holes:
    for L in LAY: blk[L].append(h.buffer(0.25 + w / 2))
    vblk.append(h.buffer(0.25 + 0.3))
# keep-out areas (rule areas with no_tracks / no_vias, BKO on B.Cu)
for ar in D['areas']:
    g = mk(ar['outline'])
    if g is None or not WIN.intersects(g): continue
    for L in LAY:
        if L in ar['layers'] and ar['no_tracks']: blk[L].append(g.buffer(w / 2))
    if ar['no_vias']: vblk.append(g.buffer(0.3))
    if ar['name'].startswith('BKO_'): blk['B.Cu'].append(g.buffer(w / 2))
edge = D['outline']
win = box(X0, Y0, X1, Y1)
free = {L: win.difference(unary_union(blk[L])) for L in LAY}
vfree = win.difference(unary_union(vblk))
# draw
sc = a.px / (X1 - X0); H = int((Y1 - Y0) * sc)


def path(g):
    s = ''
    geoms = getattr(g, 'geoms', [g])
    for p in geoms:
        if p.is_empty or p.geom_type != 'Polygon': continue
        for r in [p.exterior] + list(p.interiors):
            s += 'M' + ' L'.join('%.3f %.3f' % c for c in r.coords) + ' Z '
    return s


DL = ['%s.Cu' % q for q in a.only.split(',')]
N = len(DL)
out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="%f %f %f %f" style="background:#fff">' % (a.px * N + 20 * (N - 1), H, X0, Y0, N * (X1 - X0) + 20 * (N - 1) / sc, Y1 - Y0)]
COL = {'F.Cu': '#d22', 'B.Cu': '#26d', 'In2.Cu': '#a5a'}
for k, L in enumerate(DL):
    dx = k * ((X1 - X0) + 20 / sc)
    out.append('<g transform="translate(%f,0)">' % dx)
    out.append('<path d="%s" fill="#bfeabf" fill-rule="evenodd"/>' % path(free[L]))
    # copper of this layer, outlines
    for t in tracks:
        if t['layer'] != L or t['arc']: continue
        if not (min(t['x1'], t['x2']) < X1 + 1 and max(t['x1'], t['x2']) > X0 - 1 and min(t['y1'], t['y2']) < Y1 + 1 and max(t['y1'], t['y2']) > Y0 - 1): continue
        col = '#0a0' if t['net'] == NET else COL[L]
        out.append('<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="%s" stroke-opacity="0.45" stroke-width="%f" stroke-linecap="round"/>' % (t['x1'], t['y1'], t['x2'], t['y2'], col, t['w']))
    for p in D['pads']:
        if L not in p['poly'] or not (X0 - 2 < p['x'] < X1 + 2 and Y0 - 2 < p['y'] < Y1 + 2): continue
        g = mk(p['poly'][L])
        if g is None: continue
        out.append('<path d="%s" fill="%s" fill-opacity="0.35"/>' % (path(g), '#0a0' if p['net'] == NET else '#c80'))
        out.append('<text x="%f" y="%f" font-size="%f" fill="#000">%s-%s</text>' % (p['x'] - 0.3, p['y'] + 0.1, 0.25, p['ref'], p['num']))
    for v in vias:
        if X0 - 1 < v['x'] < X1 + 1 and Y0 - 1 < v['y'] < Y1 + 1:
            out.append('<circle cx="%f" cy="%f" r="%f" fill="%s" fill-opacity="0.6"/>' % (v['x'], v['y'], v['d'] / 2, '#0a0' if v['net'] == NET else '#555'))
    if L == 'F.Cu':
        out.append('<path d="%s" fill="#ff0" fill-opacity="0.8" fill-rule="evenodd"/>' % path(vfree))
    # grid every 1 mm with labels
    x = int(X0) + 1
    while x < X1:
        out.append('<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="#999" stroke-width="%f"/>' % (x, Y0, x, Y1, 0.5 / sc))
        out.append('<text x="%f" y="%f" font-size="%f" fill="#666">%d</text>' % (x + 0.05, Y0 + 0.35, 0.3, x)); x += 1
    y = int(Y0) + 1
    while y < Y1:
        out.append('<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="#999" stroke-width="%f"/>' % (X0, y, X1, y, 0.5 / sc))
        out.append('<text x="%f" y="%f" font-size="%f" fill="#666">%d</text>' % (X0 + 0.05, y - 0.05, 0.3, y)); y += 1
    out.append('<text x="%f" y="%f" font-size="%f" fill="#000">%s %s w%.2f</text>' % (X0 + 0.5, Y1 - 0.3, 0.5, L, NET, w))
    for m in [q for q in a.mark.split(';') if q]:
        mx, my = map(float, m.split(','))
        out.append('<circle cx="%f" cy="%f" r="0.15" fill="none" stroke="#f0f" stroke-width="0.05"/>' % (mx, my))
    out.append('</g>')
out.append('</svg>')
svg = a.out.replace('.png', '.svg')
open(svg, 'w').write('\n'.join(out))
htm = a.out.replace('.png', '.html')
open(htm, 'w').write('<html><body style="margin:0"><img src="%s"></body></html>' % os.path.basename(svg))
subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars', '--screenshot=%s' % os.path.abspath(a.out),
                '--window-size=%d,%d' % (a.px * N + 20 * (N - 1), H), 'file://' + os.path.abspath(htm)], capture_output=True)
os.remove(htm)
print('wrote', a.out)
