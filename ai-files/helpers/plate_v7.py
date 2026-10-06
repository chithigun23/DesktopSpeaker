"""Ritz plate model (free edges, point supports by penalty springs) of the PCB on its standoffs: fundamental frequencies.
usage: python3 plate_v7.py [layout.json]   (board-centred u,v frame; masses in g, estimates stated in the v7 report)"""
import json, sys, numpy as np
L = json.load(open(sys.argv[1] if len(sys.argv) > 1 else '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/layout.json'))
B = L['board']; a, b = B['w'], B['d']; u0, v0 = B['u0'], B['v0']
E, nu, h = 18e9, 0.17, 1.6e-3
D = E * h ** 3 / (12 * (1 - nu ** 2))
MASS = {'L201': 4.5, 'L202': 4.5, 'L203': 4.5, 'L204': 4.5, 'L205': 4.5, 'L206': 4.5, 'L200': 3.0, 'L1': 3.0, 'C275': 2.0, 'J9': 2.0, 'J10': 2.0, 'J11': 2.0,
        'J5': 3.0, 'J1': 2.0, 'J2': 3.0, 'J3': 3.0, 'U1': 1.5, 'SW101': 5.0, 'J7': 1.0}
rho_a = (a * b * 1e-6 * h * 1900 + 0.035) / (a * b * 1e-6)           # FR4+Cu 1900 kg/m3, plus 35 g of small parts spread uniformly [kg/m2]
M = 14
gx, gy = np.meshgrid((np.arange(0, a, 1.0) + .5), (np.arange(0, b, 1.0) + .5)); dA = 1e-6
def basis(x, y):
    out = []
    for m in range(M):
        for n in range(M):
            kx, ky = m * np.pi / (a), n * np.pi / (b)
            out.append((np.cos(kx * x) * np.cos(ky * y), -kx * kx * np.cos(kx * x) * np.cos(ky * y), -ky * ky * np.cos(kx * x) * np.cos(ky * y), kx * ky * np.sin(kx * x) * np.sin(ky * y)))
    return out
Bq = basis(gx, gy)
P = np.array([q[0].ravel() for q in Bq]); XX = np.array([q[1].ravel() for q in Bq]); YY = np.array([q[2].ravel() for q in Bq]); XY = np.array([q[3].ravel() for q in Bq])
K0 = D * dA * ((XX + YY) @ (XX + YY).T - (1 - nu) * (XX @ YY.T + YY @ XX.T - 2 * XY @ XY.T)) * 1e6 ** 0 * 1e6   # mm -> m: derivs per mm^2 -> per m^2 (x1e6 per factor, two factors 1e12), area mm2->m2 1e-6
K0 = D * ((XX + YY) @ (XX + YY).T - (1 - nu) * (XX @ YY.T + YY @ XX.T - 2 * XY @ XY.T)) * 1e12 * 1e-6
M0 = rho_a * (P @ P.T) * 1e-6
def at(x, y): return np.array([q[0] for q in basis(np.array(x), np.array(y))]).ravel()
def run(holes, label):
    K, Mm = K0.copy(), M0.copy()
    for ref, g in MASS.items():
        if ref in L['parts']:
            r = L['parts'][ref]['rect']; x, y = (r[0] + r[2]) / 2 - u0, (r[1] + r[3]) / 2 - v0
            f = at(x, y); Mm += g * 1e-3 * np.outer(f, f)
    kp = 1e3 * np.max(np.diag(K))
    for hu, hv in holes:
        f = at(hu - u0, hv - v0); K += kp * np.outer(f, f)
    w = np.sort(np.real(np.linalg.eigvals(np.linalg.solve(Mm, K))))
    w = w[w > 1]
    print('%-34s supports %2d  f1..f3 = %6.0f %6.0f %6.0f Hz' % (label, len(holes), *(np.sqrt(w[:3]) / 2 / np.pi)))
if __name__ == '__main__':
    H = [(h['u'], h['v']) for h in L['holes']]
    cor = [(u0 + 4, v0 + 4), (-u0 - 4, v0 + 4), (u0 + 4, -v0 - 4), (-u0 - 4, -v0 - 4)]
    run(cor, '4 corner holes (v6-like)')
    run(H, 'v7 holes (%d)' % len(H))
    run(H[:max(len(H) - 3, 4)], 'v7 minus 3 holes')
    # span: farthest board point from a hole
    gxs, gys = np.meshgrid(np.arange(u0 + 1, -u0, 2.0), np.arange(v0 + 1, -v0, 2.0))
    d = np.min([np.hypot(gxs - hu, gys - hv) for hu, hv in H], axis=0)
    print('max distance board point -> hole %.1f mm' % d.max())
    for ref in ('L200', 'L201', 'L202', 'L203', 'L204', 'L205', 'L206', 'L1', 'C275', 'J1', 'J5', 'J9', 'J10', 'J11', 'U1'):
        if ref in L['parts']:
            r = L['parts'][ref]['rect']; c = ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
            print(ref, 'to nearest hole centre %.1f mm' % min(np.hypot(c[0] - hu, c[1] - hv) for hu, hv in H))
