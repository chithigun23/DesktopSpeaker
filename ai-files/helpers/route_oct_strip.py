#!/usr/bin/env python3
"""route_oct_strip.py IN.kicad_pcb OUT.kicad_pcb (--nets FILE | --all-signals PRO.kicad_pro) [--list OUT.txt]
Text-level removal of segments, arcs, vias and teardrop zones of the selected nets (pcbnew Remove() + refill segfaults here).
--nets FILE        : one net name per line ('#' comments; lines like 'S1: /I2S_BCK' are accepted, the stage prefix is ignored)
--all-signals PRO  : every net whose net class (from the .kicad_pro patterns) is Default/SIGNAL/I2C/I2S_CLK/USB/AUDIO,
                     that is not GND, has at least 2 pads, and whose existing tracks are all <= 0.35 mm wide.
Plain python3 (no third-party modules). Writes the stripped net list with --list.
"""
import sys, re, json, fnmatch, collections

SIGNAL_CLASSES = {'Default', 'SIGNAL', 'I2C', 'I2S_CLK', 'USB', 'AUDIO'}


def read_netfile(path):
    out = []
    for L in open(path, encoding='utf-8'):
        L = L.split('#', 1)[0].strip()
        if not L:
            continue
        t = L.replace(':', ' ', 1).split() if re.match(r'^S\d+:', L) else L.split()
        out.append(t[1] if re.match(r'^S\d+$', t[0]) and len(t) > 1 else t[0])
    return out


def blocks(lines):
    """yield (kind, start, end) for top-level segment/arc/via/zone blocks"""
    i = 0
    while i < len(lines):
        m = re.match(r'^\t\((segment|arc|via|zone)$', lines[i])
        if m:
            j = i + 1
            while lines[j] != '\t)':
                j += 1
            yield m.group(1), i, j
            i = j + 1
        else:
            i += 1


def net_of(blk):
    for b in blk[:60]:
        mm = re.match(r'^\t\t\(net "((?:[^"\\]|\\.)*)"\)', b) or re.match(r'^\t\t\(net_name "((?:[^"\\]|\\.)*)"\)', b)
        if mm:
            return mm.group(1)
    return None


def all_signals(lines, pro):
    pats = json.load(open(pro))['net_settings']['netclass_patterns']

    def cls(n):
        for p in pats:
            if fnmatch.fnmatchcase(n, p['pattern']):
                return p['netclass']
        return 'Default'
    pads = collections.Counter(); maxw = collections.defaultdict(float)
    for L in lines:
        m = re.match(r'^\t\t\t\(net "((?:[^"\\]|\\.)*)"\)', L)
        if m:
            pads[m.group(1)] += 1   # pad net lines are indented three tabs inside footprints
    for kind, i, j in blocks(lines):
        if kind in ('segment', 'arc'):
            blk = lines[i:j + 1]; n = net_of(blk)
            for b in blk:
                mw = re.match(r'^\t\t\(width ([\d.]+)\)', b)
                if mw:
                    maxw[n] = max(maxw[n], float(mw.group(1)))
    return sorted(n for n in pads if n != 'GND' and pads[n] >= 2 and cls(n) in SIGNAL_CLASSES and maxw.get(n, 0) <= 0.35)


def main():
    a = sys.argv
    src, dst = a[1], a[2]
    lines = open(src, encoding='utf-8').read().split('\n')
    if '--nets' in a:
        nets = read_netfile(a[a.index('--nets') + 1])
    else:
        nets = all_signals(lines, a[a.index('--all-signals') + 1])
    NS = set(nets)
    out = []; last = 0; cnt = collections.Counter()
    for kind, i, j in blocks(lines):
        blk = lines[i:j + 1]; n = net_of(blk)
        drop = n in NS and (kind != 'zone' or any('(teardrop' in b for b in blk[:80]))
        if kind == 'zone' and n in NS and not drop:
            print('WARN non-teardrop zone kept for', n)
        if drop:
            out.extend(lines[last:i]); last = j + 1; cnt[kind] += 1
    out.extend(lines[last:])
    open(dst, 'w', encoding='utf-8').write('\n'.join(out))
    print('stripped nets', len(nets), dict(cnt))
    if '--list' in a:
        open(a[a.index('--list') + 1], 'w', encoding='utf-8').write('\n'.join(nets) + '\n')


if __name__ == '__main__':
    main()
