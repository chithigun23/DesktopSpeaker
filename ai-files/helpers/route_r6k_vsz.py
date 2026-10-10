"""flatpak: route_r6k_vsz.py IN OUT MODE ARG : via sizing for route_r6k_upsize.sh.
MODE 'up' ARG=classes (comma): set every via of those netclasses with drill < 0.4 to 0.8/0.4, write OUT.vsz.json (list of [net,x,y,d0,dr0]).
MODE 'revert' ARG=DRC json: put back the original size of every upsized via (OUT.vsz.json of IN) that appears in a non-silk DRC item."""
import sys, json, fnmatch
import pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1]); out = sys.argv[2]; mode = sys.argv[3]
pats = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/R6k.kicad_pro'))['net_settings']['netclass_patterns']
def cl(n):
    for p in pats:
        if fnmatch.fnmatchcase(n, p['pattern']): return p['netclass']
    return 'Default'
vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
if mode == 'up':
    cls = sys.argv[4].split(','); rec = []
    for v in vias:
        n = str(v.GetNetname())
        if cl(n) in cls and v.GetDrillValue() < 0.4 * MM - 1:
            rec.append([n, v.GetX() / MM, v.GetY() / MM, v.GetWidth(pcbnew.F_Cu) / MM, v.GetDrillValue() / MM])
            v.SetWidth(int(0.8 * MM)); v.SetDrill(int(0.4 * MM))
    json.dump(rec, open(out.replace('.kicad_pcb', '.vsz.json'), 'w')); print('upsized', len(rec))
else:
    rec = json.load(open(sys.argv[1].replace('.kicad_pcb', '.vsz.json'))); d = json.load(open(sys.argv[4]))
    bad = set()
    for x in d['violations']:
        if x['type'].startswith('silk') or x['type'] in ('lib_footprint_mismatch', 'skew_out_of_range', 'diff_pair_uncoupled_length_too_long'): continue
        for it in x['items']:
            if it['description'].startswith('Via'): bad.add((round(it['pos']['x'], 2), round(it['pos']['y'], 2)))
    keep = []; nrev = 0
    for r in rec:
        if (round(r[1], 2), round(r[2], 2)) in bad:
            for v in vias:
                if abs(v.GetX() / MM - r[1]) < 0.005 and abs(v.GetY() / MM - r[2]) < 0.005 and str(v.GetNetname()) == r[0]:
                    v.SetWidth(int(round(r[3] * MM))); v.SetDrill(int(round(r[4] * MM))); nrev += 1
        else: keep.append(r)
    json.dump(keep, open(out.replace('.kicad_pcb', '.vsz.json'), 'w')); print('reverted', nrev, 'kept', len(keep))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(out, b)
