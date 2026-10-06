# -*- coding: utf-8 -*-
"""Passive-to-IC pin distance statistics and zone separations of DesktopSpeaker.kicad_pcb.
Run: flatpak run --filesystem=/home/chithi/Desktop/DesktopSpeaker --command=python3 org.kicad.KiCad ai-files/helpers/pcb_dist_check.py [board] [out.json]
Distance = pad centre to pad centre between a passive (R/C/FB) pad on a non-GND net and the nearest pad of a non-passive part on the same net
(power rails with many IC pins: nearest pin). Passives with no IC pin on their nets are listed as 'chain' (connected only through other passives)."""
import sys, json, math, collections, re
import pcbnew
B = sys.argv[1] if len(sys.argv) > 1 else '/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb'
OUT = sys.argv[2] if len(sys.argv) > 2 else None
bd = pcbnew.LoadBoard(B)
MM = 1e6
ispas = lambda r: r[0] in 'RC' and r[1].isdigit() or r.startswith('FB')
pads = collections.defaultdict(list)   # net -> (ref, pin, x, y)
fp = {}
for f in bd.GetFootprints():
    r = f.GetReference()
    fp[r] = f
    for p in f.Pads():
        n = p.GetNetname()
        if n and n != 'GND':
            pads[n].append((r, p.GetNumber(), p.GetPosition().x / MM, p.GetPosition().y / MM))
res = collections.defaultdict(list); chain = []
decap = {}      # C with one GND pad: ref -> (distance, ic, pin, net)
for r, f in fp.items():
    if not ispas(r):
        continue
    best = None
    for p in f.Pads():
        n = p.GetNetname()
        if not n or n == 'GND':
            continue
        px, py = p.GetPosition().x / MM, p.GetPosition().y / MM
        for (r2, pin2, x, y) in pads[n]:
            if r2 == r or ispas(r2) or r2.startswith('H'):
                continue
            d = math.hypot(px - x, py - y)
            if best is None or d < best[0]:
                best = (d, r2, pin2, n)
    if best is not None and r[0] == 'C' and any(p.GetNetname() == 'GND' for p in f.Pads()):
        decap[r] = best
    if best is None:
        chain.append(r)
    else:
        res[best[1]].append((r, round(best[0], 2), best[2], best[3]))
print('%-6s %4s %6s %6s  worst' % ('IC', 'n', 'max', 'mean'))
out = {}
for ic in sorted(res):
    l = res[ic]; ds = [x[1] for x in l]
    w = max(l, key=lambda x: x[1])
    out[ic] = dict(n=len(l), max=max(ds), mean=round(sum(ds) / len(ds), 2), worst=w, items=l)
    print('%-6s %4d %6.2f %6.2f  %s -> pin %s (%s)' % (ic, len(l), max(ds), sum(ds) / len(ds), w[0], w[2], w[3]))
allds = [x[1] for l in res.values() for x in l]
print('ALL passives with IC pin: n=%d max %.2f mean %.2f; chain-only: %d' % (len(allds), max(allds), sum(allds) / len(allds), len(chain)))
print('>3mm: %d  >5mm: %d  >8mm: %d' % tuple(sum(d > t for d in allds) for t in (3, 5, 8)))
small = {r: v for r, v in decap.items() if '0402' in str(fp[r].GetFPID().GetLibItemName())}
bulk = {r: v for r, v in decap.items() if r not in small}
for nm, g in (('0402 HF decaps', small), ('0805+ bulk caps', bulk)):
    x = [v[0] for v in g.values()]
    print('%s: n=%d max %.2f mean %.2f  >3: %d  >6: %d' % (nm, len(x), max(x), sum(x) / len(x), sum(d > 3 for d in x), sum(d > 6 for d in x)))
dd = [v[0] for v in decap.values()]
print('DECAP (C with a GND pad): n=%d max %.2f mean %.2f  >2: %d  >3: %d  >5: %d' % (len(dd), max(dd), sum(dd) / len(dd), sum(d > 2 for d in dd), sum(d > 3 for d in dd), sum(d > 5 for d in dd)))
for r, v in sorted(decap.items(), key=lambda x: -x[1][0])[:int(len(sys.argv) > 3 and sys.argv[3] or 0)]:
    print('   far decap %s %.1f mm -> %s pin %s (%s)' % (r, v[0], v[1], v[2], v[3]))
# separations (courtyard/footprint bbox edges, mm)
def bbox(r):
    b = fp[r].GetBoundingBox(False)   # excludes text
    return (b.GetX() / MM, b.GetY() / MM, b.GetRight() / MM, b.GetBottom() / MM)
def gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0); dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)
def mingap(g1, g2):
    best = (1e9, '', '')
    for a in g1:
        for b in g2:
            d = gap(bbox(a), bbox(b))
            if d < best[0]:
                best = (d, a, b)
    return best
amps = ['U6', 'U7', 'L201', 'L202', 'L203', 'L204', 'L205', 'L206']
boost = ['U25', 'L200']
chg = ['U4', 'L1']
analog = ['U24', 'U10', 'U8', 'U9', 'J2', 'J3', 'U23', 'U22', 'U2']
ASHEETS = ('Source_Select_ADC', 'Headphone_Aux', 'USB_Audio')
LJ = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/layout.json'))
SH = LJ.get('sheets', {})
analog_all = [r for r in fp if SH.get(r) in ASHEETS and r not in ('Y170',)]
sep = {}
for name, g1, g2 in [('BM83-amp/inductors', ['U1'], amps), ('BM83-boost', ['U1'], boost), ('BM83-charger SW', ['U1'], chg),
                     ('BM83-analog audio', ['U1'], analog), ('classD-analog', amps, analog), ('boost-analog', boost, analog),
                     ('charger-analog', chg, analog), ('BM83-analog ALL parts', ['U1'], analog_all),
                     ('classD-analog ALL parts', amps + [r for r in fp if r.startswith('C') and SH.get(r) == 'Amplifiers' and r not in ('C275',)], analog_all),
                     ('boost-analog ALL parts', boost + ['C275'], analog_all), ('L2/U14-analog ALL', ['L2', 'U14'], analog_all)]:
    d = mingap(g1, g2); sep[name] = d
    print('SEP %-20s %6.1f mm  (%s - %s)' % (name, d[0], d[1], d[2]))
if OUT:
    json.dump(dict(ic=out, chain=chain, sep=sep), open(OUT, 'w'), indent=1)
