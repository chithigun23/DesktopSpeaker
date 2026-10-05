#!/usr/bin/env python3
"""One-shot direct gauge-to-switch wiring cleanup."""
import pathlib
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai-files/vendor"))
from sexpdata import Symbol, dumps, load  # noqa: E402

S = Symbol
p = ROOT / "DesktopSpeaker-kicad/Fuel_Gauge_Power.kicad_sch"
sch = load(open(p))


def k(z):
    return str(z[0]) if isinstance(z, list) and z else ""


def at(z):
    return next(v for v in z if k(v) == "at")


def ends(z):
    q = next(v for v in z if k(v) == "pts")
    return tuple(q[1][1:]), tuple(q[2][1:])


old_gauge = {
    ((190.5, 104.14), (196.85, 104.14)),
    ((196.85, 104.14), (196.85, 93.98)),
    ((196.85, 93.98), (208.28, 93.98)),
    ((190.5, 106.68), (208.28, 106.68)),
    ((190.5, 111.76), (196.85, 111.76)),
    ((196.85, 111.76), (196.85, 121.92)),
    ((196.85, 121.92), (208.28, 121.92)),
}
old_stubs = {
    ((229.87, 78.74), (218.44, 78.74)),
    ((229.87, 111.76), (218.44, 111.76)),
    ((229.87, 144.78), (218.44, 144.78)),
}

# Remove only the six pairwise local labels and their seven gauge-side plus
# three switch-side stubs.  Keep BAT and AO labels elsewhere in the sheet.
for z in sch[:]:
    if k(z) == "label" and str(z[1]).startswith("U5_"):
        sch.remove(z)
    elif k(z) == "wire" and (ends(z) in old_gauge or ends(z) in old_stubs):
        sch.remove(z)


def move_at(z, dy):
    a = at(z)
    a[2] = round(a[2] + dy, 4)


# Raise U13 and U16 enough for signal lanes and clear their identifier text.
for z in sch:
    if k(z) == "symbol":
        ref = next((v[2] for v in z if k(v) == "property" and v[1] == "Reference"), "")
        dy = (-7.62 if ref in {"U13", "#PWR110"}
              else -5.08 if ref in {"U16", "#PWR113"} else 0)
        if dy:
            move_at(z, dy)
            for prop in z:
                if k(prop) == "property":
                    move_at(prop, dy)
    elif k(z) == "wire":
        a, b = ends(z)
        if a[0] >= 215.9 and b[0] >= 215.9:
            if a[1] in {68.58, 63.5, 78.74, 81.28, 88.9} and b[1] in {68.58, 63.5, 78.74, 81.28, 88.9}:
                pts = next(v for v in z if k(v) == "pts")
                for v in pts[1:]:
                    v[2] = round(v[2] - 7.62, 4)
            elif a[1] in {101.6, 96.52, 111.76, 114.3, 121.92} and b[1] in {101.6, 96.52, 111.76, 114.3, 121.92}:
                pts = next(v for v in z if k(v) == "pts")
                for v in pts[1:]:
                    v[2] = round(v[2] - 5.08, 4)
    elif k(z) == "junction" and at(z)[1] == 215.9:
        if at(z)[2] == 88.9:
            move_at(z, -7.62)
        elif at(z)[2] == 121.92:
            move_at(z, -5.08)
    elif k(z) == "label":
        a = at(z)
        if a[1] == 242.57 and z[1] == "BAT_PACK":
            if a[2] == 63.5:
                move_at(z, -7.62)
            elif a[2] == 96.52:
                move_at(z, -5.08)
        elif z[1] == "GAUGE_SDA" and a[1] == 271.78 and a[2] == 78.74:
            move_at(z, -7.62)
        elif z[1] == "GAUGE_SCL" and a[1] == 271.78 and a[2] == 111.76:
            move_at(z, -5.08)


def wire(a, b):
    assert a[0] == b[0] or a[1] == b[1]
    sch.insert(-1, [S("wire"), [S("pts"), [S("xy"), *a], [S("xy"), *b]],
                    [S("stroke"), [S("width"), 0], [S("type"), S("default")]],
                    [S("uuid"), str(uuid.uuid4())]])


for a, b in [
    ((190.5, 104.14), (205.74, 104.14)),
    ((205.74, 104.14), (205.74, 71.12)),
    ((205.74, 71.12), (229.87, 71.12)),
    ((190.5, 106.68), (229.87, 106.68)),
    ((190.5, 111.76), (210.82, 111.76)),
    ((210.82, 111.76), (210.82, 144.78)),
    ((210.82, 144.78), (229.87, 144.78)),
]:
    wire(a, b)

p.write_text(dumps(sch))
print(p)
