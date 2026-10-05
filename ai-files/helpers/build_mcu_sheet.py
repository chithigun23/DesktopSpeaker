#!/usr/bin/env python3
"""Create MCU.kicad_sch (U3 moved from root), regroup STM32 symbol pins functionally, wire root.

Run once from a clean tree. Guarded: refuses to run if MCU.kicad_sch exists.
"""
import re, sys, uuid, pathlib

ROOT = pathlib.Path('/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad')
SYM = ROOT / 'kicad-library/schematic/STM32G031K8T6.kicad_sym'
ROOT_SCH = ROOT / 'DesktopSpeaker.kicad_sch'
MCU_SCH = ROOT / 'MCU.kicad_sch'
if MCU_SCH.exists():
    sys.exit('MCU.kicad_sch exists; refusing')

ROOT_UUID = 'feda53ed-537d-4f88-9436-c6075776255b'
SHEET_UUID = str(uuid.uuid4())
U = lambda: str(uuid.uuid4())
f = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')

# ---------------------------------------------------------------- symbol
old = SYM.read_text()
props = old  # keep MPN/LCSC/manufacturer
LEFT = [  # (number, name, type)
    ('2', 'PC14', 'bidirectional'), ('3', 'PC15', 'bidirectional'),
    ('1', 'PB9', 'bidirectional'), ('7', 'PA0', 'bidirectional'), ('8', 'PA1', 'bidirectional'),
    ('9', 'PA2', 'bidirectional'), ('10', 'PA3', 'bidirectional'), ('11', 'PA4', 'bidirectional'),
    ('12', 'PA5', 'bidirectional'), ('13', 'PA6', 'bidirectional'), ('14', 'PA7', 'bidirectional'),
    ('15', 'PB0', 'bidirectional'), ('16', 'PB1', 'bidirectional'), ('17', 'PB2', 'bidirectional'),
    ('6', 'PF2-NRST', 'bidirectional')]
RIGHT = [
    ('24', 'PA13-SWDIO', 'bidirectional'), ('25', 'PA14-BOOT0', 'bidirectional'),
    ('31', 'PB7', 'bidirectional'), ('30', 'PB6', 'bidirectional'),
    ('23', 'PA12[PA10]', 'bidirectional'), ('22', 'PA11[PA9]', 'bidirectional'),
    ('21', 'PA10', 'bidirectional'), ('20', 'PC6', 'bidirectional'), ('19', 'PA9', 'bidirectional'),
    ('18', 'PA8', 'bidirectional'), ('29', 'PB5', 'bidirectional'), ('26', 'PA15', 'bidirectional'),
    ('27', 'PB3', 'bidirectional'), ('28', 'PB4', 'bidirectional'), ('32', 'PB8', 'bidirectional')]
eff = '(effects (font (size 1.27 1.27)))'
def pin(t, x, y, a, name, num, ln=2.54):
    return (f'(pin {t} line (at {f(x)} {f(y)} {a}) (length {ln}) (name "{name}" {eff}) (number "{num}" {eff}))')
pins = []
for k, (n, nm, t) in enumerate(LEFT):
    pins.append(pin(t, -25.4, 17.78 - 2.54 * k, 0, nm, n))
for k, (n, nm, t) in enumerate(RIGHT):
    pins.append(pin(t, 25.4, 17.78 - 2.54 * k, 180, nm, n))
pins.append(pin('power_in', -6.35, 24.13, 270, 'VDD/VDDA', '4'))
pins.append(pin('power_in', -6.35, -24.13, 90, 'VSS/VSSA', '5'))
hide = '(effects (font (size 1.27 1.27)) (hide yes))'
sym_props = (
    f'(property "Reference" "U" (at 0 -23.5 0) {eff}) '
    f'(property "Value" "STM32G031K8T6" (at 0 -26 0) {eff}) '
    f'(property "Footprint" "DesktopSpeaker:STM32G031K8T6" (at 0 0 0) {hide}) '
    f'(property "Datasheet" "${{KIPRJMOD}}/../ai-files/datasheets/STM32G031x4_x6_x8.pdf" (at 0 0 0) {hide}) '
    f'(property "Manufacturer" "STMicroelectronics" (at 0 0 0) {hide}) '
    f'(property "MPN" "STM32G031K8T6" (at 0 0 0) {hide}) '
    f'(property "LCSC Part" "C432203" (at 0 0 0) {hide}) '
    f'(property "Description" "Arm Cortex-M0+ 64 MHz, 64 KB flash, LQFP32; pins grouped by function (inputs/analog left, outputs/buses/SWD right)" (at 0 0 0) {hide}) ')
body = ('(symbol "STM32G031K8T6_0_1" (rectangle (start -22.86 21.59) (end 22.86 -21.59) '
        '(stroke (width 0.254) (type default)) (fill (type background)))) ')
unit = '(symbol "STM32G031K8T6_1_1" ' + ' '.join(pins) + ')'
lib = ('(kicad_symbol_lib (version 20250120) (generator "kicad_symbol_editor") '
       '(symbol "STM32G031K8T6:STM32G031K8T6" (pin_names (offset 1.016)) (in_bom yes) (on_board yes) '
       + sym_props + body + unit + ' (embedded_fonts no)))\n')
lib_text = lib
# embedded form (matches how KiCad stores other embedded symbols)
emb = ('(symbol "STM32G031K8T6:STM32G031K8T6" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
       '(in_pos_files yes) (duplicate_pin_numbers_are_jumpers no) ' + sym_props + body + unit + ' (embedded_fonts no))')

# --------------------------------------------------- generic symbol blocks
def grab(text, name):
    i = text.index(f'(symbol "{name}"'); d = 0; j = i
    while True:
        if text[j] == '(': d += 1
        elif text[j] == ')':
            d -= 1
            if d == 0: break
        j += 1
    return text[i:j + 1]
fg = (ROOT / 'Fuel_Gauge_Power.kicad_sch').read_text()
PD_C = grab(fg, 'PD_C:PD_C'); PD_R = grab(fg, 'PD_R:PD_R'); GND = grab(fg, 'power:GND')
c1x05 = (pathlib.Path('/home/chithi/kicad-libs/symbols/Connector_Generic.kicad_symdir/Conn_01x05.kicad_sym').read_text())
bc = (ROOT / 'Battery_Charger.kicad_sch').read_text()
conn3 = grab(bc, 'Connector_Generic:Conn_01x03')
conn5 = (conn3.replace('01x03', '01x05').replace('Conn_01x03', 'Conn_01x05')
         .replace('(rectangle (start -1.27 3.81) (end 1.27 -3.81)', '(rectangle (start -1.27 6.35) (end 1.27 -6.35)')
         .replace('(at 0 5.08 0)', '(at 0 7.62 0)').replace('(at 0 -5.08 0)', '(at 0 -7.62 0)'))
# rebuild unit graphics/pins for 5 pins
i = conn5.index('(symbol "Conn_01x05_1_1"')
head = conn5[:i]
tick = lambda y: f'(rectangle (start -1.27 {f(y+0.127)}) (end 0 {f(y-0.127)}) (stroke (width 0.1524) (type default)) (fill (type none)))'
ys = [5.08, 2.54, 0, -2.54, -5.08]
unit5 = ('(symbol "Conn_01x05_1_1" (rectangle (start -1.27 6.35) (end 1.27 -6.35) (stroke (width 0.254) (type default)) (fill (type background))) '
         + ' '.join(tick(y) for y in ys) + ' '
         + ' '.join(f'(pin passive line (at -5.08 {f(y)} 0) (length 3.81) (name "Pin_{n+1}" (effects (font (size 1.27 1.27)))) (number "{n+1}" (effects (font (size 1.27 1.27)))))' for n, y in enumerate(ys))
         + ')')
conn5 = head + unit5 + ' (embedded_fonts no))'

# ---------------------------------------------------------- child sheet
items = []
def wire(x1, y1, x2, y2): items.append(f'(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
def junc(x, y): items.append(f'(junction (at {f(x)} {f(y)}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')
def nc(x, y): items.append(f'(no_connect (at {f(x)} {f(y)}) (uuid "{U()}"))')
def label(n, x, y, just):
    items.append(f'(label "{n}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify {just})) (uuid "{U()}"))')
def hlabel(n, shape, x, y, just):
    items.append(f'(hierarchical_label "{n}" (shape {shape}) (at {f(x)} {f(y)} 0) (effects (font (size 1.0 1.0)) (justify {just})) (uuid "{U()}"))')
def text(s, x, y):
    items.append(f'(text "{s}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
pw = [601]
def gnd(x, y):
    n = pw[0]; pw[0] += 1
    items.append(f'(symbol (lib_id "power:GND") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "#PWR{n}" (at {f(x)} {f(y+3.81)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                 f'(property "Value" "GND" (at {f(x)} {f(y+5.08)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                 f'(pin "1" (uuid "{U()}")) (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "#PWR{n}") (unit 1)))))')
def passive(lib, ref, val, fp, mpn, mfr, lcsc, x, y, ds=None):
    d = f'(property "Datasheet" "{ds}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) ' if ds else ''
    items.append(f'(symbol (lib_id "{lib}") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "{ref}" (at {f(x+1.27)} {f(y-1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
                 f'(property "Value" "{val}" (at {f(x+1.27)} {f(y+1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
                 f'(property "Footprint" "{fp}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
                 f'(property "MPN" "{mpn}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
                 f'(property "Manufacturer" "{mfr}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
                 f'(property "LCSC" "{lcsc}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) ' + d +
                 f'(pin "1" (uuid "{U()}")) (pin "2" (uuid "{U()}")) '
                 f'(instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "{ref}") (unit 1)))))')

OX, OY = 139.7, 100.33
pyl = lambda k: OY - 17.78 + 2.54 * k   # pin y for slot k
XL, XR = OX - 25.4, OX + 25.4
SX1, SX2 = XR + 10.16, XR + 15.24
# U3 (same UUID, pin UUIDs and properties as in root)
root_txt = ROOT_SCH.read_text().split('\n')
iu = [i for i, l in enumerate(root_txt) if l.startswith('(symbol (lib_id "STM32G031K8T6:STM32G031K8T6")')][0]
u3 = root_txt[iu]
u3 = u3.replace('(at 353.06 77.47 0)', f'(at {f(OX)} {f(OY)} 0)')
u3 = u3.replace('(at 353.06 102.87 0)', f'(at {f(OX)} {f(OY+23.5)} 0)').replace('(at 353.06 105.41 0)', f'(at {f(OX)} {f(OY+26.04)} 0)')
u3 = u3.replace('(path "/feda53ed-537d-4f88-9436-c6075776255b" (reference "U3")', f'(path "/{ROOT_UUID}/{SHEET_UUID}" (reference "U3")')
assert SHEET_UUID in u3 and f'(at {f(OX)} {f(OY)} 0)' in u3
items.append(u3)

LP = 45.72      # left port x
RP = 215.9      # right port x
# ---- left: inputs
left_sig = ['PD_PLUG_EVENT', 'CHG_INT', 'PD_SINK_EN', 'GAUGE_ALRT_N']
for k, n in enumerate(left_sig):
    y = pyl(k); wire(LP, y, XL, y); hlabel(n, 'input', LP, y, 'left bottom')
for k in range(4, 14): nc(XL, pyl(k))           # PA1..PB2 reserved
# NRST (slot 14): wire to C162 + label
yn = pyl(14)
wire(XL, yn, 106.68, yn)
label('NRST', 109.22, yn, 'left bottom')
passive('PD_C:PD_C', 'C162', '100nF', 'DesktopSpeaker:PD_C_0603', 'CL10B104KB8NNNC', 'Samsung Electro-Mechanics', 'C1591', 106.68, yn + 3.81,
        '${KIPRJMOD}/../ai-files/datasheets/Samsung_MLCC_LCSC_C1591_C1711.pdf')
gnd(106.68, yn + 7.62)
# ---- VDD rail with decoupling
ry = 66.04
vx = OX - 6.35
C160X, C161X = vx - 7.62, vx - 20.32
wire(vx, OY - 24.13, vx, ry)
wire(vx, ry, C160X, ry); junc(C160X, ry)
wire(C160X, ry, C161X, ry); junc(C161X, ry)
wire(C161X, ry, LP, ry)
hlabel('3V_AO', 'input', LP, ry, 'left bottom')
passive('PD_C:PD_C', 'C160', '100nF', 'DesktopSpeaker:PD_C_0603', 'CL10B104KB8NNNC', 'Samsung Electro-Mechanics', 'C1591', C160X, ry + 3.81,
        '${KIPRJMOD}/../ai-files/datasheets/Samsung_MLCC_LCSC_C1591_C1711.pdf')
gnd(C160X, ry + 7.62)
passive('PD_C:PD_C', 'C161', '4.7uF', 'DesktopSpeaker:PD_C_0603', 'CL10A475KO8NNNC', 'Samsung Electro-Mechanics', 'C19666', C161X, ry + 3.81)
gnd(C161X, ry + 7.62)
# ---- VSS
wire(vx, OY + 24.13, OX - 12.7, OY + 24.13)
gnd(OX - 12.7, OY + 24.13)
# ---- right: SWD
jx, jy = 205.74, 68.58            # J6 centre; pin1 at (175.26, 63.5)
y0, y1 = pyl(0), pyl(1)
wire(XR, y0, SX1, y0); wire(SX1, y0, SX1, jy - 5.08); wire(SX1, jy - 5.08, jx - 5.08, jy - 5.08)
wire(XR, y1, SX2, y1); wire(SX2, y1, SX2, jy - 2.54); wire(SX2, jy - 2.54, jx - 5.08, jy - 2.54)
# BOOT0 pull-down on the SWCLK line
wire(SX2, 76.2, SX2 + 5.08, 76.2); junc(SX2, 76.2)
passive('PD_R:PD_R', 'R160', '100k', 'DesktopSpeaker:PD_R_0603', 'RC0603FR-07100KL', 'YAGEO', 'C14675', SX2 + 5.08, 80.01,
        '${KIPRJMOD}/../ai-files/datasheets/Yageo_RC0603FR_series.pdf')
gnd(SX2 + 5.08, 83.82)
# header pins 3 NRST, 4 3V_AO, 5 GND
wire(jx - 5.08, jy, jx - 7.62, jy); label('NRST', jx - 7.62, jy, 'right bottom')
wire(jx - 5.08, jy + 2.54, jx - 7.62, jy + 2.54); label('3V_AO', jx - 7.62, jy + 2.54, 'right bottom')
gnd(jx - 5.08, jy + 5.08)
items.append(f'(symbol (lib_id "Connector_Generic:Conn_01x05") (at {f(jx)} {f(jy)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}") '
             f'(property "Reference" "J6" (at {f(jx+3.81)} {f(jy-1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
             f'(property "Value" "SWD" (at {f(jx+3.81)} {f(jy+1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
             f'(property "Footprint" "DesktopSpeaker:PinHeader_1x05_P2.54mm_Vertical" (at {f(jx)} {f(jy)} 0) (hide yes) (effects (font (size 1 1)))) '
             f'(property "Manufacturer" "XYECONN" (at {f(jx)} {f(jy)} 0) (hide yes) (effects (font (size 1 1)))) '
             f'(property "MPN" "XY-MTP254-1X5" (at {f(jx)} {f(jy)} 0) (hide yes) (effects (font (size 1 1)))) '
             f'(property "LCSC" "C54110162" (at {f(jx)} {f(jy)} 0) (hide yes) (effects (font (size 1 1)))) '
             + ' '.join(f'(pin "{n}" (uuid "{U()}"))' for n in range(1, 6)) +
             f' (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "J6") (unit 1)))))')
text('SWD: 1 SWDIO, 2 SWCLK, 3 NRST, 4 3V_AO (VTref), 5 GND\\nR160 holds PA14/BOOT0 low (nBOOT_SEL=1 ignores the pin)', jx - 20.32, 58.42)
# ---- right: buses and outputs
right_sig = [(2, 'CTRL_SDA', 'bidirectional'), (3, 'CTRL_SCL', 'bidirectional'), (4, 'PDCTRL_SDA', 'bidirectional'),
             (5, 'PDCTRL_SCL', 'bidirectional'), (6, 'CHG_SYS_ENABLE', 'output'), (7, 'CHG_ENABLE', 'output'),
             (8, 'BT_FORCE_PWM', 'output'), (9, 'BT_PWR_EN', 'output'), (10, '5V_LOGIC_EN', 'output')]
for k, n, shp in right_sig:
    y = pyl(k); wire(XR, y, RP, y); hlabel(n, shp, RP, y, 'right bottom')
for k in range(11, 15): nc(XR, pyl(k))
text('Reserved (no-connect): see ai-files/reports/mcu-pin-allocation.md', 45.72, 140.97)
text('3V_AO supply: 100nF + 4.7uF at VDD/VDDA (DS12992 fig. 13); NRST 100nF, internal pull-up', 45.72, 60.96)

lib_syms = '(lib_symbols ' + ' '.join([emb, PD_C, PD_R, GND, conn5]) + ')'
hdr = ['(kicad_sch', '(version 20260306)', '(generator "eeschema")', '(generator_version "10.0")',
       f'(uuid "{SHEET_UUID}")', '(paper "A4")',
       '(title_block (title "MCU and programming") (rev "0.1") (comment 1 "STM32G031K8T6: supply, reset/boot, SWD and connections to captured power blocks"))',
       lib_syms]
MCU_SCH.write_text('\n'.join(hdr + items) + '\n)\n')
SYM.write_text(lib_text)

# ---------------------------------------------------------------- root
rl = root_txt
del rl[iu]
rt = '\n'.join(rl)
# drop the STM32 embedded lib symbol
i = rt.index('(symbol "STM32G031K8T6:STM32G031K8T6"'); d = 0; j = i
while True:
    if rt[j] == '(': d += 1
    elif rt[j] == ')':
        d -= 1
        if d == 0: break
    j += 1
rt = rt[:i].rstrip(' ') + rt[j + 1:].lstrip(' ') if False else rt[:i] + rt[j + 1:]
rt = rt.replace('(lib_symbols  ', '(lib_symbols ')
lines = rt.rstrip('\n').split('\n')
drop = [(146.05, 154.94), (146.05, 162.56), (146.05, 170.18), (146.05, 177.8), (166.37, 175.26)]
out = []
for l in lines:
    m = re.match(r'\(no_connect \(at ([\d.]+) ([\d.]+)\)', l)
    if m and (float(m.group(1)), float(m.group(2))) in drop: continue
    if l.startswith('(wire (pts (xy 290.83 147.32) (xy 295.91 147.32))'):
        l = l.replace('(xy 295.91 147.32)', '(xy 320.04 147.32)')
    if l.startswith('(wire (pts (xy 290.83 195.58) (xy 295.91 195.58))'):
        l = l.replace('(xy 295.91 195.58)', '(xy 320.04 195.58)')
    out.append(l)
assert len(out) == len(lines) - 5
MX, MY, MW, MH = 320.04, 139.7, 50.8, 66.04
left_pins = [('3V_AO', 147.32), ('PD_PLUG_EVENT', 157.48), ('CHG_INT', 162.56), ('PD_SINK_EN', 167.64), ('GAUGE_ALRT_N', 195.58)]
right_pins = [('CTRL_SDA', 'bidirectional', 154.94), ('CTRL_SCL', 'bidirectional', 160.02), ('PDCTRL_SDA', 'bidirectional', 165.1),
              ('PDCTRL_SCL', 'bidirectional', 170.18), ('CHG_SYS_ENABLE', 'output', 177.8), ('CHG_ENABLE', 'output', 182.88),
              ('BT_FORCE_PWM', 'output', 187.96), ('BT_PWR_EN', 'output', 193.04), ('5V_LOGIC_EN', 'output', 198.12)]
sp = ' '.join(f'(pin "{n}" input (at {f(MX)} {f(y)} 180) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))' for n, y in left_pins)
sp += ' ' + ' '.join(f'(pin "{n}" {t} (at {f(MX+MW)} {f(y)} 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}"))' for n, t, y in right_pins)
sheet = (f'(sheet (at {f(MX)} {f(MY)}) (size {f(MW)} {f(MH)}) (stroke (width 0) (type default)) (fill (color 255 255 255 0)) (uuid "{SHEET_UUID}") '
         f'(property "Sheet name" "MCU" (at {f(MX)} {f(MY-1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
         f'(property "Sheet file" "MCU.kicad_sch" (at {f(MX)} {f(MY+MH)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
         + sp + f' (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}" (page "7")))))')
new = [sheet]
def rw(x1, y1, x2, y2): new.append(f'(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
def rl_(n, x, y, just): new.append(f'(label "{n}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify {just})) (uuid "{U()}"))')
for n, y in left_pins[1:4]:   # stub + label on MCU side
    rw(MX, y, MX - 5.08, y); rl_(n, MX - 5.08, y, 'right bottom')
for n, t, y in right_pins:
    rw(MX + MW, y, MX + MW + 5.08, y); rl_(n, MX + MW + 5.08, y, 'left bottom')
# remote stubs on PD / charger sides
for n, y in [('PD_PLUG_EVENT', 154.94), ('PD_SINK_EN', 162.56), ('PDCTRL_SCL', 170.18), ('PDCTRL_SDA', 177.8)]:
    rw(146.05, y, 148.59, y); rl_(n, 148.59, y, 'left bottom')
rw(166.37, 175.26, 161.29, 175.26); rl_('CHG_SYS_ENABLE', 161.29, 175.26, 'right bottom')
assert out[-1] == ')'
ROOT_SCH.write_text('\n'.join(out[:-1] + new + [')']))
print('sheet uuid', SHEET_UUID)
