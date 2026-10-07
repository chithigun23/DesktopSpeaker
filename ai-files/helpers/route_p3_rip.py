"""flatpak: route_p3_rip.py IN OUT NETS.json : remove all tracks/vias of the listed nets"""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); nets = set(json.load(open(sys.argv[3]))); n = 0
for t in list(b.Tracks()):
    if str(t.GetNetname()) in nets: b.RemoveNative(t); n += 1
print('removed', n); pcbnew.SaveBoard(sys.argv[2], b)
