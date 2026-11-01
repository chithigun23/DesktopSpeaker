#!/usr/bin/env python3
"""route_oct_export.py BOARD.kicad_pcb OUT.json
Run with the KiCad AppImage python:  ~/Applications/kicad.AppImage python3.11 route_oct_export.py BOARD OUT
(never pass 'python3' to the AppImage: that starts the GUI).

Exports the board geometry needed by route_oct.py (all coordinates in mm):
  outline   : board outline polygons (Edge.Cuts)
  pads      : ref, number, net, netclass, attr, layers, centre, size, orientation, drill, copper polygon per copper layer
  tracks    : segments and arcs (arcs as polylines), net, netclass, layer, width
  vias      : position, diameter, drill, net, netclass
  zones     : copper zones with filled polygons per layer (teardrops flagged)
  areas     : rule areas (keep-outs) with their flags and outline per layer
  courtyard : per footprint F/B courtyard polygons
  drawings  : copper graphics (board and footprint level) as polygons, net if any
  netclass  : net -> effective netclass name as pcbnew reports it
The board is only read; nothing is saved.
"""
import sys, os, json, pcbnew

MM = 1e-6
CU = {pcbnew.F_Cu: 'F.Cu', pcbnew.In1_Cu: 'In1.Cu', pcbnew.In2_Cu: 'In2.Cu', pcbnew.B_Cu: 'B.Cu'}


def polys(ps):
    """SHAPE_POLY_SET -> list of polygons, each [outer, hole1, ...] with [x,y] mm points."""
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        rings = [[[o.CPoint(j).x * MM, o.CPoint(j).y * MM] for j in range(o.PointCount())]]
        for h in range(ps.HoleCount(i)):
            hh = ps.Hole(i, h)
            rings.append([[hh.CPoint(j).x * MM, hh.CPoint(j).y * MM] for j in range(hh.PointCount())])
        out.append(rings)
    return out


def main(src, dst):
    b = pcbnew.LoadBoard(src)
    b.BuildConnectivity()
    D = dict(source=os.path.abspath(src), outline=[], pads=[], tracks=[], vias=[], zones=[], areas=[], courtyard={}, drawings=[], netclass={})
    o = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(o, True)
    D['outline'] = polys(o)
    for net in b.GetNetsByName().values() if hasattr(b, 'GetNetsByName') else []:
        pass
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        fp.BuildCourtyardCaches()
        cy = {}
        for lid, nm in ((pcbnew.F_CrtYd, 'F'), (pcbnew.B_CrtYd, 'B')):
            c = fp.GetCourtyard(lid)
            if c.OutlineCount():
                cy[nm] = polys(c)
        D['courtyard'][ref] = dict(poly=cy, x=fp.GetPosition().x * MM, y=fp.GetPosition().y * MM, rot=fp.GetOrientation().AsDegrees(),
                                   side='B' if fp.GetLayer() == pcbnew.B_Cu else 'F', npads=len(list(fp.Pads())))
        for p in fp.Pads():
            attr = p.GetAttribute()
            an = {pcbnew.PAD_ATTRIB_PTH: 'PTH', pcbnew.PAD_ATTRIB_SMD: 'SMD', pcbnew.PAD_ATTRIB_CONN: 'CONN', pcbnew.PAD_ATTRIB_NPTH: 'NPTH'}.get(attr, str(attr))
            cp = {}
            for lid, nm in CU.items():
                if p.IsOnLayer(lid) and p.FlashLayer(lid):
                    ps = pcbnew.SHAPE_POLY_SET()
                    p.TransformShapeToPolygon(ps, lid, 0, 200, pcbnew.ERROR_OUTSIDE)   # 0.2 um outward approximation
                    cp[nm] = polys(ps)
            sz = p.GetSize(pcbnew.F_Cu) if p.IsOnLayer(pcbnew.F_Cu) else p.GetSize(pcbnew.B_Cu)
            dr = p.GetDrillSize()
            D['pads'].append(dict(ref=ref, num=p.GetNumber(), net=p.GetNetname(), cls=p.GetNetClassName(), attr=an,
                                  x=p.GetPosition().x * MM, y=p.GetPosition().y * MM, sx=sz.x * MM, sy=sz.y * MM,
                                  rot=p.GetOrientation().AsDegrees(), drill=[dr.x * MM, dr.y * MM] if p.HasDrilledHole() or an == 'NPTH' else None,
                                  layers=sorted(cp), poly=cp))
            if p.GetNetname():
                D['netclass'][p.GetNetname()] = p.GetNetClassName()
        for g in fp.GraphicalItems():
            if g.GetLayer() in CU:
                ps = pcbnew.SHAPE_POLY_SET()
                g.TransformShapeToPolygon(ps, g.GetLayer(), 0, 2000, pcbnew.ERROR_OUTSIDE)
                D['drawings'].append(dict(ref=ref, layer=CU[g.GetLayer()], net=g.GetNetname() if hasattr(g, 'GetNetname') else '', poly=polys(ps)))
        for z in fp.Zones():
            D['areas' if z.GetIsRuleArea() else 'zones'].append(zone_rec(b, z, ref))
    for d in b.GetDrawings():
        if d.GetLayer() in CU:
            ps = pcbnew.SHAPE_POLY_SET()
            d.TransformShapeToPolygon(ps, d.GetLayer(), 0, 2000, pcbnew.ERROR_OUTSIDE)
            D['drawings'].append(dict(ref='', layer=CU[d.GetLayer()], net=d.GetNetname() if hasattr(d, 'GetNetname') else '', poly=polys(ps)))
    for t in b.GetTracks():
        c = t.GetClass()
        if c == 'PCB_VIA':
            D['vias'].append(dict(x=t.GetPosition().x * MM, y=t.GetPosition().y * MM, d=t.GetWidth(pcbnew.F_Cu) * MM, drill=t.GetDrillValue() * MM,
                                  net=t.GetNetname(), cls=t.GetNetClassName(), top=b.GetLayerName(t.TopLayer()), bot=b.GetLayerName(t.BottomLayer())))
        elif c in ('PCB_TRACK', 'PCB_ARC'):
            if c == 'PCB_ARC':
                ps = pcbnew.SHAPE_POLY_SET()
                t.TransformShapeToPolygon(ps, t.GetLayer(), 0, 2000, pcbnew.ERROR_OUTSIDE)
                pl = polys(ps)
            else:
                pl = None
            D['tracks'].append(dict(x1=t.GetStart().x * MM, y1=t.GetStart().y * MM, x2=t.GetEnd().x * MM, y2=t.GetEnd().y * MM, w=t.GetWidth() * MM,
                                    layer=b.GetLayerName(t.GetLayer()), net=t.GetNetname(), cls=t.GetNetClassName(), arc=c == 'PCB_ARC', poly=pl,
                                    uuid=t.m_Uuid.AsString()))
        if t.GetNetname():
            D['netclass'][t.GetNetname()] = t.GetNetClassName()
    for z in b.Zones():
        D['areas' if z.GetIsRuleArea() else 'zones'].append(zone_rec(b, z, ''))
    json.dump(D, open(dst, 'w'))
    print('exported', dst, {k: len(v) for k, v in D.items() if isinstance(v, (list, dict))}, flush=True)


def zone_rec(b, z, ref):
    layers = [CU[l] for l in z.GetLayerSet().Seq() if l in CU]
    r = dict(ref=ref, name=z.GetZoneName(), net=z.GetNetname(), cls=z.GetNetClassName() if z.GetNetname() else '', layers=layers)
    if z.GetIsRuleArea():
        r.update(no_tracks=z.GetDoNotAllowTracks(), no_vias=z.GetDoNotAllowVias(), no_pads=z.GetDoNotAllowPads(), no_zones=z.GetDoNotAllowZoneFills(),
                 outline=polys(z.Outline()))
    else:
        r['teardrop'] = bool(z.IsTeardropArea())
        r['fills'] = {CU[l]: polys(z.GetFilledPolysList(l)) for l in z.GetLayerSet().Seq() if l in CU and z.HasFilledPolysForLayer(l)}
    return r


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
    os._exit(0)
