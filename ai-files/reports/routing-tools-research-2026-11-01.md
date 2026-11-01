# Layout and routing tools vs the owner's standard, plus our routing history (2026-11-01)

Standard: 0/45/90 deg only; every run as short as possible; route by importance (power hot loops/paths, then clocks/USB/high speed, then analog/audio, then control). 4 layers (F.Cu / In1 GND / In2 power islands + GND / B.Cu), JLCPCB rules, 360 footprints, ~200 nets, headless Linux.

Evidence labels: [local] read from the repo or the installed jar; [web] fetched this session (vendor pages are marketing); [mem] my background knowledge, not re-verified; [UNVERIFIED] could not be confirmed. I did not run any router in this task. Nothing in the project was edited.

---------------------------------------------------------------------------
## Part 1. How the current copper ended up off-grid [local]

Measured now, from `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` (plain text parse, 2500 straight segments, 26 arcs): 953 segments (3125 mm) are within 0.6 deg of 0/45/90; 320 (1131 mm) are 0.6-3 deg off; **1227 (3855 mm) are more than 3 deg off**. So roughly 55 % of copper length is off-grid. The R-review already flagged "790 segments (2.9 m) are any-angle" in `pcb-routing-review.md` m1 and nobody fixed it.

Chain of producers:
1. **P0/P1 (R3), Freerouting 2.5.0** (jar `~/Applications/freerouting/freerouting-2.5.0.jar`, build 2026-10-05, Java 25 JRE in `jre25/`; `route_p1_fr.sh` runs `-de/-do -mp N`, headless). KiCad's DSN has no `snap_angle` and no layer-direction/cost block [local: grep of `work-p1/A1-0.dsn`]; the scripts set only widths (0.2/0.25), clearance 0.21, layer types. Angle mode was left to Freerouting's default and was never checked. Freerouting also shrank necks to 0.1874 mm, which scripts then widened (`route_p1_widen.py`).
2. **P2 onward (R4, R5), own raster router**: `route_p2_astar.c` ("multi-layer 8-direction A* on a raster", 0.05 mm grid) + `route_p2_core.py`. The raster path is octilinear only in cell space. Then `simplify_run()` does "greedy straight shortcuts ... keeping exact legality", fine-pitch pads get "exact stubs along the pad axis", and path ends are snapped to pad centres. Shortcuts and off-grid pad centres produce arbitrary angles by design. 68 nets were ripped and rerouted this way.
3. **R6a-R6q**: more rounds with the same core (`route_r6a_astar.py`, `route_r6c/h/i_route.py`), hand JSON edit lists, and `route_r6i/r6j_smooth.py`. The smoother adds more "shortcut a-d" any-angle segments and chamfers, accepted only on clearance and a corner-count metric.

Why 45 deg was never enforced: the 45/90 rule is first written down on 2026-11-01 (`pcb-layout-best-practices.md` sec. 3). Earlier criteria were open edges, DRC, clearance, necks and corner radius (`route_r6i_bends.py` checks short segments between bends, not angle classes). No tool in the loop ever tested angle or length against an octilinear minimum, and every optimisation step (shortcuts, smoothing, stubs) preferred "legal and shorter" over "on-grid". Net effect: a clean DRC board with a free-angle look.

---------------------------------------------------------------------------
## Part 2. Tools

### 2.1 Freerouting (installed: v2.5.0, 2026-10-05) [local+web]
- **45 deg**: Has an `AngleRestriction` enum {NONE, FORTYFIVE_DEGREE, NINETY_DEGREE}, a dedicated 45-degree search tree (octagon obstacles), `FoundConnectionLocator45Degree` and `TraceTightener45` in the jar [local]. Set in the Specctra DSN as `(structure ... (snap_angle fortyfive_degree))`; the parser knows `snap_angle`, `fortyfive_degree`, `ninety_degree` [local, Keyword.class]. There is no CLI flag for it. **KiCad's DSN export does not write it** [local], so we must insert it. The default when absent is [UNVERIFIED]. Whether every segment ends up an exact 45-degree multiple (pad centres off-grid, fine-pitch pins) is [UNVERIFIED]; open upstream issues about oblique board edges falsely blocking the 45 search (#1014, #1015) exist [web]. Treat the output as "mostly 45" and measure it.
- **Net ordering/priority**: no per-net priority. Controls: `-inc NETCLASS,...` skips named classes [web]; `-is sequential|prioritized` and `-us greedy|global|hybrid` govern the optimizer's item selection, not net order [local+web]. Practical method = staged runs: DSN containing only the stage's nets, earlier stages as fixed wires/obstacles (we did this in P0/P1 with `protect` wires).
- **Length minimisation**: the route-optimizer (post-route) is on by default, `-mt` threads, `--router.optimizer.improvement_threshold` default 2.5 (0.5-1.0 slower/better) [web]; `bend_cost`, `via_costs`, `start_ripup_costs`, `plane_via_costs` exist as settings [local] and in the DSN `(autoroute_settings ...)`/`.rules` file read by `-dr` [web+local]. Our own P1 finding: SES holds the last pass and passes oscillate, use `-mp 1` per chunk [local].
- **Keepouts, classes, layers**: keepouts yes (DSN `keepout`, we added the antenna one). Net-class width yes; **clearances from KiCad custom rules are not exported** [local, p0 report]. Layers: `--router.layers.routable=true,false,false,true` and `--router.layers.preferred_direction_horizontal=...` (arrays top to bottom) [web]; or DSN `layer_rule`; a layer typed `power` in the DSN is not routed (we used this for In1) [local]. Per-net layer restrictions only through classes/ordering tricks (we forced AUDIO/I2S/USB to F.Cu with DSN class rules [local P1]).
- **Planes/ground-via**: plane layers are treated as nets; via-to-plane connection with `plane_via_costs`; no concept of island splits on In2 (multiple nets on one layer).
- **Existing copper**: it can load a DSN with `wiring` and route the remainder; `protect/fix` wires are not ripped (`fix`, `shove_fixed` keywords in jar). Known traps from P1: foreign wires of nets absent from the network made it hang on SES write; SES import into a board drops tracks of nets not in the SES (merge script needed) [local].
- **KiCad 10 round trip**: pcbnew `ExportSpecctraDSN` / `ImportSpecctraSES` via Python (worked for us on 10.0.6-rc2). Freerouting 2.3+ also has an "experimental JSON/API mode"; DSN remains recommended [web].
- **Headless**: yes (`-Djava.awt.headless=true`, Java 25 needed for 2.4+; local `--help` works). REST/MCP API server exists (v2.5.0 `POST /v1/autoroute`) [web]. GPL-3.0 [mem], free.
- **Maturity/quality**: widely used; user reports say hand-tidying is normal, clearance mismatches with KiCad, boards left incomplete [web, thin]. Our own result on this board: 61 % of managed-class edges routed, GND/fine-pitch escapes stuck [local].

### 2.2 KiCad 10.0.7 interactive router (pcbnew, installed AppImage 10.0.7) [local+mem]
- Push-and-shove PNS router: 45/90/free modes, differential pairs, length tuning (KiCad 10 revamped tuning, time-domain) [web]. Best tool for the hand finishing of hot loops, USB pair, audio.
- **Scripting**: pcbnew SWIG Python can read/create/edit tracks, vias, zones and run DRC/refill, but cannot drive the PNS router [mem]. `kicad-cli pcb` has only `drc, export, import, render, upgrade` [local] so no cleanup/merge/optimise command; "Cleanup Tracks and Vias" is GUI-only [mem].
- **IPC API ("kipy")**: KiCad-side API; a `KiCad(headless=True)` option starts `kicad-cli api-server`, and `Board` has get_tracks/get_vias/refill_zones/interactive_move/get_connected_items [web]. **The installed 10.0.7 `kicad-cli` has no `api-server` subcommand** [local]; docs mark several newer calls "KiCad 11" [web]. `run_action` is documented as unstable, and arming the interactive router by action still needs a live editor [web, secondary]. Conclusion: **no usable headless routing through kipy on 10.0.7**; do not plan on it. Track creation through kipy [UNVERIFIED].
- Licence GPL-3, free.

### 2.3 KiCadRoutingTools (drandyhaas; MIT) [web]
- Grid A* with **octilinear (H/V/45) multi-layer routing**, Rust core with prebuilt Linux binary, 728 stars / 6.5k commits, v0.17.3 (July 2026), "compatible with KiCad 9 and 10", stress-tested on 45 open-source boards (scorecards not read) [web].
- Controls: `--ordering mps|inside_out|original|bus`; `--nets` to stage; `--layers`, `--layer-costs` (negative forbids a layer); `--direction-preference-cost` (default 250); `--turn-cost` 1000; `--via-cost` 75; `--grid-step` 0.1 mm; `--track-width/--clearance` from net class, `--net-clearances` JSON, `--power-nets` with widths and neckdown; `--max-ripup`; `--smoothing` (octilinear shortcuts); `--keep-input-copper`, `--rip-existing-nets`, `--force-reroute`; connected nets are skipped by default; plane/GND return-via support; writes DRC rules back into the project; `--strict-sizes` [web, CLI table].
- Limits [web]: no push-and-shove, no blind/buried vias, area-scoped rules only as keep-outs, **0.1 mm default grid (our 0.4-0.5 mm pitch pins need 0.05 or exact stubs)**; per-net layer lists not documented; reading/writing of the board uses its own Python (run in a venv, not the KiCad python) [UNVERIFIED how it parses].
- Not yet tried by anyone here. Best open-source candidate on paper for "octilinear by construction + staged `--nets` + keep copper".

### 2.4 kicad-tools (rjwalters; MIT) [web]
Python A* autorouter with net-class awareness, `kct route --nets/--skip-nets`, optional C++ backend, huge catalog tooling. Page does not mention 45-degree or pour awareness. The author's own comparison says KiCadRoutingTools was faster and completed more nets on sparse/medium boards and kicad-tools shorted on dense boards [web, unread primary]. **Not recommended** for this board.

### 2.5 TopoR (Eremex) [web, thin]
Topological, **no preferred directions, free angles by design**, so it violates the 45-degree standard. DSN/SES round trip with KiCad works per a user walkthrough [web]. Windows product, licence price and Linux availability [UNVERIFIED]. Rejected.

### 2.6 Quilter [web, secondary]
Cloud, "physics-driven" placement + routing, takes KiCad/Altium projects, claims parallel candidates checked for impedance/length/crosstalk. Unverified limits: ~500 components / 10 layers (one aggregator); pricing unclear; no public evidence it enforces 45-degree-only or importance order. Cloud + uploads the design. Not controllable enough; also we would give up the existing hand-tuned power copper.

### 2.7 DeepPCB (InstaDeep) [web, vendor page]
RL autorouter; KiCad plugin (open-source, "May 2026") and web upload (`.kicad_pcb` + `.kicad_pro`); routes only, does not move parts; pay-per-board; public plugin up to 1200 airwires, sweet spot 4 layers / ~800 pins; angle rule, priorities, locking existing copper not stated; vendor-reported 96.9 % median completion. Not headless-scriptable per the page. Possible second opinion, not a pipeline basis.

### 2.8 Flux.ai auto-layout [web]
Cloud ECAD; RL-based auto-layout (preview Dec 2024), "ideal for simple to medium boards"; KiCad import of schematics, no KiCad board export found. Reject.

### 2.9 Altium Situs / Cadence Allegro [web+mem, reference only]
Altium: routing rules for corner style (45/90/round), layer direction, per-net **Routing Priority 0-100** (confirmed by Altium docs result), topology, via style. Allegro PCB Router (Specctra lineage): route/clean/spread/miter passes. They are the model for what the owner wants (priority + corner rules); neither runs on headless Linux with a KiCad round trip; commercial.

### 2.10 Placement and layout checking
- Placers (open source, early stage, none established): pyplacer (simulated annealing, KiCad 9 files), atoplace (force-directed, IPC API), Circuit Weaver, kle-placement-router [web]. Not trusted for this board: placement is already hand-set around hot loops/antenna and moving parts is what would invalidate the existing copper.
- Checking we already have: `kicad-cli pcb drc` (custom rules), `route_p2_open2.py` open-edge oracle, `r7_metrics.py` (angle classes, return-path, parallelism), `route_r6i_bends.py`. Missing: net length vs octilinear minimum.

---------------------------------------------------------------------------
## Part 3. Recommended pipeline (one)

**Engine: Freerouting 2.5.0 in staged, locked runs, plus a deterministic octilinearising finisher in pcbnew Python.** Reasons: already installed and proven to round-trip on this exact board; has native 45-degree search + tightener; the staging/locking pattern is already scripted (`route_p0_dsn_filter.py`, `route_p1_dsn.py`, `route_p1_post.py merge`). KiCadRoutingTools is the fallback/experiment (try it on one stage in a scratch copy; if its output is on-grid with the native 0.05 mm grid, prefer it for stage 3).

### 3.0 Baseline and rip-up scope
Work on a copy under `ai-files/pcb/work-r8/`. Rip **all signal copper** (everything not power class, not GND, not zones) from the current board: keep zones, pours, In2 islands, hot-loop copper, GND/power vias and fan-out of power parts. Rationale: 55 % of copper is off-grid, so patching is worse than redoing; the signal nets are only about 140 of ~200.

### 3.1 DSN preparation (script, based on `route_p1_dsn.py`)
- Insert `(snap_angle fortyfive_degree)` in `(structure ...)`.
- Layers: F.Cu and B.Cu `signal`; In1 `power`; **In2 `power`** (no signal on In2; its island vias are pre-existing locked copper). Direction: F.Cu horizontal, B.Cu vertical (`layer_rule` / `--router.layers.preferred_direction_horizontal=true,false,false,true`), against-direction cost 2.5-3.
- Via cost raised (start 150, ripup cost 100) in the DSN `(autoroute_settings (via_costs 150) ...)` or `-dr rules` to keep runs short and few vias [exact CLI key for via cost UNVERIFIED, the DSN/`.rules` route is documented].
- Class rules: width 0.2 (0.25 AUDIO/I2S/USB), clearance 0.21; clearances above that are enforced by previously routed stages' halo as in P1 (plan clearances 0.5/0.4 collapse routing).
- Pre-placed pad stubs and vias of the stage's nets removed (P1 lesson); antenna keep-out and edge frame included; foreign copper as netless keepouts with halos (P1 lesson).
- AUDIO/I2S/USB on F.Cu only; slow control nets F.Cu first, B.Cu only over In2 GND; no In2 ever.

### 3.2 Stages (each ends with a lock)
Run: `~/Applications/freerouting/jre25/jdk-25.0.4.1+1-jre/bin/java -Djava.awt.headless=true -jar freerouting-2.5.0.jar -de S.dsn -do S.ses -mp 1 -mt 8 --router.optimizer.improvement_threshold=0.5` (repeat the `-mp 1` run up to 3 times and keep the best by open-edge count and length; P1 showed passes oscillate).
- **S0 Power hot loops and power paths: not Freerouting.** Existing locked hand copper stays. Only run scripted/hand fixes. (Stage 0 is the already built R6 power copper.)
- **S1 USB, clocks, I2S, crystals**: only these nets, F.Cu, then merge SES (`route_p1_post.py merge`), run octilinear finisher (3.3), run DRC, lock (set tracks locked, plus emit as `protect` wires in the next DSN).
- **S2 audio/analog** (AUX, BT audio, USB audio, HP, ADC inputs, VREF/VMID): same.
- **S3 control/digital** (I2C, strap/enables, UART, SWD, buttons): same, in chunks of 10-15 nets, shortest span first (P1 method).
- **S4 GND/power stubs**: via+stub fan-out to In1 last, scripted (`route_p3_gnd.py` style), not by the router.
Between stages: pcbnew DRC, `route_p2_open2.py`, angle report. A stage is accepted only if criteria below hold; else rip that stage only and re-run.

### 3.3 Octilinear finisher (pcbnew Python, run with `~/Applications/kicad.AppImage python3.11 finisher.py`, never `python3`)
For every unlocked signal segment off-grid by > 0.6 deg: replace with a two-segment 45+orthogonal dogleg between its end points (both bend orders tried; keep the shorter/legal one), check clearance with the same legality test as `route_r6h_chk`, apply only if legal, otherwise list the item for hand work. Also: merge collinear neighbours, remove sub-0.08 mm segments, enforce min 3x width between 45 bends. Do **not** run the old smoothers (`route_r6i/j_smooth.py`, `simplify_run`) because they create any-angle shortcuts.

### 3.4 Acceptance criteria (measured by a new `r8_metrics.py`, extend `r7_metrics.py`)
1. Angle: 100 % of signal+power segment length within 0.6 deg of 0/45/90; zero arcs on signals; zero joints sharper than 90 deg (135 deg interior = fine). Baseline now: 45 % on-grid by length.
2. Length: per net, routed length / octilinear minimum (`max(dx,dy)+0.414*min(dx,dy)` per MST edge) median <= 1.15, p95 <= 1.4, every net above 1.5 listed with a reason. USB DP/DN skew <= 0.5 mm; I2S per `pcb-layout-best-practices.md`.
3. Return path: F.Cu signal length over In1 GND void = 0 (baseline 161.9 mm); B.Cu length over In2 void or foreign island = 0 for AUDIO/I2S/USB/clocks (baseline: I2S_SDATA 14.2 mm void, AUD_SDA 62 mm island, etc.); slow nets on B.Cu over islands <= current and each with a GND via within 5-8 mm.
4. Layers: zero signal copper on In2 and In1; sensitive nets F.Cu only unless listed.
5. DRC: clearance/short/dangling/isolated/track width = 0; open edges = 0 except hand list; via count not above 955 (current total), signal vias per net <= 4.
6. Order evidence: a log per stage proving the stage's nets were routed before the next class and locked (item count by class and time).

### 3.5 What cannot be automated; needs hand routing (KiCad interactive router in GUI, or scripted JSON edit lists)
- Power hot loops and SW-node copper (U4 charger, U25 boost, U6/U7 amp outputs, bootstrap caps, PGND via arrays), In2 island shape/neck decisions, pour fills, EP via arrays.
- USB 90 ohm pair (coupling, equal length, via-gap), I2S skew, crystals; audio guard/ground fencing.
- Escapes of 0.4-0.5 mm pitch ICs (U3, U6/U7, U4, U10, U11, J1/J7) that P3 showed are boxed in by 0402s and 0.6 mm vias; fixing needs part nudges.
- Teardrops (GUI-only in my knowledge of KiCad, still the plan's rule), final visual review, the BM83 antenna keep-out sanity.
- Any net that stays above the length-ratio bound for geometric reasons.
- None of the cloud tools (Quilter, DeepPCB, Flux) can be verified to obey the 45 + importance + lock rules; no headless KiCad 10 API route exists on 10.0.7.

### 3.6 Main risks
(1) Freerouting's 45-degree guarantee is unverified; mitigated by the finisher and by testing S1 first on a scratch copy (decide in one hour: if S1 output is >98 % on-grid, continue; else try KiCadRoutingTools for S1-S3 with `--layers F.Cu B.Cu --ordering mps --nets <stage> --grid-step 0.05 --keep-input-copper`, flags per its docs, untested). (2) Fine-pitch escapes fail again; budget hand work. (3) Complete rip of signal copper may regress open edges (now 2) for a while; keep the old board as the fallback and diff nets by physical connectivity before accepting.

---------------------------------------------------------------------------
## Sources
- https://github.com/freerouting/freerouting/releases ; https://github.com/freerouting/freerouting ; https://github.com/freerouting/freerouting/blob/master/docs/command_line_arguments.md ; https://github.com/freerouting/freerouting/issues/1014 ; https://github.com/freerouting/freerouting/issues?q=45+degree
- Local jar inspection: `~/Applications/freerouting/freerouting-2.5.0.jar` (class/strings only; `--help` run once)
- https://docs.kicad.org/kicad-python-main/kicad.html ; https://docs.kicad.org/kicad-python-main/board.html ; https://www.kicad.org/blog/2026/03/Version-10.0.0-Released/ ; https://pypi.org/project/kicad-buddy/ (via search)
- https://github.com/drandyhaas/KiCadRoutingTools ; its docs/configuration.md and discussion #28
- https://github.com/rjwalters/kicad-tools
- https://deeppcb.ai/kicad-autorouter-alternative/ ; https://medium.com/my-life-as-a-tinkerer/using-topor-to-autoroute-a-kicad-pcb-bf5ae47cdc7b ; https://en.wikipedia.org/wiki/TopoR ; Quilter listings (sourceforge, ki-syndikat.de) ; https://www.flux.ai/docs/tutorials/copilot-use-cases/auto-layout ; Altium routing priority docs (altium.com/documentation/cstu/routing-priority)
- Placement: https://github.com/ajokela/pyplacer ; https://github.com/glovepost/atoplace
