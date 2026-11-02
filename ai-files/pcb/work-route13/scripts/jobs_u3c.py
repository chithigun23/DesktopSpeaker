#!/usr/bin/env python3
"""jobs_u3c.py GEO OUT_JOBS OUT_PLAN [--lb 0.8] [--skip net,..] [--only pin,..] : RT-8 U3 escape plan, hand-ordered (hr8 jobs).
Group V (pins whose target is behind the package or that would cross a planar neighbour): routed first, they drop to B.Cu/In2
next to the pin (N-S nets biased to In2, E-W nets to B.Cu under the package). Group F: planar F.Cu fan, per side left-turners
from the left end, right-turners from the right end, straight last. Every job keeps the exit lanes (LB mm beyond the pad tip)
of all U3 pins routed later free (F.Cu block + no-via box)."""
import sys, json
geo, outj, outp = sys.argv[1:4]
a = sys.argv
LB = float(a[a.index('--lb') + 1]) if '--lb' in a else 0.8
D = json.load(open(geo)); pc = {'%s-%s' % (p['ref'], p['num']): (p['x'], p['y']) for p in D['pads']}
CX, CY, TIP = 128.0, 76.5, 5.67 + 0.775
NS = dict(in2_cost=1.0, bcu_cost=2.5); EW = dict(in2_cost=3.0, bcu_cost=1.0)
def J(net, fr, near, r=0.6, **kw):
    if isinstance(near, str): near = pc[near]
    j = dict(net=net, **{'from': fr}, to='NET', tgt_radius=150.0, tgt_near=[near[0], near[1], r], neck_drc=True, fine_via=True,
             island_via=True, layers='FBI', via_cost=1.2, max_exp=3e6, max_cells=4000000, margin=4)
    j.update(kw); return j
PRE = [J('/CHG_INT', 'U3-5', 'R106-2', 0.3)]
V = [  # via-first (inside runs of adjacent via pins the middle one first)
 J('/5V_LOGIC_EN', 'U3-18', (124.33, 89.4), **EW), J('/GAUGE_ALRT_N', 'U3-17', (115.88, 80.65), **EW),
 J('/AMP_FAULT_N', 'U3-25', 'R262-2', 0.3, **EW), J('/AUD_SDA', 'U3-31', 'R210-2', 0.3),
 J('/HP_DET', 'U3-28', (134.62, 63.95)), J('/AUX_DET', 'U3-29', 'R242-2', 0.3), J('/HP_G1', 'U3-21', (151.03, 76.0)),
 J('/CHG_QON_SENSE', 'U3-3', (129.6, 62.48), **NS), J('/PD_PLUG_EVENT', 'U3-4', (128.9, 61.73), **NS),
 J('/HP_EN', 'U3-47', 'U10-13', 0.3), J('/MCU/ENC_A', 'U3-48', (115.75, 79.83), **EW), J('/CHG_SYS_ENABLE', 'U3-42', 'R111-1', 2.0, **NS),
 J('/CHG_ENABLE', 'U3-38', 'R107-1', 2.0, **NS), J('/CODEC_PWR_EN', 'U3-39', (128.2, 61.02)), J('/BT_PWR_EN', 'U3-36', 'R152-1', 2.0),
 J('/BT_TX_IND', 'U3-62', (117.53, 60.55)), J('/CTRL_SDA', 'U3-61', (129.6, 89.1), **EW), J('/PD_SINK_EN', 'U3-63', (137.12, 62.4), **EW),
 J('/BT_RST_N', 'U3-58', (118.38, 61.85)), J('/BT_MFB', 'U3-57', (116.78, 64.0)), J('/HP_SEL_B', 'U3-51', 'U9-1', 0.3, **EW),
 J('/MCU/ENC_B', 'U3-49', (113.66, 80.58)),
]
VSET = None
F = [  # planar F.Cu fan
 J('/AMP_PDN', 'U3-23', 'R259-1', 0.3), J('/AMP_BOOST_EN', 'U3-24', 'R255-1', 2.0), J('/ADC_INT', 'U3-26', (138.03, 90.45)),
 J('/AUD_SCL', 'U3-30', (158.62, 71.75)),
 J('/HP_G0', 'U3-16', 'U10-6', 0.3), J('/HP_SEL_A', 'U3-13', 'U8-1', 0.3), J('/MCU/NRST', 'U3-12', 'C162-1', 0.3),
 J('/MCU/SWDIO', 'U3-45', 'J7-2', 0.3), J('/MCU/SWCLK', 'U3-46', 'J7-4', 0.3), J('/PDCTRL_SCL', 'U3-43', 'R15-2', 0.3), J('/PDCTRL_SDA', 'U3-44', (130.3, 61.98)),
 J('/BT_FORCE_PWM', 'U3-54', (116.07, 67.51)), J('/BT_UART_TX', 'U3-55', 'TP21-1', 0.3), J('/BT_UART_RX', 'U3-56', (115.38, 71.95)),
 J('/MCU/ENC_SW', 'U3-64', (125.28, 92.65)), J('/CTRL_SCL', 'U3-60', (115.15, 78.9)),
]
SEC = [  # second components (start at the component, target the U3-side copper)
 J('/AUD_SDA', 'R210-2', (136.2, 89.15)), J('/AUD_SCL', 'TP18-1', 'U3-30', 14.0),
 J('/MCU/NRST', 'TP19-1', 'C162-1', 5.0), J('/MCU/NRST', [126.25, 64.38, 'B.Cu'], 'U3-12', 4.0), J('/MCU/SWCLK', 'R160-1', 'U3-46', 6.0),
 J('/CTRL_SCL', [128.75, 89.25, 'via'], 'U3-60', 6.0), J('/PDCTRL_SCL', [135.5, 61.1, 'B.Cu'], 'U3-43', 12.0), J('/PDCTRL_SCL', [115.35, 63.7, 'F.Cu'], 'U3-43', 12.0),
 J('/AMP_PDN', [118.85, 98.15, 'F.Cu'], 'U3-23', 8.0),
 J('/MCU/SWDIO', 'J6-1', 'U3-45', 25.0), J('/MCU/SWCLK', 'J6-2', 'U3-46', 25.0), J('/MCU/NRST', 'J6-3', 'U3-12', 25.0),
 J('/HP_SEL_A', 'U8-5', 'U8-1', 4.0), J('/HP_SEL_B', 'U9-5', 'U9-1', 4.0), J('/HP_G0', 'R237-1', 'U10-6', 4.0),
 J('/PD_PLUG_EVENT', 'U11-37', 'U3-4', 30.0), J('/PD_SINK_EN', 'U11-19', 'R17-2', 6.0),
 J('/AMP_PDN', 'R258-1', 'U3-23', 70.0), J('/5V_LOGIC_EN', 'R142-1', 'U14-1', 6.0), J('/CTRL_SDA', 'U13-2', 'U3-61', 30.0),
 J('/CTRL_SCL', 'U4-14', 'U4-15', 8.0), J('/AUD_SDA', 'U24-23', 'U24-24', 8.0), J('/AMP_FAULT_N', 'U6-9', 'R262-2', 3.0),
 J('/AMP_FAULT_N', 'TP20-1', 'R262-2', 30.0), J('/AMP_FAULT_N', 'U7-9', 'R262-2', 90.0), J('/CHG_INT', 'U4-21', 'R106-2', 60.0),
]


LONG = {'U3-25', 'U3-29', 'U3-47', 'U3-42', 'U3-38', 'U3-36', 'U3-51', 'U3-24', 'U3-16', 'U3-13'}
LBL = float(a[a.index('--lbl') + 1]) if '--lbl' in a else 1.5


def lane(p):
    x, y = pc[p]; dx, dy = x - CX, y - CY; L = LBL if p in LONG else LB
    if abs(dx) > 5:
        n = 1 if dx > 0 else -1; xa, xb = sorted([CX + n * TIP, CX + n * (TIP + L)]); return [xa, y - 0.15, xb, y + 0.15]
    n = 1 if dy > 0 else -1; ya, yb = sorted([CY + n * TIP, CY + n * (TIP + L)]); return [x - 0.15, ya, x + 0.15, yb]


def vbox(p):     # no-via box of a pending pin: its lane plus EXT mm further out (own via slot), widened by via radius + clearance
    x, y = pc[p]; dx, dy = x - CX, y - CY; L = (LBL if p in LONG else LB) + EXT
    if abs(dx) > 5:
        n = 1 if dx > 0 else -1; xa, xb = sorted([CX + n * TIP, CX + n * (TIP + L)]); return [xa - 0.45, y - 0.6, xb + 0.45, y + 0.6]
    n = 1 if dy > 0 else -1; ya, yb = sorted([CY + n * TIP, CY + n * (TIP + L)]); return [x - 0.6, ya - 0.45, x + 0.6, yb + 0.45]


EXT = float(a[a.index('--ext') + 1]) if '--ext' in a else 0.8
if '--sclv' in a:
    jj = [j for j in F if j['from'] == 'U3-43'][0]; F.remove(jj)
    k = [i for i, j in enumerate(V) if j['from'] == 'U3-39'][0]; V.insert(k + 1, jj)
if '--worder' in a:      # reorder a group of V jobs: pins listed are placed (in the given order) where the first of them was
    wo = ['U3-' + x for x in a[a.index('--worder') + 1].split(',')]
    idx = [k for k, j in enumerate(V) if j['from'] in wo]
    picked = sorted([V[k] for k in idx], key=lambda j: wo.index(j['from']))
    for k, j in zip(sorted(idx), picked): V[k] = j
U = (PRE if '--pre' in a else []) + V + (F if '--pre' in a else F[:6] + PRE + F[6:])
phase = a[a.index('--phase') + 1] if '--phase' in a else 'AB'
skip = set(a[a.index('--skip') + 1].split(',')) if '--skip' in a else set()
jobs = []
for k, j in enumerate(U):
    later = [o['from'] for o in U[k + 1:] if o['net'] != j['net']] + [o['from'] for o in U[:k] if o['from'] in LONG and o['net'] != j['net']]
    if phase == 'C': continue
    if phase == 'A' and j['from'] in LONG: continue
    if phase == 'B' and j['from'] not in LONG: continue
    if phase == 'B': later = []
    if j in V:      # via-first: F.Cu only in the own escape box and near the target inside the U3 square
        x, y = pc[j['from']]; dx, dy = x - CX, y - CY
        if abs(dx) > 5:
            n = 1 if dx > 0 else -1; xa, xb = sorted([CX + n * (TIP - 1.0), CX + n * (TIP + 2.4)]); esc = [xa, y - 1.0, xb, y + 1.0]
        else:
            n = 1 if dy > 0 else -1; ya, yb = sorted([CY + n * (TIP - 1.0), CY + n * (TIP + 2.4)]); esc = [x - 1.0, ya, x + 1.0, yb]
        tx, ty = j['tgt_near'][:2]
        j['fblock'] = [[CX - 11.5, CY - 11.5, CX + 11.5, CY + 11.5]]
        j['fallow'] = [esc, [tx - 1.3, ty - 1.3, tx + 1.3, ty + 1.3]]
    j['block'] = [lane(p) + ['F.Cu'] for p in later]
    j['noviabox'] = [vbox(p) for p in later]
    jobs.append(j)
jobs += SEC[:9] if phase in ('A', 'AB') else []
jobs += SEC[9:] if phase in ('C', 'AB') else []
jobs = [j for j in jobs if j['net'] not in skip]
if '--only' in a:
    keep = set(a[a.index('--only') + 1].split(',')); jobs = [j for j in jobs if str(j['from']) in keep or j['net'] in keep]
json.dump(dict(geo=geo, out_plan=outp, jobs=jobs), open(outj, 'w'), indent=0)
print(len(jobs), 'jobs')
