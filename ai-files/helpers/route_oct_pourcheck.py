#!/usr/bin/env python3
"""route_oct_pourcheck.py IN.drc.json OUT.drc.json NETFILE [--manifest M.json --stage S1] : pour-connectivity check of a stage.

After a stage is routed and refilled, copper of nets the router does not route (GND patch pours such as GND_U24_PATCH_F,
power pours) can be cut off by the new tracks. KiCad reports that as an unconnected item whose items belong to a net that is
not in the router's net file. This script compares those 'foreign' unconnected items of the stage's input board (IN) and the
refilled output board (OUT); any new one flags the stage: it is printed as 'POUR CHECK FAIL' and written into the manifest
(stages[S].pour_check = {ok: false, new: [...]}), and route_oct.py refuses to route a later stage on top of it unless
--allow-pour-flag is given. Exit code 0 either way (the stage script keeps its outputs for diagnosis), 2 on missing input.
"""
import sys, json, re, argparse, os, collections

NET = re.compile(r'\[([^\]]+)\]')
ZONE = re.compile(r"^Zone '([^']*)'")


def routed_nets(path):
    out = set()
    for L in open(path, encoding='utf-8'):
        L = L.split('#', 1)[0].split()
        if len(L) >= 2:
            out.add(L[1])
    return out


def foreign(drc, nets, planes):
    """signature of each foreign unconnected item: (nets, zone names other than the board planes). KiCad picks a different
    representative item of the same cluster from run to run (an arc instead of a track, B.Cu plane instead of In2 plane), so
    descriptions and positions are not compared."""
    D = json.load(open(drc))
    out = collections.Counter(); ex = {}
    for u in D.get('unconnected_items', []):
        its = u.get('items', [])
        ns = {m for i in its for m in NET.findall(i.get('description', ''))}
        if ns & nets:
            continue
        zs = {m.group(1) for i in its for m in [ZONE.match(i.get('description', ''))] if m} - planes
        k = (tuple(sorted(ns)), tuple(sorted(zs)))
        out[k] += 1
        ex.setdefault(k, ' | '.join('%s @%.2f,%.2f' % (i.get('description', ''), i['pos']['x'], i['pos']['y']) for i in its))
    return out, ex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inp'); ap.add_argument('out'); ap.add_argument('nets')
    ap.add_argument('--manifest'); ap.add_argument('--stage')
    ap.add_argument('--planes', default='GND_BCU,GND_IN1,GND_IN2_BG', help='plane zone names ignored in the signature')
    a = ap.parse_args()
    if not os.path.exists(a.out):
        print('pourcheck: missing', a.out); sys.exit(2)
    nets = routed_nets(a.nets)
    planes = set(a.planes.split(',')) if a.planes else set()
    fo, ex = foreign(a.out, nets, planes)
    if os.path.exists(a.inp):
        fi, _ = foreign(a.inp, nets, planes)
        d = fo - fi
        new = sorted('%s x%d: %s' % ('/'.join(k[0]) + (' zone ' + ','.join(k[1]) if k[1] else ''), n, ex[k]) for k, n in d.items())
        res = dict(ok=not new, new=new, in_foreign=sum(fi.values()), out_foreign=sum(fo.values()))
    else:
        res = dict(ok=None, new=[], in_foreign=None, out_foreign=sum(fo.values()), note='input DRC missing: %s' % a.inp)
    print('POUR CHECK %s: foreign unconnected items in %d -> out %d%s' % (
        'FAIL' if res['ok'] is False else ('OK' if res['ok'] else 'UNKNOWN'), res['in_foreign'] if res['in_foreign'] is not None else -1,
        res['out_foreign'], ''.join('\n  new: ' + k for k in res['new'])))
    if a.manifest and a.stage and os.path.exists(a.manifest):
        M = json.load(open(a.manifest))
        if a.stage in M.get('stages', {}):
            M['stages'][a.stage]['pour_check'] = res
            json.dump(M, open(a.manifest, 'w'), indent=1)


if __name__ == '__main__':
    main()
