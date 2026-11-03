"""v15 wiring check: per wire, the nearest other bodies (exact distToShape with a 6 mm box prefilter; zero distances are
cross-checked with the fuse volume because distToShape is unreliable on toroidal sweeps). Writes CAD_OUT/work/wires.json.
Run: CAD_OUT=... freecadcmd wire_check.py"""
import os, json, Part
from FreeCAD import Vector as V
OUT = os.environ.get('CAD_OUT', '/home/chithi/Desktop/DesktopSpeaker/ai-files/cad/v15/').rstrip('/') + '/'
W = OUT + 'work/'
m = json.load(open(W + 'meta.json'))
S = {o['name']: (o, Part.read(W + 'brep/' + o['file'])) for o in m['objs']}
own = lambda w, n: n.split('_')[0] in ('Housing', 'Crimp', 'Sleeve', 'Solder') and w.split('_')[1] in n
res = []
for w in [n for n in S if n.startswith('Wire_')]:
    sw = S[w][1]; bb = sw.BoundBox; bb.enlarge(4.0)
    near = []
    for n, (o, s) in S.items():
        if n == w or own(w, n) or not bb.intersect(s.BoundBox):
            continue
        if o['group'] == 'pcb_parts' and w.split('_')[1] in n:     # its own header
            continue
        try:
            if len(s.Faces) > 40:     # clip big/complex bodies to the wire neighbourhood first (distToShape on them is slow)
                cb = sw.BoundBox; cb.enlarge(4.5)        # local piece of the big bodies only (distToShape on the whole shell is slow)
                s = s.common(Part.makeBox(cb.XLength, cb.YLength, cb.ZLength, V(cb.XMin, cb.YMin, cb.ZMin)))
                if s.isNull() or s.Volume < 1e-6:
                    continue
            d = sw.distToShape(s)[0]
        except Exception:
            continue
        if d < 1e-3:
            try:
                ov = sw.Volume + s.Volume - sw.fuse(s).Volume
            except Exception:
                ov = -1
            near.append((round(d, 3), n, round(ov, 3)))
        elif d < 4.0:
            near.append((round(d, 2), n, None))
    near.sort()
    wi = [x for x in m.get('wiring', []) if x['name'] == w]
    res.append(dict(wire=w, length_mm=wi[0]['length_mm'] if wi else None, nearest=near[:6]))
json.dump(res, open(W + 'wires.json', 'w'), indent=1)
for r in res:
    print('WIRE', r['wire'], r['length_mm'], r['nearest'][:3])
