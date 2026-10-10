"""flatpak: route_r6n_pgnd.py BOARD [I_total_A] [OUT.json] : U4 PGND (pin 27) return-current distribution, two models.
F.Cu: 2D resistive grid of the GND copper connected to pin 27 (zone fills, pads, tracks, via lands) in a box around U4,
0.02 mm cells, 35 um copper. I is injected uniformly over the pin-27 pad. Copper at the F box edge is open.
Each GND via couples its F land to In1 through the F-In1 barrel (0.2104 mm prepreg, 20 um plating). Model 'ideal': In1 is
an ideal 0 V plane (worst case, crowds current into the via nearest the pin). Model 'plane': In1 is a 15.2 um (0.5 oz) grid,
0.05 mm cells, rasterised from the In1 GND fill (antipads included) over a 27 x 30 mm box whose edge is 0 V.
B.Cu is ignored in both (conservative). Env PGND_MODEL=ideal runs the fast ideal model only. Ratings: project rule 1 A per 0.3 mm of drill (0.2 mm 0.67 A, 0.3 mm 1.0 A);
IPC-2221 external, barrel area pi*(d+t)*t, 15 K rise."""
import sys, json, math
import numpy as np
import pcbnew
MM = 1e6
b = pcbnew.LoadBoard(sys.argv[1]); I = float(sys.argv[2]) if len(sys.argv) > 2 else 4.5
out = sys.argv[3] if len(sys.argv) > 3 else None
FB = (148.6, 119.95, 153.2, 130.3); H = 0.02
PB = (138.0, 107.0, 165.0, 137.0); H2 = 0.05
RSF = 1.72e-8 / 35e-6; RSI = 1.72e-8 / 15.2e-6; T = 0.020; LB = 0.2104
def raster(box, h, polys, extra=None):
    x0, y0, x1, y1 = box; nx, ny = int(round((x1 - x0) / h)), int(round((y1 - y0) / h))
    cu = np.zeros((ny, nx), bool); ex = np.zeros((ny, nx), bool)
    for j in range(ny):
        yy = int((y0 + (j + 0.5) * h) * MM)
        for i in range(nx):
            v = pcbnew.VECTOR2I(int((x0 + (i + 0.5) * h) * MM), yy)
            for ps in polys:
                if ps.Contains(v): cu[j, i] = True; break
            if extra is not None and cu[j, i] and extra.Contains(v): ex[j, i] = True
    return cu, ex
def poly_of(item, L):
    ps = pcbnew.SHAPE_POLY_SET(); item.TransformShapeToPolygon(ps, L, 0, 2000, pcbnew.ERROR_INSIDE); return ps
def bbox(bx): return pcbnew.BOX2I(pcbnew.VECTOR2I(int(bx[0] * MM), int(bx[1] * MM)), pcbnew.VECTOR2I(int((bx[2] - bx[0]) * MM), int((bx[3] - bx[1]) * MM)))
L = pcbnew.F_Cu; fbox = bbox(FB); polys = []; pin = None; vias = []
for z in b.Zones():
    if z.GetIsRuleArea() or str(z.GetNetname()) != 'GND' or not z.IsOnLayer(L) or not z.HasFilledPolysForLayer(L): continue
    if z.GetBoundingBox().Intersects(fbox): polys.append(z.GetFilledPolysList(L))
for f in b.GetFootprints():
    for p in f.Pads():
        if str(p.GetNetname()) == 'GND' and p.IsOnLayer(L) and p.GetBoundingBox().Intersects(fbox):
            polys.append(poly_of(p, L))
            if f.GetReference() == 'U4' and p.GetNumber() == '27': pin = p
for t in b.GetTracks():
    if str(t.GetNetname()) != 'GND' or not t.GetBoundingBox().Intersects(fbox): continue
    if t.GetClass() == 'PCB_VIA': vias.append((t.GetX() / MM, t.GetY() / MM, t.GetWidth(L) / MM, t.GetDrillValue() / MM)); polys.append(poly_of(t, L))
    elif t.IsOnLayer(L): polys.append(poly_of(t, L))
cuF, src = raster(FB, H, polys, poly_of(pin, L))
# keep copper connected to the pin
from collections import deque
lab = src.copy(); q = deque(zip(*np.nonzero(src))); nyF, nxF = cuF.shape
while q:
    j, i = q.popleft()
    for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        a, c = j + dj, i + di
        if 0 <= a < nyF and 0 <= c < nxF and cuF[a, c] and not lab[a, c]: lab[a, c] = True; q.append((a, c))
cuF = lab
jj, ii = np.mgrid[0:nyF, 0:nxF]; XF = FB[0] + (ii + 0.5) * H; YF = FB[1] + (jj + 0.5) * H
VS = []
for (x, y, d, dr) in vias:
    m = ((XF - x) ** 2 + (YF - y) ** 2 <= (d / 2) ** 2) & cuF
    if m.sum(): VS.append((x, y, d, dr, m, 1.0 / (1.72e-5 * LB / (math.pi * (dr + T) * T))))
def lap_parts(cu):
    cE = cu[:, :-1] & cu[:, 1:]; cS = cu[:-1, :] & cu[1:, :]; return cE, cS
def lap(v, cE, cS, g):
    r = np.zeros_like(v)
    d = (v[:, :-1] - v[:, 1:]) * cE * g; r[:, :-1] += d; r[:, 1:] -= d
    d = (v[:-1, :] - v[1:, :]) * cS * g; r[:-1, :] += d; r[1:, :] -= d
    return r
def cg(Aop, rhs, Mdiag, tol=1e-10, maxit=40000):
    x = np.zeros_like(rhs); r = rhs - Aop(x); z = Mdiag * r; p = z.copy(); rz = (r * z).sum(); n0 = math.sqrt((rhs * rhs).sum())
    for it in range(maxit):
        Ap = Aop(p); al = rz / (p * Ap).sum(); x += al * p; r -= al * Ap
        if math.sqrt((r * r).sum()) < tol * n0: break
        z = Mdiag * r; rz2 = (r * z).sum(); p = z + rz2 / rz * p; rz = rz2
    return x, it
results = {}
cEF, cSF = lap_parts(cuF); gF = 1.0 / RSF
rhsF = np.zeros(cuF.shape); rhsF[src] = I / src.sum()
# ---- model ideal
gnd = np.zeros(cuF.shape)
for (x, y, d, dr, m, gb) in VS: gnd[m] += gb / m.sum()
diag = gnd + gF * (np.pad(cEF, ((0, 0), (0, 1))) + np.pad(cEF, ((0, 0), (1, 0))) + np.pad(cSF, ((0, 1), (0, 0))) + np.pad(cSF, ((1, 0), (0, 0))))
Mi = np.where(diag > 0, 1.0 / np.where(diag > 0, diag, 1), 0)
vF, it = cg(lambda v: (lap(v, cEF, cSF, gF) + gnd * v) * cuF, rhsF, Mi)
results['ideal'] = ([float((gb / m.sum() * vF * m).sum()) for (x, y, d, dr, m, gb) in VS], float(vF[src].mean()))
import os
if os.environ.get('PGND_MODEL','both')=='ideal':
    VS2=[(x,y,d,dr) for (x,y,d,dr,m,gb) in VS]; res=sorted(zip(results['ideal'][0],VS2),key=lambda t:-t[0])
    print('ideal R %.3f mOhm' % (results['ideal'][1]/I*1e3)); [print('  via %.3f,%.3f %.2f/%.2f %.3f A load %.2f' % (v[0],v[1],v[2],v[3],a,a/(v[3]/0.3))) for a,v in res if a>0.002]; sys.exit(0)
# ---- model plane: unknowns F grid + In1 grid; via k = conductance gb between mean of its F land and mean of its In1 contact cells
L1 = pcbnew.In1_Cu; pl = [z.GetFilledPolysList(L1) for z in b.Zones() if not z.GetIsRuleArea() and str(z.GetNetname()) == 'GND' and z.IsOnLayer(L1) and z.HasFilledPolysForLayer(L1)]
cuI, _ = raster(PB, H2, pl); nyI, nxI = cuI.shape
fixed = np.zeros(cuI.shape, bool); fixed[0, :] = fixed[-1, :] = fixed[:, 0] = fixed[:, -1] = True; freeI = cuI & ~fixed
jI, iI = np.mgrid[0:nyI, 0:nxI]; XI = PB[0] + (iI + 0.5) * H2; YI = PB[1] + (jI + 0.5) * H2
cEI, cSI = lap_parts(cuI); gI = 1.0 / RSI
couple = []
for (x, y, d, dr, m, gb) in VS:
    mi = ((XI - x) ** 2 + (YI - y) ** 2 <= (dr / 2 + T + H2 / 2) ** 2) & cuI
    # each F land cell and each In1 cell tied through a star of conductances whose series total is the barrel
    couple.append((m, mi, gb))
nF = cuF.size
def split(v): return v[:nF].reshape(cuF.shape), v[nF:].reshape(cuI.shape)
def Aop(v):
    a, c = split(v); ra = lap(a, cEF, cSF, gF); rc = lap(c, cEI, cSI, gI)
    for (m, mi, gb) in couple:
        # barrel as conductance gb between land-average and contact-average (lumped node eliminated: rank-1 coupling)
        va = a[m].mean(); vc = c[mi].mean(); f = gb * (va - vc)
        ra[m] += f / m.sum(); rc[mi] -= f / mi.sum()
    return np.concatenate([(ra * cuF).ravel(), (rc * freeI).ravel()])
dA = gF * (np.pad(cEF, ((0, 0), (0, 1))) + np.pad(cEF, ((0, 0), (1, 0))) + np.pad(cSF, ((0, 1), (0, 0))) + np.pad(cSF, ((1, 0), (0, 0))))
dC = gI * (np.pad(cEI, ((0, 0), (0, 1))) + np.pad(cEI, ((0, 0), (1, 0))) + np.pad(cSI, ((0, 1), (0, 0))) + np.pad(cSI, ((1, 0), (0, 0))))
Md = np.concatenate([np.where(dA > 0, 1 / np.where(dA > 0, dA, 1), 0).ravel(), np.where((dC > 0) & freeI, 1 / np.where(dC > 0, dC, 1), 0).ravel()])
rhs = np.concatenate([rhsF.ravel(), np.zeros(cuI.size)])
v, it2 = cg(Aop, rhs, Md, tol=1e-9)
a, c = split(v)
results['plane'] = ([gb * (a[m].mean() - c[mi].mean()) for (m, mi, gb) in couple], float(a[src].mean()))
rows = []
for k, (x, y, d, dr, m, gb) in enumerate(VS):
    rule = dr / 0.3; amil = math.pi * (dr + T) * T / 0.0254 ** 2; ipc = 0.048 * 15 ** 0.44 * amil ** 0.725
    rows.append({'x': x, 'y': y, 'd': d, 'drill': dr, 'A_ideal': round(results['ideal'][0][k], 3), 'A_plane': round(results['plane'][0][k], 3), 'rule_A': round(rule, 2), 'ipc15K_A': round(ipc, 2)})
rows = [r for r in rows if max(r['A_ideal'], r['A_plane']) > 0.002]; rows.sort(key=lambda r: -r['A_ideal'])
print('board', sys.argv[1], 'I %.2f A, F cells %d, In1 cells %d, CG it %d / %d' % (I, cuF.sum(), cuI.sum(), it, it2))
for k in ('ideal', 'plane'):
    s = sum(results[k][0]); print(' model %-5s sum via current %.3f A, pin-27 land to %s %.3f mOhm' % (k, s, 'In1' if k == 'ideal' else 'In1 box edge', results[k][1] / I * 1e3))
for r in rows: print('  via %.3f,%.3f %.2f/%.2f  ideal %.3f A  plane %.3f A  rule %.2f A  IPC15K %.2f A' % (r['x'], r['y'], r['d'], r['drill'], r['A_ideal'], r['A_plane'], r['rule_A'], r['ipc15K_A']))
if out: json.dump({'I': I, 'R_ideal_mohm': results['ideal'][1] / I * 1e3, 'R_plane_mohm': results['plane'][1] / I * 1e3, 'vias': rows}, open(out, 'w'), indent=1)
