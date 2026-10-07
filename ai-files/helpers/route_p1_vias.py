#!/usr/bin/env python3
"""Routing P1 via pass (derived from route_p0_zones.py): adds GND vias / rail vias into free space around EXISTING copper (tracks, vias are obstacles), islands read from the In2 zones. Original doc: Routing phase 0: GND vias (beside every decap/IC/diode/TP GND pad, arrays in exposed pads), rail vias to In2,
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


# ---- P1: existing copper is an obstacle
for t in b.Tracks():
    if t.GetClass() == 'PCB_VIA':
        p = t.GetPosition(); register_circle(p.x/M, p.y/M, t.GetWidth(pcbnew.F_Cu)/2/M)
    else:
        a, c_ = t.GetStart(), t.GetEnd(); w = t.GetWidth()/M
        L_ = math.hypot((c_.x-a.x)/M, (c_.y-a.y)/M); n_ = max(1, int(L_/0.1))
        for i_ in range(n_+1):
            register_circle((a.x+(c_.x-a.x)*i_/n_)/M, (a.y+(c_.y-a.y)*i_/n_)/M, w/2)

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

# ---------------- 1b. islands = existing In2 zones
ISL = []
HI_NETS_ = set(['/SYS_RAW','/Battery_Charger/BAT_INT','/Fuel_Gauge_Power/BAT_PACK','/Battery_Charger/PACK_RAW','/Battery_Charger/VBUS_PD','/USB_VBUS','/Battery_Charger/PMID','/Amplifiers/PVDD_AMP'])
for z in b.Zones():
    if z.GetIsRuleArea() or not z.IsOnLayer(pcbnew.In2_Cu) or z.GetNetname() in ('', 'GND'): continue
    bb = z.GetBoundingBox()
    nn = z.GetNetname()
    ISL.append((z.GetZoneName() or nn, nn, (bb.GetLeft()/M, bb.GetTop()/M, bb.GetRight()/M, bb.GetBottom()/M), V8 if nn in HI_NETS_ else V6, False))
print('islands', len(ISL))
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
            if any(t.GetClass() == 'PCB_VIA' and t.GetNetCode() == code and math.hypot((t.GetPosition().x-p.GetPosition().x)/M, (t.GetPosition().y-p.GetPosition().y)/M) < 3.0 for t in b.Tracks()): continue
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


n_rail = sum(rail_via.values())
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(OUT, b)
json.dump({'gnd_vias_total': n_gnd_via, 'rail_vias': n_rail, 'arrays': arr_count, 'rail_via': dict(rail_via), 'rail_fail': dict(rail_fail), 'failures': [[str(x) for x in f] for f in failures]}, open(REP, 'w'), indent=0)
print('done gnd', n_gnd_via, 'rail', n_rail, 'fail', len(failures))
