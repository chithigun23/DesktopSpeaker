"""flatpak: route_p3_hand5.py IN OUT : U6 OUT_A+ local escape (pin 2 -> via -> B.Cu -> via -> C285 pad 2)"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); MM = 1e6
V = lambda x, y: pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
net = 'Net-(U6-OUT_A+)'; nt = b.FindNet(net)
def trk(pts, w, layer):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c)); t.SetLayer(layer); t.SetWidth(int(w * MM)); t.SetNet(nt); b.Add(t)
def via(x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(int(0.6 * MM)); v.SetDrill(int(0.3 * MM)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(nt); b.Add(v)
trk([(115.085, 134.855), (114.4, 134.855)], 0.2, pcbnew.F_Cu); via(114.4, 134.855)
trk([(114.4, 134.855), (116.0, 131.7)], 0.4, pcbnew.B_Cu); via(116.0, 131.7)
trk([(116.0, 131.7), (116.347, 132.45)], 0.2, pcbnew.F_Cu)
pcbnew.SaveBoard(sys.argv[2], b)
