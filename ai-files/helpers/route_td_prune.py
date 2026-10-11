"""flatpak: route_td_prune.py IN.kicad_pcb OUT.kicad_pcb [DRC.json] [--maxiter N] :
remove only the teardrop zones that take part in DRC violations, until DRC shows no teardrop-related violation.
Loop: refill all zones, save OUT (+ IN's .kicad_pro/.kicad_dru copied next to it), kicad-cli DRC (json, all severities, mm),
delete every teardrop zone that is an item of a violation (matched by uuid; fallback: same net + layer and the reported position
inside the teardrop outline or within 0.05 mm of it). An optional first DRC.json is used for iteration 1 (it must belong to IN).
Stops when no violation involves a teardrop. Prints per iteration: violations by type, teardrops removed, teardrops remaining;
at the end the remaining non-teardrop violations (not touched by this script) and OUT.drc.json."""
import sys, os, json, shutil, subprocess, collections, pcbnew
MM = 1e6
a = [x for x in sys.argv[1:] if not x.startswith('--')]
IN, OUT = a[0], a[1]; first = a[2] if len(a) > 2 else None
maxit = int(sys.argv[sys.argv.index('--maxiter') + 1]) if '--maxiter' in sys.argv else 12
si, so = IN[:-10], OUT[:-10]
b = pcbnew.LoadBoard(IN)
LN = {'F.Cu': pcbnew.F_Cu, 'In1.Cu': pcbnew.In1_Cu, 'In2.Cu': pcbnew.In2_Cu, 'B.Cu': pcbnew.B_Cu}
def tds(): return [z for z in b.Zones() if z.IsTeardropArea()]
def save():
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(OUT)
    for e in ('.kicad_pro', '.kicad_dru'):
        if os.path.exists(si + e) and os.path.abspath(si + e) != os.path.abspath(so + e): shutil.copy(si + e, so + e)
def drc(path):
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all', '--units', 'mm', '-o', path, OUT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return json.load(open(path))
def match(item, by_uuid, T):
    z = by_uuid.get(item.get('uuid'))
    if z is not None: return z
    d = item['description']
    if not d.startswith('Teardrop'): return None
    try: net = d.split('[', 1)[1].split(']', 1)[0]; lay = LN.get(d.rsplit(' on ', 1)[1].strip())
    except Exception: return None
    p = pcbnew.VECTOR2I(int(round(item['pos']['x'] * MM)), int(round(item['pos']['y'] * MM)))
    for z in T:
        if str(z.GetNetname()) == net and (lay is None or z.IsOnLayer(lay)) and z.Outline().Collide(p, int(0.05 * MM)): return z
    return None
print('teardrops at start', len(tds()))
tot = 0
for it in range(1, maxit + 1):
    if it == 1 and first: d = json.load(open(first)); save()
    else: save(); d = drc(so + '.drc.json')
    T = tds(); by_uuid = {str(z.m_Uuid.AsString()): z for z in T}
    hit = {}; other = collections.Counter(); kinds = collections.Counter(x['type'] for x in d['violations'])
    for x in d['violations']:
        zs = [match(i, by_uuid, T) for i in x['items']]; zs = [z for z in zs if z is not None]
        if zs:
            for z in zs: hit[str(z.m_Uuid.AsString())] = z
        else: other[x['type']] += 1
    for z in hit.values(): b.RemoveNative(z)
    tot += len(hit)
    print('iter %d: violations %d %s, unconnected %d; teardrops removed %d, remaining %d; non-teardrop violations %s' % (it, len(d['violations']), dict(kinds), len(d['unconnected_items']), len(hit), len(tds()), dict(other)))
    if not hit: break
save(); d = drc(so + '.drc.json')
k = collections.Counter(x['type'] for x in d['violations'])
print('FINAL teardrops remaining %d (removed %d); DRC violations %d %s, unconnected %d -> %s' % (len(tds()), tot, len(d['violations']), dict(k), len(d['unconnected_items']), so + '.drc.json'))
for x in d['violations'][:30]: print('  ', x['type'], x['description'][:80], [(i['description'][:45], i['pos']['x'], i['pos']['y']) for i in x['items']])
