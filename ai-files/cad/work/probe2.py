import Part, FreeCAD as App
L='/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/kicad-library/3d/'
s=Part.read(L+"TYPE-C-31-M-12.step")
print("PROBE usbc solids bb", [ (round(x.BoundBox.YMin,1),round(x.BoundBox.YMax,1),round(x.Volume,1)) for x in s.Solids][:14])
for y in [x*0.5 for x in range(-5,11)]:
    print("PROBE usbc y",y,[s.isInside(App.Vector(xx,y,1.2),0.01,True) for xx in (-2.5,0,2.5)])
s=Part.read(L+"PJ-307.step")
for x in range(-9,6):
    print("PROBE pj x",x,[s.isInside(App.Vector(x,yy,2.5),0.01,True) for yy in (-3,0,3)])
s=Part.read(L+"BM83SM1-00TA.step")
big=sorted(s.Solids,key=lambda q:-q.Volume)[:3]
for q in big: print("PROBE bm",q.Volume,q.BoundBox)
