"""route_r6a_lib.py : small pcbnew helpers for the R6a power phase (zones, tracks, vias, rule areas). Run in the KiCad flatpak python."""
import pcbnew, math
MM = 1e6
LAY = {'F': pcbnew.F_Cu, '1': pcbnew.In1_Cu, '2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
def V(x, y): return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
def net(b, n):
    ni = b.FindNet(n)
    if ni is None: raise KeyError(n)
    return ni
def full(n, b):
    """resolve short net names (SYS_RAW -> /SYS_RAW)"""
    if b.FindNet(n) is not None: return n
    for k in b.GetNetsByName().keys():
        k = str(k)
        if k.endswith('/' + n): return k
    raise KeyError(n)
def rect(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
def zone(b, n, lay, pts, prio=1, clr=0.3, minw=0.2, name='', conn='full', remove_islands=True, lock=True, spoke=0.5):
    z = pcbnew.ZONE(b)
    ls = pcbnew.LSET()
    for l in lay: ls.AddLayer(LAY[l])
    z.SetLayerSet(ls)
    if n: z.SetNet(net(b, full(n, b)))
    z.SetZoneName(name)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(int(round(x * MM)), int(round(y * MM)))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(int(clr * MM)); z.SetMinThickness(int(minw * MM))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if conn == 'full' else pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(int(0.25 * MM)); z.SetThermalReliefSpokeWidth(int(spoke * MM))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS if remove_islands else pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    z.SetLocked(lock)
    b.Add(z); return z
def rule_area(b, name, pts, layers='F12B', tracks=False, vias=False, zones=False):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName(name)
    ls = pcbnew.LSET()
    for l in layers: ls.AddLayer(LAY[l])
    z.SetLayerSet(ls)
    z.SetDoNotAllowZoneFills(zones); z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(int(round(x * MM)), int(round(y * MM)))
    z.SetLocked(True); b.Add(z); return z
def trk(b, n, lay, pts, w, lock=True):
    out = []
    for a, c in zip(pts[:-1], pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c)); t.SetLayer(LAY[lay]); t.SetWidth(int(round(w * MM)))
        t.SetNet(net(b, full(n, b))); t.SetLocked(lock); b.Add(t); out.append(t)
    return out
def via(b, n, x, y, d=0.6, dr=0.3, lock=True):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(int(round(d * MM))); v.SetDrill(int(round(dr * MM))); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net(b, full(n, b))); v.SetLocked(lock); b.Add(v); return v
def fp(b, ref):
    for f in b.GetFootprints():
        if f.GetReference() == ref: return f
def pad(b, ref, num):
    for p in fp(b, ref).Pads():
        if str(p.GetNumber()) == str(num): return p
def via_in_pad(p, x, y, r):
    """True if a circle (x,y,r) mm lies fully inside pad p (F.Cu)"""
    sh = p.GetEffectivePolygon(pcbnew.F_Cu)
    for k in range(16):
        a = 2 * math.pi * k / 16
        if not sh.Contains(V(x + r * math.cos(a), y + r * math.sin(a))): return False
    return sh.Contains(V(x, y))
def refill(b):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())

# ---- legality check for new vias (conservative: R6a .kicad_dru clearances without the neck relaxation)
import json as _json, fnmatch as _fn
_PATS = None
def ncls(n):
    global _PATS
    if _PATS is None:
        _PATS = _json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/R6a.kicad_pro'))['net_settings']['netclass_patterns']
    for p in _PATS:
        if _fn.fnmatchcase(n, p['pattern']): return p['netclass']
    return 'Default'
SENS = ('Default', 'SIGNAL', 'I2C', 'AUDIO', 'I2S_CLK', 'USB')
def req(ca, cb, a_pad, b_pad):
    c = 0.2
    for x, y, xp, yp in ((ca, cb, a_pad, b_pad), (cb, ca, b_pad, a_pad)):
        if x == 'POWER_HI' and not xp and not yp: c = max(c, 0.4)
        if x in ('PVDD', 'SPK_OUT') and not xp and not yp: c = max(c, 0.3)
        if x == 'SWITCH' and y not in ('SWITCH', 'GND') and not (xp and yp): c = max(c, 1.0 if y in SENS else 0.3)
        if x == 'AUDIO' and y not in ('AUDIO', 'GND') and not xp and not yp: c = max(c, 0.5)
        if x == 'I2S_CLK' and y not in ('I2S_CLK', 'GND') and not xp and not yp: c = max(c, 0.4)
    return c
def place_via(b, n, x, y, d=0.6, dr=0.3, allow_pad_overlap=False, lock=True, extra=0.0):
    """add a via only if legal against every item; returns the via or None"""
    n = full(n, b); cn = ncls(n)
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetWidth(int(round(d * MM))); v.SetDrill(int(round(dr * MM)))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    bb = pcbnew.BOX2I(V(x - 3, y - 3), V(6, 6))
    eb = b.GetBoardEdgesBoundingBox()
    if x - d / 2 < eb.GetLeft() / MM + 0.6 or x + d / 2 > eb.GetRight() / MM - 0.6 or y - d / 2 < eb.GetTop() / MM + 0.6 or y + d / 2 > eb.GetBottom() / MM - 0.6: return None
    ps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ps, True)
    if not ps.Contains(V(x, y)): return None
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowVias() and z.Outline().Collide(V(x, y), int((d / 2 + 0.3) * MM)): return None
    for f in b.GetFootprints():
        if not bb.Intersects(f.GetBoundingBox()): continue
        for p in f.Pads():
            if not bb.Intersects(p.GetBoundingBox()): continue
            pn = str(p.GetNetname())
            if p.GetDrillSizeX() > 0:
                dd = math.hypot(p.GetX() / MM - x, p.GetY() / MM - y) - p.GetDrillSizeX() / MM / 2 - dr / 2
                if dd < 0.3: return None
            same = pn == n and pn != ''
            c = 0.0 if same else req(cn, ncls(pn) if pn else 'Default', False, True) + extra
            if same and allow_pad_overlap: continue
            for L in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu):
                if p.IsOnLayer(L) and p.GetEffectiveShape(L).Collide(v.GetEffectiveShape(L), int(max(c, 0.05 if same else 0) * MM) - 1000): return None
    for t in b.Tracks():
        if not bb.Intersects(t.GetBoundingBox()): continue
        tn = str(t.GetNetname())
        if t.GetClass() == 'PCB_VIA':
            dd = math.hypot(t.GetX() / MM - x, t.GetY() / MM - y) - t.GetDrillValue() / MM / 2 - dr / 2
            if dd < 0.3: return None
            if tn == n: continue
            c = req(cn, ncls(tn), False, False) + extra
            if t.GetEffectiveShape(pcbnew.F_Cu).Collide(v.GetEffectiveShape(pcbnew.F_Cu), int(c * MM) - 1000): return None
        else:
            if tn == n: continue
            c = req(cn, ncls(tn), False, False) + extra
            if t.GetEffectiveShape().Collide(v.GetEffectiveShape(t.GetLayer()), int(c * MM) - 1000): return None
    # foreign switch-node polygons: never put another net's via inside (fills elsewhere are re-cut around the via)
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        zn = str(z.GetNetname())
        if zn in (n, '') or ncls(zn) != 'SWITCH': continue
        if z.Outline().Collide(V(x, y), int((d / 2 + req(cn, 'SWITCH', False, False)) * MM)): return None
    v.SetNet(net(b, n)); v.SetLocked(lock); b.Add(v); return v
def track_legal(b, n, a, c, w, lay='F', extra=0.0):
    n = full(n, b); cn = ncls(n); L = LAY[lay]
    t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c)); t.SetLayer(L); t.SetWidth(int(round(w * MM)))
    sh = t.GetEffectiveShape(); bb = t.GetBoundingBox(); bb.Inflate(int(2 * MM))
    for f in b.GetFootprints():
        if not bb.Intersects(f.GetBoundingBox()): continue
        for p in f.Pads():
            if not bb.Intersects(p.GetBoundingBox()): continue
            pn = str(p.GetNetname())
            if pn == n and pn != '': continue
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                if p.GetEffectiveHoleShape().Collide(sh, int(0.3 * MM)): return False
                continue
            cc = req(cn, ncls(pn) if pn else 'Default', False, True) + extra
            if p.IsOnLayer(L) and p.GetEffectiveShape(L).Collide(sh, int(cc * MM) - 1000): return False
    for u in b.Tracks():
        if not bb.Intersects(u.GetBoundingBox()): continue
        un = str(u.GetNetname())
        if un == n: continue
        cc = req(cn, ncls(un), False, False) + extra
        if u.GetClass() == 'PCB_VIA':
            if u.GetEffectiveShape(L).Collide(sh, int(cc * MM) - 1000): return False
        elif u.GetLayer() == L and u.GetEffectiveShape().Collide(sh, int(cc * MM) - 1000): return False
    for z in b.Zones():
        if z.GetIsRuleArea():
            if z.GetDoNotAllowTracks() and z.IsOnLayer(L) and z.Outline().Collide(sh): return False
            continue
        zn = str(z.GetNetname())
        if zn in (n, '') or not z.IsOnLayer(L) or (zn == 'GND' and L != pcbnew.F_Cu): continue
        short_gnd = n == 'GND' and t.GetLength() <= 1.2 * MM
        if L == pcbnew.F_Cu and not short_gnd and z.Outline().Collide(sh, int(0.3 * MM)): return False   # never cut a foreign F.Cu pour
    return True
def stub_vias(b, nets=None, maxlen=1.2, log=None):
    """connect every via that touches no same-net F.Cu copper to the nearest same-net F.Cu pad with a legal straight stub"""
    out = []
    for v in list(b.Tracks()):
        if v.GetClass() != 'PCB_VIA': continue
        n = str(v.GetNetname())
        if nets is not None and n not in nets: continue
        vs = v.GetEffectiveShape(pcbnew.F_Cu); touch = False; best = None
        for f in b.GetFootprints():
            for p in f.Pads():
                if str(p.GetNetname()) != n or not p.IsOnLayer(pcbnew.F_Cu): continue
                if p.GetEffectiveShape(pcbnew.F_Cu).Collide(vs, 0): touch = True; break
                d = math.hypot(p.GetX() - v.GetX(), p.GetY() - v.GetY()) / MM
                if best is None or d < best[0]: best = (d, p)
            if touch: break
        if touch: continue
        for u in b.Tracks():
            if u is v or str(u.GetNetname()) != n: continue
            if u.GetClass() == 'PCB_VIA': continue
            if u.GetLayer() == pcbnew.F_Cu and u.GetEffectiveShape().Collide(vs, 0): touch = True; break
        if touch or best is None or best[0] > 4.0: continue
        if ncls(n) not in ('POWER_HI', 'PVDD', 'SPK_OUT', 'GND', 'PWR_5V', 'PWR_3V', 'PWR_LOCAL'): continue
        inz = False
        for z in b.Zones():
            if not z.GetIsRuleArea() and str(z.GetNetname()) == n and z.IsOnLayer(pcbnew.F_Cu) and z.Outline().Contains(v.GetPosition()): inz = True
        if inz: continue
        p = best[1]; vx, vy = v.GetX() / MM, v.GetY() / MM
        # nearest point of the pad polygon
        poly = p.GetEffectivePolygon(pcbnew.F_Cu); o = poly.Outline(0)
        pts = [(o.CPoint(k).x / MM, o.CPoint(k).y / MM) for k in range(o.PointCount())]
        cx, cy = p.GetX() / MM, p.GetY() / MM
        # aim at pad centre but stop inside the pad: use a point 0.15 mm inside the nearest edge along the line
        tx, ty = cx, cy
        L = math.hypot(tx - vx, ty - vy)
        if L < 1e-6: continue
        ok = False
        wmin = {'POWER_HI': 0.5, 'PVDD': 0.5, 'SPK_OUT': 0.5, 'SWITCH': 0.4, 'PWR_5V': 0.4}.get(ncls(n), 0.2)
        for w in [x for x in (0.6, 0.5, 0.4, 0.3, 0.25, 0.2) if x >= wmin]:
            if track_legal(b, n, (vx, vy), (tx, ty), w):
                # length outside pad
                trk(b, n, 'F', [(vx, vy), (tx, ty)], w); out.append((n, vx, vy, w)); ok = True; break
        if not ok and log is not None: log.append(('stubfail', n, vx, vy))
    return out
