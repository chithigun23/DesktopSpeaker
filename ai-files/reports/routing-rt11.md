# RT-11: analog front-end re-place (headphone mux block) and re-route (2026-11-03)

Agent "RT-11 re-place analog front end and finish".
- **Input:** `ai-files/pcb/work-route10/RT-10.*` (DRC 0, 47 unconnected = 46 + CHG_INT accepted).
- **Work folder:** `ai-files/pcb/work-route11/` only. Nothing in `DesktopSpeaker-kicad/`, earlier work folders or `helpers/route_oct*.py` was edited. Nothing committed or published.
- **Result:** `ai-files/pcb/work-route11/RT-11.kicad_pcb` / `.kicad_pro` / `.kicad_dru`.
- **Method:** text-level edits (`scripts/edit.py`, now with `fp_move` and `zone_pts`), every build refilled in a separate pcbnew process with the pristine `base.kicad_pro` + `RT-11.kicad_dru` beside it (`scripts/cycle11.sh`). Router `scripts/hr11.py` (copy of hr10 with two additions, section 2.3).
- **Not reached:** 0 unconnected. So no release material (`proposed-project.kicad_dru`, `release-todo-2026-11-02.md`) was written; section 5 is the open-connection to-do list instead.

## Bottom line

- Unconnected **47 -> 37** (36 + CHG_INT). **10 closures, no connection lost** (per-net counts: no net increased). DRC **0 violations**.
- Closed: U8-COM1, U8-COM2, U8-NC1, U8-NC2, HP_L (U9-10 -> C239), HP_SEL_A (U8-1), HP_SEL_B (U9 pin-1/pin-5 tie), C233-Pad2, USB_AUDIO_R (C231 side), HP_G0 (U10-6 -> R237).
- The mux block was re-placed as one block (25 parts, all <= 10 mm, section 1) and every net of the moved parts was ripped locally and re-routed in importance order.
- **Gate misses (honest):**
  - **B.Cu over In2 void 268.7 mm** (RT-10 266.9; gate <= 267 missed by 1.7 mm; target <= 200 not met). Breakdown in section 3.
  - **HP_R 13.7 mm vs octilinear 7.5 mm** (ratio 1.83; audio limit 1.5 x + 1 = 12.2 mm). It must cross HP_OUTR on B outside BKO_MUX, i.e. north of y 66.45 (RT-10: 4.9 mm, ratio 2.19, so the ratio improved but the length grew).
- Task groups 3-6 (BCK, USB-C/PD/gauge, U4 charger, 3V_AO) were **not started**: the budget went into the mux block (3 placement iterations). The long U3 nets (HP_G0, HP_EN, HP_SEL_B, AUX_DET) and HP_OUTL were attempted on the new placement and failed (section 4, AG13 log).

## 1. Placement (all top side, all <= 10 mm; HA8 checked)

| ref | RT-10 (x, y) rot | RT-11 (x, y) rot | moved mm |
|---|---|---|---|
| U8 | (172.295, 65.278) 0 | (178.500, 68.500) 0 | 6.99 |
| U9 | (184.295, 65.278) 0 | (186.000, 62.400) 180 | 3.34 |
| C230 | (171.340, 59.100) 0 | (176.600, 61.450) -90 | 5.76 |
| C231 | (175.890, 62.920) -90 | (181.100, 61.450) -90 | 5.41 |
| C232 | (171.590, 71.790) 0 | (176.500, 74.970) 0 | 5.85 |
| C233 | (173.950, 70.400) 180 | (180.500, 75.100) 180 | 8.06 |
| C236 | (191.690, 62.980) -90 | (190.900, 62.800) -90 | 0.81 |
| C237 | (184.295, 59.818) 90 | (185.400, 67.200) 180 | 7.46 |
| C238 | (173.290, 58.700) 90 | (179.100, 62.800) 0 | 7.11 |
| C239 | (186.540, 61.070) 0 | (192.000, 65.600) 0 | 7.09 |
| C240 | (187.790, 63.970) 0 | (192.000, 67.000) 0 | 5.19 |
| R220 | (176.090, 60.970) 0 | (174.700, 62.700) 180 | 2.22 |
| R221 | (177.190, 62.940) 90 | (182.300, 62.700) -90 | 5.12 |
| R222 | (172.300, 73.600) -90 | (175.100, 73.150) 90 | 2.84 |
| R223 | (173.600, 72.400) -90 | (182.350, 73.700) 90 | 8.85 |
| R226 | (171.840, 60.800) 180 | (176.600, 63.900) -90 | 5.68 |
| R227 | (174.590, 63.770) 90 | (181.100, 63.900) -90 | 6.51 |
| R228 | (169.690, 70.290) 90 | (177.100, 73.050) 90 | 7.91 |
| R229 | (174.590, 67.990) 90 | (179.900, 73.250) 90 | 7.47 |
| R230 | (186.690, 65.940) -90 | (187.200, 57.200) -90 | 8.75 |
| R231 | (181.990, 64.390) -90 | (184.800, 57.200) -90 | 7.72 |
| R234 | (175.190, 65.990) 0 | (181.900, 71.720) 0 | 8.82 |
| R235 | (181.990, 67.990) -90 | (183.400, 58.100) 90 | 9.99 |
| R237 | (193.790, 67.980) 180 | (197.000, 71.600) 0 | 4.84 |
| R238 | (196.440, 69.580) -90 | (199.600, 70.400) 0 | 3.26 |

Not moved: U10 and its charge-pump / supply parts, U24 and its input RC parts, R262, R258, R111, the test points, all fixed parts (J1-J3, J5, J9-J11, holes, SW100-SW102, U1, U6, U7, U3).

**Why this placement (paper plan, verified by router runs):**
- The 5V_CODEC In2 trunk (w 1.5, line x + y = 238.25) ran under the old U8. The rule-16b COM1/COM2 B jumpers must be over In2 GND, so U8 moved north-east of that line (x + y of every U8 via >= 240.2).
- U9 is rotated 180 so its NO pins face the AUX jack (north) and HP_L / HP_R leave on the U10 side. COM1 and COM2 are B jumpers (rule 16b exemption).
- The supply pins U8-8 / U9-8 sit between two audio fans. Each gets one straight 3V3 F stub that touches the neck area (DRC neck rule), with C238 / C237 on that line and a via for the 3V3 feed (U9: via (186.0, 68.3), B 3V3 trunk to the U10 In2 3V3 via).
- The input worlds are spread west/east of a corridor at x 178.5 (USB: R226/C230/R220 west, R227/C231/R221 east; BT: R228/C232/R222 west, R229/C233/R223 east), all just outside the HA8 1.5 mm fine-pitch zone of U8.
- Rule areas NECK_U8 / NECK_U9 were translated with their ICs (`zone_pts`, in the edit reports). BKO_MUX was not changed.
- Enclosure: all moved parts stay inside the RT-10 block region (x 172-201, y 56-76), far from the knob dish (r 21 around 116.1, 100.9) and from the J2/J3 jack bodies (y < 35). The lid-screw bosses are on the enclosure perimeter, not over this region.

**HA8:** 122 -> **122** failing pairs. New: C233-TP25 1.381 mm (tier c, needs 1.5; above the 0.25 floor). Gone: U10-C236 (1.48 mm). No pair is tighter.

## 2. Edits

### 2.1 Build chain (every step refilled; edit reports in `t/<stem>.edit.json`)

- **RT-10 -> P8:** placement v8 (`t/poses_v8.json`), local rip-up (`scripts/place11.py`: nets of moved parts, box x 166.5-200.6, y 55.5-77.5).
  - GND stubs of moved GND pads and 6 conflicting GND vias removed.
  - The In2 3V3 trunk and its vias are kept.
  - Hand copper: U8-8 3V3 stub (178.5, 66.39)-(178.5, 61.6); U9-8 3V3 stub (186.0, 64.51)-(186.0, 68.3) + via; GND vias U8-3 (178.5, 72.9), U9-3 (186.0, 57.4), C238-2 (179.7, 61.75).
- **P8 -> A11 -> B11:** `scripts/run11.sh`.
  - Stage A: the 0.5-pitch fans (NC1/NC2/NO1/NO2, U9 NO1/NO2) and the COM jumpers, on a router-only model with NECK_U8/U9 grown 1.0 mm. This mirrors the DRC rule that a segment touching a neck area gets 0.2 mm (`scripts/neckgeo.py`; DRC on the real board stays the gate).
  - Stage B: everything else, on real geometry, in importance order: audio, then power, then control.
- **B11 -> F12 -> F13 -> F14:** fix-ups:
  - INR- end re-shaped clear of the U10-3 GND stub;
  - GND vias for C236-2, C237-2, R234-2, R235-2, R237-2, R238-2;
  - router port-stub trims (`scripts/trimdangle.py`);
  - two In2-only 3V3 vias removed (197.3, 61.3) and (174.2, 59.1). The In2 3V3 network stays connected through the trunk and zone.
- **F14 -> R16 -> R17:**
  - HP_G0 hand stub U10-6 (196.045, 66.778)-(196.045, 71.2425)-(196.4025, 71.6) into R237-1. It is one straight segment that touches NECK_U10 past HP_OUTR.
  - COM2 forced to a B jumper (F block box), opening an F channel for VMID R223 -> R221.
  - HP_G1 re-routed R238-1 -> port (170.275, 77.1).
- **R17 -> I3 ... I3E:** placement iteration 2 for HA8 (BT world, NC2 world, C236/C239/C240).
  - Local rip and re-route of their nets.
  - NO2 hand fan (179.0, 70.61)-(179.0, 72.4)-(179.25, 72.65)-(179.9, 72.65), clear of HP_SEL_A.
  - HP_SEL_A hand (179.5, 70.61)-(179.5, 71.72)-(181.3025, 71.72) into R234-1.
  - HP_R end re-shaped through the C239/C240 gap (via (193.4, 66.11), F y 66.3); INR- (192.5975, 67.0)-(193.77, 67.0)-(194.7425, 66.0275)-(194.795, 66.0275).
  - BT_AUDIO_R overlapping old stub removed.
  - C232 nudged 0.02 mm (HA8).
- **I3E -> I4 -> I4B -> I6:** void reduction:
  - HP_SEL_B U9 tie moved from B to In2 (HP_SEL_B is a rule-11 net);
  - the In2 3V3 link under U9 moved to B (w 0.5);
  - HP_G1 rerouted on F/In2;
  - one 3V3 B stub widened 0.3 -> 0.36.
- **I6 -> RT-11:**
  - C236 reference field moved;
  - `scripts/silk_tile11.py` (copy of helpers/silk_tile.py; only change: the 5V Codec Rail / Source Mux boundary notched from y 56.80 to 55.80 for x 182.6-188.0 over R231/R230/R235);
  - final copper fixes: HP_SEL_A port joined end-to-end, duplicate stub removed, R235 pulled back to 9.99 mm (`t/RT-11fix*.edit.json`).

### 2.2 New copper

160 new segments, 335.5 mm, **0 not exact 0/45/90** (gates4). All new vias are 0.6/0.3, or 0.5/0.2 inside neck areas. **No new via touches a pad** (`scripts/viapad.py`).

### 2.3 Router copy `scripts/hr11.py` (from hr10)

1. **No via land within 0.06 mm of any pad, own net included** (hand assembly: no via in pad). This applies to signal and stitch vias.
2. It reads `RT-11.kicad_dru`.

### 2.4 Rules

`RT-11.kicad_dru` = RT-10 byte-identical (SHA-256 c47d6aed...), `.kicad_pro` unchanged (aa88e8c9...).
- **No rule-21 extension was needed:** HP_SEL_A, HP_SEL_B and HP_EN are already in rule 11's exempt list, and HP_G0/HP_G1 are in rule 21.
- The rule-21 sentinels of RT-10 apply unchanged. The route_oct sentinel FIRES (81).

## 3. Gates (independent of the editing tools; `t/RT-11.gates.txt`)

| gate | RT-10 | RT-11 |
|---|---|---|
| kicad-cli DRC (project library, RT-11 rules) | 0 | **0** |
| unconnected | 47 | **37** (36 + CHG_INT), per-net: no increase |
| footprints moved / pad nets (360 fp, 1194 pads) | - | 25 listed parts only / **pad_net_diff []** |
| locked copper | - | 3288 of 3480 RT-10 items untouched, 192 removed/changed (all in the edit reports, 0 unexpected), SHA-256 `d953a574b0c75db2f233bc8b9a5015fb0c5b7b598558e1a4f9abac733ed91081` |
| new copper exact 0/45/90 | - | 160 seg, 335.5 mm, 0 not exact |
| route_oct_check | joints <90 0, T 13, bend-short 27, pad-exit-short 11, dangling 43 | joints <90 **0**, T 14, bend-short 34, pad-exit-short 14, dangling 63 (the 20 new are router ends that overlap port tracks inside the track width; connected, cosmetic) |
| r7 B.Cu over In2 void | 266.9 | **268.7 (gate <= 267 missed by 1.7)** |
| r7 sensitive B over void | VMID 2.7, BT_AUDIO_R 4.3 | VMID 4.6, BT_AUDIO_R 3.4, USB_AUDIO_R 0.9, others unchanged |
| r7 BM83 F.Cu in module | GND 2.3, SYS_PWR 2.0 | unchanged; antenna keep-out DRC 0 |
| parcheck | sens pairs 1, slow pairs 8 | **1 / 8** (unchanged) |
| pour check / islands | | OK; every In2 island count unchanged, GND_IN2_BG 51 -> 51 (area -12.9 mm2) |
| HA8 | 122 | **122** (1 new >= 0.25, 1 gone, 0 tighter) |
| BAT_INT 6 A | 2.889 mOhm / 104.0 mW | **unchanged** (17.3 mV, 104.0 mW) |
| silk | | `silk_tile_gate` G1, G2, G4, G5, G6 PASS. G3 "fails" only because the pre-tile board had 3 silk violations and the tiled board has 0; unconnected equal (`t/RT-11.silkgate.json`) |

**B-over-void breakdown** (`scripts/voidnet.py`, RT-10 -> RT-11, mm):

| net | RT-10 | RT-11 | note |
|---|---|---|---|
| VMID_HP | 2.7 | 4.6 | 8 vias (two inherent B crossings: USB_L/USB_R walls and HP_OUTR) |
| COM1 + COM2 | 0 | 2.2 | rule-16b jumpers, via antipads |
| HP_L | 0 | 1.2 | B hop under HP_OUTR |
| USB_AUDIO_R | 0 | 0.9 | crossing of USB_AUDIO_L (ports interleaved) |
| 3V3_AUDIO | 0 | 0.4 | |
| BT_AUDIO_R | 4.3 | 3.4 | |
| INL-, INR-, U9-NO2, C232-Pad2 | 3.4 | 0 | |

The rest is unchanged.

**Length report (route_oct_check; ratio = length / octilinear minimum):**

| net | length mm | ratio | vias |
|---|---|---|---|
| U8-COM1 | 13.1 | 1.34 | 2 |
| U8-COM2 | 8.1 | 1.20 | 2 |
| U8-NC1 / NC2 / NO1 / NO2 | 2.8 / 3.5 / 2.3 / 2.8 | 1.14 / 1.21 / 1.03 / 1.16 | 0 |
| U9-NO1 / NO2 | 2.7 / 2.7 | 0.97 | 0 |
| HP_L | 4.8 | 0.98 | 2 |
| HP_R | 13.7 | **1.83** (over the 1.5 x + 1 audio limit) | 2 |
| INL- / INR- | 3.5 / 2.6 | 1.31 / 0.99 | 0 |
| VMID_HP (whole net) | 73.5 | 1.17 | 8 |
| BT_AUDIO_L / R (whole net) | 120.3 / 108.3 | 1.18 / 1.07 | 4 / 4 |
| HP_SEL_A | 67.8 | 1.21 | 7 |
| HP_G1 | 85.0 | 1.18 | 8 |

## 4. AG13 iteration log

**Analog group (3 iterations):**
1. **Placement v1-v5** (`t/poses_v1..v5`), B6-B8 router runs. Fans failed in the strict model. One 3V3 GND via landed in the 5V_CODEC In2 trace, which forced the U8 move (v6-v8).
2. **v8** with two-stage routing (A11/B11), fix-ups F12-R17. This reached 37 open, but HA8 was 126 (C232/C233 vs TP25 0.02 mm, C238 vs C231/R227) and void was 273.
3. **Iteration 2c** (I3-I6): BT/NC2 worlds and C236/C239/C240 re-placed, slow nets re-layered. HA8 122, void 268.7.

**Long U3 nets** (`t/jL18_*.log`, hr11, 6-8 M nodes, F/B/In2): all FAIL.
- HP_SEL_B: exp 1.29 M.
- HP_EN: exp 0.48 M.
- HP_G0: exp 2; U3-16 has no exit.
- AUX_DET: exp 0.39 M.
- HP_OUTL: exp 229; the U10-16 exit is boxed by the C241/U10-14 3V3 vias.

**Other failed attempts:**
- HP_G1 B hops to In2: none legal.
- C235-Pad2 R231 -> R225: exp 1-2 M. R225-1 is sealed by the VMID_HP F loop and the C234-Pad2 B diagonal at the jack.

**Tasks 3-6** (BCK, USB-C/PD/gauge, U4, 3V_AO): not started (0 builds).

## 5. Remaining open connections (36 + CHG_INT) and minimal GUI actions

The owner routes by hand in 45-degree steps. **Audio:** 0.3 mm width, 0.5 mm clearance, B only over In2 GND, GND stitch via within 1.5 mm. **Slow nets:** may use In2 (rule 11 / rule 21 nets).

| # | from | to | net | cause (verified) | suggested layer / corridor |
|---|---|---|---|---|---|
| 1 | U3-51 (122.33, 73.75) | HP_SEL_B track end (185.0, 60.29) / R235-1 (183.4, 58.7) | HP_SEL_B | 63 mm; must cross the 5V_CODEC In2 wall (x + y = 238.25) on F/B; router exhausted | In2 from a via west of U3 east along y 72-73 to x 150, F/B across the wall near (160, 66), then In2/F along y 58 to R235 |
| 2 | U3-47 (124.75, 70.83) | U10-13 / R236 (199.34, 62.4) | HP_EN | 75 mm, same wall | as 1, continue F north of the block along y 56-57 to R236 |
| 3 | U3-16 (131.75, 82.17) | HP_G0 stub end (196.045, 71.24) / R237 | HP_G0 | U3-16 has no exit (exp 2) inside the U3 south fan | free U3-16 by moving the neighbouring HP_G1 / CHG fan stubs 0.2 mm; then In2 (rule 21) to x 160, F across the wall, F along y 76 |
| 4 | U3-29 (133.68, 74.25) | R242-2 (189.82, 36.30) | AUX_DET | 70 mm; jack area | In2 north-east to y 45, F into R242 |
| 5-8 | U3-25, U6-9, U7-9, TP20 | R262-2 (116.0, 126.74) | AMP_FAULT_N x4 | R262-2 boxed by PVDD vias, C281/C282 GND via, L201 (RT-10 4(a)) | move R262 0.8 mm SW (allowed <= 6 mm, not done) and route U6-9 north then east |
| 9 | R258-1 (183.2, 107.8) | AMP_PDN track (137.47, 80.9) | AMP_PDN | R258 pocket: LRCK via pair + halo | move R258 0.6 mm east, In2 (rule 11) west |
| 10 | R258-2 | U7-17 | U7-PDN | same pocket | F south after the R258 move |
| 11-12 | TP12 / R207-2 | U6-13, U7-13 | I2S_BCK x2 | hub window (RT-10 section 5): needs the VBUS_PD_IN2 cut and the ADC_INT/TP15 move | B hop at (144.0, 96.0) -> (141.6, 96.0) with GND stitches, after the window cut |
| 13-14 | U24-23 | AUD_SDA B track (139.05, 83.10); U7-15 | AUD_SDA x2 | U24 neck | F out of U24-23 south, B under the I2C lane |
| 15 | R204-1 (156.35, 90.73) | C204-2 (191.14, 40.17) | C204-Pad2 | 60 mm audio; C204 sits at the jack (only <= 6 mm allowed) | F north-east along y 50-55, B hops over In2 GND only |
| 16 | R205-1 (156.95, 89.28) | C205-2 (192.89, 42.37) | C205-Pad2 | as 15 | parallel to 15 |
| 17 | C200-1 (162.02, 79.0) | USB_AUDIO_L (174.55, 60.88) | USB_AUDIO_L | 25 mm audio across the U24/U2 area | F from C200 north to y 64, then NE |
| 18 | C201-1 (162.02, 77.65) | USB_AUDIO_R (168.75, 56.43) | USB_AUDIO_R | as 17 | parallel to 17 |
| 19 | U2-16 (158.47, 55.66) | C186-1 (161.13, 52.46) | U2-VOUTL | U2-16 inside BKO_CODEC, F only, pocket | F short diagonal NE |
| 20-21 | R231-1 (184.8, 56.6) / C235-2 (195.26, 40.8) | R225-1 (189.74, 40.97) | C235-Pad2 x2 | R225-1 sealed by the VMID_HP F loop (188.44, 40.43-41.38) and the C234-Pad2 B diagonal | re-route VMID to R225-2 from the north (x 187.6), then C235 B hop from (187.5, 45) to below R225-1 |
| 22 | U10-16 (195.54, 63.78) | HP_OUTL B track (175.96, 35.24) | HP_OUTL | U10-16 exit boxed by the 3V3 vias of C241/U10-14 | move those two 3V3 vias 0.5 mm east, then F north along x 195.5 to y 50, NW to J2 |
| 23 | D201-1 | AUX_L track | AUX_L | no GND stitch site within 1.5 mm for the B hop (RT-10) | add GND via at (191.6, 37.6) first |
| 24 | R241 (188.42, 39.0) | 3V_AO track (125.6, 63.1) | 3V_AO | RT-10 4(g) | In2 y 56-58 to x 138.5, B over VBUS island, B north of BKO_CODEC |
| 25 | U4-14 | CTRL_SCL track | CTRL_SCL | U4 bottom-row via site | RT-8 4.1 remedy (R103 move) |
| 26 | U4-12 | QON track | U4-QON | as 25 | as 25 |
| 27 | Q101-3 | ILIM_HIZ track | ILIM_HIZ | sense net, F/B only | as RT-10 |
| 28 | Q102-3 | Q101-G track | Q101-G | AUD_SCL between Q102-3 and Q101-1 | nudge Q102 <= 3 mm (allowed) |
| 29 | U11-7 | ADC4 track | U11-ADC4 | U11 pocket | F inside NECK_U11 |
| 30 | R18-1 | U11-36 | R18 | PD_PLUG_EVENT loop | re-shape the loop 0.2 mm |
| 31 | R17-2 | U11-19 | PD_SINK_EN | U11 pocket | F |
| 32 | C182-1 | D5-1 | USB_CC1 | | F/B lane along x 140-150 |
| 33 | C183-1 | USB_CC2 track | USB_CC2 | | as 32 |
| 34 | U14-4 | R140-2 | U14-FB | fenced by L2; no via in pad | R140 <= 2 mm (allowed) |
| 35 | R142-1 | 5V_LOGIC_EN track | 5V_LOGIC_EN | FB loop | after 34 |
| 36 | U12-EN tracks | | U12-EN | | B lane |
| 37 | GAUGE_ISO_N track | U17-4 | GAUGE_ISO_N | | F |
| - | U4-21 | | CHG_INT | accepted (I2C polling) | - |

**Hand-assembly note (unchanged):** C215-C212 are 0.14 mm apart. Place C215 and C212 first, before U24 and Y200.

## 6. Files (`ai-files/pcb/work-route11/`)

- **Result:** `RT-11.kicad_pcb`, `RT-11.kicad_pro` (= RT-10), `RT-11.kicad_dru` (= RT-10).
- **Gates:** `t/RT-11.gates.txt`, `RT-11.drc.json`, `t/RT-11.gates.json`, `t/RT-11.check.json/.txt`, `t/RT-11.r7.json`, `t/RT-11.par.json`, `t/RT-11.ha8.json`, `t/RT-11.cp.json`, `t/RT-11.rulehash.txt`, `t/RT-11.silkgate.json`, `sentinel/RT-11_sentinel.*`.
- **Plans and edit reports:** `t/poses_v*.json`, `t/poses_i2*.json`, `t/*.edit.json`. Router logs: `t/j*.log`.
- **Scripts:** `scripts/place11.py`, `cycle11.sh`, `run11.sh`, `mkblock.py`, `neckgeo.py`, `hr11.py`, `trimdangle.py`, `gndclean.py`, `viapad.py`, `voidnet.py`, `refmove.py`, `silk_tile11.py`, `gates11.sh`.
- **Evidence:**
  - full board: `evidence/rt11-F.png`, `rt11-B.png`;
  - block, before and after: `evidence/rt10-block-FB.png`, `rt11-block-FB.png`, `rt11-block-In2.png`;
  - RT-10 analysis crops: `rt10-u8.png`, `rt10-u9u10.png`, `rt10-hub.png`.
- **Size:** about 0.6 GB of intermediate boards and geo exports. Do not commit them.
