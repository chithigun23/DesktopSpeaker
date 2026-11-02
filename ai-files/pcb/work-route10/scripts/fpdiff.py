"""fpdiff.py A.kicad_pcb B.kicad_pcb NETFILE [--json OUT] : plain-python gates between the RT-1 base and a routed board.
1. footprint poses (ref, at x y rot, layer) and pad nets (ref, pad number, index) parsed from the saved text;
2. copper (segments/arcs/vias) of every net that the router does NOT route (power, GND, S0 template nets): must be identical,
   except GND vias added on B (stitching vias), which are listed;
3. zone outlines (non-teardrop) identical."""
import sys, re, json, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
try:
    import route_oct_lock as LK
except Exception: pass


def blocks(lines, head):
    i = 0
    while i < len(lines):
        if lines[i].startswith(head):
            j = i + 1
            while lines[j] != '\t)':
                j += 1
            yield lines[i:j + 1]; i = j + 1
        else:
            i += 1


def fps(path):
    L = open(path, encoding='utf-8').read().split('\n'); out = {}; pads = {}
    for b in blocks(L, '\t(footprint '):
        ref = next(re.search(r'"Reference" "([^"]*)"', x).group(1) for x in b if '(property "Reference"' in x)
        at = next(x.strip() for x in b if x.startswith('\t\t(at '))
        lay = next(x.strip() for x in b if x.startswith('\t\t(layer '))
        out[ref] = (at, lay)
        k = 0; cur = None
        for x in b:
            m = re.match(r'^\t\t\(pad "([^"]*)"', x)
            if m:
                cur = (ref, m.group(1), k); k += 1; pads[cur] = ''
            m = re.match(r'^\t\t\t\(net "([^"]*)"\)', x)
            if m and cur:
                pads[cur] = m.group(1)
    return out, pads


def zones(path):
    L = open(path, encoding='utf-8').read().split('\n'); out = collections.Counter()
    for b in blocks(L, '\t(zone'):
        if any('(teardrop' in x for x in b[:80]):
            continue
        txt = '\n'.join(b); txt = re.sub(r'\(filled_polygon.*', '', txt, flags=re.S)   # outline + settings only
        out[txt] += 1
    return out


a, b, nf = sys.argv[1:4]
routed = {l.split('#')[0].split()[1] for l in open(nf) if l.split('#')[0].split() and not l.startswith('S0')}
fa, pa = fps(a); fb, pb = fps(b)
pose = [r for r in fa if fa[r] != fb.get(r)] + [r for r in fb if r not in fa]
padd = [k for k in pa if pa[k] != pb.get(k)] + [k for k in pb if k not in pa]
allnets = set(re.findall(r'\(net "([^"]*)"\)', open(a, encoding='utf-8').read()))
other = sorted(allnets - routed)
ia = collections.Counter(LK.copper_items(a, other)); ib = collections.Counter(LK.copper_items(b, other))
removed = ia - ib; added = ib - ia
added_gnd_vias = [t for t in added.elements() if t[0] == 'via' and t[1] == 'GND']
added_other = [t for t in added.elements() if not (t[0] == 'via' and t[1] == 'GND')]
za, zb = zones(a), zones(b)
res = dict(footprints=len(fa), pads=len(pa), pose_diff=pose, pad_net_diff=[list(map(str, k)) for k in padd],
           nonrouted_nets=len(other), nonrouted_items_a=sum(ia.values()), nonrouted_removed=[list(t) for t in removed.elements()],
           nonrouted_added_gnd_vias=len(added_gnd_vias), nonrouted_added_other=[list(t) for t in added_other],
           zone_outlines_a=sum(za.values()), zone_outline_diff=sum((za - zb).values()) + sum((zb - za).values()))
print(json.dumps({k: (v if not isinstance(v, list) or len(v) < 8 else v[:8] + ['... %d' % len(v)]) for k, v in res.items()}, indent=1))
if '--json' in sys.argv:
    json.dump(res, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
