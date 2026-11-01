"""netsum.py STEM : per-net anomalies and length ratios from STEM.check.json (route_oct_check output)."""
import json, sys, statistics
d = json.load(open(sys.argv[1] + '.check.json')); n = d['nets']
for name, v in n.items():
    f = {x: v[x] for x in ('par_lt0.6_outside_neck_mm', 't_junctions', 'micro_segs', 'bend_spacing_short', 'joints_lt90', 'dangling', 'shorts', 'pad_exit_short') if (v.get(x) or 0) > 0}
    if f:
        print('ANOM', v['stage'], name, f, 'min gap', v.get('par_min_gap'))
rs = sorted(((v['ratio'], k, v['stage'], v['vias']) for k, v in n.items() if v.get('complete') and v.get('ratio')), reverse=True)
r = [x[0] for x in rs]
print('complete nets with ratio', len(r), 'median %.3f p95 %.3f max %.3f' % (statistics.median(r), sorted(r)[int(0.95 * (len(r) - 1) + 0.5)], max(r)))
for x in rs:
    if x[0] > 1.4:
        print('  >1.4 %-34s %s ratio %.3f vias %d' % (x[1], x[2], x[0], x[3]))
by = {}
for k, v in n.items():
    s = v['stage']; by.setdefault(s, [0, 0, 0]); by[s][0] += 1; by[s][1] += bool(v.get('complete')); by[s][2] += v['vias']
print('per stage nets/complete/vias', by)
