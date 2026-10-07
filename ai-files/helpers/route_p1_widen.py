#!/usr/bin/env python3
"""flatpak pcbnew: route_p1_widen.py IN OUT REPORT.json
Widen autorouted segments (width < class preferred width) segment by segment where the wider copper still keeps the required clearance
to every other-net track/via/pad (class clearance rules of the plan). Zones are refilled afterwards. Skips GND, POWER_HI, PVDD, SWITCH, SPK_OUT and P0 stubs (width >= 0.3 on those)."""
import sys, json, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); M = 1e6
ns = b.GetDesignSettings().m_NetSettings
def cname(n): return ns.GetEffectiveNetClass(n).GetName().split(',')[0]
def pref(n): return ns.GetEffectiveNetClass(n).GetTrackWidth()
SKIP = {'GND', 'POWER_HI', 'PVDD', 'SWITCH', 'SPK_OUT'}
def need(ca, cb, pad):
    if pad: return 200000
    cl = 200000
    for x, y in ((ca, cb), (cb, ca)):
        if x == 'AUDIO' and y not in ('AUDIO', 'GND'): cl = max(cl, 500000)
        if x == 'I2S_CLK' and y not in ('I2S_CLK', 'GND'): cl = max(cl, 400000)
        if x == 'POWER_HI': cl = max(cl, 400000)
        if x in ('PVDD', 'SPK_OUT'): cl = max(cl, 300000)
        if x == 'SWITCH' and y not in ('SWITCH', 'GND'): cl = max(cl, 1000000)
    return cl
items = []   # (bbox, shape, net, cls, is_pad, layers)
grid = collections.defaultdict(list)
CELL = 2000000
def addgrid(it):
    bb = it[0]
    for gx in range(bb.GetLeft() // CELL - 1, bb.GetRight() // CELL + 2):
        for gy in range(bb.GetTop() // CELL - 1, bb.GetBottom() // CELL + 2): grid[(gx, gy)].append(it)
tracks = list(b.Tracks())
for t in tracks:
    sh = t.GetEffectiveShape()
    it = [t.GetBoundingBox(), sh, t.GetNetname(), cname(t.GetNetname()), False, t, t.GetLayer() if t.GetClass() != 'PCB_VIA' else -1]
    addgrid(it)
for f in b.GetFootprints():
    for p in f.Pads():
        for ly in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not p.IsOnLayer(ly): continue
            it = [p.GetBoundingBox(), p.GetEffectiveShape(ly), p.GetNetname(), cname(p.GetNetname()) if p.GetNetname() else 'SIGNAL', True, p, ly]
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH): it[6] = -1
            addgrid(it)
done = collections.Counter(); wid_before = collections.Counter(); wid_after = collections.Counter(); skipped = 0
for t in tracks:
    if t.GetClass() == 'PCB_VIA': continue
    n = t.GetNetname(); c = cname(n)
    if c in SKIP or not n: continue
    pw = pref(n); w0 = t.GetWidth()
    if pw <= w0 or w0 >= 400000: continue
    ly = t.GetLayer()
    bb = t.GetBoundingBox(); bb.Inflate(1500000)
    near = {}
    for gx in range(bb.GetLeft() // CELL, bb.GetRight() // CELL + 1):
        for gy in range(bb.GetTop() // CELL, bb.GetBottom() // CELL + 1):
            for it in grid.get((gx, gy), []): near[id(it)] = it
    best = w0
    for w in sorted({pw, 300000, 250000}, reverse=True):
        if w <= w0 or w > pw: continue
        t.SetWidth(w); sh = t.GetEffectiveShape(); ok = True
        for it in near.values():
            if it[2] == n or (it[6] != -1 and it[6] != ly) or it[5] is t: continue
            if sh.Collide(it[1], need(c, it[3], it[4])): ok = False; break
        if ok: best = w; break
    t.SetWidth(best)
    if best != w0: done[c] += 1
    wid_before[round(w0 / M, 3)] += 1; wid_after[round(best / M, 3)] += 1
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    if z.GetZoneName().startswith('GND'): z.SetLocalClearance(400000)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
json.dump({'widened_by_class': dict(done), 'before': {str(k): v for k, v in wid_before.items()}, 'after': {str(k): v for k, v in wid_after.items()}}, open(sys.argv[3], 'w'), indent=0)
print('widened', dict(done))
