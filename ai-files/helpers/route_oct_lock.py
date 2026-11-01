"""route_oct_lock.py : canonical hash of the copper (segments, arcs, vias) of a set of nets in a .kicad_pcb (plain text parse).
Used to lock finished stages (rule OR3 / AG R-A3): the manifest stores the hash, later stages recompute and compare.
  python3 route_oct_lock.py BOARD.kicad_pcb NETFILE_OR_COMMA_LIST
"""
import re, sys, hashlib

BLK = re.compile(r'^\t\((segment|arc|via)$')


def copper_items(path, nets):
    nets = set(nets); lines = open(path, encoding='utf-8').read().split('\n'); out = []; i = 0
    while i < len(lines):
        m = BLK.match(lines[i])
        if not m:
            i += 1; continue
        j = i + 1
        while lines[j] != '\t)':
            j += 1
        blk = lines[i + 1:j]; d = {}
        for b in blk:
            mm = re.match(r'^\t\t\((start|end|mid|at|width|size|drill|layer|layers|net) (.*)\)$', b)
            if mm:
                d[mm.group(1)] = mm.group(2)
        net = d.get('net', '').strip('"')
        d = {k: ' '.join(('%.6f' % float(x)) if re.match(r'^-?[\d.]+$', x) else x for x in v.split()) for k, v in d.items()}
        if net in nets:
            out.append((m.group(1), net, d.get('start', d.get('at', '')), d.get('end', ''), d.get('mid', ''), d.get('width', d.get('size', '')),
                        d.get('drill', ''), d.get('layer', d.get('layers', ''))))
        i = j + 1
    return sorted(out)


def copper_hash(path, nets):
    items = copper_items(path, nets)
    h = hashlib.sha256('\n'.join('|'.join(t) for t in items).encode()).hexdigest()
    return h, len(items)


if __name__ == '__main__':
    arg = sys.argv[2]
    nets = arg.split(',') if ',' in arg or arg.startswith('/') else [l.split()[1] if len(l.split()) > 1 else l.strip() for l in open(arg) if l.strip() and not l.startswith('#')]
    print(copper_hash(sys.argv[1], nets))
