# R6k routing re-review (Fable, 2026-10-09): `work-r6/R6k-final.kicad_pcb`

Scope: routing quality only, read-only, independent of `pcb-routing-r6k.md`. Scratch copy with its `.kicad_pro`/`.kicad_dru` (byte-identical to
R6k-0 = R6j-final, `cmp`). Re-run: `kicad-cli pcb drc --severity-all`, `route_p2_open2.py all`, `route_r6c_gates.py`, `route_r6h_isl.py` vs R6k-0,
`route_r6i_bends.py` vs R6k-0, `route_r6k_audiogv.py`, `route_r6k_usbcpl.py`. Own pcbnew scripts (scratchpad `rv_*.py`): per-net copper union
(fills + tracks + arcs + vias + pads) rasterised at 0.05/0.1 mm for widest-path and cross-section cuts, ASCII copper maps of the U4 area on F/In2/B,
via attachment per layer, footprint/pad identity R6k-0 vs R6k-final, cap-GND-via distances, SW clearances, B.Cu GND pieces. Ratings are IPC-2221 at
15 K: 1 oz outer 0.6 mm 2.0 A, 1.0 mm 2.9 A, 2.0 mm 4.7 A, 3.0 mm 6.3 A, 4.7 mm 8.7 A; 0.5 oz inner 5.4 mm 2.9 A, 7.2 mm 3.6 A, 12 mm 5.3 A;
via 0.3 = 1 A, 0.4 = 1.5 A (project rule). Footprints: 360, none moved, every pad net identical to R6k-0; 38 nets have changed copper.

## Verdict: PASS WITH CONDITIONS

The R6j blocker is resolved (SYS leaves U4 on three layers with 9.9-12 A of parallel capacity after the cap band). DRC is clean apart from the
known USB items, no regression in connectivity, islands, In2 hygiene or audio. Two MAJORs remain before fabrication: the BAT_INT path is F-only at
2.0 mm for 10 mm (M1 not resolved: 4.7 A at 15 K against 9 A), and an inherited item the R6j review missed: the U4 SW1/SW2/PGND pin escapes are
0.2 mm wide for 1.2-1.7 mm. The first needs a user decision (derating or placement), the second is a routing-only fix.

| # | Criterion | Result | Evidence (R6k-final, my numbers) |
|---|---|---|---|
| 1 | Connectivity | PASS WITH CONDITIONS | Open edges 2 (/MCU/NRST, /MCU/SWCLK at J7, unchanged). DRC: 0 clearance/short/dangling/isolated/width, 37 silk/lib, 4 USB (3 skew, 1 uncoupled 17.34 mm). Parity not re-run on the scratch copy (no schematic beside it); footprints and pad nets are identical to R6j-final, so the R6j parity result (244 non-routing items) stands. |
| 2 | Power | PASS WITH CONDITIONS | B1 resolved, M2/M6 resolved, M3 resolved bar C271; M1 open (MAJOR A1); new MAJOR A2 (SW escapes). Islands 1 outline each (BAT_PACK_B 2). No dead vias (all power vias touch copper on >= 2 layers). |
| 3 | Switching / noise | PASS WITH CONDITIONS | SW copper to other nets unchanged except SW2 to REGN 0.32 -> 0.24 mm (B, 153.4,119.6: the REGN B track runs beside the 11 mm SW2 B jumper the whole way) and SW2 to Q103-G via 0.44 -> 0.22 mm (B, 154.95,120.1); both inside NECK_U4. SW1/SW2 bootstrap still through B jumpers (m2, inherited). C312 (PMID 100 nF) GND via 0.94 mm, C311 0.99, C313 on F with U4 pins 10/11. |
| 4 | Signal integrity | PASS WITH CONDITIONS | USB unchanged: DP 51.59 / DN 51.36 mm (skew 0.23), uncoupled 15.0/14.2 mm by section, DRC 17.34; DN 2 fine vias at J1. I2S 125.0/127.6/125.6 mm, vias 2/4/3, unchanged. Audio vias without GND via inside 1.2 mm: 8 (was 9, COM1 fixed), none new. No AUDIO/I2S/USB/clock copper on In2. |
| 5 | Part-specific | PASS WITH CONDITIONS | U4: regression on C101/C108 (22 uF PMID) GND vias 1.26 -> 3.28/3.84 mm (m-R1); PMID HF loop via C312 intact. U4 top-row pin escapes: see A2. C106 GND via 1.33 -> 1.02 mm. U6/U7/U24/U2/U3/U1/U11 untouched (track diff), R6j results stand. |
| 6 | Manufacturing | PASS WITH CONDITIONS | Via centre in SMD pad 3 (R10.2, R224.1, C215.1), was 7. Vias 733 x 0.6/0.3, 179 x 0.8/0.4, 43 x 0.5/0.2 (annular >= 0.15). 30 arcs, smallest R 0.4 mm on 0.2 mm tracks; one R 0.6 on a 1.0 mm In2 track (3V_AO 177.9,93.1, inner radius 0.1 mm, not acute). 0 micro-segments. Local zone clearance 0.2 on 6 U4 pours puts 9 A copper 0.21 mm from 20 small pads/tracks (Q103.4, R112.2 BATP, R102, BTST1/REGN caps): manufacturable, recorded in the fix report. |
| 7 | Corner rule | PASS WITH CONDITIONS | 7 hits reproduced, all inherited from R6j (3V_AO In2 x2, USB_DP x2, U2-D- escape, U24-AVDD B jumper, U7-OUT_B+ escape), 0 acute. The 42 removed hits were replaced by 30 tangent arcs and stub merges; DRC-clean. |
| 8 | Hygiene | PASS WITH CONDITIONS | In1 one outline, no tracks. Foreign vias in islands 32 (Q103-G via moved inside SYS_IN2). In2 signal nets all whitelisted, >= 0.32 mm from outlines. B.Cu GND under U4 now 4 small pieces (80 / 20 / 7.5 / 11 mm2) with 1-2 vias each (was 3 pieces, the 80 mm2 one had 3 vias): m-R2. Q103-G B route 19.9 -> 21.7 mm, nearest GND via 8.9 mm. |

## Re-verification of the R6j findings

| Item | Verified state in R6k-final | Status |
|---|---|---|
| B1 SYS_RAW out of U4.25 | Pad top: 0.29 mm at y 120.0, 0.44 at 119.8, >= 1.4 from 119.7 (map). Passage between SW2 pour and C311.2 GND pad: 0.91 mm wide (y 118.8), 0.4 mm long. Cap band 10.7 mm wide on F with 14 x 0.8/0.4 vias (21 A) on F+In2+B. In2 column 12.0 mm (5.3 A) at y 119-124, 7.24 mm (3.6 A) at y 125.65. SYS_COL_B 5.44 mm (9.8 A), 6 x 0.8/0.4 into SYS_BOOST_F (9 A); F extension 3.0 mm (6.3 A). Boost field 14 x 0.8/0.4; F to boost 4.66 mm (8.7 A) + In2 2.1 mm. Series minimum after the cap band: 3.6 + 6.3 = 9.9 A. The pin-top neck (0.3 mm x 0.2 mm) and the 0.9 mm x 0.4 mm passage are short necks between copper masses (0.2-0.3 mohm, < 20 mW at 8 A), pitch-limited by the 0.45 mm HotRod pin pitch, not long-trace ratings; the single SYS pin is the package limit. | RESOLVED (footprint-limited neck recorded) |
| M1 U4 power-pad escapes / BAT_INT | PMID: 0.29 -> 0.52 mm within 0.3 mm. VBUS 2/3 and 8/9: 0.6 mm necks, two F pours (4.7 and 11.6 mm2, 2 x 0.4 and 2 x 0.4 + 3 x 0.3 vias). BAT 22/23: 0.60 at the pad ends, 1.34 mm at x 154.9 (Q103-G via/track at 154.95,120.1 takes the north 0.7 mm of the strip until x 155.3), 2.00 mm from x 156.2 to 163.9. **No BAT_INT copper on In2 or B west of x 163.9** (In2 island now starts at 163.9; B holds via pads only). So 10 mm F-only at 2.0 mm = 4.7 A at 15 K; at 9 A 65 K, at 6.5 A 31 K, at 5 A 17 K; the 1.3 mm x 1.5 mm section is worse. Block: 39 x 0.8/0.4 + 1 x 0.6/0.3; In2 to Q103 7.30 mm (3.65 A) + F column 2.54 mm (5.6 A) = 9.3 A. | OPEN -> A1 |
| M2 VBUS_PD_IN2 | Cut 7.24 mm (3.6 A) at y 119.15 for y 118-127, 7.28 for y 110-118, 6.28 (3.3 A) at y 62.55 near U11 (the strip minimum now, unchanged). Widest lane 2.4 mm. No F/B parallel copper. 3 A input: 12 K rise. | RESOLVED |
| M3 PVDD via feeds | U6L 2 x 0.4 (3 A), U6R 3 x 0.4, U7L 2 x 0.4 + 2 x 0.3 (5 A, the C274 via touches PVDD_U7L_F), U7R 5 x 0.4, C272 4 x 0.4 + 2 x 0.3, boost output 16 x 0.4. C271 (U6 22 uF) still 1 x 0.6/0.3 on its own pour. PVDD_IN2 to U6: widest lane 2.9 mm, total cut 14.4 mm. | RESOLVED except C271 (m3) |
| M4 USB uncoupled | 17.34 mm DRC, unchanged; sections 2.8 (J1) + 5.9 (D1 loop on DN) + 5 (R171/R172 stagger) mm match the fix report; deleting the bumps would give 7.4 mm skew. Full speed: 12 Mb/s, >= 4 ns edges, knee ~90 MHz, lambda/20 ~ 100 mm; 17 mm of 0.25 mm single-ended trace and 0.23 mm skew are electrically irrelevant. | WAIVER JUSTIFIED (user) |
| M5 via-in-pad | 3 remain: R10.2 (135.8,60.23), R224.1 (191.09,37.67), C215.1 (151.15,80.7, U24 AVDD 100 nF). 4 dogboned, DRC clean. | PARTIAL (user) |
| M6 power via sizes | 179 of 207 POWER_HI/PVDD vias 0.8/0.4 (SYS 61/66, BAT 39/40, VBUS 16/20, PVDD 33/38, BAT_PACK 19/22, USB_VBUS 11/21). U11 VBUS_PD field 12 x 0.4 + 1 x 0.3 (19 A, 13 vias vs plan 15). | RESOLVED |

## Findings

### BLOCKER
None.

### MAJOR
**A1. BAT_INT is F-only at 1.3-2.0 mm for 10 mm (U4 pins 22/23 to x 163.9).** R6k gave the In2 crossing at x 157.6-163.9 to SYS, so BAT lost
its parallel In2; the F strip grew 1.3 -> 2.0 mm (4.7 A at 15 K) but is bounded by SYS_U4CAP_F (y 119.0), the Q103-G via/track (154.95,120.1),
C106.2, R102 (PROG) and SYS_BOOST_F (y 122.0). F, In2 and B all cross here (BAT west-east, SYS north-south), In1 is GND, so one of the two nets
gets one layer whatever is drawn: with SYS on In2 only (5.3 A) the SYS target fails instead. Smallest routing-only gains are small (+0.3-0.5 mm:
SYS_BOOST_F extension top 122.0 -> 122.2, Q103-G via to 154.7,119.95). Real options are a user decision: (a) derate BAT_INT to <= 5 A charge /
<= 6.5 A discharge (17-31 K); (b) move R102/PROG and C106 ~1.5 mm south so the strip can reach 3.5 mm (7 A), plus (a) for the pin end; (c) 2 oz outer.

**A2. U4 top-row pin escapes (inherited, identical in R6j-final, missed in the R6j review).** SW1 (pin 28) is 0.20 mm wide from y 120.0 to 118.9
then bends west into SW1_F; SW2 (pin 26) is 0.20-0.24 mm from y 120.0 to 118.3, then 0.6-0.7 mm to y 117.4; PGND pin 27 is a 0.2 mm track to
two 0.6/0.3 vias (117.5 / 118.4). Widest path pin to L1 pad: 0.2 mm for both SW nets (IPC 0.9 A) against the inductor current (ICHG up to 5 A plus
system load); a 0.2 x 1.5 mm neck is 3.6 mohm, 90 mW at 5 A. Cause: the five 0.2 mm pins at 0.45 mm pitch all escape north between C312.1
(x <= 150.24) and C311.1 (x >= 152.9), with the GND escape between SW1 and SW2. Smallest fix (routing only): extend SW1_F/SW2_F to the pad ends at
the pitch limit (SW1 0.34 mm, SW2 0.43 mm to y 119.4 then 0.9 mm), and take PGND pin 27 south into the body to 2-4 GND vias instead of north;
that frees SW1 to ~0.7 mm and SW2 to ~1.0 mm. Next lever is placement (C311/C312 0.3 mm outward).

### MINOR
- m-R1 (regression). C101.2/C108.2 (PMID 22 uF) GND vias moved to x 142.0: 3.28 / 3.84 mm from the pads (were 1.26), on the 20 mm2 F GND pour which
  does not reach any U4 GND pin on F (pins 10/11 sit in a separate 4.6 mm2 F piece with C313/C111, pin 27 on its own escape). Return is via In1.
  The 100 nF C312 loop (0.94 mm) is intact; the trade-off bought M2. Acceptable; +2-3 nH on the bulk loop.
- m-R2 (regression). B.Cu GND under U4 split into 4 pieces of 80/20/7.5/11 mm2 with 1-2 vias each (SYS_COL_B and the Q103-G B track cut it).
  The B.Cu signals there (CTRL_SCL, AUD_SCL, AMP_PDN, REGN, SW2 jumper, Q103-G) reference In2 power islands. Harmless for these slow nets.
- m-R3 (regression). SW2 B jumper to REGN B track 0.24 mm (parallel ~10 mm, inherited pair) and to the Q103-G via 0.22 mm; both DRC-legal inside
  NECK_U4. Fix with m2 (bootstrap on F) when the U4 area is reworked.
- m3. C271 (U6 22 uF) on one 0.6/0.3 via; reaches U6 only through PVDD_IN2. Bulk only, acceptable; add a second via if AMP_FAULT_N moves.
- m4. 8 audio/I2S vias without a GND via inside 1.2 mm (list in `pcb-routing-r6k.md`), unchanged; needs the 3V3_AUDIO In2 trunk moved 0.5 mm.
- m5. Via-in-pad R10.2, R224.1, C215.1: solder wicking on hand-soldered 0402s; C215 is the U24 AVDD HF cap.
- m6. Inherited and unchanged: 17 pre-R6i foreign vias in In2 islands, I2S trio at 0.2 mm gap over 30 mm, TP stubs on I2C, trunks below class width
  (3V3_AUDIO 0.3, 5V_LOGIC 0.4, REGN 0.4 B 42 mm), U11 VBUS_PD 13 vias vs plan 15, SW1/SW2 bootstrap on B (m2).

## Regression check summary
No footprint moved; 38 nets changed (power pours/vias, arcs, dogbones, Q103-G). Open edges, DRC, islands (1 outline each), foreign vias (32),
In2 signal gaps, audio vias (8, none new), USB copper (untouched) all equal to R6j-final or better. New B.Cu SYS pour: In2 above it is SYS_IN2,
In1 solid; no B signal crosses it (only the Q103-G track runs beside it at y 115.3). Only regressions found: m-R1, m-R2, m-R3 above.

## Items needing a USER decision
1. A1 BAT_INT: accept derating (<= 5 A charge, <= 6.5 A discharge, 17-31 K on the 2.0 mm strip) or move R102/PROG and C106 (placement).
2. A2 SW escapes: authorise the PGND pin-27 re-route (GND vias inside the U4 body) and the pitch-limit pours; optionally C311/C312 0.3 mm outward.
3. M4 USB: record the full-speed waiver (17.3 mm uncoupled, DN 2 fine vias) and relax `usb_diff` max uncoupled to 18 mm for this pair with the
   reason, or rotate D1 and move R172 (placement). Recommendation: waiver.
4. M5: POFV (paid on JLC 4-layer) for the 3 remaining via-in-pad, or move C215/C212 and re-route the two In2 slow nets, or accept for hand assembly.
5. J7 NRST/SWCLK: still 2 open edges (test-only vs connected).
6. m-R1: accept the PMID bulk GND via distance (3.3-3.8 mm) as the price of M2, or revisit when the U4 area is reworked for A2.
