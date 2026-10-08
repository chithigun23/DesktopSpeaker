#!/usr/bin/env python3
"""Copy the (stackup ...) block of the project board (read only) into a generated work board: v10_stackup.py src.kicad_pcb dst.kicad_pcb"""
import re, sys
src, dst = open(sys.argv[1]).read(), open(sys.argv[2]).read()
m = re.search(r'\n(\s*)\(stackup\n.*?\n\1\)\n', src, re.S)
if not m:
    sys.exit('no stackup in ' + sys.argv[1])
if '(stackup' not in dst:
    dst = re.sub(r'(\n\s*\(setup\n)', lambda q: q.group(1) + m.group(0).lstrip('\n'), dst, count=1)
    open(sys.argv[2], 'w').write(dst)
print('stackup', 'present' if '(stackup' in dst else 'MISSING')
