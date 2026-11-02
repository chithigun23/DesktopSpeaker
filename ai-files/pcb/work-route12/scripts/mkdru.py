#!/usr/bin/env python3
"""mkdru.py NETLIST.txt OUT.kicad_dru : RT-10 rule file = RT-9p rule file (base9p.kicad_dru, byte-identical) + rule 21 only."""
import sys
nets = [l.split('#')[0].strip() for l in open(sys.argv[1]) if l.split('#')[0].strip()]
cond = ' || '.join("A.NetName == '%s'" % n for n in nets)
r21 = '''
# 21. RT-10 (coordinator decision 2026-11-02; documented additive exemption, sentinel-tested): slow digital control / status /
#     enable / strap / UART / debug nets that rule 11 does not list may run on In2.Cu, in the In2 GND pour only.
#     Not for audio, I2S, USB data, clocks/crystals, switch nodes or analogue sense/feedback nets.
#     21a lifts rule 11 for these nets (a later matching rule takes precedence; severity ignore = allowed);
#     21b keeps them at >= 0.25 mm on In2. Clearance to In2 power islands stays 0.3 mm (rule 19, Default class).
(rule rt10_in2_slow
  (layer "In2.Cu")
  (condition "A.Type == 'Track' && (%s)")
  (constraint disallow track)
  (severity ignore))
(rule rt10_in2_slow_width
  (layer "In2.Cu")
  (condition "A.Type == 'Track' && (%s)")
  (constraint track_width (min 0.25mm)))
''' % (cond, cond)
open(sys.argv[2], 'w').write(open('base9p.kicad_dru').read() + r21)
print('rule 21 nets', len(nets))
