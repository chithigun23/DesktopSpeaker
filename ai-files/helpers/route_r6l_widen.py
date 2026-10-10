"""flatpak: route_r6l_widen.py MODE IN.kicad_pcb OUT.kicad_pcb STATE.json [DRC.json]   (R6l overspec pass, driven by route_r6l_widen2.sh)
MODE init : list every track/arc of the power-type target nets, split long segments that end in a small pad (the pad end keeps a neck
            no wider than the pad), and write STATE.json with a descending width ladder per item. Ladder entries are only kept when
            (a) wider than the current width, (b) not wider than the bend-rule cap (a segment between two plain bends keeps 3 w <= length),
            (c) not wider than the arc radius (arcs), (d) the widened copper plus 0.4 mm stays outside every non-GND zone OUTLINE of
            another net on that layer (no stealing of other power pours / In2 islands), (e) not wider than a pad it ends in (neck piece).
MODE apply: set every pending item to the first ladder width.
MODE apply takes at most N (argv 5, default 60) items per round: kicad-cli caps the violations it reports per type (about 200/500),
           so large batches hide violations.
MODE verify: every accepted item still in a non-silk DRC violation goes back to its original width (safety net).
MODE judge: items in a non-silk DRC violation go back to their accepted width and drop that ladder step; the others accept it and stop.
Targets: classes POWER_HI, PVDD, SPK_OUT, PWR_5V, PWR_3V, PWR_LOCAL (all layers) and SWITCH on F.Cu for the amp OUT_x and the
U14/U15/U25 switch nodes (the U4 SW1/SW2 nodes are excluded: minimum SW area, handled by hand).
Environment: R6L_ONLY=net[,net] restricts the pass to those nets; R6L_STEAL=m sets the (d) margin (default 0.4; 0.0 lets the track
take up to its DRC clearance from a foreign zone outline, i.e. the other pour's fill gives way by the clearance only)."""
import sys, json, math, fnmatch
import pcbnew
MM = 1e6
mode, fin, fout, fst = sys.argv[1:5]
b = pcbnew.LoadBoard(fin)
pats = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/R6l.kicad_pro'))['net_settings']['netclass_patterns']
def cl(n):
    for p in pats:
        if fnmatch.fnmatchcase(n, p['pattern']): return p['netclass']
    return 'Default'
LAD = {'POWER_HI': [3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25],
       'PVDD': [3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25],
       'SPK_OUT': [3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8],
       'PWR_5V': [2.0, 1.5, 1.2, 1.0, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25],
       'PWR_3V': [1.5, 1.2, 1.0, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25],
       'PWR_LOCAL': [0.8, 0.6, 0.5, 0.4, 0.3, 0.25],
       'SWITCH': [1.5, 1.2, 1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.25]}
SW_OK = ('OUT_A+', 'OUT_A-', 'OUT_B+', 'OUT_B-', 'U14-L1', 'U14-L2', 'U15-L1', 'U15-L2', 'U25-SW')
import os
ONLY = os.environ.get('R6L_ONLY', '')            # optional: comma list of net names to restrict the pass to
STEAL = float(os.environ.get('R6L_STEAL', '0.4'))  # copper-to-foreign-zone-outline margin of the (d) test, default 0.4 mm
STEAL0 = os.environ.get('R6L_STEAL0', '')         # comma list of nets that use a 0.0 margin in the (d) test (the In2 3V_AO trunk)
SPLIT = float(os.environ.get('R6L_SPLIT', '0'))    # >0: split straight target segments longer than 2*SPLIT into ~SPLIT mm collinear pieces
def target(t):
    n = str(t.GetNetname()); c = cl(n)
    if ONLY and n not in ONLY.split(','): return None
    if c not in LAD: return None
    if c == 'SWITCH' and (t.GetLayer() != pcbnew.F_Cu or not any(s in n for s in SW_OK)): return None
    return c
def V(x, y): return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
# net pinning: a round that widens a track over a foreign via (a short, reverted later) lets KiCad propagate the track's net onto a
# floating via when the board is loaded again; every via/track net is recorded at init (STATE.nets.json) and restored at every load
import os as _os
_nf = fst + '.nets.json'
if mode == 'init':
    json.dump({t.m_Uuid.AsString(): str(t.GetNetname()) for t in b.GetTracks()}, open(_nf, 'w'))
elif _os.path.exists(_nf):
    _nets = json.load(open(_nf)); _fix = 0
    for t in b.GetTracks():
        n0 = _nets.get(t.m_Uuid.AsString())
        if n0 is not None and str(t.GetNetname()) != n0: t.SetNet(b.FindNet(n0)); _fix += 1
    if _fix: print('net pin restored', _fix)
def tracks(): return [t for t in b.GetTracks() if t.GetClass() in ('PCB_TRACK', 'PCB_ARC')]
def byid(): return {t.m_Uuid.AsString(): t for t in tracks()}
if mode == 'init':
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads(): pads.setdefault(str(p.GetNetname()), []).append(p)
    vias = {}
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA': vias.setdefault(str(t.GetNetname()), []).append(t)
    def padat(n, L, pt):
        for p in pads.get(n, []):
            if p.IsOnLayer(L) and p.GetEffectivePolygon(L).Contains(V(*pt)): return p
    # 1. split long straight segments that end inside a small pad
    nsplit = 0
    for t in list(tracks()):
        c = target(t)
        if c is None or t.GetClass() != 'PCB_TRACK': continue
        n = str(t.GetNetname()); L = t.GetLayer(); w = t.GetWidth() / MM
        a = (t.GetStart().x / MM, t.GetStart().y / MM); e = (t.GetEnd().x / MM, t.GetEnd().y / MM)
        Ln = math.hypot(e[0] - a[0], e[1] - a[1])
        if Ln < 1.2: continue
        for end, oth in ((a, e), (e, a)):
            p = padat(n, L, end)
            if p is None: continue
            pc = min(p.GetSizeX(), p.GetSizeY()) / MM
            if pc >= LAD[c][0]: continue
            ps = p.GetEffectivePolygon(L); ux, uy = (oth[0] - end[0]) / Ln, (oth[1] - end[1]) / Ln; s = 0.0
            while s < Ln and ps.Contains(V(end[0] + ux * s, end[1] + uy * s)): s += 0.02
            s = s + 0.3
            if Ln - s < 0.6: continue
            m = (end[0] + ux * s, end[1] + uy * s)
            t2 = pcbnew.PCB_TRACK(b); t2.SetLayer(L); t2.SetWidth(t.GetWidth()); t2.SetNet(t.GetNet())
            if end == a: t2.SetStart(V(*a)); t2.SetEnd(V(*m)); t.SetStart(V(*m))
            else: t2.SetStart(V(*m)); t2.SetEnd(V(*e)); t.SetEnd(V(*m))
            b.Add(t2); nsplit += 1
            break
    # 1b. optional: split long straight segments into collinear pieces so a local obstacle only limits its own piece
    if SPLIT > 0:
        for t in list(tracks()):
            if target(t) is None or t.GetClass() != 'PCB_TRACK': continue
            Ln = t.GetLength() / MM
            if Ln <= 2 * SPLIT: continue
            k = int(Ln // SPLIT); a = t.GetStart(); e = t.GetEnd()
            pts = [pcbnew.VECTOR2I(int(a.x + (e.x - a.x) * i / k), int(a.y + (e.y - a.y) * i / k)) for i in range(k + 1)]
            t.SetEnd(pts[1])
            for i in range(1, k):
                t2 = pcbnew.PCB_TRACK(b); t2.SetLayer(t.GetLayer()); t2.SetWidth(t.GetWidth()); t2.SetNet(t.GetNet()); t2.SetStart(pts[i]); t2.SetEnd(pts[i + 1]); b.Add(t2)
            nsplit += k - 1
    # 2. bend topology (plain bends) for the 3 w <= length cap
    segs = [t for t in tracks() if t.GetClass() == 'PCB_TRACK']
    ends = {}
    def key(v): return (round(v.x / MM / 0.01), round(v.y / MM / 0.01), )
    for t in tracks():
        for v in (t.GetStart(), t.GetEnd()): ends.setdefault((str(t.GetNetname()), t.GetLayer()) + key(v), []).append(t)
    def plain_turn(t, v, d):
        k = (str(t.GetNetname()), t.GetLayer()) + key(v); lst = ends.get(k, [])
        if len(lst) != 2: return None
        n = str(t.GetNetname()); pt = (v.x / MM, v.y / MM)
        for vv in vias.get(n, []):
            if math.hypot(vv.GetX() / MM - pt[0], vv.GetY() / MM - pt[1]) <= vv.GetWidth(pcbnew.F_Cu) / MM / 2: return None
        if padat(n, t.GetLayer(), pt) is not None: return None
        o = lst[0] if lst[1] is t else lst[1]
        if o.GetClass() == 'PCB_ARC': return 0.0
        far = o.GetEnd() if key(o.GetStart()) == key(v) else o.GetStart()
        u = ((far.x - v.x) / MM, (far.y - v.y) / MM)
        if math.hypot(*u) < 1e-6: return None
        cr = d[0] * u[1] - d[1] * u[0]; dt = d[0] * u[0] + d[1] * u[1]
        return abs(math.degrees(math.atan2(cr, dt)))
    # 3. other-net non-GND zone outlines per layer
    zl = {}
    for z in b.Zones():
        if z.GetIsRuleArea() or str(z.GetNetname()) in ('GND', ''): continue
        for L in (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            if z.IsOnLayer(L): zl.setdefault(L, []).append((str(z.GetNetname()), z.Outline()))
    def steals(t, w):
        n = str(t.GetNetname()); L = t.GetLayer(); ps = pcbnew.SHAPE_POLY_SET()
        m_ = 0.0 if n in STEAL0.split(',') else STEAL; w0 = t.GetWidth(); t.SetWidth(int(round((w + 2 * m_) * MM))); t.TransformShapeToPolygon(ps, L, 0, 5000, pcbnew.ERROR_INSIDE); t.SetWidth(w0)
        for zn, o in zl.get(L, []):
            if zn == n: continue
            x = pcbnew.SHAPE_POLY_SET(ps); x.BooleanIntersection(o)
            if x.Area() > 1e-3 * MM * MM: return True
        return False
    st = {}
    for t in tracks():
        c = target(t)
        if c is None: continue
        n = str(t.GetNetname()); L = t.GetLayer(); w = t.GetWidth() / MM
        cap = 99.0; why = []
        if t.GetClass() == 'PCB_ARC':
            cap = min(cap, t.GetRadius() / MM); why.append('arc')
        else:
            a, e = t.GetStart(), t.GetEnd(); Ln = t.GetLength() / MM
            d = ((e.x - a.x) / MM, (e.y - a.y) / MM)
            ta = plain_turn(t, a, (-d[0], -d[1])); te = plain_turn(t, e, d)
            if ta is not None and te is not None and ta >= 10 and te >= 10: cap = min(cap, Ln / 3.0 - 0.005); why.append('bend')
            for v in (a, e):
                p = padat(n, L, (v.x / MM, v.y / MM))
                if p is not None and Ln < 1.0 + 0.6: cap = min(cap, min(p.GetSizeX(), p.GetSizeY()) / MM); why.append('pad')
        lad = [x for x in LAD[c] if x > w + 1e-6 and x <= cap + 1e-6]
        lad = [x for x in lad if not steals(t, x)]
        if lad: st[t.m_Uuid.AsString()] = dict(net=n, cls=c, layer=b.GetLayerName(L), w0=w, acc=w, lad=lad, why=why, cur=None)
    json.dump(st, open(fst, 'w'), indent=0); print('init split', nsplit, 'candidates', len(st))
    json.dump({t.m_Uuid.AsString(): str(t.GetNetname()) for t in b.GetTracks()}, open(_nf, 'w'))
elif mode == 'apply':
    st = json.load(open(fst)); ids = byid(); k = 0; N = int(sys.argv[5]) if len(sys.argv) > 5 else 60
    for u, s in st.items():
        if s['lad'] and u in ids and k < N: ids[u].SetWidth(int(round(s['lad'][0] * MM))); s['cur'] = s['lad'][0]; k += 1
        else: s['cur'] = None
    json.dump(st, open(fst, 'w'), indent=0); print('apply', k)
elif mode == 'judge':
    st = json.load(open(fst)); ids = byid(); d = json.load(open(sys.argv[5])); bad = set()
    for x in d['violations']:
        if x['type'].startswith('silk') or x['type'] in ('lib_footprint_mismatch', 'skew_out_of_range', 'diff_pair_uncoupled_length_too_long'): continue
        for it in x['items']: bad.add(it.get('uuid', ''))
    nb = ng = 0
    for u, s in st.items():
        if s['cur'] is None: continue
        if u in bad:
            ids[u].SetWidth(int(round(s['acc'] * MM))); s['lad'] = s['lad'][1:]; nb += 1
        else:
            s['acc'] = s['cur']; s['lad'] = []; ng += 1
        s['cur'] = None
    json.dump(st, open(fst, 'w'), indent=0); print('judge accepted', ng, 'reverted', nb, 'pending', sum(1 for s in st.values() if s['lad']))
elif mode == 'merge':
    # merge exactly collinear consecutive pieces of the same net/layer/width at a plain joint (exactly two tracks, no via or pad there):
    # undoes the R6L_SPLIT pieces wherever the neighbouring pieces ended at the same width
    nm = 0
    while True:
        segs = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and target(t) is not None]
        allends = {}
        for t in b.GetTracks():
            if t.GetClass() == 'PCB_VIA':
                allends.setdefault((str(t.GetNetname()), 'via', t.GetX(), t.GetY()), []).append(t); continue
            for v in (t.GetStart(), t.GetEnd()): allends.setdefault((str(t.GetNetname()), t.GetLayer(), v.x, v.y), []).append(t)
        padl = [(p, str(p.GetNetname())) for f in b.GetFootprints() for p in f.Pads()]
        plan = []; used = set()
        for t1 in segs:
            for v in (t1.GetStart(), t1.GetEnd()):
                n = str(t1.GetNetname()); L = t1.GetLayer(); k = (n, L, v.x, v.y); lst = allends.get(k, [])
                if len(lst) != 2 or (n, 'via', v.x, v.y) in allends: continue
                t2 = lst[0] if lst[1] is t1 else lst[1]
                if t2.GetClass() != 'PCB_TRACK' or t2.GetWidth() != t1.GetWidth(): continue
                u1 = t1.m_Uuid.AsString(); u2 = t2.m_Uuid.AsString()
                if u1 in used or u2 in used: continue
                if any(pn == n and p.IsOnLayer(L) and p.HitTest(pcbnew.VECTOR2I(v.x, v.y)) for p, pn in padl): continue
                a = t1.GetEnd() if (t1.GetStart().x, t1.GetStart().y) == (v.x, v.y) else t1.GetStart()
                c = t2.GetEnd() if (t2.GetStart().x, t2.GetStart().y) == (v.x, v.y) else t2.GetStart()
                cr = (v.x - a.x) * (c.y - v.y) - (v.y - a.y) * (c.x - v.x); dt = (v.x - a.x) * (c.x - v.x) + (v.y - a.y) * (c.y - v.y)
                ln = ((c.x - a.x) ** 2 + (c.y - a.y) ** 2) ** 0.5
                if dt <= 0 or ln == 0 or abs(cr) / ln > 2: continue   # off-line by less than 2 nm
                plan.append((t1, t2, pcbnew.VECTOR2I(a.x, a.y), pcbnew.VECTOR2I(c.x, c.y))); used.add(u1); used.add(u2)
        if not plan: break
        for t1, t2, a, c in plan: t1.SetStart(a); t1.SetEnd(c)
        for t1, t2, a, c in plan: b.Delete(t2)
        nm += len(plan)
    print('merged', nm)
elif mode == 'judgepos':
    # judge from the strict (split copy) DRC: a tried item is bad when a violating track piece of its net/layer lies on it
    st = json.load(open(fst)); d = json.load(open(sys.argv[5])); hits = []; huu = set()
    for x in d['violations']:
        if x['type'].startswith('silk') or x['type'] in ('lib_footprint_mismatch', 'skew_out_of_range', 'diff_pair_uncoupled_length_too_long'): continue
        for it in x['items']:
            ds = it['description']
            if (ds.startswith('Track') or ds.startswith('Arc')) and '[' in ds:
                hits.append((ds[ds.index('[') + 1:ds.index(']')], ds.split(' on ')[1].split(',')[0].strip(), it['pos']['x'], it['pos']['y']))
            huu.add(it.get('uuid', ''))
    ids = byid(); nb = ng = 0
    for u, s in st.items():
        if s['cur'] is None: continue
        t = ids[u]; bad = u in huu or any(n == s['net'] and ln == s['layer'] and t.HitTest(V(x, y), int(0.01 * MM)) for n, ln, x, y in hits)
        if bad: t.SetWidth(int(round(s['acc'] * MM))); s['lad'] = s['lad'][1:]; nb += 1
        else: s['acc'] = s['cur']; s['lad'] = []; ng += 1
        s['cur'] = None
    json.dump(st, open(fst, 'w'), indent=0); print('judge accepted', ng, 'reverted', nb, 'pending', sum(1 for s in st.values() if s['lad']))
elif mode == 'verify2':
    # strict oracle: DRC of a copy with every track split into <= 1 mm pieces (route_r6l_splitall.py). KiCad applies a rule area
    # (NECK_*, courtyards) to a whole track when any part of it intersects the area, so a long track that touches a neck gets the
    # relaxed neck clearance along its full length; the split copy applies the rules per 1 mm piece. Every widened item that holds
    # a piece in a non-silk violation goes back to its original width.
    st = json.load(open(fst)); d = json.load(open(sys.argv[5])); hits = []; huu = set()
    for x in d['violations']:
        if x['type'].startswith('silk') or x['type'] in ('lib_footprint_mismatch', 'skew_out_of_range', 'diff_pair_uncoupled_length_too_long'): continue
        for it in x['items']:
            ds = it['description']
            if ds.startswith('Track') and '[' in ds:
                hits.append((ds[ds.index('[') + 1:ds.index(']')], ds.split(' on ')[1].split(',')[0].strip(), it['pos']['x'], it['pos']['y']))
            huu.add(it.get('uuid', ''))
    ids = byid(); nb = 0
    for u, s in st.items():
        if s['acc'] <= s['w0'] + 1e-6 or u not in ids: continue
        t = ids[u]
        if u in huu: t.SetWidth(int(round(s['w0'] * MM))); s['acc'] = s['w0']; nb += 1; continue
        for n, ln, x, y in hits:
            if n != s['net'] or ln != s['layer']: continue
            if t.HitTest(V(x, y), int(0.01 * MM)):
                t.SetWidth(int(round(s['w0'] * MM))); s['acc'] = s['w0']; nb += 1; break
    json.dump(st, open(fst, 'w'), indent=0); print('verify2 reverted', nb)
elif mode == 'verify':
    st = json.load(open(fst)); ids = byid(); d = json.load(open(sys.argv[5])); bad = set()
    for x in d['violations']:
        if x['type'].startswith('silk') or x['type'] in ('lib_footprint_mismatch', 'skew_out_of_range', 'diff_pair_uncoupled_length_too_long'): continue
        for it in x['items']: bad.add(it.get('uuid', ''))
    nb = 0
    for u, s in st.items():
        if u in bad and s['acc'] > s['w0'] + 1e-6: ids[u].SetWidth(int(round(s['w0'] * MM))); s['acc'] = s['w0']; nb += 1
    json.dump(st, open(fst, 'w'), indent=0); print('verify reverted', nb)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(fout, b)
