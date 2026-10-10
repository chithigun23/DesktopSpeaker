"""flatpak: route_r6d_edit.py IN OUT SPEC.json : explicit hand edits for R6d (net-filtered).
SPEC list items:
 {"net":N,"layer":"F|B|2","w":0.25,"pts":[[x,y],...]}            add track polyline
 {"net":N,"via":[x,y],"d":0.6,"drill":0.3}                        add via
 {"rmseg":N,"a":[x,y],"b":[x,y]}                                  remove track of net N with these endpoints (either order, 0.03 mm)
 {"rmat":N,"p":[x,y],"layer":"F"}                                 remove tracks of net N with an endpoint at p (optional layer)
 {"rmvia":N,"p":[x,y]}                                            remove via of net N at p
 {"rmbox":N,"box":[x0,y0,x1,y1],"layer":"F"}                      remove tracks/vias of net N fully inside box (optional layer, 'V' = vias only)
 {"zone":NAME,"pts":[[x,y],...]}                                  replace the outline of zone NAME
 {"zoneadd":N,"layer":"F","name":NAME,"pts":[...],"prio":P,"clr":0.3} add a filled copper zone
 {"padsize":[REF,NUM],"size":[w,h]}                               (not used)
Prints a line per edit; fails loudly if an rm matched nothing."""
import sys, json
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import pcbnew
from route_r6a_lib import trk, via, refill, full, zone, LAY, rule_area
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
def near(q, p, tol=0.03): return abs(q.x / MM - p[0]) < tol and abs(q.y / MM - p[1]) < tol
def nn(n): return full(n, b)
bad = 0
for s in json.load(open(sys.argv[3])):
    if 'rmseg' in s:
        n = nn(s['rmseg']); r = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and str(t.GetNetname()) == n and ((near(t.GetStart(), s['a']) and near(t.GetEnd(), s['b'])) or (near(t.GetStart(), s['b']) and near(t.GetEnd(), s['a'])))]
        for t in r: b.RemoveNative(t)
        print('rmseg', n, s['a'], s['b'], len(r)); bad += (len(r) == 0)
    elif 'rmat' in s:
        n = nn(s['rmat']); L = LAY.get(s.get('layer', ''), None)
        r = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and str(t.GetNetname()) == n and (L is None or t.GetLayer() == L) and (near(t.GetStart(), s['p']) or near(t.GetEnd(), s['p']))]
        for t in r: b.RemoveNative(t)
        print('rmat', n, s['p'], len(r)); bad += (len(r) == 0)
    elif 'rmvia' in s:
        n = nn(s['rmvia']); r = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and str(t.GetNetname()) == n and near(t.GetPosition(), s['p'])]
        for t in r: b.RemoveNative(t)
        print('rmvia', n, s['p'], len(r)); bad += (len(r) == 0)
    elif 'rmbox' in s:
        n = nn(s['rmbox']); x0, y0, x1, y1 = s['box']; ly = s.get('layer', '')
        def inb(q): return x0 <= q.x / MM <= x1 and y0 <= q.y / MM <= y1
        r = []
        for t in b.GetTracks():
            if str(t.GetNetname()) != n: continue
            if t.GetClass() == 'PCB_VIA':
                if ly in ('', 'V') and inb(t.GetPosition()): r.append(t)
            elif ly != 'V' and (ly == '' or t.GetLayer() == LAY[ly]) and inb(t.GetStart()) and inb(t.GetEnd()): r.append(t)
        for t in r: b.RemoveNative(t)
        print('rmbox', n, s['box'], ly, len(r)); bad += (len(r) == 0)
    elif 'zone' in s:
        zz = [z for z in b.Zones() if z.GetZoneName() == s['zone']]
        for z in zz:
            o = z.Outline(); o.RemoveAllContours(); o.NewOutline()
            for x, y in s['pts']: o.Append(int(round(x * MM)), int(round(y * MM)))
        print('zone', s['zone'], len(zz)); bad += (len(zz) == 0)
    elif 'zoneadd' in s:
        zone(b, s['zoneadd'], s['layer'], s['pts'], prio=s.get('prio', 5), clr=s.get('clr', 0.3), name=s.get('name', ''), lock=False)
        print('zoneadd', s.get('name'))
    elif 'rulearea' in s:
        rule_area(b, s['rulearea'], s['pts'], layers=s.get('layers', 'F')); print('rulearea', s['rulearea'])
    elif 'via' in s:
        via(b, s['net'], s['via'][0], s['via'][1], s.get('d', 0.6), s.get('drill', 0.3), lock=False)
    else:
        trk(b, s['net'], s['layer'], [tuple(p) for p in s['pts']], s['w'], lock=False)
refill(b); pcbnew.SaveBoard(sys.argv[2], b)
print('EDIT-BAD', bad)
