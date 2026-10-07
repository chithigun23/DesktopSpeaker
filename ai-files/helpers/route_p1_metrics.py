#!/usr/bin/env python3
"""flatpak pcbnew: route_p1_metrics.py BOARD OUT.json"""
import sys, json, collections, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); M = 1e6
CL = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-p1/net-classes-p1.json'))
FLOOR = {'POWER_HI': .5, 'PVDD': .5, 'SPK_OUT': .5, 'PWR_5V': .4, 'SWITCH': .4, 'AUDIO': .25, 'I2S_CLK': .25, 'USB': .25}
bylayer = collections.Counter(); vias = collections.Counter(); length = collections.Counter(); below = collections.defaultdict(list)
wh = collections.defaultdict(collections.Counter); nvia = collections.Counter()
ka = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'BM83_ANTENNA_KEEPOUT'][0].GetBoundingBox()
ant = 0
for t in b.Tracks():
    n = t.GetNetname(); c = CL.get(n, '?')
    if t.GetClass() == 'PCB_VIA':
        vias['%.2f/%.2f' % (t.GetWidth(pcbnew.F_Cu) / M, t.GetDrill() / M)] += 1; nvia[n] += 1
        if ka.Contains(t.GetPosition()): ant += 1
        continue
    bylayer[b.GetLayerName(t.GetLayer())] += 1
    L = t.GetLength() / M; length[n] += L
    w = t.GetWidth() / M; wh[c][round(w, 3)] += 1
    if c in FLOOR and w < FLOOR[c] - 1e-6 and n != 'GND': below[c].append((n, round(w, 3), round(L, 2)))
    if ka.Intersects(t.GetBoundingBox()): ant += 1
key = {n: round(length[n], 2) for n in ('/I2S_BCK', '/I2S_LRCK', '/I2S_SDATA', '/USB_DP', '/USB_DN', 'Net-(U2-D+)', 'Net-(U2-D-)') if n in length}
out = {'tracks_by_layer': dict(bylayer), 'vias': dict(vias), 'via_total': sum(vias.values()), 'gnd_vias': nvia.get('GND', 0), 'antenna_keepout_hits': ant, 'key_lengths_mm': key,
       'width_hist': {c: {str(k): v for k, v in h.items()} for c, h in wh.items()}, 'below_floor_counts': {c: len(v) for c, v in below.items()}, 'below_floor_nets': {c: sorted(set(x[0] for x in v)) for c, v in below.items()}}
json.dump(out, open(sys.argv[2], 'w'), indent=1); print(json.dumps({k: out[k] for k in ('tracks_by_layer', 'vias', 'via_total', 'gnd_vias', 'antenna_keepout_hits', 'key_lengths_mm', 'below_floor_counts')}))
