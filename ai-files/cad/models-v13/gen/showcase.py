"""Make a small showcase board with selected footprints (models as on the source board) laid out in a row,
for kicad-cli render checks.  python3 showcase.py SRC.kicad_pcb OUT.kicad_pcb REF[,REF...] [pitch_mm]"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src, out, refs = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
pitch = float(sys.argv[4]) if len(sys.argv) > 4 else 30.0
txt = open(src).read()


def match_close(t, i):
    d = 0; j = i; ins = False
    while True:
        c = t[j]
        if ins:
            if c == '\\': j += 2; continue
            if c == '"': ins = False
        elif c == '"': ins = True
        elif c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: return j
        j += 1


first = txt.index('\n\t(footprint')
head = txt[:first]
blocks = {}
for m in re.finditer(r'\n\t\(footprint "', txt):
    s = m.start() + 2; e = match_close(txt, s)
    blk = txt[s:e + 1]
    r = re.search(r'\(property "Reference" "([^"]+)"', blk)
    if r and r.group(1) in refs:
        blocks[r.group(1)] = blk
body = []
x = 20.0
for ref in refs:
    blk = blocks[ref]
    # first (at x y [rot]) after the footprint header is the footprint position
    blk = re.sub(r'\(at [-\d.]+ [-\d.]+( [-\d.]+)?\)', lambda m: '(at %.3f 50%s)' % (x, m.group(1) or ''), blk, count=1)
    body.append('\t' + blk)
    x += pitch
W = x
outline = ('\t(gr_rect (start 0 30) (end %.1f 70) (stroke (width 0.1) (type solid)) (fill no) (layer "Edge.Cuts"))' % W)
open(out, 'w').write(head + '\n' + '\n'.join(body) + '\n' + outline + '\n)\n')
print('wrote', out, 'width', W)
