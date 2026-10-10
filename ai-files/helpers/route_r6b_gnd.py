"""flatpak: route_r6b_gnd.py IN OUT [maxr] : attach isolated GND copper groups (pads without a plane connection) to In1.
Per group, per SMD pad: (a) a legal F.Cu track to an existing GND via within 1.5 mm, else (b) a dogbone via beside the pad
(via copper >= 0.15 mm from the pad edge, never in a pad, never inside a non-GND In2 island, 0.5/0.2 only in NECK_* areas).
New items unlocked. Writes OUT.gnd.json with the failures."""
import sys, json, math
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
from route_r6a_lib import *
from route_p2_core import comps_of
b = pcbnew.LoadBoard(sys.argv[1]); maxr = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5
class C: pass
cx = C(); cx.b = b
isl = []; neck = []; bko = []
for z in b.Zones():
    if z.GetIsRuleArea():
        if z.GetZoneName().startswith('NECK_'): neck.append(z.Outline())
        continue
    if z.IsOnLayer(pcbnew.In2_Cu) and str(z.GetNetname()) not in ('GND', '') and z.HasFilledPolysForLayer(pcbnew.In2_Cu):
        fp_ = z.GetFilledPolysList(pcbnew.In2_Cu)
        for i in range(fp_.OutlineCount()):
            ps = pcbnew.SHAPE_POLY_SET(); ps.AddOutline(fp_.Outline(i)); isl.append(ps)
def in_island(x, y, r):
    return any(ps.Collide(V(x, y), int((r + 0.3) * MM)) for ps in isl)
def in_neck(x, y): return any(o.Contains(V(x, y)) for o in neck)
def pad_clear(x, y, r):
    """distance between circle (x,y,r) and the nearest SMD/any pad copper on F.Cu (any net)"""
    best = 9
    for f in b.GetFootprints():
        fb = f.GetBoundingBox(); fb.Inflate(int(2 * MM))
        if not fb.Contains(V(x, y)): continue
        for p in f.Pads():
            if not p.IsOnLayer(pcbnew.F_Cu): continue
            d = p.GetEffectiveShape(pcbnew.F_Cu).Collide(pcbnew.SHAPE_CIRCLE(V(x, y), int(r * MM)), int(0.15 * MM))
            if d: return 0
    return best
def gnd_vias():
    return [t for t in b.Tracks() if t.GetClass() == 'PCB_VIA' and str(t.GetNetname()) == 'GND']
EP = {('U6', '33'), ('U7', '33'), ('U25', '21')}
def main_group(comps):
    for i, g in enumerate(comps):
        if any(x[0] == 'zone' and x[2] == pcbnew.In1_Cu for x in g): return i
    return 0
comps = comps_of(cx, 'GND'); mi = main_group(comps)
print('GND groups', len(comps))
ok, fail = [], []
for gi, g in enumerate(comps):
    if gi == mi: continue
    pads = [x[1] for x in g if x[0] == 'pad' and x[1].IsOnLayer(pcbnew.F_Cu)]
    if any(x[0] == 'via' for x in g): pass   # has a via but not tied to In1 (should not happen): still try
    done = False
    for p in pads:
        px, py = p.GetX() / MM, p.GetY() / MM
        # (a) existing via
        for v in sorted(gnd_vias(), key=lambda v: math.hypot(v.GetX() / MM - px, v.GetY() / MM - py)):
            d = math.hypot(v.GetX() / MM - px, v.GetY() / MM - py)
            if d > 1.5: break
            for w in (0.3, 0.25, 0.2):
                if track_legal(b, 'GND', (px, py), (v.GetX() / MM, v.GetY() / MM), w):
                    trk(b, 'GND', 'F', [(px, py), (v.GetX() / MM, v.GetY() / MM)], w, lock=False); done = True; break
            if done: break
        if done: ok.append((p.GetParentFootprint().GetReference(), str(p.GetNumber()), 'track')); break
        # (b) dogbone via
        bb = p.GetBoundingBox(); hw = max(bb.GetWidth(), bb.GetHeight()) / MM / 2
        cands = []
        for k in range(32):
            a = 2 * math.pi * k / 32
            for r in [hw + 0.3 + 0.05 * j for j in range(int((maxr - hw) / 0.05))]:
                cands.append((r, a))
        cands.sort()
        for r, a in cands:
            x, y = px + r * math.cos(a), py + r * math.sin(a)
            fine = in_neck(x, y)
            for d, dr in ((0.6, 0.3), (0.5, 0.2)) if fine else ((0.6, 0.3),):
                if pad_clear(x, y, d / 2) == 0: continue
                if in_island(x, y, d / 2): continue
                w_ok = None
                for w in (0.3, 0.25, 0.2):
                    if track_legal(b, 'GND', (px, py), (x, y), w): w_ok = w; break
                if w_ok is None: continue
                v = place_via(b, 'GND', x, y, d, dr, lock=False)
                if v is None: continue
                trk(b, 'GND', 'F', [(px, py), (x, y)], w_ok, lock=False); done = True; break
            if done: break
        if done: ok.append((p.GetParentFootprint().GetReference(), str(p.GetNumber()), 'via')); break
    if not done: fail.append([(p.GetParentFootprint().GetReference(), str(p.GetNumber()), round(p.GetX() / MM, 2), round(p.GetY() / MM, 2)) for p in pads])
refill(b); pcbnew.SaveBoard(sys.argv[2], b)
json.dump({'ok': ok, 'fail': fail}, open(sys.argv[2].replace('.kicad_pcb', '.gnd.json'), 'w'), indent=0)
print('attached', len(ok), 'failed', len(fail)); [print(' FAIL', f) for f in fail]
