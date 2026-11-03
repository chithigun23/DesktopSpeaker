#!/usr/bin/env python3
"""paste_fix.py BOARD.kicad_pcb [-o OUT.kicad_pcb] [--lib FOOTPRINT_DIR] [--dry-run] [--report R.json]

Hand-assembly stencil fix (RT-15, plain python3, text-level, no pcbnew). Re-windows the F.Paste of the exposed / thermal
pads listed in TARGETS as separate paste-only pads ("window panes"), following the HA rules
(ai-files/reports/hand-assembly-research-2026-11-01.md section 1; draft-rt14/stencil-report-RT14.md):
  coverage 50-70 % of the copper pad (aim 60 %), web between panes >= 0.25 mm (WEB below), pane side >= 0.5 mm,
  no paste within VIA_CLR mm of an open via hole (board vias inside the pad and footprint thru-hole pads),
  each aperture checked later by draft-rt14/scripts/stencil_check.py (area ratio >= 0.66, aspect >= 1.5 at 0.10 mm).
Copper and solder mask are not touched: the copper pad only loses "F.Paste" from its (layers ...); the panes are
unnumbered SMD pads on F.Paste only (the convention of U19/D6/Q103/U11 in this library). Old paste-only pads that lie
inside a target pad are replaced. The result is idempotent: a second run gives a byte-identical file.

Layout search (pad frame): with holes, every combination of web lines through hole rows / columns is tried; a hole not
on a web gets a slot to the nearest pad edge; the outer inset is varied 0.05-0.50 mm (0.00-0.04 only when nothing
else reaches 50 %); the result closest to 60 % coverage wins. Without holes: an n x m grid of equal rectangles,
n = round(side / 1.0 mm), scaled to 60 %. Panes with notches are written as custom pads (one gr_poly each).
Pads where the rules cannot be met are left unchanged and reported (SKIP).

--lib DIR: the same pane layouts (computed on the board, pad frame) are written into DIR/<lib name>.kicad_mod for the
footprints of the target pads. Board vias are board items: the library layout assumes the via positions of the board
(reported per pad, pad-frame coordinates); all board instances of one library footprint must give the same layout.
"""
import sys, os, re, json, math, uuid, argparse

TARGETS = [('U6', '33'), ('U7', '33'), ('U25', '21'), ('U1', '56'), ('U10', '17'), ('U5', '9'), ('D6', '7'),
           ('Q103', '9'), ('U11', '39'), ('U11', '40')]
VIA_CLR = 0.10      # paste kept >= 0.10 mm from the edge of every open via / thru-hole drill inside the pad
WEB = 0.26          # web between panes (rule >= 0.25; 0.01 margin) for via layouts
WEB_GRID = 0.30     # web for plain grids (no holes)
MIN_SIDE = 0.50     # pane side (rule >= 0.5)
COV_LO, COV_HI, COV_AIM = 0.50, 0.70, 0.60
INSET = 0.05        # paste inset from the copper edge (preferred minimum)
UUID_NS = uuid.UUID('a57ef1c0-5e1c-4c11-9a5e-000000000015')
MARK = 'a57ef1c0'   # first 8 hex digits of every generated pad uuid


# ---------------------------------------------------------------- s-expression spans
def parse(text):
    """Return the root node; node = [head, start, end, children]; atoms are not stored (only lists)."""
    stack, root, i, n = [], None, 0, len(text)
    while i < n:
        c = text[i]
        if c == '(':
            j = i + 1
            while j < n and text[j] in ' \t\r\n': j += 1
            k = j
            if k < n and text[k] == '"':
                k += 1
                while text[k] != '"': k += 2 if text[k] == '\\' else 1
                k += 1
            else:
                while k < n and text[k] not in ' \t\r\n()': k += 1
            node = [text[j:k], i, None, []]
            if stack: stack[-1][3].append(node)
            else: root = node
            stack.append(node); i = k; continue
        if c == ')':
            node = stack.pop(); node[2] = i + 1
            if not stack: return root
        elif c == '"':
            i += 1
            while text[i] != '"': i += 2 if text[i] == '\\' else 1
        i += 1
    raise ValueError('unbalanced s-expression')


def toks(text, node):
    """Atoms directly inside node (strings unquoted), in order, skipping sub-lists."""
    s, e = node[1] + 1, node[2] - 1
    out, i, kids, ki = [], s, node[3], 0
    while i < e:
        if ki < len(kids) and i == kids[ki][1]:
            i = kids[ki][2]; ki += 1; continue
        c = text[i]
        if c in ' \t\r\n': i += 1; continue
        if c == '"':
            j = i + 1
            while text[j] != '"': j += 2 if text[j] == '\\' else 1
            out.append(text[i + 1:j]); i = j + 1; continue
        j = i
        while j < e and text[j] not in ' \t\r\n()': j += 1
        out.append(text[i:j]); i = j
    return out


def child(node, head):
    for c in node[3]:
        if c[0] == head: return c
    return None


def nums(text, node):
    return [float(t) for t in toks(text, node)[1:]]


# ---------------------------------------------------------------- geometry helpers
def rot(p, deg):
    """KiCad RotatePoint convention (y down): (x, y) -> (x cos + y sin, -x sin + y cos)."""
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return (p[0] * c + p[1] * s, -p[0] * s + p[1] * c)


def fmt(v):
    v = round(v, 6)
    if abs(v) < 5e-7: v = 0.0
    s = ('%.6f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def poly_area(pts):
    return abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2


def scan_x(pts, y):
    """x intersections of the horizontal line y with polygon pts (sorted)."""
    xs = []
    for i in range(len(pts)):
        (x1, y1), (x2, y2) = pts[i - 1], pts[i]
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    return sorted(xs)


def core_rect(pts):
    """Largest axis-aligned rectangle inside polygon pts that contains (0, 0) (custom pads)."""
    ys = sorted({round(p[1], 4) for p in pts})
    best = None
    for i in range(len(ys)):
        for j in range(i + 1, len(ys)):
            y0, y1 = ys[i], ys[j]
            if not (y0 < 0 < y1): continue
            lo, hi, ok = -1e9, 1e9, True
            samples = [y for y in ys if y0 < y < y1] + [y0 + 1e-4, y1 - 1e-4]
            samples += [(a + b) / 2 for a, b in zip([y0] + [y for y in ys if y0 < y < y1], [y for y in ys if y0 < y < y1] + [y1])]
            for y in samples:
                xs = scan_x(pts, y)
                seg = None
                for k in range(0, len(xs) - 1, 2):
                    if xs[k] <= 0 <= xs[k + 1]: seg = (xs[k], xs[k + 1])
                if seg is None: ok = False; break
                lo, hi = max(lo, seg[0]), min(hi, seg[1])
            if ok and hi > lo:
                a = (hi - lo) * (y1 - y0)
                if best is None or a > best[0]: best = (a, (lo, y0, hi, y1))
    return best[1]


class Shape:
    """Copper pad in its own frame: rect / roundrect (radius rc) / custom (core rectangle)."""

    def __init__(s, kind, size, rratio=0.0, poly=None):
        s.kind = kind
        if kind == 'custom':
            s.rect = core_rect(poly); s.area = poly_area(poly); s.rc = 0.0
        else:
            w, h = size; s.rect = (-w / 2, -h / 2, w / 2, h / 2)
            s.rc = rratio * min(w, h) if kind == 'roundrect' else 0.0
            s.area = w * h - (4 - math.pi) * s.rc ** 2
        s.lim = (-1e9, -1e9, 1e9, 1e9)       # clamp from neighbouring paste apertures (set_obstacles)
        s.bbox = s.rect if kind != 'custom' else (min(p[0] for p in poly), min(p[1] for p in poly),
                                                 max(p[0] for p in poly), max(p[1] for p in poly))

    def vrange(s, ua, ub, e, axis):
        """Allowed v-interval of the inset shape over the whole slice u in [ua, ub] (axis 'x': u = x)."""
        x0, y0, x1, y1 = s.rect
        if axis == 'y': x0, y0, x1, y1 = y0, x0, y1, x1
        U0, U1, V0, V1 = x0 + e, x1 - e, y0 + e, y1 - e
        L = s.lim if axis == 'x' else (s.lim[1], s.lim[0], s.lim[3], s.lim[2])
        U0, V0, U1, V1 = max(U0, L[0]), max(V0, L[1]), min(U1, L[2]), min(V1, L[3])
        if ua < U0 - 1e-9 or ub > U1 + 1e-9: return None
        if s.rc > e:
            r = s.rc - e; cu0, cu1 = x0 + s.rc, x1 - s.rc
            d = max(cu0 - ua, ub - cu1, 0.0)
            if d > 0:
                if d >= r: return None
                cut = r - math.sqrt(r * r - d * d)
                V0, V1 = V0 + cut, V1 - cut
        return (V0, V1) if V1 > V0 else None


def set_obstacles(shape, obst, gap):
    """Shrink the usable core so that paste stays >= gap from other apertures of the footprint (pad-frame rects)."""
    x0, y0, x1, y1 = shape.rect
    lim = [x0, y0, x1, y1]
    for o in obst:
        a = (o[0] - gap, o[1] - gap, o[2] + gap, o[3] + gap)
        if a[2] <= lim[0] or a[0] >= lim[2] or a[3] <= lim[1] or a[1] >= lim[3]: continue
        opts = [((lim[2] - a[0]) * (lim[3] - lim[1]), 2, a[0]), ((a[2] - lim[0]) * (lim[3] - lim[1]), 0, a[2]),
                ((lim[3] - a[1]) * (lim[2] - lim[0]), 3, a[1]), ((a[3] - lim[1]) * (lim[2] - lim[0]), 1, a[3])]
        _, k, v = min(opts)
        lim[k] = v
    shape.lim = tuple(lim)
    return shape.lim != shape.rect


def core(shape, e):
    x0, y0, x1, y1 = shape.rect
    L = shape.lim
    return max(x0 + e, L[0]), max(y0 + e, L[1]), min(x1 - e, L[2]), min(y1 - e, L[3])


def cluster(vals, tol=0.05):
    out = []
    for v in sorted(vals):
        if out and abs(v - out[-1][-1]) <= tol: out[-1].append(v)
        else: out.append([v])
    return [sum(c) / len(c) for c in out]


def iv_sub(iv, cuts):
    """Interval iv minus the list of intervals cuts -> list of intervals."""
    res = [iv]
    for a, b in cuts:
        nxt = []
        for lo, hi in res:
            if b <= lo or a >= hi: nxt.append((lo, hi)); continue
            if a > lo: nxt.append((lo, a))
            if b < hi: nxt.append((b, hi))
        res = nxt
    return [r for r in res if r[1] - r[0] > 1e-6]


# ---------------------------------------------------------------- pane layouts
def cell_panes(shape, cell, holes, e, axis, edge):
    """Slice one cell (u0, v0, u1, v1 in the slicing frame) into slices along u; returns list of panes
    (each a list of slices (ua, ub, lo, hi)) or None if a hole would be enclosed by paste."""
    u0, v0, u1, v1 = cell
    br = {u0, u1}
    for (hu, hv, r, slot) in holes:
        if (hu + r <= u0 or hu - r >= u1) and slot not in ('+u', '-u'): continue
        for k in range(9): br.add(min(max(hu - r + 2 * r * k / 8, u0), u1))
        if slot in ('+u', '-u'): br.add(min(max(hu, u0), u1))
    if shape.rc > e:
        x0, y0, x1, y1 = shape.rect
        if axis == 'y': x0, y0, x1, y1 = y0, x0, y1, x1
        for cu, sgn in ((x0 + shape.rc, -1), (x1 - shape.rc, 1)):
            for k in range(7): br.add(min(max(cu + sgn * (shape.rc - e) * k / 6, u0), u1))
    br = sorted(b for b in br if u0 <= b <= u1)
    slices = []
    for ua, ub in zip(br, br[1:]):
        if ub - ua < 1e-6: continue
        vr = shape.vrange(ua, ub, e, axis)
        if vr is None: slices.append((ua, ub, None)); continue
        iv = (max(v0, vr[0]), min(v1, vr[1]))
        if iv[1] <= iv[0]: slices.append((ua, ub, None)); continue
        cuts = []
        for (hu, hv, r, slot) in holes:
            if slot == '+u' and ub > hu + 1e-12: cuts.append((hv - r, hv + r))
            if slot == '-u' and ua < hu - 1e-12: cuts.append((hv - r, hv + r))
            d = max(hu - ub, ua - hu, 0.0)
            if d >= r - 1e-9: continue
            half = math.sqrt(r * r - d * d)
            a, b = hv - half, hv + half
            if slot == '+v': b = 1e9
            if slot == '-v': a = -1e9
            cuts.append((a, b))
        rest = iv_sub(iv, cuts)
        if len(rest) > 1: return None            # paste on both sides of a hole in one slice: enclosed hole
        slices.append((ua, ub, rest[0] if rest else None))
    # merge equal neighbours, split into connected panes
    panes, cur = [], []
    for ua, ub, iv in slices:
        if iv is None:
            if cur: panes.append(cur); cur = []
            continue
        if cur and (min(cur[-1][3], iv[1]) - max(cur[-1][2], iv[0]) < MIN_SIDE / 2):
            panes.append(cur); cur = []
        if cur and abs(cur[-1][2] - iv[0]) < 1e-9 and abs(cur[-1][3] - iv[1]) < 1e-9 and abs(cur[-1][1] - ua) < 1e-9:
            cur[-1] = (cur[-1][0], ub, iv[0], iv[1])
        else:
            cur.append((ua, ub, iv[0], iv[1]))
    if cur: panes.append(cur)
    return panes


def to_xy(pane, axis):
    """slices (u-range, v-range) -> list of rects (x0, y0, x1, y1) in the pad frame."""
    return [(a, lo, b, hi) if axis == 'x' else (lo, a, hi, b) for a, b, lo, hi in pane]


def outline(pane, axis):
    bot = []
    for a, b, lo, hi in pane: bot += [(a, lo), (b, lo)]
    top = []
    for a, b, lo, hi in reversed(pane): top += [(b, hi), (a, hi)]
    pts = bot + top
    clean = []
    for p in pts:
        if clean and abs(clean[-1][0] - p[0]) < 1e-9 and abs(clean[-1][1] - p[1]) < 1e-9: continue
        clean.append(p)
    if len(clean) > 1 and abs(clean[0][0] - clean[-1][0]) < 1e-9 and abs(clean[0][1] - clean[-1][1]) < 1e-9: clean.pop()
    k = 0
    while k < len(clean) and len(clean) > 4:          # drop collinear points
        a, b, c = clean[k - 1], clean[k], clean[(k + 1) % len(clean)]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) < 1e-12: clean.pop(k)
        else: k += 1
    return [(p[0], p[1]) if axis == 'x' else (p[1], p[0]) for p in clean]


def rect_dist(r, q):
    dx = max(q[0] - r[2], r[0] - q[2], 0.0); dy = max(q[1] - r[3], r[1] - q[3], 0.0)
    return math.hypot(dx, dy)


def evaluate(panes_xy, holes_xy, shape):
    """Independent check in the pad frame: coverage, min web, min pane side, min hole clearance."""
    area = sum((r[2] - r[0]) * (r[3] - r[1]) for p in panes_xy for r in p)
    web = min((rect_dist(r, q) for i in range(len(panes_xy)) for j in range(i + 1, len(panes_xy))
               for r in panes_xy[i] for q in panes_xy[j]), default=None)
    side = min(min(max(r[2] for r in p) - min(r[0] for r in p), max(r[3] for r in p) - min(r[1] for r in p)) for p in panes_xy)
    clr = min((rect_dist(r, (hx, hy, hx, hy)) - hr for p in panes_xy for r in p for hx, hy, hr in holes_xy), default=None)
    return dict(coverage=area / shape.area, paste_mm2=area, min_web=web, min_side=side, min_hole_clear=clr, panes=len(panes_xy))


def layout_holes(shape, holes_xy):
    """holes_xy: [(x, y, drill_radius)]; returns best layout dict or None."""
    hx = cluster([h[0] for h in holes_xy]); hy = cluster([h[1] for h in holes_xy])
    cand = []
    nx, ny = len(hx), len(hy)
    for mx in range(1 << nx):
        for my in range(1 << ny):
            wx = [hx[i] for i in range(nx) if mx >> i & 1]; wy = [hy[i] for i in range(ny) if my >> i & 1]
            for axis in ('x', 'y'):
                for es in (range(5, 51), range(4, -1, -1)):
                    for e100 in es:
                        e = e100 / 100
                        r = build(shape, holes_xy, wx, wy, e, axis)
                        if r is None: continue
                        m = r['metrics']
                        ok = (COV_LO <= m['coverage'] <= COV_HI and m['min_side'] >= MIN_SIDE - 1e-9 and
                              (m['min_web'] is None or m['min_web'] >= 0.25 - 1e-9) and m['min_hole_clear'] >= VIA_CLR - 1e-6)
                        if ok:
                            cand.append(((0 if e >= INSET else 1), abs(m['coverage'] - COV_AIM), len(r['panes']), e, r))
                        if e >= INSET and m['coverage'] < COV_LO: break      # more inset only lowers coverage
                        if e < INSET and m['coverage'] > COV_HI: break       # less inset only raises it
    if not cand: return None
    cand.sort(key=lambda c: c[:4])
    return cand[0][4]


def build(shape, holes_xy, wx, wy, e, axis):
    cx0, cy0, cx1, cy1 = core(shape, e)
    xs = [cx0] + [v for w in wx for v in (w - WEB / 2, w + WEB / 2)] + [cx1]
    ys = [cy0] + [v for w in wy for v in (w - WEB / 2, w + WEB / 2)] + [cy1]
    if any(b <= a for a, b in zip(xs, xs[1:])) or any(b <= a for a, b in zip(ys, ys[1:])): return None
    cells = [(xs[2 * i], ys[2 * j], xs[2 * i + 1], ys[2 * j + 1]) for i in range(len(xs) // 2) for j in range(len(ys) // 2)]
    panes_xy, outs = [], []
    for c in cells:
        hs = []
        for (hx_, hy_, hr) in holes_xy:
            r = hr + VIA_CLR
            if hx_ + r <= c[0] or hx_ - r >= c[2] or hy_ + r <= c[1] or hy_ - r >= c[3]: continue
            touches = hx_ - r < c[0] or hx_ + r > c[2] or hy_ - r < c[1] or hy_ + r > c[3]
            slot = None
            if not touches:
                # enclosed by this cell: slot to the nearest outer (pad) edge of the cell
                opts = []
                if abs(c[0] - cx0) < 1e-9: opts.append((hx_ - c[0], '-x'))
                if abs(c[2] - cx1) < 1e-9: opts.append((c[2] - hx_, '+x'))
                if abs(c[1] - cy0) < 1e-9: opts.append((hy_ - c[1], '-y'))
                if abs(c[3] - cy1) < 1e-9: opts.append((c[3] - hy_, '+y'))
                if not opts: return None
                pref = [o for o in opts if o[1][1] == ('y' if axis == 'x' else 'x')]   # slots across the slicing axis first
                slot = min(pref or opts)[1]
            hs.append((hx_, hy_, r, slot))
        if axis == 'x':
            cc = c; hh = [(a, b, r, {None: None, '+x': '+u', '-x': '-u', '+y': '+v', '-y': '-v'}[s]) for a, b, r, s in hs]
        else:
            cc = (c[1], c[0], c[3], c[2]); hh = [(b, a, r, {None: None, '+y': '+u', '-y': '-u', '+x': '+v', '-x': '-v'}[s]) for a, b, r, s in hs]
        ps = cell_panes(shape, cc, hh, e, axis, None)
        if ps is None: return None
        for p in ps:
            panes_xy.append(to_xy(p, axis)); outs.append(outline(p, axis))
    if not panes_xy: return None
    m = evaluate(panes_xy, [(a, b, r) for a, b, r in holes_xy], shape)
    return dict(kind='holes', axis=axis, webs_x=wx, webs_y=wy, inset=e, panes=outs, rects=panes_xy, metrics=m)


def layout_grid(shape):
    best = None
    for e in [INSET + 0.01 * k for k in range(0, 30)]:
        x0, y0, x1, y1 = core(shape, e)
        Lx, Ly = x1 - x0, y1 - y0
        n, m = max(1, round(Lx / 1.0)), max(1, round(Ly / 1.0))
        while n > 1 and (Lx - (n - 1) * WEB_GRID) / n < MIN_SIDE: n -= 1
        while m > 1 and (Ly - (m - 1) * WEB_GRID) / m < MIN_SIDE: m -= 1
        Px, Py = (Lx - (n - 1) * WEB_GRID) / n, (Ly - (m - 1) * WEB_GRID) / m
        if min(Px, Py) < MIN_SIDE: return None
        cmax = n * m * Px * Py / shape.area
        if cmax < COV_LO: return None
        k = min(1.0, math.sqrt(COV_AIM / cmax))
        px, py = max(MIN_SIDE, k * Px), max(MIN_SIDE, k * Py)
        if px > Px: px = Px
        if py > Py: py = Py
        if n * m * px * py / shape.area > COV_HI: py = COV_AIM * shape.area / (n * m * px)
        px, py = round(px, 3), round(py, 3)
        rects = []
        for i in range(n):
            for j in range(m):
                cx = x0 + Px / 2 + i * (Px + WEB_GRID); cy = y0 + Py / 2 + j * (Py + WEB_GRID)
                rects.append([(round(cx - px / 2, 4), round(cy - py / 2, 4), round(cx + px / 2, 4), round(cy + py / 2, 4))])
        # rounded corners: every pane corner inside the inset shape
        okc = all(shape.vrange(r[0][0], r[0][2], INSET, 'x') is not None and
                  shape.vrange(r[0][0], r[0][2], INSET, 'x')[0] <= r[0][1] + 1e-9 and
                  shape.vrange(r[0][0], r[0][2], INSET, 'x')[1] >= r[0][3] - 1e-9 for r in rects)
        if not okc: continue
        mtr = evaluate(rects, [], shape)
        if COV_LO <= mtr['coverage'] <= COV_HI:
            best = dict(kind='grid', grid=[n, m], inset=e, panes=[[(r[0][0], r[0][1]), (r[0][2], r[0][1]), (r[0][2], r[0][3]), (r[0][0], r[0][3])] for r in rects],
                        rects=rects, metrics=mtr)
            break
    return best


# ---------------------------------------------------------------- footprint access
class FP:
    def __init__(s, text, node, board):
        s.t, s.n, s.board = text, node, board
        s.ref = None
        for c in node[3]:
            if c[0] == 'property':
                tk = toks(text, c)
                if len(tk) >= 3 and tk[1] == 'Reference': s.ref = tk[2]
            if c[0] == 'fp_text':
                tk = toks(text, c)
                if len(tk) >= 3 and tk[1] == 'reference' and s.ref is None and not board: s.ref = tk[2]
        tk = toks(text, node)
        s.lib = tk[1] if len(tk) > 1 else ''
        at = child(node, 'at') if board else None
        a = nums(text, at) if at else [0, 0]
        s.pos = (a[0], a[1]); s.ang = a[2] if len(a) > 2 else 0.0
        s.pads = [c for c in node[3] if c[0] == 'pad']

    def pad_info(s, p):
        tk = toks(s.t, p)
        num, typ, kind = tk[1], tk[2], tk[3]
        at = nums(s.t, child(p, 'at')); size = nums(s.t, child(p, 'size'))
        lay = toks(s.t, child(p, 'layers'))[1:]
        dr = child(p, 'drill'); drill = nums(s.t, dr)[0] if dr is not None and len(toks(s.t, dr)) > 1 else 0.0
        rr = child(p, 'roundrect_rratio'); rratio = nums(s.t, rr)[0] if rr else 0.0
        poly = None
        if kind == 'custom':
            pr = child(p, 'primitives'); gp = child(pr, 'gr_poly'); pts = child(gp, 'pts')
            poly = [tuple(nums(s.t, xy)) for xy in pts[3] if xy[0] == 'xy']
        return dict(num=num, typ=typ, kind=kind, at=(at[0], at[1]), ang=at[2] if len(at) > 2 else 0.0, size=size,
                    layers=lay, drill=drill, rratio=rratio, poly=poly, node=p)


def frame(fp, pi):
    """Functions board/fp-local point -> pad frame."""
    rel = pi['ang'] - (fp.ang if fp.board else 0.0)

    def from_local(q):
        d = (q[0] - pi['at'][0], q[1] - pi['at'][1]); return rot(d, -rel)

    def from_board(q):
        d = rot((q[0] - fp.pos[0], q[1] - fp.pos[1]), -fp.ang); return from_local(d)

    def to_local(p):
        d = rot(p, rel); return (pi['at'][0] + d[0], pi['at'][1] + d[1])
    return from_local, from_board, to_local


def in_bbox(p, bb, tol=1e-6):
    return bb[0] - tol <= p[0] <= bb[2] + tol and bb[1] - tol <= p[1] <= bb[3] + tol


def board_vias(text, root):
    out = []
    for c in root[3]:
        if c[0] == 'via':
            at = nums(text, child(c, 'at')); dr = nums(text, child(c, 'drill'))[0]
            out.append((at[0], at[1], dr))
    return out


# ---------------------------------------------------------------- text generation
def pane_text(fp, pi, idx, poly, rects, ind, multiline, td_text, with_uuid, ci=None):
    from_local, _, to_local = frame(fp, pi)
    ang = pi['ang']
    key = '%s|%s|%s|%d' % ('board' if fp.board else 'lib', fp.ref if fp.board else fp.lib, pi['num'], idx)
    u = str(uuid.uuid5(UUID_NS, key)); u = MARK + u[8:]
    angs = (' ' + fmt(ang)) if abs(ang) > 1e-9 else ''
    if len(rects) == 1:
        r = rects[0]; c = ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2); at = to_local(c)
        head = ['(pad "" smd rect', '(at %s %s%s)' % (fmt(at[0]), fmt(at[1]), angs), '(size %s %s)' % (fmt(r[2] - r[0]), fmt(r[3] - r[1])),
                '(layers "F.Paste")']
        prim = None
    else:
        big = max(rects, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
        c = (round((big[0] + big[2]) / 2, 4), round((big[1] + big[3]) / 2, 4)); at = to_local(c)
        head = ['(pad "" smd custom', '(at %s %s%s)' % (fmt(at[0]), fmt(at[1]), angs), '(size 0.1 0.1)', '(layers "F.Paste")']
        prim = [(p[0] - c[0], p[1] - c[1]) for p in poly]
    if not multiline:
        s = ' '.join(head)
        if prim is not None:
            s += ' (options (clearance outline) (anchor rect)) (primitives (gr_poly (pts %s) (width 0) (fill yes)))' % \
                 ' '.join('(xy %s %s)' % (fmt(x), fmt(y)) for x, y in prim)
        if with_uuid: s += ' (uuid "%s")' % u
        return s + ')'
    i1 = ci if ci is not None else ind + '\t'
    step = i1[len(ind):] if i1.startswith(ind) and len(i1) > len(ind) else '  '
    i2 = i1 + step
    L = [ind + head[0]] + [i1 + h for h in head[1:]]
    if prim is not None:
        i3, i4 = i2 + step, i2 + step + step
        L += [i1 + '(options', i2 + '(clearance outline)', i2 + '(anchor rect)', i1 + ')', i1 + '(primitives', i2 + '(gr_poly',
              i3 + '(pts']
        xy = ['(xy %s %s)' % (fmt(x), fmt(y)) for x, y in prim]
        for k in range(0, len(xy), 6): L.append(i4 + ' '.join(xy[k:k + 6]))
        L += [i3 + ')', i3 + '(width 0)', i3 + '(fill yes)', i2 + ')', i1 + ')']
    if td_text: L += [i1 + l for l in td_text]
    if with_uuid: L.append(i1 + '(uuid "%s")' % u)
    L.append(ind + ')')
    return '\n'.join(L)


def line_indent(text, pos):
    s = text.rfind('\n', 0, pos) + 1
    return text[s:pos] if text[s:pos].strip() == '' else None


def remove_paste_layer(text, pnode):
    lay = child(pnode, 'layers')
    seg = text[lay[1]:lay[2]]
    new = re.sub(r'\s+"?F\.Paste"?(?=[\s)])', '', seg)
    return (lay[1], lay[2], new) if new != seg else None


def plan_fp(text, fp, targets, holes_board, layouts_in=None):
    """Return (edits, report rows, layouts) for one footprint."""
    edits, rows, lays = [], [], {}
    infos = [fp.pad_info(p) for p in fp.pads]
    for num in targets:
        cu = [pi for pi in infos if pi['num'] == num and pi['typ'] == 'smd' and 'F.Cu' in pi['layers']]
        if len(cu) != 1:
            rows.append(dict(pad='%s.%s' % (fp.ref, num), status='SKIP', reason='copper pad not found (%d)' % len(cu))); continue
        pi = cu[0]
        from_local, from_board, to_local = frame(fp, pi)
        shape = Shape(pi['kind'], pi['size'], pi['rratio'], pi['poly'])
        holes = []
        for q in infos:
            if q['drill'] > 0:
                p = from_local(q['at'])
                if in_bbox(p, shape.bbox): holes.append((round(p[0], 4), round(p[1], 4), q['drill'] / 2))
        if holes_board is not None:
            for vx, vy, vd in holes_board:
                p = from_board((vx, vy))
                if in_bbox(p, shape.bbox): holes.append((round(p[0], 4), round(p[1], 4), vd / 2))
        tgt_bb = []
        for q in infos:
            if q['num'] in targets and q['typ'] == 'smd' and 'F.Cu' in q['layers']:
                fl = frame(fp, q)[0]
                tgt_bb.append((fl, Shape(q['kind'], q['size'], q['rratio'], q['poly']).bbox))
        obst = []
        for q in infos:
            if 'F.Paste' not in q['layers'] or q is pi: continue
            if q['num'] == '' and q['layers'] == ['F.Paste'] and any(in_bbox(fl(q['at']), bb) for fl, bb in tgt_bb): continue
            if q['num'] in targets and 'F.Cu' in q['layers']: continue
            qs = Shape(q['kind'], q['size'], q['rratio'], q['poly'])
            qrel = q['ang'] - (fp.ang if fp.board else 0.0)
            cs = []
            for c in ((qs.bbox[0], qs.bbox[1]), (qs.bbox[2], qs.bbox[1]), (qs.bbox[2], qs.bbox[3]), (qs.bbox[0], qs.bbox[3])):
                d = rot(c, qrel); cs.append(from_local((q['at'][0] + d[0], q['at'][1] + d[1])))
            obst.append((min(c[0] for c in cs), min(c[1] for c in cs), max(c[0] for c in cs), max(c[1] for c in cs)))
        for g in fp.n[3]:
            if g[0] in ('fp_poly', 'fp_rect') and child(g, 'layer') is not None and 'F.Paste' in toks(text, child(g, 'layer')):
                if g[0] == 'fp_poly': ps = [tuple(nums(text, xy)) for xy in child(g, 'pts')[3] if xy[0] == 'xy']
                else: ps = [tuple(nums(text, child(g, 'start'))), tuple(nums(text, child(g, 'end')))]
                cs = [from_local(p) for p in ps]
                obst.append((min(c[0] for c in cs), min(c[1] for c in cs), max(c[0] for c in cs), max(c[1] for c in cs)))
        clamped = set_obstacles(shape, obst, max(WEB, WEB_GRID))
        key = (fp.lib, num)
        if layouts_in is not None:
            lay = layouts_in.get(key)
            if lay is None:
                rows.append(dict(pad='%s.%s' % (fp.lib, num), status='SKIP', reason='no board layout')); continue
            if [round(v, 4) for v in pi['size']] != lay['size'] or pi['kind'] != lay['shape']:
                rows.append(dict(pad='%s.%s' % (fp.lib, num), status='SKIP', reason='library pad differs from board pad')); continue
        else:
            lay = layout_holes(shape, holes) if holes else layout_grid(shape)
            if lay is None:
                rows.append(dict(pad='%s.%s' % (fp.ref, num), status='SKIP', reason='no layout meets coverage %d-%d %%, web 0.25, side 0.5, via clearance %.2f'
                                 % (COV_LO * 100, COV_HI * 100, VIA_CLR), holes=holes)); continue
            lay = dict(lay, size=[round(v, 4) for v in pi['size']], shape=pi['kind'], holes_padframe=holes)
        lays[key] = lay
        # remove old paste-only pads inside the target pad (and earlier generated panes)
        for q in infos:
            if q['layers'] == ['F.Paste'] and q['num'] == '':
                if in_bbox(from_local(q['at']), shape.bbox):
                    s0 = text.rfind('\n', 0, q['node'][1]) + 1
                    s0 = s0 if text[s0:q['node'][1]].strip() == '' else q['node'][1]
                    e0 = q['node'][2]
                    if s0 != q['node'][1]:
                        if text[e0:e0 + 1] == '\n': e0 += 1
                    elif text[s0 - 1:s0] == ' ': s0 -= 1
                    edits.append((s0, e0, ''))
        rl = remove_paste_layer(text, pi['node'])
        if rl: edits.append(rl)
        ind = line_indent(text, pi['node'][1])
        multiline = '\n' in text[pi['node'][1]:pi['node'][2]]
        td = child(pi['node'], 'teardrops'); td_text = None
        if td is not None and multiline:
            raw = text[td[1]:td[2]].split('\n'); base = line_indent(text, td[1]) or ''
            td_text = [raw[0]] + [l[len(base):] if l.startswith(base) else l.strip() for l in raw[1:]]
        with_uuid = child(pi['node'], 'uuid') is not None
        ci = None
        if multiline:
            nl = text.index('\n', pi['node'][1]) + 1
            k = nl
            while text[k] in ' \t': k += 1
            ci = text[nl:k]
        txt = []
        for k, (poly, rects) in enumerate(zip(lay['panes'], lay['rects'])):
            txt.append(pane_text(fp, pi, k, poly, rects, ind if ind is not None else '', multiline and ind is not None, td_text, with_uuid, ci))
        ml = multiline and ind is not None
        ins = ''.join(('\n' + t) if ml else (('\n' + ind + t) if ind is not None else (' ' + t)) for t in txt)
        edits.append((pi['node'][2], pi['node'][2], ins))
        m = lay['metrics']
        ogap = min((rect_dist(r, o) for p in lay['rects'] for r in p for o in obst), default=None)
        rows.append(dict(pad='%s.%s' % (fp.ref if fp.board else fp.lib, num), status='OK', layout=lay['kind'], axis=lay.get('axis'), grid=lay.get('grid'),
                         webs_x=lay.get('webs_x'), webs_y=lay.get('webs_y'), inset=lay['inset'], panes=m['panes'],
                         coverage_pct=round(100 * m['coverage'], 1), paste_mm2=round(m['paste_mm2'], 3), pad_mm2=round(shape.area, 3),
                         min_web=None if m['min_web'] is None else round(m['min_web'], 3), min_side=round(m['min_side'], 3),
                         min_hole_clear=None if m['min_hole_clear'] is None else round(m['min_hole_clear'], 3),
                         holes=len(holes), holes_padframe=holes, core_clamped=clamped,
                         gap_to_other_paste=None if ogap is None else round(ogap, 3),
                         pane_bbox=[[round(min(r[0] for r in p), 3), round(min(r[1] for r in p), 3), round(max(r[2] for r in p), 3), round(max(r[3] for r in p), 3)] for p in lay['rects']]))
    return edits, rows, lays


def apply_edits(text, edits):
    # drop duplicate removals, apply from the end
    seen, ed = set(), []
    for e in edits:
        if (e[0], e[1], e[2]) in seen: continue
        seen.add((e[0], e[1], e[2])); ed.append(e)
    ed.sort(key=lambda e: (e[0], e[1]), reverse=True)
    for s, e, r in ed: text = text[:s] + r + text[e:]
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('board'); ap.add_argument('-o', '--out'); ap.add_argument('--lib'); ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--report')
    a = ap.parse_args()
    text = open(a.board, encoding='utf-8').read()
    root = parse(text)
    vias = board_vias(text, root)
    want = {}
    for r, n in TARGETS: want.setdefault(r, []).append(n)
    edits, rows, layouts, fps = [], [], {}, {}
    for c in root[3]:
        if c[0] != 'footprint': continue
        fp = FP(text, c, True)
        if fp.ref not in want: continue
        e, rw, ly = plan_fp(text, fp, want[fp.ref], vias)
        edits += e; rows += rw
        for k, v in ly.items():
            if k in layouts and json.dumps(layouts[k]['panes'], default=list) != json.dumps(v['panes'], default=list):
                layouts[k]['conflict'] = True
                rows.append(dict(pad='%s.%s' % (fp.ref, k[1]), status='WARN', reason='layout differs from another instance of %s: library gets the first' % k[0]))
            layouts.setdefault(k, v)
        fps[fp.ref] = fp.lib
    new = apply_edits(text, edits)
    rep = dict(board=a.board, via_clearance_mm=VIA_CLR, web_mm=WEB, web_grid_mm=WEB_GRID, pads=rows, lib=[])
    if a.lib:
        libs = sorted({k[0] for k in layouts})
        for lib in libs:
            name = lib.split(':', 1)[-1]; f = os.path.join(a.lib, name + '.kicad_mod')
            if not os.path.exists(f):
                rep['lib'].append(dict(lib=lib, status='SKIP', reason='file not found %s' % f)); continue
            lt = open(f, encoding='utf-8').read(); lr = parse(lt)
            lfp = FP(lt, lr, False); lfp.lib = lib
            nums_ = [k[1] for k in layouts if k[0] == lib]
            e, rw, _ = plan_fp(lt, lfp, nums_, None, layouts_in=layouts)
            nl = apply_edits(lt, e)
            rep['lib'].append(dict(lib=lib, file=f, changed=nl != lt, pads=rw))
            if not a.dry_run and nl != lt: open(f, 'w', encoding='utf-8').write(nl)
    out = a.out or a.board
    changed = new != text
    if not a.dry_run and (changed or a.out): open(out, 'w', encoding='utf-8').write(new)
    if a.report: json.dump(rep, open(a.report, 'w'), indent=1, default=list)
    for r in rows:
        if r['status'] == 'OK':
            print('%-9s OK   %-5s panes %d  coverage %5.1f %%  web %s  side %.2f  hole clr %s  inset %.2f  gap to other paste %s' % (
                r['pad'], r['layout'], r['panes'], r['coverage_pct'], '-' if r['min_web'] is None else '%.2f' % r['min_web'],
                r['min_side'], '-' if r['min_hole_clear'] is None else '%.2f' % r['min_hole_clear'], r['inset'],
                '-' if r['gap_to_other_paste'] is None else '%.2f' % r['gap_to_other_paste']))
        else:
            print('%-9s %s %s' % (r['pad'], r['status'], r['reason']))
    for l in rep['lib']:
        print('lib %-40s %s' % (l['lib'], l.get('status', 'changed' if l.get('changed') else 'unchanged')))
    print('PASTE_FIX %s board %s%s' % ('dry-run' if a.dry_run else 'wrote', 'changed' if changed else 'unchanged', (' -> ' + out) if not a.dry_run else ''))


if __name__ == '__main__':
    main()
