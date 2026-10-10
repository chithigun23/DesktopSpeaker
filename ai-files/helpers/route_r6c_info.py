"""flatpak: route_r6c_info.py BOARD REF... : pad positions/nets of refs"""
import sys, pcbnew
b=pcbnew.LoadBoard(sys.argv[1]); MM=1e6
for f in b.GetFootprints():
    if f.GetReference() in sys.argv[2:]:
        bb=f.GetBoundingBox(); print(f.GetReference(), f.GetValue(), round(f.GetX()/MM,2), round(f.GetY()/MM,2), f.GetOrientationDegrees(), 'bbox', round(bb.GetLeft()/MM,1), round(bb.GetTop()/MM,1), round(bb.GetRight()/MM,1), round(bb.GetBottom()/MM,1))
        for p in f.Pads(): print('  ', p.GetNumber(), p.GetName(), round(p.GetX()/MM,3), round(p.GetY()/MM,3), round(p.GetSizeX()/MM,2), round(p.GetSizeY()/MM,2), str(p.GetNetname()))
