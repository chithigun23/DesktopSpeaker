# R6j routing review (Fable, 2026-10-09): `work-r6/R6j-final.kicad_pcb`

Scope: routing quality only (placement, schematic, silk, BOM out of scope). Read-only. Checks run on a scratch copy of the board
(`.kicad_pro`/`.kicad_dru` byte-identical): `kicad-cli pcb drc --schematic-parity --severity-all`, `route_p2_open2.py all`,
`route_r6c_gates.py`, `route_r6h_isl.py`, `route_r6i_bends.py` (ref R6j-0), plus pcbnew scripts for per-layer connectivity,
widest-path island necks (0.25 and 0.1 mm grids), clearance scans, decoupling distances and In1 coverage. Current ratings below use
IPC-2221 (inner k 0.024, outer 0.048) at the accepted 15 K rise: 0.5 oz inner 1.0 mm = 0.9 A, 2.0 mm = 1.4 A, 3.0 mm = 2.0 A,
5.4 mm = 3.0 A; 1 oz outer 0.2 mm = 0.7 A, 0.6 mm = 1.9 A, 2.5 mm = 5.5 A; 0.3 mm via = 1 A (project rule).

## Verdict: FAIL

One blocker (the SYS_RAW current path out of U4) and six majors. Everything else is PASS or PASS WITH CONDITIONS.

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Connectivity | PASS WITH CONDITIONS | Open edges 2: /MCU/NRST and /MCU/SWCLK at J7.3/J7.4 (170.77,95.94 / 94.67), as expected; J6 and TP19 carry them. DRC: 0 clearance, shorts, dangling, isolated copper, track width; 37 silk/lib warnings; 4 USB errors (see 4). Parity: 244 items, none a routing error: 199 missing symbol fields, 30 attribute flags (TP BOM, R256 DNP), 9 `{slash}` net-name artefacts (U1/U24 pins), 6 "no pad for pin 21/22/24/25/33/35" on U11 (the footprint merges those pins into pads 20/23/32/GND, which are routed). |
| 2 | Power | FAIL | BLOCKER B1, MAJOR M1-M3; island continuity 1 outline each (BAT_PACK_B 2, as before); In2 signal nets all in the rule-11 whitelist, none AUDIO/I2S/USB; 3V_AO 0.6 mm section 24.5 mm long is fine (U12 TPS7A02 200 mA max, 0.6 mm inner = 0.6 A). |
| 3 | Switching / noise | PASS WITH CONDITIONS | U25: FB/COMP/ILIM >= 2.0 mm from SW and BOOT (no item below), SS pad 1.13 mm (not in rule), SW zone 7.9 mm2, SW pin to L200 pad 3.9 mm. SW to signal 1.0 mm holds everywhere except inside NECK_U4 (rule 12 overrides): SW2 to Q103-G via 0.43 mm (B, 155.55,120.1), ILIM via 0.49, CHG_INT via 0.68, CTRL_SCL via 0.80, BATP via 1.81 (limit 2.0) - the documented R6i fine-via exception. SW1/SW2 bootstrap caps C103.2/C110.2 reach SW only through B.Cu jumpers (7 segments, 4 vias) - SW copper on B.Cu, against checklist 2. TAS5825M: 100 nF C276/C278 (U6) 2.0/2.8 mm, C289/C291 (U7) 2.0/3.25 mm, all F.Cu no via; 22 uF U7 C273/C274 F-only 4.7 mm, U6 C271/C272 through In2 vias (6.7/5.4 mm). OUT_x to inductor 8.3-10.1 mm (plan <= 3 mm, placement). Audio copper >= 18.2 mm from any SWITCH copper. |
| 4 | Signal integrity | FAIL | USB: DP 51.6 mm F.Cu 0 vias, DN 49.8 F + 1.6 B with 2 fine vias (0.5/0.2) at J1 (148.2,27.9 / 149.75,27.85), nearest GND via 2.3/3.5 mm; physical skew 0.2 mm (the DRC -2.94 mm skew counts via height; the two U2-D+/D- skew items are rule artefacts on the post-resistor nets); uncoupled 17.3 mm vs 6 mm rule (DRC error, J1 exit and the length-tuning bumps y 47-58); gap 0.15 mm; nothing within 0.45 mm; In1 solid under the pair (DP 0 mm uncovered, DN 1.0 mm at the vias). I2S: BCK 125.0 / LRCK 127.6 / SDATA 125.6 mm vs 70 mm target (U24 to U6 and U7 geometry); vias 2/4/3 with GND via 0.85 mm except BCK via 152.4,103.3 (2.22 mm); SDATA has 40.5 mm on B.Cu, 22.8 mm of it under the VBUS_PD_IN2 island, no GND plane adjacent. Audio: 43 AUDIO vias, 8 without a GND via within 1.2 mm (list in m-findings); none on In2. Long nets: see table below, all acceptable. |
| 5 | Part-specific | PASS WITH CONDITIONS | U3: C160 100 nF 2.1 mm, C161 4.7 uF 3.8 mm, C162 NRST 100 nF 2.8 mm, all F-only; G0 has no VCAP; BOOT0 = SWCLK 29.8 mm F.Cu, SWD >= 5 mm from SW nodes. U1: antenna keep-out empty on all four layers (0.2 mm grid sample, 0 copper); no F.Cu track under the module; 11 GND vias within 4 mm. U11: CC caps C182/C183 1.3/1.2 mm F-only before any via; VBUS_PD 13 vias at U11 (plan 15), USB_VBUS 12 at U11, 7 at J1; D6 9.0 mm, D5 9.3 mm, D1 6.6 mm from J1 centre. U24: AVDD 100 nF 1.7 mm F-only, LDO 100 nF 2.2 mm F-only; bulk C214/C216 through vias; crystal nets 6.4/8.9 mm F-only, C227 8.0 mm from XO. U2: C173 (VCCP2I 1 uF) and C175 (VCCCI 10 uF) through vias; crystal 7.5/10.4 mm F-only. |
| 6 | Manufacturing | FAIL | MAJOR M5: 7 vias centred in SMD pads. Vias 879 x 0.6/0.3 and 42 x 0.5/0.2, annular >= 0.15 mm, every fine via inside a neck area or IC courtyard (DRC rule 8/12); copper-to-edge 0.5 mm clean; 0 micro-segments; acid-trap wedges in finding m6. |
| 7 | Corner rule | PASS WITH CONDITIONS | 49 hits (30 corner, 5 jog, 13 acute). Harmless by class: 35 (Default 7, I2C 3, AUDIO 4, I2S_CLK 1 xtal, PWR_LOCAL 1, SPK_OUT 2, SWITCH 3 wide copper, PWR_3V/PWR_5V/POWER_HI corners and jogs 14). USB_DP 2: jog 149.23,27.05 (0.27 mm, two 22 deg turns at the J1 exit) and corner 148.03,57.4 (0.61 mm of 0.75 at the tuning bump); both electrically irrelevant at full speed (12 Mb/s, edges > 4 ns) and removing them costs uncoupled length or a gap error - justified. Harmful (acid-trap wedges, inside angle <= 45 deg): 5, see m6. |
| 8 | Hygiene | PASS WITH CONDITIONS | In1: one GND outline, no tracks, no splits. B.Cu GND 4 outlines. Foreign vias in In2 islands: 25 real (the 7 SYS_RAW vias at x 140.35 sit in SYS_IN2 copper where the outlines overlap, not in PVDD copper); 8 are the R6i U4 list, 17 are older (3V3_AUDIO, REGN x2, 5V_LOGIC x2, Q103-G x2, SW1/SW2 x4, U24-LDO x2, U25-BOOT x2, U7-BST_B+ x2). Parallel runs (same layer, >= 8 mm, edge gap < 0.5 mm): 29, mostly slow In2 pairs; the I2S trio runs 30 mm at 0.2 mm gap (plan 0.4). |

## Findings

### BLOCKER

**B1. SYS_RAW (U4 charger output) has no path rated for its current.** Pin U4.25 (SYS, 0.2 x 1.0 mm pad at 152.47,120.48) leaves on a
0.2 mm F.Cu track (0.89 + 0.65 mm) and 0.25 mm tracks (2.3 mm) to the SYS_U4CAP_F pour (x 154-163, y 116-119, 25 mm2); no pour
touches the pad. That pour's only link to the rest of SYS (SYS_BOOST_F 308 mm2 with the boost input, U14/U15/U20 feeds) is 8 vias at
161-163,116-118 into SYS_IN2, and SYS_IN2 between those vias and the 14-via field at 157-162,128-129 is choked to three strands of
0.6 / 1.0 / 0.4 mm at y 125.2-126.2, x 154.0-157.2, between the ILIM via 154.7,125.8, the SW2 via 156.55,125.57, the CTRL_SDA via
152.45,125.2 and the BAT_INT_IN2 island (x >= 157.4). F.Cu and B.Cu have no parallel copper (separate F components; no B track).
Capacity of the neck is about 1.4 A at 15 K, of the 0.2 mm escape about 0.7 A; the plan carries 6-8 A here (boost input plus bucks).
Verified on 0.25 and 0.1 mm grids (widest path 1.0 mm) and by an ASCII map of the fill. Smallest fix: (a) attach a >= 0.6 mm F.Cu neck
and pour directly to the SYS pad end and widen the escape to the cap pour; (b) move the ILIM/REGN/SW2/CTRL_SDA vias out of the x 154-157
corridor (or re-route BAT_INT_IN2's west edge east of x 160) so SYS_IN2 is >= 8 mm wide there; (c) add an F.Cu SYS pour from
SYS_U4CAP_F down to SYS_BOOST_F (y 119 to 128, x 157-163) with >= 8 vias at each end.

### MAJOR

**M1. U4 power-pad escapes are 0.2 mm necks.** PMID pad 29 (0.2 x 0.95): 0.2 mm x 1.5 mm then 0.35 mm to PMID_F (9.5 mm2) - this is
the converter input node (up to 3.3 A). VBUS_PD pads 2/3/8/9: four 0.2 mm escapes of 0.4-0.9 mm (about 2.8 A total). BAT_INT pads
22/23: two 0.6 mm x 2.75 mm tracks (about 3.8 A total) against a 9 A battery path. No pour touches any U4 pad. Fix: pour copper onto
the pad ends (0.6 mm clearance to the 0.9 mm neighbour pitch allows 0.5-0.6 mm necks) and shorten the escapes to < 0.5 mm.

**M2. VBUS_PD_IN2 neck 1.5 mm at 147.4,122.4** (the SW1 via 146.45,121.75 and the U4 fine vias cut the x 141-149 strip). The U4.8/U4.9
half (4 vias at 148.2,126.2) is fed only through it; capacity about 1.2 A at 15 K for a 3 A input. Fix: move the SW1 B jumper via off the
strip (or drop the B jumper, see m2) and keep signal vias out of x 141-149 at y 118-127.

**M3. PVDD_AMP via feeds at the amplifiers.** U7 pins 21/22 (PVDD_U7L_F, with C274/C291) hang on one 0.3 mm via at 186.09,128.3 whose
In2 approach is 2.0 mm wide; U7 pins 3/4 have 2 vias (199.2/200.0,132.3); U6 halves 2 + 2 (105.4/106.2,129.3; 115.4/116.2,129.45) and
the U6 22 uF caps C271/C272 sit on their own 1 + 2 vias (In2 island 5.4 mm there). Plan: 8 vias per transition, 0.8/0.4. One 0.3 mm via
carries about 1 A; a channel averages 1-2 A. Fix: 4-6 vias on each PVDD_U6x/U7x pour and under C271/C272 (the island is directly below).

**M4. USB uncoupled length 17.3 mm (rule 6 mm), DRC error** from the J1 exit (y 27-31) and the DP tuning bumps (y 47-58); plus DN alone
carries 2 fine vias. Full-speed USB tolerates this electrically, but the rule stands and the bumps buy only 0.2 mm of skew. Fix: delete
the DP bumps (skew 0.2 mm is already inside 0.5 mm) and run the pair coupled from J1; or record the FS waiver and the DN via asymmetry.

**M5. Via centred in an SMD pad (7, no POFV on JLC 4-layer):** R10.2 (135.8,60.23), C234.2 (192.6,39.3), R224.1 (191.09,37.67),
J7.2 (169.7,94.35), TP19.1 (178.95,96.2), C215.1 (151.15,80.7, U24 AVDD 100 nF), R185.2 (98.7,24.46). Solder wicking on hand-soldered
0402s. Fix: dogbone each via 0.5 mm beside the pad (TP19 and J7.2 may stay if J7 becomes test-only).

**M6. All power vias are 0.6/0.3** (netclass POWER_HI/PVDD say 0.8/0.4). Counts: SYS 18/14/8/7, BAT_INT 18 + 18, BAT_PACK 18,
PVDD 8 at the boost, VBUS_PD 13 at U11 (plan 15) and 4 + 2 at U4, USB_VBUS 12 at U11, 7 at J1. By the 1 A/via rule the U4 VBUS (6),
PVDD (8) and VBUS_PD at U11 fields are below their 8 A / 3 A targets with margin only from the F.Cu pours. Fix: 0.8/0.4 arrays
(two rows) at the U4 VBUS, SYS, BAT fields and the boost output.

### MINOR

- m1. Trunks below class width (DRC floor met, plan width not): 3V3_AUDIO 0.3 mm on In2 (20 segments, 165 mm, class 0.5),
  5V_LOGIC 0.4 mm In2 69 mm (class 1.0), USB_AUX_5V 0.5 In2 54 mm, REGN 0.4 B.Cu 37 mm, 3V_AO 0.2 F 3.1 mm at 169.81,96.6. All carry
  < 0.3 A (3V3_AUDIO 0.3 mm inner = 0.37 A), so acceptable; widen where room exists.
- m2. Switch nodes off F.Cu: SW1/SW2 B.Cu jumpers to C103.2/C110.2 (vias 146.45,121.75 / 150.1,115.2 / 153.0,115.2 / 156.55,125.57).
  Bootstrap loop through 2 vias and 5-8 mm of B.Cu. Fix together with M2: route the BST cap SW side on F.Cu.
- m3. Decoupling beyond plan (all F-only unless noted): U25 Cout 22 uF 4.9-7.7 mm (C290/C277/C279/C292), C275 9.5 mm, C270 1 uF 2.8 mm,
  C314 100 nF 1.3 mm; Cin C261 4.1 mm; VCC C265 2.2 mm with GND via 4.8 mm. U4 bulk 3.8-7.8 mm with 100 nF C311/C312/C313 at 1.4-1.6 mm
  (matches the mitigation plan). BST caps: U6/U7 BST_B- tracks 5.9 mm, U7 BST_B+ and U25 BOOT through B.Cu jumpers (listed exceptions).
  U24 C214/C216 and U2 C173/C175 bulk through vias; EP vias 16/16/8 vs plan 20/20/9; U10 EP has no via.
- m4. Audio vias without a GND via inside 1.2 mm: VMID_HP 189.95,38.4 (3.1), C234-Pad2 191.09,37.67 (2.9), COM2 173.55,62.22 (1.7)
  and 184.85,62.0 (2.5), COM1 183.8,64.6 (1.6), HP_L 187.3,62.45 (3.1), U10-INL- 188.0,61.6 (2.8), U10-INR- 188.35,62.7 (2.0).
  I2S BCK via 152.4,103.3 has its GND via at 2.2 mm. Fix: one 0.6/0.3 GND via beside each.
- m5. I2S bus 0.2 mm gap over 30 mm (BCK/SDATA at 185.2,103.4; LRCK/BCK 124.0,113.8), plan 0.4; AMP_FAULT_N parallel to LRCK 14.9 mm
  at 0.43 mm (186.9,118.5). TP stubs on I2C: TP18 11.5 mm, TP16 8.7, TP17 6.6, TP15 4.5 (plan <= 2 mm); I2S TPs are in line (TP13 1.4 mm).
- m6. Acute wedges (inside angle) to fix as acid traps: 5V_LOGIC In2 171.0,54.5 (25 deg, 0.4 mm) and 96.3,95.8 (30 deg, 1.5 mm),
  SYS_RAW In2 94.95,74.05 (29 deg, 2.0 mm), LDO_3V3 In2 130.85,57.15 (41 deg, 1.0 mm), HP_SEL_A F 171.15,67.0 (45 deg, 0.2 mm).
  The other 8 acutes are 60-73 deg or 3-segment junctions with a 0.25-0.7 mm stub (3V_AO 188.4,39.0 / 177.7,93.3; 5V_CODEC 161.55,88.9 /
  150.55,66.15; 5V_LOGIC 184.05,50.9): harmless, merge the stub into the junction.
- m7. Foreign vias in In2 islands: 17 pre-R6i ones are not in any exception list (see criterion 8); record or move them. The 7 SYS_RAW
  "island" vias at x 140.35 are a false positive of the outline test and can be dropped from the gate count.
- m8. SDATA 22.8 mm on B.Cu under VBUS_PD_IN2 (x 141-149, y 95-104): reference is a power island; acceptable for 3 MHz I2S, better on F.

## Long slow nets (> 120 mm)

None runs within 1.0 mm of AUDIO or I2S copper on any layer, none is parallel to audio (0 mm inside 0.6 mm), none is on In2 under
the audio block without In1 between. Classification:

| Net | mm / vias | Verdict | Why |
|---|---|---|---|
| AMP_FAULT_N | 231.7 / 5 (B 109) | acceptable, watch | open-drain flag into an MCU input; 109 mm on B.Cu over GND pour; debounce in firmware |
| AUD_SDA | 278.0 / 13 | acceptable, watch | I2C: about 35-40 pF of trace plus vias; fine at 100 kHz, use <= 2.2 k pull-ups at 400 kHz |
| CTRL_SDA / CTRL_SCL | 172.4 / 16, 141.4 / 12 | acceptable | same reasoning, shorter |
| PD_SINK_EN, QON, BT_RST_N, QON_SENSE | 134 / 136 / 187 / 135 | acceptable | static enables and button lines; BQ25792 QON is internally debounced |
| ENC_SW | 203.5 / 17 | acceptable | debounced by C310 at the MCU; 30.8 mm In2 parallel to BT_RST_N at 0.39 mm is harmless (slow edges) |
| BT_UART_TX | 146.3 / 18 | acceptable | 115 kbaud; 18 vias is untidy, not harmful |

## Waived (placement, not routing)

OUT_x to inductor 8-10 mm; U25 Cout 22 uF 4.9 mm from VOUT; I2S 125-128 mm from the U24/U6/U7 spread; J7 NRST/SWCLK pending the user's
decision; U11 pins 21/22/24/25/33/35 merged in the footprint.
