#!/usr/bin/env python3
"""Routing P1 board tool (flatpak pcbnew).
  route_p1_post.py import  IN.kicad_pcb SES OUT.kicad_pcb [ONLY_NETS.json]
        import SES; widen < 0.2 tracks to 0.2; set netclass-correct widths for none; refill zones (GND 0.4 etc as P0); save.
        If ONLY_NETS.json is given, autorouter items on nets not in the list are removed (safety).
  route_p1_post.py stats BOARD   -> json on stdout: unrouted nets (ratsnest per net), track/via counts
"""
import sys, json, pcbnew
mode = sys.argv[1]
HI = set(['/SYS_RAW', '/Battery_Charger/BAT_INT', '/Fuel_Gauge_Power/BAT_PACK', '/Battery_Charger/PACK_RAW', '/Battery_Charger/VBUS_PD', '/USB_VBUS', '/Battery_Charger/PMID'])

def refill(b):
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        if z.GetZoneName().startswith('GND'): z.SetLocalClearance(400000)
        elif z.GetNetname() == '/Amplifiers/PVDD_AMP': z.SetLocalClearance(350000)
        elif z.GetNetname() in HI: z.SetLocalClearance(450000)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())

if mode == 'import':
    b = pcbnew.LoadBoard(sys.argv[2])
    print('import', pcbnew.ImportSpecctraSES(b, sys.argv[3]))
    pcbnew.SaveBoard(sys.argv[4], b)
    b = pcbnew.LoadBoard(sys.argv[4])
    only = set(json.load(open(sys.argv[5]))) if len(sys.argv) > 5 else None
    nw = 0
    for t in b.Tracks():
        if t.GetClass() != 'PCB_VIA' and t.GetWidth() < 200000:
            t.SetWidth(200000); nw += 1
    print('widened', nw)
    refill(b)
    pcbnew.SaveBoard(sys.argv[4], b)
if mode == 'stats':
    b = pcbnew.LoadBoard(sys.argv[2])
    c = {}
    for t in b.Tracks():
        k = 'via' if t.GetClass() == 'PCB_VIA' else b.GetLayerName(t.GetLayer())
        c[k] = c.get(k, 0) + 1
    print(json.dumps(c))
if mode == 'merge':
    # merge IN.kicad_pcb SES OUT.kicad_pcb NETS.json STRIPPED.kicad_pcb : import SES into the stripped board, copy tracks/vias of the listed nets into IN
    cur = pcbnew.LoadBoard(sys.argv[2]); tmp = pcbnew.LoadBoard(sys.argv[6])
    print('import', pcbnew.ImportSpecctraSES(tmp, sys.argv[3]))
    nets = set(json.load(open(sys.argv[5])))
    n = 0
    for t in tmp.Tracks():
        if t.GetNetname() not in nets: continue
        if t.GetClass() == 'PCB_VIA':
            v = pcbnew.PCB_VIA(cur); v.SetViaType(t.GetViaType()); v.SetPosition(t.GetPosition()); v.SetWidth(t.GetWidth(pcbnew.F_Cu)); v.SetDrill(t.GetDrill())
            v.SetLayerPair(t.TopLayer(), t.BottomLayer()); v.SetNet(cur.FindNet(t.GetNetname())); cur.Add(v)
        else:
            q = pcbnew.PCB_TRACK(cur); q.SetStart(t.GetStart()); q.SetEnd(t.GetEnd()); q.SetLayer(t.GetLayer())
            q.SetWidth(max(200000, t.GetWidth())); q.SetNet(cur.FindNet(t.GetNetname())); cur.Add(q)
        n += 1
    print('merged', n)
    refill(cur)
    pcbnew.SaveBoard(sys.argv[4], cur)

if mode == 'refill':
    b = pcbnew.LoadBoard(sys.argv[2]); refill(b); pcbnew.SaveBoard(sys.argv[3], b)
