#!/usr/bin/env python3
"""mkblock.py GEO BASEPLAN OUTJOBS [groups] : RT-11 analog block job file (sequential, importance order) for hr10.py"""
import sys, json
geo, base, out = sys.argv[1:4]
groups = sys.argv[4].split(',') if len(sys.argv) > 4 else ['aud', 'pwr', 'ctl']
C = dict(neck_drc=True, fine_via=True, via_cost=2.0, max_exp=3e6, max_cells=4000000, margin=3.0, run=0.75, zone_soft=0.2)
def J(net, a, b, lay='F', **k):
    j = dict(C); j.update(net=net, layers=lay); j['from'] = a
    if isinstance(b, list) and len(b) == 3 and isinstance(b[0], (int, float)):
        j['to'] = 'NET'; j['tgt_near'] = b; j['tgt_radius'] = 200.0
    else: j['to'] = b
    j.update(k); return j
A = '/Headphone_Aux/'
jobs = {'fan': [
  J('Net-(U8-NC1)', 'U8-9', 'R226-2', fine_via=False), J('Net-(U8-NC2)', 'U8-7', 'R227-2', fine_via=False),
  J('Net-(U8-NO1)', 'U8-2', 'R228-2', fine_via=False), J('Net-(U8-NO2)', 'U8-4', 'R229-2', fine_via=False),
  J('Net-(U9-NO2)', 'U9-4', 'R231-2', fine_via=False), J('Net-(U9-NO1)', 'U9-2', 'R230-2', fine_via=False),
  J('Net-(U8-COM1)', 'U8-10', 'U9-9', 'FB', margin=4, fine_via=False), J('Net-(U8-COM2)', 'U8-6', 'U9-7', 'FB', margin=4, fine_via=False),
 ], 'aud': [
  J(A + 'HP_L', 'U9-10', 'C239-1', 'FB'), J(A + 'HP_R', 'U9-6', 'C240-1', 'FB', margin=4),
  J('Net-(U10-INL-)', 'C239-2', 'U10-1', 'FB'), J('Net-(U10-INR-)', 'C240-2', 'U10-4', 'FB'),
  J('Net-(C230-Pad2)', 'C230-2', 'R226-1'), J('Net-(C230-Pad2)', 'R220-1', 'R226-1'),
  J('Net-(C231-Pad2)', 'C231-2', 'R227-1'), J('Net-(C231-Pad2)', 'R221-1', 'C231-2'),
  J('Net-(C232-Pad2)', 'C232-2', 'R228-1'), J('Net-(C232-Pad2)', 'R222-1', 'R228-1'),
  J('Net-(C233-Pad2)', 'C233-2', 'R229-1'), J('Net-(C233-Pad2)', 'R223-1', 'R229-1'),
  J('/USB_AUDIO_L', 'C230-1', [169.43, 57.13, 0.3], 'FB', margin=4),
  J('/USB_AUDIO_R', 'C231-1', [168.197, 54.72, 0.3], 'FB', margin=4),
  J('/BT_AUDIO_L', 'C232-1', [168.772, 72.47, 0.3], 'FB', margin=4),
  J('/BT_AUDIO_L', [168.117, 73.55, 'B.Cu'], [168.772, 72.47, 0.3], 'FB', margin=3),
  J('/BT_AUDIO_R', 'C233-1', [167.367, 75.6, 0.3], 'FB', margin=4),
  J('Net-(C234-Pad2)', 'R230-1', [188.69, 52.792, 0.3], 'FB', margin=4),
  J('Net-(C235-Pad2)', 'R231-1', 'R225-1', 'FB', margin=4),
  J(A + 'VMID_HP', 'R221-2', 'C236-1', 'FB', margin=4), J(A + 'VMID_HP', 'R220-2', [182.2, 63.3, 0.5], 'FB', margin=4),
  J(A + 'VMID_HP', 'R223-2', [182.2, 63.3, 3.0], 'FB', margin=5), J(A + 'VMID_HP', 'R222-2', [182.4, 74.7, 0.5], 'FB', margin=4),
  J(A + 'VMID_HP', 'R233-1', 'C236-1', 'FB'), J(A + 'VMID_HP', 'R232-2', [194.69, 58.833, 0.3], 'FB'),
  J(A + 'VMID_HP', 'R233-1', 'R232-2', 'FB'),
 ], 'pwr': [
  J('/3V3_AUDIO', [178.5, 61.6, 'F.Cu'], [180.1, 56.25, 0.4], 'FBI', w=0.5, wn=0.3, margin=3),
  J('/3V3_AUDIO', [186.0, 68.3, 'via'], [194.245, 62.145, 0.4], 'FBI', w=0.5, wn=0.3, margin=3),
  J('/3V3_AUDIO', [180.1, 56.25, 'via'], [187.8, 60.35, 0.4], 'FI', w=0.5, margin=3),
  J('/3V3_AUDIO', 'U10-14', [194.245, 62.145, 0.4], 'FI', w=0.4, wn=0.25), J('/3V3_AUDIO', 'C241-1', [194.245, 62.145, 0.4], 'FI', w=0.4, wn=0.25),
  J('/3V3_AUDIO', 'R232-1', [194.245, 62.145, 0.4], 'FI', w=0.4, wn=0.25),
 ], 'ctl': [
  J('/HP_SEL_A', 'U8-5', 'R234-1', 'FB'), J('/HP_SEL_A', 'U8-1', [171.3, 67.975, 0.3], 'FB', margin=4),
  J('/HP_SEL_A', 'U8-5', [171.3, 67.975, 3.0], 'FBI', margin=4),
  J('/HP_SEL_B', 'U9-5', 'R235-1', 'FB'), J('/HP_SEL_B', 'U9-1', 'U9-5', 'FBI', margin=3),
  J('/HP_G1', 'U10-7', 'R238-1', 'FB'), J('/HP_G1', 'R238-1', [170.275, 77.1, 0.3], 'FBI', margin=4),
  J('/HP_G0', 'U10-6', 'R237-1', 'FB'),
 ]}
J_ = []
for g in groups: J_ += jobs[g]
json.dump(dict(geo=geo, base_plan=base, out_plan=out.replace('/j', '/p'), jobs=J_), open(out, 'w'), indent=1)
print(len(J_), 'jobs')
