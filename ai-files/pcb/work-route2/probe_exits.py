"""probe_exits.py GEO.json BOARD_STEM PAD[,PAD..] : the router's own exit model (route_oct.Router.exits, default options) for named
pads, with the blocking item of every rejected direction/variant. Read-only use of helpers/route_oct.py (imported, not changed)."""
import sys, re, json, argparse
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import route_oct as RO
from shapely.geometry import LineString
src = open(RO.__file__).read().split('\n')
i0 = next(i for i, L in enumerate(src) if L.strip() == 'ap = argparse.ArgumentParser()')
i1 = next(i for i, L in enumerate(src) if L.strip() == 'a = ap.parse_args()')
ns = {'argparse': argparse}
exec('\n'.join(L[4:] for L in src[i0:i1]), ns)
geo, stem, pads = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
a = ns['ap'].parse_args(['--board', stem + '.kicad_pcb', '--geo', geo, '--nets', 'hard-nets.txt', '--stage', 'S3', '--out', '/dev/null', '--manifest', '/dev/null',
                         '--via-cost', '1.5', '--pair-avoid', '1', '--hweight', '1', '--max-exp', '3e7'])
a.margins = [float(x) for x in a.margins.split(',')]
core = RO.load_core('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route2')
RO.HALO[0] = a.halo
stages, opts = RO.read_nets('hard-nets.txt')
B = RO.Board(geo, stem + '.kicad_dru', stem + '.kicad_pro', core, a)
R = RO.Router(B, a, opts)
for key in pads:
    ref, num = key.rsplit('-', 1)
    P = next((p for p in B.pads if p['ref'] == ref and p['num'] == num), None)
    if P is None:
        print(key, 'pad not found'); continue
    pf = R.prof(P['net'])
    R.off = (int(round(P['x'] * 1e6)) % RO.GN, int(round(P['y'] * 1e6)) % RO.GN)
    ex = R.exits(P, pf)
    why = []
    for l in [l for l in RO.RL if l in P['poly'] and (l == 'F.Cu' or pf['bcu'] != 'no')]:
        dirs, ext, bd = R.pad_dirs(P, l)
        for d in dirs:
            F0 = int(round((ext[d] + 0.3) * 1e6))
            for var in ('A', 'B+', 'B-'):
                e = R._mk_exit((int(round(P['x'] * 1e6)), int(round(P['y'] * 1e6))), d, F0, var, pf)
                if e is None:
                    why.append('%s d%d %s: no stub geometry' % (l[0], d, var)); continue
                pts = [(x / 1e6, y / 1e6) for x, y in e['pts']]
                ok, it = R.seg_ok(pts, pf['w'], l, pf, mode='contains')
                okn, itn = R.seg_ok(pts, RO.RU.NECK_W, l, pf, mode='contains')
                if not ok:
                    def nm(it):
                        return it if isinstance(it, str) else '%s %s %s' % (it.kind, it.net, it.owner if it.owner else '')
                    why.append('%s d%d %s: %s%s' % (l[0], d, var, nm(it), '' if okn else ' (neck: %s)' % nm(itn)))
    print('%-8s %-28s exits %d  %s' % (key, P['net'], len(ex), '; '.join(why[:6]) if not ex else ''))
