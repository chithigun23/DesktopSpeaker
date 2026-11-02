#!/usr/bin/env python3
"""sync.py SRC.kicad_pcb OUT.kicad_pcb REPORT.json : text-level board sync with the patched schematic (P1, P4, P5).
Pad nets from the exported netlist (2026-11-02), copper net rename /CHG_INT -> /PC15_SPARE (R106-2 to U3-5 stub kept).
Every op must match exactly once, otherwise abort."""
import sys, json, re
src, out, repf = sys.argv[1:4]
PADS = {('U3', '5'): ('/CHG_INT', '/PC15_SPARE'), ('R106', '2'): ('/CHG_INT', '/PC15_SPARE'),
        ('U4', '21'): ('/CHG_INT', 'unconnected-(U4-~{INT}-Pad21)'),
        ('U3', '33'): ('unconnected-(U3-PB13-Pad33)', '/PDCTRL_SDA'),
        ('U3', '44'): ('/PDCTRL_SDA', 'unconnected-(U3-PA12[PA10]-Pad44)'),
        ('J7', '3'): ('/MCU/NRST', 'unconnected-(J7-Pin_3-Pad3)')}
RENAME = {'/CHG_INT': '/PC15_SPARE'}
L = open(src, encoding='utf-8').read().split('\n')
rep = dict(pads=[], copper_rename=[])
i = 0; ref = None; done = {}
while i < len(L):
    s = L[i]
    if s.startswith('\t(footprint '): ref = None
    m = re.match(r'^\t\t\(property "Reference" "([^"]+)"', s)
    if m: ref = m.group(1)
    m = re.match(r'^\t\t\(pad "([^"]*)" ', s)
    if m and (ref, m.group(1)) in PADS:
        j = i + 1
        while not L[j].startswith('\t\t)'):
            if L[j].startswith('\t\t\t(net '):
                old, new = PADS[(ref, m.group(1))]
                assert L[j] == '\t\t\t(net "%s")' % old, (ref, m.group(1), L[j])
                L[j] = '\t\t\t(net "%s")' % new; done[(ref, m.group(1))] = done.get((ref, m.group(1)), 0) + 1
                rep['pads'].append([ref, m.group(1), old, new])
            j += 1
    m = re.match(r'^\t\((segment|via|arc|zone)', s)
    if m:
        j = i + 1
        while L[j] != '\t)':
            mm = re.match(r'^\t\t\(net "([^"]*)"\)$', L[j])
            if mm and mm.group(1) in RENAME:
                L[j] = '\t\t(net "%s")' % RENAME[mm.group(1)]
                u = next((re.search(r'"([^"]+)"', x).group(1) for x in L[i:j + 40] if x.startswith('\t\t(uuid ')), '?')
                rep['copper_rename'].append([m.group(1), u, mm.group(1), RENAME[mm.group(1)]])
            j += 1
        i = j
    i += 1
assert all(done.get(k) == 1 for k in PADS), done
txt = '\n'.join(L)
for n in ('"/CHG_INT"',): assert n not in txt, n
open(out, 'w', encoding='utf-8').write(txt)
json.dump(rep, open(repf, 'w'), indent=1)
print('pads', len(rep['pads']), 'copper renamed', len(rep['copper_rename']))
