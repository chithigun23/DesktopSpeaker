#!/usr/bin/env python3
"""One-shot BOM text edit for the 2026-11-03 review fixes (pack secondary protection).

Adds one sentence to the PACK row note (Availability text only; no quantity, price or formula changes) in
  ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv,
  ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx (sheet1.xml inline string; other zip members copied byte for byte),
  ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx.inspect.ndjson (same string in the inspection snapshot).
Modelled on bom_sync_pack_1s4p.py. Refuses to run twice: backups ai-files/backups/*.pre-packfuse must not exist.
Run from anywhere: python3 ai-files/helpers/bom_sync_pack_fuse_tco.py
"""
import shutil, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / 'ai-files/bom'
FILES = [B / 'DesktopSpeaker_LCSC_Starter_BOM.csv', B / 'DesktopSpeaker_LCSC_Starter_BOM.xlsx', B / 'DesktopSpeaker_LCSC_Starter_BOM.xlsx.inspect.ndjson']
BK = ROOT / 'ai-files/backups'

ANCHOR = 'vendor/MPN still UNRESOLVED (RFQ, no price). '
ADD = ('2026-11-03 review fixes: the RFQ adds a 15 A PACK+ fuse, an about 85 C thermal cut-off and a 22.3 mm maximum '
       'thickness (reports/review-fixes-2026-11-03.md). ')
PAIRS = [(ANCHOR, ANCHOR + ADD)]

for f in FILES:
    if (BK / (f.name + '.pre-packfuse')).exists():
        sys.exit(f'refusing: backup for {f.name} exists (already applied)')


def patch_text(t, where):
    if ADD in t:
        sys.exit(f'{where}: already contains the new sentence')
    for a, b in PAIRS:
        if t.count(a) != 1:
            sys.exit(f'{where}: {a[:40]!r} found {t.count(a)} times')
        t = t.replace(a, b)
    return t


new = {}
for f in (FILES[0], FILES[2]):
    new[f] = patch_text(f.read_bytes().decode('utf-8'), f.name).encode('utf-8')
zin = zipfile.ZipFile(FILES[1])
members = []
for info in zin.infolist():
    data = zin.read(info.filename)
    if info.filename == 'xl/worksheets/sheet1.xml':
        data = patch_text(data.decode('utf-8'), 'sheet1.xml').encode('utf-8')
    members.append((info, data))
zin.close()
BK.mkdir(exist_ok=True)
for f in FILES:
    shutil.copy2(f, BK / (f.name + '.pre-packfuse'))
for f in (FILES[0], FILES[2]):
    f.write_bytes(new[f])
tmp = FILES[1].with_suffix('.xlsx.tmp')
with zipfile.ZipFile(tmp, 'w') as zout:
    for info, data in members:
        zout.writestr(info, data, compress_type=info.compress_type)
tmp.replace(FILES[1])
print('patched PACK row note in', ', '.join(f.name for f in FILES))
