#!/usr/bin/env python3
"""fpfix.py SRC.kicad_pcb OUT.kicad_pcb REPORT.json : RT-5 task A footprint fixes, text-level, board only (plain python3).
 J2/J3 PJ-307   front NPTH pegs local x -5.75 -> -4.75 (HOOYA PJ-307 PCB layout: pegs 1.0 and 3.5 from the body front, pin 1 at 3.1)
 U1 BM83        GND pad 56 local (1.40, -0.03) -> (4.77, -0.03) (DS70005402D p.56 Fig. 8-2: X 12.27, Y 10.47; local x = X - 7.5, y = 10.44 - Y)
 SW100          TE 1977066-1 land pattern redrawn from TE drawing C1 p.1 (origin = terminal-pad row centre, actuator toward -y = board edge),
                footprint moved so the actuator tip (local y -2.95) sits on the board edge y 20.0: (136.07, 25.245) -> (136.07, 22.95)
 C275           CP_Elec_8x10 land -> CP_Elec_6.3x7.7 (KiCad Capacitor_SMD library geometry; part EEHZA1E101XP case D8 6.3 x 7.7)
Pad numbers and nets are kept; SW100 gains two net-less bracket pads (number "") and the TE 'no copper tracks' rule area."""
import sys, json, re, uuid as U

src, out, repf = sys.argv[1:4]
L = open(src, encoding='utf-8').read().split('\n')
LIB_CP = '/home/chithi/kicad-libs/footprints/Capacitor_SMD.pretty/CP_Elec_6.3x7.7.kicad_mod'
rep = {}
nu = lambda: str(U.uuid4())


def fp_range(ref):
    i = 0
    while i < len(L):
        if L[i].startswith('\t(footprint '):
            j = i + 1
            while L[j] != '\t)': j += 1
            if any(x.strip() == '(property "Reference" "%s"' % ref for x in L[i:j + 1]): return i, j
            i = j + 1
        else: i += 1
    sys.exit('no footprint ' + ref)


def subblocks(i0, i1):
    """depth-2 children of a footprint block: list of (start, end) line indices"""
    out = []; k = i0 + 1
    while k < i1:
        if L[k].startswith('\t\t(') and not L[k].startswith('\t\t\t'):
            if L[k].count('(') == L[k].count(')'): out.append((k, k)); k += 1; continue
            e = k + 1
            while L[e] != '\t\t)': e += 1
            out.append((k, e)); k = e + 1
        else: k += 1
    return out


edits = {}   # line index -> replacement text (None = delete)


def set_line(k, new, tag):
    rep.setdefault(tag, []).append([L[k].strip(), new.strip()]); edits[k] = new


# ---- J2 / J3 ----
for ref in ('J2', 'J3'):
    i0, i1 = fp_range(ref)
    for a, b in subblocks(i0, i1):
        if L[a].startswith('\t\t(pad "" np_thru_hole'):
            for k in range(a, b + 1):
                m = re.match(r'^\t\t\t\(at -5\.75 (-?5) 270\)$', L[k])
                if m: set_line(k, '\t\t\t(at -4.75 %s 270)' % m.group(1), ref)
    assert len(rep[ref]) == 2, rep.get(ref)

# ---- U1 pad 56 ----
i0, i1 = fp_range('U1')
for a, b in subblocks(i0, i1):
    if L[a].startswith('\t\t(pad "56" '):
        for k in range(a, b + 1):
            if L[k] == '\t\t\t(at 1.4 -0.03 90)': set_line(k, '\t\t\t(at 4.77 -0.03 90)', 'U1')
assert len(rep['U1']) == 1

# ---- C275 ----
i0, i1 = fp_range('C275')
lib = open(LIB_CP, encoding='utf-8').read().split('\n')
libg = []; k = 0
while k < len(lib):
    if re.match(r'^\t\((fp_line|fp_circle|fp_arc|fp_poly|fp_rect|fp_text)(?: |$)', lib[k]):
        e = k
        while lib[e] != '\t)': e += 1
        for x in lib[k:e + 1]:
            x = '\t' + x
            if re.match(r'^\t+\(uuid "', x): x = re.sub(r'"[^"]+"', '"%s"' % nu(), x)
            libg.append(x)
        k = e + 1
    else: k += 1
first_g = None; ng = 0
for a, b in subblocks(i0, i1):
    s = L[a]
    if re.match(r'^\t\t\((fp_line|fp_circle|fp_arc|fp_poly|fp_rect|fp_text)(?: |$)', s):
        if first_g is None: first_g = a
        for k in range(a, b + 1): edits[k] = None
        ng += 1
    if s.startswith('\t\t(pad "1" ') or s.startswith('\t\t(pad "2" '):
        sign = '-' if '"1"' in s else ''
        for k in range(a, b + 1):
            if L[k].startswith('\t\t\t(at '): set_line(k, '\t\t\t(at %s2.7 0)' % sign, 'C275')
            if L[k].startswith('\t\t\t(size '): set_line(k, '\t\t\t(size 3.5 1.6)', 'C275')
            if L[k].startswith('\t\t\t(roundrect_rratio '): set_line(k, '\t\t\t(roundrect_rratio 0.15625)', 'C275')
edits[first_g] = '\n'.join(libg)
set_line(i0, '\t(footprint "DesktopSpeaker:CP_Elec_6.3x7.7"', 'C275')
for k in range(i0, i1):
    if L[k].startswith('\t\t(descr '):
        set_line(k, '\t\t(descr "SMD capacitor, aluminum electrolytic, 6.3x7.7mm (Panasonic EEH-ZA case D8); land from KiCad Capacitor_SMD CP_Elec_6.3x7.7")', 'C275')
rep['C275_graphics'] = dict(removed_blocks=ng, added_lines=len(libg))

# ---- SW100 ----
i0, i1 = fp_range('SW100')
X0, Y0 = 136.07, 22.95
TD = ['\t\t\t(teardrops', '\t\t\t\t(best_length_ratio 0.5)', '\t\t\t\t(max_length 1)', '\t\t\t\t(best_width_ratio 1)', '\t\t\t\t(max_width 2)',
      '\t\t\t\t(curved_edges yes)', '\t\t\t\t(filter_ratio 0.9)', '\t\t\t\t(enabled yes)', '\t\t\t\t(allow_two_segments yes)',
      '\t\t\t\t(prefer_zone_connections yes)', '\t\t\t)']


def pad(num, typ, x, y, sx, sy, layers, net=None, drill=None):
    o = ['\t\t(pad "%s" %s' % (num, typ), '\t\t\t(at %s %s)' % (x, y), '\t\t\t(size %s %s)' % (sx, sy)]
    if drill: o.append('\t\t\t(drill %s)' % drill)
    o.append('\t\t\t(layers %s)' % layers)
    if net: o.append('\t\t\t(net "%s")' % net)
    if 'smd' in typ: o += TD
    o += ['\t\t\t(uuid "%s")' % nu(), '\t\t)']
    return o


def rect(layer, x1, y1, x2, y2, w):
    return ['\t\t(fp_rect', '\t\t\t(start %s %s)' % (x1, y1), '\t\t\t(end %s %s)' % (x2, y2), '\t\t\t(stroke', '\t\t\t\t(width %s)' % w,
            '\t\t\t\t(type solid)', '\t\t\t)', '\t\t\t(fill no)', '\t\t\t(layer "%s")' % layer, '\t\t\t(uuid "%s")' % nu(), '\t\t)']


def line(layer, x1, y1, x2, y2, w):
    return ['\t\t(fp_line', '\t\t\t(start %s %s)' % (x1, y1), '\t\t\t(end %s %s)' % (x2, y2), '\t\t\t(stroke', '\t\t\t\t(width %s)' % w,
            '\t\t\t\t(type solid)', '\t\t\t)', '\t\t\t(layer "%s")' % layer, '\t\t\t(uuid "%s")' % nu(), '\t\t)']


Q = '"Net-(U4-QON)"'
new = []
new += rect('F.CrtYd', -2.75, -3.2, 2.75, 1.15, 0.05)
new += rect('F.Fab', -2.0, -2.1, 2.0, 0.45, 0.1)          # case 4.0 wide, front face 0.85 behind the actuator tip, depth 2.55
new += rect('F.Fab', -1.0, -2.95, 1.0, -2.1, 0.1)         # actuator 2.0, tip at -2.95 (board edge)
new += line("F.SilkS", -2.65, -0.3, -2.65, 0.9, 0.12)
new += line("F.SilkS", 2.65, -0.3, 2.65, 0.9, 0.12)
new += pad('', 'np_thru_hole circle', -2.125, -0.9, 0.9, 0.9, '"*.Cu" "*.Mask"', drill=0.9)
new += pad('', 'np_thru_hole circle', 2.125, -0.9, 0.9, 0.9, '"*.Cu" "*.Mask"', drill=0.9)
new += pad('1', 'smd rect', -1.225, 0, 0.75, 1.8, '"F.Cu" "F.Mask" "F.Paste"', net='Net-(U4-QON)')
new += pad('1', 'smd rect', 1.225, 0, 0.75, 1.8, '"F.Cu" "F.Mask" "F.Paste"', net='Net-(U4-QON)')
new += pad('2', 'smd rect', 0, 0, 0.6, 1.8, '"F.Cu" "F.Mask" "F.Paste"', net='GND')
new += pad('', 'smd rect', -1.85, -1.95, 1.3, 0.9, '"F.Cu" "F.Mask" "F.Paste"')   # bracket solder tabs (no net)
new += pad('', 'smd rect', 1.85, -1.95, 1.3, 0.9, '"F.Cu" "F.Mask" "F.Paste"')
# TE 'prohibited area of copper tracks' 2.0 x 1.2 between the bracket pads (absolute coordinates, as KiCad stores footprint zones)
zx0, zx1, zy0, zy1 = X0 - 1.0, X0 + 1.0, Y0 - 2.4, Y0 - 1.2
fz = lambda v: ('%.4f' % v).rstrip('0').rstrip('.')
new += ['\t\t(zone', '\t\t\t(layer "F.Cu")', '\t\t\t(uuid "%s")' % nu(), '\t\t\t(name "SW100_TE_NO_TRACKS")', '\t\t\t(hatch full 0.508)',
        '\t\t\t(connect_pads', '\t\t\t\t(clearance 0)', '\t\t\t)', '\t\t\t(min_thickness 0.254)', '\t\t\t(keepout', '\t\t\t\t(tracks not_allowed)',
        '\t\t\t\t(vias not_allowed)', '\t\t\t\t(pads allowed)', '\t\t\t\t(copperpour not_allowed)', '\t\t\t\t(footprints allowed)', '\t\t\t)',
        '\t\t\t(placement', '\t\t\t\t(enabled no)', '\t\t\t\t(sheetname "")', '\t\t\t)', '\t\t\t(fill', '\t\t\t\t(thermal_gap 0.508)',
        '\t\t\t\t(thermal_bridge_width 0.508)', '\t\t\t\t(island_removal_mode 0)', '\t\t\t)', '\t\t\t(polygon', '\t\t\t\t(pts',
        '\t\t\t\t\t(xy %s %s) (xy %s %s) (xy %s %s) (xy %s %s)' % (fz(zx0), fz(zy0), fz(zx1), fz(zy0), fz(zx1), fz(zy1), fz(zx0), fz(zy1)),
        '\t\t\t\t)', '\t\t\t)', '\t\t)']
firstk = None; nrem = 0
for a, b in subblocks(i0, i1):
    if re.match(r'^\t\t\((fp_line|fp_circle|fp_arc|fp_poly|fp_rect|pad|zone) ?', L[a]):
        if firstk is None: firstk = a
        for k in range(a, b + 1): edits[k] = None
        nrem += 1
edits[firstk] = '\n'.join(new)
for k in range(i0, i1):
    if L[k] == '\t\t(at 136.07 25.245)': set_line(k, '\t\t(at %s %s)' % (X0, Y0), 'SW100')
    if L[k].startswith('\t\t(descr '):
        set_line(k, '\t\t(descr "TE 1977066-1 right-angle SMT tact switch with locating pegs, land pattern per TE drawing C1 p.1: terminals 1/3 = pad 1 (0.75 x 1.8 at +-1.225), terminal 2 = pad 2 (0.6 x 1.8), pegs 2x d0.9 at +-2.125 0.9 toward the actuator, bracket tabs 1.3 x 0.9 at +-1.85 -1.95, no tracks between the tabs. Origin = terminal-pad row centre; actuator tip at y -2.95.")', 'SW100')
rep['SW100_blocks_replaced'] = nrem
rep['SW100_move'] = [[136.07, 25.245], [X0, Y0]]

res = []
for k, x in enumerate(L):
    if k in edits:
        if edits[k] is not None: res.append(edits[k])
        continue
    res.append(x)
open(out, 'w', encoding='utf-8').write('\n'.join(res))
json.dump(rep, open(repf, 'w'), indent=1)
print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in rep.items()}))
