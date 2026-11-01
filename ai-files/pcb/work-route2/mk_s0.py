"""mk_s0.py MANIFEST BOARD : create a manifest whose stage S0 locks the kept RT-1 template copper (nets in kept.txt)."""
import sys, json, hashlib, os
sys.path.insert(0, '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers')
import route_oct_lock as LK
man, board = sys.argv[1:3]
kept = [l.strip() for l in open('kept.txt') if l.strip()]
h, n = LK.copper_hash(board, kept)
M = dict(stages=dict(S0=dict(stage='S0', nets=kept, note='S0b/USB template copper kept from work-route/RT-1 (not routed)', input_board=os.path.abspath(board),
     copper_sha256=h, copper_items=n, stitch_vias=[], dru_sha256=hashlib.sha256(open('base.kicad_dru', 'rb').read()).hexdigest(),
     pro_sha256=hashlib.sha256(open('base.kicad_pro', 'rb').read()).hexdigest())))
json.dump(M, open(man, 'w'), indent=1); print('S0 locked', h, n)
