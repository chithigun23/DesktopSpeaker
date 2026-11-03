#!/usr/bin/env python3
"""One-shot edit of ai-files/bom/hardware-buy-list.csv for the 2026-11-03 fastener schedule and review fixes.

- Updates existing rows in place (numbering stable; superseded rows keep their number with quantity 0 and a dated note).
- Appends new rows 43+ (fasteners, seals, damping, cable management, wire, pack fuse/TCO, feet, knob, tools, printed parts).
Row data for the sourced parts is in buylist_review_fixes_20261103_rows.py (same folder).
Refuses to run twice (checks for the first appended row). Backup: ai-files/backups/hardware-buy-list.csv.pre-reviewfix-20261103.
Then run render_hardware_buylist_md.py to regenerate the Markdown mirror.
"""
import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from buylist_review_fixes_20261103_rows import UPDATES, NEW_ROWS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / 'ai-files/bom/hardware-buy-list.csv'
HDR = ['Item', 'Qty', 'Qty 2nd unit', 'Spec', 'Source', 'Part number', 'Unit price', 'Line price', 'Stock/date', 'Notes',
       'Category', 'Price status', 'URL']

rows = list(csv.DictReader(open(CSV, newline='', encoding='utf-8')))
if any(r['Item'] == NEW_ROWS[0]['Item'] for r in rows):
    sys.exit('refusing: new rows already present (already applied)')
if len(rows) != 42:
    sys.exit(f'expected 42 data rows, found {len(rows)}')
for n, (must_start, changes) in UPDATES.items():
    r = rows[n - 1]
    if not r['Item'].startswith(must_start):
        sys.exit(f'row {n}: expected item starting {must_start!r}, found {r["Item"]!r}')
    for k, v in changes.items():
        if k not in HDR:
            sys.exit(f'row {n}: unknown column {k}')
        r[k] = v(r[k]) if callable(v) else v
for nr in NEW_ROWS:
    missing = set(HDR) - set(nr)
    if missing:
        sys.exit(f'new row {nr["Item"][:40]}: missing {missing}')
    rows.append({k: nr[k] for k in HDR})
buf = io.StringIO()
w = csv.DictWriter(buf, fieldnames=HDR, lineterminator='\r\n')  # the file uses CRLF line ends
w.writeheader()
w.writerows(rows)
CSV.write_text(buf.getvalue(), encoding='utf-8')
print(f'wrote {CSV.relative_to(ROOT)}: {len(rows)} data rows ({len(NEW_ROWS)} appended, {len(UPDATES)} updated)')
