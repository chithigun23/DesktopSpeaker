"""python3: route_r6j_u6fan.py THETA_DEG Y_S1 OFF_SDA OFF_SCL OUT.json : (R6j) generator for the U6 SCL/SDA/SDATA/BCK/LRCK re-fan + LRCK lane + via nudges (spec r6j/a2.json)"""
import math, json, sys
th = math.radians(float(sys.argv[1]) if len(sys.argv) > 1 else 60)
d1 = (math.cos(th), -math.sin(th)); nw1 = (-math.sin(th), -math.cos(th))   # seg1 dir, NW normal
O = (113.55, 119.95); u = (0.842, -0.539); un = math.hypot(*u); u = (u[0]/un, u[1]/un); n = (-u[1], u[0])  # n = SE normal (0.539,0.842)
def yold(x, d=0.0):   # point on old BCK line offset d (SE positive) at x
    # line: O + t u + d n
    t = (x - O[0] - d*n[0]) / u[0]; return O[1] + t*u[1] + d*n[1]
def inter(p, dv, d):   # intersect line p + s dv with old line offset d
    # solve (p + s dv - O) . n = d
    s = (d - ((p[0]-O[0])*n[0] + (p[1]-O[1])*n[1])) / (dv[0]*n[0] + dv[1]*n[1]); return (p[0]+s*dv[0], p[1]+s*dv[1])
def corner(prev_corner, x, off):   # line parallel to seg1 through prev_corner shifted off NW, evaluated at x
    q = (prev_corner[0] + off*nw1[0], prev_corner[1] + off*nw1[1]); return (x, q[1] + (q[0]-x)*math.tan(th))
S = 0.47; XA, XB = 115.5, 124.0
Lc = (110.0, 125.0); BL = inter(Lc, d1, 0.0)
Q1 = (XA, yold(XA, 0)); Q2 = (XB, yold(XB, S)); Q3 = (O[0]+30.5*u[0]+S*n[0], O[1]+30.5*u[1]+S*n[1])
Bc = corner(Lc, 109.5, S); Bb = inter(Bc, d1, -S); R1 = (XA, yold(XA, -S)); R2 = (XB, yold(XB, 0))
Dc = corner(Bc, 109.0, S)
SA = 0.645; Ac = corner(Dc, 108.37, SA)
SC = 0.42; Cc = corner(Ac, 107.93, SC)
def online(c, y): return (c[0] + (c[1]-y)/math.tan(th), y)
yS1 = float(sys.argv[2]) if len(sys.argv) > 2 else 118.6
S1 = online(Dc, yS1)
def lint(p, dv, q, dw):
    den = dv[0]*dw[1] - dv[1]*dw[0]; s = ((q[0]-p[0])*dw[1] - (q[1]-p[1])*dw[0]) / den; return (p[0]+s*dv[0], p[1]+s*dv[1])
def unit(a, b):
    l = math.hypot(b[0]-a[0], b[1]-a[1]); return ((b[0]-a[0])/l, (b[1]-a[1])/l)
def offl(a, b, off):   # point a shifted NW (left of travel a->b) by off
    dv = unit(a, b); nl = (dv[1], -dv[0]); return (a[0]+off*nl[0], a[1]+off*nl[1]), dv
V = (118.9, 113.6)
qa, dva = offl(S1, V, float(sys.argv[3]) if len(sys.argv) > 3 else 0.68); S2 = lint(Ac, d1, qa, dva)
EA = (118.62, 112.6)
qc, dvc = offl(S2, EA, float(sys.argv[4]) if len(sys.argv) > 4 else 0.44); S3 = lint(Cc, d1, qc, dvc)
r = lambda p: [round(p[0], 3), round(p[1], 3)]
spec = [
 {"rmseg": "/AUD_SCL", "a": [108.005,126.395], "b": [107.93,125.6]},
 {"rmseg": "/AUD_SCL", "a": [107.93,125.6], "b": [107.93,123.24]},
 {"rmseg": "/AUD_SCL", "a": [107.93,123.24], "b": [118.46,112.15]},
 {"rmseg": "/AUD_SCL", "a": [118.46,112.15], "b": [123.65,112.45]},
 {"rmseg": "/AUD_SDA", "a": [108.505,126.395], "b": [108.37,125.0]},
 {"rmseg": "/AUD_SDA", "a": [108.37,125.0], "b": [108.37,123.39]},
 {"rmseg": "/AUD_SDA", "a": [108.37,123.39], "b": [118.62,112.6]},
 {"rmseg": "/I2S_SDATA", "a": [109.0,126.39], "b": [109.0,124.51]},
 {"rmseg": "/I2S_SDATA", "a": [109.0,124.51], "b": [109.0,124.45]},
 {"rmseg": "/I2S_SDATA", "a": [109.0,124.45], "b": [113.4,119.1]},
 {"rmseg": "/I2S_SDATA", "a": [113.4,119.1], "b": [118.9,113.6]},
 {"rmseg": "/I2S_BCK", "a": [109.5,126.39], "b": [109.55,124.85]},
 {"rmseg": "/I2S_BCK", "a": [109.55,124.85], "b": [113.55,119.95]},
 {"rmseg": "/I2S_BCK", "a": [113.55,119.95], "b": [147.0,98.5]},
 {"rmseg": "GND", "a": [114.06,121.16], "b": [114.49,120.12]},
 {"rmvia": "GND", "p": [114.49,120.12]},
 {"net": "GND", "via": [114.55,120.2], "d": 0.6, "drill": 0.3},
 {"net": "GND", "layer": "F", "w": 0.3, "pts": [[114.06,121.16],[114.55,120.2]]},
 {"net": "/AUD_SCL", "layer": "F", "w": 0.2, "pts": [[108.005,126.395], r(Cc), r(S3), [118.37,112.07], [123.65,112.45]]},
 {"net": "/AUD_SDA", "layer": "F", "w": 0.2, "pts": [[108.505,126.395], [108.37,125.0], r(Ac), r(S2), [118.62,112.6]]},
 {"net": "/I2S_SDATA", "layer": "F", "w": 0.25, "pts": [[109.005,126.395], r(Dc), r(S1), [118.9,113.6]]},
 {"net": "/I2S_BCK", "layer": "F", "w": 0.25, "pts": [[109.505,126.395], r(Bc), r(Bb), r(R1), r(R2), [147.0,98.5]]},
 {"net": "/I2S_LRCK", "layer": "F", "w": 0.25, "pts": [[110.005,126.395], r(Lc), r(BL), r(Q1), r(Q2), r(Q3), [140.2,103.9]]},
 {"rmvia": "/AUD_SDA", "p": [125.65,113.25]},
 {"rmseg": "/AUD_SDA", "a": [120.9,113.45], "b": [125.65,113.25]},
 {"rmseg": "/AUD_SDA", "a": [125.65,113.25], "b": [124.2,111.8]},
 {"rmseg": "/AUD_SDA", "a": [129.5,116.85], "b": [125.65,113.25]},
 {"net": "/AUD_SDA", "via": [125.9,113.75], "d": 0.6, "drill": 0.3},
 {"net": "/AUD_SDA", "layer": "B", "w": 0.2, "pts": [[120.9,113.45],[125.9,113.75]]},
 {"net": "/AUD_SDA", "layer": "B", "w": 0.25, "pts": [[124.2,111.8],[125.9,113.75]]},
 {"net": "/AUD_SDA", "layer": "2", "w": 0.25, "pts": [[125.9,113.75],[129.5,116.85]]},
 {"rmvia": "/CTRL_SDA", "p": [126.55,113.1]},
 {"rmseg": "/CTRL_SDA", "a": [126.55,113.1], "b": [125.0,111.55]},
 {"rmseg": "/CTRL_SDA", "a": [129.8,116.35], "b": [126.55,113.1]},
 {"net": "/CTRL_SDA", "via": [126.6,113.18], "d": 0.6, "drill": 0.3},
 {"net": "/CTRL_SDA", "layer": "B", "w": 0.25, "pts": [[126.6,113.18],[125.0,111.55]]},
 {"net": "/CTRL_SDA", "layer": "2", "w": 0.25, "pts": [[129.8,116.35],[126.6,113.18]]},
 {"rmvia": "/CTRL_SCL", "p": [135.5,107.2]},
 {"rmseg": "/CTRL_SCL", "a": [135.5,107.2], "b": [149.05,111.65]},
 {"rmseg": "/CTRL_SCL", "a": [131.15,107.2], "b": [135.5,107.2]},
 {"net": "/CTRL_SCL", "layer": "B", "w": 0.25, "pts": [[131.15,107.2],[149.05,111.65]]},
 {"rmvia": "/5V_LOGIC_EN", "p": [139.6,104.75]},
 {"rmseg": "/5V_LOGIC_EN", "a": [139.6,104.75], "b": [140.8,105.15]},
 {"rmseg": "/5V_LOGIC_EN", "a": [135.65,104.75], "b": [139.6,104.75]},
 {"net": "/5V_LOGIC_EN", "via": [139.7,104.79], "d": 0.6, "drill": 0.3},
 {"net": "/5V_LOGIC_EN", "layer": "F", "w": 0.2, "pts": [[139.7,104.79],[140.8,105.15]]},
 {"net": "/5V_LOGIC_EN", "layer": "B", "w": 0.25, "pts": [[135.65,104.75],[139.7,104.79]]},
]
json.dump(spec, open(sys.argv[5] if len(sys.argv) > 5 else 'a2.json', 'w'), indent=0)
for k, v in dict(Lc=Lc, BL=BL, Q1=Q1, Q2=Q2, Bc=Bc, Bb=Bb, R1=R1, R2=R2, Dc=Dc, S1=S1, Ac=Ac, S2=S2, Cc=Cc, S3=S3).items(): print(k, r(v))
