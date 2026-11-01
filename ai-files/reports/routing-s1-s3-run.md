# Routing stages S1-S3 on RT-1 with the upgraded router (2026-11-02)

Agent: "Routing stages S1-S3 full run". Input `pcb/work-route/RT-1.kicad_pcb/.kicad_pro/.kicad_dru` (placement frozen; USB pair, U2 XTO template and S0b power/GND edits kept). Work folder `pcb/work-route2/` only. Result `pcb/work-route2/RT-2.kicad_pcb/.kicad_pro/.kicad_dru`. Nothing in `DesktopSpeaker-kicad/`, `work-route/`, `work-r10/`, `work-oct2/` or `helpers/` was edited (git status: only the pre-existing `.kicad_prl` change). No rule, net class or board-setup change: `.kicad_dru` 102fbee4..., `.kicad_pro` aa88e8c9... on every board, equal to the project. Not committed; nothing published.

**Result first.**

| | S1 (clocks, I2S) | S2 (audio + AUD I2C) | S3 (rest) | all |
|---|---|---|---|---|
| connections closed by the router, RT-2 | **14/19** | **58/95** | **63/157** | **135/271** |
| with the kept S0 template (USB 9/9, XTO 1/3) | 24/31 | | | **145/283 (51.2 %)** |
| baseline R10-0 (work-oct2 N2, same code, no template) | 22/31 (same 9 nets: 14/19) | 55/95 | old Hga-3 67/157 (pre-R10 placement, pre-upgrade rules) | |
| nets complete | 6/9 | 20/49 | 18/77 | **48/140** (incl. 4 S0) |
| signal vias (+ GND stitching vias) | 4 (+2) | 39 (+23) | 101 (+0) | 147 incl. 3 template (+25) |
| runtime | 315 s | 1269 s | 1475 s | 51 min |

- Geometry and rules held: 100.000 % of 2458.7 mm exact 0/45/90 (max deviation 0.0000 deg); DRC **0 violations** (0 clearance/width/edge/hole); locks S0-S3 ok; pour check OK on every stage; sentinel fires; 0 footprint pose or pad-net changes against RT-1.
- Completion is still about half. 136 router connections are open: 43 "no exit" (32 of them pad-bound on the unrouted board), 65 "no path", 22 topology/pin order, 4 pour island, 2 BM83 keep-out (section 5).
- Length quality fails the targets: median length / octilinear minimum 1.175 (target <= 1.15), p95 3.59 (target <= 1.4), 14 complete nets > 1.4.

## 1. Procedure and command lines

```
cd ai-files/pcb/work-route2            # V = scratch venv python (numpy, shapely); K = ~/Applications/kicad.AppImage
sh prep_h0.sh                          # strip list = --all-signals (140) minus kept.txt (5) -> H0.nets.txt (135), strip, refill, export, DRC, order
sh run_stages.sh A1                    # S0 lock (mk_s0.py) + S1..S3 via helpers/route_oct_stage.sh
#   each stage: export -> route_oct.py --via-cost 1.5 --pair-avoid 1 --hweight 1 --max-exp 3e7 (upgrade defaults: --module-keepout U1:0.5,
#   --halo 0.6, --par-gap 0.4 --par-pen 0.5, --sens-bcu gnd, --stitch 1.5, --sp3 2.0, --pour-guard 1, --retries 2) -> refill -> DRC -> pour check -> manifest
sh verify.sh RT-2 RT-2.manifest.json   # route_oct_check, sentinel, r7_metrics, route_oct_parcheck, fpdiff (poses, pad nets, non-routed copper), rule hashes
$V bref.py RT-2 ; $V fref.py RT-2 ; $V brun.py RT-2   # reference-plane and stitching measurements (section 3)
python3 analyze.py A1 --json A1.analyze.json ; python3 unrouted_table.py A1 > RT-2.unrouted.md
$V probe_exits.py H0.geo.json H0 PADS  # router's own exit model per pad (evidence/exitprobe-*.txt)
sh render.sh RT-2 rt2                  # evidence/rt2-F.png, rt2-B.png
```

- **Kept copper (S0).** `hard-nets.txt` starts with stage S0 = /USB_DP, /USB_DN, Net-(U2-D+), Net-(U2-D-), Net-(U2-XTO). They are not stripped and not routed. `mk_s0.py` writes their canonical copper hash into the manifest (45 items, `1f4631fd...`), so the router's lock check refuses S1-S3 if that copper changes. H0 = RT-1 refilled: whole-board copper hash identical (1633 items), DRC 0 violations / 285 unconnected.
- **XTO:** the template joins only U2-20 -> Y170-3; R174-2 and C178-1 stay open (2 connections). The router ignores same-net copper, so routing XTO would duplicate the template; it was left for a hand extension.
- The stripped list contained no other copper (RT-1 = R10-0 + S0b edits), so the strip removed 0 items.
- One background pipeline at a time; no run touched another run's files.

## 2. Attempts (AG13: 2 of 3 tuning iterations used; all logged)

| run | change | S1 /19 | S2 /95 | S3 /157 | total /271 | nets complete (of 135) | vias (+stitch) | runtime |
|---|---|---|---|---|---|---|---|---|
| **A1 = RT-2** | final parameters (attempt with the agreed set, not a tuning step) | 14 | 58 | 63 | **135** | 44 | 144 (+25) | 51 min |
| A2 (iteration 1) | `--pad-pen 6 --pad-halo 1.0` (defaults 2 / 0.6): soft keep-away around pads of nets still to route, because 30 of 44 "local pocket" failures in A1 had routed signal copper within 1 mm of an end pad | 14 | 58 | 58 | 130 | 44 | 140 (+36) | 42 min |
| A3 (iteration 2) | S3 only, on the locked A1-2, `--rrr-max 5 --rrr-time 1800` (rip-up groups up to 5 nets; only 8 S3 rip-up attempts had been refused for > 3 conflicting nets) | - | - | 63 | (135) | (44) | (= A1) | 38 min |

- A2: S3 -5 connections, S2 the same count with 17 more signal vias and 13 more stitching vias; one joint < 90 deg (VMID_HP); median ratio 1.171, p95 3.635. Worse on completion and vias, so not used.
- A3: S3 copper canonical hash **identical** to A1 (587 items). All 36 rip-up groups rolled back, 5 kept as before.
- No third iteration: the open connections are structural (pad-bound exits, sealed pockets, the reservation-order defect, pin order). No router parameter addresses them (section 5).
- RT-2 was selected on completion, vias, length and the checks in section 3, not on DRC: A1, A2 and A3 all have 0 DRC violations.

Per net against the R10-0 baseline (`work-oct2` N2-1/N2-2, and N2k-3 for the 15 BM83/SP3 nets):
- S1: all 9 nets equal, 14/19. I2S_BCK and I2S_LRCK still 1/3; Net-(U24-XO) 1/2.
- S2, better (+4): Net-(U8-NO1), Net-(U9-NO1), Net-(U9-NO2), Net-(U2-VCOM). The S0b escape fixes at U8/U9/U2 made these reachable. But U8-NO2/U9-NO1/U9-NO2 complete at 3.4-4.1x their octilinear minimum, and they took the HP_SEL escapes (section 4).
- S2, worse: Net-(C235-Pad2) 1/2 -> 0/2.
- S3 against N2k (a targeted run with only the 15 BM83/SP3 nets): BT_RST_M 1/2 (was 2/2), BT_TXD_M 1/2 (2/2), BT_RXD_M 0/2 (1/2), BT_SYS_CFG 0/1 (1/1). Here 62 other S3 nets compete, and OR2 order (fine-pitch, then longest MST first) puts the short J8/BM83 nets last.

## 3. Independent checks on RT-2

Sources: `route_oct_check.py` (does not import the router), `r7_metrics.py`, `route_oct_parcheck.py`, kicad-cli DRC `--severity-all --all-track-errors` on the refilled board, the sentinel script, `fpdiff.py`, and three small measurement scripts in the work folder (`bref.py`, `fref.py`, `brun.py`).

| check | RT-2 | target / note |
|---|---|---|
| exact 0/45/90 share of routed length (140 nets, 2458.7 mm) / max deviation | 100.000 % / 0.0000 deg | 100 %. r7 segments >= 5 mm: exact 1448 mm (RT-1: 195 mm); the 295 mm of non-exact segments are inherited power copper, unchanged |
| shorts / dangling / joints < 90 deg / 90-deg joints away from pads / colinear splits / pad exit < 0.3 mm | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| T-junctions | 4 | 3 are the S0 template (DN Y at J1, D1 taps). 1 is AUD_SDA: the known B-stub branch at U3-31 (section 9 item 5) |
| bend spacing short / micro segments outside pads (inside pad copper) | 1 (template, J1) / 1 (22) | PDCTRL_SDA: the known neck-to-class width step at U11-8 |
| r7 whole-board joints < 80 deg / < 30 deg | 19 / 7 | RT-1 19 / 7. The router added no acute joint |
| DRC violations | **0** | no clearance, width, edge, hole or USB pair items |
| DRC unconnected | 152 = 136 in the 140 routed nets + 16 inherited | the 16 are identical on H0 (pour check): 3V_AO and GND at U3/J7/R106/C160-C162/R259 (unrouted power around the MCU) and the LDO_3V3 island near U11-1. Owner: power routing |
| pour check S1 / S2 / S3 | OK / OK / OK (16 -> 16 foreign items) | the guard rejected 6 + 3 + 9 candidate paths and re-searched them |
| locks (manifest hashes S0 45, S1 70, S2 354, S3 587 items) / 25 stitch vias present | ok / ok | |
| rule files vs project / sentinel (I2S_CLK width >= 5 mm appended on a copy) | equal / **FIRES** (70 items) | |
| footprints (360) moved / pad nets (1192 pads) changed vs RT-1 | 0 / 0 | |
| copper of non-routed nets (176 nets, 1633 items) | unchanged; only 25 GND stitching vias added | |
| zone outlines (83, non-teardrop) | unchanged | |
| BM83: routed F.Cu inside the module rectangle shrunk 0.5 mm / vias inside | 0 mm / 2 GND vias, both already in RT-1 | r7 `bm83` lists only the inherited GND 2.3 and SYS_PWR 2.0 mm |
| near-parallel < 0.4 mm over > 3 mm (parcheck) | 1 pair: USB_DP/USB_DN 32.8 mm (the intended pair); other pairs 0 | |
| r7 `par` (all pairs, any length) | longest non-pair 2.3 mm (U6/U7 BST/OUT, inherited power); signal pairs <= 1.5 mm (BT_MFB/BT_RST_N) | all < 3 mm |
| checker parallel < 0.6 mm outside necks, I2S/USB/clock | 3.9 mm in pieces of 0.7 and 2 x 1.61 mm | USB_DP stub at the template (0.7). XTO (template) vs XTI at Y170, 0.36 mm gap over 1.61 mm. All below the 3 mm limit of section 14.2 |
| sensitive-net vias / GND via farther than 1.5 mm | 46 / 1 | the one is the template DP via at J1 (1.86 mm; S0b report open problem 7). All 25 router stitches within 1.5 mm |
| sensitive B.Cu: over In2 GND / in via or TH-pad antipads / elsewhere over non-GND | 98.4 / 27.6 / **0.0 mm** | 0 |
| routed F.Cu over In1 non-GND: antipads / elsewhere | 80.9 / **0.0 mm** of 1949 mm | 0 |
| GND via every 5-8 mm along sensitive B.Cu runs > 5 mm (6 runs) | 3 runs exceed: Net-(C234-Pad2) 29.9 mm run with a point 4.68 mm from the nearest GND via, /AUX_R 9.6 mm (6.8 mm), /BT_AUDIO_R 10.8 mm (4.22 mm) | **fails section 14.1** for these 3. The router stitches only at layer changes (LA5), not along runs |
| non-sensitive B.Cu over In2 void (whole board, r7) | about 71 mm of control nets (r7 B.Cu void 102.3 mm minus 3.6 inherited minus about 27.6 sensitive antipads) | allowed for slow control lines (14.1), at x3.9 cost |
| SP3 (r7 `sw`) | U14-FB 1.43 mm from U14-L2 (the 0.65 mm pad stub; pin geometry, section 9). TS_SENSE 2.15 mm from SW2. Others > 3 mm | |
| vias per complete net | 1.73 | |

**Length / octilinear minimum, complete nets (n = 48):** median **1.175**, p95 **3.591**, max 4.566. Targets are <= 1.15 and <= 1.4, so **both fail**. Nets above 1.4:

| net | stage | ratio | vias |
|---|---|---|---|
| Net-(U2-VCOM) | S2 | 4.566 | 0 |
| Net-(U8-NO2) | S2 | 4.135 | 0 |
| Net-(U9-NO1) | S2 | 3.591 | 0 |
| Net-(U9-NO2) | S2 | 3.379 | 2 |
| Net-(C230-Pad2) | S2 | 2.232 | 0 |
| /Headphone_Aux/HP_R | S2 | 2.187 | 2 |
| /AUX_R | S2 | 2.005 | 3 |
| /PDCTRL_SDA | S3 | 1.968 | 9 |
| Net-(U1-AOHPR) | S2 | 1.894 | 2 |
| /CODEC_PWR_EN | S3 | 1.786 | 4 |
| /HP_DET | S3 | 1.699 | 6 |
| Net-(U2-D-) | S0 (template) | 1.651 | 0 |
| Net-(Q104-G) | S3 | 1.502 | 2 |
| /HP_G1 | S3 | 1.423 | 4 |

Most S2 outliers are short 2-pin audio nets where the pads are too close for two 0.3 mm stubs plus forced runs (section 6 item 3 of the toolchain report), so the only legal path is a detour. These should be hand-joined, or the pads moved slightly apart.

Complete nets:
- S0: USB_DP, USB_DN, U2-D+, U2-D-.
- S1: I2S_SDATA, U2-XTI, U24-BCK/DOUT/LRCK/XI.
- S2: AUX_R, AUX_TIPSW, HP_OUTR, HP_R, HP_TIPSW, VMID_HP, C200/C201/C202/C203/C230/C232/C234-Pad2, U1-AOHPR, U10-INR-, U2-VCOM, U8-NO1/NO2, U9-NO1/NO2.
- S3: BT_MFB, BT_RST_N, BT_TX_IND, CHG_QON_SENSE, CODEC_PWR_EN, GAUGE_ALRT_N, HP_DET, HP_G1, ENC_A/B/SW, PDCTRL_SDA, C268-Pad1, Q104-G, U1-P0_0/UART_TX_IND, U1-PWR(MFB), U13-NC, U17-NC.

## 4. Router defects found in this run

1. **Escape reservation is order dependent.** At the start of S2, the reserved stubs of the neighbouring S2 audio pins block the exits of U8-1/5 and U9-1/5 (HP_SEL_A/B, S3) under the 0.5 mm audio clearance. So those pads get no reservation. Measured: the S2 tracks of U8-NO1/NO2 and U9-NO1/NO2 cross the H0 reservation of these pads (edge gap -0.15 mm), and the router's exit model on A1-2 finds 0 exits there (`evidence/exitprobe-A1-2.txt`). Net effect: +4 audio connections (detours at 3.4-4.1x) for -5 HP_SEL connections.
   - Fix: reserve all pads of later stages jointly (neck clearance between reservations), or rip the leg of a later-stage pad that has lost all exits.
2. **Pad identity by (ref, number).** SW100 has two pads "1", and U11 DRAIN has two pads "40". The router builds a connection SW100-1 -> SW100-1 and reports "no exit" because the first pad's exit is already marked used. These are pin stacks, not routing problems (2 connections).
3. **Stitching only at layer changes.** Three long sensitive B.Cu runs lack a GND via every 5-8 mm (section 3).
4. **Inherited checker items still open:** the B-stub T-junction (AUD_SDA at U3-31) and the PDCTRL_SDA width-step micro segment.

## 5. Remaining unrouted connections (RT-2: 136 router connections + 2 XTO)

Method:
- First cause from the router log (`analyze.py`).
- "No exit" is split with the router's own exit model run on H0 (no signal copper), A1-1 and A1-2 (`probe_exits.py`, `evidence/exitprobe-*.txt`).
- "Topology" = the rip-up conflict search found same-stage nets blocking the connection.
- "Local pocket" = every A* window ended in < 0.1 s, so the start or target region is sealed.
- 30 of the 44 pockets have signal copper of other routed nets within 1 mm of an end pad; the rest are sealed by fixed power copper.

| cause | S1 | S2 | S3 | total | main remedy |
|---|---|---|---|---|---|
| no exit, pad-bound on H0 (fixed copper, pad pitch, rules) | 0 | 8 | 24 | 32 | placement nudges (C124/C125, C141/C142, C173, C239, C283/C294/C296, R252/C314), RT-1 copper edits, rule questions (U4-18, J7) |
| no exit, sealed by S1-S2 copper | 0 | 1 | 6 | 7 | U1-8 hand template; HP_SEL after a reservation fix / hand reroute of U8/U9-NO; R242-2 VMID_HP leg |
| no exit, same-pad / sealed in S3 | 0 | 0 | 4 | 4 | SW100-1 and U11-40 pin stacks; U3-61 (CTRL_SDA) taken in S3 |
| keep-out (BM83 U1 / J8) | 0 | 0 | 2 | 2 | nudge R182/TP22, route J8/BM83 nets first |
| pour island (guard rejected the only path) | 0 | 0 | 4 | 4 | one extra GND via to anchor the GND_BCU piece, then reroute |
| topology / pin order | 2 | 11 | 9 | 22 | I2S hub B.Cu hop templates; AUD I2C crossing template; coupling-cap block by hand |
| no path, local pocket | 2 | 11 | 31 | 44 | hand fan-out or nudges at U24, U25, U4, U6/U7 |
| no path, global | 1 | 6 | 14 | 21 | hand routing in importance order; a negotiated-congestion stage |
| XTO (S0 template, not routed) | 2 | | | 2 | extend the XTO template by hand: R174-2, C178-1 |

Named placement nudges proposed (all from the exit model; each needs a placement round and a pad-net diff):
- C226 (Y200-1, U24-XO); C173 (U2-15/16); C239 (U10-INL-, HP_L); R226 (U8-NC1, 3V3_AUDIO feed);
- C210 and C212 (U24-30, U24-4); C283, C294, C296 (U6-17, U7-8, U7-17);
- C124/C125 (U20-2/4/7); C141/C142 (R140-2); R252 and C314 (U25-3/17);
- R182/TP22 (BT_RXD_M).

Rule questions for the user (no rule was changed):
- U4-18 BATP needs 2.0 mm to BTST2 under `switch_critical`, and U4-19 is a BTST2 pad 0.2 mm away. This is rule-bound.
- J7 (TC2030): the pads are boxed in by the neighbouring pads and by NPTH holes with the 0.5 mm edge clearance; the router only has axial exits. Options are a hand template with diagonal escapes, or a decision on the NPTH clearance at J7.
- U14-1 and U25-2 sit inside POWER_HI / switch-node clearances.

Full per-connection table (generated by `unrouted_table.py`; the cause detail is the first blocking item found by the exit model):

| # | stage | net | connection | cause (detail) | proposed remedy |
|---|---|---|---|---|---|
| 1 | S2 | /Headphone_Aux/HP_L | U9-10 - C239-1 | no exit: pad-bound on H0 (track /3V3_AUDIO  (neck: track /3V3_AUDI) | nudge C239 about 0.5 mm east or reroute the 3V3_AUDIO track along its pads |
| 2 | S2 | Net-(U1-AOHPL) | U1-8 - C194-1 | no exit: sealed by S1-S2 copper (via GND) | hand template for AOHPL/AOHPR at BM83 pins 8/9 (S2 stitch via and AOHPR via took the only outward exit) |
| 3 | S2 | Net-(U10-INL-) | U10-1 - C239-2 | no exit: pad-bound on H0 (track /3V3_AUDIO  (neck: track /3V3_AUDI) | nudge C239 about 0.5 mm east or reroute the 3V3_AUDIO track along its pads |
| 4 | S2 | Net-(U2-VOUTL) | C186-1 - U2-16 | no exit: pad-bound on H0 (track Net-(U2-VCCP1I)  (neck: track Net-) | placement nudge: C173 out of the U2-15/16 escape (RT-1 pad-bound list); VCCP1I/2I copper at the pins |
| 5 | S2 | Net-(U2-VOUTR) | C187-1 - U2-15 | no exit: pad-bound on H0 (zone Net-(U2-VCCP2I)  (neck: zone Net-(U) | placement nudge: C173 out of the U2-15/16 escape (RT-1 pad-bound list); VCCP1I/2I copper at the pins |
| 6 | S2 | Net-(U8-COM1) | U9-9 - U8-10 | no exit: pad-bound on H0 (zone /3V3_AUDIO  (neck: zone /3V3_AUDIO ) | copper edit of the 3V3_AUDIO feed under U8/U9 (RT-1 sec.3 "copper-fixable"), or nudge R226 0.5 mm north |
| 7 | S2 | Net-(U8-COM2) | U9-7 - U8-6 | no exit: pad-bound on H0 (zone /3V3_AUDIO  (neck: zone /3V3_AUDIO ) | copper edit of the 3V3_AUDIO feed under U8/U9 (RT-1 sec.3 "copper-fixable"), or nudge R226 0.5 mm north |
| 8 | S2 | Net-(U8-NC1) | R226-2 - U8-9 | no exit: pad-bound on H0 (zone /3V3_AUDIO  (neck: zone /3V3_AUDIO ) | copper edit of the 3V3_AUDIO feed under U8/U9 (RT-1 sec.3 "copper-fixable"), or nudge R226 0.5 mm north |
| 9 | S2 | Net-(U8-NC2) | U8-7 - R227-2 | no exit: pad-bound on H0 (zone /3V3_AUDIO  (neck: zone /3V3_AUDIO ) | copper edit of the 3V3_AUDIO feed under U8/U9 (RT-1 sec.3 "copper-fixable"), or nudge R226 0.5 mm north |
| 10 | S3 | /5V_LOGIC_EN | U14-1 - R142-1 | no exit: pad-bound on H0 (zone /SYS_RAW  (neck: track /SYS_RAW )) | U14-1 rule-bound (SYS_RAW, POWER_HI 0.4 mm); placement nudge R142 / hand neck; R142 -> U3-18 sequential blocking |
| 11 | S3 | /AMP_BOOST_EN | R255-1 - U25-2 | no exit: pad-bound on H0 (zone Net-(U25-SW)  (neck: zone Net-(U25-) | U25 switch-node copper and switch_critical rules: placement nudge R252 / C314 (RT-1), hand template for FB/COMP/ILIM/SS/MODE |
| 12 | S3 | /AUX_DET | R242-2 - U3-29 | no exit: sealed by S1-S2 copper (pad /Headphone_Aux/AUX_TIPSW  (neck: pad) | R242-2 sealed by S2 VMID_HP track and AUX_TIPSW pad: hand reroute of the VMID_HP leg |
| 13 | S3 | /Battery_Charger/PROG | U4-20 - R102-1 | no exit: pad-bound on H0 (zone /Battery_Charger/BAT_INT  (neck: zo) | pour/power copper edits from RT-1 sec.3 (BAT_INT notch, REGN reroute, VBUS_PD pour corner); U4-18 is rule-bound (switch_critical 2.0 mm to BTST2): rule question |
| 14 | S3 | /CTRL_SDA | TP15-1 - U3-61 | no exit: same-pad / sealed in S3 | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 15 | S3 | /CTRL_SDA | U3-61 - U13-2 | no exit: same-pad / sealed in S3 | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 16 | S3 | /HP_SEL_A | R234-1 - U8-5 | no exit: sealed by S1-S2 copper (track Net-(U8-NO2)  (neck: track Net-(U8) | S2 tracks of U8-NO1/NO2, U9-NO1/NO2 took the reserved escape (reservation order defect); hand reroute those 4 short nets (ratios 3.4-4.1) clear of U8/U9 pins 1 and 5 |
| 17 | S3 | /HP_SEL_A | U8-5 - U8-1 | no exit: sealed by S1-S2 copper (track Net-(U8-NO2)  (neck: track Net-(U8) | S2 tracks of U8-NO1/NO2, U9-NO1/NO2 took the reserved escape (reservation order defect); hand reroute those 4 short nets (ratios 3.4-4.1) clear of U8/U9 pins 1 and 5 |
| 18 | S3 | /HP_SEL_A | U8-1 - U3-13 | no exit: sealed by S1-S2 copper (track Net-(U8-NO1)  (neck: track Net-(U8) | S2 tracks of U8-NO1/NO2, U9-NO1/NO2 took the reserved escape (reservation order defect); hand reroute those 4 short nets (ratios 3.4-4.1) clear of U8/U9 pins 1 and 5 |
| 19 | S3 | /HP_SEL_B | U9-5 - U9-1 | no exit: sealed by S1-S2 copper (via Net-(U9-NO2)  (neck: via Net-(U9-NO2) | S2 tracks of U8-NO1/NO2, U9-NO1/NO2 took the reserved escape (reservation order defect); hand reroute those 4 short nets (ratios 3.4-4.1) clear of U8/U9 pins 1 and 5 |
| 20 | S3 | /HP_SEL_B | U9-1 - R235-1 | no exit: sealed by S1-S2 copper (track Net-(U9-NO1)  (neck: track Net-(U9) | S2 tracks of U8-NO1/NO2, U9-NO1/NO2 took the reserved escape (reservation order defect); hand reroute those 4 short nets (ratios 3.4-4.1) clear of U8/U9 pins 1 and 5 |
| 21 | S3 | /MCU/NRST | C162-1 - J7-3 | no exit: pad-bound on H0 (pad /3V_AO  (neck: pad /3V_AO )) | hand template: J7 (TC2030) pads are boxed by pad pitch and NPTH holes (0.5 mm edge rule); router has axial exits only. Rule question: NPTH clearance at J7 |
| 22 | S3 | /MCU/NRST | J7-3 - U3-12 | no exit: pad-bound on H0 (pad /3V_AO  (neck: pad /3V_AO )) | hand template: J7 (TC2030) pads are boxed by pad pitch and NPTH holes (0.5 mm edge rule); router has axial exits only. Rule question: NPTH clearance at J7 |
| 23 | S3 | /MCU/SWCLK | J6-2 - J7-4 | no exit: pad-bound on H0 (pad /MCU/SWDIO  (neck: pad /MCU/SWDIO )) | hand template: J7 (TC2030) pads are boxed by pad pitch and NPTH holes (0.5 mm edge rule); router has axial exits only. Rule question: NPTH clearance at J7 |
| 24 | S3 | /MCU/SWCLK | J7-4 - R160-1 | no exit: pad-bound on H0 (pad /MCU/SWDIO  (neck: pad /MCU/SWDIO )) | hand template: J7 (TC2030) pads are boxed by pad pitch and NPTH holes (0.5 mm edge rule); router has axial exits only. Rule question: NPTH clearance at J7 |
| 25 | S3 | /MCU/SWDIO | J6-1 - J7-2 | no exit: pad-bound on H0 (hole   (neck: hole  )) | hand template: J7 (TC2030) pads are boxed by pad pitch and NPTH holes (0.5 mm edge rule); router has axial exits only. Rule question: NPTH clearance at J7 |
| 26 | S3 | /MCU/SWDIO | J7-2 - U3-45 | no exit: pad-bound on H0 (hole   (neck: hole  )) | hand template: J7 (TC2030) pads are boxed by pad pitch and NPTH holes (0.5 mm edge rule); router has axial exits only. Rule question: NPTH clearance at J7 |
| 27 | S3 | /USB_CC2 | U11-29 - J1-B5 | no exit: pad-bound on H0 (via /USB_VBUS  (neck: pad /USB_VBUS )) | hand template: CC1/CC2 B.Cu hop right at J1 (S0b report open problem 3); J1-B5 pad-bound by VBUS |
| 28 | S3 | /USB_CC2 | J1-B5 - D5-2 | no exit: pad-bound on H0 (via /USB_VBUS  (neck: pad /USB_VBUS )) | hand template: CC1/CC2 B.Cu hop right at J1 (S0b report open problem 3); J1-B5 pad-bound by VBUS |
| 29 | S3 | Net-(Q101-G) | Q101-1 - R110-2 | no exit: pad-bound on H0 (track /Battery_Charger/REGN  (neck: trac) | pour/power copper edits from RT-1 sec.3 (BAT_INT notch, REGN reroute, VBUS_PD pour corner); U4-18 is rule-bound (switch_critical 2.0 mm to BTST2): rule question |
| 30 | S3 | Net-(Q103-G) | U4-24 - Q103-4 | no exit: pad-bound on H0 (zone /Battery_Charger/BAT_INT  (neck: zo) | pour/power copper edits from RT-1 sec.3 (BAT_INT notch, REGN reroute, VBUS_PD pour corner); U4-18 is rule-bound (switch_critical 2.0 mm to BTST2): rule question |
| 31 | S3 | Net-(R18-Pad1) | R18-1 - U11-36 | no exit: pad-bound on H0 (pad /PD_PLUG_EVENT  (neck: pad GND )) | footprint-bound (U11-36 vs U11-34): hand neck escape |
| 32 | S3 | Net-(U11-FAULT) | R13-2 - U11-18 | no exit: pad-bound on H0 (zone /Battery_Charger/VBUS_PD  (neck: zo) | pour/power copper edits from RT-1 sec.3 (BAT_INT notch, REGN reroute, VBUS_PD pour corner); U4-18 is rule-bound (switch_critical 2.0 mm to BTST2): rule question |
| 33 | S3 | Net-(U12-EN) | C122-1 - U20-2 | no exit: pad-bound on H0 (track /Fuel_Gauge_Power/USB_AUX_5V  (nec) | placement nudge C124/C125 (RT-1 pad-bound U20-2/4/7); USB_AUX_5V / SYS_RAW copper at the pins |
| 34 | S3 | Net-(U12-EN) | U20-2 - U20-7 | no exit: pad-bound on H0 (track /Fuel_Gauge_Power/USB_AUX_5V  (nec) | placement nudge C124/C125 (RT-1 pad-bound U20-2/4/7); USB_AUX_5V / SYS_RAW copper at the pins |
| 35 | S3 | Net-(U12-EN) | U20-7 - U12-3 | no exit: pad-bound on H0 (zone /SYS_RAW  (neck: zone /SYS_RAW )) | placement nudge C124/C125 (RT-1 pad-bound U20-2/4/7); USB_AUX_5V / SYS_RAW copper at the pins |
| 36 | S3 | Net-(U14-FB) | R141-1 - R140-2 | no exit: pad-bound on H0 (zone /5V_LOGIC  (neck: zone /5V_LOGIC )) | placement nudge C141/C142 off R140-2 (RT-1) |
| 37 | S3 | Net-(U20-PR1) | U20-4 - R124-2 | no exit: pad-bound on H0 (track /Fuel_Gauge_Power/USB_AUX_5V  (nec) | placement nudge C124/C125 (RT-1 pad-bound U20-2/4/7); USB_AUX_5V / SYS_RAW copper at the pins |
| 38 | S3 | Net-(U25-FSW) | R252-1 - U25-3 | no exit: pad-bound on H0 (zone Net-(U25-SW)  (neck: zone Net-(U25-) | U25 switch-node copper and switch_critical rules: placement nudge R252 / C314 (RT-1), hand template for FB/COMP/ILIM/SS/MODE |
| 39 | S3 | Net-(U25-MODE) | R256-1 - U25-13 | no exit: pad-bound on H0 (zone /Amplifiers/PVDD_AMP  (neck: zone /) | U25 switch-node copper and switch_critical rules: placement nudge R252 / C314 (RT-1), hand template for FB/COMP/ILIM/SS/MODE |
| 40 | S3 | Net-(U4-BATP) | U4-18 - R112-2 | no exit: pad-bound on H0 (track /Battery_Charger/BTST2  (neck: tra) | pour/power copper edits from RT-1 sec.3 (BAT_INT notch, REGN reroute, VBUS_PD pour corner); U4-18 is rule-bound (switch_critical 2.0 mm to BTST2): rule question |
| 41 | S3 | Net-(U4-QON) | SW100-1 - SW100-1 | no exit: same-pad / sealed in S3 | not a routing problem: two pads with the same number (pin stack); join under the part by hand or treat as internally connected |
| 42 | S3 | Net-(U7-ADR) | R261-2 - U7-8 | no exit: pad-bound on H0 (track Net-(U7-VR_DIG)  (neck: track Net-) | placement nudge C294 (RT-1 pad-bound U7-8) |
| 43 | S3 | unconnected-(U11-DRAIN-Pad40) | U11-40 - U11-40 | no exit: same-pad / sealed in S3 | not a routing problem: two pads with the same number (pin stack); join under the part by hand or treat as internally connected |
| 44 | S3 | /Bluetooth/BT_RXD_M | J8-3 - U1-29 | keep-out | BM83 side: placement nudge R182/TP22 (sec.9 open problem 4); pour-island rejects need one added GND via to anchor the GND_BCU piece; route the J8/BM83 nets first inside S3 |
| 45 | S3 | /Bluetooth/BT_SYS_CFG | U1-31 - J8-2 | keep-out | BM83 side: placement nudge R182/TP22 (sec.9 open problem 4); pour-island rejects need one added GND via to anchor the GND_BCU piece; route the J8/BM83 nets first inside S3 |
| 46 | S3 | /BT_UART_RX | U3-56 - R186-2 | pour island | BM83 side: placement nudge R182/TP22 (sec.9 open problem 4); pour-island rejects need one added GND via to anchor the GND_BCU piece; route the J8/BM83 nets first inside S3 |
| 47 | S3 | /Battery_Charger/CE_N | U4-13 - R103-2 | pour island | BM83 side: placement nudge R182/TP22 (sec.9 open problem 4); pour-island rejects need one added GND via to anchor the GND_BCU piece; route the J8/BM83 nets first inside S3 |
| 48 | S3 | /Bluetooth/BT_RXD_M | R182-2 - J8-3 | pour island | BM83 side: placement nudge R182/TP22 (sec.9 open problem 4); pour-island rejects need one added GND via to anchor the GND_BCU piece; route the J8/BM83 nets first inside S3 |
| 49 | S3 | /Bluetooth/BT_TXD_M | R186-1 - J8-4 | pour island | BM83 side: placement nudge R182/TP22 (sec.9 open problem 4); pour-island rejects need one added GND via to anchor the GND_BCU piece; route the J8/BM83 nets first inside S3 |
| 50 | S1 | /I2S_BCK | U6-13 - TP12-1 | topology/pin order | hand template: stitched B.Cu hops through the TP12/TP13/TP14 + R206-R208 hub (BKO_U6/U7 forbid B.Cu at the IC legs); or placement: swap TP12/TP14 order |
| 51 | S1 | /I2S_LRCK | U6-12 - TP14-1 | topology/pin order | hand template: stitched B.Cu hops through the TP12/TP13/TP14 + R206-R208 hub (BKO_U6/U7 forbid B.Cu at the IC legs); or placement: swap TP12/TP14 order |
| 52 | S2 | /AUD_SCL | TP18-1 - U3-30 | topology/pin order | hand template: AUD I2C crossing at U6/TP17/TP18 with one stitched B.Cu hop; U24-23/24 pocket is the 3V3_AUDIO feed |
| 53 | S2 | /AUD_SDA | U6-15 - TP17-1 | topology/pin order | hand template: AUD I2C crossing at U6/TP17/TP18 with one stitched B.Cu hop; U24-23/24 pocket is the 3V3_AUDIO feed |
| 54 | S2 | /AUX_L | J3-5 - C204-1 | topology/pin order | hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm |
| 55 | S2 | /BT_AUDIO_L | C232-1 - C202-1 | topology/pin order | hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm |
| 56 | S2 | /USB_AUDIO_L | C230-1 - C200-1 | topology/pin order | hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm |
| 57 | S2 | Net-(C204-Pad2) | R204-1 - C204-2 | topology/pin order | hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm |
| 58 | S2 | Net-(C205-Pad2) | R205-1 - C205-2 | topology/pin order | hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm |
| 59 | S2 | Net-(C233-Pad2) | R229-1 - C233-2 | topology/pin order | hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm |
| 60 | S2 | Net-(C235-Pad2) | R231-1 - R225-1 | topology/pin order | hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm |
| 61 | S2 | Net-(U24-VINL3) | R204-2 - C210-1 | topology/pin order | placement nudge: C210 / C212 (pad-bound at U24-30 / U24-4 in RT-1) and hand fan-out of the U24 west pins |
| 62 | S2 | Net-(U24-VREF) | C212-1 - U24-6 | topology/pin order | placement nudge: C210 / C212 (pad-bound at U24-30 / U24-4 in RT-1) and hand fan-out of the U24 west pins |
| 63 | S3 | /BT_FORCE_PWM | U15-2 - R153-1 | topology/pin order | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 64 | S3 | /BT_UART_TX | U3-55 - TP21-1 | topology/pin order | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 65 | S3 | /Bluetooth/BT_RST_M | R185-2 - J8-1 | topology/pin order | BM83 side: placement nudge R182/TP22 (sec.9 open problem 4); pour-island rejects need one added GND via to anchor the GND_BCU piece; route the J8/BM83 nets first inside S3 |
| 66 | S3 | /CHG_ENABLE | R107-1 - U3-38 | topology/pin order | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 67 | S3 | /MCU/NRST | J6-3 - TP19-1 | topology/pin order | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 68 | S3 | /PDCTRL_SCL | U3-43 - R15-2 | topology/pin order | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 69 | S3 | /PD_PLUG_EVENT | R16-1 - U11-37 | topology/pin order | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 70 | S3 | /PD_SINK_EN | U3-63 - R17-2 | topology/pin order | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 71 | S3 | Net-(U11-ADC4) | R10-2 - U11-7 | topology/pin order | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 72 | S1 | /I2S_BCK | R207-2 - U7-13 | no path (local pocket) | hand template: stitched B.Cu hops through the TP12/TP13/TP14 + R206-R208 hub (BKO_U6/U7 forbid B.Cu at the IC legs); or placement: swap TP12/TP14 order |
| 73 | S1 | /I2S_LRCK | TP14-1 - R208-2 | no path (local pocket) | hand template: stitched B.Cu hops through the TP12/TP13/TP14 + R206-R208 hub (BKO_U6/U7 forbid B.Cu at the IC legs); or placement: swap TP12/TP14 order |
| 74 | S1 | Net-(U24-XO) | Y200-3 - U24-9 | no path (global) | placement nudge: C226 about 0.3 mm off the Y200-1 centre line (Y200-1 pad-bound in RT-1) |
| 75 | S2 | /AUD_SCL | U24-24 - R209-2 | no path (local pocket) | hand template: AUD I2C crossing at U6/TP17/TP18 with one stitched B.Cu hop; U24-23/24 pocket is the 3V3_AUDIO feed |
| 76 | S2 | /AUD_SDA | R210-2 - U24-23 | no path (global) | hand template: AUD I2C crossing at U6/TP17/TP18 with one stitched B.Cu hop; U24-23/24 pocket is the 3V3_AUDIO feed |
| 77 | S2 | /AUD_SDA | U24-23 - U7-15 | no path (local pocket) | hand template: AUD I2C crossing at U6/TP17/TP18 with one stitched B.Cu hop; U24-23/24 pocket is the 3V3_AUDIO feed |
| 78 | S2 | /BT_AUDIO_R | C203-1 - C233-1 | no path (local pocket) | hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm |
| 79 | S2 | /Headphone_Aux/HP_OUTL | J2-5 - U10-16 | no path (global) | hand route J2-5 -> U10-16 (one stitched hop), corridor taken by S2 audio nets |
| 80 | S2 | /USB_AUDIO_R | C201-1 - C231-1 | no path (global) | hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm |
| 81 | S2 | /USB_AUDIO_R | C231-1 - C187-2 | no path (local pocket) | hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm |
| 82 | S2 | Net-(C231-Pad2) | C231-2 - R227-1 | no path (local pocket) | hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm |
| 83 | S2 | Net-(C235-Pad2) | R225-1 - C235-2 | no path (local pocket) | hand route the coupling-cap block C200-C205/C230-C235 (dense, 0.5 mm audio clearance + 0.6 mm halo); or spread the block by 0.5-1 mm |
| 84 | S2 | Net-(U24-VINL1) | R200-2 - C206-1 | no path (local pocket) | placement nudge: C210 / C212 (pad-bound at U24-30 / U24-4 in RT-1) and hand fan-out of the U24 west pins |
| 85 | S2 | Net-(U24-VINL1) | C206-1 - U24-3 | no path (local pocket) | placement nudge: C210 / C212 (pad-bound at U24-30 / U24-4 in RT-1) and hand fan-out of the U24 west pins |
| 86 | S2 | Net-(U24-VINL2) | C208-1 - U24-1 | no path (local pocket) | placement nudge: C210 / C212 (pad-bound at U24-30 / U24-4 in RT-1) and hand fan-out of the U24 west pins |
| 87 | S2 | Net-(U24-VINR1) | R201-2 - C207-1 | no path (global) | placement nudge: C210 / C212 (pad-bound at U24-30 / U24-4 in RT-1) and hand fan-out of the U24 west pins |
| 88 | S2 | Net-(U24-VINR1) | C207-1 - U24-4 | no path (global) | placement nudge: C210 / C212 (pad-bound at U24-30 / U24-4 in RT-1) and hand fan-out of the U24 west pins |
| 89 | S2 | Net-(U24-VINR2) | R203-2 - C209-1 | no path (local pocket) | placement nudge: C210 / C212 (pad-bound at U24-30 / U24-4 in RT-1) and hand fan-out of the U24 west pins |
| 90 | S2 | Net-(U24-VINR2) | C209-1 - U24-2 | no path (local pocket) | placement nudge: C210 / C212 (pad-bound at U24-30 / U24-4 in RT-1) and hand fan-out of the U24 west pins |
| 91 | S2 | Net-(U24-VINR3) | C211-1 - U24-30 | no path (global) | placement nudge: C210 / C212 (pad-bound at U24-30 / U24-4 in RT-1) and hand fan-out of the U24 west pins |
| 92 | S3 | /5V_LOGIC_EN | R142-1 - U3-18 | no path (global) | U14-1 rule-bound (SYS_RAW, POWER_HI 0.4 mm); placement nudge R142 / hand neck; R142 -> U3-18 sequential blocking |
| 93 | S3 | /ADC_INT | R211-1 - U24-21 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 94 | S3 | /AMP_BOOST_EN | U3-24 - R255-1 | no path (global) | U25-2 rule-bound (U25-SW pour); placement nudge R255/R252 and hand neck |
| 95 | S3 | /AMP_FAULT_N | U3-25 - R262-2 | no path (global) | hand escapes inside BKO_U6/U7 (F.Cu only); placement nudge C283 / C296 (RT-1 pad-bound U6-17 / U7-17) |
| 96 | S3 | /AMP_FAULT_N | R262-2 - U6-9 | no path (local pocket) | hand escapes inside BKO_U6/U7 (F.Cu only); placement nudge C283 / C296 (RT-1 pad-bound U6-17 / U7-17) |
| 97 | S3 | /AMP_FAULT_N | U6-9 - TP20-1 | no path (local pocket) | hand escapes inside BKO_U6/U7 (F.Cu only); placement nudge C283 / C296 (RT-1 pad-bound U6-17 / U7-17) |
| 98 | S3 | /AMP_FAULT_N | TP20-1 - U7-9 | no path (global) | hand escapes inside BKO_U6/U7 (F.Cu only); placement nudge C283 / C296 (RT-1 pad-bound U6-17 / U7-17) |
| 99 | S3 | /AMP_PDN | R257-1 - R258-1 | no path (global) | hand escapes inside BKO_U6/U7 (F.Cu only); placement nudge C283 / C296 (RT-1 pad-bound U6-17 / U7-17) |
| 100 | S3 | /BT_PWR_EN | U15-1 - R152-1 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 101 | S3 | /BT_PWR_EN | R152-1 - U3-36 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 102 | S3 | /Battery_Charger/CE_N | R103-2 - Q100-3 | no path (local pocket) | BM83 side: placement nudge R182/TP22 (sec.9 open problem 4); pour-island rejects need one added GND via to anchor the GND_BCU piece; route the J8/BM83 nets first inside S3 |
| 103 | S3 | /Battery_Charger/ILIM_HIZ | U4-17 - R108-2 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 104 | S3 | /Battery_Charger/ILIM_HIZ | R108-2 - Q101-3 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 105 | S3 | /Battery_Charger/TS_SENSE | U4-16 - J5-2 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 106 | S3 | /CHG_INT | U4-21 - R106-2 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 107 | S3 | /CHG_SYS_ENABLE | U3-42 - Q102-1 | no path (global) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 108 | S3 | /CHG_SYS_ENABLE | Q102-1 - R111-1 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 109 | S3 | /CTRL_SCL | U4-14 - TP16-1 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 110 | S3 | /CTRL_SCL | R120-2 - U3-60 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 111 | S3 | /CTRL_SDA | U4-15 - TP15-1 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 112 | S3 | /Fuel_Gauge_Power/GAUGE_ISO_N | Q104-3 - U17-4 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 113 | S3 | /HP_EN | R236-1 - U10-13 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 114 | S3 | /HP_EN | U10-13 - U3-47 | no path (global) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 115 | S3 | /HP_G0 | U3-16 - R237-1 | no path (global) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 116 | S3 | /HP_G0 | R237-1 - U10-6 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 117 | S3 | /HP_SEL_B | R235-1 - U3-51 | no path (local pocket) | S2 tracks of U8-NO1/NO2, U9-NO1/NO2 took the reserved escape (reservation order defect); hand reroute those 4 short nets (ratios 3.4-4.1) clear of U8/U9 pins 1 and 5 |
| 118 | S3 | /PDCTRL_SCL | R15-2 - J4-2 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 119 | S3 | /PD_SINK_EN | R17-2 - U11-19 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 120 | S3 | /USB_CC1 | J1-A5 - D5-1 | no path (local pocket) | hand template: CC1/CC2 B.Cu hop right at J1 (S0b report open problem 3); J1-B5 pad-bound by VBUS |
| 121 | S3 | /USB_CC1 | D5-1 - C182-1 | no path (global) | hand template: CC1/CC2 B.Cu hop right at J1 (S0b report open problem 3); J1-B5 pad-bound by VBUS |
| 122 | S3 | /USB_CC1 | C182-1 - U11-28 | no path (local pocket) | hand template: CC1/CC2 B.Cu hop right at J1 (S0b report open problem 3); J1-B5 pad-bound by VBUS |
| 123 | S3 | /USB_CC2 | D5-2 - C183-1 | no path (global) | hand template: CC1/CC2 B.Cu hop right at J1 (S0b report open problem 3); J1-B5 pad-bound by VBUS |
| 124 | S3 | Net-(Q101-G) | Q102-3 - Q101-1 | no path (global) | pour/power copper edits from RT-1 sec.3 (BAT_INT notch, REGN reroute, VBUS_PD pour corner); U4-18 is rule-bound (switch_critical 2.0 mm to BTST2): rule question |
| 125 | S3 | Net-(U15-FB) | U15-4 - R151-1 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 126 | S3 | Net-(U16-NC) | U16-1 - U5-7 | no path (global) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 127 | S3 | Net-(U2-SEL0) | U2-9 - C171-1 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 128 | S3 | Net-(U2-SEL0) | C171-1 - U2-8 | no path (global) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 129 | S3 | Net-(U2-SEL0) | U2-8 - R173-2 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 130 | S3 | Net-(U25-COMP) | R254-1 - U25-18 | no path (local pocket) | U25 switch-node copper and switch_critical rules: placement nudge R252 / C314 (RT-1), hand template for FB/COMP/ILIM/SS/MODE |
| 131 | S3 | Net-(U25-FB) | R250-2 - U25-17 | no path (local pocket) | U25 switch-node copper and switch_critical rules: placement nudge R252 / C314 (RT-1), hand template for FB/COMP/ILIM/SS/MODE |
| 132 | S3 | Net-(U25-ILIM) | R253-1 - U25-19 | no path (local pocket) | U25 switch-node copper and switch_critical rules: placement nudge R252 / C314 (RT-1), hand template for FB/COMP/ILIM/SS/MODE |
| 133 | S3 | Net-(U25-SS) | C266-1 - U25-10 | no path (local pocket) | U25 switch-node copper and switch_critical rules: placement nudge R252 / C314 (RT-1), hand template for FB/COMP/ILIM/SS/MODE |
| 134 | S3 | Net-(U4-QON) | U4-12 - R113-1 | no path (local pocket) | sequential blocking in the U3/U4/U11 fan-out: hand route in importance order, or a negotiated-congestion stage (not implemented) |
| 135 | S3 | Net-(U6-~{PDN}) | U6-17 - R257-2 | no path (local pocket) | hand escapes inside BKO_U6/U7 (F.Cu only); placement nudge C283 / C296 (RT-1 pad-bound U6-17 / U7-17) |
| 136 | S3 | Net-(U7-~{PDN}) | U7-17 - R258-2 | no path (global) | hand escapes inside BKO_U6/U7 (F.Cu only); placement nudge C283 / C296 (RT-1 pad-bound U6-17 / U7-17) |


## 6. Open problems

1. **Completion 51 % (145/283 with the template).** The router closes what is reachable. The rest needs one of the following, not tuning (AG13 stop after 2 iterations):
   - placement nudges of the named passives (section 5);
   - hand templates: I2S hub B.Cu hops, AUD I2C crossing, J1 CC hops, J7 escapes, BM83 pins 8/9, XTO extension, U24/U25 fan-outs;
   - the RT-1 copper edits (3V3_AUDIO feed at U8/U9, BAT_INT / REGN / VBUS_PD pours);
   - a router fix for the reservation order (section 4.1).
2. **Length quality fails** (median 1.175, p95 3.59, 14 nets > 1.4). Mostly short audio 2-pin nets forced into detours, plus the 4 U8/U9-NO nets that took the HP_SEL lanes. Hand-join or rip these before any acceptance.
3. **Section 14.1 stitching along B.Cu runs** fails for Net-(C234-Pad2), /AUX_R, /BT_AUDIO_R (GND via spacing > 8 mm). Add GND vias along these runs, or teach the router to stitch along runs.
4. **BM83 nets** regressed against the isolated N2k run (-5 connections) because of S3 order. Routing J8/BM83 nets first in S3 would need a change to OR2 order: a coordinator decision.
5. **Inherited items, unchanged:**
   - 16 foreign unconnected items: 3V_AO and GND around U3/J7, and the LDO_3V3 island;
   - the template DP via 1.86 mm from GND;
   - 2 template exceptions (T-junctions, bend spacing at J1/D1);
   - r7 acute joints 19 (all inherited power copper).
6. **Teardrops** are still absent: S0b removed 51, and none were regenerated.
7. **Scratch size:** `work-route2/` is about 162 MB. Commit only RT-2.*, the scripts, the evidence and this report if wanted.

## 7. Files (`ai-files/pcb/work-route2/`)

- **Result:** `RT-2.kicad_pcb/.kicad_pro/.kicad_dru` (= A1-3, byte-identical board), `RT-2.manifest.json` (S0-S3 locks).
- **Checks on RT-2:**
  - `RT-2.check.json/.txt`, `RT-2.drc.json`, `RT-2.r7.json`, `RT-2.par.json`;
  - `RT-2.sentinel.txt` with `sentinel/`;
  - `RT-2.fpdiff.json/.txt`, `RT-2.rulehash.txt`;
  - `RT-2.unrouted.md`.
- **Runs:** `A1-*`, `A2-*`, `A3-3*` (boards, `*.route.json` logs, DRC, manifests), plus `A1.log`, `A2.log`, `A3.log`, `A1.analyze.json`, `A2.analyze.json`, `A3.analyze.json`, and `A1-3/A2-3` check outputs.
- **H0:** `H0.*`, `H0.nets.txt`, `kept.txt`, `all-signals.txt`, `order.txt`, `hard-nets.txt`.
- **Scripts:**
  - pipeline: `prep_h0.sh`, `mk_s0.py`, `run_stages.sh`, `run_s3.sh`, `verify.sh`;
  - analysis: `analyze.py`, `netsum.py`, `unrouted_table.py`, `probe_exits.py`, `pocket.py`;
  - measurement: `fpdiff.py`, `bref.py`, `fref.py`, `brun.py`;
  - rendering: `render.sh`.
- **Evidence (`evidence/`):** `rt2-F.png`, `rt2-B.png` (+ `.svg`; top view, B.Cu not mirrored), `exitprobe-H0.txt`, `exitprobe-A1-1.txt`, `exitprobe-A1-2.txt`, `RT-2.unrouted.md`.
