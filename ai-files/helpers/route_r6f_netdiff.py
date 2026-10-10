"""flatpak: route_r6f_netdiff.py BOARD NETLIST.net [OUT.kicad_pcb] : compare pad nets of BOARD (netlist {slash} escapes treated as '/') with a kicad-cli sexpr netlist; with OUT, apply the netlist nets to differing pads (creating nets as needed) and save"""
import sys, re, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); txt = open(sys.argv[2]).read()
want = {}
i = txt.index('(nets'); cur = None
for m in re.finditer(r'\(name "((?:[^"\\]|\\.)*)"\)|\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', txt[i:]):
    if m.group(1) is not None: cur = m.group(1).replace('\\"', '"')
    else: want[(m.group(2), m.group(3))] = cur
diff = []
for f in b.GetFootprints():
    r = f.GetReference()
    for p in f.Pads():
        k = (r, str(p.GetNumber()))
        if k not in want: continue
        if str(p.GetNetname()) != want[k] and str(p.GetNetname()) != want[k].replace('{slash}', '/'): diff.append((k, str(p.GetNetname()), want[k], p))
print('netlist nodes', len(want), 'diffs', len(diff))
for k, o, n, p in diff: print(' ', k, o, '->', n)
if len(sys.argv) > 3:
    for k, o, n, p in diff:
        ni = b.FindNet(n)
        if ni is None:
            ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni)
        p.SetNet(ni)
    pcbnew.SaveBoard(sys.argv[3], b); print('saved', sys.argv[3])
