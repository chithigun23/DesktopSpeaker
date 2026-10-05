#!/usr/bin/env python3
"""Create USB_Audio.kicad_sch (U2 PCM2902C moved from root), regroup the PCM2902C symbol, wire J1/D1 data path in root.

Guarded: refuses to run if USB_Audio.kicad_sch exists.  Run from a clean tree (git checkout the three touched files to redo).
"""
import re, sys, uuid, pathlib

ROOT = pathlib.Path('/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad')
SYM = ROOT / 'kicad-library/schematic/PCM2902CDBR.kicad_sym'
ROOT_SCH = ROOT / 'DesktopSpeaker.kicad_sch'
OUT = ROOT / 'USB_Audio.kicad_sch'
if OUT.exists():
    sys.exit('USB_Audio.kicad_sch exists; refusing')

ROOT_UUID = 'feda53ed-537d-4f88-9436-c6075776255b'
SHEET_UUID = str(uuid.uuid4())
U = lambda: str(uuid.uuid4())
f = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')

# ------------------------------------------------------------------ symbol (lib coords, y up)
eff = '(effects (font (size 1.27 1.27)))'
def pin(t, x, y, a, name, num, ln=2.54):
    return (f'(pin {t} line (at {f(x)} {f(y)} {a}) (length {f(ln)}) (name "{name}" {eff}) (number "{num}" {eff}))')
XL, XR, YB = -35.56, 35.56, -48.26
LEFT = [('2', 'D-', 'bidirectional', 17.78), ('1', 'D+', 'bidirectional', 10.16),
        ('27', 'VDDI', 'power_out', 2.54), ('8', 'SEL0', 'input', 0), ('9', 'SEL1', 'input', -2.54),
        ('5', 'HID0', 'input', -10.16), ('6', 'HID1', 'input', -12.7), ('7', 'HID2', 'input', -15.24),
        ('24', 'DIN', 'input', -17.78), ('12', 'VINL', 'input', -22.86), ('13', 'VINR', 'input', -25.4),
        ('10', 'VCCCI', 'passive', -30.48), ('14', 'VCOM', 'passive', -35.56)]
RIGHT = [('28', '~{SSPND}', 'output', 17.78), ('25', 'DOUT', 'output', 15.24), ('21', 'XTI', 'input', 12.7),
         ('20', 'XTO', 'output', 0), ('16', 'VOUTL', 'output', -15.24), ('15', 'VOUTR', 'output', -27.94)]
BOTTOM = [('4', 'DGNDU', 'power_in', -30.48), ('26', 'DGND', 'power_in', -25.4), ('11', 'AGNDC', 'power_in', -20.32),
          ('18', 'AGNDP', 'power_in', -15.24), ('22', 'AGNDX', 'power_in', -10.16),
          ('23', 'VCCXI', 'passive', 10.16), ('19', 'VCCP2I', 'passive', 20.32), ('17', 'VCCP1I', 'passive', 30.48)]
pins = []
for n, nm, t, y in LEFT: pins.append(pin(t, XL, y, 0, nm, n))
for n, nm, t, y in RIGHT: pins.append(pin(t, XR, y, 180, nm, n))
for n, nm, t, x in BOTTOM: pins.append(pin(t, x, YB, 90, nm, n))
pins.append(pin('power_in', -22.86, 22.86, 270, 'VBUS', '3'))
hide = '(effects (font (size 1.27 1.27)) (hide yes))'
sym_props = (
    f'(property "Reference" "U" (at 0 -48.5 0) {eff}) '
    f'(property "Value" "PCM2902CDBR" (at 0 -51 0) {eff}) '
    f'(property "Footprint" "DesktopSpeaker:PCM2902CDBR" (at 0 0 0) {hide}) '
    f'(property "Datasheet" "${{KIPRJMOD}}/../ai-files/datasheets/PCM2902C.pdf" (at 0 0 0) {hide}) '
    f'(property "Manufacturer" "Texas Instruments" (at 0 0 0) {hide}) '
    f'(property "MPN" "PCM2902CDBR" (at 0 0 0) {hide}) '
    f'(property "LCSC Part" "C2651869" (at 0 0 0) {hide}) '
    f'(property "Description" "USB full-speed stereo audio codec with S/PDIF, SSOP-28; pins grouped by function, pin numbers unchanged" (at 0 0 0) {hide}) ')
body = ('(symbol "PCM2902CDBR_0_1" (rectangle (start -33.02 20.32) (end 33.02 -45.72) '
        '(stroke (width 0.254) (type default)) (fill (type background)))) ')
unit = '(symbol "PCM2902CDBR_1_1" ' + ' '.join(pins) + ')'
lib_text = ('(kicad_symbol_lib (version 20250120) (generator "kicad_symbol_editor") '
            '(symbol "PCM2902CDBR:PCM2902CDBR" (pin_names (offset 1.016)) (in_bom yes) (on_board yes) '
            + sym_props + body + unit + ' (embedded_fonts no)))\n')
emb = ('(symbol "PCM2902CDBR:PCM2902CDBR" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
       '(in_pos_files yes) (duplicate_pin_numbers_are_jumpers no) ' + sym_props + body + unit + ' (embedded_fonts no))')

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
pdsrc = (ROOT / 'USB_PD.kicad_sch').read_text(); FLAG = grab(pdsrc, 'PD_PWR_FLAG:PD_PWR_FLAG')
PD_C = grab(fg, 'PD_C:PD_C'); PD_R = grab(fg, 'PD_R:PD_R'); GND = grab(fg, 'power:GND')
xt = pathlib.Path('/home/chithi/kicad-libs/symbols/Device.kicad_symdir/Crystal_GND24.kicad_sym').read_text()
XTAL = grab(xt, 'Crystal_GND24').replace('(symbol "Crystal_GND24"', '(symbol "Device:Crystal_GND24"', 1)
XTAL = re.sub(r'\(symbol "Crystal_GND24_', '(symbol "Crystal_GND24_', XTAL)
XTAL = XTAL.replace(')\n\t)', ')\n\t)')

# ------------------------------------------------------------------ child sheet
OX, OY = 127.0, 101.6
P = lambda lx, ly: (OX + lx, OY - ly)
items = []
def wire(a, b):
    (x1, y1), (x2, y2) = P(*a), P(*b)
    items.append(f'(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
def junc(a):
    x, y = P(*a); items.append(f'(junction (at {f(x)} {f(y)}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')
def nc(a):
    x, y = P(*a); items.append(f'(no_connect (at {f(x)} {f(y)}) (uuid "{U()}"))')
def hlabel(n, shape, a, just):
    x, y = P(*a)
    items.append(f'(hierarchical_label "{n}" (shape {shape}) (at {f(x)} {f(y)} 0) (effects (font (size 1.0 1.0)) (justify {just})) (uuid "{U()}"))')
def text(s, a):
    x, y = P(*a)
    items.append(f'(text "{s}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
pw = [701]
def gnd(a):
    x, y = P(*a); n = pw[0]; pw[0] += 1
    items.append(f'(symbol (lib_id "power:GND") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "#PWR{n}" (at {f(x)} {f(y+3.81)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                 f'(property "Value" "GND" (at {f(x)} {f(y+5.08)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                 f'(pin "1" (uuid "{U()}")) (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "#PWR{n}") (unit 1)))))')
def passive(lib, ref, val, fp, mpn, mfr, lcsc, a, rot, tpos, ds=None, just='left'):
    """a: pin-centre (lib coords). rot 0 vertical, 90 horizontal. tpos: ((x,y),(x,y)) absolute-lib offsets for ref/value."""
    x, y = P(*a)
    d = f'(property "Datasheet" "{ds}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) ' if ds else ''
    (rx, ry), (vx, vy) = [P(*t) for t in tpos]
    j = f'(justify {just})' if just else ''
    tang = 270 if rot == 90 else 0
    items.append(f'(symbol (lib_id "{lib}") (at {f(x)} {f(y)} {rot}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "{ref}" (at {f(rx)} {f(ry)} {tang}) (effects (font (size 1.27 1.27)) {j})) '
                 f'(property "Value" "{val}" (at {f(vx)} {f(vy)} {tang}) (effects (font (size 1.27 1.27)) {j})) '
                 f'(property "Footprint" "{fp}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
                 f'(property "MPN" "{mpn}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
                 f'(property "Manufacturer" "{mfr}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
                 f'(property "LCSC" "{lcsc}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) ' + d +
                 f'(pin "1" (uuid "{U()}")) (pin "2" (uuid "{U()}")) '
                 f'(instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "{ref}") (unit 1)))))')
R0603 = 'DesktopSpeaker:PD_R_0603'
def res(ref, val, mpn, mfr, lcsc, a, horizontal):
    x, y = a
    if horizontal:
        passive('PD_R:PD_R', ref, val, R0603, mpn, mfr, lcsc, a, 90, ((x, y + 4.2), (x, y + 2.6)), just=None)
    else:
        passive('PD_R:PD_R', ref, val, R0603, mpn, mfr, lcsc, a, 0, ((x + 1.27, y + 1.27), (x + 1.27, y - 1.27)))
def cap(ref, val, fp, mpn, mfr, lcsc, a, horizontal=False):
    x, y = a
    if horizontal:
        passive('PD_C:PD_C', ref, val, fp, mpn, mfr, lcsc, a, 90, ((x, y + 4.2), (x, y + 2.6)), just=None)
    else:
        passive('PD_C:PD_C', ref, val, fp, mpn, mfr, lcsc, a, 0, ((x + 1.27, y + 1.27), (x + 1.27, y - 1.27)))
SAM = 'Samsung Electro-Mechanics'
C1U = ('1uF', 'DesktopSpeaker:PD_C_0805', 'CL21B105KBFNNNE', SAM, 'C28323')
C10U = ('10uF', 'DesktopSpeaker:PD_C_0805', 'CL21B106KPQNNNE', SAM, 'C32635')
C22P = ('33pF', 'DesktopSpeaker:PD_C_0603', 'CL10C330JB8NNNC', SAM, 'C1663')
C47U = ('4.7uF', 'DesktopSpeaker:PD_C_1206', 'CL31B475KBHNNNE', SAM, 'C51205')
RYAG = lambda mpn, lcsc: (mpn, 'YAGEO', lcsc)

# --- U2 instance (same UUID/pin UUIDs as in root)
root_txt = ROOT_SCH.read_text().split('\n')
iu = [i for i, l in enumerate(root_txt) if l.startswith('(symbol (lib_id "PCM2902CDBR:PCM2902CDBR")')][0]
u2 = root_txt[iu]
ux, uy = OX, OY
u2 = u2.replace('(at 271.78 76.2 0)', f'(at {f(ux)} {f(uy)} 0)')
u2 = u2.replace('(at 271.78 99.06 0)', f'(at {f(ux)} {f(uy+48.26)} 0)').replace('(at 271.78 101.6 0)', f'(at {f(ux)} {f(uy+50.8)} 0)')
u2 = u2.replace('(at 271.78 76.2 0)', f'(at {f(ux)} {f(uy)} 0)')
u2 = u2.replace('"https://www.lcsc.com/datasheet/C2651869.pdf"', '"${KIPRJMOD}/../ai-files/datasheets/PCM2902C.pdf"')
u2 = u2.replace('(path "/feda53ed-537d-4f88-9436-c6075776255b" (reference "U2")', f'(path "/{ROOT_UUID}/{SHEET_UUID}" (reference "U2")')
assert SHEET_UUID in u2 and '271.78' not in u2
items.append(u2)

LP, RP = -70.0, 88.9
# ---- VBUS filter: 5V_LOGIC -> R170 2.2R -> VBUS, C170 1uF (datasheet fig. 39)
yn = 33.02
wire((-22.86, 22.86), (-22.86, yn)); wire((-22.86, yn), (-33.02, yn)); junc((-33.02, yn))
wire((-33.02, yn), (-36.83, yn)); wire((-44.45, yn), (LP, yn))
hlabel('5V_LOGIC', 'input', (LP, yn), 'left bottom')
res('R170', '2.2', *RYAG('RC0603FR-072R2L', 'C112307'), (-40.64, yn), True)
cap('C170', *C1U, (-33.02, yn - 3.81)); gnd((-33.02, yn - 7.62))
# ---- USB data: 22R series, 1.5k D+ pull-up to VDDI (datasheet fig. 39: no internal pull-up)
for ref, y in (('R172', 17.78), ('R171', 10.16)):
    wire((XL, y), (-38.1, y)); wire((-45.72, y), (LP, y))
res('R172', '22', 'RC0603FR-0722RL', 'YAGEO', 'C107701', (-41.91, 17.78), True)
res('R171', '22', 'RC0603FR-0722RL', 'YAGEO', 'C107701', (-41.91, 10.16), True)
hlabel('USB_DN', 'bidirectional', (LP, 17.78), 'left bottom')
hlabel('USB_DP', 'bidirectional', (LP, 10.16), 'left bottom')
xn = -45.72
junc((xn, 10.16))
res('R173', '1.5k', 'RC0603FR-071K5L', 'YAGEO', 'C114668', (xn, 6.35), False)
wire((XL, 2.54), (xn, 2.54)); wire((xn, 2.54), (xn, -2.54))
wire((XL, 0), (xn, 0)); wire((XL, -2.54), (xn, -2.54))
for y in (2.54, 0, -2.54): junc((xn, y))
cap('C171', *C1U, (xn, -6.35)); gnd((xn, -10.16))
# PWR_FLAG: VBUS node is fed through R170, so no power output sits on this net
wire((-22.86, 27.94), (-20.32, 27.94)); junc((-22.86, 27.94))
fx, fy = P(-20.32, 27.94)
items.append(f'(symbol (lib_id "PD_PWR_FLAG:PD_PWR_FLAG") (at {f(fx)} {f(fy)} 270) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid "{U()}") '
             f'(property "Reference" "#FLG801" (at {f(fx)} {f(fy)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
             f'(property "Value" "PWR_FLAG" (at {f(fx+2.54)} {f(fy-3.0)} 0) (effects (font (size 1 1)) (hide yes))) '
             f'(property "Footprint" "" (at {f(fx)} {f(fy)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
             f'(property "Datasheet" "" (at {f(fx)} {f(fy)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
             f'(pin "1" (uuid "{U()}")) (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "#FLG801") (unit 1)))))')
# ---- unused pins
for n, nm, t, y in LEFT:
    if nm in ('HID0', 'HID1', 'HID2', 'DIN', 'VINL', 'VINR'): nc((XL, y))
nc((XR, 17.78)); nc((XR, 15.24))
# ---- VCCCI / VCOM (10uF) on the left
wire((XL, -30.48), (-55.88, -30.48)); cap('C175', *C10U, (-55.88, -34.29)); gnd((-55.88, -38.1))
wire((XL, -35.56), (xn, -35.56)); cap('C176', *C10U, (xn, -39.37)); gnd((xn, -43.18))
# ---- bottom: three 1uF supplies, grounds
for k, (x, ref) in enumerate(((10.16, 'C172'), (20.32, 'C173'), (30.48, 'C174'))):
    wire((x, YB), (x, YB - 2.54)); cap(ref, *C1U, (x, YB - 2.54 - 3.81)); gnd((x, YB - 2.54 - 7.62))
gx = [-30.48, -25.4, -20.32, -15.24, -10.16]
for x in gx: wire((x, YB), (x, YB - 2.54))
wire((gx[0], YB - 2.54), (gx[-1], YB - 2.54))
for x in gx[1:-1]: junc((x, YB - 2.54))
gnd((-20.32, YB - 2.54))
# ---- crystal
y1, y2 = 12.7, 0.0
x1, xr, cx, x2, xt = 43.18, 53.34, 71.12, 60.96, 83.82
wire((XR, y1), (cx - 3.81, y1)); junc((x1, y1)); junc((xr, y1))
cap('C177', *C22P, (x1, y1 - 3.81)); gnd((x1, y1 - 7.62))
wire((XR, y2), (xt, y2)); wire((xt, y2), (xt, y1)); wire((xt, y1), (cx + 3.81, y1))
junc((xr, y2)); junc((x2, y2))
wire((xr, y1), (xr, 10.16)); res('R174', '1M', 'RC0603FR-071ML', 'YAGEO', 'C105578', (xr, 6.35), False); wire((xr, 2.54), (xr, y2))
cap('C178', *C22P, (x2, y2 - 3.81)); gnd((x2, y2 - 7.62))
items.append(f'(symbol (lib_id "Device:Crystal_GND24") (at {f(OX+cx)} {f(OY-y1)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}") '
             f'(property "Reference" "Y170" (at {f(OX+cx+4.445)} {f(OY-y1-5.08)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
             f'(property "Value" "12MHz" (at {f(OX+cx+4.445)} {f(OY-y1-3.175)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
             f'(property "Footprint" "DesktopSpeaker:Crystal_SMD_3225-4Pin_3.2x2.5mm" (at {f(OX+cx)} {f(OY-y1)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
             f'(property "MPN" "X322512MSB4SI" (at {f(OX+cx)} {f(OY-y1)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
             f'(property "Manufacturer" "YXC" (at {f(OX+cx)} {f(OY-y1)} 0) (hide yes) (effects (font (size 1 1)))) '
             f'(property "LCSC" "C9002" (at {f(OX+cx)} {f(OY-y1)} 0) (hide yes) (effects (font (size 1 1)))) '
             + ' '.join(f'(pin "{n}" (uuid "{U()}"))' for n in range(1, 5)) +
             f' (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "Y170") (unit 1)))))')
gnd((cx, y1 - 5.08))
# ---- analogue outputs: 4.7uF coupling + 100k bleed, ports right
for y, nm, cref, rref in ((-15.24, 'USB_AUDIO_L', 'C186', 'R175'), (-27.94, 'USB_AUDIO_R', 'C187', 'R176')):
    wire((XR, y), (39.37, y)); cap(cref, *C47U, (43.18, y), horizontal=True)
    wire((46.99, y), (RP, y)); junc((53.34, y))
    res(rref, '100k', 'RC0603FR-07100KL', 'YAGEO', 'C14675', (53.34, y - 3.81), False)
    gnd((53.34, y - 7.62))
    hlabel(nm, 'output', (RP, y), 'right bottom')
# ---- notes
text('Supply: 5V_LOGIC (U14 TPS63802, 4.60-5.06 V worst case) feeds VBUS through 2.2R/1uF. DS range 4.35-5.25 V, 56 mA typ / 67 mA max, 250 uA suspend.', (-70, 48))
text('Codec is powered only when 5V_LOGIC_EN is high: D+ pull-up (R173 to VDDI) = USB attach. Do not enable on DCP/unknown sources.', (-70, 45.5))
text('SEL0/SEL1 = high (VDDI). HID0-2, DIN, VINL/R unused. SSPND (suspend flag, active low) reserved for a later MCU input.', (-70, 43))
text('USB_DP/USB_DN come from J1 via D1 (root). Later source-detect mux goes between those root nets and these ports.', (-70, 40.5))
text('Analogue out: 0.6 VCCCI Vpp (about 2.0 Vpp, 0.7 Vrms) centred on 1.65 V; AC-coupled (HPF ~0.4 Hz at 100k), >=10k load.', (-70, -72))

lib_syms = '(lib_symbols ' + ' '.join([emb, PD_C, PD_R, GND, XTAL, FLAG]) + ')'
hdr = ['(kicad_sch', '(version 20260306)', '(generator "eeschema")', '(generator_version "10.0")',
       f'(uuid "{SHEET_UUID}")', '(paper "A4")',
       '(title_block (title "USB audio") (rev "0.1") (comment 1 "PCM2902C bus-powered codec from 5V_LOGIC; USB D+/D- path; analogue out to USB_AUDIO_L/R"))',
       lib_syms]
OUT.write_text('\n'.join(hdr + items) + '\n)\n')
SYM.write_text(lib_text)

# ------------------------------------------------------------------ root edits
rl = root_txt
del rl[iu]
rt = '\n'.join(rl)
i = rt.index('(symbol "PCM2902CDBR:PCM2902CDBR"'); d = 0; j = i
while True:
    if rt[j] == '(': d += 1
    elif rt[j] == ')':
        d -= 1
        if d == 0: break
    j += 1
rt = rt[:i] + rt[j + 1:]
rt = rt.replace('(lib_symbols  ', '(lib_symbols ')
lines = rt.rstrip('\n').split('\n')

def retype_tpd(txt):
    for num, typ in (('1', 'no_connect'), ('2', 'no_connect'), ('3', 'passive'), ('4', 'power_in'), ('5', 'passive')):
        k = txt.index(f'(number "{num}"'); b = txt.rindex('(pin unspecified', 0, k)
        txt = txt[:b] + f'(pin {typ}' + txt[b + len('(pin unspecified'):]
    return txt
tpd_file = ROOT / 'kicad-library/schematic/TPD2E2U06DRLR.kicad_sym'
tpd_file.write_text(retype_tpd(tpd_file.read_text()))
i = lines.index(next(l for l in lines if l.startswith('(lib_symbols')))
li = lines[i]
a = li.index('(symbol "TPD2E2U06DRLR:TPD2E2U06DRLR"'); b = li.index('(symbol "power:GND"', a)
lines[i] = li[:a] + retype_tpd(li[a:b]) + li[b:]
# D1 reference/value below the body, centred
out = []
for l in lines:
    if l.startswith('(symbol (lib_id "TPD2E2U06DRLR:TPD2E2U06DRLR")'):
        l = l.replace('(property "Reference" "D1" (at 114.935 264.16 0) (effects (font (size 1.27 1.27)) (justify left))',
                      '(property "Reference" "D1" (at 105.41 272.5 0) (effects (font (size 1.27 1.27)))')
        l = l.replace('(property "Value" "TPD2E2U06DRLR" (at 114.935 266.7 0) (effects (font (size 1.27 1.27)) (justify left))',
                      '(property "Value" "TPD2E2U06DRLR" (at 105.41 275.04 0) (effects (font (size 1.27 1.27)))')
        assert '105.41 272.5' in l and '105.41 275.04' in l
    if l.startswith('(wire (pts (xy 290.83 232.41) (xy 303.53 232.41))'):
        l = l.replace('(xy 303.53 232.41)', '(xy 320.04 232.41)')
    out.append(l)

MX, MY, MW, MH = 320.04, 213.36, 50.8, 30.48
left_pins = [('USB_DN', 'bidirectional', 222.25), ('USB_DP', 'bidirectional', 227.33), ('5V_LOGIC', 'input', 232.41)]
right_pins = [('USB_AUDIO_L', 'output', 222.25), ('USB_AUDIO_R', 'output', 227.33)]
sp = ' '.join(f'(pin "{n}" {t} (at {f(MX)} {f(y)} 180) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))' for n, t, y in left_pins)
sp += ' ' + ' '.join(f'(pin "{n}" {t} (at {f(MX+MW)} {f(y)} 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}"))' for n, t, y in right_pins)
sheet = (f'(sheet (at {f(MX)} {f(MY)}) (size {f(MW)} {f(MH)}) (stroke (width 0) (type default)) (fill (color 255 255 255 0)) (uuid "{SHEET_UUID}") '
         f'(property "Sheet name" "USB_Audio" (at {f(MX)} {f(MY-1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
         f'(property "Sheet file" "USB_Audio.kicad_sch" (at {f(MX)} {f(MY+MH)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
         + sp + f' (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}" (page "8")))))')
new = [sheet]
def rw(x1, y1, x2, y2): new.append(f'(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
def rlab(n, x, y, just): new.append(f'(label "{n}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify {just})) (uuid "{U()}"))')
for n, t, y in left_pins[:2]:
    rw(MX, y, MX - 5.08, y); rlab(n, MX - 5.08, y, 'right bottom')
for n, t, y in right_pins:
    rw(MX + MW, y, MX + MW + 5.08, y); rlab(n, MX + MW + 5.08, y, 'left bottom')
# J1 data contacts (A6/B6 = D+, A7/B7 = D-): stub + label on each pin (A7 sits between A6 and B6)
for pinname, y in (('USB_DN', 244.94), ('USB_DP', 247.48), ('USB_DN', 250.02), ('USB_DP', 252.56)):
    rw(49.53, y, 40.51, y); rlab(pinname, 40.51, y, 'right bottom')
# D1: IO1 = D+, IO2 = D-, GND, NC pins
rw(96.52, 267.97, 91.44, 267.97); rlab('USB_DP', 91.44, 267.97, 'right bottom')
rw(114.3, 264.16, 119.38, 264.16); rlab('USB_DN', 119.38, 264.16, 'left bottom')
new.append(f'(no_connect (at 96.52 262.89) (uuid "{U()}"))')
new.append(f'(no_connect (at 96.52 265.43) (uuid "{U()}"))')
new.append(f'(symbol (lib_id "power:GND") (at 114.3 266.7 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid "{U()}") '
           f'(property "Reference" "#PWR801" (at 114.3 270.51 0) (effects (font (size 1.27 1.27)) (hide yes))) '
           f'(property "Value" "GND" (at 114.3 271.78 0) (effects (font (size 1.27 1.27)) (hide yes))) '
           f'(pin "1" (uuid "{U()}")) (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}" (reference "#PWR801") (unit 1)))))')
new.append(f'(text "USB D+/D- (J1 A6/B6, A7/B7) -> D1 -> USB_Audio. Tap here for the later TS3USB221A mux." (at 80.01 280.0 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
new.append(f'(text "Shield (EH 1-4) tied directly to GND, no RC." (at 20.32 277.5 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
assert out[-1] == ')'
ROOT_SCH.write_text('\n'.join(out[:-1] + new + [')']))
print('sheet uuid', SHEET_UUID)
