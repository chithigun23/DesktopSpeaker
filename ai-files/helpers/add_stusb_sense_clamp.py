from pathlib import Path
import sys, uuid, copy, json
sys.path.insert(0, 'ai-files/vendor')
from sexpdata import load, dumps, Symbol as S

def kind(a):
    return str(a[0]) if isinstance(a, list) and a else ''

def one(a, name):
    return next(z for z in a if kind(z) == name)

def props(a):
    return {z[1]: z for z in a if kind(z) == 'property'}

def unique_tree(a):
    for z in a:
        if kind(z) == 'uuid':
            z[1] = str(uuid.uuid4())
        elif isinstance(z, list):
            unique_tree(z)

def relocate(a, ref, cx, cy):
    old = one(a, 'at')
    dx, dy = cx-old[1], cy-old[2]
    old[1:3] = [cx, cy]
    for f in props(a).values():
        at = one(f, 'at')
        at[1] += dx
        at[2] += dy
    props(a)['Reference'][2] = ref
    for project in one(a, 'instances')[1:]:
        for path in project[2:]:
            one(path, 'reference')[1] = ref
    unique_tree(a)

def wire(a, b):
    return [S('wire'), [S('pts'), [S('xy'), *a], [S('xy'), *b]],
            [S('stroke'), [S('width'), 0], [S('type'), S('default')]],
            [S('uuid'), str(uuid.uuid4())]]

path = Path('DesktopSpeaker-kicad/USB_PD.kicad_sch')
original = path.read_text()
sheet = load(path.open())
refs = {props(a)['Reference'][2]: a for a in sheet if kind(a) == 'symbol'}
assert 'D9' not in refs, 'One-shot clamp already applied'
backup = Path('ai-files/backups/USB_PD-before-sense-clamp.kicad_sch')
if not backup.exists():
    backup.write_text(original)
datasheet = '${KIPRJMOD}/../ai-files/datasheets/Diodes_BZT52C_ds18004.pdf'
props(refs['D7'])['Datasheet'][2] = datasheet
diode = copy.deepcopy(refs['D7'])
relocate(diode, 'D9', 128.27, 135.89)
props(diode)['Datasheet'][2] = datasheet
for name, yy in [('Reference', 134.62), ('Value', 137.16)]:
    one(props(diode)[name], 'at')[1:] = [134.62, yy, 0]
sheet.append(diode)
ground = copy.deepcopy(refs['#PWR24'])
relocate(ground, '#PWR190', 128.27, 142.24)
one(props(ground)['Value'], 'at')[1:] = [128.27, 147.32, 0]
sheet.append(ground)
sheet.extend([wire((128.27, 129.54), (128.27, 132.08)),
              wire((128.27, 139.7), (128.27, 142.24))])
path.write_text('(' + dumps(sheet[0]) + '\n' + '\n'.join(dumps(z) for z in sheet[1:]) + ')\n')
library = Path('DesktopSpeaker-kicad/kicad-library/schematic/BZT52C12-7-F.kicad_sym')
library.write_text(library.read_text().replace('https://www.diodes.com/assets/Datasheets/ds18001.pdf', datasheet))
report = {'part': 'D9 BZT52C12-7-F /C124196',
          'scope': 'Pin-side VBUS_VS_DISCH clamp after R4=3.3k for 5/9-only contracts; not raw VDD protection',
          'datasheet': 'Diodes_BZT52C_ds18004.pdf',
          'vz_25C_at5mA_V': [11.4, 12.7],
          'temperature_coefficient_mV_per_C': [6, 10],
          'conservative_cold_min_at_minus40C_V': 10.75,
          'conservative_hot_max_at125C_V': 13.7,
          'maximum_fault_branch_current_estimate_mA': (28.4-10.75)/(3300*.99)*1000,
          'comment': 'Normal 9.45V max below estimated cold knee; 20V fault clipped but still invalid for 9V contract. Component-table arithmetic is not complete dynamic qualification. Raw VDD remains open. Corrected inherited D7 datasheet link to unrelated BZX84 SOT23 series.'}
Path('ai-files/reports/stusb-sense-clamp.json').write_text(json.dumps(report, indent=2)+'\n')
