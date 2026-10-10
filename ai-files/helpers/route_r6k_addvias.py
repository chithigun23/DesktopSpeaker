"""flatpak: route_r6k_addvias.py IN OUT PLAN.json : add vias greedily at legal grid points.
PLAN: list of {"net":N, "zones":[F zone names the via must sit in (fill, with ring margin)] or [], "box":[x0,y0,x1,y1],
 "n":max, "d":0.8, "drill":0.4, "alt":[0.6,0.3] (fallback size), "near":[x,y] (prefer points close to it), "in2":"own"|"none"|"any",
 "step":0.1, "pitch":min centre spacing to same-net vias (default d+0.1), "extra":extra clearance (default 0.05)}
in2 "own": the via must sit inside an own-net In2 island outline (ring + 0.3 inside); "none": outside every non-GND In2 island
(ring + 0.5); "any": no In2 test. The via centre is never inside a pad and the ring never overlaps a pad (no via-in-pad).
Legality: route_r6a_lib.place_via (R6a clearances without neck relaxation, conservative). Prints the placed vias."""
import sys, json, math
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import pcbnew
from route_r6a_lib import place_via, full, refill, V
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
out = []
for s in json.load(open(sys.argv[3])):
    n = full(s['net'], b); x0, y0, x1, y1 = s['box']; st = s.get('step', 0.1); placed = 0
    fills = [z.GetFilledPolysList(pcbnew.F_Cu) for z in b.Zones() if not z.GetIsRuleArea() and z.GetZoneName() in s.get('zones', []) and z.HasFilledPolysForLayer(pcbnew.F_Cu)]
    own2 = [z.Outline() for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu) and str(z.GetNetname()) == n]
    oth2 = [z.Outline() for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.In2_Cu) and str(z.GetNetname()) not in (n, 'GND', '')]
    pads = [p for f in b.GetFootprints() for p in f.Pads() if p.IsOnLayer(pcbnew.F_Cu)]
    cands = []
    y = y0
    while y <= y1 + 1e-9:
        x = x0
        while x <= x1 + 1e-9:
            cands.append((round(x, 3), round(y, 3))); x += st
        y += st
    if 'near' in s: cands.sort(key=lambda p: math.hypot(p[0] - s['near'][0], p[1] - s['near'][1]))
    sizes = [(s.get('d', 0.8), s.get('drill', 0.4))] + ([tuple(s['alt'])] if 'alt' in s else [])
    for (x, yy) in cands:
        if placed >= s.get('n', 99): break
        if 'maxdist' in s and 'near' in s and math.hypot(x - s['near'][0], yy - s['near'][1]) > s['maxdist'] - 0.0: continue
        for d, dr in sizes:
            r = d / 2; P = V(x, yy)
            if fills and not any(f.Contains(P) and all(f.Contains(V(x + r * 0.9 * math.cos(a / 8 * math.pi), yy + r * 0.9 * math.sin(a / 8 * math.pi))) for a in range(16)) for f in fills): continue
            mode = s.get('in2', 'own')
            if mode == 'own' and not any(o.Contains(P) and all(o.Contains(V(x + (r + 0.3) * math.cos(a / 8 * math.pi), yy + (r + 0.3) * math.sin(a / 8 * math.pi))) for a in range(16)) for o in own2): continue
            if mode in ('own', 'none') and any(o.Collide(P, int((r + 0.5) * MM)) for o in oth2): continue
            if any(p.GetEffectivePolygon(pcbnew.F_Cu).Collide(P, int((r + 0.02) * MM)) for p in pads if abs(p.GetX() / MM - x) < 4 and abs(p.GetY() / MM - yy) < 4): continue
            pit = s.get('pitch', d + 0.1)
            if any(t.GetClass() == 'PCB_VIA' and str(t.GetNetname()) == n and math.hypot(t.GetX() / MM - x, t.GetY() / MM - yy) < pit for t in b.GetTracks()): continue
            v = place_via(b, n, x, yy, d, dr, lock=False, extra=s.get('extra', 0.05))
            if v is not None:
                placed += 1; out.append((n, x, yy, d, dr)); print('via', n, x, yy, d, dr); break
    print('placed', n, placed, 'of', s.get('n'))
refill(b); pcbnew.SaveBoard(sys.argv[2], b)
json.dump(out, open(sys.argv[2].replace('.kicad_pcb', '.addvias.json'), 'w'))
