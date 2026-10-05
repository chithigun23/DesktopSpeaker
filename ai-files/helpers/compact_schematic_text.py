#!/usr/bin/env python3
"""Tighten USB PD placement and standardize visible symbol fields."""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vendor"))
from sexpdata import Symbol, dumps, load


ROOT = pathlib.Path(__file__).resolve().parents[2] / "DesktopSpeaker-kicad"
S = Symbol


def kind(item):
    return str(item[0]) if isinstance(item, list) and item else ""


def children(item, name):
    return [child for child in item if kind(child) == name]


def one(item, name):
    return children(item, name)[0]


def set_field(symbol, name, x, y):
    field = next(p for p in children(symbol, "property") if p[1] == name)
    one(field, "at")[1:] = [round(x, 4), round(y, 4), 0]
    effects = one(field, "effects")
    for justify in children(effects, "justify"):
        effects.remove(justify)
    effects.append([S("justify"), S("left")])


def save(expr, path):
    path.write_text("(" + " ".join(dumps(v) for v in expr[:1]) + "\n" + "\n".join(dumps(v) for v in expr[1:]) + ")\n")


root_path = ROOT / "DesktopSpeaker.kicad_sch"
root_source = root_path.read_text()
root = load(open(root_path))
body_half_heights = {
    "U1": 33.02, "U2": 19.05, "U3": 21.59, "U4": 19.05,
    "U5": 7.62, "U6": 22.86, "U7": 22.86,
    "U8": 7.62, "U9": 7.62, "U10": 12.7,
}
for symbol in children(root, "symbol"):
    ref = one(symbol, "property")[2]
    x, y = one(symbol, "at")[1:3]
    if ref in body_half_heights:
        first_y = y + body_half_heights[ref] + 3.81
        set_field(symbol, "Reference", x, first_y)
        set_field(symbol, "Value", x, first_y + 2.54)
        for field in children(symbol, "property"):
            if field[1] in ("Reference", "Value"):
                effects = one(field, "effects")
                for justify in children(effects, "justify"):
                    effects.remove(justify)
    elif ref == "D1":
        set_field(symbol, "Reference", x + 9.525, y - 1.27)
        set_field(symbol, "Value", x + 9.525, y + 1.27)
for symbol in children(root, "symbol"):
    ref = one(symbol, "property")[2]
    if ref not in body_half_heights and ref != "D1":
        continue
    start = root_source.index(f'(property "Reference" "{ref}"')
    end = root_source.index('(property "Footprint"', start)
    block = root_source[start:end]
    for name in ("Reference", "Value"):
        field = next(p for p in children(symbol, "property") if p[1] == name)
        x, y = one(field, "at")[1:3]
        match = re.search(r'(\(property "' + name + r'" "[^"]+"[\s\S]*?\(at )[^)]*\)', block)
        assert match, (ref, name)
        block = block[:match.start()] + match.group(1) + f'{x:g} {y:g} 0)' + block[match.end():]
    if ref == "D1":
        block = block.replace('(effects (font (size 1.27 1.27)))', '(effects (font (size 1.27 1.27)) (justify left))', 2)
    root_source = root_source[:start] + block + root_source[end:]
root_path.write_text(root_source)


pd_path = ROOT / "USB_PD.kicad_sch"
pd = load(open(pd_path))
drop = 20.32


def shift_y(y, x=None):
    # R11's short output stub sits just below the compression boundary.
    # Its connector and label stay below the resistor body.
    if x == 270.51 and y == 153.67:
        return y
    return round(y - drop, 4) if y >= 150 else y


for item in pd:
    name = kind(item)
    if name == "symbol":
        ref = one(item, "property")[2]
        x_delta = {"J4": -17.78, "#PWR14": -17.78, "#PWR04": -10.16}.get(ref, 0)
        for at in children(item, "at"):
            at[1] = round(at[1] + x_delta, 4)
            at[2] = shift_y(at[2], at[1])
        for prop in children(item, "property"):
            at = one(prop, "at")
            at[1] = round(at[1] + x_delta, 4)
            at[2] = shift_y(at[2], at[1])
    elif name in ("label", "text", "junction", "no_connect"):
        at = one(item, "at")
        at[2] = shift_y(at[2], at[1])
        if name == "text" and "Program and read back" in str(item[1]):
            at[2] = 232.41
    elif name == "wire":
        for point in children(one(item, "pts"), "xy"):
            if point[1] == 345.44 and point[2] >= 200:
                point[1] = 327.66
            elif point[1] == 336.55 and point[2] >= 200:
                point[1] = 318.77
            elif point[1] == 125.73 and point[2] == 200.66:
                point[1] = 115.57
            point[2] = shift_y(point[2], point[1])

for symbol in children(pd, "symbol"):
    ref = one(symbol, "property")[2]
    x, y = one(symbol, "at")[1:3]
    if ref == "U11":
        first_y = y + 17.78 + 3.81
        set_field(symbol, "Reference", x, first_y)
        set_field(symbol, "Value", x, first_y + 2.54)
        for field in children(symbol, "property"):
            if field[1] in ("Reference", "Value"):
                effects = one(field, "effects")
                for justify in children(effects, "justify"):
                    effects.remove(justify)
    elif ref.startswith("Q"):
        offset = 15.24 if ref == "Q2" else 7.62
        set_field(symbol, "Reference", x + offset, y - 1.27)
        set_field(symbol, "Value", x + offset, y + 1.27)
        if ref == "Q2":
            value = next(p for p in children(symbol, "property") if p[1] == "Value")
            one(one(value, "effects"), "justify")[1] = S("right")
    elif ref == "C10":
        set_field(symbol, "Reference", 354.33, y - 10.16)
        set_field(symbol, "Value", 354.33, y - 7.62)
    elif ref.startswith(("R", "C")):
        set_field(symbol, "Reference", x + 3.81, y - 1.27)
        set_field(symbol, "Value", x + 3.81, y + 1.27)
    elif ref == "D4":
        set_field(symbol, "Reference", x + 6.35, y - 1.27)
        set_field(symbol, "Value", x + 6.35, y + 1.27)

save(pd, pd_path)
