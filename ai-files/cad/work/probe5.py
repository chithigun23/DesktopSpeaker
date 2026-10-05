import Part, FreeCAD as App
s=Part.read("/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/kicad-library/3d/PJ-307.step")
V=App.Vector
print("PROBE z-scan x=-8.5 y=0:","".join("#" if s.isInside(V(-8.5,0,z/4),0.01,True) else "." for z in range(-12,23)))
print("PROBE y-scan x=-8.5 z=2.5:","".join("#" if s.isInside(V(-8.5,y/2,2.5),0.01,True) else "." for y in range(-12,13)))
print("PROBE y-scan x=-8.5 z=4.5:","".join("#" if s.isInside(V(-8.5,y/2,4.5),0.01,True) else "." for y in range(-12,13)))
print("PROBE z-scan x=-8.5 y=5:","".join("#" if s.isInside(V(-8.5,5,z/4),0.01,True) else "." for z in range(-12,23)))
s=Part.read("/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/kicad-library/3d/TYPE-C-31-M-12.step")
print("PROBE usb z-scan y=0 x=0:","".join("#" if s.isInside(V(0,0,z/4),0.01,True) else "." for z in range(-4,14)))
print("PROBE usb z-scan y=4 x=0:","".join("#" if s.isInside(V(0,4,z/4),0.01,True) else "." for z in range(-4,14)))
