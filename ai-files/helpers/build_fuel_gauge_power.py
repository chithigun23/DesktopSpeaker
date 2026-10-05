#!/usr/bin/env python3
"""Build the MAX17048 gauge child sheet while preserving the original U5 instance.

The gauge bus is isolated in hardware when BAT_PACK is unpowered; the
always-on 3 V logic rail is derived from SYS_RAW for USB-only startup.
"""
from __future__ import annotations

import copy
import pathlib
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai-files/vendor"))
from sexpdata import Symbol, dumps, load  # noqa: E402

S = Symbol
ROOT_SCH = ROOT / "DesktopSpeaker-kicad/DesktopSpeaker.kicad_sch"
PD_SCH = ROOT / "DesktopSpeaker-kicad/USB_PD.kicad_sch"
OUT = ROOT / "DesktopSpeaker-kicad/Fuel_Gauge_Power.kicad_sch"
ROOT_UUID = "feda53ed-537d-4f88-9436-c6075776255b"
SHEET_UUID = "9c37a727-9991-421a-8f6e-77dd39bb53fa"
INSTANCE_PATH = f"/{ROOT_UUID}/{SHEET_UUID}"


def kind(x):
    return str(x[0]) if isinstance(x, list) and x else ""


def allof(x, name):
    return [v for v in x if kind(v) == name]


def one(x, name):
    return allof(x, name)[0]


def uid():
    return str(uuid.uuid4())


def at(x, y, angle=0):
    return [S("at"), round(x, 4), round(y, 4), angle]


def xy(x, y):
    return [S("xy"), round(x, 4), round(y, 4)]


root = load(open(ROOT_SCH))
pd = load(open(PD_SCH))
root_lib = one(root, "lib_symbols")
pd_lib = one(pd, "lib_symbols")
u5_lib = copy.deepcopy(next(v for v in allof(root_lib, "symbol") if v[1] == "MAX17048G+T10:MAX17048G+T10"))
c_lib = copy.deepcopy(next(v for v in allof(pd_lib, "symbol") if v[1] == "PD_C:PD_C"))
r_lib = copy.deepcopy(next(v for v in allof(pd_lib, "symbol") if v[1] == "PD_R:PD_R"))
gnd_lib = copy.deepcopy(next(v for v in allof(pd_lib, "symbol") if v[1] == "power:GND"))
def project_symbol(part):
    path = ROOT / f"DesktopSpeaker-kicad/kicad-library/schematic/{part}.kicad_sym"
    part_lib = load(open(path))
    component = copy.deepcopy(one(part_lib, "symbol"))
    component[1] = f"{part}:{part}"
    return component

ldo_lib = project_symbol("TPS7A0230PDBVR")
mux_lib = project_symbol("TMUX1511PWR")
u5_source = next((v for v in allof(root, "symbol")
                  if one(v, "lib_id")[1] == "MAX17048G+T10:MAX17048G+T10"), None)
if u5_source is None:
    # Root integration moves the original instance into this child. Retain a
    # stable source so rebuilding the sheet remains possible after that move.
    before = load(open(ROOT / "ai-files/backups/DesktopSpeaker-before-compact-2026-10-04.kicad_sch"))
    u5_source = next(v for v in allof(before, "symbol")
                     if one(v, "lib_id")[1] == "MAX17048G+T10:MAX17048G+T10")
u5 = copy.deepcopy(u5_source)

# Existing symbol UUID, pin UUIDs, reference, displayed value, footprint and
# supplier fields are retained; only page-local placement and instance path move.
old_x, old_y = one(u5, "at")[1:3]
new_x, new_y = 177.8, 106.68
one(u5, "at")[1:3] = [new_x, new_y]
for p in allof(u5, "property"):
    pa = one(p, "at")
    if p[1] == "Reference":
        pa[1:4] = [new_x, 120.65, 0]
    elif p[1] == "Value":
        pa[1:4] = [new_x, 123.19, 0]
    else:
        pa[1:4] = [round(pa[1] + new_x - old_x, 4), round(pa[2] + new_y - old_y, 4), 0]
u5_path = one(one(one(u5, "instances"), "project"), "path")
u5_path[1] = INSTANCE_PATH

sch = [
    S("kicad_sch"),
    [S("version"), 20260306],
    [S("generator"), "eeschema"],
    [S("generator_version"), "10.0"],
    [S("uuid"), SHEET_UUID],
    [S("paper"), "A4"],
    [S("title_block"), [S("title"), "Fuel gauge and low-current power"], [S("rev"), "0.1"]],
    [S("lib_symbols"), u5_lib, c_lib, r_lib, gnd_lib, ldo_lib, mux_lib],
    u5,
    [S("embedded_fonts"), S("no")],
]


def add(expr):
    sch.insert(-1, expr)


def wire(a, b):
    if a == b:
        return
    if a[0] != b[0] and a[1] != b[1]:
        raise ValueError(("diagonal", a, b))
    add([S("wire"), [S("pts"), xy(*a), xy(*b)], [S("stroke"), [S("width"), 0], [S("type"), S("default")]], [S("uuid"), uid()]])


def path(*points):
    for a, b in zip(points, points[1:]):
        wire(a, b)


def junction(x, y):
    add([S("junction"), at(x, y)[:3], [S("diameter"), 0], [S("color"), 0, 0, 0, 0], [S("uuid"), uid()]])


def hlabel(name, shape, x, y):
    add([S("hierarchical_label"), name, [S("shape"), S(shape)], at(x, y),
         [S("effects"), [S("font"), [S("size"), 1.0, 1.0]], [S("justify"), S("left"), S("bottom")]], [S("uuid"), uid()]])


def label(name, x, y, side="left"):
    add([S("label"), name, at(x, y), [S("effects"), [S("font"), [S("size"), 1.0, 1.0]],
         [S("justify"), S(side), S("bottom")]], [S("uuid"), uid()]])


def note(message, x, y, size=1.15):
    add([S("text"), message, at(x, y), [S("effects"), [S("font"), [S("size"), size, size]],
         [S("justify"), S("left"), S("bottom")]], [S("uuid"), uid()]])


power_count = 0


def ground(x, y):
    global power_count
    power_count += 1
    ref = f"#PWR1{power_count:02d}"
    add([S("symbol"), [S("lib_id"), "power:GND"], at(x, y), [S("unit"), 1],
         [S("exclude_from_sim"), S("no")], [S("in_bom"), S("no")], [S("on_board"), S("no")],
         [S("dnp"), S("no")], [S("uuid"), uid()],
         [S("property"), "Reference", ref, at(x, y + 3.81), [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]],
         [S("property"), "Value", "GND", at(x, y + 5.08), [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("pin"), "1", [S("uuid"), uid()]],
         [S("instances"), [S("project"), "DesktopSpeaker", [S("path"), INSTANCE_PATH,
          [S("reference"), ref], [S("unit"), 1]]]]])


def capacitor(ref, value, x, y):
    add([S("symbol"), [S("lib_id"), "PD_C:PD_C"], at(x, y), [S("unit"), 1],
         [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
         [S("dnp"), S("no")], [S("uuid"), uid()],
         [S("property"), "Reference", ref, at(x + 4.0, y - 1.27), [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left")]]],
         [S("property"), "Value", value, at(x + 4.0, y + 1.27), [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left")]]],
         [S("property"), "Footprint", "DesktopSpeaker:PD_C_0603", at(x, y), [S("hide"), S("yes")], [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("property"), "Datasheet", "https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17048-MAX17049.pdf", at(x, y), [S("hide"), S("yes")], [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("property"), "MPN", "TBD", at(x, y), [S("hide"), S("yes")], [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("pin"), "1", [S("uuid"), uid()]], [S("pin"), "2", [S("uuid"), uid()]],
         [S("instances"), [S("project"), "DesktopSpeaker", [S("path"), INSTANCE_PATH,
          [S("reference"), ref], [S("unit"), 1]]]]])


def resistor(ref, value, x, y):
    add([S("symbol"), [S("lib_id"), "PD_R:PD_R"], at(x, y), [S("unit"), 1],
         [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
         [S("dnp"), S("no")], [S("uuid"), uid()],
         [S("property"), "Reference", ref, at(x + 4.0, y - 1.27), [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left")]]],
         [S("property"), "Value", value, at(x + 4.0, y + 1.27), [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left")]]],
         [S("property"), "Footprint", "DesktopSpeaker:PD_R_0603", at(x, y), [S("hide"), S("yes")], [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("property"), "MPN", "TBD", at(x, y), [S("hide"), S("yes")], [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("pin"), "1", [S("uuid"), uid()]], [S("pin"), "2", [S("uuid"), uid()]],
         [S("instances"), [S("project"), "DesktopSpeaker", [S("path"), INSTANCE_PATH,
          [S("reference"), ref], [S("unit"), 1]]]]])


def ic(part, ref, x, y, pins, below=14.0):
    add([S("symbol"), [S("lib_id"), f"{part}:{part}"], at(x, y), [S("unit"), 1],
         [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
         [S("dnp"), S("no")], [S("uuid"), uid()],
         [S("property"), "Reference", ref, at(x, y + below), [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("property"), "Value", part, at(x, y + below + 2.54), [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("property"), "Footprint", f"DesktopSpeaker:{part}", at(x, y), [S("hide"), S("yes")], [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("property"), "Datasheet", "https://www.ti.com/lit/ds/symlink/" + ("tps7a02.pdf" if ref == "U12" else "tmux1511.pdf"),
          at(x, y), [S("hide"), S("yes")], [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         [S("property"), "MPN", part, at(x, y), [S("hide"), S("yes")], [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
         *[[S("pin"), str(p), [S("uuid"), uid()]] for p in pins],
         [S("instances"), [S("project"), "DesktopSpeaker", [S("path"), INSTANCE_PATH,
          [S("reference"), ref], [S("unit"), 1]]]]])


# Always-on regulator: local EN is wired directly to the input.
hlabel("SYS_RAW", "input", 35.56, 26.67)
hlabel("3V_AO", "output", 281.94, 26.67)
ic("TPS7A0230PDBVR", "U12", 127, 35.56, (1,2,3,4,5), below=22.86)
capacitor("C122", "1uF X7R 10V", 81.28, 43.18)
capacitor("C123", "1uF X7R 10V", 175.26, 43.18)
path((35.56,26.67),(81.28,26.67),(96.52,26.67),(96.52,33.02),(111.76,33.02))
path((96.52,33.02),(96.52,38.1),(111.76,38.1));junction(96.52,33.02)
path((81.28,26.67),(81.28,39.37));junction(81.28,26.67)
path((81.28,46.99),(81.28,52.07));ground(81.28,52.07)
path((127,50.8),(127,53.34),(105.41,53.34));ground(105.41,53.34)
path((142.24,33.02),(175.26,33.02),(254,33.02),(254,26.67),(281.94,26.67))
path((175.26,33.02),(175.26,39.37));junction(175.26,33.02)
path((175.26,46.99),(175.26,52.07));ground(175.26,52.07)
add([S("no_connect"),at(142.24,38.1)[:3],[S("uuid"),uid()]])

# Protected cell powers the gauge and its powered-off bus switch.
hlabel("BAT_PACK","input",35.56,73.66)
path((35.56,73.66),(120.65,73.66),(146.05,73.66),(177.8,73.66),(234.95,73.66),(240.03,73.66),(245.11,73.66),(250.19,73.66))
path((146.05,73.66),(146.05,109.22),(165.1,109.22));junction(146.05,73.66)
capacitor("C120","100nF X7R 10V",120.65,88.9)
path((120.65,73.66),(120.65,85.09));junction(120.65,73.66)
path((120.65,92.71),(120.65,99.06));ground(120.65,99.06)
path((165.1,104.14),(156.21,104.14),(156.21,99.06),(151.13,99.06));ground(151.13,99.06)
add([S("no_connect"),at(165.1,106.68)[:3],[S("uuid"),uid()]])
path((165.1,111.76),(156.21,111.76),(156.21,119.38));ground(156.21,119.38)
path((190.5,101.6),(200.66,101.6),(200.66,95.25));ground(200.66,95.25)
path((190.5,109.22),(198.12,109.22));ground(198.12,109.22)

ic("TMUX1511PWR","U13",242.57,109.22,tuple(range(1,15)),below=27.94)
for xx in (234.95,240.03,245.11,250.19):
    path((xx,73.66),(xx,86.36));junction(xx,73.66)
capacitor("C121","100nF X7R 10V",177.8,81.28)
path((177.8,73.66),(177.8,77.47));junction(177.8,73.66)
path((177.8,85.09),(177.8,90.17));ground(177.8,90.17)
# All three gauge connections are direct, with no signal label substitutions.
path((190.5,104.14),(227.33,104.14))
path((190.5,106.68),(227.33,106.68))
path((190.5,111.76),(227.33,111.76))
path((242.57,132.08),(220.98,132.08));ground(220.98,132.08)
path((257.81,127),(270.51,127));ground(270.51,127)
for xx in (227.33,257.81):add([S("no_connect"),at(xx,124.46)[:3],[S("uuid"),uid()]])
path((257.81,104.14),(271.78,104.14));label("GAUGE_SDA",271.78,104.14)
path((257.81,106.68),(271.78,106.68));label("GAUGE_SCL",271.78,106.68)
path((257.81,111.76),(281.94,111.76));hlabel("GAUGE_ALRT_N","output",281.94,111.76)

# MCU-side bus ports and central pull-ups. Remote joins avoid crossing the cell path.
hlabel("GAUGE_SCL","input",35.56,146.05)
hlabel("GAUGE_SDA","bidirectional",35.56,151.13)
path((35.56,146.05),(66.04,146.05));label("GAUGE_SCL",66.04,146.05)
path((35.56,151.13),(66.04,151.13));label("GAUGE_SDA",66.04,151.13)
path((50.8,157.48),(76.2,157.48),(101.6,157.48));label("3V_AO",50.8,157.48);junction(76.2,157.48)
for ref,value,xx,net in (("R120","4.7k",50.8,"GAUGE_SCL"),("R121","4.7k",76.2,"GAUGE_SDA"),("R122","47k",101.6,"GAUGE_ALRT_N")):
    resistor(ref,value,xx,165.1);path((xx,157.48),(xx,161.29));path((xx,168.91),(xx,173.99));label(net,xx,173.99)
# Add sourcing fields to the new IC instances.
for obj in allof(sch,"symbol"):
    props={p[1]:p[2] for p in allof(obj,"property")}
    if props.get("Reference") in ("U12","U13"):
        part="C3747031" if props["Reference"]=="U12" else "C2866750"
        obj.append([S("property"),"LCSC",part,at(0,0),[S("effects"),[S("font"),[S("size"),1,1]],[S("hide"),S("yes")]]])
for obj in allof(sch,"hierarchical_label"):
    if one(obj,"shape")[1]==S("output"):
        one(one(obj,"effects"),"justify")[1:]=[S("right"),S("bottom")]
note("CELL pad 2 unused on MAX17048; QSTRT tied low",35.56,186.69)
note("Bus switch: 37uA typ / 70uA max; 3V_AO drops out at low SYS",35.56,191.77,1.0)
OUT.write_text(dumps(sch)+"\n")
print(OUT)
