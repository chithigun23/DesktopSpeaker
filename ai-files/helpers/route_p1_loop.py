#!/usr/bin/env python3
"""route_p1_loop.py SPEC.json  : iterate Freerouting (mp 1 per round) on a board, re-routing only still-unconnected nets.
SPEC: {tag, start (board in work-p1), classes[], dsn_cfg{...route_p1_dsn config...}, rounds, nets_only[optional]}
Writes work-p1/<tag>-rK.kicad_pcb and <tag>-best.kicad_pcb ; logs to work-p1/<tag>.log"""
import sys, os, json, subprocess, shutil, time, re, collections
W = '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-p1'; H = '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers'
os.environ['PATH'] = H + '/bin:' + os.environ['PATH']
FP = ['flatpak', 'run', '--filesystem=/home/chithi/Desktop/DesktopSpeaker', '--filesystem=/tmp', '--command=python3', 'org.kicad.KiCad']
J = os.path.expanduser('~/Applications/freerouting/jre25/jdk-25.0.4.1+1-jre/bin/java')
JAR = os.path.expanduser('~/Applications/freerouting/freerouting-2.5.0.jar')
spec = json.load(open(sys.argv[1])); tag = spec['tag']
cls = json.load(open('/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/net-classes-p0.json'))
log = open('%s/%s.log' % (W, tag), 'a')
def L(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); log.write(s + '\n'); log.flush()
def fp(*args):
    r = subprocess.run(FP + list(args), capture_output=True, text=True)
    return '\n'.join(l for l in (r.stdout + r.stderr).splitlines() if not re.search('swig|Debug|assert', l))
def drc(board):
    pro = board.replace('.kicad_pcb', '.kicad_pro'); shutil.copy(W + '/DesktopSpeaker.kicad_pro', pro); shutil.copy(W + '/DesktopSpeaker.kicad_dru', pro.replace('.kicad_pro', '.kicad_dru'))
    out = board.replace('.kicad_pcb', '.drc.json')
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all', '--units', 'mm', '-o', out, board], capture_output=True)
    d = json.load(open(out)); c = collections.Counter()
    for u in d['unconnected_items']:
        m = re.search(r'\[([^\]]*)\]', u['items'][0]['description']); c[m.group(1) if m else '?'] += 1
    return c, d
inc = set(spec['classes'])
def unc_in_set(c):
    return {n: k for n, k in c.items() if cls.get(n) in inc and ('nets_only' not in spec or n in spec['nets_only'])}
cur = W + '/' + spec['start']; best = None; bestn = 10**9
for r in range(spec['rounds']):
    c, d = drc(cur); u = unc_in_set(c); n = sum(u.values())
    L('round', r, 'board', os.path.basename(cur), 'unconnected items in set', n, 'nets', len(u))
    if n < bestn:
        bestn = n; best = W + '/%s-best.kicad_pcb' % tag; shutil.copy(cur, best); shutil.copy(cur.replace('.kicad_pcb', '.kicad_pro'), best.replace('.kicad_pcb', '.kicad_pro'))
        json.dump(u, open(W + '/%s-best.unc.json' % tag, 'w'), indent=0)
    if n == 0: break
    nets = sorted(u)
    json.dump(nets, open(W + '/%s-prune.json' % tag, 'w'))
    pr = W + '/%s-pr%d.kicad_pcb' % (tag, r)
    L(fp(H + '/route_p1_prune_nets.py', cur, W + '/%s-prune.json' % tag, pr).strip().splitlines()[-1:])
    shutil.copy(W + '/DesktopSpeaker.kicad_pro', pr.replace('.kicad_pcb', '.kicad_pro'))
    dsn0 = W + '/%s-%d.in.dsn' % (tag, r); dsn = W + '/%s-%d.dsn' % (tag, r); ses = W + '/%s-%d.ses' % (tag, r)
    fp(H + '/route_p0_dsn.py', pr, dsn0)
    cfg = dict(spec['dsn_cfg']); cfg['nets_only'] = nets; json.dump(cfg, open(W + '/%s-%d.cfg.json' % (tag, r), 'w'))
    L(subprocess.run(['python3', H + '/route_p1_dsn.py', dsn0, dsn, W + '/%s-%d.cfg.json' % (tag, r)], capture_output=True, text=True).stdout.strip())
    if os.path.exists(ses): os.remove(ses)
    t0 = time.time()
    p = subprocess.Popen(['timeout', '1500', J, '-Djava.awt.headless=true', '-jar', JAR, '-de', dsn, '-do', ses, '-mp', str(spec.get('mp', 1))], stdout=open(W + '/fr%s-%d.log' % (tag, r), 'w'), stderr=subprocess.STDOUT)
    p.wait(); L('freerouting', round(time.time() - t0), 's rc', p.returncode)
    if not os.path.exists(ses): L('no ses'); break
    nxt = W + '/%s-r%d.kicad_pcb' % (tag, r + 1)
    L(fp(H + '/route_p1_post.py', 'import', pr, ses, nxt).strip().replace('\n', ' | '))
    cur = nxt
c, d = drc(cur); u = unc_in_set(c); n = sum(u.values())
L('final board', os.path.basename(cur), 'unconnected items in set', n)
if n < bestn:
    bestn = n; best = W + '/%s-best.kicad_pcb' % tag; shutil.copy(cur, best); shutil.copy(cur.replace('.kicad_pcb', '.kicad_pro'), best.replace('.kicad_pcb', '.kicad_pro')); json.dump(u, open(W + '/%s-best.unc.json' % tag, 'w'), indent=0)
L('BEST', best, bestn)
