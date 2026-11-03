"""pcbtext.py : plain-text access to top-level segment / arc / via / zone blocks of a .kicad_pcb (no pcbnew).
items(path) -> list of dicts: kind, i0, i1 (line range), uuid, net, layer, width, start, end, at, size, drill, name, pts (zone outline)."""
import re

NUM = r'(-?[\d.]+)'


def read(path):
    return open(path, encoding='utf-8').read().split('\n')


def blocks(lines):
    i = 0
    while i < len(lines):
        m = re.match(r'^\t\((segment|arc|via|zone|footprint)(?: |$)', lines[i])
        if not m:
            i += 1; continue
        if lines[i].count('(') == lines[i].count(')'):
            yield m.group(1), i, i; i += 1; continue
        j = i + 1
        while lines[j] != '\t)':
            j += 1
        yield m.group(1), i, j
        i = j + 1


def parse_item(kind, lines, i0, i1):
    d = dict(kind=kind, i0=i0, i1=i1)
    T = lines[i0:i1 + 1]
    for L in T:
        s = L.strip()
        m = re.match(r'^\(uuid "([^"]+)"\)$', s)
        if m and L.startswith('\t\t(') and not L.startswith('\t\t\t'): d['uuid'] = m.group(1)
        if not (L.startswith('\t\t(') and not L.startswith('\t\t\t')): continue
        m = re.match(r'^\(net "([^"]*)"\)$', s)
        if m: d['net'] = m.group(1)
        m = re.match(r'^\(layer "([^"]+)"\)$', s)
        if m: d['layer'] = m.group(1)
        m = re.match(r'^\(layers (.*)\)$', s)
        if m: d['layers'] = re.findall(r'"([^"]+)"', m.group(1))
        m = re.match(r'^\(width ' + NUM + r'\)$', s)
        if m: d['width'] = float(m.group(1))
        for k in ('start', 'end', 'mid', 'at'):
            m = re.match(r'^\(' + k + ' ' + NUM + ' ' + NUM + r'(?: ' + NUM + r')?\)$', s)
            if m: d[k] = (float(m.group(1)), float(m.group(2)))
        m = re.match(r'^\(size ' + NUM + r'\)$', s)
        if m: d['size'] = float(m.group(1))
        m = re.match(r'^\(drill ' + NUM + r'\)$', s)
        if m: d['drill'] = float(m.group(1))
        m = re.match(r'^\(name "([^"]*)"\)$', s)
        if m: d['name'] = m.group(1)
    if kind == 'zone':
        txt = '\n'.join(T)
        d['teardrop'] = '(teardrop' in txt
        # outline polygon: the (polygon (pts ...)) block at depth 2
        k = next((k for k in range(i0, i1 + 1) if lines[k] == '\t\t(polygon'), None)
        if k is not None:
            e = k + 1
            while lines[e] != '\t\t)': e += 1
            d['poly_lines'] = (k, e)
            d['pts'] = [(float(a), float(b)) for a, b in re.findall(r'\(xy ' + NUM + ' ' + NUM + r'\)', '\n'.join(lines[k:e + 1]))]
    return d


def items(path, lines=None, kinds=('segment', 'arc', 'via', 'zone')):
    lines = lines or read(path)
    return [parse_item(k, lines, a, b) for k, a, b in blocks(lines) if k in kinds]


def fmt(v):
    s = ('%.6f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s
