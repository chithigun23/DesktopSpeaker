#!/usr/bin/env python3
"""Render ai-files/bom/hardware-buy-list.md from ai-files/bom/hardware-buy-list.csv (2026-11-03).

The CSV is the source of truth; the Markdown file mirrors it line for line (# = CSV data row number, stable:
new lines are appended, superseded lines keep their number with quantity 0). Subtotals are recomputed here.
Re-run after every CSV edit: python3 ai-files/helpers/render_hardware_buylist_md.py
Subtotal rule: a line counts when its Price status is exactly 'confirmed' or 'estimate' and its Line price parses.
Second-unit extra = leading integer of 'Qty 2nd unit' x unit price (0 when the column starts with 0).
USD/GBP are converted at ASSUMED 1.50 / 2.00 AUD (rates not looked up). Partial subtotal, NOT a product cost.
"""
import csv
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / 'ai-files/bom/hardware-buy-list.csv'
MD = ROOT / 'ai-files/bom/hardware-buy-list.md'
RATE = 1.50   # AUD per USD, ASSUMED
RATES = {'AUD': 1.0, 'USD': RATE, 'GBP': 2.00, 'EUR': 1.70}  # GBP/EUR ASSUMED, not looked up
TOOL_CATS = {'Tools'}

INTRO = """# Hardware and consumables buy list (one unit + second-unit column)

First compiled 2026-10-12; **updated 2026-11-03 for the fastener schedule and the CAD completeness review fixes** (`reports/fastener-schedule-2026-11-03.md`, `reports/project-review-cad-completeness-2026-11-03.md`, decisions in `reports/review-fixes-2026-11-03.md`). Everything needed to build one complete DesktopSpeaker that is NOT on `bom/DesktopSpeaker_JLC_BOM.csv` (SW101 is excluded from that BOM and is listed here). Machine-readable source: `bom/hardware-buy-list.csv`; this file is rendered from it by `helpers/render_hardware_buylist_md.py` (# = CSV data row, numbering stable: new lines are appended at the end, superseded lines keep their number with quantity 0 and a dated note).

**All prices and stock figures are snapshots (2026-10-12 or 2026-11-03, date per line; some from search-result snippets). They are not quotes. Re-check every line at order time. Shipping, GST/import duty and currency fees are not included.** Digi-Key, Mouser, LCSC, Parts Express and Tag-Connect prices are USD; Australian stores are AUD (Core, Jaycar and Bolt and Nut figures include GST). Digi-Key AU prices are AUD **ex GST**; Polymax is GBP inc VAT. Totals convert USD at an ASSUMED 1.50 AUD/USD and GBP at 2.00 AUD/GBP (rates not looked up).

Price status: **confirmed** = price read from the store page/listing; **estimate** = guessed or snippet-only figure; **TBD** = no source or quote; **printed** = made from the filament line, no purchase; lines marked *optional* or *superseded* are excluded from subtotals. Spares: at least 10 % on every new fastener and seal line (2026-11-03).
"""

TAIL = """
## Design points found while sourcing (2026-10-12, refreshed 2026-11-03)

- Micro-Fit crimps: 43030-0007 is 20-24 AWG only. PACK+/PACK- 18 AWG need 43030-0038 (insulation OD <= 1.85; use thin-wall wire, OD <= 1.7). Pin 2 (NTC, 24 AWG) uses 43030-0007.
- Pack lead: RFQ about 180 mm against the 131 mm CAD v15 route; the slack is dressed on a tie point on the J5 path.
- Tag-Connect: J7 is the legged TC2030 footprint and the STLINK-V3MINIE has STDC14, so TC2030-CTX-STDC14 plugs straight in.
- J4 (PD controller I2C) and J8 (BM83 UART) need a 3.3 V USB adapter. The MCP2221A UART speed for isUpdate/Config Tool is unverified.
- Grilles: proposed as 0.8 mm black FR4 with NPTH holes from JLCPCB (CAD mass still uses steel). Both grilles are backed with the black cloth (row 4).
- Filament: about 692 g solid-volume basis (+20 % = 831 g) before the knob cup, plungers and tie bridges: one roll per unit is tight.
- Grommet: Heyco 2000 needs a 6.35 mm hole and a panel of at most 1.57 mm: CAD v16 uses 6.35 / 1.5.
- Feet: Wurth 971120321 = RS 176-8061 (M3 M/F, 12 mm body, 6 mm stud); the rubber foot screws into its female end (row 63).
- Rocker fastons: TE 2-520194-2 (0.187 x 0.032 in tab assumed from the CAD stand-in).
- History: the 2026-10-12 version of this file (hand-written, with the A$473.59 confirmed snapshot) is in git history and `ai-files/backups/hardware-buy-list.md.pre-reviewfix-20261103`.

## Tools note (2026-11-03)

- Every enclosure screw is **T10 post-Torx (pin Torx)**: a plain T10 bit or key does not fit, and **ball-end keys do not work with post-Torx**. The old "2.5 mm ball-end hex key" instructions (M3x16 socket screws) are superseded.
- Bits: T10 post-Torx 25 mm insert bits (row 41, x2: one + spare) in a 1/4 in driver. The 8 driver screws are driven through the empty shell, about 190 mm deep: use the **1/4 in bit extension of 200 mm or more** (row 49) before the woofer-chamber insert goes in.
- L-keys: T10 post-Torx 90 mm L-key (row 45, x2). Short arm 19 mm. **H8** (under the knob dish) has 11.7 mm of headroom when the dish is part of the shell: cut the short arm of the second key to about 8 mm. With the separate knob cup (CAD v16) H8 is reached from above with the cup removed, so the cut key is a fallback. HA1/HA2 are about 120 mm in from the rear opening: check the reach with the real key.
- Woofer screws (M3x20 button) are driven before the insert goes in (77 mm vertical space): L-key or a stubby 1/4 in holder.
- Vent holes: 0.5 mm carbide PCB drill (row 65) in a pin vice; do not print 1 mm holes.
- Heat-set inserts: soldering iron with an M3 insert tip (row 38 optional) or a plain conical tip.
"""


def num(s):
    m = re.search(r'(-?\d+(?:\.\d+)?)', s or '')
    return float(m.group(1)) if m else None


def money(s):
    m = re.match(r'\s*(AUD|USD|EUR|GBP)\s*([\d.,]+)', s or '')
    if not m:
        return None, None
    return m.group(1), float(m.group(2).replace(',', ''))


def lead_int(s):
    m = re.match(r'\s*(\d+)', s or '')
    return int(m.group(1)) if m else None


def esc(s):
    return (s or '').replace('|', '/').replace('\n', ' ')


def main():
    rows = list(csv.DictReader(open(CSV, newline='', encoding='utf-8')))
    cats = OrderedDict()
    for i, r in enumerate(rows, 1):
        cats.setdefault(r['Category'], []).append((i, r))
    out = [INTRO]
    for cat, items in cats.items():
        out.append(f'\n## {cat}\n')
        out.append('| # | Item | Qty (unit 1) | 2nd unit | Spec | Source / part number | Unit price | Line price | Stock / date | Status | Notes |')
        out.append('|---|---|---|---|---|---|---|---|---|---|---|')
        for i, r in items:
            src = esc(r['Source'])
            if r['URL'] and r['URL'] != '-':
                src = f"[{src}]({r['URL']})"
            out.append('| ' + ' | '.join([str(i), esc(r['Item']), esc(r['Qty']), esc(r['Qty 2nd unit']), esc(r['Spec']),
                                           f"{src}: {esc(r['Part number'])}", esc(r['Unit price']), esc(r['Line price']),
                                           esc(r['Stock/date']), esc(r['Price status']), esc(r['Notes'])]) + ' |')
    # subtotals
    sub = OrderedDict()
    tot = {'build': 0.0, 'tools': 0.0, 'est': 0.0, 'u2': 0.0}
    for i, r in enumerate(rows, 1):
        st = r['Price status'].strip()
        if st not in ('confirmed', 'estimate'):
            continue
        cur, lp = money(r['Line price'])
        if cur is None or lp == 0:
            continue
        _, up = money(r['Unit price'])
        n2 = lead_int(r['Qty 2nd unit']) or 0
        u2 = (n2 * up) if (up is not None) else 0.0
        key = (r['Source'], cur)
        d = sub.setdefault(key, {'conf': 0.0, 'conf2': 0.0, 'est': 0.0, 'est2': 0.0})
        aud = RATES.get(cur, 1.0)
        if st == 'confirmed':
            d['conf'] += lp
            d['conf2'] += u2
            if r['Category'] in TOOL_CATS:
                tot['tools'] += lp * aud
            else:
                tot['build'] += lp * aud
        else:
            d['est'] += lp
            d['est2'] += u2
            tot['est'] += lp * aud
        tot['u2'] += u2 * aud
    out.append('\n## Subtotals per source (unit 1 order; second-unit extra)\n')
    out.append('| Source | Currency | Confirmed, unit 1 | Confirmed, 2nd-unit extra | Estimate, unit 1 | Estimate, 2nd-unit extra |')
    out.append('|---|---|---|---|---|---|')
    for (s, c), d in sub.items():
        out.append(f"| {esc(s)} | {c} | {d['conf']:.2f} | {d['conf2']:.2f} | {d['est']:.2f} | {d['est2']:.2f} |")
    out.append('')
    out.append(f"- **Unit 1, confirmed prices: about A${tot['build'] + tot['tools']:.2f}** (A${tot['build']:.2f} build parts + A${tot['tools']:.2f} one-off tools).")
    out.append(f"- Plus estimates: about A${tot['est']:.2f}. **Unit 1 including estimates: about A${tot['build'] + tot['tools'] + tot['est']:.2f}.**")
    out.append(f"- Second unit extra (from the 2nd-unit column x unit price): about A${tot['u2']:.2f}.")
    out.append('- **Not included anywhere:** the battery pack (RFQ, no price; the 15 A fuse and thermal cut-off are asked from the pack vendor), lines marked TBD, optional or superseded, printed parts (filament line only), shipping and duty, the PCB/stencil order and the electronics BOM. **This is a partial cost, not a complete product cost.**')
    # lists
    out.append('\n## Lines without a confirmed source or price\n')
    for i, r in enumerate(rows, 1):
        st = r['Price status'].strip()
        if st in ('confirmed',) or st.startswith(('printed', 'cut')) or 'superseded' in (r['Qty'] or '').lower() or 'optional' in st:
            continue
        out.append(f"- #{i} {esc(r['Item'])}: {st} ({esc(r['Notes'])[:220]})")
    out.append('\n## Superseded lines (kept for history, quantity 0)\n')
    for i, r in enumerate(rows, 1):
        if 'superseded' in (r['Qty'] or '').lower():
            out.append(f"- #{i} {esc(r['Item'])}: {esc(r['Qty'])}")
    out.append(TAIL)
    MD.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'wrote {MD.relative_to(ROOT)}: {len(rows)} lines, unit 1 confirmed A${tot["build"] + tot["tools"]:.2f}, estimates A${tot["est"]:.2f}')


if __name__ == '__main__':
    main()
