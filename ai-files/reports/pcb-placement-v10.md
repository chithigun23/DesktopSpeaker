# PCB placement v10 (2026-10-08): placement fixes from the routing review

Placement only. No routing. Nothing in `DesktopSpeaker-kicad/` was modified, and `build_pcb_v9.sh` was not run.

## Files
- **Board**: `ai-files/pcb/work-v10/DesktopSpeaker-v10.kicad_pcb`. The project rules (`.kicad_pro` netclasses and `.kicad_dru`) and the stackup are copied in for DRC. `layout-v10.json` is the CAD export.
- **Render**: `ai-files/pcb/layout-v10-top.png`.
- **Floorplan**: `ai-files/pcb/floorplan-v10.json`. It is the annealed raw `work-v10/floorplan-v10-raw133_8z.json` with one hand edit: H8 is moved above the encoder.
- **Generator**: `ai-files/helpers/build_pcb_v10.sh` / `build_pcb_v10.py` (copy of v9), `snap_v10.py`, `floorplan_v10.py`, `fp_sp_v10.py` (annealer) and `fp_spec_v10.py`.
- **Checks**:
  - `metrics_v10.py` measures per-device decoupling, inductors, crystals, USB, I2S, BM83, test points, via room and escape band.
  - `v10_compare.py` builds the before/after tables.
  - `v10_cellcheck.py` is a cluster sandbox.
  - `v10_render.sh` and `v10_crop.py` make the renders.
  - `v10_stackup.py` copies the stackup.
- **CAD sandbox**: `work-v10/cad/`. These are copies of `build_speaker_cad.py` and `check_cad.py` that read `layout-v10.json`. Project CAD files are untouched.
- **Before**: `work-v10/baseline-v9b.kicad_pcb`, the v10 generator run with the v9 tables. It reproduces the v9b project placement exactly (0 parts moved).

## What changed (generator)
- **Class-D (M2)**:
  - U6 and U7 are rotated 180°, so the OUT pins face the inductors and the I2S/I2C pins face the board interior.
  - The inductors are REL anchors, placed with pad 1 next to the OUT pins.
  - U6: L202/L204 sit in a row in front of the IC, with the inline mounting hole between them (v9b request kept). L201/L203 sit beside the IC.
  - U7 (PBTL): L205/L206 sit in a row with the inline hole.
  - Routing corridors are kept free of passives: the front OUT channels, and the OUT_x+ path past the PVDD caps.
- **Per-device decoupling (B3)**:
  - Explicit ownership plus pin-group targets in the snap.
  - U6: C276/C271 at pins 3/4, C278/C272 at pins 21/22, C281/C280 at DVDD.
  - U7: C289/C273 at pins 3/4, C291/C274 at pins 21/22, C294/C293 at DVDD.
- **TPS61088 (B4)**: the four spare 22 µF (C277, C279, C290, C292) and C270 (1 µF) go to VOUT pins 14-16. C275 stays as the bulk cap.
- **BQ25792 (B6)**: a hand-placed ring in the datasheet 12.1 order:
  - PMID caps C101/C108/C112 in a row above pin 29, rail pad down.
  - SYS caps C104/C105/C107 above pin 25.
  - A SW1/SW2 channel between them up to L1 (pad gap 5.7 mm).
  - VBUS C100 (pins 2/3) and C111 (pins 8/9), REGN C102, BAT C106.
- **Crystals (M5)**: Y200 sits on U24 pins 9/10 (U24 is rotated 270°, so the I2S pins face the amps). Y170 sits on U2 pins 20/21.
- **USB (M6)**: USBAUD now sits next to PDIN. D1/D5/D6 stay directly behind J1. The CC caps C182/C183 move into the PD cell at the U11 CC pins.
- **BM83 (M7)**:
  - The BT Supply cell is merged into the Bluetooth cell. U15 is a REL anchor 7.5 mm from U1 pin 23, with L3 and the caps beside it on the pad side, away from the antenna.
  - The antenna keep-out margin now also applies along u.
- **I2S (M3)**:
  - The source series resistors R206-R208 sit directly below U24 pins 16-18.
  - The floorplan annealer has key-pin objectives: I2S source to both amps, USB, PVDD, SYS, BAT_INT, CC and battery. It also keeps the CAD rear-lid rocker zone free of modelled tall parts.
- **Test points (m5)**: test points are moved at least 3 mm from the edge after the snap (TP22, TP24).

## Results (v9b -> v10)
| IC / pin group | caps <= 3 mm (v9b -> v10) | nearest HF cap mm | nearest bulk cap mm |
|---|---|---|---|
| U6 PVDD 3/4 | 3 -> 1 | C276 1.21 -> C276 1.2 | C272 4.08 -> C271 5.82 |
| U6 PVDD 21/22 | 2 -> 1 | C278 1.2 -> C278 1.21 | C271 4.31 -> C272 4.23 |
| U6 DVDD 6 | 2 -> 1 | C281 1.58 -> C281 2.01 | C280 4.36 -> C280 3.91 |
| U7 PVDD 3/4 | 0 -> 1 | - -> C289 1.21 | - -> C273 4.75 |
| U7 PVDD 21/22 | 0 -> 1 | - -> C291 1.2 | - -> C274 4.37 |
| U7 DVDD 6 | 0 -> 2 | - -> C294 2.01 | - -> C293 2.99 |
| U25 VOUT 14-16 | 0 -> 1 | - -> C270 1.8 | - -> C277 4.2 |
| U25 VIN 9 | 1 -> 1 | C260 2.13 -> C260 2.13 | C261 3.57 -> C261 3.75 |
| U25 VCC 1 | 1 -> 1 | - -> - | - -> - |
| U4 SYS 25 | 1 -> 1 | - -> - | C104 3.0 -> C104 2.18 |
| U4 PMID 29 | 2 -> 1 | - -> - | C101 2.0 -> C101 2.16 |
| U4 VBUS 2/3/8/9 | 2 -> 2 | - -> - | C100 1.67 -> C100 1.72 |
| U4 REGN 5 | 0 -> 1 | - -> - | C109 7.47 -> C102 2.01 |
| U4 BAT 22/23 | 0 -> 1 | - -> - | - -> C106 1.72 |
| U15 VIN 10 | 1 -> 1 | - -> - | C150 2.21 -> C150 2.11 |
| U15 VOUT 6 | 1 -> 1 | - -> C191 5.69 | C153 2.58 -> C190 2.9 |
| U14 VIN 10 | 0 -> 0 | - -> - | C140 3.77 -> C140 3.77 |
| U14 VOUT 6 | 1 -> 1 | - -> - | C141 2.91 -> C141 2.9 |
| U1 3V8_BT 23 | 1 -> 1 | C191 1.91 -> C191 1.94 | C190 3.81 -> - |
| U1 SYS_PWR 24 | 0 -> 1 | C193 3.21 -> C193 3.0 | - -> - |
| U1 VDD_IO 25 | 1 -> 1 | C192 1.91 -> C192 1.94 | - -> - |
| U24 AVDD | 9 -> 8 | C208 1.41 -> C211 1.41 | C214 4.77 -> C223 3.78 |
| U2 VCC | 7 -> 5 | C177 1.9 -> C170 1.91 | C176 1.97 -> C176 1.96 |
| U11 VBUS | 4 -> 6 | C184 1.8 -> C182 1.3 | C2 1.8 -> C181 1.8 |
| U3 3V_AO | 3 -> 3 | C160 1.8 -> C160 1.8 | C161 2.97 -> C161 2.98 |

| Inductor | OUT pin -> pad gap mm (v9b -> v10) | filter cap gap mm |
|---|---|---|
| L201 (OUT_A+) | 20.7 -> 5.2 | 19.5 -> 4.9 |
| L202 () | 9.8 -> 6.6 | 18.0 -> 1.2 |
| L203 (OUT_B+) | 20.7 -> 5.2 | 27.7 -> 4.9 |
| L204 () | 9.8 -> 6.6 | 16.9 -> 1.2 |
| L205 (OUT_A+) | 9.2 -> 6.6 | 26.4 -> 4.9 |
| L206 (OUT_B+) | 10.8 -> 6.6 | 16.9 -> 4.9 |

| Crystal net | pad gap mm (v9b -> v10) |
|---|---|
| Y200 Net-(U24-XI) | 7.8 -> 1.5 |
| Y200 Net-(U24-XO) | 10.2 -> 3.3 |
| Y170 Net-(U2-XTI) | 6.0 -> 1.2 |
| Y170 Net-(U2-XTO) | 6.0 -> 3.0 |

| I2S net | source -> U6 | source -> U7 | U6 -> U7 (v9b -> v10, octilinear mm) |
|---|---|---|---|
| /I2S_SDATA | 135 -> 55 | 109 -> 57 | 62 -> 83 |
| /I2S_BCK | 131 -> 53 | 106 -> 59 | 62 -> 83 |
| /I2S_LRCK | 139 -> 51 | 114 -> 61 | 62 -> 83 |

- /USB_DP J1 -> D1 -> R -> U2 chain: 91 -> 39 mm (J1 -> U2 direct 78 -> 36)
- /USB_DN J1 -> D1 -> R -> U2 chain: 90 -> 40 mm (J1 -> U2 direct 79 -> 36)
- CC caps to U11: C182 67.2 -> 1.3 mm, C183 62.7 -> 2.2 mm; VBUS J1 -> U11 74 -> 50 mm
- TVS gap to the J1 body: {'D1': 1.64, 'D5': 3.55, 'D6': 5.3} -> {'D1': 1.64, 'D5': 3.55, 'D6': 5.3}
- BM83: U15 -> U1.23 117.8 -> 7.5 mm, L3 115.0 -> 10.8 mm; parts within 3 mm of the antenna keep-out [['R181', 2.46], ['C195', 2.15], ['R187', 1.68]] -> []
- Board 137.0 x 127.9 = 17522 mm2 -> 127.6 x 137.7 = 17571 mm2
- Test point closest to the edge: [1.44, 'TP22', 'BT_UART_RX'] -> [3.07, 'TP24', 'GND']
- GND cap pads without room for a 0.6 mm via within 1 mm: ['C276'] -> ['C291'] (of 121)
- 1 mm escape band around the IC covered by other courtyards: U4 0.61 -> 0.49, U6 0.34 -> 0.20, U7 0.29 -> 0.18, U25 0.31 -> 0.32, U11 0.53 -> 0.53, U24 0.57 -> 0.53, U2 0.15 -> 0.17, U1 0.00 -> 0.00, U15 0.43 -> 0.21, U3 0.24 -> 0.23
- Courtyard rectangle overlaps: 0 -> 0

Power-path distances (octilinear, pin to pin, mm):

| Path | v9b | v10 |
|---|---|---|
| PVDD U25 -> U6 | 74.5 | 50.2 |
| PVDD U25 -> U7 | 30.5 | 47.5 |
| SYS U4 -> U25 | 40.1 | 28.9 |
| BAT_INT Q103 -> U4 | 24.8 | 22.3 |
| BAT_PACK J5 -> Q103 | 98.2 | 34.4 |
| VBUS_PD U11 -> U4 | 22.8 | **63.4** (worse) |

Distances are pad centre to pad centre unless stated as a gap. The decoupling table metric is the nearest pin of the named group, centre to centre. I2S figures are octilinear source-to-sink estimates, not routed lengths.

- **Area**: 127.5 x 137.6 mm = 17,544 mm². v9b is 136.9 x 127.8 = 17,496 mm², so v10 is +0.3% (limit +5%).
- **DRC**:
  - 0 courtyard, overlap and outline findings.
  - The rest are the inherited types: SW100 hole_clearance 2, U11 0.2 mm via drill 8, silk 50 (v9b 43). The silk findings are mainly test point and title labels.
  - 499 unconnected (unrouted).
- **Holes**: 10 holes; all are valid in DRC.
  - The inductor-row holes in AMP6 and AMP7 are kept.
  - A hole sits between AMP6 and the boost at IC level, which is where the old "between the amps" hole is.
  - The encoder has H8 above it and H4 at its lower right. This differs from v9b's two holes on its right side.
- **CAD sandbox** (`work-v10/cad/interference.md`): 0 unintended overlaps; woofer chamber net 0.525 L. The enclosure gets 10 mm deeper (196 to 206 mm) because the board is deeper.
- **Via room / escape band**: only C291 (U7 PVDD 0.1 µF) has no 0.6 mm via spot within 1 mm. Its GND pad sits next to pin 20 and the EP, so it can tie there on F.Cu. The EPs are clear for 4x4+ thermal via arrays; all parts are on top, so B.Cu under the amps is free.

## Schematic gaps (not edited)
1. U4 BQ25792 needs a 0.1 µF 0402 HF cap on each of SYS, PMID and VBUS (datasheet 12.1 items 1-3, "closer than the 10 µF"). The ring leaves the bulk caps closest; when the caps are added they belong directly at pins 25, 29 and 2/3.
2. U25 VOUT has no 0.1 µF 0402 HF cap (review B4). C270 is 1 µF 0805.
3. U6/U7 now have 2 x (22 µF + 0.1 µF) PVDD plus DVDD sets per device, and U25 has 4 x 22 µF + 1 µF. This uses all 13 PVDD caps, so there is no spare.

## Open items and decisions needed
1. **J9/J10 orientation**: with U6 rotated 180°, channel A (J9 "Front Left") ends up on the right of the AMP6 cell and J10 on the left. Either relabel or swap the harness, or swap L/R in the TAS5825M input mixer.
2. **Enclosure depth vs rocker**: a shallower floorplan (`raw108_8k`, 134.7 x 125.7 mm, about 2 mm shallower than v9b) puts J3 under the CAD rear-lid rocker stand-in at x 66 (130 mm³ clash). Choose v10 as is (+10 mm depth), or move the rocker in the enclosure and use 108k.
3. **I2S**:
   - The star branches are 51-61 mm; LRCK to U7 is 61 mm, about 1 mm over the 60 mm plan limit.
   - U6 to U7 is 83 mm, so a daisy chain would be about 135 mm.
   - Decide the star or series-terminated topology. The 20.4 mm analogue to class-D/boost separation is what limits it.
4. **SW1/SW2 routing**: TI's own layout example (BQ25792 DS 12.2) routes SW to vias under the IC and out on an inner layer to make room for the 0.1 µF caps. The review asked for F.Cu with no vias. The channel left between the PMID and SYS rows is 1.7 mm.
5. **VBUS_PD U11 -> U4** got longer (22.8 to 63.4 mm, a 3 A path; pour it on L3).
6. Smaller items:
   - Filter caps sit 4.9 mm from the outer inductors' far pads (1.2 mm for L202/L204); the inductor body sets this.
   - I2S test points TP14/TP13 are not yet in line (12-19 mm detour).
   - The rear-right corner, under the rocker, is left free of modelled parts.

## v10b (2026-10-08): fixes from `pcb-placement-v10-review.md`

Same floorplan, local fixes only; placement only, no routing. The project board was not touched.

**Files**
- Board: `ai-files/pcb/work-v10b/DesktopSpeaker-v10b.kicad_pcb`, with `layout-v10b.json` (CAD export), `fix-v10b.log` (every move and nudge), `drc-v10b.json` and `metrics-v10b.json`.
- Render: `ai-files/pcb/layout-v10b-top.png`.
- Generator: `build_pcb_v10b.sh` runs two stages.
  - `build_pcb_v10b.py` is the v10 generator with two cell moves (`V10B_MOVE`), the border change and `floorplan-v10b.json` (v10 plus H9). It writes `DesktopSpeaker-v10b-base.kicad_pcb`. With no cell moves it reproduces v10 exactly (0 of 351 parts differ).
  - `fix_v10b.py` then applies the local moves. It lifts all moving parts first, places each one at its target or the nearest legal spot within a small radius, and keeps the escape bands as keep-outs.
- CAD sandbox: `work-v10b/cad/`.

**Changes** (82 parts moved in `fix_v10b.py` and 22 by the two cell moves; 9 placeholders and 37 vias added)

- **B1/B2, U4.**
  - L1 is 1 mm up. The PMID row is 1.4 mm left and the SYS row 1.4 mm right, both 1 mm up. The pad-to-pad channel for SW1 | PGND | SW2 is 5.3 mm (was 2.7).
  - Pin 27 has a column of 3 GND vias (x 151.57). Each PMID/SYS cap gets 2 GND vias, C100/C111 2 each, C106 2.
  - 0.1 µF placeholders: CPH2 PMID and CPH1 SYS at a 0.7 mm gap, CPH3 VBUS at pins 8/9 at a 0.6 mm gap, with its GND pad on pins 10/11.
  - C103 sits at BTST1 pin 4 (0.5 mm), and C110 below BTST2 pin 19. Both have SW via pairs.
  - C106 is vertical (BAT pad 2.3 mm from pins 22/23) with 2 BAT_INT vias to In2. CHG_INT and PROG leave under C106. R102 moved right of C106; R108 and R100 stay below.
  - BATP has a reserved via (155.0, 123.0).
- **B3, U6/U7.** The 3 mm band above pins 9-16 is empty: escape-blocked top pins went from 4 to 0 on each amp.
  - Left side, so that PDN, GVDD and AVDD escape without crossings:
    - PDN runs up beside the pins to R257/R258.
    - The GVDD/AVDD caps are horizontal in line with pins 18/19.
    - The PVDD 0.1 µF (C278/C291) is horizontal in line with pins 21/22, 0.3 mm from the pins, with its GND pad on vias to In1.
    - The BST_B+ cap sits below the OUT_B+ corridor.
  - Right side: VR_DIG sits under the DVDD row, and C280/C271 are above it, outside the band.
  - U7: C301/C298 are under pins 27-30 between the OUT channels; R261 and C295 are on the right.
- **M1/M8, PD cell.** U11 is at (137.4, 55.8), in the free block under J1. The PD tile moved with it; the BM83 and USBAUD tile edges are clipped to the free space.
  - USB_VBUS J1->U11 is 49.7 -> 31.4 mm, CC 50 -> 32 mm, VBUS_PD U11->U4 63.4 -> 68.4 mm. The whole 3 A path is 113 -> 100 mm.
  - C2 is at the top right.
  - R10/R11/R13/R17 are 1.5 mm below the pin row: blocked bottom pins went from 8 to 0.
  - Placeholders: CPH5 (47 µF, 1206, PPHV) at pin 20 at a 3.3 mm gap, and CPH6 (U19 input) at a 0.6 mm gap.
- **M2.** C120 sits at U5 pins 3/4 (0.6 mm) and C126 at U21 pin 3 (0.6 mm); both were 77 mm away.
- **M3.** The 3V_AO cell (U12 + C122) moved into the space the PD cell left (113.2, 77.2), as its own tile. That is 21 mm from U20 (was 95 mm). C123 sits on pin 5 (0.8 mm).
- **M4, U24.** C212 (VREF) and C215 (AVDD) are on pins 6/8 (0.5 mm; were 3.7/3.0 mm).
  - Y200 moved left with C226/C227. XI/XO pad gaps are 3.4/4.9 mm (were 1.5/3.3), F.Cu, with no crossings.
  - C214 moved 0.6 mm left.
- **M5, U25.**
  - CPH4 (0.1 µF placeholder) is at pins 14-16 (0.5 mm); C270 next to it (1.7 mm).
  - The 2x2 block of 22 µF is C270/C290 over C277/C292, with C279 beside it.
  - The FB/COMP/ILIM network is a column at the top right (R253, R254/C268, C269, R251, R250), away from SW. R256 (MODE) sits at pin 13.
  - C275 moved to (166.7, 152.1). C261/C264 moved 0.4 mm down.
  - m7: C262 sits at the L200 input pad.
- **M6.**
  - U15: C152/C153/C190 are at VOUT pin 6 (1.1/1.3/1.6 mm; was 2.0 mm for C190 only). L3 moved 1 mm up. The FB divider is on the left. C154 is at the U1 end.
  - U14: C142 is next to C141 (3.3 mm).
- **M7.**
  - C222 sits at U22 pin 5 (0.5 mm; was 23.6 mm).
  - C238 is the U8 V+ cap (1.7 mm; nudged 1.45 mm off its target by the input network).
  - CPH7 is a placeholder at U9 V+ (0.6 mm). C237/C241 stay at U10 VDD.
- **M8, U3.** C161/C162 moved 1 mm left and C160 0.34 mm left (R106 is beside it). Blocked left pins went from 6 to 1.
- **Minors.**
  - m1: R173 sits next to R171.
  - m2: TP12-14 form a column under R206-R208 (I2S TP detour 18.6 -> 4.8 mm). GND test loops TPG1 (141.0, 91.6) and TPG2 (146.0, 132.0) are placeholders. TP10 is 1.5 mm further from HA1.
  - m3: new M3 hole H9 at (92, 60), 19 mm from the antenna.
  - m5: the board border silk is inset 1 mm and broken at edge parts.

**Validation**
- DRC: 0 courtyard and 0 clearance findings. The errors are only the inherited ones (SW100 hole_clearance 2, U11 0.2 mm drill 8).
  - Silk findings: 32 (v10: 50).
  - via_dangling: 37. These are the reservation vias, which have no tracks yet.
  - 499 unconnected (unrouted).
- Metrics: escape-band cover changed as follows:

  | IC | v10 | v10b |
  |---|---|---|
  | U4 | 0.49 | 0.35 |
  | U6 | 0.20 | 0.08 |
  | U7 | 0.18 | 0.13 |
  | U11 | 0.53 | 0.38 |
  | U3 | 0.23 | 0.14 |
  | U15 | 0.21 | 0.46 |

  U15 rose because its caps are now on VOUT, as asked. GND cap pads without via room: 0 (was 1).
- Area: unchanged, 127.6 x 137.7 mm (same outline).
- CAD sandbox (`work-v10b/cad/interference.md`): 0 unintended overlaps (7 intended); woofer net 0.525 L. It includes the moved C275/L1/L3/U11 and H9.

**Deviations from the review text**
- R257 sits left of the band (106.7, 121.8) instead of at y 119.5. This keeps PDN from crossing the I2S fan-out.
- C206/C209 were not moved: the crystal is now more than 4 mm from them, and moving them would lengthen the VIN filter loops.
- C271/C272 (PVDD 22 µF) are 5.5/4.2 mm from the pins and via-fed from In2, as the review allows.
- C278/C291 changed to horizontal (GND by via, not a pin-20 F.Cu loop). This is the price of crossing-free GVDD/AVDD escapes.
- CPH4 has no GND via (no room). Its GND reaches the C270 GND pad through a 0.42 mm gap between the C270 PVDD pad and R256.

**Open items**
1. **Schematic additions** for the placeholders. They are in `fix_v10b.py` only, with refs CPH*/TPG* and a Note field:
   - CPH1-3: 0.1 µF on U4 SYS, PMID and VBUS.
   - CPH4: 0.1 µF on U25 VOUT.
   - CPH5: 47 µF on PPHV.
   - CPH6: 1 µF U19 input.
   - CPH7: 0.1 µF U9 V+. The schematic has 2 x 0.1 µF for the 3 needs in HANDOVER (U8 V+, U9 V+, U10 VDD).
   - TPG1/TPG2: GND test points.
2. **MAX17048 U5 pin 2 (CELL) is unconnected in the netlist.** The datasheet connects CELL to the cell positive (usually tied to VDD). This needs a schematic check. It was found during M2.
3. **Not done (library or routing items):**
   - m4: SW100 NPTH footprint fix and the U11 via-drill rule.
   - m5: LOGO1 over PTH pads, the "J10 Front Right" label at the edge, and SW101 silk.
   - m6/m8: routing notes.
4. **Routing-time tight spots:**
   - U4: VBUS pins 2/3 leave above C103; the BTST1/REGN stubs are about 0.25 mm apart.
   - U8/U9: the top-row fan-out runs around the V+ cap.
   - U7 PBTL: OUT pins 27/30 jog around C301/C298.
   - U11: the top pins are still blocked by C182/C184 (unchanged, 7 pins).

## v10c (2026-10-08): fixes from `pcb-placement-v10b-review.md`, real schematic parts

Same floorplan, local fixes only, placement only. The project board was not touched.

**Files**
- Board: `ai-files/pcb/work-v10c/DesktopSpeaker-v10c.kicad_pcb`, with `layout-v10c.json`, `fix-v10c.log`/`fix-v10c.json` (moves, 110 reservation vias), `drc-v10c.json`, `metrics-v10c.json`. Render: `ai-files/pcb/layout-v10c-top.png`.
- Generator: `build_pcb_v10c.sh` re-exports the netlist (kicad-cli 10.0.6) into `work-v10c/ds_net.xml`, then runs:
  - `build_pcb_v10c.py`: the v10b generator. The new schematic parts (C311-C316, TP26, TP27) are loaded from the netlist but kept out of the greedy placer. The base reproduces the v10b base exactly (0 of 352 parts differ).
  - `fix_v10c.py`: the v10b fixes plus the v10b-review fixes. The placeholder code paths are gone: CPH1-6 -> C311-C316, TPG1/2 -> TP26/TP27. CPH7 is dropped, and C237 is now the U9 V+ cap.
- Checks: `work-v10c/review/` (copies of the v10b-review scripts plus `verify_v10c.py`, with `esc-v10c.txt`, `dec-v10c.txt`, `verify-v10c.txt` and crops). CAD sandbox: `work-v10c/cad/`.

**Changes** (all relative to v10b; gaps are pad edge to pad edge)

| Item | Change | Result |
|---|---|---|
| B1 U7 PBTL bottom | C299 (192.6, 133.31) r180, C301 (192.5, 134.61) r0, C298 (196.0, 132.1) r0 | Pins 27/29/30: nearest copper 1.45 mm (same as U6). `esc.py` U7 B: 3 -> 0 blocked |
| B2 U6/U7 right side | C276 (113.75, 129.3) r0 and C289 (196.53, 129.3) r0, PVDD pad 0.31 mm from pins 3/4, GND via outward. C285 (114.2, 131.2) r0. C293 0.9 mm right | Pins 5-8 lateral clear 0.63 mm. OUT_A+ gap C276 -> C285: 1.28 mm. U6/U7 R: 3 -> 0 blocked |
| B3 U11 top | C183/C182 vertical over pins 29/28 (0.57 mm), each with a GND via. Corner GND via. C184 at (135.5, 50.9) with a USB_VBUS via. R12/R18 at (132.1/133.6, 48.3) with GND vias. PD_PLUG_EVENT via | Pins 34-38: 1.98 mm band; C6/C184 channel 1.38 mm. U11 T: 7 -> 3 blocked (GND pins 26/27 tie to the corner via; pin 30 is nc) |
| M1 U4 | VBUS_PD vias (148.45, 120.0/120.7), (148.55, 125.0), (148.25, 127.0). GND vias for C312 and C311 (m1) | - |
| M2 via fields | BAT_INT: 8 at C106 and 9 at Q103 (was 2). SYS_RAW: 8 at C104-C107 and 7 beside L200 pad 1. PVDD: 5 under C277/C292, 3 at C275, 2 each at C271/C272/C273. C315 at r270 (VBUS pad up, GND pad away from pin 20) with 4 VBUS_PD vias toward D7 | 110 reservation vias (v10b: 37) |
| M3 | BATP via moved to (155.1, 123.35) | U4 R VIA:19 cleared |
| M4 U24 | Filter re-sorted in pin order: rows at a 1.3 mm pitch (y 77.05-80.95), each row shunt cap (node pad left) / GND via / series R (0.65 mm lower) / coupling cap. Pin 4 -> C207/R201/C201, pin 3 -> C206/R200, pin 2 -> C209/R203/C203, pin 1 -> C208/R202/C202. C216 moved above the rows, C212 0.05 mm left. R223/C233 re-placed about 1 mm away | Fan-out is crossing-free on F.Cu. Shunt-cap gaps for pins 4/3/2/1: 4.9/3.6/2.2/0.8 mm (cost of pin order). U24 R: 1 -> 0 blocked |
| M5 U8/U9 | R226, C230 and C238 1.07 mm up; C237 at the U9 V+ spot, 1 mm higher. GND vias for both. Audio vias: U8 COM1, U9 HP_L, U9 COM2. C239 0.25 mm right and 0.4 mm up | U8 top band 1.64 mm. V+ caps at 2.8 mm (U8) and 1.6 mm (U9) |
| Minors | m3: U6/U7 outer PVDD-cap GND via moved up. m4: R106 below C162. m5: C140 0.5 mm left. m6: R211 at (150.6, 92.45), right of pin 21 | U14 L: 3 -> 0; U24 L: 2 -> 1 blocked |
| Real parts | C311-C314 on the CPH1-4 spots (0.6-0.69 mm). C316 (0805) at U19 pin 8 (0.64 mm). TP26 at (141.0, 90.9), 0.7 mm higher because the 5010 silk is larger, label on the left. TP27 on the TPG2 spot | - |

**Validation**
- DRC: 0 courtyard and 0 clearance findings. The errors are only the inherited ones: SW100 hole_clearance (2) and the U11 0.2 mm drills (8).
- Silk: 32, the same as v10b. via_dangling: 110 (the reservation vias). 499 unconnected (unrouted). Schematic parity: 0.
- `esc.py`: the remaining blocked pins are inherited or intended:
  - U4 L: nc pins 1/6/7; VBUS pins 3/8 by the review's own M1 entry.
  - U4 R: pin 17 ILIM passes the BATP via at x 154.4, per the review.
  - U11 T: GND corner pins and nc pin 30.
  - U24: pins 5 (nc) and 13/14/7.
  - U3, U5 and U10 R are unchanged.
- Metrics: escape-band cover changed as follows:

  | IC | v10b | v10c |
  |---|---|---|
  | U11 | 0.38 | 0.25 |
  | U24 | 0.56 | 0.42 |
  | U7 | 0.13 | 0.11 |

  All other ICs are unchanged. Courtyard-rect overlaps: 0. GND cap pads without via room: 0.
- Area: unchanged, 127.6 x 137.7 mm (17,571 mm²).
- CAD sandbox (`work-v10c/cad/interference.md`): 0 unintended overlaps (7 intended); woofer net 0.525 L. None of the modelled parts moved; the test points and 0402-1206 parts are not modelled.

**Open items**
1. M6 rules (not edited; they need exemptions before routing):
   - `switch_clear` (1.0 mm): exempt `BOOT`. Also add a fine-pitch neck-down for SW1/SW2 against PMID/SYS at U4 pins 25-29.
   - `width_power` (0.5 mm): exempt inside the U4 courtyard (VBUS pins 2/3/8/9, 0.2 mm pads at 0.4 mm pitch) and the U25 courtyard (VOUT pins 14-16, 0.25 mm). PVDD at U6/U7 pins 3/4/21/22 also needs it.
   - The neck-down rule should cover U4, U6, U7, U11, U14, U15 and U25, plus U24 and U8/U9:
     - `width_audio` 0.25 mm at a 0.5 mm pitch leaves exactly 0.25 mm. The U24 VIN risers pass C212 (VREF) at 0.2 mm only if they stay centred.
     - `audio_clear` (0.5 mm to non-AUDIO tracks) cannot be met at the U8/U9 top rows (V+, HP_SEL) or at U24 pin 5-8.
   - `vbus_clear` (0.4 mm): the U4 pin 2/3 stub against BTST1/REGN.
   - `fine_pitch` (pad-pad 0.1 mm for J1/U11/U19) is unchanged.
   - U11 needs a footprint drill exception (0.2 mm).
2. Schematic items:
   - R256 (DNP, U25 MODE) still sits on the C314 GND return (v10b review m2). Delete it, or tie MODE to pin 12.
   - U5 CELL (pin 2) is unconnected.
   - U10 now has only C241 (1 µF, 1.9 mm) on 3V3_AUDIO, with no 100 nF.
3. Routing notes:
   - U11: C184's USB_VBUS pad is fed by its via (136.55, 49.5); the J1 -> pin 23 VBUS stays on the right.
   - CC2 rises at x ≈ 137.85 between C184 and C183. CC1 leaves C182 to the right below TP1.
   - Pins 36-38 run up the C6/C184 channel in the order 38, 37, 36.
   - U24 coupling caps: C200 (pin 3 chain) is still in the USB-audio cell at (158.1, 47.1).
   - R223/C233 (HP bias) moved about 1 mm.

## v10d (2026-10-08): PVDD lane fix from `pcb-placement-v10c-review.md` (B1) and m5

Board `ai-files/pcb/work-v10d/DesktopSpeaker-v10d.kicad_pcb`, built by `build_pcb_v10d.sh` (copy of v10c; `fix_v10d.py` adds a v10d block at the end). The project board is untouched.

**Changes (exactly the review's list)**
- C276 to (114.15, 128.85) r90; C278 to (104.0, 129.36) r180; C289 to (196.94, 128.85) r90; C291 to (186.9, 130.45) r270. All landed on target with no nudge.
- GND vias deleted at (104.2, 129.35) and (186.99, 128.95). GND via added at (186.05, 131.0).
- PVDD vias (0.6/0.3) at (115.4, 129.45), (116.2, 129.45), (106.2, 129.3), (105.4, 129.3).
- m5: two more VBUS_PD reservation vias at U4 at (148.3, 128.0) and (147.65, 124.6). The first pick (148.4, 126.0) broke `vbus_clear` against the REGN via at (147.5, 126.0).
- Vias: 115 (110 + 1 + 4 + 2 - 2).

**Validation**
- DRC: 0 courtyard and 0 clearance findings. Only the inherited findings remain: SW100 hole_clearance (2), U11 drill (8), silk 32, via_dangling 115 (reservation vias), unconnected 499. Schematic parity: 0.
- `esc.py`: U6 and U7 are 0 blocked on all four sides (v10c: also clear). The other ICs are unchanged.
- `fan2.py U6 U7` (copies in `work-v10d/review/`): 30/30 each, after the rip-up retry.
- `route1.py` PVDD lane (F.Cu, 0.3 clearance, 1 mm pin neck, fan-out tracks as obstacles):

  | Path | Width found |
  |---|---|
  | U6 pin 3 to C276 | 0.9 mm (max 0.88) |
  | U6 pin 22 to C278 | 0.9 mm (max 0.89) |
  | U7 pin 3 to C273 | 0.9 mm (max 0.89) |
  | U7 pin 22 to C274 | 0.8 mm (max 0.76 at the narrowest point; the router tolerance is 0.02 mm per side) |

  The U7-left value is 0.04 mm below the review's 0.80 because C291 is at x 186.9 (the review's what-if used 186.8). It stays at the 0.8 mm target within the router tolerance.
- CAD sandbox (`work-v10d/cad/`): 0 unintended overlaps (7 intended), woofer net 0.525 L, identical to v10c. None of these parts is modelled.
- Area unchanged: 127.6 x 137.7 mm.
- Render: `ai-files/pcb/layout-v10d-top.png`.

**Accepted deviation**: the U6-left and U7-left 100 nF PVDD caps are now 2-3 mm from the pins (small HF-loop penalty). Record in the handover when v10d is adopted.
