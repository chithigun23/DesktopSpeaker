#!/usr/bin/env python3
"""probe13.py GEO DIR : one independent job file per open connection (RT-13 list), island_via relaxation (BAT_INT, VBUS_PD, SYS_RAW forbidden)."""
import sys, json
geo, d = sys.argv[1:3]
C = dict(neck_drc=True, fine_via=True, via_cost=2.0, max_exp=8e6, max_cells=12000000, margin=4.0, run=0.75, zone_soft=0.2,
         island_via=True, island_forbid=['/Battery_Charger/BAT_INT', '/Battery_Charger/VBUS_PD', '/SYS_RAW'])
def J(name, net, a, b, lay='FB', **k):
    j = dict(C); j.update(net=net, layers=lay); j['from'] = a
    if isinstance(b, list) and len(b) == 3 and isinstance(b[0], (int, float)):
        j['to'] = 'NET'; j['tgt_near'] = b; j['tgt_radius'] = 300.0
    else: j['to'] = b
    j.update(k); return name, j
A = '/Headphone_Aux/'
P = [
 J('cc1', '/USB_CC1', 'C182-1', 'D5-1', 'FB'),
 J('cc2', '/USB_CC2', 'C183-1', [152.79, 32.8, 0.4], 'FB'),
 J('fu3', '/AMP_FAULT_N', 'U3-25', [111.5, 125.5, 1.5], 'FBI', ic_allow=['U3'], box=[100, 70, 150, 132]),
 J('fu7', '/AMP_FAULT_N', 'U7-9', 'U3-25', 'FBI', ic_allow=['U3'], box=[128, 70, 200, 132]),
 J('tp20', '/AMP_FAULT_N', 'TP20-1', [111.5, 126.0, 2.0], 'FBI', box=[98, 118, 125, 153]),
 J('pdn', '/AMP_PDN', 'R258-1', [137.47, 79.5, 2.0], 'FBI', box=[130, 72, 192, 120]),
 J('selb', '/HP_SEL_B', 'U3-51', 'R235-1', 'FBI', ic_allow=['U3'], box=[116, 50, 190, 82]),
 J('hpen', '/HP_EN', 'U3-47', [197.04, 63.78, 0.4], 'FBI', ic_allow=['U3'], box=[116, 50, 202, 80]),
 J('auxdet', '/AUX_DET', 'U3-29', 'R242-2', 'FBI', ic_allow=['U3'], box=[126, 32, 196, 80]),
 J('3vao', '/3V_AO', 'R241-1', [126.95, 64.48, 0.5], 'FBI', w=0.5, box=[120, 34, 194, 70]),
 J('usbl', '/USB_AUDIO_L', 'C200-1', [176.6, 60.88, 0.3], 'FB', margin=5),
 J('usbr', '/USB_AUDIO_R', 'C201-1', [168.75, 56.43, 0.3], 'FB', margin=5),
 J('c204', 'Net-(C204-Pad2)', 'R204-1', 'C204-2', 'FB', margin=5),
 J('c205', 'Net-(C205-Pad2)', 'R205-1', 'C205-2', 'FB', margin=5),
 J('auxl', '/AUX_L', [191.14, 39.03, 'F.Cu'], [194.19, 36.59, 0.3], 'FB'),
 J('c235a', 'Net-(C235-Pad2)', 'R231-1', 'R225-1', 'FB', margin=5),
 J('c235b', 'Net-(C235-Pad2)', 'C235-2', 'R225-1', 'FB', margin=5),
 J('sda1', '/AUD_SDA', 'U24-23', [139.05, 81.0, 0.3], 'FB', margin=5),
 J('sda2', '/AUD_SDA', 'U7-15', 'U24-23', 'FB', box=[136, 80, 198, 130]),
]
for n, j in P:
    json.dump(dict(geo=geo, base_plan=None, out_plan='%s/p_%s.json' % (d, n), jobs=[j]), open('%s/j_%s.json' % (d, n), 'w'), indent=1)
print(' '.join(n for n, j in P))
