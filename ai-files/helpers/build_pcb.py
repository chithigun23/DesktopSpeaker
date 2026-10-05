# -*- coding: utf-8 -*-
"""Generate DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb: PLACEMENT ONLY (no tracks, no copper zones except rule areas).

Run through build_pcb.sh (exports the netlist with kicad-cli, then runs this file in the flatpak KiCad python):
    ai-files/helpers/build_pcb.sh
Inputs : /tmp/ds_net.xml (kicadxml netlist of the root sheet), project footprint library (kicad-library/footprint).
Outputs: DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb, ai-files/pcb/layout.json (connector/hole positions for the CAD).
Frame  : u = right, v = rear (as the CAD: X right, Y rear). KiCad x = X0 + u, y = Y0 - v (rear edge at the top of the sheet).
Method : anchors (ICs, connectors, inductors) are placed by hand in ANCHORS; satellites (small ICs, diodes, FETs, crystals) and
         all R/C are placed by a greedy ring search that minimises pad-to-pad distance to already placed pins on the same nets,
         with courtyard gap rules, a reference text slot per part, and board/hole/antenna obstacles.
Re-running overwrites the board (manual edits in KiCad are lost); edit the tables below instead.
"""
import math, json, re, sys, os, collections
import xml.etree.ElementTree as ET
import pcbnew

ROOT = '/home/chithi/Desktop/DesktopSpeaker/'
FPLIB = ROOT + 'DesktopSpeaker-kicad/kicad-library/footprint'
NET = '/tmp/ds_net.xml'
OUT = ROOT + 'DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb'
LAYOUT_JSON = ROOT + 'ai-files/pcb/layout.json'
MM = 1e6

# ------------------------------------------------------------------ board parameters
UL, UR = -59.0, 55.0                  # board left/right edge: u = CAD X (0 = enclosure centre); right edge limited by the rocker body
BW, BD = UR - UL, 92.0                # board width (u) x depth (v)
VF, VR = -BD / 2, BD / 2
CORNER_R = 3.0
X0, Y0 = 150.0 - (UL + UR) / 2, 100.0     # sheet position of u = 0, v = 0 (mm)
HOLES = [('H1', UL + 3.5, -(BD / 2 - 3.5)), ('H2', 51.5, -(BD / 2 - 3.5)), ('H3', UL + 3.5, BD / 2 - 3.5), ('H4', 51.5, 18.5)]
HOLE_R = 3.45 + 0.3
PCB_CY_CAD = 156.5 - BD / 2           # CAD y of the board centre (rear edge fixed at 156.5)
GAP_EDGE = 0.5
TXT_H = 0.8                           # reference text height/width (mm)
TXT_T = 0.12

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


# ------------------------------------------------------------------ anchors: ref -> (mode, a, b, rot[, overhang])
# 'c': courtyard centre at (a, b); 'o': footprint origin at (a, b);
# 'rear'/'front'/'left'/'right': courtyard flush to that board edge (+overhang), a = position along the edge
R = VR
ANCHORS = {
    'J1': ('rear', 20.0, 180, 1.25),    # USB-C: shell tab pads end 0.5 mm inside the edge, body 1.25 mm past it
    'J2': ('rear', -26.0, 270, -0.30),  # 3.5 mm jacks, bore to the rear, 0.3 mm inside the edge (silk clearance)
    'J3': ('rear', -12.0, 270, -0.30),
    'SW100': ('rear', -1.0, 0, 0.0),    # tact switch: plunger to the rear
    'SW101': ('o', 52.0, 32.5, 90),     # rocker wire pads at the rear-right corner, panel body overhangs the edges
    'J8': ('c', -44.0, 35.0, 0),
    'U1': ('left', 14.0, 90, 8.0),      # BM83: antenna overhangs the left edge by 8 mm
    'J5': ('right', -8.0, 270, 0.0),   # Micro-Fit, mating face at the right edge
    'J9': ('front', -17.0, 0, 0.0), 'J10': ('front', 0.5, 0, 0.0), 'J11': ('front', 18.0, 0, 0.0),
    'J7': ('front', -42.0, 0, 0.0), 'J6': ('front', -33.0, 0, 0.0),
    'J4': ('c', 33.0, 33.0, 0),
    'U3': ('c', -37.0, -22.0, 0),
    'L201': ('c', -17.0, -24.4, 0), 'L202': ('c', -17.0, -10.2, 0),
    'L203': ('c', 0.5, -24.4, 0), 'L204': ('c', 0.5, -10.2, 0),
    'L205': ('c', 18.0, -24.4, 0), 'L206': ('c', 18.0, -10.2, 0),
    'U6': ('c', -8.25, 5.0, 0), 'U7': ('c', 18.0, 5.0, 0),
    'U25': ('c', 33.0, -33.5, 0), 'L200': ('c', 43.0, -35.0, 0), 'C275': ('c', 45.0, -22.5, 0),
    'U4': ('c', 38.0, 3.0, 0), 'L1': ('c', 28.0, 3.0, 0),
    'U11': ('c', 20.0, 27.0, 0),
    'U24': ('c', -22.0, 4.0, 0), 'U2': ('c', -8.0, 14.0, 0),
}
# satellites: greedy placement (hint = zone centre, used when no placed pin attracts them)
SATELLITES = [
    ('D5', 14.0, 33.0), ('D6', 26.0, 33.0), ('D1', 20.0, 22.0), ('U19', 8.0, 24.0), ('D7', 12.0, 26.0),
    ('Q103', 46.0, 2.0), ('U5', 31.0, -8.0), ('U12', 36.0, -8.0), ('U13', 31.0, -12.0), ('U16', 36.0, -12.0),
    ('U17', 31.0, -16.0), ('U20', 36.0, -16.0), ('U21', 31.0, -20.0), ('Q104', 36.0, -20.0),
    ('Q100', 44.0, 8.0), ('Q101', 46.0, 12.0), ('Q102', 38.0, 12.0),
    ('U14', -4.0, 18.0), ('L2', -2.0, 22.0), ('U15', -46.0, -6.0), ('L3', -41.0, -8.0),
    ('U22', -18.0, 12.0), ('U23', -16.0, 14.0), ('Y200', -26.0, 10.0), ('Y170', -4.0, 22.0),
    ('U8', -27.0, 22.0), ('U9', -18.0, 22.0), ('U10', -8.0, 22.0), ('D200', -30.0, 30.0), ('D201', -16.0, 30.0),
    ('FB200', -26.0, 8.0),
]
SHEET_HINT = {'USB_PD': (20, 28), 'Battery_Charger': (36, 4), 'Fuel_Gauge_Power': (36, -10), 'Amplifiers': (4, -8),
              'Bluetooth': (-38, 12), 'Bluetooth_Power': (-44, -4), 'MCU': (-37, -22), 'USB_Audio': (-8, 12),
              'Source_Select_ADC': (-22, 6), 'Headphone_Aux': (-18, 22), 'Logic_Audio_Power': (-2, 16), '': (0, 0)}
NETBASED = {'D1', 'D5', 'D6', 'D7', 'D200', 'D201', 'Q100', 'Q101', 'Q102', 'Q103', 'Q104', 'Y170', 'Y200', 'L2', 'L3', 'FB200'}
ANTENNA_MARGIN = 3.0


def stretch(u, v):
    """tables below were drawn for a 110 x 84 board: stretch to the current outline."""
    dv = (BD - 84.0) / 2
    return (u + (UL + 55.0) if u < -20.0 else u), (v + dv if v > 0 else v - dv if v < 0 else v)


def _fix_tables():
    for k, a in list(ANCHORS.items()):
        if a[0] in ('c', 'o'):
            u, v = stretch(a[1], a[2])
            ANCHORS[k] = (a[0], u, v) + a[3:]
        elif a[0] in ('rear', 'front'):
            ANCHORS[k] = (a[0], stretch(a[1], 0)[0]) + a[2:]
        else:
            ANCHORS[k] = (a[0], stretch(0, a[1])[1]) + a[2:]
    SATELLITES[:] = [(r,) + stretch(u, v) for r, u, v in SATELLITES]
    for k, (u, v) in list(SHEET_HINT.items()):
        SHEET_HINT[k] = stretch(u, v)


STEP = 0.5                           # ring search step (mm)


# ------------------------------------------------------------------ helpers
_fix_tables()


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

    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    netitems = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netitems[name] = ni

    # ---- footprints loaded at the origin, rotation 0: courtyard rect and net pad positions in footprint coordinates
    fps, crt = {}, {}
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
            return 2.0 if 'pas' in (ka, kb) else 1.0
        if 'qfn' in (ka, kb):
            if 'pas' in (ka, kb) and conn(a['ref'], b['ref']):
                return 0.6
            return 1.0
        if ka == 'pas' and kb == 'pas':
            return 0.5
        return 0.6

    def keep(rect, label):
        grid.add(rect, dict(kind='keep', ref=label))
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
            attract[comps[ref]['pins'][num]].append((ou + x, ov - y, ref))

    def free(rect, ref, kd, exempt_edge=False):
        if not exempt_edge and not board_ok(rect):
            return False
        for orect, meta in grid.near(rect, 2.1):
            if meta['ref'] != ref and inter(rect, orect, gap_for(kd, meta)):
                return False
        return True

    def txt_slots(ref, rect, order):
        w, h = len(ref) * TXT_H * 0.95 + 0.3, TXT_H + 0.3
        cx, cy, g = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2, 0.2
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
            print('WARNING anchor overlap', ref, [round(x, 2) for x in rect])
        commit(ref, ou, ov, rot, rect, None, None)
        if ref == 'U1':
            ax = rot_rect((-8.0, -22.0, 8.0, -11.0), rot)
            antenna_keep = dict(u0=UL, u1=ou + ax[2], v0=ov - ax[3], v1=ov - ax[1])
            keep((UL - 20, antenna_keep['v0'] - ANTENNA_MARGIN, antenna_keep['u1'], antenna_keep['v1'] + ANTENNA_MARGIN), 'ANT')
    for ref in ANCHORS:                       # reference text slots after all anchor courtyards are known
        k, tr = pick_slot(ref, placed[ref]['rect'], 'BTRLbtrl')
        placed[ref]['txt'], placed[ref]['slot'] = tr, k
        if tr:
            grid.add(tr, dict(kind='txt', ref=ref))

    # ---- greedy placer
    def attractors_for(ref):
        c, out = comps[ref], []
        for num, px, py in c['pads']:
            nm = c['pins'][num]
            if nm == 'GND' or len(nets[nm]) > 70:
                out.append((None, 0.0))
                continue
            w = 1.0 if len(nets[nm]) <= 4 else (0.6 if len(nets[nm]) <= 12 else 0.3)
            pts = [(a, b, r) for a, b, r in attract.get(nm, ()) if r != ref]
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
            tot += (1.0 if strict else (0.02 if any(a[0] for a in attr) else 0.5)) * (abs(u - hint[0]) + abs(v - hint[1]))
        if rot in (180, 270):
            tot += 0.3
        return tot

    failed = []

    def place_greedy(ref, hint, relax=False):
        c = comps[ref]
        kd = dict(kind=c['kind'], ref=ref)
        attr = attractors_for(ref)
        hint = hint or SHEET_HINT.get(c['sheet'], (0, 0))
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
                    cst = cost_of(ref, ou, ov, rot, attr, hint, strict)
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
        return True

    def try_place(ref, hint):
        if not place_greedy(ref, hint) and not place_greedy(ref, hint, relax=True):
            failed.append(ref)

    for ref, hu, hv in SATELLITES:
        try_place(ref, (hu, hv))

    rest = [r for r in comps if r not in placed and comps[r]['kind'] == 'pas']
    rest.sort(key=lambda r: (0 if r[0] == 'C' else 1, min([len(nets[n]) for n in comps[r]['pins'].values() if n != 'GND'] or [99]), r))
    while rest:
        remaining, progress = [], False
        for ref in rest:
            if not any(a[0] for a in attractors_for(ref)):
                remaining.append(ref)
                continue
            try_place(ref, SHEET_HINT.get(comps[ref]['sheet']))
            progress = True
        if not progress:
            for ref in remaining:
                try_place(ref, SHEET_HINT.get(comps[ref]['sheet']))
            break
        rest = remaining
    failed += [r for r in comps if r not in placed and r not in failed]

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
        else:
            rf.SetLayer(pcbnew.F_Fab)
            rf.SetVisible(False)
        vl = f.Value()
        vl.SetLayer(pcbnew.F_Fab)
        vl.SetTextSize(pcbnew.VECTOR2I(int(0.6 * MM), int(0.6 * MM)))
        vl.SetVisible(False)
        board.Add(f)

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
        mh = pcbnew.FootprintLoad(FPLIB, 'MountingHole_3.2mm_M3')
        mh.SetReference(nm)
        mh.SetValue('M3 NPTH 3.2')
        mh.SetFPID(pcbnew.LIB_ID('DesktopSpeaker', 'MountingHole_3.2mm_M3'))
        mh.SetAttributes(mh.GetAttributes() | pcbnew.FP_BOARD_ONLY)
        mh.SetPosition(ip(K(hu, hv)))
        mh.Reference().SetVisible(False)
        mh.Value().SetVisible(False)
        board.Add(mh)
        text(nm + ' M3', hu, hv + (-3.4 if hv > 0 else 3.4), 0.8, 0.12)     # label on the inner side of the ring (silk is under the screw head)

    t = pcbnew.PCB_TEXT(board)                 # board name/revision on the (empty) bottom silk, mirrored
    t.SetText('DesktopSpeaker rev A 2026-10-06 (placement only)')
    t.SetLayer(pcbnew.B_SilkS)
    t.SetMirrored(True)
    t.SetTextSize(pcbnew.VECTOR2I(int(1.5 * MM), int(1.5 * MM)))
    t.SetTextThickness(int(0.2 * MM))
    t.SetPosition(ip(K(0.0, 0.0)))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    board.Add(t)
    title = find_free(26.0, 1.4, around=(0, VF))
    if title:
        text('DesktopSpeaker rev A', (title[0] + title[2]) / 2, (title[1] + title[3]) / 2, 1.0, 0.15)
    else:
        print('NOTE: no room for a top-side board title (bottom silk only)')

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
            cad[ref] = dict(origin_u=round(p['u'], 3), origin_v=round(p['v'], 3), rot=p['rot'],
                            cy_u=round((rr[0] + rr[2]) / 2, 3), cy_v=round((rr[1] + rr[3]) / 2, 3), rect=[round(x, 3) for x in rr])
    json.dump(dict(board=dict(w=BW, d=BD, u0=UL, u1=UR, v0=VF, v1=VR, corner_r=CORNER_R, rear_edge_cad_y=156.5, centre_cad_y=PCB_CY_CAD),
                   holes=[dict(name=n, u=u, v=v) for n, u, v in HOLES], parts=cad, antenna=antenna_keep, failed=failed,
                   noslot=[r for r, p in placed.items() if not p['txt']]),
              open(LAYOUT_JSON, 'w'), indent=1)
    print('placed', len(placed), 'failed', failed, 'noslot', [r for r, p in placed.items() if not p['txt']])


main()
