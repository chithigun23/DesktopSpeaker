"""flatpak: route_r6l_pourarea.py BOARD OUT.json : filled pour area per net and layer (all zones of the net, R6l companions included), non-GND."""
import sys, json, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1]); LN = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: '2', pcbnew.B_Cu: 'B'}; out = {}
for z in b.Zones():
    n = str(z.GetNetname())
    if z.GetIsRuleArea() or n in ('', 'GND'): continue
    for L in LN:
        if z.IsOnLayer(L) and z.HasFilledPolysForLayer(L): out[n + '|' + LN[L]] = round(out.get(n + '|' + LN[L], 0) + z.GetFilledPolysList(L).Area() / MM / MM, 1)
json.dump(out, open(sys.argv[2], 'w'), indent=0)
