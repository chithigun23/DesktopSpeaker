#!/usr/bin/env python3
"""mkj10.py DRC.json GEO.json TAG NETREGEX [--layers FBI] [--margin 4] [--extra k=v,...] [--rev] : RT-10 job files for hr10.py,
one per unconnected DRC item whose net matches NETREGEX (t/j_TAG_k.json -> plan t/p_TAG_k.json). from = first item
(pad REF-NUM or a point on the track), to = NET with tgt_near at the second item (r 0.6)."""
import sys, json, re
a = sys.argv; drc, geo, tag, rx = a[1:5]
LAY = a[a.index('--layers') + 1] if '--layers' in a else 'FBI'
MG = float(a[a.index('--margin') + 1]) if '--margin' in a else 4.0
EX = {}
if '--extra' in a:
    for kv in a[a.index('--extra') + 1].split(','):
        k, v = kv.split('='); EX[k] = json.loads(v)
D = json.load(open(drc)); n = 0; out = []
def ep(i):
    d = i['description']; m = re.match(r'(?:PTH )?[Pp]ad (\S+) \[(.*?)\] of (\S+)', d)
    if m: return m.group(3) + '-' + m.group(1), m.group(2)
    m = re.match(r"Track \[(.*?)\] on ([^, ]+)", d)
    return [i['pos']['x'], i['pos']['y'], m.group(2), 0.12], m.group(1)
for u in D['unconnected_items']:
    A, B = u['items']; ea, net = ep(A); eb, _ = ep(B)
    if not re.search(rx, net): continue
    if '--rev' in a: ea, eb, A, B = eb, ea, B, A
    j = dict(net=net, to='NET', tgt_radius=200.0, neck_drc=True, fine_via=True, layers=LAY, via_cost=1.5, max_exp=5e6,
             max_cells=9000000, margin=MG, run=0.75)
    j['from'] = ea; j['tgt_near'] = [B['pos']['x'], B['pos']['y'], 0.6]
    j.update(EX)
    f = 't/j_%s_%d.json' % (tag, n)
    json.dump(dict(geo=geo, out_plan='t/p_%s_%d.json' % (tag, n), jobs=[j]), open(f, 'w'))
    out.append(f); n += 1
print(' '.join(out))
