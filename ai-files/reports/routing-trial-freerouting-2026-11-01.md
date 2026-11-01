# Routing trial: Freerouting 2.5.0 with 45-degree snap (2026-11-01)

Purpose: decide whether Freerouting can be the engine for exact 0/45/90 signal routing in the routing restart. Scratch work only, in `ai-files/pcb/work-trial/` (nothing in `DesktopSpeaker-kicad/` touched, nothing committed). Headless throughout (KiCad 10.0.7 AppImage `kicad-cli` and `python3.11`, Java 25 JRE, Freerouting 2.5.0 jar).

Verdict first: **angle exactness is solved, completion is not.** Every Freerouting segment is exactly 0/45/90 (114 segments, 291.6 mm, max deviation 3e-14 mm), but the board is not completed: 1 of 11 nets fully connected after both stages, 0 vias used, I2S spacing 0.20 mm, and the optimizer never improved anything. Not viable as the unattended signal router for this board; viable only as a 45-degree path generator for easy nets, with hand or scripted escapes.

## 1. Setup (reproducible)

Files in `ai-files/pcb/work-trial/`: `strip.py` (text-level strip), `refill.py`, `dsnexp.py`, `trial_dsn.py` (DSN builder), `fr.sh` (Freerouting runner), `ses_import.py` + `run_import.sh` (SES merge), `widen.py`, `trial_metrics.py` (measurements), `mk.sh` (DRC), `drcsum.py`, `unconn.py`. Boards: `base.kicad_pcb` (copy of project board), `trial-stripped.kicad_pcb`, `A1*.kicad_pcb` (stage 1), `A2*.kicad_pcb` (stage 2), `*.drc.json`, `*.metrics.json`.

Step 1, strip. Removed from the copy: all tracks, arcs, vias and the teardrop zones of /I2S_BCK, /I2S_LRCK, /I2S_SDATA, /USB_DP, /USB_DN, /AUD_SDA, /AUD_SCL, /BT_UART_TX, /BT_UART_RX, /CTRL_SDA, /CTRL_SCL (273 segments, 1 arc, 65 vias and 193 teardrop zones), then refilled zones. `pcbnew` `board.Remove()` followed by `ZONE_FILLER.Fill()` segfaults silently on this board (rc 0, no output), so the strip is done as a text edit of the .kicad_pcb. The refill must run with the `.kicad_pro` and `.kicad_dru` beside the board: without them the custom zone clearance rules are not applied and 22 false clearance errors appear. Checks: untouched project board refilled gives DRC 0 violations / 0 unconnected; stripped board gives 0 violations / 38 unconnected (the 11 nets' airwires).

Step 2, DSN (`trial_dsn.py`, from the KiCad export `raw.dsn`, details below). Step 3, CLI:

```
FREEROUTING__USAGE_AND_DIAGNOSTIC_DATA__DISABLE_ANALYTICS=true FREEROUTING__GUI__ENABLED=false \
~/Applications/freerouting/jre25/jdk-25.0.4.1+1-jre/bin/java -Djava.awt.headless=true \
 -jar ~/Applications/freerouting/freerouting-2.5.0.jar -de S.dsn -do S.ses -mp N -mt 8 \
 -dr S.rules --router.fanout.enabled=false --router.neck_width_um=200
```
Not-routed nets are simply absent from the DSN network (the `-inc`/ignore-class option was not needed). SES import: `ImportSpecctraSES` drops all copper not in the SES, so the SES is imported into a scratch copy and only the trial nets' tracks/vias are copied into the stripped board (same merge pattern as `route_p1_post.py merge`), then zones are refilled.

### Exact DSN edits
1. `(structure ...)`: inserted `(snap_angle fortyfive_degree)` before the final `(rule`; default rule width 200 clearance 200.
2. All 1691 zone-outline `(plane ...)` entries removed. In1 planes and GND planes dropped (signals may cross the GND pours; KiCad refills around them). All other planes turned into netless `(keepout "" (polygon L 0 ...))` on their own layer, buffered by a per-class halo (audio 0.5, POWER_HI 0.4, PVDD/SPK_OUT 0.3, SWITCH 1.0 mm clearance; stage 1 additionally 0.4 mm to all non-GND foreign copper because of rule `clk_clear`).
3. The 65 neutral rule-area keepouts that KiCad exports (NECK_*) deleted; BM83 antenna keepout (4 layers) and the six BKO_* B.Cu keepouts kept.
4. Existing wires and vias of all other nets (2157 wires, 823 vias) converted to netless keepouts (path with width + 2 x halo; vias as circles on all four layers). Foreign pads stay as pads.
5. Edge frame: 0.3 mm keepout strips on all four layers (copper-edge 0.5 mm with 0.2 clearance).
6. In1/In2: Freerouting treats a power layer without a plane as a signal layer (warning in the log), so layer type stays `signal`; inner layers were made unattractive through the rules file (trace cost 500) or, in the first runs, whole-layer `wire_keepout` polygons.
7. Network: only the stage nets; classes I2S_CLK and USB width 250, others 200, clearance 200 um, via `Via[0-3]_600:300_um`.
8. `S.rules` (`-dr`): `(snap_angle fortyfive_degree)`, `(via_costs 150)`, `(start_ripup_costs 100)`, `(fanout off)`, layer rules F.Cu horizontal (against-direction cost 3.0), B.Cu vertical (3.0), In1/In2 trace cost 500 or inactive.

## 2. Findings about Freerouting itself

- **Snap angle works and is the default.** Same board, SES geometry measured: `snap_angle none` 5.3 % of length on 0/45/90; `ninety_degree` 100 % on 0/90; `fortyfive_degree` 100 % on 0/45/90; keyword absent (plain KiCad export) also 100 % on 0/45/90. So the old P1 off-grid copper did not come from Freerouting's routing core; it came from later steps (widening, stubs, smoothing).
- **Fanout stage runs by default** (added 4 vias on SMD pins in the first run). Disable with `--router.fanout.enabled=false`.
- **Necks.** With automatic neckdown Freerouting writes 0.1874, 0.15, 0.125 mm segments at pins; DRC floors are 0.2 (0.25 for I2S/USB outside neck areas). `--router.automatic_neckdown=false` keeps widths but completion drops (10 vs 6 unrouted items in stage 1). `--router.neck_width_um=200` makes the retry use 0.2 but 0.1874 and 0.15 segments still appear. A widening pass afterwards (`widen.py`) fixed all width violations in stage 1 with no new clearance error (halos made room); stage 2 still has 6 x 0.15 mm segments (unwidened in A2, widened in A2w).
- **Via cost.** `via_costs 150` (task value) gave 0 vias in every run; routes stay on F.Cu. With via cost 5 two vias and 3 B.Cu paths appear (stage 1); via cost 20 gave 0 vias, 50 gave 2. Unrouted count stayed 6-7 in all variants. Also: a layer set `active off` in the rules file removes vias entirely (a via spans the inactive layers), so inner layers must be discouraged with trace costs, not deactivated.
- **Pass oscillation is real.** Stage 2, 18 passes: unrouted items 15, 20, 19, 19, 19, 19, 18, 15 (pass 8 is a restore of the best), 20, ... The SES contains the last pass, not the best (last = 19, best = 15). Use `-mp 1`, or keep a copy per pass count. Stage 1 best was pass 1 in all runs.
- **Optimizer only runs on fully routed boards** ("Skipping optimization stage ... unrouted connections"). Forced with `--router.optimizer.enable_preflight_guards=false` it ran and reported "OPTIMIZER_SCORE_NOT_IMPROVED, UNCHANGED 0.0000 %" on both the stage-1 board and a 2-net subset. The 10 "pre-existing clearance violations" Freerouting reports (pad-to-pad inside U25 and Q103 footprints) are in every run and may be part of why candidates are rejected [unverified]. `improvement_threshold` is a fraction (0.5 = 50 %), not 0.5 %.
- **Clearance export.** KiCad exports no custom-rule clearances (audio 0.5, clk 0.4, switch 1.0); only the class clearance 0.2 is seen. Emulated with foreign-copper halos. Pad-to-track rules cannot be emulated. Foreign-pad halos were not added (SWITCH pad rule `switch_sensitive` includes pads; not checked here, no violation appeared).
- **Fine-pitch escapes fail, with and without any foreign copper.** In stage 1 the same four connections (U6-14, U7-12, U7-13/R207-2, and DN at J1-B7/R172) stay open on a DSN containing only pads and the edge frame (variants s1g, s1h: "4 unrouted"), i.e. they are not caused by my halos or keepouts. Dropping those pins from the network just moved the failure to other pins (3 unrouted after 30 passes). Same conclusion as P1: escapes need pre-placed stubs or hand work.
- Runtime: 3-15 s per pass, 15 s for `-mp 1`; 70-90 s for 18 passes.

## 3. Numbers (final trial board `A2w.kicad_pcb`: stage 1 I2S+USB, stage 2 I2C+UART on top)

Stage 1 (5 nets, strict 0.4 mm halos, `-mp 1`, `A1w`): 244 mm, 100 % exact. Stage 2 (6 nets on `A1w`, `-mp 1`, `A2w`): 47 mm, 100 % exact; the 30-pass run was worse (last pass 19 unrouted vs best 15).

Exact definition: |dx|,|dy| equal within 0.005 mm or one under 0.005 mm, plus all 114 segments checked for a max deviation of 3e-14 mm. Joints sharper than 90 degrees: 0 (baseline 3 across the 11 nets). Arcs: 0 (baseline 1).

| net | before: len / exact % / vias | trial: len mm / exact % / vias | note |
|---|---|---|---|
| I2S_BCK | 125.0 / 55.8 / 2 | 9.2 / 100 / 0 | mostly open (octilinear minimum 113.4 mm) |
| I2S_LRCK | 127.6 / 50.5 / 4 | 112.5 / 100 / 0 | 2 airwires open, ratio 0.99 not meaningful |
| I2S_SDATA | 125.6 / 62.1 / 3 | 64.2 / 100 / 0 | open |
| USB_DP | 51.6 / 99.5 / 0 | 44.8 / 100 / 0 | **complete**, length / minimum 1.21 (before 1.39) |
| USB_DN | 51.4 / 92.4 / 2 | 13.7 / 100 / 0 | open at J1-B7 and R172 |
| AUD_SDA / AUD_SCL | 219.5 / 154.3, 43 / 9 % | 6.9 / 13.3, 100 | mostly open |
| BT_UART_TX / RX | 134.9 / 140.7 | 17.3 / 3.9, 100 | open |
| CTRL_SDA / SCL | 162.7 / 140.5 | 3.8 / 2.1, 100 | almost nothing routed |
| total | 1433.8 mm, 38.7 % exact (47.7 % within 0.6 deg), 65 vias | 291.6 mm, 100 %, 0 vias | |

Before-values from the project board (`base.metrics.json`); the trial has no complete net except USB_DP, so length ratios for the other nets are not comparable (ratio below 1 means open). Unconnected after both stages: 21 items (38 airwires before the trial), of which 15 belong to stage-2 nets and 6 to stage-1 nets. About 17 of 38 airwires closed.

Reference (B.Cu over In2 islands/voids): 0 mm, because nothing is on B.Cu (before: I2S_SDATA 14.5 mm void, AUD_SDA 62.9 mm over islands, etc.). F.Cu over In1: all routed length over GND. Parallel runs: I2S_LRCK|I2S_SDATA 17.3 mm at 0.202 mm edge gap (standard is 0.6 mm; Freerouting has no per-pair spacing; also 15.3 mm at 0.40 to AMP_FAULT_N). USB pair gap not tested (pair incomplete).

DRC with project rules (`kicad-cli`, zones refilled): `A2w` 4 violations, all USB-pair rules of the open /USB_DN (skew, 2 x pair gap, uncoupled length); 0 clearance, 0 track width, 0 shorts; 21 unconnected. `A2` before widening: 6 track_width (0.15 mm). Stage 1 before widening (`A1`): 32 track_width violations; after widening to 0.25 (`A1w`): 0 track_width, 0 clearance. These are not signs of quality: the board has 21 open airwires.

## 4. Step 5 (finisher)

Not run: on-grid share is 100 %, above the 98 % threshold. What a finisher would still be needed for is not off-grid segments but the open connections, the 0.2 mm spacing and the widths.

## 5. Recommendation

Freerouting staged pipeline for **exact 45-degree**: the angle problem is solved by the engine itself; no finisher required. Staged pipeline for **complete routing**: not viable on this board as tested. Evidence: 38 airwires, 17 closed, 1 of 11 nets complete; fine-pitch pin escapes fail on a near-empty DSN; vias suppressed at cost 150 and not helpful at lower cost; pass oscillation with last-pass SES; optimizer inactive; no spacing rules for I2S.

If Freerouting is kept: use it only for open-field nets, stage by stage with `-mp 1`, fanout off, neck 200, widen afterwards, pre-place the pin escapes (stubs and fan-out vias) by script, give I2S its own corridor by keepouts, check each stage with `trial_metrics.py` and DRC, and plan hand routing for the fine-pitch ICs. The alternative worth trying on one stage is KiCadRoutingTools (octilinear by construction, `--keep-input-copper`), as already suggested in the tools report; not tried here.

## 6. Unverified / limits

- One board state, one stage order; no tuning of halo size, via cost beyond three values, or of class order.
- The strict 0.4 halos around all foreign copper in stage 1 may over-constrain it; the 4-connection failure persisted without any foreign copper, but the stage-2 failures (15 open) were only tested with the foreign-copper keepouts, not without.
- I did not verify visually in KiCad; checks are numeric (SES parse, board parse, kicad-cli DRC).
- Whether the forced optimizer would work on a complete route is untested because no complete routing was reachable.
- Teardrops of the trial nets were removed with the strip and not recreated.
