#!/usr/bin/env python3
"""Replace 1x5 SWD header J6 by J6 (1x4 2.54 mm: SWDIO SWCLK NRST GND) + J7 (Tag-Connect TC2030-IDC with legs).
Guarded: refuses if J7 already exists. Patches MCU.kicad_sch in place."""
import re, sys, uuid, pathlib
P = pathlib.Path('/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/MCU.kicad_sch')
s = P.read_text()
if '"J7"' in s: sys.exit('J7 exists; refusing')
ROOT_UUID = 'feda53ed-537d-4f88-9436-c6075776255b'
SHEET_UUID = re.search(r'^\(uuid "([^"]+)"\)', s, re.M).group(1)
U = lambda: str(uuid.uuid4())
f = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')
lines = s.split('\n')
def drop(prefix):
    global lines
    n = len(lines); lines = [l for l in lines if not l.startswith(prefix)]; assert len(lines) == n - 1, prefix
for p in ['(wire (pts (xy 175.26 82.55) (xy 175.26 63.5))', '(wire (pts (xy 175.26 63.5) (xy 200.66 63.5))',
          '(wire (pts (xy 180.34 66.04) (xy 200.66 66.04))', '(wire (pts (xy 200.66 68.58) (xy 198.12 68.58))',
          '(label "NRST" (at 198.12 68.58', '(wire (pts (xy 200.66 71.12) (xy 198.12 71.12))', '(label "3V_AO" (at 198.12 71.12',
          '(symbol (lib_id "power:GND") (at 200.66 73.66', '(symbol (lib_id "Connector_Generic:Conn_01x05")', '(text "SWD: 1 SWDIO']:
    drop(p)
out = []
for l in lines:
    if l.startswith('(wire (pts (xy 165.1 82.55) (xy 175.26 82.55))'): l = l.replace('175.26', '172.72')
    if l.startswith('(wire (pts (xy 180.34 85.09) (xy 180.34 66.04))'): l = l.replace('(xy 180.34 66.04)', '(xy 180.34 76.2)')
    out.append(l)
s = '\n'.join(out)
# lib symbols: swap 01x05 for 01x04 and 01x06
i = s.index('(symbol "Connector_Generic:Conn_01x05"'); d = 0; j = i
while True:
    if s[j] == '(': d += 1
    elif s[j] == ')':
        d -= 1
        if d == 0: break
    j += 1
old = s[i:j + 1]
def conn(n):
    top, bot = 2.54 * (n - 1) / 2 + 1.27, -(2.54 * (n - 1) / 2 + 1.27)
    top = 2.54 * (n - 3) + 1.27 if False else None
    # KiCad generic: first pin at y = 2.54*(n-1)/2 rounded up to grid
    y0 = 2.54 * ((n - 1) // 2 + (1 if n % 2 == 0 else 0)) if False else None
    y0 = {4: 2.54, 6: 5.08}[n]
    t, b = y0 + 1.27, y0 - 2.54 * (n - 1) - 1.27
    h = old[:old.index('(symbol "Conn_01x05_1_1"')].replace('01x05', f'01x0{n}')
    h = h.replace('(at 0 7.62 0)', f'(at 0 {f(t+1.27)} 0)').replace('(at 0 -7.62 0)', f'(at 0 {f(b-1.27)} 0)')
    g = f'(symbol "Conn_01x0{n}_1_1" (rectangle (start -1.27 {f(t)}) (end 1.27 {f(b)}) (stroke (width 0.254) (type default)) (fill (type background))) '
    for k in range(n):
        y = y0 - 2.54 * k
        g += f'(rectangle (start -1.27 {f(y+0.127)}) (end 0 {f(y-0.127)}) (stroke (width 0.1524) (type default)) (fill (type none))) '
    for k in range(n):
        y = y0 - 2.54 * k
        g += (f'(pin passive line (at -5.08 {f(y)} 0) (length 3.81) (name "Pin_{k+1}" (effects (font (size 1.27 1.27)))) '
              f'(number "{k+1}" (effects (font (size 1.27 1.27))))) ')
    return h + g.rstrip() + ') (embedded_fonts no))', y0
c4, y4 = conn(4); c6, y6 = conn(6)
s = s[:i] + c4 + ' ' + c6 + s[j + 1:]
add = []
def wire(x1, y1, x2, y2): add.append(f'(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
def label(n, x, y, just): add.append(f'(label "{n}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify {just})) (uuid "{U()}"))')
def nc(x, y): add.append(f'(no_connect (at {f(x)} {f(y)}) (uuid "{U()}"))')
pw = [610]
def gnd(x, y):
    n = pw[0]; pw[0] += 1
    add.append(f'(symbol (lib_id "power:GND") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid "{U()}") '
               f'(property "Reference" "#PWR{n}" (at {f(x)} {f(y+3.81)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
               f'(property "Value" "GND" (at {f(x)} {f(y+5.08)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
               f'(pin "1" (uuid "{U()}")) (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "#PWR{n}") (unit 1)))))')
label('SWDIO', 172.72, 82.55, 'left bottom'); label('SWCLK', 167.64, 85.09, 'left bottom')
def conn_sym(lib, x, y, ref, val, fp, mfr, mpn, lcsc, n, bom, extra=''):
    return (f'(symbol (lib_id "Connector_Generic:{lib}") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom {bom}) (on_board yes) (dnp no) (uuid "{U()}") '
            f'(property "Reference" "{ref}" (at {f(x+3.81)} {f(y-1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
            f'(property "Value" "{val}" (at {f(x+3.81)} {f(y+1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
            f'(property "Footprint" "{fp}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
            f'(property "Manufacturer" "{mfr}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
            f'(property "MPN" "{mpn}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
            f'(property "LCSC" "{lcsc}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
            + ' '.join(f'(pin "{k}" (uuid "{U()}"))' for k in range(1, n + 1)) +
            f' (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "{ref}") (unit 1)))))')
# J7 TC2030 (6 pins) at (190.5, 66.04): pin k at y = 66.04 - (y6 - 2.54*(k-1)); 1 3V_AO 2 SWDIO 3 NRST 4 SWCLK 5 GND 6 SWO nc
jx, jy = 190.5, 66.04; px = jx - 5.08
py = lambda k: jy - (y6 - 2.54 * (k - 1))
for k, n in ((1, '3V_AO'), (2, 'SWDIO'), (3, 'NRST'), (4, 'SWCLK')):
    wire(px, py(k), px - 2.54, py(k)); label(n, px - 2.54, py(k), 'right bottom')
wire(px, py(5), px - 2.54, py(5)); gnd(px - 2.54, py(5)); nc(px, py(6))
add.append(conn_sym('Conn_01x06', jx, jy, 'J7', 'SWD_TC2030', 'DesktopSpeaker:Tag-Connect_TC2030-IDC-FP_2x03_P1.27mm_Vertical',
                    'Tag-Connect', 'TC2030-IDC', '', 6, 'no'))
# J6 (4 pins) at (228.6, 66.04): 1 SWDIO 2 SWCLK 3 NRST 4 GND
hx, hy = 228.6, 66.04; qx = hx - 5.08
qy = lambda k: hy - (y4 - 2.54 * (k - 1))
for k, n in ((1, 'SWDIO'), (2, 'SWCLK'), (3, 'NRST')):
    wire(qx, qy(k), qx - 2.54, qy(k)); label(n, qx - 2.54, qy(k), 'right bottom')
gnd(qx, qy(4))
add.append(conn_sym('Conn_01x04', hx, hy, 'J6', 'SWD', 'DesktopSpeaker:PinHeader_1x04_P2.54mm_Vertical',
                    'Ckmtw', 'B-2100S04P-A110', 'C124378', 4, 'yes'))
add.append(f'(text "SWD: J7 Tag-Connect TC2030-IDC (with legs; 6 SWO unused) and J6 4-pin 2.54 mm header share SWDIO, SWCLK, NRST\\nR160 holds PA14/BOOT0 low (nBOOT_SEL=1 ignores the pin)" (at 176.53 56.39 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
k = s.rindex('\n)')  # before final close of schematic
s = s[:k] + '\n' + '\n'.join(add) + s[k:]
P.write_text(s)
