#!/usr/bin/env python3
"""Create Amplifiers.kicad_sch (U25 TPS61088 boost, U6/U7 TAS5825M with supports, output filters, J9-J11), move U6/U7 out of the
root keeping reference/value/UUID, add the root sheet block, connect the MCU reserved AMP_* signals, and write the new library files
(TPS61088RHLR, PD_L, PD_CP, JST_B2P_VH symbols; TPS61088/B2P-VH/inductor/polymer footprints; TAS5825M symbol regrouped by function).
Guarded: refuses to run when Amplifiers.kicad_sch exists. Python 3, no dependencies.  Run from a clean tree."""
import re, sys, uuid, pathlib, shutil, json

ROOT = pathlib.Path('/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad')
LIB = ROOT / 'kicad-library/schematic'
FP = ROOT / 'kicad-library/footprint'
M3D = ROOT / 'kicad-library/3d'
STOCK = pathlib.Path('/home/chithi/kicad-libs')
OUT = ROOT / 'Amplifiers.kicad_sch'
if OUT.exists():
    sys.exit('Amplifiers.kicad_sch exists; refusing')
ROOT_UUID = 'feda53ed-537d-4f88-9436-c6075776255b'
SHEET_UUID = str(uuid.uuid4())
U = lambda: str(uuid.uuid4())
f = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')
eff = '(effects (font (size 1.27 1.27)))'
eff10 = '(effects (font (size 1 1)))'
hide = '(effects (font (size 1.27 1.27)) (hide yes))'

# ------------------------------------------------------------------ library symbols
def pin(t, x, y, a, name, num, ln=2.54, e=eff):
    return f'(pin {t} line (at {f(x)} {f(y)} {a}) (length {f(ln)}) (name "{name}" {e}) (number "{num}" {e}))'

def make_sym(name, ref, ref_at, val_at, props, body, pins, hide_names=False, hide_nums=False):
    pn = '(pin_names (offset 1.016) (hide yes))' if hide_names else '(pin_names (offset 1.016))'
    pnum = ' (pin_numbers (hide yes))' if hide_nums else ''
    base = (f'(property "Reference" "{ref}" (at {f(ref_at[0])} {f(ref_at[1])} 0) {eff}) '
            f'(property "Value" "{name}" (at {f(val_at[0])} {f(val_at[1])} 0) {eff}) '
            + ''.join(f'(property "{k}" "{v}" (at 0 0 0) {hide}) ' for k, v in props))
    unit = f'(symbol "{name}_0_1" {body}) (symbol "{name}_1_1" ' + ' '.join(pins) + ')'
    lib = (f'(kicad_symbol_lib (version 20250120) (generator "kicad_symbol_editor") (symbol "{name}" {pn}{pnum} '
           f'(in_bom yes) (on_board yes) ' + base + unit + ' (embedded_fonts no)))\n')
    emb = (f'(symbol "{name}:{name}" {pn}{pnum} (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) '
           f'(duplicate_pin_numbers_are_jumpers no) ' + base + unit + ' (embedded_fonts no))')
    return lib, emb

def rect(x1, y1, x2, y2):
    return f'(rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width 0.254) (type default)) (fill (type background)))'

DS = '${KIPRJMOD}/../ai-files/datasheets/'
TI = 'Texas Instruments'
# --- TAS5825MRHBR (VQFN-32 RHB + EP). Pad numbers unchanged; grouped by function.
# stacks: PVDD [3,4,21,22]; GND [5,20,25,26,31,32,33] = DGND, AGND, PGND x4, thermal pad (all ground per the datasheet application figures)
HB, E = 20.32, 22.86
tas_pins = [
    pin('input', -E, 25.4, 0, 'SCLK', '13', e=eff10), pin('input', -E, 22.86, 0, 'LRCLK', '12', e=eff10), pin('input', -E, 20.32, 0, 'SDIN', '14', e=eff10),
    pin('bidirectional', -E, 12.7, 0, 'SDA', '15', e=eff10), pin('input', -E, 10.16, 0, 'SCL', '16', e=eff10),
    pin('input', -E, 2.54, 0, '~{PDN}', '17', e=eff10), pin('passive', -E, -5.08, 0, 'ADR', '8', e=eff10),
    pin('open_collector', -E, -12.7, 0, 'GPIO0', '9', e=eff10), pin('bidirectional', -E, -15.24, 0, 'GPIO1', '10', e=eff10),
    pin('bidirectional', -E, -17.78, 0, 'GPIO2', '11', e=eff10),
    pin('power_in', -7.62, 33.02, 270, 'DVDD', '6', e=eff10), pin('power_in', 7.62, 33.02, 270, 'PVDD', '[3,4,21,22]', e=eff10),
    pin('power_out', -17.78, -35.56, 90, 'VR_DIG', '7', 7.62, eff10), pin('power_out', -10.16, -35.56, 90, 'GVDD', '18', 7.62, eff10),
    pin('power_out', 10.16, -35.56, 90, 'AVDD', '19', 7.62, eff10), pin('power_in', 20.32, -35.56, 90, 'GND', '[5,20,25,26,31,32,33]', 7.62, eff10),
    pin('passive', E, 27.94, 180, 'BST_A+', '1', e=eff10), pin('passive', E, 20.32, 180, 'OUT_A+', '2', e=eff10),
    pin('passive', E, 15.24, 180, 'OUT_A-', '30', e=eff10), pin('passive', E, 7.62, 180, 'BST_A-', '29', e=eff10),
    pin('passive', E, 2.54, 180, 'BST_B+', '24', e=eff10), pin('passive', E, -5.08, 180, 'OUT_B+', '23', e=eff10),
    pin('passive', E, -10.16, 180, 'OUT_B-', '27', e=eff10), pin('passive', E, -17.78, 180, 'BST_B-', '28', e=eff10)]
tas_lib, tas_emb = make_sym('TAS5825MRHBR', 'U', (0, -30.5), (0, -32.5), [
    ('Footprint', 'DesktopSpeaker:TAS5825MRHBR'), ('Datasheet', DS + 'TAS5825M.pdf'), ('Manufacturer', TI), ('MPN', 'TAS5825MRHBR'),
    ('LCSC Part', 'C471049'),
    ('Description', '4.5-26.4 V, 2 x 23 W stereo / 1 x 45 W mono digital-input class-D amplifier with DSP, VQFN-32 (RHB). Pads grouped by function: PVDD stack 3,4,21,22; ground stack 5,20,25,26,31,32,33 (DGND, AGND, PGND, thermal pad); pad numbers per SLASEH7F')],
    rect(-HB, 30.48, HB, -27.94), tas_pins, hide_nums=False)

# --- TPS61088RHLR (VQFN-20 RHL + thermal pad 21), SLVSCW8 / ZHCSDP8A pin table
BX = 12.7; BE = 15.24
ic_pins = [
    pin('input', -BE, 5.08, 0, 'EN', '2', e=eff10), pin('passive', -BE, -7.62, 0, 'FSW', '3', e=eff10), pin('passive', -BE, -15.24, 0, 'BOOT', '8', e=eff10),
    pin('passive', -BE, -22.86, 0, 'SW', '[4-7]', e=eff10), pin('input', -BE, -30.48, 0, 'MODE', '13', e=eff10),
    pin('power_in', -7.62, 20.32, 270, 'VIN', '9', e=eff10), pin('power_out', 2.54, 20.32, 270, 'VCC', '1', e=eff10),
    pin('power_out', BE, 15.24, 180, 'VOUT', '[14-16]', e=eff10), pin('input', BE, 7.62, 180, 'FB', '17', e=eff10),
    pin('passive', BE, -5.08, 180, 'COMP', '18', e=eff10), pin('passive', BE, -25.4, 180, 'ILIM', '19', e=eff10),
    pin('passive', BE, -38.1, 180, 'SS', '10', e=eff10),
    pin('power_in', -10.16, -43.18, 90, 'PGND', '[11,12,21]', e=eff10), pin('power_in', 10.16, -43.18, 90, 'AGND', '20', e=eff10)]
ic_lib, ic_emb = make_sym('TPS61088RHLR', 'U', (0, -43.5), (0, -45.5), [
    ('Footprint', 'DesktopSpeaker:TPS61088RHLR'), ('Datasheet', DS + 'TPS61088_zh.pdf'), ('Manufacturer', TI), ('MPN', 'TPS61088RHLR'),
    ('LCSC Part', 'C87357'),
    ('Description', '2.7-12 V in, 4.5-12.6 V out, 10 A synchronous boost converter, VQFN-20 (RHL). Pads: SW 4-7; VOUT 14-16; PGND stack 11,12 (internal NC, grounded per datasheet) and 21 (thermal pad)')],
    rect(-BX, 17.78, BX, -40.64), ic_pins)

# --- inductor (4-arc), polarized capacitor, JST B2P-VH
arcs = ''.join(f'(arc (start 0 {f(2.54 - 1.27 * k)}) (mid 1.016 {f(2.54 - 1.27 * k - 0.635)}) (end 0 {f(2.54 - 1.27 * (k + 1))}) (stroke (width 0.254) (type default)) (fill (type none)))' for k in range(4))
l_lib, l_emb = make_sym('PD_L', 'L', (2.54, 1.27), (2.54, -1.27), [('Footprint', ''), ('Description', 'Inductor')], arcs,
                        [pin('passive', 0, 3.81, 270, '~', '1', 1.27), pin('passive', 0, -3.81, 90, '~', '2', 1.27)], True, True)
cp_body = ('(polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.508) (type default)) (fill (type none))) '
           '(arc (start -2.032 -1.016) (mid 0 -0.5) (end 2.032 -1.016) (stroke (width 0.508) (type default)) (fill (type none))) '
           '(polyline (pts (xy -2.54 2.032) (xy -1.27 2.032)) (stroke (width 0.2) (type default)) (fill (type none))) '
           '(polyline (pts (xy -1.905 1.397) (xy -1.905 2.667)) (stroke (width 0.2) (type default)) (fill (type none)))')
cp_lib, cp_emb = make_sym('PD_CP', 'C', (2.54, 1.27), (2.54, -1.27), [('Footprint', ''), ('Description', 'Polarized capacitor, pin 1 positive')], cp_body,
                          [pin('passive', 0, 3.81, 270, '+', '1', 2.794), pin('passive', 0, -3.81, 90, '-', '2', 2.794)], True, True)
j_lib, j_emb = make_sym('JST_B2P_VH', 'J', (3.81, 1.27), (3.81, -1.27), [
    ('Footprint', 'DesktopSpeaker:JST_B2P_VH_1x02_P3.96mm_Vertical'), ('Datasheet', 'https://www.jst-mfg.com/product/pdf/eng/eVH.pdf'),
    ('Manufacturer', 'JST'), ('MPN', 'B2P-VH(LF)(SN)'), ('LCSC Part', 'C160315'), ('Description', '2-position VH header, 3.96 mm pitch, 10 A, through hole; pin 1 +, pin 2 -')],
    rect(-2.54, 5.08, 2.54, -5.08),
    [pin('passive', -5.08, 2.54, 0, '1', '1', 2.54, eff10), pin('passive', -5.08, -2.54, 0, '2', '2', 2.54, eff10)], True)
for nm, txt in (('TAS5825MRHBR', tas_lib), ('TPS61088RHLR', ic_lib), ('PD_L', l_lib), ('PD_CP', cp_lib), ('JST_B2P_VH', j_lib)):
    p = LIB / f'{nm}.kicad_sym'
    if nm != 'TAS5825MRHBR' and p.exists(): sys.exit(f'{p} exists')
    p.write_text(txt)

# ------------------------------------------------------------------ footprints / models
def copy_fp(src, dst, model_src, model_dst):
    t = (STOCK / 'footprints' / src).read_text()
    t = t.replace(pathlib.Path(src).stem, dst)
    if model_src:
        t = re.sub(r'\(model "[^"]*"', f'(model "${{KIPRJMOD}}/kicad-library/3d/{model_dst}"', t, 1)
        shutil.copyfile(STOCK / '3dmodels' / model_src, M3D / model_dst)
    else:
        t = re.sub(r'\n\t\(model "[^"]*".*?\n\t\)', '', t, flags=re.S)
    (FP / f'{dst}.kicad_mod').write_text(t)
copy_fp('Inductor_SMD.pretty/L_Sunlord_MWSA1265S.kicad_mod', 'L_Sunlord_MWSA1265S', 'Inductor_SMD.3dshapes/L_Sunlord_MWSA1265S.step', 'L_Sunlord_MWSA1265S.step')
copy_fp('Inductor_SMD.pretty/L_Coilcraft_XAL7070-XXX.kicad_mod', 'L_Coilcraft_XAL7070-XXX', 'Inductor_SMD.3dshapes/L_Coilcraft_XAL7070-XXX.step', 'L_Coilcraft_XAL7070-XXX.step')
copy_fp('Capacitor_SMD.pretty/CP_Elec_8x10.kicad_mod', 'CP_Elec_8x10', 'Capacitor_SMD.3dshapes/CP_Elec_8x10.step', 'CP_Elec_8x10.step')
copy_fp('Connector_JST.pretty/JST_VH_B2P-VH_1x02_P3.96mm_Vertical.kicad_mod', 'JST_B2P_VH_1x02_P3.96mm_Vertical', None, None)

# TPS61088RHLR footprint from the EasyEDA/LCSC official C87357 package (VQFN-20 L4.5 W3.5 P0.50), pads mapped to the TI pin numbers
d = json.load(open('/tmp/amp/c87357.json'))['result']['packageDetail']['dataStr']['shape']
pads = []; poly = None
for s in d:
    if s.startswith('PAD~RECT'):
        a = s.split('~'); cx, cy, w, h, num = float(a[2]), float(a[3]), float(a[4]), float(a[5]), a[8]
        pads.append((num, (cx - 400) * 0.254, (cy - 300) * 0.254, w * 0.254, h * 0.254))
    if s.startswith('PAD~POLYGON'):
        a = s.split('~'); nums = a[10].split(); poly = [((float(nums[i]) - 400) * 0.254, (float(nums[i + 1]) - 300) * 0.254) for i in range(0, len(nums), 2)]
assert len(pads) == 20 and poly
fpt = ['(footprint "TPS61088RHLR"', '\t(version 20260206)', '\t(generator "kicad-footprint-generator")', '\t(layer "F.Cu")',
       '\t(descr "VQFN-20 4.5x3.5 mm, 0.5 mm pitch, TPS61088RHLR (pads from the LCSC/EasyEDA official package C87357; verify against TI RHL0020A before PCB release)")',
       '\t(tags "VQFN20 RHL TPS61088")',
       '\t(property "Reference" "REF**" (at 0 -3.2 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
       '\t(property "Value" "TPS61088RHLR" (at 0 3.2 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
       '\t(attr smd)']
for num, x, y, w, h in sorted(pads, key=lambda p: int(p[0])):
    fpt.append(f'\t(pad "{num}" smd roundrect (at {x:.4f} {y:.4f}) (size {w:.4f} {h:.4f}) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25))')
pts = ' '.join(f'(xy {x:.4f} {y:.4f})' for x, y in poly)
fpt.append(f'\t(pad "21" smd custom (at 0 0) (size 0.1 0.1) (layers "F.Cu" "F.Mask" "F.Paste") (options (clearance outline) (anchor circle)) '
           f'(primitives (gr_poly (pts {pts}) (width 0) (fill yes))))')
for (x1, y1, x2, y2) in ((-2.25, -1.75, 2.25, 1.75),):
    fpt.append(f'\t(fp_rect (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))')
fpt.append('\t(fp_rect (start -2.8 -2.3) (end 2.8 2.3) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))')
fpt.append('\t(fp_circle (center -2.95 1.5) (end -2.85 1.5) (stroke (width 0.2) (type solid)) (fill no) (layer "F.SilkS"))')
fpt.append('\t(embedded_fonts no)')
fpt.append('\t(model "${KIPRJMOD}/kicad-library/3d/TPS61088RHLR.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
fpt.append(')')
(FP / 'TPS61088RHLR.kicad_mod').write_text('\n'.join(fpt) + '\n')
shutil.copyfile('/tmp/amp/t88.step', M3D / 'TPS61088RHLR.step')

# ------------------------------------------------------------------ embedded library helpers
def grab(text, name):
    i = text.index(f'(symbol "{name}"'); dd = 0; j = i
    while True:
        if text[j] == '(': dd += 1
        elif text[j] == ')':
            dd -= 1
            if dd == 0: break
        j += 1
    return text[i:j + 1]
fg = (ROOT / 'Fuel_Gauge_Power.kicad_sch').read_text()
PD_C = grab(fg, 'PD_C:PD_C'); PD_R = grab(fg, 'PD_R:PD_R'); GND = grab(fg, 'power:GND')
rt = (ROOT / 'DesktopSpeaker.kicad_sch').read_text()

def symblock(text, ref):
    k = text.index(f'(property "Reference" "{ref}"')
    a = text.rfind('(symbol (lib_id', 0, k); dd = 0; e = a
    while True:
        if text[e] == '(': dd += 1
        elif text[e] == ')':
            dd -= 1
            if dd == 0: break
        e += 1
    return a, e + 1, text[a:e + 1]
old = {}
for r in ('U6', 'U7'):
    old[r] = symblock(rt, r)

# ------------------------------------------------------------------ sheet building (local coords, y up, 1.27 mm grid)
OX, OY = 139.7, 165.1
def P(lx, ly):
    x, y = OX + lx, OY - ly
    for v in (x, y):
        assert abs(v / 1.27 - round(v / 1.27)) < 1e-3, ('off grid', lx, ly)
    return x, y
PT = lambda lx, ly: (OX + lx, OY - ly)
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
pw = [1101]
def gnd(a):
    x, y = P(*a); n = pw[0]; pw[0] += 1
    items.append(f'(symbol (lib_id "power:GND") (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "#PWR{n}" (at {f(x)} {f(y+3.81)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                 f'(property "Value" "GND" (at {f(x)} {f(y+5.08)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
                 f'(pin "1" (uuid "{U()}")) (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "#PWR{n}") (unit 1)))))')
def passive(lib, ref, val, fp_, mpn, mfr, lcsc, a, rot, tpos, just='left', dnp=False):
    tpos = list(tpos)
    x, y = P(*a)
    (rx, ry), (vx, vy) = [PT(*t) for t in tpos]
    j = f'(justify {just})' if just else ''
    tang = 270 if rot == 90 else 0
    items.append(f'(symbol (lib_id "{lib}") (at {f(x)} {f(y)} {rot}) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp {"yes" if dnp else "no"}) (uuid "{U()}") '
                 f'(property "Reference" "{ref}" (at {f(rx)} {f(ry)} {tang}) (effects (font (size 1.27 1.27)) {j})) '
                 f'(property "Value" "{val}" (at {f(vx)} {f(vy)} {tang}) (effects (font (size 1.27 1.27)) {j})) '
                 f'(property "Footprint" "{fp_}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
                 f'(property "MPN" "{mpn}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
                 f'(property "Manufacturer" "{mfr}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
                 f'(property "LCSC" "{lcsc}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1 1)))) '
                 f'(pin "1" (uuid "{U()}")) (pin "2" (uuid "{U()}")) '
                 f'(instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "{ref}") (unit 1)))))')
def res(ref, val, part, a, horizontal=False, dnp=False):
    mpn, mfr, lcsc = part; x, y = a
    if horizontal: passive('PD_R:PD_R', ref, val, 'DesktopSpeaker:PD_R_0603', mpn, mfr, lcsc, a, 90, ((x, y + 4.7), (x, y + 3.2)), just=None, dnp=dnp)
    else: passive('PD_R:PD_R', ref, val, 'DesktopSpeaker:PD_R_0603', mpn, mfr, lcsc, a, 0, ((x + 2.54, y + 1.27), (x + 2.54, y - 1.27)), dnp=dnp)
def cap(ref, val, part, a, horizontal=False, lib='PD_C:PD_C', tl=False):
    fp_, mpn, mfr, lcsc = part; x, y = a
    if horizontal: passive(lib, ref, val, fp_, mpn, mfr, lcsc, a, 90, ((x, y + 4.7), (x, y + 3.2)), just=None)
    elif tl: passive(lib, ref, val, fp_, mpn, mfr, lcsc, a, 0, ((x - 2.54, y + 1.27), (x - 2.54, y - 1.27)), just='right')
    else: passive(lib, ref, val, fp_, mpn, mfr, lcsc, a, 0, ((x + 2.54, y + 1.27), (x + 2.54, y - 1.27)))
def ind(ref, val, part, a):      # horizontal inductor, pins at +-3.81
    fp_, mpn, mfr, lcsc = part; x, y = a
    passive('PD_L:PD_L', ref, val, fp_, mpn, mfr, lcsc, a, 90, ((x, y + 4.7), (x, y + 3.2)), just=None)
def vcap(ref, val, part, top, lib='PD_C:PD_C', tl=False):   # vertical cap, top pin at `top`, ground symbol below
    x, y = top; cap(ref, val, part, (x, y - 3.81), lib=lib, tl=tl); gnd((x, y - 7.62))
def vres(ref, val, part, top, dnp=False):
    x, y = top; res(ref, val, part, (x, y - 3.81), dnp=dnp)
def rcap(ref, val, part, top, tl=False):     # vertical cap between two nets (no ground symbol)
    x, y = top; cap(ref, val, part, (x, y - 3.81), tl=tl)

SAM = 'Samsung Electro-Mechanics'
C100N = ('DesktopSpeaker:PD_C_0603', 'CL10B104KB8NNNC', SAM, 'C1591')
C1U = ('DesktopSpeaker:PD_C_0805', 'CL21B105KBFNNNE', SAM, 'C28323')
C2U2 = ('DesktopSpeaker:PD_C_0805', 'CL21B225KAFNNNE', SAM, 'C19110')
C4U7 = ('DesktopSpeaker:PD_C_0603', 'CL10A475KO8NNNC', SAM, 'C19666')
C47N = ('DesktopSpeaker:PD_C_0603', 'CC0603KRX7R9BB473', 'CCTC', 'C107093')
C22_10 = ('DesktopSpeaker:PD_C_0805', 'GRM21BZ71A226ME15L', 'Murata', 'C907991')
C22_25 = ('DesktopSpeaker:PD_C_1210', 'CL32B226KAJNNNE', SAM, 'C309062')
C470N = ('DesktopSpeaker:PD_C_0603', 'CL10B474KA8NNNC', SAM, '')
C680N = ('DesktopSpeaker:PD_C_0805', 'CL21B684KBFVPNE', SAM, 'C472832')
C6N8 = ('DesktopSpeaker:PD_C_0603', 'CL10B682KB8NNNC', SAM, '')
C47P = ('DesktopSpeaker:PD_C_0603', 'CL10C470JB8NNNC', SAM, '')
C100U = ('DesktopSpeaker:CP_Elec_8x10', 'EEH-ZA1E101P', 'Panasonic', '')
RY = lambda mpn, lcsc: (mpn, 'YAGEO', lcsc)
R100K = RY('RC0603FR-07100KL', 'C14675'); R1K = RY('RC0603FR-071KL', 'C22548'); R10K = RY('RC0603FR-0710KL', 'C98220')
R499K = RY('RC0603FR-07499KL', ''); R56K = RY('RC0603FR-0756KL', ''); R301K = RY('RC0603FR-07301KL', '')
R150K = RY('RC0603FR-07150KL', ''); R82K = RY('RC0603FR-0782KL', ''); R0 = RY('RC0603FR-070RL', '')
L22 = ('DesktopSpeaker:L_Sunlord_MWSA1265S', 'MWSA1265S-220MT', 'Sunlord', '')
L2U2 = ('DesktopSpeaker:L_Coilcraft_XAL7070-XXX', 'XAL7070-222MEC', 'Coilcraft', '')

def instance(libname, ref, val, fp_, c, tref, tval, props, pins, hl='left', extra=''):
    x, y = P(*c); (rx, ry), (vx, vy) = PT(*tref), PT(*tval)
    pr = ''.join(f'(property "{k}" "{v}" (at {f(x)} {f(y)} 0) (hide yes) (effects (font (size 1.27 1.27)))) ' for k, v in props)
    items.append(f'(symbol (lib_id "{libname}:{libname}") (at {f(x)} {f(y)} 0) (unit 1) (body_style 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) (dnp no) (uuid "{U()}") '
                 f'(property "Reference" "{ref}" (at {f(rx)} {f(ry)} 0) {eff}) (property "Value" "{val}" (at {f(vx)} {f(vy)} 0) {eff}) '
                 f'(property "Footprint" "{fp_}" (at {f(x)} {f(y)} 0) (hide yes) {eff}) ' + pr +
                 ' '.join(f'(pin "{n}" (uuid "{u}"))' for n, u in pins) +
                 f' (instances (project "DesktopSpeaker" (path "/{ROOT_UUID}/{SHEET_UUID}" (reference "{ref}") (unit 1)))))')

def transplant(ref, c, tref, tval, newpins):
    b = old[ref][2]
    x, y = P(*c)
    b = re.sub(r'^(\(symbol \(lib_id "[^"]*"\)) \(at [^)]*\)', lambda m: f'{m.group(1)} (at {f(x)} {f(y)} 0)', b, 1)
    for prop, pos in (('Reference', tref), ('Value', tval)):
        px, py = PT(*pos)
        b = re.sub(r'(\(property "%s" "[^"]*" )\(at [^)]*\)' % prop, lambda m: f'{m.group(1)}(at {f(px)} {f(py)} 0)', b, 1)
    b = b.replace(f'(path "/{ROOT_UUID}"', f'(path "/{ROOT_UUID}/{SHEET_UUID}"')
    om = dict(re.findall(r'\(pin "([^"]*)" \(uuid "([^"]*)"\)\)', b))
    b = re.sub(r'\(pin "[^"]*" \(uuid "[^"]*"\)\) ?', '', b)
    pins = ' '.join(f'(pin "{n}" (uuid "{om.get(n, U())}"))' for n in newpins)
    b = b.replace('(instances', pins + ' (instances', 1)
    b = b.replace('(property "Datasheet" "https://lcsc.com/product-detail/Audio-Power-OpAmps_Texas-Instruments-Texas-Instruments-TAS5825MRHBR_C471049.html"',
                  '(property "Datasheet" "${KIPRJMOD}/../ai-files/datasheets/TAS5825M.pdf"')
    items.append(b)

# =========================================================== PVDD boost (U25) centred at (0, 0)
instance('TPS61088RHLR', 'U25', 'TPS61088RHLR', 'DesktopSpeaker:TPS61088RHLR', (0, 0), (0, -43.5), (0, -45.5),
         [('Datasheet', DS + 'TPS61088_zh.pdf'), ('MPN', 'TPS61088RHLR'), ('Manufacturer', TI), ('LCSC Part', 'C87357')],
         [(n, U()) for n in ('2', '3', '8', '[4-7]', '13', '9', '1', '[14-16]', '17', '18', '19', '10', '[11,12,21]', '20')])
# input rail SYS_RAW: VIN up to the rail, 0.1 uF + 4 x 22 uF, L200 from the rail to SW
RY_ = 30.48
wire((-7.62, 20.32), (-7.62, RY_), (-88.9, RY_))
hlabel('SYS_RAW', 'input', (-88.9, RY_), 180)
junc((-78.74, RY_))
for x in (-17.78, -30.48, -43.18, -55.88, -68.58): junc((x, RY_))
cap('C260', '100nF', C100N, (-17.78, RY_ - 3.81)); gnd((-17.78, RY_ - 7.62))
for k, x in enumerate((-30.48, -43.18, -55.88, -68.58)):
    vcap(f'C{261+k}', '22uF 10V', C22_10, (x, RY_))
wire((-78.74, RY_), (-78.74, -22.86), (-49.53, -22.86))
ind('L200', '2.2uH', L2U2, (-45.72, -22.86))
wire((-41.91, -22.86), (-15.24, -22.86)); junc((-30.48, -22.86)); junc((-17.78, -22.86))
# FSW resistor to SW, BOOT capacitor to SW
wire((-15.24, -7.62), (-30.48, -7.62)); vres('R252', '301k', R301K, (-30.48, -7.62)); wire((-30.48, -15.24), (-30.48, -22.86))
wire((-15.24, -15.24), (-17.78, -15.24)); rcap('C267', '100nF', C100N, (-17.78, -15.24), tl=True)
# EN (AMP_BOOST_EN port) with pull-down
wire((-15.24, 5.08), (-33.02, 5.08)); junc((-22.86, 5.08)); hlabel('AMP_BOOST_EN', 'input', (-33.02, 5.08), 180)
vres('R255', '100k', R100K, (-22.86, 5.08)); gnd((-22.86, -2.54))
# MODE: floating = PFM; DNP 0R to GND = forced PWM option
wire((-15.24, -30.48), (-27.94, -30.48)); vres('R256', '0R DNP', R0, (-27.94, -30.48), dnp=True); gnd((-27.94, -38.1))
# VCC 2.2 uF
wire((2.54, 20.32), (2.54, 27.94), (15.24, 27.94)); vcap('C265', '2.2uF', C2U2, (15.24, 27.94))
# VOUT rail: feedback divider, output capacitors, PVDD_AMP
wire((15.24, 15.24), (114.3, 15.24)); label('PVDD_AMP', (114.3, 15.24))
junc((17.78, 15.24))
vres('R250', '499k', R499K, (17.78, 15.24)); wire((15.24, 7.62), (17.78, 7.62)); junc((17.78, 7.62))
vres('R251', '56k', R56K, (17.78, 7.62)); gnd((17.78, 0))
vcap('C270', '1uF', C1U, (30.48, 15.24)); junc((30.48, 15.24))
for k, x in enumerate((45.72, 60.96, 76.2, 91.44)):
    vcap(f'C{271+k}', '22uF 25V', C22_25, (x, 15.24)); junc((x, 15.24))
vcap('C275', '100uF 25V', C100U, (106.68, 15.24), lib='PD_CP:PD_CP'); junc((106.68, 15.24))
# COMP network
wire((15.24, -5.08), (33.02, -5.08)); junc((17.78, -5.08))
vres('R254', '82k', R82K, (17.78, -5.08)); vcap('C268', '6.8nF', C6N8, (17.78, -12.7))
vcap('C269', '47pF', C47P, (33.02, -5.08))
# ILIM and SS
wire((15.24, -25.4), (17.78, -25.4)); vres('R253', '150k', R150K, (17.78, -25.4)); gnd((17.78, -33.02))
wire((15.24, -38.1), (17.78, -38.1)); vcap('C266', '47nF', C47N, (17.78, -38.1))
gnd((-10.16, -43.18)); gnd((10.16, -43.18))

# =========================================================== TAS5825M blocks
def tas(ref, c, first, adr_val, adr_part, caprefs, rows, jdefs, pbtl, res_refs):
    cx, cy = c
    X = lambda dx: cx + dx
    Y = lambda dy: cy + dy
    pins_new = ['13', '12', '14', '15', '16', '17', '8', '9', '10', '11', '6', '[3,4,21,22]', '7', '18', '19', '[5,20,25,26,31,32,33]',
                '1', '2', '30', '29', '24', '23', '27', '28']
    transplant(ref, c, (cx, cy - 30.5), (cx, cy - 32.5), pins_new)
    # --- digital stubs (left)
    for dy, name, shape in ((25.4, 'I2S_BCK', 'input'), (22.86, 'I2S_LRCK', 'input'), (20.32, 'I2S_SDATA', 'input'),
                            (12.7, 'AUD_SDA', 'bidirectional'), (10.16, 'AUD_SCL', 'bidirectional')):
        wire((X(-E), Y(dy)), (X(-30.48), Y(dy)))
        if first: hlabel(name, shape, (X(-30.48), Y(dy)), 180)
        else: label(name, (X(-30.48), Y(dy)), 'right bottom')
    # PDN: 1k series, shared pull-down at the first device
    rA, rB, rC, rD = res_refs
    res(rA, '1k', R1K, (X(-E - 3.81), Y(2.54)), True)
    wire((X(-E - 7.62), Y(2.54)), (X(-35.56), Y(2.54)))
    if first:
        wire((X(-35.56), Y(2.54)), (X(-48.26), Y(2.54))); junc((X(-43.18), Y(2.54)))
        hlabel('AMP_PDN', 'input', (X(-48.26), Y(2.54)), 180)
        vres(rD, '100k', R100K, (X(-43.18), Y(2.54))); gnd((X(-43.18), Y(-5.08)))
    else:
        label('AMP_PDN', (X(-35.56), Y(2.54)), 'right bottom')
    # ADR strap
    res(rB, adr_val, adr_part, (X(-E - 3.81), Y(-5.08)), True); gnd((X(-E - 7.62), Y(-5.08)))
    # GPIO0 FAULT (open drain, wired-OR), GPIO1/2 unused
    wire((X(-E), Y(-12.7)), (X(-30.48), Y(-12.7))); label('AMP_FAULT_N', (X(-30.48), Y(-12.7)), 'right bottom')
    nc((X(-E), Y(-15.24))); nc((X(-E), Y(-17.78)))
    # --- DVDD (3V3_AUDIO) and PVDD (PVDD_AMP) rails
    wire((X(-7.62), Y(33.02)), (X(-7.62), Y(45.72)), (X(-40.64), Y(45.72)))
    if first: hlabel('3V3_AUDIO', 'input', (X(-40.64), Y(45.72)), 180)
    else: label('3V3_AUDIO', (X(-40.64), Y(45.72)), 'right bottom')
    junc((X(-17.78), Y(45.72))); junc((X(-30.48), Y(45.72)))
    c1, c2, c3, c4, c5, c6 = caprefs[:6]
    vcap(c1, '4.7uF', C4U7, (X(-17.78), Y(45.72))); vcap(c2, '100nF', C100N, (X(-30.48), Y(45.72)))
    wire((X(7.62), Y(33.02)), (X(7.62), Y(45.72)), (X(76.2), Y(45.72))); label('PVDD_AMP', (X(76.2), Y(45.72)))
    for dx, nm, v, part in ((17.78, c3, '100nF', C100N), (33.02, c4, '22uF 25V', C22_25), (48.26, c5, '100nF', C100N), (63.5, c6, '22uF 25V', C22_25)):
        junc((X(dx), Y(45.72))); vcap(nm, v, part, (X(dx), Y(45.72)))
    # --- internal regulator capacitors and ground stack
    vcap(caprefs[6], '1uF', C1U, (X(-17.78), Y(-35.56)), tl=True); vcap(caprefs[7], '1uF', C1U, (X(-10.16), Y(-35.56))); vcap(caprefs[8], '1uF', C1U, (X(10.16), Y(-35.56)))
    gnd((X(20.32), Y(-35.56)))
    # --- bootstrap capacitors, one per BST pin to its output pin
    XC = E + 7.62
    # BST_A+ (27.94) -> OUT_A+ (20.32); OUT_A- (15.24) -> BST_A- (7.62); BST_B+ (2.54) -> OUT_B+ (-5.08); OUT_B- (-10.16) -> BST_B- (-17.78)
    b1, b2, b3, b4 = caprefs[9:13]
    wire((X(E), Y(27.94)), (X(XC), Y(27.94))); rcap(b1, '0.47uF', C470N, (X(XC), Y(27.94)))
    wire((X(E), Y(20.32)), (X(XC), Y(20.32))); junc((X(XC), Y(20.32)))
    wire((X(E), Y(15.24)), (X(XC), Y(15.24))); junc((X(XC), Y(15.24)))
    rcap(b2, '0.47uF', C470N, (X(XC), Y(15.24))); wire((X(XC), Y(7.62)), (X(E), Y(7.62)))
    wire((X(E), Y(2.54)), (X(XC), Y(2.54))); rcap(b3, '0.47uF', C470N, (X(XC), Y(2.54)))
    wire((X(E), Y(-5.08)), (X(XC), Y(-5.08))); junc((X(XC), Y(-5.08)))
    wire((X(E), Y(-10.16)), (X(XC), Y(-10.16))); junc((X(XC), Y(-10.16)))
    rcap(b4, '0.47uF', C470N, (X(XC), Y(-10.16))); wire((X(XC), Y(-17.78)), (X(E), Y(-17.78)))
    # --- output filters and connectors
    XL, XN, XA, XB, XJ = 60.96, 73.66, 91.44, 96.52, 106.68
    if not pbtl:
        XJ_ = {}
        xj = {0: XC, 1: XC + 17.78, 2: XC + 15.24, 3: XC + 12.7}
        pin_y = (20.32, 15.24, -5.08, -10.16)
        for k, (py, ry) in enumerate(zip(pin_y, rows)):
            if k == 0:
                wire((X(XC), Y(py)), (X(XL - 3.81), Y(ry)))
            else:
                wire((X(XC), Y(py)), (X(xj[k]), Y(py)), (X(xj[k]), Y(ry)), (X(XL - 3.81), Y(ry)))
    else:
        XM = XC + 3.81
        wire((X(XC), Y(20.32)), (X(XM), Y(20.32)), (X(XM), Y(15.24)), (X(XC), Y(15.24)))
        junc((X(XM), Y(17.78))); wire((X(XM), Y(17.78)), (X(XL - 3.81), Y(rows[0])))
        wire((X(XC), Y(-5.08)), (X(XM), Y(-5.08)), (X(XM), Y(-10.16)), (X(XC), Y(-10.16)))
        junc((X(XM), Y(-7.62))); wire((X(XM), Y(-7.62)), (X(XL - 3.81), Y(rows[1])))
    for k, ry in enumerate(rows):
        lref, cref = jdefs['L'][k], jdefs['C'][k]
        ind(lref, '22uH', L22, (X(XL), Y(ry)))
        wire((X(XL + 3.81), Y(ry)), (X(XN), Y(ry))); junc((X(XN), Y(ry)))
        vcap(cref, '0.68uF 50V', C680N, (X(XN), Y(ry)))
    for (jref, jname, jy, ra, rb, ya, yb) in jdefs['J']:
        jc = (X(XJ + 5.08), Y(jy))
        instance('JST_B2P_VH', jref, 'B2P-VH', 'DesktopSpeaker:JST_B2P_VH_1x02_P3.96mm_Vertical', jc, (jc[0] + 5.08, jc[1] + 1.27), (jc[0] + 5.08, jc[1] - 1.27),
                 [('Datasheet', 'https://www.jst-mfg.com/product/pdf/eng/eVH.pdf'), ('MPN', 'B2P-VH(LF)(SN)'), ('Manufacturer', 'JST'), ('LCSC Part', 'C160315')],
                 [('1', U()), ('2', U())])
        wire((X(XN), Y(ra)), (X(XA), Y(ra)), (X(XA), Y(jy + 2.54)), (X(XJ), Y(jy + 2.54)))
        wire((X(XN), Y(rb)), (X(XB), Y(rb)), (X(XB), Y(jy - 2.54)), (X(XJ), Y(jy - 2.54)))
        text(jname, (X(XJ + 12.7), Y(jy + 6.35)))

CX = 177.8
U6c = (CX, 48.26); U7c = (CX, -48.26 + 0.0)
tas('U6', U6c, True, '0R', R0, ['C280', 'C281', 'C276', 'C277', 'C278', 'C279', 'C282', 'C283', 'C284', 'C285', 'C286', 'C287', 'C288'],
    (20.32, 5.08, -12.7, -27.94), {'L': ['L201', 'L202', 'L203', 'L204'], 'C': ['C302', 'C303', 'C304', 'C305'],
     'J': [('J9', 'FRONT_L', 12.7, 20.32, 5.08, 0, 0), ('J10', 'FRONT_R', -20.32, -12.7, -27.94, 0, 0)]}, False,
    ('R257', 'R260', None, 'R259'))
tas('U7', U7c, False, '1k', R1K, ['C293', 'C294', 'C289', 'C290', 'C291', 'C292', 'C295', 'C296', 'C297', 'C298', 'C299', 'C300', 'C301'],
    (17.78, -7.62), {'L': ['L205', 'L206'], 'C': ['C306', 'C307'], 'J': [('J11', 'WOOFER', 5.08, 17.78, -7.62, 0, 0)]}, True,
    ('R258', 'R261', None, None))
# FAULT pull-up and output port (right side)
fx = CX + 129.54
x_, y_ = fx, U7c[1] - 17.78
label('3V3_AUDIO', (x_, y_)); vres('R262', '10k', R10K, (x_, y_))
wire((fx, U7c[1] - 25.4), (fx, U7c[1] - 27.94), (fx + 7.62, U7c[1] - 27.94)); hlabel('AMP_FAULT_N', 'output', (fx + 7.62, U7c[1] - 27.94), 0)
# notes
NX, NY = -99.06, -60.96
notes = [
    'U7 PBTL pairing verified against SLASEH7F Fig. 159 / 10.2.5 (page 86 rendered): OUT_A+ (2) with OUT_A- (30) merged to L205; OUT_B+ (23) with OUT_B- (27) merged to L206; speaker between the two filtered nodes.',
    'Firmware: write DAMP_PBTL (reg 0x02 bit 2) = 1 on U7 before it leaves Hi-Z; the PBTL mixer takes the left I2S frame, so the U7 DSP forms (L+R)/2. No cycle-by-cycle current limit in PBTL.',
    'U25: VOUT = 1.204 V x (1 + 499k/56k) = 11.93 V (PFM: 12.0 V; OVP 12.7-13.6 V). FSW about 494 kHz (RFREQ 301k). ILIM 150k = 7.9 A typ, 6.6 A min in PFM (equation 3). L200 Isat 19.6 A.',
    'COMP: R254 82k, C268 6.8nF, C269 47pF (equations 18-20, fc about 5 kHz, effective Co about 170 uF): calculated only, bench check required. MODE floating = PFM; R256 DNP 0R to GND = forced PWM.',
    'TAS5825M addresses: U6 ADR 0R = 0x4C, U7 ADR 1k = 0x4D. AMP_PDN shared (1k each, 100k pull-down). GPIO0 = FAULTZ (open drain) wired-OR to AMP_FAULT_N, 10k pull-up to 3V3_AUDIO. GPIO1/2 not connected.',
    'DVDD = 3V3_AUDIO. Bootstrap caps are 0.47uF (Table 66). Filter 22uH + 0.68uF per output. No MCLK pin: TAS5825M locks to SCLK. Speaker connectors: pin 1 +, pin 2 -.']
for i, s in enumerate(notes):
    text(s, (NX, NY - 2.54 * i))

lib_syms = '(lib_symbols ' + ' '.join([tas_emb, ic_emb, l_emb, cp_emb, j_emb, PD_C, PD_R, GND]) + ')'
hdr = ['(kicad_sch', '(version 20260306)', '(generator "eeschema")', '(generator_version "10.0")',
       f'(uuid "{SHEET_UUID}")', '(paper "A2")',
       '(title_block (title "Amplifiers") (rev "0.1") (comment 1 "TPS61088 PVDD boost, two TAS5825M (stereo BTL and mono PBTL), LC output filters, speaker connectors"))',
       lib_syms]
OUT.write_text('\n'.join(hdr + items) + '\n)\n')

# ------------------------------------------------------------------ sym-lib-table
tbl = (ROOT / 'sym-lib-table').read_text()
add = ''
for nm, ds in (('TPS61088RHLR', 'Texas Instruments TPS61088 boost converter'), ('PD_L', 'Generic inductor'), ('PD_CP', 'Generic polarized capacitor'),
               ('JST_B2P_VH', 'JST B2P-VH 2-pin VH header')):
    if f'(name "{nm}")' not in tbl:
        add += f'  (lib (name "{nm}") (type "KiCad") (uri "${{KIPRJMOD}}/kicad-library/schematic/{nm}.kicad_sym") (options "") (descr "{ds}"))\n'
idx = tbl.rindex(')')
(ROOT / 'sym-lib-table').write_text(tbl[:idx] + add + tbl[idx:])

# ------------------------------------------------------------------ root edits
for r in sorted(old, key=lambda r: -old[r][0]):
    a, e, _ = old[r]
    rt = rt[:a] + rt[e:]
s = grab(rt, 'TAS5825MRHBR:TAS5825MRHBR'); rt = rt.replace(s, '', 1)
MX, MY, MW, MH = 203.2, 15.24, 40.64, 50.8
left = [('3V3_AUDIO', 'input', 20.32), ('SYS_RAW', 'input', 25.4), ('I2S_BCK', 'input', 30.48), ('I2S_LRCK', 'input', 35.56), ('I2S_SDATA', 'input', 40.64),
        ('AMP_PDN', 'input', 45.72), ('AUD_SCL', 'bidirectional', 50.8), ('AUD_SDA', 'bidirectional', 55.88), ('AMP_BOOST_EN', 'input', 60.96)]
right = [('AMP_FAULT_N', 'output', 20.32)]
new = []
sp = ''
for n, t, y in left:
    sp += f'(pin "{n}" {t} (at {f(MX)} {f(y)} 180) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}")) '
    new.append(f'(wire (pts (xy {f(MX)} {f(y)}) (xy {f(MX-5.08)} {f(y)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    new.append(f'(label "{n}" (at {f(MX-5.08)} {f(y)} 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}"))')
for n, t, y in right:
    sp += f'(pin "{n}" {t} (at {f(MX+MW)} {f(y)} 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}")) '
    new.append(f'(wire (pts (xy {f(MX+MW)} {f(y)}) (xy {f(MX+MW+5.08)} {f(y)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    new.append(f'(label "{n}" (at {f(MX+MW+5.08)} {f(y)} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
new.insert(0, f'(sheet (at {f(MX)} {f(MY)}) (size {f(MW)} {f(MH)}) (stroke (width 0) (type default)) (fill (color 255 255 255 0)) (uuid "{SHEET_UUID}") '
           f'(property "Sheet name" "Amplifiers" (at {f(MX)} {f(MY-1.27)} 0) (effects (font (size 1.27 1.27)) (justify left))) '
           f'(property "Sheet file" "Amplifiers.kicad_sch" (at {f(MX)} {f(MY+MH)} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
           + sp + f'(instances (project "DesktopSpeaker" (path "/{ROOT_UUID}" (page "12")))))')
# MCU block: grow upward, add AMP_PDN / AMP_BOOST_EN outputs and AMP_FAULT_N input
assert '(sheet (at 320.04 109.22) (size 50.8 96.52)' in rt
rt = rt.replace('(sheet (at 320.04 109.22) (size 50.8 96.52)', '(sheet (at 320.04 99.06) (size 50.8 106.68)', 1)
rt, n1 = re.subn(r'(\(property "Sheet name" "MCU" \(at 320.04 )[\d.]+( 0\))', r'\g<1>97.79\2', rt, 1); assert n1
mcu_i = rt.index('(property "Sheet name" "MCU"')
amp_out = [('AMP_PDN', 104.14), ('AMP_BOOST_EN', 106.68)]
amp_in = [('AMP_FAULT_N', 127.0)]
mp = ''.join(f'(pin "{n}" output (at 370.84 {f(y)} 0) (effects (font (size 1 1)) (justify right bottom)) (uuid "{U()}")) ' for n, y in amp_out)
mp += ''.join(f'(pin "{n}" input (at 320.04 {f(y)} 180) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}")) ' for n, y in amp_in)
j = rt.index('(pin ', mcu_i)
rt = rt[:j] + mp + rt[j:]
for n, y in amp_out:
    new.append(f'(wire (pts (xy 370.84 {f(y)}) (xy 375.92 {f(y)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    new.append(f'(label "{n}" (at 375.92 {f(y)} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{U()}"))')
for n, y in amp_in:
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
for nm, py in (('AMP_PDN', '123.19'), ('AMP_BOOST_EN', '125.73')):
    mt = rm_nc(mt, '165.1', py); mt = rm_text(mt, f'{nm} (reserved)')
    add.append(f'(wire (pts (xy 165.1 {py}) (xy 215.9 {py})) (stroke (width 0) (type default)) (uuid "{U()}"))')
    add.append(f'(hierarchical_label "{nm}" (shape output) (at 215.9 {py} 0) (effects (font (size 1.0 1.0)) (justify right bottom)) (uuid "{U()}"))')
mt = rm_nc(mt, '114.3', '100.33'); mt = rm_text(mt, 'AMP_FAULT_N (reserved)')
add.append(f'(wire (pts (xy 45.72 100.33) (xy 114.3 100.33)) (stroke (width 0) (type default)) (uuid "{U()}"))')
add.append(f'(hierarchical_label "AMP_FAULT_N" (shape input) (at 45.72 100.33 0) (effects (font (size 1.0 1.0)) (justify left bottom)) (uuid "{U()}"))')
assert mt.rstrip().endswith(')')
(ROOT / 'MCU.kicad_sch').write_text(mt.rstrip()[:-1] + '\n'.join(add) + '\n)\n')
print('sheet uuid', SHEET_UUID)
