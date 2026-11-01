"""analyze.py RUN [--json OUT] : stage summaries of RUN-1..3.route.json, per-net comparison with the R10-0 baseline (work-oct2 N2,
same router code, USB/XTO not templated there) and the list of unrouted connections with a first cause class.
Cause classes: no exit | keep-out (BM83 U1 pad or J7) | pour island (a GND-pour cut was rejected) |
topology/pin order (blocked by copper of same-stage nets: the conflict search found a set) | no path (local pocket: every window
search ended in < 0.1 s, i.e. the start or target region is sealed) | no path (global: the search ran and found no corridor)."""
import sys, json, collections
R = sys.argv[1]
OCT2 = '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-oct2/'
base = {}
for f in ('N2-1', 'N2-2', 'N2k-3'):
    for r in json.load(open(OCT2 + f + '.route.json'))['nets']:
        base[r['net']] = (sum(c['status'] == 'ok' for c in r['conns']), len(r['conns']), f)
out = dict(stages={}, nets={}, unrouted=[])
for s in (1, 2, 3):
    try:
        d = json.load(open('%s-%d.route.json' % (R, s)))
    except FileNotFoundError:
        continue
    sm = d['summary']; out['stages']['S%d' % s] = {k: sm[k] for k in ('conns_ok', 'conns', 'complete_nets', 'segments', 'vias', 'stitch_vias', 'runtime_s')}
    out['stages']['S%d' % s]['nets'] = len(sm['nets']); out['stages']['S%d' % s]['stats'] = sm['stats']
    rr = collections.defaultdict(list)
    for e in d['rrr']:
        rr[(e['net'], e['conn'])].append(e)
    for r in d['nets']:
        ok = sum(c['status'] == 'ok' for c in r['conns'])
        out['nets'][r['net']] = dict(stage='S%d' % s, ok=ok, n=len(r['conns']), base=base.get(r['net']), cls=r['cls'])
        for c in r['conns']:
            if c['status'] == 'ok':
                continue
            st = c['status']; pads = (c['a'], c['b'])
            tries = c.get('tries', []); ret = ' '.join(c.get('retries', []))
            conf = [e['conflicts'] for e in rr.get((r['net'], '%s>%s' % pads), []) if e.get('conflicts')]
            if st.startswith('no exit'):
                cause = 'no exit'
            elif any(p.startswith('U1-') or p.startswith('J7-') for p in pads):
                cause = 'keep-out'
            elif 'isolate' in ret or 'isolate' in st:
                cause = 'pour island'
            elif conf:
                cause = 'topology/pin order'
            elif tries and max(t.get('t', 0) for t in tries) < 0.1:
                cause = 'no path (local pocket)'
            else:
                cause = 'no path (global)'
            out['unrouted'].append(dict(stage='S%d' % s, net=r['net'], cls=r['cls'], a=pads[0], b=pads[1], status=st[:60], cause=cause,
                                        conflicts=sorted({n for x in conf for n in x}), retries=c.get('retries', []),
                                        tmax=round(max((t.get('t', 0) for t in tries), default=0), 2)))
print(json.dumps(out['stages'], indent=1))
cc = collections.Counter((u['stage'], u['cause']) for u in out['unrouted'])
print('unrouted by stage/cause:', sorted(cc.items()))
cmp = collections.Counter()
for n, v in out['nets'].items():
    if v['base']:
        b = v['base'][0]; cmp['better' if v['ok'] > b else 'worse' if v['ok'] < b else 'same'] += 1
print('per-net vs R10-0 baseline (nets present in both):', dict(cmp))
for n, v in out['nets'].items():
    if v['base'] and v['ok'] != v['base'][0]:
        print('  %-30s %s now %d/%d  base %d/%d (%s)' % (n, v['stage'], v['ok'], v['n'], v['base'][0], v['base'][1], v['base'][2]))
if '--json' in sys.argv:
    json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
