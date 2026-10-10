#!/usr/bin/env python3
"""One-shot BOM edit for the sync-y200-c275 pass (2026-10-10).

- Y200: JYJE 3TJ424576UYFBC C2149067 (CL 15 pF, 135 stock) -> YXC X322524576MOB4SI C70568 (CL 12 pF).
- C226/C227: 22 pF GRM1555C1H220JA01D C76960 -> 15 pF GRM1555C1H150JA01D C76950 (matches 12 pF CL).
- C275: function/notes text only (3D model repointed, datasheet D8 dimensions corrected).

Patches the CSV, then the matching data rows of the 'Selected BOM' sheet XML in the xlsx
(formulas kept, cached values of I/L/M and E4/E5 recomputed). Other zip members are copied byte for byte.
Refuses to run twice: backups ai-files/backups/*.pre-sync must not exist.
Run from the project root: python3 ai-files/helpers/bom_sync_y200_c275.py
"""
import csv, io, math, re, shutil, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / 'ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv'
XLSX = ROOT / 'ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx'
BK = ROOT / 'ai-files/backups'

for f in (CSV, XLSX):
    b = BK / (f.name + '.pre-sync')
    if b.exists():
        sys.exit(f'refusing: {b} exists (already applied)')
for f in (CSV, XLSX):
    shutil.copy2(f, BK / (f.name + '.pre-sync'))

raw = CSV.read_text(encoding='utf-8')
rows = list(csv.reader(io.StringIO(raw, newline='')))
H = rows[0]
col = {h: i for i, h in enumerate(H) if h}
NOTE = 17  # unnamed notes column (R)

def find(ref):
    hits = [i for i, r in enumerate(rows) if r[0] == ref]
    if len(hits) != 1:
        sys.exit(f'row {ref!r}: {len(hits)} hits')
    return hits[0]

def setrow(i, **kw):
    r = rows[i]
    for k, v in kw.items():
        if k == 'notes':
            r[NOTE] = v
        else:
            r[col[k]] = v

# --- Y200 ---
i = find('Y200')
old = rows[i][:]
assert old[col['LCSC part']] == 'C2149067', old
setrow(i, **{
    'Function': '24.576 MHz crystal for PCM1862 (3225-4P, CL 12 pF)',
    'Manufacturer': 'YXC', 'MPN': 'X322524576MOB4SI', 'LCSC part': 'C70568',
    'Fitted qty': '1', 'MOQ': '5', 'Multiple': '5', 'Order qty': '5', 'Tier start': '5',
    'Unit USD': '0.1042', 'Fitted USD': '0.1042', 'Order USD': '0.521', 'Stock qty': '4055',
    'Availability': ('In stock; replacement 2026-10-10 (sync-y200-c275; was JYJE 3TJ424576UYFBC C2149067, 135 in stock); '
                     'verified against LCSC listing C70568 (YXC X322524576MOB4SI, SMD3225-4P; 24.576MHz, 12pF, ±10ppm, ±20ppm, ESR 50Ω); '
                     'JLC extended; LCSC stock 4055, JLC list stock 5135 at lookup vs order qty 5; price is the listed ladder at order qty; re-check at order.'),
    'Accessed': '46305', 'Cache age': '2026-10-10',
    'LCSC source URL': 'https://www.lcsc.com/product-detail/C70568.html',
    'notes': ('Source_Select_ADC sheet, 2026-10-06. REPLACEMENT 2026-10-10 (reports/sync-y200-c275.md): JYJE 3TJ424576UYFBC C2149067 '
              '(CL 15 pF, 135 in stock) -> YXC X322524576MOB4SI C70568: 24.576 MHz fundamental, CL 12 pF, +/-10 ppm at 25 C, +/-20 ppm -40..85 C, '
              'ESR 50 ohm max (16-31 MHz), C0 3 pF max, 3.2 x 2.5 x 0.7 mm, 4055 in stock. Reason: no 15 pF 24.576 MHz 3225 crystal had more '
              'than 1000 in stock; with the 12 pF part, C226/C227 change 22 pF -> 15 pF C0G: CL = 15*15/30 + 3-5 pF stray = 10.5-12.5 pF. '
              'Lower CL also lowers the gm needed from the PCM1862 1.8 V XI/XO oscillator. Datasheet datasheets/YXC_YSX321SL_X322524576MOB4SI.pdf: '
              'pads 1/3 crystal, 2/4 GND, land 1.4 x 1.2 mm at 2.2 x 1.7 mm pitch, matches Crystal_SMD_3225-4Pin_3.2x2.5mm (pad 1 XI, pad 3 XO). '
              'History: Lucki L327S240P11L C5261154 (listed as 24 MHz, wrong frequency; stock 0) -> 3TJ424576UYFBC C2149067 -> this part.'),
})
print('Y200:', old[2], old[3], old[4], '->', rows[i][2], rows[i][3], rows[i][4])

# --- C226, C227 ---
i = find('C226, C227')
old = rows[i][:]
assert old[col['LCSC part']] == 'C76960', old
setrow(i, **{
    'Function': '15pF C0G 0402 hand-solder (C_0402_1005Metric)',
    'Manufacturer': 'Murata', 'MPN': 'GRM1555C1H150JA01D', 'LCSC part': 'C76950',
    'Fitted qty': '2', 'MOQ': '100', 'Multiple': '100', 'Order qty': '100', 'Tier start': '100',
    'Unit USD': '0.0054', 'Fitted USD': '0.0108', 'Order USD': '0.54', 'Stock qty': '55300',
    'Availability': ('In stock; value change 2026-10-10 (sync-y200-c275; was 22pF GRM1555C1H220JA01D C76960); verified against LCSC listing '
                     'C76950 (muRata GRM1555C1H150JA01D, 0402; 15pF, ±5%, 50V, C0G); JLC extended; LCSC stock 55300, JLC list stock 60138 at lookup '
                     'vs order qty 100; price is the listed ladder at order qty; re-check at order.'),
    'Accessed': '46305', 'Cache age': '2026-10-10',
    'LCSC source URL': 'https://www.lcsc.com/product-detail/C76950.html',
    'notes': ('Passive repackage 2026-10-06 (hand-solder policy): was C_0603 using CL10C220JB8NNNC. See reports/passive-repackage-2026-10-06.md. '
              'VALUE CHANGE 2026-10-10 (reports/sync-y200-c275.md): 22 pF GRM1555C1H220JA01D C76960 -> 15 pF GRM1555C1H150JA01D C76950 to match '
              'the 12 pF Y200 replacement (X322524576MOB4SI): CL = 7.5 pF + 3-5 pF stray = 10.5-12.5 pF. Same Murata C0G 50 V +/-5% 0402 series, '
              'same footprint. Trim at bring-up if the measured frequency error exceeds about 20 ppm.'),
})
print('C226/C227:', old[3], old[4], '->', rows[i][3], rows[i][4])

# --- C275 (text only) ---
i = find('C275')
r = rows[i]
assert r[col['LCSC part']] == 'C264047', r
r[col['Function']] = 'PVDD_AMP bulk 100uF 25V hybrid polymer (D6.3 x 7.7 mm part on CP_Elec_8x10 pads)'
n = r[NOTE]
a = 'terminals span about +/-1.1 to +/-3.5 mm (datasheet P 2.2, I 2.4 for size D8)'
b = 'terminals span about +/-0.9 to +/-3.9 mm (datasheet size D8: P 1.8, I 2.6, H 7.8 max, W 0.65; corrected 2026-10-10)'
c = '3D model is the 8x10 one, cosmetic only.'
d = ('3D model repointed 2026-10-10 (reports/sync-y200-c275.md) to kicad-library/3d/CP_Elec_6.3x7.7.step (KiCad library model; '
     'measured body D6.3, base 6.6 x 6.6, height 7.7, terminal span 7.8, terminal width 0.65 mm = datasheet D8); pads and copper unchanged.')
assert a in n and c in n, n
r[NOTE] = n.replace(a, b).replace(c, d)
print('C275: function/notes updated')

def enc(rr):
    return ','.join(('"%s"' % f.replace('"', '""')) if f != '' else '' for f in rr)
CSV.write_text('\n'.join(enc(rr) for rr in rows) + '\n', encoding='utf-8')

# ---------------- xlsx ----------------
def xesc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

fitted = sum(float(rr[col['Fitted USD']]) for rr in rows[1:] if rr[col['Fitted USD']])
order = sum(float(rr[col['Order USD']]) for rr in rows[1:] if rr[col['Order USD']])
E4, E5 = round(fitted, 2), round(order, 2)
print('totals: fitted %.4f -> E4 %.2f, order %.4f -> E5 %.2f' % (fitted, E4, order, E5))

zin = zipfile.ZipFile(BK / (XLSX.name + '.pre-sync'))
sheet = zin.read('xl/worksheets/sheet1.xml').decode('utf-8')
letters = [chr(65 + k) for k in range(19)]  # A..S

def patch_cell(rowxml, ref, value, numeric):
    m = re.search(r'<x:c r="%s"( s="\d+")?( t="\w+")?\s*(/>|>(.*?)</x:c>)' % ref, rowxml, re.S)
    if not m:
        sys.exit('cell %s not found' % ref)
    style = m.group(1) or ''
    inner = m.group(4) or ''
    fm = re.search(r'<x:f>.*?</x:f>', inner, re.S)
    f = fm.group(0) if fm else ''
    if value == '':
        new = '<x:c r="%s"%s />' % (ref, style) if not f else '<x:c r="%s"%s t="str">%s<x:v></x:v></x:c>' % (ref, style, f)
    elif numeric:
        new = '<x:c r="%s"%s t="n">%s<x:v>%s</x:v></x:c>' % (ref, style, f, value)
    else:
        new = '<x:c r="%s"%s t="str">%s<x:v>%s</x:v></x:c>' % (ref, style, f, xesc(value))
    return rowxml[:m.start()] + new + rowxml[m.end():]

NUMERIC = {'Fitted qty', 'MOQ', 'Multiple', 'Order qty', 'Tier start', 'Unit USD', 'Fitted USD', 'Order USD', 'Stock qty', 'Accessed'}
for ref in ('Y200', 'C226, C227', 'C275'):
    ci = find(ref)
    xr = ci + 10  # CSV row index 1 -> sheet row 11
    m = re.search(r'<x:row r="%d"[^>]*>.*?</x:row>' % xr, sheet, re.S)
    rowxml = m.group(0)
    first = re.search(r'<x:c r="A%d"[^>]*><x:v>(.*?)</x:v>' % xr, rowxml).group(1)
    if first != xesc(ref):
        sys.exit('sheet row %d is %r, expected %r' % (xr, first, ref))
    for k, letter in enumerate(letters):
        name = H[k] if H[k] else None
        val = rows[ci][k]
        rowxml = patch_cell(rowxml, '%s%d' % (letter, xr), val, (name in NUMERIC) and val != '')
    sheet = sheet[:m.start()] + rowxml + sheet[m.end():]
sheet = re.sub(r'(<x:c r="E4"[^>]*><x:f>[^<]*</x:f><x:v>)[^<]*(</x:v>)', r'\g<1>%.2f\g<2>' % E4, sheet)
sheet = re.sub(r'(<x:c r="E5"[^>]*><x:f>[^<]*</x:f><x:v>)[^<]*(</x:v>)', r'\g<1>%.2f\g<2>' % E5, sheet)

tmp = XLSX.with_suffix('.xlsx.tmp')
with zipfile.ZipFile(tmp, 'w') as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == 'xl/worksheets/sheet1.xml':
            data = sheet.encode('utf-8')
        zout.writestr(item, data)
tmp.replace(XLSX)
print('wrote', CSV.relative_to(ROOT), XLSX.relative_to(ROOT))
