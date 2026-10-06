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

## 4. MCU, controls and configuration — PARTIAL

- [x] Connect the STM32G071RBT6 (U3, replaced the STM32G031K8T6 on 2026-10-06 per the audio architecture, moved to child sheet `MCU.kicad_sch`, symbol pins regrouped by function) supply/grounds, decoupling (C160 100nF, C161 4.7uF), NRST 100nF (C162), BOOT0/SWCLK pull-down (R160) and SWD connectors: J7 Tag-Connect TC2030-IDC (legged footprint; 1 3V_AO, 2 SWDIO, 3 NRST, 4 SWCLK, 5 GND, 6 SWO unused) and J6 4-pin 2.54 mm header (1 SWDIO, 2 SWCLK, 3 NRST, 4 GND), see 2026-10-06 SWD update.
- [x] Connect MCU to the captured power blocks only: CTRL_SDA/SCL (I2C1 PB7/PB6), PDCTRL_SDA/SCL (software I2C PA12/PA11), CHG_ENABLE, CHG_SYS_ENABLE, CHG_INT, GAUGE_ALRT_N, PD_PLUG_EVENT, PD_SINK_EN, BT_PWR_EN, BT_FORCE_PWM, 5V_LOGIC_EN. Allocation and rationale: `ai-files/reports/mcu-pin-allocation.md`. All other MCU pins are no-connect (reserved list in that report).
- [x] Check pin allocation and voltage domains for amplifiers, Bluetooth UART and controls (reserved pins only: PA2/PA3 UART, PA4/PA5 selects, PA6/PA7 amp PDN/FAULT, PA1 button ladder, PB0 headphone detect, PB1 USB-source detect). GPIO budget is tight; third I2C bus for audio has no hardware instance left (bit-bang on PB3/PB4 or share CTRL). (Done: `ai-files/reports/mcu-pin-allocation.md`; 3V3 MCU domain, series resistors on BT UART.)
- [ ] Define buttons, indicators, volume/source control and battery display requirements. QON sense needs a new Battery_Charger port (no net exists today).
- [x] Allocate remaining interrupt/enable/mute lines and bus addresses; select pull-ups by bus capacitance and rail state. (Done in the pin allocation; audio I2C is on the PCM1862/TAS bus with 2.2k pull-ups R209/R210.)
- [ ] Document startup/shutdown sequencing, fault handling and external-power charge policy (see `reports/replacement-power-control-contract.md`).
- [ ] Resolve any MCU/Bluetooth architecture change explicitly before replacing the currently selected parts.
- [x] Rotary encoder SW102 (Alps EC11E, push switch) added on MCU sheet: ENC_A/ENC_B/ENC_SW on PC8/PC9/PC10 (internal pull-ups), 10 nF debounce C308-C310 (2026-10-06). Part number/LCSC unverified; stock footprint has no 3D model.
- [x] 25 debug test points (TP1-TP22 rails/signals, Keystone 5015 SMD; TP23-TP25 GND, Keystone 5010-5014 THT) placed on the owning sheets (2026-10-06, not committed).

## 5. USB audio and connector data path — PARTIAL

- [x] Connect PCM2902C (U2, moved to child sheet `USB_Audio.kicad_sch`, root page 8) supplies/grounds, decoupling, 12 MHz crystal (Y170, R174, C177/C178), SEL0/SEL1 high, D+ 1.5 k pull-up and 22 R series resistors, VCOM/VCCCI bypass. Supply is now `5V_CODEC` (switched by U23 on Source_Select_ADC; was `5V_LOGIC`) through R170 2.2 R / C170 1 uF. See `ai-files/reports/usb-audio-notes.md`.
- [x] Wire USB-C D+/D- (J1 A6/B6, A7/B7) through D1 to the sheet ports USB_DP/USB_DN. Tap point for the later source-detect mux noted in the root; mux not added.
- [x] Shield: EH pins direct to GND (no RC). Note: this also joins the previously isolated root-local J1 `/GND` net to system GND.
- [x] Codec output: 4.7 uF coupling + 100 k bleed to ports `USB_AUDIO_L/R` (about 2 Vpp, 1.65 V DC before coupling). Now feeds Source_Select_ADC VIN1 (2026-10-06).
- [ ] Source-selection mux, SSPND/HID/MCU connections, crystal/ceramic qualification, LCSC codes for R170/R171/R172, 100 mA/suspend budget handling (5V_LOGIC_EN sequencing).
- [ ] Check USB data operation under 5 V fallback, PD operation and battery/rail transitions.

## 6. Bluetooth audio — CAPTURED, qualification open (2026-10-06)

- [x] `Bluetooth.kicad_sch` (root page 9, above Battery_Charger). U1 BM83SM1-00TA moved from root (reference/value/UUID kept); BAT_IN from 3V8_BT with C190 10 uF + C191 100 nF; SYS_PWR/VDD_IO are outputs with 1 uF each (C192/C193), nothing else loads them; ADAP_IN, I2S, mics, LEDs, buttons, USB, I2C unused (no-connect). Symbol regrouped, GND pads 16/50/56/57 a native stack.
- [x] Audio: analogue single-ended DAC out (AOHPL/AOHPR), 4.7 uF + 100k bleed, ports BT_AUDIO_L/R (open stubs until the source-select sheet). Capless mode rejected (needs AOHPM sense, only for 16/32 ohm headphones). No I2S.
- [x] Control: Host-mode UART PA2/PA3 (BT_UART_TX/BT_UART_RX), BT_MFB on PB3, BT_RST_N on PB4 (open-drain low), BT_TX_IND (module P0_0) on PB8. 10k/1k series resistors limit back-power; 100k MFB pull-down. No module pin reports power-off: the ACK is a UART message. Details/sequence/qualification: `ai-files/reports/bluetooth-notes.md`.
- [x] J8 5-pin test/programming header (RST_N, P3_4 test-mode strap, UART RXD/TXD, GND): datasheet reserves UART P8_5/P8_6 for flash download and Config Tool in Test mode; USB DFU path (ADAP_IN + DP/DM) not provided.
- [x] Antenna: integrated PCB antenna kept; keep-out/ground-plane rules recorded for the later PCB (no layout).
- [ ] Open: confirm MFB VIH/idle polarity, BM83 SYS_PWR/VDD_IO capacitor values against Microchip hardware design guide/EVB schematic, Host-mode Config Tool setup (UART baud, TX_IND), FCC/ISED host-board ground plane, RF test pad cut-out, powered-off signal isolation measurement. ERC 193 -> 139 (see HANDOVER).
- [ ] If revisiting ESP32, explicitly select a device supporting the required Bluetooth audio profile; compare audio capability and power before changing the BOM.

## 7. Source selection and analogue-to-digital conversion

- [x] Source_Select_ADC child sheet captured (2026-10-06, root page 10): U24 PCM1862DBTR (I2C 0x4A, I2S master from Y200 24.576 MHz, VIN1 USB / VIN2 BT / VIN3 AUX, 2.2 uF-100R-10 nF C0G input networks), U22 TPS7A2033PDBVR 3V3_AUDIO LDO (EN tied to IN) from 5V_LOGIC, U23 TPS22917DBVR load switch for 5V_CODEC (CODEC_PWR_EN, 100 k pull-down), FB200 on AVDD, I2S through 33 R to ports I2S_BCK/LRCK/SDATA, AUD_SCL/SDA 2.2 k pull-ups to 3V3_AUDIO, ADC_INT 100 k pull-down. MCU PB10/PB11/PC5/PC7 connected. USB_Audio now supplied from 5V_CODEC. AUX_L/R now come from Headphone_Aux; I2S stays an open root stub until Amplifiers. Y200 load caps changed to 22 pF C0G; LCSC codes filled except 10 nF C0G and 33R. Open: LCSC codes/stock for U22-U24 passives, crystal CL (15 pF) trim, PCM1862 bench check. See HANDOVER.
- [x] Define the complete USB/Bluetooth/auxiliary audio path and switching truth table. (PCM1862 4:1 input, 2026-10-06.)
- [x] Connect/configure TS5A23157 switches only after confirming signal swing, bias, supply and default state. (Headphone_Aux sheet, USB default.)
- [x] Select an audio ADC or a compatible alternative architecture. TAS5825M requires digital audio; current analogue codec/mux outputs cannot directly drive it. (PCM1862DBTR selected.)
- [x] Evaluate PCM1862DBTR as a candidate; finalize channels, gain, input bias/coupling, digital format and clocks.
- [ ] Define source-change mute timing and prevent clicks or simultaneous source contention.
- [ ] Confirm stereo handling, woofer summing and any DSP crossover/equalization architecture.

## 8. Headphone output and auxiliary input

- [x] Headphone_Aux child sheet captured (2026-10-06, root page 11): U8/U9 TS5A23157 3:1 mux (USB default, BT, AUX; HP_SEL_A/B 100 k pull-downs), six 1 uF / 100 k to VMID_HP / 1 k input networks, VMID_HP 47 k/47 k + 4.7 uF, U10 TPA6132A2 (1 uF inputs, 2.2 uF HPVDD/HPVSS, 1 uF flying cap, EN/G0/G1 ports with 100 k pull-downs), J2 HEAD_OUT and J3 AUX_IN (verified mapping: sleeve 1, ring 2, switched ring 3 NC, switched tip 4 = HP_DET / AUX_DET, tip 5), D200/D201 PESD5V0S2BT, AUX 10 k bleeds. MCU PC0-PC3, PA4, PB1, PB2 connected. See HANDOVER.
- [x] Connect TPA6132A2 decoupling/charge-pump and shutdown control per datasheet (SLOS597B fig. 27).
- [x] Headphone source/volume path: fixed-gain analogue pass-through, volume at the source (architecture doc section 4); loads 16-300 ohm.
- [x] Insertion detection and speaker mute behaviour: HP_DET/AUX_DET to the MCU; insertion mutes the speaker chain by firmware only (no hardware mute), then the TPA6132A2 is enabled after the source settles.
- [x] Input/output protection, coupling: PESD5V0S2BT on each jack, 1 uF AC coupling, 1 k series.
- [ ] Open: verify PESD5V0S2BT pin 3 common and stock (LCSC C5380400 is a DOWO listing), PJ-307 mapping against the part, HP_DET behaviour with the real jack, TPA6132A2 click/pop timing on the bench, amplifiers (section 9) not started.

## 9. Amplifier supply and three-driver audio output - CAPTURED, unverified on hardware (2026-10-06)

- [x] Amplifier boost supply: U25 TPS61088RHLR from SYS_RAW to PVDD_AMP 11.9 V (499k/56k, RFREQ 301k about 494 kHz, ILIM 150k = 7.9 A typ / 6.6 A min, 2.2 uH Isat 19.6 A). Equations checked against the Chinese LCSC edition of the datasheet (English PDF blocked); COMP network calculated only.
- [x] Battery versus 5 V / 2 A power limits and charging priority: see `reports/audio-chain-architecture.md` section 3 (U25 fed from SYS_RAW, AGL firmware ceilings).
- [x] Both TAS5825M captured on `Amplifiers.kicad_sch`: PVDD/DVDD/regulator/bootstrap capacitors, ADR 0R (U6, 0x4C) and 1k (U7, 0x4D), shared AMP_PDN, GPIO0 FAULTZ wired-OR, I2S and audio I2C ports, MCU AMP_PDN/AMP_BOOST_EN/AMP_FAULT_N connected.
- [x] Channels: U6 stereo BTL (J9 FRONT_L, J10 FRONT_R), U7 mono PBTL (J11 WOOFER). **PBTL pairing verified from the rendered SLASEH7F Fig. 159 (page 86): OUT_A+ (2) with OUT_A- (30) to one inductor, OUT_B+ (23) with OUT_B- (27) to the other. This corrects the earlier plan (A+ with B+).**
- [ ] Open: driver impedances/power ratings, crossover/DSP and loudness limits; mute/fault/shutdown firmware sequence; bench check of boost compensation, PFM acoustics and the 22 uH inductors.
- [x] Speaker connectors (JST B2P-VH) and 22 uH + 0.68 uF output filters added.
- [ ] Open parts (2026-10-06 sweep: only C1623 for CL10B474KA8NNNC found; LCSC search blocked, 8-lookup budget spent): LCSC codes for the 22 uH (Sunlord MWSA1265S-220MT) and 2.2 uH (Coilcraft XAL7070-222MEC, not at LCSC) inductors, 0.47 uF 25 V, 6.8 nF, 47 pF, 100 uF polymer, boost resistors and 0R; TPS61088 footprint pads are from the EasyEDA package (verify against TI RHL0020A); no 3D model on the VH connector; reference range extended to C300-C307.

## 10. Integration, BOM and schematic review

- [x] Agree rail names, voltage domains, hierarchical ports, reference ranges and sheet ownership before connecting subsystems. (11 child sheets plus root.)
- [x] Integrate each subsystem into the root hierarchy; keep direct local wiring and clear functional boundaries. (Done; hierarchical pin names/types verified against child ports by script 2026-10-06.)
- [ ] Finalize all remaining parts and passives; distinguish candidates from selected parts.
- [x] Reconcile the LCSC BOM with current captured power parts, quantities and unresolved selections (2026-10-05). Continue updating as open MPNs are selected; current costs are partial subtotals, not complete product cost.
- [x] Confirm symbol pin-to-footprint mapping and project-relative footprint/3D links for newly added parts. (Scripted 2026-10-06: every symbol footprint and linked 3D path resolves; no model on PD_C_0402, J5 Micro-Fit, SW101, JST VH, SW100.)
- [ ] Review the complete schematic against manufacturer datasheets, power budget, signal domains and startup states.
- [ ] When verification is requested, export/inspect all pages, run ERC and reconcile every finding. 2026-10-06 final: ERC 19 = 18 root `endpoint_off_grid` at J1 (symbol geometry/off-grid origin 248.75, documented) + 1 `power_pin_not_driven` (U11 VIN_3V3 deliberately tied low via R12). lib_symbol_mismatch U4 and BAT/BATP power_pin_not_driven cleared (PWR_FLAGs on BAT_INT/BATP nets). Not ERC-clean; remaining items are justified.
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

Current partial BOM (2026-10-06 sweep): US$78.94 fitted / US$95.64 MOQ order estimate (workbook E4/E5; unchanged by the sweep, still excludes ~25 unpriced rows incl. pack, switches, J5, inductors, boost/filter passives, many unverified stocks). Shared MPN orders are consolidated; repeated functional rows show order quantity0. Snapshots remain per-row dated; these are not a complete product cost.


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


## Pack connector and switch selection (2026-10-06)
- J5 = Molex 43650-0300 (LCSC C503478, Micro-Fit 3.0 3-pos right-angle, 8.5 A/contact; pins 1/2/3 = PACK+/TS/GND), footprint `Molex_Micro-Fit_3.0_43650-0300_1x03_P3.00mm_Horizontal` copied from the KiCad stock library; no STEP downloaded (stock KiCad 3D source not reachable). Note the LCSC-linked datasheet file is an LXW 5 A clone drawing; the LCSC listing states Molex 8.5 A. Mating housing 43645-0300 and crimps not yet in BOM.
- SW100 = TE 1977066-1 (LCSC C2972219 confirmed, 2009 in stock, US$0.6291 at 2026-10-06). Footprint `TE_1977066-1_Tact_RA_SMD` is a DRAFT from the TE drawing (land dims approximated); circuit: pins 1+3 common (footprint pad 1 x2), pin 2 other contact (pad 2). No STEP; verify land pattern and enclosure plunger before layout.
- SW101 = SHOU HAN KCD1-201-R (LCSC C5884429), 20 mm round SPST rocker, datasheet rating 10 A @12 VDC, 6 A 250 VAC. LCSC stock 0 at 2026-10-06; the datasheet drawing shows 3 terminals at 7 mm pitch (4.7 mm tabs): outer terminals assumed switched (symbol 1/2 -> pads 1/3, pad 2 NC), UNVERIFIED by continuity. Rating is below the assumed 15-20 A peak; treat as service/transport disconnect or add current limiting. Footprint `SHOUHAN_KCD1-201-R_Rocker_D20_Panel`, no STEP.
- Pack itself remains PENDING (datasheet needed; not selected). Charge current recommendation: default 0.2-0.3C (2-3 A), gentle 0.1C; from a 5 V/2 A source limit to ~0.5-1 A charge. Peak discharge 15-20 A is an unverified assumption.
- BOM rows J5/SW100/SW101 filled; prices are unverified listing snapshots. Datasheets in ai-files/datasheets: Molex_43650-0300_C503478.pdf, TE_1977066-1_datasheet.pdf, SHOU_HAN_KCD1-201-R_C5884429.pdf. ERC unchanged at 260; netlist unchanged.

## MCU sheet capture (2026-10-06)
- [x] `MCU.kicad_sch` added (root page 7, right of Fuel_Gauge_Power). U3 reference/UUID preserved (the placed MCU is U3, not U1). TAS5825M U6/U7 moved up in the root to clear the sheet. New parts C160-C162, R160, J6 added to the BOM (unverified prices). ERC 260 -> 222 (fewer root pin_not_connected and label_dangling); MCU sheet adds 0.

## USB audio sheet capture (2026-10-06)
- [x] `USB_Audio.kicad_sch` added (root page 8, right of Logic_Audio_Power). U2 reference/UUID preserved. ERC 222 -> 193 (root pin_not_connected -37, label_dangling +2 for the open USB_AUDIO_L/R stubs, endpoint_off_grid +7 at J1 stubs); USB_Audio sheet 0. New parts BOM-listed; unverified prices/LCSC gaps recorded.

## SWD connectors and crystal caps (2026-10-06)
- [x] J6 1x5 replaced by J6 (1x4 header, footprint `PinHeader_1x04_P2.54mm_Vertical` + stock STEP in `3d/`, Ckmtw B-2100S04P-A110 / C124378 price unverified) and new J7 (`Tag-Connect_TC2030-IDC-FP_2x03_P1.27mm_Vertical`, legged, no 3D, not in BOM). SWDIO/SWCLK/NRST joined by labels; PB3/SWO left no-connect (PB3 reserved for later use). ERC stays 193; SWD net pin groups verified. Helper `replace_swd_connectors.py`.
- [x] USB_Audio C177/C178 22 pF -> 33 pF C0G (CL10C330JB8NNNC, C1663; ~19.5 pF effective vs 20 pF crystal). LCSC added: R170 C112307, R171/R172 C107701 (stock/price unverified). BOM updated via `update_swd_usbaudio_bom.mjs`.

## MCU swap to STM32G071RBT6 (2026-10-06, not committed)
- [x] U3 STM32G031K8T6 -> STM32G071RBT6 (LQFP64, LCSC C432213): new symbol/footprint/STEP (`STM32G071RBT6.*`, stock KiCad LQFP-64_10x10mm_P0.5mm, 64 pads verified), datasheet `ai-files/datasheets/STM32G071x8_xB.pdf` (DS12232 Rev 2). All 18 captured MCU nets re-pinned; netlist compare: every net keeps its non-MCU pin groups. Decoupling C160/C161 (VDD/VDDA), new C163 100nF + C164 1uF (VREF+), VBAT tied to VDD.
- [x] Full pin allocation incl. reserved pins for sections 7-9 (AUD I2C2 on PB10/PB11, enables, HP controls, faults, detects, LEDs, buttons, USB controls) and constraint checks: `ai-files/reports/mcu-pin-allocation.md`. Reserved signals are labelled no-connects on the MCU sheet; PDCTRL is now software I2C.
- [x] New `CHG_QON_SENSE` (Battery_Charger output, MCU PC13/WKUP2 input) through R113 100k from the BQ QON net (high-impedance tap, no divider needed). BOM updated (U3, C163, C164, R113; C164 LCSC unverified; subtotals still partial).
- [ ] Verify G071 stock/price at order; confirm C164 LCSC code; capture the reserved signals with their sheets and add the external pull-downs listed in the allocation report.


## Final consistency sweep (2026-10-06, not committed)
- Open items: see "Final open-items list" at the end of `ai-files/HANDOVER.md`.
- Sweep results: 321 references, no duplicates; BOM covers all (R256 DNP inside the R260 row, PACK is external); D6 MPN property corrected to TVS2200DRVR; stray note rows removed from the BOM; CHG_VIO_3V0 is a dangling port with nothing behind it in Battery_Charger (BQ25792 has no VIO pin).


## Mechanical CAD (2026-10-06, not committed)
- [x] Internal CAD built under `ai-files/cad/` (README there): FCStd + STEP assembly, renders, interference check (0 unintended overlaps in 107 solids), chamber volumes, mechanical BOM.
- [x] Pack decision: LP1260100 pouch rejected (3 A continuous). Pack choice now: 2P 21700 (2 x Samsung 50S 5 Ah) with protection board (4-5 A+ continuous capability; PCM and 10k NTC still to be sourced); J5 stays.
- [x] Enclosure 163 x 100 x 160 mm (+15 mm feet), 2 ND65-4 front, W3-2052SC down, sealed woofer chamber 0.506 L net, main chamber 1.436 L net; PCB estimate 100 x 66 mm (area method in `ai-files/cad/pcb-size-estimate.md`, about 5 300 mm2 courtyard sum x 2.0 / two sides + 15 %).
- [ ] Open: Tang Band drawing (flange thickness/hole pattern/cutout/magnet), ND65 aperture 59.5 and 11 mm pad vs M3x10 (or switch to M3x6), PCM/NTC/holder sourcing, real PCB layout, grommets for woofer wires, J5/SW100/SW101/JST VH models, connector overhang on the real footprints.

## Hand-solder passive repackage (2026-10-06)
- [x] Policy: all resistors/capacitors on hand-solder footprints, 0402 by default; 0805 only for large or high-voltage capacitors (10/22/4.7 uF, 50 V 1 uF, 0.68 uF filter, C265). 262 passives repackaged, netlist identical, ERC 19, BOM merged by MPN. Details and FLAGS (X5R derating on VBUS/PMID/PVDD, unverified MPNs/LCSC codes): `ai-files/reports/passive-repackage-2026-10-06.md`.
- [ ] Open before ordering: verify stock/LCSC codes of the new 0402/0805 MPNs; decide extra parallel capacitors on VBUS/PMID/PVDD at layout.

## PCB layout (2026-10-06, user-authorised: placement only)
- [x] `DesktopSpeaker-kicad/DesktopSpeaker.kicad_pcb`: 114 x 92 mm, 322 parts top side, 4 M3 holes, BM83 antenna keepout, no routing/zones. Method/rules/DRC/open concerns: `ai-files/reports/pcb-placement-2026-10-06.md`; regenerate with `ai-files/helpers/build_pcb.sh`, check with `pcb_check.sh`. CAD rebuilt from the layout (0 unintended overlaps).
- [x] Placement v2 (2026-10-06): 116 x 96 mm, 311 parts, noise zoning (BM83 rear-left corner >= 40 mm from class-D/boost, boost >= 45 mm from audio, class-D 17.9 mm from analogue ICs and 10 mm from analogue passives, BM83 13.5 mm from U24), 4 plated M3 GND mounting holes (`MountingHole_3.2mm_M3_PTH_GND`, 6.2 mm pad), enclosure depth 164 mm (CAD rebuilt, 0 overlaps, woofer chamber 0.530 L). DRC courtyard/overlap/outline 0. Report: `ai-files/reports/pcb-placement-v2-2026-10-06.md`.
- [x] Placement v3 (2026-10-06): 116 x 112 mm, enclosure 163 x 100 x 180 mm (CAD rebuilt, 0 overlaps, woofer chamber 0.625 L), class-D to analogue 24.0 mm (ICs) / 20.8 mm (all parts), BM83 to analogue 16.1, BM83 to U15/L3 33.6, U14/L2 31 mm from analogue, boost 51 mm, U25 FB/COMP away from SW. DRC courtyard/overlap/outline 0. Report: `ai-files/reports/pcb-placement-v3-2026-10-06.md`.
- [ ] Placement v3 open: decoupling <= 3 mm only for part of the caps (HF 0402 mean 3.45 mm, 78 of 116 GND caps > 3 mm; U6 PVDD, U4 SYS, U25 VCC/SS, U24 AVDD remain 5-10 mm), charger passives 14.1 mm from analogue (aim 15), woofer chamber 0.625 L > 0.60, TPS61088 datasheet PDF.
- [x] (superseded by v3) Placement v2 open: class-D 20 mm and BM83-U15/L3 25 mm not met on one board (two-board split or deeper board), decoupling distances still 5-7 mm mean (target 2-3), U25 FB/COMP 2-5 mm from SW, fetch the TPS61088 datasheet PDF (excerpt only in `ai-files/datasheets/tps61088-layout-excerpt.txt`).
- [ ] Review placement, then routing/stackup/planes, test points, silk slots for 5 refs, footprint clearance fixes (J1/U11/U19/SW100) are NOT started.

## Low-risk BOM reduction (2026-10-06)
- [x] Removed C185, C113-C115, C121, C143, C151, C163, C164, C242, R260 (U6 ADR now tied directly to GND). ERC 19 unchanged; netlist pin groups unchanged apart from the removed pins and U6 pin 8 on GND. BOM subtotal US$74.38 fitted / US$83.57 order (partial). Preview refreshed.
- [x] Kept after datasheet check: C126 (U21 TPS3839 VDD bypass), R12, R18, C184.
- [ ] Deferred pending bench: M1 USB/BT bias merge, ADC anti-alias C206-C211, PVDD caps C279/C292, low-med items (C131/C132, C154, C263/C264, C222/C223, R122).
- [x] The 11 removed footprints are gone from the PCB (placement v2 regenerated from the netlist).

## PCB routing plan (2026-10-06, planned and rules set up, NOT routed)
- [x] `ai-files/reports/pcb-routing-plan.md`: stackup (JLC04161H-7628, 1 oz outer recommended), 15 netclasses covering all 311 nets (`ai-files/pcb/net-classes.json`), routing order, per-block guidance, decoupling mitigation, teardrop plan, pre/post-route checklists. Rules installed (`DesktopSpeaker.kicad_pro`, `DesktopSpeaker.kicad_dru`, stackup in the .kicad_pcb, `ai-files/helpers/setup_pcb_rules.py`); DRC 22 violations (inherited), no tracks yet.
- [ ] Open: TPS61088 datasheet, JLC impedance confirmation (USB 0.25/0.15), inner 1 oz, teardrops only via pcbnew GUI (no CLI/Python API), decoupling > 3 mm.

## PCB placement v4 (2026-10-06)
Cell-based tiled floorplan with boxed, titled sections (report `ai-files/reports/pcb-placement-v4-2026-10-06.md`). Done: deterministic 12 s generator `build_pcb_v4.sh`, DRC courtyard/overlap/outline 0, hard separations met, CAD rebuilt (0 unintended overlaps). Open: board 117.5 x 176 mm (v3 116 x 112), critical decaps <= 2.5 mm unmet for U6/U4/U25/U24, woofer chamber now 1.003 L (target 0.60), no routing.

## PCB placement v5 (2026-10-06)
- [x] Denser cells, 0.6 mm labels, minimum-separation packer, 116 x 152 mm (17,632 mm2), woofer chamber auto-sized to 0.525 L net, enclosure 220 mm deep (`reports/pcb-placement-v5-2026-10-06.md`).

## PCB placement v6 (2026-10-06)
- [x] Tighter cells, 1.2 mm title strip, 0.25 mm raster packer, class-D/analogue 15.4 mm (deliberate; 47.9 mm achieved), BT supply >= 10 mm from analogue: 116 x 138 mm (16,008 mm2), enclosure 206 mm, chamber 0.525 L (`reports/pcb-placement-v6-2026-10-06.md`).
- [ ] Unmet: area <= 13,000 / depth <= 190, critical decaps <= 2.5 mm (0402 mean 3.23), 4 label overlaps.
- [ ] Open: area <= 13,000 mm2 and depth <= 185 mm unmet (separation chain); per-cap decoupling <= 2.5 mm unmet for U6/U24/U4/U25; corner holes.
- [x] Decap snap (`helpers/snap_v6.py`): 0402 passive reference designators on F.Fab (silk kept for ICs, connectors, inductors, switches, diodes/transistors, roomy 0805), 0402 gap 0.25 mm; 0402 caps near ICs mean 3.23 -> 2.07 mm, board unchanged. [ ] Open: 24 critical 0402 caps still 2.5-3.9 mm (U24, U6, U2), bulk 0805 3-7 mm from U6/U4/U25.

- [ ] PCB v8 follow-up (2026-10-06): 121.1 x 127.4 mm = 15,428 mm2 (v6 16,008; v7 17,802), 10 M3 GND holes, plate f1 387 Hz, CAD 0 unintended overlaps. Unmet: area <= 14,000 (tile sum 12.9k + holes; separation rules and 2.3 mm title strips), hole distance to J9/J10 26 mm, L200 17.7 mm, max board point to hole 42.6 mm. Not done: tile rotation/mirroring. See ai-files/reports/pcb-placement-v8-2026-10-06.md.


## Placement v9 (2026-10-06)
EC11E volume encoder SW102 (+C308-C310), 25 test points (TP1-TP25), full silkscreen pass, Orwellian logo on the back, board 130.5 x 127.8 mm. Details and open items: `ai-files/reports/pcb-placement-v9.md`; pipeline `helpers/build_pcb_v9.sh`. Routing not started.
