import sys; sys.path.insert(0,'scripts')
from mkplan import P
p=P(sys.argv[1] if len(sys.argv)>1 else 'B1.kicad_pcb')
SCL='/AUD_SCL'; SDA='/AUD_SDA'; SD='/I2S_SDATA'; BCK='/I2S_BCK'; LR='/I2S_LRCK'
# remove the old U6 escapes of AUD_SCL and I2S_SDATA (they sealed pins 12/13/15)
p.seg_del_at(SCL,108.005,126.395,108.005,124.195); p.seg_del_at(SCL,108.005,124.195,124.205,107.995)
p.seg_del_at(SD,109.005,126.395,109.005,125.745); p.seg_del_at(SD,109.005,125.745,111.255,123.495)
p.seg_del_at(SD,111.255,123.495,111.255,122.245); p.seg_del_at(SD,111.255,122.245,118.905,114.595)
Y=117.0
# 5-track fan: verticals out of the pins, 45-degree NE runs at c = x+y: SCL 228.74, SDA 229.74, SDATA 230.98, BCK 232.19, LRCK 233.40
p.seg('F.Cu',SCL,0.3,(108.005,126.395),(108.005,125.9),(107.475,125.37),(107.475,121.265),(228.74-Y,Y))
p.seg('F.Cu',SDA,0.3,(108.505,126.395),(108.505,125.6),(108.175,125.27),(108.175,121.565),(229.74-Y,Y))
p.seg('F.Cu',SD,0.25,(109.005,126.395),(109.005,121.975),(116.385,114.595),(118.905,114.595))
p.seg('F.Cu',BCK,0.25,(109.505,126.395),(109.505,122.685),(232.19-Y,Y))
p.seg('F.Cu',LR,0.25,(110.005,126.395),(110.005,123.395),(233.40-Y,Y))
p.save('t/planU6.json')
