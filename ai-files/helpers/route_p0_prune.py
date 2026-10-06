#!/usr/bin/env python3
"""Remove autorouter-added tracks/vias that appear in DRC clearance/annular/dangling-via violations (items of the P0 base board are kept), refill, save.
usage (flatpak pcbnew): route_p0_prune.py BOARD DRC.json BASE.kicad_pcb OUT.kicad_pcb [CRITICAL_NETS.json]  (critical nets: all non-base items removed)"""
import sys, json, pcbnew
brd, drc, basep, out = sys.argv[1:5]
b = pcbnew.LoadBoard(brd); base = pcbnew.LoadBoard(basep)
def key(t):
    if t.GetClass() == 'PCB_VIA':
        p = t.GetPosition(); return ('v', t.GetNetname(), round(p.x/1e4), round(p.y/1e4))
    a, c = t.GetStart(), t.GetEnd()
    k = sorted([(round(a.x/1e4), round(a.y/1e4)), (round(c.x/1e4), round(c.y/1e4))])
    return ('t', t.GetNetname(), tuple(k[0]), tuple(k[1]))
keep = set(key(t) for t in base.Tracks())
bad = set()
d = json.load(open(drc))
for v in d['violations']:
    if v['type'] in ('clearance', 'annular_width', 'via_dangling', 'hole_to_hole', 'shorting_items', 'track_dangling', 'hole_clearance'):
        for i in v['items']: bad.add(i['uuid'])
crit = set(json.load(open(sys.argv[5]))) if len(sys.argv) > 5 else set()
rm = []
for t in list(b.Tracks()):
    if key(t) in keep: continue
    if t.m_Uuid.AsString() in bad or t.GetNetname() in crit: rm.append(t)
for t in rm: b.Remove(t)
print('pruned', len(rm))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(out, b)
