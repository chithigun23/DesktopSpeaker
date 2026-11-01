// route_oct_core.c : exact-octilinear A* router core for route_oct.py
// Build: gcc -O2 -shared -fPIC -o route_oct_core.so route_oct_core.c -lm
//
// Grid: cell centres on a square lattice (window coordinates, integer x,y). Two routing layers (NL<=4).
// State = (layer, y, x, dir) with dir 0..7 (0=+x, 1=+x+y, 2=+y, 3=-x+y, 4=-x, 5=-x-y, 6=-y, 7=+x-y; y grows downwards like KiCad).
// Moves:
//   straight : one cell along dir
//   turn     : dir -> dir+-1 (45 deg only) followed by a forced straight run of Lmin cells (Lmin_o orthogonal, Lmin_d diagonal),
//              so the segment between two bends is never shorter than Lmin (bend spacing by construction)
//   via      : change layer at a via-ok cell, then a forced straight run of Lmin cells in any of the 8 directions
// No 90 or 135 degree turn exists as a move, so every corner away from pads/vias is a 45 degree mitre.
// Costs: step length (1 or sqrt2) * cost[cell] * dircost[layer*8+dir]; + turn_cost per 45 deg bend; + via_cost per via.
// Targets: tgt[cell] bit d (low byte) = state (cell,d) is a goal; bit 8+d = goal also reachable in the middle of a forced run
// (only used for straight arrivals into a pad stub).
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>

static const int DX[8] = {1, 1, 0, -1, -1, -1, 0, 1};
static const int DY[8] = {0, 1, 1, 1, 0, -1, -1, -1};

typedef struct { float f; float g; int32_t s; } HN;
typedef struct { HN *a; int64_t n, cap; } Heap;
static void hpush(Heap *h, float f, float g, int32_t s) {
  if (h->n >= h->cap) { h->cap = h->cap ? h->cap * 2 : (1 << 16); h->a = realloc(h->a, h->cap * sizeof(HN)); }
  int64_t i = h->n++;
  while (i > 0) { int64_t p = (i - 1) / 2;
    // tie-break: larger g first (deeper)
    if (h->a[p].f < f || (h->a[p].f == f && h->a[p].g >= g)) break;
    h->a[i] = h->a[p]; i = p; }
  h->a[i].f = f; h->a[i].g = g; h->a[i].s = s;
}
static HN hpop(Heap *h) {
  HN top = h->a[0]; HN l = h->a[--h->n]; int64_t i = 0;
  for (;;) { int64_t c = 2 * i + 1; if (c >= h->n) break;
    if (c + 1 < h->n && (h->a[c + 1].f < h->a[c].f || (h->a[c + 1].f == h->a[c].f && h->a[c + 1].g > h->a[c].g))) c++;
    if (h->a[c].f > l.f || (h->a[c].f == l.f && h->a[c].g <= l.g)) break;
    h->a[i] = h->a[c]; i = c; }
  h->a[i] = l; return top;
}

static int W_, H_, NL_; static const int32_t *HP_; static int NH_; static float HM_;
static int bx0_, by0_, bx1_, by1_;
static inline float octile(int dx, int dy) { dx = abs(dx); dy = abs(dy); return dx > dy ? (dx - dy) + 1.41421356f * dy : (dy - dx) + 1.41421356f * dx; }
static inline float heur(int y, int x) {
  if (NH_ <= 48) { float b = 1e30f; for (int i = 0; i < NH_; i++) { float d = octile(x - HP_[2 * i + 1], y - HP_[2 * i]); if (d < b) b = d; } return HM_ * b; }
  int dx = x < bx0_ ? bx0_ - x : (x > bx1_ ? x - bx1_ : 0), dy = y < by0_ ? by0_ - y : (y > by1_ ? y - by1_ : 0);
  return HM_ * octile(dx, dy);
}

// returns number of states written to out (layer,y,x,dir quads, from start to goal), -1 no path, -2 out of memory, -3 expansion limit
int oct_astar(int W, int H, int NL, const uint8_t *free_, const float *cost, const uint8_t *viaok, const uint16_t *tgt,
              const int32_t *starts, int nstarts, const float *start_g, const int32_t *hpts, int nh, int Lmin_o, int Lmin_d,
              float turn_cost, float via_cost, float hmul, const float *dircost, int64_t maxexp, int32_t *out, int maxout, float *out_cost) {
  W_ = W; H_ = H; NL_ = NL; HP_ = hpts; NH_ = nh; HM_ = hmul;
  bx0_ = 1 << 30; by0_ = 1 << 30; bx1_ = -1; by1_ = -1;
  for (int i = 0; i < nh; i++) { int y = hpts[2 * i], x = hpts[2 * i + 1]; if (x < bx0_) bx0_ = x; if (x > bx1_) bx1_ = x; if (y < by0_) by0_ = y; if (y > by1_) by1_ = y; }
  int64_t HW = (int64_t)H * W, NC = (int64_t)NL * HW, NS = NC * 8;
  float *g = malloc(NS * sizeof(float)); int32_t *par = malloc(NS * sizeof(int32_t)); uint8_t *cl = calloc(NS, 1);
  if (!g || !par || !cl) { free(g); free(par); free(cl); return -2; }
  for (int64_t i = 0; i < NS; i++) g[i] = 1e30f;
  Heap h = {0};
  for (int i = 0; i < nstarts; i++) {
    int l = starts[4 * i], y = starts[4 * i + 1], x = starts[4 * i + 2], d = starts[4 * i + 3];
    int64_t s = ((l * HW) + (int64_t)y * W + x) * 8 + d; float g0 = start_g ? start_g[i] : 0.f;
    if (g0 < g[s]) { g[s] = g0; par[s] = -1; hpush(&h, g0 + heur(y, x), g0, (int32_t)s); }
  }
  int64_t nexp = 0, found = -1; int rc = -1;
  while (h.n > 0) {
    HN n = hpop(&h); int64_t s = n.s; if (cl[s]) continue; cl[s] = 1;
    int64_t c = s >> 3; int d = s & 7; float gs = g[s];
    if (tgt[c] & (1 << d)) { found = s; break; }
    if (++nexp > maxexp) { rc = -3; break; }
    int l = (int)(c / HW); int64_t r = c % HW; int y = (int)(r / W), x = (int)(r % W);
    const float *dc = dircost + l * 8;
    // 1. straight
    { int ny = y + DY[d], nx = x + DX[d];
      if (ny >= 0 && ny < H && nx >= 0 && nx < W) { int64_t nc = l * HW + (int64_t)ny * W + nx;
        if (free_[nc]) { float st = ((d & 1) ? 1.41421356f : 1.f) * cost[nc] * dc[d]; float ng = gs + st; int64_t ns = nc * 8 + d;
          if (ng < g[ns]) { g[ns] = ng; par[ns] = (int32_t)s; hpush(&h, ng + heur(ny, nx), ng, (int32_t)ns); } } } }
    // 2. 45 degree turns with forced run
    for (int t = -1; t <= 1; t += 2) {
      int nd = (d + t + 8) & 7; int L = (nd & 1) ? Lmin_d : Lmin_o; float stl = (nd & 1) ? 1.41421356f : 1.f;
      float acc = turn_cost; int ok = 1; int cy = y, cx = x;
      for (int k = 1; k <= L; k++) { cy += DY[nd]; cx += DX[nd];
        if (cy < 0 || cy >= H || cx < 0 || cx >= W) { ok = 0; break; }
        int64_t nc = l * HW + (int64_t)cy * W + cx; if (!free_[nc]) { ok = 0; break; }
        acc += stl * cost[nc] * dc[nd];
        if (k < L && (tgt[nc] & (1 << (8 + nd)))) { // straight arrival into a stub in the middle of the run
          float ng = gs + acc; int64_t ns = nc * 8 + nd;
          if (ng < g[ns]) { g[ns] = ng; par[ns] = (int32_t)s; hpush(&h, ng + heur(cy, cx), ng, (int32_t)ns); } } }
      if (ok) { int64_t nc = l * HW + (int64_t)cy * W + cx; float ng = gs + acc; int64_t ns = nc * 8 + nd;
        if (ng < g[ns]) { g[ns] = ng; par[ns] = (int32_t)s; hpush(&h, ng + heur(cy, cx), ng, (int32_t)ns); } }
    }
    // 3. via
    if (NL > 1 && viaok[r]) {
      for (int l2 = 0; l2 < NL; l2++) { if (l2 == l) continue; int64_t vc = l2 * HW + r; if (!free_[vc]) continue;
        const float *dc2 = dircost + l2 * 8;
        for (int nd = 0; nd < 8; nd++) { int L = (nd & 1) ? Lmin_d : Lmin_o; float stl = (nd & 1) ? 1.41421356f : 1.f;
          float acc = via_cost; int ok = 1; int cy = y, cx = x;
          for (int k = 1; k <= L; k++) { cy += DY[nd]; cx += DX[nd];
            if (cy < 0 || cy >= H || cx < 0 || cx >= W) { ok = 0; break; }
            int64_t nc = l2 * HW + (int64_t)cy * W + cx; if (!free_[nc]) { ok = 0; break; }
            acc += stl * cost[nc] * dc2[nd];
            if (k < L && (tgt[nc] & (1 << (8 + nd)))) { float ng = gs + acc; int64_t ns = nc * 8 + nd;
              if (ng < g[ns]) { g[ns] = ng; par[ns] = (int32_t)s; hpush(&h, ng + heur(cy, cx), ng, (int32_t)ns); } } }
          if (ok) { int64_t nc = l2 * HW + (int64_t)cy * W + cx; float ng = gs + acc; int64_t ns = nc * 8 + nd;
            if (ng < g[ns]) { g[ns] = ng; par[ns] = (int32_t)s; hpush(&h, ng + heur(cy, cx), ng, (int32_t)ns); } } }
      }
    }
  }
  int cnt = rc;
  if (found >= 0) {
    // count, then write in forward order
    int n = 0; int64_t s = found; while (s >= 0) { n++; s = par[s]; }
    if (n > maxout) cnt = -4;
    else { s = found; for (int i = n - 1; i >= 0; i--) { int64_t c = s >> 3; int l = (int)(c / HW); int64_t r = c % HW;
        out[4 * i] = l; out[4 * i + 1] = (int)(r / W); out[4 * i + 2] = (int)(r % W); out[4 * i + 3] = (int)(s & 7); s = par[s]; }
      cnt = n; if (out_cost) *out_cost = g[found]; }
  }
  free(g); free(par); free(cl); free(h.a);
  return cnt;
}

// Even-odd scanline fill of one polygon (outer ring + holes) into R (H*W uint8, value OR-ed). Coordinates in cell units
// (cell (x,y) centre at (x,y)). A centre exactly on an edge counts as inside (conservative for obstacles).
void fill_poly(uint8_t *R, int W, int H, const double *xy, const int32_t *rs, int nrings, uint8_t val) {
  double ymin = 1e30, ymax = -1e30; int npt = rs[nrings];
  for (int i = 0; i < npt; i++) { double y = xy[2 * i + 1]; if (y < ymin) ymin = y; if (y > ymax) ymax = y; }
  int y0 = (int)ceil(ymin - 1e-9), y1 = (int)floor(ymax + 1e-9); if (y0 < 0) y0 = 0; if (y1 > H - 1) y1 = H - 1;
  double *xs = malloc((npt + 4) * sizeof(double));
  for (int Y = y0; Y <= y1; Y++) {
    int nx = 0;
    for (int rr = 0; rr < nrings; rr++) { int a = rs[rr], b = rs[rr + 1];
      for (int i = a; i < b; i++) { int j = (i + 1 < b) ? i + 1 : a;
        double xa = xy[2 * i], ya = xy[2 * i + 1], xb = xy[2 * j], yb = xy[2 * j + 1];
        if ((ya <= Y && yb > Y) || (yb <= Y && ya > Y)) xs[nx++] = xa + (Y - ya) * (xb - xa) / (yb - ya); } }
    // insertion sort (small)
    for (int i = 1; i < nx; i++) { double v = xs[i]; int k = i - 1; while (k >= 0 && xs[k] > v) { xs[k + 1] = xs[k]; k--; } xs[k + 1] = v; }
    for (int k = 0; k + 1 < nx; k += 2) { int xa = (int)ceil(xs[k] - 1e-9), xb = (int)floor(xs[k + 1] + 1e-9);
      if (xa < 0) xa = 0; if (xb > W - 1) xb = W - 1; uint8_t *row = R + (int64_t)Y * W; for (int X = xa; X <= xb; X++) row[X] |= val; }
  }
  free(xs);
}
