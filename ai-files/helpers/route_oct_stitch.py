#!/usr/bin/env python3
"""route_oct_stitch.py : GND stitching vias along EXISTING sensitive B.Cu runs (fix 6 for copper that is already on the board).

  route_oct_stitch.py --board IN.kicad_pcb --geo IN.geo.json --nets NETFILE --out OUT.kicad_pcb --manifest MAN.json --stage SX
                      [--run-stitch 6.0] [--run-stitch-dist 1.5]
For every net of NETFILE that route_oct.py stitches (sensitive classes and the r7 gvia set), the B.Cu tracks are merged into
runs; along each run a GND via (existing via, plated GND hole or a new one) must lie within --run-stitch-dist of the track at
least every --run-stitch mm. Missing stations are added as new GND vias with route_oct's legality (via_ok_exact for net GND,
In1 + In2 GND copper around the via, spacing to other new vias). Nothing else is changed. The copper of the input stays locked:
with a continuation manifest (route_oct.py --cont-drc) the lock is checked first and the new vias are recorded as stage SX
(added_items), so later continuation stages and route_oct_check.py verify them. A run that cannot be covered is reported.
"""
import sys, os, json, argparse, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import route_oct as RO
import route_oct_lock as LK
from shapely.geometry import LineString
from shapely.ops import unary_union, linemerge


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--board', required=True); ap.add_argument('--geo', required=True); ap.add_argument('--nets', required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--manifest', required=True); ap.add_argument('--stage', required=True)
    ap.add_argument('--dru'); ap.add_argument('--pro'); ap.add_argument('--workdir')
    ap.add_argument('--run-stitch', type=float, default=6.0); ap.add_argument('--run-stitch-dist', type=float, default=1.5)
    ap.add_argument('--log')
    a = ap.parse_args()
    stem = os.path.splitext(a.board)[0]; a.dru = a.dru or stem + '.kicad_dru'; a.pro = a.pro or stem + '.kicad_pro'
    man = json.load(open(a.manifest))
    if man.get('mode') != 'continue':
        raise SystemExit('route_oct_stitch: needs a continuation manifest (C0 lock)')
    man['stages'].pop(a.stage, None)
    lk = LK.cont_lock(a.board, man)
    if not all(v['ok'] for v in lk.values()):
        raise SystemExit('LOCK VIOLATION (continuation): %s' % lk)
    # router model with its defaults (only the board model and the GND-via legality are used)
    r_ap_src = open(RO.__file__).read()
    ns = {}
    code = r_ap_src[r_ap_src.index('    ap = argparse.ArgumentParser()'):r_ap_src.index('    a = ap.parse_args()')]
    exec('import argparse\n' + '\n'.join(l[4:] for l in code.split('\n')), ns)
    ra = ns['ap'].parse_args(['--board', a.board, '--geo', a.geo, '--nets', a.nets, '--stage', a.stage, '--out', a.out, '--manifest', a.manifest,
                              '--run-stitch', str(a.run_stitch), '--run-stitch-dist', str(a.run_stitch_dist)])
    ra.margins = [float(x) for x in ra.margins.split(',')]
    core = RO.load_core(a.workdir or os.path.dirname(os.path.abspath(a.out)))
    RO.HALO[0] = ra.halo
    B = RO.Board(a.geo, a.dru, a.pro, core, ra)
    stages, opts = RO.read_nets(a.nets)
    R = RO.Router(B, ra, opts); R.cont = True
    nets = [n for st in stages.values() for n in st]
    rows = []; out_vias = []
    for net in nets:
        pf = R.prof(net)
        if not pf['stitch']:
            continue
        ls = [LineString([(t['x1'], t['y1']), (t['x2'], t['y2'])]) for t in B.D['tracks']
              if t['net'] == net and t['layer'] == 'B.Cu' and not t['arc'] and (t['x1'], t['y1']) != (t['x2'], t['y2'])]
        w = max([t['w'] for t in B.D['tracks'] if t['net'] == net and t['layer'] == 'B.Cu'] or [0.25])
        u = unary_union(ls) if ls else None; m = (linemerge(u) if hasattr(u, 'geoms') else u) if ls else None
        for run in ((list(m.geoms) if hasattr(m, 'geoms') else [m]) if ls else []):
            pts = list(run.coords)
            segs = [['B.Cu', (int(round(p[0] * 1e6)), int(round(p[1] * 1e6))), (int(round(q[0] * 1e6)), int(round(q[1] * 1e6))), w] for p, q in zip(pts[:-1], pts[1:])]
            placed, bad = R.place_run_stitches(pf, segs, [], [])
            row = dict(net=net, len=round(run.length, 2), new=0)
            if placed is None:
                row['fail_at'] = [round(bad[0], 3), round(bad[1], 3)]
            else:
                row['new'] = len(placed)
                if placed:
                    R.commit(pf, [], [], placed)
                    out_vias += [dict(a=(int(round(x * 1e6)), int(round(y * 1e6))), net='GND', owner=net) for x, y in placed]
            rows.append(row)
            print('%-28s run %6.2f mm: %s' % (net, run.length, ('%d new GND vias' % row['new']) if 'fail_at' not in row else 'NOT COVERABLE near %s' % row['fail_at']), flush=True)
        # LA5 for existing copper: every via of the net gets a GND via within --stitch (route_oct default 1.5 mm)
        for v in [v for v in B.D['vias'] if v['net'] == net]:
            placed, bad = R.place_stitches(pf, [], [(int(round(v['x'] * 1e6)), int(round(v['y'] * 1e6)))])
            row = dict(net=net, via=[round(v['x'], 3), round(v['y'], 3)], new=0)
            if placed is None:
                row['fail_at'] = row['via']
            elif placed:
                row['new'] = len(placed); R.commit(pf, [], [], placed)
                out_vias += [dict(a=(int(round(x * 1e6)), int(round(y * 1e6))), net='GND', owner=net) for x, y in placed]
            if placed is None or placed:
                rows.append(row)
                print('%-28s via %.3f,%.3f: %s' % (net, v['x'], v['y'], 'NO STITCH SPOT' if placed is None else '%d new GND via' % len(placed)), flush=True)
    RO.write_board(a.board, a.out, [], out_vias)
    added = LK.item_strings(a.out) - LK.item_strings(a.board)
    ent = dict(stage=a.stage, mode='stitch-existing', input_board=os.path.abspath(a.board), output_board=os.path.abspath(a.out),
               runs=rows, stitch_vias=['%.6f %.6f' % (v['a'][0] / 1e6, v['a'][1] / 1e6) for v in out_vias],
               added_items=sorted(added.elements()), output_sha256=hashlib.sha256(open(a.out, 'rb').read()).hexdigest(),
               dru_sha256=RO.RU.check_dru(a.dru)[1], pro_sha256=hashlib.sha256(open(a.pro, 'rb').read()).hexdigest(),
               params=dict(run_stitch=a.run_stitch, run_stitch_dist=a.run_stitch_dist))
    ent['copper_sha256'], ent['copper_items'] = LK.hash_strings(ent['added_items'])
    man['stages'][a.stage] = ent
    json.dump(man, open(a.manifest, 'w'), indent=1)
    if a.log:
        json.dump(ent, open(a.log, 'w'), indent=1)
    print('STITCH %s: %d runs, %d new GND vias, %d runs not coverable' % (a.stage, len(rows), len(out_vias), sum(1 for r in rows if 'fail_at' in r)), flush=True)


if __name__ == '__main__':
    main()
