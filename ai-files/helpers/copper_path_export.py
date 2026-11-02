# Export copper (filled zones, tracks, pads, vias) of the named nets from a .kicad_pcb to JSON for copper_path_solve.py.
# Usage: ~/Applications/kicad.AppImage python3.11 copper_path_export.py BOARD.kicad_pcb OUT.json "/Net/A,/Net/B"
# Written 2026-11-02 for reports/charge-policy-2026-11-02.md. Read-only on the board.
import pcbnew, sys, json
B=pcbnew.LoadBoard(sys.argv[1]); out=sys.argv[2]
NETS=sys.argv[3].split(",")
mm=pcbnew.ToMM
CU=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]
LN={pcbnew.F_Cu:"F.Cu",pcbnew.In1_Cu:"In1.Cu",pcbnew.In2_Cu:"In2.Cu",pcbnew.B_Cu:"B.Cu"}
def sps(ps):
    res=[]
    for i in range(ps.OutlineCount()):
        o=ps.Outline(i); ring=[(mm(o.CPoint(k).x),mm(o.CPoint(k).y)) for k in range(o.PointCount())]
        holes=[]
        for h in range(ps.HoleCount(i)):
            hh=ps.Hole(i,h); holes.append([(mm(hh.CPoint(k).x),mm(hh.CPoint(k).y)) for k in range(hh.PointCount())])
        res.append([ring,holes])
    return res
D={n:{"zones":[],"tracks":[],"vias":[],"pads":[]} for n in NETS}
for z in B.Zones():
    n=z.GetNetname()
    if n not in D: continue
    for L in CU:
        if z.IsOnLayer(L):
            fp=z.GetFilledPolysList(L)
            D[n]["zones"].append({"name":z.GetZoneName(),"layer":LN[L],"polys":sps(fp),"area":fp.Area()/1e12 if fp.OutlineCount() else 0,
               "padconn":int(z.GetPadConnection()),"tgap":mm(z.GetThermalReliefGap()),"tspoke":mm(z.GetThermalReliefSpokeWidth())})
for t in B.GetTracks():
    n=t.GetNetname()
    if n not in D: continue
    if t.Type()==pcbnew.PCB_VIA_T:
        v=pcbnew.Cast_to_PCB_VIA(t)
        D[n]["vias"].append({"x":mm(v.GetPosition().x),"y":mm(v.GetPosition().y),"drill":mm(v.GetDrillValue()),"dia":mm(v.GetWidth(pcbnew.F_Cu)),
            "layers":[LN[L] for L in CU if v.IsOnLayer(L)]})
    else:
        ps=pcbnew.SHAPE_POLY_SET(); t.TransformShapeToPolygon(ps,t.GetLayer(),0,int(0.005e6),pcbnew.ERROR_INSIDE)
        D[n]["tracks"].append({"layer":LN.get(t.GetLayer(),"?"),"w":mm(t.GetWidth()),"x1":mm(t.GetStart().x),"y1":mm(t.GetStart().y),"x2":mm(t.GetEnd().x),"y2":mm(t.GetEnd().y),"len":mm(t.GetLength()),"polys":sps(ps)})
for fp in B.GetFootprints():
    for p in fp.Pads():
        n=p.GetNetname()
        if n not in D: continue
        for L in CU:
            if p.IsOnLayer(L) and p.FlashLayer(L):
                ps=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(ps,L,0,int(0.005e6),pcbnew.ERROR_INSIDE)
                D[n]["pads"].append({"ref":fp.GetReference(),"num":p.GetNumber(),"layer":LN[L],"x":mm(p.GetPosition().x),"y":mm(p.GetPosition().y),
                    "drill":mm(p.GetDrillSize().x),"polys":sps(ps)})
json.dump(D,open(out,"w"))
for n in NETS:
    d=D[n]; print(n,"zones",len(d["zones"]),"tracks",len(d["tracks"]),"vias",len(d["vias"]),"pads",len(d["pads"]))
    for z in d["zones"]: print("   zone",z["name"],z["layer"],"area %.1f mm2"%z["area"],"pieces",len(z["polys"]),"padconn",z["padconn"],"spoke",z["tspoke"])
    import collections
    c=collections.Counter((t["layer"],round(t["w"],3)) for t in d["tracks"]); L=collections.defaultdict(float)
    for t in d["tracks"]: L[(t["layer"],round(t["w"],3))]+=t["len"]
    for k in sorted(c): print("   track",k,"n",c[k],"len %.2f"%L[k])
    cv=collections.Counter((v["drill"],v["dia"]) for v in d["vias"]); print("   vias",dict(cv))
