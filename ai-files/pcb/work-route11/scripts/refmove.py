#!/usr/bin/env python3
"""refmove.py IN.kicad_pcb OUT.kicad_pcb REF=dx,dy[,rot] ... : set the footprint Reference field position (footprint-relative)"""
import sys, re
L = open(sys.argv[1], encoding='utf-8').read().split('\n'); mv = {}
for a in sys.argv[3:]:
    r, v = a.split('='); mv[r] = v.split(',')
for i, l in enumerate(L):
    m = re.match(r'^\t\t\(property "Reference" "([^"]+)"$', l)
    if m and m.group(1) in mv:
        j = i + 1
        assert L[j].startswith('\t\t\t(at '), L[j]
        v = mv[m.group(1)]; L[j] = '\t\t\t(at %s %s %s)' % (v[0], v[1], v[2] if len(v) > 2 else '0'); print('moved', m.group(1), L[j].strip())
open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(L))
