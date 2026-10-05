import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[2]
xml_path = root / 'ai-files/reports/gauge-voltage-domain-after.xml'
csv_path = root / 'ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv'
out_path = root / 'ai-files/reports/gauge-interface-bom-reconciliation.json'
net_root = ET.parse(xml_path).getroot()
components = []
for comp in net_root.findall('.//components/comp'):
    props = {p.get('name'): p.get('value', '') for p in comp.findall('./property')}
    components.append({
        'reference': comp.get('ref'),
        'mpn': props.get('MPN', ''),
        'lcsc': props.get('LCSC', props.get('LCSC Part', '')),
    })

rows = list(csv.reader(csv_path.open(newline='', encoding='utf-8')))
bom = {}
duplicates = []
for row in rows[1:]:
    if not row or not row[0]:
        continue
    for ref in re.findall(r'\b[A-Z]+\d+\b', row[0]):
        if ref in bom:
            duplicates.append(ref)
        bom[ref] = {
            'mpn': row[3] if len(row) > 3 else '',
            'lcsc': row[4] if len(row) > 4 else '',
            'function': row[1] if len(row) > 1 else '',
            'fitted_qty': row[5] if len(row) > 5 else '',
        }

net_refs = {c['reference'] for c in components}
bom_refs = set(bom)
missing_from_bom = sorted(net_refs - bom_refs)
extra_in_bom = sorted(bom_refs - net_refs)
checks = {'mpn': {'checked': 0, 'matched': 0, 'mismatches': [], 'unresolved': []},
          'lcsc': {'checked': 0, 'matched': 0, 'mismatches': [], 'unresolved': []}}
for comp in components:
    row = bom.get(comp['reference'])
    if not row:
        continue
    for field in ('mpn', 'lcsc'):
        expected = comp[field]
        listed = row[field]
        if expected and expected != 'TBD':
            checks[field]['checked'] += 1
            if not listed:
                checks[field]['unresolved'].append(comp['reference'])
            elif listed != expected:
                checks[field]['mismatches'].append({'reference': comp['reference'], 'netlist': expected, 'bom': listed})
            else:
                checks[field]['matched'] += 1
        elif listed and listed != 'TBD':
            checks[field]['unresolved'].append(comp['reference'])

focus = ['Q104', 'C126', 'U21', 'R126', 'R127']
net_by_ref = {c['reference']: c for c in components}
requested_identity = {ref: {'netlist': {'mpn': net_by_ref.get(ref, {}).get('mpn', ''), 'lcsc': net_by_ref.get(ref, {}).get('lcsc', '')}, 'bom': {'mpn': bom.get(ref, {}).get('mpn', ''), 'lcsc': bom.get(ref, {}).get('lcsc', '')}, 'matches': bool(net_by_ref.get(ref)) and net_by_ref[ref]['mpn'] == bom.get(ref, {}).get('mpn') and net_by_ref[ref]['lcsc'] == bom.get(ref, {}).get('lcsc')} for ref in focus}
report = {
    'date': '2026-10-05',
    'scope': 'Current active fuel-gauge undervoltage interface; candidate charger/PD parts excluded.',
    'sources': {
        'bom_xlsx': 'ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx',
        'bom_csv': 'ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv',
        'netlist_xml': str(xml_path.relative_to(root)),
    },
    'coverage': {
        'netlist_physical_references': len(components),
        'bom_physical_references': len(bom_refs),
        'missing_from_bom': missing_from_bom,
        'extra_in_bom': extra_in_bom,
        'duplicate_bom_references': sorted(set(duplicates)),
        'identity_checks': checks,
        'existing_unresolved_netlist_metadata': checks['mpn']['unresolved'] + checks['lcsc']['unresolved'],
    },
    'requested_rows': {ref: bom.get(ref) for ref in focus},
    'requested_reference_identity': requested_identity,
    'materials': {
        'U21': {'manufacturer': 'Texas Instruments', 'mpn': 'TPS3839G33DBZR', 'lcsc': 'C485802', 'listing_snapshot_stock': 3444, 'listing_snapshot_usd_at_1': 0.439, 'datasheet': 'https://www.ti.com/lit/ds/symlink/tps3839.pdf'},
        'R126_R127': {'manufacturer': 'YAGEO', 'mpn': 'RC0603FR-071ML', 'lcsc': 'C105578', 'value': '1 MOhm, 1%, 0603', 'listing_snapshot_stock': 359600, 'listing_snapshot_usd_at_100': 0.0056, 'moq_multiple': 100, 'datasheet': 'https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-071ML'},
        'Q104_reuse': {'mpn': '2N7002,215', 'lcsc': 'C65189', 'shared_bom_row': 'Q100, Q104'},
        'C126_reuse': {'mpn': 'CL10B104KB8NNNC', 'lcsc': 'C1591', 'shared_bom_row': 'C120, C121, C130, C131, C132, C143, C151, C126'},
    },
    'formula_scan': {'result_path': 'ai-files/reports/gauge-interface-bom-formula-scan.ndjson', 'matches': 0},
    'subtotal_usd': {'fitted': 75.61, 'in_stock_order': 95.01, 'complete_product_cost': False},
    'limitations': ['Listing stock and price are volatile snapshots.', '2N7002 cold gate-drive qualification remains open.'],
}
out_path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
