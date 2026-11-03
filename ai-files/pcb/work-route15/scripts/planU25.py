import sys; sys.path.insert(0,'scripts')
from mkplan import P
p=P(sys.argv[1] if len(sys.argv)>1 else 'B1.kicad_pcb')
p.seg('F.Cu','Net-(U25-FB)',0.2,(154.91,146.44),(155.72,146.44),(156.86,145.3),(158.89,145.3),(159.24,144.95),(159.24,143.46))
p.seg('F.Cu','Net-(U25-MODE)',0.2,(154.91,148.44),(155.58,148.44),(155.58,149.4),(155.88,149.7))
p.save('t/planU25.json')
