# Desktop Speaker handover

Updated 2026-10-05. The current KiCad schematics are the source of truth. Update this file in place; keep future AI exports, reports and helpers under `ai-files/` instead of creating additional notes around the project.

## Current continuation summary

Read this summary and root `plan.md` first; dated sections below retain earlier evidence and are superseded by later decisions.

- User now authorizes actual 5–20 V PD operation (higher EPR scope pending), alongside ordinary 5 V / 2 A adapter operation. Do not assume fallback 5 V grants 2 A. The active 5/9-only power circuit has not yet been redesigned.
- User: automatic USB source detection; protected1S pack around10Ah with10k NTC; dimensions/acoustic volume lead, weight unimportant. Both physical pack disconnect and electronic ship/off with USB/button wake. Exact pack geometry/NTC/current, switches and driver choices remain open.
- Active power children: USB_PD, Battery_Charger, Fuel_Gauge_Power, Bluetooth_Power, Logic_Audio_Power. MCU/audio blocks remain unconnected; noPCB. Use installedKiCad10.0.6 CLI and personal readable-schematic skill.
- Completed review fixes: compatible TPS63802/TS5A3167 individual-library headers, verified BQ/MAX electrical pin types/native stacks, switched-source flags, direct GND connections, text cleanup. U14 nowTPS63802 with0.47uH Coilcraft L2 and78.7k/9.1k divider. SteadyPWM nominal4.82418V/DC4.60004–5.05869V; startupPFM/ripple/overshoot remain open.
- D9 BZT52C12 afterR4 clamps STUSB sense pin for5/9-only policy; rawVDD now fed through U19 TPS7B8450 40V-input5V LDO; capacitor/dropout/transient qualification remains open. Correct Diodesdatasheet isds18004, notoldwrongds18001.
- Fresh connectivity preserves all retained physical pin groups excluding intended U14/L2/D9 changes. FullERC319 inheritedroot findings, allfivepowerchildren0; no suppressions. Preview `DesktopSpeaker-preview.pdf` refreshed.
- BOM XLSX/CSV:103physicalrefs covered in72rows, US$75.08 partialfitted /US$94.01 MOQ snapshot estimate, notfullproductcost. D4 1N4148W-7-F/C83528 and C103 Yageo CC0603KRX7R9BB473/C107093 are selected; headers/switches/pack/speakers/audio remain open. Guarded`reconcile_power_bom.mjs --codec` preservesnewrows; originalunguardedmodeunsafe. Historicalmetadatahelper excludesR140/R141.
- Replacement direction: BQ25792RQMR native 5–20 V charger and TPS25730D autonomous SPR controller with integrated sink path are selected for prototype capture. Agents own isolated candidates under `candidates/`; active sheets still use STUSB4500/BQ25895. Prior LTC4368/pre-buck/limited-bootstrap proposals are superseded design alternatives, not next integration tasks.
- Exact TI BQ25792 RQM0029A STEP was sourced; 4×4×1 mm extents agree with datasheet. Corrected official 29-pad footprint and functional symbol are candidates pending integration. External SDRV ship NMOS selection is underway; physical switch remains in series.
- New cold-start strategy: BQ25792 ILIM_HIZ held low disables conversion while REGN and source detection remain available. An independent USB auxiliary rail must power MCU before enabling the converter. U19 is retained for that proposed role; `reports/usb-auxiliary-logic-power.md` evaluates TPS2116 reverse-blocking priority mux into U12. Unknown USB attach and suspend budgets still require resolution; no 100mA-compliance claim.
- TPS25730 exposes explicit PD contract current over I2C, but not documented non-PD Rp status. Generic BC1.2 DCP budget is conservative1.5A, not its charger3.25A reset/detection setting. Source detection/data mux and firmware sequencing are unfinished.
- TI recommends TVS2200 for TPS25730, but maximum rated clamp28.35V exceeds controller28V absolute maximum; actual transient pin voltage needs physical qualification. Do not claim a guaranteed full-rated surge result.
- Existing L1 is provisional for the new charger: SYS plus charging current must fit6A thermal/9.5A saturation definitions. See `reports/bq25792-l1-envelope.md`; 750kHz uses2.2µH, not1µH.
- Latest decisions/evidence: `reports/5-20v-charger-selection.md`, `reports/5-20v-pd-front-end-review.md`, `reports/bq25792-library-review.json`, `reports/usb-auxiliary-logic-power.md`; previous review reports remain historical evidence.

## Project locations

- Open `../DesktopSpeaker-kicad/DesktopSpeaker.kicad_pro`.
- Root schematic: `../DesktopSpeaker-kicad/DesktopSpeaker.kicad_sch`.
- Connected USB PD child sheet: `../DesktopSpeaker-kicad/USB_PD.kicad_sch`. This is an active project file, not a disposable generated output.
- Libraries: `../DesktopSpeaker-kicad/kicad-library/{schematic,footprint,3d}`. Keep these paths and the adjacent library tables intact.
- Datasheets: `datasheets/`. Local symbol fields were updated to `../ai-files/datasheets/`, relative to the KiCad project.
- Latest rendered schematic: `DesktopSpeaker-preview.pdf`.
- Starter BOM: `bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx` and `.csv`.
- Import evidence: `reports/new-parts-library-audit.json` and `reports/USB-PD-library-audit.json`.
- Last electrical rules report: `reports/vdd-ldo-erc.json` (319 inherited root findings; zero in captured power children).
- Recovery snapshots: `backups/`.
- Earlier system diagrams: `diagrams/`. These show an older component set; do not use them as a purchasing list.

## Working preferences

Use the installed KiCad 10.0.6 / 10.0.6-rc2 CLI:

```sh
flatpak run --user --command=kicad-cli org.kicad.KiCad
```

Preserve the user's existing placements, reference designators and displayed values. Keep IC reference/value text close below the body and centered; put passive/transistor reference/value text to the right. This supersedes the earlier above-body preference. Reduce unnecessary whitespace without crowding wires or text. Schematics must be human readable: use standard transistor graphics and ground symbols (including in child sheets), wire connections directly whenever practical, and use at most one net label per connected wired section. Keep child-sheet inputs on the left and outputs on the right, retaining their chosen positions. Avoid nonconnecting wire crossings. Group functions and inspect the exported pages.

Keep one component symbol per `.kicad_sym` file. The schematic, footprint and 3D library folders must stay flat. Use dimension-checked STEP models, with linked project-relative paths. Do not create a PCB layout without a request. USB PD plus plan sections 2 (battery charging/external power) and 3 (fuel gauge/low-current power control) are authorized for connections. Other sections remain placed but unconnected.

Use cheaper subagents for independent sourcing/library/BOM tasks, with the main conversation coordinating and reviewing. Downloads and reversible edits are authorized. Keep `../AGENTS.md` as the project instruction file.

## Intended product

Desktop stereo speaker with two front drivers and a downward-facing woofer; USB-C audio/power, 3.5 mm input, Bluetooth, headphone output, battery and direct external-power operation. Footprint is approximately two Samsung S22 Ultras, with height approximately half the phone length. Battery life and low storage current are priorities. Support traditional 5 V / 2 A USB supplies and optional PD; charging policy should reduce battery ageing during prolonged plugged-in operation.

## Selected major parts

| References | Part | LCSC |
| --- | --- | --- |
| U1 | BM83SM1-00TA Bluetooth audio module | C6752723 |
| U2 | PCM2902CDBR USB audio codec | C2651869 |
| U3 | STM32G031K8T6 MCU | C432203 |
| U4 | BQ25895RTWR charger | C80200 |
| U5 | MAX17048G+T10 fuel gauge | C2682616 |
| U6, U7 | TAS5825MRHBR amplifiers | C471049 |
| U8, U9 | TS5A23157DGSR analogue switches | C11133 |
| U10 | TPA6132A2RTER headphone amplifier | C69901 |
| J1 | TYPE-C-31-M-12, 16-contact USB-C | C165948 |
| J2, J3 | HOOYA PJ-307 switched stereo jacks | C2939173 |
| D1 | TPD2E2U06DRLR USB data protection | C1972959 |
| U11 | STUSB4500QTR PD sink controller | C2678061 |
| Q1, Q2 | STL9P3LLH6 P-channel MOSFETs | C2969828 |

J2/J3 retain the displayed values HEAD_OUT/AUX_IN. Hidden MPN/LCSC fields identify actual parts. PJ-307 pin mapping is sleeve 1, ring 2, switched ring 3, switched tip 4, tip 5. Rejected PJ-320 variants had inconsistent library/datasheet contacts; do not substitute them without a fresh check.

The starter BOM predates the PD additions: approximately US$50.07 fitted parts or US$52.52 with purchase quantity rounding. U11 plus Q1/Q2 add approximately US$3.99 at the observed single-unit prices, excluding supporting components. These are partial subtotals, not total product costs. Stock and prices are snapshots, not verified order-time availability. Exact PD passive and service-header MPNs remain unselected.

## USB PD section

The STUSB4500 runs from connector VBUS, with VSYS grounded to avoid intentional battery standby draw. CC1DB/CC2DB follow CC1/CC2 for dead-battery attachment. GND and exposed pad are grounded; ADDR0/ADDR1 are low. Included support circuitry comprises VDD/regulator decoupling, RESET pulldown, VBUS sense/filter, common-source reverse-blocking MOSFET pair, gate RC and system-side discharge.

**Before hardware use, program and read back a two-PDO 5 V / 9 V profile.** Factory NVM requests 5 V / 1.5 A, 15 V / 1.5 A and 20 V / 1 A. The last two are unsuitable for the intended charger operating range. Keep `POWER_ONLY_ABOVE_5V = 0` for 5 V fallback. PDO current requests and charger input limits still require a power budget and source-capability handling. A 5 V / 2 A adapter label does not authorize 2 A from every USB port/cable.

`VBUS_PD` is intended for the charger input, not direct connection to 5 V-only codec circuitry. J4 is a service I2C header using external programmer logic power; program with USB attached and disconnect the programmer when USB is absent. VREG_2V7 is for decoupling only. A future battery-powered MCU connection needs isolation or compatible power domains.

ST Figure 10 was used for circuit review. Local `STUSB4500.pdf` is ST-authored DS12499 Rev 3 from a mirror; Rev 8 was consulted online. Do not relabel the local PDF as Rev 8. STL9P3LLH6 uses source pins 1–3, gate 4, drain 5–8; its exposed footprint land is also drain pad 5, not an invented pin 9. USB-C connector pin types were corrected to passive.

The original 14 root symbol instances retain their placements, reference designators and displayed values; local datasheet paths were updated during artifact relocation. KiCad PDF/netlist exports, pin-to-net checks, footprint/model link checks and page inspection were completed. The last ERC report has 292 findings: 268 unfinished-section pins, 21 preserved-root off-grid endpoints, two undriven BM83 ground pins and the unused VBUS_PD output awaiting charger wiring. The PD circuit's connections were reviewed by item reference/UUID, since KiCad places many hierarchy diagnostics in the root report.

## Remaining design work

1. Add USB CC/VBUS TVS protection and wire USB data protection. D1 is currently unconnected and is reserved for D+/D−, not CC protection.
2. Finalize PD capacitor MPNs, voltage ratings and retained capacitance under DC bias; check discharge resistor pulse/power ratings and header selection.
3. Connect/configure BQ25895, input-current control, battery protection/temperature sensing and the protected regulated 5 V codec supply. Define plugged-in charge target/recharge policy.
4. Select an audio ADC: the analogue PCM2902C/mux outputs cannot directly drive TAS5825M's digital audio input. PCM1862DBTR is a candidate; clocking/bias/coupling remain open.
5. Select the amplifier boost supply: the single-cell battery cannot directly satisfy TAS5825M's minimum power-stage voltage. TPS61088 is a candidate; voltage, magnetics, compensation, output capability and idle behaviour remain open.
6. Finalize battery capacity, rail isolation, Bluetooth power switching, controls, remaining passives and firmware.
7. Select drivers/impedances, acoustic volumes and woofer tuning. No PCB layout exists.

## Cleanup performed

Moved retained BOMs, preview, audits, backups and earlier diagrams into this folder. Deleted temporary `testlib0..5`, `libs` and `nolibs` schematics, duplicate test PDFs, BOM inspection scratch output/preview images, redundant netlist/asset-check exports and superseded selection/PD note files. Active KiCad files and flat libraries remain in place. All datasheets, helper scripts, BOMs, previews, reports and snapshots are now under `ai-files/`; local datasheet links were updated. KiCad local session data and Git history were preserved.

## Readability guide and saved skill

The reusable personal skill is `/home/chithi/.codex/skills/kicad-readable-schematics/SKILL.md`, validated with the skill-creator validator. Apply it for future schematic capture or redraws. No KiCad skill was found in the curated installer catalogue; this focused skill was written using official guidance and project preferences.

Primary sources: [functional pin grouping](https://klc.kicad.org/symbol/s4/s4.2/), [KiCad 10 native pin stacks](https://klc.kicad.org/symbol/s4/s4.3/) and [KiCad 10 schematic editor manual](https://docs.kicad.org/10.0/en/eeschema/eeschema.html). Library conventions inform symbol design; page composition and compact text placement also follow the user's preferences.

The USB PD redraw uses standard PMOS graphics, native source `[1-3]` and drain `[5-8]` stacks, 14 ground symbols and direct orthogonal wiring. Inputs/outputs retain their selected positions. Before/after full-project netlists have exactly the same 295 physical pin connectivity groups. No interior nonconnecting wire crossings remain in the PD sheet. Root schematic placement, references and displayed values were preserved; only local datasheet paths changed during artifact relocation.

Final KiCad 10.0.6 ERC remains at the same 292 inherited/incomplete-design findings described above. Added ground symbols have a registered standard power library, and the decoupling rail is on the connection grid.

## Delegation workflow

Use this chat for system architecture, design decisions and final integration. Assign bounded subsystem sheets to cheaper subagents using compact briefs, agreed interfaces/reference ranges and existing datasheets. Agents own separate child sheets; the main coordinator owns root hierarchy/shared tables and reviews each result. This reduces main-chat context use; total token savings depend on avoiding duplicated research and oversized handoffs.

## Completion checklist

The root `../plan.md` tracks schematic completion by subsystem, with USB PD marked PARTIAL and remaining protection/configuration/integration work explicit. Update its checkboxes alongside this handover; AGENTS.md points continuing agents to both.

## Compact placement update

IC references/values now sit below centered; PD passive/transistor labels and root D1 labels are to the right. The PD controller/support area moved upward 20.32 mm and the service-header wiring shortened 17.78 mm. Main-sheet symbol positions, references and displayed values were retained. All five PD port positions and all 295 physical pin connectivity groups are unchanged. The latest PDF pages were rendered and visually inspected, including fixes for mirrored Q2 text and crowded ground/C10 labels. The previous ERC report predates this placement-only update; no new ERC run was requested.

## Charger and gauge integration (2026-10-04)

Active children: `Battery_Charger.kicad_sch` (sheet a7066d55-4393-49f1-9dcb-c2e9f1db9549) and `Fuel_Gauge_Power.kicad_sch` (sheet 9c37a727-9991-421a-8f6e-77dd39bb53fa). U4/U5 moved from the root with original UUID/ref/value/footprint retained. Root power sheets are adjacent left-to-right in functional order, with moved/aligned ports as requested. U10 and U6 moved clear. Latest ordered-root netlist has 288 physical groups matching the immediately preceding electrically reviewed power draft.

BQ25895 support includes VBUS/PMID/REGN/BAT/SYS capacitors, 47nF bootstrap, 2.2uH L1 candidate, 220R ILIM ceiling, provisional 103AT-2 TS divider, OTG low and D+/D− disconnected from USB codec. R103 pulls /CE to REGN; canonical 2N7002 Q100 sinks it only when CHG_ENABLE is high, with gate pulldown. Charging defaults disabled. Firmware must set source-aware current and pack-specific charge voltage/current/termination/watchdog before enabling; AUTO_DPDM can overwrite the reset 500mA input limit. BAT_PACK is bidirectional. Central gauge-sheet bus pull-ups replace duplicate charger I2C pull-ups; R106 retains charger INT pull-up.

Gauge U5 VDD3 senses protected BAT_PACK; CTG1/GND4/EP9/QSTRT6 grounded; CELL2 is NC on MAX17048. U12 TPS7A0230PDBVR (C3747031) derives nominal 3V_AO from SYS_RAW, with EN wired to IN and 1uF input/output capacitors. Output may drop out near low battery voltage; 200mA is an upper capability, not an allocated rail budget. U13 TMUX1511PWR (C2866750) is BAT-powered and isolates SCL/SDA/ALRT when BAT is unpowered. The physical S/D/SEL map is preserved in a functional symbol layout; gauge-to-switch paths are direct wires. Switch IQ37uA typ/70uA max is an explicit standby cost. See plan.md for conditional budget and open user decisions.

Local STEP links for U12/U13/Q100/J5 and C101 reserve are present, from installed KiCad standard package models. U12 uses five-lead SOT-23-5, not three-lead SOT-23. Q100 G1/S2/D3 matches Nexperia; model/footprint use standard SOT-23. J5 footprint is provisional JST VH 3pin, with battery+/NTC/GND assigned 1/2/3; pack/mating harness remains unspecified. L1 footprint/model and all exact power-capacitor MPNs/DC-bias proofs remain open. FEXU0524 candidate manufacturer PDF is under datasheets; EasyEDA model API returned403, so no verified STEP was obtained and no mismatched model was substituted.

Datasheets added locally: TPS7A02, TMUX1511, 2N7002, JST_VH and FEXU0524S2R2MGS. Major-part source/stock snapshots reported by the sourcing agent are not order-time verification. No final BOM subtotal, PCB layout or new ERC run was performed for this stage; the old PD-only ERC report is historical.

Build helpers are under helpers/. `integrate_power_sheets.py` preserves unrelated root objects from the pre-power snapshot and applies the agreed root moves; do not rerun blindly after manual user edits. Likewise redraw/refinement helpers are one-off authoring tools, not idempotent project synchronization. Update actual schematics and keep the single handover plus plan in sync.

Model-link cleanup: removed the duplicate installed-library JST model reference, retaining its local STEP and placement; C101 1210 model now references the local STEP. All five new selected footprint model links resolve locally.

## Protected pack decision and source policy continuation

User selected a protected 1S lithium-ion pack with a temperature sensor. Capacity/current/connector and NTC curve are still open. The existing 103AT-2 TS divider is provisional until the actual pack sensor is specified. External SYS operation with charge disabled/no battery is supported by BQ25895 NVDC, within source/converter limits; weak sources reduce charging first and may draw battery supplement. Proposed source-aware/current/plugged-in policy is recorded in plan.md; no firmware or final pack settings have been claimed. APPPD USB reference was absent and user is cloning it; wait for the actual source before claiming its protection topology was inspected.

Primary evidence: local BQ25895 datasheet §§8.2.3–8.2.6, REG00/REG02/REG06; https://www.ti.com/lit/ds/symlink/bq25895.pdf and https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1376269/bq25895-bq25895-with-no-battery-operation .

User also selected BOTH physical battery disconnect and electronic off with USB/button wake. Physical switch must interrupt protected-pack positive upstream of all BAT_PACK loads; retain pack ground/NTC. QON can wake ship mode after its specified press time, and USB adapter insertion also wakes; long QON hold can reset battery-powered SYS. With USB present, ship mode alone does not turn off SYS, so switched audio/BT rails and firmware remain necessary. Physical switch rating and UI/off-button sensing are not yet finalized.

Implemented storage hardware: charger SW100 standard momentary pushbutton QON12→GND; SW101 standard SPST between protected-pack J5.1 and all BAT_PACK board loads. J5.2 NTC and J5.3 ground unchanged. Pin-net inspection confirms pack-positive isolation; no ERC run. Both switch MPNs/footprints remain open, especially SW101 DC continuous/pulse rating. QON note moved into upper-left annotation area to avoid U4 identifier overlap. Registered installed Switch library.

## Charger inductor and SYS capacitor selection

L1 is now Bourns SRN6045TA-2R2Y (C1332316). Selected exact-series KiCad community STEP/footprint, copied flat locally; manufacturer body6±0.3×6±0.3×4.2±0.3mm, model bounds6×6×4.328mm. Land-pattern outer span6.5mm and pad length5.1mm match; KiCad pad width2.35mm vs Bourns1.8mm recommendation is explicitly retained as the community-library variation. This supersedes FEXU candidate/open L1 status above. Datasheet ai-files/datasheets/Bourns_SRN6045TA.pdf.

C104/C105/C107 are selected Murata GRM21BZ71A226ME15L (C907991); C107 added in parallel on SYS_RAW with local ground and matching0805footprint/STEP. Existing C104/C105 positions/ref/values preserved. Manufacturer-authored characterization PDF saved as Murata_GRM21BZ71A226ME15.pdf. Third capacitor improves margin against DC-bias/initial/temperature reductions, but typical curves do not provide guaranteed corners; final hardware qualification remains. Samsung CL32B226KAJNNNE C309062 is a C101 candidate only until numeric9V effective-capacitance proof. Source stock snapshots are not guaranteed order-time stock.

APPPD reference inspected at /home/chithi/Desktop/APPPD: USBLC6-2SC6 protects USB D+/D−, CC contacts have pull-downs without CC TVS, USB VBUS has Schottky series connection and USBLC VBUS connection but no dedicated VBUS shunt TVS. Its separate AQ1005/SMF16A parts are on other nets. Do not treat this design as evidence of complete PD port protection.

## USB CC/VBUS protection integrated

D5 ESDA25L (ST, C95343) CC protection: physical1CC1,2CC2,3GND. D6 SMBJ10A (Littelfuse, C151250): physical1cathode rawUSB_VBUS,2anode GND. Dedicated individual local symbols/footprints and project-relative SOT-23/SMB STEP package models registered; standard KiCad origin, not maker CAD. Datasheets: ESDAL-ST.pdf (ST-authored via mirror), Littelfuse_SMBJ.pdf (manufacturer-authored LCSC copy; directmakerdownload403). SMBJ10A10V standoff tolerates9V+10%; rated17V clamp at35.3A10/1000µs is belowBQ22V absmax andPMOS30V. This is not a guarantee of fast board-level ESD overshoot or sustainedOVP:5/9V-onlyNVM mandatory. LCSC C151250 listing snapshot10,100units2026-10-04; verify atorder.

Integrated netlist review ai-files/reports/storage-protection-review.json passes all new physical pin relations. Existing connectivity is unchanged after excluding intended J5.1 positive split and U4.12 formerly-NC wake connection. C107 is onSYS_RAW/GND; switch disconnect includesgauge/isolation. Combined preview exported withKiCad10.0.6/rc2; changedcharger andPDpages visuallyreviewed. No newERC run; inherited unfinishedsections remain. Old model audit/PD ERC reports remain historical; current added-parts linkage evidence is in storage-protection-review.json.

## Regulated supply children integrated (2026-10-04)

The cheaper agents completed regulator research and the 5 V draft, then reached their usage limit; the main agent completed integration and Bluetooth capture. Active new children are Logic_Audio_Power (root sheet instance 31d56ed5-71f9-4c5a-b590-b5d5119f00f9, page 6) and Bluetooth_Power (f761c113-2c86-429a-8773-5f4b423ef275, page 5). Both take SYS_RAW and default-low 3 V logic enables. Outputs are 5V_LOGIC (about 4.95 V) and 3V8_BT (about 3.819 V). BT_FORCE_PWM defaults low via R153. Module/audio/MCU pins are still unconnected as required by scope.

U14 TPS61023DRLT uses correct physical pins FB1/EN2/VIN3/GND4/SW5/VOUT6. R140 732k and R141 100k set nominal 4.9504 V; R142 100k defaults off. L2 changed from unfinished SRP4020TA draft to verified SRN6045TA-1R0Y (C3013497), exact-family local footprint/STEP matching the previously reviewed SRN6045TA series. C140/C141/C142 are Murata GRM21BZ71A226ME15L; C143 100nF MPN remains open. Regulator/package model origin is installed KiCad. U14 ground was routed to the side to keep centered IC identifiers clear; new EN resistor/ground were put on the 50 mil grid.

U15 TPS63802DLAR physical mapping: EN1/MODE2/AGND3/FB4/PG5/VOUT6/L2-switch7/GND8/L1-switch9/VIN10. L3 is Coilcraft XFL4015-471MEC 0.47uH candidate (C18221164), R150 604k/R151 91k; R152/R153 100k default-low; R154 100k output bleeder. C150 and C152/C153/C154 use the selected Murata 22uF part; C151 100nF open. Output 500mA reserve is not a current clamp. Exact DLA0010A HotRod and Coilcraft STEP models remain unavailable. Their unfinished footprint files were moved into ai-files/candidates and active U15/L3 footprint assignments remain blank. Do not replace DLA with a generic DFN having a different exposed pad. User was asked for the exact STEP downloads; no browser is connected and vendor downloads returned403.

Power-up/down, voltage margins and conditional standby estimates are in plan.md. BM83 requires BAT_IN3.2–4.2V; SYS_PWR/VDD_IO are outputs. Follow module OFF acknowledgment and validate >640us supply ramp-down; downstream IO isolation is still necessary. These regulators are power control only; they do not implement the audio path or amplifier rail.

Main moved U7 to the right amplifier group, J1 with all stubs to lower left, D1 clear of enable labels, and added the two lower power sheets. Review in ai-files/reports/regulated-power-review.json confirms all prior physical pin groups preserved and all new regulator relations correct. Root/new children visually inspected; combined six-page preview updated using KiCad10.0.6/rc2. No new ERC or physical tests. Existing PD ERC findings remain historical/unfinished. One-shot builders/integrators are not synchronization tools and must not be rerun over later user edits.

BOM CSV/XLSX were updated by the sourcing agent: earlier selected power additions plus U14, with partial priced fitted subtotal $57.38 and MOQ order subtotal $63.83. Newly captured U15/L2/support rows still need reconciliation; do not report those figures as full power-system or product cost.

## Exact Bluetooth power models resolved (2026-10-04)

User provided Downloads/ul_TPS63802DLAR/DLA0010A.stp (Ultra Librarian TI package download) and Downloads/XFL4015.STEP (Coilcraft mechanical model download). Imported originals into the flat local 3d folder as TPS63802DLAR.step and Coilcraft_XFL4015-471MEC.step. OpenCascade geometry review: TI bounds 2×3×1mm, underside at z=0, pin 1 square terminal at x<0/y>0 matches footprint upper-left (KiCad drawing y negative). STEP assembly transforms already put TI upright: no extra rotation/offset. Coilcraft native height axis is Y; footprint model rotates X +90°, offsets Z +0.1mm, giving 4.3×4.3×1.6mm with terminal bottoms at board level. Body size is the allowed maximum of 4.0±0.3mm. Alignment image: reports/power-model-alignment.png; exact solid bounds: reports/downloaded-model-geometry.json. Download provenance is user-provided vendor assets, not an independently authenticated download.

Corrected the unfinished TI candidate before activation: left pad centers x=-0.9mm, right four x=+0.75mm, pad8 x=+0.55mm; pitch0.5mm and pad widths0.6/0.9/1.3mm, all heights0.25mm and radius0.05mm, match TI datasheet board-layout example. Pad8 has two 0.55×0.25mm paste apertures at x0.175/0.925mm (83% coverage), per TI stencil example; no fictitious pad11. Coilcraft pads remain0.98×3.4mm at x±1.185mm, matching maker land pattern. U15/L3 active footprints and U15 standalone/cached symbol footprint now assigned, all model links local. These facts supersede the missing-model/blank-footprint status above.

Physical pin net groups before/after model import are identical. No ERC or physical testing was run; electrical margin, regulator transient/noise qualification, module I/O isolation, unresolved passive/switch selections and BOM reconciliation remain open. Latest six-page preview refreshed using installed KiCad10.0.6/rc2. Temporary CAD environment removed after review to avoid retaining 1.3GB of tools in the project; helpers require cadquery-ocp and matplotlib if rerun.

## Gauge signal isolation redesigned (2026-10-04)

User requested lower drain following the critical review. Replaced BAT-powered TMUX1511 U13 with three TS5A3167DBVR (LCSC C128416, order-time stock unverified): U13 SDA, U16 SCL, U17 ALRT. Physical map NC1 gauge side/COM2 AO side/GND3/active-low IN4 tied ground/VCC5 BAT_PACK. Each has100nF C130/C131/C132. One flat local symbol/footprint/STEP, symbol table registered by main; model is installed KiCad generic SOT-23-5, with TI DBV pad geometry verified. Existing MAX17048/gauge support pin relations preserved. This supersedes all earlier active TMUX1511 status and budgets; its old library file is retained as historical unused asset.

Three-switch supply subtotal ~0.03µA typical/3µA maximum at5.5V specified conditions. Updated preliminary inactive system subtotal ~35–37µA typical, before MCU/pack protection/leakage/other loads. Powered-off signal leakage full-temp up to±25µA per port at0–3.6V, or±50µA at0–5.5V; relevant AO rail is3V. MAX17048 digital pin absolute ratings0–5.5V independent VDD avoid direct unpowered-pin absolute-max conflict, but partial bias and behavior still need hardware qualification. TS5A3167 operation guaranteed VCC≥1.65V and powered-off isolation atVCC0: intermediate pack-collapse behavior remains open. These are mode qualifications, not claimed measured standby failures.

Battery power path uses physical SW101 plus the charger internal BATFET; SW100 is only QON wake, and U13/U16/U17 switch signals rather than battery power. User accepts source-aware MCU wiring and regulator qualifications remaining on the progression checklist.

## Hardware USB overvoltage cutoff integrated (2026-10-04)

The PD agent reached its usage limit after capture; main completed integration and review. U18 TPS26600PWPR (C544399) sits after Q1/Q2, making VBUS_PD the protected charger input. Normal operation remains 5/9 V; accidental sustained 15/20 V is rejected rather than used for charging.

Configuration:
- R180 100k / R181 12.1k, both 1%, set OVP about 11.03 V nominal, approximately 10.64–11.48 V across threshold/resistor corners.
- R182 5.36k sets 2.23 A typical / 2.35 A maximum current limit, above the BQ hardware ILIM ceiling.
- UVLO3 connects to IN1/2 as TI specifies. SHDN7 is externally NC and uses its internal 2–3.4 V pull-up. MODE6, RTN8, GND9 and EP17 are grounded. dVdT12, IMON10, FLT14 and NC4/13 are intentionally NC.
- C180 1uF 50V is local IN/GND decoupling. MPN/effective capacitance/inrush remain open.
- RTN/GND connection disables reverse-input-polarity protection; no reverse-input-fault survival is claimed.

Independent review caught the earlier SHDN-to-IN connection (outside recommended 0–4 V pin operation) and missing local input capacitor. Both are corrected.

Protection parts:
- D6 TI TVS2200DRVR C523793 replaces raw SMBJ10A. Native pads4–6 connect raw USB; pads1–3 and EP7 ground. Standoff22 V.
- D7 Diodes BZT52C12-7-F C124196, 12 V: cathode1 to common PMOS sources, anode2 to common gates.
- D8 **Taiwan Semiconductor SMA6J10A M2G**, C2444429: cathode1 protected VBUS_PD, anode2 ground. Maker clamp maximum15.7 V at38.2 A, 10/1000us, 25°C. Littelfuse's same-named part clamps17 V and is NOT selected.
- R4 changed to3.3k1206 with local model; pulse-rated MPN remains open. C2/C4/C5/C6 specified50 V instead of25 V; exact MPNs and DC bias remain open.

Main corrected inherited D6 manufacturer metadata, replaced D7/D8 rectangles with standard zener graphics preserving pins, removed an isolated junction, resolved text overlap and put the OVP label endpoint on the50mil grid. The final report `reports/integrated-power-fixes-review.json` passes13 pin relations and preserves all retained physical pin groups after excluding intended replaced/new parts and Q2 drain splitting. PD and gauge pages were rendered and inspected; combined preview uses KiCad10.0.6-rc2. No ERC or physical testing was run. Existing unfinished sections remain.

Libraries:
- U18 footprint follows TI PWP0016A: leads1.5×0.45mm at x±2.9mm, pitch0.65mm; EP3.3×3.3mm with paste per TI's0.125mm stencil example.
- Exact U18 STEP remains open. Installed body model has EP3.4×5mm versus maker's2.7–3.3mm square exposed pad. It is held at `candidates/TPS26600-body-only-wrong-EP.step`, with no active link. Attempts to retrieve an older matching community model returned404. Do not link the wrong pad model.
- D6 DRV0006A footprint was corrected to maker lands0.45×0.3mm at x±0.975mm, pitch0.65mm; EP1×1.6mm and two1×0.7mm paste windows. Its installed WSON package model matches body/EP and is linked locally.
- Other new models are installed SOT-23-5/SOD-123/SMA package models, not maker-specific CAD. Main alone updated shared symbol table.

Qualification boundaries:
- Raw TVS2200 maximum rated clamp28.4 V exceeds STUSB4500's28 V absolute before trace inductance. D8 clamp15.7 V at25°C leaves only0.3 V to BQ SW16 V absolute. Full-rated surge immunity and live-transition survival are NOT proven.
- BQ22 V VBUS absolute applies only with converter **not switching**. Do not cite it as proof that a live9→20 V step is safe. OVP delay is about6us; steady current limit is not an instantaneous surge bound. Temperature, layout and transient validation remain open.
- eFuse resistance150mΩtyp/250mΩmax adds0.27/0.45 V drop and0.49/0.81 W at1.8 A. Check5 V source/cable headroom, thermal performance and inrush.
- Still program/read back5/9 V NVM with POWER_ONLY_ABOVE_5V=0.

`reports/pd-20v-tolerance-options.md` contains source links and prior architecture decisions; the rating/footprint updates above supersede its older25 V capacitor status. The BOM was subsequently reconciled as recorded below. MCU/source integration and regulator qualification remain accepted checklist work.

## Power BOM, 5 V headroom and eFuse model continuation (2026-10-04)

Reconciled `bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx` and CSV against the captured power circuitry. Replaced the old single TMUX1511 row with U13/U16/U17 TS5A3167 (qty3), replaced raw SMBJ10A with TVS2200, added U15/L2/L3/U18/D7/D8, raised the selected Murata22uF quantity to10 and split/updated support passive rows for actual references and50V/1206 requirements. U18 and five other new/replacement major selections use accessed2026-10-04 LCSC listing snapshots. L2 C3013497 and D8 C2444429 still have unverified stock/price. Existing older selected-part prices were retained with their snapshot information. Current partial priced fitted subtotal **US$66.93**, MOQ order subtotal **US$75.46**, 25 priced rows among67 rows. This excludes unpriced passives, pack/switch selections, speakers and unresolved audio architecture. Formula error scan found none; modified rows and totals rendered/inspected, wrap/row heights adjusted. Helper is one-shot for reconciliation; `--review` is read-only and `--format` adjusts formatting. Do not rerun its unguarded edit mode as a synchronization tool.

`reports/5v-input-headroom.md` records datasheet references and illustrative arithmetic. TPS26600 allowance250mΩ plus paired PMOS45mΩ gives0.295Ω board series resistance under their distinct specified conditions; this is not a complete5V/hot corner guarantee. With a4.75V source and0.20Ω cable/contact loop,1.5A gives only about4.008V at the charger. At1.77A the eFuse conduction allowance is0.783W; JEDEC reference-board thermal figures do not validate our enclosed PCB. No hardware is changed by this calculation. Firmware must enforce source permission, preserve hardware ILIM, check VINDPM/IDPM/VBUS, reduce charge current first and reduce load afterward. Battery-absent operation cannot assume supplement mode. Final5V loudness/current capability and transition/surge qualification remain open.

User supplied `Downloads/ul_TPS26600PWPR.zip` after the DigiKey model request. Its `PWP0016H.stp` has correct4.4×5mm molded body,6.4mm lead span,0.65mm pitch and1.13mm height. However, downloaded EP measures2.509×2.91mm and sits atz0.13mm; TI's selected PWP0016A drawing specifies a2.7–3.3mm square EP. Preserve the downloaded original under `candidates/TPS26600-vendor`. Main created **`kicad-library/3d/TPS26600PWPR_datasheet_EP.step`**, retaining the original molded body/16 lead solids and replacing only EP with nominal3×3mm, undersidez0, height0.28mm. Colors were assigned for body/leads. It is a clearly marked **derived mechanical visualization**, not a manufacturer-authenticated exact STEP. `TPS26600PWPR.kicad_mod` links it with zero rotation/offset and unit scale. Lead bottoms and corrected EP sit at board plane; native pin1 marker x<0/y>0 aligns footprint upper-left. Footprint remains maker3.3×3.3mm copper/paste. Geometry/source hashes: `reports/efuse-model-provenance.json`; original/corrected geometry and footprint-overlay PNGs are adjacent. Temporary CAD environment removed after review; helpers require cadquery-ocp-novtk and matplotlib.

Additional passive sourcing leads: Samsung CL10B104KB8NNNC C1591 (100nF50VX7R0603), CL21B104KBCNNNC C1711 (100nF50VX7R0805), CL21B105KBFNNNE C28323 (1uF50VX7R0805). These remain **unselected candidates**; manufacturer catalog downloaded as `datasheets/Samsung_MLCC_LCSC_C1591_C1711.pdf`. No specific DC-bias/effective-capacitance qualification is claimed. C1591 listing inventory conflicts with other cached variants/FAQ; do not assume million-unit stock or quote an unverified checkout price.

Installed CLI now reports **10.0.6** (version command on2026-10-04). Combined six-page `DesktopSpeaker-preview.pdf` refreshed. Electrical schematic connections/positions were not changed in this continuation; only the eFuse footprint's3D model association was changed. No ERC, physical tests or PCB layout.

Final read-only BOM coverage review found no active physical schematic references missing from the reconciled CSV. Model import/cleanup completed2026-10-05; pricing snapshots remain2026-10-04. Temporary CAD environment removed.


## Power passive selections and startup margin (2026-10-05)

Delegated independent passive sourcing and charger capacitor review to gpt-6-luna agents; main integrated USB PD/gauge/regulator metadata, libraries and BOM. Existing reference designators and displayed values preserved; only the newly introduced C181 dielectric changed from unavailable C0G to selected X7R.

USB_PD adds C181 Samsung CL10B223KB8NNNC / C21122,22nF50VX7R0603, direct U18dVdT12–GND. Removed only that pin's prior no-connect. Nominal ramp estimate5.255V/ms,9V startup1.713ms. Electrical/capacitor illustrative corner range3.41–8.33V/ms before aging/bias. With deliberately conservative60uF capacitor scenario, demand~0.315A typical/~0.500A fast corner before dynamic loads. This is not USB current entitlement/compliance or a complete BQ startup model. PMID bank's nominal charge doubled, accounted for in the scenario. R182 ground tail shortened to make room. See reports/power-passive-inrush-review.md.

R4 selected YAGEO RC1206FR-073K3L / C137292,3.3k1206,0.25W70C. Initial-tolerance arithmetic gives0.0248W9V /0.1224W20V /0.1481W22V; enclosure heat, thermal derating and discharge/pulse qualification remain open. No specialized pulse-overload claim. C5 selected Samsung CL31B475KBHNNNE / C51205 and changed to local PD_C_1206 footprint/STEP, copied from installed KiCad standard3216Metric package. Not exact vendor CAD. C1/C3/C4/C6/C180 use CL21B105KBFNNNE/C28323; C2/C10 use CL21B104KBCNNNC/C1711; minimum displayed voltage ratings retained when actual selected part is higher-rated.

Battery_Charger adds C108 parallel to C101 on PMID and C109 parallel to C102 on REGN. C101/C108 are Samsung CL32B226KAJNNNE/C309062,22uF25V1210; typical9V curve plus illustrative initial/temp factors gives17.604uF for pair before aging/chart uncertainty. TI8.2uF is suggested for typical3–5A charging, not a stated guaranteed biased-capacitance minimum. C102/C109 are CL21B106KPQNNNE/C32635,10uF10V0805;6V curve plus same factors gives~6.09uF pair. TI4.7uF REGN ceramic guidance is nominal. Larger banks improve typical margin and increase startup demand; hardware qualification still open.

C100 selected CL21B225KBYNNNE/C2762602,2.2uF50V0805 while displayed minimum remains25V. Exact listing verified, standalone exact manufacturer PDF unavailable; hidden Datasheet links exact LCSC listing. C106 now uses selected Murata GRM21BZ71A226ME15L/C907991, bringing captured quantity to11. C10347nF remains without selected metadata. Most captured power feedback/configuration resistors and gauge/regulator decouplers now have MPN/LCSC/Datasheet fields, including Taiyo LMK107B7105KA-T/C92806 for C122/C123. Typical LDO-cap margin is estimated, not guaranteed. Sourcing facts in reports/power-passives-selected.json and pd-charger-capacitors.json; all downloaded assets remain under ai-files.

Reviewed63 selected-passive footprint/model links: all resolve. Standard chip models represent package families. Retained physical net groups match baseline after excluding intended additions C181/C108/C109 and U18.12; added nets are eFuse ramp, PMID/GND and REGN/GND as intended. Reports/final-power-passives-connectivity.json and selected-passive-library-links.json record evidence. No new ERC, physical tests or PCB layout. Existing unfinished-section ERC status persists.

Regulator feedback sourcing identifies up to100ppm/C TCR. Opposing drift across75C can alter divider ratio~1.5% before reference/ripple. TPS61023 PFM reference has no listed maximum, so nominal4.95V codec rail remains unqualified against PCM2902C5.25V operating maximum over all modes/temperatures. Revisit target or bounded regulator before codec wiring; do not silently call earlier initial-only corner values full-temperature limits.

Legacy USB source policy: PCM2902C fixed descriptor is bus-powered bMaxPower0x32=100mA. Distinguish host from known5V2A adapter or negotiatedType-C/PD grant; BQ reset500mA is not universal permission. BQ D+/D− remain NC; automatic legacy detection would need a shared-data detection/mux design. User was asked automatic detection versus manual known-adapter mode; response pending. No MCU/codec/audio wiring added.

BOM XLSX/CSV now70 rows,61 priced: **US$68.70 partial fitted / US$87.96 partial MOQ order estimate**. Orders for common MPNs consolidated across functional rows (repeat rows quantity0), line totals retain sub-cent precision and totals round cents. Captured11 Murata bulk parts order15 under existing5-piece multiple. New passive prices/stock dated2026-10-05, earlier rows retain their existing snapshots. L2/D8 stock/price remain unverified; pack/switches/speakers and audio candidates excluded. Main reviewed exported formula errors, independent subtotal/order grouping and reference coverage: no missing active refs or order-group discrepancies. Open selections sheet now distinguishes selected PMID part from pending qualification. Evidence reports/passive-bom-review.json; helpers/reconcile_power_bom.mjs --passives is guarded/idempotent for these additions. Never rerun its original unguarded edit mode. Metadata helper apply_selected_power_passives.py preserves wires/positions, --include-charger allowed only after sheet owner handoff.

Final readability cleanup moved the REGN C102/C109 bank left of the VBUS trunk, joined capacitor tops locally with one REGN label, and removed both nonconnecting crossings. Main restored resistor sourcing metadata after the agent redraw and moved the two GND text properties with their symbols. Final six-page preview refreshed with installed KiCad10.0.6; charger page visually inspected after integration. Connectivity review still preserves all retained groups. BOM final figures above include the restored charger resistor selections.


## Current critical review (2026-10-05)

User requested review. Independent gpt-6-luna power review plus main fresh netlist, full ERC, BOM association/library pad/model checks and six-page visual inspection; circuits/libraries/BOM left unchanged. Consolidated findings: reports/current-review-findings.md. Definite new issue: standalone TPS63802DLAR(version20260306) and TS5A3167DBVR(version20251103) cannot load in installed KiCad10.0.6 although cached schematic symbols render. Diagnostic copies changing only header20231120 load/export; active originals unchanged. Four ERC library warnings refer to U15/U13/U16/U17. BQ/gauge Unspecified electrical roles additionally obscure meaningful ERC and create29 warnings. Normalize format and assign verified pin roles before integration; preserve physical mappings/positions.

Known electrical gaps remain source entitlement, codec rail full-mode/TCR/transient bounds, transient protection coordination,5V series-drop/heat, actual pack NTC/current and storage leakage. No new wrong power net found:15 expected relations match fresh netlist.101 refs are BOM-covered; populated MPN/LCSC/qty associations match.99 assigned footprints have mapped pads and resolving models; only SW100/SW101 footprints unassigned. This is an association review, not a new complete mechanical dimension audit. ERC358=247errors+111warnings, root326 mostly unfinished, USBPD1 source annotation, charger21 unspecified, gauge10(8unspecified+2source annotations), regulated sheets0. No suppressions. Updated preview inspected; no physical measurements or PCB layout.

35–37uA subtotal is normal inactive battery mode with BATFET enabled/monitor disabled. BQ ship/noVBUS/monitor-disabled current is12uA typical/23uA maximum at stated datasheet conditions, plus gauge/switch/pack leakage; ship drain must be budgeted separately. Agent power report updated with fresh netlist evidence. Model link resolution does not resolve the discovered standalone-symbol format compatibility problem. plan.md includes follow-up checkboxes and flags older status paragraphs for refresh.


## Battery and source preferences confirmed (2026-10-05)

User selected automatic USB-A source detection with conservative fallback and a protected1S battery target around10Ah. Enclosure dimensions and acoustic volume take priority over weight; a heavier build is acceptable if acoustics benefit. Do not fill the enclosure with battery volume before selecting driver/back-volume arrangements. Exact pack geometry, protection/current ratings, NTC curve and mating connector remain open. Source detection still requires shared USB-data arbitration and firmware; neither the charger reset current nor a 2A adapter label grants a USB-host load.


## Integrated review fixes (2026-10-05)

StandaloneTPS63802DLAR andTS5A3167DBVR headers normalized to20231120; both load/export with installedKiCad10.0.6. Verified BQ25895/MAX17048 electrical pin roles applied to cached and individual symbols; BQ commonBAT/SYS/PGND/SW pads use native stacks. BTST is passive floating bootstrap node, not an externalDCpowerinput. Added switched-source flags to post-PMOSUSBinput and externalprotectedBAT_PACK; these annotate real sources and do not grant source current or certify surge safety. No ERC rule suppression.

U14 codec rail replaced with TPS63802DLAR, R140/R141787k/91k, L2 CoilcraftXFL4015-471MEC0.47uH shared withL3. MODE onSYS_RAW selects forcedPWM aftersoft-start; EN defaultoff viaR142 retained. C140–143 retained, PGNC, AGND/GND directly wired to downwardGND. Main integration corrected the new ground branch junction and removed oldconverter terminal stubs and a redundant globalGNDlabel. SteadyPWM DC bound4.52779–5.13094V, nominal4.82418V, with reference/resistor1%, opposing100ppm/C over100C and conservative signed100nAFB bias; about119mV upper margin toPCM5.25V. Startup temporarilyPFM/ripple/overshoot/load/thermal/effectivecapacitance remain unqualified. Existing TPS63802/Coilcraft footprints and reviewedSTEP links reused. R141 selectedYageoAC0603FR-0791KL/C228098. R140 exactstockedUNI-ROYAL0603WAF7873T5E/C23245 found; datasheet/BOM reconciliation inprogress at this entry. Metadata helper now excludes supersededR140/R141 historical selections.

Physical netlist groups before/after match after excluding intended U14/L2 replacement and virtualpowerflags (reports/integrated-review-fixes-connectivity.json). FullERC319, all on inherited unfinishedroot:234unconnectedpins,75offgrid,8danglinglabels,2BM83ground-undriven. Allfivecaptured powerchildren zero findings. Combinedpreview refreshed andPD/codecpages inspected; C10text movedcloser andC180ground shortened clearofQ2. These checks do not prove physical operation.

Inputprotection redesign remains open. TPS25982/83 raw28.4Vclamp margin insufficient; TPS26630 lowerdrop but4.5Vminimum fails conservativeweak5Vcablecase. LTC4368-2/externalNFET candidate is being checked for gate/inrush/control/surge behavior. STUSB4500 rawVDD and rawVBUS_VS_DISCH both have28Vabsolute ratings; a highvoltageLDO fixes onlyVDD and must not hide the raw sensepin exposure. Do not implementVSYS-only/VDDNC because STrequiresVDD-onlymonitoring topology. See reports/power-protection-fix-options.md and subsequent reviewed candidate when available. NoMCU/audio wiring orPCB layout added.


### Final codec divider and sense clamp refinement (2026-10-05)

Supersedes787k/91k above: R14078.7k SAE1RC0603F7872/C54531588 andR1419.1k YageoRC0603FR-079K1L/C114639. PrimaryseriesPDFs verify1%,100ppm/C,-55–155C. Currentlistingstock4700/296500 with100MOQ; snapshotnotpurchaseguarantee. Lowerimpedance divider55uA whenenabled removes mostFBbiaserror; same4.82418Vnominal, conservativeDC4.60004–5.05869V, uppermargin191mV. Startup/ripple/overshootstillopen. Metadata/BOMupdated. R140previous787kstocksearchconflictedwithliveoutstock; do notreuseitsclaim.

AddedD9 BZT52C12-7-F/C124196, cathodeU11.18/R4.2 andanodeGND. Existing3.3k R4 limitsbranch current~5mA underraw28.4V; normal5/9onlysense retained,20fault deliberatelyclipped abovevalid9window. Manufacturerds18004 table11.4–12.7V@5mA and6–10mV/C givesillustrativecoldmin10.75V/hotmax13.7V; normal9.45V remainsbelowestimatedcoldknee. This is not physicaldynamicclamp qualification. RawU11VDDstillneedsHV LDO/protection. ReusedD7standardSOD123FP/model. CorrectedwrongD7cached/standalone/instance datasheetlinkds18001(BZX84SOT23) tolocalds18004(BZT52). Reportstusb-sense-clamp.json; connectivityreportexcludesintendedU14/L2/D9 andmatchesallretainedgroups.

BOM71rows nowUS$73.69partialfitted /US$91.69MOQorderestimate, computedunroundedlines; D7/D9qty2share10pieceorder. Otherunpricedcomponents/pack/speakers/selectedaudioarchitectureexcluded. Guardedhelpers--codec preserveallupdates; formulaerror scanzero, changedrangesrendered/reviewedbyagent.

AutomaticUSB research ai-files/reports/automatic-usb-source-policy.md identifies a hardwarecoldstartgap: factoryBQ AUTO_DPDM1/IINLIM500mA, startup200mA, analogILIM unsupportedbelow500mA. Dataswitchdefaultoff plusMCUfirmwarecannotaloneguarantee100mA fallback. Evaluateactualcurrent-limited~60–70mA bootstrap with default-off lower-lossmainpath; preservebatteryabs/SW101offUSBoperation. Do not simply raiseILIMresistance for100mA—it is outside datasheet support. No datamux/MCUfirmware implementationyet.


### Cold-start candidate screening and inactive assets (2026-10-05)

TPS26620 andTPS22946 startupbranches are rejected as proven100mA ceilings: TPS26620 lacks guaranteed60–70mA accuracy andlatch behavior/qualificationcurrent needreview; TPS22946nom70max115mAplusstartup685mA8ms andnoreverseblocking. See reports/coldstart-safe-input-path-options.md andlimited-5v-bootstrap-path-review.md. Searchcontinuesforloadswitchwithguaranteedmax~90mA, sufficientminqualificationcurrent,andnoinrushbypass;5V HVLDOplusratedreverseblockingdiode wouldisolate9V mainpath. No bootstrapcaptured.

Unregisteredcandidateassets BSC014N06NS standardNMOSsymbol/nativeG4/S1–3/D5–8 andBSC014N06NS_TDSON-8FL footprint exist in flatlibrary. MaincaughtmalformedDescription/footprintfilename/unmappedEP9; agentcorrectedall. InfineonhasnoEP9: exposeddrainusesrepeatedpad5. SymbolCLIexportsuccess. GenericinstalledSTEPenvelopechecked,notauthenticatedmakerSTEP. TPS7B8450 DRB candidateFP/modelalsoexistsunregistered; no activeplacement/circuit. Mainlibrarytableunchanged.

## Resumed integration audit (2026-10-05)

Latest `reports/final-review-fix-bom-coverage.json` covers102 activephysicalrefs with71 BOMrows and no MPN/LCSC discrepancies. Raw totals73.7302USD fitted /92.6647USD ordered; partial, not product cost. Unpriced capturedrefs J4/J5/SW100/SW101/D8 plus separately budgeted pack. D4 maker PDF confirms100VVRRM versus displayed75V minimum; C103 maker PDF confirms47nF50VX7R0603 versus displayed10V minimum. Neither hiddenfield update changes connectivity. Retained physical net groups match `before-review-fixes.xml` excluding intendedU14/L2/D9. Latest ERC319allroot,0 eachcapturedpowerchild; preview refreshed and inspected.

USB-IF current compliance update distinguishes attach inrush from steady current: analyze charge above100mA over each region in at least100ms capture. A brief LDO capacitor charge exceeding100mA is not intrinsically a failure; the total charge/waveform must be qualified. Primary reference https://compliance.usb.org/index.asp?UpdateFile=Electrical (Inrush Current Test Description, requiredJune2021). MAX4995 candidate still does not prove battery-absent BQstartup or suspend. Do not treat200mA BQstartup current-limit as forced current demand. Independent reviewer report now reflects this distinction. C5 may be reused as the LDO output capacitor rather than added a second time; total charge must include internal ST regulator loads. An independent auxiliary rail plus dedicated BC1.2 detector is under review as a simpler architecture.

### Prepared assets and storage-switch sourcing

New unregistered TPS7B8450QWDRBRQ1 individual symbol validated by CLI10.0.6. Exact fixed-output pin map: OUT1, NC2/3/4/6, GND5, EN7, IN8, thermalpad9GND. `reports/vdd-ldo-library-review.json` records footprint/STEP findings; generic KiCad STEP, not TI-authenticated. Datasheet clarification: recommended nominal output2.2–220uF, effective minimum1uF and ESR0.001–2ohm. Existing C5 is Samsung CL31B475KBHNNNE/C51205,4.7uF50VX7R1206±10%; not Murata. Its DC-bias/temp/aging minimum still needs proof. Do not double-count C5 when reusing it for the new LDO output. U19 subsequently integrated into activeUSB_PD; see continuation below.

`reports/storage-switch-selection.md`: provisionalSW100 TE1977066-1/C2972219 signalmomentary,50mA12VDC,2009stock snapshot2026-10-05. Right-angle SMT needs enclosureplunger/footprint/STEP review before activation. SW101 needs explicit DC make/break/continuous/pulse ratings matched to futureaudio battery current; examined20A14VDC panelrocker C7369595 is outofstock and notselected. Preserve protectedpackpositive physicaldisconnect in series with chargerBATFET electronicoff; QONbutton is a control, not a second load switch.

### Active PD VDD hardening

U19 TPS7B8450QWDRBRQ1/C3751394 now captured in USB_PD and individual library registered. RawUSB feeds IN8/EN7; OUT1 feeds U11VDD24 and existingC5positive; GND5/EP9 directly grounded. C2/C6 stayraw; C5 reusesexistingpart rather thanaddingcapacitor. Newblock arranged belowcontroller clear of serviceheader, directorthogonalwire withsinglelocalrail label plus necessaryremotePDlabel. `reports/vdd-ldo-integration.json` checks everyintendedjoin/raw-outputisolation; retainedgroups match previousnetlistexcludingU19/U11.24/C5.1. `reports/vdd-ldo-erc.json`:319root,0eachpowerchild. Preview refreshed and inspected. No fullsurge/weak5V/output-effectivecap claim; normalPDprofile remains5/9 only. This is PDVDD only, noauxMCU/codecfeed yet.

Dedicated BC1.2 detection alternative remains research: BQ24392 C128408 avoids BQbootstrap dependency but requires4.75–5.25V supply (TIsection6.3 confirmed from downloadedprimaryPDF), so existingLDO cannot guarantee its weakUSBcorner. No newdetector captured. Review report corrected separateUSBcharge-inrush vssteadybudget and confirmedPCM67mA MAXtableunderstatedtestconditions; notwholeboardbudget.

Final U19 BOM reconciliation: `reports/vdd-ldo-bom-coverage.json` confirms103physicalrefs/72rows, no missing/extraneousrefs or MPN/LCSC mismatches. Raw totals75.0754USD fitted /94.0099USD ordered (US$75.08/$94.01). U19 freshLCSC snapshot1in-stock at$1.3452, MOQ1/multiple1. Workbook changedrows/totals rendered and inspected. Partialprice excludes actualpack/drivers/unpricedheaders/disconnect and unresolvedaudio.

## New voltage-range requirement

User requests actual operation from PD voltages up to20V rather than merely survival of unexpected15/20V. Coordinator judgment favors comparing a native high-voltage1S power-path charger against extra pre-buck conversion. Independent charger and frontend reviews are underway; reportfiles `reports/5-20v-charger-selection.md` and `reports/5-20v-pd-front-end-review.md`. Existing 11V cutoff, D8 10V TVS, D9 12V sense clamp and BQ25895 remain active; therefore existing NVM warning remains valid until integrated hardware supports20V. U19 protectsPDVDD but does not make charger/sense/output protection compatible with20V. EPR28/36/48V optional scope question pending; proceed independent5–20V evaluation.

### Git checkpoint

Reviewed captured power-subsystem project/library assets, BOM, preview, helpers and evidence were committed and pushed to `origin/main` as `4d29246` (2026-10-05). Branch and remote were checked; no force push. Execution caches, dependency symlinks and local recovery backups are ignored. New 5–20 V research remains separate from the active 5/9 V circuit until reviewed integration.

### Coordinator charger selection

BQ25792RQMR / C2862876 is selected for the replacement design, pending library/capture review. LCSC research snapshot4970stock/$2.0489 at1+. Native3.6–24Vinput/1S NVDC and buck-boost weak5Vheadroom avoid additionalpre-buckstage. BQ25672also supports3.6–24V (originalagent6Vexclusion was corrected againstprimarySection7.3); its observed$4.4266 price is higher and quotedstandby is similar, so no benefit warrants it here. BQ25792requires externalSDRVshipNFET for dependableelectronicbatteryoff; do not relyonlyoninternalBATFET. This choice does not yet alter activeU4/BOM. Standby tableconditions8V/TJ<85C not guaranteed1Sbudget.

PDcontrollerselection remains underreview: TPS25730D autonomousrange matching/integratedlowRDS mayremoveST+PMOS+eFuse+U19 andavoidfirmwareprofilecoldboot dependency; verifyI2C TypeC/PDcurrentstatus andnonPDcurrentpolicy plusrawTVSmarginbeforecommitment. ST4500only3staticPDOs cancoverallcommonvoltagesonlyviaMCUruntimeprofileadjustment. Do notclaimstatic5/9/20matches15/12sources.

### 5–20 V planning Git checkpoint

Commit message: `Record 5-20V redesign direction and retain active hardware limits`. Includes the reviewed plan, design-selection notes and matching schematic/preview warning. No electrical connections were changed in this checkpoint. Candidate libraries and draft research stay outside this checkpoint while their review continues. Git add/commit/push is required at subsequent reviewed milestones, per AGENTS.md.

### Replacement PD controller and cold-start direction

Coordinator selects TPS25730DREFR/C22438973 for the 5–20 V SPR prototype. Its autonomous range matching removes ST4500 three-PDO firmware dependence; its managed integrated sink path removes the old PMOS/eFuse loss. TI explicitly recommends TVS2200 in the controller input guidance, so use that pairing as a prototype baseline. The TVS full-rated maximum clamp (28.35 V) exceeds the controller 28 V absolute maximum: no extra transient allowance has been established, and actual hot-plug/surge pin waveforms remain a release gate. This is not a guaranteed full-rated surge design. EPR is not included.

Keep U19 as proposed USB-only auxiliary 5 V regulator rather than deleting it: MCU startup must be independent of SYS while ILIM_HIZ prevents charger switching. Existing active rail remains PD_VDD_5V until replacement capture; USB_AUX_5V will be the new role/interface. Review reverse-blocking low-current OR/mux from USB_AUX_5V and SYS_RAW into U12 before relying on battery-absent startup. MCU/audio wiring remains outside the current capture scope. TPS I2C reports explicit PDO/RDO contract current, not non-PD Rp current. BC1.2 DCP detection supports a conservative 1.5 A budget, not automatic use of the BQ 3.25 A preset or a generic adapter's printed 2 A.

Git: reviewed architecture/startup constraint milestone `14d95e0` pushed to origin/main on2026-10-05. Replacement sheet capture still isolated and not yet integrated.

### Active auxiliary logic supply integration (2026-10-05)

U20 TPS2116DRLR/C3235557 is integrated in Fuel_Gauge_Power: VIN1 pin3 and MODE5 use U19 USB_AUX_5V, VIN2 pin6 uses SYS_RAW, VOUT pins2/7 feed U12 IN/EN and C122, PR1 pin4 is the R124 180k/R125 100k divider midpoint, GND1 grounded and ST8 intentionally NC. C124/C125 reuse the selected C122 1uF10V capacitor. TPS2116 individual symbol/footprint/STEP registered; model is reviewed installed KiCad SOT-583-8 geometry, not TI-authenticated. R124 Yageo RC0603FR-07180KL/C123419 selected electrically; retrieved supplier stock/price may be stale and must be reconfirmed. R125 reuses RC0603FR-07100KL/C14675.

USB_PD now exports the U19 rail as USB_AUX_5V. Root wire runs above the ordered power row; SYS_RAW branch label was moved below its direct link to prevent an accidental contact caught during review. Final physical pin groups match before-5-20v-integration.xml after excluding only new mux/support parts and the intended U12.1/U12.3/C122.1 feed change. Six domains (raw USB, AUX, SYS, mux output, PR1 and 3V_AO) remain distinct. Evidence reports/usb-aux-logic-integration.json and integrated.xml; final ERC remains319 in unfinished root, zero all five captured power children. Root/gauge/PD pages rendered and inspected.

Independent datasheet review confirms MODE priority/manual fallback and reverse-current blocking with residual leakage. Divider threshold is nominal2.8V, approximately2.54–3.06V with reference/resistor corners, plus about±0.02V leakage allowance. Inputs require1.6–5.5V recommended range: enforce 1S SYS configuration and transient margin in BQ replacement. Fast VIN collapse greater than1V/10us needs alternate supply at least2.5V for documented switchover conditions; qualify depleted-pack dropout/BOR and U19 weak5V output. AUX integration is not measured USB compliance or complete MCU startup. Existing gauge signal-domain/pack-collapse concerns remain open. Active STUSB4500/BQ25895 and protection STILL REQUIRE5/9V only; 15/20V not enabled. Replacement PD/charger candidates remain isolated pending review.

Replacement draft review: BQ25792 capture initially had invalid GND text justification (justify center) and several real shorts; agent is correcting it in candidates. TPS25730D first wired draft still overuses labels, has off-grid placement/text overlaps and left-side output ports; returned for functional-symbol/layout redraw and physical-net preservation. Neither draft is approved for active integration. TPS25730 ADCIN2 code7 for20V is supported by revised EVM User Guide RevA (Aug2025); older datasheet example conflict remains a silicon/configuration qualification gate.

Auxiliary BOM reconciliation: active108/108 physical references covered, plus explicit nonphysical PACK budget row. All populated MPN/LCSC values match active netlist (103/103 MPN,58/58 LCSC), zero formula errors. Selected fitted partial estimateUSD75.13 includes R124 stale listing tier; in-stock MOQ partialUSD94.01 excludes unverified R124/U20 pricing/stock. Neither is total product cost. Evidence reports/usb-aux-bom-reconciliation.json and rendered changed rows/totals.

Git: auxiliary logic mux/BOM/library milestone2fb1ac3 pushed to origin/main2026-10-05.

### Corrected sink-bulk interpretation

Coordinator visually inspected TPS25730 datasheet page10 table6.4 (reports/tps25730-capacitance-table.png). CPPHV47uF is NOMINAL, not a specified minimum; MIN column is blank, MAX100uF. Earlier agent wording47–100uF effective minimum range was incorrect. Derating/transient checks still matter, but do not force extra bulk solely to guarantee47uF minimum. Replacement architecture uses shared charger2x10uF VBUS plus3x10uF PMID bank (~50uF nominal plus100n bypass), and removes the separate33uF C180 polymer placeholder from PD draft. At ±20% initial and +15% X7R temperature,50uF becomes69uF before small bypass, leaving meaningful margin to100uF. This is arithmetic on capacitor limits, not hot-plug qualification; count all downstream caps and topology-dependent attach charge. BQ25792 table8.3 effective minima are VBUS2uF,PMID4uF,SYS6uF,BAT3uF. Exact35/50V ceramic MPNs and effective20V corner still need selection/review. No active circuit change from this decision yet.

Ship-FET library preparation: CSD17579Q3A individual symbol/footprint and exact TI DNH0008A STEP are now registered for the forthcoming charger replacement, with no active placement. PinsG4/S1–3/D5–9 and footprint1–9 checked. TI page9 land pad9 anchor1.775x2.45 atx0.3275; stencil four0.705x1.125 windows centersx−0.208/+0.697,y±0.6625. Root caught and corrected an initial0.083mm stencil offset before activation. Evidence reports/ship-fet-library-activation.json and CSD17579Q3A-stencil-datum-review.json. SDRV weak gate drive, ship switching time and power dissipation remain system qualification items; no gate pulldown is permitted without checking driver current.

Provisional replacement input ceramic selection: Samsung CL32B106KBJNNNE/C13868710uF50V±10%X7R1210 for two VBUS and three PMID capacitors. Maker typical21V bias curve≈5.04uF each; with−10% initial/−15%temperature estimate3.86uF, giving7.72uF VBUS and11.57uF PMID versus BQ minima2/4uF. Not guaranteed across aging/ripple/lot. Maximum nominal50uF x1.10 x1.15=63.25uF plus bypass leaves margin below TPS100uF shared max. Source snapshot5piecesUSD0.7855, existing generic KiCad1210 FP/model reused; actualstock volatile. No active BOM or charger change yet.

Critical charger startup review (candidate not approved): BQ25792§9.3.4.3 samples ILIM_HIZ at POR; pin below1.08V becomes cached100mA clamp. Default-off Q101 holds pin below0.75V during startup, so simply releasing it has not been established to allow higher IINDPM while EN_EXTILIM=1. Disabling EN_EXTILIM permits hostcurrent limits but removes the presumed hardwareceiling. REG14 EN_EXTILIM resets on REG_RST, not watchdog; REG06 IINDPM also resets only on REG_RST, so earlier direct-watchdog-to-3A claim is withdrawn. Watchdog can reset other control/auto-detection bits and needs an explicit policy. Earlier candidate0.8–1.1A continuousanalog ceiling claim is withdrawn. Independent primary-source review underway in reports/bq25792-ilim-startup-review.md. Define explicit startup/readback/watchdog/reset/source-transition policy before integrating replacement; do not claim USB current compliance based on the divider alone. Active hardware remains unchanged5/9V.

Independent ILIM review complete: reports/bq25792-ilim-startup-review.md confirms no documented resampling on HIZ release. Candidate divider is a gating bias, not a proven fixed current ceiling after EN_EXTILIM=0. Proposed host policy holds HIZ through watchdog/auto-detection/ICO disable, sets and reads back source and1S limits with explicit external-clamp override, then releases system gate and charge independently. Every MCU reset must return gate low; adapter/source changes need current-limit requalification. Prototype register-order and source transition behavior remain validation gates.

Frozen BQ25792 draft checkpoint: candidates/Battery_Charger.kicad_sch/.net and Battery_Charger-candidate.pdf/.png are parseable and retain external ship-FET series routing. Not approved: crowded pin labels, many GND labels instead of required symbols, label-heavy support circuitry, detached-looking ports, bootstrap/inductor text orientation and switch/header overlap remain. Main reviewed helpers/check_bq25792_netlist.py and found its assertion coverage partial: it does not verify both BTST capacitor terminals and omits VBUS/GND from isolation set; passing is not a full no-short proof. Next pass must draw clean local support blocks and compare complete physical pin groups, clear stale purchasing fields and reconcile new hierarchy ports before any active replacement. PD redraw remains candidate-only in progress; no15/20V enable.

Coordinator full BQ draft connectivity review now passes all29 physical U4 pins and29 exact expected net groups, covering every physical component pin with no unexpected/missing joins. Includes both bootstrap terminals and VBUS/GND: helpers/review_bq25792_candidate.py and reports/bq25792-candidate-full-pin-review.json. This supersedes the limited checker as connectivity evidence only; style/configuration/MPN review remains unapproved. A purchasing-field defect remains: draft R102 displays4.7k but retains old220R MPN RC0603FR-07220RL/C107696. Audit every changed passive and synchronize displayed value/MPN/footprint before BOM integration; C110 can reuse C103 selected47nF, and new resistors can reuse already sourced mappings where values match. No candidate part has been inserted into active BOM.
