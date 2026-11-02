"""fpdiff.py A.kicad_pcb B.kicad_pcb NETFILE [--json OUT] : plain-python gates between the RT-1 base and a routed board.
1. footprint poses (ref, at x y rot, layer) and pad nets (ref, pad number, index) parsed from the saved text;
2. copper (segments/arcs/vias) of every net that the router does NOT route (power, GND, S0 template nets): must be identical,
   except GND vias added on B (stitching vias), which are listed;
3. zone outlines (non-teardrop) identical."""
import sys, re, json, collections
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
try:
    import route_oct_lock as LK
except Exception: pass


def blocks(lines, head):
    i = 0
    while i < len(lines):
        if lines[i].startswith(head):
            j = i + 1
            while lines[j] != '\t)':
                j += 1
            yield lines[i:j + 1]; i = j + 1
        else:
            i += 1


def fps(path):
    L = open(path, encoding='utf-8').read().split('\n'); out = {}; pads = {}
    for b in blocks(L, '\t(footprint '):
        ref = next(re.search(r'"Reference" "([^"]*)"', x).group(1) for x in b if '(property "Reference"' in x)
        at = next(x.strip() for x in b if x.startswith('\t\t(at '))
        lay = next(x.strip() for x in b if x.startswith('\t\t(layer '))
        out[ref] = (at, lay)
        k = 0; cur = None
        for x in b:
            m = re.match(r'^\t\t\(pad "([^"]*)"', x)
            if m:
                cur = (ref, m.group(1), k); k += 1; pads[cur] = ''
            m = re.match(r'^\t\t\t\(net "([^"]*)"\)', x)
            if m and cur:
                pads[cur] = m.group(1)
    return out, pads


def zones(path):
    L = open(path, encoding='utf-8').read().split('\n'); out = collections.Counter()
    for b in blocks(L, '\t(zone'):
        if any('(teardrop' in x for x in b[:80]):
            continue
        txt = '\n'.join(b); txt = re.sub(r'\(filled_polygon.*', '', txt, flags=re.S)   # outline + settings only
        out[txt] += 1
    return out


