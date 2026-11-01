# Hand assembly rules: stencil, hotplate reflow (leaded paste), DFA

Scope: DesktopSpeaker 127 x 138 mm, 4 layer, ENIG, all SMD top side, hand-printed stencil, tweezers, hotplate, iron/hot-air rework.
Owner answers applied: hotplate is very large (board size/plate uniformity not a concern, not researched); paste is Chemtools leaded (Altronics H1640 / NC254, "Sn63/Pb37" per retailer; flux type, powder type, melting point and profile are NOT published on the retailer page; TDS is linked but I could not read it).

Tags: CONSENSUS = 3+ independent sources agree. DISPUTED = sources conflict. SINGLE-VOICE = one source. OPINION = my engineering judgement, no source (use as a default, verify).
How I read sources: WebFetch returns a model summary of the page, not the raw page; numbers below are what that summary reported. Items marked (snippet) come only from search-result snippets and I did not open the page.

## What I could not open / verify
- JLCPCB "stencil aperture design 2025" URL (404); the non-2025 URL worked and is used.
- Chip Quik SMD291AX datasheet (403), MG 4860P datasheet, Kester sheets: only search snippets seen.
- Chemtools TDS (not reachable from the retailer page); BM83 datasheet pad dimensions / AN233 (radiolocman page is metadata only; Microchip onlinedocs 404/irrelevant); TAS5825M package addendum stencil/via drawing (only TOC snippets); IPC-7525 / IPC-7351 / IPC-7093 themselves (paywalled; only vendor summaries).
- element14 DIY profile thread (timeout). No Hackaday/EEVblog hotplate thread was reached; hotplate evidence is thin.
- Indium mixed-alloy blog redirected twice, content not returned.

## 1. Stencil

| Rule | Value | Tag | Source |
|---|---|---|---|
| Area ratio (opening area / wall area) | >= 0.66; below ~0.50 unreliable; electropolish ~0.60, nano-coat ~0.55 | CONSENSUS (IPC-7525B) | https://www.jlcpcb.com/blog/stencil-aperture-design-geometry-area-ratio-tips , https://www.lcsc.com/blog/qfn-pcb-layout-guide/ |
| Aspect ratio (width / thickness) | >= 1.5 | CONSENSUS | same |
| Foil thickness, 0.4-0.5 mm pitch | 0.10-0.12 mm (JLC); 0.12-0.15 (LCSC QFN); 0.127 (TI QFN) | DISPUTED (range) | JLC, LCSC, https://www.ti.com/lit/sloa122 |
| Fine pitch definition | <= 0.5 mm | SINGLE-VOICE | JLC |
| Min aperture width: 0.5 mm pitch | 0.24 mm (+0.1 mm length if pad < 1.5 mm) | SINGLE-VOICE | JLC |
| Min aperture width: 0.4 mm pitch QFP/QFN | 0.19 mm (+0.1 mm length) | SINGLE-VOICE | JLC |
| 0402 aperture | 0.26 mm wide, +0.15 mm length | SINGLE-VOICE | JLC |
| 0603 / 0805 | 0.28 / 0.32 mm wide, +0.20 mm length | SINGLE-VOICE | JLC |
| 1206 | 0.5-0.6 mm or 30-35% of pad spacing | SINGLE-VOICE | JLC |
| Hand-printing registration reality | industrial +/-5 um; manual/cheap +/-50 um or worse | SINGLE-VOICE | JLC |
| Paste type | Type 3 or finer for QFN | SINGLE-VOICE (TI) | TI SLOA122 |

My arithmetic (OPINION, check): 0.4 mm pitch QFN pad 0.2 x 0.8 mm, aperture 0.19 x 0.8: at T=0.12 mm area ratio 0.64, aspect 1.58 (marginal); at T=0.10 mm area ratio 0.77, aspect 1.9 (passes). 0805/1206 are happy at 0.10 mm but deposit less paste; leaded paste is forgiving, and hand reflow tolerates small fillets. Recommendation: one 0.10 mm stainless, laser-cut, electropolished (or 0.12 if the 0.4 mm pitch parts are few and are made 1:1 aperture reduced). Check every aperture with the two ratios; do not rely on the fab.

Thermal pads (QFN, TAS5825M, TPS25730D, BQ25792, TPS61088):
- Coverage 50-75% of pad area as separate "window panes": LCSC 50-75% (65-75% when vias are inside, 65% typical for through-vias); JLC 60-75% in 4/6/9 panes; TI "cross-hatching"; one forum summary ~50-70%. CONSENSUS (50-75%).
- Pane pitch 1.0-1.5 mm, web (bridge) >= 0.2-0.3 mm: LCSC (SINGLE-VOICE). IPC paper used 0.38 and 0.51 mm webs (iconnect007 / Lentz; fetched, parameters only, no results).
- Open thermal vias: keep paste off via centres; the panes sit between vias (TI via spacing 1.0 mm, vias <= 0.3 mm). "Window pane printed away from vias" is the method in https://iconnect007.com/article/102307/the-impact-of-via-and-pad-design-on-qfn-assembly/102310/smt (SINGLE-VOICE). Voiding: TI wants < 50%; IPC-A-610 25% max per LCSC (DISPUTED limits, both sourced).
- Fix for the 0.1 mm comb problem (OPINION + above webs): export the paste layer as plain rectangles (no comb/fine-hatch polygons); every web >= 0.25 mm and every pane side >= 0.5 mm (so pane aspect ratio >> 1.5 and area ratio > 0.66); no opening or web narrower than the fab minimum (JLC laser: 0.1 mm absolute floor, which is why the previous 0.1 mm comb is unreliable at 0.1 mm foil). Prefer fewer, larger panes (2x2 or 3x3).
- Large pads (>= 1206, connector tab pads, big power pads): reduce to 80-90% or split into panes (JLC: reduce, split; LCSC window-pane). OPINION for the number.

Alignment for hand printing:
- Fiducials per IPC (as quoted by JLC): 1-3 mm solid copper circle, mask opening 2-3 mm (clearance >= radius, ideally = diameter), 3 global fiducials (lower-left, lower-right, upper-right), local fiducial 1 mm copper near fine pitch QFN/QFP. SINGLE-VOICE (JLC blog). https://jlcpcb.com/blog/the-role-of-fiducials-in-smt-stencil-alignment . These are for pick-and-place cameras; for hand printing they are only visual aids.
- Tooling-hole jig is the real alignment method: SINGLE-VOICE sources (KiKit jig: 3 mm acrylic, 4 pins of 2 mm, 8 M2 screws, board-specific printed alignment pieces https://yaqwsx.github.io/KiKit/v1.3/stencil ; a forum user used Delrin with 2.5 mm pins and 2.6 mm stencil holes, from a search snippet https://forum.kicad.info/t/using-mounting-holes-for-stencil-alignment/39274 , not opened).
- OPINION defaults: 3 non-plated tooling holes 2.5 mm +/-0.05 at board corners (non-collinear, e.g. 3 corners), same pattern in the stencil at 2.6 mm; 3 global 1 mm fiducials at the same corners for visual alignment; no copper or parts within 3 mm of the holes; leave a free side for squeegee sweep; paste a first test print on a spare board and check pad overlap through the openings before the real board. Rough rule from a forum user: if you see the pad edges through the apertures, you are off.

## 2. Footprint and pad design for hand assembly

- Pad extension: signal pad 0.1-0.2 mm beyond package outline for QFN (LCSC, SINGLE-VOICE); IPC-7351 0402 toe 0.15 mm, heel 0.00 (snippet, SINGLE-VOICE). For iron access extend the toe, not the gap between pads (EEVblog/SparkFun posters; CONSENSUS-ish forum opinion). Reference 0402 sizes: Worthington 0.60 x 0.70 mm at 1.00 mm pitch (gap 0.40), no tombstoning reported (SINGLE-VOICE, via Hackaday comments https://hackaday.com/2023/02/01/want-better-0402-reflow-consider-these-footprints ); KiCad default 0.54 x 0.64 at 1.02. KiCad HandSolder variants are known to be inconsistent between versions (https://forum.kicad.info/t/handsoldering-footprints-narrowed/16814 , snippet): audit actual pad numbers, do not trust the name.
- Tombstoning prevention (CONSENSUS across JLC/NextPCB/AllPCB/Altium/Hackaday comments): identical pad size, shape, copper connection on both pads; equal trace width and equal count of vias; no trace under only one end; paste volume equal; thermal relief on any pad connected to a pour; pad keep rounded corners (SINGLE-VOICE). Paste printing quality and reflow ramp matter more than footprint (SINGLE-VOICE comment).
- No via in a passive pad (CONSENSUS). Via at least ~0.3 mm clear of pad edge (OPINION); neck traces out.
- Pour connection numbers (OPINION; sources give no spoke widths): 4 spokes, 0.25-0.3 mm wide, gap 0.25 mm for 0402-0805 pads; thermal pad of QFN: solid connection to the inner plane (TI says no web/spoke in the thermal-via-to-plane link, SINGLE-VOICE). Spokes on hand-soldered THT pads too, but power pins that carry current can be solid.
- Solder mask: NSMD (copper-defined) preferred for signal pads (Hackaday comment, LCSC "mask opening 60-70 um larger", TI uses thermal pad SMD-defined, mask 0.07 mm around QFN finger pads). CONSENSUS for NSMD fine pitch; TI thermal pad is mask-defined (SINGLE-VOICE).
- Mask dam: JLC minimum between pad openings 0.10 mm green/red/yellow/blue/purple at 1 oz; 0.13 black/white; 0.20 at 2 oz; keep 0.09 mm between mask opening and neighbouring trace (https://jlcpcb.com/capabilities/pcb-capabilities , SINGLE-VOICE, current as fetched). On 0.4 mm pitch with ~0.2 mm pads, a 0.06 mm expansion per side leaves 0.08 mm: below 0.10, so either expand 0.04 per side or gang the openings ("slot" mask opening along the row). OPINION. Fully remove mask dams rather than leave slivers.
- Silkscreen (OPINION, no source): pin-1 mark and polarity outside the part courtyard so it stays visible after placement; outline lines clear of pads; text >= 0.8 mm high, 0.15 mm stroke; no silkscreen on pads; refdes visible for hand placing; mark diode/LED cathode, electrolytic/polymer polarity bar, connector pin 1.
- Courtyard / spacing (OPINION): tweezers 0.5-1.0 mm between small parts; 0.25 mm KiCad default courtyard is a minimum; leave >= 1.5 mm around ICs for tweezers/iron tip, 3 mm around a hot-air rework target and clear of plastic parts; no part taller than 3 mm within 3 mm of an 0402; tall parts (polymer cap 10 mm, jacks) kept to board edges/one region so the stencil can lie flat and the iron can reach; orientation: all passives of a kind on 0/90 degrees only, all ICs pin 1 in the same corner where possible, polarity marks all pointing the same way (CONSENSUS practice, unsourced here).

## 3. Hotplate reflow with LEADED paste

Board size and uniformity: owner says not a concern (not researched). Note: all-top-side SMD is required; no bottom-side parts or protruding leads/solder balls on B.Cu (the plate contact must be flat). Thick GND copper pours and inner planes slow and lag heating; measure with a thermocouple on the board (OPINION; sources only say bottom heating is used by IR/hotplate and pour/thermal mass differences cause uneven heating).

Profile (starting point; no Chemtools TDS read, so confirm against the TDS you can request):
| Phase | Leaded Sn63/Pb37 | Lead-free SAC305 (for comparison) |
|---|---|---|
| Liquidus | 183 C | ~217-221 C |
| Ramp | <= 2 C/s (OPINION; JLC vendor 1.5-2.5 C/s, element14 snippet) | same |
| Soak | 150 C (to ~155-183 C) for 60-90 s (Jufeng sheet 155 C preheat, 155-183 soak (snippet); jpralves DIY: ~150 C for ~90 s then ~220 C https://jpralves.net/post/2023/03/09/smd-reflow-hot-plate-new-version.html ) | 150-200 C for 60-90 s (JLC vendor blog snippet) |
| Time above liquidus | 45-90 s (OPINION; one snippet claims >60 s) | 45-90 s |
| Peak (on the board/component) | 205-220 C; aim 215 C. Datasheets quote 220 +/-5 (Jufeng) and 220-225 (LINQALLOY); Chip Quik generic curve peaks 235 (all snippets; upper end is for an oven where top temps lag) | 235-250 C |
| Cooling | <= 4 C/s; slow, on a cool metal plate would shock; lift board off the plate to cool on a heatsink or leave plate off (OPINION) |

Peak numbers are CONSENSUS-ish at 205-225 C; exact TAL and soak are SINGLE-VOICE/OPINION. On a hotplate you heat from below, so the bottom is hotter than the top: watch the paste go shiny (jpralves, JLC "watch the joints"), do not go on a timer alone. Chemtools page: 24 h stencil life, 12-14 h tack (retailer claim); fridge-store, warm 4 h before use (Chip Quik/MG for their pastes, SINGLE-VOICE).

What leaded paste changes (mostly OPINION grounded in melting-point difference):
- Peak is ~20-35 C lower than lead-free. That gives more margin for the polymer cap, plastic connectors, encoder, tact switches, and BM83 (BM83 itself is rated for leaded or lead-free profiles, peak <= 260 C, MSL per AN233 - Microchip soldering page snippet).
- Still do not put these on the plate: polymer cap 8x10 (check its TDS: reflow-rated polymer aluminium parts exist, typically 1-2 reflows, peak 250-260 C, but not a 90 s soak with a bottom-heated plate; Chemi-Con says bottom heating is used to limit stress but larger boards need more heat which can damage caps, SINGLE-VOICE), JST VH and Micro-Fit (nylon/PBT housings, designed for wave/iron, THT anyway), 3.5 mm jacks, rotary encoder, tact switches (many are not reflow-rated; some are only 260 C for 5 s hand-soldering). All of those: solder after reflow by iron, or place after the plate and iron only the pad. If the tact switches / USB-C receptacle are SMT and rated, reflow is fine; otherwise iron. USB-C receptacle: check its TDS for reflow rating; the shell tabs are THT and the plastic is LCP (usually 260 C rated). BM83: reflow with other parts, or drag/iron the castellations; vendor says leaded profile OK.
- Mixing: SnPb paste with SAC (lead-free) BGA balls needs peak >= ~218-222 C for homogeneous alloy; at 210-215 C the SAC balls may not collapse (IPC paper/snippet; peak has the greatest effect, TAL little). The board has QFN/LQFP/SOT/chip parts with matte Sn or NiPdAu finishes, not BGAs, so this does not apply to these finishes: they dissolve into the SnPb joint at 183 C. It does matter for any BGA/ball-grid part. Joint-reliability of mixed alloys is DISPUTED (Pb precipitates vs no effect) but irrelevant for hobby hand assembly. Flux/wetting: a "rework gel / broad process window" paste is advertised for high temps (retailer page, SINGLE-VOICE). Unknown flux type: if it is water-soluble you must wash within hours; if no-clean, leave it (I cannot determine; the retailer says "low clear pin-probe-testable residue").
- ENIG + SnPb: wetting is good; the thin gold (0.05-0.1 um) dissolves into the joint. I found no ENIG-specific source (OPINION). Keep ENIG lead-time storage in mind; do not rework the same pad many times (nickel exposure); gold embrittlement is a concern for >3-4 wt% Au, not for thin ENIG in paste joints (OPINION, standard lore).
- Moisture-sensitive parts: use the label MSL and bake before reflow if the bag was opened (BM83, TAS5825M, QFNs); the sources I opened do not give bake numbers. Common: 125 C 4-24 h (OPINION, not verified here). Leaded paste's lower peak lowers popcorn risk but a hotplate with a rapid ramp still can pop QFNs; keep ramp <= 2 C/s.

## 4. Via rules

- Thermal-pad vias <= 0.3 mm drill, spacing 1.0 mm (TI SLOA122, SINGLE-VOICE; LCSC 0.30-0.33 mm, 1 oz barrel, 9-25 vias, >= 16 for 6x6 mm pad; SINGLE-VOICE; KiCad forum: 0.254 mm hole still pulled solder, 0.3 mm open via ok per one user). So 16 open vias in a TAS5825M pad matches vendor advice if drill <= 0.3 mm.
- Open vs tented/plugged/filled: DISPUTED. TI says "do not cover vias with solder mask, causes excessive voiding", plugging optional but not recommended; LCSC/Freescale AN1902 say plug/tent/fill to stop wicking; filled-capped = IPC Type VII. JLC offers epoxy- or copper-paste-filled-and-capped vias (0.15-0.55 mm drill), tented vias up to 0.5 mm, 0.35 mm clearance from other mask openings (JLC capabilities). Recommendation for hand printing: open on top (TI, so the vias are not tented over the stencil), paste panes between the vias, and tent the vias on B.Cu (GND pour) so no solder protrusion reaches the hotplate surface (OPINION; TI warns protrusions at the back; the iconnect007 study measured it). Do not use via-in-pad for passives/fine-pitch signals at all (CONSENSUS). Via-in-pad thermal pads only on exposed pad.
- Vias near other pads: >= 0.3 mm from pad edge, or tented with mask dam; no via within 0.5 mm of a hand-soldered THT pad's iron contact area unless thermally necked (OPINION). Via 0.15/0.25 mm mini-vias are JLC minimum, 0.2 mm hole preferred.
- X-ray / visual check: TI asks for >= 50% soldered area; target 75% (IPC-A-610 25% void max per LCSC). Hand rework: add paste in the panes, flux, hot air from the top.

## 5. Routing rules affected by hand assembly, and script-checkable DFA

Rules:
- Leave pads symmetrically (same width and direction on both ends of a passive) - CONSENSUS; trace width at pad <= pad width and necked 0.2 mm for the first 0.5 mm.
- No trace between fine-pitch pads, no trace under a pad's body unless covered and symmetric. Fan out QFN pins radially; vias outside the pad ring.
- No tracks/vias under hand-soldered pads or in the iron contact zone; no copper under castellations beyond the pad (BM83 antenna keep-out per datasheet - not read).
- Test points: 1.0-1.5 mm round pads, 2.54 mm grid-ish spacing, >= 2 mm from tall parts, top side, labelled (OPINION).
- Pour connections via spokes (see section 2).
- Reviewer DFA script checks on the .kicad_pcb (all measurable): (1) pad-to-pad mask dam, (2) both pads of each 2-pad passive have equal pad size and equal connected-copper (track width, via count, pour connection kind), (3) any via inside a non-thermal pad, (4) via-to-pad edge distance, (5) all SMD on F.Cu, no B.Cu parts, (6) paste layer apertures: area ratio >= 0.66 and aspect >= 1.5 per aperture at chosen foil, no paste web < 0.25 mm, thermal pad paste coverage 50-75%, (7) courtyard-to-courtyard gaps >= 0.25-1 mm, tall-part vs small-part spacing, (8) silkscreen overlap with pads, pin-1 present, (9) track entering a fine-pitch pad at angle/offset, (10) fiducial/tooling hole count and placement, (11) test point accessibility vs courtyard, (12) refdes uniqueness and orientation consistency, (13) THT parts excluded from the plate flagged DNP-for-reflow with a hand-solder list, (14) bottom-side protrusion (no B.Cu exposed copper on tented vias).

## 6. Part-specific cautions

- BM83 castellated module: reflow with leaded profile allowed, peak <= 260 C (Microchip soldering page snippet, SINGLE-VOICE). I could not obtain pad/castellation dimensions or antenna keepout; take them from the datasheet physical-dimension chapter and AN233. OPINION: paste apertures 1:1 on the outer pad extension, keep paste off the module's ground pad vias; module floats on paste, so use a reduced aperture on the inner thermal/ground pads and check no bridging between castellations (they are 1.0-ish mm pitch but verify). Hand-fix with iron on the edge pads and flux.
- USB-C receptacle: THT shell tabs/ SMT signal pads at 0.5 mm pitch; reflow only if the part is rated; otherwise paste, then place after plate and iron-with-flux (drag soldering). Keep the 0.5 mm row's mask dam and no trace between the pads.
- QFN with thermal pad: panes (50-75%), no via-in-pad on leads; extend pads 0.1-0.2 mm (LCSC); 0.07 mm mask ring (TI). BQ25792 ~0.4-0.45 mm pitch: stencil 0.10 mm, aperture 0.19 mm wide minimum (JLC).
- TAS5825M with 16 open thermal vias: verify package from the TI addendum (I could not fetch it; the search snippets referenced a 32-pin VQFN RHB table and "HTSSOP DAP" naming - confirm which you have). Vias <= 0.3 mm, spacing 1.0 mm (TI); panes between vias; bottom side tented or at least no solder balls; X-ray or inspect side wetting. TAS5825M E2E thread: customers add more vias (https://e2e.ti.com/support/audio-group/audio/f/audio-forum/1583064/tas5825m-thermal-issue).
- Polymer capacitor 8x10: do not reflow unless TDS says reflow-rated; if it is the radial/SMD "hybrid polymer" type, Chemi-Con notes cap stress from board heat (https://www.chemi-con.co.jp/products/relatedfiles/capacitor/catalog/al-solderhybrid-e.pdf , snippet). Place late, solder by iron. Tall: keep > 3 mm from small passives and in a region the stencil does not cover (print before placing it).
- 0.4 mm pitch parts: stencil 0.10 mm, aperture >= 0.19 mm, mask dams 0.10 mm min (fab), local fiducials 1 mm near the part, no vias between pads, drag-solder rework with flux.
