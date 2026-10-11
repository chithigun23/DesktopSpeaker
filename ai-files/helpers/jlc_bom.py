#!/usr/bin/env python3
"""jlc_bom.py SCH_BOM.csv OUT.csv : JLC assembly BOM (Comment, Designator, Footprint, LCSC Part #, MPN, Manufacturer, Qty) from a
per-reference kicad-cli BOM export (fields Reference,Value,Footprint,MPN,Manufacturer,LCSC,LCSC Part,DNP). Groups by LCSC code + footprint;
skips DNP parts and the off-board panel rocker SW101."""
import csv, sys, re, collections
rows = list(csv.DictReader(open(sys.argv[1])))
OFF = {'SW101'}
def rk(r): m = re.match(r'([A-Za-z]+)(\d+)', r); return (m.group(1), int(m.group(2)))
g = collections.OrderedDict()
for r in sorted(rows, key=lambda r: rk(r['Reference'])):
    ref = r['Reference']; code = (r['LCSC'] or r['LCSC Part']).strip()
    if r['DNP'].strip() or ref in OFF: continue
    fp = r['Footprint'].split(':')[-1]
    d = g.setdefault((code, fp), {'refs': [], 'vals': collections.Counter(), 'mpn': r['MPN'], 'mfr': r['Manufacturer']})
    d['refs'].append(ref); d['vals'][r['Value']] += 1
with open(sys.argv[2], 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #', 'MPN', 'Manufacturer', 'Qty'])
    for (code, fp), d in g.items(): w.writerow([d['vals'].most_common(1)[0][0], ','.join(d['refs']), fp, code, d['mpn'], d['mfr'], len(d['refs'])])
print('lines', len(g), 'placements', sum(len(d['refs']) for d in g.values()), 'no code:', [d['refs'] for (c, fp), d in g.items() if not c])
