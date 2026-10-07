#!/usr/bin/env python3
"""flatpak pcb: route_p1_open.py BOARD OUT.json : {net: components-1} own union-find connectivity (DRC json is capped at 499 items).
Items: pads, tracks, vias, same-net filled zones (a pad/track/via connects to a zone if its position hits the filled area on that layer)."""
import sys, json, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); out = {}
LAY = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
byn = collections.defaultdict(list)   # net -> list of (kind, obj, layers)
for f in b.GetFootprints():
    for p in f.Pads():
        n = p.GetNetname()
        if n: byn[n].append(('pad', p, [l for l in LAY if p.IsOnLayer(l)]))
for t in b.Tracks():
    n = t.GetNetname()
    if not n: continue
    if t.GetClass() == 'PCB_VIA': byn[n].append(('via', t, LAY))
    else: byn[n].append(('trk', t, [t.GetLayer()]))
zones = collections.defaultdict(list)
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname() == '': continue
    zones[z.GetNetname()].append(z)
def shape(it, ly):
    k, o, _ = it
    if k == 'pad': return o.GetEffectiveShape(ly)
    return o.GetEffectiveShape()
for n, its in byn.items():
    N = len(its) + sum(len(zones[n]) * len(LAY) for _ in [0])
    par = list(range(len(its) + len(zones[n]) * len(LAY)))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    def uni(a, c): par[find(a)] = find(c)
    for i in range(len(its)):
        for j in range(i + 1, len(its)):
            la = set(its[i][2]) & set(its[j][2])
            if not la: continue
            if its[i][0] == 'pad' and its[j][0] == 'pad': continue
            for ly in la:
                try:
                    if shape(its[i], ly).Collide(shape(its[j], ly), 0): uni(i, j); break
                except Exception: pass
    for zi, z in enumerate(zones[n]):
        for li, ly in enumerate(LAY):
            if not z.IsOnLayer(ly) or z.GetFilledPolysList(ly).OutlineCount() == 0: continue
            zn = len(its) + zi * len(LAY) + li
            for i, it in enumerate(its):
                if ly not in it[2]: continue
                pos = it[1].GetPosition() if it[0] != 'trk' else None
                if it[0] == 'trk':
                    if z.HitTestFilledArea(ly, it[1].GetStart()) or z.HitTestFilledArea(ly, it[1].GetEnd()): uni(i, zn)
                elif z.HitTestFilledArea(ly, pos): uni(i, zn)
    # components that contain at least one pad
    roots = set(); padroots = set()
    for i, it in enumerate(its):
        if it[0] == 'pad': padroots.add(find(i))
    if len(padroots) > 1: out[n] = len(padroots) - 1
json.dump(out, open(sys.argv[2], 'w'))
print('open', len(out), sum(out.values()))
