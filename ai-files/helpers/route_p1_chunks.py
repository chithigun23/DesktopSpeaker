#!/usr/bin/env python3
"""route_p1_chunks.py SPEC.json : route nets in chunks (shortest span first), each chunk = one Freerouting run (-mp MP) on the current board,
all earlier copper protected. After each chunk, tracks of chunk nets that are still unconnected are removed. Final report of open nets.
SPEC: {tag,start,classes[],chunk,mp,dsn_cfg{...},retry_rounds}"""
import sys, os, json, subprocess, shutil, re, collections, time
W = '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-p1'; H = '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers'
os.environ['PATH'] = H + '/bin:' + os.environ['PATH']
FP = ['flatpak', 'run', '--filesystem=/home/chithi/Desktop/DesktopSpeaker', '--filesystem=/tmp', '--command=python3', 'org.kicad.KiCad']
J = os.path.expanduser('~/Applications/freerouting/jre25/jdk-25.0.4.1+1-jre/bin/java')
JAR = os.path.expanduser('~/Applications/freerouting/freerouting-2.5.0.jar')
spec = json.load(open(sys.argv[1])); tag = spec['tag']
cls = json.load(open(W + '/net-classes-p1.json'))
logf = open('%s/%s.log' % (W, tag), 'a')
def L(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); logf.write(s + '\n'); logf.flush()
def fp(*args):
    r = subprocess.run(FP + list(args), capture_output=True, text=True)
    return '\n'.join(l for l in (r.stdout + r.stderr).splitlines() if not re.search('swig|Debug|assert|memory leak', l))
def openmap(board):
    o = board.replace('.kicad_pcb', '.open.json')
    fp(H + '/route_p1_open.py', board, o)
    return collections.Counter(json.load(open(o)))
def drc_unused(board):
    shutil.copy(W + '/DesktopSpeaker.kicad_pro', board.replace('.kicad_pcb', '.kicad_pro')); shutil.copy(W + '/DesktopSpeaker.kicad_dru', board.replace('.kicad_pcb', '.kicad_dru'))
    out = board.replace('.kicad_pcb', '.drc.json')
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all', '--units', 'mm', '-o', out, board], capture_output=True)
    d = json.load(open(out)); c = collections.Counter()
    for u in d['unconnected_items']:
        m = re.search(r'\[([^\]]*)\]', u['items'][0]['description']); c[m.group(1) if m else '?'] += 1
    return c
inc = set(spec['classes'])
cur = W + '/' + spec['start']
fp(H + '/route_p1_netinfo.py', cur, W + '/%s-netinfo.json' % tag)
ni = json.load(open(W + '/%s-netinfo.json' % tag))
def span(n):
    p = ni[n]; xs = [q[0] for q in p]; ys = [q[1] for q in p]; return (max(xs) - min(xs)) + (max(ys) - min(ys))
c = openmap(cur)
todo = sorted([n for n in c if cls.get(n) in inc and n in ni], key=span)
L('start: nets to route', len(todo), 'items', sum(c[n] for n in todo))
ch = spec.get('chunk', 15); k = 0
rounds = spec.get('retry_rounds', 1)
pending = todo
for rnd in range(rounds):
    chunks = [pending[i:i + ch] for i in range(0, len(pending), ch)]
    for nets in chunks:
        k += 1
        pr = W + '/%s-c%d.kicad_pcb' % (tag, k)
        shutil.copy(cur, pr); shutil.copy(W + '/DesktopSpeaker.kicad_pro', pr.replace('.kicad_pcb', '.kicad_pro'))
        dsn0 = W + '/%s-c%d.in.dsn' % (tag, k); dsn = W + '/%s-c%d.dsn' % (tag, k); ses = W + '/%s-c%d.ses' % (tag, k)
        fp(H + '/route_p0_dsn.py', pr, dsn0)
        cfg = dict(spec['dsn_cfg']); cfg['nets_only'] = nets; cfg['nets_keep'] = spec.get('keep', []); json.dump(cfg, open(W + '/%s-c%d.cfg.json' % (tag, k), 'w'))
        r = subprocess.run(['python3', H + '/route_p1_dsn.py', dsn0, dsn, W + '/%s-c%d.cfg.json' % (tag, k)], capture_output=True, text=True)
        t0 = time.time()
        p = subprocess.Popen(['timeout', '300', J, '-Djava.awt.headless=true', '-jar', JAR, '-de', dsn, '-do', ses, '-mp', str(spec.get('mp', 1))], stdout=open(W + '/fr%s-c%d.log' % (tag, k), 'w'), stderr=subprocess.STDOUT)
        p.wait()
        if not os.path.exists(ses): L('chunk', k, 'no ses'); continue
        imp = W + '/%s-c%d-imp.kicad_pcb' % (tag, k)
        json.dump(nets, open(W + '/%s-c%d-nets.json' % (tag, k), 'w'))
        fp(H + '/route_p1_post.py', 'merge', cur, ses, imp, W + '/%s-c%d-nets.json' % (tag, k), W + '/nowire.kicad_pcb')
        shutil.copy(W + '/DesktopSpeaker.kicad_pro', imp.replace('.kicad_pcb', '.kicad_pro'))
        c2 = openmap(imp)
        bad = sorted(n for n in nets if c2.get(n, 0) >= c.get(n, 0))
        if bad:
            json.dump(bad, open(W + '/%s-c%d-bad.json' % (tag, k), 'w'))
            nb = W + '/%s-c%d-pruned.kicad_pcb' % (tag, k)
            fp(H + '/route_p1_prune_nets.py', imp, W + '/%s-c%d-bad.json' % (tag, k), nb)
            shutil.copy(W + '/DesktopSpeaker.kicad_pro', nb.replace('.kicad_pcb', '.kicad_pro'))
            cur = nb
        else: cur = imp
        L('chunk', k, 'nets', len(nets), 'failed', len(bad), 'span<=%.0f' % span(nets[-1]), '%ds' % (time.time() - t0), os.path.basename(cur))
    c = openmap(cur); pending = sorted([n for n in c if cls.get(n) in inc and n in ni], key=span)
    L('after round', rnd, 'open nets', len(pending), 'items', sum(c[n] for n in pending))
    if not pending: break
shutil.copy(cur, W + '/%s-final.kicad_pcb' % tag); shutil.copy(W + '/DesktopSpeaker.kicad_pro', W + '/%s-final.kicad_pro' % tag)
json.dump({n: c[n] for n in pending}, open(W + '/%s-open.json' % tag, 'w'), indent=0)
L('DONE', tag, 'open nets', len(pending), pending)
