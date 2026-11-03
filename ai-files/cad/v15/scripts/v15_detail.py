# -*- coding: utf-8 -*-
"""v15 detail helpers, exec'd into build_speaker_cad.py's namespace (needs box, cyl, fuse, tr, V, Rot, Pl, Part, math, P, ...).

Owner requests 2026-11-03 (coordinator brief):
  - real wires (swept insulation, colours, bend radius >= 6 x OD, routed through free space and the grommet), real crimps and housings
    (Molex Micro-Fit 43645-0300 + 43030 crimps on J5; JST VHR-2N + SVH-21T-P1.1 on J9-J11; JST PH on the woofer pigtail),
  - the 1S4P brick as a vendor-built pack (wrap, nickel, per-cell fusible links, fish paper, PCM, NTC) seated in the cradle with the strap,
  - countersunk post-Torx T10 M3x10 (Hobson, boltandnut.com.au) with 6.0 x 90 deg countersinks; cup washers on the ND65 flange.
Sources and accuracy are recorded per object in model_source() and in work/meta.json 'wiring'.
"""

# ------------------------------------------------------------------ path geometry: polyline with fillet arcs
def _vec(a):
    return V(*a) if not isinstance(a, V) else V(a)

def fillet_path(pts, R):
    """pts: list of 3-tuples; R: float or list (per interior vertex). Returns (prims, length, rmin_used, notes).
    prims: ('L', a, b) or ('A', a, m, b, centre, radius)."""
    P_ = [_vec(p) for p in pts]
    n = len(P_)
    Rs = R if isinstance(R, (list, tuple)) else [R] * max(0, n - 2)
    trims = [0.0] * n
    ang = [0.0] * n
    notes = []
    for i in range(1, n - 1):
        d1 = (P_[i] - P_[i - 1]); d1.normalize()
        d2 = (P_[i + 1] - P_[i]); d2.normalize()
        c = max(-1.0, min(1.0, d1.dot(d2)))
        th = math.acos(c)
        ang[i] = th
        trims[i] = Rs[i - 1] * math.tan(th / 2) if th > 1e-6 else 0.0
    # check segment lengths
    for i in range(n - 1):
        L = (P_[i + 1] - P_[i]).Length
        if trims[i] + trims[i + 1] > L + 1e-6:
            notes.append('segment %d (%.2f mm) shorter than the fillet trims %.2f + %.2f' % (i, L, trims[i], trims[i + 1]))
    prims = []
    cur = P_[0]
    rmin = 1e9
    for i in range(1, n - 1):
        if ang[i] < 1e-6:
            continue
        d1 = (P_[i] - P_[i - 1]); d1.normalize()
        d2 = (P_[i + 1] - P_[i]); d2.normalize()
        a = P_[i] - d1 * trims[i]
        b = P_[i] + d2 * trims[i]
        if (a - cur).Length > 0.02:
            prims.append(('L', cur, a))
        else:
            a = cur
        bis = d2 - d1; bis.normalize()
        Rr = Rs[i - 1]
        centre = P_[i] + bis * (Rr / math.cos(ang[i] / 2))
        mdir = P_[i] - centre; mdir.normalize()
        m = centre + mdir * Rr
        prims.append(('A', a, m, b, centre, Rr))
        rmin = min(rmin, Rr)
        cur = b
    if (P_[-1] - cur).Length > 0.02:
        prims.append(('L', cur, P_[-1]))
    return prims

def prims_edges(prims):
    es = []
    for p in prims:
        if p[0] == 'L':
            es.append(Part.LineSegment(p[1], p[2]).toShape())
        else:
            es.append(Part.Arc(p[1], p[2], p[3]).toShape())
    return es

def sample_prims(prims, step=0.5):
    """dense samples (point, unit tangent) along the primitives"""
    out = []
    for p in prims:
        if p[0] == 'L':
            a, b = p[1], p[2]
            d = b - a; L = d.Length
            if L < 1e-9:
                continue
            t = d * (1.0 / L)
            k = max(1, int(math.ceil(L / step)))
            for j in range(k):
                out.append((a + d * (j / k), V(t)))
        else:
            e = Part.Arc(p[1], p[2], p[3]).toShape()
            L = e.Length
            k = max(2, int(math.ceil(L / step)))
            u0, u1 = e.FirstParameter, e.LastParameter
            for j in range(k):
                u = u0 + (u1 - u0) * j / k
                t = e.tangentAt(u); t.normalize()
                out.append((e.valueAt(u), t))
    last = prims[-1]
    endp = last[2] if last[0] == 'L' else last[3]
    if last[0] == 'L':
        t = last[2] - last[1]; t.normalize()
    else:
        e = Part.Arc(last[1], last[2], last[3]).toShape(); t = e.tangentAt(e.LastParameter); t.normalize()
    out.append((V(endp), t))
    return out

def transport(samples, n0):
    """parallel-transport a unit normal n0 (perpendicular to the first tangent) along the samples (rotation-minimising frame)"""
    t0 = samples[0][1]
    n = n0 - t0 * n0.dot(t0); n.normalize()
    frames = [(samples[0][0], t0, V(n))]
    for k in range(1, len(samples)):
        p, t = samples[k]
        tp = frames[-1][1]
        ax = tp.cross(t)
        s = ax.Length
        if s > 1e-9:
            ang_ = math.atan2(s, tp.dot(t))
            ax.normalize()
            r = Rot(ax, math.degrees(ang_))
            n = r.multVec(n)
        n = n - t * n.dot(t); n.normalize()
        frames.append((p, t, V(n)))
    return frames

def offset_points(frames, offs):
    """offs: function s(mm) -> (a, b) offsets along n and t x n"""
    pts = []
    s = 0.0
    prev = None
    for (p, t, n) in frames:
        if prev is not None:
            s += (p - prev).Length
        prev = p
        a, b = offs(s)
        bn = t.cross(n)
        pts.append(p + n * a + bn * b)
    return pts

def curve_stats(pts):
    L = sum((pts[i + 1] - pts[i]).Length for i in range(len(pts) - 1))
    rmin = 1e9
    for i in range(2, len(pts) - 2, 2):
        a, b, c = pts[i - 2], pts[i], pts[i + 2]
        ab, bc, ca = (b - a).Length, (c - b).Length, (a - c).Length
        cr = (b - a).cross(c - a).Length
        if cr > 1e-9:
            rmin = min(rmin, ab * bc * ca / (2 * cr))
    return L, rmin

def sweep_circle_on(edge_or_wire, r, start_pt, start_t):
    w = edge_or_wire if isinstance(edge_or_wire, Part.Wire) else Part.Wire([edge_or_wire])
    circ = Part.Wire([Part.makeCircle(r, start_pt, start_t)])
    errs = []
    for how in ('pipeshell', 'frenet'):
        try:
            if how == 'pipeshell':
                s = w.makePipeShell([circ], True, False)
            elif how == 'pipe':
                s = w.makePipe(Part.Face(circ))
            else:
                s = w.makePipeShell([circ], True, True)
            if s.isValid() and abs(s.Volume) > 0:
                bb_ = s.BoundBox; bb_.enlarge(1.0)
                cv = s.common(Part.makeBox(bb_.XLength, bb_.YLength, bb_.ZLength, V(bb_.XMin, bb_.YMin, bb_.ZMin))).Volume
                if s.Volume < 0 or abs(cv - abs(s.Volume)) > 0.01 * abs(s.Volume) + 0.01:     # inside-out pipe solid
                    s = s.copy(); s.reverse()
                return s
            errs.append(how + ': invalid')
        except Exception as ex:
            errs.append('%s: %s' % (how, str(ex)[:60]))
    skipped.append('wire sweep failed (%s); fallback tube' % '; '.join(errs))
    pts = [w.valueAt(w.FirstParameter)] if False else [v.Point for v in w.Vertexes]
    ed = w.discretize(Distance=1.0)
    hs = [cyl(r, (b_ - a_).Length, a_, b_ - a_) for a_, b_ in zip(ed[:-1], ed[1:]) if (b_ - a_).Length > 1e-6]
    return Part.makeCompound(hs)

def wire_solid_from_points(pts, r):
    bs = Part.BSplineCurve()
    bs.interpolate(pts)
    e = bs.toShape()
    t = e.tangentAt(e.FirstParameter); t.normalize()
    return sweep_circle_on(e, r, pts[0], t)

def wire_solid_from_prims(prims, r):
    w = Part.Wire(prims_edges(prims))
    p0 = prims[0][1]
    t = (prims[0][2] - prims[0][1]) if prims[0][0] == 'L' else None
    if t is None:
        e = Part.Arc(prims[0][1], prims[0][2], prims[0][3]).toShape(); t = e.tangentAt(e.FirstParameter)
    t.normalize()
    return sweep_circle_on(w, r, p0, t)

WIRING = []          # cut list / meta
def add_wire(name, cable, gauge, od, colour_name, solid, length, rmin, ends, terms, note=''):
    cols = {'red': (0.80, 0.10, 0.08), 'black': (0.06, 0.06, 0.06), 'white': (0.92, 0.92, 0.88), 'yellow': (0.92, 0.80, 0.10)}
    add(name, 'wiring', solid, cols[colour_name])
    WIRING.append(dict(name=name, cable=cable, gauge=gauge, od_mm=od, colour=colour_name, length_mm=round(length, 1),
                       cut_length_mm=int(5 * math.ceil((length + 8.0) / 5.0)), min_bend_radius_mm=round(rmin, 2),
                       bend_ratio=round(rmin / od, 2), meets_6xOD=bool(rmin >= 6 * od - 0.05), ends=ends, terminations=terms, note=note))

def single_wire(name, cable, gauge, od, colour, pts, R, ends, terms, note=''):
    prims = fillet_path(pts, R)
    sol = wire_solid_from_prims(prims, od / 2)
    L = sum((e.Length) for e in prims_edges(prims))
    rads = [p[5] for p in prims if p[0] == 'A']
    rmin = min(rads) if rads else 1e9
    add_wire(name, cable, gauge, od, colour, sol, L, rmin, ends, terms, note)
    return prims

def multi_wire(names, cable, gauges, ods, colours, pts, R, n0, offsets, ends, terms, note=''):
    """several wires following one centreline (pair/ribbon) with offsets(s) along the transported normal"""
    prims = fillet_path(pts, R)
    fr = transport(sample_prims(prims, 0.5), n0)
    res = []
    for k, nm in enumerate(names):
        op = offset_points(fr, lambda s, k=k: offsets(s)[k])
        sol = wire_solid_from_points(op, ods[k] / 2)
        L, rmin = curve_stats(op)
        add_wire(nm, cable, gauges[k], ods[k], colours[k], sol, L, rmin, ends[k], terms[k], note)
        res.append(op)
    return prims, fr, res

def multi_wire_exact(names, cable, gauges, ods, colours, pts, R, n0, sgns, d0, d1, ends, terms, note='', ext=None):
    """wires offset by sgn_k * d along a rotation-minimising normal of the filleted centreline, built EXACTLY from lines and arcs
    (offset arcs stay arcs). The offset d changes from d0 to d1 only on the first straight of >= 15 mm (a straight taper);
    ext: optional per-wire straight extension (mm) at the end. Returns (prims, end point, end tangent, end normal, wire end points)."""
    prims = fillet_path(pts, R)
    t0 = (prims[0][2] - prims[0][1]) if prims[0][0] == 'L' else Part.Arc(prims[0][1], prims[0][2], prims[0][3]).toShape().tangentAt(0)
    t0.normalize()
    n = n0 - t0 * n0.dot(t0); n.normalize()
    d = d0; done = d0 == d1
    edges = [[] for _ in names]
    radii = [[] for _ in names]
    for p in prims:
        if p[0] == 'L':
            a_, b_ = p[1], p[2]
            ds = de = d
            if not done and (b_ - a_).Length >= 15.0:
                ds, de = d0, d1; d = d1; done = True
            for k, sg in enumerate(sgns):
                edges[k].append(Part.LineSegment(a_ + n * (sg * ds), b_ + n * (sg * de)).toShape())
        else:
            a_, m_, b_, C, Rr = p[1], p[2], p[3], p[4], p[5]
            u, v = a_ - C, b_ - C
            ax = u.cross(v); ax.normalize()
            th = math.degrees(math.acos(max(-1.0, min(1.0, u.dot(v) / (u.Length * v.Length)))))
            nm = Rot(ax, th / 2).multVec(n); ne = Rot(ax, th).multVec(n)
            for k, sg in enumerate(sgns):
                e_ = Part.Arc(a_ + n * (sg * d), m_ + nm * (sg * d), b_ + ne * (sg * d)).toShape()
                edges[k].append(e_)
                radii[k].append(e_.Curve.Radius)
            n = ne
    last = prims[-1]
    p_end = last[2] if last[0] == 'L' else last[3]
    t_end = (last[2] - last[1]) if last[0] == 'L' else Part.Arc(last[1], last[2], last[3]).toShape().tangentAt(Part.Arc(last[1], last[2], last[3]).toShape().LastParameter)
    t_end.normalize()
    wends = []
    for k, nm_ in enumerate(names):
        e0 = edges[k][-1]
        q = e0.valueAt(e0.LastParameter)
        if ext and ext[k] > 0:
            edges[k].append(Part.LineSegment(q, q + t_end * ext[k]).toShape()); q = q + t_end * ext[k]
        wr = Part.Wire(edges[k])
        st = edges[k][0]; tt = st.tangentAt(st.FirstParameter); tt.normalize()
        sol = sweep_circle_on(wr, ods[k] / 2, st.valueAt(st.FirstParameter), tt)
        rmin = min(radii[k]) if radii[k] else 1e9
        add_wire(nm_, cable, gauges[k], ods[k], colours[k], sol, wr.Length, rmin, ends[k], terms[k], note)
        wends.append(q)
    return prims, p_end, t_end, n, wends

def ramp(s, pts_):
    """piecewise-linear profile [(s, v), ...]"""
    if s <= pts_[0][0]:
        return pts_[0][1]
    for (s0, v0), (s1, v1) in zip(pts_[:-1], pts_[1:]):
        if s <= s1:
            return v0 + (v1 - v0) * (s - s0) / (s1 - s0)
    return pts_[-1][1]

def oriented_box(c, ex, ey, ez, sx, sy, sz):
    """box of size (sx along ex, sy along ey, sz along ez) centred at c"""
    return _place(Part.makeBox(sx, sy, sz, V(-sx / 2, -sy / 2, -sz / 2)), ex, ey, ez, c)

def _place(shape, ex, ey, ez, c):
    s = shape.copy()
    m = App.Matrix(ex.x, ey.x, ez.x, 0, ex.y, ey.y, ez.y, 0, ex.z, ey.z, ez.z, 0, 0, 0, 0, 1)
    s.Placement = Pl(c, Rot(m))
    return s

# ------------------------------------------------------------------ countersunk post-Torx T10 M3 (Hobson Engineering via boltandnut.com.au)
CSK = dict(dk=5.90, k=2.00, angle=90, d=3.0, drive='T10 post (pin) Torx', A=2.74, B=1.97, depth=1.1, pin=0.9,
           src='boltandnut.com.au product page (fetched 2026-11-03): head dia 5.90, head height 2.00, 90 deg, T10 post Torx, A2-70 G304, full thread, '
               'product dia 2.87-2.98; MPN list YCXSA2M3X6/8/10/12/16/20/25')
def csk_screw(L):
    """origin = head top centre, +z out of the material, shank along -z (overall length L incl. head).
    Head: 0.55 mm cylinder dia 5.90 + 90 deg cone to dia 3.0 (1.45): totals the 2.00 head height of the vendor page."""
    r_k = CSK['dk'] / 2
    head = cyl(r_k, 0.55, V(0, 0, -0.55)).fuse(Part.makeCone(1.5, r_k, 1.45, V(0, 0, -2.0)))
    star = []
    for i in range(12):
        rr = CSK['A'] / 2 if i % 2 == 0 else CSK['B'] / 2
        a_ = math.radians(30 * i)
        star.append(V(rr * math.cos(a_), rr * math.sin(a_), -CSK['depth']))
    star.append(star[0])
    rec = Part.Face(Part.makePolygon(star)).extrude(V(0, 0, CSK['depth'] + 0.5))
    head = head.cut(rec).fuse(cyl(CSK['pin'] / 2, CSK['depth'] + 0.01, V(0, 0, -CSK['depth'] - 0.01)))
    return head.fuse(cyl(1.5, L - 2.0 + 0.01, V(0, 0, -L))).removeSplitter()

def csk_tool(x, z, y_face, sgn):
    """6.0 x 90 deg countersink (0.6 counterbore + cone to the 3.4 clearance) in a face at y = y_face, material toward -sgn*Y... (lid: sgn=+1, face Dd)"""
    a = cyl(3.0, 0.6 + 1.0, V(x, y_face - sgn * 0.6, z), V(0, sgn, 0))
    c = Part.makeCone(1.7, 3.0, 1.3, V(x, y_face - sgn * 1.9, z), V(0, sgn, 0))
    return a.fuse(c)

CUPW = dict(od=8.0, h=1.6, src='parametric M3 stainless countersunk (cup / finishing) washer, OD 8.0 x 1.6: typical catalogue size, NOT sourced')
def cup_washer():
    """origin = bottom centre, +z out of the material"""
    outer = cyl(CUPW['od'] / 2, 0.4, V(0, 0, 0)).fuse(Part.makeCone(CUPW['od'] / 2, 3.4, 1.2, V(0, 0, 0.4)))
    inner = cyl(3.0, 0.7, V(0, 0, 1.0)).fuse(Part.makeCone(2.0, 3.0, 1.0, V(0, 0, 0))).fuse(cyl(2.0, 0.2, V(0, 0, -0.1)))
    return outer.cut(inner).removeSplitter()

# ------------------------------------------------------------------ 1S4P vendor-built brick
PACKD = {}
def build_pack_4p(cellm):
    """cells + negative nickel strip + fish paper + positive nickel with per-cell fusible links + PCM + NTC + heat-shrink wrap"""
    rc = 21.25 / 2                      # 50S max diameter incl. its own sleeve
    wt = 0.25                           # pack heat-shrink (PVC), estimate
    xs_ = [c[0] for c in CELL_POS]
    y0c = CELL_POS[0][1]                # negative end faces
    y1c = y0c + 70.62                   # positive button (50S max length)
    NI, NIc = 0.15, (0.72, 0.72, 0.70)
    for i, (cx_, cy_) in enumerate(CELL_POS):          # positive end toward +Y (the PCM end)
        add('Battery_Cell%d_21700_50S' % (i + 1), 'battery', tr(cellm, V(cx_, cy_, bz), Rot(V(0, 0, 1), V(0, 1, 0))), (0.2, 0.45, 0.8))
    add('Battery_Nickel_neg_strip', 'battery', box(xs_[0] - 6.0, xs_[-1] + 6.0, y0c - NI, y0c, bz - 4.0, bz + 4.0), NIc)
    yp0, yp1 = y1c, y1c + 0.25          # fish paper (insulation over the can shoulders), holes at the buttons
    paper = box(xs_[0] - rc + 0.5, xs_[-1] + rc - 0.5, yp0, yp1, bz - 9.5, bz + 9.2)
    for x_ in xs_:
        paper = paper.cut(cyl(3.5, 2.0, V(x_, yp0 - 1.0, bz), V(0, 1, 0)))
    add('Battery_FishPaper_pos', 'battery', paper, (0.55, 0.12, 0.10))
    yn0, yn1 = yp1, yp1 + NI            # positive nickel on the paper: pads through the holes, fusible necks, bus bar
    parts_ = []
    for x_ in xs_:
        parts_.append(cyl(3.0, yn1 - y1c, V(x_, y1c, bz), V(0, 1, 0)))                 # pad (dimpled through the paper hole onto the button)
        parts_.append(box(x_ - 0.5, x_ + 0.5, yn0, yn1, bz + 2.9, bz + 6.3))           # fusible link: 1.0 mm neck, 3.4 long
    parts_.append(box(xs_[0] - 6.0, xs_[-1] + 6.0, yn0, yn1, bz + 6.2, bz + 9.0))     # bus bar to the PCM B+
    add('Battery_Nickel_pos_fused_links', 'battery', fuse(parts_), NIc)
    ypc0 = yn1 + 0.1; ypc1 = ypc0 + 1.6          # PCM FR4 1.6, 60 x 18, components on the rear face
    pcm = box(-30.0, 30.0, ypc0, ypc1, bz - 9.0, bz + 9.0)
    add('Battery_PCM_board', 'battery', pcm, (0.1, 0.5, 0.2))
    comps = fuse([box(-24, -18, ypc1, ypc1 + 1.0, bz - 3, bz + 2), box(-14, -8, ypc1, ypc1 + 1.0, bz - 3, bz + 2),
                  box(4, 8, ypc1, ypc1 + 0.9, bz - 2, bz + 1), box(14, 17, ypc1, ypc1 + 0.6, bz - 6, bz - 4)])
    add('Battery_PCM_parts', 'battery', comps, (0.08, 0.08, 0.08))
    ymid = (y0c + y1c) / 2                          # NTC 103AT between cells 2 and 3 at mid-length, in the top valley
    add('Battery_NTC_103AT', 'battery', cyl(1.2, 3.5, V(0.0, ymid - 1.75, bz + 9.2), V(0, 1, 0)), (0.85, 0.75, 0.2))
    add('Battery_NTC_lead', 'battery', cyl(0.4, ypc0 + 0.8 - (ymid + 1.75), V(0.0, ymid + 1.75, bz + 9.6), V(0, 1, 0)), (0.92, 0.92, 0.88))
    # heat-shrink sleeve over the brick (stadium section) with 3 mm end rims; lead exit slit over the PCM pads
    def stadium(r, y0, y1):
        return fuse([box(xs_[0], xs_[-1], y0, y1, bz - r, bz + r), cyl(r, y1 - y0, V(xs_[0], y0, bz), V(0, 1, 0)), cyl(r, y1 - y0, V(xs_[-1], y0, bz), V(0, 1, 0))])
    ywf0, ywf1 = y0c - NI - wt, ypc1 + 1.1 + wt
    sleeve = stadium(rc + wt, ywf0, ywf1).cut(stadium(rc, ywf0 - 1, ywf1 + 1))
    rims = stadium(rc + wt, ywf0, ywf0 + wt).fuse(stadium(rc + wt, ywf1 - wt, ywf1)).cut(stadium(rc - 3.0, ywf0 - 1, ywf1 + 1))
    wrap = sleeve.fuse(rims).cut(box(9.5, 20.5, ypc0 - 0.2, ypc1 + 0.2, bz, bz + 12)).removeSplitter()
    add('Battery_Wrap_heatshrink', 'battery', wrap, (0.15, 0.30, 0.60))
    PACKD.update(cell_r=rc, wrap_t=wt, wrap_y=(round(ywf0, 2), round(ywf1, 2)), pcm_y=(round(ypc0, 2), round(ypc1, 2)),
                 brick_mm=(round(xs_[-1] - xs_[0] + 2 * (rc + wt), 2), round(ywf1 - ywf0, 2), round(2 * (rc + wt), 2)),
                 cradle_radial_gap=round(P['cell_r'] + P['cradle_gap'] - (rc + wt), 3), front_gap=round(ywf0 - (y0c - 1.0), 2),
                 rear_gap_to_partition=round(P['ch_y0'] - ywf1, 2), ntc=(0.0, round(ymid, 2), round(bz + 9.2, 2)), pads_y=round((ypc0 + ypc1) / 2, 2),
                 polarity='positive buttons toward +Y (PCM end, rear); negative ends toward the baffle')
    return PACKD

def strap_channel_tool():
    """0.6 mm floor channel under the strap path (strap 1.2 thick between the floor and the wrap); 45 deg on its rear (+Y) side for printing"""
    ys = CRADLE['strap_y'][0]
    y0, y1 = ys - 11.0, ys + 11.0
    return prism_yz([(y0, ZB_IN + 0.01), (y0, ZB_IN - 0.6), (y1, ZB_IN - 0.6), (y1 + 0.6, ZB_IN + 0.01)], -55.6, 55.6)

def build_strap():
    ys = CRADLE['strap_y'][0]; w = 20.0; th = 1.2; h = th / 2
    xs_ = [c[0] for c in CELL_POS]
    ro = PACKD['cell_r'] + PACKD['wrap_t'] + h
    zb_ = ZB_IN - 0.6 + 0.15 + h        # bottom run centre (0.15 above the channel floor)
    xo = 53.7 + h                       # outside the anchor blocks
    ztop_blk = ZB_IN + 6.0 + h
    def tangent(E, C, r, side):
        d = (E - C); L = d.Length; d.normalize()
        a = math.acos(r / L)
        base = math.atan2(d.z, d.x)
        t = base + side * a
        return C + V(r * math.cos(t), 0, r * math.sin(t)), t
    pts = []
    y = ys - w / 2
    def P2(x, z): return V(x, y, z)
    CR, CL = P2(xs_[-1], bz), P2(xs_[0], bz)
    ER, EL = P2(xo, ztop_blk), P2(-xo, ztop_blk)
    TR, tR = tangent(ER, CR, ro, +1)
    TL, tL = tangent(EL, CL, ro, -1)
    es = [Part.LineSegment(P2(-xo, zb_), P2(xo, zb_)).toShape(), Part.LineSegment(P2(xo, zb_), ER).toShape(), Part.LineSegment(ER, TR).toShape()]
    topR = P2(xs_[-1], bz + ro); topL = P2(xs_[0], bz + ro)
    mR = CR + V(ro * math.cos((tR + math.pi / 2) / 2), 0, ro * math.sin((tR + math.pi / 2) / 2))
    es.append(Part.Arc(TR, mR, topR).toShape())
    es.append(Part.LineSegment(topR, topL).toShape())
    tl2 = tL if tL > 0 else tL + 2 * math.pi
    mL = CL + V(ro * math.cos((math.pi / 2 + tl2) / 2), 0, ro * math.sin((math.pi / 2 + tl2) / 2))
    es.append(Part.Arc(topL, mL, TL).toShape())
    es += [Part.LineSegment(TL, EL).toShape(), Part.LineSegment(EL, P2(-xo, zb_)).toShape()]
    wcl = Part.Wire(Part.__sortEdges__(es))
    f = Part.Face(wcl)
    band = f.makeOffset2D(h, 0).cut(f.makeOffset2D(-h, 0)) if False else f.makeOffset2D(h, 0).extrude(V(0, w, 0)).cut(f.makeOffset2D(-h, 0).extrude(V(0, w, 0)))
    add('Strap_hook_loop_20mm', 'hardware', band, (0.12, 0.12, 0.14))
    PACKD['strap'] = dict(width=w, thickness=th, centreline_length_mm=round(wcl.Length, 1), y=(round(y, 2), round(y + w, 2)),
                          path='under the brick in a 0.6 mm floor channel, through both anchor tunnels, up the outer block faces, over the brick')
    return band

# ------------------------------------------------------------------ connectors (mating housings + crimps) and wiring
ND65_TABS = dict(dx=(-7.615, 6.955), tip_dy=(21.13, 22.35), top_dz=27.0, width=1.95, thick=0.5,
                 src='measured on the ND65-4 maker STEP (terminal strip on top of the basket): two flat solder tabs, about 1.95 wide x 0.5 thick, '
                     'pointing rearward; Dayton spec sheet drawing shows two solder lugs with holes; no quick-connect size stated')
def nd65_tabs(cx):
    """((x, y_tip, z_top), ...) for the driver centred at x = cx; tab order: 0 = toward -X of the axis, 1 = toward +X (mirrored for the left driver)"""
    sg = 1 if cx > 0 else -1
    out = []
    for k in range(2):
        out.append((cx + sg * ND65_TABS['dx'][k], P['drv_y_flange'] + ND65_TABS['tip_dy'][k], dzc + ND65_TABS['top_dz']))
    return out

def header_info(ref):
    sol = max(placed[ref].Solids, key=lambda q: q.Volume)
    pins = sorted([q for q in placed[ref].Solids if q is not sol and q.Volume < 60], key=lambda q: (q.BoundBox.XMin + q.BoundBox.XMax, q.BoundBox.YMin + q.BoundBox.YMax))
    return sol, pins

def vh_housing(ref, label):
    """JST VHR-2N (7.86 x 10.5 x 13.3, mated height 16.5 above the board) on a B2P-VH top-entry header + 2 x SVH-21T-P1.1"""
    body, pins = header_info(ref)
    bb = body.BoundBox
    wall = None
    for zz in (bb.ZMax - 0.3, bb.ZMax - 2.0, bb.ZMax - 4.0):
        sec = body.common(box(bb.XMin - 1, bb.XMax + 1, bb.YMin - 1, bb.YMax + 1, zz - 0.05, zz + 0.05)).BoundBox
        wall = sec if wall is None else wall.united(sec)
    base_top = PCB_TOP
    for k in range(60):
        zz = PCB_TOP + 0.1 * k
        sl = body.common(box(bb.XMin - 1, bb.XMax + 1, bb.YMin - 1, bb.YMax + 1, zz - 0.02, zz + 0.02))
        if sl.Volume > 1e-6 and sl.BoundBox.YLength > 0.8 * bb.YLength:
            base_top = zz
    lock_low = (wall.YMin + wall.YMax) / 2 < (bb.YMin + bb.YMax) / 2
    ztop = PCB_TOP + 16.5
    zbot = max(ztop - 13.3, base_top + 0.1)
    yl0, yl1 = (bb.YMax - 10.5, bb.YMax) if lock_low else (bb.YMin, bb.YMin + 10.5)
    xc = (bb.XMin + bb.XMax) / 2
    h = box(xc - 3.93, xc + 3.93, yl0, yl1, zbot, ztop)
    h = h.cut(box(wall.XMin - 0.15, wall.XMax + 0.15, wall.YMin - 0.15, wall.YMax + 0.15, zbot - 1, wall.ZMax + 0.3))
    pcs = []
    for p_ in pins:
        pb = p_.BoundBox
        px, py = (pb.XMin + pb.XMax) / 2, (pb.YMin + pb.YMax) / 2
        h = h.cut(box(px - 1.4, px + 1.4, py - 1.4, py + 1.4, zbot - 1, ztop + 1))
        c_ = box(px - 1.2, px + 1.2, py - 1.2, py + 1.2, zbot + 0.6, pb.ZMax + 2.0).cut(box(px - 0.75, px + 0.75, py - 0.75, py + 0.75, zbot, pb.ZMax + 0.5))
        c_ = c_.fuse(cyl(0.95, 1.6, V(px, py, pb.ZMax + 2.0))).fuse(cyl(1.3, ztop - 0.15 - (pb.ZMax + 3.6), V(px, py, pb.ZMax + 3.6)))
        pcs.append((px, py, c_))
    add('Housing_%s_JST_VHR-2N' % label, 'wiring', h.removeSplitter(), (0.93, 0.92, 0.86))
    for k, (px, py, c_) in enumerate(pcs):
        add('Crimp_%s_SVH-21T-P1.1_%d' % (label, k + 1), 'wiring', c_.removeSplitter(), (0.78, 0.78, 0.74))
    return [(px, py, ztop) for px, py, _ in pcs], dict(base_top=round(base_top, 2), z=(round(zbot, 2), round(ztop, 2)), lock_side='-Y' if lock_low else '+Y')

def microfit_receptacle():
    """Molex 43645-0300 receptacle (envelope ESTIMATED: drawing not obtained) on the 43650-0300 RA header + 3 x 43030 crimps.
    Towers enter the header's 2.6 mm square holes 5.0 mm; body 9.9 x 5.2 x 5.0 outside the header face; latch on top."""
    body, pins = header_info('J5')
    bb = body.BoundBox
    xf = bb.XMax
    zc = 71.0
    ys_ = sorted(set(round((q.BoundBox.YMin + q.BoundBox.YMax) / 2, 2) for q in pins))
    yc = sum(ys_) / len(ys_)
    hb = box(xf, xf + 5.0, yc - 4.95, yc + 4.95, PCB_TOP + 0.15, PCB_TOP + 5.35)
    hb = hb.fuse(box(xf + 0.5, xf + 4.0, yc - 1.5, yc + 1.5, PCB_TOP + 5.35, PCB_TOP + 6.6))
    tw = []
    for y_ in ys_:
        tw.append(box(xf - 5.0, xf + 0.01, y_ - 1.22, y_ + 1.22, zc - 1.22, zc + 1.22).cut(box(xf - 6, xf + 1, y_ - 0.55, y_ + 0.55, zc - 0.55, zc + 0.55)))
    h = hb.fuse(fuse(tw))
    crs = []
    for y_ in ys_:
        h = h.cut(box(xf + 0.2, xf + 6, y_ - 1.15, y_ + 1.15, zc - 1.15, zc + 1.15))
        c_ = box(xf + 0.3, xf + 3.2, y_ - 1.0, y_ + 1.0, zc - 1.0, zc + 1.0).fuse(cyl(0.85, 0.8, V(xf + 3.2, y_, zc), V(1, 0, 0))).fuse(cyl(1.1, 0.95, V(xf + 4.0, y_, zc), V(1, 0, 0)))
        crs.append(c_)
    add('Housing_J5_Molex_43645-0300', 'wiring', h.removeSplitter(), (0.12, 0.12, 0.12))
    for k, c_ in enumerate(crs):
        add('Crimp_J5_43030-%s_%d' % ('0007' if k == 1 else '0038', k + 1), 'wiring', c_.removeSplitter(), (0.78, 0.78, 0.74))
    return xf + 5.0, ys_, zc

def ph_pair(c_end, t, n, label_m, label_f):
    """JST PH mated pair along t starting at c_end: inline 2-pin PH male (B2B-PH-style shroud, ESTIMATED) then PHR-2 (5.8 x 4.5 x 6.0, datasheet)"""
    bn = t.cross(n)
    m_c = c_end + t * 3.25
    male = oriented_box(m_c, n, bn, t, 6.4, 4.9, 6.5)
    f_c = c_end + t * (6.5 + 3.0)
    fem = oriented_box(f_c, n, bn, t, 5.8, 4.5, 6.0)
    pins_, cr_ = [], []
    for sg in (-1, 1):
        q = c_end + n * (sg * 1.0)
        male = male.cut(oriented_box(q + t * 3.25, n, bn, t, 1.3, 1.3, 7.0))
        pins_.append(oriented_box(q + t * 3.25, n, bn, t, 1.0, 1.0, 6.3))
        fem = fem.cut(oriented_box(q + t * 9.5, n, bn, t, 1.4, 1.4, 6.2))
        cr_.append(oriented_box(q + t * 9.5, n, bn, t, 1.2, 1.2, 5.6))
    add('Housing_%s' % label_m, 'wiring', male.removeSplitter(), (0.10, 0.10, 0.10))
    add('Housing_%s' % label_f, 'wiring', fem.removeSplitter(), (0.93, 0.92, 0.86))
    for k in range(2):
        add('Crimp_%s_pin_%d' % (label_m, k + 1), 'wiring', pins_[k], (0.85, 0.75, 0.3))
        add('Crimp_%s_SPH-002T-P0.5S_%d' % (label_f, k + 1), 'wiring', cr_[k], (0.78, 0.78, 0.74))
    return c_end + t * 12.5

def pad_numbers(ref):
    """KiCad pad numbers of a footprint in CAD coordinates: {pad: (x, y)} (board file read as text)"""
    txt = open(os.environ.get('BOARD_PCB', ''), encoding='utf-8').read() if os.environ.get('BOARD_PCB') else ''
    out = {}
    if not txt:
        return out
    for blk in re.split(r'\n\t\(footprint ', txt)[1:]:
        if '"Reference" "%s"' % ref not in blk:
            continue
        mo = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
        fx, fy, fr = float(mo.group(1)), float(mo.group(2)), float(mo.group(3) or 0)
        for pm in re.finditer(r'\(pad "([^"]+)" \w+ \w+\s*\n?\s*\(at ([-\d.]+) ([-\d.]+)', blk):
            px, py = float(pm.group(2)), float(pm.group(3))
            a_ = math.radians(-fr)
            gx = fx + px * math.cos(a_) - py * math.sin(a_)
            gy = fy + px * math.sin(a_) + py * math.cos(a_)
            out[pm.group(1)] = (gx - 147.25 + P['pcb_cx'] + 0.0, 0.0)  # x in CAD = u + pcb_cx; y handled below
            out[pm.group(1)] = (gx - 147.25 + P['pcb_cx'], P['pcb_cy'] + (88.8 - gy))
        break
    return out

def nearest_pad(pads, x, y):
    if not pads:
        return None
    return min(pads, key=lambda k: (pads[k][0] - x) ** 2 + (pads[k][1] - y) ** 2)

def build_wiring():
    HAR = {}
    ZR = PCB_TOP + 16.5            # VH housing tops
    OD20, OD18, OD24, OD26 = 1.75, 1.80, 1.30, 1.00
    R20, R18 = 6 * OD20, 6 * OD18
    zrun = ZR + R20                # 95.6: horizontal runs under the top wall
    # ---------------- J9 (FRONT_L) and J10 (FRONT_R): VH housing + SVH crimps -> 20 AWG -> solder on the ND65 tabs (+ heat-shrink)
    tabsL, tabsR = nd65_tabs(-dcx), nd65_tabs(dcx)
    for ref, label, tabs in (('J9', 'J9_FrontL', tabsL), ('J10', 'J10_FrontR', tabsR)):
        ends, info = vh_housing(ref, label)
        pads = pad_numbers(ref)
        ends = sorted(ends, key=lambda e: e[0])          # by x
        pn = [nearest_pad(pads, e[0], e[1]) or str(k + 1) for k, e in enumerate(ends)]
        HAR[label] = dict(housing=info, pins=pn)
        if ref == 'J9':      # pins x -25 / -21 -> left tabs -47.95 (outer) / -33.39
            tsel = sorted(tabs, key=lambda q: q[0])          # [-47.95, -33.39]
            routes = []
            for k, (px, py, pz) in enumerate(ends):
                tx, ty, tz = tsel[k]
                yc2 = 51.5
                E = (tx, ty - 1.0, tz + OD20 / 2 + 0.03)
                pts = [(px, py, pz), (px, py, zrun), (tx, yc2, zrun), (tx, ty - 1.0 + 10.65, zrun), E]
                routes.append(pts)
        else:                # J10 pins x -61 / -57 -> forward over the left driver, across the front, up the right side, U-turn onto the right tabs
            tsel = sorted(tabs, key=lambda q: q[0])          # [33.39, 47.95]
            A_ = [e for e in ends if e[0] == max(e_[0] for e_ in ends)][0]   # -57 (inner)
            B_ = [e for e in ends if e[0] == min(e_[0] for e_ in ends)][0]   # -61 (outer)
            routes = []
            # explicit (no loop trickery): outer B -> tab 33.39, inner A -> tab 47.95
            for (e_, yf, xr, tab, ytop) in ((B_, 13.5, 72.95, tsel[0], 60.5), (A_, 17.5, 68.95, tsel[1], 56.5)):
                px, py, pz = e_
                tx, ty, tz = tab
                E = (tx, ty - 1.0, tz + OD20 / 2 + 0.03)
                routes.append([(px, py, pz), (px, py, zrun), (px, yf, zrun), (xr, yf, zrun), (xr, ytop, zrun), (tx, ytop, zrun), (tx, ty - 1.0 + 10.65, zrun), E])
            ends = [B_, A_]
        for k, pts in enumerate(routes):
            px, py, pz = pts[0]
            pnum = nearest_pad(pads, px, py) or str(k + 1)
            col = 'red' if pnum == '1' else 'black'
            tab = (pts[-1][0], pts[-1][1] + 1.0, pts[-1][2] - OD20 / 2 - 0.03)
            single_wire('Wire_%s_%s' % (label, pnum), label, '20 AWG (0.5 mm2) stranded, PVC/silicone, OD 1.75', OD20, col, pts, R20,
                        ['%s pin %s (VHR-2N, SVH-21T-P1.1)' % (ref, pnum), 'ND65-4 %s solder tab at x %.1f' % ('left' if 'L' in label else 'right', tab[0])],
                        ['JST SVH-21T-P1.1 crimp in VHR-2N', 'soldered to the ND65 solder tab'])
            # solder joint: stripped conductor (dia 0.9) along the tab top + heat-shrink tube over tab end and wire end
            ex, ey, ez = pts[-1]
            add('Solder_%s_%s_tab' % (label, pnum), 'wiring', cyl(0.45, 4.0, V(ex, ey - 4.0, tab[2] + 0.46), V(0, 1, 0)), (0.75, 0.75, 0.72))
        HAR[label]['tabs'] = [list(map(lambda v: round(v, 2), t_)) for t_ in tabs]
    # ---------------- J11 (WOOFER): VH + SVH -> 20 AWG pair -> grommet (Heyco 2000, ID 3.56) -> splice -> 24 AWG -> PH male | PHR-2 <- woofer pigtail
    ends, info = vh_housing('J11', 'J11_Woofer')
    ends = sorted(ends, key=lambda e: e[0])
    pads = pad_numbers('J11')
    pn = [nearest_pad(pads, e[0], e[1]) or str(k + 1) for k, e in enumerate(ends)]
    cx_, cy_ = (ends[0][0] + ends[1][0]) / 2, ends[0][1]
    half = (ends[1][0] - ends[0][0]) / 2
    gx, gz = P['grom_x'], P['grom_z']
    ych = P['ch_y0']
    cl = [(cx_, cy_, ZR), (cx_, cy_, zrun), (cx_, 94.0, zrun), (72.0, 94.0, zrun), (72.0, 94.0, gz), (72.0, 65.0, gz), (gx, 65.0, gz),
          (gx, 103.0, gz), (53.0, 111.0, 40.0), (53.0, 117.5, 40.0)]
    Rl = [R20, R20 + 2.0, R20, R20 + 2.0, R20, R20, R20 + 2.0, R20 + 2.0]
    d_conv = 0.90                     # pair touching through the grommet (2 x 1.75 in the 3.56 bore); taper on the 25 mm down-leg
    names = ['Wire_J11_Woofer_adapter_%s' % p_ for p_ in pn]
    cols = ['red' if p_ == '1' else 'black' for p_ in pn]
    _, p_end, t_end, n_end, wends = multi_wire_exact(names, 'J11_Woofer', ['20 AWG, OD 1.75'] * 2, [OD20] * 2, cols, cl, Rl, V(1, 0, 0), (-1, 1), half, d_conv,
        [['J11 pin %s (VHR-2N, SVH-21T-P1.1)' % p_, 'solder splice to the 24 AWG tail of the PH plug (woofer chamber)'] for p_ in pn],
        [['JST SVH-21T-P1.1 crimp in VHR-2N', 'solder splice + heat-shrink'] for p_ in pn],
        'adapter lead: passes the partition through the 6 mm grommet (Heyco 2000) as a touching pair', ext=[0.0, 8.5])
    HAR['J11_Woofer'] = dict(housing=info, pins=pn, centreline=[list(map(lambda v: round(v, 2), p_)) for p_ in cl])
    # staggered splice sleeves (heat-shrink 3.2 x 8), 24 AWG tails to the PH male at 18 mm from the centreline end
    ph0 = p_end + t_end * 18.0
    for k, q in enumerate(wends):
        add('Sleeve_J11_splice_%s' % pn[k], 'wiring', cyl(1.6, 8.0, q, t_end), (0.05, 0.05, 0.05))
        a_ = q + t_end * 8.0
        b_ = ph0 + n_end * ((-1 if k == 0 else 1) * 1.0)
        d_ = b_ - a_
        add_wire('Wire_J11_Woofer_tail_%s' % pn[k], 'J11_Woofer', '24 AWG, OD 1.2', 1.2, cols[k], cyl(0.6, d_.Length, a_, d_), d_.Length, 1e9,
                 ['splice sleeve', 'JST-PH-compatible 2-pin male (inline)'], ['solder splice + heat-shrink', 'PH male pin (crimp, non-JST inline plug)'])
    end_ph = ph_pair(ph0, t_end, n_end, 'J11_Woofer_PH_male_inline', 'Woofer_JST_PHR-2')
    # woofer pigtail (26 AWG pair, pitch 2.0) from the PHR-2 to the frame rib (+X side), R 7 (inner wire 6 = 6 x OD)
    rib = (P['woof_cx'] + 41.8, P['woof_cy'], 27.0)
    pc = [(end_ph.x, end_ph.y, end_ph.z), (end_ph.x, end_ph.y + 12.0, end_ph.z), rib]
    multi_wire_exact(['Wire_Woofer_pigtail_1', 'Wire_Woofer_pigtail_2'], 'Woofer_pigtail', ['26 AWG (woofer lead, estimated)'] * 2, [OD26] * 2, ['red', 'black'],
                     pc, 6 * OD26 + 1.0, n_end, (-1, 1), 1.0, 1.0, [['PHR-2', 'W3-2052SC frame rib'], ['PHR-2', 'W3-2052SC frame rib']],
                     [['JST SPH-002T-P0.5S in PHR-2', 'factory'], ['JST SPH-002T-P0.5S in PHR-2', 'factory']],
                     'part of the woofer (about 100 mm, photo estimate): the CAD shows the shortest route; fold the slack beside the woofer')
    # grommet: Heyco 2000 (ID 3.56) in the 1.6 mm web of the partition
    y_web = ych + t - P['grom_web']
    grom = fuse([cyl(3.0, P['grom_web'], V(gx, y_web, gz), V(0, 1, 0)), cyl(4.6, 1.0, V(gx, y_web - 1.0, gz), V(0, 1, 0)),
                 cyl(4.6, 1.0, V(gx, ych + t, gz), V(0, 1, 0))]).cut(cyl(1.78, 10, V(gx, y_web - 3, gz), V(0, 1, 0)))
    add('Grommet_Heyco2000_ID3.56', 'hardware', grom, (0.05, 0.05, 0.05))
    # ---------------- J5 pack harness: Micro-Fit 43645-0300 + 43030 crimps -> 2 x 18 AWG + 24 AWG NTC -> PCM top-edge pads
    xr0, ys_, zc = microfit_receptacle()
    pads = pad_numbers('J5')
    xdn = Wd / 2 - t - 0.65 - OD18 / 2                     # 76.95: down-leg next to the right wall
    zlev = {ys_[0]: 38.85, ys_[1]: 36.85, ys_[2]: 34.85}      # stacked -Y runs (front pin highest)
    xpad = {ys_[0]: 12.0, ys_[1]: 15.0, ys_[2]: 18.0}
    yT = PACKD.get('pads_y', 87.4)
    zpad = bz + 9.0 + 0.15
    for y_ in ys_:
        pnum = nearest_pad(pads, 60.0, y_) or str(ys_.index(y_) + 1)
        role = {'1': 'PACK+', '2': 'TS (NTC)', '3': 'GND (PACK-)'}.get(pnum, pnum)
        od, gauge, col = (OD24, '24 AWG, OD 1.3', 'white') if role.startswith('TS') else (OD18, '18 AWG thin-wall, OD 1.80', 'red' if role == 'PACK+' else 'black')
        pts = [(xr0, y_, zc), (xdn, y_, zc), (xdn, y_, zlev[y_]), (xdn, yT, zlev[y_]), (xpad[y_], yT, zlev[y_]), (xpad[y_], yT, zpad)]
        Rl = [9.5, R18, R18, R18]
        single_wire('Wire_J5_%s_%s' % (pnum, role.split(' ')[0].replace('+', 'plus').replace('-', 'minus')), 'J5_pack', gauge, od, col, pts, Rl,
                    ['J5 pin %s (%s), Molex 43645-0300' % (pnum, role), 'pack PCM top-edge pad (%s)' % role],
                    ['Molex 43030-%s crimp' % ('0007' if od < 1.5 else '0038'), 'soldered on the PCM by the pack vendor'],
                    'first bend at the receptacle R 9.5 (5.3 x OD): the receptacle faces the right wall with 11.05 mm free; 6 x OD needs 11.7' if od >= 1.8 else
                    'first bend at the receptacle R 9.5 (7.3 x OD)')
        if pnum == '2' or role.startswith('TS'):
            HAR['j5'] = [list(map(lambda v: round(v, 2), p_)) for p_ in pts]
    HAR.setdefault('j5', [[xr0, ys_[1], zc]])
    return HAR
