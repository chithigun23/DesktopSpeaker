#!/usr/bin/env python3
"""Markdown before/after tables from two metrics_v10.py JSON files: v10_compare.py before.json after.json"""
import json, sys
A, B = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))


def dec(R):
    return {(d['ic'], d['group']): d for d in R['decoupling']}


da, db = dec(A), dec(B)
print('| IC / pin group | caps <= 3 mm (v9b -> v10) | nearest HF cap mm | nearest bulk cap mm |')
print('|---|---|---|---|')
for k in db:
    a, b = da.get(k), db[k]
    f = lambda d, key: ('%s %s' % (d[key][1], d[key][0])) if d and d.get(key) else '-'
    print('| %s %s | %s -> %s | %s -> %s | %s -> %s |' % (k[0], k[1], a['n3'] if a else '-', b['n3'], f(a, 'hf'), f(b, 'hf'), f(a, 'bulk'), f(b, 'bulk')))
print()
print('| Inductor | OUT pin -> pad gap mm (v9b -> v10) | filter cap gap mm |')
print('|---|---|---|')
ia = {d['L']: d for d in A['inductors']}
for d in B['inductors']:
    a = ia[d['L']]
    print('| %s (%s) | %.1f -> %.1f | %.1f -> %.1f |' % (d['L'], d['net'].split('-')[-1].rstrip(')'), a['pad_gap'], d['pad_gap'], a['filter_cap'][0], d['filter_cap'][0]))
print()
print('| Crystal net | pad gap mm (v9b -> v10) |')
print('|---|---|')
xa = {d['net']: d for d in A['crystals']}
for d in B['crystals']:
    print('| %s %s | %.1f -> %.1f |' % (d['xtal'], d['net'], xa[d['net']]['pad_gap'], d['pad_gap']))
print()
print('| I2S net | source -> U6 | source -> U7 | U6 -> U7 (v9b -> v10, octilinear mm) |')
print('|---|---|---|---|')
for n, d in B['i2s'].items():
    a = A['i2s'][n]
    print('| %s | %.0f -> %.0f | %.0f -> %.0f | %.0f -> %.0f |' % (n, a['src_U6'], d['src_U6'], a['src_U7'], d['src_U7'], a['U6_U7'], d['U6_U7']))
print()
for n in ('/USB_DP', '/USB_DN'):
    print('- %s J1 -> D1 -> R -> U2 chain: %.0f -> %.0f mm (J1 -> U2 direct %.0f -> %.0f)' % (n, A['usb'][n]['total'], B['usb'][n]['total'], A['usb'][n]['J1_U2_direct'], B['usb'][n]['J1_U2_direct']))
print('- CC caps to U11: C182 %.1f -> %.1f mm, C183 %.1f -> %.1f mm; VBUS J1 -> U11 %.0f -> %.0f mm' % (A['usb']['CC']['C182']['to_U11'], B['usb']['CC']['C182']['to_U11'], A['usb']['CC']['C183']['to_U11'], B['usb']['CC']['C183']['to_U11'], A['usb']['VBUS_J1_U11'], B['usb']['VBUS_J1_U11']))
print('- TVS gap to the J1 body: %s -> %s' % (A['usb']['TVS_gap_to_J1_body'], B['usb']['TVS_gap_to_J1_body']))
print('- BM83: U15 -> U1.23 %.1f -> %.1f mm, L3 %.1f -> %.1f mm; parts within 3 mm of the antenna keep-out %s -> %s' % (A['bm83']['U15_to_U1.23'], B['bm83']['U15_to_U1.23'], A['bm83']['L3_to_U1.23'], B['bm83']['L3_to_U1.23'], A['bm83']['parts_within_3mm_of_antenna_keepout'], B['bm83']['parts_within_3mm_of_antenna_keepout']))
print('- Board %.1f x %.1f = %d mm2 -> %.1f x %.1f = %d mm2' % (A['board']['W'], A['board']['H'], A['board']['area'], B['board']['W'], B['board']['H'], B['board']['area']))
print('- Test point closest to the edge: %s -> %s' % (A['testpoints_edge']['min'], B['testpoints_edge']['min']))
print('- GND cap pads without room for a 0.6 mm via within 1 mm: %s -> %s (of %d)' % (A['gnd_via_room']['without_room'], B['gnd_via_room']['without_room'], B['gnd_via_room']['gnd_cap_pads']))
print('- 1 mm escape band around the IC covered by other courtyards: ' + ', '.join('%s %.2f -> %.2f' % (k, A['escape_band_covered'][k], v) for k, v in B['escape_band_covered'].items()))
print('- Courtyard rectangle overlaps: %d -> %d' % (A['courtyard_rect_overlap_count'], B['courtyard_rect_overlap_count']))
