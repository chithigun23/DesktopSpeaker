# -*- coding: utf-8 -*-
"""Post-fix of single outliers in DesktopSpeaker.kicad_pcb (run with the flatpak KiCad python AFTER build_pcb.sh).
Moves each listed passive to the nearest free spot (0.25 mm grid, 0/90 deg, courtyard gap 0.5 mm, label slot adjacent, board edge clear)
around its target pad while keeping >= MIN_AWAY from a set of pads.  Usage: pcb_refine.py REF:TARGETREF:PIN[:AWAYNET:MIN] ..."""
import sys, math, itertools
import pcbnew
B = '/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb'
MM = 1e6
bd = pcbnew.LoadBoard(B)
fps = {f.GetReference(): f for f in bd.GetFootprints()}

def crt(f):
    b = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
    r = [b.GetX() / MM, b.GetY() / MM, b.GetRight() / MM, b.GetBottom() / MM]
    for q in f.Pads():        # courtyards smaller than the pads exist in the library: union with the pad extents + 0.2 mm (as build_pcb.py)
        pb = q.GetBoundingBox()
        r = [min(r[0], pb.GetX() / MM - 0.2), min(r[1], pb.GetY() / MM - 0.2), max(r[2], pb.GetRight() / MM + 0.2), max(r[3], pb.GetBottom() / MM + 0.2)]
    return r

def txt(f):
    b = f.Reference().GetBoundingBox()
    return [b.GetX() / MM, b.GetY() / MM, b.GetRight() / MM, b.GetBottom() / MM]

def inter(a, b, g):
    return a[0] < b[2] + g and a[2] > b[0] - g and a[1] < b[3] + g and a[3] > b[1] - g

edge = [fps['U1'].GetBoundingBox().GetX() / MM]  # unused
bb = bd.GetBoardEdgesBoundingBox()
EDGE = (bb.GetX() / MM + 0.5, bb.GetY() / MM + 0.5, bb.GetRight() / MM - 0.5, bb.GetBottom() / MM - 0.5)
for spec in sys.argv[1:]:
    p = spec.split(':')
    ref, tref, pin = p[0], p[1], p[2]
    awaynet = p[3] if len(p) > 3 else None
    minaway = float(p[4]) if len(p) > 4 else 0.0
    maxy = float(p[5]) if len(p) > 5 else 1e9      # courtyard bottom limit (sheet y; analogue parts: v >= 10.5 => y <= 89.5)
    f = fps[ref]
    tp = [q for q in fps[tref].Pads() if q.GetNumber() == pin][0].GetPosition()
    tx, ty = tp.x / MM, tp.y / MM
    away = [(q.GetPosition().x / MM, q.GetPosition().y / MM) for ff in fps.values() for q in ff.Pads() if awaynet and q.GetNetname() == awaynet]
    others = [(r, crt(g), txt(g)) for r, g in fps.items() if r != ref]
    cx0, cy0 = f.GetPosition().x / MM, f.GetPosition().y / MM
    cur_rot = f.GetOrientationDegrees()
    tnet = fps[tref].FindPadByNumber(pin).GetNetname()
    cur_d = min([math.hypot(q.GetPosition().x / MM - tx, q.GetPosition().y / MM - ty) for q in f.Pads() if q.GetNetname() == tnet] or [99])
    best = None
    for rot in (0, 90):
        f.SetOrientationDegrees(rot)
        for dx in [i * 0.25 for i in range(-48, 49)]:
            for dy in [i * 0.25 for i in range(-48, 49)]:
                f.SetPosition(pcbnew.VECTOR2I(int((tx + dx) * MM), int((ty + dy) * MM)))
                c = crt(f)
                if c[0] < EDGE[0] or c[1] < EDGE[1] or c[2] > EDGE[2] or c[3] > EDGE[3] or c[3] > maxy:
                    continue
                if any(inter(c, oc, 0.5) or inter(c, ot, 0.0) for r, oc, ot in others):
                    continue
                pads = [(q.GetPosition().x / MM, q.GetPosition().y / MM, q.GetNetname()) for q in f.Pads()]
                if away and min(math.hypot(x - a, y - b) for x, y, n in pads for a, b in away) < minaway:
                    continue
                d = min(math.hypot(x - tx, y - ty) for x, y, n in pads if n == fps[tref].FindPadByNumber(pin).GetNetname())
                # label slot: right, left, below, above of the courtyard
                w, h = len(ref) * 0.76 + 0.3, 1.1
                slots = [((c[2] + 0.2 + w / 2, (c[1] + c[3]) / 2), (c[2] + 0.2, (c[1] + c[3]) / 2 - h / 2, c[2] + 0.2 + w, (c[1] + c[3]) / 2 + h / 2)),
                         (((c[0] + c[2]) / 2, c[1] - 0.2 - h / 2), ((c[0] + c[2]) / 2 - w / 2, c[1] - 0.2 - h, (c[0] + c[2]) / 2 + w / 2, c[1] - 0.2)),
                         (((c[0] + c[2]) / 2, c[3] + 0.2 + h / 2), ((c[0] + c[2]) / 2 - w / 2, c[3] + 0.2, (c[0] + c[2]) / 2 + w / 2, c[3] + 0.2 + h)),
                         ((c[0] - 0.2 - w / 2, (c[1] + c[3]) / 2), (c[0] - 0.2 - w, (c[1] + c[3]) / 2 - h / 2, c[0] - 0.2, (c[1] + c[3]) / 2 + h / 2))]
                for pos, sr in slots:
                    if sr[0] < EDGE[0] or sr[2] > EDGE[2] or sr[1] < EDGE[1] or sr[3] > EDGE[3]:
                        continue
                    if any(inter(sr, oc, 0.1) or inter(sr, ot, 0.1) for r, oc, ot in others):
                        continue
                    if best is None or d < best[0]:
                        best = (d, rot, tx + dx, ty + dy, pos)
                    break
    if best is not None and best[0] > cur_d - 0.4:
        best = None
        print('keep', ref, 'current %.2f mm' % cur_d)
        f.SetOrientationDegrees(cur_rot); f.SetPosition(pcbnew.VECTOR2I(int(cx0 * MM), int(cy0 * MM)))
        continue
    if best is None:
        f.SetOrientationDegrees(cur_rot); f.SetPosition(pcbnew.VECTOR2I(int(cx0 * MM), int(cy0 * MM)))
        print('no spot for', ref)
        continue
    d, rot, x, y, pos = best
    f.SetOrientationDegrees(rot)
    f.SetPosition(pcbnew.VECTOR2I(int(x * MM), int(y * MM)))
    f.Reference().SetTextAngleDegrees(0)
    f.Reference().SetPosition(pcbnew.VECTOR2I(int(pos[0] * MM), int(pos[1] * MM)))
    print('moved %s to (%.2f, %.2f) rot %d, %.2f mm (was %.2f) from %s pin %s' % (ref, x, y, rot, d, cur_d, tref, pin))
pcbnew.SaveBoard(B, bd)
