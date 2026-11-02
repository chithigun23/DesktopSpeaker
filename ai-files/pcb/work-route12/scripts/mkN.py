#!/usr/bin/env python3
"""mkN.py GEO BASEPLAN TAG ORDER [--lb 1.0] [--extra json] : RT-9 north-corridor jobs (hr8) in the given order (letters):
 S=PDCTRL_SCL U3-43, D=PDCTRL_SDA U3-44, C=CODEC_PWR_EN U3-39, B=BT_PWR_EN U3-36, Q=CHG_QON_SENSE via, P=PD_PLUG_EVENT via.
Exit lanes of later U3 pins are kept free (F.Cu block LB beyond the tip, no-via box)."""
import sys, json
a = sys.argv; geo, base, tag, order = a[1:5]
LB = float(a[a.index('--lb') + 1]) if '--lb' in a else 1.0
D = json.load(open(geo)); pc = {'%s-%s' % (p['ref'], p['num']): (p['x'], p['y']) for p in D['pads']}
CX, CY, TIP = 128.0, 76.5, 5.67 + 0.775
B = dict(to='NET', tgt_radius=150.0, neck_drc=True, fine_via=True, island_via=True, layers='FBI', via_cost=1.2, max_exp=4e6, max_cells=6000000, margin=4)
def J(net, fr, near, **kw):
    j = dict(B); j.update(net=net, **{'from': fr}); j['tgt_near'] = near; j.update(kw); return j
JJ = {'S': J('/PDCTRL_SCL', 'U3-43', [130.3, 59.5, 1.3]), 'D': J('/PDCTRL_SDA', 'U3-44', [133.6, 59.0, 1.6]),
      'W': J('/MCU/SWDIO', 'J7-2', [125.75, 70.3, 0.3]), 'w': J('/MCU/SWDIO', 'U3-45', [129.365, 71.695, 0.3]),
      'K': J('/MCU/SWCLK', 'U3-46', [129.015, 72.135, 0.3]), 'k': J('/MCU/SWCLK', [122.95, 65.525, 'via'], [125.25, 70.3, 0.3]),
      'r': J('/MCU/SWCLK', [123.4, 69.625, 'via'], [125.25, 70.3, 1.5]), 'b': J('/BT_PWR_EN', [127.35, 58.575, 'via'], [130.25, 70.825, 0.3]),
      'c': J('/CODEC_PWR_EN', [128.2, 61.025, 'via'], [128.75, 70.825, 0.3]),
      'C': J('/CODEC_PWR_EN', 'U3-39', [128.2, 61.025, 0.4]), 'B': J('/BT_PWR_EN', 'U3-36', [127.35, 58.575, 0.4]),
      'Q': J('/CHG_QON_SENSE', [131.05, 68.725, 'via'], [129.6, 62.0, 0.6]), 'P': J('/PD_PLUG_EVENT', [131.15, 69.525, 'via'], [128.9, 61.725, 0.4])}
def lane(p):
    x, y = pc[p]; ya, yb = sorted([CY - TIP, CY - (TIP + LB)]); return [x - 0.15, ya, x + 0.15, yb, 'F.Cu']
def vbox(p):
    x, y = pc[p]; ya, yb = sorted([CY - TIP, CY - (TIP + LB + 0.8)]); return [x - 0.6, ya - 0.45, x + 0.6, yb + 0.45]
jobs = []
for k, c in enumerate(order):
    j = dict(JJ[c]); PIN = dict(S='U3-43', D='U3-44', C='U3-39', c='U3-39', B='U3-36', b='U3-36', w='U3-45', K='U3-46')
    later = [PIN[o] for o in order[k + 1:] if o in PIN]
    j['block'] = [lane(p) for p in later]; j['noviabox'] = [vbox(p) for p in later]; jobs.append(j)
if '--extra' in a: jobs += json.load(open(a[a.index('--extra') + 1]))
json.dump(dict(geo=geo, base_plan=base, out_plan='t/pN_%s.json' % tag, jobs=jobs), open('t/jN_%s.json' % tag, 'w'))
