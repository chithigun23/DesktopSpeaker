"""route_r6h_dru.py : write work-r6/R6h.kicad_dru = R6g rules + R6h In2 slow-net exception (whitelist route_r6h_slow.json, or the nets given on the command line)"""
import json, sys
W = '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/'
nets = sys.argv[1:] or json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/route_r6h_slow.json'))
s = open(W + 'R6g.kicad_dru').read()
old = "A.NetClass != 'PWR_3V' && A.NetClass != 'GND'\")\n  (constraint disallow track))"
assert old in s
ex = ''.join(" && A.NetName != '%s'" % n for n in nets)
s = s.replace(old, "A.NetClass != 'PWR_3V' && A.NetClass != 'GND'" + ex + "\")\n  (constraint disallow track))")
BKO_EX = ['Net-(U8-COM1)', 'Net-(U8-COM2)']   # R6h exception (3): AUDIO B jumpers inside BKO_MUX only (U8 COM1/COM2 to U9)
for k in ('bko_tracks', 'bko_vias'):
    i = s.index('(condition', s.index('(rule ' + k)); j = s.index('")', i)
    s = s[:j] + ''.join(" && A.NetName != '%s'" % n for n in BKO_EX) + s[j:]
s += """
# 16b. R6h: rule 16 exempts Net-(U8-COM1)/Net-(U8-COM2) (one AUDIO B jumper each, inside BKO_MUX between U8 and U9, GND via beside).
# 19. R6h (coordinator exception): slow Default/I2C nets listed in rule 11 may run on In2 outside the power islands,
#     at least 0.3 mm from any non-GND In2 island (zone); 0.2 mm to In2 power tracks (standard).
(rule in2_slow_island
  (layer "In2.Cu")
  (condition "A.Type == 'Track' && (A.NetClass == 'Default' || A.NetClass == 'I2C') && B.Type == 'Zone' && B.NetClass != 'GND'")
  (constraint clearance (min 0.3mm)))
"""
open(W + 'R6h.kicad_dru', 'w').write(s); print('R6h.kicad_dru', len(nets), 'slow nets')
