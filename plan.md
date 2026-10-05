# Desktop Speaker schematic completion plan

Updated: 2026-10-05. Use this checklist with `AGENTS.md` and `ai-files/HANDOVER.md`. The active KiCad project is the source of truth. Checkboxes indicate completed work; **PARTIAL** sections still have open tasks. Update this file in place as work progresses.

## Product and architecture requirements

- Two front-facing stereo drivers and one downward-facing woofer; front on the enclosure's long side.
- Approximate footprint: two Samsung S22 Ultras; height approximately half a phone length. Size may change to improve acoustics and battery life.
- USB-C audio/power, Bluetooth and 3.5 mm auxiliary input; switched 3.5 mm headphone output.
- Battery operation and operation directly from external power. User now requests actual operation across common 5–20 V USB PD contracts, alongside traditional 5 V / 2 A adapter support. User decided (2026-10-05): support standard 5/9/15/20 V PD only; EPR 28/36/48 V is out of scope. Actual allowed current depends on source/cable capability; fallback to 5 V does not grant 2 A.
- Prioritize battery life, low standby/storage current and battery longevity when usually plugged in.
- Target a protected 1S pack around 10 Ah. Enclosure dimensions and acoustic volume drive selection; weight is not a concern and a heavier enclosure is welcome if acoustics benefit.
- Use automatic USB-A source detection with a conservative fallback; a 2 A label alone does not grant USB host current.
- Custom PCB for internal electronics. No PCB layout is authorized yet.

## 1. USB-C power delivery — PARTIAL

- [x] Add STUSB4500QTR and common-source STL9P3LLH6 reverse-blocking PMOS pair.
- [x] Connect CC/dead-battery pins, reset/address configuration, decoupling, sense/filter, discharge and service I2C header.
- [x] Use standard PMOS graphics, KiCad 10 native pad stacks, explicit grounds and left/right hierarchy ports.
- [x] Review configuration against the ST circuit guidance and preserve physical connectivity through readability edits.
- [x] Compact the controller/support area and review IC text below centered, passive/transistor text right; retain physical connectivity; root ports may move to improve the ordered power row.
- [x] Add D5 ESDA25L CC protection, D6 TVS2200 raw-VBUS TVS and U18 hardware overvoltage cutoff for 5/9 V operation; D1 remains USB data protection. Final transient qualification and NVM programming remain open.
- [x] Select captured power resistor/decoupling MPNs and add eFuse startup ramp C181.
- [ ] Finalize service header, remaining capacitor selections/effective-capacitance proof, and discharge/pulse qualification.
- [ ] Define 5 V fallback and 5–20 V contract/current policy with the charger and total power budget.
- [ ] Redesign charger/protection/sense circuitry for 5–20 V operation, then define/program/read back compatible PDOs. Until that redesign is integrated, the active schematic still requires a 5 V / 9 V-only profile; do not enable 15/20 V against the present 11 V cutoff/BQ25895.
- [x] Connect `VBUS_PD` to the charger; keep it away from 5 V-only audio electronics.
- [ ] Recheck final pin connectivity, hierarchy and applicable ERC findings after system integration.

## 2. Battery charging, external power and protection — PARTIAL

- [x] Create/connect the BQ25895 charger subsystem using its datasheet configuration and decoupling.
- [x] Integrate `VBUS_PD`, `SYS_RAW` and `BAT_PACK`; add default-disabled charge enable through Q100.
- [x] Add the provisional 103AT-2 thermistor divider and three-contact battery interface. Pack protection/current/temperature specifications remain open.
- [ ] Select battery chemistry, cell count/capacity, pack/connector and protection arrangement; confirm charge/discharge current requirements.
- [ ] Add temperature sensing, protection and required charge/power-path support components.
- [ ] Define adapter input-current limits for ordinary USB and negotiated PD, including audio load and charging together.
- [ ] Define firmware charge target, recharge thresholds and plugged-in policy to reduce battery ageing; confirm what the charger actually supports.
- [ ] Confirm direct external-power operation, weak-source behaviour and battery absent/depleted behaviour.
- [ ] Define safe behaviour during overload, thermal faults and source insertion/removal.

## 3. Fuel gauge and low-current power control — PARTIAL

- [x] Connect MAX17048, its decoupling, battery measurement, I2C and alert signal as required by its datasheet.
- [x] Add nominal 3.0 V AO logic rail (TPS7A0230) and three TS5A3167 gauge signal switches for BAT-unpowered/USB-powered operation. Confirm final operating margins, leakage and pack-collapse behavior with the MCU/rail load.
- [x] Connect shared charger/gauge I2C with central AO pull-ups; MCU connections remain in section 4.
- [ ] Set a measured/calculated standby budget covering gauge, MCU, charger, leakage, dividers and disabled rails.
- [ ] Add Bluetooth/audio rail enables or load switches as needed; define awake, idle, sleep and storage states.
- [x] Capture enabled TPS63802 codec rail at nominal4.824V, forced PWM after soft-start, default-off enable and output disconnect; replaces TPS61023 after corner review.
- [x] Capture an enabled TPS63802 3.8 V rail for BM83, with default-off enable and selectable PWM/PFM. Module connections remain in section 6.
- [ ] Finish regulator passive/corner review, source power limits and downstream signal-pin isolation. Bluetooth regulator/inductor footprint and STEP assignments are complete.
- [x] Add TPS2116 USB-priority logic mux between USB_AUX_5V/SYS_RAW and U12; USB-powered logic no longer depends on charger switching. Physical pin connectivity and schematic readability reviewed; MCU startup and switchover qualification remain open.
- [x] Add SW100 QON wake button and SW101 pack-positive physical disconnect to the charger sheet.
- [ ] Finalize both selected storage modes: physical battery disconnect and electronic off with USB/button wake; finalize switch ratings, shutdown sequencing and drain budget.

## 4. MCU, controls and configuration

- [ ] Connect the currently placed STM32G031K8T6 supply/grounds, decoupling, reset/boot and programming/debug interface.
- [ ] Check pin allocation and voltage domains for charger/gauge, PD, amplifiers, Bluetooth and controls.
- [ ] Define buttons, indicators, volume/source control and battery display requirements.
- [ ] Allocate interrupt/enable/mute lines and bus addresses; select pull-ups by bus capacitance and rail state.
- [ ] Document startup/shutdown sequencing, fault handling and external-power charge policy.
- [ ] Resolve any MCU/Bluetooth architecture change explicitly before replacing the currently selected parts.

## 5. USB audio and connector data path

- [ ] Connect PCM2902C supplies/grounds, decoupling, clock and required configuration from its datasheet.
- [ ] Wire USB-C USB 2.0 data contacts correctly and connect D1 data protection.
- [ ] Finalize USB shield/ground arrangement and any required data-path supporting components.
- [ ] Define codec analogue signal levels, coupling/bias and routing into the source-selection path.
- [ ] Check USB data operation under 5 V fallback, PD operation and battery/rail transitions.

## 6. Bluetooth audio

- [ ] Connect the currently selected BM83SM1-00TA module, supplies, decoupling, controls and programming requirements.
- [ ] Choose analogue or digital audio interface and define levels/clocks with the rest of the audio chain.
- [ ] Define power switching, wake/reconnect behaviour and prevention of signal-pin back-powering.
- [ ] Record antenna clearance requirements for later PCB/enclosure work.
- [ ] If revisiting ESP32, explicitly select a device supporting the required Bluetooth audio profile; compare audio capability and power before changing the BOM.

## 7. Source selection and analogue-to-digital conversion

- [ ] Define the complete USB/Bluetooth/auxiliary audio path and switching truth table.
- [ ] Connect/configure TS5A23157 switches only after confirming signal swing, bias, supply and default state.
- [ ] Select an audio ADC or a compatible alternative architecture. TAS5825M requires digital audio; current analogue codec/mux outputs cannot directly drive it.
- [ ] Evaluate PCM1862DBTR as a candidate; finalize channels, gain, input bias/coupling, digital format and clocks.
- [ ] Define source-change mute timing and prevent clicks or simultaneous source contention.
- [ ] Confirm stereo handling, woofer summing and any DSP crossover/equalization architecture.

## 8. Headphone output and auxiliary input

- [ ] Connect switched PJ-307 jacks using verified contact mapping (sleeve 1, ring 2, switched ring 3, switched tip 4, tip 5).
- [ ] Connect TPA6132A2, decoupling/charge-pump components and shutdown control per datasheet.
- [ ] Define headphone source/volume path and supported load range.
- [ ] Define insertion detection and speaker mute behaviour; check how jack switches interact with audio routing.
- [ ] Add appropriate input/output protection, filtering and coupling where required.

## 9. Amplifier supply and three-driver audio output

- [ ] Select the amplifier boost supply. A single-cell battery cannot directly meet TAS5825M power-stage minimum voltage; TPS61088 is only a candidate so far.
- [ ] Define battery versus 5 V / 2 A source power limits, amplifier rail and charging priority.
- [ ] Connect both TAS5825M devices, decoupling, clocks, digital audio, control/address pins and output networks from the datasheet.
- [ ] Allocate channels for front left, front right and woofer; confirm whether woofer channel bridging is supported and appropriate before using it.
- [ ] Select driver impedances/power ratings, crossover/DSP and loudness limits to suit battery life and enclosure volume.
- [ ] Define mute/fault/shutdown sequence and amplifier idle current policy.
- [ ] Add speaker connectors and any required protection/filter components.

## 10. Integration, BOM and schematic review

- [ ] Agree rail names, voltage domains, hierarchical ports, reference ranges and sheet ownership before connecting subsystems.
- [ ] Integrate each subsystem into the root hierarchy; keep direct local wiring and clear functional boundaries.
- [ ] Finalize all remaining parts and passives; distinguish candidates from selected parts.
- [x] Reconcile the LCSC BOM with current captured power parts, quantities and unresolved selections (2026-10-05). Continue updating as open MPNs are selected; current costs are partial subtotals, not complete product cost.
- [ ] Confirm symbol pin-to-footprint mapping and project-relative footprint/3D links for newly added parts.
- [ ] Review the complete schematic against manufacturer datasheets, power budget, signal domains and startup states.
- [ ] When verification is requested, export/inspect all pages, run ERC and reconcile every finding. Current unfinished sections mean the project is not ERC-clean.
- [ ] Record open hardware/firmware assumptions in the single handover. Do not begin PCB layout without a request.

## Schematic style and user feedback

- Use installed KiCad 10.0.6 / 10.0.6-rc2 CLI; never the nightly AppImage.
- Apply `/home/chithi/.codex/skills/kicad-readable-schematics/SKILL.md`.
- IC reference and value: close below the body, horizontally centered. Passive/transistor reference and value: to the right. This replaces the earlier above-body preference.
- Reduce unnecessary whitespace and long local loops within reason; retain functional grouping and enough clearance for text, pins and wires.
- Prefer familiar standard symbols, particularly PMOS transistor graphics. Preserve physical pad mapping; use native KiCad 10 stacks for common pads.
- Connect nearby items with orthogonal wires. Use at most one net label per connected wired section; matching labels on remote sections are permitted when useful.
- Use downward-facing ground symbols even inside subsheets. Keep hierarchy input ports on the left and outputs on the right with correct types; adjust root port positions to align connections and eliminate crossing wires.
- Avoid nonconnecting intersections, ambiguous junctions, text/wire overlaps and labels crossing symbol pins.
- Preserve reference designators and displayed values. Preserve existing user placements unless a requested readability change requires movement.
- One component per symbol file; keep existing schematic/footprint/3D library folders flat. Check downloaded STEP model origin/dimensions before linking.

## Continuation workflow and file locations

- Main chat owns architecture, decisions, shared tables and integration. Use cheaper subagents with compact briefs for bounded subsystem sheets and independent sourcing/library work.
- Give agents exclusive file ownership and agreed interfaces; review each handoff before dependent work. Avoid duplicated research.
- Active project and libraries stay under `DesktopSpeaker-kicad/`. All AI helpers, exports, PDFs, datasheets, BOMs, reports and recovery snapshots go under `ai-files/`.
- `ai-files/HANDOVER.md` is the only handover document. This root `plan.md` is the explicitly requested task checklist, not a second handover.
- Downloads and reversible project edits are authorized. Ask for missing design decisions when needed; do not repeatedly ask permission for downloads.

## Current power implementation and open decisions

The root power row now reads USB_PD → Battery_Charger → Fuel_Gauge_Power, with aligned straight power/bus links. U4/U5 retain their original instance UUIDs, references and values in child sheets. The headphone amp and U6 were moved clear with their displayed values retained.

User selected a protected 1S lithium-ion pack with a 10 kΩ temperature sensor. Exact NTC curve remains to be matched to the TS divider. User selected both a physical battery disconnect and electronic off with USB/button wake. User targets around 10 Ah; maximum charge current, pack geometry and connector mating lead are not finalized. Charging defaults disabled in hardware until firmware programs verified pack/source limits. The REGN/TS example assumes a 103AT-2 10k thermistor; do not use another curve without recalculating.

L1 selected: Bourns SRN6045TA-2R2Y (C1332316), with exact-series installed KiCad footprint/STEP copied locally and dimensions reviewed. Previous FEXU candidate is superseded. PMID C101/C108 use selected Samsung 22uF25V1210 parts in parallel; REGN C102/C109 use selected 10uF10V0805 parts in parallel. Typical maker curves were reviewed; guaranteed effective capacitance and hardware qualification remain open. Most captured power passives now have MPNs; C103 is now selected as Yageo C107093; final headers/switches/pack remain open. Regulated supply children are captured; downstream audio/BT isolation and final storage/wake qualification remain unfinished.

Preliminary battery-only inactive budget, excluding MCU, other rails, signal activity, leakage and pack protection: BQ25895 BATFET-enabled/monitor-off32uA typical + MAX17048 hibernate3–5uA + three TS5A3167 switches0.03uA combined typical + LDO roughly0.025uA, approximately35–37uA before disabled-regulator input current. This is conditional arithmetic, not measured standby or a battery-life guarantee. Ship mode removes SYS/AO but leaves the BAT-powered gauge/switches unless physically disconnected.

## Power policy continuation (2026-10-04)

- Protected 1S pack with temperature sensor is selected by the user. Pack target is around10Ah; exact geometry, continuous/pulse discharge rating, charge current and actual NTC curve remain open; do not assume any generic 10 kΩ NTC is interchangeable with 103AT-2.
- BQ25895 supports SYS operation from external input with charging disabled and battery absent, subject to source and converter limits (datasheet §8.2.6). System voltage is near SYS_MIN for no/depleted battery, not a regulated 5 V audio rail.
- Source policy: start with charging disabled; read detected Type-C current/PD contract, then set IINLIM no higher than source permission and hardware ILIM. Disable AUTO_DPDM/HVDCP/MAXC/ICO for host-controlled limits; reapply after resets/watchdog events. Legacy USB host default current and enumeration rules need a distinct case; the reset 500 mA setting is not universal authorization.
- Existing 220 Ω ILIM hardware clamp spans approximately1.45–1.77 A using datasheet KILIM range, so it deliberately leaves headroom on a 2 A adapter but requires lower software limits for weaker sources. Audio loudness must adapt to this budget; charge current is reduced first. Battery supplement is permitted by the charger and is not battery-independent operation under overload.
- Proposed plugged-in policy (not yet final): charge to a reduced voltage consistent with the selected cell, stop charging at a chosen fuel-gauge threshold, restart with broad hysteresis; offer a deliberate full-charge mode for portable use. Keep CE disabled on unknown pack/NTC/source or temperature/charger faults. Exact thresholds/current await pack selection. No firmware has been implemented.
- APPPD was inspected; CC/VBUS protection is now added as detailed below.

Storage modes selected by user: physical switch in protected-pack positive upstream of BAT_PACK (gauge and isolation included), plus QON momentary button for battery ship-mode wake. NTC and ground remain unswitched. A QON press must satisfy datasheet tSHIPMODE (up to2.25s under specified conditions); holding it for12–18s can reset SYS on battery unless BATFET_RST_EN is disabled. Adapter insertion exits ship mode. Ship mode is not a latch that keeps SYS off while USB power is present: firmware must disable audio/BT rails for plugged-in electronic off. Physical disconnect stops board drain but not the pack protection circuit or cell self-discharge. Exact switch MPNs/footprints and off-button MCU sensing remain open.

Storage hardware update: SW100 connects QON pin12 to GND, and SW101 interrupts only J5 pin1 battery positive before BAT_PACK. Pin-net review confirms J5.1 has only SW101.2, SW101.1 joins the charger/gauge BAT_PACK loads, and J5 NTC/GND are unchanged. Standard switch symbols added; switch footprints and MPNs remain unselected.

Charger sourcing update: L1 uses Bourns SRN6045TA-2R2Y (2.2uH ±30%, 6A rated/9.5A saturation at manufacturer conditions); local exact-series footprint/STEP dimensions match manufacturer body tolerances. C104/C105/C107 now use Murata GRM21BZ71A226ME15L (C907991), 22uF10V0805. Third parallel cap adds margin: representative DC-bias chart at4.5V indicates about65% retained; 3×22×0.65×0.8×0.85≈29.2uF after initial/temp allowances, before ageing and chart uncertainty. Treat typical bias curves as characterization, not a guaranteed corner proof. C101/C108 Samsung CL32B226KAJNNNE C309062 are selected; typical9V bias review is recorded in the handover, with guaranteed effective capacitance still open.

USB protection update: D5 ST ESDA25L protects CC. D6 TI TVS2200 protects raw VBUS, U18 TPS26600 rejects overvoltage before the charger, D7 clamps PMOS gate drive and D8 Taiwan Semiconductor SMA6J10A M2G clamps protected VBUS. Normal charging remains5/9V only. The overvoltage/surge limits and unresolved qualification are recorded below and in the handover; protection capture is not proof of full-rated surge immunity.

## Regulated rail capture (2026-10-04) — PARTIAL

- New children: `Bluetooth_Power.kicad_sch` and `Logic_Audio_Power.kicad_sch`, below the charger/gauge row. SYS_RAW branches use one label per wired section. U7, J1 with its stubs and D1 moved clear; reference/value and previous physical connectivity preserved.
- U14 now TPS63802DLAR (C2845237), replacing TPS61023. MODE tied SYS_RAW selects PWM after soft-start; R142100k default EN-low, L2 CoilcraftXFL4015-471MEC0.47uH shared withL3,22uF+100nF input/two22uF output. R140/R14178.7k/9.1k nominal4.82418V; conservative steady-PWM DC4.60004–5.05869V includes1% reference/resistors,100ppm/C drift100C and100nA FB bias. Startup uses PFM; ripple/overshoot/load/thermal/effective-cap qualification remain open.500mA is a reserve, not current entitlement. Existing exact shared footprint/STEP reused.
- U15 TPS63802DLAR (C2845237): buck-boost from SYS_RAW to nominal 3.8187 V, 604 kΩ / 91 kΩ feedback, EN/MODE each 100 kΩ default-low, 0.47 µH Coilcraft XFL4015-471MEC L3 (C18221164). C150 input 22 µF plus 100 nF; C152–C154 three 22 µF output caps provide DC-bias margin. 100 kΩ output bleeder; PG deliberately NC. BT_FORCE_PWM allows noise comparison during audio; default PFM. Feedback corners plus maximum stated FB bias estimate remain below 4.2 V, but transient regulation/ripple need qualification.
- [x] U15/L3 exact STEP downloads imported from the user, geometry/orientation reviewed, footprints assigned and project-relative model links resolved. TI land-pattern centers corrected and pad 8 paste split to the manufacturer example. See the model-import evidence in the handover.
- BM83 BAT_IN is 3.2–4.2 V; SYS_PWR and VDD_IO are module outputs and must not be fed by these rails. ADAP_IN/internal charger is not used by this power design. Shutdown requires BM83 power-off acknowledgment first, then rail disable; verify the >640 µs supply ramp-down with the actual module load. The bleeder calculation alone is not proof. MCU/module I/O and audio-path back-power prevention remain open.
- Added disabled converter input current is approximately0.1µA (U14) +0.045µA (U15) typical under their specified conditions, giving roughly35.2–37.2µA preliminary battery-only inactive subtotal before MCU, leakage, pack protection and other rails. Ship mode still leaves gauge/isolation powered; physical disconnect is required for the lowest board storage drain. No measured standby result is claimed.
- BOM workbook/CSV reconciled with captured power parts; see the latest dated subtotal below. Older price snapshots remain dated per row. Pack/switch/speakers and unresolved audio parts are excluded; not a complete product cost.

## Critical review follow-up priorities (2026-10-04)

- [x] Capture hardware overvoltage cutoff for accidental 15/20 V contracts: TPS26600 U18, raw TVS2200 D6, gate clamp D7 and protected-side clamp D8. Normal operation remains5/9V; transient qualification is still open.
- [x] Import/review the user-supplied eFuse STEP, retain its original and link a clearly marked derived model with a datasheet-corrected nominal3×3mm exposed pad. The download's PWP0016H pad was undersized for PWP0016A. This is not an authenticated exact manufacturer model.
- [x] Record the first 5V cable-drop/thermal calculation and source-management implications in `ai-files/reports/5v-input-headroom.md`.
- [ ] Finish passive selections, effective capacitance/inrush, final 5V current/thermal qualification and transition/surge qualification. Raw TVS28.4V full-rated clamp exceeds ST28V absolute; no full-rated surge immunity is claimed.
- [x] Replace U13 TMUX1511 with three TS5A3167DBVR switches U13/U16/U17, reducing combined typical switch supply current to about 0.03 µA. Validate powered-off leakage, pack brownout and system standby later.
- MCU/source-state integration and regulator component qualification remain scheduled above; user accepts addressing these as their subsystems progress.
- Distinguish battery-power disconnect (SW101 and charger internal BATFET) from U13 signal isolation. SW100 is a momentary QON wake button, not a second series power switch.

Gauge isolation redesign: U13/U16/U17 each use protected BAT_PACK for VCC and ground for the active-low IN. NC connects gauge SDA/SCL/ALRT and COM connects the AO/control side. Separate 100nF C130–C132 provide decoupling. TS5A3167 supply current at5.5V is10nA typical/1µA maximum per switch; three sum to0.03µA typical/3µA maximum under specified conditions. Preliminary subtotal now about35–37µA typical before MCU, pack protection and other loads; this supersedes prior TMUX1511-based72–74µA arithmetic, not a measured storage result. Powered-off port leakage can reach25µA per port over temperature at0–3.6V (50µA at0–5.5V); BAT absent/USB present and BAT collapse through0–1.65V need qualification.

PD tolerance capture: U18 TPS26600PWPR (C544399) follows Q1/Q2. OVP is about11.03V nominal; normal operation remains5/9V. R180/R181=100k/12.1k, R182=5.36k. UVLO connects IN; SHDN uses its internal low-voltage pull-up and is externally NC. MODE/RTN/GND are grounded, disabling reverse-input-polarity protection. C1801uF50V is local input decoupling. D6 TVS2200DRVR C523793 protects raw VBUS, D7 BZT52C12-7-F C124196 clamps the gates, D8 TaiwanSemi SMA6J10A M2G C2444429 protects output. R4 is3.3k1206; upstream C2/C4/C5/C6 are specified50V. Captured resistor/decoupling MPNs are selected; C18122nF sets startup ramp. C5 now uses documented1206 packaging. The linked eFuse STEP is a derived visualization with corrected exposed pad, not maker-authenticated exact CAD. Effective-capacitance guarantees, discharge pulse behavior and transient qualification remain open. See the handover for rating limits. Added series resistance is150mΩ typical/250mΩ maximum: account for voltage drop and external-power heat. This stage rejects20V rather than charging from it.


## Power passive integration (2026-10-05)

- [x] Add C18122nF50VX7R0603 from TPS26600 dVdT to GND, retaining prior connectivity. Startup estimate5.26V/ms typical; source/inrush qualification remains open.
- [x] Select R4RC1206FR-073K3L; check sustained9/20/22V arithmetic against0.25W70C rating. Thermal/pulse qualification remains open.
- [x] Select power resistor/decoupler MPNs, correct C5 to1206, and retain all earlier displayed values. C10347nF is now selected as CC0603KRX7R9BB473 / C107093 (50V X7R; effective-capacitance qualification open).
- [x] Add parallel C108PMID and C109REGN after typical DC-bias review. Pair estimates17.60uF at9V and6.09uF at6V include illustrative tolerance/temp factors, not guarantees. Increased startup demand is recorded.
- [x] Review local footprint/model links for63 selected passive references; all links resolve. Generic chip models are package visualizations.
- [ ] Resolve legacy USB-A source identification: PCM2902C advertises100mA bus power, so distinguish host from known2A adapter. User selected automatic detection with conservative fallback; detector/mux capture and source-state firmware remain pending. Do not infer entitlement from BQ reset500mA.
- [x] Replace codec TPS61023 with TPS63802, R140/R14178.7k/9.1k and0.47uH L2. Conservative steady-PWM DC bound4.600–5.059V; startup PFM/ripple/load-step qualification remains open.
- [ ] Complete physical startup/transient, temperature, surge and5V weak-source validation. Current CLI ERC319 inherited root findings; all captured power children zero. No physical tests or PCB layout.

Current partial BOM: US$75.08 fitted / US$94.01 MOQ order estimate (2026-10-05 U19 integration). Shared MPN orders are consolidated; repeated functional rows show order quantity0. Snapshots remain per-row dated; these are not a complete product cost.


## Review follow-up (2026-10-05)

See ai-files/reports/current-review-findings.md. Authorized fixes are in progress; current changes supersede the review baseline.

- [x] Normalize standalone TPS63802DLAR and TS5A3167DBVR format headers; both load/export with installed KiCad10.0.6.
- [x] Assign verified BQ/gauge electrical pin roles, native common-pad stacks and switched-source annotations. All captured power children now have zero ERC findings;319 inherited root findings remain in unfinished blocks, without suppression.
- [ ] Close codec upper/lower rail bounds, USB source permission, protection margins and5V load/thermal limits before dependent integration.
- [ ] Match purchased pack NTC/current rating; select physical/wake switches; separate inactive and ship current budgets.
- [x] Refresh superseded codec/C101/source-policy paragraphs; bring C10 text closer and move C180 ground clear of Q2 text. Render inspected; retained physical connectivity verified.

Fresh review found15 expected power net relations correct,101 component refs covered by BOM and99 assigned footprint/model links resolving. SW100/SW101 remain unassigned. These checks do not replace electrical/thermal/transient qualification.


## Source/protection continuation (2026-10-05)

- [x] Refine U14 feedback to78.7k/9.1k using currentlylisted SAE/Yageo parts; nominal unchanged, conservativeDC4.60004–5.05869V. Enableddivider55uA; outputdisconnect preservesoff priority.
- [x] Add D9 selected BZT52C12 after R4 on U11 VBUS_VS_DISCH, directly toGND; retained physical pin groups verified. Correct inheritedD7 datasheet link (ds18004 BZT52, notds18001 BZX84). Temperature-table arithmetic improves sensepin margin; dynamic qualification and rawVDD remain open.
- Superseded proposal: LTC4368/NFET mainpath retained as an alternative report; the selected TPS25730D replacement now supplies the managed low-loss sink path. No LTC capture is currently planned.
- [ ] Resolve automatic USB cold-start through the new BQ25792 ILIM_HIZ default-off converter plus independent USB auxiliary MCU supply. The active BQ25895 circuit still has its documented startup/current gap until replaced.
- [ ] Capture source-detectionmux and gates only after hardwarecoldstart/resetbudget and3D modelgap resolved. CandidateTS3USB221ARSER C128396; VCC2.5–3.3V guaranteed, not2.3V.

## Latest integration check (2026-10-05)

- [x] Reconcile all102 physical references against the71-row BOM: no missing/extraneous references or MPN/LCSC mismatches. Partial subtotal US$73.73 fitted /US$92.66 MOQ; pack and final headers/switches/D8 remain unpriced.
- [x] Select D4 1N4148W-7-F/C83528 and C103 CC0603KRX7R9BB473/C107093; retain displayed minimum ratings and existing positions.
- [x] Re-export/inspect PD and codec pages using KiCad10.0.6; retained physical net groups preserved excluding intentionalU14/L2/D9 changes.
- [ ] Qualify legacy startup and suspend with the replacement architecture: distinguish charge-qualified attach inrush from100mA sustained attach and2.5mA suspend budgets. Prior MAX4995B bootstrap is an inactive alternative, not planned capture.

- [x] Prepare unregistered TPS7B8450QWDRBRQ1 functional symbol and review DRB footprint/generic STEP for raw-VDD hardening. Activation waits for integration and output-cap review; this is not yet a completed protection fix.
- [x] Source provisional QON momentary candidate TE1977066-1/C2972219; geometry/model and activeBOM integration remain open. Mechanical disconnect remains unselected until battery current/audio budget is fixed.

- [x] Capture U19 TPS7B8450 rawUSB-to5V STUSB4500VDD supply, reuseC5 output, retainC2/C6 onrawUSB. Pin-group comparison preserves all other nets; ERC319root/0powerchildren; finalpage rendered/inspected. Weak5V, capacitor and transient qualification remain open.

- [x] Add U19 to72-row XLSX/CSV BOM; independent main reconciliation103refs/no MPN-LCSC mismatches. New partial subtotal US$75.08 fitted /US$94.01 order; U19 snapshot only1in stock.

## Authorized voltage-range redesign (2026-10-05)

- [x] Select BQ25792 as the native 5–20 V-capable 1S charger; no pre-buck stage. Active replacement capture and review remain pending below.
- [ ] Redesign input cutoff, FETs and TVS/clamp coordination for normal 20 V plus tolerances/transients. The present D9 12 V sense clamp and D8 10 V TVS are incompatible with normal 20 V operation.
- [ ] Review STUSB4500 three-PDO limits and controller policy against requested source compatibility; EPR support is not implied by accepting common 20 V PD.
- [ ] Update child-sheet capture, libraries/BOM, power budget, preview and configuration warning together after reviewed integration.

### Reviewed charger direction

- [x] Select BQ25792RQMR / C2862876 for the replacement design: native 3.6–24 V input, 1S power path and buck-boost headroom on weak 5 V supplies. No extra pre-buck stage. BQ25672 is also voltage-compatible, but its observed price is higher with no cited standby benefit.
- [ ] Finish BQ25792 library/package/model review and child-sheet capture; retain source-aware default-disabled charge and add the explicitly required external ship FET. The active schematic still uses BQ25895 until integration.
- [x] Select TPS25730DREFR / C22438973 for the replacement prototype: autonomous fixed 5–20 V SPR matching and integrated sink switch. TI recommends TVS2200, but its full-rated clamp versus the controller absolute maximum still needs physical qualification; this is not a proven surge rating. Non-PD Rp current is not exposed by documented TPS interfaces; conservative fallback plus separate BC1.2 policy is required.
- [ ] Capture/review TPS25730D and BQ25792 replacements, including exact models, ship FET, source detection ports and root interfaces.
- [ ] Provide independent USB-powered MCU startup while the charger converter remains hardware-disabled. Review low-current OR/mux into the existing always-on regulator; avoid backfeeding SYS or USB.

### Auxiliary logic integration (2026-10-05)

U20 TPS2116DRLR now selects U19 USB_AUX_5V or SYS_RAW into U12. R124/R125 180k/100k set nominal 2.8 V priority threshold; C124/C125 bypass the inputs. Preserve SYS_RAW below 5.5 V recommended maximum (6 V absolute); replacement charger must enforce the selected 1S configuration. Fast input collapse with alternate supply below 2.5 V needs switchover/BOR qualification. The physical gauge, storage switches and other power circuits are unchanged. Active USB PD/charger remains 5/9 V only pending reviewed TPS25730D/BQ25792 integration.

Replacement sink-bulk correction: TPS25730 datasheet table6.4 specifies47uF nominal and100uF maximum, with no47uF minimum. Use the charger shared input bank; remove extra33uF polymer placeholder. Verify converter effective capacitance minima, shared maximum and startup/transient behavior rather than adding unneeded bulk.

Replacement charger startup gate: review POR-sampled ILIM_HIZ100mA clamp under default-off gating, EN_EXTILIM override and watchdog/reset behavior. Current candidate analog-ceiling claim is unverified/withdrawn; independent review needed before capture integration. Selected high-voltage input ceramics remain provisional pending effective-capacitance qualification.

## Latest read-only review (2026-10-05)

See `ai-files/reports/review-2026-10-05.md` (from root) for the current consolidated findings; earlier review baselines are historical. Fresh checks:108 physical refs covered,106 assigned footprint/model paths resolve,SW100/SW101 unassigned,ERC319 inherited root/0 captured children. No circuit fixes made in this review.

Open priorities: active battery-powered gauge switches versus3V_AO pullups at low nonzero BAT_PACK; draft R1024.7k versus220R purchasing code; remaining draft sourcing; source-aware HIZ/current/watchdog/reset policy; SFET_PRESENT firmware setup; visible pins/direct-wire/readability redraw of both replacement sheets. Protection/startup/thermal corners remain qualification gates. Active PD/charger remains5/9V only. User additionally requested a quick mechanical envelope check including drivers,pack,PCB and enclosure.

Quick mechanical envelope review: `ai-files/reports/mechanical-fit-rough-2026-10-05.md`. Two phone faces side-by-side gives163.3×155.8×81.7mm external;2–3mm walls leave1.79–1.88L gross internal. Illustrative unselected driver/pack/PCB reservations total~0.64L; lateral placement needed because stacking woofer/pack/board consumes nearly all internal height. Actual10Ah protected pack and drivers remain unselected, PCB outline absent; bass chamber/tuning and downward clearance are likely constraints. This is not a validated fit or authorized PCB layout.

## Gauge voltage-domain fix and continued replacement work (2026-10-05)

- [x] Move U13/U16/U17 supply and bypass capacitors to3V_AO; replace grounded IN pins with default-off shared GAUGE_ISO_N.
- [x] Add BAT-powered U21 TPS3839G33DBZR/C485802 (3.003–3.126V falling threshold), Q1042N7002/C65189 inverter, R126/R1271M RC0603FR-071ML/C105578 and C126100nF. Retained physical pin groups preserved except intended supplies/enables; complete new nets checked. Render inspected and identifiers/wires separated; ERC remains319 root/0 captured children.
- [x] Reconcile113active physical references with XLSX/CSV BOM; no missing selected parts. Partial estimatesUS$75.61 fitted/US$95.01 in-stock order, not full product cost.
- [ ] Qualify cold MOS gate-drive and voltage-collapse/reset timing. RESETVOH worst mintrip3.003−.4=2.603V exceeds2N7002 maxVth2.5V at25C but not the2.75V −55C corner. Gate leakage does not subtractIgss×R127 from an actively driven push-pull output; R1271M is for safe off when reset is unpowered/undefined. Added BAT load~4.35uA typical at4.2V (supervisor+gate pulldown), even if AOoff; physical switch removes it.
- [x] Record explicit source/startup/reset/ship policy inreports/replacement-power-control-contract.md. This is an implementation contract, not firmware. Whole-board100mA host budget and battery-absent codec bootstrap remain open; charger100mA limit alone is insufficient.
- [ ] Finish visible-pin/direct-wire redraw and full-pin review of isolated charger/PD replacements before integration; no15/20Venable yet.

## 2026-10-05 TPS25730D / BQ25792 integration (supersedes the STUSB4500/BQ25895 entries above)
- [x] Active USB_PD child is now TPS25730DREFR (U11, fixed 5-20 V SPR, integrated sink path) and Battery_Charger is BQ25792RQMR + CSD17579Q3A ship FET Q103. The active circuit is now 5-20 V; the earlier 5/9 V-only restriction no longer applies to the schematic (hardware still unqualified).
- [x] Root: USB_PD GND pin removed; PDCTRL_SDA/SCL, PD_PLUG_EVENT, PD_SINK_EN and Battery_Charger CHG_SYS_ENABLE added as no-connects (MCU not authorized yet). CHG_DP_RAW/DM_RAW dropped (BQ D+/D- pins no-connect).
- [ ] Qualify (review section D): TVS2200/U11 VBUS waveform at 20 V and ROC headroom; PDO selection, AlwaysEnableSink, 5 mA dead-battery LDO_3V3 budget, pin 36; BQ25792 POR from BATP at 0 V, Q103 inrush, QON wake, EN_EXTILIM/IINDPM write order; fill MPN/LCSC for R10, C182, C183, J5, SW100, SW101 and verify U4/U11/Q103 price and stock (BOM subtotal stays partial); optional MCU-side simplifications.
