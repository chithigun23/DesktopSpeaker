"""flatpak: route_p3_movecaps.py IN OUT dy : move bootstrap caps by dy mm (negative=up), rip tracks of nets on their pads; writes OUT.q.json"""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); dy = float(sys.argv[3]); MM = 1e6
nets = set()
for f in b.GetFootprints():
    if f.GetReference() in ('C286', 'C288', 'C299', 'C301'):
        for p in f.Pads(): nets.add(str(p.GetNetname()))
        f.Move(pcbnew.VECTOR2I(0, int(dy * MM)))
nets.discard('GND')
n = 0
for t in list(b.Tracks()):
    if str(t.GetNetname()) in nets: b.RemoveNative(t); n += 1
print('nets', nets, 'removed', n)
json.dump(sorted(nets), open(sys.argv[2].replace('.kicad_pcb', '.q.json'), 'w'))
pcbnew.SaveBoard(sys.argv[2], b)
