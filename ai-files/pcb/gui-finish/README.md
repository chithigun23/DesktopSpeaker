# Finish the last 9 connections in the KiCad GUI (board RT-15H, 2026-11-03)

Open `DesktopSpeaker-RT15H.kicad_pro` in this folder with KiCad 10 (close the other DesktopSpeaker project first: it has a lock file). The board is `DesktopSpeaker-RT15H.kicad_pcb`; its rules file and library link are already beside it (`kicad-library` is a link to the project library).

State: DRC 0 violations, 9 unconnected (273 of 282 connections routed). Paste windows for the exposed pads, the LDO_3V3 stub fix and the footprint fixes are already applied. Teardrops are NOT yet generated (do that last, see below).

## The 9 connections (each in `ai-files/reports/routing-rt15.md` section 6, with the verified cause, suggested layer and corridor; numbers match this list)
1. I2S_BCK: U7-13 to the BCK stub near (147.15, 93.75): re-space the U7 bundle (row 1).
2. AUD_SDA: U7-15 to TP17-1 (row 2; needs row 1 first).
3. AUD_SDA: U24-23 to the AUD_SDA In2 track near (139.05, 83.10) (row 3).
4. C204-2 to R204-1 (row 4).
5. C205-2 to R205-1 (row 5).
6. USB_AUDIO_R: C201-1 to the USB_AUDIO_R track near (168.75, 56.43) (row 6).
7. USB_AUDIO_L: C200-1 to the USB_AUDIO_L track near (174.55, 60.88) (row 7).
8. HP_SEL_B: U3-51 to R235-1 (row 9: re-route BT_RST_N and BT_TX_IND first).
9. AUX_DET: U3-29 to R242-2 (row 10: reshape the AUX_TIPSW loop first).
(HP_EN, row 8 of the report, is already routed in this board.)

## Routing rules to keep (the project rule file already enforces most of them: run DRC often)
- 45-degree steps only, shortest runs. Audio 0.3 mm wide with 0.5 mm clearance; I2S 0.6 mm spacing; B.Cu only over In2 GND with a GND stitch via within 1.5 mm; slow nets may use In2 (rules 11 and 21).
- Do not move parts (only TP17 moved in this round).
- Keep DRC at 0 violations. Do not edit the rule file.

## When the 9 are done
1. Save the board in KiCad, close KiCad.
2. From the project root run: `python3 ai-files/fab/draft-rt14/ldo_stub_fix.py BOARD` (reports 'already applied'), then `bash ai-files/pcb/work-route15/scripts/td15.sh` or `ai-files/fab/draft-rt14/regen_final.sh BOARD OUTDIR --teardrops` (headless teardrop regeneration; expected about 1905 teardrop zones) and finally `regen_final.sh` without `--draft` until it prints RESULT PASS.
3. Tell me and I will adopt the board into DesktopSpeaker-kicad/, update the project rule file (rules 20 and 21), regenerate the position files, BOM, gerbers and STEP, and rebuild the CAD from the final board.
