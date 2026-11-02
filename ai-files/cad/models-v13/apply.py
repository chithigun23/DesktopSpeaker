#!/usr/bin/env python3
"""Apply the models-v13 3D model mapping to COPIES of the project footprint library and/or a board.

  python3 apply.py --map apply-map.json [--footprints DIR] [--board FILE.kicad_pcb] [--models-dir DIR] [--dry-run]

--footprints  folder of .kicad_mod files (a copy of DesktopSpeaker-kicad/kicad-library/footprint)
--board       a .kicad_pcb copy; footprints are matched by their library id "DesktopSpeaker:<name>"
--models-dir  a 3d folder (copy); the new STEP files listed in the map are copied there (flat)
The (model ...) blocks of every mapped footprint are replaced by the map entries. Idempotent: running twice
changes nothing the second time. Footprints not in the map are untouched. Plain python3, no dependencies.
Do not point it at DesktopSpeaker-kicad/ until the coordinator decides to (the script refuses unless --allow-project).
"""
import argparse, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def fmt_model(m, indent):
    t = indent
    path = m['path']
    o = m.get('offset', [0, 0, 0]); s = m.get('scale', [1, 1, 1]); r = m.get('rotate', [0, 0, 0])
    g = lambda v: ' '.join(('%g' % x) for x in v)
    return (f'{t}(model "{path}"\n{t}\t(offset\n{t}\t\t(xyz {g(o)})\n{t}\t)\n{t}\t(scale\n{t}\t\t(xyz {g(s)})\n{t}\t)\n'
            f'{t}\t(rotate\n{t}\t\t(xyz {g(r)})\n{t}\t)\n{t})')


def match_close(txt, i):
    """index of the ')' closing the '(' at txt[i]"""
    depth = 0; j = i; n = len(txt); instr = False
    while j < n:
        ch = txt[j]
        if instr:
            if ch == '\\':
                j += 2; continue
            if ch == '"':
                instr = False
        elif ch == '"':
            instr = True
        elif ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return j
        j += 1
    raise ValueError('unbalanced')


def rewrite_block(block, models):
    """block = text of one footprint s-expression; returns block with model blocks replaced"""
    # remove existing (model ...) children (direct children only: they start with '(model ')
    out = block; pos = 0; first = None
    while True:
        mm = re.compile(r'\(model[ \t\n]').search(out, pos)
        k = mm.start() if mm else -1
        if k < 0:
            break
        e = match_close(out, k)
        ls = out.rfind('\n', 0, k) + 1
        if first is None:
            first = ls
        end = e + 1
        if out[end:end + 1] == '\n':
            end += 1
        out = out[:ls] + out[end:]
        pos = ls
    # indentation of children
    m = re.search(r'\n([ \t]+)\(', out)
    indent = m.group(1) if m else '\t\t'
    close = out.rstrip().rfind(')')
    head = out[:close].rstrip('\n \t')
    new = head + '\n' + '\n'.join(fmt_model(x, indent) for x in models) + '\n' + indent[:-1] + ')'
    return new


def process_text(txt, fpmap, board):
    changed = []
    if not board:
        name = None
        m = re.match(r'\s*\((?:footprint|module) "?([^"\s)]+)"?', txt)
        if not m:
            return txt, changed
        name = m.group(1).split(':')[-1]
        if name in fpmap:
            s = re.search(r'\((?:footprint|module)[ \t]', txt).start()
            e = match_close(txt, s)
            new = rewrite_block(txt[s:e + 1], fpmap[name]['models'])
            if new != txt[s:e + 1]:
                changed.append(name)
            return txt[:s] + new + txt[e + 1:], changed
        return txt, changed
    out = []; pos = 0
    for m in re.finditer(r'\(footprint "([^"]+)"', txt):
        if m.start() < pos:
            continue
        name = m.group(1).split(':')[-1]
        if name not in fpmap:
            continue
        s = m.start(); e = match_close(txt, s)
        blk = txt[s:e + 1]
        new = rewrite_block(blk, fpmap[name]['models'])
        out.append(txt[pos:s]); out.append(new); pos = e + 1
        if new != blk:
            ref = re.search(r'\(property "Reference" "([^"]+)"', blk)
            changed.append(ref.group(1) if ref else name)
    out.append(txt[pos:])
    return ''.join(out), changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--map', default=os.path.join(HERE, 'apply-map.json'))
    ap.add_argument('--footprints'); ap.add_argument('--board'); ap.add_argument('--models-dir')
    ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--allow-project', action='store_true')
    a = ap.parse_args()
    for p in (a.footprints, a.board, a.models_dir):
        if p and 'DesktopSpeaker-kicad' in os.path.abspath(p) and not a.allow_project:
            sys.exit('refusing to touch DesktopSpeaker-kicad/ without --allow-project')
    mp = json.load(open(a.map))
    fpmap = mp['footprints']
    if a.models_dir:
        for f in mp.get('files', []):
            src = os.path.join(HERE, f); dst = os.path.join(a.models_dir, os.path.basename(f))
            same = os.path.exists(dst) and open(src, 'rb').read() == open(dst, 'rb').read()
            print(('same  ' if same else 'copy  ') + f + ' -> ' + dst)
            if not same and not a.dry_run:
                shutil.copyfile(src, dst)
    if a.footprints:
        for name in sorted(fpmap):
            p = os.path.join(a.footprints, name + '.kicad_mod')
            if not os.path.exists(p):
                print('missing footprint', p); continue
            txt = open(p).read()
            new, ch = process_text(txt, fpmap, board=False)
            print(('change' if ch else 'same  ') + ' footprint ' + name)
            if ch and not a.dry_run:
                open(p, 'w').write(new)
    if a.board:
        txt = open(a.board).read()
        new, ch = process_text(txt, fpmap, board=True)
        print('board: %d footprint(s) changed: %s' % (len(ch), ' '.join(ch)))
        if ch and not a.dry_run:
            open(a.board, 'w').write(new)


if __name__ == '__main__':
    main()
