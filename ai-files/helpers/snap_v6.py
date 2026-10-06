# -*- coding: utf-8 -*-
"""Decap snap stage (v6, placement only): after the cell packer and floorplan shift, every R/C/FB that has an IC pin on one of its
signal nets is lifted off the board and re-placed in priority order as close as legal to the IC pin it serves (critical decoupling first).
Reference designators of passives live on F.Fab (0402) so no silk label slot is needed; courtyard gap 0.25 mm (0402/0402) / 0.3 mm, pad to pad >= 0.2 mm.
Called from build_pcb_v6.py with the closure objects in ctx (a dict)."""
import math, re, collections, time

PAD_GAP = 0.2
CY_GAP_0402 = 0.25
CY_GAP_PAS = 0.30
CY_GAP_TALL = 0.5
CY_GAP_IC = 0.15
CRIT_ORDER = ['U6', 'U7', 'U4', 'U25', 'U24', 'U3', 'U1', 'U15', 'U22', 'U23', 'U2', 'U14', 'U11']


def capv(c):
    m = re.match(r'\s*([\d.]+)\s*([pnuµm]?)', c['value'].replace(',', '.'), re.I)
    if not m:
        return 1.0
    try:
        v = float(m.group(1))
    except ValueError:
        return 1.0
    return v * {'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'µ': 1e-6, 'm': 1e-3}.get(m.group(2).lower(), 1e-6)


def run(ctx):
    T0 = time.time()
    placed, comps, nets, fps, crt_s = ctx['placed'], ctx['comps'], ctx['nets'], ctx['fps'], ctx['crt_s']
    ispas, cell_name, rot_pt, rot_rect, inter, board_ok = ctx['ispas'], ctx['cell_name'], ctx['rot_pt'], ctx['rot_rect'], ctx['inter'], ctx['board_ok']
    rect_at, txt_slots, cellrect, keeps = ctx['rect_at'], ctx['txt_slots'], ctx['cellrect'], ctx['keeps']
    away_set, SW_NET, AWAY_MM, UL, UR, VF, VR = ctx['away_set'], ctx['SW_NET'], ctx['AWAY_MM'], ctx['UL'], ctx['UR'], ctx['VF'], ctx['VR']
    MM = ctx['MM']
    padgeo = {}
    for r, f in fps.items():
        padgeo[r] = [(p.GetNumber(), p.GetPosition().x / MM, p.GetPosition().y / MM, p.GetSize().x / MM, p.GetSize().y / MM, comps[r]['pins'].get(p.GetNumber()))
                     for p in f.Pads()]

    def pboxes(ref, ou, ov, rot):
        out = []
        sw = int(round(rot)) % 180 == 0
        for num, px, py, w, h, net in padgeo[ref]:
            x, y = rot_pt(px, py, rot)
            cu, cv = ou + x, ov - y
            if not sw:
                w, h = h, w
            out.append((cu - w / 2, cv - h / 2, cu + w / 2, cv + h / 2, net, cu, cv))
        return out

    def trect(ref, ou, ov, rot):
        rr = rot_rect(crt_s[ref], rot)
        return (ou + rr[0], ov - rr[3], ou + rr[2], ov - rr[1])

    is0402 = lambda r: '0402' in comps[r]['fp']
    cap_gnd = lambda r: r[0] == 'C' and any(n == 'GND' for n in comps[r]['pins'].values())

    # ---- which passives are lifted
    ic_of_net = collections.defaultdict(list)       # net -> IC pins (ref, pin)
    for n, lst in nets.items():
        non_t = [(r, p) for r, p in lst if not ispas(r) and not r.startswith('H') and comps[r]['kind'] != 'tall']
        ic_of_net[n] = non_t or [(r, p) for r, p in lst if not ispas(r) and not r.startswith('H')]
    pas_all = [r for r in placed if comps[r]['kind'] == 'pas']

    def sig_nets(r):
        return [n for n in set(comps[r]['pins'].values()) if n and n != 'GND' and len(nets[n]) <= 70]

    lifted = [r for r in pas_all if sig_nets(r)]
    lifted_set = set(lifted)

    # ---- spatial hash of everything placed (items removable per ref)
    C = 2.0
    bins = collections.defaultdict(list)
    owned = collections.defaultdict(list)

    def cells(rect):
        return [(ix, iy) for ix in range(int(math.floor(rect[0] / C)), int(math.floor(rect[2] / C)) + 1)
                for iy in range(int(math.floor(rect[1] / C)), int(math.floor(rect[3] / C)) + 1)]

    def add(rect, item):
        owned[item[2]].append((rect, item))
        for k in cells(rect):
            bins[k].append(item)

    def drop(ref):
        for rect, item in owned.pop(ref, ()):
            for k in cells(rect):
                bins[k] = [x for x in bins[k] if x is not item]

    def near(rect, g):
        seen, out = set(), []
        for k in cells((rect[0] - g, rect[1] - g, rect[2] + g, rect[3] + g)):
            for it in bins.get(k, ()):
                if id(it) not in seen:
                    seen.add(id(it)); out.append(it)
        return out

    def add_part(ref, true_rect):
        p = placed[ref]
        kd = comps[ref]['kind']
        rc = true_rect if kd == 'pas' else p['rect']
        add(rc, ('C', rc, ref, kd, is0402(ref)))
        for pb in pboxes(ref, p['u'], p['v'], p['rot']):
            add(pb, ('P', pb[:4], ref))
        if p.get('txt'):
            add(p['txt'], ('T', p['txt'], ref))

    for ref, p in placed.items():
        if ref in lifted_set:
            continue
        add_part(ref, trect(ref, p['u'], p['v'], p['rot']) if comps[ref]['kind'] == 'pas' else None)
    kobs = list(keeps)

    def legal(ref, ou, ov, rot, region, blockers=None):
        """None if illegal. With a set `blockers`, collisions with evictable lifted passives are collected instead (hard collisions still return None)."""
        cr = trect(ref, ou, ov, rot)
        if cr[0] < region[0] or cr[2] > region[2] or cr[1] < region[1] or cr[3] > region[3]:
            return None
        if not board_ok(cr):
            return None
        for k in kobs:
            if inter(cr, k):
                return None
        mine = is0402(ref)
        bad = set()
        for it in near(cr, 0.5):
            if it[2] == ref:
                continue
            hit = False
            if it[0] == 'C':
                if it[3] == 'pas':
                    g = CY_GAP_0402 if (mine and it[4]) else CY_GAP_PAS
                elif it[3] == 'tall':
                    g = CY_GAP_TALL
                else:
                    g = CY_GAP_IC
                hit = inter(cr, it[1], g)
            elif it[0] == 'T':
                hit = inter(cr, it[1], 0.05)
            if hit:
                if blockers is None or it[2] not in evictable:
                    return None
                bad.add(it[2])
        pbs = pboxes(ref, ou, ov, rot)
        for pb in pbs:
            for it in near(pb[:4], PAD_GAP):
                if it[0] == 'P' and it[2] != ref and inter(pb[:4], it[1], PAD_GAP):
                    if blockers is None or it[2] not in evictable:
                        return None
                    bad.add(it[2])
        if blockers is not None:
            blockers |= bad
        return cr, pbs

    # ---- static pin coordinates
    def pin_xy(ref, pin):
        p = placed[ref]
        out = []
        for num, px, py, w, h, net in padgeo[ref]:
            if num == pin:
                x, y = rot_pt(px, py, p['rot'])
                out.append((p['u'] + x, p['v'] - y))
        return out

    gnd_pts = collections.defaultdict(list)
    for r, p in placed.items():
        if comps[r]['kind'] in ('qfn', 'ic'):
            for num, px, py, w, h, net in padgeo[r]:
                if net == 'GND':
                    x, y = rot_pt(px, py, p['rot'])
                    gnd_pts[cell_name(r)].append((p['u'] + x, p['v'] - y))
    sw_pts = []
    for r, p in placed.items():
        for pb in pboxes(r, p['u'], p['v'], p['rot']):
            if pb[4] == SW_NET:
                sw_pts.append((pb[5], pb[6]))

    # ---- per passive: owning IC (nearest IC pin on its signal nets), priority
    info = {}
    for r in lifted:
        p0 = placed[r]
        cn = cell_name(r)
        best = None
        for n in sig_nets(r):
            for (o, pin) in ic_of_net[n]:
                for q in pin_xy(o, pin):
                    d = math.hypot(q[0] - p0['u'], q[1] - p0['v'])
                    if best is None or d < best[0]:
                        best = (d, o)
        info[r] = dict(owner=best[1] if best else None, cell=cn, orig=(p0['u'], p0['v'], p0['rot']))
    crit_idx = {u: i for i, u in enumerate(CRIT_ORDER)}

    def tier_of(r):
        o = info[r]['owner']
        small = is0402(r)
        if o in crit_idx and r[0] == 'C' and (small or cap_gnd(r)):
            return 0
        if small and cap_gnd(r):
            return 1
        return 2 if small else 3

    def prio(r):
        o = info[r]['owner']
        return (tier_of(r), 0 if is0402(r) else 1, crit_idx.get(o, 99), capv(comps[r]) if r[0] == 'C' else 1.0, r)

    order = sorted(lifted, key=prio)
    evictable = {r for r in lifted if tier_of(r) >= 2 or (tier_of(r) == 1 and info[r]['owner'] not in crit_idx)}
    dyn = collections.defaultdict(list)          # net -> (ref, u, v)
    for r in pas_all:
        if r not in lifted_set:
            for pb in pboxes(r, placed[r]['u'], placed[r]['v'], placed[r]['rot']):
                if pb[4] and pb[4] != 'GND':
                    dyn[pb[4]].append((r, pb[5], pb[6]))
    cell_grow = lambda cn, m: (cellrect[cn][0] - m, cellrect[cn][1] - m, cellrect[cn][2] + m, cellrect[cn][3] + m)
    gone = set()                                  # lifted passives currently not on the board

    def model(r):
        """(cost function, centre) for passive r from the current dyn/placed state; None when it has no target."""
        cn = info[r]['cell']
        orig = info[r]['orig']
        pad_t = []
        for num, px, py, w, h, net in padgeo[r]:
            if not net or net == 'GND' or len(nets[net]) > 70:
                continue
            same = [(o, pin) for (o, pin) in ic_of_net[net] if o in placed and cell_name(o) == cn]
            use = same or [(o, pin) for (o, pin) in ic_of_net[net] if o in placed]
            pts = []
            for (o, pin) in use:
                pts += pin_xy(o, pin)
            if not pts:
                pts = [(u, v) for (rr, u, v) in dyn.get(net, ()) if rr != r and rr not in gone]
            pts.sort(key=lambda q: abs(q[0] - orig[0]) + abs(q[1] - orig[1]))
            pts = pts[:6]
            if pts:
                pad_t.append((num, px, py, pts))
        if not pad_t:
            return None
        nsig = len(pad_t)
        gps = gnd_pts.get(cn, [])
        away = r in away_set
        gpad = [(px, py) for num, px, py, w, h, net in padgeo[r] if net == 'GND']

        def cost(ou, ov, rot, pref=True):
            tot = 0.0
            for num, px, py, pts in pad_t:
                x, y = rot_pt(px, py, rot)
                a, b = ou + x, ov - y
                tot += min(math.hypot(a - q[0], b - q[1]) for q in pts) / nsig
                if away:
                    for q in sw_pts:
                        dd = math.hypot(a - q[0], b - q[1])
                        if dd < AWAY_MM:
                            tot += 12.0 * (AWAY_MM - dd) ** 2
            if gps and gpad and r[0] == 'C':
                for px, py in gpad:
                    x, y = rot_pt(px, py, rot)
                    tot += 0.08 * min(math.hypot(ou + x - q[0], ov - y - q[1]) for q in gps)
            return tot + (0.03 * (abs(ou - orig[0]) + abs(ov - orig[1])) if pref else 0.0)
        ctr = min((q for _n, _x, _y, pts in pad_t for q in pts[:1]), key=lambda q: abs(q[0] - orig[0]) + abs(q[1] - orig[1]))
        return cost, ctr

    def cands_for(r, cost, ctr, region, rad, step, maxcost=None):
        n = int(rad / step)
        out = []
        for ix in range(-n, n + 1):
            for iy in range(-n, n + 1):
                ou, ov = round(ctr[0] + ix * step, 2), round(ctr[1] + iy * step, 2)
                if ou < region[0] or ou > region[2] or ov < region[1] or ov > region[3]:
                    continue
                for rot in (0, 90, 180, 270):
                    c = cost(ou, ov, rot)
                    if maxcost is None or c < maxcost:
                        out.append((c, ou, ov, rot))
        out.sort()
        return out

    def commit(r, ou, ov, rot, cr, pbs):
        p0 = placed[r]
        p0['u'], p0['v'], p0['rot'] = ou, ov, rot
        p0['rect'], _ = rect_at(r, ou, ov, rot, 'o')
        add(cr, ('C', cr, r, 'pas', is0402(r)))
        for pb in pbs:
            add(pb[:4], ('P', pb[:4], r))
            if pb[4] and pb[4] != 'GND':
                dyn[pb[4]].append((r, pb[5], pb[6]))
        gone.discard(r)

    def uncommit(r):
        drop(r)
        for n in list(dyn):
            dyn[n] = [x for x in dyn[n] if x[0] != r]
        gone.add(r)

    def search(r, mc=None):
        """best legal placement of r now: (cost, ou, ov, rot, cr, pbs, grown) or None"""
        m = model(r)
        if m is None:
            return None
        cost, ctr = m
        for margin in (0.3, 2.0):
            region = cell_grow(info[r]['cell'], margin)
            for rad, step in ((3.0, 0.1), (6.0, 0.2), (11.0, 0.3)):
                for c, ou, ov, rot in cands_for(r, cost, ctr, region, rad, step, mc):
                    res = legal(r, ou, ov, rot, region)
                    if res:
                        return (c, ou, ov, rot, res[0], res[1], margin > 0.3)
        return None

    failed, grown = [], []
    deferred = []
    queue = list(order)
    for r in order:
        gone.add(r)
    while queue:
        r = queue.pop(0)
        res = search(r)
        if res is None:
            if model(r) is None and r not in deferred:
                deferred.append(r); queue.append(r)
                continue
            failed.append(r)
            o = info[r]['orig']
            placed[r]['u'], placed[r]['v'], placed[r]['rot'] = o
            commit(r, o[0], o[1], o[2], trect(r, *o), pboxes(r, *o))
            continue
        c, ou, ov, rot, cr, pbs, gr = res
        if gr:
            grown.append(r)
        commit(r, ou, ov, rot, cr, pbs)

    # ---- eviction pass: critical caps still far from their pin push lower-priority passives aside
    moved = 0
    for rnd in range(2):
        far = []
        for r in order:
            if tier_of(r) > 1 or r in failed or r in evictable:
                continue
            m = model(r)
            if m is None:
                continue
            d = m[0](placed[r]['u'], placed[r]['v'], placed[r]['rot'], False)
            if d > 1.9:
                far.append((d, r))
        far.sort(reverse=True)
        for d0, r in far:
            m = model(r)
            cost, ctr = m
            region = cell_grow(info[r]['cell'], 0.3)
            cur = (placed[r]['u'], placed[r]['v'], placed[r]['rot'])
            uncommit(r)
            done = False
            tried = 0
            for c, ou, ov, rot in cands_for(r, cost, ctr, region, 3.0, 0.1, d0 - 0.25):
                bl = set()
                res = legal(r, ou, ov, rot, region, bl)
                if not res:
                    continue
                if not bl:
                    commit(r, ou, ov, rot, *res)
                    done = True
                    break
                if len(bl) > 3 or tried > 60:
                    continue
                tried += 1
                saved = {b: (placed[b]['u'], placed[b]['v'], placed[b]['rot']) for b in bl}
                for b in bl:
                    uncommit(b)
                commit(r, ou, ov, rot, *res)
                ok = True
                new = {}
                for b in sorted(bl, key=prio):
                    sb = search(b)
                    if sb is None or sb[6]:
                        ok = False
                        break
                    commit(b, sb[1], sb[2], sb[3], sb[4], sb[5])
                    new[b] = sb
                if ok:
                    done = True
                    moved += len(bl)
                    break
                for b in new:
                    uncommit(b)
                uncommit(r)
                for b, o in saved.items():
                    commit(b, o[0], o[1], o[2], trect(b, *o), pboxes(b, *o))
            if not done:
                commit(r, cur[0], cur[1], cur[2], trect(r, *cur), pboxes(r, *cur))

    # ---- labels: F.Fab for 0402; others try a silk slot
    for r in lifted:
        p0 = placed[r]
        cr = trect(r, p0['u'], p0['v'], p0['rot'])
        cn = info[r]['cell']
        p0['txt'], p0['slot'], p0['fab'] = None, None, True
        if is0402(r):
            continue
        for k, tr in txt_slots(r, cr, 'RLBTrl'):
            if tr[0] < UL + 0.8 or tr[2] > UR - 0.8 or tr[1] < VF + 0.8 or tr[3] > VR - 0.8:
                continue
            cb = cellrect[cn]
            if tr[0] < cb[0] + 0.1 or tr[2] > cb[2] - 0.1 or tr[1] < cb[1] + 0.1 or tr[3] > cb[3] - 0.1:
                continue
            ok = not any(inter(tr, kk, 0.3) for kk in kobs)
            if ok:
                for it in near(tr, 0.4):
                    if it[2] == r:
                        continue
                    if it[0] in ('C', 'P') and inter(tr, it[1], 0.35 if it[0] == 'C' else 0.15):
                        ok = False; break
                    if it[0] == 'T' and inter(tr, it[1], 0.15):
                        ok = False; break
            if ok:
                p0['txt'], p0['slot'], p0['fab'] = tr, k, False
                add(tr, ('T', tr, r))
                break
    print('SNAP lifted %d failed %s grown(>0.3 mm outside cell) %s evicted-moves %d in %.0fs' % (len(lifted), failed, grown, moved, time.time() - T0), flush=True)
