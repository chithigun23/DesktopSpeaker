#!/usr/bin/env python3
"""Assert critical BQ25792 candidate net groups and power-rail isolation."""
from pathlib import Path
import re

NET = Path(__file__).resolve().parents[1] / "candidates/Battery_Charger-candidate.net"
text = NET.read_text()

def members(net):
    pattern = r'\(net\s*\(code\s+"\d+"\)\s*\(name "' + re.escape(net) + r'"\)(.*?)(?=\n\t\t\(net|\n\t\)\n\t\(net|\Z)'
    match = re.search(pattern, text, re.S)
    if not match:
        raise AssertionError(f"missing net {net}")
    return set(re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', match.group(1)))

required = {
    "/PMID": {("U4", "29"), ("C101", "1"), ("C108", "1"), ("C112", "1"), ("C114", "1")},
    "/REGN": {("U4", "5"), ("C102", "1"), ("C109", "1")},
    "/SYS_RAW": {("U4", "25"), ("C104", "1"), ("C105", "1"), ("C107", "1")},
    "/BAT_INT": {("U4", "22"), ("U4", "23"), ("Q103", "1"), ("Q103", "2"), ("Q103", "3"), ("C106", "1")},
    "/BAT_PACK": {("Q103", "5"), ("Q103", "6"), ("Q103", "7"), ("Q103", "8"), ("Q103", "9"), ("SW101", "1"), ("R112", "1")},
    "/SDRV": {("U4", "24"), ("Q103", "4")},
    "/SW1": {("U4", "28"), ("C103", "2"), ("L1", "1")},
    "/SW2": {("U4", "26"), ("C110", "2"), ("L1", "2")},
}
for net, expected in required.items():
    actual = members(net)
    missing = expected - actual
    if missing:
        raise AssertionError(f"{net} missing expected pins: {sorted(missing)}")
    print(f"{net}: {sorted(actual)}")

isolated = ("/PMID", "/REGN", "/SYS_RAW", "/BAT_INT", "/BAT_PACK", "/SW1", "/SW2")
for index, left in enumerate(isolated):
    for right in isolated[index + 1:]:
        overlap = members(left) & members(right)
        if overlap:
            raise AssertionError(f"short between {left} and {right}: {sorted(overlap)}")
print("critical rail and switch-node isolation assertions passed")
