#!/usr/bin/env python3
"""jobs_B.py GEO BASEPLAN OUT_JOBS [--only k,..] : RT-8 phase B (long U3 nets and remote components), one job per connection,
importance order (debug/reset, analog control, charger, amps, headphone, BT). Each is run as its own process (par8.sh)."""
import sys, json
geo, base, outj = sys.argv[1:4]
D = json.load(open(geo)); pc = {'%s-%s' % (p['ref'], p['num']): (p['x'], p['y']) for p in D['pads']}
def J(net, fr, near, r=0.6, **kw):
    if isinstance(near, str): near = pc[near]
    j = dict(net=net, **{'from': fr}, to='NET', tgt_radius=200.0, tgt_near=[near[0], near[1], r], neck_drc=True, fine_via=True,
             island_via=True, layers='FBI', via_cost=1.2, max_exp=4e6, max_cells=7000000, margin=5)
    j.update(kw); return j
jobs = [
 J('/MCU/NRST', 'J6-3', 'U3-12', 6.0), J('/MCU/SWDIO', 'J6-1', 'U3-45', 8.0), J('/MCU/SWCLK', 'J6-2', 'U3-46', 8.0),
 J('/AUD_SCL', 'TP18-1', 'U3-30', 16.0), J('/AUD_SDA', 'U24-23', 'U24-23', 6.0),
 J('/CTRL_SCL', 'U4-14', (133.8, 96.2), 3.0), J('/CTRL_SDA', 'U13-2', 'U3-61', 30.0),
 J('/CHG_ENABLE', 'U3-38', (163.0, 108.0), 3.0), J('/CHG_SYS_ENABLE', 'U3-42', 'R111-1', 2.5),
 J('/AMP_PDN', 'R258-1', 'U3-23', 60.0), J('/AMP_BOOST_EN', 'U3-24', (149.06, 140.44), 2.0), J('/AMP_FAULT_N', 'U3-25', (114.0, 126.5), 4.0),
 J('/HP_SEL_A', 'U3-13', 'U8-1', 1.0), J('/HP_SEL_B', 'U3-51', 'U9-1', 1.2), J('/HP_G0', 'U3-16', 'U10-6', 1.5), J('/HP_EN', 'U3-47', 'U10-13', 1.5),
 J('/AUX_DET', 'U3-29', 'R242-2', 0.5), J('/BT_PWR_EN', 'U3-36', 'R152-1', 3.0),
 J('/PD_PLUG_EVENT', 'U11-37', 'U3-4', 40.0), J('/PD_SINK_EN', 'U11-19', 'R17-2', 6.0), J('/5V_LOGIC_EN', 'R142-1', 'U14-1', 6.0),
]
if '--only' in sys.argv:
    keep = [int(x) for x in sys.argv[sys.argv.index('--only') + 1].split(',')]; jobs = [jobs[k] for k in keep]
json.dump(dict(geo=geo, base_plan=base, out_plan='t/pB.json', jobs=jobs), open(outj, 'w'), indent=0)
for k, j in enumerate(jobs): print(k, j['net'], j['from'])
