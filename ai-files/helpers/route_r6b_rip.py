"""flatpak: route_r6b_rip.py IN OUT NETS(comma)|@DRC.json : remove all unlocked tracks/vias of the nets (or of every non-power
net with an item in a clearance/shorting/track_width/hole/dangling DRC violation)."""
import sys, json, re
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b = pcbnew.LoadBoard(sys.argv[1]); a = sys.argv[3]
POW = ('POWER_HI', 'PVDD', 'SPK_OUT', 'SWITCH', 'BOOT', 'PWR_5V', 'PWR_3V')
if a.startswith('@'):
    d = json.load(open(a[1:])); nets = set()
    for v in d['violations']:
        if v['type'] not in ('clearance', 'shorting_items', 'track_width', 'hole_clearance', 'track_dangling', 'via_dangling', 'items_not_allowed', 'copper_edge_clearance', 'hole_to_hole'): continue
        for it in v['items']:
            m = re.search(r'\[(.*?)\]', it['description'])
            if m and ncls(m.group(1)) not in POW and m.group(1) != 'GND': nets.add(m.group(1))
else: nets = set(full(n, b) for n in a.split(','))
k = 0
for t in list(b.Tracks()):
    if str(t.GetNetname()) in nets and not t.IsLocked(): b.Remove(t); k += 1
refill(b); pcbnew.SaveBoard(sys.argv[2], b); print('ripped', k, 'items of', sorted(nets))
