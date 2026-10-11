"""flatpak: route_r6p_try.py BOARD CANDS.json : legality (route_r6k_why / route_r6j_smooth rules) of candidate polylines and vias.
CANDS: [{"id":..,"net":N,"layer":"F|B|2","w":W,"pts":[[x,y],...]} | {"id":..,"net":N,"via":[x,y],"d":0.6}, ...]
Same-net copper is ignored. Prints per candidate ok or the first failing segment with the rule code and blockers."""
import sys, json
H = '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/'
src = open(H + 'route_r6k_why.py').read(); src = src[:src.index("net = a[2]; L =")]
cands = json.load(open(sys.argv[2])); sys.argv = [H + 'route_r6k_why.py', sys.argv[1]]
exec(src)
LL = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, '2': pcbnew.In2_Cu}
def blockers(net, L, sh):
    out = []
    for u in b.Tracks():
        if str(u.GetNetname()) == net: continue
        us = u.GetEffectiveShape(L) if u.GetClass() == 'PCB_VIA' else (u.GetEffectiveShape() if u.GetLayer() == L else None)
        if us is None: continue
        r = need(net, str(u.GetNetname()), False, False, sh, L)
        if not gap_ok(us, sh, r): out.append('%s %s (%.3f,%.3f) need %.2f' % (u.GetClass()[4:], u.GetNetname(), u.GetPosition().x / MM, u.GetPosition().y / MM, r))
    for f in b.GetFootprints():
        for pd in f.Pads():
            if str(pd.GetNetname()) == net or not pd.IsOnLayer(L): continue
            r = need(net, str(pd.GetNetname()), False, True, sh, L)
            if not gap_ok(pd.GetEffectiveShape(L), sh, r): out.append('pad %s.%s %s need %.2f' % (f.GetReference(), pd.GetNumber(), pd.GetNetname(), r))
    return out[:4]
for c in cands:
    n = full(c['net'], b)
    if 'via' in c:
        x, y = c['via']; bad = []
        for Lk in ('F', '2', 'B'):
            L = LL[Lk]; v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetWidth(int(c.get('d', 0.6) * MM)); v.SetDrill(int(c.get('drill', 0.3) * MM)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            sh = v.GetEffectiveShape(L)
            bl = blockers(n, L, sh)
            if bl: bad.append((Lk, bl))
            for z in fzones:
                if str(z.GetNetname()) != n and z.IsOnLayer(L) and z.Outline().Collide(sh, int(0.3 * MM)): bad.append((Lk, 'zone ' + z.GetZoneName()))
        print(c.get('id'), 'VIA', 'ok' if not bad else bad); continue
    L = LL[c['layer']]; res = 'ok'
    for p, q in zip(c['pts'][:-1], c['pts'][1:]):
        r = why(n, L, tuple(p), tuple(q), c['w'], set())
        if r != 'ok':
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(*p)); t.SetEnd(V(*q)); t.SetLayer(L); t.SetWidth(int(round(c['w'] * MM)))
            res = '%s at %s-%s %s' % (r, p, q, blockers(n, L, t.GetEffectiveShape())); break
    print(c.get('id'), res)
