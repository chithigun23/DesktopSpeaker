"""flatpak: route_r6j_dangle.py BOARD DRC.json OUT : (R6j) remove the tracks/vias that a kicad-cli DRC report lists as track_dangling / via_dangling (use route_r6j_clean.sh)"""
import sys,json,pcbnew
b=pcbnew.LoadBoard(sys.argv[1]);d=json.load(open(sys.argv[2]));MM=1e6;n=0
for v in d['violations']:
    if v['type'] not in ('track_dangling','via_dangling'): continue
    for it in v['items']:
        u=it.get('uuid')
        for t in b.GetTracks():
            if t.m_Uuid.AsString()==u: b.RemoveNative(t); n+=1; break
pcbnew.SaveBoard(sys.argv[3],b);print('removed',n)
