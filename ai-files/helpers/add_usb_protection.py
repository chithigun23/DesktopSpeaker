#!/usr/bin/env python3
"""Add the selected connector-side CC and 5/9 V VBUS shunt protectors."""
from __future__ import annotations

import copy
import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vendor"))
from sexpdata import Symbol, dumps, load

S = Symbol
ROOT = pathlib.Path(__file__).resolve().parents[2]
PROJECT = ROOT / "DesktopSpeaker-kicad"
SCH = PROJECT / "USB_PD.kicad_sch"
SYMS = PROJECT / "kicad-library/schematic"
FPS = PROJECT / "kicad-library/footprint"
MODELS = PROJECT / "kicad-library/3d"


def kind(x):
    return str(x[0]) if isinstance(x, list) and x else ""


def sub(x, name):
    return next(v for v in x if kind(v) == name)


def uid():
    return str(uuid.uuid4())


def ef(hidden=False, size=1.27, justify=None):
    v = [S("effects"), [S("font"), [S("size"), size, size]]]
    if justify:
        v.append([S("justify"), S(justify)])
    if hidden:
        v.append([S("hide"), S("yes")])
    return v


def prop(name, val, x, y, hidden=False, justify=None):
    return [S("property"), name, val, [S("at"), x, y, 0], ef(hidden, justify=justify)]


def pin(name, number, x, y, angle):
    return [S("pin"), S("passive"), S("line"), [S("at"), x, y, angle],
            [S("length"), 2.54],
            [S("name"), name, ef()], [S("number"), number, ef()]]


def poly(points):
    return [S("polyline"), [S("pts"), *[[S("xy"), x, y] for x, y in points]],
            [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]],
            [S("fill"), [S("type"), S("none")]]]


def make_cc():
    # ST's ESDAxxL functional diagram: pins 1/2 are cathodes; 3 is common anode.
    sym = [S("symbol"), "ESDA25L",
           [S("pin_numbers"), [S("hide"), S("yes")]],
           [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
           prop("Reference", "D", 0, 7.62), prop("Value", "ESDA25L", 0, -10.16),
           prop("Footprint", "DesktopSpeaker:ESDA25L", 0, 0, True),
           prop("Datasheet", "../ai-files/datasheets/ESDAL-ST.pdf", 0, 0, True),
           [S("symbol"), "ESDA25L_0_1",
            [S("rectangle"), [S("start"), -2.54, 5.08], [S("end"), 2.54, -5.08],
             [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]],
             [S("fill"), [S("type"), S("background")]]],
            [S("text"), "TVS", [S("at"), 0, 0, 0], ef(size=1.0)]],
            [S("polyline"), [S("pts"), [S("xy"), -2.54, 2.54], [S("xy"), 0, 2.54],
             [S("xy"), 0, -5.08]], [S("stroke"), [S("width"), 0.1524],
             [S("type"), S("default")]], [S("fill"), [S("type"), S("none")]]],
            [S("polyline"), [S("pts"), [S("xy"), -2.54, -2.54], [S("xy"), 0, -2.54]],
             [S("stroke"), [S("width"), 0.1524], [S("type"), S("default")]],
             [S("fill"), [S("type"), S("none")]]],
           [S("symbol"), "ESDA25L_1_1",
            pin("CC1/K1", "1", -5.08, 2.54, 0),
            pin("CC2/K2", "2", -5.08, -2.54, 0),
            pin("GND/A", "3", 0, -7.62, 90)],
           [S("embedded_fonts"), S("no")]]
    return sym


def make_vbus():
    # Littelfuse SMBJ10A is unidirectional; pin 1 is cathode/stripe.
    sym = [S("symbol"), "SMBJ10A",
           [S("pin_numbers"), [S("hide"), S("yes")]],
           [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
           prop("Reference", "D", 0, 5.08), prop("Value", "SMBJ10A", 0, -5.08),
           prop("Footprint", "DesktopSpeaker:SMBJ10A", 0, 0, True),
           prop("Datasheet", "https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet?assetguid=ba555e99-a12d-4f72-a0b6-86b06c67171e", 0, 0, True),
           [S("symbol"), "SMBJ10A_0_1", poly([(-1.27, 1.27), (1.27, 1.27),
               (0, -1.27), (-1.27, 1.27)]), poly([(-1.651, 1.27), (1.651, 1.27)]),
            poly([(0, 3.81), (0, 1.27)]), poly([(0, -1.27), (0, -3.81)])],
           [S("symbol"), "SMBJ10A_1_1",
            pin("K", "1", 0, 3.81, 270), pin("A", "2", 0, -3.81, 90)],
           [S("embedded_fonts"), S("no")]]
    return sym


def instance(name, ref, x, y, value, lcsc, mfr, datasheet, path):
    pins = ("1", "2", "3") if name == "ESDA25L" else ("1", "2")
    return [S("symbol"), [S("lib_id"), f"{name}:{name}"],
            [S("at"), x, y, 0], [S("unit"), 1],
            [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")],
            [S("on_board"), S("yes")], [S("dnp"), S("no")],
            [S("uuid"), uid()],
            prop("Reference", ref, x + 6.35, y - 1.27, justify="left"),
            prop("Value", value, x + 6.35, y + 1.27, justify="left"),
            prop("Footprint", f"DesktopSpeaker:{name}", x, y, True),
            prop("Datasheet", datasheet, x, y, True),
            prop("Manufacturer", mfr, x, y, True),
            prop("MPN", name, x, y, True),
            prop("LCSC Part", lcsc, x, y, True),
            *[[S("pin"), p, [S("uuid"), uid()]] for p in pins],
            [S("instances"), [S("project"), "DesktopSpeaker",
                [S("path"), path, [S("reference"), ref], [S("unit"), 1]]]]]


def wire(a, b):
    return [S("wire"), [S("pts"), [S("xy"), *a], [S("xy"), *b]],
            [S("stroke"), [S("width"), 0], [S("type"), S("default")]],
            [S("uuid"), uid()]]


def label(name, x, y):
    return [S("label"), name, [S("at"), x, y, 0],
            [S("effects"), [S("font"), [S("size"), 1.0, 1.0]],
             [S("justify"), S("right"), S("bottom")]], [S("uuid"), uid()]]


sch = load(open(SCH))
lib = sub(sch, "lib_symbols")
path = sub(next(v for v in sch if kind(v) == "symbol"), "instances")[1][2][1]
assert not any(ref in ("D5", "D6") for s in sch if kind(s) == "symbol"
               for p in s if kind(p) == "property" for ref in ([p[2]] if p[1] == "Reference" else []))

for name, maker in (("ESDA25L", make_cc), ("SMBJ10A", make_vbus)):
    sym = maker()
    (SYMS / f"{name}.kicad_sym").write_text(dumps([S("kicad_symbol_lib"),
        [S("version"), 20231120], [S("generator"), S("kicad_symbol_editor")], sym]) + "\n")
    embedded = copy.deepcopy(sym)
    embedded[1] = f"{name}:{name}"
    lib.append(embedded)

sch.append(instance("ESDA25L", "D5", 96.52, 53.34, "ESDA25L", "C95343",
                    "STMicroelectronics", "../ai-files/datasheets/ESDAL-ST.pdf", path))
sch.extend([wire((87.63, 50.8), (91.44, 50.8)), label("USB_CC1", 87.63, 50.8),
            wire((87.63, 55.88), (91.44, 55.88)), label("USB_CC2", 87.63, 55.88),
            wire((96.52, 60.96), (96.52, 66.04))])
gnd = copy.deepcopy(next(v for v in sch if kind(v) == "symbol" and sub(v,"lib_id")[1] == "power:GND"))
sub(gnd, "at")[1:3] = [96.52, 66.04]
sub(gnd, "uuid")[1] = uid()
sub(gnd, "property")[2] = "#PWR15"
for p in gnd:
    if kind(p) == "property":
        sub(p, "at")[1] = 96.52
        sub(p, "at")[2] += 66.04 - 63.5
    if kind(p) == "pin": sub(p, "uuid")[1] = uid()
sub(gnd, "instances")[1][2][2][1] = "#PWR15"
sch.append(gnd)

# Branch VBUS between connector input and the first sense branch.
old = next(v for v in sch if kind(v) == "wire" and
           sub(v, "pts")[1][1:] == [35.56, 39.37] and
           sub(v, "pts")[2][1:] == [78.74, 39.37])
sch.remove(old)
sch.extend([wire((35.56,39.37),(68.58,39.37)), wire((68.58,39.37),(78.74,39.37)),
            wire((68.58,39.37),(68.58,64.77)),
            [S("junction"), [S("at"),68.58,39.37], [S("diameter"),0],
             [S("color"),0,0,0,0], [S("uuid"),uid()]]])
sch.append(instance("SMBJ10A", "D6", 68.58, 68.58, "SMBJ10A", "C151250",
                    "Littelfuse", "https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet?assetguid=ba555e99-a12d-4f72-a0b6-86b06c67171e", path))
sch.append(wire((68.58,72.39),(68.58,77.47)))
gnd2 = copy.deepcopy(gnd)
sub(gnd2,"at")[1:3] = [68.58,77.47]
sub(gnd2,"uuid")[1] = uid()
for p in gnd2:
    if kind(p) == "property":
        if p[1] == "Reference": p[2] = "#PWR16"
        sub(p,"at")[1] = 68.58
        sub(p,"at")[2] += 77.47 - 66.04
    if kind(p) == "pin": sub(p,"uuid")[1] = uid()
sub(gnd2,"instances")[1][2][2][1] = "#PWR16"
sch.append(gnd2)

SCH.write_text(dumps(sch) + "\n")

# Reuse KiCad's matching standard package outlines and checked generic STEP sizes.
fp = (FPS / "2N7002.kicad_mod").read_text().replace('(footprint "2N7002"',
    '(footprint "ESDA25L"').replace('"2N7002"', '"ESDA25L"').replace(
    '/3d/2N7002.step', '/3d/ESDA25L.step')
(FPS / "ESDA25L.kicad_mod").write_text(fp)
src3d = pathlib.Path('/home/chithi/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Packages3D/x86_64/beta/dea563e605c33133d67186ee2c0e13f523783d384aec223a80053bc95fe99ba4/files/3dmodels')
import shutil
shutil.copyfile(src3d/'Package_TO_SOT_SMD.3dshapes/SOT-23.step', MODELS/'ESDA25L.step')
srcfp = pathlib.Path('/home/chithi/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Footprints/x86_64/beta/active/files/footprints/Diode_SMD.pretty/D_SMB.kicad_mod')
smb = srcfp.read_text().replace('(footprint "D_SMB"', '(footprint "SMBJ10A"').replace(
    '"D_SMB"', '"SMBJ10A"').replace('${KICAD10_3DMODEL_DIR}/Diode_SMD.3dshapes/D_SMB.step',
    '${KIPRJMOD}/kicad-library/3d/SMBJ10A.step')
(FPS/'SMBJ10A.kicad_mod').write_text(smb)
shutil.copyfile(src3d/'Diode_SMD.3dshapes/D_SMB.step', MODELS/'SMBJ10A.step')
