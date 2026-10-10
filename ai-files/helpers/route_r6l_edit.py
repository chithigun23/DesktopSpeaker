"""flatpak: route_r6l_edit.py IN OUT SPEC.json : route_r6k_edit.py ops plus R6l op
 {"textmove":REF,"text":TXT,"d":[dx,dy]}                          move a footprint text item (field or text) by an offset
 {"boardtext":TXT,"p":[x,y],"d":[dx,dy]}                          move a board-level text near p by an offset
R6k ops:
 {"viasize":N,"p":[x,y],"d":0.8,"drill":0.4}                     resize the via of net N at p
 {"viabox":N,"box":[x0,y0,x1,y1],"d":0.8,"drill":0.4}              resize every via of net N inside box
 {"zoneset":NAME,"clr":C,"prio":P}                              set zone local clearance / priority
 {"rmzone":NAME}                                                  delete zone NAME
 {"movevia":N,"p":[x,y],"to":[x,y]}                               move a via (tracks are not moved)
zoneadd accepts "layer" F|B|2 and an optional "minw".
SPEC list items:
 {"net":N,"layer":"F|B|2","w":0.25,"pts":[[x,y],...]}            add track polyline
 {"net":N,"via":[x,y],"d":0.6,"drill":0.3}                        add via
 {"rmseg":N,"a":[x,y],"b":[x,y]}                                  remove track of net N with these endpoints (either order, 0.03 mm)
 {"rmat":N,"p":[x,y],"layer":"F"}                                 remove tracks of net N with an endpoint at p (optional layer)
 {"rmvia":N,"p":[x,y]}                                            remove via of net N at p
 {"rmbox":N,"box":[x0,y0,x1,y1],"layer":"F"}                      remove tracks/vias of net N fully inside box (optional layer, 'V' = vias only)
 {"zone":NAME,"pts":[[x,y],...]}                                  replace the outline of zone NAME
 {"zoneadd":N,"layer":"F","name":NAME,"pts":[...],"prio":P,"clr":0.3} add a filled copper zone
 {"move":REF,"to":[x,y],"rot":deg}                                 move footprint (absolute position, optional absolute orientation)
 {"moveby":REF,"d":[dx,dy]}                                       move footprint by an offset
 {"ripnet":N,"keep":[[x0,y0,x1,y1],...]}                          remove all tracks/vias of net N except items fully inside a keep box
 {"ripbox":N,"box":[x0,y0,x1,y1]}                                 remove tracks/vias of net N with any endpoint (or via) inside box
 {"setw":N,"a":[x,y],"b":[x,y],"w":W}                              change width of a track (endpoints as rmseg)
Prints a line per edit; fails loudly if an rm matched nothing."""
import sys, json
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import pcbnew
from route_r6a_lib import trk, via, refill, full, zone, LAY, rule_area
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1])
def near(q, p, tol=0.03): return abs(q.x / MM - p[0]) < tol and abs(q.y / MM - p[1]) < tol
def nn(n): return full(n, b)
bad = 0
for s in json.load(open(sys.argv[3])):
    if 'rmseg' in s:
        n = nn(s['rmseg']); r = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and str(t.GetNetname()) == n and ((near(t.GetStart(), s['a']) and near(t.GetEnd(), s['b'])) or (near(t.GetStart(), s['b']) and near(t.GetEnd(), s['a'])))]
        for t in r: b.RemoveNative(t)
        print('rmseg', n, s['a'], s['b'], len(r)); bad += (len(r) == 0)
    elif 'rmat' in s:
        n = nn(s['rmat']); L = LAY.get(s.get('layer', ''), None)
        r = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and str(t.GetNetname()) == n and (L is None or t.GetLayer() == L) and (near(t.GetStart(), s['p']) or near(t.GetEnd(), s['p']))]
        for t in r: b.RemoveNative(t)
        print('rmat', n, s['p'], len(r)); bad += (len(r) == 0)
    elif 'rmvia' in s:
        n = nn(s['rmvia']); r = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and str(t.GetNetname()) == n and near(t.GetPosition(), s['p'])]
        for t in r: b.RemoveNative(t)
        print('rmvia', n, s['p'], len(r)); bad += (len(r) == 0)
    elif 'rmbox' in s:
        n = nn(s['rmbox']); x0, y0, x1, y1 = s['box']; ly = s.get('layer', '')
        def inb(q): return x0 <= q.x / MM <= x1 and y0 <= q.y / MM <= y1
        r = []
        for t in b.GetTracks():
            if str(t.GetNetname()) != n: continue
            if t.GetClass() == 'PCB_VIA':
                if ly in ('', 'V') and inb(t.GetPosition()): r.append(t)
            elif ly != 'V' and (ly == '' or t.GetLayer() == LAY[ly]) and inb(t.GetStart()) and inb(t.GetEnd()): r.append(t)
        for t in r: b.RemoveNative(t)
        print('rmbox', n, s['box'], ly, len(r)); bad += (len(r) == 0)
    elif 'ripnet' in s:
        n = nn(s['ripnet']); K = s.get('keep', [])
        def kin(q): return any(k[0] <= q.x / MM <= k[2] and k[1] <= q.y / MM <= k[3] for k in K)
        r = [t for t in b.GetTracks() if str(t.GetNetname()) == n and not ((kin(t.GetPosition()) if t.GetClass() == 'PCB_VIA' else (kin(t.GetStart()) and kin(t.GetEnd()))))]
        for t in r: b.RemoveNative(t)
        print('ripnet', n, len(r)); bad += (len(r) == 0)
    elif 'ripbox' in s:
        n = nn(s['ripbox']); x0, y0, x1, y1 = s['box']
        def inb(q): return x0 <= q.x / MM <= x1 and y0 <= q.y / MM <= y1
        r = [t for t in b.GetTracks() if str(t.GetNetname()) == n and ((inb(t.GetPosition())) if t.GetClass() == 'PCB_VIA' else (inb(t.GetStart()) or inb(t.GetEnd())))]
        for t in r: b.RemoveNative(t)
        print('ripbox', n, len(r)); bad += (len(r) == 0)
    elif 'setw' in s:
        n = nn(s['setw']); r = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and str(t.GetNetname()) == n and ((near(t.GetStart(), s['a']) and near(t.GetEnd(), s['b'])) or (near(t.GetStart(), s['b']) and near(t.GetEnd(), s['a'])))]
        for t in r: t.SetWidth(int(round(s['w'] * MM)))
        print('setw', n, len(r)); bad += (len(r) == 0)
    elif 'viasize' in s or 'viabox' in s:
        n = nn(s.get('viasize', s.get('viabox')))
        if 'viasize' in s: r = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and str(t.GetNetname()) == n and near(t.GetPosition(), s['p'])]
        else:
            x0, y0, x1, y1 = s['box']; r = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and str(t.GetNetname()) == n and x0 <= t.GetX() / MM <= x1 and y0 <= t.GetY() / MM <= y1]
        for t in r: t.SetWidth(int(round(s['d'] * MM))); t.SetDrill(int(round(s['drill'] * MM)))
        print('viasize', n, len(r)); bad += (len(r) == 0)
    elif 'movevia' in s:
        n = nn(s['movevia']); r = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and str(t.GetNetname()) == n and near(t.GetPosition(), s['p'])]
        for t in r: t.SetPosition(pcbnew.VECTOR2I(int(round(s['to'][0] * MM)), int(round(s['to'][1] * MM))))
        print('movevia', n, len(r)); bad += (len(r) == 0)
    elif 'textmove' in s:
        f = b.FindFootprintByReference(s['textmove']); r = []
        for it in list(f.GraphicalItems()) + list(f.GetFields()):
            if hasattr(it, 'GetText') and it.GetText() == s['text']: r.append(it)
        for it in r: it.Move(pcbnew.VECTOR2I(int(round(s['d'][0] * MM)), int(round(s['d'][1] * MM))))
        print('textmove', s['textmove'], s['text'], len(r)); bad += (len(r) == 0)
    elif 'boardtext' in s:
        r = [d for d in b.GetDrawings() if d.GetClass() in ('PCB_TEXT', 'PTEXT') and d.GetText() == s['boardtext'] and near(d.GetPosition(), s['p'], 0.1)]
        for it in r: it.Move(pcbnew.VECTOR2I(int(round(s['d'][0] * MM)), int(round(s['d'][1] * MM))))
        print('boardtext', s['boardtext'], len(r)); bad += (len(r) == 0)
    elif 'zoneset' in s:
        zz = [z for z in b.Zones() if z.GetZoneName() == s['zoneset']]
        for z in zz:
            if 'clr' in s: z.SetLocalClearance(int(s['clr'] * MM))
            if 'prio' in s: z.SetAssignedPriority(s['prio'])
        print('zoneset', s['zoneset'], len(zz)); bad += (len(zz) == 0)
    elif 'rmzone' in s:
        zz = [z for z in b.Zones() if z.GetZoneName() == s['rmzone']]
        for z in zz: b.RemoveNative(z)
        print('rmzone', s['rmzone'], len(zz)); bad += (len(zz) == 0)
    elif 'zone' in s:
        zz = [z for z in b.Zones() if z.GetZoneName() == s['zone']]
        for z in zz:
            o = z.Outline(); o.RemoveAllContours(); o.NewOutline()
            for x, y in s['pts']: o.Append(int(round(x * MM)), int(round(y * MM)))
        print('zone', s['zone'], len(zz)); bad += (len(zz) == 0)
    elif 'zoneadd' in s:
        zone(b, s['zoneadd'], s['layer'], s['pts'], prio=s.get('prio', 5), clr=s.get('clr', 0.3), minw=s.get('minw', 0.2), name=s.get('name', ''), lock=False)
        print('zoneadd', s.get('name'))
    elif 'rulearea' in s:
        rule_area(b, s['rulearea'], s['pts'], layers=s.get('layers', 'F')); print('rulearea', s['rulearea'])
    elif 'move' in s or 'moveby' in s:
        f = b.FindFootprintByReference(s.get('move', s.get('moveby')))
        p0 = (f.GetX() / MM, f.GetY() / MM)
        if 'move' in s: f.SetPosition(pcbnew.VECTOR2I(int(round(s['to'][0] * MM)), int(round(s['to'][1] * MM))))
        else: f.SetPosition(pcbnew.VECTOR2I(int(round((p0[0] + s['d'][0]) * MM)), int(round((p0[1] + s['d'][1]) * MM))))
        if 'rot' in s: f.SetOrientationDegrees(s['rot'])
        print('move', f.GetReference(), p0, '->', (f.GetX() / MM, f.GetY() / MM), f.GetOrientationDegrees())
    elif 'via' in s:
        via(b, s['net'], s['via'][0], s['via'][1], s.get('d', 0.6), s.get('drill', 0.3), lock=False)
    else:
        trk(b, s['net'], s['layer'], [tuple(p) for p in s['pts']], s['w'], lock=False)
refill(b); pcbnew.SaveBoard(sys.argv[2], b)
print('EDIT-BAD', bad)
