"""Build kicad-library/footprint/Logo_Orwellian.kicad_mod from the Orwellian Industries logo footprint of the keyboard project
(/home/chithi/Desktop/keyboardProject/KiCAD/mcuBoard/mcu_DaughterBoard.kicad_pcb, footprint 'LOGO': 25 filled silk polygons, 19.4 x 21.4 mm).
Re-centred and scaled by S (default 2.95 -> 57 x 63 mm, about 24% of the board area). Polygons are on F.SilkS; the board script flips the footprint to the back."""
import re, sys
SRC = '/home/chithi/Desktop/keyboardProject/KiCAD/mcuBoard/mcu_DaughterBoard.kicad_pcb'
OUT = '/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/kicad-library/footprint/Logo_Orwellian.kicad_mod'
S = float(sys.argv[1]) if len(sys.argv) > 1 else 2.95
t = open(SRC).read()
i = t.index('(footprint "LOGO"')
depth, j = 0, i
while True:
    c = t[j]
    depth += (c == '(') - (c == ')')
    j += 1
    if depth == 0:
        break
fp = t[i:j]
polys = []
for m in re.finditer(r'\(fp_poly\s+\(pts(.*?)\)\s+\(stroke', fp, re.S):
    polys.append([(float(a), float(b)) for a, b in re.findall(r'\(xy ([-\d.e]+) ([-\d.e]+)\)', m.group(1))])
xs = [x for p in polys for x, y in p]; ys = [y for p in polys for x, y in p]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
o = ['(footprint "Logo_Orwellian"', '\t(version 20240108)', '\t(generator "pcbnew")', '\t(layer "F.Cu")',
     '\t(descr "Orwellian Industries logo, silkscreen only, %.1f x %.1f mm (scale %.2f of the keyboard-project logo)")' % ((max(xs) - min(xs)) * S, (max(ys) - min(ys)) * S, S),
     '\t(attr board_only exclude_from_pos_files exclude_from_bom)']
for p in polys:
    o.append('\t(fp_poly\n\t\t(pts')
    for x, y in p:
        o.append('\t\t\t(xy %.4f %.4f)' % ((x - cx) * S, -(y - cy) * S))
    o.append('\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill yes)\n\t\t(layer "F.SilkS")\n\t)')
o.append(')')
open(OUT, 'w').write('\n'.join(o) + '\n')
print(len(polys), 'polygons', (max(xs) - min(xs)) * S, (max(ys) - min(ys)) * S)
