# PCB routing phase 0 and first autorouter trial (2026-10-07) - DRAFT, not sign-off

Board: placement v9b (136.9 x 127.8 mm, 4 layers). All work was done on copies in `ai-files/pcb/work-p0/`; nothing was written to `DesktopSpeaker-kicad/`. Routed draft: `ai-files/pcb/DesktopSpeaker-p0-routed.kicad_pcb` (needs its `.kicad_pro`/`.kicad_dru` from `work-p0/DesktopSpeaker-final.*` for DRC). Phase-0 only (zones + vias, no autorouter): `ai-files/pcb/DesktopSpeaker-p0-zones-vias.kicad_pcb`. Placement backup: `ai-files/pcb/DesktopSpeaker-v9-placement.kicad_pcb`. No footprint was moved.

## 1. What was done
1. **Zones** (`helpers/route_p0_zones.py`, nothing hard-coded: outline, BM83 keep-out and islands are derived from the board):
   - In1.Cu (L2) solid GND over the outline (inset 0.3 mm), B.Cu GND pour; filled 95.6 % / 95.0 % of the board area. BM83_ANTENNA_KEEPOUT stays empty on all 4 layers (0 copper hits, rule rf_keepout clean).
   - In2.Cu islands: 21 rectangles from pad clusters per rail (single-linkage 10 mm, grown 1 mm, min width 3.5 VBUS / 8 SYS / 6 BAT, PVDD / 2.5 mm others, clipped to the outline and trimmed against each other, gap >= 0.5 mm). Nets: SYS_RAW x5, USB_VBUS x2, VBUS_PD, BAT_INT, BAT_PACK x2, PACK_RAW, PVDD x3, 5V_LOGIC, 5V_CODEC, 3V8_BT x2, 3V3_AUDIO x2, 3V_AO x2. An island is only kept if at least one rail via lands in it; 4 clusters were dropped (BAT_INT#1, PVDD#3, 5V_LOGIC#0, 3V3_AUDIO#0).
   - F.Cu pours: same rectangles for the POWER_HI/PVDD nets (not PACK_RAW), pad connection thermal with 0.4 mm spokes, power pads of those nets direct. 24 F.Cu no-pour rule areas (pad + 0.8 mm) around SWITCH-class pads that overlap a pour.
   - Pad connection: mounting holes H1-H10 and TP GND pads direct; hand-soldered THT GND pads (connector shields) get spokes; SMD exposed pads direct.
   - Zone clearances: GND pours 0.4 mm (the zone filler ignores the `.kicad_dru` vbus/pvdd rules; with 0.2 mm the HI vias sat 0.2 mm from GND copper and DRC flagged 40+ clearance errors), POWER_HI zones 0.45, PVDD 0.35, others 0.25.
2. **Vias** (0.6/0.3 GND, 0.8/0.4 power with 0.6/0.3 fallback): 203 GND vias, each beside its pad with a 0.2-0.5 mm stub on F.Cu (own via per pad, DRC clean): decap and IC GND pads, plus diodes, crystals, TPs, ferrites and inductors. Exposed-pad arrays: U6 and U7 16 each (0.9 mm pitch), U25 pad 21 6, U1 pad 56 4, U10 1, C275 4, U11 and U19 0. 44 further rail vias to In2 (SYS 9, 5V_LOGIC 7, 3V3_AUDIO 6, PVDD 6, 3V_AO 5, 3V8_BT 5, 5V_CODEC 5, USB_VBUS 3, BAT_PACK 2, VBUS_PD 1, BAT_INT 1). Totals in the final board: 275 vias (254 0.6/0.3, 21 0.8/0.4).
3. **Autorouter**: DSN export (pcbnew `ExportSpecctraDSN`), then `route_p0_dsn_filter.py` removes critical nets from the DSN network (they stay as pad obstacles), turns existing wiring into `protect`, sets In1.Cu to a power layer (no routing on the GND plane). Freerouting 2.5.0 on **Java 25** (needs it; the Java 21 JRE fails with class file 69; Temurin 25.0.4.1 JRE installed in `~/Applications/freerouting/jre25`). Two batches, `-mp 4` and `-mp 3`, 25 min cap each, run in the background:
   - Batch A: SIGNAL + I2C: 146 nets started, 41 unrouted after 4 passes, 3 min 53 s.
   - Batch B: PWR_5V + PWR_3V + PWR_LOCAL + GND (GND fan-out to planes): 251 started, 100 unrouted, 8 min 13 s.
   - Excluded (121 nets, `ai-files/pcb/route-p0-critical-nets.json`): AUDIO, I2S_CLK, USB, SWITCH, BOOT, SPK_OUT, POWER_HI, PVDD and every net touching U1, U6 or U7. After import no track of those nets exists (all non-P0 items of these nets are removed by `route_p0_prune.py`).
   - The DSN carries only the class widths, not clearances: every class has clearance 0.2 in the DSN; the custom `.kicad_dru` clearances (audio 0.5, vbus 0.4, pvdd 0.3, switch 1.0, clk 0.4) are NOT exported, so the autorouter does not know them.
4. **Clean-up** (scripted): widen 0.1874 mm neck-down tracks (Freerouting shrinks at fine-pitch pins) to the 0.2 mm project minimum; delete autorouter items involved in clearance/annular/dangling violations, 7 prune rounds; fix one 0.6/0.4 via to 0.6/0.3; refill all zones.

## 2. Metrics (final board)
| Item | Value |
|---|---|
| DRC (all severities, project rules) | 54 items, all inherited: silk_over_copper 19, silk_overlap 18, drill_out_of_range 8 (U11 thermal vias 0.2), silk_edge_clearance 6, hole_clearance 2 (SW100); 1 new warning: track_dangling 1 |
| clearance / shorting / annular / via_dangling | 0 |
| unconnected items | 474 (499 before routing). The autorouted net lengths below were cut back by the dangling-track prune, so only a small part of batch A/B stayed |
| unconnected by class (items) | AUDIO 85, SIGNAL 125, GND 43, PWR_3V 41, SWITCH 30, POWER_HI 32, I2C 23, I2S_CLK 22, PVDD 17, PWR_LOCAL 15, SPK_OUT 12, BOOT 11, PWR_5V 9, USB 9 |
| routed length (final) | GND stubs 502 mm, PWR_5V 171, PWR_3V 94, SIGNAL 51, PWR_LOCAL 44, POWER_HI 19 (P0 rail stubs), PVDD 8, I2C 6 |
| tracks by layer | F.Cu 620, B.Cu 34 (slow signals), In2.Cu 30 (slow signals, none on In1) |
| track width audit vs plan sec. 2 DRC minimum | 98 tracks below: 93 GND stubs (0.2-0.375 mm vs GND 0.4: stub width follows the 0.28-0.5 mm pad width) and 5 PWR_3V (0.25 on 3V_AO vs 0.3). Nothing on POWER_HI/PVDD/SPK_OUT/AUDIO/I2S/USB below its minimum |
| vias | 275 (254 x 0.6/0.3, 21 x 0.8/0.4); GND 215 |
| GND decap/IC pads (209) without own via | 28 (list below) |
| antenna keep-out | empty on 4 layers |

Note: unconnected items is the DRC count (ratsnest pairs), not nets; it fell only 5 % because the cut-back removed most partial routes. Treat the autorouter result as a draft that proves the toolchain, not as routing progress.

## 3. Nets left for hand routing, by block
- **AUDIO** (47 nets, all): AUX_L/R, BT_AUDIO_L/R, USB_AUDIO_L/R, headphone and mux nets, ADC inputs, VMID_HP (8 open pairs), VREF; L1 only over In1, 0.3 wide, 0.5 clearance, guard fence.
- **I2S / clocks** (10): I2S_BCK/LRCK/SDATA, U24 BCK/LRCK/DOUT, both crystal pairs.
- **USB** (4): USB_DP/DN, U2 D+/D-; pair 0.25/0.15.
- **Class-D outputs** (SWITCH 13 + SPK_OUT 6 + BOOT 11): U6/U7 OUT_x to L201-L206, filters C302-C307 to J9-J11, BST caps, U25 SW/BOOT.
- **Boost loop and power** (POWER_HI 7, PVDD 1): SYS_RAW L200/U25/C26x, PVDD_AMP U25 to U6/U7 (largest open: PVDD 17 pairs), BAT_INT/BAT_PACK/PACK_RAW to Q103, SW101, J5; USB_VBUS J1 to U11 (8 open pairs), VBUS_PD.
- **Charger SW**: SW1/SW2 L1, BTST1/2, REGN (4 open), PMID.
- **BM83 supply and U1/U6/U7 nets**: 3V8_BT (6 open), U15 L1/L2, all control nets touching U1 (UART, RST, MFB, PWR_EN), U6/U7 digital nets (I2C AUD_SCL/SDA 5 each, PDN, FAULT).
- **Rails not finished**: 3V3_AUDIO (23 open pairs), 3V_AO (7), LDO_3V3, 5V_LOGIC; GND: 43 pad pairs (resistor/connector GND pads and the 28 pads without via).
- **GND pads without own via** (no room beside pad, all need a hand decision): U3.9, U10.10, U4.10/11, U6.20/26/31, U7.5/20, U11.2/5/11/12/14/16/17/26/27/31, U15.3/8, U25.11, U14.8, C213.2, C294.2, C278.2, C238.2, C289.2. Most are IC GND pins beside an exposed pad that can be bridged to it by a short stub.

## 4. Problems in the plan or placement
1. Netclasses and stackup were missing from the project and board (build_pcb_v9 reset them). `setup_pcb_rules.py` must run after each placement build (now done by the build script).
2. **U4 BQ25792**: footprint `BQ25792RQMR.kicad_mod` has 29 pads; pad 29 is PMID (0.2 x 0.95 mm), consistent with the datasheet table (pin 29 = PMID). RQM0029A VQFN-HR has no exposed thermal pad, so the plan's "12 thermal vias in the IC pad" does not apply to U4; the heat goes through the pins and the SW/PMID pours.
3. **U25 TPS61088**: `TPS61088RHLR.kicad_mod` has 21 pads; pad 21 is a single custom polygon (about 3.05 x 2.0 mm centre plus side fingers) = the PowerPAD, so the pad exists; my array found 6 vias inside it (0.9 mm pitch, hit-tested). The plan's 9 vias do not fit unless pitch drops to 0.8 mm. TPS61088 datasheet is still only an excerpt.
4. U6/U7 exposed pad is 3.45 mm square: 16 vias at 0.9 mm pitch (plan says ~20 at 1.0-1.2 mm: not possible). U11 pad has its own 0.2 mm vias (inherited drill flags), U19 pad (1.6 x 2.0) took no via.
5. No room for a beside-pad via on 41 GND pads and for 55 rail vias; dense blocks: U4 charger (VBUS_PD, SYS_RAW, PMID, BAT_INT within 10 mm, islands only 3-8 mm wide), Q103 (BAT_INT and BAT_PACK pads 3 mm apart), U6 PVDD pins versus 3V3 pins at 0.5 mm.
6. Zone filler ignores `.kicad_dru` clearances for zone-to-via: set the zone clearance in the zone itself (done: GND 0.4).
7. Freerouting ignores the dru clearances and the island pours, wastes 7 min on fan-out for GND, and its passes oscillate (batch A: 114, 258, 151, 249, 143 unrouted), so many short pad-to-pad routes dangle after DRC pruning. The default run also puts signals on In1 unless In1 is a power layer (fixed in the filter).
8. In2 signal routes cut through the rail islands (the autorouter does not know them); about 30 In2 segments exist, to be reviewed or moved to B.Cu.

## 5. Recommended order for the next pass
1. Decide the 28 GND pins without via (bridge to the exposed pad) and approve the island rectangles (list in `ai-files/pcb/route-p0-zones-report.json`).
2. Hand route PD input and charger: J1 to U11, VBUS_PD and SYS pours, SW1/SW2 and BTST (rule: no inner connection of SW).
3. Boost U25/L200 and PVDD to U6/U7 on the L1 pour with the 6-8 vias per transition; class-D OUT_x to inductors and filters.
4. BM83 supply and UART; then codec/analogue (AUDIO nets) and USB pair, I2S.
5. Re-run Freerouting only on SIGNAL/I2C/PWR_LOCAL/enable lines, one block per run, minimum 0.25 mm, no In2 for signals through islands, and give Freerouting the dru clearances through the DSN (add per-class clearances before export).
6. Teardrops (GUI), zone refill, DRC, loop-area and width scripts from plan sec. 7.

## 6. Scripts (`ai-files/helpers/`)
`route_p0_classes.py` (net to class), `route_p0_zones.py` (P0 zones and vias), `route_p0_dsn.py`, `route_p0_dsn_filter.py`, `route_p0_batch.sh` (prep/post), `route_p0_ses.py` (import, clean), `route_p0_prune.py`, `route_p0_final.py`, `route_p0_metrics.py`, `route_p0_checks.py`. Evidence: `ai-files/pcb/route-p0-*` (DSN/SES per batch, DRC json, renders, F.Cu/In2.Cu plots), `work-p0/` (Freerouting logs, intermediate boards).
