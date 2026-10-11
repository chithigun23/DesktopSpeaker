"""flatpak: route_r6p_dangle.py IN.kicad_pcb OUT.kicad_pcb DRC.json NET1,NET2|* : delete the tracks / vias that kicad-cli DRC reports as
track_dangling / via_dangling (matched by uuid), only for the listed nets ('*' = any net); refill and save. Prints the count."""
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); d = json.load(open(sys.argv[3])); nets = None if sys.argv[4] == '*' else set(sys.argv[4].split(','))
U = set()
for x in d['violations']:
    if x['type'] in ('track_dangling', 'via_dangling'):
        for i in x['items']: U.add(i['uuid'])
rm = [t for t in b.GetTracks() if t.m_Uuid.AsString() in U and (nets is None or str(t.GetNetname()) in nets)]
for t in rm: b.RemoveNative(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[2]); print('removed dangling', len(rm))
