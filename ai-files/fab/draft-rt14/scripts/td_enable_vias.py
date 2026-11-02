#!/usr/bin/env python3
"""td_enable_vias.py IN.kicad_pcb OUT.kicad_pcb  (plain python3, text edit only)
Give every via that has no (teardrops ...) block the block the R6q release board used on all its vias
(curved, length ratio 0.5, max length 0.6 mm, width ratio 1, max width 2 mm, filter 0.9, two segments, prefer zones).
Router/text-edited vias were written without the block, so KiCad treats them as teardrops disabled.
Pads and vias that already have a block are left unchanged. Prints the count."""
import re, sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
BLOCK = ('\t\t(teardrops\n\t\t\t(best_length_ratio 0.5)\n\t\t\t(max_length 0.6)\n\t\t\t(best_width_ratio 1)\n\t\t\t(max_width 2)\n'
         '\t\t\t(curved_edges yes)\n\t\t\t(filter_ratio 0.9)\n\t\t\t(enabled yes)\n\t\t\t(allow_two_segments yes)\n'
         '\t\t\t(prefer_zone_connections yes)\n\t\t)\n')
n = 0
def fix(m):
    global n
    body = m.group(0)
    if '(teardrops' in body: return body
    n += 1
    return re.sub(r'(\n\t\t\(layers [^\n]*\)\n)', lambda k: k.group(1) + BLOCK, body, count=1)
out = re.sub(r'\n\t\(via\n.*?\n\t\)', fix, s, flags=re.S)
open(dst, 'w').write(out)
total = len(re.findall(r'\n\t\(via\n', out)); dis = sum(1 for v in re.findall(r'\n\t\(via\n.*?\n\t\)', out, flags=re.S) if '(teardrops' not in v)
print(f'vias {total}, teardrops block added {n}, vias still without block {dis}')
