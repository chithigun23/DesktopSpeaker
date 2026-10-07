"""flatpak: route_p2_open2.py BOARD OUT.json [all] : fragment-aware open edges (zone fill outlines are separate nodes) for the 5 target classes (or all nets)"""
import sys, json, fnmatch
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import pcbnew
from route_p2_core import comps_of
class C: pass
c = C(); c.b = pcbnew.LoadBoard(sys.argv[1])
pro = json.load(open(sys.argv[1].replace('.kicad_pcb', '.kicad_pro'))); pats = pro['net_settings']['netclass_patterns']
def cl(n):
    for p in pats:
        if fnmatch.fnmatchcase(n, p['pattern']): return p['netclass']
    return 'SIGNAL'
nets = sorted(set(str(t.GetNetname()) for t in c.b.Tracks()) | set(str(p.GetNetname()) for f in c.b.GetFootprints() for p in f.Pads()) | set(str(z.GetNetname()) for z in c.b.Zones() if not z.GetIsRuleArea()))
out = {}
for n in nets:
    if n == '' or n.startswith('unconnected-'): continue
    if len(sys.argv) < 4 and cl(n) not in ('SWITCH', 'POWER_HI', 'PVDD', 'SPK_OUT', 'BOOT'): continue
    k = len(comps_of(c, n)) - 1
    if k > 0: out[n] = k
json.dump(out, open(sys.argv[2], 'w')); print('open2', len(out), sum(out.values()), out)
