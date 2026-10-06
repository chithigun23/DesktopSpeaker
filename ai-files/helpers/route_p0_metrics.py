#!/usr/bin/env python3
"""DRC summary by type, unconnected per netclass, track width audit, via counts.  usage: route_p0_metrics.py DRC.json BOARD OUT.json  (run: host python for DRC part is fine; board part needs flatpak pcbnew)"""
import sys, json, collections, re
drc, brd, out = sys.argv[1:4]
cls = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/net-classes-p0.json'))
MINW = {'POWER_HI':0.5,'PVDD':0.5,'SPK_OUT':0.5,'SWITCH':0.4,'BOOT':0.25,'PWR_5V':0.4,'PWR_3V':0.3,'PWR_LOCAL':0.25,'AUDIO':0.25,'I2S_CLK':0.25,'USB':0.25,'I2C':0.25,'GND':0.4,'SIGNAL':0.2}
d = json.load(open(drc)); res = {}
for k in ('violations', 'unconnected_items', 'schematic_parity'):
    res[k] = dict(collections.Counter(x['type'] for x in d.get(k, [])))
un = collections.Counter(); unnets = collections.Counter()
for u in d['unconnected_items']:
    m = re.search(r'\[([^\]]*)\]', u['items'][0]['description'])
    n = m.group(1) if m else '?'
    un[cls.get(n, 'SIGNAL')] += 1; unnets[n] += 1
res['unconnected_by_class'] = dict(un)
import pcbnew
b = pcbnew.LoadBoard(brd)
M = 1e6
narrow = []; wcount = collections.Counter(); tl = collections.Counter(); lens = collections.Counter(); vias = collections.Counter()
for t in b.GetTracks():
    nm = t.GetNetname()
    if t.GetClass() == 'PCB_VIA':
        vias[(round(t.GetWidth(pcbnew.F_Cu)/M, 2), round(t.GetDrillValue()/M, 2))] += 1; continue
    c = cls.get(nm, 'SIGNAL'); w = t.GetWidth()/M
    tl[(c, b.GetLayerName(t.GetLayer()))] += 1; lens[c] += t.GetLength()/M
    if w + 1e-6 < MINW.get(c, 0.2): narrow.append((nm, c, round(w, 3), b.GetLayerName(t.GetLayer()), round(t.GetStart().x/M, 1), round(t.GetStart().y/M, 1)))
res['tracks_by_class_layer'] = {'%s|%s' % k: v for k, v in tl.items()}
res['track_len_mm_by_class'] = {k: round(v, 1) for k, v in lens.items()}
res['vias_by_size'] = {'%s/%s' % k: v for k, v in vias.items()}
res['narrow_tracks'] = narrow
res['unconnected_nets_top'] = unnets.most_common(15)
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('narrow_tracks',)}, indent=0)[:3000]); print('narrow', len(narrow), narrow[:8])
