import pcbnew, os
p=pcbnew.PCB_IO_KICAD_SEXPR().FootprintLoad(os.path.abspath('ai-files/candidates/footprint-preview.pretty'),'CSD17579Q3A_DNH0008A')
assert p is not None
b=pcbnew.BOARD(); p.SetPosition(pcbnew.VECTOR2I(100000000,100000000)); b.Add(p)
pcbnew.SaveBoard(os.path.abspath('ai-files/candidates/CSD17579Q3A-footprint-preview.kicad_pcb'),b)
print('pads',p.GetPadCount(),[(x.GetNumber(), x.GetSize().x/1e6,x.GetSize().y/1e6,x.GetPosition().x/1e6,x.GetPosition().y/1e6) for x in p.Pads()])
