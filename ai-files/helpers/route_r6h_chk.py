"""flatpak: route_r6h_chk.py BOARD SPEC.json : pre-check the add-items of a route_r6g_edit spec (tracks/vias) before applying.
Rules: route_r6a_lib.req() (AUDIO 0.5, I2S 0.4, POWER_HI 0.4, PVDD 0.3, SWITCH 1.0 to sensitive / 0.3), BATP & U25 FB/COMP/ILIM 2.0 to SWITCH/BOOT,
NECK_* areas relax everything to 0.2 (DRC rule neck_ic is last), foreign F/B pour fills 0.3 (reported, not always fatal: a pour is re-cut),
In2 tracks: 0.3 to non-GND In2 island outlines; vias inside a non-GND In2 island are reported (island exception).
Items removed by the spec (rmseg/rmvia/rmbox/ripnet/rmat) are ignored as obstacles. Prints one line per violation; 'OK n items' if clean."""
import sys, json, math
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b = pcbnew.LoadBoard(sys.argv[1]); spec = json.load(open(sys.argv[2]))
def near(q, p, tol=0.03): return abs(q.x / MM - p[0]) < tol and abs(q.y / MM - p[1]) < tol
gone = set()
for s in spec:
    if 'rmseg' in s:
        n = full(s['rmseg'], b)
        for t in b.GetTracks():
            if t.GetClass() != 'PCB_VIA' and str(t.GetNetname()) == n and ((near(t.GetStart(), s['a']) and near(t.GetEnd(), s['b'])) or (near(t.GetStart(), s['b']) and near(t.GetEnd(), s['a']))): gone.add(t.m_Uuid.AsString())
    elif 'rmvia' in s:
        n = full(s['rmvia'], b)
        for t in b.GetTracks():
            if t.GetClass() == 'PCB_VIA' and str(t.GetNetname()) == n and near(t.GetPosition(), s['p']): gone.add(t.m_Uuid.AsString())
    elif 'rmat' in s:
        n = full(s['rmat'], b)
        for t in b.GetTracks():
            if t.GetClass() != 'PCB_VIA' and str(t.GetNetname()) == n and (near(t.GetStart(), s['p']) or near(t.GetEnd(), s['p'])): gone.add(t.m_Uuid.AsString())
    elif 'ripnet' in s:
        n = full(s['ripnet'], b); K = s.get('keep', [])
        def kin(q): return any(k[0] <= q.x / MM <= k[2] and k[1] <= q.y / MM <= k[3] for k in K)
        for t in b.GetTracks():
            if str(t.GetNetname()) == n and not ((kin(t.GetPosition()) if t.GetClass() == 'PCB_VIA' else (kin(t.GetStart()) and kin(t.GetEnd())))): gone.add(t.m_Uuid.AsString())
    elif 'rmbox' in s or 'ripbox' in s:
        n = full(s.get('rmbox', s.get('ripbox')), b); x0, y0, x1, y1 = s['box']
        def inb(q): return x0 <= q.x / MM <= x1 and y0 <= q.y / MM <= y1
        for t in b.GetTracks():
            if str(t.GetNetname()) != n: continue
            if t.GetClass() == 'PCB_VIA':
                if inb(t.GetPosition()): gone.add(t.m_Uuid.AsString())
            elif ('rmbox' in s and inb(t.GetStart()) and inb(t.GetEnd())) or ('ripbox' in s and (inb(t.GetStart()) or inb(t.GetEnd()))): gone.add(t.m_Uuid.AsString())
moved = {}
for s in spec:
    if 'move' in s or 'moveby' in s:
        f = b.FindFootprintByReference(s.get('move', s.get('moveby')))
        if 'move' in s: f.SetPosition(V(*s['to']))
        else: f.SetPosition(V(f.GetX() / MM + s['d'][0], f.GetY() / MM + s['d'][1]))
        if 'rot' in s: f.SetOrientationDegrees(s['rot'])
necks = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('NECK')]
isl = [z for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu) and str(z.GetNetname()) not in ('GND', '')]
CRITN = ('Net-(U4-BATP)', 'Net-(U25-FB)', 'Net-(U25-COMP)', 'Net-(U25-ILIM)')
def inneck(sh, L):
    return any(z.IsOnLayer(L) and z.Outline().Collide(sh) for z in necks)
def need(na, nb, apad, bpad, sh, L):
    if na == nb and na: return None
    ca, cb = ncls(na), (ncls(nb) if nb else 'Default')
    r = req(ca, cb, apad, bpad)
    if not (apad and bpad):
        if (na in CRITN and cb in ('SWITCH', 'BOOT')) or (nb in CRITN and ca in ('SWITCH', 'BOOT')): r = max(r, 2.0)
    if inneck(sh, L): r = 0.2 if not (ca == 'USB' and cb == 'USB') else 0.15
    return r
new = []
for s in spec:
    if 'via' in s:
        n = full(s['net'], b); d = s.get('d', 0.6); dr = s.get('drill', 0.3)
        t = pcbnew.PCB_VIA(b); t.SetPosition(V(*s['via'])); t.SetWidth(int(d * MM)); t.SetDrill(int(dr * MM)); t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); t.SetViaType(pcbnew.VIATYPE_THROUGH)
        new.append((n, 'via', t, s))
    elif 'pts' in s:
        n = full(s['net'], b)
        for a, c in zip(s['pts'][:-1], s['pts'][1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c)); t.SetLayer(LAY[s['layer']]); t.SetWidth(int(s['w'] * MM))
            new.append((n, 'trk', t, s))
L4 = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
def lays(kind, t): return [x for x in L4 if x != pcbnew.In1_Cu] if kind == 'via' else [t.GetLayer()]
def shp(kind, t, L): return t.GetEffectiveShape(L) if kind == 'via' else t.GetEffectiveShape()
def gap(s1, s2):
    lo, hi = 0.0, 3.0
    if not s1.Collide(s2, int(hi * MM)): return 9.0
    for _ in range(14):
        m = (lo + hi) / 2
        if s1.Collide(s2, int(m * MM)): hi = m
        else: lo = m
    return hi
bad = 0
def rep(*a):
    global bad; bad += 1; print(*a)
for i, (n, kind, t, s) in enumerate(new):
    bb = t.GetBoundingBox(); bb.Inflate(int(2.6 * MM)); tag = '%s %s %s' % (n[-18:], kind, (s.get('via') or [round(t.GetStart().x / MM, 2), round(t.GetStart().y / MM, 2), round(t.GetEnd().x / MM, 2), round(t.GetEnd().y / MM, 2)]))
    for L in lays(kind, t):
        sh = shp(kind, t, L)
        for f in b.GetFootprints():
            if not bb.Intersects(f.GetBoundingBox()): continue
            for p in f.Pads():
                if not p.IsOnLayer(L) and not (p.GetDrillSizeX() > 0): continue
                pn = str(p.GetNetname())
                if pn == n and pn: continue
                if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    g = gap(p.GetEffectiveHoleShape(), sh)
                    if g < 0.3: rep(tag, 'NPTH', f.GetReference(), round(g, 3))
                    continue
                if not p.IsOnLayer(L): continue
                r = need(n, pn, False, True, sh, L); g = gap(p.GetEffectiveShape(L), sh)
                if g < r - 1e-4: rep(tag, 'L%d pad %s.%s %s gap %.3f req %.2f' % (L, f.GetReference(), p.GetNumber(), pn[-16:], g, r))
        for u in b.Tracks():
            if u.m_Uuid.AsString() in gone or not bb.Intersects(u.GetBoundingBox()): continue
            un = str(u.GetNetname())
            if u.GetClass() == 'PCB_VIA':
                if kind == 'via':
                    dd = math.hypot(u.GetX() - t.GetX(), u.GetY() - t.GetY()) / MM - (u.GetDrillValue() + t.GetDrillValue()) / MM / 2
                    if dd < 0.25 and un != n: rep(tag, 'hole-hole via', un[-16:], round(dd, 3))
                us = u.GetEffectiveShape(L)
            elif u.GetLayer() == L: us = u.GetEffectiveShape()
            else: continue
            if un == n: continue
            r = need(n, un, False, False, sh, L); g = gap(us, sh)
            if g < r - 1e-4: rep(tag, 'L%d %s %s (%.2f,%.2f)-(%.2f,%.2f) gap %.3f req %.2f' % (L, 'via' if u.GetClass() == 'PCB_VIA' else 'trk', un[-16:], u.GetStart().x / MM, u.GetStart().y / MM, u.GetEnd().x / MM, u.GetEnd().y / MM, g, r))
        for j, (n2, k2, t2, s2) in enumerate(new):
            if j <= i or n2 == n: continue
            if L not in lays(k2, t2): continue
            r = need(n, n2, False, False, sh, L); g = gap(shp(k2, t2, L), sh)
            if g < r - 1e-4: rep(tag, 'NEW', n2[-16:], k2, 'gap %.3f req %.2f' % (g, r))
        for z in b.Zones():
            zn = str(z.GetNetname())
            if not z.IsOnLayer(L): continue
            if z.GetIsRuleArea():
                nm = z.GetZoneName()
                if (nm.startswith('BKO') and L == pcbnew.B_Cu and ncls(n) not in ('GND', 'PVDD', 'POWER_HI', 'SPK_OUT', 'SWITCH', 'PWR_5V', 'PWR_3V')) or nm == 'BM83_ANTENNA_KEEPOUT':
                    if z.Outline().Collide(sh): rep(tag, 'rulearea', nm)
                continue
            if zn in (n, '', 'GND'): continue
            if L == pcbnew.In2_Cu:
                if kind == 'via':
                    if z.Outline().Collide(sh): print('  note: via inside In2 island', z.GetZoneName(), tag)
                elif z.Outline().Collide(sh, int(0.3 * MM) - 1000): rep(tag, 'In2 track < 0.3 to island', z.GetZoneName())
                continue
            if z.HasFilledPolysForLayer(L) and z.GetFilledPolysList(L).Collide(sh, int(max(0.2, req(ncls(n), ncls(zn), False, False)) * MM) - 1000):
                rep(tag, 'L%d cuts pour %s %s' % (L, z.GetZoneName(), zn[-14:]))
print('OK' if bad == 0 else 'BAD %d' % bad, len(new), 'items')
