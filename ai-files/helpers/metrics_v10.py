# -*- coding: utf-8 -*-
"""Placement v10 metrics (read only). Run with the KiCad python:
  flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --command=python3 org.kicad.KiCad ai-files/helpers/metrics_v10.py board.kicad_pcb out.json
Per-device decoupling (cap pad centre -> nearest pin of the named pin group, centre to centre, mm), class-D inductor pad gap to its OUT pin,
crystals, USB D+/D- chain, BM83 supply/antenna, I2S source->sink distances, board area, test points to edge, holes, via room beside GND pads,
1 mm escape band around the power ICs."""
import sys, json, math, collections, re
import pcbnew
B = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else None
bd = pcbnew.LoadBoard(B)
MM = 1e6
fp = {f.GetReference(): f for f in bd.GetFootprints()}
R = {}


def pads(ref, pins=None):
    return [p for p in fp[ref].Pads() if pins is None or p.GetNumber() in pins]


def pc(p):
    q = p.GetPosition()
    return (q.x / MM, q.y / MM)


def pbox(p):
    b = p.GetBoundingBox()
    return (b.GetX() / MM, b.GetY() / MM, b.GetRight() / MM, b.GetBottom() / MM)


def rgap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def octi(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def capval(ref):
    v = fp[ref].GetValue()
    m = re.match(r'\s*([\d.]+)\s*([pnuµm]?)', v.replace(',', '.'))
    if not m:
        return 0.0
    return float(m.group(1)) * {'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'µ': 1e-6, 'm': 1e-3, '': 1e-6}[m.group(2)]


def gndcaps(net):
    out = []
    for r, f in fp.items():
        if r[0] != 'C' or not r[1:2].isdigit():
            continue
        ps = list(f.Pads())
        if any(p.GetNetname() == 'GND' for p in ps):
            for p in ps:
                if p.GetNetname() == net:
                    out.append((r, p))
    return out


# ---------------------------------------------------------------- per-device decoupling
GROUPS = [('U6', 'PVDD 3/4', ['3', '4']), ('U6', 'PVDD 21/22', ['21', '22']), ('U6', 'DVDD 6', ['6']),
          ('U7', 'PVDD 3/4', ['3', '4']), ('U7', 'PVDD 21/22', ['21', '22']), ('U7', 'DVDD 6', ['6']),
          ('U25', 'VOUT 14-16', ['14', '15', '16']), ('U25', 'VIN 9', ['9']), ('U25', 'VCC 1', ['1']),
          ('U4', 'SYS 25', ['25']), ('U4', 'PMID 29', ['29']), ('U4', 'VBUS 2/3/8/9', ['2', '3', '8', '9']), ('U4', 'REGN 5', ['5']),
          ('U4', 'BAT 22/23', ['22', '23']),
          ('U15', 'VIN 10', ['10']), ('U15', 'VOUT 6', ['6']), ('U14', 'VIN 10', ['10']), ('U14', 'VOUT 6', ['6']),
          ('U1', '3V8_BT 23', ['23']), ('U1', 'SYS_PWR 24', ['24']), ('U1', 'VDD_IO 25', ['25']),
          ('U24', 'AVDD', None), ('U2', 'VCC', None), ('U11', 'VBUS', None), ('U3', '3V_AO', None)]
dec = []
for ic, name, pins in GROUPS:
    if ic not in fp:
        continue
    if pins is None:     # every power-ish pin of the IC that has a GND cap
        pins = [p.GetNumber() for p in fp[ic].Pads() if p.GetNetname() and p.GetNetname() != 'GND' and gndcaps(p.GetNetname())]
    gp = pads(ic, pins)
    if not gp:
        continue
    nets_ = {p.GetNetname() for p in gp}
    rows = []
    for n in nets_:
        for r, p in gndcaps(n):
            d = min(dist(pc(p), pc(q)) for q in gp if q.GetNetname() == n)
            if d <= 8.0:
                rows.append((round(d, 2), r, fp[r].GetValue(), str(fp[r].GetFPID().GetLibItemName())[:6]))
    rows.sort()
    hf = [x for x in rows if capval(x[1]) <= 1.1e-6]
    bulk = [x for x in rows if capval(x[1]) >= 4.6e-6]
    dec.append(dict(ic=ic, group=name, n2=sum(x[0] <= 2.0 for x in rows), n3=sum(x[0] <= 3.0 for x in rows), n6=sum(x[0] <= 6.0 for x in rows),
                    hf=hf[0] if hf else None, bulk=bulk[0] if bulk else None, caps=rows[:8]))
R['decoupling'] = dec

# ---------------------------------------------------------------- class-D inductors: gap OUT pin pad -> inductor pad on the same net
ind = []
for L in ('L201', 'L202', 'L203', 'L204', 'L205', 'L206'):
    if L not in fp:
        continue
    lp = [p for p in fp[L].Pads() if p.GetNetname().startswith('Net-(U6-OUT') or p.GetNetname().startswith('Net-(U7-OUT')]
    if not lp:
        continue
    n = lp[0].GetNetname()
    u = 'U6' if 'U6' in n else 'U7'
    up = [p for p in fp[u].Pads() if p.GetNetname() == n]
    g = min(rgap(pbox(a), pbox(b)) for a in lp for b in up)
    cc = min(dist(pc(a), pc(b)) for a in lp for b in up)
    # the 0.68 uF filter cap on the far pad
    far = [p for p in fp[L].Pads() if p not in lp][0]
    fc = [(round(rgap(pbox(far), pbox(p)), 2), r) for r, p in gndcaps(far.GetNetname())]
    ind.append(dict(L=L, ic=u, net=n, pad_gap=round(g, 2), centre=round(cc, 2), filter_cap=min(fc) if fc else None))
R['inductors'] = ind

# ---------------------------------------------------------------- crystals
xt = []
for Y, ic in (('Y200', 'U24'), ('Y170', 'U2')):
    for p in fp[Y].Pads():
        n = p.GetNetname()
        if n and n != 'GND':
            q = [x for x in fp[ic].Pads() if x.GetNetname() == n]
            if q:
                xt.append(dict(xtal=Y, ic=ic, net=n, pad_gap=round(rgap(pbox(p), pbox(q[0])), 2), centre=round(dist(pc(p), pc(q[0])), 2)))
R['crystals'] = xt

# ---------------------------------------------------------------- USB chain J1 -> D1 -> R171/R172 -> U2
usb = {}
for net, R_, upin in (('/USB_DP', 'R171', None), ('/USB_DN', 'R172', None)):
    j = [p for p in fp['J1'].Pads() if p.GetNetname() == net]
    d = [p for p in fp['D1'].Pads() if p.GetNetname() == net]
    rp = [p for p in fp[R_].Pads() if p.GetNetname() == net]
    rq = [p for p in fp[R_].Pads() if p.GetNetname() != net][0]
    u = [p for p in fp['U2'].Pads() if p.GetNetname() == rq.GetNetname()]
    a = min(octi(pc(x), pc(d[0])) for x in j)
    b = octi(pc(d[0]), pc(rp[0]))
    c = octi(pc(rq), pc(u[0]))
    usb[net] = dict(J1_D1=round(a, 1), D1_R=round(b, 1), R_U2=round(c, 1), total=round(a + b + c, 1),
                    J1_U2_direct=round(min(dist(pc(x), pc(u[0])) for x in j), 1))
tvs = {}
for D in ('D1', 'D5', 'D6'):
    tvs[D] = round(rgap(pbox(fp[D].Pads()[0]), (lambda b: (b.GetX() / MM, b.GetY() / MM, b.GetRight() / MM, b.GetBottom() / MM))(fp['J1'].GetBoundingBox(False))), 2)
usb['TVS_gap_to_J1_body'] = tvs
cc = {}
for net, C_ in (('/USB_CC1', 'C182'), ('/USB_CC2', 'C183')):
    cp = [p for p in fp[C_].Pads() if p.GetNetname() == net][0]
    up = [p for p in fp['U11'].Pads() if p.GetNetname() == net][0]
    jp = [p for p in fp['J1'].Pads() if p.GetNetname() == net][0]
    cc[C_] = dict(to_U11=round(dist(pc(cp), pc(up)), 1), to_J1=round(dist(pc(cp), pc(jp)), 1), J1_U11=round(octi(pc(jp), pc(up)), 1))
usb['CC'] = cc
vb = [p for p in fp['J1'].Pads() if p.GetNetname() == '/USB_VBUS']
uv = [p for p in fp['U11'].Pads() if p.GetNetname() == '/USB_VBUS']
usb['VBUS_J1_U11'] = round(min(octi(pc(a), pc(b)) for a in vb for b in uv), 1)
R['usb'] = usb

# ---------------------------------------------------------------- BM83 supply and antenna
ka = None
for z in bd.Zones():
    if z.GetZoneName() == 'BM83_ANTENNA_KEEPOUT':
        bb = z.GetBoundingBox()
        ka = (bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM)
bt = {}
p23 = pads('U1', ['23'])[0]
for r in ('U15', 'L3'):
    bt[r + '_to_U1.23'] = round(min(dist(pc(p23), pc(p)) for p in fp[r].Pads() if p.GetNetname() in ('/3V8_BT', 'Net-(U15-L1)', 'Net-(U15-L2)')), 1)
bt['U15.6_to_U1.23_octi'] = round(octi(pc(pads('U15', ['6'])[0]), pc(p23)), 1)
inside = []
if ka:
    for r, f in fp.items():
        if r == 'U1':
            continue
        b = f.GetBoundingBox(False)
        rr = (b.GetX() / MM, b.GetY() / MM, b.GetRight() / MM, b.GetBottom() / MM)
        if rgap(rr, ka) < 3.0:
            inside.append((r, round(rgap(rr, ka), 2)))
bt['parts_within_3mm_of_antenna_keepout'] = inside
R['bm83'] = bt

# ---------------------------------------------------------------- I2S: source series R (R206 SDATA, R207 BCK, R208 LRCK) -> U6/U7 pins
i2s = {}
for net, Rs in (('/I2S_SDATA', 'R206'), ('/I2S_BCK', 'R207'), ('/I2S_LRCK', 'R208')):
    s = [p for p in fp[Rs].Pads() if p.GetNetname() == net][0]
    sinks = {u: [p for p in fp[u].Pads() if p.GetNetname() == net][0] for u in ('U6', 'U7')}
    tp = [p for r, f in fp.items() if r.startswith('TP') for p in f.Pads() if p.GetNetname() == net]
    d6, d7 = octi(pc(s), pc(sinks['U6'])), octi(pc(s), pc(sinks['U7']))
    d67 = octi(pc(sinks['U6']), pc(sinks['U7']))
    i2s[net] = dict(src_U6=round(d6, 1), src_U7=round(d7, 1), U6_U7=round(d67, 1), star_max=round(max(d6, d7), 1),
                    chain=round(min(d6, d7) + d67, 1), tp_edge=None)
    if tp:
        t = pc(tp[0])
        u_ = min(sinks, key=lambda u: octi(t, pc(sinks[u])))
        i2s[net]['tp_detour'] = round(octi(t, pc(s)) + octi(t, pc(sinks[u_])) - octi(pc(s), pc(sinks[u_])), 1)     # extra length if the TP is put in line
src = pads('U24', None)
R['i2s'] = i2s

# ---------------------------------------------------------------- board
ec = bd.GetBoardEdgesBoundingBox()
W, H = ec.GetWidth() / MM, ec.GetHeight() / MM
E = (ec.GetX() / MM, ec.GetY() / MM, ec.GetRight() / MM, ec.GetBottom() / MM)
R['board'] = dict(W=round(W, 2), H=round(H, 2), area=round(W * H))


def edge_d(rr):
    return min(rr[0] - E[0], rr[1] - E[1], E[2] - rr[2], E[3] - rr[3])


tps = []
for r, f in sorted(fp.items()):
    if r.startswith('TP'):
        b = f.GetBoundingBox(False)
        rr = (b.GetX() / MM, b.GetY() / MM, b.GetRight() / MM, b.GetBottom() / MM)
        tps.append((round(edge_d(rr), 2), r, f.GetValue()))
tps.sort()
R['testpoints_edge'] = dict(min=tps[0], under3=[t for t in tps if t[0] < 3.0])
holes = []
for r, f in fp.items():
    if r.startswith('H') and f.GetValue().startswith('M3'):
        c = pc(f.Pads()[0])
        holes.append((r, round(c[0], 2), round(c[1], 2), round(min(c[0] - E[0], c[1] - E[1], E[2] - c[0], E[3] - c[1]), 2)))
R['holes'] = holes

# ---------------------------------------------------------------- via room beside GND pads of decaps (0.6 mm via, 0.2 mm clearance, within 1.0 mm of the pad edge)
allp = [(pbox(p), p.GetNetname(), r) for r, f in fp.items() for p in f.Pads()]
grid = collections.defaultdict(list)
for i, (bb, n, r) in enumerate(allp):
    for gx in range(int(bb[0] // 2) - 1, int(bb[2] // 2) + 2):
        for gy in range(int(bb[1] // 2) - 1, int(bb[3] // 2) + 2):
            grid[(gx, gy)].append(i)
crt = {}
for r, f in fp.items():
    try:
        b = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
        crt[r] = (b.GetX() / MM, b.GetY() / MM, b.GetRight() / MM, b.GetBottom() / MM)
    except Exception:
        pass


def via_ok(x, y, own):
    rv = 0.3 + 0.2
    for i in grid.get((int(x // 2), int(y // 2)), ()):
        bb, n, r = allp[i]
        if n == 'GND':
            continue
        dx = max(bb[0] - x, 0, x - bb[2]); dy = max(bb[1] - y, 0, y - bb[3])
        if math.hypot(dx, dy) < rv:
            return False
    for r, c in crt.items():           # not under another part's body (inside its courtyard), except the cap itself
        if r != own and not r.startswith('H') and c[0] + 0.1 < x < c[2] - 0.1 and c[1] + 0.1 < y < c[3] - 0.1 and r[0] in 'UQLJY':
            return False
    return True


noroom = []
ncap = 0
for r, f in fp.items():
    if r[0] != 'C' or not r[1:2].isdigit():
        continue
    for p in f.Pads():
        if p.GetNetname() != 'GND':
            continue
        ncap += 1
        bb = pbox(p)
        ok = False
        for k in range(0, 9):
            off = 0.3 + 0.1 + k * 0.1          # via edge 0.1 .. 0.9 mm from the pad edge
            cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            for x, y in ((bb[0] - off, cy), (bb[2] + off, cy), (cx, bb[1] - off), (cx, bb[3] + off),
                         (bb[0] - off * 0.75, bb[1] - off * 0.75), (bb[2] + off * 0.75, bb[1] - off * 0.75), (bb[0] - off * 0.75, bb[3] + off * 0.75), (bb[2] + off * 0.75, bb[3] + off * 0.75)):
                if via_ok(x, y, r):
                    ok = True; break
            if ok:
                break
        if not ok:
            noroom.append(r)
R['gnd_via_room'] = dict(gnd_cap_pads=ncap, without_room=sorted(noroom))

# ---------------------------------------------------------------- 1 mm escape band around the power/audio ICs: fraction of the band covered by other courtyards
band = {}
for ic in ('U4', 'U6', 'U7', 'U25', 'U11', 'U24', 'U2', 'U1', 'U15', 'U3'):
    c = crt[ic]
    tot = cov = 0
    st = 0.1
    x = c[0] - 1.0
    while x <= c[2] + 1.0:
        y = c[1] - 1.0
        while y <= c[3] + 1.0:
            if not (c[0] <= x <= c[2] and c[1] <= y <= c[3]):
                tot += 1
                if any(o != ic and q[0] <= x <= q[2] and q[1] <= y <= q[3] for o, q in crt.items()):
                    cov += 1
            y += st
        x += st
    band[ic] = round(cov / max(tot, 1), 2)
R['escape_band_covered'] = band

# ---------------------------------------------------------------- courtyard overlaps (pairwise, rectangles; DRC is authoritative)
ov = []
ks = sorted(crt)
for i, a in enumerate(ks):
    for b in ks[i + 1:]:
        A, Bq = crt[a], crt[b]
        if A[0] < Bq[2] - 0.01 and A[2] > Bq[0] + 0.01 and A[1] < Bq[3] - 0.01 and A[3] > Bq[1] + 0.01:
            ov.append((a, b))
R['courtyard_rect_overlaps'] = ov[:40]
R['courtyard_rect_overlap_count'] = len(ov)

print(json.dumps(R, indent=1)[:200000])
if OUT:
    json.dump(R, open(OUT, 'w'), indent=1)
