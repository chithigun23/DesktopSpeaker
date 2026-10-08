# PCB placement v10 review (2026-10-08)

This is a read-only critique of `ai-files/pcb/work-v10/DesktopSpeaker-v10.kicad_pcb`, judged as a placement for routability and best practice. The checklists are `pcb-layout-best-practices.md` and `pcb-routing-review.md`; the claims checked are in `pcb-placement-v10.md`. No board was modified.

Scratch files are in `ai-files/pcb/work-v10-review/`:
- `dump.py` produces `dump.json` (geometry and nets)
- `dec.py`: decoupling pad gap and cap GND to IC GND gap
- `esc.py`: 1 mm pin escape check
- `occ.py`: courtyard occupancy map
- `near.py`: parts in a region
- `crop.sh` with `top.pdf`, `top600.png` and the crops `chg/boost/u6/u7/u24/u11/u3.png`

Coordinates are board mm. "Gap" means pad edge to pad edge.

These decisions were treated as given: v10 enclosure depth, I2S star, charger SW nodes on F.Cu, J9/J10 handled by silk-by-net. The J9/J10 silk matches the nets: J9 = U6 channel A via L201/L202, J10 = channel B. The SW-on-top decision is raised again only where the current geometry cannot implement it (B1).

## Verdict: FAIL

The overall arrangement is a large step forward and is close to routable:
- The amp inductors sit at the OUT pins.
- Each device has its own PVDD 100 nF at a 0.6 mm gap.
- The CC caps are at U11, the crystals are at their ICs, and U15 is next to the BM83.
- There are no courtyard overlaps.

Three local clusters still cannot be routed to the rules: the U4 ring (B1, B2) and the top pin rows of U6/U7 (B3). Several support parts were left in their old cells, 35-95 mm from the ICs they serve (M2, M3, M7). All of these fixes are local, so a v10b with the same floorplan is enough.

## BLOCKER

**B1. U4 BQ25792: power ground pin 27 cannot be connected, and the SW channel is too narrow.**
- Pin 27 (151.57, 120.48) is the **only** power GND of the IC; pins 10/11 are ACDRV2/ACDRV1 tied to GND. It sits between SW1 (pin 28) and SW2 (pin 26).
- The ring leaves a 2.7 mm copper channel between the C101 and C104 pads (x 150.2-152.9, y 115.6-119.5). Both SW traces must run up this channel to L1 (pads at x 149.5 / 153.65, y 111). That leaves no room for a GND via at pin 27.
- The PMID and SYS cap GND pads (y 116.5, facing L1) cannot reach pin 27 on F.Cu without crossing SW1 or SW2. This is topological: the pin order is PMID | SW1 | PGND | SW2 | SYS.
- So "SW on F.Cu" and DS 12.1 item 4 ("0.1 µF loop and return on the top layer") cannot both hold. That is exactly why TI's 12.2 example sends SW through vias under the IC.
- Fix (keeps SW on F.Cu):
  - Spread the rows. Move C112/C108/C101 1.4 mm left (to x 143.4/145.8/148.2) and C104/C105/C107 1.4 mm right (to x 154.9/157.3/159.7). Move L1 up 1.0 mm (to y 110.0).
  - This gives a channel of about 5.5 mm: SW1 at least 1.3 mm | 0.25 mm | a column of 2-3 GND vias (0.3/0.6 mm) at x 151.57, y 117.4-119.2, fed straight off pin 27 | 0.25 mm | SW2 at least 1.3 mm.
  - Give every PMID/SYS/VBUS cap GND pad its own 2 vias, so each HF loop closes through In1, 0.2 mm below.
  - Record this as an accepted deviation from DS item 4.
- Alternative (TI method): SW1/SW2 drop through 3 vias each under the IC to In2, which frees the top for the 0.1 µF loops and a direct PGND pour. This contradicts the decision, so it is the user's call. It is the only way to meet DS items 1-4 literally.
- Either way, the three 0.1 µF 0402 caps (schematic gap) need reserved spots now:
  - SYS: at pin 25, about (153.0, 119.3)
  - PMID: at pin 29, about (150.1, 119.3)
  - VBUS: at pins 2/3, about (148.8, 121.2)

**B2. U4: the bootstrap caps are on the wrong side, and BAT_INT has no entry.**
- C103 (BTST1/SW1) is at (154.72, 124.08) on the right, but BTST1 is pin 4 on the **left** (149.67, 121.78) and SW1 leaves the top-left. Both nets would wrap around the package past BATP pin 18 (153.44, 122.98) and ILIM_HIZ. This breaks DS items 7 and 10, and the routing review's 2 mm BATP rule.
- C110's SW2 pad (156.03, 123.52) also puts switch copper next to pins 17-19.
- The BAT_INT 8 A entry to pins 22/23 is boxed in on three sides: by the SYS row above (lower edge y 119.46), C106's GND pad on the right (157.26, 120.89) and C103/C110 below (top y 122.94).
- Fix:
  - Rotate C106 to vertical at (155.0, 121.6), with the BAT pad at the pins and GND down. This opens a BAT_INT pour corridor from Q103 along y 120-122 at x > 155.6.
  - Move C103 to the top-left corner at about (148.4, 119.6). This needs the B1 row shift. Its SW1 pad takes the SW1 copper by a short via pair (low current, as in the TI EVM). Its BTST1 pad sits about 1 mm from pin 4.
  - Move C110 to the top-right corner at about (154.3, 119.6), next to SW2 / pin 19.
  - Keep R100/R102/R103/R108 below the IC.
- Also fix the layer plan here. SYS must leave the top-right row (y 117.5) and reach L200 pad 1 (142.78, 146.69), so it has to cross either VBUS_PD (left) or BAT_INT (right). Put SYS on B.Cu as an 8 mm pour (via arrays at C104-C107 and at L200/C261-C264), and put VBUS_PD and BAT_INT on In2. Reserve the via spots now.

**B3. U6/U7: the I2S/I2C/FAULT pin row (top, pins 9-16) has no F.Cu escape.**
- U6:
  - C284 (106.9-109.2, 124.6-125.7) sits in front of pins 14-16, and C282 (110.5-112.8) in front of pins 9-11. The pin-tip-to-pad gap is about 0.5 mm.
  - The only gap, 1.3 mm at x 109.2-110.5, then runs into C271 (22 µF, 108.8-112.7, 122.2-124.3).
- U7: C297 stands vertically in front of pins 13/14 (191.0-192.0, 123.3-125.6), with C296 0.35 mm from it and C295 on the right.
- The six digital lines (I2S x3, SDA, SCL, FAULT) would need vias under the amp. That kills the B.Cu heat spreader (review B2) and breaks the I2S rule of F.Cu with no vias.
- Fix: keep the full top edge of each amp clear to 3 mm.
  - U6:
    - C284 (AVDD, pin 19 left) to (105.0, 127.0) vertical beside C283.
    - C282 (VR_DIG, pin 7 right) to (114.1, 125.4) horizontal below C281.
    - C271 to the left of C272, at about (101.6, 125.3) vertical. It can be via-fed from the In2 PVDD island; the 0.1 µF C276/C278 stay at the pins.
    - Move R257 up to y 119.5.
  - U7, mirrored:
    - C297 (AVDD) to the left side beside C296, at about (188.1, 124.6).
    - C295 to (196.9, 125.2) horizontal below C294.
    - R258/R261 out of x 190-195.
  - Then fan the I2S out vertically from pins 12-14 in a 0.25/0.4 mm group.

## MAJOR

**M1. VBUS path: U11 is off the J1-U4 axis. Proposed VBUS_PD fix.**
- J1 (149, 26) to U4 VBUS (149.7, 121) is about 98 mm and fixed by the rear-edge connector and the central charger. U11 can only split it between USB_VBUS and VBUS_PD.
- At (121.4, 67.4), U11 is 28 mm off the axis: USB_VBUS 50 + VBUS_PD 63 = **113 mm** of 3 A path (v9b: 74 + 23 = 97).
- There is a free 22 x 22 mm block directly under J1 and left of U2, at x 126-148, y 39-61 (`occ.py`). The PD cell is 20.7 x 21.7 mm.
- Fix:
  - Move the whole PD cell there, with U11 at about **(137.7, 51.0) rot 0**: CC/VBUS_IN on the top and right, PPHV pin 20 at the lower right.
  - Move C2 from in front of pin 20 to the top-right next to pins 32/23, so the right-hand lower edge is free for the PPHV pour and its 15 vias.
  - Estimates: USB_VBUS about 27 mm, CC about 28 mm, VBUS_PD about 73 mm in one straight run (x 140-146 down to the U4 left side). Total about 100 mm (−13 mm).
  - Route VBUS_PD as an In2 pour at least 4 mm wide: about 20 mΩ, 60 mV, 0.18 W at 3 A on 0.5 oz. Make it at least 3.5 mm with 1 oz inner copper.
- VBUS_PD itself gets longer. What improves is the total path, and the hot-plug, TVS and CC paths stay at the connector (TPS25730 and USB practice, review M6).
- Not recommended: putting U11 next to U4 in the gap x 126-148, y 93-108. That gives VBUS_PD about 26 mm, but needs about 75 mm of unprotected USB_VBUS and the CC/BMC lines through the ADC column next to L1. It also needs the cell squeezed to 15 mm height.
- Add a local PPHV cap at U11: TPS25730 CPPHV is 47 µF typical, and today all PPHV capacitance sits at U4, 56-61 mm away. This is a schematic item. Reserve a 1206 spot at the pin-20 exit.
- Also give U19 (148.98, 37.5) a local USB_VBUS input cap (today's nearest is 37 mm). It falls within 10 mm of C184 after the move.

**M2. Gauge and supervisor bypass caps are at Q103, not at the ICs.**
- C120 (U5 MAX17048 VDD = cell sense) and C126 (U21 TPS3839 VDD; HANDOVER says it must be at U21) sit at (175.2, 109.0)/(175.9, 111.0), **77-78 mm** from U5/U21 at (100, 82-89).
- They also sit about 0.6 mm from the Q103 BAT_PACK pads 5-8, blocking the 8 A BAT_PACK pour entry from SW101.
- Fix: C120 to (101.6, 88.7), with its GND pad at U5 pin 4/EP. C126 to (101.6, 82.2). Route BAT_PACK sense as a dedicated thin Kelvin trace from the SW101 pin 1 side, not tapped off the pour.

**M3. The 3V_AO LDO U12 is stranded in the charger area.**
- U12 (165.15, 121.23) is fed from U20 VOUT at (92.6, 74.2), about 95 mm away. Its output cap C123 sits at U13 (100, 74), 78 mm away.
- Its loads are U13/U16/U17 (left) and U3 (186, 88).
- Fix: move the AO3V cell (U12 + C122 + C123) into the free space beside U20, at about **(104.5, 78)** (x 98-112, y 76-79 is free). This removes two 80-95 mm runs. C123 goes on pin 5, and C160/C161 stay at U3.

**M4. U24: the crystal Y200 occupies the AVDD/VREF decoupling spot.**
- Y200 (150.85, 78.91) sits directly over pins 6-10.
- That pushes VREF C212 to a 3.7 mm gap, AVDD C215 to 3.0 mm and C216 to 5.4 mm, all routed around the crystal.
- The crystal courtyard is 0.2-0.3 mm from C212 (VREF), C209 and C206 (VIN filter caps). That is a 24.576 MHz clock beside the reference and the inputs.
- Fix:
  - Put C212 (1 µF) and C215 (100 nF) as vertical 0402s directly on pins 6 and 8, at about (151.75, 80.9) and (150.75, 80.9).
  - Move Y200 to about (148.6, 77.2) with C226/C227 beside it. XI/XO stay 3-5 mm, F.Cu only, with a GND guard.
  - Move C206/C209 right to x ≥ 156.5, next to C207/C208.
  - Keep C214 (LDO) at pin 11.

**M5. U25 output caps are interleaved with the FB/COMP/ILIM network.**
- VOUT (14-16) and FB/COMP/ILIM (17-19) share the right side.
- C279 (156.1, 141.3) and C290 (159.3, 144.7) can only reach VOUT across the FB/COMP fan-out (C269 at 157.3, 144.8; R250/R251 at 158.7, 141-142).
- R253 (ILIM) is on the top-left (151.1, 141.0), so ILIM crosses over GND pin 20 / VCC.
- Only C270 (1 µF, 0.7 mm) and C277 (about 4 mm) actually close the hot loop to pin 12/EP.
- Fix:
  - Put the four 22 µF as a 2x2 block on the right/bottom-right at x 156.5-161, y 147-155, with PVDD pads toward pins 14-16 and GND toward pin 12/EP.
  - Move R250/R251/R254/C268/C269/R253 to the top-right, x 155-162, y 140-145, with short FB/COMP/ILIM traces running away from VOUT and SW.
  - Reserve a 0402 0.1 µF spot (schematic gap) at pins 14-16 / pin 12.

**M6. TPS63802 output hot loops (U15, U14).**
- U15 (BT supply): C190 10 µF at a 2.0 mm gap is the only near output cap. C152, C153 and C154 are 5.2, 6.6 and 9.0 mm away.
- U14: C142 is 5.3 mm away.
- In boost mode the output loop is the hot one, and here it radiates beside the BM83.
- Fix: put C152/C153 within 1.5 mm of pin 6 and the pin 3/8 GND, on the right of U15 around (119.5, 39-41). L3 shifts up 1 mm if needed. Move C154 to the U1 pin 23 end. For U14, move C142 next to C141.

**M7. The 3V3_AUDIO LDO U22 has no local output cap.**
- U22 (172.84, 51.84) pin 5's nearest cap is C241 at a 23.6 mm gap. C218/C222 are at the ADC, 35-40 mm away.
- TPS7A20 needs at least 1 µF at OUT.
- Fix: move C222 (1 µF) to U22 pin 5, at about (175.3, 50.9). Optionally move the whole U22/C221/C224 group to the free x 128-140, y 62-72 block next to the ADC.
- U8/U9 (V+ pin 8): the nearest 3V3_AUDIO caps are 23.7/11.7 mm away, although HANDOVER says each switch has a 0.1 µF. Find their refs (probably among C237/C238/C241 at U10) and put one on each pin 8.

**M8. U11 and U3 escape bands.**
- U11: R10/R13 are about 0.4 mm from the bottom pin tips, blocking 8 of 15 bottom pins (I2C, ADCIN, FAULT, SINK_EN, GND).
- U3: C161 blocks pins 3/4 (CHG_QON_SENS, PD_PLUG_EVEN) and C162 blocks pins 12-14 (NRST, HP_SEL_A/B), each about 0.35 mm from the tips.
- Fix: keep the 1 mm clear band.
  - In the M1 move, put R10-R17 at least 1.5 mm below the pin row.
  - Shift C160/C161/C162 left by 1.0 mm (to x 177.5). Turn C161 horizontal at (177.0, 86.0) so it sits in front of the VDD pins only.

## MINOR

- **m1. USB D+ pull-up stub.** R173 (1.5k on USB_DP) is at (158.76, 65.18), across U2 from R171, which makes a stub of about 10 mm. Move it next to R171, at about (147.6, 58.4).
- **m2. Test points.**
  - TP12-14 (I2S) at (135-137, 81-91) are 10-12 mm off the star point. Move them in line below R206-R208, at y about 93-95, x 145-150 (free).
  - There are only 3 GND TPs, none near the ADC, charger or boost. Add GND loops at about (144, 92) and (146, 132).
  - TP10 is 0.75 mm from the HA1 screw head.
- **m3. Mechanical.**
  - The rear-left quadrant (x 86-136, y 20-70) has no hole, yet carries the 8 mm BM83 overhang and the J8 programming header. Add an M3 at about **(92, 60)**, where x 86-115, y 56-70 is free.
  - Check in CAD that lid screws and inserts at the rear-left are at least 15 mm from the antenna (x 78-89, y 26-41). The CAD has no metal-clearance check.
  - HA1/HA2 courtyards are 0.75 mm from the 12 mm inductors, so only screwdriver access works (no nut driver).
- **m4. Footprint and DRC.**
  - SW100 NPTH peg is 0.175 mm from pad 1 (hole_clearance x2; fix the footprint).
  - U11's 0.2 mm thermal-via drills need a U11-scoped rule exception.
- **m5. Silk.**
  - A board-outline silk rectangle at about 0.4 mm inside the edge overlaps J1/J2/J3/J5/SW101 silk and lies over the J1 GND pads (fab will clip it). Remove it, or inset it 1 mm and break it at the connectors.
  - LOGO1 (B.Silk) covers PTH pads of H1/H4/H8/HA1/SW102. Shrink or move it to a clear B.Cu area.
  - The "J10 Front Right" text crosses the board edge and the L204 ref.
  - SW101 silk extends beyond x 213.8.
  - 50 silk findings in total, all warnings.
- **m6. Class-D filter returns.** In PBTL, C306/C307 sit 31 mm apart at opposite ends of U7's cell, and the AMP6 filter caps ground about 20 mm from U6. This is acceptable with solid In1 under the trunks. Keep In2/B.Cu free under them and stitch GND at each filter cap.
- **m7. Boost input.** C261-C264 sit at VIN pin 9, but 6-12 mm from L200 pad 1 (142.78, 146.69). Move one 22 µF to the L200 input pad. C275 (electrolytic) is 12 mm from U25/L200; keep it there or farther.
- **m8. BT audio routing.** BT_AUDIO_L/R run from U1 to the ADC/mux diagonally through x 120-160, y 40-80. After M1 they will pass the PD cell. Route them along y 42-45, then down at x ≥ 160, clear of CC/VBUS.

## What is good
- The PVDD 100 nF caps are at a 0.6 mm gap on both amps (C276/C278, C289/C291), and each device has its own set.
- U7 now has its own decoupling (old B3 fixed).
- Inductor gaps to the OUT pins are 5-7 mm, down from 10-21 mm.
- The CC caps are at 0.7/1.6 mm with the via-after-cap order possible.
- Y170 is tight at its IC.
- U15 is 7 mm from U1 pin 23.
- The antenna keep-out has no copper on any layer, the on-board antenna strip is 2.6 mm, and the antenna end overhangs as in BM83 Fig. 7-6.
- There are 0 courtyard overlaps.
- The EPs are clear for thermal-via arrays, and B.Cu under the amps is free.
- J1/J4/SW100 are at the rear edge and H7 sits 10 mm from J1.
- The board has generous free space (x 126-148, y 39-72; x 126-148, y 90-108), so every fix above is local and needs no floorplan change.

## Fix order for v10b
1. U4 ring (B1, B2), including the 0.1 µF spots and the SYS/BAT/VBUS layer plan.
2. Clear the top edge of U6/U7 (B3).
3. Move the PD cell under J1 (M1).
4. Re-home the stray support parts (M2, M3, M7).
5. U24 crystal/VREF (M4), U25 caps (M5), U15/U14 (M6), escape bands (M8).
6. Re-run `metrics_v10.py` plus `esc.py`, then DRC and the CAD check.
