"""flatpak: route_r6b_widen.py IN OUT : unlocked AUDIO/I2S_CLK/USB tracks narrower than 0.25 mm that lie fully outside the
NECK_* areas and IC courtyards of the neck rule are widened to 0.25 mm when legal (route_r6a_lib.track_legal).
Unlocked signal tracks (any class except power) are then widened to 0.25 mm where legal (class preference). Report on stdout."""
import sys
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
b = pcbnew.LoadBoard(sys.argv[1])
NECKREF = ['U4', 'U6', 'U7', 'U8', 'U9', 'U11', 'U14', 'U15', 'U19', 'U24', 'U25', 'U3', 'U5', 'U10', 'U20', 'J1']
areas = [z.Outline() for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('NECK_')]
for r in NECKREF:
    f = fp(b, r)
    try:
        c = f.GetCourtyard(pcbnew.F_CrtYd)
        if c.OutlineCount(): areas.append(c)
    except Exception: pass
def in_neck(t):
    sh = t.GetEffectiveShape()
    return any(a.Collide(sh) for a in areas)
POW = ('POWER_HI', 'PVDD', 'SPK_OUT', 'SWITCH', 'BOOT', 'PWR_5V', 'PWR_3V', 'GND')
fixed = bad = 0; badl = []
for t in list(b.Tracks()):
    if t.GetClass() == 'PCB_VIA' or t.IsLocked(): continue
    n = str(t.GetNetname()); c = ncls(n)
    if c in POW: continue
    w = t.GetWidth() / MM
    if w >= 0.25 - 1e-6: continue
    must = c in ('AUDIO', 'I2S_CLK', 'USB') and not in_neck(t)
    lay = {pcbnew.F_Cu: 'F', pcbnew.B_Cu: 'B'}.get(t.GetLayer())
    if lay is None: continue
    a = (t.GetStart().x / MM, t.GetStart().y / MM); e = (t.GetEnd().x / MM, t.GetEnd().y / MM)
    b.Remove(t)
    if track_legal(b, n, a, e, 0.25, lay):
        t.SetWidth(int(0.25 * MM)); fixed += 1
    elif must:
        bad += 1; badl.append((n, round(a[0], 2), round(a[1], 2)))
    b.Add(t)
refill(b); pcbnew.SaveBoard(sys.argv[2], b)
print('widened', fixed, 'still sub-floor outside neck', bad, badl[:30])
