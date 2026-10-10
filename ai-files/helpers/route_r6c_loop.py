"""python3 route_r6c_loop.py IN OUT NETS.json [--prm JSON] [--pass N] : route each net in a fresh pcbnew process (route_r6c_route.py), keep the board when the net is completed; repeat passes until no gain.
(Batch runs showed state leaking after failed nets: XI/XO failed in a batch but route alone.)"""
import sys, json, subprocess, shutil, re, os
W='/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-r6/'
inp, out, nets = sys.argv[1:4]
extra = sys.argv[sys.argv.index('--prm'):sys.argv.index('--prm')+2] if '--prm' in sys.argv else []
passes = int(sys.argv[sys.argv.index('--pass')+1]) if '--pass' in sys.argv else 2
nets = json.load(open(nets)); cur = W + 'loop_cur.kicad_pcb'; shutil.copy(inp, cur); shutil.copy(inp.replace('.kicad_pcb','.kicad_pro'), cur.replace('.kicad_pcb','.kicad_pro')) if os.path.exists(inp.replace('.kicad_pcb','.kicad_pro')) else None
FP = ['flatpak','run','--filesystem=/home/chithi/Desktop/DesktopSpeaker','--command=python3','org.kicad.KiCad','/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/route_r6c_route.py']
done = {}
for ps in range(passes):
    gain = 0
    for n in nets:
        if done.get(n): continue
        tmp = W + 'loop_tmp.kicad_pcb'
        r = subprocess.run(FP + [cur, tmp, n] + extra, capture_output=True, text=True)
        ok = ' OK ' in r.stdout and 'open 0' in r.stdout
        line = [l for l in r.stdout.splitlines() if n in l and 'items' in l]
        print(ps, 'OK  ' if ok else 'FAIL', line[0][:110] if line else r.stdout[-200:], flush=True)
        if ok: shutil.move(tmp, cur); done[n] = 1; gain += 1
    print('pass', ps, 'gain', gain, flush=True)
    if not gain: break
shutil.copy(cur, out)
