# Hand-solder gap check: courtyard(+pads) gaps < 0.5 mm (2.0 mm tall-vs-passive is enforced by the generator) and reference-label overlaps. Flatpak python.
import pcbnew, itertools, sys
MM = 1e6
bd = pcbnew.LoadBoard('/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb')
R = {}
T = {}
for f in bd.GetFootprints():
    b = f.GetCourtyard(pcbnew.F_CrtYd).BBox(); r = [b.GetX() / MM, b.GetY() / MM, b.GetRight() / MM, b.GetBottom() / MM]
    for q in f.Pads():
        pb = q.GetBoundingBox(); r = [min(r[0], pb.GetX() / MM - 0.2), min(r[1], pb.GetY() / MM - 0.2), max(r[2], pb.GetRight() / MM + 0.2), max(r[3], pb.GetBottom() / MM + 0.2)]
    R[f.GetReference()] = r
    if f.Reference().IsVisible():
        tb = f.Reference().GetBoundingBox(); T[f.GetReference()] = [tb.GetX() / MM, tb.GetY() / MM, tb.GetRight() / MM, tb.GetBottom() / MM]
def gap(a, b):
    return max(max(a[0] - b[2], b[0] - a[2]), max(a[1] - b[3], b[1] - a[3]))
bad = [(a, b, round(gap(R[a], R[b]), 2)) for a, b in itertools.combinations(R, 2) if gap(R[a], R[b]) < 0.45 and not (a.startswith('H') or b.startswith('H'))]
print('courtyard gaps < 0.45 mm:', len(bad), bad[:20])
tb_ = [(a, b) for a in T for b in R if a != b and gap(T[a], R[b]) < -0.05 and not (b.startswith('H'))]
print('reference text overlapping another courtyard:', len(tb_), tb_[:20])
tt = [(a, b) for a, b in itertools.combinations(T, 2) if gap(T[a], T[b]) < 0.0]
print('reference text overlapping text:', len(tt), tt[:20])
