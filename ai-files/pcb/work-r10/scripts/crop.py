"""crop.py DUMP.json OUT.png x0 y0 x1 y1 [net-substring ...] : render pads (highlight nets), F.Cu/B.Cu tracks, vias, courtyards, refs"""
import sys, json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Circle
D = json.load(open(sys.argv[1])); out = sys.argv[2]; x0, y0, x1, y1 = map(float, sys.argv[3:7]); hl = sys.argv[7:]
COL = ['red', 'blue', 'green', 'magenta', 'orange', 'cyan', 'brown', 'olive', 'purple', 'teal']
def col(n):
    for i, h in enumerate(hl):
        if h in n: return COL[i % len(COL)]
    return None
S = float(__import__("os").environ.get("CS", "0.9")); fig, ax = plt.subplots(figsize=(max(6, (x1 - x0) * S), max(6, (y1 - y0) * S)))
inb = lambda x, y: x0 - 2 < x < x1 + 2 and y0 - 2 < y < y1 + 2
for t in D['tracks']:
    if not (inb(t['x1'], t['y1']) or inb(t['x2'], t['y2'])): continue
    c = 'darkorange' if t['l'] == 'F.Cu' else ('steelblue' if t['l'] == 'B.Cu' else None)
    if c is None: continue
    ax.plot([t['x1'], t['x2']], [t['y1'], t['y2']], color=c, lw=max(0.5, t['w'] * 20), alpha=0.35, solid_capstyle='round')
for v in D['vias']:
    if inb(v['x'], v['y']): ax.add_patch(Circle((v['x'], v['y']), v['d'] / 2, color='gray', alpha=0.6))
for f in D['fps']:
    if not inb(f['x'], f['y']) or f['side'] != 'F': continue
    for o in f['cy']:
        if len(o) >= 3: ax.add_patch(MP(o, closed=True, fill=False, ec='0.6', lw=0.4))
    for p in f['pads']:
        c = col(p['net']) if p['net'] else None
        if p['poly'] and len(p['poly'][0]) >= 3:
            ax.add_patch(MP(p['poly'][0], closed=True, fc=c or ('0.75' if p['net'] != 'GND' else '0.88'), ec='k', lw=0.2))
        if c: ax.text(p['x'], p['y'], p['net'].split('/')[-1][:8], fontsize=4, ha='center', va='center')
    ax.text(f['x'], f['y'], f['ref'], fontsize=6, color='navy', ha='center', va='bottom')
ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect('equal'); ax.grid(True, lw=0.2)
plt.tight_layout(); plt.savefig(out, dpi=110)
