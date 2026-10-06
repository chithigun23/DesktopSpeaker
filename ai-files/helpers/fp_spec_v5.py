"""Pick the smallest floorplan-v5-raw*.json and write floorplan-v5.json (edge flush specs, title, titles at the bottom of rear-edge tiles)."""
import json, glob
ROOT = '/home/chithi/Desktop/DesktopSpeaker/ai-files/'
raws = [json.load(open(f)) for f in glob.glob(ROOT + 'pcb/floorplan-v5-raw*.json')]
r = min(raws, key=lambda q: q['H'])
sizes = json.load(open(ROOT + 'pcb/cells-v5.json'))['sizes']
MG, MT = 0.5, 1.9
sizes['BM83'][0] -= 8
rects = []
for n, (x, y) in r['abs'].items():
    rects.append((x, y, x + sizes[n][0] + 2 * MG + 0.1, y + sizes[n][1] + MG + MT + 0.1) if n in sizes else (x, y, x + 8, y + 8))
W, H = r['W'], r['H']
best = None
for yy in range(int(H) - 5, 5, -1):
    for xx in range(int(W) - 22, 1, -1):
        c = (xx, yy, xx + 20, yy + 3.5)
        if not any(c[0] < q[2] and c[2] > q[0] and c[1] < q[3] and c[3] > q[1] for q in rects):
            d = (H - yy) + (W - xx)
            if best is None or d < best[0]: best = (d, xx, yy)
ul = -61.0
title = [ul + best[1] + 10, -(best[2] + 1.75)] if best else [ul + 20, -H + 5]
spec = dict(W=W, H=H, ul=ul, abs=r['abs'], ovh={'BM83': 8.0}, title_bottom=['WAKE', 'JACKS', 'PDIN'],
            edge={'BM83': {'left': ['U1', 8.0]}, 'JACKS': {'rear': ['J2', -0.30]}, 'PDIN': {'rear': ['J1', 1.25]}, 'WAKE': {'rear': ['SW100', 0.0]},
                  'AMP6': {'front': ['J9', -0.4]}, 'AMP7': {'front': ['J11', -0.4]}, 'BATIO': {'right': ['J5', 0.0]}}, title=title)
json.dump(spec, open(ROOT + 'pcb/floorplan-v5.json', 'w'), indent=1)
print('spec W %.1f H %.1f area %.0f title %s' % (W, H, W * H, title))
