#!/usr/bin/env python3
"""One-shot BOM text edit for the 1S4P pack decision (2026-11-03).

Updates the PACK row (Function and Availability/notes text only; no quantity, price or formula changes) in
  ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv,
  ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx (sheet1.xml inline strings B38 / O38; other zip members copied byte for byte),
  ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx.inspect.ndjson (same strings in the inspection snapshot).
Refuses to run twice: backups ai-files/backups/*.pre-pack1s4p must not exist.
Run from anywhere: python3 ai-files/helpers/bom_sync_pack_1s4p.py
"""
import shutil, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / 'ai-files/bom'
FILES = [B / 'DesktopSpeaker_LCSC_Starter_BOM.csv', B / 'DesktopSpeaker_LCSC_Starter_BOM.xlsx', B / 'DesktopSpeaker_LCSC_Starter_BOM.xlsx.inspect.ndjson']
BK = ROOT / 'ai-files/backups'

OLD_FN = 'Protected 1S Li-ion pack with 10k NTC; capacity/curve/lead open'
NEW_FN = 'Protected 1S4P Li-ion pack, 20 Ah (4 x INR21700-50S), 10k NTC (B 3435); vendor/MPN open (RFQ)'
OLD_NOTE = 'UNRESOLVED 2026-10-10: no pack MPN chosen. Cells (2P 21700), '
NEW_NOTE = ('2026-11-03: pack decided 1S4P (4 x INR21700-50S, 20 Ah, about 72 Wh; spec in hardware-buy-list.csv row 32 and '
            'reports/battery-pack-rfq.md); vendor/MPN still UNRESOLVED (RFQ, no price). '
            'UNRESOLVED 2026-10-10: no pack MPN chosen. Cells (2P 21700 at the time), ')
PAIRS = [(OLD_FN, NEW_FN), (OLD_NOTE, NEW_NOTE)]

for f in FILES:
    if (BK / (f.name + '.pre-pack1s4p')).exists():
        sys.exit(f'refusing: backup for {f.name} exists (already applied)')

def patch_text(t, where):
    for a, b in PAIRS:
        if t.count(a) != 1:
            sys.exit(f'{where}: {a[:40]!r} found {t.count(a)} times')
        t = t.replace(a, b)
    return t

new = {}
# the CSV Function field was unquoted; the new text has commas, so it is written quoted
_csv = FILES[0].read_bytes().decode('utf-8').replace('PACK,' + OLD_FN + ',', 'PACK,"' + OLD_FN + '",', 1)
new[FILES[0]] = patch_text(_csv, 'csv').encode('utf-8')
new[FILES[2]] = patch_text(FILES[2].read_bytes().decode('utf-8'), 'ndjson').encode('utf-8')
zin = zipfile.ZipFile(FILES[1])
members = []
for info in zin.infolist():
    data = zin.read(info.filename)
    if info.filename == 'xl/worksheets/sheet1.xml':
        data = patch_text(data.decode('utf-8'), 'sheet1.xml').encode('utf-8')
    members.append((info, data))
BK.mkdir(exist_ok=True)
for f in FILES:
    shutil.copy2(f, BK / (f.name + '.pre-pack1s4p'))
for f in (FILES[0], FILES[2]):
    f.write_bytes(new[f])
tmp = FILES[1].with_suffix('.xlsx.tmp')
with zipfile.ZipFile(tmp, 'w') as zout:
    for info, data in members:
        zout.writestr(info, data, compress_type=info.compress_type)
tmp.replace(FILES[1])
print('patched PACK row in', ', '.join(f.name for f in FILES))
