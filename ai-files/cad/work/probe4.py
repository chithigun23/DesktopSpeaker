import Part, FreeCAD as App
s=Part.read("/home/chithi/Desktop/DesktopSpeaker/ai-files/cad/parts/ND65_3D/ND65-4 and 8.step")
print("PROBE type",s.ShapeType,s.isValid(),s.Solids[0].isClosed() if s.Solids else None)
rows=[]
for f in s.Faces:
    if f.Surface.__class__.__name__=="Plane":
        n=f.normalAt(0,0)
        if abs(abs(n.z)-1)<1e-3 and f.Area>20:
            b=f.BoundBox; rows.append((round(b.ZMin,2),round(f.Area,1),round(b.XMin,1),round(b.XMax,1),round(b.YMin,1),round(b.YMax,1)))
for r in sorted(rows): print("PROBE",r)
cyl=[]
for f in s.Faces:
    if f.Surface.__class__.__name__=="Cylinder" and f.Surface.Radius<3 :
        b=f.BoundBox; cyl.append((round(f.Surface.Radius,2),round(b.XMin+b.XMax,1)/2,round((b.YMin+b.YMax)/2,1),round(b.ZMin,1),round(b.ZMax,1)))
for c in cyl: print("PROBE cyl",c)
