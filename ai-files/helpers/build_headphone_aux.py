#!/usr/bin/env python3
"""Create Headphone_Aux.kicad_sch (U8/U9 TS5A23157 mux, U10 TPA6132A2, J2 HEAD_OUT, J3 AUX_IN, D200/D201 ESD, passives),
move those parts out of the root keeping reference/value/UUID, add the root sheet block, connect the MCU reserved signals,
and fix the library symbols (functional pin grouping; pad numbers unchanged).  Guarded: refuses to run if the sheet exists.
Run from a clean tree.  Python 3, no dependencies."""
import re, sys, uuid, pathlib, shutil

ROOT = pathlib.Path('/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad')
LIB = ROOT / 'kicad-library/schematic'
FP = ROOT / 'kicad-library/footprint'
M3D = ROOT / 'kicad-library/3d'
OUT = ROOT / 'Headphone_Aux.kicad_sch'
if OUT.exists():
    sys.exit('Headphone_Aux.kicad_sch exists; refusing')
ROOT_UUID = 'feda53ed-537d-4f88-9436-c6075776255b'
SHEET_UUID = str(uuid.uuid4())
U = lambda: str(uuid.uuid4())
f = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')
eff = '(effects (font (size 1.27 1.27)))'
hide = '(effects (font (size 1.27 1.27)) (hide yes))'

# ------------------------------------------------------------------ library symbols
def pin(t, x, y, a, name, num, ln=2.54):
    return f'(pin {t} line (at {f(x)} {f(y)} {a}) (length {f(ln)}) (name "{name}" {eff}) (number "{num}" {eff}))'

def make_sym(name, ref, ref_at, val_at, props, body, pins, hide_names=False):
    pn = '(pin_names (offset 1.016) (hide yes))' if hide_names else '(pin_names (offset 1.016))'
    base = (f'(property "Reference" "{ref}" (at {f(ref_at[0])} {f(ref_at[1])} 0) {eff}) '
            f'(property "Value" "{name}" (at {f(val_at[0])} {f(val_at[1])} 0) {eff}) '
            + ''.join(f'(property "{k}" "{v}" (at 0 0 0) {hide}) ' for k, v in props))
    unit = f'(symbol "{name}_0_1" {body}) (symbol "{name}_1_1" ' + ' '.join(pins) + ')'
    lib = (f'(kicad_symbol_lib (version 20250120) (generator "kicad_symbol_editor") (symbol "{name}" {pn} '
           f'(in_bom yes) (on_board yes) ' + base + unit + ' (embedded_fonts no)))\n')
    emb = (f'(symbol "{name}:{name}" {pn} (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) '
           f'(duplicate_pin_numbers_are_jumpers no) ' + base + unit + ' (embedded_fonts no))')
    return lib, emb

def rect(x1, y1, x2, y2):
    return f'(rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width 0.254) (type default)) (fill (type background)))'

DS = '${KIPRJMOD}/../ai-files/datasheets/'
# --- TS5A23157DGSR (VSSOP-10 DGS, SCDS165F table 5): 1 IN1, 2 NO1, 3 GND, 4 NO2, 5 IN2, 6 COM2, 7 NC2, 8 V+, 9 NC1, 10 COM1
ts_pins = [pin('passive', -17.78, 7.62, 0, 'NC1', '9'), pin('passive', -17.78, 5.08, 0, 'NC2', '7'),
           pin('passive', -17.78, 2.54, 0, 'NO1', '2'), pin('passive', -17.78, 0, 0, 'NO2', '4'),
           pin('input', -17.78, -7.62, 0, 'IN1', '1'), pin('input', -17.78, -10.16, 0, 'IN2', '5'),
           pin('passive', 17.78, 7.62, 180, 'COM1', '10'), pin('passive', 17.78, 5.08, 180, 'COM2', '6'),
           pin('power_in', 10.16, 15.24, 270, 'V+', '8'), pin('power_in', 10.16, -15.24, 90, 'GND', '3')]
ts_lib, ts_emb = make_sym('TS5A23157DGSR', 'U', (0, -14.6), (0, -16.5), [
    ('Footprint', 'DesktopSpeaker:TS5A23157DGSR'), ('Datasheet', DS + 'TS5A23157.pdf'),
    ('Manufacturer', 'Texas Instruments'), ('MPN', 'TS5A23157DGSR'), ('LCSC Part', 'C11133'),
    ('Description', 'Dual SPDT analog switch (2 x 1:2), 1.65-5.5 V, ~10 ohm, VSSOP-10 (DGS); pins grouped by function, pad numbers per SCDS165F')],
    rect(-15.24, 12.7, 15.24, -12.7), ts_pins)

# --- TPA6132A2RTER (WQFN-16 RTE + EP, SLOS597B): pads 2,3,10,17 are one native stack (all ground)
tp_pins = [pin('passive', -17.78, 12.7, 0, 'INL-', '1'), pin('passive', -17.78, 2.54, 0, 'INR-', '4'),
           pin('input', -17.78, -10.16, 0, 'EN', '13'), pin('input', -17.78, -12.7, 0, 'G0', '6'), pin('input', -17.78, -15.24, 0, 'G1', '7'),
           pin('passive', 17.78, 12.7, 180, 'OUTL', '16'), pin('passive', 17.78, 5.08, 180, 'OUTR', '5'), pin('passive', 17.78, 2.54, 180, 'SGND', '15'),
           pin('passive', 17.78, -5.08, 180, 'HPVDD', '12'), pin('passive', 17.78, -12.7, 180, 'HPVSS', '8'),
           pin('passive', 17.78, -20.32, 180, 'CPP', '11'), pin('passive', 17.78, -27.94, 180, 'CPN', '9'),
           pin('power_in', -7.62, 20.32, 270, 'VDD', '14'),
           pin('power_in', -10.16, -33.02, 90, 'GND', '[2,3,10,17]')]
tp_lib, tp_emb = make_sym('TPA6132A2RTER', 'U', (0, -49.9), (0, -51.8), [
    ('Footprint', 'DesktopSpeaker:TPA6132A2RTER'), ('Datasheet', DS + 'TPA6132A2.pdf'),
    ('Manufacturer', 'Texas Instruments'), ('MPN', 'TPA6132A2RTER'), ('LCSC Part', 'C69901'),
    ('Description', '25 mW capless stereo headphone amplifier with charge pump, WQFN-16 (RTE). GND stack = INL+ (2), INR+ (3), PGND (10), thermal pad (17); SGND (15) is separate for the jack sleeve')],
    rect(-15.24, 17.78, 15.24, -30.48), tp_pins)

# --- PESD5V0S2BT (SOT-23): 1 = K1, 2 = K2, 3 = common (VERIFY pin 3 against the Nexperia datasheet)
es_pins = [pin('passive', -6.35, 2.54, 0, '~', '1'), pin('passive', -6.35, -2.54, 0, '~', '2'), pin('passive', 0, -7.62, 90, '~', '3')]
es_body = (rect(-3.81, 5.08, 3.81, -5.08) +
           '(text "TVS" (at 0 0 0) (effects (font (size 1.27 1.27))))')
es_lib, es_emb = make_sym('PESD5V0S2BT', 'D', (7.62, 1.27), (7.62, -1.27), [
    ('Footprint', 'DesktopSpeaker:PESD5V0S2BT'), ('Datasheet', DS + 'PESD5V0S2BT.pdf'),
    ('Manufacturer', 'Nexperia'), ('MPN', 'PESD5V0S2BT'), ('LCSC Part', 'C5380400'),
    ('Description', 'Bidirectional two-line 5 V ESD protection diode, SOT-23: lines 1 and 2 each protected against common pin 3 (LCSC C5380400 is a DOWO second source; Nexperia part not stock-checked)')],
    es_body, es_pins, True)

for nm, txt in (('TS5A23157DGSR', ts_lib), ('TPA6132A2RTER', tp_lib), ('PESD5V0S2BT', es_lib)):
    p = LIB / f'{nm}.kicad_sym'
    if nm == 'PESD5V0S2BT' and p.exists(): sys.exit(f'{p} exists')
    p.write_text(txt)
# footprint + 3D model for PESD5V0S2BT: stock KiCad SOT-23 (same STEP already used by ESDA25L)
fp = (FP / 'ESDA25L.kicad_mod').read_text()
fp = fp.replace('(footprint "ESDA25L"', '(footprint "PESD5V0S2BT"', 1).replace('(property "Value" "ESDA25L"', '(property "Value" "PESD5V0S2BT"')
fp = fp.replace('kicad-library/3d/ESDA25L.step', 'kicad-library/3d/PESD5V0S2BT.step')
assert 'ESDA25L' not in fp
(FP / 'PESD5V0S2BT.kicad_mod').write_text(fp)
shutil.copyfile(M3D / 'ESDA25L.step', M3D / 'PESD5V0S2BT.step')

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
rt = (ROOT / 'DesktopSpeaker.kicad_sch').read_text()
PJ = grab(rt, 'PJ-307:PJ-307')

def symblock(text, ref):
    k = text.index(f'(property "Reference" "{ref}"')
    a = text.rfind('(symbol (lib_id', 0, k); d = 0; e = a
    while True:
        if text[e] == '(': d += 1
        elif text[e] == ')':
            d -= 1
            if d == 0: break
        e += 1
    return a, e + 1, text[a:e + 1]
old = {}
for r in ('U8', 'U9', 'U10', 'J2', 'J3'):
    a, e, b = symblock(rt, r); old[r] = (a, e, b)

# ------------------------------------------------------------------ sheet building (local coords, y up, 1.27 mm grid)
OX, OY = 190.5, 95.25
def P(lx, ly):
    x, y = OX + lx, OY - ly
    for v in (x, y):
        assert abs(v / 1.27 - round(v / 1.27)) < 1e-3, ('off grid', lx, ly)
    return x, y
PT = lambda lx, ly: (OX + lx, OY - ly)      # text positions need not be on the grid
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
def text(s, a, size=1):
    x, y = P(*a)
    items.append(f'(text "{s}" (at {f(x)} {f(y)} 0) (effects (font (size {size} {size})) (justify left bottom)) (uuid "{U()}"))')
pw = [1001]
def gnd(a):
    x, y = P(*a); n = pw[0]; pw[0] += 1
    items.append(f'(symbol (lib_id "power:GND") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "#PWR{n}" (at {f(x)} {f(y+3.81)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                 f'(property "Value" "GND" (at {f(x)} {f(y+5.08)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                 f'(pin "1" (uuid "{U()}")) (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "#PWR{n}") (unit 1)))))')
def passive(lib, ref, val, fp_, mpn, mfr, lcsc, a, rot, tpos, just='left'):
    x, y = P(*a)
    (rx, ry), (vx, vy) = [PT(*t) for t in tpos]
    j = f'(justify {just})' if just else ''
    tang = 270 if rot == 90 else 0
    items.append(f'(symbol (lib_id "{lib}") (at {f(x)} {f(y)} {rot}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "{ref}" (at {f(rx)} {f(ry)} {tang}) (effects (font (size 1.27 1.27)) {j})) '
                 f'(property "Value" "{val}" (at {f(vx)} {f(vy)} {tang}) (effects (font (size 1.27 1.27)) {j})) '
                 f'(property "Footprint" "{fp_}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
                 f'(property "MPN" "{mpn}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
                 f'(property "Manufacturer" "{mfr}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
                 f'(property "LCSC" "{lcsc}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
                 f'(pin "1" (uuid "{U()}")) (pin "2" (uuid "{U()}")) '
                 f'(instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "{ref}") (unit 1)))))')
def res(ref, val, part, a, horizontal=False):
    mpn, mfr, lcsc = part; x, y = a
    if horizontal: passive('PD_R:PD_R', ref, val, 'DesktopSpeaker:PD_R_0603', mpn, mfr, lcsc, a, 90, ((x, y + 4.7), (x, y + 3.2)), just=None)
    else: passive('PD_R:PD_R', ref, val, 'DesktopSpeaker:PD_R_0603', mpn, mfr, lcsc, a, 0, ((x + 1.27, y + 1.27), (x + 1.27, y - 1.27)))
def cap(ref, val, part, a, horizontal=False):
    fp_, mpn, mfr, lcsc = part; x, y = a
    if horizontal: passive('PD_C:PD_C', ref, val, fp_, mpn, mfr, lcsc, a, 90, ((x, y + 4.7), (x, y + 3.2)), just=None)
    else: passive('PD_C:PD_C', ref, val, fp_, mpn, mfr, lcsc, a, 0, ((x + 1.27, y + 1.27), (x + 1.27, y - 1.27)))
def vcap(ref, val, part, top):   # vertical cap whose top pin sits at `top`; ground symbol below
    x, y = top; cap(ref, val, part, (x, y - 3.81)); gnd((x, y - 7.62))
def vres(ref, val, part, top):
    x, y = top; res(ref, val, part, (x, y - 3.81))

SAM = 'Samsung Electro-Mechanics'
C100N = ('DesktopSpeaker:PD_C_0603', 'CL10B104KB8NNNC', SAM, 'C1591')
C1U = ('DesktopSpeaker:PD_C_0805', 'CL21B105KBFNNNE', SAM, 'C28323')
C2U2 = ('DesktopSpeaker:PD_C_0805', 'CL21B225KAFNNNE', SAM, 'C19110')
C4U7 = ('DesktopSpeaker:PD_C_1206', 'CL31B475KBHNNNE', SAM, 'C51205')
RY = lambda mpn, lcsc: (mpn, 'YAGEO', lcsc)
R100K = RY('RC0603FR-07100KL', 'C14675'); R1K = RY('RC0603FR-071KL', 'C22548'); R47K = RY('RC0603FR-0747KL', 'C105579')
R10K = RY('RC0603FR-0710KL', 'C98220'); R1M = RY('RC0603FR-071ML', 'C105578')

def transplant(ref, c, rot, mirror, tref, tval, extra_pins=None, just=''):
    """Reuse the root symbol block (same symbol/pin UUIDs), move it to the sheet."""
    b = old[ref][2]
    x, y = P(*c)
    mir = f' (mirror {mirror})' if mirror else ''
    b = re.sub(r'^(\(symbol \(lib_id "[^"]*"\)) \(at [^)]*\)', lambda m: f'{m.group(1)} (at {f(x)} {f(y)} {rot}){mir}', b, 1)
    for prop, pos in (('Reference', tref), ('Value', tval)):
        px, py = PT(*pos)
        b = re.sub(r'(\(property "%s" "[^"]*" )\(at [^)]*\)' % prop, lambda m: f'{m.group(1)}(at {f(px)} {f(py)} 0)', b, 1)
    b = b.replace(f'(path "/{ROOT_UUID}"', f'(path "/{ROOT_UUID}/{SHEET_UUID}"')
    b = b.replace('"../ai-files/datasheets/', '"${KIPRJMOD}/../ai-files/datasheets/')
    if just:
        for prop in ('Reference', 'Value'):
            b = re.sub(r'(\(property "%s" "[^"]*" \(at [^)]*\) (?:\(show_name no\) \(do_not_autoplace no\) )?\(effects \(font \(size 1.27 1.27\)\))\)' % prop,
                       lambda m: m.group(1) + f' (justify {just}))', b, 1)
    if extra_pins is not None:
        b = re.sub(r'\(pin "[^"]*" \(uuid "[^"]*"\)\) ?', '', b)
        pins = ' '.join(f'(pin "{n}" (uuid "{u}"))' for n, u in extra_pins)
        b = b.replace('(instances', pins + ' (instances', 1)
    items.append(b)

def oldpins(ref):
    return re.findall(r'\(pin "([^"]*)" \(uuid "([^"]*)"\)\)', old[ref][2])

# =========================================================== layout (local coordinates)
X0 = -165.1                      # left ports
# ---- six input networks: port - 1uF - node(100k to VMID_HP) - 1k - jog - mux pin
U8c = (-50.8, 38.1); U9c = (12.7, -12.7); U10c = (88.9, -17.78)
rows = [('USB_AUDIO_L', 66.04, 45.72, -91.44), ('USB_AUDIO_R', 53.34, 43.18, -99.06),
        ('BT_AUDIO_L', 35.56, 40.64, -106.68), ('BT_AUDIO_R', 22.86, 38.1, -91.44),
        ('AUX_L', 10.16, -10.16, -86.36), ('AUX_R', -2.54, -12.7, -91.44)]
PINX8 = U8c[0] - 17.78; PINX9 = U9c[0] - 17.78
for k, (port, y, py, xj) in enumerate(rows):
    px = PINX8 if k < 4 else PINX9
    if k < 4: hlabel(port, 'input', (X0, y), 180)
    else: label(port, (X0, y), 'right bottom')
    wire((X0, y), (-157.48, y))
    cap(f'C{230+k}', '1uF', C1U, (-153.67, y), True)
    wire((-149.86, y), (-138.43, y)); junc((-142.24, y))
    vres(f'R{220+k}', '100k', R100K, (-142.24, y)); label('VMID_HP', (-142.24, y - 7.62))
    res(f'R{226+k}', '1k', R1K, (-134.62, y), True)
    pts = [(-130.81, y)]
    if abs(py - y) > 1e-6: pts += [(xj, y), (xj, py)]
    pts += [(px, py)]
    wire(*pts)
# ---- U8 / U9 (TS5A23157, same UUIDs as the former root parts)
transplant('U8', U8c, 0, None, (U8c[0], U8c[1] - 14.6), (U8c[0], U8c[1] - 16.5), oldpins('U8'))
transplant('U9', U9c, 0, None, (U9c[0], U9c[1] - 14.6), (U9c[0], U9c[1] - 16.5), oldpins('U9'))
# control inputs: IN1 and IN2 of each switch tied by a matching label
for (cx, cy), sel in ((U8c, 'HP_SEL_A'), (U9c, 'HP_SEL_B')):
    for dy in (-7.62, -10.16):
        wire((cx - 17.78, cy + dy), (cx - 20.32, cy + dy)); label(sel, (cx - 20.32, cy + dy), 'right bottom')
    gnd((cx + 10.16, cy - 15.24))
    vx, vy = cx + 10.16, cy + 15.24
    wire((vx, vy), (vx, vy + 7.62), (vx + 12.7, vy + 7.62)); label('3V3_AUDIO', (vx, vy + 7.62))
    vcap('C237' if sel == 'HP_SEL_A' else 'C238', '100nF', C100N, (vx + 12.7, vy + 7.62))
# U8 COM -> U9 NC
wire((U8c[0] + 17.78, U8c[1] + 7.62), (-12.7, U8c[1] + 7.62), (-12.7, U9c[1] + 7.62), (PINX9, U9c[1] + 7.62))
wire((U8c[0] + 17.78, U8c[1] + 5.08), (-17.78, U8c[1] + 5.08), (-17.78, U9c[1] + 5.08), (PINX9, U9c[1] + 5.08))
# ---- U10 TPA6132A2
ux, uy = U10c
transplant('U10', U10c, 0, None, (ux, uy - 32.1), (ux, uy - 34.0), [(n, u) for n, u in oldpins('U10')[:1]] +
           [('[2,3,10,17]', U())] + [(n, u) for n, u in oldpins('U10') if n in ('4', '5', '6', '7', '8', '9', '11', '12', '13', '14', '15', '16')])
# series input caps from the mux commons
cy1 = uy + 12.7; cy2 = uy + 2.54
wire((U9c[0] + 17.78, U9c[1] + 7.62), (55.88, cy1)); label('HP_L', (40.64, cy1))
cap('C239', '1uF', C1U, (59.69, cy1), True); wire((63.5, cy1), (ux - 17.78, cy1))
wire((U9c[0] + 17.78, U9c[1] + 5.08), (36.83, U9c[1] + 5.08), (36.83, cy2), (55.88, cy2)); label('HP_R', (45.72, cy2))
cap('C240', '1uF', C1U, (59.69, cy2), True); wire((63.5, cy2), (ux - 17.78, cy2))
# control pins EN, G0, G1 (ports with pull-downs at the left of the sheet; matching labels here)
for dy, nm in ((-10.16, 'HP_EN'), (-12.7, 'HP_G0'), (-15.24, 'HP_G1')):
    wire((ux - 17.78, uy + dy), (ux - 20.32, uy + dy)); label(nm, (ux - 20.32, uy + dy), 'right bottom')
# supply VDD: 1 uF + 100 nF
vx = ux - 7.62
wire((vx, uy + 20.32), (vx, uy + 33.02), (vx - 15.24, uy + 33.02)); label('3V3_AUDIO', (vx, uy + 33.02))
junc((vx - 7.62, uy + 33.02))
vcap('C241', '1uF', C1U, (vx - 7.62, uy + 33.02)); vcap('C242', '100nF', C100N, (vx - 15.24, uy + 33.02))
# ground stack
gnd((ux - 10.16, uy - 33.02))
# charge pump, HPVDD, HPVSS
rx = ux + 17.78
for dy, ref, val in ((-5.08, 'C243', '2.2uF'), (-12.7, 'C244', '2.2uF')):
    y = uy + dy
    wire((rx, y), (rx + 3.81, y)); cap(ref, val, C2U2, (rx + 7.62, y), True); wire((rx + 11.43, y), (rx + 15.24, y)); gnd((rx + 15.24, y))
yp, yn = uy - 20.32, uy - 27.94
wire((rx, yp), (rx + 7.62, yp)); cap('C245', '1uF', C1U, (rx + 7.62, yp - 3.81)); wire((rx + 7.62, yn), (rx, yn))
# ---- J2 HEAD_OUT (rotated 180: pins on the left, tip on top)
J2c = (152.4, -11.43)
transplant('J2', J2c, 180, None, (J2c[0] + 13.97, J2c[1] + 1.27), (J2c[0] + 13.97, J2c[1] - 1.27), None, 'left')
jx = J2c[0] - 7.62
tipy, ringy, sley = J2c[1] + 6.35, J2c[1] - 1.27, J2c[1] - 3.81
wire((rx, uy + 12.7), (jx, tipy)); label('HP_OUTL', (116.84, tipy))
wire((rx, uy + 5.08), (jx, ringy)); label('HP_OUTR', (116.84, ringy))
wire((rx, uy + 2.54), (jx, sley)); junc((139.7, sley)); wire((139.7, sley), (139.7, sley - 2.54)); gnd((139.7, sley - 2.54))
wire((jx, J2c[1] + 3.81), (jx - 3.81, J2c[1] + 3.81)); label('HP_TIPSW', (jx - 3.81, J2c[1] + 3.81), 'right bottom')
nc((jx, J2c[1] + 1.27))
# D200 across tip and ring
D200c = (147.32, -40.64)
def esd(ref, c, la, lb):
    x, y = P(*c); (rx_, ry_), (vx_, vy_) = PT(c[0] + 7.62, c[1] + 1.27), PT(c[0] + 7.62, c[1] - 1.27)
    items.append(f'(symbol (lib_id "PESD5V0S2BT:PESD5V0S2BT") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "{ref}" (at {f(rx_)} {f(ry_)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
                 f'(property "Value" "PESD5V0S2BT" (at {f(vx_)} {f(vy_)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
                 f'(property "Footprint" "DesktopSpeaker:PESD5V0S2BT" (at {f(x)} {f(y)} 0) {hide}) '
                 f'(property "Datasheet" "{DS}PESD5V0S2BT.pdf" (at {f(x)} {f(y)} 0) {hide}) '
                 f'(property "MPN" "PESD5V0S2BT" (at {f(x)} {f(y)} 0) {hide}) (property "Manufacturer" "Nexperia" (at {f(x)} {f(y)} 0) {hide}) '
                 f'(property "LCSC Part" "C5380400" (at {f(x)} {f(y)} 0) {hide}) '
                 + ' '.join(f'(pin "{n}" (uuid "{U()}"))' for n in (1, 2, 3)) +
                 f' (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "{ref}") (unit 1)))))')
    wire((c[0] - 6.35, c[1] + 2.54), (c[0] - 8.89, c[1] + 2.54)); label(la, (c[0] - 8.89, c[1] + 2.54), 'right bottom')
    wire((c[0] - 6.35, c[1] - 2.54), (c[0] - 8.89, c[1] - 2.54)); label(lb, (c[0] - 8.89, c[1] - 2.54), 'right bottom')
    gnd((c[0], c[1] - 7.62))
esd('D200', D200c, 'HP_OUTL', 'HP_OUTR')
# HP_DET: switched tip, 100k pull-up to 3V3_AUDIO, 1k series to the MCU
hy = -17.78
wire((172.72, hy), (177.8, hy)); label('HP_TIPSW', (172.72, hy), 'right bottom'); junc((177.8, hy))
vres('R239', '100k', R100K, (177.8, hy + 7.62)); label('3V3_AUDIO', (177.8, hy + 7.62))
res('R240', '1k', R1K, (190.5, hy), True); wire((177.8, hy), (186.69, hy)); wire((194.31, hy), (198.12, hy))
hlabel('HP_DET', 'output', (198.12, hy), 0)
# ---- J3 AUX_IN (mirrored: pins on the right, tip on top)
J3c = (139.7, -67.31)
transplant('J3', J3c, 0, 'x', (J3c[0] - 8.89, J3c[1] + 11.43), (J3c[0] - 8.89, J3c[1] + 9.53), None, 'left')
jx3 = J3c[0] + 7.62
t3, r3, s3 = J3c[1] + 6.35, J3c[1] - 1.27, J3c[1] - 3.81
wire((jx3, t3), (198.12, t3)); hlabel('AUX_L', 'output', (198.12, t3), 0)
wire((jx3, r3), (198.12, r3)); hlabel('AUX_R', 'output', (198.12, r3), 0)
wire((jx3, s3), (jx3 + 2.54, s3)); gnd((jx3 + 2.54, s3))
wire((jx3, J3c[1] + 3.81), (jx3 + 3.81, J3c[1] + 3.81)); label('AUX_TIPSW', (jx3 + 3.81, J3c[1] + 3.81))
nc((jx3, J3c[1] + 1.27))
# D201 and bleeds
esd('D201', (116.84, -76.2), 'AUX_L', 'AUX_R')
for nm, x, ref in (('AUX_L', 85.09, 'R243'), ('AUX_R', 97.79, 'R244')):
    label(nm, (x, -66.04), 'left bottom'); wire((x, -66.04), (x, -67.31)); vres(ref, '10k', R10K, (x, -67.31)); gnd((x, -74.93))
# AUX_DET: switched tip, 1M to 3V_AO, 100 nF filter, 10k series to the MCU
ay = -83.82
wire((172.72, ay), (177.8, ay)); label('AUX_TIPSW', (172.72, ay), 'right bottom'); junc((177.8, ay))
vres('R241', '1M', R1M, (177.8, ay + 7.62)); wire((177.8, ay + 7.62), (172.72, ay + 7.62)); hlabel('3V_AO', 'input', (172.72, ay + 7.62), 180)
junc((181.61, ay)); vcap('C246', '100nF', C100N, (181.61, ay))
wire((177.8, ay), (186.69, ay)); res('R242', '10k', R10K, (190.5, ay), True); wire((194.31, ay), (198.12, ay))
hlabel('AUX_DET', 'output', (198.12, ay), 0)
# ---- VMID_HP: 47k / 47k from 3V3_AUDIO with 4.7 uF
dx = -160.02
hlabel('3V3_AUDIO', 'input', (X0, -17.78), 180); wire((X0, -17.78), (dx, -17.78), (dx, -20.32))
res('R232', '47k', R47K, (dx, -24.13)); junc((dx, -27.94))
res('R233', '47k', R47K, (dx, -31.75)); gnd((dx, -35.56))
wire((dx, -27.94), (-148.59, -27.94)); label('VMID_HP', (-157.48, -27.94))
vcap('C236', '4.7uF', C4U7, (-148.59, -27.94))
# ---- control ports with 100k pull-downs (default low: USB source, amp off, -6 dB)
for k, nm in enumerate(('HP_SEL_A', 'HP_SEL_B', 'HP_EN', 'HP_G0', 'HP_G1')):
    y = -45.72 - 10.16 * k
    hlabel(nm, 'input', (X0, y), 180); wire((X0, y), (-157.48, y))
    res(f'R{234+k}', '100k', R100K, (-153.67, y), True); wire((-149.86, y), (-146.05, y)); gnd((-146.05, y))
# ---- notes
text('Mux: USB (default), BT, AUX select by HP_SEL_B/HP_SEL_A = 00 / 01 / 1x. HP_SEL_A,B, HP_EN, HP_G0/G1 default low (pull-downs): USB, amp off, -6 dB.', (-165.1, -97.79))
text('Sequence: HP_EN low, change HP_SEL, wait 1 ms, HP_EN high (5 ms start-up). Hold HP_EN, HP_G0, HP_G1 low while 3V3_AUDIO is off.', (-165.1, -100.33))
text('Inputs: 1 uF AC coupling, 100 k bias to VMID_HP (1.65 V from 3V3_AUDIO), 1 k series. TPA6132A2 inputs are single-ended (INL+/INR+ grounded).', (-165.1, -102.87))
text('J2 switched tip (4) = HP_DET (low without plug, high with plug). J3 switched tip (4) = AUX_DET. Switched ring (3): not connected. No hardware speaker mute: firmware mutes the speaker chain on insertion.', (-165.1, -105.41))
text('SGND (pin 15) goes to the J2 sleeve: route as its own trace to the jack sleeve ground, away from PGND. PESD5V0S2BT pin 3 = common: VERIFY against datasheet.', (-165.1, -107.95))

lib_syms = '(lib_symbols ' + ' '.join([ts_emb, tp_emb, es_emb, PJ, PD_C, PD_R, GND]) + ')'
hdr = ['(kicad_sch', '(version 20260306)', '(generator "eeschema")', '(generator_version "10.0")',
       f'(uuid "{SHEET_UUID}")', '(paper "A3")',
       '(title_block (title "Headphone output and aux input") (rev "0.1") (comment 1 "TS5A23157 3:1 headphone mux, TPA6132A2 headphone amplifier, switched PJ-307 jacks"))',
       lib_syms]
OUT.write_text('\n'.join(hdr + items) + '\n)\n')

# ------------------------------------------------------------------ sym-lib-table
tbl = (ROOT / 'sym-lib-table').read_text()
if 'PESD5V0S2BT' not in tbl:
    add = '  (lib (name "PESD5V0S2BT") (type "KiCad") (uri "${KIPRJMOD}/kicad-library/schematic/PESD5V0S2BT.kicad_sym") (options "") (descr "Nexperia PESD5V0S2BT ESD diode"))\n'
    idx = tbl.rindex(')')
    (ROOT / 'sym-lib-table').write_text(tbl[:idx] + add + tbl[idx:])

# ------------------------------------------------------------------ root edits
# remove the old blocks (descending offsets) and their lib symbols
for r in sorted(old, key=lambda r: -old[r][0]):
    a, e, _ = old[r]
    rt = rt[:a] + rt[e:]
for nm in ('TS5A23157DGSR:TS5A23157DGSR', 'TPA6132A2RTER:TPA6132A2RTER', 'PJ-307:PJ-307'):
    s = grab(rt, nm); rt = rt.replace(s, '', 1)
MX, MY, MW, MH = 35.56, 15.24, 40.64, 66.04
left = [('USB_AUDIO_L', 'input'), ('USB_AUDIO_R', 'input'), ('BT_AUDIO_L', 'input'), ('BT_AUDIO_R', 'input'), ('3V3_AUDIO', 'input'),
        ('3V_AO', 'input'), ('HP_SEL_A', 'input'), ('HP_SEL_B', 'input'), ('HP_EN', 'input'), ('HP_G0', 'input'), ('HP_G1', 'input')]
right = [('AUX_L', 'output'), ('AUX_R', 'output'), ('HP_DET', 'output'), ('AUX_DET', 'output')]
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
         f'(property "Sheet name" "Headphone_Aux" (at {f(MX)} {f(MY-1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
         f'(property "Sheet file" "Headphone_Aux.kicad_sch" (at {f(MX)} {f(MY+MH)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
         + sp + f'(instances (project "DesktopSpeaker" (path "/{ROOT_UUID}" (page "11")))))')
new.insert(0, sheet)

def rep(s, a, b, count=1):
    assert s.count(a) == count, (a, s.count(a))
    return s.replace(a, b)
# replace the old AUX note
m = re.search(r'\(text "AUX_L/AUX_R come from the later Headphone_Aux sheet[^\n]*\n', rt); assert m
rt = rt[:m.start()] + (f'(text "AUX_L/AUX_R leave the Headphone_Aux sheet (J3 AUX_IN) and join the Source_Select_ADC inputs by label. USB_AUDIO and BT_AUDIO nets fan out to both sheets. Speaker mute on headphone insertion is firmware only (HP_DET)." '
                       f'(at 20.32 86.36 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))\n') + rt[m.end():]
# MCU sheet block: grow upward for 5 outputs, add 2 inputs
mcu_i = rt.index('(property "Sheet name" "MCU"'); sh_a = rt.rfind('(sheet (at', 0, mcu_i)
assert rt[sh_a:sh_a + 60].startswith('(sheet (at 320.04 121.92) (size 50.8 83.82)')
rt = rt[:sh_a] + rt[sh_a:].replace('(sheet (at 320.04 121.92) (size 50.8 83.82)', '(sheet (at 320.04 109.22) (size 50.8 96.52)', 1)
mcu_i = rt.index('(property "Sheet name" "MCU"')
ns = re.compile(r'(\(property "Sheet name" "MCU" \(at 320.04 )[\d.]+( 0\))')
rt = ns.sub(r'\g<1>107.95\2', rt, 1)
nf = re.compile(r'(\(property "Sheet file" "MCU.kicad_sch" \(at 320.04 )[\d.]+( 0\))')
assert nf.search(rt); rt = nf.sub(r'\g<1>205.74\2', rt, 1)
hp_out = [('HP_SEL_A', 111.76), ('HP_SEL_B', 114.3), ('HP_EN', 116.84), ('HP_G0', 119.38), ('HP_G1', 121.92)]
hp_in = [('HP_DET', 182.88), ('AUX_DET', 187.96)]
mp = ''.join(f'(pin "{n}" output (at 370.84 {f(y)} 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}")) ' for n, y in hp_out)
mp += ''.join(f'(pin "{n}" input (at 320.04 {f(y)} 180) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}")) ' for n, y in hp_in)
j = rt.index('(pin ', mcu_i)
rt = rt[:j] + mp + rt[j:]
for n, y in hp_out:
    new.append(f'(wire (pts (xy 370.84 {f(y)}) (xy 375.92 {f(y)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    new.append(f'(label "{n}" (at 375.92 {f(y)} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
for n, y in hp_in:
    new.append(f'(wire (pts (xy 320.04 {f(y)}) (xy 314.96 {f(y)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    new.append(f'(label "{n}" (at 314.96 {f(y)} 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}"))')
assert rt.rstrip().endswith(')')
(ROOT / 'DesktopSpeaker.kicad_sch').write_text(rt.rstrip()[:-1] + '\n'.join(new) + '\n)\n')

# ------------------------------------------------------------------ MCU sheet: connect reserved labels
mt = (ROOT / 'MCU.kicad_sch').read_text()
def rm_nc(t, x, y):
    pat = re.compile(r'\(no_connect \(at %s %s\) \(uuid "[^"]*"\)\)\n' % (re.escape(x), re.escape(y))); assert pat.search(t), (x, y)
    return pat.sub('', t, 1)
def rm_text(t, s):
    pat = re.compile(r'\(text "%s" [^\n]*\n' % re.escape(s)); assert pat.search(t), s
    return pat.sub('', t, 1)
add = []
for nm, py in (('HP_SEL_A', '130.81'), ('HP_SEL_B', '133.35'), ('HP_EN', '135.89'), ('HP_G0', '138.43'), ('HP_G1', '140.97')):
    mt = rm_nc(mt, '165.1', py); mt = rm_text(mt, f'{nm} (reserved)')
    add.append(f'(wire (pts (xy 165.1 {py}) (xy 215.9 {py})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    add.append(f'(hierarchical_label "{nm}" (shape output) (at 215.9 {py} 0) (effects (font (size 1.0 1.0)) (justify right bottom)) (uuid "{U()}"))')
for nm, py in (('HP_DET', '105.41'), ('AUX_DET', '107.95')):
    mt = rm_nc(mt, '114.3', py); mt = rm_text(mt, f'{nm} (reserved)')
    add.append(f'(wire (pts (xy 45.72 {py}) (xy 114.3 {py})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    add.append(f'(hierarchical_label "{nm}" (shape input) (at 45.72 {py} 0) (effects (font (size 1.0 1.0)) (justify left bottom)) (uuid "{U()}"))')
assert mt.rstrip().endswith(')')
(ROOT / 'MCU.kicad_sch').write_text(mt.rstrip()[:-1] + '\n'.join(add) + '\n)\n')
print('sheet uuid', SHEET_UUID)
