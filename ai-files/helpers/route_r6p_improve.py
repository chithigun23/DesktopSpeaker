"""host python: route_r6p_improve.py START.kicad_pcb OUT.kicad_pcb LOG.json NET[+NET2..] ... [--keep 1.5] [--min 3]
Greedy detour reduction with the R6i plan router (route_r6i_route.py). For each item (one net, or a '+' group that is ripped
together and re-routed in the given order): rip (pad-local copper within KEEP mm kept), re-route (F/In2/B; In2 only where the
router allows it), then accept only if every routed net is OK, kicad-cli DRC has no violation and no unconnected item, the
fragment-aware open-edge count of the board is 0, and the group's total track length fell by at least MIN mm without more
than one extra via per net. Accepted boards become the new base. Writes a per-item log (lengths before/after, verdict)."""
import sys, os, json, subprocess, shutil, collections
W = '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/'; H = '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/'
FP = ['flatpak', 'run', '--filesystem=/home/chithi/Desktop/DesktopSpeaker', '--filesystem=/tmp/claude-1000', '--command=python3', 'org.kicad.KiCad']
A = sys.argv; start, out, logf = A[1], A[2], A[3]
keep = float(A[A.index('--keep') + 1]) if '--keep' in A else 1.5
mn = float(A[A.index('--min') + 1]) if '--min' in A else 3.0
items = []; i = 4
while i < len(A):
    if A[i] in ('--keep', '--min'): i += 2; continue
    items.append(A[i]); i += 1
os.chdir(W); tmp = os.environ.get('IMPTMP', W + 'r6p/imp/'); os.makedirs(tmp, exist_ok=True)
def cpaux(stem):
    shutil.copy(W + 'R6o.kicad_pro', stem + '.kicad_pro'); shutil.copy(W + 'R6o.kicad_dru', stem + '.kicad_dru')
def fp(*args): return subprocess.run(FP + list(args), capture_output=True, text=True).stdout
def geom(board, nets):
    fp(H + 'route_r6p_geom.py', board, '--nets', ','.join(nets), '--json', tmp + 'g.json')
    g = json.load(open(tmp + 'g.json')); return {n: (g[n]['length'], g[n]['vias']) if n in g else (0, 0) for n in nets}
cur = tmp + 'cur.kicad_pcb'; shutil.copy(start, cur); cpaux(cur[:-10])
log = []
for k, it in enumerate(items):
    nets = it.split('+'); before = geom(cur, nets)
    plan = tmp + 'p.json'
    cand = tmp + 'cand.kicad_pcb'
    for kk in (keep, 0):   # retry with a full rip when the pad-local stubs block the router
        fp(W + 'r6p/mkplan.py', cur, plan, str(kk), '[0,1,2]', '{"margins":[8,20,50],"viacost":6}', *nets)
        o = fp(H + 'route_r6i_route.py', cur, cand, plan)
        st = [l for l in o.split('\n') if l.split()[:1] and (' OK ' in l or 'FAIL' in l or 'PART' in l or 'LOST' in l or 'REFUSE' in l)]
        ok = all(' OK ' in l for l in st if not l.strip().startswith('REFUSE')) and len([l for l in st if ' OK ' in l]) == len(nets)
        if ok or kk == 0: break
    rec = dict(item=it, before=before, router=st)
    if ok:
        cpaux(cand[:-10]); after = geom(cand, nets); rec['after'] = after
        gain = sum(before[n][0] for n in nets) - sum(after[n][0] for n in nets)
        vv = all(after[n][1] <= before[n][1] + 1 for n in nets)
        rec['gain'] = round(gain, 2)
        if gain >= mn and vv:
            for _ in range(6):   # drop leftover dangling stubs of the routed nets (KiCad's own dangling verdict, by uuid)
                subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all', '--units', 'mm', '-o', tmp + 'd.json', cand], capture_output=True, env=dict(os.environ, PATH=H + 'bin:' + os.environ['PATH']))
                d = json.load(open(tmp + 'd.json')); nv = [x for x in d['violations'] if x['type'] != 'lib_footprint_issues']
                dg = [x for x in nv if x['type'] in ('track_dangling', 'via_dangling') and any(n in i['description'] for i in x['items'] for n in ['[' + q + ']' for q in nets])]
                if not dg or len(dg) != len(nv): break
                fp(H + 'route_r6p_dangle.py', cand, cand, tmp + 'd.json', ','.join(nets)); cpaux(cand[:-10])
            after = geom(cand, nets); rec['after'] = after; rec['gain'] = round(sum(before[n][0] for n in nets) - sum(after[n][0] for n in nets), 2)
            fp(H + 'route_p2_open2.py', cand, tmp + 'o.json', 'all'); op = sum(json.load(open(tmp + 'o.json')).values())
            rec['drc'] = len(nv); rec['unc'] = len(d['unconnected_items']); rec['open'] = op
            if not nv and not d['unconnected_items'] and op == 0:
                shutil.copy(cand, cur); rec['verdict'] = 'ACCEPT'
            else: rec['verdict'] = 'reject-gates'; rec['drcitems'] = [(x['type'], x['description'][:60], [(i['description'][:40], i['pos']['x'], i['pos']['y']) for i in x['items']]) for x in nv[:5]]
        else: rec['verdict'] = 'reject-gain' if gain < mn else 'reject-vias'
    else: rec['verdict'] = 'router-fail'
    log.append(rec); json.dump(log, open(logf, 'w'), indent=1)
    print(k, it, rec['verdict'], rec.get('gain'), before, rec.get('after'), flush=True)
shutil.copy(cur, out); cpaux(out[:-10])
print('done', sum(1 for r in log if r['verdict'] == 'ACCEPT'), 'accepted of', len(log))
