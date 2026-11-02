#!/usr/bin/env python3
"""final10.py CHGPLAN OUT_JOBS : RT-10 final composition (sequential hr10 job file).
 base adds : BT_RST_M (hr10 route, start reshaped onto the RT-8 escape stub end), CHG_ENABLE + CHG_SYS_ENABLE (CHGPLAN),
             AUX_L (hr10 route without its overlapping F stub), CODEC_PWR_EN (manual F, replaces the B loop).
 jobs      : B-over-void repairs V1-30 GAUGE_ALRT_N, V1-9 SWDIO, V2-42 PDCTRL_SDA, V2-32 CHG_QON_SENSE, V2-9 HP_SEL_A."""
import sys, json
chg, out = sys.argv[1:3]
P = dict(seg_add=[], via_add=[], seg_del=[], via_del=[], seg_set={}, via_del_xy=[])
# BT_RST_M
P['seg_add'] += [['In2.Cu', '/Bluetooth/BT_RST_M', 0.25, 98.795, 24.365, 98.795, 46.865], ['F.Cu', '/Bluetooth/BT_RST_M', 0.25, 98.795, 46.865, 102.795, 50.865]]
P['via_add'] += [['/Bluetooth/BT_RST_M', 98.795, 24.365, 0.6, 0.3], ['/Bluetooth/BT_RST_M', 98.795, 46.865, 0.6, 0.3]]
P['seg_del'] += ['12447eb0']; P['seg_set']['1656e077'] = [97.095, 24.365, 98.795, 24.365]
# CHG
C = json.load(open(chg)); P['seg_add'] += [s for s in C['seg_add'] if 'CHG_' in s[1]]; P['via_add'] += [v for v in C['via_add'] if 'CHG_' in v[0]]
# AUX_L
P['seg_add'] += [['B.Cu', '/AUX_L', 0.3, 195.0375, 36.595, 192.5375, 36.595], ['B.Cu', '/AUX_L', 0.3, 192.5375, 36.595, 190.6375, 38.495],
                 ['F.Cu', '/AUX_L', 0.3, 190.6375, 38.495, 191.1875, 39.045]]
P['via_add'] += [['/AUX_L', 195.0375, 36.595, 0.6, 0.3], ['/AUX_L', 190.6375, 38.495, 0.6, 0.3]]
# CODEC_PWR_EN: R212-1 straight into U23-3, B loop and its vias removed
P['seg_del'] += ['d6c15db0', '030047e4', '4dae2f8f', '95773a97']; P['via_del'] += ['40f10cf4', 'f94f5923']; P['via_del_xy'] += [[185.7575, 54.29], [183.4575, 52.79]]
P['seg_add'] += [['F.Cu', '/CODEC_PWR_EN', 0.25, 184.2075, 54.29, 184.2075, 52.79]]
# PDCTRL_SDA: via left on F only after the repair
P['via_del'] += ['2ce55e7c']; P['via_del_xy'] += [[137.4, 42.525]]
jobs = []
for tag, k in [('V1', 30), ('V1', 9), ('V2', 42), ('V2', 32), ('V2', 9), ('V1', 4)]:
    P['seg_del'] += json.load(open('t/r_%s_%d.json' % (tag, k)))['seg_del']
    jobs += json.load(open('t/j_%s_%d.json' % (tag, k)))['jobs']
json.dump(P, open(out.replace('.json', '_base.json'), 'w'), indent=1)
json.dump(dict(geo='R1.geo.json', base_plan=out.replace('.json', '_base.json'), out_plan=out.replace('/j', '/p'), jobs=jobs), open(out, 'w'))
print('ok', len(jobs))
