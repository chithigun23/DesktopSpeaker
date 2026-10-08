#!/usr/bin/env python3
"""Crop a region of a 1:1 plotted board PDF around a footprint: v10_crop.py board.kicad_pcb plot.pdf REF half_w_mm half_h_mm out.png [dpi]
(the kicad-cli PDF plot is 1:1, page mm = board mm)."""
import re, subprocess, sys
b, pdf, ref, hw, hh, out = sys.argv[1:7]
dpi = int(sys.argv[7]) if len(sys.argv) > 7 else 500
s = open(b).read()
m = re.search(r'\(footprint "[^"]*"\s*\(layer "[^"]*"\)\s*\(uuid[^)]*\)\s*\(at ([-\d.]+) ([-\d.]+)[^)]*\)(?:(?!\(footprint ).)*?\(property "Reference" "%s"' % re.escape(ref), s, re.S)
x, y = float(m.group(1)), float(m.group(2))
k = dpi / 25.4
hw, hh = float(hw), float(hh)
subprocess.run(['pdftoppm', '-png', '-r', str(dpi), '-singlefile', '-x', str(int((x - hw) * k)), '-y', str(int((y - hh) * k)),
                '-W', str(int(2 * hw * k)), '-H', str(int(2 * hh * k)), pdf, out[:-4]], check=True)
print(ref, x, y, out)
