"""flatpak: route_r6l_gndfill.py BOARD : GND zone fill pieces per zone and layer (count, total area, pieces < 2 mm2), and the pad count of GND
pads not touched by any GND fill or GND track/via on their layer (to see that widening other nets did not cut GND pours away from pads)."""
import sys, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: '1', pcbnew.In2_Cu: '2', pcbnew.B_Cu: 'B'}
tot = {}
for z in b.Zones():
    if z.GetIsRuleArea() or str(z.GetNetname()) != 'GND': continue
    for L in LN:
        if z.IsOnLayer(L) and z.HasFilledPolysForLayer(L):
            fp = z.GetFilledPolysList(L); n = fp.OutlineCount(); a = fp.Area() / MM / MM
            small = sum(1 for k in range(n) if fp.Outline(k).Area() / MM / MM < 2.0)
            tot.setdefault(LN[L], [0, 0.0]); tot[LN[L]][0] += n; tot[LN[L]][1] += a
            print('GNDZONE %-18s %s pieces %3d area %9.1f small %d' % (z.GetZoneName() or '-', LN[L], n, a, small))
for k, v in sorted(tot.items()): print('GND layer %s pieces %d area %.1f' % (k, v[0], v[1]))
