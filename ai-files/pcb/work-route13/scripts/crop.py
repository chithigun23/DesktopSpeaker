#!/usr/bin/env python3
"""crop.py GEO.json X0 Y0 X1 Y1 OUT.png [--layers F,B] [--labels] [--px 1400] [--mark x,y;x,y]
SVG crop of the board geometry (zones fills, tracks, vias, pads, areas) rendered with headless chrome. Layers drawn
in order: In2 (faint), B, F. Pad/track net labels with --labels."""
import sys, json, subprocess, os, argparse, html

ap = argparse.ArgumentParser()
ap.add_argument('geo'); ap.add_argument('x0', type=float); ap.add_argument('y0', type=float); ap.add_argument('x1', type=float); ap.add_argument('y1', type=float)
ap.add_argument('out'); ap.add_argument('--layers', default='In2,B,F'); ap.add_argument('--labels', action='store_true'); ap.add_argument('--px', type=int, default=1400)
ap.add_argument('--mark', default=''); ap.add_argument('--grid', type=float, default=0.5)
a = ap.parse_args()
D = json.load(open(a.geo))
X0, Y0, X1, Y1 = a.x0, a.y0, a.x1, a.y1
W, H = X1 - X0, Y1 - Y0
sc = a.px / W
COL = {'F.Cu': '#d22', 'B.Cu': '#26d', 'In2.Cu': '#c9a', 'In1.Cu': '#9c9'}
ZOP = {'F.Cu': 0.28, 'B.Cu': 0.22, 'In2.Cu': 0.12, 'In1.Cu': 0.1}
lay = ['%s.Cu' % l for l in a.layers.split(',')]


def inb(pts, m=1.0):
    return any(X0 - m <= x <= X1 + m and Y0 - m <= y <= Y1 + m for x, y in pts)


def path(rings):
    s = ''
    for r in rings:
        s += 'M' + ' L'.join('%.3f %.3f' % (x, y) for x, y in r) + ' Z '
    return s


out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="%f %f %f %f" style="background:#fff">' % (a.px, int(H * sc), X0, Y0, W, H)]
# grid
g = a.grid
x = (int(X0 / g) + 1) * g
while x < X1:
    out.append('<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="#eee" stroke-width="%f"/>' % (x, Y0, x, Y1, 0.6 / sc)); x += g
y = (int(Y0 / g) + 1) * g
while y < Y1:
    out.append('<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="#eee" stroke-width="%f"/>' % (X0, y, X1, y, 0.6 / sc)); y += g
labels = []
for L in lay:
    for z in D['zones']:
        for pl in z['fills'].get(L, []):
            if inb(pl[0], 5):
                out.append('<path d="%s" fill="%s" fill-opacity="%.2f" fill-rule="evenodd" stroke="%s" stroke-width="%f" stroke-opacity="0.5"/>' % (path(pl), COL[L], ZOP[L], COL[L], 0.5 / sc))
    if L in ('F.Cu', 'B.Cu'):
        for t in D['tracks']:
            if t['layer'] != L or not inb([(t['x1'], t['y1']), (t['x2'], t['y2'])]): continue
            out.append('<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="%s" stroke-opacity="0.75" stroke-width="%f" stroke-linecap="round"/>' % (t['x1'], t['y1'], t['x2'], t['y2'], COL[L], t['w']))
            if a.labels and ((t['x2'] - t['x1']) ** 2 + (t['y2'] - t['y1']) ** 2) > 0.5:
                labels.append(((t['x1'] + t['x2']) / 2, (t['y1'] + t['y2']) / 2, t['net'].split('/')[-1], '#600' if L == 'F.Cu' else '#036'))
for p in D['pads']:
    for L in ('B.Cu', 'F.Cu'):
        if L not in p['poly'] or L.split('.')[0] not in a.layers: continue
        for pl in p['poly'][L]:
            if inb(pl[0]):
                out.append('<path d="%s" fill="%s" fill-opacity="0.55" stroke="#000" stroke-width="%f"/>' % (path(pl), '#e80' if L == 'F.Cu' else '#08c', 0.4 / sc))
    if p['drill'] and inb([(p['x'], p['y'])]):
        out.append('<circle cx="%f" cy="%f" r="%f" fill="#000" fill-opacity="0.6"/>' % (p['x'], p['y'], p['drill'][0] / 2))
    if inb([(p['x'], p['y'])], 0) and a.labels:
        labels.append((p['x'], p['y'], '%s-%s %s' % (p['ref'], p['num'], (p['net'] or '').split('/')[-1][:14]), '#000'))
for v in D['vias']:
    if inb([(v['x'], v['y'])]):
        out.append('<circle cx="%f" cy="%f" r="%f" fill="#888" stroke="#000" stroke-width="%f"/><circle cx="%f" cy="%f" r="%f" fill="#fff"/>' % (v['x'], v['y'], v['d'] / 2, 0.4 / sc, v['x'], v['y'], v['drill'] / 2))
        if a.labels: labels.append((v['x'], v['y'] + v['d'] / 2 + 0.1, v['net'].split('/')[-1][:12], '#444'))
for ar in D['areas']:
    for pl in ar['outline']:
        if inb(pl[0], 5):
            out.append('<path d="%s" fill="none" stroke="#0a0" stroke-dasharray="%f,%f" stroke-width="%f"/>' % (path(pl), 3 / sc, 2 / sc, 1 / sc))
            labels.append((pl[0][0][0], pl[0][0][1], ar['name'], '#070'))
fs = 9 / sc
for x, y, t, c in labels:
    if X0 <= x <= X1 and Y0 <= y <= Y1:
        out.append('<text x="%f" y="%f" font-size="%f" fill="%s" font-family="monospace" text-anchor="middle">%s</text>' % (x, y, fs, c, html.escape(t)))
for m in [s for s in a.mark.split(';') if s]:
    mx, my = map(float, m.split(','))
    out.append('<circle cx="%f" cy="%f" r="%f" fill="none" stroke="#0c0" stroke-width="%f"/>' % (mx, my, 0.15, 2 / sc))
# scale ticks
out.append('<text x="%f" y="%f" font-size="%f" fill="#000">grid %.2f mm  [%.2f,%.2f]-[%.2f,%.2f]</text>' % (X0 + 0.2, Y0 + 12 / sc, 10 / sc, g, X0, Y0, X1, Y1))
out.append('</svg>')
svg = a.out.replace('.png', '.svg')
open(svg, 'w').write('\n'.join(out))
hh = int(H * sc) + 2
htm = svg.replace('.svg', '.html')
open(htm, 'w').write('<html><body style="margin:0"><img src="%s" style="width:%dpx;display:block"></body></html>' % (os.path.basename(svg), a.px))
subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars', '--screenshot=' + os.path.abspath(a.out),
                '--window-size=%d,%d' % (a.px, hh), 'file://' + os.path.abspath(htm)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
os.remove(htm)
print('wrote', a.out)
