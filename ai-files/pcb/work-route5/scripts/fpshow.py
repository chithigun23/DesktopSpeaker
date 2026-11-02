"""fpshow.py BOARD REF [--full] : print a footprint block summary (at, pads, holes, courtyard lines) from the board text."""
import sys, re
L = open(sys.argv[1], encoding='utf-8').read().split('\n'); ref = sys.argv[2]
i = 0
while i < len(L):
    if L[i].startswith('\t(footprint '):
        j = i + 1
        while L[j] != '\t)': j += 1
        blk = L[i:j + 1]
        if any(x.strip() == '(property "Reference" "%s"' % ref for x in blk):
            print('lines', i + 1, j + 1)
            if '--full' in sys.argv:
                print('\n'.join(blk)); break
            depth_pad = False
            for k, x in enumerate(blk):
                s = x.strip()
                if x.startswith('\t\t(at ') or x.startswith('\t\t(layer ') or x.startswith('\t(footprint'): print(s)
                if x.startswith('\t\t(pad '): print('PAD', s, end=' ')
                if x.startswith('\t\t\t(at ') or x.startswith('\t\t\t(size ') or x.startswith('\t\t\t(drill ') or x.startswith('\t\t\t(net ') or x.startswith('\t\t\t(layers '):
                    print(s, end=' ')
                if x == '\t\t)' and k > 0: print()
                if x.startswith('\t\t(fp_') and 'CrtYd' in '\n'.join(blk[k:k+8]): pass
                if x.startswith('\t\t(model'): print('MODEL', s)
            break
        i = j + 1
    else: i += 1
