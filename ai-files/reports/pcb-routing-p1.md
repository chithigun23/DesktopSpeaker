# Routing P1 notes (work-p1, copies only; started 2026-10-07)
## Stage 1 diagnosis (running notes)
Tools: helpers/route_p1_dsn.py (DSN transformer, config json), route_p1_post.py (SES import + refill). Freerouting -mp = max PASSES (no time limit option; SIGTERM loses the SES, so use -mp 5-6, ~2.5 min/pass).
Test set: SIGNAL,I2C,PWR_LOCAL,PWR_3V,PWR_5V,BOOT nets (149 nets, GND excluded), In1 power.
Pass-1 unrouted items (Freerouting score):
- V0 baseline (all planes, protected P0 wiring): 109
- V1 B.Cu plane dropped: 113; V2 + F.Cu pours/keepouts dropped: 109; V3 + In2 planes dropped: 99 (then oscillates 144,131)
- V4 V3 + P0 GND wiring (stubs/vias) removed: 74 (baseline 156 items, only 13 violations vs 263)
- V5 V3 + clearance 0.15: 82
Conclusion so far: planes are NOT the cause; protected P0 GND stubs/vias (203 vias, 0.4 stubs) and the 0.2 clearance are. Idea: route signals first on bare pads, then re-add GND vias.
Note: pkill -f kills the own shell; kill by PID.
### Findings 2026-10-07 (after the interruption)
- ROOT CAUSE 1 (main): Freerouting class width 0.25-0.5 cannot exit fine-pitch pads (0.4 pitch QFN, pad 0.2 wide): isolated test of 3 trivial nets: width 0.25 -> 0/3 routed, width 0.2 -> 2/3. Fix: route everything at 0.2 (project minimum), widen afterwards where room allows.
- ROOT CAUSE 2: protected P0 GND stubs/vias (203 vias) block escapes: removing all P0 tracks/vias before routing: unrouted 99 -> 74 (pass 1). Plan: strip P0 vias (nowire.kicad_pcb), route, re-add GND/rail vias later around the finished copper.
- ROOT CAUSE 3 (project bug): KiCad netclass patterns do not support [..] ranges: 30 nets (all Net-(C20[0-5]-Pad2), C23x, U10-IN[LR]-, U24-VIN.., U2-VOUT, U1-AOHP, and the 6 SPK_OUT filter nets C30[2-7]) are in class SIGNAL in KiCad, so DRC rules audio_clear/pvdd_clear/width_audio do NOT apply to them. Fixed in work-p1/DesktopSpeaker.kicad_pro by explicit patterns (89 -> 112 patterns). Must be applied to the real .kicad_pro on adoption.
- Not causes: B.Cu GND plane (113 vs 109), F.Cu pours/keepouts (109 vs 109), In2 planes (99 vs 109, small), clearance 0.2 vs 0.15 (82 vs 99 with wiring, 72 vs 74 without).
- Freerouting passes oscillate (74 -> 126 -> ...) and the SES holds the LAST pass: use -mp 1-2. SES import into a board with tracks DROPS tracks of nets not in the SES: use helpers/route_p1_post.py merge (import into stripped board, copy tracks of chunk nets).
- Chunked routing (15 nets per run, shortest span first, failed nets pruned, 2 rounds) works better than one big run: helpers/route_p1_chunks.py. C1 (planes B.Cu+F.Cu+keepouts dropped, In2 planes dropped): 53 -> 27 open nets.
- Helper summary: route_p1_dsn.py (DSN config), route_p1_post.py (import/merge/stats), route_p1_chunks.py, route_p1_loop.py (obsolete), route_p1_fr.sh, route_p1_unc.py, route_p1_view.sh/png.mjs (crops).
- pkill -f kills the own shell; use pgrep -x java.
- IMPORTANT MEASUREMENT BUG FOUND: kicad-cli drc json caps unconnected_items at 499 (always 499, GND 253 of them), so all earlier "open" numbers were lower bounds. Real oracle: helpers/route_p1_open.py (own union-find incl. zones). Real open at start (nowire, non-GND): 208 nets / 504 edges (AUDIO 85, SIGNAL 143, I2S 22, USB 9, PWR_3V 69, I2C 24, PWR_LOCAL 23, SWITCH 30, POWER_HI 34, PVDD 17, BOOT 11, PWR_5V 25, SPK_OUT 12).
- Order test: critical nets (AUDIO/I2S/USB, F.Cu only, width 0.25) FIRST works (K3: 61 nets/116 edges -> 16 nets/25 edges open, ~5 min) while routing them last (K2) or with 0.5/0.4 clearance halos (B1, K2) routes almost nothing. So: critical first at 0.21 clearance, check audio_clear afterwards with DRC.
- Post pipeline built: route_p1_vias.py (GND/rail vias around finished copper), G1 = Freerouting for GND only (fanout to In1 plane, ~8 min), route_p1_widen.py (segment-wise widening to class pref where clearances hold), route_p1_fix.py + route_p1_cycle.sh (DRC-driven removal: shorts, dangling, holes, clearance/audio_clear/clk_clear -> whole net removed and rerouted; GND item-level).
- State after B3 + vias + G1 + widen + fix cycles (W5): DRC clearance 0, shorts 0, via_dangling 0, track_dangling 1, width floors 39 (neck-downs at pins). Open (edges, non-SWITCH/HI/PVDD/SPK): see final table.
