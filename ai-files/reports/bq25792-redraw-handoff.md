# BQ25792 Battery_Charger candidate: readable redraw handoff

2026-10-05. Isolated candidate only; no change to `DesktopSpeaker-kicad/`, root hierarchy or libraries. Nothing committed.

Files: `ai-files/candidates/Battery_Charger.kicad_sch` (regenerated), `ai-files/helpers/build_bq25792_candidate.py` (layout section rewritten), `ai-files/helpers/netgroups_candidate.py` (new, physical pin-group extractor), refreshed `candidates/Battery_Charger-candidate.{pdf,png,net}`.

## Changes
- Whole sheet redrawn from pin coordinates: VBUS rail, PMID and REGN rails across the top; SW1/SW2/L1 and SYS to the right; BAT, ship FET Q103, R112, SW101 and J5 in a row below; host ports and configuration blocks to the left. Wires are orthogonal, 50 mil grid, GND symbols point down, and wired sections carry at most one label (remote sections repeat the label: REGN, BTST1/2, SW1/2, CE_N, PROG, TS_SENSE, ILIM_HIZ, CHG_INT).
- IC text is centred below U4. Passive and transistor text sits to the right (bottom for the horizontal R112/SW100/SW101). Inputs are on the left, outputs on the right.
- Ports: VBUS_PD, CHG_VIO_3V0, CHG_ENABLE, CHG_SYS_ENABLE, CHG_DP_RAW, CHG_DM_RAW (in or bidirectional, left); CHG_SCL and CHG_SDA (bidirectional); SYS_RAW, CHG_INT (out, right); BAT_PACK (bidirectional, right).
- Embedded U4 symbol (sheet cache only; `BQ25792RQMR.kicad_sym` file untouched) regrouped: host pins left (D+, D-, SCL, SDA, CE, TS, ILIM_HIZ, PROG, INT, QON), power/switch pins right, GND/ACDRV1/ACDRV2 on the bottom, and BATP moved below SDRV. Datasheet pin names and numbers retained (the earlier abbreviated HIZ/ILIM, ACD1, ACD2 names were reverted).
- Ship FET Q103 (CSD17579Q3A) is vertically mirrored. BAT goes straight to its source, SDRV straight to its gate, and its drain is the BAT_PACK node. R112 (100R) feeds BATP from that pack-side node, as in TI Fig. 9-14.
- Default-off gating kept: Q101 clamps ILIM_HIZ low (R110 pulls its gate to REGN, Q102 releases it, R111 holds Q102 off). Q100/R103/R107 keep CE high (charge off) unless CHG_ENABLE is driven high.
- R102 text/metadata is 4.7k with `RC0603FR-074K7L`, LCSC C99782.

## Connectivity proof
Baseline netlist taken from the pre-edit sheet (`kicad-cli sch export netlist`), compared as sets of (reference, physical pin) groups with net names ignored and power symbols excluded. The nets below were unchanged: ILIM_HIZ (Q101.3 R108.2 R109.1 U4.17), Q101 gate (Q101.1 Q102.3 R110.2), CHG_ENABLE, CHG_SYS_ENABLE, CHG_INT (R106.2 U4.21), BTST1/2, SW1/2, PMID, SDA/SCL/D+/D-, QON (SW100.1 kept on QON by rotating the switch rather than swapping pins), and GND with all ACDRV and ground pins.

The pre-edit draft sheet, as saved, contained wiring merges that contradict its own build-script intent. All differences are therefore FLAGGED corrections, not silent ones:
1. PROG (U4.20, R102.1) was merged into REGN. It is now its own net, with R102.2 to GND.
2. TS (U4.16, R100.2, R101.1, J5.2) was merged into BAT_PACK. It is now TS_SENSE alone.
3. BAT (U4.22/23, C106.1, Q103.1-3) was merged into SYS_RAW. It is now BAT_INT, separate from SYS_RAW (C104.1 C105.1 C107.1 U4.25).
4. SW101.1 and SW101.2 were shorted (both on BAT_PACK together with J5.1). Now SW101.1 is BAT_PACK (Q103 drain, R112.1, the port) and SW101.2 is PACK_RAW (J5.1).
5. CE_N now includes Q100.3 (the drain was unconnected, so the CE disable did not work). R106.1 has left CE_N and is now CHG_VIO_3V0 (the previously missing port).
6. VAC1/VAC2 (U4.9, U4.8) were left unconnected; they now join VBUS_PD, as TI requires when no ACFETs are fitted.
7. Port types: CHG_DP_RAW and CHG_DM_RAW changed from input to bidirectional (analog I/O pins).

Netlist artifacts: `candidates/Battery_Charger-candidate.net`. The pre-edit baseline is in the session scratchpad only.

## ERC (kicad-cli 10.0.6, `--severity-all`, no suppression): 113 findings
- 59 `lib_symbol_issues` and 33 `footprint_link_issues`: the standalone candidate has no project library tables (inherited; the same libs resolve in the real project).
- 11 `pin_not_connected` hierarchical labels: "cannot be connected to non-existent parent sheet" (inherited, standalone child sheet). These are the 11 ports.
- 5 `isolated_pin_label`: the BTST1/BTST2/SW1/SW2 stubs on the bootstrap caps and the CHG_INT remote stub. These are intentional remote-section labels.
- 4 `power_pin_not_driven`: U4 BATP, BAT and VAC2 (power-input pins on nets with no power-output or flag driver), plus a GND symbol (no PWR_FLAG). These are the usual child-sheet flag findings; they need coordinator decisions, not suppression.
- 1 `pin_not_driven`: SCL (input with no driver on this sheet; the I2C master is the host).
- No wire/endpoint/crossing violations. Render inspected at overview: no nonconnecting crossings, with all junctions at true branches.

## Datasheet pin review (BQ25792 Rev. C): FLAGS, nothing silently fixed
1. SYS: TI recommends 5x10uF plus 0.1uF; the draft has 3x22uF/10V and no 0.1uF at SYS. Check DC-bias effective capacitance, add the 0.1uF, and confirm the 10V rating against the maximum programmed SYS (abs max 23V).
2. BAT: TI recommends 2x10uF; the draft has one 22uF/10V (C106). Verify effective capacitance; the optional 47nF at BATP is not fitted.
3. VBUS/VAC: TI marks 2.2uF plus 0.1uF at VAC as recommended when hot-plugging adapters above 15V. VAC1/2 are tied straight to VBUS with no local bypass. A 20V PD source's ringing and PMID/VBUS 10uF/50V DC-bias loss are open (also per the `5-20v-charger-selection` report).
4. SDRV/ship FET: orientation is source = BAT, drain = pack (body diode blocks pack to SYS when off), and the charger quiescent supply reaches it via BATP (the datasheet quotes IQ at BATP). SDRV-BAT abs max is 6V and gate drive is only 100nA typical, so turn-on is slow and gate leakage matters. **SFET_PRESENT** (REG14[7]) powers up as 0 and locks SDRV_CTRL, EN_BATOC and FORCE_SFET_OFF. The datasheet does not say whether SDRV already drives the FET on at 0. On a pack-only cold start Q103 may stay off, because the body diode does not conduct pack to charger. This must be bench-verified (EVM); firmware must set and read back SFET_PRESENT=1 before ship commands (as in the replacement power-control contract).
5. ILIM_HIZ: a pin voltage below 0.75V at POR is cached as the 100mA clamp, and the 180k/100k divider only means about 1A if sampled while REGN is valid. Releasing Q101 does not re-sample, so firmware must clear EN_EXTILIM (see `bq25792-ilim-startup-review`). The divider is not an assured hardware ceiling.
6. PROG: 4.7k to GND selects 1S/750kHz, consistent with L1 2.2uH. The R102 tolerance must be 1% or 2% (RC0603FR is 1%). L1 envelope concerns remain (`bq25792-l1-envelope`: 6A Irms, ripple at 21V).
7. TS: 5.23k/30.1k with the pack's 10k NTC across R101 is within about 0.2% of TI's 5.24k/30.31k. TS must never float; if the pack NTC is absent, TS reads about 30k (cold side) and charging is suspended, which is safe.
8. CE: R103 pulls CE to REGN and Q100 pulls it low. TI says CE must not float; REGN is absent only when neither VBUS nor BAT is present (the charger is off then). The Q100/Q102 gates are driven from the 3.0V logic domain, so check 2N7002 Vgs(th) (max 2.5V) margin and Rds(on) at 3.0V.
9. INT and SCL/SDA: INT has a 10k pull-up to CHG_VIO_3V0. TI wants 10k pull-ups on SCL/SDA to the logic rail; none are on this sheet, so the host must supply them. D+/D- (abs max 6V) go raw to ports with no series or ESD protection here.
10. STAT is left unconnected (open drain, usable with DIS_STAT). Allowed, but no hardware charge-status indicator.
11. QON: SW100 to GND, internal pull-up; typical wake 1s. No external ESD or pull-up.
12. Rating spot-checks (OK): BTST caps 50V against a 6V max; REGN caps 10V; ACDRV1/2 tied to GND (allowed when no ACFET); VAC tied to VBUS (allowed).

## Open items you asked about
- **R102 4.7k vs 220R:** the candidate sheet carries 4.7k with RC0603FR-074K7L / C99782, but `ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv/.xlsx` still has R102 "Charger 220R ILIM resistor", RC0603FR-07220RL, C107696, and the active `DesktopSpeaker-kicad/Battery_Charger.kicad_sch` R102 still has the same MPN/LCSC. The mismatch persists until the BOM and the active sheet are integrated (outside my ownership). The BOM also still lists U4 BQ25895, C100 2.2uF/25V and C101/C108 22uF/25V where the candidate uses 10uF/50V. Candidate metadata is partial: the 0.1uF C113/C114 and 47nF C103/C110 have MPNs, and the ship FET Q103 shows C97376 (verify stock).
- **SFET_PRESENT:** not settable in hardware, so firmware only; flag 4 above and the startup note on the sheet.

## Unresolved
- Candidate U4 symbol cache differs from `candidates/BQ25792RQMR.kicad_sym` (layout only); decide whether to regenerate that library file from the cached layout.
- Stock/price for several selected parts is unverified; the BOM subtotal is partial.
- Preview PDF `ai-files/DesktopSpeaker-preview.pdf` was not refreshed (this is a candidate sheet).
- Root sheet pins for CHG_SYS_ENABLE, CHG_DP_RAW and CHG_DM_RAW do not exist yet; the integrator must add them.
