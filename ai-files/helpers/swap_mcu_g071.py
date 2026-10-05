#!/usr/bin/env python3
"""Swap U3 STM32G031K8T6 -> STM32G071RBT6 (LQFP64) on MCU.kicad_sch, add CHG_QON_SENSE.

Guarded: refuses to run if kicad-library/schematic/STM32G071RBT6.kicad_sym already exists.
Edits MCU.kicad_sch, Battery_Charger.kicad_sch, DesktopSpeaker.kicad_sch (root), sym-lib-table.
Footprint/STEP are copied separately (stock KiCad LQFP-64_10x10mm_P0.5mm).
"""
import re, sys, uuid, pathlib

ROOT = pathlib.Path('/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad')
SYMF = ROOT / 'kicad-library/schematic/STM32G071RBT6.kicad_sym'
if SYMF.exists():
    sys.exit('already done; refusing')
U = lambda: str(uuid.uuid4())
f = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')
ROOT_UUID = 'feda53ed-537d-4f88-9436-c6075776255b'
BC_UUID = 'a7066d55-4393-49f1-9dcb-c2e9f1db9549'

# ------------------------------------------------ pin table (DS12232 Rev 2, Table 12, LQFP64)
# (pin number, datasheet name, signal).  'R:' = reserved (labelled no-connect), None = spare.
LEFT = [
    ('3', 'PC13', 'CHG_QON_SENSE'), ('4', 'PC14-OSC32_IN', 'PD_PLUG_EVENT'), ('5', 'PC15-OSC32_OUT', 'CHG_INT'),
    ('17', 'PA0', 'GAUGE_ALRT_N'), ('63', 'PB9', 'PD_SINK_EN'), ('62', 'PB8', 'BT_TX_IND'), ('20', 'PA3', 'BT_UART_RX'),
    ('25', 'PC4', 'R:AMP_FAULT_N'), ('26', 'PC5', 'R:ADC_INT'), ('28', 'PB1', 'R:HP_DET'), ('29', 'PB2', 'R:AUX_DET'),
    ('27', 'PB0', 'R:USB_SRC_DET'), ('18', 'PA1', 'R:BTN_ADC'),
    ('12', 'PF2-NRST', 'NRST'),
    ('22', 'PA5', None), ('47', 'PA15', None), ('32', 'PB12', None), ('48', 'PC8', None), ('49', 'PC9', None),
    ('64', 'PC10', None), ('1', 'PC11', None), ('2', 'PC12', None), ('56', 'PD6', None), ('40', 'PD8', None),
    ('41', 'PD9', None), ('10', 'PF0-OSC_IN', None), ('11', 'PF1-OSC_OUT', None)]
RIGHT = [
    ('45', 'PA13-SWDIO', 'SWDIO'), ('46', 'PA14-BOOT0', 'SWCLK'),
    ('61', 'PB7', 'CTRL_SDA'), ('60', 'PB6', 'CTRL_SCL'),
    ('31', 'PB11', 'R:AUD_SDA'), ('30', 'PB10', 'R:AUD_SCL'),
    ('44', 'PA12[PA10]', 'PDCTRL_SDA'), ('43', 'PA11[PA9]', 'PDCTRL_SCL'),
    ('42', 'PA10', 'CHG_SYS_ENABLE'), ('38', 'PC6', 'CHG_ENABLE'), ('37', 'PA9', 'BT_FORCE_PWM'), ('36', 'PA8', 'BT_PWR_EN'),
    ('59', 'PB5', '5V_LOGIC_EN'), ('57', 'PB3', 'BT_MFB'), ('58', 'PB4', 'BT_RST_N'), ('19', 'PA2', 'BT_UART_TX'),
    ('23', 'PA6', 'R:AMP_PDN'), ('24', 'PA7', 'R:AMP_BOOST_EN'), ('39', 'PC7', 'R:CODEC_PWR_EN'),
    ('13', 'PC0', 'R:HP_SEL_A'), ('14', 'PC1', 'R:HP_SEL_B'), ('15', 'PC2', 'R:HP_EN'), ('16', 'PC3', 'R:HP_G0'),
    ('21', 'PA4', 'R:HP_G1'), ('33', 'PB13', 'R:LED_R'), ('34', 'PB14', 'R:LED_G'), ('35', 'PB15', 'R:LED_B'),
    ('50', 'PD0', 'R:USB_DATA_SEL'), ('51', 'PD1', 'R:USB_DATA_OE_N'), ('52', 'PD2', 'R:CODEC_SSPND'),
    ('53', 'PD3', 'R:USB_HID_MUTE'), ('54', 'PD4', 'R:USB_HID_VOLUP'), ('55', 'PD5', 'R:USB_HID_VOLDN')]
SHAPE = {'CTRL_SDA': 'bidirectional', 'CTRL_SCL': 'bidirectional', 'PDCTRL_SDA': 'bidirectional',
         'PDCTRL_SCL': 'bidirectional', 'CHG_SYS_ENABLE': 'output', 'CHG_ENABLE': 'output',
         'BT_FORCE_PWM': 'output', 'BT_PWR_EN': 'output', '5V_LOGIC_EN': 'output', 'BT_MFB': 'output',
         'BT_RST_N': 'output', 'BT_UART_TX': 'output'}
POWER_TOP = [('6', 'VBAT', -5.08), ('7', 'VREF+', 0.0), ('8', 'VDD/VDDA', 5.08)]
POWER_BOT = [('9', 'VSS/VSSA', -10.16)]
allpins = [p[0] for p in LEFT + RIGHT] + [p[0] for p in POWER_TOP + POWER_BOT]
assert sorted(map(int, allpins)) == list(range(1, 65)), sorted(map(int, allpins))

OX, OY = 139.7, 123.19
XL, XR = OX - 25.4, OX + 25.4
Y0 = 82.55
slot = lambda k: Y0 + 2.54 * k
LP, RP = 45.72, 215.9

eff = '(effects (font (size 1.27 1.27)))'
hide = '(effects (font (size 1.27 1.27)) (hide yes))'
def sympin(t, x, y, a, name, num):
    return f'(pin {t} line (at {f(x)} {f(y)} {a}) (length 2.54) (name "{name}" {eff}) (number "{num}" {eff}))'
pins = []
for k, (n, nm, s_) in enumerate(LEFT):
    pins.append(sympin('bidirectional', -25.4, 40.64 - 2.54 * k, 0, nm, n))
for k, (n, nm, s_) in enumerate(RIGHT):
    pins.append(sympin('bidirectional', 25.4, 40.64 - 2.54 * k, 180, nm, n))
for n, nm, x in POWER_TOP:
    pins.append(sympin('power_in', x, 45.72, 270, nm, n))
for n, nm, x in POWER_BOT:
    pins.append(sympin('power_in', x, -45.72, 90, nm, n))
DS = '${KIPRJMOD}/../ai-files/datasheets/STM32G071x8_xB.pdf'
sym_props = (
    f'(property "Reference" "U" (at 0 -46.5 0) {eff}) '
    f'(property "Value" "STM32G071RBT6" (at 0 -49 0) {eff}) '
    f'(property "Footprint" "DesktopSpeaker:STM32G071RBT6" (at 0 0 0) {hide}) '
    f'(property "Datasheet" "{DS}" (at 0 0 0) {hide}) '
    f'(property "Manufacturer" "STMicroelectronics" (at 0 0 0) {hide}) '
    f'(property "MPN" "STM32G071RBT6" (at 0 0 0) {hide}) '
    f'(property "LCSC Part" "C432213" (at 0 0 0) {hide}) '
    f'(property "Description" "Arm Cortex-M0+ 64 MHz, 128 KB flash, 36 KB RAM, LQFP64 10x10 mm (DS12232 Rev 2); pins grouped by function: inputs left, outputs/buses/SWD right, supply top, ground bottom" (at 0 0 0) {hide}) ')
body = ('(symbol "STM32G071RBT6_0_1" (rectangle (start -22.86 43.18) (end 22.86 -43.18) '
        '(stroke (width 0.254) (type default)) (fill (type background)))) ')
unit = '(symbol "STM32G071RBT6_1_1" ' + ' '.join(pins) + ')'
SYMF.write_text('(kicad_symbol_lib (version 20250120) (generator "kicad_symbol_editor") '
                '(symbol "STM32G071RBT6:STM32G071RBT6" (pin_names (offset 1.016)) (in_bom yes) (on_board yes) '
                + sym_props + body + unit + ' (embedded_fonts no)))\n')
emb = ('(symbol "STM32G071RBT6:STM32G071RBT6" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes) '
       '(in_pos_files yes) (duplicate_pin_numbers_are_jumpers no) ' + sym_props + body + unit + ' (embedded_fonts no))')

st = ROOT / 'sym-lib-table'
s = st.read_text()
entry = ('  (lib (name "STM32G071RBT6") (type "KiCad") (uri "${KIPRJMOD}/kicad-library/schematic/STM32G071RBT6.kicad_sym") '
         '(options "") (descr "STMicroelectronics STM32G071 MCU"))\n')
s = s.replace('  (lib (name "BQ25895RTWR")', entry + '  (lib (name "BQ25895RTWR")', 1)
st.write_text(s)

def match_close(t, i):
    d = 0; j = i
    while True:
        c = t[j]
        if c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: return j
        elif c == '"':
            j += 1
            while t[j] != '"':
                if t[j] == '\\': j += 1
                j += 1
        j += 1

mcu = (ROOT / 'MCU.kicad_sch').read_text()
i = mcu.index('(symbol "STM32G031K8T6:STM32G031K8T6"'); j = match_close(mcu, i)
mcu = mcu[:i] + emb + mcu[j + 1:]
lines = mcu.split('\n')
u3_old = [l for l in lines if l.startswith('(symbol (lib_id "STM32G031K8T6')][0]
tmpl_c160 = [l for l in lines if l.startswith('(symbol (lib_id "PD_C:PD_C")') and '"C160"' in l][0]
gnd_tmpl = [l for l in lines if l.startswith('(symbol (lib_id "power:GND") (at 127 124.46')][0]
r160 = [l for l in lines if l.startswith('(symbol (lib_id "PD_R:PD_R")') and '"R160"' in l][0]

def xy_in(l):
    return [(float(a), float(b)) for a, b in re.findall(r'\((?:xy|at) ([-\d.]+) ([-\d.]+)', l)]
keep = []
for l in lines:
    if l.startswith('(symbol (lib_id "STM32G031K8T6'): continue
    if l.startswith('(hierarchical_label') or l.startswith('(no_connect'): continue
    if l.startswith('(junction') and abs(xy_in(l)[0][1] - 66.04) < 1e-6: continue
    if l.startswith('(wire'):
        pts = xy_in(l)
        if any(abs(x - 45.72) < 1e-6 or abs(x - 215.9) < 1e-6 or abs(x - 114.3) < 1e-6 or abs(x - 133.35) < 1e-6 for x, y in pts): continue
        if any(abs(x - 125.73) < 1e-6 and abs(y - 66.04) < 1e-6 for x, y in pts): continue
    if l.startswith('(label "NRST" (at 109.22 118.11'): continue
    if l.startswith('(text "Reserved') or l.startswith('(text "3V_AO supply') or l.startswith('(text "BT_RST_N'): continue
    if l == gnd_tmpl: continue
    keep.append(l)
items = []

u3 = u3_old
u3 = u3.replace('(lib_id "STM32G031K8T6:STM32G031K8T6") (at 139.7 100.33 0)', f'(lib_id "STM32G071RBT6:STM32G071RBT6") (at {f(OX)} {f(OY)} 0)')
u3 = re.sub(r'\(property "Reference" "U3" \(at [\d. ]+\)', f'(property "Reference" "U3" (at {f(OX)} {f(OY+46.74)} 0)', u3)
u3 = re.sub(r'\(property "Value" "STM32G031K8T6" \(at [\d. ]+\)', f'(property "Value" "STM32G071RBT6" (at {f(OX)} {f(OY+49.28)} 0)', u3)
u3 = u3.replace('DesktopSpeaker:STM32G031K8T6', 'DesktopSpeaker:STM32G071RBT6')
u3 = re.sub(r'\(property "Datasheet" "[^"]*"', '(property "Datasheet" "https://lcsc.com/product-detail/ST-Microelectronics_STMicroelectronics-STM32G071RBT6_C432213.html"', u3)
u3 = u3.replace('"MPN" "STM32G031K8T6"', '"MPN" "STM32G071RBT6"').replace('"LCSC Part" "C432203"', '"LCSC Part" "C432213"')
u3 = u3.replace('(at 139.7 100.33 0)', f'(at {f(OX)} {f(OY)} 0)')
pinblk = ' '.join(f'(pin "{n}" (uuid "{U()}"))' for n in sorted(allpins, key=int))
u3 = re.sub(r'(\(pin "\d+" \(uuid "[^"]+"\)\) ?)+', pinblk + ' ', u3, count=1)
assert 'G031' not in u3, u3[:600]
items.append(u3)

def wire(x1, y1, x2, y2): items.append(f'(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
def junc(x, y): items.append(f'(junction (at {f(x)} {f(y)}) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')
def nc(x, y): items.append(f'(no_connect (at {f(x)} {f(y)}) (uuid "{U()}"))')
def label(n, x, y, just): items.append(f'(label "{n}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify {just})) (uuid "{U()}"))')
def hlabel(n, shape, x, y, just): items.append(f'(hierarchical_label "{n}" (shape {shape}) (at {f(x)} {f(y)} 0) (effects (font (size 1.0 1.0)) (justify {just})) (uuid "{U()}"))')
def text(t, x, y, just='left bottom'): items.append(f'(text "{t}" (at {f(x)} {f(y)} 0) (effects (font (size 1 1)) (justify {just})) (uuid "{U()}"))')

for k, (n, nm, sig) in enumerate(LEFT):
    y = slot(k)
    if sig is None:
        nc(XL, y)
    elif sig.startswith('R:'):
        nc(XL, y); text(sig[2:] + ' (reserved)', XL - 3.81, y + 0.4, 'right bottom')
    elif sig == 'NRST':
        wire(XL, y, 106.68, y); wire(106.68, y, 106.68, 118.11); label('NRST', 109.22, y, 'left bottom')
    else:
        wire(LP, y, XL, y); hlabel(sig, 'input', LP, y, 'left bottom')
for k, (n, nm, sig) in enumerate(RIGHT):
    y = slot(k)
    if sig in ('SWDIO', 'SWCLK'):
        continue                       # SWD wiring kept from the previous sheet
    if sig.startswith('R:'):
        nc(XR, y); text(sig[2:] + ' (reserved)', XR + 3.81, y + 0.4, 'left bottom')
    else:
        wire(XR, y, RP, y); hlabel(sig, SHAPE[sig], RP, y, 'right bottom')

ry = 66.04
vx = {n: OX + x for n, nm, x in POWER_TOP}
ytop = OY - 45.72
for n in ('6', '7', '8'):
    wire(vx[n], ytop, vx[n], ry)
xs = [LP, 113.03, 125.73, vx['6'], vx['7'], vx['8'], 152.4, 160.02]
for a, b in zip(xs, xs[1:]):
    wire(a, ry, b, ry)
hlabel('3V_AO', 'input', LP, ry, 'left bottom')
for x in (113.03, 125.73, vx['6'], vx['7'], 152.4): junc(x, ry)

def make_cap(tmpl, ref, val, x, mpn, lcsc):
    m = re.search(r'\(at ([-\d.]+) ([-\d.]+) 0\)', tmpl); cx, cy = float(m.group(1)), float(m.group(2))
    sh = lambda mm: '(at %s %s %s)' % (f(float(mm.group(1)) - cx + x), f(float(mm.group(2)) - cy + ry + 3.81), mm.group(3))
    l = re.sub(r'\(at ([-\d.]+) ([-\d.]+) (\d+)\)', sh, tmpl)
    l = re.sub(r'\(uuid "[^"]+"\)', lambda mm: f'(uuid "{U()}")', l)
    l = re.sub(r'\(property "Reference" "[^"]+"', f'(property "Reference" "{ref}"', l)
    l = re.sub(r'\(property "Value" "[^"]+"', f'(property "Value" "{val}"', l)
    l = re.sub(r'\(reference "[^"]+"\)', f'(reference "{ref}")', l)
    l = re.sub(r'\(property "MPN" "[^"]+"', f'(property "MPN" "{mpn}"', l)
    l = re.sub(r'\(property "LCSC" "[^"]+"', f'(property "LCSC" "{lcsc}"', l)
    if ref == 'C164': l = re.sub(r'\(property "Datasheet" "[^"]*"', '(property "Datasheet" ""', l)
    return l
def gnd_at(x, y, n):
    m = re.search(r'\(at ([-\d.]+) ([-\d.]+) 0\)', gnd_tmpl); cx, cy = float(m.group(1)), float(m.group(2))
    l = re.sub(r'\(at ([-\d.]+) ([-\d.]+) (\d+)\)', lambda q: '(at %s %s %s)' % (f(float(q.group(1)) - cx + x), f(float(q.group(2)) - cy + y), q.group(3)), gnd_tmpl)
    l = re.sub(r'\(uuid "[^"]+"\)', lambda q: f'(uuid "{U()}")', l)
    return re.sub(r'#PWR\d+', f'#PWR{n}', l)
items.append(make_cap(tmpl_c160, 'C163', '100nF', 152.4, 'CL10B104KB8NNNC', 'C1591'))
items.append(gnd_at(152.4, ry + 7.62, 910))
items.append(make_cap(tmpl_c160, 'C164', '1uF', 160.02, 'CL10A105KB8NNNC', 'C15849'))
items.append(gnd_at(160.02, ry + 7.62, 911))
vss_x = OX + POWER_BOT[0][2]; vss_y = OY + 45.72
wire(vss_x, vss_y, vss_x, vss_y + 2.54)
items.append(gnd_at(vss_x, vss_y + 2.54, 912))

text('3V_AO supply: VDD/VDDA 100nF + 4.7uF (DS12232 fig. 13); VREF+ 100nF + 1uF (VREFBUF off, VREF+ = VDDA); VBAT tied to VDD (no backup cell); NRST 100nF, internal pull-up', LP, 61.0)
text('Reserved (no-connect, labelled): signals of sections 7-9 and open sections; see ai-files/reports/mcu-pin-allocation.md. Unlabelled no-connects on the left are spare GPIO.', LP, 181.0)
text('BT_RST_N: drive open-drain (low only). BT_MFB/BT_UART_TX: drive low before BT_PWR_EN goes low (3V8_BT back-power). BT_TX_IND = module P0_0 (EXTI/wake).', LP, 184.0)
text('PDCTRL_SDA/SCL: software (bit-banged) I2C on PA12/PA11, open-drain, pull-ups on the PD sheet. AUD_SDA/SCL reserved on hardware I2C2 (PB11/PB10 AF6). CHG_QON_SENSE: PC13 (WKUP), input only.', LP, 187.0)

out = [l.replace('STM32G031K8T6: supply, reset/boot, SWD and connections to captured power blocks',
                 'STM32G071RBT6 (LQFP64): supply, reset/boot, SWD and connections to captured power blocks; reserved audio/UI pins') for l in keep]
while out[-1].strip() == '': out.pop()
assert out[-1] == ')'
out = out[:-1] + items + [')']
(ROOT / 'MCU.kicad_sch').write_text('\n'.join(out) + '\n')

# ------------------------------------------------ Battery_Charger: QON sense (R113 100k, high impedance tap)
bcp = ROOT / 'Battery_Charger.kicad_sch'
bc = bcp.read_text()
m = re.search(r'\(at ([-\d.]+) ([-\d.]+) 0\)', r160); cx, cy = float(m.group(1)), float(m.group(2))
rx, rcy = 198.12, 152.4
rsh = lambda mm: '(at %s %s %s)' % (f(float(mm.group(1)) - cx + rx), f(float(mm.group(2)) - cy + rcy), mm.group(3))
r113 = re.sub(r'\(at ([-\d.]+) ([-\d.]+) (\d+)\)', rsh, r160)
r113 = re.sub(r'\(uuid "[^"]+"\)', lambda mm: f'(uuid "{U()}")', r113)
r113 = r113.replace('"R160"', '"R113"').replace('/feda53ed-537d-4f88-9436-c6075776255b/4ab2b160-efba-45d8-be2c-c7b2862cfacf', f'/{ROOT_UUID}/{BC_UUID}')
assert '"R113"' in r113 and BC_UUID in r113
add = [r113]
def bw(x1, y1, x2, y2): add.append(f'(wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
bw(rx, 142.24, rx, rcy - 3.81)
add.append(f'(junction (at {f(rx)} 142.24) (diameter 0) (color 0 0 0 0) (uuid "{U()}"))')
bw(rx, rcy + 3.81, rx, rcy + 7.62)
add.append(f'(label "CHG_QON_SENSE" (at {f(rx)} {f(rcy+7.62)} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
bw(381.0, 187.96, 391.16, 187.96)
add.append(f'(label "CHG_QON_SENSE" (at 381.0 187.96 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}"))')
add.append(f'(hierarchical_label "CHG_QON_SENSE" (shape output) (at 391.16 187.96 0) (effects (font (size 1.0 1.0)) (justify right bottom)) (uuid "{U()}"))')
k = bc.rstrip().rfind(')')
bcp.write_text(bc[:k] + '\n'.join(add) + '\n)\n')

# ------------------------------------------------ root: sheet pins + stubs
rp = ROOT / 'DesktopSpeaker.kicad_sch'
rt = rp.read_text()
a = rt.index('(property "Sheet name" "Battery_Charger"'); a = rt.index('(pin "VBUS_PD"', a)
rt = rt[:a] + f'(pin "CHG_QON_SENSE" output (at 219.71 187.96 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}")) ' + rt[a:]
b = rt.index('(property "Sheet name" "MCU"'); b = rt.index('(pin "3V_AO"', b)
rt = rt[:b] + f'(pin "CHG_QON_SENSE" input (at 320.04 142.24 180) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}")) ' + rt[b:]
stubs = [
    f'(wire (pts (xy 219.71 187.96) (xy 224.79 187.96)) (stroke (width 0) (type default)) (uuid "{U()}"))',
    f'(label "CHG_QON_SENSE" (at 224.79 187.96 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))',
    f'(wire (pts (xy 320.04 142.24) (xy 314.96 142.24)) (stroke (width 0) (type default)) (uuid "{U()}"))',
    f'(label "CHG_QON_SENSE" (at 314.96 142.24 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}"))']
k = rt.rstrip().rfind(')')
rp.write_text(rt[:k] + '\n'.join(stubs) + '\n)\n')
print('ok')
