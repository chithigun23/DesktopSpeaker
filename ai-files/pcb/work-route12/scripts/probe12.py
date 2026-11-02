#!/usr/bin/env python3
"""probe12.py GEO TAG : one job file per open connection (RT-11 list), each probed independently (no interaction)."""
import sys, json
geo, tag = sys.argv[1:3]
C = dict(neck_drc=True, fine_via=True, via_cost=2.0, max_exp=4e6, max_cells=6000000, margin=3.0, run=0.75, zone_soft=0.2)
def J(name, net, a, b, lay='FB', **k):
    j = dict(C); j.update(net=net, layers=lay); j['from'] = a
    if isinstance(b, list) and len(b) == 3 and isinstance(b[0], (int, float)):
        j['to'] = 'NET'; j['tgt_near'] = b; j['tgt_radius'] = 300.0
    else: j['to'] = b
    j.update(k); return name, j
A = '/Headphone_Aux/'
P = [
 J('sda1', '/AUD_SDA', 'U24-23', [139.05, 81.0, 0.3], 'FB'),
 J('sda2', '/AUD_SDA', 'U7-15', 'U24-23', 'FB', margin=5),
 J('auxl', '/AUX_L', [191.14, 39.03, 'F.Cu'], [194.19, 36.59, 0.3], 'FB'),
 J('ctrlscl', '/CTRL_SCL', 'U4-14', [140, 110, 60], 'FBI'),
 J('gauge', '/Fuel_Gauge_Power/GAUGE_ISO_N', 'U17-4', [99.96, 76.48, 0.3], 'FB'),
 J('3vao', '/3V_AO', 'R241-2', [126.95, 64.48, 0.5], 'FBI', w=0.5),
 J('q101g', 'Net-(Q101-G)', 'Q102-3', [176.59, 109.42, 0.3], 'FB'),
 J('c205', 'Net-(C205-Pad2)', 'R205-1', 'C205-2', 'FB', margin=5),
 J('c204', 'Net-(C204-Pad2)', 'R204-1', 'C204-2', 'FB', margin=5),
 J('hpoutl', A + 'HP_OUTL', 'U10-16', [174.71, 33.99, 0.3], 'FB', margin=4),
 J('adc4', 'Net-(U11-ADC4)', 'U11-7', [135.45, 61.53, 0.3], 'FB', neck_val=0.15, wn=0.15),
 J('fault_u6', '/AMP_FAULT_N', 'U6-9', 'R262-2', 'FBI'),
 J('fault_u3', '/AMP_FAULT_N', 'U3-25', 'R262-2', 'FBI', margin=4),
 J('fault_u7', '/AMP_FAULT_N', 'U7-9', 'R262-2', 'FBI', margin=4),
 J('bck6', '/I2S_BCK', 'TP12-1', 'U6-13', 'FB', margin=4),
 J('bck7', '/I2S_BCK', 'U7-13', [147.15, 93.75, 0.3], 'FB', margin=4),
 J('ilim', '/Battery_Charger/ILIM_HIZ', [153.42, 123.39, 'F.Cu'], [180.96, 110.73, 0.3], 'FB', margin=4),
 J('c235a', 'Net-(C235-Pad2)', 'R231-1', 'R225-1', 'FB', margin=4),
 J('c235b', 'Net-(C235-Pad2)', 'C235-2', 'R225-1', 'FB', margin=4),
 J('r18', 'Net-(R18-Pad1)', 'R18-1', 'U11-36', 'FB', neck_val=0.15, wn=0.15),
 J('hpg0', '/HP_G0', 'U3-16', [196.04, 69.0, 2.5], 'FBI', margin=4),
 J('voutl', 'Net-(U2-VOUTL)', 'U2-16', 'C186-1', 'FB'),
 J('usbl', '/USB_AUDIO_L', 'C200-1', [176.6, 60.88, 0.3], 'FB', margin=4),
 J('usbr', '/USB_AUDIO_R', 'C201-1', [168.75, 56.43, 0.3], 'FB', margin=4),
 J('5vlen', '/5V_LOGIC_EN', 'R142-1', [98.72, 98.2, 0.3], 'FBI'),
 J('fb14', 'Net-(U14-FB)', 'R140-2', [93.22, 101.58, 0.3], 'FB'),
 J('cc1', '/USB_CC1', 'C182-1', 'D5-1', 'FB', margin=4),
 J('cc2', '/USB_CC2', 'C183-1', [152.79, 32.8, 0.3], 'FB', margin=4),
 J('u12en', 'Net-(U12-EN)', [93.35, 73.98, 'F.Cu', 0.3], [110.46, 76.28, 0.4], 'FBI'),
 J('qon', 'Net-(U4-QON)', 'U4-12', [140, 110, 120], 'FBI'),
 J('pdn', '/AMP_PDN', 'R258-1', [137.47, 80.9, 0.3], 'FBI', margin=4),
 J('hpen', '/HP_EN', 'U3-47', [197.04, 63.78, 0.4], 'FBI', margin=4),
 J('selb', '/HP_SEL_B', 'U3-51', 'R235-1', 'FBI', margin=4),
 J('auxdet', '/AUX_DET', 'U3-29', 'R242-2', 'FBI', margin=4),
 J('sinken', '/PD_SINK_EN', 'R17-2', 'U11-19', 'FBI', neck_val=0.15, wn=0.15),
 J('u7pdn', 'Net-(U7-~{PDN})', 'R258-2', 'U7-17', 'FBI'),
]
for n, j in P:
    json.dump(dict(geo=geo, base_plan=None, out_plan='t/probe/p%s_%s.json' % (tag, n), jobs=[j]), open('t/probe/j%s_%s.json' % (tag, n), 'w'), indent=1)
print(' '.join(n for n, j in P))
