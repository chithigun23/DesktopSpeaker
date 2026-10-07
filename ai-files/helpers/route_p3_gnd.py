"""P3 variant (GND clusters without via are stripped and re-attached). flatpak: route_p3_gnd.py IN.kicad_pcb OUT.kicad_pcb RUN.json : (1) re-attach GND pads that lost their via, (2) vias for isolated In2 pour fragments"""
import sys, json, math, fnmatch, pcbnew
MM = 1e6
inp, outp, runj = sys.argv[1:4]
b = pcbnew.LoadBoard(inp)
pro = json.load(open(inp.replace('.kicad_pcb', '.kicad_pro')))
pats = pro['net_settings']['netclass_patterns']
def ncls(n):
    for p in pats:
        if fnmatch.fnmatchcase(n, p['pattern']): return p['netclass']
    return 'SIGNAL'
LAYS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
bb = b.GetBoardEdgesBoundingBox()
ant = None
for z in b.Zones():
    if z.GetIsRuleArea() and z.GetZoneName() == 'BM83_ANTENNA_KEEPOUT': ant = z.GetBoundingBox()
CL = {'AUDIO': 0.5, 'I2S_CLK': 0.4, 'USB': 0.4, 'POWER_HI': 0.4, 'PVDD': 0.3, 'SPK_OUT': 0.3, 'SWITCH': 0.3}
def items_near(pt, r):
    box = pcbnew.BOX2I(pcbnew.VECTOR2I(int(pt[0]*MM - r*MM), int(pt[1]*MM - r*MM)), pcbnew.VECTOR2I(int(2*r*MM), int(2*r*MM)))
    out = []
    for f in b.GetFootprints():
        if not box.Intersects(f.GetBoundingBox()): continue
        for p in f.Pads():
            if box.Intersects(p.GetBoundingBox()): out.append(('pad', p))
    for t in b.Tracks():
        if box.Intersects(t.GetBoundingBox()): out.append(('via' if t.GetClass() == 'PCB_VIA' else 'trk', t))
    return out
def shape_pt(pt, w, net):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(int(round(pt[0]*MM)), int(round(pt[1]*MM)))); v.SetWidth(int(w*MM)); return v
def legal_via(pt, dia, drill, net, near=None):
    if pt[0] < bb.GetLeft()/MM + 0.8 or pt[0] > bb.GetRight()/MM - 0.8 or pt[1] < bb.GetTop()/MM + 0.8 or pt[1] > bb.GetBottom()/MM - 0.8: return False
    if ant is not None:
        if ant.Contains(pcbnew.VECTOR2I(int(pt[0]*MM), int(pt[1]*MM))) or (ant.GetLeft()/MM - 0.7 < pt[0] < ant.GetRight()/MM + 0.7 and ant.GetTop()/MM - 0.7 < pt[1] < ant.GetBottom()/MM + 0.7): return False
    v = shape_pt(pt, dia, net)
    for kind, o in (near if near is not None else items_near(pt, 3)):
        n = str(o.GetNetname())
        if kind == 'pad' and o.GetDrillSizeX() > 0:
            d = math.hypot(o.GetX()/MM - pt[0], o.GetY()/MM - pt[1]) - o.GetDrillSizeX()/MM/2 - drill/2
            if d < 0.3: return False
        if kind == 'via':
            d = math.hypot(o.GetPosition().x/MM - pt[0], o.GetPosition().y/MM - pt[1]) - o.GetDrillValue()/MM/2 - drill/2
            if d < 0.3: return False
        if n == net: continue
        if kind == 'pad':
            c = 0.2
            # hole to hole
            if o.GetDrillSizeX() > 0:
                d = math.hypot(o.GetX()/MM - pt[0], o.GetY()/MM - pt[1]) - o.GetDrillSizeX()/MM/2 - drill/2
                if d < 0.3: return False
            for L in LAYS:
                if o.IsOnLayer(L) and o.GetEffectiveShape(L).Collide(v.GetEffectiveShape(L), int((c - 0.001)*MM)): return False
        else:
            cl = ncls(n)
            c = CL.get(cl, 0.2)
            if cl == 'GND' or (net == 'GND' and cl in ('AUDIO', 'I2S_CLK', 'USB', 'SWITCH')): c = 0.2
            if kind == 'via':
                if o.GetEffectiveShape(pcbnew.F_Cu).Collide(v.GetEffectiveShape(pcbnew.F_Cu), int((max(c, 0.2) - 0.001)*MM)): return False
                d = math.hypot(o.GetPosition().x/MM - pt[0], o.GetPosition().y/MM - pt[1]) - o.GetDrillValue()/MM/2 - drill/2
                if d < 0.3: return False
            else:
                if o.GetLayer() in LAYS and o.GetEffectiveShape().Collide(v.GetEffectiveShape(o.GetLayer()), int((c - 0.001)*MM)): return False
    return True
def add_via(pt, dia, drill, net):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(int(round(pt[0]*MM)), int(round(pt[1]*MM)))); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(int(dia*MM)); v.SetDrill(int(drill*MM)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet(net)); b.Add(v); return v
def add_trk(a, c, w, net):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(int(round(a[0]*MM)), int(round(a[1]*MM)))); t.SetEnd(pcbnew.VECTOR2I(int(round(c[0]*MM)), int(round(c[1]*MM))))
    t.SetLayer(pcbnew.F_Cu); t.SetWidth(int(w*MM)); t.SetNet(b.FindNet(net)); b.Add(t); return t
def stub_legal(a, c, w, net, near):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(int(a[0]*MM), int(a[1]*MM))); t.SetEnd(pcbnew.VECTOR2I(int(c[0]*MM), int(c[1]*MM))); t.SetLayer(pcbnew.F_Cu); t.SetWidth(int(w*MM)); sh = t.GetEffectiveShape()
    for kind, o in near:
        n = str(o.GetNetname())
        if n == net: continue
        cl = ncls(n) if kind != 'pad' else 'x'
        cc = 0.2 if (kind == 'pad' or cl == 'GND') else CL.get(cl, 0.2)
        if kind == 'pad':
            if o.IsOnLayer(pcbnew.F_Cu) and o.GetEffectiveShape(pcbnew.F_Cu).Collide(sh, int((cc - 0.001)*MM)): return False
        elif kind == 'via':
            if o.GetEffectiveShape(pcbnew.F_Cu).Collide(sh, int((cc - 0.001)*MM)): return False
        elif o.GetLayer() == pcbnew.F_Cu and o.GetEffectiveShape().Collide(sh, int((cc - 0.001)*MM)): return False
    return True
res = {'gnd_ok': 0, 'gnd_fail': [], 'isl_ok': 0, 'isl_fail': []}
# ---- (1) GND pads
gz = [z for z in b.Zones() if not z.GetIsRuleArea() and str(z.GetNetname()) == 'GND']
# --- strip degenerate and via-less F.Cu GND copper clusters
for t in list(b.Tracks()):
    if str(t.GetNetname()) == 'GND' and t.GetClass() != 'PCB_VIA' and t.GetLength() < 0.01 * MM: b.RemoveNative(t)
gt = [t for t in b.Tracks() if str(t.GetNetname()) == 'GND']
gp = [p for f in b.GetFootprints() for p in f.Pads() if str(p.GetNetname()) == 'GND' and p.IsOnLayer(pcbnew.F_Cu) and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
items = [('t', t) for t in gt] + [('p', p) for p in gp]
par = list(range(len(items)))
def fnd(i):
    while par[i] != i: par[i] = par[par[i]]; i = par[i]
    return i
def shp(it):
    k, o = it
    if k == 'p': return o.GetEffectiveShape(pcbnew.F_Cu)
    if o.GetClass() == 'PCB_VIA': return o.GetEffectiveShape(pcbnew.F_Cu)
    return o.GetEffectiveShape() if o.GetLayer() == pcbnew.F_Cu else None
shs = [shp(i) for i in items]
for i in range(len(items)):
    if shs[i] is None: continue
    bi = items[i][1].GetBoundingBox()
    for j in range(i + 1, len(items)):
        if shs[j] is None or (items[i][0] == 'p' and items[j][0] == 'p'): continue
        if bi.Intersects(items[j][1].GetBoundingBox()) and shs[i].Collide(shs[j], 0): par[fnd(i)] = fnd(j)
cl = {}
for i in range(len(items)): cl.setdefault(fnd(i), []).append(items[i])
nstrip = 0
for k, mem in cl.items():
    hasvia = any(m[0] == 't' and m[1].GetClass() == 'PCB_VIA' for m in mem)
    if hasvia: continue
    for m in mem:
        if m[0] == 't' and m[1].GetLayer() == pcbnew.F_Cu: b.RemoveNative(m[1]); nstrip += 1
print('stripped via-less GND stubs', nstrip)
gpads = set()
for f in b.GetFootprints():
    for p in f.Pads():
        if str(p.GetNetname()) != 'GND' or not p.IsOnLayer(pcbnew.F_Cu) or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
        key = (f.GetReference(), str(p.GetNumber()))
        # connected? any GND track/via touching, or pad itself has no neighbours needed
        touched = False
        for t in b.Tracks():
            if str(t.GetNetname()) != 'GND': continue
            if t.GetClass() == 'PCB_VIA':
                if p.GetEffectiveShape(pcbnew.F_Cu).Collide(t.GetEffectiveShape(pcbnew.F_Cu), 0): touched = True; break
            elif t.GetLayer() == pcbnew.F_Cu and p.GetEffectiveShape(pcbnew.F_Cu).Collide(t.GetEffectiveShape(), 0): touched = True; break
        if touched: continue
        if any(z.HitTestFilledArea(pcbnew.F_Cu, p.GetPosition()) for z in gz if z.IsOnLayer(pcbnew.F_Cu)): continue
        c = (p.GetX()/MM, p.GetY()/MM); near = items_near(c, 4); done = False
        cands = []
        for ix in range(-60, 61):
            for iy in range(-60, 61):
                q = (c[0] + ix*0.1, c[1] + iy*0.1); d = math.hypot(ix, iy)*0.1
                if d <= 6.0: cands.append((d, q))
        cands.sort()
        pw = p.GetBoundingBox(); hwid = max(pw.GetWidth(), pw.GetHeight())/MM/2
        for d, q in cands:
            if not legal_via(q, 0.6, 0.3, 'GND', near): continue
            inside_pad = p.HitTest(pcbnew.VECTOR2I(int(q[0]*MM), int(q[1]*MM)))
            if inside_pad and p.GetSizeX()/MM >= 1.0 and p.GetSizeY()/MM >= 1.0:
                add_via(q, 0.6, 0.3, 'GND'); done = True; break
            if d < 0.05: continue
            for w in (0.3, 0.25, 0.2):
                if stub_legal(c, q, w, 'GND', near):
                    add_via(q, 0.6, 0.3, 'GND'); add_trk(c, q, w, 'GND'); done = True; break
            if done: break
        if done: res['gnd_ok'] += 1
        else: res['gnd_fail'].append(key)
print('gnd', res['gnd_ok'], 'fail', len(res['gnd_fail']), res['gnd_fail'][:20])
# ---- (2) isolated In2 fragments
def refill():
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
refill()
L2 = pcbnew.In2_Cu
for z in list(b.Zones()):
    if z.GetIsRuleArea() or not z.IsOnLayer(L2): continue
    net = str(z.GetNetname())
    if net in ('GND', ''): continue
    fp = z.GetFilledPolysList(L2)
    f1 = [zz for zz in b.Zones() if not zz.GetIsRuleArea() and str(zz.GetNetname()) == net and zz.IsOnLayer(pcbnew.F_Cu)]
    for i in range(fp.OutlineCount()):
        o = fp.Outline(i)
        pts = [(o.CPoint(k).x/MM, o.CPoint(k).y/MM) for k in range(o.PointCount())]
        # connected if same net via/pad(PTH) inside
        conn = False
        poly = pcbnew.SHAPE_POLY_SET(); poly.AddOutline(o)
        for t in b.Tracks():
            if str(t.GetNetname()) == net and t.GetClass() == 'PCB_VIA' and poly.Collide(t.GetPosition()): conn = True; break
        if not conn:
            for f in b.GetFootprints():
                for p in f.Pads():
                    if str(p.GetNetname()) == net and p.IsOnLayer(L2) and poly.Collide(p.GetPosition()): conn = True; break
                if conn: break
        if conn: continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)
        cands = []
        gx = min(xs)
        while gx <= max(xs):
            gy = min(ys)
            while gy <= max(ys):
                cands.append((math.hypot(gx - cx, gy - cy), (gx, gy))); gy += 0.1
            gx += 0.1
        cands.sort(); done = False
        for dia, drill in ((0.8, 0.4), (0.6, 0.3)):
            for d, q in cands:
                qv = pcbnew.VECTOR2I(int(q[0]*MM), int(q[1]*MM))
                if not poly.Collide(qv, int((dia/2 + 0.1)*MM)): continue
                # same-net copper on F.Cu to tie to
                ok1 = any(zz.HitTestFilledArea(pcbnew.F_Cu, qv) for zz in f1)
                if not ok1:
                    for f in b.GetFootprints():
                        for p in f.Pads():
                            if str(p.GetNetname()) == net and p.IsOnLayer(pcbnew.F_Cu) and p.HitTest(qv): ok1 = True
                if not ok1: continue
                if legal_via(q, dia, drill, net):
                    add_via(q, dia, drill, net); done = True; break
            if done: break
        if done: res['isl_ok'] += 1
        else: res['isl_fail'].append((net, round(cx, 1), round(cy, 1)))
print('islands', res['isl_ok'], 'fail', res['isl_fail'])
refill()
pcbnew.SaveBoard(outp, b)
json.dump(res, open(outp.replace('.kicad_pcb', '.fix.json'), 'w'))
