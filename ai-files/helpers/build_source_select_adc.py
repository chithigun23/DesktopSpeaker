#!/usr/bin/env python3
"""Create Source_Select_ADC.kicad_sch (U22 TPS7A2033, U23 TPS22917, U24 PCM1862, Y200, FB200 ...), library symbols,
root sheet block, MCU hookups and the USB_Audio 5V_CODEC re-route.  Guarded: refuses to run if the sheet exists.
Run from a clean tree.  Python 3, no dependencies."""
import re, sys, uuid, pathlib

ROOT = pathlib.Path('/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad')
LIB = ROOT / 'kicad-library/schematic'
OUT = ROOT / 'Source_Select_ADC.kicad_sch'
if OUT.exists():
    sys.exit('Source_Select_ADC.kicad_sch exists; refusing')
ROOT_UUID = 'feda53ed-537d-4f88-9436-c6075776255b'
SHEET_UUID = str(uuid.uuid4())
U = lambda: str(uuid.uuid4())
f = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')
eff = '(effects (font (size 1.27 1.27)))'
hide = '(effects (font (size 1.27 1.27)) (hide yes))'

# ------------------------------------------------------------------ library symbols
def pin(t, x, y, a, name, num, ln=5.08):
    return f'(pin {t} line (at {f(x)} {f(y)} {a}) (length {f(ln)}) (name "{name}" {eff}) (number "{num}" {eff}))'

def make_sym(name, ref_at, val_at, props, body, pins):
    base = (f'(property "Reference" "U" (at {f(ref_at[0])} {f(ref_at[1])} 0) {eff}) '
            f'(property "Value" "{name}" (at {f(val_at[0])} {f(val_at[1])} 0) {eff}) '
            + ''.join(f'(property "{k}" "{v}" (at 0 0 0) {hide}) ' for k, v in props))
    unit = f'(symbol "{name}_0_1" {body}) (symbol "{name}_1_1" ' + ' '.join(pins) + ')'
    lib = (f'(kicad_symbol_lib (version 20250120) (generator "kicad_symbol_editor") (symbol "{name}" (pin_names (offset 1.016)) '
           f'(in_bom yes) (on_board yes) ' + base + unit + ' (embedded_fonts no)))\n')
    emb = (f'(symbol "{name}:{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) '
           f'(duplicate_pin_numbers_are_jumpers no) ' + base + unit + ' (embedded_fonts no))')
    return lib, emb

def rect(x1, y1, x2, y2):
    return f'(rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width 0.254) (type default)) (fill (type background)))'

# --- PCM1862 pin table: (number, name, type, side, coord)  side L/R: coord=y ; T/B: coord=x
PCM = [
 ('3', 'VINL1', 'input', 'L', 50.8), ('4', 'VINR1', 'input', 'L', 38.1), ('1', 'VINL2', 'input', 'L', 25.4),
 ('2', 'VINR2', 'input', 'L', 12.7), ('29', 'VINL3', 'input', 'L', 0), ('30', 'VINR3', 'input', 'L', -12.7),
 ('27', 'VINL4', 'input', 'L', -22.86), ('28', 'VINR4', 'input', 'L', -27.94), ('5', 'MICBIAS', 'passive', 'L', -33.02),
 ('26', 'MD0', 'input', 'L', -43.18), ('25', 'MS/AD', 'input', 'L', -48.26), ('15', 'SCKI', 'input', 'L', -53.34),
 ('18', 'DOUT', 'output', 'R', 50.8), ('17', 'BCK', 'bidirectional', 'R', 43.18), ('16', 'LRCK', 'bidirectional', 'R', 35.56),
 ('14', 'IOVDD', 'power_in', 'R', 58.42), ('24', 'MC/SCL', 'input', 'R', 15.24), ('23', 'MOSI/SDA', 'bidirectional', 'R', 0),
 ('21', 'GPIO1/INTA', 'bidirectional', 'R', -15.24), ('22', 'MISO/GPIO0', 'bidirectional', 'R', -25.4),
 ('20', 'GPIO2/INTB', 'bidirectional', 'R', -30.48), ('19', 'GPIO3/INTC', 'bidirectional', 'R', -35.56),
 ('10', 'XI', 'input', 'R', -45.72), ('9', 'XO', 'output', 'R', -58.42),
 ('8', 'AVDD', 'power_in', 'T', -10.16), ('13', 'DVDD', 'power_in', 'T', 5.08),
 ('6', 'VREF', 'passive', 'B', -12.7), ('7', 'AGND', 'power_in', 'B', -7.62), ('12', 'DGND', 'power_in', 'B', 7.62),
 ('11', 'LDO', 'passive', 'B', 12.7),
]
PCMXY = {}
pp = []
for n, nm, t, s, c in PCM:
    if s == 'L': x, y, a = -20.32, c, 0
    elif s == 'R': x, y, a = 20.32, c, 180
    elif s == 'T': x, y, a = c, 68.58, 270
    else: x, y, a = c, -71.12, 90
    PCMXY[nm] = (x, y); pp.append(pin(t, x, y, a, nm, n))
pcm_lib, pcm_emb = make_sym('PCM1862DBTR', (0, -68.58), (0, -71.12), [
    ('Footprint', 'DesktopSpeaker:PCM1862DBTR'), ('Datasheet', '${KIPRJMOD}/../ai-files/datasheets/PCM1862.pdf'),
    ('Manufacturer', 'Texas Instruments'), ('MPN', 'PCM1862DBTR'), ('LCSC Part', 'C544647'),
    ('Description', '103 dB stereo audio ADC, 4:1 input mux, I2S master, TSSOP-30 (DBT); pins grouped by function, numbers per SLAS831D')],
    rect(-15.24, 63.5, 15.24, -66.04), pp)

# --- TPS7A2033PDBVR (SOT-23-5): 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT
ldo_pins = [pin('power_in', -17.78, 2.54, 0, 'IN', '1'), pin('input', -17.78, -2.54, 0, 'EN', '3'),
            pin('power_out', 17.78, 2.54, 180, 'OUT', '5'), pin('no_connect', 17.78, -2.54, 180, 'NC', '4'),
            pin('power_in', 10.16, -15.24, 90, 'GND', '2', 2.54)]
ldo_lib, ldo_emb = make_sym('TPS7A2033PDBVR', (0, -15.24), (0, -17.78), [
    ('Footprint', 'DesktopSpeaker:TPS7A2033PDBVR'), ('Datasheet', '${KIPRJMOD}/../ai-files/datasheets/TPS7A20.pdf'),
    ('Manufacturer', 'Texas Instruments'), ('MPN', 'TPS7A2033PDBVR'), ('LCSC Part', 'C2862740'),
    ('Description', '300 mA ultra-low-noise LDO, fixed 3.3 V with output discharge, SOT-23-5 (DBV)')],
    rect(-12.7, 10.16, 12.7, -12.7), ldo_pins)
# --- TPS22917DBVR (SOT-23-6): 1 VIN, 2 GND, 3 ON, 4 CT, 5 QOD, 6 VOUT
sw_pins = [pin('input', -17.78, 7.62, 0, 'ON', '3'), pin('passive', -17.78, 0, 0, 'CT', '4'), pin('power_in', -17.78, -7.62, 0, 'VIN', '1'),
           pin('power_out', 17.78, -7.62, 180, 'VOUT', '6'), pin('passive', 17.78, -2.54, 180, 'QOD', '5'),
           pin('power_in', 10.16, -17.78, 90, 'GND', '2', 2.54)]
sw_lib, sw_emb = make_sym('TPS22917DBVR', (0, -15.24), (0, -17.78), [
    ('Footprint', 'DesktopSpeaker:TPS22917DBVR'), ('Datasheet', '${KIPRJMOD}/../ai-files/datasheets/TPS22917.pdf'),
    ('Manufacturer', 'Texas Instruments'), ('MPN', 'TPS22917DBVR'), ('LCSC Part', 'C2681320'),
    ('Description', '1-5.5 V 2 A load switch, active-high ON, adjustable slew (CT), quick output discharge (QOD), SOT-23-6 (DBV)')],
    rect(-12.7, 12.7, 12.7, -15.24), sw_pins)

for nm, txt in (('PCM1862DBTR', pcm_lib), ('TPS7A2033PDBVR', ldo_lib), ('TPS22917DBVR', sw_lib)):
    p = LIB / f'{nm}.kicad_sym'
    if p.exists(): sys.exit(f'{p} exists')
    p.write_text(txt)

# ------------------------------------------------------------------ embedded library helpers
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
xt = pathlib.Path('/home/chithi/kicad-libs/symbols/Device.kicad_symdir/Crystal_GND24.kicad_sym').read_text()
XTAL = grab(xt, 'Crystal_GND24').replace('(symbol "Crystal_GND24"', '(symbol "Device:Crystal_GND24"', 1)
fb = pathlib.Path('/home/chithi/kicad-libs/symbols/Device.kicad_symdir/FerriteBead_Small.kicad_sym').read_text()
FLAG = grab(pathlib.Path(ROOT/'USB_PD.kicad_sch').read_text(), 'PD_PWR_FLAG:PD_PWR_FLAG')
FERR = grab(fb, 'FerriteBead_Small').replace('(symbol "FerriteBead_Small"', '(symbol "Device:FerriteBead_Small"', 1)

# ------------------------------------------------------------------ sheet building (local coords, y up)
OX, OY = 190.5, 170.18
P = lambda lx, ly: (OX + lx, OY - ly)
items = []
def wire(*pts):
    for a, b in zip(pts, pts[1:]):
        (x1, y1), (x2, y2) = P(*a), P(*b)
        items.append(f'(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
def junc(a):
    x, y = P(*a); items.append(f'(junction (at {f(x)} {f(y)}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')
def nc(a):
    x, y = P(*a); items.append(f'(no_connect (at {f(x)} {f(y)}) (uuid "{U()}"))')
def hlabel(n, shape, a, ang):
    x, y = P(*a)
    j = 'left bottom' if ang == 0 else 'right bottom'
    items.append(f'(hierarchical_label "{n}" (shape {shape}) (at {f(x)} {f(y)} {ang}) (effects (font (size 1.0 1.0)) (justify {j})) (uuid "{U()}"))')
def label(n, a, just='left bottom'):
    x, y = P(*a); items.append(f'(label "{n}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify {just})) (uuid "{U()}"))')
def text(s, a):
    x, y = P(*a)
    items.append(f'(text "{s}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
pw = [951]
def gnd(a):
    x, y = P(*a); n = pw[0]; pw[0] += 1
    items.append(f'(symbol (lib_id "power:GND") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "#PWR{n}" (at {f(x)} {f(y+3.81)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                 f'(property "Value" "GND" (at {f(x)} {f(y+5.08)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                 f'(pin "1" (uuid "{U()}")) (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "#PWR{n}") (unit 1)))))')
def ic(lib, ref, val, c, rot, tpos, props, pins, justify=''):
    jj = f'(justify {justify})' if justify else ''
    x, y = P(*c)
    (rx, ry), (vx, vy) = [P(*t) for t in tpos]
    ptxt = ''.join(f'(property "{k}" "{v}" (at {f(x)} {f(y)} 0) {hide}) ' for k, v in props)
    items.append(f'(symbol (lib_id "{lib}") (at {f(x)} {f(y)} {rot}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "{ref}" (at {f(rx)} {f(ry)} 0) (effects (font (size 1.27 1.27)) {jj})) (property "Value" "{val}" (at {f(vx)} {f(vy)} 0) (effects (font (size 1.27 1.27)) {jj})) ' + ptxt +
                 ' '.join(f'(pin "{n}" (uuid "{U()}"))' for n in pins) +
                 f' (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "{ref}") (unit 1)))))')
def passive(lib, ref, val, fp, mpn, mfr, lcsc, a, rot, tpos, just='left', desc=''):
    x, y = P(*a)
    (rx, ry), (vx, vy) = [P(*t) for t in tpos]
    j = f'(justify {just})' if just else ''
    tang = 270 if rot == 90 else 0
    items.append(f'(symbol (lib_id "{lib}") (at {f(x)} {f(y)} {rot}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "{ref}" (at {f(rx)} {f(ry)} {tang}) (effects (font (size 1.27 1.27)) {j})) '
                 f'(property "Value" "{val}" (at {f(vx)} {f(vy)} {tang}) (effects (font (size 1.27 1.27)) {j})) '
                 f'(property "Footprint" "{fp}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
                 f'(property "MPN" "{mpn}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
                 f'(property "Manufacturer" "{mfr}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
                 f'(property "LCSC" "{lcsc}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
                 f'(pin "1" (uuid "{U()}")) (pin "2" (uuid "{U()}")) '
                 f'(instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "{ref}") (unit 1)))))')
def res(ref, val, part, a, horizontal=False):
    mpn, mfr, lcsc = part; x, y = a
    if horizontal: passive('PD_R:PD_R', ref, val, 'DesktopSpeaker:PD_R_0603', mpn, mfr, lcsc, a, 90, ((x, y + 4.2), (x, y + 2.6)), just=None)
    else: passive('PD_R:PD_R', ref, val, 'DesktopSpeaker:PD_R_0603', mpn, mfr, lcsc, a, 0, ((x + 1.27, y + 1.27), (x + 1.27, y - 1.27)))
def cap(ref, val, part, a, horizontal=False):
    fp, mpn, mfr, lcsc = part; x, y = a
    if horizontal: passive('PD_C:PD_C', ref, val, fp, mpn, mfr, lcsc, a, 90, ((x, y + 4.2), (x, y + 2.6)), just=None)
    else: passive('PD_C:PD_C', ref, val, fp, mpn, mfr, lcsc, a, 0, ((x + 1.27, y + 1.27), (x + 1.27, y - 1.27)))
def vcap(ref, val, part, top):   # vertical cap whose top pin sits at `top`, ground symbol below
    x, y = top; cap(ref, val, part, (x, y - 3.81)); gnd((x, y - 7.62))
def vres(ref, val, part, top):
    x, y = top; res(ref, val, part, (x, y - 3.81))

SAM = 'Samsung Electro-Mechanics'
C100N = ('DesktopSpeaker:PD_C_0603', 'CL10B104KB8NNNC', SAM, 'C1591')
C1U = ('DesktopSpeaker:PD_C_0805', 'CL21B105KBFNNNE', SAM, 'C28323')
C10U = ('DesktopSpeaker:PD_C_0805', 'CL21B106KPQNNNE', SAM, 'C32635')
C22U = ('DesktopSpeaker:PD_C_0805', 'CL21B225KAFNNNE', SAM, '')
C10N = ('DesktopSpeaker:PD_C_0603', 'GRM1885C1H103JA01D', 'Murata', '')
C20P = ('DesktopSpeaker:PD_C_0603', 'CL10C200JB8NNNC', SAM, '')
RY = lambda mpn, lcsc: (mpn, 'YAGEO', lcsc)
R100 = RY('RC0603FR-07100RL', ''); R33 = RY('RC0603FR-0733RL', ''); R2K2 = RY('RC0603FR-072K2L', '')
R100K = RY('RC0603FR-07100KL', 'C14675')

# ---- U24 PCM1862
ic('PCM1862DBTR:PCM1862DBTR', 'U24', 'PCM1862DBTR', (0, 0), 0, ((0, -68.58), (0, -71.12)),
   [('Footprint', 'DesktopSpeaker:PCM1862DBTR'), ('Datasheet', '${KIPRJMOD}/../ai-files/datasheets/PCM1862.pdf'),
    ('Manufacturer', 'Texas Instruments'), ('MPN', 'PCM1862DBTR'), ('LCSC Part', 'C544647')], [p[0] for p in PCM])
XY = PCMXY
# ---- input networks: port - 2.2uF - 100R - node(10nF C0G to GND) - VINx
rows = [('USB_AUDIO_L', 'VINL1'), ('USB_AUDIO_R', 'VINR1'), ('BT_AUDIO_L', 'VINL2'), ('BT_AUDIO_R', 'VINR2'),
        ('AUX_L', 'VINL3'), ('AUX_R', 'VINR3')]
LP = -149.86; NODE = -93.98
for k, (port, vin) in enumerate(rows):
    y = XY[vin][1]
    hlabel(port, 'input', (LP, y), 180)
    wire((LP, y), (-135.89, y))
    cap(f'C{200+k}', '2.2uF', C22U, (-132.08, y), True)
    wire((-128.27, y), (-115.57, y))
    res(f'R{200+k}', '100', R100, (-111.76, y), True)
    wire((-107.95, y), XY[vin]); junc((NODE, y))
    vcap(f'C{206+k}', '10nF C0G', C10N, (NODE, y))
for nm in ('VINL4', 'VINR4', 'MICBIAS'): nc(XY[nm])
# strap pins to ground
bx = -27.94
wire(XY['MD0'], (bx, XY['MD0'][1]), (bx, -55.88)); wire(XY['MS/AD'], (bx, XY['MS/AD'][1])); wire(XY['SCKI'], (bx, XY['SCKI'][1]))
junc((bx, XY['MS/AD'][1])); junc((bx, XY['SCKI'][1])); gnd((bx, -55.88))
# ---- bottom: VREF, grounds, LDO
vcap('C212', '1uF', C1U, XY['VREF'])
wire(XY['AGND'], (-7.62, -76.2), (0, -76.2), (7.62, -76.2)); wire(XY['DGND'], (7.62, -76.2)); junc((0, -76.2)); gnd((0, -76.2))
vcap('C213', '100nF', C100N, XY['LDO'])
wire(XY['LDO'], (22.86, -71.12)); junc(XY['LDO']); vcap('C214', '10uF', C10U, (22.86, -71.12))
# ---- supply rails (3V3_AUDIO bus at y=96.52)
BUS = 96.52
RPX = 95.25; PUX = 60.96
LX = -86.36                       # U22 / U23 centre x
ic('TPS7A2033PDBVR:TPS7A2033PDBVR', 'U22', 'TPS7A2033PDBVR', (LX, 93.98), 0, ((LX, 78.74), (LX, 76.2)),
   [('Footprint', 'DesktopSpeaker:TPS7A2033PDBVR'), ('Datasheet', '${KIPRJMOD}/../ai-files/datasheets/TPS7A20.pdf'),
    ('Manufacturer', 'Texas Instruments'), ('MPN', 'TPS7A2033PDBVR'), ('LCSC Part', 'C2862740')], ['1', '2', '3', '4', '5'])
INx, OUTx = LX - 17.78, LX + 17.78
wire((INx, BUS), (-119.38, BUS))
wire((INx, 91.44), (-107.95, 91.44), (-107.95, BUS)); junc((-107.95, BUS))
junc((-113.03, BUS)); vcap('C221', '1uF', C1U, (-113.03, BUS))
nc((OUTx, 91.44))
gnd((LX + 10.16, 78.74))
# bus
wire((OUTx, BUS), (RPX, BUS))
for x, ref, val, part in ((-60.96, 'C222', '1uF', C1U), (-50.8, 'C223', '10uF', C10U)):
    junc((x, BUS)); vcap(ref, val, part, (x, BUS))
hlabel('3V3_AUDIO', 'output', (RPX, BUS), 0)
# U23 load switch
SY = 132.08
ic('TPS22917DBVR:TPS22917DBVR', 'U23', 'TPS22917DBVR', (LX, SY), 0, ((LX, SY - 17.78), (LX, SY - 20.32)),
   [('Footprint', 'DesktopSpeaker:TPS22917DBVR'), ('Datasheet', '${KIPRJMOD}/../ai-files/datasheets/TPS22917.pdf'),
    ('Manufacturer', 'Texas Instruments'), ('MPN', 'TPS22917DBVR'), ('LCSC Part', 'C2681320')], ['1', '2', '3', '4', '5', '6'])
VINy = SY - 7.62
hlabel('5V_LOGIC', 'input', (LP, VINy), 180)
wire((LP, VINy), (INx, VINy)); wire((-119.38, VINy), (-119.38, BUS)); junc((-119.38, VINy))
junc((-110.49, VINy)); vcap('C224', '1uF', C1U, (-110.49, VINy))
ONy = SY + 7.62
hlabel('CODEC_PWR_EN', 'input', (LP, ONy), 180)
wire((LP, ONy), (INx, ONy)); junc((-132.08, ONy)); vres('R212', '100k', R100K, (-132.08, ONy)); gnd((-132.08, ONy - 7.62))
nc((INx, SY))
gnd((LX + 10.16, SY - 17.78))
wire((OUTx, VINy), (RPX, VINy))
wire((OUTx, SY - 2.54), (-62.23, SY - 2.54), (-62.23, VINy)); junc((-62.23, VINy))
junc((-55.88, VINy)); vcap('C225', '1uF', C1U, (-55.88, VINy))
hlabel('5V_CODEC', 'output', (RPX, VINy), 0)
# ---- AVDD via FB200, DVDD, IOVDD
AVx, DVx, IOx = XY['AVDD'][0], XY['DVDD'][0], 38.1
NY = 83.82
ic('Device:FerriteBead_Small', 'FB200', 'BLM18AG601SN1D', (AVx, 93.98), 0, ((AVx + 2.54, 95.25), (AVx + 2.54, 92.71)),
   [('Footprint', 'DesktopSpeaker:PD_R_0603'), ('MPN', 'BLM18AG601SN1D'), ('Manufacturer', 'Murata'), ('LCSC', 'C19330'),
    ('Datasheet', '')], ['1', '2'], 'left')
junc((AVx, BUS))
wire((AVx, 91.44), (AVx, XY['AVDD'][1])); junc((AVx, NY))
wire((AVx, NY), (-30.48, NY)); junc((-20.32, NY))
fx, fy = P(AVx + 5.08, NY)
wire((AVx, NY), (AVx + 5.08, NY))
items.append(f'(symbol (lib_id "PD_PWR_FLAG:PD_PWR_FLAG") (at {f(fx)} {f(fy)} 270) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid "{U()}") '
             f'(property "Reference" "#FLG951" (at {f(fx)} {f(fy)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
             f'(property "Value" "PWR_FLAG" (at {f(fx+2.54)} {f(fy-3.0)} 0) (effects (font (size 1 1)) (hide yes))) '
             f'(property "Footprint" "" (at {f(fx)} {f(fy)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
             f'(property "Datasheet" "" (at {f(fx)} {f(fy)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
             f'(pin "1" (uuid "{U()}")) (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "#FLG951") (unit 1)))))')
vcap('C215', '100nF', C100N, (-20.32, NY)); vcap('C216', '10uF', C10U, (-30.48, NY))
wire(XY['DVDD'], (DVx, BUS)); junc((DVx, BUS)); junc((DVx, NY))
wire((DVx, NY), (25.4, NY)); junc((15.24, NY))
vcap('C217', '100nF', C100N, (15.24, NY)); vcap('C218', '10uF', C10U, (25.4, NY))
wire(XY['IOVDD'], (IOx, XY['IOVDD'][1]), (IOx, BUS)); junc((IOx, BUS)); junc((IOx, NY))
wire((IOx, NY), (58.42, NY)); junc((48.26, NY))
vcap('C219', '100nF', C100N, (48.26, NY)); vcap('C220', '1uF', C1U, (58.42, NY))
# ---- right side: I2S through 33R, I2C pull-ups, INT, crystal
for k, (pn, port) in enumerate((('DOUT', 'I2S_SDATA'), ('BCK', 'I2S_BCK'), ('LRCK', 'I2S_LRCK'))):
    y = XY[pn][1]
    wire(XY[pn], (29.21, y)); res(f'R{206+k}', '33', R33, (33.02, y), True); wire((36.83, y), (RPX, y))
    hlabel(port, 'output', (RPX, y), 0)
for pn, port, ref in (('MC/SCL', 'AUD_SCL', 'R209'), ('MOSI/SDA', 'AUD_SDA', 'R210')):
    y = XY[pn][1]
    wire(XY[pn], (RPX, y)); hlabel(port, 'bidirectional', (RPX, y), 0); junc((PUX, y))
    res(ref, '2.2k', R2K2, (PUX, y + 3.81)); wire((PUX, y + 7.62), (PUX, y + 10.16)); label('3V3_AUDIO', (PUX, y + 10.16))
y = XY['GPIO1/INTA'][1]
wire(XY['GPIO1/INTA'], (RPX, y)); hlabel('ADC_INT', 'output', (RPX, y), 0); junc((PUX, y))
vres('R211', '100k', R100K, (PUX, y)); gnd((PUX, y - 7.62))
for nm in ('MISO/GPIO0', 'GPIO2/INTB', 'GPIO3/INTC'): nc(XY[nm])
# crystal Y200 (24.576 MHz): XI row crystal, XO row returns around the right
xiy, xoy = XY['XI'][1], XY['XO'][1]
cx = 55.88
wire(XY['XI'], (cx - 3.81, xiy)); junc((33.02, xiy)); vcap('C226', '20pF C0G', C20P, (33.02, xiy))
wire((cx + 3.81, xiy), (71.12, xiy), (71.12, xoy), XY['XO']); junc((45.72, xoy)); vcap('C227', '20pF C0G', C20P, (45.72, xoy))
x, y = P(cx, xiy)
items.append(f'(symbol (lib_id "Device:Crystal_GND24") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}") '
             f'(property "Reference" "Y200" (at {f(x+5.08)} {f(y-5.08)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
             f'(property "Value" "24.576MHz" (at {f(x+5.08)} {f(y-7.62)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
             f'(property "Footprint" "DesktopSpeaker:Crystal_SMD_3225-4Pin_3.2x2.5mm" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
             f'(property "MPN" "L327S240P11L" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
             f'(property "Manufacturer" "Lucki" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
             f'(property "LCSC" "C5261154" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
             + ' '.join(f'(pin "{n}" (uuid "{U()}"))' for n in range(1, 5)) +
             f' (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "Y200") (unit 1)))))')
gnd((cx, xiy - 5.08))
# ---- notes
text('Power: U22 TPS7A2033 (3V3_AUDIO, EN tied to IN) and U23 TPS22917 (5V_CODEC for USB_Audio, CODEC_PWR_EN, QOD tied to VOUT, CT open).', (-60.96, 154.94))
text('PCM1862: I2C mode (MD0 low), address 0x4A (MS/AD low), I2S master from the 24.576 MHz crystal (512 fs, PLL off), SCKI grounded. VIN1 = USB, VIN2 = BT, VIN3 = AUX.', (-60.96, 152.4))
text('Inputs: 2.2 uF - 100 R - 10 nF C0G (datasheet fig. 61 filter; ~5 mA ESD-diode limit). AVDD via FB200. No reset pin: firmware re-initialises after every 3V3_AUDIO enable.', (-60.96, 149.86))
text('Crystal CL 15 pF (Lucki L327S240P11L): 2 x 20 pF with about 3 pF stray gives about 13 pF; trim at bring-up. Spare VIN4, MICBIAS and GPIO0/2/3 are no-connect.', (-60.96, 147.32))

lib_syms = '(lib_symbols ' + ' '.join([pcm_emb, ldo_emb, sw_emb, PD_C, PD_R, GND, XTAL, FERR, FLAG]) + ')'
hdr = ['(kicad_sch', '(version 20260306)', '(generator "eeschema")', '(generator_version "10.0")',
       f'(uuid "{SHEET_UUID}")', '(paper "A3")',
       '(title_block (title "Source select and ADC") (rev "0.1") (comment 1 "PCM1862 4:1 input ADC with I2S master, 3V3_AUDIO LDO, 5V_CODEC load switch"))',
       lib_syms]
OUT.write_text('\n'.join(hdr + items) + '\n)\n')

# ------------------------------------------------------------------ sym-lib-table
tbl = (ROOT / 'sym-lib-table').read_text()
add = ''.join(f'  (lib (name "{n}") (type "KiCad") (uri "${{KIPRJMOD}}/kicad-library/schematic/{n}.kicad_sym") (options "") (descr "{d}"))\n'
              for n, d in (('PCM1862DBTR', 'Texas Instruments PCM1862 audio ADC'), ('TPS7A2033PDBVR', 'Texas Instruments TPS7A2033 LDO'),
                           ('TPS22917DBVR', 'Texas Instruments TPS22917 load switch')))
idx = tbl.rindex(')')
(ROOT / 'sym-lib-table').write_text(tbl[:idx] + add + tbl[idx:])

# ------------------------------------------------------------------ root edits
rt = (ROOT / 'DesktopSpeaker.kicad_sch').read_text()
MX, MY, MW, MH = 109.22, 15.24, 50.8, 50.8
left = [('5V_LOGIC', 'input'), ('USB_AUDIO_L', 'input'), ('USB_AUDIO_R', 'input'), ('BT_AUDIO_L', 'input'), ('BT_AUDIO_R', 'input'),
        ('AUX_L', 'input'), ('AUX_R', 'input'), ('CODEC_PWR_EN', 'input')]
right = [('3V3_AUDIO', 'output'), ('5V_CODEC', 'output'), ('I2S_BCK', 'output'), ('I2S_LRCK', 'output'), ('I2S_SDATA', 'output'),
         ('ADC_INT', 'output'), ('AUD_SCL', 'bidirectional'), ('AUD_SDA', 'bidirectional')]
new = []
sp = ''
for i, (n, t) in enumerate(left):
    y = MY + 5.08 * (i + 1); sp += f'(pin "{n}" {t} (at {f(MX)} {f(y)} 180) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}")) '
    new.append(f'(wire (pts (xy {f(MX)} {f(y)}) (xy {f(MX-5.08)} {f(y)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    new.append(f'(label "{n}" (at {f(MX-5.08)} {f(y)} 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}"))')
for i, (n, t) in enumerate(right):
    y = MY + 5.08 * (i + 1); sp += f'(pin "{n}" {t} (at {f(MX+MW)} {f(y)} 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}")) '
    new.append(f'(wire (pts (xy {f(MX+MW)} {f(y)}) (xy {f(MX+MW+5.08)} {f(y)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    new.append(f'(label "{n}" (at {f(MX+MW+5.08)} {f(y)} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
sheet = (f'(sheet (at {f(MX)} {f(MY)}) (size {f(MW)} {f(MH)}) (stroke (width 0) (type default)) (fill (color 255 255 255 0)) (uuid "{SHEET_UUID}") '
         f'(property "Sheet name" "Source_Select_ADC" (at {f(MX)} {f(MY-1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
         f'(property "Sheet file" "Source_Select_ADC.kicad_sch" (at {f(MX)} {f(MY+MH)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
         + sp + f'(instances (project "DesktopSpeaker" (path "/{ROOT_UUID}" (page "10")))))')
new.insert(0, sheet)
new.append(f'(text "AUX_L/AUX_R come from the later Headphone_Aux sheet (J3 AUX_IN); stubs only for now. I2S fans out to both TAS5825M in the Amplifiers sheet." (at 20.0 70.0 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')

def rep(s, a, b, count=1):
    assert s.count(a) == count, (a, s.count(a))
    return s.replace(a, b)
# 5V_LOGIC supply split: Logic_Audio_Power output keeps 5V_LOGIC; USB_Audio port now carries 5V_CODEC
rt = rep(rt, '(wire (pts (xy 290.83 232.41) (xy 320.04 232.41))',
         f'(wire (pts (xy 314.96 232.41) (xy 320.04 232.41)) (stroke (width 0) (type default)) (uuid "{U()}"))\n'
         f'(label "5V_CODEC" (at 314.96 232.41 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}"))\n'
         f'(wire (pts (xy 290.83 232.41) (xy 295.91 232.41))')
rt = rep(rt, '(label "5V_LOGIC" (at 303.53 232.41 0)', '(label "5V_LOGIC" (at 295.91 232.41 0)')
rt = rep(rt, '(pin "5V_LOGIC" input (at 320.04 232.41 180)', '(pin "5V_CODEC" input (at 320.04 232.41 180)')
# MCU sheet block pins
mcu_pins = (f'(pin "CODEC_PWR_EN" output (at 370.84 124.46 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}")) '
            f'(pin "AUD_SDA" bidirectional (at 370.84 144.78 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}")) '
            f'(pin "AUD_SCL" bidirectional (at 370.84 149.86 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}")) '
            f'(pin "ADC_INT" input (at 320.04 177.8 180) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}")) ')
i = rt.index('(property "Sheet name" "MCU"'); j = rt.index('(pin ', i)
rt = rt[:j] + mcu_pins + rt[j:]
for n, x1, x2, y, side in (('CODEC_PWR_EN', 370.84, 375.92, 124.46, 'r'), ('AUD_SDA', 370.84, 375.92, 144.78, 'r'),
                           ('AUD_SCL', 370.84, 375.92, 149.86, 'r'), ('ADC_INT', 320.04, 314.96, 177.8, 'l')):
    new.append(f'(wire (pts (xy {f(x1)} {f(y)}) (xy {f(x2)} {f(y)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    just = 'left bottom' if side == 'r' else 'right bottom'
    new.append(f'(label "{n}" (at {f(x2)} {f(y)} 0) (effects (font (size 1 1)) (justify {just})) (uuid "{U()}"))')
assert rt.rstrip().endswith(')')
body = rt.rstrip()[:-1]
(ROOT / 'DesktopSpeaker.kicad_sch').write_text(body + '\n'.join(new) + '\n)\n')

# ------------------------------------------------------------------ MCU sheet: connect reserved labels
mt = (ROOT / 'MCU.kicad_sch').read_text()
def rm_nc(t, x, y):
    pat = re.compile(r'\(no_connect \(at %s %s\) \(uuid "[^"]*"\)\)\n' % (re.escape(x), re.escape(y))); assert pat.search(t), (x, y)
    return pat.sub('', t, 1)
def rm_text(t, s):
    pat = re.compile(r'\(text "%s" [^\n]*\n' % re.escape(s)); assert pat.search(t), s
    return pat.sub('', t, 1)
add = []
for nm, py, nx in (('AUD_SDA', '92.71', '165.1'), ('AUD_SCL', '95.25', '165.1'), ('CODEC_PWR_EN', '128.27', '165.1')):
    mt = rm_nc(mt, nx, py); mt = rm_text(mt, f'{nm} (reserved)')
    add.append(f'(wire (pts (xy 165.1 {py}) (xy 215.9 {py})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    add.append(f'(hierarchical_label "{nm}" (shape {"output" if nm=="CODEC_PWR_EN" else "bidirectional"}) (at 215.9 {py} 0) (effects (font (size 1.0 1.0)) (justify right bottom)) (uuid "{U()}"))')
mt = rm_nc(mt, '114.3', '102.87'); mt = rm_text(mt, 'ADC_INT (reserved)')
add.append(f'(wire (pts (xy 45.72 102.87) (xy 114.3 102.87)) (stroke (width 0) (type default)) (uuid "{U()}"))')
add.append(f'(hierarchical_label "ADC_INT" (shape input) (at 45.72 102.87 0) (effects (font (size 1.0 1.0)) (justify left bottom)) (uuid "{U()}"))')
assert mt.rstrip().endswith(')')
(ROOT / 'MCU.kicad_sch').write_text(mt.rstrip()[:-1] + '\n'.join(add) + '\n)\n')

# ------------------------------------------------------------------ USB_Audio: supply label 5V_LOGIC -> 5V_CODEC
ut = (ROOT / 'USB_Audio.kicad_sch').read_text()
ut = rep(ut, '(hierarchical_label "5V_LOGIC"', '(hierarchical_label "5V_CODEC"')
ut = ut.replace('Supply: 5V_LOGIC (U14 TPS63802, 4.60-5.06 V worst case) feeds VBUS', 'Supply: 5V_CODEC (U23 load switch from 5V_LOGIC, 4.60-5.06 V worst case) feeds VBUS')
ut = ut.replace('Codec is powered only when 5V_LOGIC_EN is high:', 'Codec is powered only when CODEC_PWR_EN (U23) and 5V_LOGIC are on:')
ut = ut.replace('Do not enable on DCP/unknown sources.', 'Do not enable CODEC_PWR_EN on DCP/unknown sources.')
(ROOT / 'USB_Audio.kicad_sch').write_text(ut)
print('sheet uuid', SHEET_UUID)
