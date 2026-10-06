#!/usr/bin/env python3
"""Routing phase 0: GND vias (beside every decap/IC/diode/TP GND pad, arrays in exposed pads), rail vias to In2,
zones (In1 GND, B.Cu GND, In2 rail islands, F.Cu power pours + F.Cu no-pour areas around switch pads), pad zone connections.
Run inside flatpak pcbnew:  route_p0_zones.py IN.kicad_pcb OUT.kicad_pcb REPORT.json
Never moves a footprint."""
import sys, math, json, collections
import pcbnew
IN, OUT, REP = sys.argv[1:4]
M = 1e6
b = pcbnew.LoadBoard(IN)
mm = lambda v: int(round(v * M))
def net(name):
    n = b.FindNet(name)
    return n.GetNetCode() if n else None
GND = net('GND')

# ---------------- geometry derived from the board (nothing hard-coded) -------------------
def board_outline():
    ps = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(ps, True)
    o = ps.Outline(0)
    pts = [(o.CPoint(i).x/M, o.CPoint(i).y/M) for i in range(o.PointCount())]
    # drop collinear/duplicate points
    out = []
    for p in pts:
        if out and abs(out[-1][0]-p[0]) < 1e-6 and abs(out[-1][1]-p[1]) < 1e-6: continue
        out.append(p)
    return out
EDGE = board_outline()
ka = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'BM83_ANTENNA_KEEPOUT'][0].GetBoundingBox()
KEEP = (ka.GetLeft()/M, ka.GetTop()/M, ka.GetRight()/M, ka.GetBottom()/M)
EX0 = min(p[0] for p in EDGE); EX1 = max(p[0] for p in EDGE); EY0 = min(p[1] for p in EDGE); EY1 = max(p[1] for p in EDGE)
V6, V8 = (0.6, 0.3), (0.8, 0.4)
# rail nets that get an In2 island: net, plan minimum island width (mm), via size, F.Cu pour too
RAILS = [
 ('/Battery_Charger/VBUS_PD', 3.5, V8, True), ('/USB_VBUS', 3.5, V8, True), ('/SYS_RAW', 8.0, V8, True),
 ('/Battery_Charger/BAT_INT', 6.0, V8, True), ('/Fuel_Gauge_Power/BAT_PACK', 6.0, V8, True), ('/Battery_Charger/PACK_RAW', 6.0, V8, False),
 ('/Amplifiers/PVDD_AMP', 6.0, V8, True),
 ('/5V_LOGIC', 2.5, V6, False), ('/5V_CODEC', 2.5, V6, False), ('/3V8_BT', 2.5, V6, False), ('/3V3_AUDIO', 2.5, V6, False), ('/3V_AO', 2.5, V6, False),
]

# ---------------- obstacle model -------------------
class Grid:
    def __init__(s): s.c = collections.defaultdict(list)
    def add(s, key, item):
        for k in key: s.c[k].append(item)
def cells(x0, y0, x1, y1):
    return [(i, j) for i in range(int(math.floor(x0)), int(math.floor(x1)) + 1) for j in range(int(math.floor(y0)), int(math.floor(y1)) + 1)]
rect_grid = Grid(); circ_grid = Grid()
def rdist(px, py, r):
    dx = max(r[0] - px, 0, px - r[2]); dy = max(r[1] - py, 0, py - r[3])
    return math.hypot(dx, dy)
def pkey(p):
    return (p.GetParentFootprint().GetReference(), str(p.GetNumber()), p.GetPosition().x, p.GetPosition().y)
pad_rects = []   # (rect, ref, padobj)
for f in b.GetFootprints():
    for p in f.Pads():
        bb = p.GetBoundingBox()
        r = (bb.GetLeft()/M, bb.GetTop()/M, bb.GetRight()/M, bb.GetBottom()/M)
        it = {'r': r, 'pad': pkey(p), 'ref': f.GetReference()}
        pad_rects.append(it)
        rect_grid.add(cells(r[0]-1, r[1]-1, r[2]+1, r[3]+1), it)
def seg_dist(px, py, a, c):
    ax, ay = a; cx, cy = c
    dx, dy = cx-ax, cy-ay; L = dx*dx+dy*dy
    t = 0 if L == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))
EDGE_SEGS = [(EDGE[i], EDGE[(i+1) % len(EDGE)]) for i in range(len(EDGE))]
def edge_ok(x, y, rad, clr=0.5):
    if not (EX0 < x < EX1 and EY0 < y < EY1): return False
    return all(seg_dist(x, y, a, c) >= rad + clr for a, c in EDGE_SEGS)
def point_ok(x, y, rad, gap, owner, ignore_rects=()):
    if owner is not None and not isinstance(owner, tuple): owner = pkey(owner)
    """point with copper radius rad against pads, keepout, edge, placed circles"""
    if not edge_ok(x, y, rad): return False
    if rdist(x, y, KEEP) < rad + 0.3: return False
    for it in rect_grid.c.get((int(math.floor(x)), int(math.floor(y))), []):
        if it['pad'] == owner: continue
        if rdist(x, y, it['r']) < rad + gap: return False
    for (cx, cy, cr) in circ_grid.c.get((int(math.floor(x)), int(math.floor(y))), []):
        if math.hypot(x-cx, y-cy) < rad + cr + gap: return False
    return True
def register_circle(x, y, r):
    for k in cells(x-r-1, y-r-1, x+r+1, y+r+1):
        circ_grid.c[k].append((x, y, r))

vias = []; stubs = []; failures = []
def add_via(x, y, netcode, dia, drill):
    v = pcbnew.PCB_VIA(b)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetWidth(mm(dia)); v.SetDrill(mm(drill)); v.SetNetCode(netcode)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    b.Add(v); register_circle(x, y, dia/2)
    return v
def add_stub(x0, y0, x1, y1, netcode, w):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0))); t.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetWidth(mm(w)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(netcode)
    b.Add(t)
    n = max(1, int(math.hypot(x1-x0, y1-y0)/0.1))
    for i in range(n+1):
        register_circle(x0+(x1-x0)*i/n, y0+(y1-y0)*i/n, w/2)

def stub_ok(sx, sy, vx, vy, w, owner, gap=0.2):
    n = max(2, int(math.hypot(vx-sx, vy-sy)/0.05))
    for i in range(n+1):
        x = sx+(vx-sx)*i/n; y = sy+(vy-sy)*i/n
        if not point_ok(x, y, w/2, gap, owner): return False
    return True

def place_beside(fp, pad, netcode, dia, drill, w=None, label='', gap=0.2, region=None):
    bb = pad.GetBoundingBox()
    cx, cy = pad.GetPosition().x/M, pad.GetPosition().y/M
    hx, hy = bb.GetWidth()/M/2, bb.GetHeight()/M/2
    fc = fp.GetPosition(); fx, fy = fc.x/M, fc.y/M
    ax, ay = cx-fx, cy-fy
    al = math.hypot(ax, ay) or 1; ax /= al; ay /= al
    short = min(hx, hy)*2
    if w is None: w = max(0.2, min(0.4, short))
    r = dia/2
    cands = []
    dirs = [(1,0,hx),(-1,0,hx),(0,1,hy),(0,-1,hy)]
    for dx, dy, ext in dirs:
        for gi, g in enumerate((0.2, 0.3, 0.45, 0.7, 1.0, 1.5, 2.0, 2.6)):
            d = ext + g + r
            cands.append((gi, -(dx*ax+dy*ay), cx+dx*d, cy+dy*d))
    for sx_ in (1, -1):
        for sy_ in (1, -1):
            ex = math.sqrt(2)*min(hx, hy)
            for gi, g in enumerate((0.3, 0.5, 0.8, 1.2, 1.6, 2.2)):
                d = ex + g + r
                dx, dy = sx_/math.sqrt(2), sy_/math.sqrt(2)
                cands.append((gi+0.5, -(dx*ax+dy*ay), cx+dx*d, cy+dy*d))
    cands.sort(key=lambda c: (c[0], c[1]))
    for gi, _, vx, vy in cands:
        if region and not (region[0]+0.4 <= vx <= region[2]-0.4 and region[1]+0.4 <= vy <= region[3]-0.4): continue
        if not point_ok(vx, vy, r, gap, pad): continue
        # via must stay clear of own pad bbox
        if rdist(vx, vy, (bb.GetLeft()/M, bb.GetTop()/M, bb.GetRight()/M, bb.GetBottom()/M)) < r + 0.1: continue
        if not stub_ok(cx, cy, vx, vy, w, pad, gap): continue
        add_stub(cx, cy, vx, vy, netcode, w)
        v = add_via(vx, vy, netcode, dia, drill)
        vias.append((fp.GetReference(), pad.GetNumber(), vx, vy, 'beside', w))
        return True
    failures.append((fp.GetReference(), pad.GetNumber(), netcode, label))
    return False

def place_array(fp, pad, netcode, dia, drill, pitch, maxn=None):
    bb = pad.GetBoundingBox()
    cx, cy = pad.GetPosition().x/M, pad.GetPosition().y/M
    wx, wy = bb.GetWidth()/M, bb.GetHeight()/M
    marg = dia/2 + 0.05
    ux, uy = wx-2*marg, wy-2*marg
    if ux < 0 or uy < 0:
        return 0
    nx = int(ux/pitch+1e-6)+1; ny = int(uy/pitch+1e-6)+1
    if maxn:
        while nx*ny > maxn and (nx > 1 or ny > 1):
            if nx >= ny and nx > 1: nx -= 1
            elif ny > 1: ny -= 1
    px_ = pitch if nx > 1 else 0; py_ = pitch if ny > 1 else 0
    if nx > 1: px_ = min(pitch, ux/(nx-1))
    if ny > 1: py_ = min(pitch, uy/(ny-1))
    n = 0
    for i in range(nx):
        for j in range(ny):
            vx = cx + (i-(nx-1)/2)*px_; vy = cy + (j-(ny-1)/2)*py_
            rr = dia/2+0.05
            if not all(pad.HitTest(pcbnew.VECTOR2I(mm(vx+dx_), mm(vy+dy_))) for dx_, dy_ in ((0, 0), (rr, 0), (-rr, 0), (0, rr), (0, -rr))): continue
            if not point_ok(vx, vy, dia/2, 0.2, pad): continue
            # hole-to-hole vs placed circles already handled (gap 0.2 > 0.3 drill rule needs hole gap >=0.3)
            add_via(vx, vy, netcode, dia, drill); vias.append((fp.GetReference(), pad.GetNumber(), vx, vy, 'array', 0)); n += 1
    return n

# ---------------- 1. exposed-pad arrays and GND vias -------------------
arr_count = {}
GND_REFS = ('C', 'U', 'D', 'Y', 'TP', 'FB', 'L')
gnd_pad_list = []
for f in b.GetFootprints():
    ref = f.GetReference()
    if f.GetLayer() != pcbnew.F_Cu: continue
    for p in f.Pads():
        if p.GetNetCode() != GND: continue
        if p.GetAttribute() not in (pcbnew.PAD_ATTRIB_SMD,): continue
        if not any(ref.startswith(x) for x in GND_REFS): continue
        gnd_pad_list.append((f, p))
exposed = []; normal = []
for f, p in gnd_pad_list:
    bb_ = p.GetBoundingBox(); area = bb_.GetWidth()*bb_.GetHeight()/1e12
    ref = f.GetReference()
    if area >= 2.0 and (ref.startswith('U') or ref.startswith('C')) and min(bb_.GetWidth(), bb_.GetHeight())/M >= 1.2:
        exposed.append((f, p, area))
    else:
        normal.append((f, p))
# exposed first
for f, p, area in exposed:
    isU = f.GetReference().startswith('U')
    n = place_array(f, p, GND, 0.6, 0.3, 0.9 if isU else 1.2, None if isU else 4)
    arr_count[f.GetReference()+'.'+str(p.GetNumber())] = n
    if n == 0: failures.append((f.GetReference(), p.GetNumber(), GND, 'array none'))
# IC pads first, then caps/others (ICs are the more constrained)
normal.sort(key=lambda fp: (0 if fp[0].GetReference().startswith('U') else 1))
for f, p in normal:
    place_beside(f, p, GND, 0.6, 0.3, label='GND')
n_gnd_via = len(vias)

# ---------------- 1b. derive In2 islands / F.Cu pours from the pad positions -------------------
def inter(r, q, g):
    return not (r[2]+g <= q[0] or r[0] >= q[2]+g or r[3]+g <= q[1] or r[1] >= q[3]+g)
ISL = []; isl_dropped = []
placed = [(KEEP, 0.4)]
for nn, minw, via, fcu in RAILS:
    code = net(nn)
    if code is None: continue
    pads = []
    for f in b.GetFootprints():
        if f.GetLayer() != pcbnew.F_Cu or f.GetReference().startswith('TP'): continue
        for p in f.Pads():
            if p.GetNetCode() == code and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                bb = p.GetBoundingBox()
                pads.append(((bb.GetLeft()/M, bb.GetTop()/M, bb.GetRight()/M, bb.GetBottom()/M), p.GetPosition().x/M, p.GetPosition().y/M))
    par = list(range(len(pads)))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(len(pads)):
        for j in range(i+1, len(pads)):
            if math.hypot(pads[i][1]-pads[j][1], pads[i][2]-pads[j][2]) <= 10.0: par[find(i)] = find(j)
    groups = collections.defaultdict(list)
    for i in range(len(pads)): groups[find(i)].append(pads[i])
    short = nn.split('/')[-1]
    for gi, (_, cl) in enumerate(sorted(groups.items(), key=lambda kv: min(p[1] for p in kv[1]))):
        if len(cl) < 2: continue
        x0 = min(p[0][0] for p in cl)-1.0; y0 = min(p[0][1] for p in cl)-1.0
        x1 = max(p[0][2] for p in cl)+1.0; y1 = max(p[0][3] for p in cl)+1.0
        if x1-x0 < minw: c = (x0+x1)/2; x0, x1 = c-minw/2, c+minw/2
        if y1-y0 < minw: c = (y0+y1)/2; y0, y1 = c-minw/2, c+minw/2
        r = [max(x0, EX0+0.8), max(y0, EY0+0.8), min(x1, EX1-0.8), min(y1, EY1-0.8)]
        ok = True
        for _ in range(12):
            hit = [(q, g) for q, g in placed if inter(r, q, 0.5 if g != 0.4 else 0.4)]
            if not hit: break
            q, g = hit[0]; gg = 0.5 if g != 0.4 else 0.4
            opts = [[r[0], r[1], q[0]-gg, r[3]], [q[2]+gg, r[1], r[2], r[3]], [r[0], r[1], r[2], q[1]-gg], [r[0], q[3]+gg, r[2], r[3]]]
            best = None
            for o in opts:
                if o[2]-o[0] < 1.8 or o[3]-o[1] < 1.8: continue
                n_in = sum(1 for p in cl if o[0] <= p[1] <= o[2] and o[1] <= p[2] <= o[3])
                sc = (n_in, (o[2]-o[0])*(o[3]-o[1]))
                if best is None or sc > best[0]: best = (sc, o)
            if best is None or best[0][0] < 2: ok = False; break
            r = best[1]
        else:
            ok = False
        if ok and any(inter(r, q, 0.5 if g != 0.4 else 0.4) for q, g in placed): ok = False
        n_in = sum(1 for p in cl if r[0] <= p[1] <= r[2] and r[1] <= p[2] <= r[3])
        if not ok or n_in < 2:
            isl_dropped.append((nn, gi, len(cl))); continue
        r = tuple(round(v, 2) for v in r)
        placed.append((r, 0.5))
        ISL.append(('%s_%d' % (short, gi), nn, r, via, fcu))

# ---------------- 2. rail vias to In2 -------------------
HI_NETS = set(['/SYS_RAW','/Battery_Charger/BAT_INT','/Fuel_Gauge_Power/BAT_PACK','/Battery_Charger/PACK_RAW','/Battery_Charger/VBUS_PD','/USB_VBUS','/Battery_Charger/PMID','/Amplifiers/PVDD_AMP'])
rail_via = collections.Counter(); rail_fail = collections.Counter()
for name, nn, rect, (dia, drill), fcu in ISL:
    code = net(nn)
    x0, y0, x1, y1 = rect
    for f in b.GetFootprints():
        ref = f.GetReference()
        if f.GetLayer() != pcbnew.F_Cu or ref.startswith('TP') or ref.startswith('R'): continue
        for p in f.Pads():
            if p.GetNetCode() != code or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
            px, py = p.GetPosition().x/M, p.GetPosition().y/M
            if not (x0 <= px <= x1 and y0 <= py <= y1): continue
            bbx = p.GetBoundingBox()
            hi = nn in HI_NETS
            wst = 0.5 if hi else max(0.3, min(0.8, min(bbx.GetWidth(), bbx.GetHeight())/M))
            ok = False
            for d_, dr_ in ((dia, drill), (0.6, 0.3)):
                ok = place_beside(f, p, code, d_, dr_, w=wst, label='rail '+name, gap=(0.45 if hi else 0.25), region=rect)
                if ok: break
                failures.pop()
            if ok: rail_via[name] += 1
            else:
                failures.append((ref, p.GetNumber(), code, 'rail '+name)); rail_fail[name] += 1

# ---------------- 3. zones -------------------
def poly_zone(layer, netcode, pts, name, priority=0, thermal=False, clr=0.2, minw=0.25, island=True):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer); z.SetNetCode(netcode); z.SetZoneName(name)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(mm(clr)); z.SetMinThickness(mm(minw))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(mm(0.25)); z.SetThermalReliefSpokeWidth(mm(0.4 if thermal else 0.5))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    b.Add(z); return z
def inset_octagon(d):
    # offset each edge inward by d (convex polygon, clockwise or ccw: compute via normals)
    pts = EDGE; n = len(pts)
    # orientation
    area = sum(pts[i][0]*pts[(i+1)%n][1]-pts[(i+1)%n][0]*pts[i][1] for i in range(n))/2
    sgn = 1 if area > 0 else -1
    lines = []
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i+1)%n]
        dx, dy = x1-x0, y1-y0; L = math.hypot(dx, dy)
        nx, ny = -dy/L*sgn, dx/L*sgn   # inward normal
        lines.append((x0+nx*d, y0+ny*d, dx, dy))
    out = []
    for i in range(n):
        a = lines[i-1]; c = lines[i]
        det = a[2]*(-c[3]) - a[3]*(-c[2])
        t = ((c[0]-a[0])*(-c[3]) - (c[1]-a[1])*(-c[2]))/det
        out.append((a[0]+a[2]*t, a[1]+a[3]*t))
    return out
oct_in = inset_octagon(0.3)
zones = []
# GND pours keep 0.4: the zone filler ignores the .kicad_dru vbus/pvdd rules, so HI vias would otherwise sit 0.2 from GND copper
zones.append(poly_zone(pcbnew.In1_Cu, GND, oct_in, 'GND_L2', 0, False, 0.4, 0.2))
zones.append(poly_zone(pcbnew.B_Cu, GND, oct_in, 'GND_B', 0, False, 0.4, 0.2))
# overlap/gap check for islands
bad = []
for i in range(len(ISL)):
    for j in range(i+1, len(ISL)):
        a, c = ISL[i][2], ISL[j][2]
        gx = max(a[0]-c[2], c[0]-a[2]); gy = max(a[1]-c[3], c[1]-a[3])
        if max(gx, gy) < 0.5: bad.append((ISL[i][0], ISL[j][0], round(max(gx, gy), 2)))
overlaps = bad
def rect_pts(r): return [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
def ZC(nn):
    return 0.35 if nn == '/Amplifiers/PVDD_AMP' else (0.45 if nn in HI_NETS else 0.25)
pri = 1
for name, nn, rect, via, fcu in ISL:
    code = net(nn)
    if rail_via[name] > 0:
        zones.append(poly_zone(pcbnew.In2_Cu, code, rect_pts(rect), 'L3_'+name, pri, False, ZC(nn), 0.4))
    if fcu and rail_via[name] > 0:
        zones.append(poly_zone(pcbnew.F_Cu, code, rect_pts(rect), 'L1_'+name, pri, True, ZC(nn), 0.4))
    pri += 1

# F.Cu no-pour rule areas around SWITCH-class pads that overlap F.Cu pours
SW_NETS = set(['/Battery_Charger/SW1', '/Battery_Charger/SW2', 'Net-(U25-SW)', 'Net-(U14-L1)', 'Net-(U14-L2)', 'Net-(U15-L1)', 'Net-(U15-L2)'])
sw_codes = set()
for nm in list(b.GetNetsByName().keys()):
    s = str(nm)
    if s in SW_NETS or s.startswith('Net-(U6-OUT_') or s.startswith('Net-(U7-OUT_'): sw_codes.add(b.FindNet(s).GetNetCode())
fcu_rects = [r for (n_, _, r, _, f) in ISL if f and rail_via[n_] > 0]
sw_ko = 0
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetCode() in sw_codes:
            bb = p.GetBoundingBox(); m = 0.8
            r = (bb.GetLeft()/M-m, bb.GetTop()/M-m, bb.GetRight()/M+m, bb.GetBottom()/M+m)
            if any(not (r[2] < q[0] or r[0] > q[2] or r[3] < q[1] or r[1] > q[3]) for q in fcu_rects):
                z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName('SW_NOPOUR_%s_%s' % (f.GetReference(), p.GetNumber()))
                ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); z.SetLayerSet(ls)
                z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False)
                z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
                o = z.Outline(); o.NewOutline()
                for x, y in rect_pts(r): o.Append(mm(x), mm(y))
                b.Add(z); sw_ko += 1

# ---------------- 4. pad zone connections -------------------
POUR_NETS = set(net(n) for n_, n, _, _, f in ISL if f and rail_via[n_] > 0)
full = 0; therm = 0
for f in b.GetFootprints():
    ref = f.GetReference()
    for p in f.Pads():
        s = p.GetSize(); area = s.x*s.y/1e12
        code = p.GetNetCode()
        if code == GND:
            if ref.startswith('H') or ref.startswith('TP'):
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL); full += 1
            elif p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or p.GetDrillSize().x > 0:
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL); therm += 1   # hand-soldered THT: spokes
            elif area >= 2.0:
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL); full += 1
        elif code in POUR_NETS:
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL); full += 1

# ---------------- 5. fill + save -------------------
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
pcbnew.SaveBoard(OUT, b)
json.dump({'gnd_vias_total': n_gnd_via, 'vias': len(vias), 'arrays': arr_count, 'rail_via': dict(rail_via), 'rail_fail': dict(rail_fail),
           'failures': [(a, str(c), d, e) for a, c, d, e in failures], 'island_overlaps': overlaps, 'islands': [(n, nn, r) for n, nn, r, _, _ in ISL], 'islands_dropped': isl_dropped, 'edge_pts': len(EDGE), 'keep': KEEP, 'sw_nopour': sw_ko,
           'pad_full': full, 'pad_thermal': therm, 'stubs': len(stubs)}, open(REP, 'w'), indent=1)
print('done', n_gnd_via, len(vias), 'fail', len(failures), 'overlap', overlaps, 'sw_ko', sw_ko)
