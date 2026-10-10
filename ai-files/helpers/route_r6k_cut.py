"""flatpak: route_r6k_cut.py BOARD CUTS.json : minimum copper cross-section of power fills.
Each cut: [zones ('A+B'), layer F|2|B, axis 'h'|'v', [c0, c1], [s0, s1], label]. For every line (axis 'h': y = c, x from s0 to s1;
'v': x = c, y from s0 to s1) with c stepped 0.05 mm through [c0, c1], the copper length of the union of the fills on the line is
measured (0.02 mm sampling); the minimum over c is the narrowest cross-section the current must pass (all parallel lanes summed)."""
import sys, json, pcbnew
MM = 1e6; b = pcbnew.LoadBoard(sys.argv[1]); LY = {'F': pcbnew.F_Cu, '2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
for zn, ly, ax, (c0, c1), (s0, s1), lab in json.load(open(sys.argv[2])):
    L = LY[ly]; fs = [z.GetFilledPolysList(L) for z in b.Zones() if not z.GetIsRuleArea() and z.GetZoneName() in zn.split('+') and z.IsOnLayer(L) and z.HasFilledPolysForLayer(L)]
    best = (1e9, None); c = c0
    while c <= c1 + 1e-9:
        n = 0; s = s0; st = 0.02
        while s <= s1:
            v = pcbnew.VECTOR2I(int(s * MM), int(c * MM)) if ax == 'h' else pcbnew.VECTOR2I(int(c * MM), int(s * MM))
            if any(f.Contains(v) for f in fs): n += 1
            s += st
        w = n * st
        if w < best[0]: best = (w, c)
        c += 0.05
    print('%-46s %-24s %s cut min %.2f mm at %s=%.2f' % (lab, zn, ly, best[0], 'y' if ax == 'h' else 'x', best[1]))
