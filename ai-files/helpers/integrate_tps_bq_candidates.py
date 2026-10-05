#!/usr/bin/env python3
"""Integrate reviewed TPS25730D USB_PD and BQ25792 Battery_Charger candidates into the active project (2026-10-05)."""
import re, shutil, uuid, pathlib
R = pathlib.Path('/home/chithi/Desktop/DesktopSpeaker')
C = R/'ai-files/candidates'; P = R/'DesktopSpeaker-kicad'; L = P/'kicad-library'
ROOT = 'feda53ed-537d-4f88-9436-c6075776255b'
U = lambda: str(uuid.uuid4())

# --- library assets
fp = (C/'TPS25730D.pretty/Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4.kicad_mod').read_text()
fp = fp.replace('(footprint "Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4"', '(footprint "TPS25730D"', 1)
fp = fp.replace('${KIPRJMOD}/ai-files/candidates/REF0038A.stp', '${KIPRJMOD}/kicad-library/3d/REF0038A.stp')
assert '(footprint "TPS25730D"' in fp and 'kicad-library/3d/REF0038A.stp' in fp
(L/'footprint/TPS25730D.kicad_mod').write_text(fp)
shutil.copy(C/'REF0038A.stp', L/'3d/REF0038A.stp')
shutil.copy(C/'PD_C_0402.kicad_mod', L/'footprint/PD_C_0402.kicad_mod')
sym = (C/'TPS25730D.kicad_sym').read_text().replace('TPS25730D:Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4', 'DesktopSpeaker:TPS25730D')
(L/'schematic/TPS25730DREFR.kicad_sym').write_text(sym)
t = (P/'sym-lib-table').read_text()
if 'TPS25730DREFR' not in t:
    t = t.rstrip().rstrip(')') + '  (lib (name "TPS25730DREFR") (type "KiCad") (uri "${KIPRJMOD}/kicad-library/schematic/TPS25730DREFR.kicad_sym") (options "") (descr "5-20V USB PD sink controller, TI REF0038A"))\n)\n'
    (P/'sym-lib-table').write_text(t)

# --- flag lib symbol extracted from old USB_PD
old = (P/'USB_PD.kicad_sch').read_text()
def balanced(s, start):
    d = 0
    for i in range(start, len(s)):
        if s[i] == '(': d += 1
        elif s[i] == ')':
            d -= 1
            if d == 0: return s[start:i+1]
flag_lib = balanced(old, old.index('(symbol "PD_PWR_FLAG:PD_PWR_FLAG"'))

def flag(x, y, ref, path, rot=0, hide_val=False):
    v = ' (hide yes)' if hide_val else ''
    return (f'(symbol (lib_id "PD_PWR_FLAG:PD_PWR_FLAG") (at {x} {y} {rot}) (unit 1) (exclude_from_sim no) (in_bom no) (on_board no) (dnp no) (uuid "{U()}") '
            f'(property "Reference" "{ref}" (at {x} {y-6.35} 0) (effects (font (size 1.27 1.27)) (hide yes))) '
            f'(property "Value" "PWR_FLAG" (at {x} {y-3.81} 0) (effects (font (size 1.27 1.27)){v})) '
            f'(property "Footprint" "" (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27)))) (property "Datasheet" "" (at {x} {y} 0) (hide yes) (effects (font (size 1.27 1.27)))) '
            f'(pin "1" (uuid "{U()}")) (instances (project "DesktopSpeaker" (path "{path}" (reference "{ref}") (unit 1)))))\n')

def build(src, dst, flags, repl):
    s = (C/src).read_text()
    for a, b in repl: 
        assert a in s, a
        s = s.replace(a, b)
    i = s.index('(symbol "', s.index('(lib_symbols') )
    s = s[:i] + flag_lib + ' ' + s[i:]
    s = s.rstrip()
    assert s.endswith(')')
    s = s[:-1] + ''.join(flags) + ')\n'
    (P/dst).write_text(s)

pd = f'/{ROOT}/f38b7023-3d53-43ea-b3db-e2c826d87b35'
bc = f'/{ROOT}/a7066d55-4393-49f1-9dcb-c2e9f1db9549'
build('TPS25730D_USB_PD_candidate.kicad_sch', 'USB_PD.kicad_sch',
      [flag(50.8, 60.96, '#FLG301', pd), flag(215.9, 68.58, '#FLG302', pd), flag(114.3, 71.12, '#FLG303', pd, 270, True)],
      [('TPS25730D:Texas_REF0038A_WQFN-38-2EP_6x4mm_P0.4', 'DesktopSpeaker:TPS25730D')])
build('Battery_Charger.kicad_sch', 'Battery_Charger.kicad_sch',
      [flag(365.76, 167.64, '#FLG304', bc)],
      [('DesktopSpeaker:SRN6045TA-2R2Y', 'DesktopSpeaker:Bourns_SRN6045TA-2R2Y')])

# --- root sheet pins
r = (P/'DesktopSpeaker.kicad_sch').read_text()
def rm(pat):
    global r
    n = len(re.findall(pat, r)); assert n == 1, (pat, n)
    r = re.sub(pat, '', r)
rm(r'\(pin "GND" input \(at 100\.33 170\.18 180\).*?\(uuid "63c7c9a1[^"]*"\)\)\s')
rm(r'\(wire \(pts \(xy 100\.33 170\.18\) \(xy 95\.25 170\.18\)\).*?\)\n')
rm(r'\(wire \(pts \(xy 95\.25 170\.18\) \(xy 95\.25 175\.26\)\).*?\)\n')
m = re.search(r'\(symbol \(lib_id "power:GND"\) \(at 95\.25 175\.26 0\).*?\n', r); assert m
r = r.replace(m.group(0), '')
def pin(name, kind, x, y, ang, just):
    return f'(pin "{name}" {kind} (at {x} {y} {ang}) (effects (font (size 1 1)) (justify {just})) (uuid "{U()}")) '
newpd = (pin('PD_PLUG_EVENT','output',146.05,154.94,0,'right bottom') + pin('PD_SINK_EN','output',146.05,162.56,0,'right bottom') +
         pin('PDCTRL_SCL','bidirectional',146.05,170.18,0,'right bottom') + pin('PDCTRL_SDA','bidirectional',146.05,177.8,0,'right bottom'))
a = '(pin "USB_AUX_5V" output (at 146.05 144.78 0)'
assert a in r; r = r.replace(a, newpd + a)
newbc = pin('CHG_SYS_ENABLE','input',166.37,175.26,180,'left bottom')
a = '(pin "SYS_RAW" output (at 219.71 147.32 0)'
assert a in r; r = r.replace(a, newbc + a, 1)
ncs = ''.join(f'(no_connect (at 146.05 {y}) (uuid "{U()}"))\n' for y in (154.94,162.56,170.18,177.8)) + f'(no_connect (at 166.37 175.26) (uuid "{U()}"))\n'
i = r.rindex(')')
r = r[:i].rstrip('\n') + '\n' + ncs + ')\n'
(P/'DesktopSpeaker.kicad_sch').write_text(r)
print('ok')
