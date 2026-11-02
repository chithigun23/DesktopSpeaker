#!/usr/bin/env python3
"""mkplan.py : helpers to build edit.py plans by coordinates (uuid lookup in the board text).
  from mkplan import P ; p = P('board.kicad_pcb') ; p.seg_del_at(net, x1,y1,x2,y2) ; p.via_del_at(net,x,y) ; p.via_set_at(net,x,y,nx,ny)
  p.seg(layer, net, w, pts...) adds a polyline ; p.via(net, x, y, d, dr) ; p.move(ref, x, y, rot) ; p.save(path)"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcbtext import read, items


class P:
    def __init__(s, board):
        s.IT = items(board, read(board))
        s.plan = dict(seg_del=[], seg_set={}, seg_add=[], via_del=[], via_set={}, via_add=[], fp_move={}, zone_pts={})

    def _seg(s, net, x1, y1, x2, y2, tol=0.02):
        m = [d for d in s.IT if d['kind'] == 'segment' and d.get('net') == net and
             ((math.dist(d['start'], (x1, y1)) < tol and math.dist(d['end'], (x2, y2)) < tol) or
              (math.dist(d['start'], (x2, y2)) < tol and math.dist(d['end'], (x1, y1)) < tol))]
        if len(m) != 1: raise SystemExit('seg %s (%.3f,%.3f)-(%.3f,%.3f) matches %d' % (net, x1, y1, x2, y2, len(m)))
        return m[0]

    def _via(s, net, x, y, tol=0.02):
        m = [d for d in s.IT if d['kind'] == 'via' and d.get('net') == net and math.dist(d['at'], (x, y)) < tol]
        if len(m) != 1: raise SystemExit('via %s (%.3f,%.3f) matches %d' % (net, x, y, len(m)))
        return m[0]

    def seg_del_at(s, net, x1, y1, x2, y2):
        s.plan['seg_del'].append(s._seg(net, x1, y1, x2, y2)['uuid'])

    def seg_set_at(s, net, x1, y1, x2, y2, n):
        s.plan['seg_set'][s._seg(net, x1, y1, x2, y2)['uuid']] = list(n)

    def via_del_at(s, net, x, y):
        s.plan['via_del'].append(s._via(net, x, y)['uuid'])

    def via_set_at(s, net, x, y, nx, ny):
        s.plan['via_set'][s._via(net, x, y)['uuid']] = [nx, ny]

    def seg(s, layer, net, w, *pts):
        for a, b in zip(pts, pts[1:]):
            s.plan['seg_add'].append([layer, net, w, a[0], a[1], b[0], b[1]])

    def via(s, net, x, y, d=0.6, dr=0.3):
        s.plan['via_add'].append([net, x, y, d, dr])

    def move(s, ref, x, y, rot=None):
        s.plan['fp_move'][ref] = [x, y] + ([rot] if rot is not None else [])

    def save(s, path):
        json.dump(s.plan, open(path, 'w'), indent=1)
        print('plan', path, {k: len(v) for k, v in s.plan.items()})
