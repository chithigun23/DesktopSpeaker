# R6l routing re-review (Fable, 2026-10-09): `work-r6/R6l-final.kicad_pcb`

Scope: routing quality only, read-only, independent of `pcb-routing-r6l.md`. Scratch copies of R6l-0 (= R6k-final, `cmp` identical) and R6l-final with
their `.kicad_pro`/`.kicad_dru` (byte-identical to R6k, `cmp`). Re-run on the scratch copies: `kicad-cli pcb drc --severity-all`, the strict check
(`route_r6l_splitall.py` 1 mm pieces + `drc --all-track-errors`, both boards), `route_p2_open2.py all`, `route_r6c_gates.py`, `route_r6h_isl.py` vs
R6l-0, `route_r6i_bends.py` vs R6l-0, `route_r6k_audiogv.py`, `route_r6k_neck.py`/`route_r6k_cut.py` (agent cases + my own cuts). Own pcbnew scripts
(`/tmp/scratchpad/rv_*.py`): per-net width statistics and footprint/pad/via/track net diff by uuid, companion-zone (`*_G`) pieces/clearance/sliver/
attachment test, GND fill pieces and floating-piece test, per-net clearance tables for SWITCH and AUDIO/I2S/USB classes before vs after, widened-track
proximity to sensitive copper, U4 pad audit, track-wider-than-pad ends. Ratings IPC-2221 at 15 K as in the R6k review (1 oz: 2.0 mm 4.7 A, 3.1 mm 6.5 A,
4.7 mm 8.7 A; 0.5 oz inner 7.24 mm 3.3-3.6 A).

## Verdict: PASS WITH CONDITIONS

A1 and A2 are resolved to the extent the footprint allows; DRC, strict DRC, connectivity, islands, corner rule and In2 hygiene are at or better than
R6k-final; the overspec pass is real (every row of the 29-net width table reproduced exactly, no net's minimum or average width decreased, no net
changed on any pad/via/track). Nothing blocks. Before fabrication: remove the sub-minimum copper slivers that the companion pours created (MAJOR B1,
trivial), and decide the PGND-via and clearance items below. One claim in the fix report is stale (SW2-REGN on B is 0.215 mm, not 0.306).

| # | Criterion | Result | Evidence (R6l-final, my numbers) |
|---|---|---|---|
| 1 | Connectivity | PASS WITH CONDITIONS | Open edges 2 (J7 NRST/SWCLK, unchanged). DRC: 0 clearance/short/dangling/isolated/width/courtyard, 36 silk + 1 lib, 4 USB (3 skew, 1 uncoupled 17.34). Strict DRC (5269 split pieces): the same 3 inherited items as R6l-0 (5V_LOGIC-SYS_RAW In2 0.3991; U24 XI/VINR2 0.2 mm escapes; USB gap pieces at J1), nothing new: confirmed clean. Footprints 360/360, only C106 (+0.4, +1.24) and R102 (+0.3, +1.14) moved; pad nets, via nets, track nets identical by uuid. |
| 2 | Power | PASS WITH CONDITIONS | A1: BAT_INT F strip widest 3.1 / cut 3.14 mm (x 156.5-163.8), near-pin cut 2.12 mm (x 154.6-156.5, was 1.34), pin end 0.74 mm (2 x 0.2 mm pads). A2: SW1 1.1 mm / SW2 0.9 mm from y 118.6 to L1, pitch-limited 0.5 / 0.3 mm for ~1 mm at the pins (was 0.1-0.2). PGND pin 27: 2 x 0.5/0.2 vias (m-L1). SYS: SYS_COL_B cut 6.20 mm (y 117-123.2), F copper at the second via row 4.74 mm (was 5.54; 8.7 A) in parallel with SYS_IN2 7.24 mm: series minimum >= 9 A still. VBUS_PD_IN2 cuts 7.28 / 7.24 / 6.28 unchanged. Overspec: 236 tracks widened, 291 split pieces, 13 companion pours +908 mm2; 15+ nets spot-checked, all match the table. |
| 3 | Switching / noise | PASS WITH CONDITIONS | SW1/SW2 pours >= 0.3 mm to PMID/SYS/BOOT, 0.203 mm SW1-SW2 at the pin ends (pitch). Regressions from widening (all DRC-legal inside NECK areas): SW2 B jumper to REGN B 0.237 -> **0.215** (REGN widened to 0.70 at 153.48,121.62; the report's 0.306 predates the overspec pass); U15 L1 0.6 mm track 0.206 from the SYS_RAW pin-10 pad (118.4,35.8; was 0.25); U14 L2 arc 1.0 mm 0.777 from U14 FB (95.98,102.56; was 0.90); U6/U7 OUT_x to BST pins 0.22 -> 0.20 at the pads. SW2 to Q103-G via 0.24. |
| 4 | Signal integrity | PASS WITH CONDITIONS | USB copper untouched: DP 51.59 / DN 51.36 mm, uncoupled 17.34. I2S 125.0/127.6/125.6 mm, vias 2/4/3, unchanged. Audio/I2S vias without GND via in 1.2 mm: 8, unchanged. Regressions: USB_AUDIO_R via barrel (174.2,61.8) to the widened 2.0 mm 5V_CODEC In2 track 0.542 -> **0.292** (audio rule 0.5, relaxed by NECK_U8); I2S_LRCK via to VBUS_PD_IN2_G 0.501 -> 0.402 (clk rule 0.4, at the limit); U24 AVDD 0.6 mm stub 0.225 from the XO crystal track (0.4 mm long, negligible). No AUDIO/I2S/USB/clock copper on In2. |
| 5 | Part-specific | PASS WITH CONDITIONS | U4 (no thermal pad: HotRod, pads 10/11 are ACDRV tied to GND, pin 27 is the only ground return): see m-L1. C101/C108 GND vias 0.91 / 2.51 mm (were 2.67 / 3.06). C271 second via 0.6/0.3, 0.32 from AMP_FAULT_N. PROG runs 0.35 mm between the C106 pads; BTST2 0.21 to pin 18. U6/U7/U24/U2/U3/U1/U11 pads untouched. |
| 6 | Manufacturing | PASS WITH CONDITIONS | Via-in-pad 3 (R10.2, R224.1, C215.1, unchanged). Vias 733 x 0.6/0.3, 179 x 0.8/0.4, 45 x 0.5/0.2 (+2 PGND, ring 0.15, hole-to-hole 0.37). 30 arcs, 0 micro-segments. **Slivers in companion pours (B1).** Track-wider-than-pad ends: 4 new, all on 1.8 mm test-point pads (TP3/TP7/TP10), cosmetic. |
| 7 | Corner rule | PASS WITH CONDITIONS | 7 hits, all tagged inherited vs R6l-0 (6 corner, 1 jog), 0 acute, 0 new. |
| 8 | Hygiene | PASS | In1 1 piece, 16519.8 mm2, unchanged. In2 GND filler 8897 -> 7780 mm2, 103 -> 121 pieces (44 < 2 mm2), **0 floating** (every piece holds a GND via or pad); In2 is the secondary plane, In1 return paths untouched. B.Cu GND 15285 -> 15196 mm2, 5 pieces as before; under U4 23.2 / 13.8 mm2 pieces with own vias. Foreign vias in In2 islands 32 (Q103-G via moved within SYS_IN2). In2 slow signals >= 0.32 mm from islands (same two inherited 0.32/0.33 nets; grown islands keep 0.35). |

## A1 and A2 verification

**A1 BAT_INT.** Measured 3.1 mm widest / 3.14 mm cut for x 156.5-163.8, 2.12 mm cut for x 154.6-156.5, 0.74 mm at the pins (package). 6.5 A at 15 K,
7 A 18 K, 8 A 24 K, 9 A 31 K (was 65 K). Real currents (schematic / handover): **charge** <= 5 A (BQ25792 ICHG ceiling), intended 1-3 A
(handover: start 1.0 A, 0.2-0.3 C), and bounded by the U18 eFuse limit 2.23/2.35 A (R182 5.36k) at 5/9 V, i.e. <= ~4.5 A at the cell;
**discharge** through the same pins is limited by the BQ25792 BATFET rating, IBAT 6 A RMS continuous / 10 A peak <= 1 s (datasheet
`BQ25792.txt` line 514), with the load set by U25 (ILIM 150k = 6.6-7.9 A inductor peak, so <= ~7 A DC input at low pack voltage) plus ~1 A for the
other rails: <= ~8 A momentary, far below continuous. The plan's 9 A is the pack-protection trip on BAT_PACK, not a BAT_INT design current; the
15-20 A pack peak is an unverified assumption and sits on the pack side of Q103. **The remaining derating is acceptable: the 3.1 mm strip (6.5 A at
15 K) exceeds the device's own 6 A RMS limit; no further fix required.** Record "BAT_INT <= 6 A RMS continuous, 8 A for <= 1 s" in the handover.
Parallel B.Cu copper is indeed impossible without cutting SYS_COL_B (verified: B.Cu west of x 157 holds only the SW2/REGN jumpers and GND).

**A2 SW escapes.** SW1: 0.5 mm from the pin top (y 119.6, pitch-limited) then 1.1 mm from y 118.6 to L1.1; SW2: 0.3 mm + pad then 0.9 mm. Pour
areas 14.7 / 13.2 mm2 (+3.2 / +1.9), still minimum-area pours. Resolved as far as the 0.45 mm pitch allows. PGND pin 27: the 0.2 mm north track and
its two 0.6/0.3 vias are gone; the pin now ends in a 1.68 mm2 F island inside the body with 2 x 0.5/0.2 vias (1.08 / 1.48 mm from the pad), not
joined on F to any other GND copper (see m-L1).

## Findings

### BLOCKER
None.

### MAJOR
**B1. Sub-minimum copper slivers in the companion pours** (fill tongues attached to the parent island, created where growth was clipped to
< 0.2 mm). `USB_VBUS_IN2_G` (In2, 0.5 oz): five tongues at x 153.5-153.8, y 39.2-48.8 of 0.06-0.3 mm width (two pieces 0.05 mm2 over 0.8 mm length,
about 0.06 mm wide), limited by the PDCTRL_SCL In2 track at x 154.2. `SYS_U4CAP_F_G` (F): a 6 mm x ~0.12 mm strip at y 116.4-116.8 between the C104/
C105/C107 SYS pads and their GND pads (0.75 mm2). `PVDD_BOOST_F_G` (F): 0.07 mm2 piece at (156.4-156.6, 153.6-154.1) and a 3.5 x 0.22 mm strip at
y 148.6-148.9; `PVDD_U7R_F_G` 0.5 x 1.7 mm at 0.24 mm. Below the 0.1 mm fab minimum on In2 and classic DFM rejects; KiCad's sliver check does not
see parallel-edged tongues. Smallest fix: delete `USB_VBUS_IN2_G` (USB_VBUS needs none of its 36.7 mm2) and trim `SYS_U4CAP_F_G` to y >= 116.9 and
`PVDD_BOOST_F_G` to the 47 mm2 main piece; or set min thickness 0.3 mm on all `*_G` zones, refill, re-run the piece test. All 13 companion fills
are edge-attached to their parents (gap 0.000, union 1 piece per net/layer), and their clearances are >= 0.40 mm (F) / 0.35 mm (In2) to non-GND nets
and 0.20 (F) / 0.30-from-annulus (In2) to GND, the same as the parent pours in R6l-0.

### MINOR
- m-L1. **PGND pin 27 on 2 x 0.5/0.2 vias.** Pin 27 is the only ground pin of the HotRod package (no thermal pad; pads 10/11 are ACDRV1/2 tied to
  GND). In buck mode its return is IL x (1-D): ~2.7 A average at 3 A charge from 9 V (0.8 A from 5 V), ~4 A at the 5 A ICHG ceiling. Two 0.2 mm
  barrels: ~1.4 A by the project via rule, ~3 A at 15 K by IPC; the 0.2 x 1.0 mm pad itself is the smaller cross-section. Better than the 0.9 A track
  it replaces, below the project rule at >= 3 A charge from 9 V. Smallest fix: extend `GND_U4_PGND_F` south on F to the pad-10/11 GND piece (adds its
  vias in parallel; only via pads block F copper, not the B tracks), or a third 0.5/0.2 via at the first free spot.
- m-L2 (regression, report error). SW2 B jumper to REGN B 0.215 mm at (153.73,119.48): the REGN B segment (153.48,121.62)-(153.40,119.60) was widened
  0.40 -> 0.70 after the A2 measurement. Fix: set that segment back to 0.40 (restores ~0.31).
- m-L3 (regression). 5V_CODEC In2 track widened to 2.0 mm passes 0.292 mm from the USB_AUDIO_R via barrel at (174.2,61.8) (audio rule 0.5; was 0.54).
  Fix: narrow the piece (176.28,61.97)-(170.52,67.73) to 1.0 mm or shift it 0.3 mm north-east.
- m-L4 (regression). U15 L1 switch track 0.6 mm from x 118.57 sits 0.206 mm from the SYS_RAW pin-10 pad (was 0.25); U14 L2 arc 1.0 mm is 0.777 from
  U14 FB (was 0.90). Fix: start the U15 L1 0.6 mm piece at x >= 118.9; revert the U14 L2 arc to 0.6 or leave (FB is 0.78 mm away, still DRC-legal).
- m-L5. SYS F copper at the second via row 4.74 mm (was 5.54; 8.7 A) because the two SYS via rows moved to y 123.7/124.6; with SYS_IN2 in parallel the
  series minimum stays >= 9 A. No action.
- m-L6. Inherited and unchanged: 3 via-in-pad, 8 audio vias without a GND via, 7 corner hits, 3 strict-DRC items, USB 17.3 mm uncoupled (waiver),
  J7 2 open edges, 17 pre-R6i foreign vias in In2 islands, I2S trio at 0.2 mm gap, SW1/SW2 bootstrap on B, teardrops not yet generated (GUI).

## Regression check summary
R6l-0 -> R6l-final: 2 footprints moved as authorised, 8 vias removed / 10 added / 3 moved (SYS, GND, Q103-G, PVDD only), 0 net changes, 0 width
decreases on any net, open edges / DRC / strict DRC / islands (1 outline per original island) / foreign vias / audio vias / USB / I2S / corner hits
all equal to R6l-0 or better. Only regressions found: m-L2, m-L3, m-L4 (clearances) and the B1 slivers; the C101 PMID bulk GND via improved to 0.91.

## Items needing a USER decision
1. A1: accept BAT_INT at 6.5 A continuous / 8 A for <= 1 s (matches the BQ25792 BATFET 6 A RMS / 10 A peak rating) and record it; or 2 oz outer.
2. m-L1: accept 2 x 0.5/0.2 PGND vias with charge <= 3 A from 9 V sources, or authorise the F bridge to pads 10/11 / a third via.
3. B1 fix route: delete `USB_VBUS_IN2_G` + trim two pours (recommended) versus min-thickness 0.3 on all `*_G` zones and refill.
4. m-L3/m-L4: revert the three widened pieces (recommended, 0 capacity cost) or accept the 0.21-0.29 mm gaps inside the NECK areas.
5. Standing: M4 USB waiver, M5 via-in-pad (POFV or accept), J7 NRST/SWCLK open edges, m-R1 PMID C108 GND via 2.51 mm.
