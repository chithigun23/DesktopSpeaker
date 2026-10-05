# BOM reduction audit (read-only, 2026-10-06)

Source: kicad-cli netlist/BOM of DesktopSpeaker.kicad_sch (322 components, 261 chip R/C: 104 R, 157 C; 106 grouped BOM rows, 63 of them passive).
Basis for A/B/C/D: AGENTS.md, plan.md, HANDOVER.md, reports/bq25792-vbus-pmid-ceramic-review.md (BQ25792 DS 10.2.2.2: 2xVBUS + 3xPMID), reports/mcu-pin-allocation.md (DS12232 fig.13), reports/usb-audio-notes.md, bluetooth-notes.md, audio-chain-architecture.md.
Datasheet page numbers were NOT re-opened (no web, local PDFs not re-read); items marked "verify" need a datasheet check before editing.
A = required by datasheet/reference design; B = robustness/margin/default-safe chosen here; C/D = candidate cut/merge.

## 1. Summary by sheet (current / A / B / C-D)

| Sheet | Parts | A | B | C/D | Notes |
|---|---|---|---|---|---|
| USB_PD (U11 TPS25730D) | 17 | 12 | 3 | 2 | C185+R12 on VIN_3V3 tied to GND |
| Battery_Charger (U4 BQ25792) | 28 | 17 | 8 | 3 | C113-115 100 nF extras |
| Fuel_Gauge_Power (U5/U12/U20) | 17 | 9 | 4 | 4 | 3x100 nF on BAT_PACK, 3x on 3V_AO |
| MCU (U3 STM32G071) | 6 | 3 | 1 | 2 | VREF+ caps with VREF+=VDDA |
| Bluetooth (U1 BM83) | 14 | 8 | 4 | 2 | R180/R181 DC refs |
| Bluetooth_Power (U15) | 10 | 4 | 4 | 2 | C151, 3rd out cap C154 |
| Logic_Audio_Power (U14) | 7 | 4 | 2 | 1 | C143 |
| USB_Audio (U2 PCM2902C) | 18 | 16 | 0 | 2 | R175/R176 (merge option) |
| Source_Select_ADC (U24 PCM1862, U22, U23) | 41 | 22 | 11 | 8 | 6 anti-alias C, 3V3 duplicates |
| Headphone_Aux (U8-U10) | 42 | 15 | 20 | 7 | 6 coupling C (merge), C242 |
| Amplifiers (U6/U7 TAS5825M, U25 TPS61088) | 61 | 40 | 16 | 5 | PVDD/SYS bulk, ADR 0R |
| **Total** | **261** | **150** | **73** | **38** | |

Roughly 57% of passives are datasheet-mandated; 28% are deliberate safe-default/margin parts; 15% are candidates.

## 2. Findings per function (grouped; refs, class, basis)

USB_PD
- A: C2 4.7u VBUS, C5 4.7u AUX_5V, C6 22u LDO_3V3, C181 10u LDO_1V5, C182/C183 330 pF CC filters, R10/R11 ADC4 config divider, R13 FAULT, R14/R15 PD I2C pull-ups (to LDO_3V3 on purpose, mcu-pin-allocation.md), R18 10k on RESERVED pin 36 (A, verify DS wording).
- B: C184 1u/50V second VBUS cap (vestige of earlier eFuse IN cap, HANDOVER "C180 local IN decoupling"; keep, verify vs TPS25730 CVBUS); R16/R17 100k open-drain pull-ups.
- C: C185 10u on VIN_3V3 while R12 ties that pin to GND via 100k: a bypass cap on a grounded pin does nothing. Cut C185. R12 could become a direct GND tie if DS permits (verify; HANDOVER notes ERC power_pin_not_driven by design).

Battery_Charger
- A: C100/C111 (VBUS x2), C101/C108/C112 (PMID x3) per BQ25792 DS 10.2.2.2; C102 REGN; C103/C110 BTST; C104/C105 SYS; C106 BAT; R100/R101 TS; R102 PROG; R106 INT pull-up; R108/R109 ILIM divider.
- B: C109 second REGN cap. Calc: 10u 10V 0805 X7R at 5 V ~55% = 5.5u; -10% tol, -15% temp -> ~4.2u per cap, below the ~4.7u typ, so one cap is marginal: keep. C107 third SYS cap (documented selection, HANDOVER L156): keep. R103/R107/R110/R111 default-off pull-ups/downs, R112 BATP 100R, R113 QON tap.
- C: C113/C114/C115 100 nF on VBUS_PD/PMID/SYS_RAW; reference design has none, 1210 10u parts already give wideband bypass. Cut.

Fuel_Gauge_Power
- A: C120 (MAX17048 VDD), C122-C125 (U12 IN/OUT, TPS2116 VIN1/VIN2 1u), R120/R121 CTRL I2C pull-ups, R124/R125 PR1 divider.
- B: R122 ALRT pull-up (MCU internal pull-up could replace: low-med), R126/R127 1M gating defaults, C130.
- D: C121 and C126 duplicate C120 (three 100 nF on BAT_PACK, device needs one). C131/C132 on 3V_AO next to TS5A3167 U13/U16/U17 (3 switches, 3 caps; one per two is acceptable if placed close).

MCU
- A: C160 100n + C161 4.7u VDD/VDDA, R160 BOOT0/SWCLK pull-down. B: C162 NRST 100 nF.
- D: C163 100n + C164 1u on VREF+. VREF+ (pin 7) and VDDA (pin 8) are the same net 3V_AO and VREFBUF is off; ST package schemes need the separate VREF+ caps only when VREF+ is decoupled independently. Cut both (ADC is used only for BTN_ADC and USB_SRC_DET).

Bluetooth / Bluetooth_Power / Logic_Audio_Power
- A: BM83 C190-C193, MFB divider R183/R184, audio coupling C194/C195; TPS63802 C150/C152, R150/R151 and C140/C141, R140/R141.
- B: R182/R185/R186/R187 series back-power protection (bluetooth-notes.md); R152/R153/R142 default-off pulldowns; R154 3V8 bleeder (needed for >640 us ramp-down, HANDOVER L174); C142, C153 second output caps.
- C/D: C143, C151 100 nF on SYS_RAW at the TPS63802 inputs (DS lists only the 10u CIN; no HF cap needed, RF noise is not reduced at 2.4 GHz by 100 nF). R180/R181 see merge below.
- Calc for C154 (third 3V8 22u): 22u 10V 0805 X7R at 3.8 V ~55% = 12u each; -10%/-15% -> 9u; two caps = 18u effective, above the TPS63802 COUT (10u effective min; verify). Third cap redundant. 5V rail (C141/C142) at 5 V ~40% retention: keep both.

USB_Audio (all A except R175/R176)
- C170-C174 1u, C175/C176 10u, C177/C178 33 pF, R170 2.2R, R171/R172 22R, R173 1.5k, R174 1M, C186/C187 4.7u: PCM2902C reference (usb-audio-notes.md, datasheet Fig. 39). No cuts.
- R175/R176 100k to GND after C186/C187 define the DC of USB_AUDIO_L/R, which fans out to C230 (headphone branch) and C200 (ADC branch). See merge M1.

Source_Select_ADC
- A: C212 VREF, C213-C216 LDO/AVDD (0.1u + 10u per PCM1862 DS), C217-C219 DVDD/IOVDD, C220 U22 COUT 1u, C221/C224/C225 U22/U23 1u, C226/C227 crystal caps, R209/R210 I2C pull-ups (separate 3V3_AUDIO bus; cannot merge with the 3V_AO CTRL bus because of power gating), C200-C205 input coupling.
- B: R200-R205 100R, R206-R208 33R I2S series, R211/R212 pull-downs.
- C: C206-C211 10 nF C0G RC (R200-R205 + C = fc 159 kHz) are optional anti-alias filters on an oversampling ADC whose DS shows only AC coupling; 6 parts. Bench-check noise before removing.
- D: C222 1u + C223 10u on 3V3_AUDIO: TPS7A2033 needs only 1u COUT (C220); the rail already has 10u (C218) plus Headphone/Amp local caps (14 caps on one rail). Verify placement before cutting.

Headphone_Aux
- A: C236 VMID 4.7u, C237/C238 TS5A23157 bypass, C239/C240 input caps and C241, C243/C244, C245 TPA6132A2 reference (U10), R232/R233 VMID divider, R239/R241 tip detect, R243/R244 AUX termination.
- B: R220-R225 VMID bias, R226-R231 1k series into the mux (power-off ESD/back-power), R234-R238 default pull-downs (HP_EN, HP_SEL_A/B, G0/G1), R240/R242, C246.
- D: C242 100 nF in parallel with C241 1u on the same 3V3_AUDIO supply of U10 (TPA6132A2 DS shows 1u at CPVDD only): cut. C230-C233 see merge M1. C234/C235 must stay (AUX jack is ground-referenced, needs level shift to VMID).

Amplifiers
- A: TAS5825M DVDD C280/C281/C293/C294, VR_DIG/GVDD/AVDD C282-C284/C295-C297, bootstrap C285-C288/C298-C301 (Table 66, Fig. 159 PBTL), PVDD 100n C276/C278/C289/C291, output 0.68u C302-C307; TPS61088 C265 VCC, C266 SS, C267 boot, C268/C269/R254 comp, R250/R251 FB (11.93 V), R252 FSW, R253 ILIM, ADR R261, R262 FAULTZ pull-up.
- B: R255/R257-R259 default-off, R256 DNP; C260 100n SYS_RAW; C270 1u PVDD; C271-C279/C290/C292 8x22u 25V + C275 100u on the 12 V rail; C261-C264 4x22u on SYS_RAW.
- D: R260 0R to GND on ADR: tie the strap pin directly to GND (DS ADR GND strap), saves a part and a BOM line. C263/C264 and C279/C292 are bulk extras.
- Calc, SYS_RAW (TPS61088 VIN): 22u 10V 0805 at ~4 V ~60% -> 13u, with tolerance/temp ~10u. 2 caps = 20u vs TPS61088 CIN >=10u effective; SYS_RAW already carries 3x22u charger (C104/C105/C107), C140, C150, so 4 amp-side caps are excessive; keep 2.
- Calc, 12 V rail: 22u 25V 0805 X7R at 12 V ~35-40% -> ~8u (6u worst). Eight caps ~50-64u + C275 100u. Output ripple dV = Iout*D/(fsw*C) = 2 A*0.75/(0.5 MHz*C): 148u -> 20 mV, 124u -> 24 mV (ESR ignored). Two fewer 22u costs ~12u: acceptable but class-D burst transients must be benched; keep 2x22u + 100 nF per amplifier PVDD per DS plus bulk.

### Merge M1 (audio coupling, medium risk, saves 8)
Currently USB and BT each have C186/C187 or C194/C195 (4.7u coupling), then R175/R176 or R180/R181 100k to GND on the node, then C230-C233 1u into a VMID-biased node (R220-R223). Bias USB_AUDIO_L/R and BT_AUDIO_L/R directly with R220-R223 to VMID_HP, delete C230-C233 and R175/R176/R180/R181. The ADC branch keeps its own C200-C203 so DC offset of the node does not matter there. Risks: VMID start-up now charges 4.7u (tau ~0.47 s instead of 0.1 s) which can thump when 3V3_AUDIO is enabled; VMID collapse with codec still powered leaves the Bluetooth/USB codec output biased at 0. Mute by default (mux/EN default off) mitigates; bench the pop and re-check codec output DC limits.

## 3. Ranked proposals

| # | Change | Refs | Saved | Risk | Recommendation |
|---|---|---|---|---|---|
| 1 | Remove bypass on grounded VIN_3V3 | C185 (R12 -> direct GND, verify) | 1 (+1) | low | apply (R12 after DS check) |
| 2 | Drop extra 100 nF beside 10u/22u on charger | C113, C114, C115 | 3 | low | apply |
| 3 | Dedupe 100 nF on BAT_PACK | C121, C126 | 2 | low | apply |
| 4 | Drop VREF+ caps (VREF+ = VDDA) | C163, C164 | 2 | low | apply |
| 5 | Drop 100 nF on TPS63802 inputs | C143, C151 | 2 | low | apply |
| 6 | Drop U10 100 nF parallel to 1u | C242 | 1 | low | apply |
| 7 | ADR strap resistor to direct GND | R260 | 1 | low | apply |
| 8 | 3V_AO bypass on 3 TS5A3167 | C131, C132 | 2 | low-med | apply-after-layout |
| 9 | Third 3V8 output cap | C154 | 1 | low-med | apply-after-bench |
| 10 | SYS_RAW bulk at amplifier boost | C263, C264 | 2 | low-med | apply-after-bench |
| 11 | Duplicate 3V3_AUDIO bulk | C222, C223 | 2 | low-med | apply-after-bench (placement) |
| 12 | ALRT pull-up via MCU internal PU | R122 | 1 | low-med | apply-after-bench |
| 13 | Merge audio coupling/bias (M1) | C230-C233, R175, R176, R180, R181 | 8 | med | apply-after-bench |
| 14 | Remove ADC anti-alias caps (keep 100R) | C206-C211 | 6 | med | apply-after-bench (noise) |
| 15 | Two PVDD bulk caps | C279, C292 | 2 | med | apply-after-bench |
| - | Keep (documented margin/protection): C109, C107, C142, C153, C184, C141/C142, R103/R107/R110/R111, R112/R113, R152-R154, R182/R185-R187, R220-R231, R234-R238, R142, R255-R259, TVS/ESD, series R on back-power nets | | 0 | high if cut | keep |

## 4. Totals
- Low-risk (#1-#7, with R12 held back): 12 passives saved -> 249 (261 -> 249). With R12: 13.
- Plus low-med (#8-#12): 8 more -> 241.
- Plus med bench items (#13-#15): 16 more -> 225 (-36, -14%).
- Resulting BOM lines: current 106 grouped rows (63 passive). Low-risk cuts remove the 4 rows with unique raw value text (C185, 0.1uF/50V C113-115, 100nF 10V X7R C143/C151, R260 0R) -> about 102. Normalizing value strings (100nF/0.1uF/100nF X7R 10V, 100/100R, 1uF...) collapses the 63 passive rows to ~45 distinct electrical value+package lines, i.e. about 85-88 total rows. Grouping BOM by value+footprint rather than raw text is the biggest line-count win and costs no parts.
- Not removable without function loss: ~150 required parts.

## 5. Why the count is high
1. About 12 ICs, several with 3-8 supply/internal-rail pins: TAS5825M (x2) alone takes 18 caps each side (PVDD, DVDD, VR_DIG, GVDD, AVDD, 4 bootstraps, 3 output caps/filters), PCM1862 12, PCM2902C 11, BQ25792 16.
2. 12 audio networks: 6 input paths each with coupling cap, bias R, series R and RC (about 36 parts) plus 4 codec output coupling/DC-ref parts.
3. Bulk caps in parallel: SYS_RAW 9x22u, 3V3_AUDIO 14 caps on one rail, PVDD 8x22u+100u, because 0805 X7R lose 40-65% under bias (calcs above).
4. Default-off and back-power protection: ~25 pull-downs/pull-ups (100k x33 is the single largest group) and 14 series resistors, all intentionally required by the power-gating architecture.
5. Three I2C buses (PD on LDO_3V3, CTRL on 3V_AO, AUD on gated 3V3_AUDIO) each with its own pull-ups (6 R); they cannot be merged for domain/back-power reasons.
6. Datasheet RC items: CC filters, ADC dividers, feedback/compensation networks for 3 converters and a boost.
Most of the avoidable count is in a handful of duplicated 100 nF/bulk caps; a first pass of 12 low-risk cuts plus BOM value normalization addresses the line count without touching protection.
