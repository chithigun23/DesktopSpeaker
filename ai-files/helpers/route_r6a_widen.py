"""flatpak: route_r6a_widen.py IN OUT : widen power-class tracks below their DRC floor (outside neck areas) when legal; report the rest"""
import sys, json
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b = pcbnew.LoadBoard(sys.argv[1])
FLOOR = {'POWER_HI': 0.5, 'PVDD': 0.5, 'SPK_OUT': 0.5, 'SWITCH': 0.4, 'PWR_5V': 0.4, 'PWR_3V': 0.3}
necks = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('NECK_')]
cys = {}
def in_neck(t):
    sh = t.GetEffectiveShape()
    for z in necks:
        if z.Outline().Collide(sh): return True
    return False
done, left = 0, []
for t in list(b.Tracks()):
    if t.GetClass() == 'PCB_VIA': continue
    n = str(t.GetNetname()); fl = FLOOR.get(ncls(n))
    if fl is None or t.GetWidth() >= fl * MM - 1000 or in_neck(t): continue
    a = (t.GetStart().x / MM, t.GetStart().y / MM); c = (t.GetEnd().x / MM, t.GetEnd().y / MM)
    lay = {pcbnew.F_Cu: 'F', pcbnew.B_Cu: 'B', pcbnew.In2_Cu: '2'}[t.GetLayer()]
    w0 = t.GetWidth(); b.Remove(t)
    ok = False
    for w in (fl + 0.2, fl + 0.1, fl):
        if track_legal(b, n, a, c, w, lay):
            t.SetWidth(int(round(w * MM))); ok = True; break
    b.Add(t)
    if ok: done += 1
    else: left.append((n, round(a[0], 2), round(a[1], 2), round(c[0], 2), round(c[1], 2), w0 / MM))
refill(b); pcbnew.SaveBoard(sys.argv[2], b)
print('widened', done, 'left', len(left)); [print(' ', x) for x in left]
