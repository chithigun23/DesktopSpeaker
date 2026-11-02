#!/usr/bin/env python3
"""edit.py SRC.kicad_pcb PLAN.json OUT.kicad_pcb [REPORT.json] : text-level copper editor (no pcbnew, plain python3).
PLAN keys (every uuid key is a unique prefix; an op that matches 0 or >1 items aborts):
  seg_del  [uuid]                          delete segments
  seg_set  {uuid: [x1, y1, x2, y2]}        new end points of a segment
  seg_add  [[layer, net, w, x1, y1, x2, y2]]
  via_del  [uuid]
  via_set  {uuid: [x, y]}
  via_add  [[net, x, y, size, drill]]      through via F.Cu-B.Cu
  zone_pts {uuid: [[x, y], ...]}           replace a zone outline (fill is redone by the separate refill process)
  td_clear_r  mm (default 0.8): teardrop zones with a vertex within this distance of edited copper are removed
Writes a JSON report of every change (old and new coordinates)."""
import sys, json, math, uuid as U
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pcbtext import read, items, fmt

src, planf, out = sys.argv[1:4]
PL = json.load(open(planf))
lines = read(src)
IT = items(src, lines)
rep = dict(src=src, plan=planf, seg_del=[], seg_set=[], seg_add=[], via_del=[], via_set=[], via_add=[], zone_pts=[], td_removed=[])
hot = []
newl, dele, adds = {}, set(), []


def one(kind, key):
    m = [d for d in IT if d['kind'] == kind and d.get('uuid', '').startswith(key)]
    if len(m) != 1: sys.exit('ABORT: %s %s matches %d' % (kind, key, len(m)))
    return m[0]


def setline(d, tag, v):
    for k in range(d['i0'], d['i1'] + 1):
        L = lines[k]
        if L.startswith('\t\t(%s ' % tag):
            newl[k] = '\t\t(%s %s %s)' % (tag, fmt(v[0]), fmt(v[1])); return
    sys.exit('ABORT: no %s line in %s' % (tag, d.get('uuid')))


for key in PL.get('seg_del', []):
    d = one('segment', key); dele.update(range(d['i0'], d['i1'] + 1)); hot += [d['start'], d['end']]
    rep['seg_del'].append([d['uuid'], d['net'], d['layer'], d['width'], *d['start'], *d['end']])
for key in PL.get('arc_del', []):      # RT-8: delete an arc
    d = one('arc', key); dele.update(range(d['i0'], d['i1'] + 1)); hot += [d['start'], d['end']]
    rep.setdefault('arc_del', []).append([d['uuid'], d['net'], d['layer'], d['width'], *d['start'], *d['end'], *d.get('mid', (0, 0))])
for key, v in PL.get('seg_set', {}).items():
    d = one('segment', key); setline(d, 'start', v[:2]); setline(d, 'end', v[2:]); hot += [d['start'], d['end'], tuple(v[:2]), tuple(v[2:])]
    rep['seg_set'].append([d['uuid'], d['net'], d['layer'], d['width'], [*d['start'], *d['end']], v])
for key in PL.get('via_del', []):
    d = one('via', key); dele.update(range(d['i0'], d['i1'] + 1)); hot.append(d['at'])
    rep['via_del'].append([d['uuid'], d['net'], *d['at'], d['size'], d['drill']])
for key, v in PL.get('via_set', {}).items():
    d = one('via', key); setline(d, 'at', v); hot += [d['at'], tuple(v)]
    rep['via_set'].append([d['uuid'], d['net'], list(d['at']), v])
for key, pts in PL.get('zone_pts', {}).items():
    d = one('zone', key); a, b = d['poly_lines']
    body = ['\t\t(polygon', '\t\t\t(pts']
    for i in range(0, len(pts), 6):
        body.append('\t\t\t\t' + ' '.join('(xy %s %s)' % (fmt(x), fmt(y)) for x, y in pts[i:i + 6]))
    body += ['\t\t\t)', '\t\t)']
    newl[a] = '\n'.join(body); dele.update(range(a + 1, b + 1))
    rep['zone_pts'].append([d['uuid'], d.get('name'), d.get('net'), d.get('layer'), d['pts'], pts])
    hot += [tuple(p) for p in pts]
for a in PL.get('seg_add', []):
    layer, net, w, x1, y1, x2, y2 = a; u = str(U.uuid4())
    adds += ['\t(segment', '\t\t(start %s %s)' % (fmt(x1), fmt(y1)), '\t\t(end %s %s)' % (fmt(x2), fmt(y2)), '\t\t(width %s)' % fmt(w),
             '\t\t(layer "%s")' % layer, '\t\t(net "%s")' % net, '\t\t(uuid "%s")' % u, '\t)']
    rep['seg_add'].append([u, *a]); hot += [(x1, y1), (x2, y2)]
for a in PL.get('via_add', []):
    net, x, y, s, dr = a; u = str(U.uuid4())
    adds += ['\t(via', '\t\t(at %s %s)' % (fmt(x), fmt(y)), '\t\t(size %s)' % fmt(s), '\t\t(drill %s)' % fmt(dr),
             '\t\t(layers "F.Cu" "B.Cu")', '\t\t(net "%s")' % net, '\t\t(uuid "%s")' % u, '\t)']
    rep['via_add'].append([u, *a]); hot.append((x, y))
rep['fp_move'] = []
for ref, v in PL.get('fp_move', {}).items():
    fb = [d for d in items(src, lines, kinds=('footprint',)) if any(lines[k].strip() == '(property "Reference" "%s"' % ref for k in range(d['i0'], d['i1'] + 1))]
    if len(fb) != 1: sys.exit('ABORT: footprint %s matches %d' % (ref, len(fb)))
    d = fb[0]
    k = next(k for k in range(d['i0'], d['i1'] + 1) if lines[k].startswith('\t\t(at '))
    old = lines[k].strip()[4:-1].split()
    r0 = float(old[2]) if len(old) > 2 else 0.0
    r1 = float(v[2]) if len(v) > 2 else r0
    newl[k] = '\t\t(at %s %s%s)' % (fmt(v[0]), fmt(v[1]), (' ' + fmt(r1)) if r1 != 0 else '')
    if r1 != r0:   # pad orientations in the board file are absolute: add the rotation change to every pad (at x y rot)
        inpad = False
        for kk in range(d['i0'], d['i1'] + 1):
            L2 = lines[kk]
            if L2.startswith('\t\t(pad '): inpad = True
            elif L2.startswith('\t\t(') or L2 == '\t\t)': inpad = inpad and L2 == '\t\t)' and False
            if inpad and L2.startswith('\t\t\t(at '):
                q = L2.strip()[4:-1].split(); pr = (float(q[2]) if len(q) > 2 else 0.0) + (r1 - r0)
                pr = pr % 360
                newl[kk] = '\t\t\t(at %s %s%s)' % (q[0], q[1], (' ' + fmt(pr)) if abs(pr) > 1e-9 else '')
    hot += [(float(old[0]), float(old[1])), tuple(v[:2])]
    rep['fp_move'].append([ref, [float(old[0]), float(old[1])], v])
R = PL.get('td_clear_r', 0.8)
for d in IT:
    if d['kind'] != 'zone' or not d.get('teardrop'): continue
    if any(math.hypot(px - hx, py - hy) < R for px, py in d['pts'] for hx, hy in hot):
        dele.update(range(d['i0'], d['i1'] + 1)); rep['td_removed'].append(d.get('uuid', '?'))
first = next(d['i0'] for d in IT if d['kind'] == 'segment')
res = []
for k, L in enumerate(lines):
    if k == first: res += adds
    if k in dele and k not in newl: continue
    res.append(newl.get(k, L))
open(out, 'w', encoding='utf-8').write('\n'.join(res))
rf = sys.argv[4] if len(sys.argv) > 4 else out.replace('.kicad_pcb', '.edit.json')
json.dump(rep, open(rf, 'w'), indent=1)
print('edit:', {k: len(v) for k, v in rep.items() if isinstance(v, list)})
