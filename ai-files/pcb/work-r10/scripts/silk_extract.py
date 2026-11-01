"""silk_extract.py BOARD OUT.json : board-level F.Silkscreen lines/rects/polys/texts (text as an approximate box)"""
import re, json, sys
s = open(sys.argv[1]).read().split('\n'); out = []; i = 0
while i < len(s):
    L = s[i]
    if L.startswith('\t(gr_'):
        j = i
        if L.count('(') != L.count(')'):
            j = i + 1
            while s[j] != '\t)': j += 1
        B = '\n'.join(s[i:j + 1])
        if re.search(r'\(layer "F\.(SilkS|Silkscreen)"', B):
            kind = L.strip()[1:].split()[0]
            g = lambda k: re.search(r'\(' + k + r' ([-\d.]+) ([-\d.]+)', B)
            st, en, at = g('start'), g('end'), g('at')
            w = re.search(r'\(width ([-\d.]+)\)', B); sz = re.search(r'\(size ([-\d.]+) ([-\d.]+)\)', B)
            txt = re.search(r'\(gr_text "([^"]*)"', B)
            out.append(dict(kind=kind, start=[float(st.group(1)), float(st.group(2))] if st else None,
                            end=[float(en.group(1)), float(en.group(2))] if en else None, w=float(w.group(1)) if w else 0.15,
                            pts=[(float(a), float(b)) for a, b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', B)],
                            at=[float(at.group(1)), float(at.group(2))] if at else None, text=txt.group(1) if txt else None,
                            size=[float(sz.group(1)), float(sz.group(2))] if sz else None))
        i = j + 1; continue
    i += 1
json.dump(out, open(sys.argv[2], 'w')); import collections; print(len(out), collections.Counter(o['kind'] for o in out))
