#!/usr/bin/env python3
"""silk_tile.py - redraw the F.SilkS section boxes of the DesktopSpeaker board as one tiling.

Usage:  python3 silk_tile.py IN.kicad_pcb OUT.kicad_pcb [--report OUT.json]

Plain python3, text-level edit. Only F.SilkS board graphics are touched:
  * every F.SilkS gr_line / gr_arc of width BOX_W (the old box lines, outer frame and its corner arcs) is removed;
  * the boundaries of the section regions below are written as gr_line (width BOX_W), one segment per edge
    between junctions, so every segment end is shared by 2 (corner) or 3 (T) segment ends, or lies on the
    tiled-region boundary (there is no outer frame: the Edge.Cuts outline closes the tiling);
  * section titles (gr_text found by text) and the listed labels/graphics (by uuid) are set to absolute positions;
  * missing titles are added (deterministic uuid).
Footprints, tracks, vias, zones and every other item are left byte-identical. Idempotent: a second run on the
output reproduces the same bytes.

Section regions are unions of axis-aligned rectangles. Most are single rectangles; three are L-shaped (or
L with a notch) because fixed parts leave no straight edge position (see ai-files/reports/silk-boxes-rt3.md).
"""
import re, sys, json, uuid

# ---------------------------------------------------------------- data
BOX_W = 0.15                      # box line width (as RT-2)
REGION = (86.65, 20.4, 213.35, 157.2)   # tiled region: Edge.Cuts 86.25..213.75 x 20..157.6, inset 0.4 (no frame line)
X0, Y0, X1, Y1 = REGION

# named edge positions (mm)
XG = 110.40   # Gauge | MCU, 3V AO west
X3 = 117.00   # 3V AO east
XA = 127.50   # Bluetooth | Wake, PD ; MCU arm east
XW = 143.00   # Wake | USB-C Jack
XP = 147.95   # USB-C PD | USB Audio Codec
XM = 137.30   # MCU | ADC
XS1 = 169.55  # upper spine: Jack | Audio Conn, Codec | 5V rail, Codec | Source Mux (east of the C187 reference text)
XS2 = 165.95  # lower spine: ADC | Source Mux, ADC | SWD, Test Points | SWD (west of the J6 outline)
XL = 103.50   # 5V Logic | Volume Encoder
XV = 130.00   # Volume Encoder | Test Points
XF = 140.75   # Front Amp | Charger, Boost ; Test Points arm east
XC = 162.40   # Charger | Charger FETs
XB = 172.50   # Boost, Charger | Woofer
XH = 188.20   # SWD, Charger FETs | Battery
YJ = 40.52    # Wake, Jack | PD, Codec
YA = 45.00    # Audio Connectors | 5V Codec Rail
YB = 55.90    # Bluetooth | Gauge, MCU
YR = 56.80    # 5V Codec Rail | Source Mux
YP = 68.70    # PD, Codec | MCU, ADC
Y3T = 71.30   # 3V AO top
Y3B = 80.60   # 3V AO bottom
YSM = 75.75   # Source Mux | SWD, Battery
YMW = 91.40   # Gauge, MCU | 5V Logic, Volume Encoder (C120 above, U5 ref text and room for the Volume Encoder title below)
YM = 93.30    # MCU step, ADC | Test Points (R206-R209 bottom 93.11, H2 top 93.4)
YT = 103.13   # Test Points | Charger, FETs ; SWD | FETs
YF = 109.30   # 5V Logic, Vol Enc, Test Points | Front Amp
YW = 114.86   # FETs, Battery | Woofer, Charger arm
YC = 136.40   # Charger | Boost

# section name (= title text), region as a union of rectangles (x0, y0, x1, y1); the first rectangle holds the title
SECTIONS = [
    ("Bluetooth",              [(X0, Y0, XA, YB)]),
    ("Wake",                   [(XA, Y0, XW, YJ)]),
    ("USB-C Jack",             [(XW, Y0, XS1, YJ)]),
    ("Audio Connectors",       [(XS1, Y0, X1, YA)]),
    ("USB-C PD",               [(XA, YJ, XP, YP)]),
    ("USB Audio Codec",        [(XP, YJ, XS1, YP)]),
    ("5V Codec Rail",          [(XS1, YA, X1, YR)]),
    ("Source Mux + Headphone", [(XS1, YR, X1, YSM), (XS2, YP, XS1, YSM)]),
    ("Gauge + LC Power",       [(X0, YB, XG, YMW)]),
    ("3V AO",                  [(XG, Y3T, X3, Y3B)]),
    ("MCU",                    [(XG, YB, XA, Y3T), (X3, Y3T, XA, Y3B), (XG, Y3B, XA, YMW), (XA, YP, XM, YMW), (XV, YMW, XM, YM)]),
    ("ADC",                    [(XM, YP, XS2, YM)]),
    ("SWD Header",             [(XS2, YSM, XH, YT)]),
    ("Battery",                [(XH, YSM, X1, YW)]),
    ("Charger FETs",           [(XC, YT, XH, YW)]),
    ("5V Logic",               [(X0, YMW, XL, YF)]),
    ("Volume Encoder",         [(XL, YMW, XV, YF)]),
    ("Test Points",            [(XV, YM, XS2, YT), (XV, YT, XF, YF)]),
    ("Charger",                [(XF, YT, XC, YC), (XC, YW, XB, YC)]),
    ("Front Amp U6 + Filters", [(X0, YF, XF, Y1)]),
    ("Boost Converter",        [(XF, YC, XB, Y1)]),
    ("Woofer Amp U7",          [(XB, YW, X1, Y1)]),
]

# section titles (F.SilkS gr_text, matched by text): anchor (at) and optional new size; thickness and justification kept.
TITLES = {   # text: (at_x, at_y, size or None = keep); placed by the title rule (see report): top-left, else top-right,
 # else shrink to 1.2/1.0 at top-left/top-right, else the free spot nearest the top-left corner
    'Bluetooth': (92.21, 21.72, None),   # top-left
    'Wake': (130.66, 21.72, None),   # top-left
    'USB-C Jack': (162.457, 21.72, None),   # top-right
    'Audio Connectors': (179.31, 40.22, None),   # scan
    'USB-C PD': (133.66, 45.09, None),   # scan
    'USB Audio Codec': (157.677, 41.84, None),   # top-left
    '5V Codec Rail': (177.643, 46.32, None),   # top-left
    'Source Mux + Headphone': (203.002, 57.8, 1.0),   # top-right
    'Gauge + LC Power': (97.243, 64.72, None),   # scan
    '3V AO': (113.024, 72.327, None),   # top-left
    'MCU': (113.193, 57.22, None),   # top-left
    'ADC': (139.86, 70.02, None),   # top-left
    'SWD Header': (170.988, 76.836, 1.0),   # top-left
    'Battery': (192.46, 77.07, None),   # top-left
    'Charger FETs': (169.893, 104.45, None),   # top-left
    '5V Logic': (91.777, 92.72, None),   # top-left
    'Volume Encoder': (112.527, 92.72, None),   # top-left
    'Test Points': (153.894, 101.95, 1.2),   # below H2 (scan, shrunk)
    'Charger': (145.377, 104.45, None),   # top-left
    'Front Amp U6 + Filters': (99.777, 110.62, None),   # top-left
    'Boost Converter': (149.743, 137.72, None),   # top-left
    'Woofer Amp U7': (181.193, 116.18, None),   # top-left
}
NEW_TITLE_FONT = (1.4, 0.2)
# other F.SilkS board items to place, by uuid: absolute (at_x, at_y) for gr_text, (dx, dy) translation for gr_line groups
TEXT_MOVES = {}       # uuid -> (x, y)
# gr_line groups moved as a whole, by uuid: bbox minimum of the group's points goes to 'to'
LINE_GROUP_MOVES = {'bluetooth_rune': {'uuids': ['307955ab-fbe7-4c92-91ef-250ed57aa4e7', '50ec0a17-c4f4-4289-8989-d1bae896ddb4', '680e57e3-fa8c-4159-8ea0-2ed4d8892d76', '14dcdddd-d59b-4f69-a48f-fcbf4a211827', 'a0882aaf-9e35-4f8e-8486-74da7754b5cc'], 'to': (98.92, 20.82)}}  # rune follows the Bluetooth title (1.55 mm gap, centred)

# ---------------------------------------------------------------- geometry
EPS = 1e-6
def fmt(v):
    s = ('%.6f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s

def section_at(px, py):
    for name, rects in SECTIONS:
        for (a, b, c, d) in rects:
            if a - EPS <= px <= c + EPS and b - EPS <= py <= d + EPS and a < px < c and b < py < d:
                return name
    return None

def build_lines():
    """Return maximal boundary segments split at junctions: list of ((x1,y1),(x2,y2))."""
    xs = sorted({r[i] for _, rs in SECTIONS for r in rs for i in (0, 2)})
    ys = sorted({r[i] for _, rs in SECTIONS for r in rs for i in (1, 3)})
    h = 1e-3
    elem = []   # elementary segments on the grid
    for y in ys:
        for xa, xb in zip(xs, xs[1:]):
            xm = (xa + xb) / 2
            up, dn = section_at(xm, y - h), section_at(xm, y + h)
            if up != dn and up is not None and dn is not None:
                elem.append(((xa, y), (xb, y)))
    for x in xs:
        for ya, yb in zip(ys, ys[1:]):
            ym = (ya + yb) / 2
            lf, rt = section_at(x - h, ym), section_at(x + h, ym)
            if lf != rt and lf is not None and rt is not None:
                elem.append(((x, ya), (x, yb)))
    # vertex degree; merge collinear chains through degree-2 straight vertices
    deg = {}
    for a, b in elem:
        deg[a] = deg.get(a, 0) + 1; deg[b] = deg.get(b, 0) + 1
    def straight(p):
        segs = [s for s in elem if p in s]
        if len(segs) != 2: return False
        (a, b), (c, d) = segs
        return (a[0] == b[0] == c[0] == d[0]) or (a[1] == b[1] == c[1] == d[1])
    stop = {p for p in deg if not straight(p)}
    used = set(); out = []
    adj = {}
    for i, (a, b) in enumerate(elem):
        adj.setdefault(a, []).append(i); adj.setdefault(b, []).append(i)
    for i, (a, b) in enumerate(elem):
        if i in used: continue
        # extend both ways
        chain = [a, b]; used.add(i)
        for end in (0, 1):
            while True:
                p = chain[-1] if end else chain[0]
                if p in stop: break
                nxt = [j for j in adj[p] if j not in used]
                if not nxt: break
                j = nxt[0]; used.add(j)
                q = elem[j][1] if elem[j][0] == p else elem[j][0]
                if end: chain.append(q)
                else: chain.insert(0, q)
        p, q = chain[0], chain[-1]
        if (p[0], p[1]) > (q[0], q[1]): p, q = q, p
        out.append((p, q))
    return sorted(out, key=lambda s: (s[0][1], s[0][0], s[1][1], s[1][0]))

# ---------------------------------------------------------------- text edit
def blocks(text):
    """Yield (start, end, block) for top-level '\t(gr_...' blocks."""
    for m in re.finditer(r'^\t\(gr_(line|arc|text|rect|circle|poly)\b', text, re.M):
        s = m.start(); depth = 0; i = s
        in_str = False
        while True:
            ch = text[i]
            if in_str:
                if ch == '\\': i += 1
                elif ch == '"': in_str = False
            elif ch == '"': in_str = True
            elif ch == '(': depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0: break
            i += 1
        e = i + 1
        if text[e:e + 1] == '\n': e += 1
        yield s, e, text[s:e]

def is_box_item(b):
    return (b.startswith('\t(gr_line') or b.startswith('\t(gr_arc')) and '(layer "F.SilkS")' in b \
        and re.search(r'\(width %s\)' % re.escape(fmt(BOX_W)), b) is not None

def line_block(p, q):
    u = uuid.uuid5(uuid.NAMESPACE_URL, 'silk_tile:%s,%s,%s,%s' % (fmt(p[0]), fmt(p[1]), fmt(q[0]), fmt(q[1])))
    return ('\t(gr_line\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type default)\n\t\t)\n'
            '\t\t(layer "F.SilkS")\n\t\t(uuid "%s")\n\t)\n') % (fmt(p[0]), fmt(p[1]), fmt(q[0]), fmt(q[1]), fmt(BOX_W), u)

def text_block(txt, x, y, size, th):
    u = uuid.uuid5(uuid.NAMESPACE_URL, 'silk_tile:title:' + txt)
    return ('\t(gr_text "%s"\n\t\t(at %s %s 0)\n\t\t(layer "F.SilkS")\n\t\t(uuid "%s")\n\t\t(effects\n\t\t\t(font\n'
            '\t\t\t\t(size %s %s)\n\t\t\t\t(thickness %s)\n\t\t\t)\n\t\t)\n\t)\n') % (txt, fmt(x), fmt(y), u, fmt(size), fmt(size), fmt(th))

def set_at(b, x, y):
    return re.sub(r'\(at [-\d.]+ [-\d.]+( [-\d.]+)?\)', lambda m: '(at %s %s%s)' % (fmt(x), fmt(y), m.group(1) or ''), b, count=1)

def shift_line(b, dx, dy):
    def f(m):
        return '(%s %s %s)' % (m.group(1), fmt(round(float(m.group(2)) + dx, 6)), fmt(round(float(m.group(3)) + dy, 6)))
    return re.sub(r'\((start|end|mid) ([-\d.]+) ([-\d.]+)\)', f, b)

def main():
    src, dst = sys.argv[1], sys.argv[2]
    text = open(src).read()
    segs = build_lines()
    out = []; pos = 0; inserted = False; removed = 0
    titles_done = set(); moved = []
    group_uuid = {u: g for g, d in LINE_GROUP_MOVES.items() for u in d['uuids']}
    group_old = {}
    # first pass: find the current reference point of each line group (bbox min of its lines) for idempotent moves
    for s, e, b in blocks(text):
        m = re.search(r'\(uuid "([^"]+)"\)', b)
        if m and m.group(1) in group_uuid:
            pts = [(float(a), float(c)) for a, c in re.findall(r'\((?:start|end|mid) ([-\d.]+) ([-\d.]+)\)', b)]
            g = group_uuid[m.group(1)]
            o = group_old.setdefault(g, [1e9, 1e9])
            o[0] = min(o[0], min(p[0] for p in pts)); o[1] = min(o[1], min(p[1] for p in pts))
    for s, e, b in blocks(text):
        out.append(text[pos:s]); pos = e
        if is_box_item(b):
            removed += 1
            if not inserted:
                out.append(''.join(line_block(p, q) for p, q in segs)); inserted = True
            continue
        if b.startswith('\t(gr_text') and '(layer "F.SilkS")' in b:
            t = re.match(r'\t\(gr_text "((?:[^"\\]|\\.)*)"', b).group(1)
            u = re.search(r'\(uuid "([^"]+)"\)', b).group(1)
            if t in TITLES and t not in titles_done:
                x, y, sz = TITLES[t]
                b = set_at(b, x, y); titles_done.add(t)
                if sz is not None:
                    b = re.sub(r'\(size [-\d.]+ [-\d.]+\)', '(size %s %s)' % (fmt(sz), fmt(sz)), b, count=1)
            elif u in TEXT_MOVES:
                b = set_at(b, *TEXT_MOVES[u])
        m = re.search(r'\(uuid "([^"]+)"\)', b)
        if m and m.group(1) in group_uuid and b.startswith('\t(gr_line'):
            g = group_uuid[m.group(1)]; d = LINE_GROUP_MOVES[g]
            ox, oy = group_old[g]
            b = shift_line(b, d['to'][0] - ox, d['to'][1] - oy)
        out.append(b)
    out.append(text[pos:])
    new = ''.join(out)
    if not inserted:
        raise SystemExit('no box lines found to replace')
    # add missing titles after the last gr_text
    missing = [t for t in TITLES if t not in titles_done]
    if missing:
        last = None
        for s, e, b in blocks(new):
            if b.startswith('\t(gr_text'): last = e
        add = ''.join(text_block(t, TITLES[t][0], TITLES[t][1], TITLES[t][2] or NEW_TITLE_FONT[0], NEW_TITLE_FONT[1]) for t in missing)
        new = new[:last] + add + new[last:]
    open(dst, 'w').write(new)
    rep = {'removed_items': removed, 'segments': len(segs), 'added_titles': missing,
           'segments_list': [[list(p), list(q)] for p, q in segs]}
    if '--report' in sys.argv:
        json.dump(rep, open(sys.argv[sys.argv.index('--report') + 1], 'w'), indent=1)
    print('removed %d box items, wrote %d segments, added titles %s' % (removed, len(segs), missing))

if __name__ == '__main__':
    main()
