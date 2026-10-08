# PCB placement v10b review (2026-10-08)

This is a read-only re-review of `ai-files/pcb/work-v10b/DesktopSpeaker-v10b.kicad_pcb`. It checks the fixes for `pcb-placement-v10-review.md` (B1-B3, M1-M8) against the v10b section of `pcb-placement-v10.md`, and then looks for new problems and overall routability. No board was modified.

Scratch files are in `ai-files/pcb/work-v10b-review/`:
- Scripts reused from `work-v10-review`: `dump.py` (now also dumps vias), `esc.py` (now counts reserved vias as blockers and includes U5/U8/U9/U12/U19/U22), `dec.py`, `near.py`, `occ.py`, `crop.sh`
- `pins.py`: pad dump for chosen parts
- `drc.json`: DRC re-run on a scratch copy
- Renders: `top.pdf`, `full.png`, and crops `u4/chg/u6/u7/u8/u11/u24/u25.png`

Coordinates are board mm. "Gap" means pad edge to pad edge. Clearances are checked against the board's own rules (`DesktopSpeaker-v10b.kicad_dru` plus the netclasses): 0.2 mm default, SWITCH 1.0 mm to non-GND tracks, POWER_HI 0.4 mm with a 0.5 mm minimum width, PVDD/SPK_OUT 0.3 mm.

Placeholders CPH1-7 and TPG1-2 were treated as real parts (they are being added to the schematic).

## Verdict: FAIL

v10b fixes most of what was asked:
- The U4 channel is open.
- The amp top edges are clear.
- The PD cell is under J1.
- The stray caps and the 3V_AO LDO have been re-homed.
- The DRC re-run matches the report: 0 courtyard and 0 clearance errors. What remains is 2 SW100 hole_clearance errors, 8 U11 drill errors, 32 silk warnings, 37 dangling reservation vias and 499 unconnected items.

Three local pin-escape blockers remain, each fixed by moving one to four 0402 parts:
- One is a v10b regression: the U7 PBTL bottom row.
- Two were inherited from v10 and missed by the v10 review: the U6/U7 DVDD/VR_DIG pins, and U11 CC2.

Six majors are also fixable locally. A v10c with the same floorplan is enough.

## Earlier items: status

| Item | Status | Evidence |
|---|---|---|
| B1 U4 channel / pin 27 | **Fixed** | C101 pad to C104 pad is 5.25 mm (x 148.94-154.19). GND vias at x 151.57, y 116.6/117.5/118.4. SW1 and SW2 each have about 1.9 mm above y 118.7. Pinch: about 0.78 mm beside the CPH1/CPH2 pads (y 118.8-119.4); acceptable, the pins are 0.2 mm wide. |
| B1 0.1 µF spots | Fixed, with a gap | CPH2/CPH1 are at a 0.7 mm gap and CPH3 at 0.6 mm. The CPH1/CPH2 GND pads face outward and have **no GND via** (m1). |
| B2 bootstraps / BAT_INT | Mostly fixed | C103 sits at pin 4 (0.53 mm) with SW1 vias. C106 is vertical, and the BAT corridor is open. C110 sits below pin 19, not at the top-right as suggested. That creates M3 (BATP via). Only 2 BAT_INT vias (M2). |
| B3 amp top pins | **Fixed** | The 3 mm band above pins 9-16 is empty on both amps: 0 parts, 0 vias. Escape is clear up to x 107-113 (U6). |
| M1 PD cell | Fixed | U11 is at (137.4, 55.8). USB_VBUS is 31.4 mm and CC 32 mm. The whole 3 A path is 100 mm. C2 is at the top-right. VBUS_PD has no via field (M2). |
| M2 C120/C126 | Fixed | 0.6 mm at U5/U21. |
| M3 3V_AO | Fixed | U12 is at (113.2, 77.2), with C123 at 0.8 mm. |
| M4 U24 | Fixed | C212/C215 are at 0.5 mm, and the crystal at 3.4/4.9 mm. The filter caps were left where they were, which is now M4 below. |
| M5 U25 | Fixed, except one small conflict | CPH4 is at 0.5 mm, with the 2x2 block and the FB column at the top right. The MODE/R256 conflict is m2. |
| M6 U15/U14 | Fixed | C152/C153/C190 are at 1.1/1.3/1.6 mm. |
| M7 U22/U8/U9 | Fixed | C222 is at 0.5 mm, C238 at 1.7 mm and CPH7 at 0.6 mm. C238's GND pad is 7 mm from U8 GND (M5). |
| M8 U11/U3 bands | Fixed | U11 bottom: 0 of 15 blocked. U3: 1 left pin, which is a 3V_AO pin that can tie at its tip. |

## BLOCKER

**B1. U7 (PBTL) bottom row: pins 27, 29 and 30 cannot be connected. This is a v10b regression.**
- C301 (191.95, 132.8) and C298 (193.0, 132.8) are vertical 0402s whose top pads sit **0.32 mm** below the pin tips (pads y 131.87, tips 131.55).
  - Pin 27 (OUT_B+, 191.79) sits over C301's BST_B- pad. Its only side gap, to pin 26 GND, is 0.22 mm.
  - Pin 30 (OUT_A+, 193.29) sits over C298's BST_A+ pad. Its side gap, to pin 31 GND, is 0.22 mm.
  - Pin 29 (BST_A-, 192.79) faces a 0.43 mm slot between the two caps. It needs at least 0.5 mm, and its cap C299 is below them.
- No trace of any width can leave pins 27 or 30 at 0.2 mm clearance. The BST_A+ route from pin 1 to C298's top pad would also wall in pin 30.
- Pins 27/30 are the paralleled PBTL half-bridges and carry full output current. Pin 29 is a bootstrap. All three are required.
- Fix: copy U6's working bottom arrangement (C286/C288 at 1.45 mm from the pins).
  - **C299 to (192.6, 133.31) r180.** OUT_A+ pad at 193.17 under pin 30; BST_A- pad at 192.03.
  - **C301 to (192.5, 134.61) r0.** OUT_B+ pad at 191.93; BST_B- pad at 193.07. BST_B- reaches it through the slot between the two caps, as C288 does on U6.
  - **C298 to (196.0, 132.0) r0**, in the bottom-right corner inside the OUT_A+ loop. BST_A+ pad at 195.43, near pin 1; OUT_A+ pad at 196.57, toward the trunk.
  - All three positions are free: L205 starts at y 133.01, HA2 at y 135.81 and C273 at x 198.63.
  - OUT_A+ then runs pin 2 → right, and pin 30 → C299 → right under C298, joining at x ≈ 197.5 down into L205. OUT_B+ runs pins 23/27 → C300/C301 → L206. Neither crosses anything.

**B2. U6 and U7, right side: DVDD (pin 6) and VR_DIG (pin 7) cannot both escape. Inherited from v10.**
- The C276 GND pad (113.05-113.67, 127.52-128.25) sits **0.55 mm** in front of pins 5-6. On U7, C289 does the same at 0.56 mm.
- The only exit is a single 0.55 mm slot, and it fits one track.
  - If pin 7 VR_DIG rises to C282 through it, pin 6 DVDD (to C281 at 113.49, 126.55) is shut in between pin 5, pin 7 and the C276 pad.
  - If DVDD takes the slot instead, it passes in front of pin 7 and shuts it in.
  - `esc.py` flags C276:5,6,7 and C289:5,6,7.
- Related, also inherited: **C285 (114.66, 128.65)** has its BST_A+ pad at the bottom, facing the OUT trunk.
  - The OUT_A+ trunk from pin 2 to L201 must pass the BST_A+ track from pin 1. So it either crosses it, or squeezes through the 0.68 mm C276/C285 slot at 0.28 mm or less, below the 0.4 mm SWITCH minimum.
- Fix for U6:
  - **C285 to (114.2, 131.2) r0**: BST pad at 113.63 by pin 1, OUT pad at 114.77 below the trunk. This is free space: L202 starts at y 133.01 and L201 at x 117.2.
  - **C276 to (113.75, 129.3) r0**: horizontal, PVDD pad about 0.2 mm from pins 3/4, GND pad outward with a via to In1 at about (114.9, 128.4). This is the same scheme already accepted for C278.
  - This frees pins 5-8. VR_DIG takes the inner riser at x ≈ 112.75 to C282. DVDD goes out to x ≈ 113.5 and up to C281. Pin 8 GND ties inward to the EP.
  - The OUT_A+ trunk gets about 0.9 mm between C276 (pad bottom 129.6) and the new C285 (pad top 130.9), then rises into L201 at x ≥ 117.6.
- Fix for U7 (mirror):
  - **C289 to (196.45, 129.3) r0** (PVDD pad at 195.88), with its GND via outward.
  - Move **C293 0.6 mm right, to (199.56, 128.45)**, to make room.
  - Keep the U7 OUT_A+ trunk below C289, running down to L205 (B1).

**B3. U11, top row: CC2 (pin 29) has no escape, and pins 36-38 cannot all leave. Inherited from v10.**
- Pin 29 (138.5-138.7) sits under the 0.40 mm gap between C182's two pads (CC1 pad 138.7-139.44, GND pad 137.56-138.30), 0.71 mm above the tip.
- Its filter cap C183 (140.4, 51.98) is on the other side of CC1. CC2 must therefore cross CC1, which goes straight up from pin 28 into C182, or the pin-32 VBUS riser. There is no room for a via.
- The v10 review's statement that "the CC caps are at 0.7/1.6 mm with the via-after-cap order possible" was wrong for CC2.
- Also in this row:
  - Pin 36 must reach R18 (138.0, 51.1), which is on the far side of the USB_VBUS riser (pin 32 to C184).
  - Pins 37/38 share a 0.8 mm band under C184, room for one track, plus the body gap.
- Fix: there is plenty of free space above, at y 40-49 (`occ.py`).
  - Put the CC caps in pin order, vertical, directly above the pins:
    - **C183 (CC2) at about (138.6, 52.2) r90**
    - **C182 (CC1) at about (139.6, 52.2) r90**
    - CC pads at the bottom, GND pads at the top, with one GND via each at y ≈ 51.0.
  - Tie corner GND pins 26/27 right to a via at about (140.6, 52.9), which is free once C183 moves. Tie pins 31/34 inward to the EP.
  - Move **C184 up about 1.2 mm**, to about (135.1, 50.9), and **R12/R18 up and left** into the free area (for example y ≈ 48.5-49.5). This gives pins 34-38 a band of at least 1.8 mm.
  - Put R18 at the left end of that band, so pin 36 does not cross VBUS.
  - Re-run `esc.py`: the U11 top row should show 0 blocked.

## MAJOR

**M1. U4: VBUS_PD has no entry and no via. REGN is cut off by the pins 8/9 column.**
- The C100 VBUS pad (146.6-147.78, 119.34-120.8) is boxed in:
  - the PMID row is 0.6 mm above;
  - C103 and the SW1 via (146.45, 121.75) are below;
  - its own GND pad and vias face outward, toward the trunk.
- The 3 A feed for pins 2/3 therefore has no copper path and no via.
- Pins 8/9 → CPH3 → C111 run as one column down from the corner. That column separates REGN caps C102/C109 from REGN loads R103/R108/R100/TP11, so REGN must cross VBUS.
- Fix (spots checked against the 0.4 mm POWER_HI and 0.2 mm pad rules):
  - VBUS_PD vias at **(148.45, 120.0) and (148.45, 120.7)**, beside the C100 pad. Pins 2/3 join them with a 0.5 mm track at y 120.73-121.23, which is 0.4 mm clear of the BTST1 stub.
  - VBUS_PD vias at **(148.55, 125.0)** (beside CPH3) and **(148.25, 127.0)** (left of the C111 pad).
  - Run REGN from C102 down the x ≈ 147.4 strip to C109. Then route it on F.Cu under C111 (y ≈ 130.8, between the C111 GND vias and TP11) to TP11 → R100/R103/R108.
  - On In2, the VBUS_PD island must reach both via pairs.
  - The CPH2 GND via moves to (147.85, 118.75) (see m1).

**M2. Power-layer transitions: almost none are reserved.**
- BAT_INT has only **2 vias** (157.9/158.7, 120.4) for a path of 5-8 A, and none at Q103.
  - The F.Cu corridor from Q103 pins 1-3 (171, 110) to C106 is free (x 158-171, y 112-121).
  - Either make BAT_INT an F.Cu pour of at least 4 mm and take Q103-G through one via, or use at least 8 vias at each end.
- SYS_RAW has **no** vias reserved at C104-C107, L200 or U14/U15.
  - Reserve 6-8 vias at x 161-163, y 115-119 (free).
  - Reserve a field beside the L200 pad 1 (142.78, 146.69).
- PVDD has 1 via, at U7 (186.09, 128.3). There are none at the U25 2x2 block, C275, C271 or C272, although the report says C271/C272 are "via-fed from In2".
- VBUS_PD at U11 has no vias. CPH5 (143.2, 59.0) also has its **GND pad toward pin 20** and its VBUS pad 3 mm away.
  - Flip CPH5 to r270, VBUS pad up at y ≈ 57.5.
  - Add 4-6 vias between CPH5 and D7.
- Add these as reservation vias now. Each one competes with the escapes above.

**M3. U4: BTST2 cannot pass the BATP via.**
- The order of pins 21-16 forces the fan-out PROG (pin 20, right) → BTST2 (pin 19, over the via to C110) → BATP (via) → ILIM/TS (down).
- BTST2 has to pass between the PROG track (y ≈ 122.2) and the BATP via (155.0, 123.0; top 122.7). The gap is 0.2 mm short even for a 0.15 mm track.
- Fix: move the BATP via to **(155.1, 123.35)**. Then BTST2 runs at y ≈ 122.6 over it and drops at x 155.75 into C110. ILIM passes at x ≈ 154.4.
- Route the SW2 bootstrap link (via at 156.55, 125.57 to via at 153.0, 115.2, on B.Cu) at least 1 mm from the BATP via and track. BTST2 passing 0.3-0.5 mm from the BATP via is inherent to the pin order; keep that run under 2.5 mm.

**M4. U24: the VIN1/VIN2 input filter is in the wrong order for the pins. Inherited.**
- Pins 4/3/2/1 (VINR1, VINL1, VINR2, VINL2; x 152.75-154.25) fan out to the right.
- Pin 2 (VINR2) sits under C206's VINL1 pad (0.66 mm gap), and its cap C209 sits behind C206.
- Pin 4 must reach C207 (155.65, 82.58) below pin 1's cap C208 (156.25, 81.12). So the four AUDIO nets cross one another (the 0.5 mm audio clearance applies).
- Fix: re-sort so the order along the fan-out matches the pin order.
  - Make a column right of the corner at x ≈ 156, from top to bottom: C207 (pin 4), C206 (pin 3), C209 (pin 2), C208 (pin 1), at about 1.1 mm pitch (y ≈ 79.6 to 82.9).
  - Put the GND pads outward, on a shared GND via column.
  - Place R201/R200/R203/R202 behind them in the same order.
  - The v10 request to move C206/C209 to x ≥ 156.5 still applies.

**M5. U8/U9: top-row fan-out needs vias, and there is no room for them.**
- U8 COM1 (pin 10, the left end) and COM2 (pin 6) both go to U9. COM1 has to cross pins 9-6.
- On U9:
  - HP_L (pin 10, the left end) goes to C239 on the right, across pins 9-6.
  - COM2 enters pin 7, on the far side of V+ (pin 8).
- R226 (172.49, 61.47) is 0.4 mm in front of U8 pins 7-9. CPH7 (184.29, 60.82) is 0.66 mm in front of U9 pins 7-9. That leaves no space for the 2-3 vias these crossings need.
- C238's GND pad is 7 mm from U8 GND pin 3, with no GND via.
- Fix:
  - Give both top rows a clear band of at least 1.6 mm: move R226 up 1.0 mm (C230 and C238 with it) and CPH7 up 1.0 mm.
  - Reserve audio-class vias for U8 COM1 (about (170.5, 61.9)), U9 HP_L and U9 COM2.
  - Give C238 and CPH7 each a GND via.
  - As an alternative, try U9 at r180, which turns HP_L/HP_R outward. Check the bottom row if you do.

**M6. Rules: the netclass widths and clearances cannot be met at the fine-pitch pins.**
- This is not placement, but it blocks a clean DRC.
- `switch_clear` (1.0 mm) excludes only GND and pads. As a result:
  - every OUT/BST track pair at the amp corners fails (BOOT is not exempt);
  - so does SW1 against the PMID stub at U4 pins 28/29 (0.45 mm pitch);
  - so does SW2 against SYS (pin 25).
- POWER_HI and PVDD require at least 0.5 mm width. The U4 VBUS pins are 0.2 mm wide at 0.4 mm pitch, and the U25 VOUT pins are 0.25 mm. Neither can be entered legally.
- Fix, before routing:
  - Add `B.NetClass != 'BOOT'` to `switch_clear`.
  - Add a final neck-down rule:
    ```
    (condition "A.insideCourtyard('U4') || A.insideCourtyard('U6') || A.insideCourtyard('U7') || A.insideCourtyard('U25') || A.insideCourtyard('U11') || A.insideCourtyard('U14') || A.insideCourtyard('U15')")
    ```
    with track_width min 0.2 and clearance min 0.2. Extend it about 1.5 mm with a rule area if needed.

## MINOR

- **m1. U4 HF caps.**
  - CPH2 and CPH1 have GND pads facing away from pin 27, and no via. Reserve GND vias at (147.85, 118.75) and (155.4, 119.1); both were checked against the C101/C104/C100/C106 pads.
  - The Q103-G track then runs at y ≈ 119.8 between the CPH1 via and the C106 BAT pad.
  - The HF loop closes through In1 to the pin-27 via column (about 3 mm). Record this as an accepted deviation from DS item 4, as agreed.
- **m2. U25 MODE.**
  - R256 (DNP, MODE to GND) sits on the CPH4 → C270 GND return. Pin 13 (MODE) lies between pin 14 (VOUT) and pin 12 (GND). MODE cannot reach R256 without crossing that return.
  - Since R256 is DNP: delete it (MODE floats = auto-PFM), or tie MODE hard to pin 12 in the schematic.
  - The CPH4 GND then takes a direct stub to pin 12.
- **m3. U6/U7 OUT_B+ neck.**
  - GND vias (103.4/104.2, 129.35) and (186.99, 129.35) leave OUT_B+ about 0.5 mm wide for about 3 mm under C278/C291.
  - Acceptable. Moving the outer via 0.5 mm up would widen it.
- **m4. U3.**
  - The CHG_INT track (pin 5) to R106 (177.14, 87.15) passes 0.04 mm from the C160 pad.
  - Pins 3-5 can only leave through the 1.6 mm channel at x 178-179.5 and turn up past C161.
  - Move R106 below C162, or route CHG_INT up the channel.
- **m5. U14** (inherited): the EN (pin 1) and FB (pin 4) tracks pass under/beside C140 (0.9 mm between its pads). Acceptable, or shift C140 0.5 mm left.
- **m6. U24 ADC_INT.** Pin 21 must reach R211 (145.15, 88.48), across the LRCK/BCK/DOUT risers to R206-R208. Move R211 to the right of pin 21, near R209, or take ADC_INT straight toward U3 and put the pull-down there.
- **m7. Power path lengths** (inherited floorplan, information only):
  - VBUS: 31 + 68 = 100 mm
  - SYS U4 → L200: about 32 mm direct
  - PVDD U25 → U6: about 56 mm; U25 → U7: about 36 mm
  - These are fine as In2/B.Cu pours of at least 4 mm, once M2's via fields exist.
- **m8. Known carry-overs, confirmed by the DRC re-run:**
  - SW100 NPTH footprint (2 hole_clearance errors)
  - U11 0.2 mm drills (8 errors)
  - LOGO1 over PTH pads, the J10 label at the edge and the SW101 silk (32 silk warnings)
  - U5 CELL (pin 2) is unconnected in the netlist; this is a schematic item.

## What is good
- The U4 channel, pin-27 GND column, C103 and C106 now follow the review. SW1 and SW2 run straight to L1.
- The amp top edges are completely clear, and the I2S/I2C exits have a channel about 5.8 mm wide.
- The U6 bottom bootstrap stack (C286/C288) and both left-side BST_B+ caps (C287/C300) are correct, crossing-free arrangements. B1 and B2 reuse them.
- C278/C291 (PVDD 100 nF, left) are at a 0.33 mm gap with a GND via 0.4 mm away. That works.
- The PD cell sits under J1 with a 100 mm total path. M2, M3, M4, M6 and M7 are fixed as asked. Courtyard and clearance DRC are clean.

## Fix order for v10c
1. B1 (U7 bottom: C299/C301/C298).
2. B2 (U6: C285 then C276; U7: C289, C293).
3. B3 (U11 top row).
4. M1-M3 (the U4 via reservations, BATP via) and M2 (the power via fields).
5. M4 and M5.
6. M6 rules.
7. Re-run `esc.py` from `work-v10b-review`. It counts vias as blockers. Target 0 blocked signal pins, apart from nc pins and GND pins tied to the EP. Then re-run DRC.
