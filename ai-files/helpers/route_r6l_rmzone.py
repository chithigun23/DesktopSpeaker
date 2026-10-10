"""flatpak: route_r6l_rmzone.py IN OUT NAME [NAME..] : delete the named zones, refill, save (R6l: drops SYS_IN2_G, whose fill made an In2 copper sliver)."""
import sys,pcbnew
b=pcbnew.LoadBoard(sys.argv[1])
for z in list(b.Zones()):
    if z.GetZoneName() in sys.argv[3:]: b.Remove(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(sys.argv[2],b)
