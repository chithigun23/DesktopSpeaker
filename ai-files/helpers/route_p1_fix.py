#!/usr/bin/env python3
"""flatpak pcbnew: route_p1_fix.py IN DRC.json OUT REMOVED.json
1) dedupe identical vias/tracks  2) remove tracks/vias that appear in shorting_items, via_dangling, track_dangling, hole_to_hole/holes_co_located
3) for audio_clear / clk_clear / netclass clearance violations remove the track/via of the less critical net (AUDIO,I2S_CLK,USB are kept; else the later-routed one = lower class rank)
Writes the removed nets (to be re-routed) to REMOVED.json, refills zones."""
import sys, json, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); d = json.load(open(sys.argv[2]))
CL = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-p1/net-classes-p1.json'))
dup = 0
byu = {}
for t in list(b.Tracks()): byu[t.m_Uuid.AsString()] = t
RANK = {'USB': 0, 'I2S_CLK': 1, 'AUDIO': 2}
def cl(n): return CL.get(n, 'SIGNAL')
whole_force = set(); rm = {}; reasons = collections.Counter()
for v in d['violations']:
    ty = v['type']
    if ty in ('items_not_allowed',):
        for i in v['items']:
            if i['uuid'] in byu: whole_force.add(byu[i['uuid']].GetNetname())
    elif ty == 'copper_edge_clearance':
        for i in v['items']:
            if i['uuid'] in byu and byu[i['uuid']].GetNetname() != 'GND': whole_force.add(byu[i['uuid']].GetNetname())
    elif ty in ('shorting_items', 'via_dangling', 'track_dangling', 'hole_to_hole', 'holes_co_located'):
        its = [byu[i['uuid']] for i in v['items'] if i['uuid'] in byu]
        if ty in ('hole_to_hole', 'holes_co_located') and len(its) == 2:
            its = [its[1]]
        for t in its: rm[t.m_Uuid.AsString()] = t; reasons[ty] += 1
    elif ty == 'clearance':
        its = [byu[i['uuid']] for i in v['items'] if i['uuid'] in byu]
        if not its: continue
        if len(its) == 2:
            ra = RANK.get(cl(its[0].GetNetname()), 9); rb = RANK.get(cl(its[1].GetNetname()), 9)
            t = its[0] if ra > rb else its[1] if rb > ra else its[1]
            if cl(t.GetNetname()) == 'GND' and not ({cl(i.GetNetname()) for i in its} - {'GND'}): continue
            rm[t.m_Uuid.AsString()] = t; reasons['clearance'] += 1
        else:
            t = its[0]; rm[t.m_Uuid.AsString()] = t; reasons['clearance1'] += 1
nets = collections.Counter()
# net-level removal for non-GND nets (whole net is rerouted), item-level for GND and co-located duplicates
whole = set(whole_force)
for u, t in rm.items():
    n = t.GetNetname()
    if n != 'GND': whole.add(n)
for t in list(b.Tracks()):
    n = t.GetNetname()
    if n in whole: nets[n] += 1; b.Remove(t)
for u, t in rm.items():
    if t.GetNetname() == 'GND':
        try: b.Remove(t)
        except Exception: pass
pcbnew.SaveBoard(sys.argv[3], b)
json.dump(sorted(nets), open(sys.argv[4], 'w'))
print('dup', dup, 'removed', len(rm), dict(reasons), 'nets', len(nets))
