#!/usr/bin/env python3
"""Routing P1 DSN transformer (plain python3).
usage: route_p1_dsn.py IN.dsn OUT.dsn CONFIG.json
CONFIG keys:
  nets_include   : list of netclass names (kicad class, first part of 'A,SIGNAL') whose nets stay in the network
  nets_exclude   : optional list of net names removed even if their class is included
  nets_only      : optional list of net names; if given only these stay (and are in nets_include classes)
  drop_planes    : list of layers whose (plane ...) entries are dropped ('B.Cu','F.Cu','In1.Cu','In2.Cu')
  drop_keepouts  : true -> drop the F.Cu no-pour keepout polygons ((keepout "" (polygon F.Cu ...)) lines)
  in1_power      : true -> In1.Cu is not routable
  in2_power      : true -> In2.Cu is not routable
  class_rules    : {class: {"width":um,"clearance":um,"extra":"text", "layers":["F.Cu"], "novia":bool}}
  default_clear  : clearance (um) for classes not in class_rules (default 200)
  protect        : true -> existing wires/vias become (type protect)
"""
import sys, re, json
src, dst, cfgp = sys.argv[1:4]
cfg = json.load(open(cfgp))
txt = open(src).read()
i = txt.index('  (network'); j = txt.index('  (wiring')
head, net, tail = txt[:i], txt[i:j], txt[j:]

def blocks(s):
    out = []; depth = 0; start = None; instr = False
    for k, ch in enumerate(s):
        if ch == '"': instr = not instr
        if instr: continue
        if ch == '(':
            if depth == 1: start = k
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 1: out.append((start, k + 1))
    return out

# ---- structure: planes / keepouts / layer types
def drop_scopes(text, pat_start):
    """remove complete scopes starting with pat_start (regex on '(plane NET (polygon LAYER' etc.)"""
    res = []; pos = 0
    for m in re.finditer(pat_start, text):
        a = m.start()
        if a < pos: continue
        d = 0; k = a; instr = False
        while True:
            ch = text[k]
            if ch == '"': instr = not instr
            elif not instr:
                if ch == '(': d += 1
                elif ch == ')':
                    d -= 1
                    if d == 0: break
            k += 1
        res.append((a, k + 1)); pos = k + 1
    out = []; last = 0
    for a, b in res:
        out.append(text[last:a]); last = b
        # also swallow the newline
        if text[last:last+1] == '\n': last += 1
    out.append(text[last:]); return ''.join(out), len(res)

nrem = {}
for ly in cfg.get('drop_planes', []):
    head, n = drop_scopes(head, r'\(plane\s+("[^"]*"|\S+)\s*\(polygon\s+' + re.escape(ly) + r'\s')
    nrem['plane ' + ly] = n
if cfg.get('drop_keepouts'):
    head, n = drop_scopes(head, r'\(keepout\s+""\s*\(polygon\s+F\.Cu\s+0\s+(?!81550 -41865)')
    nrem['F.Cu keepouts'] = n
if cfg.get('in1_power', True):
    head = re.sub(r'(\(layer In1\.Cu\s*\(type )signal', r'\1power', head)
if cfg.get('in2_power'):
    head = re.sub(r'(\(layer In2\.Cu\s*\(type )signal', r'\1power', head)

# ---- network
bl = blocks(net)
def nname(b):
    m = re.match(r'\(net\s+("[^"]*"|\S+)', b); return m.group(1).strip('"')
netcls = {}
for a, c in bl:
    b = net[a:c]
    if b.startswith('(class '):
        m = re.search(r'\(circuit', b)
        toks = re.findall(r'"[^"]*"|[^\s]+', b[:m.start()])
        cname = toks[1].split(',')[0]
        for t in toks[2:]: netcls[t.strip('"')] = cname
inc = set(cfg['nets_include']); excl = set(cfg.get('nets_exclude', []))
only = set(cfg['nets_only']) | set(cfg.get('nets_keep', [])) if 'nets_only' in cfg else None
def keep_net(n):
    if n.startswith('unconnected-'): return False
    c = netcls.get(n)
    if c not in inc or n in excl: return False
    if only is not None and n not in only: return False
    return True

crules = cfg.get('class_rules', {}); dclr = cfg.get('default_clear', 200)
classes = []; netblocks = []
for a, c in bl:
    b = net[a:c]
    if b.startswith('(net '):
        if keep_net(nname(b)): netblocks.append(b)
    elif b.startswith('(class '):
        m = re.search(r'\(circuit', b)
        toks = re.findall(r'"[^"]*"|[^\s]+', b[:m.start()])
        full = toks[1]; cname = full.split(',')[0]
        mem = [t for t in toks[2:] if keep_net(t.strip('"'))]
        rest = b[m.start():]
        r = crules.get(cname, {})
        w = re.search(r'\(width\s+(\d+)', rest)
        width = r.get('width', int(w.group(1)) if w else 250)
        clr = r.get('clearance', dclr)
        lay = ''.join('(use_layer %s)' % l for l in r.get('layers', []))
        extra = r.get('extra', '')
        if cname == 'kicad_default' or mem == []:
            if cname != 'kicad_default': continue
        via = '' if r.get('novia') else re.search(r'\(use_via[^)]*\)', rest).group(0)
        if cname != 'kicad_default' and not r.get('via_override') is None and r.get('via_override'):
            via = '(use_via "%s")' % r['via_override']
        classes.append((clr, '    (class %s %s\n      (circuit %s%s)\n      (rule\n        (width %d)\n        (clearance %d)\n%s      )\n    )\n' % (full if cname != 'kicad_default' else 'kicad_default', ' '.join(mem), via, lay, width, clr, extra)))
# order: loosest first, strictest last (later classes override earlier ones in the clearance matrix)
classes.sort(key=lambda x: x[0])
# the net list of each class goes first, remaining blocks follow
body = net[:bl[0][0]] + ''.join('    ' + b + '\n' for b in netblocks) + '    (net OBST_FOREIGN\n      (pins)\n    )\n' + ''.join(c for _, c in classes) + '  )\n'
# via padstack names: keep (via ...) line already inside head
out = head + body + tail
# wires/vias of nets that are not in the network become netless fixed obstacles (otherwise Freerouting drops vias and hangs on the SES write)
kept = set(nname(x) for x in netblocks)
def _strip(m):
    n = m.group(2).strip('"')
    return m.group(0) if n in kept else m.group(1) + '(net OBST_FOREIGN)'
tail = re.sub(r'(\((?:wire|via)[^\n]*?)\(net ("[^"]*"|[^\s)]+)\)', _strip, tail)
out = head + body + tail
if cfg.get('no_wiring'):
    k = out.index('  (wiring'); out = out[:k] + '  (wiring\n  )\n)\n'
if cfg.get('protect', True): out = out.replace('(type route)', '(type protect)')
open(dst, 'w').write(out)
print('nets in network', len(netblocks), 'classes', len(classes), nrem)
