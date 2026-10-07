#!/usr/bin/env python3
"""route_p1_rounds.py START_STEM N TAG : N times {DRC fix cycle, chunk-route open managed nets}; stops after 2 rounds without gain."""
import sys, json, subprocess, os
W = '/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-p1'; H = '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers'
os.environ['PATH'] = H + '/bin:' + os.environ['PATH']
stem, n, tag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
base = json.load(open(W + '/specR3.json'))
def edges(st):
    subprocess.run([H + '/route_p1_stat.sh', st], capture_output=True)
    o = json.load(open('%s/%s.open.json' % (W, st))); cls = json.load(open(W + '/net-classes-p1.json'))
    return sum(v for k, v in o.items() if cls.get(k) in base['classes'] and not k.startswith('unconnected-'))
def log(*a):
    s = ' '.join(map(str, a)); print(s, flush=True); open(W + '/%s.rounds.log' % tag, 'a').write(s + '\n')
best = edges(stem); log('start', stem, best); stall = 0
for i in range(1, n + 1):
    sh = subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all', '--units', 'mm', '-o', '%s/%s.drc.json' % (W, stem), '%s/%s.kicad_pcb' % (W, stem)], capture_output=True)
    r = subprocess.run([H + '/route_p1_cycle.sh', stem, '%s-x%d' % (tag, i)], capture_output=True, text=True); log(r.stdout.strip())
    s = dict(base); s['tag'] = '%s%d' % (tag, i); s['start'] = '%s-x%d.kicad_pcb' % (tag, i)
    json.dump(s, open('%s/spec%s%d.json' % (W, tag, i), 'w'))
    subprocess.run(['python3', H + '/route_p1_chunks.py', '%s/spec%s%d.json' % (W, tag, i)], capture_output=True)
    stem = '%s%d-final' % (tag, i)
    e = edges(stem); log('round', i, stem, 'managed open edges', e)
    if e < best: best = e; stall = 0
    else: stall += 1
    if stall >= 2: break
log('DONE', stem, best)
