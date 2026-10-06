# PCB routing plan (2026-10-06): plan and project rule setup only, NOTHING ROUTED

Basis: `pcb-layout-rules-audio.md` (mandatory), `pcb-placement-v3-2026-10-06.md`, `ai-files/pcb/dist-v3.txt`. Board 116 x 112 mm, 311 parts, 311 nets (194 named + 117 `Net-(...)`, 112 of them one-pin `unconnected-*`). Policy from the user: AI routers go narrower than wanted, so every width below is a MINIMUM for trunks; go wider wherever space allows; power by pours; teardrops on every track-to-pad and track-to-via joint; audio noise first; hand-solder 0402/0805.

## 1. Stackup (set in the .kicad_pcb: `ai-files/helpers/setup_pcb_rules.py`)
JLC04161H-7628, 1.6 mm, 4 copper layers: F.Cu 35 um | prepreg 7628 0.2104 mm (Er 4.4) | In1 | core 1.065 mm | In2 | prepreg 7628 0.2104 mm | B.Cu 35 um, ENIG.
| Layer | Use |
|---|---|
| L1 F.Cu | all parts, all audio, I2S, USB, local power, SW nodes, every decoupling loop |
| L2 In1 | SOLID GND, no splits, no routing (<= 2 documented jumpers, none under audio/USB/I2S) |
| L3 In2 | power pours, one island per rail (SYS_RAW, BAT, PVDD, 5V, 3V rails) + a few slow signals (enables) |
| L4 B.Cu | GND pour + slow signals (strap/enable lines), no parts, stitched to L2 |
Stackup numbers are the JLC table values (0.5 oz inner 15.2 um): CONFIRM in the JLC calculator, the fetched table showed a 1.1 mm variant. Inner copper: order 1 oz inner (cheap, helps L3 power pours); set `In1/In2` thickness 0.035 and core 1.0 in the stackup if JLC confirms (re-run impedance then).
**1 oz vs 2 oz outer: recommend 1 oz outer.** 2 oz forces 0.16/0.16 mm rules, fails the 0.1 mm fine pitch of J1/U11/U19, raises cost and adds little because power is carried by L1+L3 pours with via arrays (SYS 6 A, BAT 9 A, PVDD 4 A avg). Reconsider 2 oz only if the L1/L3 pour widths in sec. 2 do not fit after routing (then limit to a "heavy copper" request, not default).
USB 90 ohm (edge-coupled microstrip over L2, h 0.2104, t 0.035, Er 4.4; IPC-2141 approximation): w 0.25 / gap 0.15 -> Zdiff about 92 ohm (the rules-doc start value 0.20/0.15 computes to about 102 ohm). Set to 0.25/0.15. The approximation is +-10 %: **JLC's calculator must confirm** (also order note "impedance control USB 90 ohm" or accept USB 2.0 tolerance; USB is under 30 mm).

## 2. Netclasses (in `DesktopSpeaker.kicad_pro`, patterns = exact net names, `SIGNAL` = catch-all `*`; per-net list `ai-files/pcb/net-classes.json`)
Track widths in mm. min = DRC floor (pad escapes) in `DesktopSpeaker.kicad_dru`; pref = router default (class track width); "trunk min" = rules-doc 2x-margin minimum for runs longer than 3 mm (checked in review, pours preferred). Clearance = planned value, enforced by `.kicad_dru` for track/via/zone items; pad-to-pad pitch is left to the footprints (netclass clearance field kept at 0.2 or the fine-pitch ICs flag 186 false hits).
| Class | Nets (count) | DRC min | pref | trunk min / form | Clearance | Via dia/drill | Notes |
|---|---|---|---|---|---|---|---|
| POWER_HI | /SYS_RAW, BAT_INT, BAT_PACK, PACK_RAW, VBUS_PD, USB_VBUS, PMID (7) | 0.5 | 2.0 | VBUS 3.5 pour, SYS 8 pour, BAT 12 pour (L3 15 mm wide + L1 pour), PMID with SYS | 0.4 | 0.8/0.4 | via count I/1 A x2: VBUS 6, SYS 12, BAT 18 per layer change |
| PVDD | /Amplifiers/PVDD_AMP (1) | 0.5 | 2.0 | 6 pour (L3 plane + L1 pour at U6/U7/U25) | 0.3 | 0.8/0.4 | 4 A avg, 8 A peaks; decap loops L1 only |
| SPK_OUT | Net-(C302..C307-Pad1) (6) filtered outputs to J9-J11 | 0.5 | 2.0 | 2.0 (3.5 if < 10 mm) | 0.3 | 0.8/0.4 | BTL pair parallel 0.3 apart, <= 40 mm |
| SWITCH | SW1, SW2, U25 SW, U14 L1/L2, U15 L1/L2, U6/U7 OUT_x (13) | 0.4 | 1.5 | polygon, 4 mm at U25/L200, short <= 15 mm | 1.0 (goal 2.0) | 0.6/0.3, no vias except SW1/SW2 pin arrays | min copper area, nothing under on L1 |
| BOOT | BTST1/2, U25 BOOT, U6/U7 BST_x (11) | 0.25 | 0.3 | 0.3, <= 3 mm | 0.3 | 0.6/0.3 | cap adjacent to IC |
| PWR_5V | 5V_LOGIC, 5V_CODEC, USB_AUX_5V, REGN (4) | 0.4 | 1.0 | 1.0 (REGN 0.5) | 0.25 | 0.6/0.3 | L3 5V pour island |
| PWR_3V | 3V3_AUDIO, 3V8_BT, 3V_AO, LDO_3V3, LDO_1V5, U1 SYS_PWR, VDD_IO (7) | 0.3 | 0.5 | 0.5 (BM83 supply 0.8) | 0.25 | 0.6/0.3 | star from regulator, one feed per IC cluster |
| PWR_LOCAL | AVDD/GVDD/VR_DIG/LDO/VCC/charge-pump/PCM2902 VCC* nodes (19) | 0.25 | 0.4 | 0.4 | 0.25 | 0.6/0.3 | local decoupling nets, L1 only |
| AUDIO | AUX_L/R, BT_AUDIO, USB_AUDIO, HP_*, coupling nets, ADC inputs, mux nets, VREF/VCOM/VMID (47) | 0.25 | 0.3 | 0.3 | 0.5 (3x w) | 0.6/0.3, avoid | L1 only over L2, ground fence |
| I2S_CLK | I2S_BCK/LRCK/SDATA, U24 BCK/LRCK/DOUT, both crystal pairs (10) | 0.25 | 0.25 | 0.25 | 0.4 | 0.6/0.3, avoid | series 22-33 ohm at source, <= 60 mm |
| USB | USB_DP/DN, U2 D+/D- (4) | 0.25 | 0.25 | pair 0.25 / gap 0.15 | 0.4 | 0.6/0.3 pair via gap 0.25 | 90 ohm, skew <= 0.5 mm |
| I2C | AUD/CTRL/PDCTRL SCL+SDA (6) | 0.25 | 0.3 | 0.3 | 0.3 | 0.6/0.3 | |
| GND | GND (1) | 0.4 | 0.5 | pours all layers | 0.2 | 0.6/0.3 | stitch grid sec. 3 |
| SIGNAL (Default) | everything else incl. 112 one-pin nets (175) | 0.2 | 0.25 | 0.25 | 0.2 | 0.6/0.3 | enables, CC lines, FB/COMP (keep away from SW) |
Total 311 nets all assigned (script verifies; Net-(U8-*)/Net-(U9-*) mux nets are AUDIO). Project minima set: clearance 0.1 (fine pitch), track 0.2, via 0.5/0.3, annular 0.15, hole-to-hole 0.3, edge 0.5. Preset lists: widths 0.25/0.3/0.4/0.5/1/1.5/2/3, vias 0.6/0.3 and 0.8/0.4, diff pair 0.25/0.15.
Custom rules (`DesktopSpeaker.kicad_dru`): audio_clear 0.5, vbus_clear 0.4, pvdd_clear 0.3, switch_clear 1.0, clk_clear 0.4, width floors, usb_diff (gap 0.15-0.25, skew 0.5), rf_keepout (no track/via/zone in `BM83_ANTENNA_KEEPOUT`), via_min (0.3 hole / 0.6 dia), fine_pitch 0.1 for J1/U11/U19, edge_hole 0.5. The width floors are below the trunk minima on purpose: a floor equal to the trunk minimum would flag every 0402 pad stub; the trunk check is the post-route script in sec. 7.

## 3. Routing order and per-block guidance (all on L1 unless stated)
Order: 1) fixed GND/L2 and keep-outs, 2) PD input chain, 3) charger/power path pours, 4) boost, 5) class-D, 6) BM83 supply, 7) codec and analogue, 8) USB audio, 9) I2S/I2C/control, 10) MCU, 11) enables/straps, 12) fill, stitching, teardrops. Escape/decoupling loops of each IC are routed before its signals. L3 islands are drawn after the power parts are routed.
- **Common rules:** one via per decap GND pad directly beside the pad (no shared vias), cap-to-pin trace short and wide (>= pad width), no vias in decap-to-pin paths (PCM1862/TAS5825M/TPS25730 DS). Orient 0402s with the narrow end to the IC. Ground stitching grid every 4-5 mm (L1/L4 pours, 0.6/0.3 vias), <= 3 mm near BM83 and along the left board edge, <= 2.5 mm beside the audio block edge. PTH M3 holes H1-H4: GND pad, 4 stitching vias each ring plus L1/L4 pours directly at the pad.
- **USB_PD (U11 TPS25730D, J1):** VBUS from J1 to TVS D6 (< 3 mm, 2 mm wide) then pour VBUS_PD >= 3.5 mm to U11 VBUS_IN/PPHV and Q-FETs; >= 15 vias at VBUS_IN/PPHV, >= 6 on other VBUS pours (0.4 drill); CC caps C181/C182 close to CC pins with via AFTER the cap; ESD D5 at the connector; do not connect the 3 unconnected DRAIN pads; D+/D- from J1 as the USB pair (via D1 TVS), stitch GND both sides.
- **Battery_Charger (U4 BQ25792):** priority SYS caps C104/C105/C107 (now 8.7-9.5 mm: see sec. 4), PMID, VBUS caps on L1 with a 0.1 uF closer than the 10 uF; SW1/SW2 polygon straight to L1 inductor pads, 4+ vias in the pins only to L1 pads, no inner-layer connection of SW; REGN and BTST1/2 caps adjacent; BATP/sense away from SW (>= 3 mm); PMID/SYS/VBUS pours L1 plus L3 island with 12 vias per transition; 12+ thermal vias in the IC pad; BAT_INT/PACK_RAW to J5 and Q103 on a 12 mm L3 plane plus L1 pour, 18-via array.
- **Fuel_Gauge_Power (U5 MAX17048, Q103/Q104 switch):** BAT_PACK shared with the L3 battery plane; gauge CELL/VDD 0.1 uF at the pins; sense kept away from SW.
- **TPS61088 boost (U25, L200, C275, rot 270):** loop VIN cap - L200 - SW - Cout - PGND < 80 mm2, input/output caps <= 2 mm (VCC C265 8.5 mm and SS C266 9-11 mm are placement misses); SW 4 mm polygon <= 15 mm long, FB/COMP network on the far side, 1 mm from other nets; >= 9 thermal vias in the pad; PVDD_AMP out on L1 pour + L3 plane (>= 6 mm). **Datasheet is missing (only the excerpt): verify pin function/rotation of U25 before routing.**
- **Class-D (U6, U7 TAS5825M):** per IC PVDD pins with 0.1/1 uF directly (<= 1.5 mm, L1, no vias), 22 uF+ bulk <= 6 mm, PVDD island 6 mm on L1 + L3; OUT_x to L201-L206 <= 3 mm, 1.5 mm wide; filter cap < 3 mm from the inductor returning to that amp's PGND pins; BST caps <= 1 mm; thermal pad: ~20 vias 0.3 mm at 1.0-1.2 mm pitch in columns radiating outward, no thermal relief, connected to L2 and an L4 pad plane of >= 900 mm2 under/around, no parts on L4 there; AVDD/GVDD/VR_DIG caps <= 2 mm; digital I2S/I2C come in at the opposite package side; BTL output pairs parallel 0.3 mm apart, 2.0 mm wide to J9-J11 (<= 40 mm), loop L-C-GND < 100 mm2.
- **BM83 (U1, rear-left corner):** antenna keep-out `BM83_ANTENNA_KEEPOUT` empty on all four layers (rule rf_keepout; no ground plane around the antenna end); L2 solid GND under the module body, no L1 traces beneath; ground via fence <= 3 mm around the module (not into the antenna area), supply 10 uF/0.1 uF/1 nF at the supply pads <= 3 mm, 0.8 mm feed from U15; UART/RST/control strapped away on L3/L4 (digital slow) or L1 away from antenna; BT audio (BT_AUDIO_L/R, AOHPL/R) as an AUDIO pair to the codec, RF filtering at the jacks.
- **PCM1862 (U24) and analogue input:** inputs AUX_L/R, BT_AUDIO and mux nets 0.3 wide, L1 only, over unbroken L2, 0.5 mm clearance and a guard ground trace/fence between L and R and from digital; pairs 0.3 apart or signal plus own return; no vias (decap vias to GND only, no via between a cap and its pin); AVDD/VREF/LDO caps <= 1.5 mm on the same layer; one GND plane, all AGND/DGND pins land on L2 at the IC; keep digital return currents (I2S) on their own corridor and never route digital across the input area; jack-side series R + filter C at the jack.
- **I2S:** BCK/LRCK/DATA 0.25 wide, 0.4 apart, length-matched to 5 mm, series 22-33 ohm at the source, no vias, never parallel to analogue (>= 5 mm), with L2 solid.
- **USB audio (U2 PCM2902C):** D+/D- pair 0.25/0.15 from the connector pair through the series R at the IC, matched to 0.5 mm, ESD at the connector; AGND/DGND pins to L2 within 0.1 V at the device; VDDI/VBUS caps <= 2 mm; 12 MHz crystal within 5 mm, load caps <= 2 mm, ground guard around, nothing beneath on L1.
- **Headphone/Aux (U10 TPA6132A2, U8/U9 muxes, J2/J3):** capless outputs as a pair on L1 away from class-D, pad to ground only; flying cap and CPVDD caps <= 2 mm; RF ferrite + 100 pF at the jacks.
- **MCU (U3 STM32G071, J6/J7):** 100 nF at every VDD <= 1.5 mm, 4.7 uF <= 5 mm, VDDA 100 nF + 1 uF; SWD short; I2C pull-ups near the MCU; no digital routing through the analogue corridor.
- **Pours vs tracks:** pours (L1 + L3 + L4): GND, VBUS_PD/USB_VBUS (3.5), SYS_RAW (8), BAT_INT/BAT_PACK/PACK_RAW (12), PVDD_AMP (6), 5V_LOGIC (L3), 3V8_BT, 3V3_AUDIO, 3V_AO islands (L3 + short L1 stubs). Tracks: SPK_OUT 2.0, SWITCH 1.5-4.0 polygons, 5V 1.0, 3V 0.5, AUDIO 0.3, I2S 0.25, USB 0.25, I2C 0.3, signals 0.25-0.3, PWR_LOCAL 0.4.

## 4. Decoupling caps beyond 3 mm and mitigation (dist-v3: 78 of 116 GND caps > 3 mm; 0402 HF mean 3.45, bulk mean 6.85; per-IC worst only: `ai-files/pcb/dist-v3.txt`; full list from `pcb_dist_check.py`)
Mitigation for every cap > 3 mm, in order: (1) route L1, trace >= pad width (0.5 mm) and as short as geometry allows, never through a via; (2) its own GND via at the pad, 0.6/0.3, no shared vias; (3) one 0.1 uF 0402 within 1.5 mm of the pin if the larger cap cannot get closer (add parts as the datasheets prescribe); (4) review inductance by reading loop area (< 25 mm2 per cap loop); (5) if it still fails, nudge parts by hand (placement v3 open item 1).
| IC | Worst caps | Action |
|---|---|---|
| U4 BQ25792 | SYS C104/C105/C107 8.7-9.5, PMID 2.5-4.3, VBUS 4.9-6.1, REGN 5.0, C110 4.2, other max 10.3 (R100) | 0.1 uF 0402 at each pin first, 10 uF 0805 on a 2 mm wide L1 neck to SYS; SYS 0805 caps tied on the L1 SYS pour |
| U6 TAS5825M | PVDD caps 5-10, C293 12.7 (3V3 cap far) | priority nudge; PVDD 0.1/1 uF within 1.5 mm no via; if not possible add a wide PVDD L1 pour under the caps |
| U7 | max 8.2 | as U6 |
| U25 TPS61088 | C265 VCC 8.5, C266 SS 9-11, C275 8.9 | VCC/SS on L1 with GND via at cap, 0.4 mm trace; C275 PVDD pour with 6 vias |
| U24 PCM1862 | AVDD caps 5-10 (max 10.3) | no-via L1 traces 0.3-0.4; accept noise on AVDD if > 5 mm: add 0.1 uF within 2 mm |
| U20 | C263 20.75 (SYS_RAW) | route on the SYS_RAW pour with 2 vias to L3; not a precision part |
| U15 | C150 7.2 | L1 0.8 mm |
| L200 | C264 12.0 | SYS_RAW bulk, on the pour, acceptable |
| U22/U14/U2/U3 | 7.5 / 3.5 / 5.0 / 7.0 | L1 short, own GND via |
Output filter caps (J9-J11 C302-C307 up to 12 mm) and ones on R-chains are not decoupling: treat them as SPK_OUT trunks (2.0 mm).

## 5. Teardrop plan
KiCad 10.0.6 has no Python or kicad-cli teardrop generator (`pcbnew` exposes only the `ZONE` teardrop setters, no `TEARDROP_MANAGER`; `kicad-cli pcb` has drc/export/render/upgrade only). Generation is therefore **in the GUI: Edit > Teardrops (Add Teardrops, scope "All")** after routing and before the final zone refill; there is no scripted path. Project parameters are already in `DesktopSpeaker.kicad_pro` (`teardrop_parameters`, set by `setup_pcb_rules.py`): length ratio 0.5, max length 1.0 mm, height ratio 1.0, max width 2.0 mm, 5 curve points, two-track span allowed, prefer-zone-connection off, targets: round pads, rect pads, track end (track-to-track), vias, SMD and PTH pads on. For 0402 hand-solder pads (0.5 mm wide) use max length 0.6 mm via per-pad override (pad properties, "Override teardrop settings"). Re-run Remove then Add Teardrops after any routing edit (teardrops are stored as zones and are not refreshed automatically).
Post-route verification: count teardrop zones vs track-pad/via joints (pcbnew script in the verify step, tolerance: all targets except QFN 0.4 pitch pads where KiCad skips and TPS25730D/J1 are listed), DRC after refill, view the 3D/zone render of the BM83 castellations and connector pads. Teardrops required on all power and audio vias and every connector pad.

## 6. Pre-route checklist
- [ ] TPS61088 datasheet fetched, U25 pin map/rotation verified (open).
- [ ] JLC stackup 04161H-7628 + impedance calculator confirmed (USB 0.25/0.15, inner 1 oz or 0.5 oz).
- [ ] 1 oz vs 2 oz outer: 1 oz decided here, confirm after the first pour-width check.
- [ ] Placement open items accepted: decoupling > 3 mm (sec. 4), charger passives 14.1 mm, woofer chamber 0.625 L.
- [ ] Footprint issues fixed or accepted: J1/U11/U19 pitch, TPS25730D thermal via drill 0.2 (8 drill flags), SW100, J2/J3 silk.
- [ ] Rule files loaded (`.kicad_pro` netclasses, `.kicad_dru`), stackup in the board, DRC runs, class of every net checked (311).
- [ ] Zones planned: L2 GND, L4 GND, L3 islands outlined (not drawn), BM83 keep-out in place (no copper in any layer).
- [ ] Test points and ferrite filters (jacks) decided; 4 M3 holes GND confirmed.

## 7. Post-route DRC / verification checklist
- [ ] `kicad-cli pcb drc --severity-all` clean: 0 clearance, 0 shorting, 0 unconnected, only the recorded inherited items (silk J2/J3, SW100 hole clearance, U1/J1 silk edge).
- [ ] Width script: every POWER_HI/PVDD/SPK_OUT run > 3 mm >= trunk minimum or in a pour (list exceptions); SWITCH polygons min area; AUDIO/I2S/USB min 0.25.
- [ ] Teardrops: count vs joints (sec. 5), skipped list reviewed.
- [ ] Loops measured (area from the L1 geometry): BQ25792 SYS/PMID/VBUS cap loops < 25 mm2, TPS61088 power loop < 80 mm2, TAS5825M PVDD loop and L-C-GND output loops < 100 mm2, BST caps <= 1 mm.
- [ ] Antenna keep-out empty on four layers; >= 15 mm external metal; module GND via fence <= 3 mm; no L1 trace under the BM83.
- [ ] L2 solid GND: zone fill inspected, no slots under I2S/USB/audio; stitching every <= 5 mm (<= 3 mm near BM83); each GND decoupling cap has its own via.
- [ ] Via counts: VBUS_PD >= 6 per transition (15 at U11 VBUS_IN/PPHV), SYS 12, BAT 18, PVDD 8, thermal pads (U6/U7 ~20, U4 12, U25 9).
- [ ] Return path check: analogue nets vs class-D/boost >= 20 mm; USB pair length skew <= 0.5 mm, 90 ohm calculator check.
- [ ] No via in decap-to-pin traces for PCM1862 / TAS5825M / TPS25730 CC; CC caps then via.
- [ ] 3D check (connectors, rocker, M3 heads), gerber/drill review, BOM/position files regenerated.

## 8. Open questions
1. TPS61088 datasheet missing (U25 layout and pin rotation unverified).
2. JLC impedance calculator confirmation (USB 0.25/0.15 here; rules doc had 0.20/0.15) and the exact inner copper/core thickness.
3. 2 oz outer (recommended no), inner 1 oz yes/no.
4. Decoupling > 3 mm (78 caps): accept with mitigation or hand-nudge parts.
5. Teardrops can only be generated in the pcbnew GUI (no CLI/Python): the user (or a scripted GUI session) must run it; alternatively write teardrop zones by script with a custom generator (not done).
6. DRC floors below trunk minima (pad escapes): confirm that the post-route width script is acceptable.

## 9. Setup done (reversible)
- `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pro`: 15 netclasses (Default + SIGNAL + 13), 89 patterns, minima, width/via/diff presets, teardrop parameters. `DesktopSpeaker.kicad_dru`: 13 rules. `DesktopSpeaker.kicad_pcb`: stackup block only (git diff +17 lines). Re-run/undo: `ai-files/helpers/setup_pcb_rules.py`; `git checkout` of the two project files reverts.
- DRC after setup (`ai-files/pcb/drc-rules-setup.json`): 22 violations (was 35): drill_out_of_range 8 (U11 thermal vias), silk_over_copper 8 (J2/J3), silk_edge_clearance 4, hole_clearance 2 (SW100); the 13 pad-pitch clearance flags on J1/U11/U19 are gone via the min clearance 0.1 and fine_pitch rule. 499 unconnected items (nothing is routed), no width violations because there are no tracks.
