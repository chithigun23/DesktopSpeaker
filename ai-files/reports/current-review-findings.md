# Desktop Speaker review findings

2026-10-05. Main integration review with an independent gpt-6-luna power review. Active schematic/library/BOM files were not changed. Preview refreshed using installed KiCad10.0.6. All six pages inspected; fresh physical netlist and full ERC exported. No PCB or physical measurements.

## Resolution status after integration (2026-10-05)

The findings below describe the original review baseline. Later fixes supersede those circuit and BOM snapshots.

| Finding | Current status |
| --- | --- |
| Source permission | User chose automatic detection. Hardware startup, source controls and suspend budget remain open. |
| Codec supply | U14 replaced with TPS63802; steady PWM DC bound 4.600–5.059 V. Startup, ripple and load transients remain open. |
| Libraries | Both incompatible headers corrected; CLI symbol exports succeed. |
| Electrical roles | BQ/MAX roles and common-pad stacks corrected; actual source flags added. Captured power sheets have zero ERC findings. |
| Higher input voltage | D9 clamps the sense node after R4; new U19 40 V-input LDO feeds PD VDD. Raw VBUS is no longer directly on U11 VDD. Dynamic clamp, surge and downstream BQ margin still need qualification. |
| 5 V losses | Lower-loss LTC4368/NFET main path remains a candidate. Existing eFuse losses remain active. |
| Pack/storage | Protected 1S ~10 Ah target confirmed; dimensional/acoustic constraints lead. QON momentary candidate sourced, disconnect rating/pack NTC remain open. |
| Readability | C10/C180 text corrected; new LDO block below controller clear of service wiring. Preview rendered and inspected. |

Latest evidence: `vdd-ldo-integration.json`, `vdd-ldo-erc.json`, `codec-rail-dc-review.json`, `bootstrap-integration-review.md`. Current ERC: 319 inherited root findings, zero in each captured power child. U19 brings the physical component count to 103; all 103 references are reconciled against the 72-row BOM, with no MPN/LCSC mismatches.

## Findings in action order

### 1. High: USB source permission is unfinished (known integration gap)

PCM2902C fixed descriptor is bus powered,100mA. BQ reset500mA and hardware ILIM1.45–1.77A are not a source grant. Charge defaults disabled, regulator enables default low, but source-aware MCU control is not captured. Define host/Type-C/PD/legacy adapter behavior, including reset/suspend, before connecting loads. Automatic legacy detection versus manual known-adapter mode remains unanswered. Review total port draw including circuitry outside BQ's input limit. Evidence: fresh netlist, local PCM2902C descriptor table and BQ datasheet. [TI PCM2902C](https://www.ti.com/lit/ds/symlink/pcm2902c.pdf), [TI BQ25895](https://www.ti.com/lit/ds/symlink/bq25895.pdf).

### 2. High: codec supply upper limit is unqualified (known margin gap)

TPS61023 R140/R141732k/100k yields4.9504V nominal. PCM2902C VBUS operating range4.35–5.25V. PFM feedback table lists585mV min/601mV typical with no maximum; selected1% feedback resistors introduce TCR uncertainty beyond initial tolerance. This does not demonstrate overvoltage, but does not guarantee the allowed range. Select a target/regulator with a defensible full-mode bound before codec capture. Lower target alone must also meet4.35V at lower corners. Evidence: current-TPS61023.txt electrical table, current-PCM2902C.txt recommended conditions, active divider nets. [TPS61023](https://www.ti.com/lit/ds/symlink/tps61023.pdf).

### 3. Medium: two standalone symbol libraries cannot load (confirmed new finding)

Installed CLI cannot load TS5A3167DBVR.kicad_sym and TPS63802DLAR.kicad_sym. Files exist and table paths are correct. Their version headers20251103 and20260306 are incompatible with the installed loader. Diagnostic copies under reports/library-format-diagnostic changing only the header to20231120 export successfully. Root ERC reports four library-not-found warnings for U13/U16/U17/U15. Cached symbols permit rendering/capture, masking this library problem. Normalize these files to the installed supported format and verify library/cached symbol agreement. Do not replace cached pin mappings/positions when fixing. Active originals left unchanged for review.

### 4. Medium: symbol electrical roles weaken ERC (confirmed metadata deficiency)

BQ U4 and gauge U5 pins are Unspecified. This produces29 power-sheet pin-to-pin warnings and fails to describe true power/logic roles for rule checking. Connected sheets also show missing-source annotations for U18IN, U12IN and BAT-powered switches. Assign verified electrical pin types in standalone/cached symbols and annotate genuine sources through switches. Do not suppress warnings or add indiscriminate power flags. These are ERC-model issues, not evidence of a wrong physical net.

### 5. Medium: 20V fault/surge guarantee remains open (known qualification gap)

U18 OVP~11.03V correctly separates the charger from sustained high input; this supersedes the old unprotected-path finding. It does not establish survival of live9→20V edges. Raw TVS2200 maximum28.4V clamp exceeds STUSB4500's28V absolute limit at the rated surge; protected SMA6J10A15.7V clamp at its specified25C surge condition leaves little margin to BQ SW16V absolute. OVP response, inductive overshoot and temperature matter. Review protection coordination/parts to obtain margin before claiming15/20V tolerance; physical qualification follows PCB. [TVS2200](https://www.ti.com/product/TVS2200), [STUSB4500](https://www.st.com/resource/en/datasheet/stusb4500.pdf). This is not a demonstrated normal5/9V failure.

### 6. Medium: ordinary5V full-load headroom/heat is conditional (known budget gap)

Existing illustrative4.75V source,0.20ohm cable,0.295ohm board at1.5A gives4.008V at charger; TPS26600 conduction allowance reaches~0.78W at1.77A. Source management must reduce charge first and load afterward. Battery-absent full loudness cannot be promised. Larger charger capacitors improve typical margin but increase startup demand; C181 ramp arithmetic excludes converter/load dynamics. See5v-input-headroom.md and power-passive-inrush-review.md.

### 7. Medium: pack/temperature/storage targets need closure (known selection gaps)

Only protected1S plus10k sensor is selected, not an actual pack/NTC curve or current capability. TS divider assumes103AT-2. Match sensor curve and hot/cold limits before enabling charge. Select SW101 for actual pack peak/continuous current; SW100 is QON wake, not another power disconnect. Fresh netlist confirms physicalSW101 and charger internalBATFET lie in the battery-to-SYS path.35–37uA is conditional normal inactive current, not ship-off drain. BQ ship-mode/noVBUS/monitor-disabled BAT current is12uA typical/23uA maximum at stated conditions; gauge, switch and pack currents remain additional. Verify transitions/leakage, especially BAT-collapse0–1.65V.

### 8. Low: readability/documentation follow-up

Power row and local REGN cleanup are readable; IC values/references are centered below and passives generally right. USB_PD C10 identifiers remain unusually far from the symbol and the Q2/input-cap ground area has crowded text. Gauge decouplers are remote from switches on the drawing; PCB decoupling must be placed at pins. plan.md still contains older C101-candidate andUS$66.93 cost paragraphs contradicted by its newer status; refresh current paragraphs, retain historical evidence in HANDOVER. No drawing edits made.

## Checks without new defects

- Fresh netlist:15 explicitly reviewed power relations match intended physical nets (current-reviewed-power-nets.json).
-101 real component references all represented by BOM reference rows. Quantities match listed reference groups; populated MPN/LCSC fields agree. No fresh stock recheck performed; prices retain dated snapshots and remain partial.
-99 assigned footprints resolve locally; direct standalone symbol-pin/pad comparison found no missing numbered pads. Every assigned footprint has a resolvable model link (current-library-integrity.json). This checks associations, not every land-pattern dimension. SW100/SW101 are the two unassigned footprints, already open selections.
-Each local symbol file contains one top-level component. Generic chip models/derived eFuse model remain disclosed; resolving a model link does not authenticate its geometry.

## ERC evidence

358 findings:247 errors/111 warnings. Root326 (234 unconnected pins,78 off-grid endpoints,8 dangling labels,4 library warnings,2 undriven BM83 ground pins). Root largely intentionally unfinished. USB_PD1 undriven-power annotation; Battery_Charger21 Unspecified-pin warnings; Fuel_Gauge_Power10 (8 Unspecified-pin warnings,2 undriven-power annotations); Bluetooth_Power0; Logic_Audio_Power0. Zero findings on regulator sheets is not proof of electrical margin. Inherited unconnected audio/MCU findings were not suppressed. current-review-erc.json and current-review-erc-summary.json preserve details.

Independent power findings:current-power-critical-review.md. No newly demonstrated wrong power connection was found. Recommended next work:fix library compatibility and electrical pin types, then close codec rail/source policy before dependent MCU/audio integration.
