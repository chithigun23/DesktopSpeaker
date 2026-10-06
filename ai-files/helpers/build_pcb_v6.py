# -*- coding: utf-8 -*-
"""Generate DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb: PLACEMENT ONLY (no tracks, no copper zones except rule areas).

Run through build_pcb.sh (exports the netlist with kicad-cli, then runs this file in the flatpak KiCad python):
    ai-files/helpers/build_pcb.sh
Inputs : /tmp/ds_net.xml (kicadxml netlist of the root sheet), project footprint library (kicad-library/footprint).
Outputs: DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb, ai-files/pcb/layout.json (connector/hole positions for the CAD).
Frame  : u = right, v = rear (as the CAD: X right, Y rear). KiCad x = X0 + u, y = Y0 - v (rear edge at the top of the sheet).
v6 CELL generator: every IC/functional group is placed as an isolated cell on a far-apart canvas, then cells are translated to a floorplan (ai-files/pcb/floorplan-v6.json).
Method : anchors (ICs, connectors, inductors) are placed by hand in ANCHORS; satellites (small ICs, diodes, FETs, crystals) and
         all R/C are placed by a greedy ring search that minimises pad-to-pad distance to already placed pins on the same nets,
         with courtyard gap rules, a reference text slot per part, and board/hole/antenna obstacles.
Re-running overwrites the board (manual edits in KiCad are lost); edit the tables below instead.
"""
import math, json, re, sys, os, collections, time
T_START = time.time()
import xml.etree.ElementTree as ET
import pcbnew

ROOT = '/home/chithi/Desktop/DesktopSpeaker/'
FPLIB = ROOT + 'DesktopSpeaker-kicad/kicad-library/footprint'
NET = '/tmp/ds_net.xml'
OUT = ROOT + 'DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb'
LAYOUT_JSON = ROOT + 'ai-files/pcb/layout.json'
MM = 1e6

# ------------------------------------------------------------------ board parameters (set by set_board; canvas first, floorplan later)
CORNER_R = 3.0
FRONT_CAD_Y = 64.5
GAP_EDGE = 0.5
TXT_H = 0.6                           # reference text height/width (mm)
TXT_T = 0.10
HOLE_R = 3.75
HOLE_FP = 'MountingHole_3.2mm_M3_PTH_GND'
HOLES = []
FLOOR = ROOT + 'ai-files/pcb/floorplan-v6.json'


def set_board(ul, ur, vf, vr):
    global UL, UR, VF, VR, BW, BD, VCEN, X0, Y0, REAR_CAD_Y, PCB_CY_CAD
    UL, UR, VF, VR = ul, ur, vf, vr
    BW, BD = UR - UL, VR - VF
    VCEN = (VF + VR) / 2
    X0, Y0 = 150.0 - (UL + UR) / 2, (20.0 + VR if VR < 500 else 100.0)
    REAR_CAD_Y = FRONT_CAD_Y + BD
    PCB_CY_CAD = FRONT_CAD_Y + BD / 2


set_board(-900.0, 900.0, -900.0, 900.0)

# ------------------------------------------------------------------ classification
TALL = re.compile(r'^(L\d+|C275|J\d+|SW\d+)$')
QFN_FP = ('BQ25792', 'TAS5825', 'TPA6132', 'TPS25730', 'TPS7B8450', 'TPS61088', 'BM83', 'CSD17579', 'TPS63802', 'PCM1862')


def kind_of(ref, fp):
    if TALL.match(ref):
        return 'tall'
    if ref[0] in 'RC' or ref.startswith('FB'):
        return 'pas'
    if any(k in fp for k in QFN_FP):
        return 'qfn'
    return 'ic'


# ------------------------------------------------------------------ cells
# name: (title, heads {ref: (du, dv, rot)} anchored at the cell origin, satellites [(ref, du, dv)] greedy-placed near the hint, zone limits l/r/b/t relative to the origin)
ANCHORS = {}
CELLDEF = {
    'BM83': ('Bluetooth', {'U1': (0, 0, 90)}, [('J8', 12, -17)], dict(l=-16.1)),
    'BTSUP': ('BT supply', {'U15': (0, 0, 0)}, [('L3', 6.5, 0)], {}),
    'MCU': ('MCU + SWD', {'U3': (0, 0, 0), 'J6': (-17.75, 4.5, 0), 'J7': (-15.5, -7.0, 0)}, [], dict(l=-19.6, b=-11.4)),
    'AMP6': ('Amplifier front (U6) + output filters', {'U6': (0, 0, 0), 'J9': (-15.5, -6.5, 0), 'J10': (15.5, -6.5, 0)}, [], dict(b=-11.6)),
    'AMP7': ('Amplifier woofer (U7) + filters', {'U7': (-2, 0, 0), 'J11': (10.9, -6.5, 0)}, [], dict(b=-11.6, l=-15.8, r=15.8)),
    'BOOST': ('Boost', {'U25': (0, 0, 270), 'L200': (-8.0, 0.5, 0), 'C275': (13.5, 0, 0)}, [], {}),
    'CHG': ('Charger', {'U4': (0, 0, 0), 'L1': (0, 10.5, 0)}, [], {}),
    'CHGQ': ('Charger FETs', {'Q103': (0, 0, 0)}, [('Q100', -7.5, 0), ('Q101', 7.5, 0), ('Q102', 0, -7)], {}),
    'BATIO': ('Battery I/O', {'J5': (0, 0, 270), 'SW101': (2.25, 17.8, 90)}, [], dict(r=5.55)),
    'WAKE': ('Wake', {'SW100': (0, 0, 0)}, [], dict(t=3.8)),
    'AO3V': ('3V AO', {'U12': (0, 0, 0)}, [], {}),
    'SWG': ('Fuel gauge + low-current power', {'U20': (-7.5, 4.0, 0), 'U13': (0, 4.0, 0), 'U16': (7.5, 4.0, 0), 'U17': (-7.5, -4.0, 0), 'U21': (0, -4.0, 0), 'Q104': (7.5, -4.0, 0), 'U5': (0, -10.5, 0)}, [], {}),
    'LOG5V': ('5V logic', {'U14': (0, 0, 0)}, [('L2', 7, 0)], {}),
    'ADC': ('ADC', {'U24': (0, 0, 0)}, [('Y200', -11, 0), ('FB200', 9, 6)], {}),
    'CODSUP': ('5V codec rail', {'U22': (-6.5, 0, 0), 'U23': (6.5, 0, 0)}, [], {}),
    'USBAUD': ('USB audio codec', {'U2': (0, 0, 0)}, [('Y170', 0, -9)], {}),
    'JACKS': ('Jacks', {'J2': (-6.7, 0, 270), 'J3': (6.7, 0, 270)}, [('D200', -6.7, -6.5), ('D201', 6.7, -6.5)], dict(t=7.2)),
    'MUX': ('Source mux + headphone', {'U8': (-12, 0, 0), 'U9': (0, 0, 0), 'U10': (12, 0, 0)}, [], {}),
    'PD': ('USB-C + PD input', {'U11': (0, 0, 0)}, [('D7', 11, -5)], {}),
    'PDIN': ('USB-C connector + ESD', {'J1': (0, 0, 180), 'J4': (9.6, -3.9, 0)}, [('D1', -9, -7), ('D5', -3, -7), ('D6', 3, -7), ('U19', 0, -13)], dict(t=3.75)),
}
CELL_ORDER = list(CELLDEF)
CELL_XY = {}
ZONES, ZONE_OF, SATELLITES, TITLES = {}, {}, [], {}
for _i, (_n, _d) in enumerate(CELLDEF.items()):
    _cx, _cy = (_i % 5) * 130.0, (_i // 5) * 130.0
    _ttl, _heads, _sats, _zl = _d
    TITLES[_n] = _ttl
    ZONES[_n] = (_cx + _zl.get('l', -50), _cx + _zl.get('r', 50), _cy + _zl.get('b', -50), _cy + _zl.get('t', 50))
    CELL_XY[_n] = (_cx, _cy)
    for _r, (_u, _v, _rot) in _heads.items():
        ANCHORS[_r] = ('c', _cx + _u, _cy + _v, _rot)
        ZONE_OF[_r] = _n
    for _r, _u, _v in _sats:
        SATELLITES.append((_r, _cx + _u, _cy + _v))
        ZONE_OF[_r] = _n
AMP_L = {'AMP6': ('U6', ['L201', 'L202', 'L203', 'L204']), 'AMP7': ('U7', ['L205', 'L206'])}
for _n, (_u, _ls) in AMP_L.items():
    for _l in _ls:
        ZONE_OF[_l] = _n
SHEET_ZONE = {'USB_PD': 'PD', 'Battery_Charger': 'CHG', 'Fuel_Gauge_Power': 'SWG', 'Amplifiers': 'AMP6', 'Bluetooth': 'BM83',
              'Bluetooth_Power': 'BTSUP', 'MCU': 'MCU', 'USB_Audio': 'USBAUD', 'Source_Select_ADC': 'ADC', 'Headphone_Aux': 'MUX',
              'Logic_Audio_Power': 'LOG5V', '': 'ADC'}
CLAMP = {}
ZONE_OF['R223'] = ZONE_OF['C233'] = 'ADC'      # BT-audio coupling parts are analogue-side parts
CRIT_OWNERS = {'U6': 1.6, 'U7': 1.6, 'U4': 1.6, 'U25': 1.8, 'U3': 1.6, 'U24': 1.4, 'U22': 1.8, 'U23': 1.8, 'U2': 1.5, 'U15': 1.4, 'U14': 1.4, 'U11': 1.3}
AWAY_NETS = ('Net-(U25-FB)', 'Net-(U25-COMP)')      # U25 feedback/compensation: keep away from the SW pins/inductor
SW_NET = 'Net-(U25-SW)'
AWAY_MM = 6.0
PRE_OWNERS = ['U6', 'U7', 'U25', 'U4', 'U11', 'U24', 'U2', 'U3', 'U14', 'U15', 'U22', 'U23', 'U10', 'U12', 'U5', 'U19', 'U20', 'U13', 'U16', 'U17', 'U21', 'U1', 'U8', 'U9']
OWNER_ORDER = ['U6', 'U7', 'U25', 'L200', 'U4', 'U11', 'U24', 'U2', 'U10', 'U1', 'U15', 'U14', 'U3', 'U8', 'U9', 'U22', 'U23']
NETBASED = {'D1', 'D5', 'D6', 'D7', 'D200', 'D201', 'Q100', 'Q101', 'Q102', 'Q104', 'Y170', 'Y200', 'L2', 'L3', 'FB200', 'L201', 'L202', 'L203', 'L204', 'L205', 'L206'}
ANTENNA_MARGIN = 3.0
ASHEETS = ('Source_Select_ADC', 'Headphone_Aux', 'USB_Audio')
NOCLAMP = [False]
TITLE_AT = (9000.0, 9000.0)


HW = float(os.environ.get('HINTW', '0.6'))
STEP = 0.5                           # ring search step (mm)


# ------------------------------------------------------------------ helpers


def rot_pt(x, y, r):
    t = math.radians(r)
    c, s = round(math.cos(t), 12), round(math.sin(t), 12)
    return x * c + y * s, -x * s + y * c          # visual CCW on a y-down sheet


def rot_rect(rc, r):
    pts = [rot_pt(x, y, r) for x, y in ((rc[0], rc[1]), (rc[2], rc[1]), (rc[2], rc[3]), (rc[0], rc[3]))]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def K(u, v):          # board (u, v) -> sheet mm
    return X0 + u, Y0 - v


def inter(a, b, g=0.0):
    return a[0] < b[2] + g and a[2] > b[0] - g and a[1] < b[3] + g and a[3] > b[1] - g


class Grid:
    def __init__(self, cell=3.0):
        self.cell, self.d, self.items = cell, collections.defaultdict(list), []

    def add(self, rect, meta):
        idx = len(self.items)
        self.items.append((rect, meta))
        c = self.cell
        for i in range(int(rect[0] // c), int(rect[2] // c) + 1):
            for j in range(int(rect[1] // c), int(rect[3] // c) + 1):
                self.d[(i, j)].append(idx)

    def near(self, rect, g):
        c, seen = self.cell, set()
        for i in range(int((rect[0] - g) // c), int((rect[2] + g) // c) + 1):
            for j in range(int((rect[1] - g) // c), int((rect[3] + g) // c) + 1):
                for idx in self.d.get((i, j), ()):
                    if idx not in seen:
                        seen.add(idx)
                        yield self.items[idx]


def ip(v):
    return pcbnew.VECTOR2I(int(round(v[0] * MM)), int(round(v[1] * MM)))


def main():
    root = ET.parse(NET).getroot()
    comps = {}
    for c in root.find('components'):
        ref = c.get('ref')
        sp = c.find('sheetpath')
        comps[ref] = dict(ref=ref, fp=(c.findtext('footprint') or '').split(':')[-1], value=c.findtext('value') or '',
                          sheet=(sp.get('names').strip('/') if sp is not None else ''),
                          path=(sp.get('tstamps') if sp is not None else '/') + (c.findtext('tstamps') or ''), pins={})
    nets = {}
    for n in root.find('nets'):
        for nd in n:
            comps[nd.get('ref')]['pins'].setdefault(nd.get('pin'), n.get('name'))
            nets.setdefault(n.get('name'), []).append((nd.get('ref'), nd.get('pin')))

    # ---- owner IC of each passive (most shared non-GND nets, same sheet preferred), chain passives inherit from a neighbour
    ispas = lambda k: (k[0] in 'RC' and k[1:2].isdigit()) or k.startswith('FB')
    owner = {}
    for k, c in comps.items():
        if not ispas(k):
            continue
        sc = collections.Counter()
        for n in set(c['pins'].values()):
            if n == 'GND':
                continue
            for o, _p in nets[n]:
                if not ispas(o) and not o.startswith('H'):
                    sc[o] += 1.0 / (1 + len(nets[n]) / 6.0) + (0.5 if comps[o]['sheet'] == c['sheet'] else 0)
        if c['sheet'] in ASHEETS:          # audio-sheet passives must not be owned (and pulled) by a part of another sheet (e.g. the BM83)
            sc2 = collections.Counter({o: v for o, v in sc.items() if comps[o]['sheet'] in ASHEETS})
            sc = sc2
        owner[k] = sc.most_common(1)[0][0] if sc else None
    for _ in range(4):
        for k in [k for k, o in owner.items() if o is None]:
            for n in set(comps[k]['pins'].values()):
                if n == 'GND' or len(nets[n]) > 8:
                    continue
                for o, _p in nets[n]:
                    if o != k and owner.get(o):
                        owner[k] = owner[o]
                        break
                if owner[k]:
                    break

    def cell_name(ref):
        return ZONE_OF.get(ref) or ZONE_OF.get(owner.get(ref)) or SHEET_ZONE.get(comps[ref]['sheet'], 'ADC')

    def hint_of(ref):
        return CELL_XY[cell_name(ref)]

    def zone_rect(ref, margin=0.0):
        zn = cell_name(ref)
        z = ZONES[zn]
        zs = z if isinstance(z[0], tuple) else (z,)
        out = [(q[0] - margin, q[2] - margin, q[1] + margin, q[3] + margin) for q in zs]      # list of (u0, v0, u1, v1)
        for i, cl in enumerate(() if NOCLAMP[0] else CLAMP.get(zn, ())):
            o = out[i]
            out[i] = (max(o[0], cl[0]), max(o[1], cl[2]), min(o[2], cl[1]), min(o[3], cl[3]))
        return out
    ZM = [0.0]                                    # current zone margin (escalated when a part does not fit)

    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    netitems = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netitems[name] = ni

    # ---- footprints loaded at the origin, rotation 0: courtyard rect and net pad positions in footprint coordinates
    fps, crt, crt_s = {}, {}, {}
    for ref, c in comps.items():
        f = pcbnew.FootprintLoad(FPLIB, c['fp'])
        if f is None:
            sys.exit('missing footprint ' + c['fp'])
        f.SetReference(ref)
        f.SetValue(c['value'])
        f.SetFPID(pcbnew.LIB_ID('DesktopSpeaker', c['fp']))
        f.SetPath(pcbnew.KIID_PATH(c['path']))
        for p in f.Pads():
            nm = c['pins'].get(p.GetNumber())
            if nm:
                p.SetNet(netitems[nm])
        bb = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
        rc = [bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM]
        for p in f.Pads():          # some library courtyards are smaller than the pads: use the union with the pad extents + 0.2 mm
            pb = p.GetBoundingBox()
            rc = [min(rc[0], pb.GetX() / MM - 0.2), min(rc[1], pb.GetY() / MM - 0.2),
                  max(rc[2], pb.GetRight() / MM + 0.2), max(rc[3], pb.GetBottom() / MM + 0.2)]
        crt[ref] = tuple(rc)
        rs = [bb.GetX() / MM, bb.GetY() / MM, bb.GetRight() / MM, bb.GetBottom() / MM]     # true courtyard united with the pad extents (no margin)
        for p in f.Pads():
            pb = p.GetBoundingBox()
            rs = [min(rs[0], pb.GetX() / MM), min(rs[1], pb.GetY() / MM), max(rs[2], pb.GetRight() / MM), max(rs[3], pb.GetBottom() / MM)]
        crt_s[ref] = tuple(rs)
        c['pads'] = [(p.GetNumber(), p.GetPosition().x / MM, p.GetPosition().y / MM) for p in f.Pads() if c['pins'].get(p.GetNumber())]
        fps[ref] = f
        c['kind'] = kind_of(ref, c['fp'])

    grid = Grid()
    placed = {}
    attract = collections.defaultdict(list)
    conn_cache = {}

    def conn(r1, r2):
        key = (r1, r2) if r1 < r2 else (r2, r1)
        if key not in conn_cache:
            n1 = {n for n in comps[r1]['pins'].values() if n != 'GND' and len(nets[n]) <= 12}
            n2 = {n for n in comps[r2]['pins'].values() if n != 'GND' and len(nets[n]) <= 12}
            conn_cache[key] = bool(n1 & n2)
        return conn_cache[key]

    def gap_for(a, b):
        ka, kb = a['kind'], b['kind']
        if 'keep' in (ka, kb):
            return 0.0
        if 'txt' in (ka, kb):
            return 0.15
        if ka == 'tall' and kb == 'tall':
            return 0.8
        if 'tall' in (ka, kb):
            return 1.2 if 'pas' in (ka, kb) else 0.8
        if 'qfn' in (ka, kb):
            if 'pas' in (ka, kb) and (conn(a['ref'], b['ref']) or owner.get(a['ref']) == b['ref'] or owner.get(b['ref']) == a['ref']):
                return 0.35
            return 0.8
        if ka == 'pas' and kb == 'pas':
            return 0.3
        return 0.6

    def keep(rect, label):
        grid.add(rect, dict(kind='keep', ref=label))
    keep((TITLE_AT[0] - 9.0, TITLE_AT[1] - 0.8, TITLE_AT[0] + 9.0, TITLE_AT[1] + 0.8), 'TITLE')
    for nm, hu, hv in HOLES:
        keep((hu - HOLE_R, hv - HOLE_R, hu + HOLE_R, hv + HOLE_R), nm)

    def board_ok(rect):
        if rect[0] < UL + GAP_EDGE or rect[2] > UR - GAP_EDGE or rect[1] < VF + GAP_EDGE or rect[3] > VR - GAP_EDGE:
            return False
        for cu, cv in ((UL, VF), (UR, VF), (UL, VR), (UR, VR)):
            # rounded corner: keep out the 3 x 3 mm corner square
            if inter(rect, (cu - 3 if cu > 0 else cu, cv - 3 if cv > 0 else cv, cu + 3 if cu < 0 else cu, cv + 3 if cv < 0 else cv)):
                return False
        return True

    def rect_at(ref, u, v, rot, mode='c'):
        rr = rot_rect(crt[ref], rot)
        ru = (rr[0], -rr[3], rr[2], -rr[1])        # to the (u, v) frame
        if mode == 'c':
            ou, ov = u - (ru[0] + ru[2]) / 2, v - (ru[1] + ru[3]) / 2
        else:
            ou, ov = u, v
        return (ou + ru[0], ov + ru[1], ou + ru[2], ov + ru[3]), (ou, ov)

    def commit(ref, ou, ov, rot, rect, txt, slot):
        placed[ref] = dict(u=ou, v=ov, rot=rot, rect=rect, txt=txt, slot=slot)
        grid.add(rect, dict(kind=comps[ref]['kind'], ref=ref))
        if txt:
            grid.add(txt, dict(kind='txt', ref=ref))
        for num, px, py in comps[ref]['pads']:
            x, y = rot_pt(px, py, rot)
            attract[comps[ref]['pins'][num]].append((ou + x, ov - y, ref, num))

    def free(rect, ref, kd, exempt_edge=False):
        if not exempt_edge and not board_ok(rect):
            return False
        if not exempt_edge and ref in comps:
            if not any(rect[0] >= zr[0] and rect[2] <= zr[2] and rect[1] >= zr[1] and rect[3] <= zr[3] for zr in zone_rect(ref, ZM[0])):
                return False
        for orect, meta in grid.near(rect, 2.1):
            if meta['ref'] != ref and inter(rect, orect, gap_for(kd, meta)):
                return False
        return True

    def txt_slots(ref, rect, order):
        w, h = len(ref) * TXT_H * 0.95 + 0.2, TXT_H + 0.2
        cx, cy, g = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2, 0.12
        d = {'R': (rect[2] + g, cy - h / 2, rect[2] + g + w, cy + h / 2),
             'L': (rect[0] - g - w, cy - h / 2, rect[0] - g, cy + h / 2),
             'B': (cx - w / 2, rect[1] - g - h, cx + w / 2, rect[1] - g),        # below on the sheet = lower v
             'T': (cx - w / 2, rect[3] + g, cx + w / 2, rect[3] + g + h),
             # vertical text (rotated 90 deg) for tight gaps
             'r': (rect[2] + g, cy - w / 2, rect[2] + g + h, cy + w / 2),
             'l': (rect[0] - g - h, cy - w / 2, rect[0] - g, cy + w / 2),
             'b': (cx - h / 2, rect[1] - g - w, cx + h / 2, rect[1] - g),
             't': (cx - h / 2, rect[3] + g, cx + h / 2, rect[3] + g + w)}
        return [(k, d[k]) for k in order]

    def slot_free(ref, tr):
        if ref in comps and not NOCLAMP[0] and not any(tr[0] >= zr[0] and tr[2] <= zr[2] and tr[1] >= zr[1] and tr[3] <= zr[3] for zr in zone_rect(ref, 0.0)):
            return False
        if tr[0] < UL + 0.3 or tr[2] > UR - 0.3 or tr[1] < VF + 0.3 or tr[3] > VR - 0.3:
            return False
        for orect, meta in grid.near(tr, 0.3):
            if meta['ref'] != ref and inter(tr, orect, 0.15 if meta['kind'] != 'keep' else 0.0):
                return False
        return True

    def pick_slot(ref, rect, order):
        for k, tr in txt_slots(ref, rect, order):
            if slot_free(ref, tr):
                return k, tr
        return None, None

    # ---- class-D inductor heads: 2x2 block above the amp (or a row for the mono amp); IC-side pad towards the IC
    LV = float(os.environ.get('LV', '14.5'))
    for cn, (uref, ls) in AMP_L.items():
        cx, cy = CELL_XY[cn]
        up = comps[uref]
        pad_x = {}
        for L in ls:
            n1 = comps[L]['pins']['1']
            xs = [px for num, px, py in up['pads'] if up['pins'][num] == n1]
            pad_x[L] = (xs[0] if xs else 0.0)
        order = sorted(ls, key=lambda L: pad_x[L])
        if len(ls) == 4:
            slots = {order[0]: (-23.9, LV, 180), order[1]: (-8.0, LV, 180), order[2]: (8.0, LV, 0), order[3]: (23.9, LV, 0)}
        else:
            slots = {order[0]: (-8.0, LV, 180), order[1]: (8.0, LV, 0)}
        for L, (du, dv, rr) in slots.items():
            ANCHORS[L] = ('c', cx + du, cy + dv, rr)
    # ---- anchors
    antenna_keep = None
    for ref, spec in ANCHORS.items():
        c = comps[ref]
        kd = dict(kind=c['kind'], ref=ref)
        mode = spec[0]
        if mode in ('c', 'o'):
            rot = spec[3]
            rect, (ou, ov) = rect_at(ref, spec[1], spec[2], rot, mode)
        else:
            along, rot, ovh = spec[1], spec[2], spec[3]
            r0, _ = rect_at(ref, 0.0, 0.0, rot, 'c')
            w, h = r0[2] - r0[0], r0[3] - r0[1]
            pos = {'rear': (along, R + ovh - h / 2), 'front': (along, VF + 0.4 + h / 2),
                   'left': (UL - ovh + w / 2, along), 'right': (UR + ovh - w / 2, along)}[mode]
            rect, (ou, ov) = rect_at(ref, pos[0], pos[1], rot, 'c')
        if not free(rect, ref, kd, exempt_edge=True):
            print('WARNING anchor overlap', ref, [round(x, 2) for x in rect],
                  [m['ref'] for orect, m in grid.near(rect, 2.1) if m['ref'] != ref and inter(rect, orect, gap_for(kd, m))])
        commit(ref, ou, ov, rot, rect, None, None)
        if ref == 'U1':
            ax = rot_rect((-8.0, -22.0, 8.0, -11.0), rot)
            antenna_keep = dict(u0=ou + ax[0], u1=ou + ax[2], v0=ov - ax[3], v1=ov - ax[1])
            keep((antenna_keep['u0'], antenna_keep['v0'] - ANTENNA_MARGIN, antenna_keep['u1'], antenna_keep['v1'] + ANTENNA_MARGIN), 'ANT')
    for ref in ANCHORS:                       # reference text slots after all anchor courtyards are known
        k, tr = pick_slot(ref, placed[ref]['rect'], 'BTRLbtrl')
        if tr is None and TALL.match(ref):        # no free slot around a tall part: label on the body centre (between the pads)
            rr = placed[ref]['rect']
            cx, cy = (rr[0] + rr[2]) / 2, (rr[1] + rr[3]) / 2
            w_ = len(ref) * TXT_H * 0.95 + 0.2
            tr, k = (cx - w_ / 2, cy - (TXT_H + 0.2) / 2, cx + w_ / 2, cy + (TXT_H + 0.2) / 2), 'B'
        placed[ref]['txt'], placed[ref]['slot'] = tr, k
        if tr:
            grid.add(tr, dict(kind='txt', ref=ref))

    # ---- greedy placer
    pin_load = collections.Counter()
    chosen_pin = {}

    def attractors_for(ref):
        c, out = comps[ref], []
        own = owner.get(ref) if c['kind'] == 'pas' else None
        for num, px, py in c['pads']:
            nm = c['pins'][num]
            if nm == 'GND' or len(nets[nm]) > 70:
                out.append((None, 0.0))
                continue
            w = 1.0 if len(nets[nm]) <= 4 else (0.6 if len(nets[nm]) <= 12 else 0.3)
            pts = [(a, b, r) for a, b, r, _n in attract.get(nm, ()) if r != ref and cell_name(r) == cell_name(ref)]
            if own and own in placed:
                op = [(a, b, n) for a, b, r, n in attract.get(nm, ()) if r == own]
                if op:                              # decoupling/pull-up: this pin of the owner IC, least loaded first
                    key = (ref, nm)
                    if key not in chosen_pin:
                        hint = hint_of(ref)
                        chosen_pin[key] = min(op, key=lambda q: (pin_load[(own, q[2])], abs(q[0] - hint[0]) + abs(q[1] - hint[1])))
                    q = chosen_pin[key]
                    out.append(([(q[0], q[1])], 1.5))
                    continue
            same = [(a, b) for a, b, r in pts if comps[r]['sheet'] == c['sheet']]
            out.append((same or [(a, b) for a, b, r in pts] or None, w))
        return out

    def cost_of(ref, u, v, rot, attr, hint, strict=False):
        tot = 0.0
        for (num, px, py), (use, w) in zip(comps[ref]['pads'], attr):
            if use:
                x, y = rot_pt(px, py, rot)
                tot += (0.1 if strict else 1.0) * w * min(abs(u + x - a) + abs(v - y - b) for a, b in use)
        if hint:
            tot += (1.0 if strict else (HW if any(a[0] for a in attr) else 0.5)) * (abs(u - hint[0]) + abs(v - hint[1]))
        if rot in (180, 270):
            tot += 0.3
        if ref in away_set:
            for num, px, py in comps[ref]['pads']:
                x, y = rot_pt(px, py, rot)
                for a, b, _r, _n in attract.get(SW_NET, ()):
                    dd = math.hypot(u + x - a, v - y - b)
                    if dd < AWAY_MM:
                        tot += 12.0 * (AWAY_MM - dd) ** 2
        return tot

    away_set = {k for k, c in comps.items() if ispas(k) and any(n in AWAY_NETS for n in c['pins'].values())}
    failed = []

    def place_greedy(ref, hint, relax=False):
        c = comps[ref]
        kd = dict(kind=c['kind'], ref=ref)
        attr = attractors_for(ref)
        hint = hint or hint_of(ref)
        strict = c['kind'] != 'pas' and ref not in NETBASED
        pts = [pt for use, w in attr if use for pt in use]
        centre = hint if (strict or not pts) else min(pts, key=lambda q: abs(q[0] - hint[0]) + abs(q[1] - hint[1]))
        rots = (0, 90, 180, 270) if (c['kind'] != 'pas' or len(c['pads']) == 2) else (0, 90)
        order = 'RLBTrlbt' if c['kind'] == 'pas' else 'BTRLbtrl'
        best, found_at, step = None, None, STEP
        for ring in range(0, int(45 / step)):
            if found_at is not None and ring * step > found_at + 1.2:
                break
            if ring == 0:
                cand = [(0.0, 0.0)]
            else:
                n = ring
                cand = [(i * step, s * n * step) for i in range(-n, n + 1) for s in (-1, 1)] + \
                       [(s * n * step, j * step) for j in range(-n + 1, n) for s in (-1, 1)]
            for dx, dy in cand:
                for rot in rots:
                    rect, (ou, ov) = rect_at(ref, centre[0] + dx, centre[1] + dy, rot, 'c')
                    if not free(rect, ref, kd):
                        continue
                    k, tr = pick_slot(ref, rect, order)
                    if tr is None and not relax:
                        continue
                    cst = cost_of(ref, ou, ov, rot, attr, hint, strict) + (3.0 if tr is None else 0.0)
                    if best is None or cst < best[0]:
                        best = (cst, ou, ov, rot, rect, tr, k)
                        if found_at is None:
                            found_at = ring * step
        if best is None:
            if relax:
                nfree = 0
                for uu in range(-54, 55):
                    for vv in range(-41, 42):
                        for rr in (0, 90):
                            rc, _ = rect_at(ref, uu, vv, rr, 'c')
                            nfree += free(rc, ref, kd)
                print('FAIL free positions on board:', nfree)
                print('FAIL', ref, c['value'], 'centre', centre, 'hint', hint, 'kind', c['kind'], [pt for pt in pts][:3])
            return False
        commit(ref, best[1], best[2], best[3], best[4], best[5], best[6])
        for (r2, nm2), q in list(chosen_pin.items()):
            if r2 == ref:
                pin_load[(owner[ref], q[2])] += 1
        return True

    def try_place(ref, hint):
        ok = False
        for m in (0.0, 1.0, 3.0, 6.0, 300.0):
            ZM[0] = m
            if place_greedy(ref, hint):
                ok = True
                if m > 1.0:
                    print('WARNING zone margin %.0f needed for %s' % (m, ref), flush=True)
                break
        if not ok:
            ZM[0] = 300.0
            ok = place_greedy(ref, hint, relax=True)
            if not ok:
                print('WARNING %s placed without clamps' % ref, flush=True)
                NOCLAMP[0] = True
                ok = place_greedy(ref, hint, relax=True)
                NOCLAMP[0] = False
        ZM[0] = 0.0
        if not ok:
            failed.append(ref)

    locked = set()
    for o in PRE_OWNERS:
        cl = [r for r in comps if comps[r]['kind'] == 'pas' and owner.get(r) == o and r not in placed and
              ((r[0] == 'C' and 'GND' in comps[r]['pins'].values()) or r in away_set)]
        rail = lambda r: max([len(nets[n]) for n in comps[r]['pins'].values() if n != 'GND'] or [0]) >= 3
        cl.sort(key=lambda r: ((0 if (r[0] == 'C' and '0402' in comps[r]['fp'] and r not in away_set and rail(r)) else (1 if (r[0] == 'C' and '0402' in comps[r]['fp'] and r not in away_set) else (2 if r in away_set else 3))), (0 if '0402' in comps[r]['fp'] else 1), -min([len(nets[n]) for n in comps[r]['pins'].values() if n != 'GND'] or [0]) if rail(r) else 0, r))
        for r in cl:
            if r[0] == 'C' and '0402' in comps[r]['fp'] and r not in away_set and o in CRIT_OWNERS:
                ZM[0] = 6.0
                if not place_greedy(r, hint_of(r), relax=True):
                    try_place(r, hint_of(r))
                ZM[0] = 0.0
            else:
                try_place(r, hint_of(r))
            locked.add(r)
    print('pre-stage locked %d caps %.0fs' % (len(locked), time.time() - T_START), flush=True)
    for ref, hu, hv in SATELLITES:
        try_place(ref, (hu, hv))
    print('satellites done %.0fs' % (time.time() - T_START), flush=True)

    def prio(r):
        o = owner.get(r)
        oi = OWNER_ORDER.index(o) if o in OWNER_ORDER else len(OWNER_ORDER)
        return (oi, (0 if '0402' in comps[r]['fp'] else 1) if r[0] == 'C' else 2, min([len(nets[n]) for n in comps[r]['pins'].values() if n != 'GND'] or [99]), r)
    rest = [r for r in comps if r not in placed and comps[r]['kind'] == 'pas']
    rest.sort(key=prio)
    while rest:
        remaining, progress = [], False
        for ref in rest:
            if not any(a[0] for a in attractors_for(ref)):
                remaining.append(ref)
                continue
            try_place(ref, hint_of(ref))
            progress = True
        if not progress:
            for ref in remaining:
                try_place(ref, hint_of(ref))
            break
        rest = remaining
    failed += [r for r in comps if r not in placed and r not in failed]
    print('greedy done %.0fs, failed %s' % (time.time() - T_START, failed), flush=True)

    # ---- soft-constraint simulated annealing of the passives (overlap/zone penalties ramped up), then legalisation of violators
    def anneal(iters, seed=7, lam0=20.0, lam1=320.0, t0=0.6, t1=0.02):
        import random
        rnd = random.Random(seed)
        movers = [r for r, p in placed.items() if comps[r]['kind'] == 'pas' and r not in ANCHORS and r not in locked]
        mset = set(movers)
        cell = 3.0
        buckets = collections.defaultdict(set)
        items = {}
        cnt = [0]

        def cells(rc):
            return [(i, j) for i in range(int(rc[0] // cell), int(rc[2] // cell) + 1) for j in range(int(rc[1] // cell), int(rc[3] // cell) + 1)]

        def add(rc, meta):
            i = cnt[0]; cnt[0] += 1
            items[i] = (rc, meta)
            for c_ in cells(rc):
                buckets[c_].add(i)
            return i

        def remove(i):
            rc, meta = items.pop(i)
            for c_ in cells(rc):
                buckets[c_].discard(i)

        for rc, meta in grid.items:
            if meta['ref'] not in mset:
                add(rc, meta)

        def near(rc, g):
            seen = set()
            for c_ in cells((rc[0] - g, rc[1] - g, rc[2] + g, rc[3] + g)):
                for i in buckets.get(c_, ()):
                    if i not in seen:
                        seen.add(i)
                        yield items[i]

        zones = {r: zone_rect(r, 1.0) for r in movers}

        def zpen(ref, rc):
            best = 1e9
            for z in zones[ref]:
                v = max(0.0, z[0] - rc[0]) + max(0.0, rc[2] - z[2]) + max(0.0, z[1] - rc[1]) + max(0.0, rc[3] - z[3])
                if v < best:
                    best = v
            return best

        def bpen(rc, edge):
            return max(0.0, UL + edge - rc[0]) + max(0.0, rc[2] - (UR - edge)) + max(0.0, VF + edge - rc[1]) + max(0.0, rc[3] - (VR - edge))

        def depth(a_, b_, g):
            dx = min(a_[2], b_[2]) - max(a_[0], b_[0]) + g
            dy = min(a_[3], b_[3]) - max(a_[1], b_[1]) + g
            return min(dx, dy) if dx > 0 and dy > 0 else 0.0

        def pen_all(ref, rc, tx):
            tot = 0.0
            kd = dict(kind='pas', ref=ref)
            for orc, meta in near(rc, 2.1):
                if meta['ref'] != ref:
                    tot += depth(rc, orc, gap_for(kd, meta))
            if tx is not None:
                tk = dict(kind='txt', ref=ref)
                for orc, meta in near(tx, 0.5):
                    if meta['ref'] != ref:
                        tot += depth(tx, orc, gap_for(tk, meta))
                tot += 2.0 * bpen(tx, 0.3)
            return tot

        padinfo, ROTS = {}, (0, 90, 180, 270)
        fixed_pads = collections.defaultdict(list)
        mover_pads = collections.defaultdict(list)
        for r, p in placed.items():
            if r in mset:
                continue
            for num, px, py in comps[r]['pads']:
                x, y = rot_pt(px, py, p['rot'])
                fixed_pads[comps[r]['pins'][num]].append((p['u'] + x, p['v'] - y))
        for r in movers:
            c = comps[r]
            small_cap = r[0] == 'C' and '0402' in c['fp'] and 'GND' in c['pins'].values()
            bulk_cap = r[0] == 'C' and not small_cap and 'GND' in c['pins'].values()
            padinfo[r] = {rot: [(rot_pt(px, py, rot)[0], -rot_pt(px, py, rot)[1], c['pins'][num]) for num, px, py in c['pads']] for rot in ROTS}
            ws = []
            for num, px, py in c['pads']:
                nm = c['pins'][num]
                if nm == 'GND' or len(nets[nm]) > 70:
                    ws.append(0.0)
                elif small_cap:
                    ws.append(10.0 * CRIT_OWNERS.get(owner.get(r), 1.0))
                elif bulk_cap:
                    ws.append(3.0 if CRIT_OWNERS.get(owner.get(r), 1.0) <= 1.0 else 6.0 * CRIT_OWNERS[owner.get(r)])
                else:
                    ws.append((1.0 if len(nets[nm]) <= 12 else 0.4) * (3.0 if CRIT_OWNERS.get(owner.get(r), 1.0) > 1.0 else 1.0))
            c['w'] = ws
            for k, (num, px, py) in enumerate(c['pads']):
                mover_pads[c['pins'][num]].append((r, k))
        st = {}
        tg = {}                                            # per mover pad: target pads = those of the owner IC on that net, else all fixed pads on the net
        for r in movers:
            c = comps[r]
            o = owner.get(r)
            row = []
            for num, px, py in c['pads']:
                nm = c['pins'][num]
                allp = fixed_pads.get(nm, [])
                op = [(placed[o]['u'] + rot_pt(qx, qy, placed[o]['rot'])[0], placed[o]['v'] - rot_pt(qx, qy, placed[o]['rot'])[1])
                      for n2, qx, qy in comps[o]['pads'] if comps[o]['pins'][n2] == nm] if (o and o in placed and o not in mset) else []
                row.append(op or allp)
            tg[r] = row

        away_refs = {r for r in movers if any(n in AWAY_NETS for n in comps[r]['pins'].values())}
        sw_pads = [pt for pt in fixed_pads.get(SW_NET, [])]

        def pcost(ref, ou, ov, rot):
            tot = 0.0
            ws = comps[ref]['w']
            for k, (dx, dy, nm) in enumerate(padinfo[ref][rot]):
                w = ws[k]
                if w == 0.0:
                    continue
                x, y = ou + dx, ov + dy
                fp_ = tg[ref][k]
                if fp_:
                    d = min((x - a) ** 2 + (y - b) ** 2 for a, b in fp_) ** 0.5
                else:
                    d = 40.0
                    for r2, k2 in mover_pads[nm]:
                        if r2 != ref and r2 in st:
                            o2 = st[r2]
                            dx2, dy2, _ = padinfo[r2][o2[2]][k2]
                            d = min(d, ((x - o2[0] - dx2) ** 2 + (y - o2[1] - dy2) ** 2) ** 0.5)
                crit = CRIT_OWNERS.get(owner.get(ref), 1.0) > 1.0 and w >= 6.0
                tot += w * (d + (0.4 * max(0.0, d - (2.0 if crit else 3.0)) ** 2 if w >= 3.0 else 0.0))
            if ref in away_refs:
                for k, (dx, dy, nm) in enumerate(padinfo[ref][rot]):
                    for a, b in sw_pads:
                        dd = ((ou + dx - a) ** 2 + (ov + dy - b) ** 2) ** 0.5
                        if dd < AWAY_MM:
                            tot += 12.0 * (AWAY_MM - dd) ** 2
            return tot

        for r in movers:
            p = placed[r]
            cid = add(p['rect'], dict(kind='pas', ref=r))
            tid = add(p['txt'], dict(kind='txt', ref=r)) if p['txt'] else None
            st[r] = [p['u'], p['v'], p['rot'], p['slot'], cid, tid, p['rect'], p['txt']]
        lam = [2.0]

        GR = float(os.environ.get('GRAV', '0.5'))
        gc = {}
        for r in movers:
            o_ = owner.get(r)
            if o_ in placed:
                q_ = placed[o_]['rect']; gc[r] = ((q_[0] + q_[2]) / 2, (q_[1] + q_[3]) / 2)
            else:
                gc[r] = CELL_XY[cell_name(r)]

        def energy(ref, ou, ov, rot, rc, tx):
            e = pcost(ref, ou, ov, rot) + lam[0] * (pen_all(ref, rc, tx) + 2.0 * zpen(ref, rc) + 3.0 * bpen(rc, GAP_EDGE))
            e += GR * math.hypot((rc[0] + rc[2]) / 2 - gc[ref][0], (rc[1] + rc[3]) / 2 - gc[ref][1])
            if tx is None:
                e += 4.0
            elif (tx[2] - tx[0]) < (tx[3] - tx[1]):          # vertical text: small penalty so rows stay readable
                e += 0.6
            return e
        q = lambda v: round(v * 4) / 4.0
        acc = 0
        T0, T1 = t0, t1
        for it in range(iters):
            prog = it / float(iters)
            T = T0 * (T1 / T0) ** prog
            lam[0] = lam0 + (lam1 - lam0) * prog
            r = movers[rnd.randrange(len(movers))]
            ou, ov, rot, slot, cid, tid, rc0, tx0 = st[r]
            kind = rnd.random()
            if kind < 0.5:
                sg = 2.5 * (1 - prog) + 0.25
                nu, nv, nrot = q(ou + rnd.gauss(0, sg)), q(ov + rnd.gauss(0, sg)), rot
            elif kind < 0.9:
                nrot = rnd.choice(ROTS) if rnd.random() < 0.5 else rot
                ks = [k for k, w in enumerate(comps[r]['w']) if w > 0]
                if not ks:
                    continue
                k = rnd.choice(ks)
                fp_ = tg[r][k]
                if not fp_:
                    continue
                a, b = fp_[rnd.randrange(len(fp_))]
                ang, rad = rnd.random() * 6.2832, 1.0 + rnd.random() * (3.0 + 4.0 * (1 - prog))
                dx, dy, _ = padinfo[r][nrot][k]
                nu, nv = q(a + rad * math.cos(ang) - dx), q(b + rad * math.sin(ang) - dy)
            else:
                nu, nv, nrot = ou, ov, rnd.choice(ROTS)
            rect, (nu2, nv2) = rect_at(r, nu, nv, nrot, 'o')
            sl = dict(txt_slots(r, rect, 'RLBTrlbt'))
            if slot in sl and rnd.random() < 0.6:
                ks_ = [slot]
            else:
                ks_ = rnd.sample(list(sl), 3)
            # temporarily take this part out of the grid so it does not collide with itself
            remove(cid)
            if tid is not None:
                remove(tid)
            ecur = energy(r, ou, ov, rot, rc0, tx0)
            best = None
            for k_ in ks_:
                en = energy(r, nu2, nv2, nrot, rect, sl[k_])
                if best is None or en < best[0]:
                    best = (en, k_)
            en, k_ = best
            d = en - ecur
            if d <= 0 or rnd.random() < math.exp(-d / T):
                cid = add(rect, dict(kind='pas', ref=r))
                tid = add(sl[k_], dict(kind='txt', ref=r))
                st[r] = [nu2, nv2, nrot, k_, cid, tid, rect, sl[k_]]
                acc += 1
            else:
                cid = add(rc0, dict(kind='pas', ref=r))
                tid = add(tx0, dict(kind='txt', ref=r)) if tx0 else None
                st[r][4], st[r][5] = cid, tid
        lam[0] = 100.0
        bad = []
        for r in movers:
            u_, v_, rot, slot, cid, tid, rc, tx = st[r]
            remove(cid)
            if tid is not None:
                remove(tid)
            ok = board_ok(rc) and zpen(r, rc) == 0 and pen_all(r, rc, tx) < 1e-6 and tx is not None
            if ok:
                cid = add(rc, dict(kind='pas', ref=r)); tid = add(tx, dict(kind='txt', ref=r))
                st[r][4], st[r][5] = cid, tid
                placed[r].update(u=u_, v=v_, rot=rot, rect=rc, txt=tx, slot=slot)
            else:
                bad.append(r)
        print('anneal: %d moves accepted of %d; violators after SA: %d' % (acc, iters, len(bad)))
        # rebuild the global grid with the legal parts, then legalise the violators by ring search around their SA position
        grid.items = [(rc, m) for rc, m in items.values()]
        grid.d = collections.defaultdict(list)
        for idx, (rc, m) in enumerate(grid.items):
            for i in range(int(rc[0] // grid.cell), int(rc[2] // grid.cell) + 1):
                for j in range(int(rc[1] // grid.cell), int(rc[3] // grid.cell) + 1):
                    grid.d[(i, j)].append(idx)
        fails = []
        ZM[0] = 1.0
        for r in bad:
            u_, v_, rot0 = st[r][0], st[r][1], st[r][2]
            c = comps[r]
            kd = dict(kind='pas', ref=r)
            best = None
            for ring in range(0, 200):
                if best is not None and ring * 0.25 > best[0] / 1.0 + 1.0:
                    break
                ZM[0] = 1.0 if ring < 12 else (3.0 if ring < 24 else (5.0 if ring < 48 else 300.0))
                if ring in (12, 24, 48):
                    print('WARNING legalise %s needs zone margin %.0f' % (r, ZM[0]), flush=True)
                pts = [(0.0, 0.0)] if ring == 0 else [(i * 0.25, s_ * ring * 0.25) for i in range(-ring, ring + 1) for s_ in (-1, 1)] + [(s_ * ring * 0.25, j * 0.25) for j in range(-ring + 1, ring) for s_ in (-1, 1)]
                for dx_, dy_ in pts:
                    for rot in ROTS:
                        rect, (ou, ov) = rect_at(r, u_ + dx_, v_ + dy_, rot, 'o')
                        if not free(rect, r, kd):
                            continue
                        k_, tr_ = pick_slot(r, rect, 'RLBTrlbt')
                        if tr_ is None:
                            continue
                        cst = pcost(r, ou, ov, rot) + 2.0 * (abs(dx_) + abs(dy_))
                        if best is None or cst < best[0]:
                            best = (cst, ou, ov, rot, rect, tr_, k_)
            if best is None and not NOCLAMP[0]:
                NOCLAMP[0] = True
                print('WARNING legalise %s without clamps' % r, flush=True)
                for ring in range(0, 120):
                    if best is not None and ring * 0.25 > best[0] / 1.0 + 1.0:
                        break
                    ZM[0] = 300.0
                    pts = [(0.0, 0.0)] if ring == 0 else [(i * 0.25, s_ * ring * 0.25) for i in range(-ring, ring + 1) for s_ in (-1, 1)] + [(s_ * ring * 0.25, j * 0.25) for j in range(-ring + 1, ring) for s_ in (-1, 1)]
                    for dx_, dy_ in pts:
                        for rot in ROTS:
                            rect, (ou, ov) = rect_at(r, u_ + dx_, v_ + dy_, rot, 'o')
                            if not free(rect, r, kd):
                                continue
                            k_, tr_ = pick_slot(r, rect, 'RLBTrlbt')
                            if tr_ is None:
                                continue
                            cst = pcost(r, ou, ov, rot) + 2.0 * (abs(dx_) + abs(dy_))
                            if best is None or cst < best[0]:
                                best = (cst, ou, ov, rot, rect, tr_, k_)
                NOCLAMP[0] = False
            if best is None:
                fails.append(r)
                continue
            _, ou, ov, rot, rect, tr_, k_ = best
            placed[r].update(u=ou, v=ov, rot=rot, rect=rect, txt=tr_, slot=k_)
            grid.add(rect, dict(kind='pas', ref=r))
            grid.add(tr_, dict(kind='txt', ref=r))
            st[r][:3] = [ou, ov, rot]
        ZM[0] = 0.0
        print('legalised %d violators; unplaceable: %s' % (len(bad) - len(fails), fails))
        for r in fails:
            failed.append(r)

    if int(os.environ.get('SA', '0')) > 0:
        anneal(int(os.environ['SA']))
        print('anneal done %.0fs' % (time.time() - T_START), flush=True)
    # ---- floorplan: cells translated from the canvas to the board
    bbox = {}
    for r_, p_ in placed.items():
        b_ = bbox.setdefault(cell_name(r_), [1e9, 1e9, -1e9, -1e9])
        for q_ in (p_['rect'], p_['txt']):
            if q_:
                b_[0], b_[1], b_[2], b_[3] = min(b_[0], q_[0]), min(b_[1], q_[1]), max(b_[2], q_[2]), max(b_[3], q_[3])
    sizes = {n_: (round(b_[2] - b_[0], 1), round(b_[3] - b_[1], 1)) for n_, b_ in bbox.items()}
    print('CELL SIZES', json.dumps(sizes), flush=True)
    json.dump(dict(sizes=sizes, bbox=bbox), open(ROOT + 'ai-files/pcb/cells-v6.json', 'w'))
    sys.path.insert(0, ROOT + 'ai-files/helpers')
    import floorplan_v6
    if os.path.exists(FLOOR):
        fl = floorplan_v6.layout(sizes, json.load(open(FLOOR)), 0.5, 1.2)
    else:       # fallback: shelf packing so that a board is always produced
        fl, x_, y_, rowh = {'board': dict(ul=-60, ur=60, vf=-50, vr=0), 'cells': {}, 'tiles': {}}, 0.0, 0.0, 0.0
        for n_ in CELL_ORDER:
            w_, h_ = sizes[n_]
            if x_ + w_ > 118:
                x_, y_, rowh = 0.0, y_ + rowh + 4.0, 0.0
            fl['cells'][n_] = dict(u0=-60 + x_, v0=-50 + y_)
            fl['tiles'][n_] = [-60 + x_ - 0.9, -50 + y_ - 0.9, -60 + x_ + w_ + 0.9, -50 + y_ + h_ + 2.4]
            x_, rowh = x_ + w_ + 4.0, max(rowh, h_)
        fl['board']['vr'] = -50 + y_ + rowh + 2
    B_ = fl['board']
    set_board(B_['ul'], B_['ur'], B_['vf'], B_['vr'])
    HOLES[:] = [tuple(h_) for h_ in fl.get('holes', [])]
    TITLE_AT_FINAL = tuple(fl.get('title', (0.0, 0.0)))
    shift = {}
    for n_, s_ in fl['cells'].items():
        b_ = bbox[n_]
        du_ = dv_ = None
        if 'u0' in s_: du_ = s_['u0'] - b_[0]
        if 'u1' in s_: du_ = s_['u1'] - b_[2]
        if 'v0' in s_: dv_ = s_['v0'] - b_[1]
        if 'v1' in s_: dv_ = s_['v1'] - b_[3]
        for side_, key_ in (('left', 0), ('right', 2), ('front', 1), ('rear', 3)):
            if side_ in s_:
                rf_, ov_ = s_[side_]
                rc_ = placed[rf_]['rect']
                tgt_ = {'left': UL - ov_, 'right': UR + ov_, 'front': VF - ov_, 'rear': VR + ov_}[side_]
                if key_ in (0, 2): du_ = tgt_ - rc_[key_]
                else: dv_ = tgt_ - rc_[key_]
        shift[n_] = (du_, dv_)
    for r_, p_ in placed.items():
        du_, dv_ = shift[cell_name(r_)]
        p_['u'] += du_; p_['v'] += dv_
        p_['rect'] = (p_['rect'][0] + du_, p_['rect'][1] + dv_, p_['rect'][2] + du_, p_['rect'][3] + dv_)
        if p_['txt']:
            p_['txt'] = (p_['txt'][0] + du_, p_['txt'][1] + dv_, p_['txt'][2] + du_, p_['txt'][3] + dv_)
    if antenna_keep:
        du_, dv_ = shift['BM83']
        antenna_keep = dict(u0=UL, u1=antenna_keep['u1'] + du_, v0=antenna_keep['v0'] + dv_, v1=antenna_keep['v1'] + dv_)
    cellrect = {}
    for n_ in CELL_ORDER:
        du_, dv_ = shift[n_]
        b_ = bbox[n_]
        cellrect[n_] = (b_[0] + du_, b_[1] + dv_, b_[2] + du_, b_[3] + dv_)
    for r_, p_ in placed.items():            # sanity: every part inside the board, no cell overlap
        rc_ = p_['rect']
        if not (rc_[0] >= UL - 8.5 and rc_[2] <= UR + 2.0 and rc_[1] >= VF - 0.5 and rc_[3] <= VR + 1.5):
            print('WARNING outside board', r_, [round(x, 1) for x in rc_])
    for i_, a_ in enumerate(CELL_ORDER):
        for b2_ in CELL_ORDER[i_ + 1:]:
            if inter(cellrect[a_], cellrect[b2_], 1.0):
                print('WARNING cells overlap/too close', a_, b2_)
        for hn_, hu_, hv_ in HOLES:
            if inter(cellrect[a_], (hu_ - HOLE_R, hv_ - HOLE_R, hu_ + HOLE_R, hv_ + HOLE_R)):
                print('WARNING hole', hn_, 'overlaps cell', a_)
    # ---- decap snap (v6): lift every passive that serves an IC pin and re-place it as close as legal (snap_v6.py)
    if os.environ.get('SNAP', '1') != '0':
        import snap_v6
        kp_ = [(hu_ - HOLE_R, hv_ - HOLE_R, hu_ + HOLE_R, hv_ + HOLE_R) for hn_, hu_, hv_ in HOLES]
        kp_.append((TITLE_AT_FINAL[0] - 9.0, TITLE_AT_FINAL[1] - 1.0, TITLE_AT_FINAL[0] + 9.0, TITLE_AT_FINAL[1] + 1.0))
        if antenna_keep:
            kp_.append((antenna_keep['u0'], antenna_keep['v0'] - ANTENNA_MARGIN, antenna_keep['u1'], antenna_keep['v1'] + ANTENNA_MARGIN))
        snap_v6.run(dict(placed=placed, comps=comps, nets=nets, fps=fps, crt_s=crt_s, ispas=ispas, cell_name=cell_name, rot_pt=rot_pt,
                         rot_rect=rot_rect, inter=inter, board_ok=board_ok, rect_at=rect_at, txt_slots=txt_slots, cellrect=cellrect, keeps=kp_,
                         away_set=away_set, SW_NET=SW_NET, AWAY_MM=AWAY_MM, UL=UL, UR=UR, VF=VF, VR=VR, MM=MM))
    # ---- free rectangle finder for board texts
    def find_free(w, h, around=None):
        best = None
        v = VF + 1.0
        while v + h < VR - 0.5:
            u = UL + 1.0
            while u + w < UR - 0.5:
                rc = (u, v, u + w, v + h)
                ok = slot_free('', rc)
                if ok:
                    d = 0 if around is None else abs(u + w / 2 - around[0]) + abs(v + h / 2 - around[1])
                    if best is None or d < best[0]:
                        best = (d, rc)
                u += 1.0
            v += 1.0
        return best[1] if best else None

    # ---- footprints into the board
    for ref, p in placed.items():
        f = fps[ref]
        f.SetOrientationDegrees(p['rot'])
        f.SetPosition(ip(K(p['u'], p['v'])))
        rf = f.Reference()
        rf.SetLayer(pcbnew.F_SilkS)
        rf.SetTextSize(pcbnew.VECTOR2I(int(TXT_H * MM), int(TXT_H * MM)))
        rf.SetTextThickness(int(TXT_T * MM))
        rf.SetTextAngleDegrees(90 if (p['slot'] or 'R').islower() else 0)
        rf.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        rf.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        if p['txt']:
            t = p['txt']
            rf.SetPosition(ip(K((t[0] + t[2]) / 2, (t[1] + t[3]) / 2)))
            rf.SetVisible(True)
        elif p.get('fab'):                      # passive labels on the assembly layer (silk has no room near the decoupling)
            rf.SetLayer(pcbnew.F_Fab)
            rf.SetTextAngleDegrees(0)
            rf.SetPosition(ip(K(p['u'], p['v'])))
            rf.SetVisible(True)
        else:
            rf.SetLayer(pcbnew.F_Fab)
            rf.SetVisible(False)
        vl = f.Value()
        vl.SetLayer(pcbnew.F_Fab)
        vl.SetTextSize(pcbnew.VECTOR2I(int(0.6 * MM), int(0.6 * MM)))
        vl.SetVisible(False)
        board.Add(f)

    # ---- cell outlines + titles on F.SilkS (sides on the board edge are left open)
    def seg(u0, v0, u1, v1, w=0.15):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.F_SilkS)
        s.SetWidth(int(w * MM))
        s.SetStart(ip(K(u0, v0))); s.SetEnd(ip(K(u1, v1)))
        board.Add(s)
    for n_ in CELL_ORDER:
        r0, r1, r2, r3 = fl['tiles'][n_]
        eps = 0.05
        if r0 > UL + eps: seg(r0, max(r1, VF + 0.6), r0, min(r3, VR - 0.6))
        if r2 < UR - eps: seg(r2, max(r1, VF + 0.6), r2, min(r3, VR - 0.6))
        if r1 > VF + eps: seg(max(r0, UL + 0.6), r1, min(r2, UR - 0.6), r1)
        if r3 < VR - eps: seg(max(r0, UL + 0.6), r3, min(r2, UR - 0.6), r3)
        t = pcbnew.PCB_TEXT(board)
        t.SetText(TITLES[n_])
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(int(0.7 * MM), int(0.7 * MM)))
        t.SetTextThickness(int(0.12 * MM))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        t.SetPosition(ip(K((r0 + r2) / 2, (r1 + 0.65) if fl.get('title_bottom', {}).get(n_) else (r3 - 0.65))))
        board.Add(t)

    # ---- texts
    def text(s, u, v, size=0.8, thick=0.12):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(s)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(int(size * MM), int(size * MM)))
        t.SetTextThickness(int(thick * MM))
        t.SetPosition(ip(K(u, v)))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        board.Add(t)

    for nm, hu, hv in HOLES:
        mh = pcbnew.FootprintLoad(FPLIB, HOLE_FP)
        mh.SetReference(nm)
        mh.SetValue('M3 PTH GND')
        mh.SetFPID(pcbnew.LIB_ID('DesktopSpeaker', HOLE_FP))
        mh.SetAttributes(mh.GetAttributes() | pcbnew.FP_BOARD_ONLY)
        for p_ in mh.Pads():
            p_.SetNet(netitems['GND'])
        mh.SetPosition(ip(K(hu, hv)))
        mh.Reference().SetVisible(False)
        mh.Value().SetVisible(False)
        board.Add(mh)

    t = pcbnew.PCB_TEXT(board)                 # board name/revision on the (empty) bottom silk, mirrored
    t.SetText('DesktopSpeaker rev A 2026-10-06 (placement only)')
    t.SetLayer(pcbnew.B_SilkS)
    t.SetMirrored(True)
    t.SetTextSize(pcbnew.VECTOR2I(int(1.5 * MM), int(1.5 * MM)))
    t.SetTextThickness(int(0.2 * MM))
    t.SetPosition(ip(K((UL + UR) / 2, (VF + VR) / 2)))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    board.Add(t)
    text('DesktopSpeaker rev A', TITLE_AT_FINAL[0], TITLE_AT_FINAL[1], 1.0, 0.15)

    # ---- outline
    def shape(kind, pts):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(kind)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(int(0.1 * MM))
        if kind == pcbnew.SHAPE_T_SEGMENT:
            s.SetStart(ip(pts[0])); s.SetEnd(ip(pts[1]))
        else:
            s.SetArcGeometry(ip(pts[0]), ip(pts[1]), ip(pts[2]))
        board.Add(s)
    xl, xr, yt, yb, r = X0 + UL, X0 + UR, Y0 - VR, Y0 - VF, CORNER_R
    d = r * (1 - math.sqrt(0.5))
    S = pcbnew.SHAPE_T_SEGMENT
    shape(S, ((xl + r, yt), (xr - r, yt))); shape(S, ((xr, yt + r), (xr, yb - r)))
    shape(S, ((xr - r, yb), (xl + r, yb))); shape(S, ((xl, yb - r), (xl, yt + r)))
    A = pcbnew.SHAPE_T_ARC
    shape(A, ((xr - r, yt), (xr - d, yt + d), (xr, yt + r))); shape(A, ((xr, yb - r), (xr - d, yb - d), (xr - r, yb)))
    shape(A, ((xl + r, yb), (xl + d, yb - d), (xl, yb - r))); shape(A, ((xl, yt + r), (xl + d, yt + d), (xl + r, yt)))

    # ---- antenna keep-out (copper rule area, tracks/vias/pour; no footprint restriction because the BM83 itself sits partly in it)
    if antenna_keep:
        a = antenna_keep
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetZoneName('BM83_ANTENNA_KEEPOUT')
        ls = pcbnew.LSET()
        for lay in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            ls.AddLayer(lay)
        z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        ol = z.Outline()
        ol.NewOutline()
        for pu, pv in ((a['u0'], a['v0']), (a['u1'], a['v0']), (a['u1'], a['v1']), (a['u0'], a['v1'])):
            x, y = K(pu, pv)
            ol.Append(int(round(x * MM)), int(round(y * MM)))
        board.Add(z)

    pcbnew.SaveBoard(OUT, board)

    os.makedirs(os.path.dirname(LAYOUT_JSON), exist_ok=True)
    cad = {}
    for ref, p in placed.items():
        if TALL.match(ref) or ref in ANCHORS or comps[ref]['kind'] != 'pas':
            rr = p['rect']
            cad[ref] = dict(origin_u=round(p['u'], 3), origin_v=round(p['v'] - VCEN, 3), rot=p['rot'],
                            cy_u=round((rr[0] + rr[2]) / 2, 3), cy_v=round((rr[1] + rr[3]) / 2 - VCEN, 3),
                            rect=[round(rr[0], 3), round(rr[1] - VCEN, 3), round(rr[2], 3), round(rr[3] - VCEN, 3)])
    ant = dict(antenna_keep, v0=antenna_keep['v0'] - VCEN, v1=antenna_keep['v1'] - VCEN) if antenna_keep else None
    json.dump(dict(board=dict(w=BW, d=BD, u0=UL, u1=UR, v0=-BD / 2, v1=BD / 2, corner_r=CORNER_R, rear_edge_cad_y=REAR_CAD_Y, centre_cad_y=PCB_CY_CAD, v_design_offset=VCEN),
                   holes=[dict(name=n, u=u, v=v - VCEN) for n, u, v in HOLES], parts=cad, sheets={r: c['sheet'] for r, c in comps.items()}, owner=owner, antenna=ant, failed=failed,
                   noslot=[r for r, p in placed.items() if not p['txt']]),
              open(LAYOUT_JSON, 'w'), indent=1)
    print('placed', len(placed), 'failed', failed, 'noslot', [r for r, p in placed.items() if not p['txt']])


main()
