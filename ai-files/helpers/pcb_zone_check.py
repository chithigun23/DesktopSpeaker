# Lists parts whose footprint box is outside their zone (ZONES/ZONE_OF from build_pcb.py). Run with the flatpak KiCad python.
import json, sys
src = open('/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/build_pcb.py').read()
ns = {}
exec(src[src.index("ZONES = {"):src.index("# sheet fallback")], ns)
exec(src[src.index("SHEET_ZONE = {"):src.index("SHEET_HINT")], ns)
import pcbnew
d = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/layout.json'))
bd = pcbnew.LoadBoard('/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb')
UL, UR = d['board']['u0'], d['board']['u1']
X0 = 150 - (UL + UR) / 2
out = []
for f in bd.GetFootprints():
    r = f.GetReference()
    if r.startswith('H'):
        continue
    b = f.GetBoundingBox(False)
    x0 = b.GetX() / 1e6 - X0; x1 = b.GetRight() / 1e6 - X0
    y0 = 100 - b.GetBottom() / 1e6; y1 = 100 - b.GetY() / 1e6
    sh = d['sheets'][r]; o = d['owner'].get(r)
    zn = ns['ZONE_OF'].get(r) or ns['ZONE_OF'].get(o) or ns['SHEET_ZONE'].get(sh, 'AUDIO')
    z = ns['ZONES'][zn]; zs = z if isinstance(z[0], tuple) else (z,)
    if not any(x0 >= q[0] - 0.3 and x1 <= q[1] + 0.3 and y0 >= q[2] - 0.3 and y1 <= q[3] + 0.3 for q in zs):
        out.append((zn, r, round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)))
print(len(out), 'parts outside zone')
for o in sorted(out):
    print(o)
