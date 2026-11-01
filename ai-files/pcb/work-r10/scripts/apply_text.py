#!/usr/bin/env python3
"""apply_text.py SRC.kicad_pcb PLAN.json OUT.kicad_pcb : text-level placement edit (no pcbnew; plain python3).
PLAN keys:
  poses   {ref: [x, y, rot]}         new absolute footprint pose. On a rotation change, every pad angle in the footprint
                                     gets the same delta (pad angles are absolute in the file); text angles are kept (upright).
  seg_set {uuid-prefix: [x1, y1, x2, y2]}  new end points of an existing segment
  seg_del [uuid-prefix]              delete segments
  seg_add [[layer, net, width, x1, y1, x2, y2]]
  via_set {uuid-prefix: [x, y]}      move a via
  texts   {board text: [x, y, justify]}  move a board-level silkscreen text (TP net-name labels follow their TPs)
  td_clear_r  mm (default 0.8)       teardrop zones with a point within this distance of an old/new pad or edited copper are removed
Prints a report of every change."""
import sys, re, json, math, uuid
src, planf, out = sys.argv[1:4]
PL = json.load(open(planf))
lines = open(src, encoding='utf-8').read().split('\n')
# top-level blocks
blocks = []; i = 0
while i < len(lines):
    L = lines[i]
    if L.startswith('\t(') and not L.startswith('\t\t'):
        if L.count('(') == L.count(')'): blocks.append([i, i]); i += 1; continue
        j = i + 1
        while lines[j] != '\t)': j += 1
        blocks.append([i, j]); i = j + 1; continue
    i += 1
def btext(b): return lines[b[0]:b[1] + 1]
rep = dict(poses=[], seg_set=[], seg_del=[], seg_add=0, via_set=[], td_removed=0)
hot = []   # points whose neighbourhood loses teardrops
num = r'(-?[\d.]+)'
def fmt(v):
    s = ('%.6f' % v).rstrip('0').rstrip('.'); return '0' if s in ('-0', '') else s
def normang(a):
    a = (a + 180) % 360 - 180
    return 180.0 if abs(a + 180) < 1e-9 else a
newlines = {}; dele = set(); adds = []
for b in blocks:
    head = lines[b[0]]
    if head.startswith('\t(footprint'):
        T = btext(b); ref = None
        for L in T:
            m = re.match(r'\t\t\(property "Reference" "([^"]+)"', L)
            if m: ref = m.group(1); break
        if ref not in PL.get('poses', {}): continue
        nx, ny, nr = PL['poses'][ref]
        for k in range(b[0], b[1] + 1):
            m = re.match(r'^\t\t\(at ' + num + ' ' + num + r'(?: ' + num + r')?\)$', lines[k])
            if m:
                ox, oy, orr = float(m.group(1)), float(m.group(2)), float(m.group(3) or 0); atk = k; break
        d = normang(nr - orr)
        newlines[atk] = '\t\t(at %s %s%s)' % (fmt(nx), fmt(ny), '' if abs(normang(nr)) < 1e-9 else ' ' + fmt(normang(nr)))
        # pads: old absolute centres for teardrop clean-up, rotate pad angles
        cur = None; npad = 0
        for k in range(b[0], b[1] + 1):
            L = lines[k]
            if L.startswith('\t\t(') and not L.startswith('\t\t\t'): cur = L.strip().split(' ')[0]
            m = re.match(r'^\t\t\t\(at ' + num + ' ' + num + r'(?: ' + num + r')?\)$', L)
            if m and cur == '(pad':
                px, py, pa = float(m.group(1)), float(m.group(2)), float(m.group(3) or 0)
                r0 = math.radians(orr); c, s = math.cos(r0), math.sin(r0)
                hot.append((ox + px * c + py * s, oy - px * s + py * c))
                r1 = math.radians(nr); c, s = math.cos(r1), math.sin(r1)
                hot.append((nx + px * c + py * s, ny - px * s + py * c))
                if abs(d) > 1e-9:
                    na = normang(pa + d)
                    newlines[k] = '\t\t\t(at %s %s%s)' % (fmt(px), fmt(py), '' if abs(na) < 1e-9 else ' ' + fmt(na))
                npad += 1
        rep['poses'].append([ref, ox, oy, orr, nx, ny, nr, npad])
    elif head.startswith('\t(segment'):
        T = btext(b); u = re.search(r'\(uuid "([^"]+)"\)', '\n'.join(T)).group(1)
        for key, v in PL.get('seg_set', {}).items():
            if u.startswith(key):
                for k in range(b[0], b[1] + 1):
                    m = re.match(r'^\t\t\(start ' + num + ' ' + num + r'\)$', lines[k])
                    if m: hot.append((float(m.group(1)), float(m.group(2)))); newlines[k] = '\t\t(start %s %s)' % (fmt(v[0]), fmt(v[1]))
                    m = re.match(r'^\t\t\(end ' + num + ' ' + num + r'\)$', lines[k])
                    if m: hot.append((float(m.group(1)), float(m.group(2)))); newlines[k] = '\t\t(end %s %s)' % (fmt(v[2]), fmt(v[3]))
                hot += [(v[0], v[1]), (v[2], v[3])]; rep['seg_set'].append([u, v])
        for key in PL.get('seg_del', []):
            if u.startswith(key):
                for k in range(b[0], b[1] + 1):
                    m = re.match(r'^\t\t\((?:start|end) ' + num + ' ' + num + r'\)$', lines[k])
                    if m: hot.append((float(m.group(1)), float(m.group(2))))
                dele.update(range(b[0], b[1] + 1)); rep['seg_del'].append(u)
    elif head.startswith('\t(gr_text'):
        m = re.match(r'^\t\(gr_text "([^"]*)"', head)
        if m and m.group(1) in PL.get('texts', {}):
            x, y, just = PL['texts'][m.group(1)]
            for k in range(b[0], b[1] + 1):
                mm = re.match(r'^\t\t\(at ' + num + ' ' + num + r'(?: ' + num + r')?\)$', lines[k])
                if mm: old = (mm.group(1), mm.group(2)); newlines[k] = '\t\t(at %s %s%s)' % (fmt(x), fmt(y), ' ' + mm.group(3) if mm.group(3) else '')
                if re.match(r'^\t\t\t\(justify ', lines[k]): newlines[k] = '\t\t\t(justify %s)' % just
            rep.setdefault('texts', []).append([m.group(1), old, [x, y, just]])
    elif head.startswith('\t(via'):
        T = btext(b); u = re.search(r'\(uuid "([^"]+)"\)', '\n'.join(T)).group(1)
        for key, v in PL.get('via_set', {}).items():
            if u.startswith(key):
                for k in range(b[0], b[1] + 1):
                    m = re.match(r'^\t\t\(at ' + num + ' ' + num + r'\)$', lines[k])
                    if m: hot.append((float(m.group(1)), float(m.group(2)))); newlines[k] = '\t\t(at %s %s)' % (fmt(v[0]), fmt(v[1]))
                hot.append(tuple(v)); rep['via_set'].append([u, v])
# teardrop zones near hot points
R = PL.get('td_clear_r', 0.8)
for b in blocks:
    if not lines[b[0]].startswith('\t(zone'): continue
    T = '\n'.join(btext(b))
    if '(teardrop' not in T: continue
    pts = [(float(a), float(c)) for a, c in re.findall(r'\(xy ' + num + ' ' + num + r'\)', T)]
    if any(math.hypot(px - hx, py - hy) < R for px, py in pts for hx, hy in hot):
        dele.update(range(b[0], b[1] + 1)); rep['td_removed'] += 1
for a in PL.get('seg_add', []):
    layer, net, w, x1, y1, x2, y2 = a
    adds += ['\t(segment', '\t\t(start %s %s)' % (fmt(x1), fmt(y1)), '\t\t(end %s %s)' % (fmt(x2), fmt(y2)), '\t\t(width %s)' % fmt(w),
             '\t\t(layer "%s")' % layer, '\t\t(net "%s")' % net, '\t\t(uuid "%s")' % uuid.uuid4(), '\t)']
    rep['seg_add'] += 1
res = []
first_seg = next(b[0] for b in blocks if lines[b[0]].startswith('\t(segment'))
for k, L in enumerate(lines):
    if k == first_seg: res += adds
    if k in dele: continue
    res.append(newlines.get(k, L))
open(out, 'w', encoding='utf-8').write('\n'.join(res))
print(json.dumps(rep, indent=0))
