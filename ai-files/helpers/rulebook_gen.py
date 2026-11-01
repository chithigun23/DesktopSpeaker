import html, os, sys
FORUM = open(sys.argv[1]).read() if len(sys.argv)>1 and os.path.exists(sys.argv[1]) else '<p class="note">Forum research is still being collected. This section is filled in when it finishes.</p>'
LV={'M':('MUST','must'),'S':('SHOULD','should')}
def rules(rows):
    out='<div class="tblwrap"><table><thead><tr><th>ID</th><th>Rule</th><th>How it is measured, and the pass mark</th><th>Source</th></tr></thead><tbody>'
    for rid,lv,rule,meas,src in rows:
        out+=f'<tr><td class="id">{rid}<br><span class="pill {LV[lv][1]}">{LV[lv][0]}</span></td><td>{rule}</td><td>{meas}</td><td class="src">{src}</td></tr>'
    return out+'</tbody></table></div>'
def sec(title,intro,rows,idn):
    return f'<section id="{idn}"><h2>{title}</h2><p class="intro">{intro}</p>{rules(rows)}</section>'
PL=[
('PL1','M','Placement is finished and signed off before any routing starts. Parts with a location constraint stay; every other part may move, the MCU included. Fixed: connectors J1&ndash;J3, J5, J9&ndash;J11, mounting and lid-screw holes, controls SW100&ndash;SW102, the BM83 at the antenna edge, the two amplifiers beside their speaker connectors.','Move log with reference, old and new position and reason. After the pass, position files, JLC preview material, 3D render and fab output are regenerated.','USER'),
('PL2','M','Each IC sits close to the centre of the pads it talks to. Score = sum of octilinear distances from the IC to the pads on its signal nets (rails and ground excluded).','Per IC, score within 10% of the best position the free space allows. Baseline: U3 (MCU) is 20% above the optimum and sits 35 mm from it.','Review R6q'),
('PL3','M','Decoupling and hot-loop parts are placed first, in the vendor order, and everything else is placed around them. High-frequency cap pad within 3 mm of the pin it serves, same side, no via between them.','Pad-to-pin distance for every cap on every IC. Baseline already passes (1.1&ndash;3 mm); it must not get worse.','TI BQ25792 EVM guide, SLYT614, TAS5825M datasheet'),
('PL4','M','All parts at 0&deg; or 90&deg; rotation. Rotate a part until its pin rows face the parts it connects to, so buses leave in straight parallel runs.','Rotation list. Baseline passes (all 360 are on 90&deg; steps).','USER, owner style'),
('PL5','M','Every fine-pitch IC edge keeps a clear corridor at least 1 mm deep in front of its pins for escape routing. Nothing is placed in that corridor.','Courtyard check by script.','Owner style, TAS5825M datasheet (route perpendicular)'),
('PL6','S','Sensitive analog parts (ADC inputs, headphone amplifier, mux and jack network) sit at least 5 mm from any switching node and from digital clocks.','Distance table from the placement pass.','Project audio rules'),
('PL7','M','A slow control net longer than 100 mm needs a written reason. The fix is to move a part, not to route around it.','Net-length list. Baseline: 30 nets over 100 mm; worst ENC_SW at 194 mm against a 67 mm minimum.','Review R6q'),
]
OR=[
('OR1','M','Route in importance order and finish each stage before the next: S0 power hot loops and power paths; S1 USB pair, clocks, I2S; S2 analog audio and the amplifier I2C; S3 control signals; S4 ground fan-out and stitching vias; S5 pours and necks; S6 clean-up and teardrops.','Per-stage log. Each stage ends with the gates in section VF.','TI SLYT614 (power loop first), owner style'),
('OR2','M','Inside a stage, route the most constrained nets first: fine-pitch escapes, then longest, then the rest.','Stage log shows the order used.','Forum consensus, see section F'),
('OR3','M','A finished stage is locked. Later stages do not change its copper except by a recorded exception.','Each finished stage is saved as a locked copy with its SHA-256 in a manifest. Diff of earlier-stage copper after each stage: 0 changes.','Process'),
('OR4','M','A stage that fails any MUST below for its own nets is not accepted; rework it before moving on.','Metrics report per stage.','Process'),
]
GE=[
('GE1','M','Every straight track segment is exactly 0&deg;, 45&deg; or 90&deg;.','Segment angle to the nearest grid angle: |dx| and |dy| equal to within 0.005 mm for 45&deg;, or one of them under 0.005 mm. Pass: 100% of segments and of length. Baseline: 38.5% of length exact; 35% of long segments 5&deg; or more off.','USER, owner style'),
('GE2','M','No arcs on signal or power tracks. Teardrops and zone outlines are the only curved copper.','Arc count on non-teardrop tracks: 0. Baseline: 26.','USER, owner style'),
('GE3','M','Corners are built from two 45&deg; bends. A single 90&deg; turn is allowed only at a pad or via entry.','Count of 90&deg; joints away from pads on signal nets: 0. Baseline: 103 joints near 90&deg;.','Altium angle article; owner style'),
('GE4','M','No joint turns more than 90&deg;; that is, no joint with an interior angle under 90&deg;.','Joints with interior angle under 90&deg;: 0. Baseline: 36 under 80&deg;, 7 under 30&deg;.','Etchant traps; manufacturing practice'),
('GE5','M','Segments between two bends are at least 3&times; the track width and at least 0.4 mm long.','Short-segment count: 0.','Project rule 13 (2026-10-09)'),
('GE6','M','No stub or dead end longer than 0.3 mm except a pad-to-via fan-out. No T-junction on a signal net except at a pad or via. No colinear split, zero-length or duplicate segment, or overlapping run of the same net (a Specctra import leaves these).','Stub and T-junction count by script: 0.','Owner style, I2C and multi-drop practice'),
('GE7','M','A track leaves a pad along the pad&rsquo;s long axis and runs straight for at least 0.3 mm before its first bend.','First-segment check on every pad: 0 failures.','Fan-out practice'),
('GE8','S','Width stays constant along a run. A neck at a pad is allowed and is no longer than 1 mm.','Width changes per net.','Layout practice'),
('GE9','M','A bus (I2S trio, I2C pair, USB pair) keeps a uniform gap and turns at the same place, each line mitred concentrically.','Gap variation along the bus no more than 0.05 mm outside bends.','Layout practice'),
]
LE=[
('LE1','M','Every signal net is as short as it can be. The reference length is the octilinear minimum: a minimum spanning tree over its pads using distance = max(dx,dy) + 0.414&middot;min(dx,dy).','Per net routed length / octilinear minimum: median at most 1.15, 95th percentile at most 1.4, none above 1.6 without sign-off.','USER, owner style'),
('LE2','M','Whole-board signal length stays near the minimum.','Total signal length / total octilinear minimum at most 1.12. Baseline 1.24. Reference boards: 0.99 and 1.11 (see benchmarks).','Benchmark boards'),
('LE3','M','A detour above 1.4&times; is fixed by moving a part or swapping pins, not by routing around.','List of nets above 1.4&times; with the fix applied.','Review R6q'),
('LE4','M','Layer changes are minimal. Clocks, I2S and USB use no via between source and sink. A two-pin net uses at most two vias.','Via count per net.','Signal integrity practice'),
('LE5','M','Where two pads face each other, connect them with one straight segment: align or rotate the parts so that it is possible.','Count of two-pad nets with a bend: reported.','Owner style'),
]
LA=[
('LA1','M','F.Cu is the main signal layer, B.Cu the second. In1 is solid ground: no tracks, no cuts other than via antipads. In2 carries power pours and ground only.','Signal track length on In2: 0 mm (baseline about 1,160 mm). Tracks on In1: 0.','4-layer practice, TI guidance'),
('LA2','M','Sensitive nets (USB, I2S and clocks, analog audio, amplifier I2C) are on F.Cu over In1 ground. A layer change is allowed only to reach a pad.','Sensitive length on B.Cu: 0 mm, or the stretch lies over In2 ground and is stitched (LA5). Baseline: about 190 mm over islands or voids.','Review R6q'),
('LA3','M','Other signals may use B.Cu but only over In2 ground.','At least 90% of B.Cu signal length over In2 ground, 0 mm over PVDD, VBUS_PD or BAT islands. Baseline: 44% over ground.','Review R6q'),
('LA4','M','No signal crosses a slot or void in its reference plane.','Sampled every 0.4 mm against the refilled zones: at least 99.5% coverage for every signal, 100% for critical nets; 0 mm over a void larger than a via antipad. Baseline: 162 mm on F.Cu, 664 mm on B.Cu.','EMC practice'),
('LA5','M','Every layer change of a sensitive net has a ground via within 1.5 mm. Other signals: within 5 mm.','Distance table. Baseline: I2S worst 2.2 mm, AUD I2C worst 8.9 mm.','Forum and vendor practice'),
('LA6','S','Prefer horizontal runs on F.Cu and vertical on B.Cu, to avoid mutual blocking.','Direction share by layer.','Layout practice'),
]
SP=[
('SP1','M','Parallel runs of different signal nets longer than 3 mm have an edge gap of at least 3&times; the height above the reference plane: 0.6 mm on F.Cu (prepreg 0.21 mm). This applies between the three I2S lines.','Near-parallel length (angle within 12&deg;) at gap under 0.6 mm: 0 mm. Baseline: I2S BCK|LRCK 86 mm and BCK|SDATA 62 mm at 0.20 mm.','3W rule family; project stack-up'),
('SP2','M','Analog audio nets keep at least 0.5 mm from every other net. USB pair stays at least 1.0 mm from other signals.','DRC rule <code>audio_clear</code> and a new USB rule, both after the neck rules.','Project rules'),
('SP3','M','Feedback, compensation, current-limit, program and sense pins (FB, COMP, ILIM, PROG, TS, BATP) keep at least 2.0 mm from SW, BST and OUT copper, except at the pins themselves.','Distance table. Baseline: ILIM_HIZ about 0.6 mm from SW2.','TI layout sections; SLVA773'),
('SP4','M','The spacing rules in SP1&ndash;SP3 exist as custom DRC rules, placed after the <code>neck_</code> relaxations, and each has been proven by a sentinel test.','Sentinel run fires every new rule. Baseline: SP1 had no rule and <code>neck_ic</code> overrides SP2 and SP3 inside IC courtyards.','Review R6q'),
]
PW=[
('PW1','M','Hot loops follow the vendor order. BQ25792: 0.1 &micro;F caps on SYS, PMID and VBUS first, each closer than its 10 &micro;F, on the IC layer and with no via; then bulk caps; REGN and BTST caps; VBUS and BAT caps with at least two vias per terminal where vias are needed; inductor next to SW1/SW2. Boost and buck stages: input cap, then inductor and SW, then output cap, then small-signal parts, then digital pins.','Pad-to-pin distances; loop on one layer; 0 vias in the loop; first output cap of the TPS61088 within 3 mm (baseline 4.9 mm); a ground via within 1.5 mm of every decoupling cap&rsquo;s ground pad.','TI BQ25792 EVM guide; SLYT614; SLVA773'),
('PW2','M','Power paths are sized for the current: pours above 2 A. 1 oz outer copper at 10 K rise needs about 0.3 mm per 1 A, 1.4 mm for 3 A, 3.6 mm for 6 A; 0.5 oz inner needs about 2.5&times; the outer width. No existing power neck is narrowed.','Width and cross-section table per power net, no narrower than the R6l reviewed values.','IPC-2221; R6k and R6l reviews'),
('PW3','M','Switch-node copper is as small as the current allows and on F.Cu only.','SW pour areas not above the current 8&ndash;15 mm&sup2;; no SW copper on B.Cu or In2. Baseline has B.Cu SW jumpers; remove them where possible.','TI datasheets'),
('PW4','M','A 3V3 rail with mixed loads branches from the filter point as a star: amplifier DVDD, ADC AVDD and the headphone amplifier each get their own branch, at least 0.4 mm wide.','Topology drawing and widths. Baseline: one 298 mm tree, 43% narrower than 0.5 mm.','Review R6q'),
('PW5','M','Via count on a power path follows one via per amp (0.3 mm drill about 1 A, 0.4 mm about 1.5 A).','Via count and current per path.','TI SLVA773; project rule'),
]
VI=[
('VI1','M','Standard via 0.6/0.3 mm, power via 0.8/0.4 mm, 0.5/0.2 mm only in the TPS25730D necks. No via in a pad except the recorded exceptions; put the via at the end of a short stub beside the pad.','Via-in-pad list: at most the three recorded.','JLCPCB capabilities; release review R8'),
('VI2','M','No via sits between a decoupling cap and the pin it serves.','Check on all 17 ICs.','TI layout sections'),
('VI3','M','A via is never closer than 0.15 mm to a pad&rsquo;s mask opening unless it is intended.','Count: 0. Baseline: 22.','Release review R8'),
('VI4','S','Ground stitching around the Bluetooth module at most 3 mm apart and along the board perimeter at most 10 mm apart.','Via spacing check.','Project rule; vendor and forum practice'),
]
FO=[
('FO1','M','QFN and other fine-pitch parts: escape perpendicular to the package edge, no trace between the pads of another part, no track across a thermal-pad heat path.','Visual crop of every IC plus pad-axis check.','TAS5825M datasheet'),
('FO2','M','TAS5825M thermal pad: via columns in radial order, no thermal relief on thermal vias, no signal tracks across the pad&rsquo;s ground copper.','Via count 16 or more, relief off.','TAS5825M datasheet 10.4'),
('FO3','M','Bus pins that leave a part together stay in the same order all the way to the far part, with no crossings. Swap pins in the schematic where it removes a crossing.','Crossing count on buses: 0.','Layout practice'),
]
MF=[
('MF1','M','JLCPCB limits: track and clearance at least 0.2 mm (0.1 mm only on the U11 and J1 necks), annular ring at least 0.15 mm, drill at least 0.3 mm (0.2 mm only on U11), via or pad to board edge at least 0.5 mm, silkscreen off pads, teardrops on every pad and via joint, no copper sliver under 0.15 mm, zones refilled before the last DRC.','DRC, sliver scan, teardrop count.','JLCPCB capabilities'),
('MF2','M','Antenna keep-out stays empty on all layers and no top-layer routing sits under the BM83 body if the datasheet&rsquo;s certified-layout condition applies.','F.Cu length inside the module pad rectangle. Baseline 14.9 mm.','Microchip BM83 datasheet'),
]
VF=[
('VF1','M','DRC with every custom rule active: 0 violations, 0 unconnected, 0 parity items.','<code>kicad-cli pcb drc --severity-all --all-track-errors</code>, plus a sentinel rule that must fire.','Review R6q'),
('VF2','M','The metrics report passes every MUST above and is stored with the board.','<code>ai-files/helpers/r7_metrics.py</code> and the angle and length checks; JSON stored beside the board.','Review R6q'),
('VF3','M','A second reviewer, working from the raw board file and not from the author&rsquo;s scripts, repeats the metrics and looks at crops of every IC.','Written review with its own numbers.','Review R6q'),
('VF4','M','No stage is merged into the project board until it passes. The project board is changed once, at the end, by the coordinator.','Git history.','Process'),
]
AG=[
('AG1','M','No agent relaxes, exempts or narrows a DRC rule, net class, rule area or keep-out to clear a violation without a written user decision. No board-wide or width-based exemptions; rule areas only per named footprint.','SHA-256 of <code>.kicad_dru</code>, the board setup block and the net-class rows recorded at stage start and compared at the end: identical. Diff against the approved baseline: 0 unapproved changes. Every custom rule has a sentinel test and a per-piece DRC (board split into 1 mm pieces) because neck rules apply to a whole item.','Own history, cluster A (7 cases, R6l report line 43)'),
('AG2','M','Goal metrics are fixed before routing starts and are not the gate counts. Open edges and DRC 0 are not evidence of quality.','The metrics in this rulebook (GE, LE, LA, SP, PW) with the baseline, produced by script. The agent cannot edit the measuring script. Before and after files are written by that script, and the agent&rsquo;s text may not state a number that is not in them. The reviewer re-measures with its own scripts.','Own history, cluster B (10 cases); AI-routing research'),
('AG3','M','Every round reports a before/after table of all metrics, not only the targeted one. A protected metric that gets worse stops the round: protected means decoupling distances, thermal-via counts, power necks, clearances of touched copper, island pieces, slivers.','Table in the round report; reviewer recomputes it. Never re-base on an older work copy: each round starts from the last adopted board, followed by a full footprint, model and pad-net diff.','Own history, cluster C (5 regressions)'),
('AG4','M','An item called &ldquo;inherited&rdquo; is re-checked against this standard every round, has an owner and a decision, and counts against release. Anything inherited twice goes to the user.','Inherited-items list with dates.','Own history: the same list ran from R6j to R6q'),
('AG5','M','No number in a report without the command that produced it, and a date or commit for anything that can go stale. The reviewer reproduces at least 10 numbers plus every number used to justify a PASS, and cross-checks a measurement artefact with a second method.','Commands in the report; reviewer notes.','Own history, cluster D'),
('AG6','M','Outside KiCad DRC the reviewer parses the saved board, refills zones before any DRC, parses the gerbers (mask, paste, via openings), tests via distance to the pad opening rather than the via centre, scans pours for slivers and checks the net class of every net by name.','Review checklist with outputs.','Own history: DRC cannot see mask or paste; 22 vias half exposed; comb-shaped U11 openings'),
('AG7','M','No routing past a placement failure. Decoupling, ground-pin and escape-lane faults are fixed in placement first. Every routing report lists nets above 2&times; their minimum.','Placement gate result recorded before stage S0.','Own history, rule R-G'),
('AG8','M','Each adopted round is committed; there is one handover; user decisions are recorded the same day.','Git log.','Own history, rule R-H'),
('AG9','M','Completion is binary and counted. A stage report states &ldquo;routed X of Y nets&rdquo; and lists the unrouted ones. Unconnected items, shorts and dangling tracks or vias are all zero before a stage is called done.','DRC unconnected count plus the agent-independent connectivity trace (union-find over tracks, vias, pads and zones): 0 unconnected, 0 shorts, 0 dangling.','AI-routing research (PCBWorld, DeepPCB)'),
('AG10','M','A partial or timed-out run is reported as partial. Intermediate boards are never presented as results.','Run log shows completion status.','AI-routing research'),
('AG11','M','Net and pin names come from the netlist only. No agent types a net or pin name by hand.','Every net name and pad-to-net map in the output equals the netlist export: 0 differences.','HWE-Bench, PCBWorld (invented waypoints)'),
('AG12','M','No best-of-N reporting. If several attempts are made, report how many and that the winner was chosen by the stated metrics, not by DRC alone. Keep a log of all attempts.','Attempt log.','PCBWorld: best-of-5 versus best-of-1 gaps up to three times'),
('AG13','M','Stop on stagnation. After three consecutive attempts that do not improve the worst metric, stop and report. Do not loosen rules to continue.','Attempt log with the worst metric per attempt.','METR reward-hacking findings; own history'),
('AG14','M','Every waived item is in an exceptions table with net, location, value and reason. An unlisted violation is a failure even if the agent thinks it harmless.','Exceptions table.','AI-routing research'),
('AG15','M','A second reviewer, without the producer&rsquo;s transcript, runs the measuring script on the delivered file. A disagreement above 1% on any metric fails the stage.','Reviewer output.','AI-routing research'),
('AG16','M','Every claim of &ldquo;fixed&rdquo;, &ldquo;improved&rdquo; or &ldquo;clean&rdquo; points to a before and after pair in the metrics file. No pair, no claim.','Report cross-reference check.','ADE9000 blog (&ldquo;false confidence&rdquo;)'),
]
HA=[
('HA1','M','All SMD parts are on the top side. Nothing SMD on the bottom, so the bottom lies flat on the hotplate. Through-hole parts are soldered after reflow.','Footprints on B.Cu with SMD pads: 0. Baseline passes (only the logo graphic).','Hand assembly (user)'),
('HA2','M','Stencil: 0.10 mm laser-cut, electropolished foil. Every paste aperture has area ratio at least 0.66 and aspect ratio at least 1.5 on that foil.','Script from pad and paste geometry. Baseline on 0.10 mm: 9 pads fail (J1, U25, U4); on 0.12 mm: 57 fail (J1, U11, U25, U4). The J1 pads read 0.005 mm and must be checked in the footprint.','IPC-7525B via JLCPCB and LCSC; own arithmetic (0.2 mm pad at 0.4 mm pitch: ratio 0.64 on 0.12 mm, 0.77 on 0.10 mm)'),
('HA3','M','No paste aperture narrower than 0.19 mm at 0.4 mm pitch or 0.24 mm at 0.5 mm pitch. QFN and other thermal pads use window panes covering 50&ndash;75% of the pad, pane pitch 1.0&ndash;1.5 mm, webs at least 0.25 mm, panes at least 0.5 mm on a side, and no paste over a via centre. No comb-shaped apertures.','Aperture geometry check. Baseline: the U11 combs were fixed in release review R8; TAS5825M U6/U7 have 100% paste over 16 open vias each.','JLCPCB stencil capabilities; LCSC; TI; release review R8'),
('HA4','M','Pads on hand-soldered passives extend 0.1&ndash;0.2 mm beyond the package outline at the toe, so an iron can reach them. The footprint library&rsquo;s HandSolder variants are audited for their real pad sizes.','Pad size per footprint against the reference table in the footprint audit.','LCSC; Worthington 0402 reference'),
('HA5','M','Tombstoning: the two pads of every two-pad passive have the same pad size, the same track width, the same via count and the same pour connection. A pad on a pour connects through four spokes of 0.25&ndash;0.3 mm or, if solid, so does its partner. No via in a passive&rsquo;s pad.','Script over every 2-pad part: pad-pair asymmetry list, target 0.','Forum and vendor consensus'),
('HA6','M','Vias stay at least 0.5 mm from an SMD pad edge unless tented and dogboned; no via in the pad of a passive or a fine-pitch signal pin. Thermal vias are 0.3 mm drill or smaller on a 1.0 mm pitch, left open on top with paste panes between them, and tented on B.Cu so no solder reaches the plate.','Via-to-pad distances; via-in-pad list (baseline 3 recorded plus 22 half-exposed); tenting flag.','TI, LCSC; owner recommendation (open versus tented is disputed)'),
('HA7','M','Pads are copper-defined (NSMD). The mask dam between fine-pitch pads is at least 0.10 mm (JLCPCB minimum). At 0.4 mm pitch, gang the openings or reduce the mask expansion instead of leaving a dam under 0.10 mm.','Minimum mask web between pad openings.','JLCPCB capabilities'),
('HA8','M','Spacing for tweezers and hot air: at least 1.0 mm between neighbouring courtyards (0.5 mm for two 0402s on the same net); at least 3 mm clear around every QFN, LQFP and fine-pitch IC; no part taller than 3 mm within 2 mm of a small passive or a fine-pitch IC edge.','Gap table from the placement pass. Baseline: median 0.68 mm nearest-neighbour pad-box gap, 56 parts under 0.5 mm.','Practice (research defaults, no standard found); owner constraint'),
('HA9','M','Silkscreen: pin-1 and polarity marks and part outlines are visible after the part is placed, not under the body. Text at least 1.0 mm high, strokes at least 0.15 mm, nothing on pads.','Silkscreen check by script plus visual crop of every IC.','JLCPCB capabilities; practice'),
('HA10','M','Alignment for the hand stencil: three non-plated tooling holes (2.5 mm in the board, 2.6 mm in the stencil) in a non-symmetric pattern, or the existing mounting holes if a jig is built for them. Optional 1 mm fiducials.','Scheme recorded in the assembly notes and the stencil order.','KiKit and forum jig practice (single voice)'),
('HA11','M','Parts soldered by hand after reflow, with iron access left around them: polymer cap C275, JST VH (J9&ndash;J11), Micro-Fit J5, jacks J2 and J3, the encoder SW102, SW101 and any tact switch or USB-C receptacle not rated for reflow. The BM83 may go on the plate (Microchip allows a peak up to 260 &deg;C).','List in the assembly notes; at least 2 mm iron access around each.','Microchip BM83 datasheet; practice'),
('HA12','M','Test points are reachable from above and are not under tall parts.','Courtyard check.','Practice'),
]
bench=[('USB2Speakon (4 layers)','100%','1.50&times;','Tiny board; short runs dominate'),('analog-toolkit (4 layers, STM32 + USB-C PD)','100%','1.11&times;','Mixed analog and digital'),('power-manifold charger (4 layers, buck-boost + STM32G071)','100%','0.99&times;','Closest topology to ours'),('LibreSolar BMS-C1 (4 layers)','100%','0.88&times;','Pads on pours reduce the signal length'),('IP5328P power bank (2 layers)','100%','1.32&times;','Weakest benchmark'),('<b>DesktopSpeaker R6q</b>','<b>38.5%</b>','<b>1.24&times;</b>','Current board; <b>fails both marks</b>')]
bt=''.join(f'<tr><td>{a}</td><td class="n">{b}</td><td class="n">{c}</td><td>{d}</td></tr>' for a,b,c,d in bench)
base=[('Length exactly on 0/45/90&deg;','38.5%','100%','GE1'),('Joints with interior angle under 90&deg;','36 (7 under 30&deg;)','0','GE4'),('Signal track length on In2','about 1,160 mm','0 mm','LA1'),('Sensitive nets on B.Cu over island or void','about 190 mm','0 mm','LA2'),('B.Cu signal over In2 ground','44%','at least 90%','LA3'),('F.Cu signal over In1 void','162 mm','0 mm (beyond via antipads)','LA4'),('Near-parallel I2S at gap under 0.6 mm','148 mm','0 mm','SP1'),('Control-pin distance to SW node (ILIM_HIZ)','about 0.6 mm','at least 2.0 mm','SP3'),('Total signal length / octilinear minimum','1.24','at most 1.12','LE2'),('Nets above 100 mm','30','justify each; target under 10','PL7'),('Worst ground-via distance, sensitive layer change','2.2 mm (I2S), 8.9 mm (AUD I2C)','1.5 mm','LA5'),('MCU position against optimum','20% above','within 10%','PL2')]
bs=''.join(f'<tr><td>{a}</td><td class="n">{b}</td><td class="n">{c}</td><td class="id">{d}</td></tr>' for a,b,c,d in base)
drc='''(rule i2s_pair_gap
  (condition "A.NetClass == 'I2S_CLK' &amp;&amp; B.NetClass == 'I2S_CLK'")
  (constraint clearance (min 0.6mm)))

(rule no_signals_on_in2
  (layer "In2.Cu")
  (condition "A.Type == 'Track' &amp;&amp; A.NetClass != 'POWER_HI' &amp;&amp; A.NetClass != 'PVDD' &amp;&amp; A.NetClass != 'PWR_5V' &amp;&amp; A.NetClass != 'PWR_3V' &amp;&amp; A.NetClass != 'GND'")
  (constraint disallow track))

(rule sensitive_not_on_bcu
  (layer "B.Cu")
  (condition "A.NetClass == 'AUDIO' || A.NetClass == 'I2S_CLK' || A.NetClass == 'USB'")
  (constraint disallow track))

(rule control_pins_far_from_sw
  (condition "A.NetClass == 'SWITCH' &amp;&amp; (B.NetName == 'Net-(U4-BATP)' || B.NetName == '/Battery_Charger/ILIM_HIZ' || B.NetName == '/Battery_Charger/TS_SENSE' || B.NetName == '/Battery_Charger/PROG') &amp;&amp; !(A.Type == 'Pad' &amp;&amp; B.Type == 'Pad')")
  (constraint clearance (min 2.0mm)))'''
EXT=open('/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/rb/external.html').read() if os.path.exists('/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/rb/external.html') else ''
page=f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Routing Rulebook</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&amp;family=IBM+Plex+Mono:wght@400;500&amp;display=swap" rel="stylesheet">
<style>
/* Layout: summary, stage order, rule tables by area (ID, rule, measure, source), baseline vs pass mark, benchmarks, enforcement, pipeline, forum findings. Board-green ink; amber and red only for severity. */
:root{{--bg:#f3f5f2;--panel:#fff;--ink:#17211b;--muted:#59665d;--line:#d6ddd5;--accent:#1d5f47;--accent-soft:#dbeae2;--hi:#a63a2b;--hi-soft:#f4dcd7;--mid:#96600a;--mid-soft:#f5e7c6;--lo:#3d5f8a;--lo-soft:#dde6f1;--display:"IBM Plex Mono",ui-monospace,Menlo,monospace;--body:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,sans-serif}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#0f1511;--panel:#171f19;--ink:#e3eae4;--muted:#9aa89e;--line:#2a362d;--accent:#62c493;--accent-soft:#1c3427;--hi:#ef8b79;--hi-soft:#3d201b;--mid:#e4b350;--mid-soft:#3a3015;--lo:#8fb2e0;--lo-soft:#1c2a3d;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#0f1511;--panel:#171f19;--ink:#e3eae4;--muted:#9aa89e;--line:#2a362d;--accent:#62c493;--accent-soft:#1c3427;--hi:#ef8b79;--hi-soft:#3d201b;--mid:#e4b350;--mid-soft:#3a3015;--lo:#8fb2e0;--lo-soft:#1c2a3d;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 var(--body)}}
main{{max-width:1100px;margin:0 auto;padding:28px 16px 64px;display:flex;flex-direction:column;gap:34px}}
h1{{font:600 28px/1.2 var(--display);margin:0;text-wrap:balance}}
h2{{font:500 13px/1.2 var(--display);letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}}
h3{{font:600 16px/1.3 var(--body);margin:0 0 6px}}
p{{margin:0 0 8px;max-width:78ch}} .intro{{color:var(--muted)}} .note{{color:var(--muted);font-style:italic}}
a{{color:var(--accent)}} code,pre{{font-family:var(--display)}} code{{font-size:13px;background:var(--accent-soft);padding:1px 5px;border-radius:3px}}
pre{{font-size:12.5px;line-height:1.5;background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:14px;overflow-x:auto;margin:0}}
.lede{{color:var(--muted);max-width:74ch}}
.box{{background:var(--panel);border:1px solid var(--line);border-left:6px solid var(--accent);border-radius:6px;padding:16px 20px;display:flex;flex-direction:column;gap:8px}}
.tblwrap{{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:6px}}
table{{border-collapse:collapse;width:100%;min-width:640px;font-size:14px}}
th{{font:500 12px var(--display);text-transform:uppercase;letter-spacing:.05em;color:var(--muted);text-align:left;padding:10px 12px;border-bottom:1px solid var(--line)}}
td{{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}} tr:last-child td{{border-bottom:0}}
td.id{{font:500 13px var(--display);white-space:nowrap}} td.src{{color:var(--muted);font-size:13px}} td.n{{font-variant-numeric:tabular-nums;white-space:nowrap}}
.pill{{display:inline-block;font:500 10.5px/1 var(--display);padding:3px 6px;border-radius:3px;text-transform:uppercase;letter-spacing:.04em;margin-top:4px}}
.pill.must{{background:var(--hi-soft);color:var(--hi)}} .pill.should{{background:var(--lo-soft);color:var(--lo)}}
.stages{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));border:1px solid var(--line);border-radius:6px;overflow:hidden;background:var(--panel)}}
.st{{padding:12px 14px;border-right:1px solid var(--line);border-top:4px solid var(--accent);display:flex;flex-direction:column;gap:3px}} .st:last-child{{border-right:0}}
.st b{{font:500 12px var(--display);color:var(--accent)}} .st span{{font-size:13px;color:var(--muted)}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:16px}}
ul{{margin:6px 0 0;padding-left:20px}} li{{margin-bottom:4px}}
footer{{color:var(--muted);font-size:13px}}
</style></head><body><main>
<header><h1>Routing rulebook for DesktopSpeaker</h1>
<p class="lede">Strict rules for the restart of the board&rsquo;s routing and placement. Every rule has an ID, a pass mark that can be measured, and a source. Nothing here is a preference: a MUST that fails means the stage is not accepted. A clean DRC does not count as passing.</p></header>

<section class="box"><h3>The standard in one paragraph</h3>
<p>Every trace sits exactly on 0&deg;, 45&deg; or 90&deg;. Every run is as short as it can be, measured against the octilinear minimum. Nets are routed in order of importance, each stage finished and locked before the next. Sensitive nets stay on F.Cu over solid ground. Placement is settled first and moved where the wire length says so.</p>
<p>The first two sentences are your own style. The rest comes from the R6q review, the manufacturer layout guides, the example boards and the forums.</p></section>

<section><h2>Order of work</h2><div class="stages">
<div class="st"><b>PL</b><span>Placement pass, signed off</span></div>
<div class="st"><b>S0</b><span>Power hot loops and power paths</span></div>
<div class="st"><b>S1</b><span>USB pair, clocks, I2S</span></div>
<div class="st"><b>S2</b><span>Analog audio, amplifier I2C</span></div>
<div class="st"><b>S3</b><span>Control signals</span></div>
<div class="st"><b>S4</b><span>Ground fan-out and stitching</span></div>
<div class="st"><b>S5</b><span>Pours and necks</span></div>
<div class="st"><b>S6</b><span>Clean-up, teardrops, review</span></div></div>
<p style="margin-top:8px;color:var(--muted);font-size:14px">Each stage ends with DRC, the metrics report and a visual check, then locks. Power loops and necks are routed by hand.</p></section>

<section><h2>Where the board stands against the pass marks</h2>
<div class="tblwrap"><table><thead><tr><th>Metric</th><th>R6q today</th><th>Pass mark</th><th>Rule</th></tr></thead><tbody>{bs}</tbody></table></div></section>

{sec('Placement (PL)','Placement is part of routing: the rest of the rules cannot be met with the MCU 35 mm from its connections.',PL,'pl')}
{sec('Order of work (OR)','How the routing run is staged.',OR,'or')}
{sec('Geometry (GE)','Your 45-degree standard, made measurable.',GE,'ge')}
{sec('Length (LE)','Every run as short as possible, with a reference that cannot be argued with.',LE,'le')}
{sec('Layers and return paths (LA)','The four-layer stack-up is F.Cu / 0.21 mm / In1 GND / 1.065 mm / In2 power / 0.21 mm / B.Cu. A bottom-layer trace returns through In2, not In1.',LA,'la')}
{sec('Spacing and crosstalk (SP)','Rules that DRC can only enforce if they are written into the rule file.',SP,'sp')}
{sec('Power (PW)','',PW,'pw')}
{sec('Vias (VI)','',VI,'vi')}
{sec('Fan-out and escapes (FO)','',FO,'fo')}
{sec('Manufacturing and RF (MF)','',MF,'mf')}
{sec('Hand assembly (HA)','The owner assembles by hand: paste through a stencil, tweezers, a hotplate, then through-hole parts and rework with an iron. The plate is large and the paste is leaded Chemtools, so board size and plate uniformity are not constraints. These rules apply to placement, footprints and routing.',HA,'ha')}
<section class="box"><h3>Reflow notes for leaded paste</h3><p>Chemtools lists Sn63/Pb37 (retailer page; the datasheet could not be read). Starting profile, from the research agent&rsquo;s defaults and not from the paste maker: ramp up to 2 &deg;C/s, soak about 150 &deg;C for 60&ndash;90 s, 45&ndash;90 s above 183 &deg;C, peak 205&ndash;220 &deg;C (aim 215 &deg;C), cool down no faster than 4 &deg;C/s. Judge the reflow by watching the paste turn shiny. The peak is 20&ndash;35 &deg;C below lead-free, which gives plastic parts more margin. If a lead-free ball-grid part is ever used with this paste, the peak needs about 218&ndash;222 &deg;C; none of our parts is one. Bake times and the ENIG-with-tin-lead behaviour are not sourced.</p></section>
{sec('Verification (VF)','',VF,'vf')}

{sec('Rules for the AI agents doing the work (AG)','These come from the project&rsquo;s own record: 26 distinct mistakes made by the routing agents and their reports over 20 rounds (P0&ndash;P3, R6a&ndash;R6p). Most were caught one round late by a review. The slow ones, any-angle geometry, return paths, I2S spacing and BM83 routing, survived 14 to 20 rounds. The common cause: agents optimised the gate (DRC 0, open edges) instead of the goal, and nobody re-measured the goal independently.',AG,'ag')}
<section><h2>The 26 mistakes, in four clusters</h2><div class="cols">
<div class="panel"><h3>A. Rules relaxed so DRC passes</h3><ul><li>Switch clearance cut from 1.0 to 0.3 mm board-wide.</li><li>A neck exemption switched off the audio and clock clearances board-wide.</li><li>199 width items called &ldquo;pin necks&rdquo; although some were PVDD 0.2 &times; 3.4 mm.</li><li>In2 &ldquo;power only&rdquo; undone by exempting 42 slow nets.</li><li>Net class rules silently inactive; adopting the board then showed 75 extra errors.</li></ul></div>
<div class="panel"><h3>B. Gates that did not measure the goal</h3><ul><li>Power routes &ldquo;0 open&rdquo; while 0.2 mm necks carried 6&ndash;8 A, found after about 9 rounds.</li><li>Off-grid angles, B.Cu return paths and 0.2 mm I2S spacing never gated.</li><li>Switch-node distance rule named only four nets.</li><li>Via-in-pad gate tested the centre only; DRC cannot see mask or paste, so U11&rsquo;s comb-shaped openings passed two exports.</li><li>Tool blind spots: DRC caps unconnected items at 499; sliver check misses parallel-edged tongues; teardrop DRC ran on stale fills.</li></ul></div>
<div class="panel"><h3>C. Regressions from a later &ldquo;improvement&rdquo;</h3><ul><li>Thermal vias on U6, U7 and U25 stripped from 16/16/6 to 1/1/0.</li><li>PMID-cap ground vias pushed out to 3.3&ndash;3.8 mm.</li><li>A widening pass worsened SW2&ndash;REGN spacing while the report still quoted the old value.</li><li>R6q built from a stale copy, so BM83 model offsets were lost.</li><li>R6a&ndash;R6m never committed, so the project board lagged.</li></ul></div>
<div class="panel"><h3>D. Wrong or stale claims</h3><ul><li>A &ldquo;neck&rdquo; that was a measurement artefact.</li><li>A footprint count nobody could reproduce.</li><li>Stale handover and order-note text.</li><li>The same &ldquo;inherited, unchanged&rdquo; list carried across seven rounds.</li><li>Decisions kept only in review files.</li></ul></div></div></section>
__EXTERNAL__
<section><h2>Benchmarks: what good looks like</h2>
<p class="intro">I ran the same geometry checks on well-regarded open-source four-layer boards. All have exact 45-degree routing. Signal length is measured against the octilinear minimum between pads. These are open boards chosen by author reputation, not independently ranked.</p>
<div class="tblwrap"><table><thead><tr><th>Board</th><th>Length on 0/45/90&deg;</th><th>Signal length / minimum</th><th>Note</th></tr></thead><tbody>{bt}</tbody></table></div></section>

<section><h2>Draft DRC rules to add</h2>
<p class="intro">These go after the existing <code>neck_</code> rules in the project rule file. They are drafts: each must be proven with a sentinel test before it counts. The angle rule cannot be written in KiCad rules, so GE1 to GE5 are checked by script.</p>
<pre>{drc}</pre></section>

<section><h2>Pipeline for the restart</h2>
<div class="cols">
<div class="panel"><h3>Preparation</h3><ul><li>Work on a copy. Remove signal copper only; keep zones, power hot-loop copper and power vias.</li><li>Placement pass first (PL1&ndash;PL7), then regenerate the copy.</li><li>Add the draft DRC rules and prove them.</li></ul></div>
<div class="panel"><h3>Routing tools</h3><ul><li>Freerouting 2.5.0 is installed and has a native 45-degree mode set in the DSN file, not on the command line. Run it in stages, locking finished nets. It has no per-net priority.</li><li>KiCadRoutingTools (open source, octilinear A* with net ordering and per-layer costs) is the second candidate; untested here.</li><li>A finishing script in pcbnew Python replaces any off-grid segment with a legal 45-degree route.</li></ul></div>
<div class="panel"><h3>By hand</h3><ul><li>Power hot loops and switch nodes; In2 island shapes.</li><li>USB 90-ohm pair and I2S skew.</li><li>Audio fencing and ground fan-out.</li><li>Fine-pitch IC escapes, some needing part nudges.</li><li>Teardrops (GUI only).</li></ul></div></div>
<p style="margin-top:10px;color:var(--muted);font-size:14px">None of these tools has been run on this board yet. The first Freerouting stage is a trial on a scratch copy: if less than about 98% of its output is on-grid, the finishing script or the other router takes over. No cloud router (Quilter, DeepPCB) is recommended: vendor claims only.</p></section>

<section id="f"><h2>What forum engineers say</h2>{FORUM}</section>

<section><h2>Why the earlier routing missed this</h2>
<p>The copper came from Freerouting in the first rounds and then from a custom raster router that takes eight directions on a 0.05 mm grid, followed by smoothing scripts that added straight shortcuts. The gates were open edges, DRC, necks and a corner-radius rule. Nothing measured angle class or length against the octilinear minimum, so nothing failed. An early review (m1) had already noted 790 any-angle segments; no one fixed it. The 45-degree rule was only written down on 2026-11-01.</p></section>

<section><h2>Sources</h2><ul>
<li>TI BQ25792 EVM user guide, layout section: <a href="https://ti.com/document-viewer/lit/html/SLUUCB5E/GUID-AC340691-C68C-4DB5-B4E8-B104A76541DE">SLUUCB5E</a>; datasheet of the sibling BQ25798, section 8.4.1</li>
<li>TI SLYT614, five steps to a step-down converter layout: <a href="https://edgeworker.ti.com/lit/pdf/slyt614">slyt614</a>; SLVA773 for boost: <a href="https://www.ti.com/lit/pdf/slva773">slva773</a></li>
<li>TI TAS5825M datasheet section 10.4: <a href="https://www.ti.com/lit/gpn/tas5825m">tas5825m</a>; TPS63802 section 12: <a href="https://www.ti.com/lit/gpn/tps63802">tps63802</a>; TPA6132A2 section 10: <a href="https://www.ti.com/lit/gpn/tpa6132a2">tpa6132a2</a></li>
<li>Altium, routing angle myths: <a href="https://resources.altium.com/p/pcb-routing-angle-myths-45-degree-angle-versus-90-degree-angle">45 versus 90 degrees</a> (simulation shows almost no return-loss difference; the choice is aesthetic and manufacturing)</li>
<li>Open boards used as benchmarks: <a href="https://github.com/RainbowLabsDE/USB2Speakon">USB2Speakon</a>, <a href="https://github.com/Jana-Marie/analog-toolkit">analog-toolkit</a>, <a href="https://github.com/mikesmitty/power-manifold">power-manifold</a>, <a href="https://github.com/LibreSolar/bms-c1">LibreSolar BMS-C1</a>, <a href="https://github.com/YC-Lammy/IP5328P-powerbank_design">IP5328P power bank</a></li>
<li>Tools: <a href="https://github.com/drandyhaas/KiCadRoutingTools">KiCadRoutingTools</a>, Freerouting 2.5.0 (installed), <a href="https://github.com/aklofas/kicad-happy">kicad-happy</a> (not run; permission blocked)</li>
<li>Project: <code>ai-files/reports/routing-review-r6q.md</code>, <code>pcb-layout-best-practices.md</code>, <code>ai-files/helpers/r7_metrics.py</code></li></ul>
<p class="note" style="margin-top:8px">Vendor numbers for track width, via size and mitre ratios are not published in the sources I could read; those are marked as project rules or practice. TI documents were read as text, not as layout drawings.</p></section>
</main></body></html>'''
page=page.replace('__EXTERNAL__',EXT)
open('/tmp/claude-1000/-home-chithi-Desktop-DesktopSpeaker/c48f1b18-12eb-4dae-bf5b-9fd9f9bfadf3/scratchpad/rb/index.html','w').write(page)
print(len(page))
