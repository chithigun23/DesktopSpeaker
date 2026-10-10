"""flatpak: route_r6l_zgrow.py MODE IN.kicad_pcb OUT.kicad_pcb STATE.json [ARG]   (R6l overspec pass: pour growth, driven by route_r6l_zgrow.sh)
Zones grown: non-GND, non-rule-area copper zones on F.Cu and In2.Cu of the classes POWER_HI, PVDD, SPK_OUT, PWR_5V, PWR_3V (SWITCH pours are
not grown: minimum switch-node area). B.Cu pours are not grown (B.Cu is the second GND plane and the amp thermal plane).
MODE grow ARG=d : for every pending zone, new outline = (original outline inflated by d) minus (every other non-GND zone outline on that layer
                  inflated by 0.5 mm) minus every other-net track/via (+0.4 mm on F, +0.35 mm on In2) and pad (+0.6 mm on F, +0.35 on In2; GND
                  items are ignored on In2 only) minus the NECK_* rule areas, so a pour only grows into empty copper or open GND pour and never
                  squeezes between foreign items (keeps the In2 island hygiene gates and the fragment-aware connectivity);
                  union with the original outline; only the part connected to the original is kept. STATE keeps the original outline.
MODE judge ARG=DRC.json : a grown zone in any non-silk DRC violation, or whose fill now has more pieces than before, or whose fill area
                  did not grow, goes back to its previous outline; accepted zones keep the growth and are tried again with the next step."""
import sys, json, fnmatch
import pcbnew
MM = 1e6
mode, fin, fout, fst = sys.argv[1:5]
b = pcbnew.LoadBoard(fin)
pats = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/R6l.kicad_pro'))['net_settings']['netclass_patterns']
def cl(n):
    for p in pats:
        if fnmatch.fnmatchcase(n, p['pattern']): return p['netclass']
    return 'Default'
CLS = ('POWER_HI', 'PVDD', 'SPK_OUT', 'PWR_5V', 'PWR_3V')
LAYS = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: '2'}
def zl(z):
    for L in LAYS:
        if z.IsOnLayer(L): return L
def poly_to_list(ps):
    out = []
    for k in range(ps.OutlineCount()):
        c = [ps.Outline(k)] + [ps.Hole(k, h) for h in range(ps.HoleCount(k))]
        out.append([[[p.x, p.y] for p in [cc.CPoint(i) for i in range(cc.PointCount())]] for cc in c])
    return out
def list_to_poly(lst):
    ps = pcbnew.SHAPE_POLY_SET()
    for o in lst:
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in o[0]: ch.Append(int(x), int(y))
        ch.SetClosed(True); ps.AddOutline(ch)
        for h in o[1:]:
            hc = pcbnew.SHAPE_LINE_CHAIN()
            for x, y in h: hc.Append(int(x), int(y))
            hc.SetClosed(True); ps.AddHole(hc, ps.OutlineCount() - 1)
    return ps
def setout(z, ps):
    o = z.Outline(); o.RemoveAllContours(); o.Append(ps); z.UnFill()
def fillinfo(z):
    L = zl(z)
    if not z.HasFilledPolysForLayer(L): return 0, 0.0
    f = z.GetFilledPolysList(L); return f.OutlineCount(), f.Area() / MM / MM
def zones():
    return [z for z in b.Zones() if not z.GetIsRuleArea() and zl(z) is not None and str(z.GetNetname()) not in ('', 'GND') and cl(str(z.GetNetname())) in CLS
            and sum(1 for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if z.IsOnLayer(L)) == 1 and not relaxed(z)]
def cands():
    return [z for z in b.Zones() if not z.GetIsRuleArea() and zl(z) is not None and str(z.GetNetname()) not in ('', 'GND') and cl(str(z.GetNetname())) in CLS
            and sum(1 for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if z.IsOnLayer(L)) == 1]
def zid(z): return z.m_Uuid.AsString()
# zones that touch a NECK_* rule area or a fine-pitch IC courtyard get the relaxed neck_ic clearance over their whole fill (KiCad applies
# intersectsArea/intersectsCourtyard to the whole item), so growing them would spread the relaxation: they are not grown.
NECKREF = ('U4', 'U6', 'U7', 'U8', 'U9', 'U11', 'U14', 'U15', 'U19', 'U24', 'U25', 'U3', 'U5', 'U10', 'U20', 'J1')
_relax = []
for _y in b.Zones():
    if _y.GetIsRuleArea() and _y.GetZoneName().startswith('NECK'): _relax.append(pcbnew.SHAPE_POLY_SET(_y.Outline()))
for _r in NECKREF:
    _f = b.FindFootprintByReference(_r)
    if _f is not None:
        for _L in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            _c = _f.GetCourtyard(_L)
            if _c.OutlineCount(): _relax.append(pcbnew.SHAPE_POLY_SET(_c))
def relaxed(z):
    for r in _relax:
        x = pcbnew.SHAPE_POLY_SET(z.Outline()); x.BooleanIntersection(r)
        if x.Area() > 0: return True
    return False
if mode == 'grow':
    d = float(sys.argv[5])
    st = json.load(open(fst)) if d is not None and len(sys.argv) > 6 and sys.argv[6] == 'cont' else {}
    allz = [z for z in b.Zones() if not z.GetIsRuleArea()]
    k = 0; st['__round'] = st.get('__round', 0) + 1
    if '__pieces0' not in st:
        st['__pieces0'] = {}
        for z in b.Zones():
            if z.GetIsRuleArea(): continue
            for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
                if z.IsOnLayer(L) and z.HasFilledPolysForLayer(L): st['__pieces0'][zid(z) + str(L)] = z.GetFilledPolysList(L).OutlineCount()
    relu = pcbnew.SHAPE_POLY_SET()
    for r in _relax: relu.Append(r)
    relu.Simplify(); relu.Inflate(int(0.15 * MM), pcbnew.CORNER_STRATEGY_CHAMFER_ALL_CORNERS, 20000)
    for z in cands():
        u = zid(z); s = st.get(u)
        if s is None:
            n, a = fillinfo(z); s = st[u] = dict(name=z.GetZoneName(), net=str(z.GetNetname()), layer=LAYS[zl(z)], orig=poly_to_list(z.Outline()), prev=None, n0=n, a0=a, done=False, grown=0.0)
        if s['done']: continue
        L = zl(z); n = str(z.GetNetname())
        base = pcbnew.SHAPE_POLY_SET(z.Outline()); g = pcbnew.SHAPE_POLY_SET(base)
        g.Inflate(int(d * MM), pcbnew.CORNER_STRATEGY_CHAMFER_ALL_CORNERS, 20000)
        cut = pcbnew.SHAPE_POLY_SET()
        for y in allz:
            yn = str(y.GetNetname())
            if y is z or yn in ('', 'GND', n) or not y.IsOnLayer(L): continue
            c = pcbnew.SHAPE_POLY_SET(y.Outline()); c.Inflate(int(0.5 * MM), pcbnew.CORNER_STRATEGY_CHAMFER_ALL_CORNERS, 20000); cut.Append(c)
        for t in b.GetTracks():
            tn = str(t.GetNetname())
            if tn == n or not t.IsOnLayer(L): continue
            if L == pcbnew.In2_Cu and tn == 'GND': continue
            t.TransformShapeToPolygon(cut, L, int((0.35 if L == pcbnew.In2_Cu else 0.4) * MM), 20000, pcbnew.ERROR_OUTSIDE)
        for f in b.GetFootprints():
            for p in f.Pads():
                if str(p.GetNetname()) != n and p.IsOnLayer(L) and not (L == pcbnew.In2_Cu and str(p.GetNetname()) == 'GND'):
                    p.TransformShapeToPolygon(cut, L, int((0.35 if L == pcbnew.In2_Cu else 0.6) * MM), 20000, pcbnew.ERROR_OUTSIDE)
        for y in b.Zones():
            if y.GetIsRuleArea() and y.GetZoneName().startswith('NECK') and y.IsOnLayer(L): cut.Append(pcbnew.SHAPE_POLY_SET(y.Outline()))
        cut.Simplify()
        g.BooleanSubtract(cut); g.BooleanAdd(base); g.Simplify()
        keep = pcbnew.SHAPE_POLY_SET()
        for kk in range(g.OutlineCount()):
            one = pcbnew.SHAPE_POLY_SET(); one.AddOutline(g.Outline(kk))
            for h in range(g.HoleCount(kk)): one.AddHole(g.Hole(kk, h))
            x = pcbnew.SHAPE_POLY_SET(one); x.BooleanIntersection(base)
            if x.Area() > 0: keep.Append(one)
        if keep.Area() <= base.Area() * 1.0005: s['tried'] = False; continue
        if relaxed(z):
            # companion pour: the growth outside the neck areas goes into a new same-net zone <name>_G that touches no NECK area or
            # IC courtyard (strict rules on its fill), one priority below the original (same-net intersecting zones need distinct
            # priorities), and overlaps the original only where the original is outside those areas
            reg = pcbnew.SHAPE_POLY_SET(keep); reg.BooleanSubtract(base); reg.BooleanSubtract(relu)
            s['done'] = True
            if reg.Area() < 0.5 * MM * MM: continue
            ov = pcbnew.SHAPE_POLY_SET(reg); ov.Inflate(int(0.6 * MM), pcbnew.CORNER_STRATEGY_CHAMFER_ALL_CORNERS, 20000)
            bo = pcbnew.SHAPE_POLY_SET(base); bo.BooleanSubtract(relu); ov.BooleanIntersection(bo)
            reg.BooleanAdd(ov); reg.Simplify()
            z2 = z.Duplicate(False); z2 = pcbnew.Cast_to_ZONE(z2) if hasattr(pcbnew, 'Cast_to_ZONE') and not isinstance(z2, pcbnew.ZONE) else z2; b.Add(z2); z2.SetZoneName(z.GetZoneName() + '_G'); setout(z2, reg)
            used = set()
            for y in b.Zones():
                if y is z2 or y.GetIsRuleArea() or str(y.GetNetname()) != str(z.GetNetname()) or not y.IsOnLayer(zl(z)): continue
                x = pcbnew.SHAPE_POLY_SET(reg); x.BooleanIntersection(y.Outline())
                if x.Area() > 0 or y is z: used.add(y.GetAssignedPriority())
            pr = [p for p in list(range(z.GetAssignedPriority() - 1, 0, -1)) + list(range(z.GetAssignedPriority() + 1, 40)) if p not in used][0]
            z2.SetAssignedPriority(pr)
            st[zid(z2)] = dict(name=z2.GetZoneName(), net=str(z2.GetNetname()), layer=LAYS[zl(z2)], orig=None, prev=None, comp=True, n0=999, a0=0.0, done=False, grown=0.0,
                               tried=True, d=d, d_round=st['__round'])
            k += 1; continue
        s['prev'] = poly_to_list(base); setout(z, keep); s['tried'] = True; s['d'] = d; s['d_round'] = st['__round']; k += 1
    json.dump(st, open(fst, 'w')); print('grow', d, 'zones tried', k)
elif mode == 'judge':
    st = json.load(open(fst)); dr = json.load(open(sys.argv[5])); bad = set(); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    for x in dr['violations']:
        if x['type'].startswith('silk') or x['type'] in ('lib_footprint_mismatch', 'skew_out_of_range', 'diff_pair_uncoupled_length_too_long'): continue
        for it in x['items']: bad.add(it.get('uuid', ''))
    ng = nb = 0
    for z in zones():
        u = zid(z); s = st.get(u)
        if not s or not s.get('tried'): continue
        n, a = fillinfo(z)
        if u in bad or n > s['n0'] or a < s.get('a_acc', s['a0']) + 0.05:
            if s.get('comp') and s['prev'] is None: b.Remove(z)
            else: setout(z, list_to_poly(s['prev']))
            s['done'] = True; nb += 1; s['why'] = 'drc' if u in bad else ('pieces' if n > s['n0'] else 'nogain')
        else:
            s['a_acc'] = a; s['grown'] += s['d']; ng += 1; s['tried'] = False; continue
        s['d_round'] = None
        s['tried'] = False
    # global check: no zone of any net (GND included) may end up with more fill pieces than before the pass; revert the zones accepted
    # in this round one by one, nearest first, until every zone is back to its starting piece count (GND_IN2_BG, the In2 GND filler
    # between the islands, is exempt: more filler pieces only means more small GND islands, each stitched by its own vias)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    def pieces():
        out = {}
        for z in b.Zones():
            if z.GetIsRuleArea() or z.GetZoneName() == 'GND_IN2_BG': continue
            for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
                if z.IsOnLayer(L) and z.HasFilledPolysForLayer(L): out[zid(z) + str(L)] = (z.GetFilledPolysList(L).OutlineCount(), z)
        return out
    p0 = st.setdefault('__pieces0', {})
    acc = [z for z in zones() if st.get(zid(z), {}).get('d_round') == st.get('__round')]
    while True:
        cur = pieces(); worse = [v[1] for k, v in cur.items() if v[0] > p0.get(k, 99)]
        if not worse or not acc: break
        y = worse[0]; yb = y.GetBoundingBox()
        def dist(z):
            zb = z.GetBoundingBox(); dx = max(0, max(zb.GetLeft(), yb.GetLeft()) - min(zb.GetRight(), yb.GetRight())); dy = max(0, max(zb.GetTop(), yb.GetTop()) - min(zb.GetBottom(), yb.GetBottom()))
            return (0 if zl(z) is not None and y.IsOnLayer(zl(z)) else 1, dx + dy, z.GetBoundingBox().GetArea())
        acc.sort(key=dist); z = acc.pop(0); s = st[zid(z)]
        if s.get('comp') and s['prev'] is None: b.Remove(z)
        else: setout(z, list_to_poly(s['prev']))
        s['done'] = True; s['grown'] -= s['d']; s['why'] = 'pieces(%s)' % y.GetZoneName(); nb += 1; ng -= 1
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    json.dump(st, open(fst, 'w')); print('judge accepted', ng, 'reverted', nb)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(fout, b)
