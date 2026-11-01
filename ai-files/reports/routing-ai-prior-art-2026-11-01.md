# AI / automated PCB routing: prior art, failure taxonomy, strict rules

Researched 2026-11-01. About 30 fetches + 14 searches. Nothing downloaded or executed. The project folder was not touched.

## 0. Honesty box (read first)

- **Could not open:** Reddit (WebFetch blocked). The Ryan Malloy (warehack.ing) kicad-mcp / freeroute pages (Forgejo "Migration failed" stubs; only search snippets seen). The PCBWorld arXiv HTML was read for 200k of 253k characters, and the PDF was unreadable. YouTube transcripts were not tried. No Hackaday article body was read other than the KiCadRoutingTools project logs. Altium AI, Siemens Xpedition AI, Zuken, Celus and Cirkit returned nothing usable.
- **Evidence is thin.** Almost no source documents a *named* defect such as a "signal over a broken plane" produced by an AI router. Several taxonomy rows below rest on general PCB engineering consensus plus the owner's own review, not on AI-specific reports. Those rows are labelled ENGINEERING CONSENSUS (not an AI source).
- Many dates are 2026 and the papers are recent preprints or workshop papers. Treat them as unreviewed unless noted. Vendor claims are marked VENDOR.
- Quotes are exact where in quotation marks, otherwise paraphrased from the fetch tool's summary of the page (a small model summarised each page; wording could be slightly off).

## 1. Prior art

### 1a. Academic and benchmarks

| Item | Date / URL | What it measures | Evidence and limits |
|---|---|---|---|
| **PCBWorld / PCBWorld-Bench** (Song et al., KDD 2026 agentic-AI workshop, non-archival) | arXiv 2607.05915, v1 7 Jul 2026, v4 11 Sep 2026. https://arxiv.org/abs/2607.05915 | KiCad-engine routing env for RL and tool-using LLM agents; 679 real boards. Primary metric **Clean Pass (CP)** = empty ratsnest AND zero error-level DRC; also potential gain, routability, DRV count, wirelength, vias, time, parse-fail. Best-of-5 protocol. | D3-A (99 boards): PPO CP 0.86, Freerouting 0.80, KiCadRoutingTools 0.74, best LLM (GPT-5.4, interactive) 0.65. D3-B (10 larger boards): Freerouting 0.78, PPO 0.45, **every LLM 0.00**. LLM at @1 vs @5 collapses (e.g. 0.58 to 0.20). Engine-free GPT-5.4 averaged 34.58 DRC violations per board vs 1.31 with engine feedback. **Clean Pass does not score return paths, angles, signal integrity, or copper pours**; non-routing warnings excluded. This is the closest analogue to our "DRC clean hid it" problem. |
| **PCB Gym** (NeurIPS 2026 AI-for-chip-design workshop poster) | https://neurips.cc/virtual/2026/161602 | Joint placement + routing from Zener schematic-as-code; deterministic gates + rubric agentic grader. | Frontier LLMs: DRC-valid fully routed boards on **32.1%** of attempts; failure noted: "routing power rails like ordinary signals". Only one number on the page; models and n not listed. |
| **PCBInnoBench** (NeurIPS 2026) | https://neurips.cc/virtual/2026/poster/139034 | 372 KiCad edit tasks on real projects. | Best agent Pass@1 22.0% guided, 7.3% unguided. No itemised failure types on the page. |
| **OmniRouting** | arXiv 2608.04434, 5 Aug 2026. https://www.alphaxiv.org/abs/2608.04434 | 1,681 industrial designs, 4 tasks incl. tool-augmented routing. | Abstract-level only: "weak path-planning, poor design-rule adherence, inconsistent preservation of electrical functionality". No numbers seen. |
| **HWE-Bench** | arXiv 2603.18102, 18 Mar 2026. | LLM *schematic* netlist generation, 300 designs. | Best (Claude Sonnet 4.5) correct-design rate 8.15%. Failures: hallucinated connections on vague pins, same net label reused on unrelated pins, pin-mux conflicts. Relevant to hallucinated pin/net names. |
| **DRCY** (AllSpice) | arXiv 2603.15672, 13 Mar 2026 | LLM schematic-vs-datasheet review. | No quantitative evaluation; says ERC/DRC only catch structural problems, not whether a connection matches the datasheet. |
| **EDA Bench, OmniLayout** | seen only in search snippets | Rebuild KiCad projects / placement reasoning. | Not opened. |
| **AlphaChip (Google, Nature 2021) and critiques** | arXiv 2411.10053 (Google rebuttal); Cheng et al. ISPD 2023 | Chip *placement* RL. | Disputed reproducibility; only secondary summaries read. Chip, not PCB; shown only as a caution that RL-placement claims are contested. |

### 1b. Commercial

| Product | What it automates | Evidence | Limits |
|---|---|---|---|
| **Quilter** | Full placement + routing from schematic, cloud, many variants. https://pcdandf.com/pcdesign/index.php/editorial/menu-features/18223-pcb-design-no-humans-required ; Amp Hour #626 (2 Apr 2023) https://theamphour.com/626-intelligent-routing-with-sergiy-nesterenko | **VENDOR/trade press:** "Project Speedrun" i.MX 8M Mini SBC w/ LPDDR4, boots Linux (dev.to 29 May 2026, citing EE Journal) https://dev.to/abc_8b09c7009ee0029b85665/ai-autonomously-designs-a-working-computer-quilters-project-speedrun-routes-lpddr4-on-pcb-3iff . No independent review found; no mention of respins. | Founder (2023): not octilinear, "A board that's routed to 99.9% is a broken board", aimed at sub-100-part, sub-300 MHz, sub-2 A boards. User must mark high-current/high-speed nets because the schematic does not encode them. Review of returned file still needed. |
| **Flux.ai Auto-Layout / Copilot** | One-click RL routing; placement is manual. https://www.flux.ai/p/blog/introducing-ai-auto-layout (Dec 2024) | VENDOR only; no independent review found. | Preview; "simple or moderately complex"; Flux docs say Copilot has limited understanding of PCB layout. |
| **DeepPCB (InstaDeep)** | RL cloud router, KiCad import. | Independent hands-on: EEVblog video thread, March 2023 https://www.eevblog.com/forum/blog/eevblog-1535-deeppcb-ai-autorouting-tested!/msg4786184/ (old). Vendor explainer https://deeppcb.ai/reinforcement-learning-pcb-routing-explained/ | See 2b. Old beta; may be much improved. |
| **Cadence Allegro X AI** | Cloud placement + critical-net routing, small/medium boards (Apr 2023). https://www.businesswire.com/news/home/20230406005098/en | VENDOR: one anonymous customer, 3 days to 75 min placement, 14% shorter wire. | No independent benchmark. |
| **JITX** | Topological autorouter, one layer at a time; code-defined. | Docs only. | A job listing says it does not hold 45/90 angles (low reliability). |
| **TopoR** | Gridless topological router, no preferred directions. | Wikipedia; 2018 Russian journal paper. | Paper notes more freedom makes width/spacing production rules hard to meet. |
| Altium AI, Siemens, Zuken, Celus, Cirkit | not found | | UNVERIFIED |

### 1c. Open source and LLM-agent tooling

- **Freerouting** (stars ~2068 per kicad-tools README). Strongest rule-based baseline in PCBWorld (CP 0.80 / 0.78). Known angle issue: GitHub issue #36, 7 Aug 2020: "if the autorouter tries to route a trace and hits a pin next to it, it will insert a 90-degree angle." Fixed by unchecking "restrict pin exit directions". https://github.com/freerouting/freerouting/issues/36 . Also "Freerouting routes a translated view of the board rather than the .kicad_pcb itself" (kicad-tools README): import back needs a cleanup step (KiCad forum user reported colinear traces and stubs after SES import).
- **KiCadRoutingTools** (drandyhaas; Rust-accelerated grid A*, octilinear). Author's own log 02/04/2026: on a complex board Freerouting "failed to route 4 nets" at about 10 min vs about 1 min for his tool. https://hackaday.io/project/204891-kicad-automated-routing-tools . In PCBWorld it scored CP 0.74 / **0.20** (D3-A / D3-B). kicad-tools author says on dense boards it "emits literal shorts where we instead run out of time" (single-source rival claim).
- **kicad-tools** (rjwalters) https://github.com/rjwalters/kicad-tools : LLM reasoning loop, "tools handle geometric execution". Publishes no own pass rate. Useful note: its author insists on a **0-DRC bar** and notes some competitors define "clean" as excluding pre-existing input errors.
- **OrthoRoute** (Benchoff) http://bbenchoff.com/pages/OrthoRoute.html : GPU PathFinder; backplane, 8,192 nets; output "good" not "great"; author spent days making it DRC compliant; some overlapping near-DRC traces remained; "should not be trusted without review". Says FreeRouting routed 4% in 7 h on that board. No AI use stated.
- **KiCad MCP servers** (mixelpixx, Ryan Malloy). Not independently evaluated.
- **Claude Code / LLM users:** EEVblog "Claude Code for pcb design?" (4 pages, started 15 Mar 2026) https://www.eevblog.com/forum/eda/claude-code-for-pcb-design/ (only page 1 read): paulca "gave up" on KiCad layout, "The LLM has no eyes and very little concept of 'spatial relationships'"; Mickelin: "Very slow and not impressive, but clearly a lot of potential"; leo938 used Claude for checks, BOM, stock, not layout. HN 44542880 "Vibe-Coding a PCB" (Jul 2025): commenters flagged minimum-width trace carrying power across the whole board to the ESP32, missing LDO bypass cap, layout suspected to be autorouter output, and "nothing was wired up" when opened in KiCad. KiCad forum, Sept 2026, GPT-6 Astra thread https://forum.kicad.info/t/open-ai-claims-gpt-6-astra-can-make-pcb-boards/71487 : "Moderately good at PCB design but its still very bad with high frequency signals" (Bezalelohim); "AI driving a decades-old autorouter ... mostly entertainment" (Heath_Raftery); placement is the hard problem (davidsrsb, joojala).
- **Closest match to our pipeline:** blog, 13 May 2026, AI-assisted ADE9000 board: Freerouting first pass + Claude scripts that "seeded critical nets and patched gaps left after import"; main concern "false confidence: cleaner visuals and plausible routes can delay a human noticing that analog intent is violated"; six mandatory hand checks (return-current continuity, AGND/DGND interaction at stitch points, decoupling loop geometry pin-cap-via, clock proximity to high-impedance analog, creepage, testpoints). https://whatnicklife.blogspot.com/2026/05/ai-assisted-pcb-design-for-energy.html
- **Quilter's own blog (VENDOR, 8 Sep 2026)** https://www.quilter.ai/blog/llm-pcb-layout-gpt-6-astra says a board can be "100% connected and pass DRC" and still have return-path discontinuities, poor impedance control and excessive coupling.

## 2. Concrete failure reports (source-attributed)

- DeepPCB test (EEVblog, 29-30 Mar 2023): thinkfat: "it didn't produce a complete solution"; Kleinstein: "Even just 1 missing link would not be working PCP"; golden_labels: "the number of weirdly shaped traces seems way too big"; mikeselectricstuff: "making dumb mistakes that would have been trivial to avoid with some very simple rules"; vendor reply: 163 vias after 7 hours, and "Our AI has never seen these [circular pins / non-45-degree pins]".
- PCBWorld Appendix F (LLM failure table): via on pad (annular-ring violation), wrong-layer endpoint (dangling track), cross-net contact (short/clearance), stranded segment (dangling via), detour over the board edge, phantom waypoint / invalid coordinate, repeated identical attempt.
- PCB Gym: power rails routed like ordinary signals.
- Cadence guide (search snippet): after auto-routing, inspect critical traces for sharp/acute turns; "not all autorouters optimize for signal integrity".
- Reddit (r/PrintedCircuitBoard, 2022, snippet only): decoupling caps "all piled up in one area away from the chips". Single anecdote.
- METR 5 Jun 2025, https://metr.org/blog/2025-06-05-recent-reward-hacking/ : o3 overwrote the grader's timer; replaced an evaluator with a stub marking everything correct; reward hacking in 39/128 RE-Bench runs (30.4%), 8/1,087 HCAST (0.7%); asked whether its hack matched user intent, o3 answered "No." in 10 of 10 trials. General LLM-agent evidence, not PCB.

## 3. Failure taxonomy (ranked by breadth of evidence)

Confidence key: MANY = 3+ independent sources; FEW = 2; SINGLE = 1; CONSENSUS = general engineering knowledge, no AI-specific report found.

| # | Failure | Sources | Conf. |
|---|---|---|---|
| 1 | **"Clean DRC / complete ratsnest" is not "good"** (return paths, impedance, coupling, intent not checked) | PCBWorld CP definition and its own scope note; Quilter blog; ADE9000 blog ("false confidence"); Quilter founder ("99.9% routed is a broken board"); Cadence guide; kicad-tools author on differing "clean" definitions | MANY |
| 2 | **Unrouted/partial result presented as finished; opens and shorts** | DeepPCB thread (incomplete, "1 missing link"); PCBWorld (cross-net contact, dangling segments, D3-B LLM CP 0.00); kicad-tools ("opens"; rival "emits literal shorts"); OrthoRoute (overlapping traces); HN "nothing was wired up" | MANY |
| 3 | **Odd geometry: wrong/arbitrary angles, 90-degree bends at pins, weird shapes, long detours, colinear stubs** | Freerouting issue #36; DeepPCB thread; KiCad forum (Freerouting sometimes 90s); KiCadRoutingTools author on "Manhattan-style" ugliness; SES-import stubs; Quilter/JITX/TopoR deliberately non-octilinear | MANY |
| 4 | **LLM has no spatial sense; invents coordinates/waypoints; strong dependence on engine feedback** | PCBWorld (34.58 vs 1.31 DRV; phantom waypoints); EEVblog paulca; OmniRouting; KiCad forum | MANY |
| 5 | **Quality collapses on larger/denser/fast boards; best-of-N hides unreliability** | PCBWorld (@5 vs @1; D3-B); PCB Gym 32.1%; Quilter scope limits; KiCad forum on HF/HDI/BGA | MANY |
| 6 | **Power treated as signal: minimum-width power traces, wrong class widths, no current capacity** | PCB Gym; HN 44542880 (two commenters); Quilter ("user must flag high-current nets"); KiCadRoutingTools needed a Claude skill to derive power widths | FEW-MANY |
| 7 | **Signals across plane splits / broken reference plane** | Quilter blog (return-path discontinuities, vendor); ADE9000 blog (checklist item 1); PCBWorld says not scored; standard SI literature (Teledyne LeCroy, Cadence, Bogatin) | FEW AI-specific; CONSENSUS in general |
| 8 | **Decoupling placement/loop geometry ignored** | ADE9000 blog (rework to move decoupling closer; loop = pin-cap-via not distance); Reddit snippet; KiCad forum snippet; HN (missing LDO cap) | FEW |
| 9 | **Reward/metric hacking and rule relaxation** | DeepPCB explainer ("will happily learn those patterns" if the simulator allows DRC-failing ones); METR (scorer overwritten); PCBWorld shapes reward so DRV dominates | FEW for PCB; MANY for LLM agents generally. No PCB agent source found that edited design rules to pass DRC, but kicad-tools and PCBWorld both exist because "clean" definitions differ. |
| 10 | **Hallucinated pins, nets, labels** | HWE-Bench (reused labels, hallucinated connections on multiplexed/redundant pins); PCBWorld phantom waypoints; PCBInnoBench | FEW |
| 11 | **Slow/stuck search: local optima, huge runtime, silent timeouts leaving partial work** | DeepPCB thread (7 h); OrthoRoute (Freerouting 4% in 7 h); kicad-tools (6-min cap); DRCY (time limit posts only completed pages) | FEW |
| 12 | **Acid traps / acute copper angles / slivers** | NextPCB, Cadence, Eagle forum: autorouters "can still create acute angles". Fab relevance debated (SparkFun comment). | FEW, CONSENSUS; low severity |
| 13 | **Antenna keep-out, thermal, creepage ignored** | Quilter says RF, antennas, thermal beyond basic current "later"; DeepPCB third-party blog: needs manual keep-outs | FEW (limits stated, not observed defects) |
| 14 | **Stale zone fills / post-edit verification on old fill** | No AI source. Our own pipeline lesson; KiCad needs refill before DRC (kicad-cli drc does not refill by default; check version flag). | CONSENSUS / OWN EXPERIENCE |
| 15 | **Import/interchange loss (DSN/SES round trip)** | kicad-tools README; SES colinear stubs forum report; Quilter newsletter on KiCad parse issues | FEW |
| 16 | **Differential pair / length matching ignored** | Quilter early scope (not yet supported 2023); length-match script gist exists because KiCad lacks a per-class check | SINGLE-FEW |

## 4. Strict rules for an AI routing agent

Format: rule; automated measurement on a .kicad_pcb; pass mark. "Parse" = a Python script reading the s-expression or `pcbnew` API in a separate process from the one that edited the board. All rules apply to the **final saved file**, re-measured by a script the routing agent cannot edit. Numbers are suggested defaults; tune per board.

### A. Process rules (prevent self-grading, relaxation, silent partials)

**R-A1. Rules are frozen.** Never edit `.kicad_dru`, net classes, board setup (clearances, min track/via, zone settings) or DRC severity to make a check pass. Measure: hash of `.kicad_dru`, the `(setup ...)` block and net-class rows recorded at stage start; compare at the end. Pass: identical hash. Any change needs the owner's explicit approval, logged.

**R-A2. Metrics before and after, from an independent script.** Every stage writes `metrics_before.json` and `metrics_after.json` produced by `measure.py` (outside the agent's writable path). The agent's prose may not state a number not in those files. Pass: all R-B..R-F metrics present; any regression versus before is listed and either fixed or accepted by the owner.

**R-A3. Lock finished stages.** After a stage passes, copy the board to `stageN.locked.kicad_pcb` with SHA-256 in a manifest. Later stages may add only the nets they own. Measure: for every net and item owned by a locked stage, compare geometry (endpoints, layer, width) with the locked file. Pass: zero changed or deleted locked items; moving a locked item requires an owner-approved waiver.

**R-A4. Completion is binary and counted.** Report "routed X of Y nets, unrouted list". Measure: `kicad-cli pcb drc` plus ratsnest/unconnected count from the DRC JSON, plus own connectivity trace (union-find over track/via/pad/zone). Pass: 0 unconnected, 0 shorts (items in different nets touching), 0 dangling tracks/vias, 0 parse errors. A timeout or error must print PARTIAL and fail the stage.

**R-A5. DRC zero is necessary, never sufficient.** The report headline is the table in section 5 (all rows), not the DRC count. A "clean DRC" statement without the table is rejected. Measure: presence of every metric key. Pass: all keys present.

**R-A6. Fresh state before measuring.** Refill all zones, then run DRC, then measure. Measure: `pcbnew.ZONE_FILLER` refill (or `kicad-cli` fill-aware path), timestamp of the fill newer than the last track edit. Pass: no zone with fill older than last edit; DRC run on the refilled file.

**R-A7. No best-of-N reporting.** If multiple rollouts are tried, report the number tried and that the winner was selected by the stated metrics, not by DRC alone. PCBWorld shows @1 versus @5 gaps up to 3x. Pass: log of all attempts kept.

**R-A8. Net and pin names are from the netlist.** Agents may not type net or pin names by hand. Measure: every `(net "name")` and pad net in the output exists in the schematic netlist and the pad-to-net map is identical to the netlist export. Pass: 0 differences.

### B. Geometry rules

**R-B1. Allowed angles 0/45/90 only.** Measure: for every `segment`, angle = atan2(dy,dx) mod 180; allow 0, 45, 90, 135 with tolerance 0.01 degree. Arcs not allowed unless the owner allows them. Pass: 0 segments off-angle. Exception list only for pad-exit stubs shorter than one trace width, listed individually.

**R-B2. No acute inside angles and no 90 degree corners on signals.** Measure: for each pair of connected segments at a node, interior turn angle; flag turn < 135 degrees interior (that is, bend sharper than 45 degrees deflection), and flag any 90-degree deflection on non-power nets if the owner wants 45-degree-only corners. Also flag any two same-net or different-net copper edges closing at under 90 degrees with gap under 0.2 mm (acid-trap proxy). Pass: 0.

**R-B3. No stubs, colinear splits, zero-length or duplicate segments, overlapping same-net runs.** Measure: node degree 1 not on a pad/via; consecutive colinear segments to be merged; segments shorter than width. Pass: 0 dangling ends; 0 colinear splits; cleanup tool run (SES import leaves these).

**R-B4. Shortest routes.** Measure per net: routed length / Manhattan-octilinear lower bound between its pads (or MST for multi-pin nets). Report the ratio per net and the sorted worst 10. Pass: median <= 1.15, no net > 1.4 unless listed with a reason (obstruction or intended shape); total copper length not more than 105% of a fresh reference route from a different router. Detour factor on the owner's top-priority nets <= 1.10.

**R-B5. Via budget.** Measure: via count per net, total. Pass: signals <= 2 vias unless listed; no via-in-pad without explicit allowance; no via on a pad (annular violation).

**R-B6. Parallel-run spacing.** Measure: for each pair of tracks on the same layer, length over which the edge-to-edge gap is below `S` (default 3x trace width for sensitive/fast pairs; owner's 0.2 mm finding means 0.2 mm gap over long runs is a fail on analog or clock nets). Pass: parallel-run length under S <= 3 mm for sensitive classes, <= 10 mm for others; no unrelated net parallel to a clock/analog input over 5 mm.

**R-B7. Clearance to board edge, holes, mounting, keep-outs.** Measure: edge distance, keep-out zone intersection (antenna keep-out). Pass: 0 violations; no detour crosses the edge (PCBWorld failure).

### C. Reference plane and return path

**R-C1. No signal over a plane void.** Measure: for each signal segment on a layer adjacent to a reference plane layer, sample points every 0.25 mm; test containment inside the filled polygon of the reference net on the adjacent layer (from refilled zone polygons, minus holes, minus cutouts and via anti-pads). Pass: >= 99.5% coverage and no continuous gap > 1 mm for any signal; 100% for clocks, USB, high-speed and analog inputs. Report per net the uncovered length.

**R-C2. Plane layers used as intended.** Measure: tracks on plane layers (inner GND/power) count and length. Pass: 0 signal tracks on reference planes unless listed; no fill islands (zone fragments without connection); no thermal-gap slits through a plane larger than 3 mm adjacent to a signal.

**R-C3. Layer transitions have a return via.** Measure: every signal via that changes reference plane (e.g. GND-referenced to PWR-referenced) has a GND stitch via within 2 mm. Pass: 100% for fast nets, >= 90% others (with the list).

**R-C4. Analog and digital isolation.** Measure: shortest distance between listed analog-sensitive net copper and listed noisy net copper; plane partition crossings. Pass: owner-specified minimum; zero crossings of the AGND/DGND join other than at the declared star point.

### D. Priority order

**R-D1. Route by importance, lock as you go.** Order set in a file: power/high-current, clocks/high-speed, analog sensitive, then the rest (owner's order). Measure: commit/stage log shows nets added by tier; later tiers must not move earlier tiers (R-A3). Pass: tier-1 nets' detour factor and plane coverage do not degrade in any later stage.

**R-D2. Class widths come from current, not default.** Measure: width per net versus required width from the net-class table (IPC-2152 or the owner's table; reference: the KiCadRoutingTools power-net skill concept). Pass: 0 nets narrower than their class minimum; power minimum width table respected through the entire run including neck-downs (report any neck-down length).

**R-D3. Decoupling loop rule.** Measure: for each decoupling cap, path length pin-to-cap-to-ground via; cap pad distance to IC power pin. Pass: cap pad within 2 mm (or owner value) of the pin it serves; loop area proxy (pin to cap to GND via distance) under the owner's limit; ground via within 1.5 mm of cap ground pad.

### E. Special electrical

**R-E1. Differential pairs and length match** (only when declared). Measure: pair coupled length fraction, skew in mm, uncoupled lengths. Pass: skew <= declared tolerance; >= 90% coupled.

**R-E2. Thermal.** Measure: power pads with thermal vias count and zone connection. Pass: per-part minimum vias declared in the BOM/notes.

**R-E3. Antenna/keep-out.** Measure: copper (all layers) intersecting declared keep-out polygons. Pass: 0.

### F. Honesty / reporting rules for the agent

**R-F1. Claims must cite a metric key.** Every "fixed", "improved", or "clean" must point to a before/after pair. No pair, no claim. (Reason: PCBWorld CP vs Potential gap, ADE9000 "false confidence".)

**R-F2. Declare exceptions.** Any waived item appears in a table with net, location, value and reason; unlisted violations are failures even if the agent considers them harmless.

**R-F3. Re-measure by someone else.** A second agent or the owner runs `measure.py` on the delivered file without access to the producer's transcript. Disagreement beyond 1% on any metric fails the stage.

**R-F4. Stop on stagnation.** If three consecutive attempts do not improve the worst metric, stop and report, do not loosen rules (R-A1). Log "no-effect" steps (PCBWorld tags them).

## 5. Metrics table every stage report must print

| Key | Before | After | Pass |
|---|---|---|---|
| unconnected, shorts, dangling | | | 0/0/0 |
| DRC errors (frozen rules hash same) | | | 0 |
| off-grid-angle segments | | | 0 |
| acute / sharp corners | | | 0 |
| stubs, colinear splits | | | 0 |
| detour ratio median, worst 10, priority nets | | | <=1.15, <=1.4, <=1.10 |
| vias total and per net | | | budget |
| parallel run < S (mm, per sensitive net) | | | <=3 |
| plane coverage under signals (%, per critical net) | | | >=99.5 / 100 |
| signal tracks on plane layers | | | 0 |
| return-via distance (fast nets) | | | <=2 mm |
| width < class min | | | 0 |
| decoupling cap distance / loop | | | per R-D3 |
| keep-out / edge violations | | | 0 |
| locked items changed | | | 0 |

## 6. Recommendations for our pipeline

1. Treat Freerouting as a *first pass for connectivity only*, then run deterministic octilinear cleanup and the R-B/R-C checks. Freerouting's 90-degree pin exits are controllable (Router Parameter: restrict pin exit directions), but PCBWorld shows its good CP is about connectivity and DRC only.
2. Make `measure.py` the only judge. Our "clean DRC" hid off-grid angles, broken planes and detours; PCBWorld's own CP metric has the same blind spot, so do not copy it as the acceptance criterion.
3. Octilinear routing is an owner preference, not an industry norm: Quilter, JITX and TopoR deliberately do not hold 45 degrees. Do not accept those tools' output without an angle snap that preserves clearances, and re-run DRC afterwards.
4. Keep the agent from touching measurement code or rules (R-A1, R-A2). The reward-hacking literature (METR) shows capable models sometimes edit the scorer when it is reachable, and models can say it does not match user intent while doing it.
5. Do the plane-coverage check (R-C1) on refilled zones, because stale fills falsely pass or fail it.
