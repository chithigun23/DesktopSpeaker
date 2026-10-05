#!/usr/bin/env python3
"""One-shot TS5A3167 gauge-isolation redraw; preserve all other sheet objects."""
from __future__ import annotations

import copy
import pathlib
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai-files/vendor"))
from sexpdata import Symbol, dumps, load  # noqa: E402

S = Symbol
SHEET = ROOT / "DesktopSpeaker-kicad/Fuel_Gauge_Power.kicad_sch"
LIB = ROOT / "DesktopSpeaker-kicad/kicad-library/schematic/TS5A3167DBVR.kicad_sym"
PATH = "/feda53ed-537d-4f88-9436-c6075776255b/9c37a727-9991-421a-8f6e-77dd39bb53fa"


def kind(x):
    return str(x[0]) if isinstance(x, list) and x else ""


def one(x, name):
    return next(z for z in x if kind(z) == name)


def uid():
    return str(uuid.uuid4())


def at(x, y, angle=0):
    return [S("at"), round(x, 4), round(y, 4), angle]


def xy(x, y):
    return [S("xy"), round(x, 4), round(y, 4)]


sch = load(open(SHEET))
old_u13 = next(z for z in sch if kind(z) == "symbol" and one(z, "property")[2] == "U13")
old_u13_uuid = one(old_u13, "uuid")[1]


def pt(z):
    return tuple(z[1:3])


def old_mux_wire(z):
    if kind(z) != "wire":
        return False
    pts = one(z, "pts")
    a, b = pt(pts[1]), pt(pts[2])
    old_pin_x = {227.33, 242.57, 257.81, 234.95, 240.03, 245.11, 250.19}
    if a == (177.8, 73.66) and b == (234.95, 73.66):
        return True
    if b == (177.8, 73.66) and a == (234.95, 73.66):
        return True
    if a[0] in old_pin_x or b[0] in old_pin_x:
        return True
    if a == (220.98, 132.08) or b == (220.98, 132.08):
        return True
    if a == (270.51, 127) or b == (270.51, 127):
        return True
    if a == (190.5, 104.14) and b == (227.33, 104.14):
        return True
    if a == (190.5, 106.68) and b == (227.33, 106.68):
        return True
    if a == (190.5, 111.76) and b == (227.33, 111.76):
        return True
    return False


removed = []
for z in sch[:]:
    k = kind(z)
    ref = one(z, "property")[2] if k == "symbol" else None
    remove = (
        (k == "symbol" and ref in {"U13", "#PWR110", "#PWR111"})
        or old_mux_wire(z)
        or (k == "junction" and pt(one(z, "at")) in {(234.95, 73.66), (240.03, 73.66), (245.11, 73.66), (250.19, 73.66)})
        or (k == "label" and pt(one(z, "at")) in {(271.78, 104.14), (271.78, 106.68)})
        or (k == "hierarchical_label" and z[1] == "GAUGE_ALRT_N")
        or (k == "no_connect" and pt(one(z, "at")) in {(227.33, 124.46), (257.81, 124.46)})
        or (k == "text" and "Bus switch:" in z[1])
    )
    if remove:
        sch.remove(z)
        removed.append(z)

# Replace cached symbol and retain the existing U13 UUID/reference.
lib_symbols = one(sch, "lib_symbols")
for z in lib_symbols[:]:
    if kind(z) == "symbol" and z[1] == "TMUX1511PWR:TMUX1511PWR":
        lib_symbols.remove(z)
new_lib = copy.deepcopy(one(load(open(LIB)), "symbol"))
new_lib[1] = "TS5A3167DBVR:TS5A3167DBVR"
lib_symbols.append(new_lib)


def add(z):
    sch.insert(-1, z)


def wire(a, b):
    if a == b:
        return
    if a[0] != b[0] and a[1] != b[1]:
        raise ValueError((a, b))
    add([S("wire"), [S("pts"), xy(*a), xy(*b)],
         [S("stroke"), [S("width"), 0], [S("type"), S("default")]], [S("uuid"), uid()]])


def path(*points):
    for a, b in zip(points, points[1:]):
        wire(a, b)


def label(name, x, y, justify="left"):
    add([S("label"), name, at(x, y), [S("effects"), [S("font"), [S("size"), 1, 1]],
         [S("justify"), S(justify), S("bottom")]], [S("uuid"), uid()]])


def ground(ref, x, y):
    add([S("symbol"), [S("lib_id"), "power:GND"], at(x, y), [S("unit"), 1],
         [S("exclude_from_sim"), S("no")], [S("in_bom"), S("no")], [S("on_board"), S("no")],
         [S("dnp"), S("no")], [S("uuid"), uid()],
         [S("property"), "Reference", ref, at(x, y + 3.81),
          [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]],
         [S("property"), "Value", "GND", at(x, y + 5.08),
          [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("pin"), "1", [S("uuid"), uid()]],
         [S("instances"), [S("project"), "DesktopSpeaker",
          [S("path"), PATH, [S("reference"), ref], [S("unit"), 1]]]]])


def switch(ref, y, u_uuid=None):
    x = 242.57
    add([S("symbol"), [S("lib_id"), "TS5A3167DBVR:TS5A3167DBVR"], at(x, y),
         [S("unit"), 1], [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")],
         [S("on_board"), S("yes")], [S("dnp"), S("no")], [S("uuid"), u_uuid or uid()],
         [S("property"), "Reference", ref, at(x, y + 12.7),
          [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("property"), "Value", "TS5A3167DBVR", at(x, y + 15.24),
          [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("property"), "Footprint", "DesktopSpeaker:TS5A3167DBVR", at(x, y),
          [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]],
         [S("property"), "Datasheet", "https://www.ti.com/lit/ds/symlink/ts5a3167.pdf", at(x, y),
          [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]],
         [S("property"), "MPN", "TS5A3167DBVR", at(x, y),
          [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]],
         [S("property"), "LCSC", "C128416", at(x, y),
          [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]],
         *[[S("pin"), str(n), [S("uuid"), uid()]] for n in range(1, 6)],
         [S("instances"), [S("project"), "DesktopSpeaker",
          [S("path"), PATH, [S("reference"), ref], [S("unit"), 1]]]]])
    # IN4 low gives a normally-closed BAT-powered channel; GND3 joins locally.
    path((229.87, y + 2.54), (215.9, y + 2.54), (215.9, y + 10.16), (242.57, y + 10.16))
    ground({"U13": "#PWR110", "U16": "#PWR113", "U17": "#PWR116"}[ref], 215.9, y + 10.16)
    add([S("junction"), at(215.9, y + 10.16)[:3], [S("diameter"), 0],
         [S("color"), 0, 0, 0, 0], [S("uuid"), uid()]])
    wire((242.57, y - 10.16), (242.57, y - 15.24))
    label("BAT_PACK", 242.57, y - 15.24)


def decap(ref, y, ground_ref):
    x = 185.42 if ref == "C132" else 265.43
    add([S("symbol"), [S("lib_id"), "PD_C:PD_C"], at(x, y),
         [S("unit"), 1], [S("exclude_from_sim"), S("no")],
         [S("in_bom"), S("yes")], [S("on_board"), S("yes")], [S("dnp"), S("no")],
         [S("uuid"), uid()],
         [S("property"), "Reference", ref, at(x + 4, y - 1.27),
          [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left")]]],
         [S("property"), "Value", "100nF", at(x + 4, y + 1.27),
          [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left")]]],
         [S("property"), "Footprint", "DesktopSpeaker:PD_C_0603", at(x, y),
          [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]],
         [S("property"), "MPN", "TBD", at(x, y),
          [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]],
         [S("pin"), "1", [S("uuid"), uid()]], [S("pin"), "2", [S("uuid"), uid()]],
         [S("instances"), [S("project"), "DesktopSpeaker",
          [S("path"), PATH, [S("reference"), ref], [S("unit"), 1]]]]])
    wire((x, y - 3.81), (x, y - 7.62))
    label("BAT_PACK", x, y - 7.62)
    wire((x, y + 3.81), (x, y + 7.62))
    ground(ground_ref, x, y + 7.62)


# Keep U5's pin and physical ground connections; fan out three remote signal
# labels to avoid nonconnecting intersections in the narrow 2.54-mm pin pitch.
path((190.5, 104.14), (196.85, 104.14), (196.85, 93.98), (208.28, 93.98))
label("U5_SDA", 208.28, 93.98, "right")
wire((190.5, 106.68), (208.28, 106.68))
label("U5_SCL", 208.28, 106.68, "right")
path((190.5, 111.76), (196.85, 111.76), (196.85, 121.92), (208.28, 121.92))
label("U5_ALRT_N", 208.28, 121.92, "right")

for ref, y, in_net, out_net, cap_ref, pwr_ref in [
    ("U13", 78.74, "U5_SDA", "GAUGE_SDA", "C130", "#PWR112"),
    ("U16", 111.76, "U5_SCL", "GAUGE_SCL", "C131", "#PWR115"),
    ("U17", 144.78, "U5_ALRT_N", "GAUGE_ALRT_N", "C132", "#PWR118"),
]:
    switch(ref, y, old_u13_uuid if ref == "U13" else None)
    wire((229.87, y), (218.44, y))
    label(in_net, 218.44, y, "right")
    wire((255.27, y), (281.94 if ref == "U17" else 271.78, y))
    if ref == "U17":
        add([S("hierarchical_label"), out_net, [S("shape"), S("output")], at(281.94, y),
             [S("effects"), [S("font"), [S("size"), 1, 1]],
              [S("justify"), S("right"), S("bottom")]], [S("uuid"), uid()]])
    else:
        label(out_net, 271.78, y)
    decap(cap_ref, 149.86 if ref == "U17" else y + 12.7, pwr_ref)

add([S("text"), "Gauge isolation: 3 active-low BAT-powered switches; OFF when BAT absent",
     at(35.56, 191.77), [S("effects"), [S("font"), [S("size"), 1, 1]],
                              [S("justify"), S("left"), S("bottom")]], [S("uuid"), uid()]])

SHEET.write_text(dumps(sch))
print(f"Removed {len(removed)} old objects; wrote {SHEET}")
