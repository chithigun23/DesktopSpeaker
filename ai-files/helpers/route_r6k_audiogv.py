"""flatpak: route_r6k_audiogv.py BOARD [OUT_PLAN.json] : AUDIO / I2S_CLK vias and the distance to the nearest GND via;
with OUT_PLAN writes a route_r6k_addvias.py plan (one GND via within 1.2 mm of each via lacking one)."""
import sys, json, math, fnmatch, pcbnew
MM = 1e6; b = pcbnew.LoadBoard(sys.argv[1])
pats = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/R6k.kicad_pro'))['net_settings']['netclass_patterns']
def cl(n):
    for p in pats:
        if fnmatch.fnmatchcase(n, p['pattern']): return p['netclass']
    return 'Default'
vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
g = [(v.GetX() / MM, v.GetY() / MM) for v in vias if str(v.GetNetname()) == 'GND']
plan = []; nbad = 0; tot = 0
for v in vias:
    n = str(v.GetNetname()); c = cl(n)
    if c not in ('AUDIO', 'I2S_CLK'): continue
    tot += 1; x, y = v.GetX() / MM, v.GetY() / MM
    d = min(math.hypot(x - gx, y - gy) for gx, gy in g)
    if d > 1.2:
        nbad += 1; print('  %s %s (%.2f,%.2f) nearest GND via %.2f mm' % (c, n, x, y, d))
        plan.append({"net": "GND", "zones": [], "box": [x - 1.2, y - 1.2, x + 1.2, y + 1.2], "n": 1, "d": 0.6, "drill": 0.3, "near": [x, y], "in2": "none", "pitch": 0.7, "step": 0.05, "maxdist": 1.2})
print('audio/I2S vias', tot, 'without GND via within 1.2 mm:', nbad)
if len(sys.argv) > 2: json.dump(plan, open(sys.argv[2], 'w'), indent=0)
