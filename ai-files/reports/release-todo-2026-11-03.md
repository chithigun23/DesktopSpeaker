# Release to-do: RT-14 to JLC order (2026-11-03)

Agent "Draft release package on RT-14". Draft material: `ai-files/fab/draft-rt14/`. Nothing in `DesktopSpeaker-kicad/` was edited. Nothing was committed.

## Status now

- **Board:** `ai-files/pcb/work-route14/RT-14.kicad_pcb`. DRC 0 violations and 12 unconnected. Parity is 243, the inherited set, with 0 new. `lib_footprint_mismatch` is 0. ERC is 240, the inherited set.
- **Draft outputs** (`draft-rt14/out/`, marked DRAFT, not for ordering):
  - gerbers, drills, maps and a zip
  - KiCad and JLC position files
  - BOM, which is byte-for-byte equal to the committed `DesktopSpeaker_JLC_BOM.csv`: 90 lines, 318 placements
  - STEP
  - stencil report
  - hand-assembly sheet
  - `SUMMARY.txt`
- **Gate failures in the draft:** 2, both expected.
  - `drc_unconnected` is 12.
  - `teardrops_current`: the board carries 325 inherited teardrops, but a regeneration gives 1886.
- **CAD v14:** published to the site with the hub title "CAD v14 (RT-14 draft)". Report: `reports/cad-v14-2026-11-03.md`.

## 1. Owner GUI work (KiCad 10.0.7, on a copy of RT-14)

1. **Route the 12 open connections.** Use `reports/routing-rt14.md` section 5, rows 1-12. Each row gives the verified cause and a corridor.
   - Rows 1-4: I2S_BCK x2 and AUD_SDA x2.
   - Row 5: ILIM_HIZ. Re-route the TS_SENSE B section first.
   - Rows 6-9: C204-2, C205-2, USB_AUDIO_L and USB_AUDIO_R. Re-route the AUD_SCL hook first.
   - Rows 10-12: HP_EN, HP_SEL_B and AUX_DET. Move PD_SINK_EN and HP_DET locally first.
   - Rules for all rows: 45-degree steps only. Audio needs 0.3 / 0.5 mm. B.Cu runs only over In2 GND, with a stitch via within 1.5 mm. I2S needs 0.6 mm spacing.
2. **Remove the dead LDO_3V3 stub.** A stale In2 teardrop zone hides it in RT-14. Once the teardrops are regenerated, DRC reports `via_dangling` at (133.85, 38.35).
   - The stub runs from J4-1 (133.5, 42.5) along an In2 track to a via at (133.85, 40.6), then on F.Cu to a via at (133.85, 38.35), where it ends.
   - Fix: delete both vias and the F segment (133.85, 40.6)-(133.85, 38.35). Then shorten the In2 track (133.85, 45.4)-(133.85, 40.6) so it ends at (133.85, 42.5), inside the J4-1 pad.
   - Verified on a copy (`draft-rt14/work/tdtest/jfix.*`): DRC 0 violations, 12 unconnected, 1886 teardrops. The connection to J4-1 is kept.
   - Deleting the whole In2 branch instead disconnects J4-1 (13 unconnected), so do not do that.
3. **Optional cheap quality fixes while in the GUI:** see section 7.
4. **Teardrops.** There are two ways; the headless one is recommended.
   - **Headless (KiCad 10.0.7, verified in this session).** `kicad-cli pcb drc --refill-zones --save-board` regenerates the teardrops of every pad and via whose teardrop property is enabled. The earlier claim that no headless method exists was wrong for 10.0.7. pcbnew Python `ZONE_FILLER` alone does **not** do it.
     - 460 of RT-14's 964 vias were written by the router without a `(teardrops ...)` block, so their teardrops are off. `draft-rt14/scripts/td_enable_vias.py` gives them the block that all 888 vias on the R6q release board had.
     - `regen_final.sh --teardrops` does both steps.
     - Result on RT-14: **1886 teardrop zones** (F 1430, B 288, In2 168), all pad/via type and none track-to-track. The result is deterministic: a re-run gives a byte-identical board. Every pour's fill matches a separate pcbnew refill.
   - **GUI alternative.**
     1. Select all, then open Edit > Edit Teardrops… (KiCad 9/10 name; KiCad 8 called it "Add Teardrops").
     2. Settings, matching the project `.kicad_pro` td_* values and the per-item blocks on the R6q board:
        - Targets: round pads, rectangular pads (PTH and SMD) and vias. Track-to-track off.
        - Best length 50 %, maximum length 1.0 mm on pads and 0.6 mm on vias.
        - Best width 100 %, maximum width 2.0 mm.
        - Curved edges on. Allow two tracks on. Prefer zone connections on. Teardrops on pads inside zones off. Filter ratio 90 %.
        - Apply to all pads and vias.
     3. Fill all zones (B), then run DRC with "Refill all zones" and "Report all errors for tracks". Save.
   - **Expected count:** 1886 on RT-14, plus a few for the new copper in step 1. The old committed board (R6q/R9, `git show HEAD:DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb`) had **1825**. The "371" figure from the brief appears nowhere in the history.
   - The count to compare against is whatever `regen_final.sh` reports as "headless regeneration". The gate `teardrops_current` checks that the board's teardrops equal that regeneration.

## 2. Final regeneration (one command)

```
ai-files/fab/draft-rt14/regen_final.sh FINAL.kicad_pcb ai-files/fab/out-R10 --tag DesktopSpeaker-R10 [--teardrops]
# optional: HA8=<ha8.json from the routing gates> also writes hand-assembly-sheet.md
```

- **What it does:**
  - Makes a work copy beside the pristine project `.kicad_pro`, `proposed-project.kicad_dru`, the schematics and a `kicad-library` symlink.
  - Teardrops: regenerates them (`--teardrops`), or checks the board's own against a regeneration.
  - Refills zones in a separate pcbnew process. If the fill signature changed, it exports the refilled board.
  - Runs DRC with parity. Gates: 0 violations, 0 unconnected, 0 lib mismatch, 0 new parity issues against `parity-baseline.json`.
  - Runs three sentinel DRCs: the rule file is read (81 hits), rule 21 blocks and allows the right nets, and rule 20 clears the SW100 pegs (4 violations without it).
  - Exports gerbers (11 layers), drills and maps, position files, BOM (with diff), ERC and STEP.
  - Runs `fab_check.py`, the stencil check (0.10 mm) and the via-in-pad check, then writes `SHA256SUMS` and `SUMMARY.txt`.
  - Exits 0 only if no gate fails.
- **OUTDIR** must be new or empty.
- **Tested end to end on RT-14:** 58 s, RESULT FAIL.
  - FAIL: `drc_unconnected` 12 and `teardrops_current`.
  - WARN: F.Silkscreen extent (the BM83 outline overhangs by design) and `stencil_thermal_pads`.
  - Everything else PASS. The `--teardrops` run in `draft-rt14/work/regen-td/` shows 325 -> 1886 teardrops and the `via_dangling` from step 1.2.
- **Pass condition:** the final board must give RESULT PASS, apart from WARNs you accept.

## 3. Adoption into `DesktopSpeaker-kicad/` (close KiCad first; a `~DesktopSpeaker.kicad_pro.lck` was present)

```
cd /home/chithi/Desktop/DesktopSpeaker
git switch main && git status --short            # expect only .kicad_prl and unrelated files
cp ai-files/fab/out-R10/board/DesktopSpeaker.kicad_pcb DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb
cp ai-files/fab/draft-rt14/proposed-project.kicad_dru  DesktopSpeaker-kicad/DesktopSpeaker.kicad_dru
cat ai-files/fab/out-R10/checks/kicad_pro-diff.txt   # differences between the GUI-saved .kicad_pro and the project one
# keep DesktopSpeaker-kicad/DesktopSpeaker.kicad_pro unless that diff shows a setting you changed on purpose
ai-files/fab/draft-rt14/regen_final.sh DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb ai-files/fab/out-R10-verify --tag DesktopSpeaker-R10
# must print RESULT PASS and the same board SHA-256 in and out
```

- **Rules file:** `proposed-project.kicad_dru` is the project file plus rules 20 and 21. It is byte-identical to `RT-14.kicad_dru` (SHA-256 c47d6aed…).
- **Cleanup candidate:** rule 11 `in2_power_only` still names `/CHG_INT`. That net no longer exists: patch P1 renamed it PC15_SPARE. Removing the term is harmless, but it was left unchanged here. No other rule names a missing net, area or reference.
- **The RT-14 `.kicad_pro`** is JSON-identical to the project file today.
- **Then update:**
  - `ai-files/fab/ORDER-NOTES.md`:
    - 964 vias, 91 + 8 holes of 0.2 mm (R9 had 42 fine vias)
    - PTH 1034, NPTH 24
    - CPL 345 rows (318 BOM + 27 TP)
  - `bom/jlc-assembly-notes.md`: CPL 345.
  - Replace `fab/out` (R9).
  - The handover RT-14 entry, the plan, and `DesktopSpeaker-preview.pdf`.

## 4. Commit (owner asked for checkpoints; do not force-push)

1. `git add`:
   - `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb` and `DesktopSpeaker.kicad_dru`
   - `ai-files/fab/out-R10/` (without `work/`)
   - `ai-files/fab/draft-rt14/` (scripts, `regen_final.sh`, `proposed-project.kicad_dru`, `parity-baseline.json`, `hand-assembly-sheet.md`, `stencil-report-RT14.md`; not `work/` or `out/work/`)
   - `ai-files/reports/release-todo-2026-11-03.md` and `cad-v14-2026-11-03.md`
   - `ai-files/cad/v14/`, except `web-staging/` (about 100 MB of copies, not git-ignored) and `work/`
   - the site `cad/meta.json`, `cad/cad_status.json` and `renders/` (the GLBs and downloads are git-ignored)
   - `HANDOVER.md` and `plan.md`
2. Review `git diff --cached --stat`. Commit with a message such as "R10 release: RT-14 + GUI routing, teardrops, project rules 20/21, fab outputs" and push.
3. Leave out `ai-files/pcb/work-route14/` trial boards (0.33 GB), `work-cad14/` (80 MB) and `draft-rt14/work/`.

## 5. Open design decisions (owner)

1. **Battery pack:** 2P (current CAD), 3P or 4P. See `reports/battery-4p-feasibility-2026-11-03.md`: 4P is feasible with a shell cradle change only and no board change. CAD v14 is the 2P design. Also choose the PCM spec: the 8 A+ limits, the NTC, and the pack quote (`reports/battery-pack-rfq.md`).
2. **Woofer:** calliper the Tang Band W3-2052SC (frame, gasket, holes, depth) before printing. M3x20 gives only 3.4-4.4 mm of thread; consider M3x22. A PH-to-VH adapter lead is needed for J11.
3. **SW100 lid plunger:** the actuator now ends at the board edge. It is 0.50 mm short of the lid inner face and 4.50 mm behind the outer face, and the switch body is 1.35 mm from the lid (CAD v14). Approve a printed plunger (4.5 mm bridge plus a collar pocket in the lid), and confirm the switch travel; the TE drawing gives no travel figure.
4. **Placeholders:** knob, rubber feet, gaskets and grommet.
5. **TP20 relocation** (40.8 mm): fine in CAD (≥ 8.5 mm to every enclosure body). Coordinator confirmation is still pending.

## 6. Hand-assembly and JLC notes

- **Placement order:** `draft-rt14/hand-assembly-sheet.md`.
  - **C215 and C212 go first** (courtyard gap 0.14 mm), before U24 and Y200.
  - Then the fine-pitch and exposed-pad ICs, 0402s, 0805/1206s and low discretes.
  - Medium-height parts next, and the tall SMD last: J1, SW100, L1, L201-L206, L200, C275 (7.7 mm).
  - THT parts are soldered by iron afterwards, low to tall (SW102 last).
  - The sheet lists 40 courtyard pairs under 0.20 mm.
- **Stencil (0.10 mm, electropolished):** `draft-rt14/stencil-report-RT14.md`.
  - All 1085 apertures pass area ratio 0.66 and aspect 1.5. The worst are the U11 0.20 x 0.55 mm openings at area ratio 0.76.
  - **10 of 11 exposed pads break the HA windowing rules:**
    - U6.33 and U7.33: 100 % paste over 16 open vias each.
    - U25.21: 100 % over 8 vias.
    - U1.56, U10.17 and U5.9: 100 %.
    - D6.7: 87 %, web 0.20 mm.
    - Q103.9: 76 %, web 0.20 mm, panes 0.30 mm.
    - U11.39: web 0.20 mm.
    - U11.40: 79 %, web 0.21 mm.
    - Only U19.9 passes.
  - Fix: paste-only footprint edits (window panes 50-75 %, webs ≥ 0.25 mm, panes ≥ 0.5 mm, paste kept off the vias). They change no copper, so they can be made before `regen_final.sh`. Alternatively, mask the apertures with Kapton when printing.
- **SW100 pads:** the TE land pattern leaves 0.075 mm between the peg holes and the lands (rule 20), so JLC may nick the pad corners. Option: trim the outer pads to 0.65 mm, which gives 0.175 mm.
- **Via in pad:** via centres sit inside C215.1 and R185.2. Hole within 0.15 mm of a same-net pad: U16.4 and C274.1 (touching), plus R209.1, U2.10, U4.10, C102.1, C130.2 and R153.2. Inspect these joints, or move the vias 0.2-0.3 mm in the GUI.
- **JLC:**
  - Zero stock on U1 (BM83), U2 (PCM2902) and U19 is **not a blocker** for hand assembly; buy from any distributor.
  - On the order form, choose the 0.2 mm via-hole option, ENIG, 4 layers JLC04161H-7628, 1.6 mm, tented vias, and "Remove mark" or "Order number".
  - CPL: 345 rows. SW101 (panel, wire pads), R256 (DNP), J7, H*, and LOGO1 are excluded. The 27 TP rows have no BOM line.
  - Check rotations in the JLC preview only if you use JLC assembly.

## 7. Known routing quality exceptions (RT-14 final numbers; accept or fix each)

Sources: `work-route14/t/RT-14.r7.json`, `.par.json`, `.check.json` and `routing-rt14.md`.

| # | item | number | limit / standard | note |
|---|---|---|---|---|
| 1 | B.Cu over In2 void | 284.5 mm | ≤ 285 (slow nets only) | sensitive nets add 0 mm in RT-13/14; sensitive B over void still totals 29.5 mm (12 nets, each ≤ 4.6 mm: VMID_HP 4.6, HP_OUTL 3.6, BT_AUDIO_R 3.4, …) |
| 2 | slow-net pairs < 0.4 mm for ≥ 3 mm | 11 pairs | 0.4 mm | worst: CTRL_SCL/SDA 0.20 (U4 neck), QON/NRST In2 0.203 over 6.9 mm, SWCLK/SWDIO 0.215, 3V_AO/HP_DET 0.248, QON/AMP_PDN 0.279 over 6.0 mm; sensitive pair: USB_DN/DP 0.15 (intended diff pair) |
| 3 | stitch via > 1.5 mm from a sensitive via | AUX_L 2.77 mm (190.59, 38.48); USB_DP 1.86 mm | 1.5 mm | no legal site found for AUX_L |
| 4 | audio length ratio | HP_R 1.83 (13.7 mm) | 1.5 x + 1 mm | U2-VCOM 4.57 (9.1 mm), U1-AOHPR 1.89 |
| 5 | ADC_INT length | 35.6 mm | 34.1 mm sense limit | move TP26 about 2 mm |
| 6 | USB_CC2 vias | 8 vias, 56.3 mm | - | |
| 7 | ILIM_HIZ to SW2 | 1.23 mm (F.Cu) | 1.0 mm switch rule met | the 0.36 mm figure was RT-5; final ILIM_HIZ copper comes with row 5; check the input-current-limit readback at bring-up |
| 8 | long analogue / control lines | U11-ADC4 2.22x, U14-FB 2.33x (1.16 mm from U14-L2), CE_N 2.95x, U11-FAULT 2.89x, QON 1.75x (199 mm, 12 vias) | - | |
| 9 | inherited non-octilinear power copper | about 295 mm of segments ≥ 5 mm off the 0/45/90 grid (112 mm 0.6-5°, 81 mm 5-15°, 102 mm 15-22.5°); 20 joints < 80° (7 < 30°: BAT_PACK In2 1° at (104.55, 89.15), 3V3_AUDIO In2 9° at (174.2, 59.1), 5V_LOGIC 16°, GND, LDO_3V3, 5V_CODEC …) | exact 0/45/90, no sharp joints | all on power nets in pre-restart copper; the router's 140 nets are 100 % exact |
| 10 | dangling route ends | 63 (route_oct_check), T-junctions 25 | - | cosmetic; one real dead stub (LDO_3V3, step 1.2) |
| 11 | HA8 courtyard pairs | 121 failing | rulebook HA8 | 40 under 0.20 mm, listed in the hand-assembly sheet |
| 12 | BM83 F.Cu inside the module outline | BT_SYS_CFG 0.28 mm; 2 GND vias | - | antenna keep-out DRC 0 |
| 13 | BAT_INT 6 A path | 17.3 mV / 104 mW | - | unchanged since RT-12 |

## 8. Draft files

`ai-files/fab/draft-rt14/`:

- **Entry point:** `regen_final.sh`.
- **Rules and baseline:** `proposed-project.kicad_dru`, `parity-baseline.json`.
- **Owner documents:** `hand-assembly-sheet.md`, `stencil-report-RT14.md`.
- **Scripts in `scripts/`:**
  - `regen_checks.py`: gates and sentinels.
  - `td_enable_vias.py`
  - `fillsig.py`
  - `fpdump.py`
  - `paste_dump.py`
  - `stencil_check.py`
  - `via_in_pad.py`
  - `make_ha_sheet.py`
- **Draft run:** `out/`, DRAFT-RT14. `out/SUMMARY.txt` lists every gate.
- **Scratch:** `work/` holds the parity run, the teardrop experiments and an older draft run; do not commit it.
