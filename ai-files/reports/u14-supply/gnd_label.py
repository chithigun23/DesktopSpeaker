from pathlib import Path
import sys,uuid
sys.path.insert(0,'ai-files/vendor')
from sexpdata import loads,dumps,Symbol as S
p=Path('DesktopSpeaker-kicad/Logic_Audio_Power.kicad_sch');d=loads(p.read_text())
d.append([S('global_label'),'GND',[S('shape'),S('input')],[S('at'),149.86,115.57,0],[S('effects'),[S('font'),[S('size'),1.0,1.0]],[S('justify'),S('left')]],[S('uuid'),str(uuid.uuid4())]])
p.write_text(dumps(d)+'\n')
