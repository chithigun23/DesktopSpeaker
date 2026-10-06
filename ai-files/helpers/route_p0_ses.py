#!/usr/bin/env python3
"""Step A (import): route_p0_ses.py import IN.kicad_pcb SES OUT.kicad_pcb
   Step B (clean):  route_p0_ses.py clean IN.kicad_pcb OUT.kicad_pcb EXCLUDED.json P0BOARD.kicad_pcb
   Import SES, save; then reload, delete tracks/vias of excluded critical nets, refill zones, save. (flatpak pcbnew)"""
import sys, json, pcbnew
mode = sys.argv[1]
if mode == 'import':
    b = pcbnew.LoadBoard(sys.argv[2])
    print('import', pcbnew.ImportSpecctraSES(b, sys.argv[3]))
    pcbnew.SaveBoard(sys.argv[4], b)
else:
    b = pcbnew.LoadBoard(sys.argv[2])
    excl = set(json.load(open(sys.argv[4])))
    base = pcbnew.LoadBoard(sys.argv[5])      # phase-0 board: its own tracks/vias are kept
    def key(t):
        if t.GetClass() == 'PCB_VIA':
            p = t.GetPosition(); return ('v', t.GetNetname(), round(p.x/1e4), round(p.y/1e4))
        a, c = t.GetStart(), t.GetEnd()
        k = sorted([(round(a.x/1e4), round(a.y/1e4)), (round(c.x/1e4), round(c.y/1e4))])
        return ('t', t.GetNetname(), tuple(k[0]), tuple(k[1]))
    keep = set(key(t) for t in base.Tracks())
    rm = []
    for t in list(b.Tracks()):
        if t.GetNetname() in excl and key(t) not in keep:
            rm.append((t.GetNetname(), t.GetClass()))
    for t in list(b.Tracks()):
        if t.GetNetname() in excl and key(t) not in keep: b.Remove(t)
    print('removed tracks/vias of excluded nets:', len(rm))
    json.dump(rm, open(sys.argv[3] + '.removed.json', 'w'))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(sys.argv[3], b)
