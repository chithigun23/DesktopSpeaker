#!/usr/bin/env python3
"""zoneclr.py IN.kicad_pcb OUT.kicad_pcb NAME CLEARANCE : RT-10 text edit - set the (connect_pads (clearance X)) of the named zone."""
import sys
src, out, name, c = sys.argv[1:5]
L = open(src, encoding='utf-8').read().split('\n'); n = 0
for i, l in enumerate(L):
    if l.strip() == '(name "%s")' % name:
        j = i
        while not L[j].startswith('\t(zone'): j -= 1
        k = j
        while '(polygon' not in L[k]:
            if L[k].strip().startswith('(clearance ') and L[k - 1].strip().startswith('(connect_pads'):
                print('zone %s clearance %s -> %s' % (name, L[k].strip(), c)); L[k] = L[k].split('(')[0] + '(clearance %s)' % c; n += 1
            k += 1
assert n == 1, n
open(out, 'w', encoding='utf-8').write('\n'.join(L))
