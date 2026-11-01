"""win.py STEM x0 y0 x1 y1 [--png OUT.png] [--layer F.Cu] : list and render copper in a window (venv python).
Lists pads (ref-num net centre size rot), segments/arcs (uuid8 layer net w ends), vias (uuid8 net at size), zones (uuid8 name net layer outline)
from STEM.kicad_pcb (text) and STEM.geo.json (pads, fills)."""
import sys, json
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pcbtext import items
W = '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route'
st = sys.argv[1]; x0, y0, x1, y1 = map(float, sys.argv[2:6])
args = sys.argv[6:]
png = args[args.index('--png') + 1] if '--png' in args else None
lay = args[args.index('--layer') + 1] if '--layer' in args else 'F.Cu'
G = json.load(open(f'{W}/{st}.geo.json'))
IT = items(f'{W}/{st}.kicad_pcb')
inb = lambda p, m=0: x0 - m <= p[0] <= x1 + m and y0 - m <= p[1] <= y1 + m
print('PADS')
for p in G['pads']:
    if inb((p['x'], p['y']), 0.3):
        print('  %s-%s %s (%.3f, %.3f) %.3fx%.3f r%g %s' % (p['ref'], p['num'], p['net'], p['x'], p['y'], p['sx'], p['sy'], p['rot'], p['cls']))
print('SEGMENTS')
for d in IT:
    if d['kind'] in ('segment', 'arc') and (inb(d['start']) or inb(d['end'])):
        print('  %s %s %s %-28s w%.3f (%.4f, %.4f)-(%.4f, %.4f)' % (d['kind'][0], d['uuid'][:8], d['layer'], d['net'], d['width'], *d['start'], *d['end']))
print('VIAS')
for d in IT:
    if d['kind'] == 'via' and inb(d['at']):
        print('  %s %-28s (%.4f, %.4f) %.2f/%.2f' % (d['uuid'][:8], d['net'], *d['at'], d['size'], d['drill']))
print('ZONES')
for d in IT:
    if d['kind'] == 'zone' and not d.get('teardrop') and d.get('pts') and any(inb(p) for p in d['pts']) or (
            d['kind'] == 'zone' and not d.get('teardrop') and d.get('pts') and
            min(p[0] for p in d['pts']) < x1 and max(p[0] for p in d['pts']) > x0 and min(p[1] for p in d['pts']) < y1 and max(p[1] for p in d['pts']) > y0):
        pts = d['pts']
        print('  %s %-22s %-28s %s n%d %s' % (d.get('uuid', '?')[:8], d.get('name', ''), d.get('net', ''), d.get('layer', d.get('layers')), len(pts),
                                           ' '.join('(%g,%g)' % p for p in pts) if len(pts) <= 24 else '(big)'))
if png:
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP, Circle
    fig, ax = plt.subplots(figsize=(max(6, (x1 - x0) * float(__import__("os").environ.get("WS","1.3"))), max(6, (y1 - y0) * float(__import__("os").environ.get("WS","1.3")))))
    for z in G['zones']:
        if lay not in z['fills']: continue
        for poly in z['fills'][lay]:
            ring = poly[0]
            if any(inb(p, 3) for p in ring) or True:
                c = '#cfe8cf' if z['cls'] == 'GND' else ('#f7d2c4' if not z['teardrop'] else '#eeeeaa')
                ax.add_patch(MP(ring, closed=True, fc=c, ec='none', alpha=0.8))
    for d in IT:
        if d['kind'] in ('segment', 'arc') and d['layer'] == lay and (inb(d['start'], 2) or inb(d['end'], 2)):
            c = 'green' if d['net'] == 'GND' else 'darkorange'
            ax.plot([d['start'][0], d['end'][0]], [d['start'][1], d['end'][1]], color=c, lw=d['width'] * 72 * 1.3 / 25.4 * 25.4 / 1.0 * 0.0 + max(0.6, d['width'] * 37), alpha=0.5, solid_capstyle='round')
            mx, my = (d['start'][0] + d['end'][0]) / 2, (d['start'][1] + d['end'][1]) / 2
            if inb((mx, my)): ax.text(mx, my, d['uuid'][:4], fontsize=4, color='k')
    for d in IT:
        if d['kind'] == 'via' and inb(d['at'], 1):
            ax.add_patch(Circle(d['at'], d['size'] / 2, color='green' if d['net'] == 'GND' else 'gray', alpha=0.7))
            ax.text(d['at'][0], d['at'][1], d['uuid'][:4], fontsize=4, color='w', ha='center', va='center')
    for p in G['pads']:
        if not inb((p['x'], p['y']), 2): continue
        for poly in p['poly'].get(lay, []):
            ax.add_patch(MP(poly[0], closed=True, fc='0.85' if p['net'] == 'GND' else '0.6', ec='k', lw=0.3, alpha=0.9))
        ax.text(p['x'], p['y'], '%s-%s\n%s' % (p['ref'], p['num'], p['net'].split('/')[-1][:10]), fontsize=3.5, ha='center', va='center')
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect('equal'); ax.grid(True, lw=0.2)
    import matplotlib.ticker as T
    ax.xaxis.set_major_locator(T.MultipleLocator(0.5)); ax.yaxis.set_major_locator(T.MultipleLocator(0.5))
    ax.tick_params(labelsize=5)
    plt.tight_layout(); plt.savefig(png, dpi=150)
