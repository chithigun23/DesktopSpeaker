#!/usr/bin/env python3
"""gates4.py BASE.kicad_pcb NEW.kicad_pcb OUT.json [--allow-move REF,..] [--edits E1.edit.json,E2.edit.json,...]
Independent text-level gates (no pcbnew, does not import hr.py or edit.py):
 1. footprint poses: only the allowed refs moved; pad nets of every footprint (ref, number, index) unchanged
 2. copper lock: every BASE copper item (segment/arc/via, canonical) is still present in NEW unless it is listed as deleted or changed
    in one of the edit reports; SHA-256 of the locked (untouched) set
 3. new copper: exact 0/45/90 (|dx|=|dy| or axis within 1e-4 mm) for every segment present in NEW and not in BASE
 4. non-teardrop zone outlines: unchanged except the ones listed in the edit reports"""
import sys, json, hashlib, collections, math, re
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pcbtext import items
from fplib import fps

base, new, outp = sys.argv[1:4]
allow = set(sys.argv[sys.argv.index('--allow-move') + 1].split(',')) if '--allow-move' in sys.argv else set()
edits = sys.argv[sys.argv.index('--edits') + 1].split(',') if '--edits' in sys.argv else []
r4 = lambda v: tuple(round(x, 4) for x in v)


def canon(d):
    if d['kind'] in ('segment', 'arc'):
        a, b = sorted([r4(d['start']), r4(d['end'])])
        return (d['kind'], d['net'], d['layer'], round(d['width'], 4), a, b, r4(d.get('mid', (0, 0))))
    if d['kind'] == 'via':
        return ('via', d['net'], r4(d['at']), round(d['size'], 4), round(d['drill'], 4))
    return ('zone', d.get('uuid'), d.get('net', ''), tuple(r4(p) for p in d.get('pts', [])))


IA = [d for d in items(base) if not (d['kind'] == 'zone' and d.get('teardrop'))]
IB = [d for d in items(new) if not (d['kind'] == 'zone' and d.get('teardrop'))]
CA = collections.Counter(canon(d) for d in IA); CB = collections.Counter(canon(d) for d in IB)
# items intentionally removed/changed (from the edit reports, in base coordinates)
rm = collections.Counter(); zch = set()
for e in edits:
    E = json.load(open(e))
    for s in E['seg_del']: rm[('segment', s[1], s[2], round(s[3], 4)) + tuple(sorted([r4(s[4:6]), r4(s[6:8])])) + ((0.0, 0.0),)] += 1
    for s in E['seg_set']: rm[('segment', s[1], s[2], round(s[3], 4)) + tuple(sorted([r4(s[4][:2]), r4(s[4][2:])])) + ((0.0, 0.0),)] += 1
    for v in E['via_del']: rm[('via', v[1], r4(v[2:4]), round(v[4], 4), round(v[5], 4))] += 1
    for s in E.get('arc_del', []): rm[('arc', s[1], s[2], round(s[3], 4)) + tuple(sorted([r4(s[4:6]), r4(s[6:8])])) + (r4(s[8:10]),)] += 1
    for v in E['via_set']: zch.add(('via', v[1], r4(v[2])))
    for z in E['zone_pts']: zch.add(z[0])
lost = CA - CB
unexpected = []
for k, n in lost.items():
    if k[0] == 'zone':
        if k[1] not in zch: unexpected.append(list(map(str, k[:3])))
        continue
    if k[0] == 'via' and ('via', k[1], k[2]) in zch: continue
    if rm[k] >= n: continue
    unexpected.append(list(map(str, k)))
locked = CA - lost
h = hashlib.sha256('\n'.join(sorted(repr(k) for k in locked.elements())).encode()).hexdigest()
added = CB - CA
bad = []; nseg = 0; L = 0.0
for k in added.elements():
    if k[0] != 'segment': continue
    (x1, y1), (x2, y2) = k[4], k[5]; dx, dy = abs(x2 - x1), abs(y2 - y1); nseg += 1; L += math.hypot(dx, dy)
    if not (dx < 1e-4 or dy < 1e-4 or abs(dx - dy) < 2e-4): bad.append(list(map(str, k)))

res = fps(base); resb = fps(new)
pos_a, pad_a = res[0], res[1]; pos_b, pad_b = resb[0], resb[1]
moved = sorted(r for r in pos_a if pos_a[r] != pos_b.get(r))
padd = [list(map(str, k)) for k in pad_a if pad_a[k] != pad_b.get(k)] + [list(map(str, k)) for k in pad_b if k not in pad_a]
out = dict(footprints=len(pos_a), pads=len(pad_a), moved=moved, moved_not_allowed=[r for r in moved if r not in allow], pad_net_diff=padd,
           base_copper_items=sum(CA.values()), new_copper_items=sum(CB.values()), removed_or_changed=sum(lost.values()),
           unexpected_removed=unexpected, locked_items=sum(locked.values()), locked_sha256=h,
           added_items=sum(added.values()), new_segments=nseg, new_length_mm=round(L, 3), new_not_exact=bad)
json.dump(out, open(outp, 'w'), indent=1)
for k, v in out.items():
    print(k, v if not isinstance(v, list) or len(v) < 12 else '%d items, e.g. %s' % (len(v), v[:3]))
