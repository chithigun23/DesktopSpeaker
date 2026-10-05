import Part, FreeCAD as App
s=Part.read("/home/chithi/Desktop/DesktopSpeaker/ai-files/cad/parts/ND65_3D/ND65-4 and 8.step")
V=App.Vector
for (x,y) in [(23.35,23.35),(26.5,23.35),(23.35,-23.35),(0,0),(0,28),(0,31)]:
    print("PROBE",x,y,"".join("#" if s.isInside(V(x,y,z),0.01,True) else "." for z in range(-26,23)))
print("PROBE vol",s.Volume,"faces",len(s.Faces))
# hole search along diagonal at z=20
print("PROBE diag z=20","".join("#" if s.isInside(V(d,d,20),0.01,True) else "." for d in [x*0.5 for x in range(0,66)]))
print("PROBE x z=20 y=23.35","".join("#" if s.isInside(V(d,23.35,20),0.01,True) else "." for d in [x*0.5 for x in range(0,66)]))
