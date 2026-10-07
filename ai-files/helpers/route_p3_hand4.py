"""flatpak: route_p3_hand.py IN OUT : hand layout of U6 bootstrap caps (C286 pads x 116.35/117.5, C288 pads 118.45/119.58 at y 131.0) + short tracks"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); MM = 1e6
V = lambda x, y: pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
fp = {f.GetReference(): f for f in b.GetFootprints()}
fp['C286'].SetPosition(V(117.597, 131.0)); fp['C288'].SetPosition(V(119.467, 129.7))
nets = ['Net-(U6-OUT_A-)', 'Net-(U6-OUT_B-)', 'Net-(U6-BST_A-)', 'Net-(U6-BST_B-)']
n = 0
for t in list(b.Tracks()):
    nm = str(t.GetNetname())
    if nm not in nets: continue
    if nm.endswith('OUT_A-)') and (t.GetWidth() > 0.3 * MM) and t.GetStart().x / MM < 117.0 and t.GetStart().y / MM < 129.5 and t.GetEnd().y / MM < 129.5 and abs(t.GetStart().x/MM - 111.12) < 0.1: continue  # trunk piece far
    keep = False
    if nm.endswith('OUT_A-)') and abs(t.GetStart().x / MM - 116.55) < 0.01 and abs(t.GetStart().y / MM - 129.1) < 0.01 and abs(t.GetEnd().x / MM - 111.12) < 0.01: keep = True
    if nm.endswith('OUT_B-)') and abs(t.GetStart().x / MM - 119.25) < 0.01 and abs(t.GetStart().y / MM - 128.55) < 0.01: keep = False; t.SetStart(V(120.17, 127.16))
    if keep: continue
    b.RemoveNative(t); n += 1
print('removed', n)
def trk(net, pts, w):
    ni = b.FindNet(net).GetNetCode()
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c)); t.SetLayer(pcbnew.F_Cu); t.SetWidth(int(w * MM)); t.SetNet(b.FindNet(net)); b.Add(t)
trk('Net-(U6-OUT_A-)', [(116.745, 133.695), (116.745, 133.15), (117.03, 132.76), (117.03, 131.0)], 0.2)
trk('Net-(U6-OUT_A-)', [(117.03, 131.0), (116.55, 129.1)], 0.4)
trk('Net-(U6-BST_A-)', [(117.245, 133.695), (117.245, 133.4), (117.455, 132.76), (117.455, 132.14), (118.164, 131.0)], 0.2)
trk('Net-(U6-BST_B-)', [(117.745, 133.695), (117.745, 133.3), (117.875, 132.76), (117.875, 132.3), (118.9, 131.6), (118.9, 129.7)], 0.2)
trk('Net-(U6-OUT_B-)', [(118.245, 133.695), (118.245, 133.0), (119.1, 132.4), (119.55, 131.3), (120.034, 129.7)], 0.2)
trk('Net-(U6-OUT_B-)', [(120.034, 129.7), (120.034, 128.5)], 0.6)
trk('Net-(U6-OUT_B-)', [(120.034, 128.5), (120.17, 127.16)], 0.8)
trk('Net-(U6-OUT_B-)', [(120.17, 127.16), (123.87, 121.605)], 1.5)
pcbnew.SaveBoard(sys.argv[2], b)
