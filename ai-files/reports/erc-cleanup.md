# ERC cleanup (2026-10-09)

KiCad 10.0.6 (Flatpak `org.kicad.KiCad` kicad-cli). These are schematic-only changes and the netlist does not change. PCB files and `ai-files/pcb/work-r6` were not touched. Not committed.

## Result

| | Before | After |
|---|---|---|
| ERC, default severities | 19 (18 `endpoint_off_grid` warnings, 1 `power_pin_not_driven` error) | **0** |
| ERC, `--severity-all` | 19 | 1 listed as `excluded: true` with a comment (U11 pin 38) |
| Netlist (`kicadxml`) | baseline | identical: 348 components, 311 nets, 1130 pin-to-net entries, 45 libparts. The raw XML only differs in `<date>`/`<tool>` |

Evidence is in `reports/erc-cleanup/`: `erc-before.json`, `erc-after.json`, `netlist-before.xml`, `netlist-after.xml`, `netlist-compare.json` (produced by `helpers/netlist_equiv.py`, which compares refs, values, footprints, all fields, net membership with pin types, pin-to-net mapping and libpart pin tables), and before/after crops `j1-*.png` and `usba-*.png`.

## (a) endpoint_off_grid (18)

- **Cause, root sheet (15 flags):** the J1 `TYPE-C-31-M-12` instance origin was at y 248.75 mm. The symbol's pin offsets are all multiples of 1.27 mm, so every pin landed 0.17 mm off grid. The stub label ends at x 40.51 and 76.83 were also off grid. The library symbol itself is clean, so it was not edited.
- **Fix, root sheet:** I moved the J1 origin to y 248.92 (+0.17 mm). Its displayed fields, 14 stub wires, 14 labels and 2 SBU no-connect markers moved +0.17 mm in y with it. The label ends moved to x 40.64 (left) and x 76.20 (right), so every stub is now 8.89 mm long. Reference, value and the label text are unchanged.
- **Cause and fix, USB_Audio sheet (3 flags):** three of the flags, which KiCad listed under `/`, are in `USB_Audio.kicad_sch`. The hierarchical labels 5V_CODEC, USB_DN and USB_DP and their wire ends were at x 57.00. I moved them to x 57.15. The port names and the root sheet pins are unchanged.
- **Helper:** `helpers/erc_grid_fix.py` is a one-shot script. It edits only the items it identifies by UUID and refuses to run a second time.
- **Visual check:** I compared the before/after crops. The shift is not visible, nothing overlaps, the wiring is still direct and orthogonal, and the J1 reference/value block is unchanged. The four shield-GND labels on J1 come from earlier work and were left alone: changing them was outside this task.

## (b) power_pin_not_driven: U11 pin 38 VIN_3V3

- **Net:** VIN_LOW contains only U11.38 and R12.1. R12 (100k) goes to GND. This is intended: VIN_3V3 is unused, the core runs from the internal VBUS LDO, and the TI EVM uses the same pull-down (`reports/opus-candidate-review-2026-10-05.md`).
- **Options rejected:**
  - A PWR_FLAG would claim a supply on a net that has none.
  - Changing the pin type would misstate the TPS25730 datasheet, and it would change the libpart pin table in the netlist.
- **Fix:** one ERC marker exclusion, with a comment, in `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pro` (`erc.erc_exclusions`). This is KiCad's own exclusion mechanism. kicad-cli honours it: the marker is reported as excluded with its comment and is no longer counted. The schematic, R12 and every connection are unchanged.
- **Caveat:** the exclusion is keyed to the marker position (184.15, 71.12 mm), the pin UUID and the USB_PD sheet path. If U11 is moved or re-placed, the exclusion no longer matches and the error comes back. In that case, re-exclude it in the ERC dialog.
- **Project file note:** pcbnew rewrites `DesktopSpeaker.kicad_pro` when it saves. KiCad's project JSON keeps sections it does not own, so the exclusion should survive, but re-run ERC after any pcbnew save of the main project.

## Files

- Changed:
  - `DesktopSpeaker-kicad/DesktopSpeaker.kicad_sch`
  - `DesktopSpeaker-kicad/USB_Audio.kicad_sch`
  - `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pro` (`erc` section added only)
  - `ai-files/DesktopSpeaker-preview.pdf` (refreshed, 12 pages)
  - `plan.md` (ERC line)
  - `ai-files/HANDOVER.md`
- Backups: `ai-files/backups/{DesktopSpeaker.kicad_sch,USB_Audio.kicad_sch,DesktopSpeaker.kicad_pro}.pre-erc`
- New helpers: `ai-files/helpers/erc_grid_fix.py`, `ai-files/helpers/netlist_equiv.py`
