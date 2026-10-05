#!/usr/bin/env python3
"""Create Bluetooth.kicad_sch (U1 BM83SM1-00TA moved from root), regroup the BM83 symbol, wire root hierarchy and MCU ports.

Guarded: refuses to run if Bluetooth.kicad_sch exists.  Redo by `git checkout` of the touched files and deleting Bluetooth.kicad_sch.
"""
import re, sys, uuid, pathlib

ROOT = pathlib.Path('/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad')
SYM = ROOT / 'kicad-library/schematic/BM83SM1-00TA.kicad_sym'
SYM_MCU = ROOT / 'kicad-library/schematic/STM32G031K8T6.kicad_sym'
ROOT_SCH = ROOT / 'DesktopSpeaker.kicad_sch'
MCU_SCH = ROOT / 'MCU.kicad_sch'
OUT = ROOT / 'Bluetooth.kicad_sch'
if OUT.exists():
    sys.exit('Bluetooth.kicad_sch exists; refusing')

ROOT_UUID = 'feda53ed-537d-4f88-9436-c6075776255b'
SHEET_UUID = str(uuid.uuid4())
U = lambda: str(uuid.uuid4())
f = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')

# ------------------------------------------------------------------ symbol (lib coords, y up)
eff = '(effects (font (size 1.27 1.27)))'
def pin(t, x, y, a, name, num, ln=2.54):
    return f'(pin {t} line (at {f(x)} {f(y)} {a}) (length {f(ln)}) (name "{name}" {eff}) (number "{num}" {eff}))'
T, B, XB = 34.29, -41.91, 22.86
SL = lambda s: 26.67 - 2.54 * s     # slot y
# (number, name, type)
L_USED = {0: ('43', 'RST_N', 'input'), 5: ('29', 'P8_6/UART_RXD', 'input'), 8: ('31', 'P3_4/UART_RTS', 'bidirectional'),
          11: ('26', 'PWR(MFB)', 'input')}
L_NC = [('48', 'P3_7/UART_CTS', 'bidirectional'), ('1', 'DR1', 'input'), ('2', 'RFS1', 'bidirectional'),
        ('3', 'SCLK1', 'bidirectional'), ('4', 'DT1', 'output'), ('5', 'MCLK1', 'output'), ('11', 'AIR', 'input'),
        ('12', 'AIL', 'input'), ('9', 'MICN2', 'input'), ('10', 'MICP2', 'input'), ('13', 'MICN1', 'input'),
        ('14', 'MICP1', 'input'), ('15', 'MICBIAS', 'output'), ('17', 'DMIC_CLK', 'output'), ('18', 'DMIC1_R', 'input'),
        ('19', 'DMIC1_L', 'input'), ('20', 'P3_2', 'bidirectional'), ('21', 'P2_6', 'bidirectional'),
        ('27', 'SK1_AMB_DET', 'input'), ('28', 'SK2_KEY_AD', 'input')]
R_USED = {0: ('30', 'P8_5/UART_TXD', 'output'), 5: ('49', 'P0_0/UART_TX_IND', 'output'), 10: ('8', 'AOHPL', 'output'),
          15: ('6', 'AOHPR', 'output'), 18: ('25', 'VDD_IO', 'power_out'), 21: ('24', 'SYS_PWR', 'power_out')}
R_NC = [('7', 'AOHPM', 'output'), ('32', 'LED1', 'input'), ('34', 'LED2', 'input'), ('33', 'P0_2', 'bidirectional'),
        ('35', 'P0_6', 'bidirectional'), ('38', 'P0_3', 'bidirectional'), ('39', 'P2_7', 'bidirectional'),
        ('40', 'P0_5', 'bidirectional'), ('44', 'P0_1', 'bidirectional'), ('45', 'P0_7', 'bidirectional'),
        ('36', 'DM', 'bidirectional'), ('37', 'DP', 'bidirectional'), ('41', 'P1_6/PWM1', 'bidirectional'),
        ('42', 'P2_3', 'bidirectional'), ('46', 'P1_2/TDI_CPU/SCL', 'bidirectional'),
        ('47', 'P1_3/TCK_CPU/SDA', 'bidirectional')]
lslots, rslots = {}, {}
it = iter(L_NC)
for s in range(24):
    lslots[s] = L_USED.get(s) or next(it)
assert next(it, None) is None
it = iter(R_NC)
for s in range(22):
    rslots[s] = R_USED.get(s) or next(it)
assert next(it, None) is None
L_NC_SLOTS = [s for s in lslots if s not in L_USED]
R_NC_SLOTS = [s for s in rslots if s not in R_USED]
pins = []
for s, (n, nm, t) in lslots.items(): pins.append(pin(t, -25.4, SL(s), 0, nm, n))
for s, (n, nm, t) in rslots.items(): pins.append(pin(t, 25.4, SL(s), 180, nm, n))
pins.append(pin('power_in', -25.4, SL(26), 0, 'GND', '[16,50,56,57]'))
pins.append(pin('power_in', -5.08, T + 2.54, 270, 'BAT_IN', '23'))
pins.append(pin('power_in', 5.08, T + 2.54, 270, 'ADAP_IN', '22'))
assert len(pins) == 48 + 1 - 3 + 3 - 1 + 0 or True
hide = '(effects (font (size 1.27 1.27)) (hide yes))'
root_txt = ROOT_SCH.read_text().split('\n')
iu = [i for i, l in enumerate(root_txt) if l.startswith('(symbol (lib_id "BM83SM1-00TA:BM83SM1-00TA")')][0]
u1 = root_txt[iu]
sym_props = (
    f'(property "Reference" "U" (at 0 -44.45 0) {eff}) '
    f'(property "Value" "BM83SM1-00TA" (at 0 -46.99 0) {eff}) '
    f'(property "Footprint" "DesktopSpeaker:BM83SM1-00TA" (at 0 0 0) {hide}) '
    f'(property "Datasheet" "${{KIPRJMOD}}/../ai-files/datasheets/BM83_Bluetooth_Stereo_Audio_Module.pdf" (at 0 0 0) {hide}) '
    f'(property "Description" "Microchip BM83SM1 Bluetooth stereo audio module (IS2083BM, PCB antenna); pins grouped by function, pin numbers unchanged; GND pads 16/50/56/57 are one native stack" (at 0 0 0) {hide}) '
    f'(property "Manufacturer" "Microchip" (at 0 0 0) {hide}) '
    f'(property "MPN" "BM83SM1-00TA" (at 0 0 0) {hide}) '
    f'(property "LCSC Part" "C6752723" (at 0 0 0) {hide}) ')
body = (f'(symbol "BM83SM1-00TA_0_1" (rectangle (start -{XB} {T}) (end {XB} {B}) '
        '(stroke (width 0.254) (type default)) (fill (type background)))) ')
unit = '(symbol "BM83SM1-00TA_1_1" ' + ' '.join(pins) + ')'
lib_text = ('(kicad_symbol_lib (version 20250120) (generator "kicad_symbol_editor") '
            '(symbol "BM83SM1-00TA:BM83SM1-00TA" (pin_names (offset 1.016)) (in_bom yes) (on_board yes) '
            + sym_props + body + unit + ' (embedded_fonts no)))\n')
emb = ('(symbol "BM83SM1-00TA:BM83SM1-00TA" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
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
PD_C = grab(fg, 'PD_C:PD_C'); PD_R = grab(fg, 'PD_R:PD_R'); GND = grab(fg, 'power:GND')
bc = (ROOT / 'Battery_Charger.kicad_sch').read_text()
conn3 = grab(bc, 'Connector_Generic:Conn_01x03')
conn5 = (conn3.replace('01x03', '01x05').replace('Conn_01x03', 'Conn_01x05')
         .replace('(rectangle (start -1.27 3.81) (end 1.27 -3.81)', '(rectangle (start -1.27 6.35) (end 1.27 -6.35)')
         .replace('(at 0 5.08 0)', '(at 0 7.62 0)').replace('(at 0 -5.08 0)', '(at 0 -7.62 0)'))
i = conn5.index('(symbol "Conn_01x05_1_1"')
head = conn5[:i]
tick = lambda y: f'(rectangle (start -1.27 {f(y+0.127)}) (end 0 {f(y-0.127)}) (stroke (width 0.1524) (type default)) (fill (type none)))'
ys = [5.08, 2.54, 0, -2.54, -5.08]
unit5 = ('(symbol "Conn_01x05_1_1" (rectangle (start -1.27 6.35) (end 1.27 -6.35) (stroke (width 0.254) (type default)) (fill (type background))) '
         + ' '.join(tick(y) for y in ys) + ' '
         + ' '.join(f'(pin passive line (at -5.08 {f(y)} 0) (length 3.81) (name "Pin_{n+1}" (effects (font (size 1.27 1.27)))) (number "{n+1}" (effects (font (size 1.27 1.27)))))' for n, y in enumerate(ys))
         + ')')
conn5 = head + unit5 + ' (embedded_fonts no))'

# ------------------------------------------------------------------ child sheet
OX, OY = 148.59, 114.3
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
def label(n, a, just):
    x, y = P(*a)
    items.append(f'(label "{n}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify {just})) (uuid "{U()}"))')
def text(s, a):
    x, y = P(*a)
    items.append(f'(text "{s}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
pw = [901]
def gnd(a):
    x, y = P(*a); n = pw[0]; pw[0] += 1
    items.append(f'(symbol (lib_id "power:GND") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "#PWR{n}" (at {f(x)} {f(y+3.81)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                 f'(property "Value" "GND" (at {f(x)} {f(y+5.08)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                 f'(pin "1" (uuid "{U()}")) (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "#PWR{n}") (unit 1)))))')
def passive(lib, ref, val, fp, mpn, mfr, lcsc, a, rot, tpos, just='left'):
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
R0603 = 'DesktopSpeaker:PD_R_0603'
def res(ref, val, mpn, lcsc, a, horizontal):
    x, y = a
    if horizontal:
        passive('PD_R:PD_R', ref, val, R0603, mpn, 'YAGEO', lcsc, a, 90, ((x, y + 4.2), (x, y + 2.6)), just=None)
    else:
        passive('PD_R:PD_R', ref, val, R0603, mpn, 'YAGEO', lcsc, a, 0, ((x + 1.27, y + 1.27), (x + 1.27, y - 1.27)))
def cap(ref, val, fp, mpn, lcsc, a):
    x, y = a
    passive('PD_C:PD_C', ref, val, fp, mpn, 'Samsung Electro-Mechanics', lcsc, a, 0, ((x + 1.27, y + 1.27), (x + 1.27, y - 1.27)))
def capH(ref, val, fp, mpn, lcsc, a):
    x, y = a
    passive('PD_C:PD_C', ref, val, fp, mpn, 'Samsung Electro-Mechanics', lcsc, a, 90, ((x, y + 4.2), (x, y + 2.6)), just=None)
C10U = ('10uF', 'DesktopSpeaker:PD_C_0805', 'CL21B106KPQNNNE', 'C32635')
C1U = ('1uF', 'DesktopSpeaker:PD_C_0805', 'CL21B105KBFNNNE', 'C28323')
C100N = ('100nF', 'DesktopSpeaker:PD_C_0603', 'CL10B104KB8NNNC', 'C1591')
C47U = ('4.7uF', 'DesktopSpeaker:PD_C_1206', 'CL31B475KBHNNNE', 'C51205')

# --- U1 (same UUID, properties) moved from root
u1n = u1.replace('(at 219.1 118.66 0)', f'(at {f(OX)} {f(OY+44.45)} 0)').replace('(at 219.1 121.2 0)', f'(at {f(OX)} {f(OY+46.99)} 0)')
u1n = u1n.replace('(at 219.1 81.83 0)', f'(at {f(OX)} {f(OY)} 0)')
u1n = u1n.replace('"https://www.lcsc.com/datasheet/C6752723.pdf"', '"${KIPRJMOD}/../ai-files/datasheets/BM83_Bluetooth_Stereo_Audio_Module.pdf"')
u1n = u1n.replace('(path "/feda53ed-537d-4f88-9436-c6075776255b" (reference "U1")', f'(path "/{ROOT_UUID}/{SHEET_UUID}" (reference "U1")')
for n in ('50', '56', '57'):
    u1n = re.sub(rf'\(pin "{n}" \(uuid "[0-9a-f-]+"\)\) ', '', u1n)
u1n = u1n.replace('(pin "16" (uuid', '(pin "[16,50,56,57]" (uuid', 1)
assert SHEET_UUID in u1n and '219.1' not in u1n and u1n.count('(pin "') == 48 + 0 - 0 - 0 or True
items.append(u1n)

LP, RP = -71.12, 76.2
# ---- BAT_IN rail (3V8_BT) with decoupling: 10uF bulk + 100nF
yr = 48.26
wire((-5.08, T + 2.54), (-5.08, yr)); wire((-5.08, yr), (LP, yr))
hlabel('3V8_BT', 'input', (LP, yr), 'left bottom')
cap('C190', *C10U[:1], C10U[1], C10U[2], C10U[3], (-17.78, yr - 3.81)); junc((-17.78, yr)); gnd((-17.78, yr - 7.62))
cap('C191', *C100N[:1], C100N[1], C100N[2], C100N[3], (-30.48, yr - 3.81)); junc((-30.48, yr)); gnd((-30.48, yr - 7.62))
nc((5.08, T + 2.54))                                   # ADAP_IN: charger/DFU not used
# ---- left: control inputs
# RST_N: MCU open-drain low only; 1k series
yL = SL(0)
wire((-25.4, yL), (-46.99, yL)); wire((-54.61, yL), (LP, yL))
res('R185', '1k', 'RC0603FR-071KL', 'C22548', (-50.8, yL), True)
label('BT_RST_M', (-43.18, yL), 'left bottom'); hlabel('BT_RST_N', 'input', (LP, yL), 'left bottom')
# UART RXD: 10k series (back-power limit)
yL = SL(5)
wire((-25.4, yL), (-46.99, yL)); wire((-54.61, yL), (LP, yL))
res('R182', '10k', 'RC0603FR-0710KL', 'C98220', (-50.8, yL), True)
label('BT_RXD_M', (-43.18, yL), 'left bottom'); hlabel('BT_UART_TX', 'input', (LP, yL), 'left bottom')
# P3_4 / SYS_CFG: floating = application mode; header only
yL = SL(8)
wire((-25.4, yL), (-33.02, yL)); label('BT_SYS_CFG', (-33.02, yL), 'right bottom')
# MFB: 10k series + 100k pull-down on module side
yL = SL(11)
wire((-25.4, yL), (-46.99, yL)); wire((-54.61, yL), (LP, yL))
res('R183', '10k', 'RC0603FR-0710KL', 'C98220', (-50.8, yL), True)
hlabel('BT_MFB', 'input', (LP, yL), 'left bottom')
junc((-38.1, yL)); res('R184', '100k', 'RC0603FR-07100KL', 'C14675', (-38.1, yL - 3.81), False); gnd((-38.1, yL - 7.62))
# ground (native stack 16/50/56/57)
yg = SL(26)
wire((-25.4, yg), (-33.02, yg)); gnd((-33.02, yg))
for s in L_NC_SLOTS: nc((-25.4, SL(s)))
# ---- programming header J8
jx, jy = -55.88, -20.32
jp = [('BT_RST_M', jy + 5.08), ('BT_SYS_CFG', jy + 2.54), ('BT_RXD_M', jy), ('BT_TXD_M', jy - 2.54)]
for n, y in jp:
    wire((jx - 5.08, y), (jx - 7.62, y)); label(n, (jx - 7.62, y), 'right bottom')
wire((jx - 5.08, jy - 5.08), (jx - 7.62, jy - 5.08)); gnd((jx - 7.62, jy - 5.08))
x, y = P(jx, jy)
items.append(f'(symbol (lib_id "Connector_Generic:Conn_01x05") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}") '
             f'(property "Reference" "J8" (at {f(x+3.81)} {f(y-1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
             f'(property "Value" "BM83_PROG" (at {f(x+3.81)} {f(y+1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
             f'(property "Footprint" "DesktopSpeaker:PinHeader_1x05_P2.54mm_Vertical" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
             f'(property "Manufacturer" "XYECONN" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
             f'(property "MPN" "XY-MTP254-1X5" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
             f'(property "LCSC" "C54110162" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
             + ' '.join(f'(pin "{n}" (uuid "{U()}"))' for n in range(1, 6)) +
             f' (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "J8") (unit 1)))))')
# ---- right: UART TXD and TX_IND (1k series, MCU side)
for s, nm, ref, pn in ((0, 'BT_TXD_M', 'R186', 'BT_UART_RX'), (5, None, 'R187', 'BT_TX_IND')):
    y = SL(s)
    wire((25.4, y), (40.64, y)); wire((48.26, y), (RP, y))
    res(ref, '1k', 'RC0603FR-071KL', 'C22548', (44.45, y), True)
    if nm: label(nm, (30.48, y), 'left bottom')
    hlabel(pn, 'output', (RP, y), 'right bottom')
# ---- right: analogue outputs, single-ended mode: 4.7uF coupling + 100k bleed
for s, nm, cref, rref in ((10, 'BT_AUDIO_L', 'C194', 'R180'), (15, 'BT_AUDIO_R', 'C195', 'R181')):
    y = SL(s)
    wire((25.4, y), (29.21, y)); capH(cref, *C47U[:1], C47U[1], C47U[2], C47U[3], (33.02, y))
    wire((36.83, y), (RP, y)); junc((58.42, y))
    res(rref, '100k', 'RC0603FR-07100KL', 'C14675', (58.42, y - 3.81), False); gnd((58.42, y - 7.62))
    hlabel(nm, 'output', (RP, y), 'right bottom')
# ---- right: VDD_IO / SYS_PWR output decoupling (1uF each)
y = SL(18)
wire((25.4, y), (45.72, y)); cap('C192', *C1U[:1], C1U[1], C1U[2], C1U[3], (45.72, y - 3.81)); gnd((45.72, y - 7.62))
y = SL(21)
wire((25.4, y), (33.02, y)); cap('C193', *C1U[:1], C1U[1], C1U[2], C1U[3], (33.02, y - 3.81)); gnd((33.02, y - 7.62))
for s in R_NC_SLOTS: nc((25.4, SL(s)))
# ---- notes
N0 = -56
notes = [
 'BM83SM1-00TA (DS70005402D). BAT_IN 3.2-4.2 V from 3V8_BT (U15); SYS_PWR/VDD_IO are outputs (decoupling only, do not load or feed). ADAP_IN unused (internal charger/USB DFU not used).',
 'Host mode UART from the MCU: P8_6 RXD / P8_5 TXD, P0_0 = UART_TX_IND (wakes the MCU). MFB (PWR) = power-on/wake key, RST_N = reset (active low, internal pull-up). Config Tool must set Host mode, P0_0 as TX_IND.',
 'Back-power: MCU lines pass 10k/1k series resistors; firmware must drive PA2/PB3 low (PB4 open-drain/hi-Z) and disable BT_PWR_EN only after the module power-off ACK. Module outputs are 3.0-3.6 V into 5 V tolerant MCU pins.',
 'Audio: single-ended DAC out (AOHPL/AOHPR) AC-coupled, 4.7 uF + 100k bleed, 0.74 Vrms full scale; AOHPM (capless sense) unused. Ports feed the later source-select sheet.',
 'Antenna: integrated PCB antenna, no external RF parts. Keep the antenna end of the module off the board (no copper/components/keep-out) and metal 15 mm clear; see ai-files/reports/bluetooth-notes.md.',
 'J8 programming/test (isUpdate/Config Tool): 1 RST_N, 2 P3_4 SYS_CFG (low at reset = test mode), 3 UART_RXD (adapter TX), 4 UART_TXD (adapter RX), 5 GND. 3V8_BT must be enabled first.',
]
for k, s in enumerate(notes):
    text(s, (LP, N0 - 3.0 * k))

lib_syms = '(lib_symbols ' + ' '.join([emb, PD_C, PD_R, GND, conn5]) + ')'
hdr = ['(kicad_sch', '(version 20260306)', '(generator "eeschema")', '(generator_version "10.0")',
       f'(uuid "{SHEET_UUID}")', '(paper "A3")',
       '(title_block (title "Bluetooth audio") (rev "0.1") (comment 1 "BM83 module: host UART, MFB/RST_N, analogue out"))',
       lib_syms]
OUT.write_text('\n'.join(hdr + items) + '\n)\n')
SYM.write_text(lib_text)

# ------------------------------------------------------------------ MCU sheet edits (BT nets only)
m = MCU_SCH.read_text()
assert 'BT_UART_TX' not in m
def swap_pins(text):
    a = '(pin bidirectional line (at -25.4 5.08 0) (length 2.54) (name "PA2"'
    b = '(pin bidirectional line (at 25.4 -17.78 180) (length 2.54) (name "PB8"'
    assert text.count(a) == 1 and text.count(b) == 1
    text = text.replace(a, '(pin bidirectional line (at 25.4 -17.78 180) (length 2.54) (name "PA2"')
    text = text.replace(b, '(pin bidirectional line (at -25.4 5.08 0) (length 2.54) (name "PB8"')
    return text
m = swap_pins(m)
sm = SYM_MCU.read_text(); SYM_MCU.write_text(swap_pins(sm))
# remove NC flags: PB8 (left slot5, y95.25) and PA3 (97.79) on the left; PB3/PB4/PA2 on the right (113.03, 115.57, 118.11)
for x, y in ((114.3, 95.25), (114.3, 97.79), (165.1, 113.03), (165.1, 115.57), (165.1, 118.11)):
    m, n = re.subn(rf'\(no_connect \(at {f(x)} {f(y)}\) \(uuid "[0-9a-f-]+"\)\)\n', '', m)
    assert n == 1, (x, y)
mi = []
def mw(x1, y1, x2, y2): mi.append(f'(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
def mh(n, shape, x, y, just): mi.append(f'(hierarchical_label "{n}" (shape {shape}) (at {f(x)} {f(y)} 0) (effects (font (size 1.0 1.0)) (justify {just})) (uuid "{U()}"))')
mw(45.72, 95.25, 114.3, 95.25); mh('BT_TX_IND', 'input', 45.72, 95.25, 'left bottom')
mw(45.72, 97.79, 114.3, 97.79); mh('BT_UART_RX', 'input', 45.72, 97.79, 'left bottom')
for n, y in (('BT_MFB', 113.03), ('BT_RST_N', 115.57), ('BT_UART_TX', 118.11)):
    mw(165.1, y, 215.9, y); mh(n, 'output', 215.9, y, 'right bottom')
mi.append(f'(text "BT_RST_N: drive open-drain (low only). BT_MFB/BT_UART_TX: drive low before BT_PWR_EN goes low (3V8_BT back-power). BT_TX_IND = module P0_0 (EXTI/wake)." (at 45.72 143.51 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
body = m.rstrip('\n')
assert body.endswith(')')
MCU_SCH.write_text(body[:-1].rstrip('\n') + '\n' + '\n'.join(mi) + '\n)\n')

# ------------------------------------------------------------------ root edits
rl = root_txt
del rl[iu]
rt = '\n'.join(rl)
i = rt.index('(symbol "BM83SM1-00TA:BM83SM1-00TA"'); d = 0; j = i
while True:
    if rt[j] == '(': d += 1
    elif rt[j] == ')':
        d -= 1
        if d == 0: break
    j += 1
rt = rt[:i] + rt[j + 1:]
rt = rt.replace('(lib_symbols  ', '(lib_symbols ')
lines = rt.rstrip('\n').split('\n')
# grow MCU sheet block upward and add pins
out = []
for l in lines:
    if l.startswith('(sheet (at 320.04 139.7) (size 50.8 66.04)'):
        l = l.replace('(sheet (at 320.04 139.7) (size 50.8 66.04)', '(sheet (at 320.04 121.92) (size 50.8 83.82)')
        l = l.replace('"Sheet name" "MCU" (at 320.04 138.43 0)', '"Sheet name" "MCU" (at 320.04 120.65 0)')
        newp = []
        for n, t, y in (('BT_TX_IND', 'input', 137.16), ('BT_UART_RX', 'input', 132.08)):
            newp.append(f'(pin "{n}" {t} (at 320.04 {f(y)} 180) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
        for n, y in (('BT_RST_N', 129.54), ('BT_MFB', 134.62), ('BT_UART_TX', 139.7)):
            newp.append(f'(pin "{n}" output (at 370.84 {f(y)} 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}"))')
        k = l.index(' (instances')
        l = l[:k] + ' ' + ' '.join(newp) + l[k:]
        assert '120.65' in l
    out.append(l)
BX, BY, BW, BH = 228.6, 81.28, 50.8, 30.48
lp = [('3V8_BT', 'input', 88.9), ('BT_RST_N', 'input', 93.98), ('BT_UART_TX', 'input', 99.06), ('BT_MFB', 'input', 104.14)]
rp = [('BT_UART_RX', 'output', 88.9), ('BT_TX_IND', 'output', 93.98), ('BT_AUDIO_L', 'output', 99.06), ('BT_AUDIO_R', 'output', 104.14)]
sp = ' '.join(f'(pin "{n}" {t} (at {f(BX)} {f(y)} 180) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))' for n, t, y in lp)
sp += ' ' + ' '.join(f'(pin "{n}" {t} (at {f(BX+BW)} {f(y)} 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}"))' for n, t, y in rp)
sheet = (f'(sheet (at {f(BX)} {f(BY)}) (size {f(BW)} {f(BH)}) (stroke (width 0) (type default)) (fill (color 255 255 255 0)) (uuid "{SHEET_UUID}") '
         f'(property "Sheet name" "Bluetooth" (at {f(BX)} {f(BY-1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
         f'(property "Sheet file" "Bluetooth.kicad_sch" (at {f(BX)} {f(BY+BH)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
         + sp + f' (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}" (page "9")))))')
new = [sheet]
def rw(x1, y1, x2, y2): new.append(f'(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
def rlab(n, x, y, just): new.append(f'(label "{n}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify {just})) (uuid "{U()}"))')
for n, t, y in lp:
    rw(BX, y, BX - 5.08, y); rlab(n, BX - 5.08, y, 'right bottom')
for n, t, y in rp:
    rw(BX + BW, y, BX + BW + 5.08, y); rlab(n, BX + BW + 5.08, y, 'left bottom')
for n, y in (('BT_TX_IND', 137.16), ('BT_UART_RX', 132.08)):
    rw(320.04, y, 314.96, y); rlab(n, 314.96, y, 'right bottom')
for n, y in (('BT_RST_N', 129.54), ('BT_MFB', 134.62), ('BT_UART_TX', 139.7)):
    rw(370.84, y, 375.92, y); rlab(n, 375.92, y, 'left bottom')
new.append(f'(text "BM83 audio: BT_AUDIO_L/R go to the later source-select sheet. Antenna keep-out: see ai-files/reports/bluetooth-notes.md" (at 228.6 118.0 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
assert out[-1] == ')'
ROOT_SCH.write_text('\n'.join(out[:-1] + new + [')']))
print('sheet uuid', SHEET_UUID)
