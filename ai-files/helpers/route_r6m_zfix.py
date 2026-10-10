"""flatpak: route_r6m_zfix.py IN OUT SPEC.json : R6m zone fixes, then refill and save. SPEC list items:
 {"rmzone":NAME}                               delete zone NAME
 {"minw":FNMATCH,"w":0.3}                      set min thickness on every (non rule-area) zone whose name matches
 {"zsub":NAME,"box":[x0,y0,x1,y1]}             subtract a rectangle from the zone outline (outline only; fill follows on refill)
Prints a line per op; EDIT-BAD counts ops that matched nothing."""
import sys, json, fnmatch, pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1]); bad = 0
def zs(n): return [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetZoneName() == n]
for s in json.load(open(sys.argv[3])):
    if 'rmzone' in s:
        r = zs(s['rmzone'])
        for z in r: b.RemoveNative(z)
    elif 'minw' in s:
        r = [z for z in b.Zones() if not z.GetIsRuleArea() and fnmatch.fnmatchcase(z.GetZoneName(), s['minw'])]
        for z in r: z.SetMinThickness(int(round(s['w'] * MM)))
        print('  ', sorted(z.GetZoneName() for z in r))
    elif 'zsub' in s:
        r = zs(s['zsub']); x0, y0, x1, y1 = [int(round(v * MM)) for v in s['box']]
        for z in r:
            c = pcbnew.SHAPE_POLY_SET(); c.NewOutline()
            for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): c.Append(x, y)
            o = z.Outline(); a0 = o.Area() / MM / MM; o.BooleanSubtract(c); o.Simplify()
            print('   outline %s %.2f -> %.2f mm2, %d outline(s)' % (z.GetZoneName(), a0, o.Area() / MM / MM, o.OutlineCount()))
    else: raise ValueError(s)
    print(list(s.items())[0], len(r)); bad += (len(r) == 0)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[2], b)
print('EDIT-BAD', bad)
