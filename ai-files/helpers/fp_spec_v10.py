"""python3 fp_spec_v8.py raw.json -> pcb/floorplan-v10.json (edge flush specs, board title in the biggest free void, titles at the bottom of rear-edge tiles)."""
import json, sys
ROOT = '/home/chithi/Desktop/DesktopSpeaker/ai-files/'
r = json.load(open(sys.argv[1]))
sizes = json.load(open(ROOT + 'pcb/work-v10/cells-v10.json'))['sizes']
MG, MT, HOLE = 0.5, 2.3, 7.8
sizes['BM83'][0] -= 8
rects = [(x, y, x + sizes[n][0] + 2 * MG, y + sizes[n][1] + MG + MT) if n in sizes else (x, y, x + HOLE, y + HOLE) for n, (x, y) in r['abs'].items()]
W, H = r['W'], r['H']
best = None
for tw in (20, 17, 14, 11):
    for yy in [i * 0.5 for i in range(int(H * 2) - 7)]:
        for xx in [i * 0.5 for i in range(int((W - tw) * 2))]:
            c = (xx, yy, xx + tw, yy + 3.5)
            if not any(c[0] < q[2] - 1e-6 and c[2] > q[0] + 1e-6 and c[1] < q[3] - 1e-6 and c[3] > q[1] + 1e-6 for q in rects):
                d = (H - yy) + (W - xx)
                if best is None or d < best[0]: best = (d, xx, yy, tw)
    if best: break
ul = -61.0
title = [ul + best[1] + best[3] / 2, -(best[2] + 1.75)] if best else [ul + 20, -H + 5]
print('title void', best)
spec = dict(W=W, H=H, ul=ul, abs=r['abs'], ovh={'BM83': 8.0}, title_bottom=['WAKE', 'JACKS', 'PDIN', 'BM83'],
            edge={'BM83': {'left': ['U1', 8.0]}, 'JACKS': {'rear': ['J2', -0.30]}, 'PDIN': {'rear': ['J1', 1.25]}, 'WAKE': {'rear': ['SW100', 0.0]},
                  'AMP6': {'front': ['J9', -0.4]}, 'AMP7': {'front': ['J11', -0.4]}, 'BATIO': {'right': ['J5', 0.0]}}, title=title)
json.dump(spec, open(ROOT + 'pcb/floorplan-v10.json', 'w'), indent=1)
print('spec W %.1f H %.1f area %.0f' % (W, H, W * H))
