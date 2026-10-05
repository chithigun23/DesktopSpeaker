import Part,glob,os
L='/home/chithi/Desktop/DesktopSpeaker/DesktopSpeaker-kicad/kicad-library/3d/'
for n in ["BM83SM1-00TA","PJ-307","TYPE-C-31-M-12","L_Sunlord_MWSA1265S","L_Coilcraft_XAL7070-XXX","STM32G071RBT6","TAS5825MRHBR","TPS61088RHLR","CP_Elec_8x10","PCM2902CDBR","PCM1862DBTR","Bourns_SRN6045TA-2R2Y","Coilcraft_XFL4015-471MEC","BQ25895RTWR","STUSB4500QTR","JST_B3P-VH","PinHeader_1x04_P2.54mm_Vertical","TPA6132A2RTER","TS5A23157DGSR","TPS26600PWPR_datasheet_EP","STL9P3LLH6","PD_C_1210"]:
    f=L+n+".step"
    if not os.path.exists(f): f=L+n+".stp"
    try:
        s=Part.read(f); b=s.BoundBox
        print("PROBE",n,len(s.Solids),"x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f"%(b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax))
    except Exception as e: print("PROBE",n,"ERR",e)
for f in ["/home/chithi/Desktop/DesktopSpeaker/ai-files/cad/parts/ND65_3D/ND65-4 and 8.step"]:
    s=Part.read(f);b=s.BoundBox;print("PROBE ND65",len(s.Solids),b)
    # flange thickness: slice at corner hole region
    import FreeCAD as App
    for x,y in [(23.3,23.3)]:
        for z in [22,21,20,19,18,17,16,15]:
            print("PROBE pt",z,s.isInside(App.Vector(x+4,y+4,z),0.01,True))
