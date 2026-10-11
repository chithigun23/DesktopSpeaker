#!/usr/bin/env python3
"""fab_check.py OUT_DIR BOARD.kicad_pcb : numeric consistency checks of a fab_export.sh output set against the board (pcbnew).
Checks: layer files present; gerber extents per copper layer vs board outline; flash (D03) counts on paste/mask vs pads;
PTH/NPTH drill hit counts vs pads+vias; position file count vs footprints; gbrjob layer list."""
import sys, os, re, json, glob, collections
import pcbnew
MM = 1e6
out, board = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(board)
bb = b.GetBoardEdgesBoundingBox()
bx0, by0, bx1, by1 = bb.GetX()/MM, bb.GetY()/MM, bb.GetRight()/MM, bb.GetBottom()/MM
gdir = os.path.join(out, 'gerbers')
files = sorted(os.listdir(gdir))
need = ['F_Cu.gtl','In1_Cu.g1','In2_Cu.g2','B_Cu.gbl','F_Paste.gtp','B_Paste.gbp','F_Silkscreen.gto','B_Silkscreen.gbo','F_Mask.gts','B_Mask.gbs','Edge_Cuts.gm1','PTH.drl','NPTH.drl','job.gbrjob']
miss = [n for n in need if not any(f.endswith(n) for f in files)]
print('files', len(files), 'missing', miss)
def gerber_stats(path):
    xs=[]; ys=[]; flashes=0; fmt=None
    for line in open(path, errors='ignore'):
        if line.startswith('%FSLA'):
            m=re.search(r'X(\d)(\d)Y', line); fmt=int(m.group(2))
        m=re.match(r'X(-?\d+)Y(-?\d+)D0([123])\*', line)
        if m:
            x=int(m.group(1))/10**fmt; y=int(m.group(2))/10**fmt; xs.append(x); ys.append(y)
            if m.group(3)=='3': flashes+=1
    return (min(xs),min(ys),max(xs),max(ys)) if xs else None, flashes
for n in need[:11]:
    f=[x for x in files if x.endswith(n)]
    if not f: continue
    ext, fl = gerber_stats(os.path.join(gdir,f[0]))
    note=''
    if ext:
        # gerber y is up; KiCad board y is down: compare widths/heights and x range only
        w=ext[2]-ext[0]; h=ext[3]-ext[1]
        if w > (bx1-bx0)+0.2 or h > (by1-by0)+0.2: note='EXCEEDS OUTLINE'
    print(f'  {n:18s} flashes {fl:5d} extents {tuple(round(v,2) for v in ext) if ext else None} {note}')
# pads/vias
smd_f = sum(1 for fp in b.GetFootprints() for p in fp.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and p.IsOnLayer(pcbnew.F_Cu))
smd_b = sum(1 for fp in b.GetFootprints() for p in fp.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and p.IsOnLayer(pcbnew.B_Cu))
pth = sum(1 for fp in b.GetFootprints() for p in fp.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH)
npth = sum(1 for fp in b.GetFootprints() for p in fp.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH)
vias = sum(1 for t in b.GetTracks() if t.GetClass()=='PCB_VIA')
paste_f = sum(1 for fp in b.GetFootprints() for p in fp.Pads() if p.IsOnLayer(pcbnew.F_Paste))
print(f'board: SMD pads F {smd_f} B {smd_b}, PTH pads {pth}, NPTH {npth}, vias {vias}, pads with F.Paste {paste_f}')
def drl_hits(path):
    n=0; tools=collections.Counter(); t=None
    for line in open(path, errors='ignore'):
        m=re.match(r'T(\d+)C([\d.]+)', line)
        if m: tools[m.group(1)]=float(m.group(2)); continue
        if re.match(r'T\d+$', line.strip()): t=line.strip(); continue
        if re.match(r'X-?[\d.]+Y-?[\d.]+', line): n+=1
        if re.match(r'G85', line) or 'G85' in line: n+=0
    return n, tools
for n in ('PTH.drl','NPTH.drl'):
    f=[x for x in files if x.endswith('-'+n)][0]; hits,tools=drl_hits(os.path.join(gdir,f))
    print(f'  {n}: hits {hits} tools {len(tools)} dia {sorted(set(tools.values()))}')
print('expected PTH hits (pads+vias, slots count once) ~', pth+vias, '; NPTH ~', npth)
pos=[f for f in os.listdir(out) if f.endswith('-pos-jlc.csv')]
if pos:
    rows=open(os.path.join(out,pos[0])).read().strip().splitlines()[1:]
    fps=[fp for fp in b.GetFootprints() if not fp.IsExcludedFromPosFiles() and not fp.IsDNP()]
    print(f'position rows {len(rows)} vs footprints not excluded/DNP {len(fps)}')
job=[f for f in files if f.endswith('.gbrjob')]
if job:
    j=json.load(open(os.path.join(gdir,job[0]))); print('gbrjob layers', len(j.get('FilesAttributes',[])), 'size', j.get('GeneralSpecs',{}).get('Size'))
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and p.IsOnLayer(pcbnew.B_Cu): print('  B-side SMD pad:', fp.GetReference(), p.GetNumber(), 'paste', p.IsOnLayer(pcbnew.B_Paste))
