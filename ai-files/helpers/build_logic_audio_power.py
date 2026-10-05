#!/usr/bin/env python3
"""Create the isolated SYS_RAW to 5V_LOGIC TPS61023 child sheet."""
from __future__ import annotations

import copy
import pathlib
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai-files/vendor"))
from sexpdata import Symbol, dumps, load  # noqa: E402

S = Symbol
PROJ = ROOT / "DesktopSpeaker-kicad"
LIB = PROJ / "kicad-library"
SHEET_UUID = "31d56ed5-71f9-4c5a-b590-b5d5119f00f9"
ROOT_UUID = "feda53ed-537d-4f88-9436-c6075776255b"
INSTANCE = f"/{ROOT_UUID}/{SHEET_UUID}"


def uid(): return str(uuid.uuid4())
def at(x, y, a=0): return [S("at"), x, y, a]
def xy(x, y): return [S("xy"), x, y]
def effects(just=None, hide=False, size=1.27):
    e = [S("effects"), [S("font"), [S("size"), size, size]]]
    if just: e.append([S("justify"), S(just)])
    if hide: e.append([S("hide"), S("yes")])
    return e
def prop(n,v,x=0,y=0,hide=False,just=None): return [S("property"),n,v,at(x,y),effects(just,hide)]
def kind(x): return str(x[0]) if isinstance(x,list) and x else ""
def one(x,k): return next(v for v in x if kind(v)==k)


# Source: TI TPS61023 Rev B, pin functions and 6-pin DRL top view.
pin_positions = {
    1: (12.7,-5.08,180,"FB","input"),
    2: (-12.7,-5.08,0,"EN","input"),
    3: (-12.7,5.08,0,"VIN","power_in"),
    4: (0,-10.16,90,"GND","power_in"),
    5: (0,10.16,270,"SW","output"),
    6: (12.7,5.08,180,"VOUT","power_out"),
}
def pin(num,x,y,a,name,etype):
    return [S("pin"),S(etype),S("line"),at(x,y,a),[S("length"),2.54],
            [S("name"),name,effects()], [S("number"),str(num),effects()]]
ic_symbol = [S("symbol"),"TPS61023DRLT",
    prop("Reference","U",0,-15.24),prop("Value","TPS61023DRLT",0,-17.78),
    prop("Footprint","DesktopSpeaker:TPS61023DRLT",hide=True),
    prop("Datasheet","../ai-files/datasheets/TPS61023.pdf",hide=True),
    prop("Description","Synchronous 5 V boost with true shutdown disconnect",hide=True),
    prop("Manufacturer","Texas Instruments",hide=True),
    prop("MPN","TPS61023DRLT",hide=True),prop("LCSC Part","C1852149",hide=True),
    [S("symbol"),"TPS61023DRLT_0_1",
     [S("rectangle"),[S("start"),-10.16,7.62],[S("end"),10.16,-7.62],
      [S("stroke"),[S("width"),0],[S("type"),S("default")]],
      [S("fill"),[S("type"),S("background")]]]],
    [S("symbol"),"TPS61023DRLT_1_1",*[pin(n,*v) for n,v in pin_positions.items()]]]
sym_path = LIB / "schematic/TPS61023DRLT.kicad_sym"
sym_path.write_text(dumps([S("kicad_symbol_lib"),[S("version"),20250217],
    [S("generator"),"kicad_symbol_editor"],ic_symbol])+"\n")

charger = load(open(PROJ/"Battery_Charger.kicad_sch"))
gauge = load(open(PROJ/"Fuel_Gauge_Power.kicad_sch"))
charger_lib = one(charger,"lib_symbols")
gauge_lib = one(gauge,"lib_symbols")
def copied(lib, ident):
    return copy.deepcopy(next(v for v in lib if kind(v)=="symbol" and v[1]==ident))
embedded_ic = copy.deepcopy(ic_symbol); embedded_ic[1]="TPS61023DRLT:TPS61023DRLT"
sch = [S("kicad_sch"),[S("version"),20260306],[S("generator"),"eeschema"],
       [S("generator_version"),"10.0"],[S("uuid"),SHEET_UUID],[S("paper"),"A4"],
       [S("title_block"),[S("title"),"Regulated 5 V logic and audio supply"],[S("rev"),"0.1"]],
       [S("lib_symbols"),embedded_ic,copied(charger_lib,"PD_R:PD_R"),
        copied(charger_lib,"PD_C:PD_C"),copied(charger_lib,"Device:L"),
        copied(gauge_lib,"power:GND")],
       [S("embedded_fonts"),S("no")]]
def add(v): sch.insert(-1,v)
def wire(a,b):
    if a==b:return
    assert a[0]==b[0] or a[1]==b[1],(a,b)
    add([S("wire"),[S("pts"),xy(*a),xy(*b)],
         [S("stroke"),[S("width"),0],[S("type"),S("default")]],
         [S("uuid"),uid()]])
def path(*points):
    for a,b in zip(points,points[1:]):wire(a,b)
def junction(x,y):add([S("junction"),[S("at"),x,y],[S("diameter"),0],
                        [S("color"),0,0,0,0],[S("uuid"),uid()]])
def hlabel(name,shape,x,y):
    add([S("hierarchical_label"),name,[S("shape"),S(shape)],at(x,y),
         effects("left",size=1.0),[S("uuid"),uid()]])
def text(msg,x,y):
    add([S("text"),msg,at(x,y),effects("left",size=1.0),[S("uuid"),uid()]])
def instance(lib_id,ref,value,x,y,pins,footprint=None,mpn=None,lcsc=None,refxy=None,valxy=None,extra=None):
    parts=[S("symbol"),[S("lib_id"),lib_id],at(x,y),[S("unit"),1],
           [S("exclude_from_sim"),S("no")],[S("in_bom"),S("yes")],
           [S("on_board"),S("yes")],[S("dnp"),S("no")],[S("uuid"),uid()],
           prop("Reference",ref,*(refxy or (x+4,y-1.27)),just="left" if refxy is None else None),
           prop("Value",value,*(valxy or (x+4,y+1.27)),just="left" if valxy is None else None)]
    if footprint:parts.append(prop("Footprint",footprint,x,y,hide=True))
    if mpn:parts.append(prop("MPN",mpn,x,y,hide=True))
    if lcsc:parts.append(prop("LCSC Part",lcsc,x,y,hide=True))
    if extra:
        for n,v in extra.items():parts.append(prop(n,v,x,y,hide=True))
    parts.extend([[S("pin"),str(p),[S("uuid"),uid()]] for p in pins])
    parts.append([S("instances"),[S("project"),"DesktopSpeaker",
                  [S("path"),INSTANCE,[S("reference"),ref],[S("unit"),1]]]])
    add(parts)
def ground(x,y):
    ref=f"#PWR{140+len([a for a in sch if kind(a)=='symbol' and one(a,'lib_id')[1]=='power:GND']):03d}"
    add([S("symbol"),[S("lib_id"),"power:GND"],at(x,y),[S("unit"),1],
         [S("exclude_from_sim"),S("no")],[S("in_bom"),S("no")],
         [S("on_board"),S("no")],[S("dnp"),S("no")],[S("uuid"),uid()],
         prop("Reference",ref,x,y+3.81,hide=True),prop("Value","GND",x,y+5.08),
         [S("pin"),"1",[S("uuid"),uid()]],
         [S("instances"),[S("project"),"DesktopSpeaker",
          [S("path"),INSTANCE,[S("reference"),ref],[S("unit"),1]]]]])
def cap(ref,x,y,value="22uF 10V X7R",mpn="GRM21BZ71A226ME15L",lcsc="C907991",size="0805"):
    instance("PD_C:PD_C",ref,value,x,y,(1,2),f"DesktopSpeaker:PD_C_{size}",mpn,lcsc)
def res(ref,x,y,value,mpn="TBD 1%",lcsc="TBD"):
    instance("PD_R:PD_R",ref,value,x,y,(1,2),"DesktopSpeaker:PD_R_0603",mpn,lcsc)

# The 50-mil grid is used throughout. Ports remain left-input / right-output.
hlabel("SYS_RAW","input",25.4,43.18)
hlabel("5V_LOGIC_EN","input",25.4,114.3)
hlabel("5V_LOGIC","output",254,63.5)
instance("TPS61023DRLT:TPS61023DRLT","U14","TPS61023DRLT",139.7,93.98,
         (1,2,3,4,5,6),"DesktopSpeaker:TPS61023DRLT","TPS61023DRLT","C1852149",
         (139.7,111.76),(139.7,114.3),{"Datasheet":"../ai-files/datasheets/TPS61023.pdf"})
instance("Device:L","L2","1uH",139.7,69.85,(1,2),
         "DesktopSpeaker:Bourns_SRP4020TA-1R0M","SRP4020TA-1R0M","C913245",
         (144.78,68.58),(144.78,71.12),{"Datasheet":"../ai-files/datasheets/Bourns_SRP4020TA.pdf"})
cap("C140",76.2,58.42)
cap("C141",208.28,81.28)
cap("C142",231.14,81.28)
cap("C143",118.11,58.42,"100nF 10V X7R","TBD","TBD","0603")
res("R140",187.96,93.98,"732k 1%")
res("R141",187.96,118.11,"100k 1%")
res("R142",69.85,126.365,"100k")

# Input and local decoupling. SYS_RAW has charger-side bulk elsewhere.
path((25.4,43.18),(76.2,43.18),(101.6,43.18),(118.11,43.18),(139.7,43.18),(139.7,66.04))
path((76.2,43.18),(76.2,54.61));junction(76.2,43.18)
path((76.2,62.23),(76.2,67.31));ground(76.2,67.31)
path((118.11,43.18),(118.11,54.61));junction(118.11,43.18)
path((118.11,62.23),(118.11,67.31));ground(118.11,67.31)
path((101.6,43.18),(101.6,88.9),(127,88.9));junction(101.6,43.18)
path((139.7,73.66),(139.7,83.82))

# 3 V AO control: hardware defaults disabled until firmware asserts EN.
path((25.4,114.3),(69.85,114.3),(88.9,114.3),(88.9,99.06),(127,99.06))
path((69.85,114.3),(69.85,122.555));junction(69.85,114.3)
path((69.85,130.175),(69.85,135.255));ground(69.85,135.255)
path((139.7,104.14),(139.7,106.68));ground(139.7,106.68)

# Output reservoir and precision feedback divider.
path((152.4,88.9),(168.91,88.9),(168.91,63.5),(187.96,63.5),
     (208.28,63.5),(231.14,63.5),(254,63.5))
path((187.96,63.5),(187.96,90.17));junction(187.96,63.5)
path((187.96,97.79),(187.96,104.14),(187.96,114.3))
path((152.4,99.06),(165.1,99.06),(165.1,104.14),(187.96,104.14));junction(187.96,104.14)
path((187.96,121.92),(187.96,127));ground(187.96,127)
for x in (208.28,231.14):
    path((x,63.5),(x,77.47));junction(x,63.5)
    path((x,85.09),(x,90.17));ground(x,90.17)
text("Protected 1S SYS to switched 5 V; reserve 500 mA total. Codec and other 5 V loads connect later.",36.83,25.4)
text("EN low = true input/output disconnect. Sequence downstream loads after rail settles.",36.83,30.48)
text("R140/R141 set about 4.95 V; C141/C142 require effective-capacitance review at 5 V.",36.83,35.56)

(PROJ/"Logic_Audio_Power.kicad_sch").write_text(dumps(sch)+"\n")
