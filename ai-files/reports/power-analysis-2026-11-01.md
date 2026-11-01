# Power analysis 2026-11-01: standby budget, TVS clamp, PPHV capacitance/inrush, charge policy

Analysis only. No schematic, board, library, plan or handover file was edited. Builds on `replacement-power-control-contract.md`, `5-20v-pd-front-end-review.md`, `bq25792-*.md`, `audio-chain-architecture.md` and `mcu-pin-allocation.md` (not repeated here). Net/part membership was read from the current `DesktopSpeaker.kicad_pcb` (360 footprints) and the schematic MPN properties, not from the stale 2026-10-05 netlist.

Conventions: "typ" = datasheet typical (25 C unless noted), "max" = datasheet maximum (85 C or full range where the datasheet says so), "est." = my arithmetic, "ASSUMPTION" = not from a datasheet. Page numbers are the printed datasheet page. Where a figure comes from a proxy part or a web page rather than a local PDF this is stated.

---

## 1. Standby / storage current budget

### 1.1 What is actually always on (from the board netlist)

- BAT_PACK (always live while SW101 is closed): Q103 drain, U5 MAX17048 VDD, U21 TPS3839 VDD, R127 gate pulldown (U21 output is push-pull high above 3.0 V so R127 conducts), R112 to U4 BATP, C120/C126.
- In ship mode (SDRV_CTRL=10) Q103 and the BATFET are off, so BAT_INT, SYS_RAW, U20 TPS2116, U12 TPS7A0230, 3V_AO, the MCU, U14/U15/U25 and everything behind them are dead. Only the BAT_PACK items above and U4 BATP remain.
- With the SFET on and no USB (electronic-off / idle): SYS_RAW feeds U20 (TPS2116 VIN2, SYS_RAW is VIN2 and USB_AUX_5V is VIN1 in priority mode) -> U12 -> 3V_AO. 3V_AO feeds U3 MCU, U13/U16/U17 TS5A3167, R126 (ISO_N pull-up), R241 (AUX_DET 1 M), I2C pull-ups (idle high: no current), J7.
- SYS_RAW also feeds U14 and U15 (TPS63802, EN low), U25 TPS61088 (EN low, 100 k pulldown) and, through U25's high-side body diode, PVDD_AMP (about SYS_RAW minus one diode drop). PVDD_AMP carries the 499 k/56 k feedback divider (R250/R251) and both TAS5825M PVDD pins (PDN held low). This path has no load disconnect (already recorded in `audio-chain-architecture.md` section 3).
- TVS/ESD: D6 TVS2200 and D7 1N5819HW sit on raw USB_VBUS only; D1/D5 on USB data/CC; D200/D201 PESD5V0S2BT on headphone/aux audio lines. No TVS is on BAT_PACK, SYS_RAW or 3V_AO. With no USB their leakage contributes nothing (no DC across them).
- REGN-referenced networks (R100/R101 TS divider, R108/R109/R110 ILIM_HIZ, R103 CE pull-up) draw only when REGN is on. BQ25792 §9.3.3 p.27 ("The REGN LDO stays off to minimize the quiescent current" in battery-only mode): REGN is off on battery, so they cost 0 in all three states.

### 1.2 Table (uA; typ / max)

State columns: **A** ship mode (SDRV_CTRL=10, QON or USB wakes); **A'** shutdown mode (SDRV_CTRL=01, wakes on adapter only, optional); **B** electronic-off (SFET on, all switched rails off, MCU Stop 1, wakes on button/PD_PLUG_EVENT/ALRT); **C** idle-awake, BM83 off, rails off, MCU running about 2 % duty. BQ25792 ADC assumed disabled.

| Consumer | A ship | A' shutdown | B elec-off | C idle-awake | Source (datasheet, section/page) and notes |
|---|---|---|---|---|---|
| U4 BQ25792 | 11 / 16 | 0.5 / 0.7 | 17 / 24 | 17 / 24 | BQ25792 SLUSDG1C §8.5 p.9: IQ_BAT_ON / IQ_BAT_OFF (ship), ISD_BAT (shutdown), IQ_BAT_ON (battery only, I2C on, ADC off), TJ<85 C. **Tested at VBAT = 8 V (2S); no 1S figure is given.** ADC enabled would be 540 typ (same table), so the ADC must stay off in standby. |
| U5 MAX17048 | 3 / 5 | 3 / 5 | 3 / 5 | 3 / 5 | MAX17048 DS p.2: IDD0 hibernate, reset comparator enabled (default). Active is 23 / 40, sleep 0.5 / 2 (needs firmware: MODE.EnSleep and CONFIG.SLEEP, or SCL/SDA low > 2.5 s). Hibernate is automatic at low current, so in ship mode (battery static) it should be in hibernate; unverified. |
| U21 TPS3839 | 0.15 / 0.5 | 0.15 / 0.5 | 0.15 / 0.5 | 0.15 / 0.5 | TPS383x SBVS193D electrical characteristics, IDD (output not connected). |
| R127 1 M (U21 OUT to GND) | 3.7 / 4.25 | 3.7 / 4.25 | 3.7 / 4.25 | 3.7 / 4.25 | est. VBAT/1 M (3.7 V typ, 4.2 V + 1 % max). Always on while the pack is above the 3.0 V threshold. |
| Q103 CSD17579Q3A off leakage | 0.05 / 1 | 0.05 / 1 | n/a | n/a | CSD17579Q3A IDSS 1 uA max at VDS 24 V (DS electrical table); typ not given, 0.05 is an ASSUMPTION; at 4.2 V the real value is far below max. |
| U20 TPS2116 (VIN2 powers VOUT) | 0 | 0 | 1.35 / 3.7 | 1.35 / 3.7 | TPS2116 DS §6.5 p.5, IQ,VIN2: typ 25 C, max -40..85 C. PR1 pin leak 0.1 max. Dead in A/A' (SYS_RAW off). |
| U12 TPS7A0230 | 0 | 0 | 0.1 / 0.2 | 0.1 / 0.2 | TPS7A02 §6.5: IGND 25 nA typ / 60 nA max (IOUT=0, 85 C) plus 1 % of load (IGND/IOUT, 5 uA-1 mA range). |
| U3 STM32G071 | 0 | 0 | 3.4 / 15 | ~33 / ~45 | STM32G071 DS12232 Rev 2, Table 29 p.64: Stop 1, 3.0 V, RTC off, flash not powered: 3.4 typ / 15 max at 25 C (33 typ / 135 max at 85 C). **Column C** adds an ASSUMED 2 % duty of Run at 16 MHz (about 1.5 mA, from about 94 uA/MHz, Table 26) = +30. Standby alternative: 0.20 / 0.9 (Table 30 p.64, RTC off) but see 1.4. |
| MCU GPIO leakage | 0 | 0 | 0.1 / 2 | 0.1 / 2 | ASSUMPTION (not in IDD tables). |
| R126 1 M (3V_AO to GAUGE_ISO_N, Q104 on) | 0 | 0 | 3.0 / 3.1 | 3.0 / 3.1 | est. 3.0 V/1 M. Q104 is on whenever U21 OUT is high, i.e. VBAT above its threshold. |
| R241 1 M (3V_AO to AUX_TIPSW, no plug) | 0 | 0 | 3.0 / 3.1 | 3.0 / 3.1 | est. 3.0 V/(1 M + 10 k). Matches the "3 uA AUX_DET" in `audio-chain-architecture.md`. Zero when a plug is inserted. |
| U13/U16/U17 TS5A3167 (3 devices) | 0 | 0 | 0.003 / 0.9 | 0.003 / 0.9 | TS5A3167 DS electrical characteristics (3.3 V supply table): ICC 0.001 typ / 0.05 max (25 C), 0.3 max over temperature, at 3.6 V, each. Off-leakage (0.5 nA typ) negligible; powered-off port leakage (0.1 typ / 5 uA max) only matters with voltage across it (none in ship). |
| U25 TPS61088 shutdown | 0 | 0 | 1 / 3 | 1 / 3 | TI TPS61088 DS ISD (EN=0, no FB divider, TJ<=85 C), obtained from the TI online datasheet via web search; **the local PDF is missing** (HANDOVER open item). |
| U6+U7 TAS5825M PVDD shutdown (PDN low) | 0 | 0 | 15.6 / ~31 | 15.6 / ~31 | TAS5825M DS §7.5: ICC(PVDD) shutdown 7.8 uA typ each at PVDD=13.5 V, **typ only, no max given**; the max shown is an ASSUMED 2x. PVDD is only about 3.3 V here (below the 4.5 V minimum) so the real value is probably lower. DVDD shutdown (7.4 typ) is not counted: 3V3_AUDIO is off. |
| PVDD feedback divider R250+R251 (555 k) | 0 | 0 | 6.0 / 7.5 | 6.0 / 7.5 | est. (VBAT - ~0.5 V)/555 k. |
| U14 + U15 disabled | 0 | 0 | 0.09 / 1.2 | 0.09 / 1.2 | TPS63802 DS electrical characteristics: ISD into VIN 45 nA typ / 600 nA max (EN low, VIN 3.6 V, 85 C), each. |
| D6 TVS2200, D7, D1/D5, D200/D201 | 0 | 0 | 0 | 0 | No VBUS present. For reference with VBUS at 20 V: TVS2200 ILEAK 3.5 nA typ / 62 nA max (27 C), 400 nA max (85 C), 1.3 uA max (105 C), DS §7.6 p.5. D7 1N5819HW reverse leakage at 20 V hot is NOT quantified (datasheet not in repo); it only affects USB-plugged idle, not battery standby. |
| **Total (sum of the rows)** | **17.9 / 26.8** | **7.4 / 11.4** | **57.5 / 104.7** | **87.5 / 134.7** | Sum of maxima is pessimistic. At 85 C add roughly +120 (MCU Stop max 135 vs 15). |

Not in the board budget (ASSUMPTIONS): pack protection IC and cell self-discharge. A protection IC typically costs a few uA; cell self-discharge for Li-ion is commonly 1.5-3 % per month, which for 10 Ah is the equivalent of roughly 210-420 uA continuous. Pack unselected, no figure available.

Variants (est., same table): state B with MCU in Standby 54.3 / 90.6; B with gauge in sleep 55.0 / 101.7; B without the PVDD path (22.6 typ / 41.7 max removed) 34.9 / 63.0; B with R126, R127, R241 raised to 10 M (leaves about 0.9) 48.7 typ.

### 1.3 Self-discharge days for a 10 Ah pack (board load only, nominal 10 Ah)

| State | Typ uA | Days to empty (typ) | Max uA | Days to empty (max) | Days to lose 10 % (typ / max) |
|---|---|---|---|---|---|
| A ship | 17.9 | about 23 300 (64 y) | 26.8 | about 15 500 (43 y) | 2 330 / 1 550 |
| A' shutdown | 7.4 | about 56 300 | 11.4 | about 36 600 | 5 630 / 3 660 |
| B electronic-off | 57.5 | about 7 250 (19.8 y) | 104.7 | about 3 980 (10.9 y) | 725 / 400 |
| C idle-awake | 87.5 | about 4 760 (13 y) | 134.7 | about 3 090 (8.5 y) | 475 / 310 |
| C' rails on, audio idle, BM83 off (est., section 1.5) | about 3 700 | about 113 | | | 11 |

Days = 10 Ah / I / 24 (ideal, no cell self-discharge, no cutoff reserve). Even state B is irrelevant next to cell self-discharge (about 200-400 uA equivalent); the board load matters mainly for depleted-pack protection (the gauge and U21 keep draining a pack that is already low, so a low-battery software cutoff plus ship mode is the real protection) and for "ship it and shelve it" claims.

### 1.4 What dominates

1. State A: BQ25792 (11 of 17.9 typ, 61 %), then R127 (3.7, 21 %) and the gauge (3, 17 %). Using shutdown mode instead of ship cuts the total to 7.4 typ but removes the QON button wake (adapter plug-in only, BQ25792 §9.3.12.1 p.47). I2C is disabled in shutdown, so the charger restarts from POR defaults (full register reset assumed, not stated).
2. State B: the PVDD path (22.6 typ, 39 %; unverified, the TAS figure is a 13.5 V number), the BQ25792 (17, 30 %), then three 1 M resistors worth 9.7 (R126, R127, R241), the MCU (3.4 typ but 15 max, 135 max at 85 C), the gauge (3).
3. State C: MCU duty dominates the addition; the BQ25792 ADC (540 typ) would swamp everything if left on.
4. Standby wake limitation: `mcu-pin-allocation.md` shows PD_PLUG_EVENT (PC14) is EXTI-only, so "wake on USB attach" needs Stop (3.4 / 15), not Standby (0.20 / 0.9). Only PA0 (ALRT) and PC13 (QON) are WKUP pins. Moving the attach event to a WKUP pin would save about 3-14 uA in state B.
5. Zero-cost-to-the-board levers, listed without changing the design: gauge sleep before ship/off (about 2.5 typ), shutdown instead of ship for long storage, PDN/boost off sequence already assumed, raise R126/R127/R241 (bench-check Q104 gate and AUX_DET RC first), SW101 open removes everything.

### 1.5 Rails-on audio idle (estimate for scale, not datasheet-closed)

5V_LOGIC, 3V3_AUDIO and PVDD on, amplifiers in Deep Sleep, no signal, BM83 off: 2 x TAS5825M Deep Sleep DVDD 0.82 mA (DS §7.5), PCM1862 standby about 0.2 mA, VMID 35 uA, TPS61088 about 110 uA from PVDD (as recorded in `audio-chain-architecture.md`), TAS PVDD Deep Sleep 12 uA each. Power about 13 mW at 85 % conversion, about 3.5-4 mA from the pack at 3.7 V (est.), plus the table C items. Bench step D6 / T5 should replace this.

### 1.6 Caveats

- IQ figures for the BQ25792 are at VBAT 8 V (§8.5 p.9). The 1S value is not stated; plan on bench measurement (bench plan B1.15, T5, T6).
- The old 35-37 uA figure (BQ25895 era) is replaced. The prior bench estimates "40-80 uA standby" and "18-45 uA ship" in `bench-bringup-plan.md` bracket these totals on the low side for standby (57 typ / 105 max here) and agree for ship.
- QON pull-up into R113/PC13 with the MCU unpowered (ship mode): PC13 is an FT pin; backfeed into 3V_AO is not expected but not proven; measure 3V_AO in ship mode.

---

## 2. TVS2200 (D6) clamp versus the TPS25730D 28 V absolute maximum

### 2.1 Datasheet limits used

- TPS25730 SLVSGP9 §6.1.1 p.8: VBUS_IN, VBUS absolute maximum 28 V (recommended maximum 22 V, §6.3.1 p.9). Footnote (4) on that table says: "A TVS with a break down voltage falling between the Recommended max and the Abs max value is recommended such as TVS2200." So TI itself endorses this pairing. TVS2200 VBR 24.6 / 25.9 / 27.6 V (min / typ / max, 1 mA, §7.6 p.5) is inside that window.
- TVS2200 SLVSED5C §7.6 p.5 (VCLAMP, IO to GND, 8/20 us, VIN=0 before surge, 27 C): 24 A 27.2 typ / 27.7 max; 40 A 27.6 typ / 28.0 max. 35 A at 125 C with VIN=VRWM before the surge: 27.8 typ / **28.35 max**. RDYN 30 mOhm (typ). Absolute maximum surge current 40 A (8/20 us), 5 A (10/1000 us), §7.1 p.4. VRWM 22 V. Clamp ratio 27.7/22 = 1.26, the lowest-ratio 22 V device in the family (§5 p.3 table); the next, TVS2700, clamps 32.5 V.
- BQ25792 downstream (SLUSDG1C §8.1 p.8): VBUS/PMID absolute maximum 30 V (converter not switching); VBUS_OVP falls at 25.2-26.2 V (§8.5 p.10). So the charger has 1.65 V of margin over the worst clamp; the PD controller is the limiting part.
- I did not read values off Figs 7-1/7-2 (waveform plots); the datasheet's tabulated points above are the numbers used. Extrapolations are marked.

### 2.2 Surge model

IEC 61000-4-5 combination wave: short-circuit current peak I = (Voc - Vclamp) / Rs, 8/20 us. Rs = 2 ohm (DC power port, line-to-line), 12 ohm (line to earth), 42 ohm (signal-line coupling; this is the condition TVS2200 claims, "1 kV, 42 ohm"). Clamp estimate: linear interpolation between the datasheet points (slope 0.019 V/A on the max column, 0.030 V/A RDYN beyond 40 A, flagged), plus +0.44 V for 125 C (the hot max point at 35 A is 0.44 V above the 27 C max curve at the same current).

| Voc | Rs | Surge current | Clamp typ | Clamp max 27 C | Clamp max 125 C | Over 28 V (max, hot) | Within 40 A rating? |
|---|---|---|---|---|---|---|---|
| 0.5 kV | 42 | 11 A | 26.9 | 27.5 | 27.9 | none (-0.1) | yes |
| 1 kV | 42 | 23 A | 27.2 | 27.7 | 28.1 | +0.13 V | yes |
| 2 kV | 42 | 47 A | 27.8 | 28.2 (ext.) | 28.7 (ext.) | +0.65 V | **no (47 A > 40 A)** |
| 4 kV | 42 | 95 A | 29.2 | 29.6 (ext.) | 30.1 (ext.) | +2.1 V | **no** |
| 0.5 kV | 12 | 39 A | 27.6 | 28.0 | 28.4 | +0.43 V | marginal |
| 1 kV | 12 | 81 A | 28.8 | 29.2 (ext.) | 29.7 (ext.) | +1.7 V | **no** |
| 0.5 kV | 2 | 236 A | 33.5 | 33.9 (ext.) | 34.3 (ext.) | +6.3 V | **no (6x)** |
| 1 kV | 2 | 486 A | 41.0 | 41.4 (ext.) | 41.8 (ext.) | +13.8 V | **no (12x)** |

Voc that just reaches 40 A: 108 V (2 ohm), 508 V (12 ohm), 1 708 V (42 ohm).

### 2.3 Answer

- **Inside the datasheet's rated range (current <= 40 A, i.e. up to 1 kV through 42 ohm, or about 0.5 kV through 12 ohm):** the maximum clamp is 28.0 V at 27 C and 28.35 V at 125 C. The 28 V absolute maximum is therefore met with zero margin at room temperature and **exceeded by up to 0.35 V (1.25 %) hot** (up to about 0.45 V by the estimate above at equal current). The typical value (27.2-27.6 V) is 0.4-0.8 V inside the limit.
- **Beyond 40 A:** exceeded by roughly 0.2-0.7 V at 2 kV/42 ohm and 2 V at 4 kV/42 ohm (extrapolation), but then the TVS is also outside its own 40 A rating.
- **2 ohm and 12 ohm coupling:** TVS2200 alone cannot withstand even 0.5 kV; this part gives no meaningful IEC 61000-4-5 power-port immunity. The datasheet claim is 1 kV/42 ohm only.
- 28 V is an absolute-maximum (no-damage) rating, and a 20-30 us plateau at 28.0-28.35 V is 0-1.3 % over it. TI recommends exactly this device for this pin, so the pair is the vendor's own recommendation, but no pulse-rated allowance is documented; this is not a proven surge rating.

### 2.4 Additional risk, model-based, UNVERIFIED: ringing between D6 and U11

Board file centres: D6 is about 9 mm from J1 and about 26 mm from U11 (VBUS_IN pads 23/32); the U11-side ceramics are C2 (4.7 uF), C184 (1 uF) near U11 and C316 (1 uF) 5 mm from D6. The 26 mm F.Cu run is about 8-25 nH (ASSUMPTION: 0.3-1 nH/mm). Against the effective raw-side capacitance at high bias (about 3.5 uF, section 3.4) this gives Z0 = sqrt(L/C) of 46-80 mOhm with trace plus ESR of about 20-35 mOhm: damping ratio about 0.2-0.35, so an ideal fast clamp step could overshoot by 33-54 % of the step at U11 (step = clamp voltage minus pre-surge voltage: about 8 V from a 20 V contract, about 22 V from a 5 V contract, so up to +3 to +4 V or +7 to +12 V). This is an upper bound from a lumped ideal-step model; the TVS dynamic resistance, source impedance and real plane coupling reduce it, possibly by a factor of two or more. It cannot be dismissed from the datasheets alone; it needs a bench check (surge/ESD generator or a fast step injected at J1 with a probe at U11 VBUS_IN) or a SPICE run with TI's TVS2200 model (not checked whether the model is published).

### 2.5 Mitigation options (listed, not applied)

1. Accept and label: TI-recommended pairing; no surge-immunity claim; for a consumer product the USB DC port is normally not surge-tested (ASSUMPTION; check the intended product standard).
2. Verify on the bench first (section 2.4): this decides whether anything else is needed.
3. Damping at U11: RC branch across C2/C184 (for example 4.7 uF/50 V in series with about 0.2-0.5 ohm) or a small series bead in the C2 branch; values need simulation.
4. Second-stage clamp or lower-clamp device at the IC: no lower-ratio 22 V flat-clamp exists in the TI family; a lower-voltage TVS would fall below the 20 V (21 V with tolerance) operating range, so a second stage cannot reduce the clamp below about 25-27 V without conducting on a legal 20 V contract.
5. Two TVS2200 in parallel: at 40 A total each carries about 20 A, giving about 27.6 V max (27 C) / 28.1 V hot; sharing is unreliable because VBR spreads 24.6-27.6 V, so the lower-VBR part takes most of the current.
6. Series pass element ahead of the IC that opens on overvoltage (surge stopper/eFuse with at least 40 V rating): `LTC4368-2-protection-redesign-candidate.md` and `power-protection-fix-options.md` already cover this class; it costs drop and board area and was rejected earlier for the 5 V cable case.
7. Move or add a TVS/cap stage physically at U11 (layout change, not done).
8. Operationally nothing in the contract lowers the clamp; limiting PD to 15 V does not help (the clamp is voltage-fixed by the TVS).

---

## 3. VBUS_PD bulk capacitance and attach inrush

### 3.1 Capacitors on the actual nets (schematic MPN properties)

| Net | Reference | Value / MPN | Notes |
|---|---|---|---|
| USB_VBUS (raw, TPS25730 VBUS_IN) | C2 | 4.7 uF X7R 50 V 0805, TDK C2012X7R1H475KT0A0E | |
| | C184, C316 | 1 uF X7R 50 V 0805, Samsung CL21B105KBFNNNE (x2) | Samsung curve in repo: 0.70 uF at 20 V |
| | D6 TVS2200 | 105 pF typ (§7.6) | |
| VBUS_PD (TPS25730 PPHV and BQ25792 VBUS/VAC1/VAC2) | C100, C111 | 10 uF X5R 50 V 0805, Murata GRM21BR61H106KE43L | |
| | C315 | 47 uF X5R 25 V 1206, Murata GRM31CR61E476ME44L | 25 V part on a 20-21 V rail (ratio 0.8-0.84) |
| | C313 | 100 nF X7R 50 V 0402, Murata GRM155R71H104KE14D | |
| PMID (BQ25792 behind the VBUS-PMID input-sense element, pin table: "input current sensing circuit is connected between VBUS and PMID") | C101, C108, C112 | 10 uF X5R 50 V 0805 (same Murata part, x3) | |
| | C312 | 100 nF | |

Nominal totals: raw VBUS 6.7 uF; PPHV (VBUS_PD) 67.1 uF (47 + 10 + 10 + 0.1); PPHV + PMID 97.2 uF. The handover's "about 97 uF" is the PPHV + PMID figure. Note that the older review `bq25792-vbus-pmid-ceramic-review.md` assumed Samsung CL32B106KBJNNNE (1210 X7R, 5.04 uF at 21 V); the board now uses Murata 0805 **X5R**, which is expected to bias-derate the same or worse.

### 3.2 DC-bias derating (method and proxies)

No Murata curve for GRM21BR61H106KE43L or GRM31CR61E476ME44L is in the repo, and the Murata sheets found online ("typical specification" PDFs from distributors) carry no bias chart. **PROXY, ASSUMPTION:** Samsung typical curves from `samsung-mlcc-dcbias-estimates.json` and `Samsung_CL32B106KBJNNN_DCBias_25C_1kHz.json` (25 C, 1 kHz): 10 uF/50 V class retention 94 % / 83 % / 65 % / 53 % at 5 / 9 / 15 / 20 V; 22 uF/25 V class retention 80 % / 52 % / 32 % / 23 % at 5 / 9 / 15 / 20 V (applied to the 47 uF part). Low case multiplies by tolerance and temperature (10 uF parts x0.9 x0.85; 47 uF part x0.8 x0.85); high case by +10 % / +20 % tolerance. Samsung 1210 X7R is likely optimistic for 0805 X5R. Get the Murata SimSurfing curves before relying on these.

### 3.3 Effective capacitance versus the TPS25730 limit (TPS25730 SLVSGP9 §6.4 pp.9-10)

Limit: CPPHV (TPS25730D): NOM 47 uF, MAX 100 uF, no MIN printed, rated 25 V. Footnote (1): "Capacitance values do not include any derating factors": the table values are effective values, so derating must be applied to the capacitors fitted.

Effective PPHV capacitance, uF (low / typ / high):

| VBUS_PD bias | PPHV only | PPHV + PMID |
|---|---|---|
| 0 V (start of ramp) | 47 / 67 / 79 | 70 / 97 / 112 |
| 5 V | 40 / 56 / 66 | 62 / 85 / 97 |
| 9 V | 30 / 41 / 48 | 49 / 66 / 75 |
| 15 V | 20 / 28 / 32 | 35 / 48 / 54 |
| 20 V | 16 / 22 / 25 | 28 / 37 / 42 |

- **100 uF maximum:** PPHV alone never exceeds it (79 uF worst). PPHV + PMID reaches 112 uF only at zero bias with simultaneous +tolerance on every part (and only if the BQ25792 VBUS-PMID path conducts at that moment); at any real bias it is under 100 uF. Verdict: OK.
- **47 uF NOM:** effective PPHV is about 56 uF typ at 5 V but about 41 (9 V), 28 (15 V) and 22 uF typ (16-25 range) at 20 V, i.e. 33-53 % of NOM at 20 V. No MIN is published and TI does not say what NOM protects (stability, OVP response, sink-path behaviour are not stated), so the consequence is unknown. This is the only point of concern. Options (not applied): fit a higher-voltage-rating bulk part at C315 (for example 2 x 22 uF 50 V/35 V class, then re-check the 100 uF maximum at low bias); or accept and bench (load-step and hot-unplug waveforms on VBUS_PD at 20 V, not covered by any datasheet figure).
- BQ25792 minima (§8.3 pp.8-9, effective): CVBUS 2 uF (C100+C111: 8-12 uF at 20 V, passes), CPMID 4 uF (C101+C108+C112: 12-16 uF at 20 V, passes even at 25 % retention).
- Raw side, TPS25730 CVBUS 1 / 4.7 / 10 uF (§6.4 p.10): nominal 6.7 uF is within 1-10; effective about 5.9 uF at 5 V and about 3.5 uF at 20 V (C2 retention ASSUMED 0.85 / 0.45 at 5 / 20 V; the 1 uF parts 0.93 / 0.70). Within limits.

### 3.4 Attach inrush

- **Cable attach (always vSafe5V, even for a 20 V PD source):** the TPS25730 sink path is off; the load is the 6.7 uF raw bank (about 5.9 uF effective at 5 V, charge about 30 uC). Hot-plug ringing on the cable inductance can reach about 2x 5 V = 10 V, well below the 22 V standoff. Not a concern.
- **Sink-path enable (PPHV soft start):** TPS25730 §6.8 p.12 "SS" 2.8 / 3.3 / 3.8 V/ms (min / typ / max); §6.8 p.13 tPPHV_ON 1.5 / 1.8 / 2.1 ms to 5 V (soft-start setting 3, no cap). Inrush I = C x dV/dt:
  - PPHV only: **0.22 A typ** (67 uF x 3.3 V/ms), **0.30 A max** (79 uF x 3.8 V/ms).
  - PPHV + PMID: **0.32 A typ**, **0.42 A max**.
  - Declines as bias grows (to 0.12 A typ at 20 V PPHV-only). Ramp time 5 V / 20 V: about 1.5 ms / 6.1 ms (5.3-7.1 ms). Charge delivered about 0.32-0.46 mC at 5 V and 0.84-1.3 mC at 20 V; dissipated in the PPHV switch roughly 1/2 x Q x V, about 8-13 mJ at 20 V (est., not a datasheet figure; the datasheet gives no SOA for this event).
  - Versus a non-PD 0.5 A default source: 0.42 A worst plus the AUX/PD overhead leaves a thin margin; versus 1.5 A or a PD contract it is comfortable. Remember it is the PPHV switch ramp, so the source sees this only after Rp/PD qualification.
- **Voltage transition (5 -> 9/15/20 V) with the sink path closed:** the source slews VBUS at up to 30 mV/us (ASSUMPTION: USB PD source slew limit, quoted from memory, not re-checked in a local spec), so I = C x 30 V/ms = 0.6-1.2 A (low), 0.8-1.7 A typ, up to 2.0 A PPHV only; adding PMID, up to 2.9 A at 5 V. Whether the TPS25730 holds PPHV closed or opens it during transitions is **not stated in the datasheet text available locally**; this is exactly why cSnkBulkPd is capped at 100 uF (§6.4 footnote 4). Bench item A2.6 should capture VBUS_PD and the source current during a 5 -> 20 V request.

---

## 4. Charge and input-current policy (PROPOSAL, needs user approval)

All values are proposals, defaults chosen from BQ25792 SLUSDG1C. REG numbers per §9.5.1. Register scaling: ICHG, IINDPM 10 mA/LSB; VREG 10 mV/LSB; VINDPM 100 mV/LSB; ITERM, IPRECHG 40 mA/LSB; VRECHG offset 50 mV + 50 mV x field.

### 4.1 Charge current ceiling

- **ICHG ceiling 3.0 A** (REG03 = 0x12C), about 0.3C for a 10 Ah pack, 1.5 A per cell for a 2P 21700 pack (cells unselected; confirm the cell datasheet's maximum standard charge). Normal default 2.0 A (0xC8, the BQ25792 1S POR default, Table 9-9) to keep U4/L1/PGND-via heating down until the bench step clears 3 A (handover: PGND via area unchecked, bench starts at 0.5 A).
- BQ25792 accuracy at 3 A is not tabulated; at 4 A/VBAT 8 V buck-mode it is -5.5 / +2.5 % (§8.5 p.12).
- ICHG (REG03), VRECHG, ITERM, precharge reset on watchdog and REG_RST; **VREG (REG01) and IINDPM (REG06) reset only on REG_RST** (register field notes). With CE held high by default (R103, CHG_ENABLE low) a dead MCU means no charging at all, so a post-reset 4.2 V default is not reached unattended.

### 4.2 Input limits by source

Rule: IINDPM = advertised current minus about 0.1 A (leaves room for the TPS25730, U19/AUX and 3V_AO draws, which sit upstream of the charger's input limit), capped at 3.0 A; the charger limit regulates input current to at most the setting (accuracy at 9 V: set 3.0 A -> 2.72-2.92 A, set 0.5 A -> 0.415-0.500 A, §8.5 p.13 "IINDPM_ACC", so the actual current never exceeds the setting). VINDPM about 88 % of the contract voltage (min 3.6 V). The charger reduces ICHG first (DPM), then the battery supplements (NVDC, §9.3.8.1-2) and the firmware sheds audio.

| Source | VINDPM | IINDPM | Max charge while idle (1 W load) | while playing 10 W | Notes |
|---|---|---|---|---|---|
| USB 5 V default 0.5 A / unknown | 4.4 V (0x2C) | 0.45 A (0x2D) | about 0.26 A | 0 (battery supplements) | conservative fallback for unclassified non-PD sources (Rp current not readable via TPS25730, see contract) |
| USB-C 5 V 1.5 A | 4.4 V | 1.40 A (0x8C) | about 1.4 A | 0 | |
| USB-C 5 V 3 A | 4.4 V | 2.90 A (0x122) | 3.0 A | about 0.7 A | |
| PD 9 V (up to 3 A) | 7.7 V (0x4D) | contract - 0.1 A, max 2.90 A | 3.0 A | 3.0 A | 26 W in |
| PD 15 V (up to 3 A) | 12.8 V (0x80) | same rule | 3.0 A | 3.0 A | 43 W in |
| PD 20 V (up to 3 A) | 17.0 V (0xAA) | same rule (2.9 A max; charger input 3.3 A recommended maximum, §8.3) | 3.0 A | 3.0 A | 58 W in; 20 V x 3 A is more than the system needs, so IINDPM never binds |

Charge-while-load columns are est.: (eta x V x IINDPM - Psys)/3.8 V with eta 0.88 at 5 V, 0.92 at 9-20 V (ASSUMED efficiencies), capped at 3.0 A. EN_ICO stays 0 (default), automatic D+/D- detection stays disabled, EN_IINDPM stays 1 (as in the contract). Respect the existing startup ordering and the contract's note that ILIM_HIZ/EN_EXTILIM override applies before raising IINDPM.

### 4.3 Float voltage and recharge for a mostly-plugged-in product

Recommended default: **VREG 4.10 V**, recharge 200 mV below (3.90 V), termination 400 mA. Offer three user-visible modes; ageing factors below are ASSUMPTIONS from commonly cited Li-ion behaviour (the cell is not selected, so no cell datasheet to check):

| Mode | VREG (REG01) | Approx. usable capacity vs 4.20 V | VRECHG (REG0A[3:0]) | Recharge at | Use |
|---|---|---|---|---|---|
| Full | 4.20 V (0x1A4, the 1S POR default) | 100 % | 3h = 200 mV (POR) | 4.00 V | travel / maximum run time |
| Longevity (proposed default) | 4.10 V (0x19A) | about 90 % | 3h = 200 mV (POR) | 3.90 V | normally on the dock |
| Storage-on-dock | 4.00 V (0x190) | about 80 % | 1h = 100 mV | 3.90 V | long plug-in with little use |
| 4.05 V / 4.15 V are 0x195 / 0x19F | | | | | |

- Rationale for 200 mV recharge window at 4.10 V: after termination the BATFET turns off and the converter powers the system (§9.3.9.3 p.41), so the pack rests between 4.10 V and about 3.90 V (roughly 60-85 % state of charge) instead of 100 %. A 100 mV window keeps it higher (more ageing) with no benefit; 200 mV is the POR value so no write is needed. VREG_ACC (§8.5 p.11) is tabulated only for 2S-4S (-0.85 to +0.65 %); no 1S figure is given, so assume about +/-0.7 %, roughly +/-30 mV at 4.10 V.
- **Termination:** ITERM 400 mA (REG09[4:0] = 0x0A) about C/25 for 10 Ah (POR is 200 mA, 0x05). Termination accuracy is +/-14 % at 480 mA (§8.5 p.12). Top-off timer (REG0E[7:6]) stays 0 (disabled); the comparator offset problem (§9.3.9.3) applies only at 40-160 mA.
- **JEITA/NTC:** the POR warm-zone rule lowers VREG by 400 mV (JEITA_VSET = 3h, REG17[7:5], §9.5.1.20). At a 4.10 V float that would be 3.70 V above about 45 C inside a warm enclosure; propose JEITA_VSET = 6h (-100 mV) so warm charging still reaches 4.0 V. Leave JEITA_ISETH = unchanged, JEITA_ISETC = 20 % (cool region).
- Timers: fast-charge CHG_TMR (REG0E[2:1]) 8 h (field 1h) instead of the 12 h default; TMR2X stays on (timer counts at half rate during DPM). Pre-charge timer 2 h and trickle 1 h unchanged (Table 9-9).
- Gauge consequence: MAX17048's default model reports about 100 % at 4.20 V, so at a 4.10 V float it will read roughly 85-90 % while the charger reports charge done (CHG_STAT = 111, §9.3.9.1). Firmware should map CHG_STAT = 111 to 100 % (or re-run the gauge model); not a hardware issue.
- Plugged-in idle input draw: BQ25792 IQ_VBUS 3 mA typ (5 mA with out-of-audio enabled) at 15 V, charge disabled, converter switching (§8.5 p.9) = about 45-75 mW before the TPS25730, U19 and 3V_AO loads. Not a battery-standby item.

### 4.4 Abnormal conditions

| Condition | Behaviour (datasheet-backed) | Proposed firmware policy |
|---|---|---|
| **Weak source** (0.5 A, cable drop, collapsing 5 V) | IINDPM/VINDPM regulate: charge current falls first, then the battery supplements (NVDC §9.3.8.1-2). Termination and safety timers are suspended/halved while in DPM (§9.3.9.3-.4). | Set IINDPM/VINDPM per section 4.2 before releasing the system gate. Shed audio (AGL) to the input budget when the battery is below about 20 % or absent; never raise IINDPM above the grant. |
| **Battery absent** (J5/SW101 open, NTC open) | With no battery and charge disabled by CE/EN_CHG or a thermistor fault, the charger keeps BAT at a low steady voltage and regulates SYS to VSYSMIN (§9.3.6 p.34). With no pack the TS divider R100/R101 reads high (about 85 % of REGN, above the 73 % cold threshold), charging is suspended, which is the safe state (also the case in `bq25792-redraw-handoff.md` flag 7). If TS were disabled and CE low the charger would oscillate BAT between low and BATOVP and SYS could reach SYSOVP (same section), so **do not set TS_IGNORE (REG18[0])**. Default VSYSMIN 3.5 V (REG00 = 0x04, 250 mV steps). | Detect via TS fault bits and ADC VBAT (ADC temporarily on), keep CE high (disabled) until a pack is seen. Run with a hard cap of about 5 W audio (already in `audio-chain-architecture.md`) because SYS has no battery to supplement. |
| **Battery depleted** | VBAT < VBAT_SHORT (2.06 V falling) / VBAT_SHORTZ (2.25 V rising): trickle 100 mA, fixed 1 h timer. Then pre-charge IPRECHG (POR 120 mA) up to VBAT_LOWV = 71.4 % x VREG (REG08[7:6]=11): 2.93 V at 4.10 V (3.00 V at 4.20 V), 2 h timer. In SYSMIN regulation (BATFET LDO) charge current is limited to 2 A regardless of ICHG (§9.3.9.2). | Raise IPRECHG to about 0.5 A (REG08[5:0] = 0x0C, 40 mA steps, accuracy +/-8 % at 480 mA) only after confirming the pack's depleted-state limit. Hold audio and the amplifier boost off until VBAT >= about 3.3 V and SOC >= 5 %. A protection-board-latched pack (0 V at the connector) needs a bench wake test with the 100 mA trickle. |
| **MCU reset / watchdog** | VREG and IINDPM persist; ICHG/VRECHG/ITERM/JEITA revert on watchdog or REG_RST (§9.5.1 notes). CE high by default stops charging. | As the contract: gates low, re-qualify, re-write all policy registers; set the watchdog consciously (default 40 s, REG10[2:0]=5). |

### 4.5 Items for the user to approve

1. ICHG ceiling 3.0 A, default 2.0 A until U4/L1 thermals are benched.
2. Default float: 4.20 V (full) or 4.10 V (longevity, recommended) or user-selectable.
3. Recharge window 200 mV, ITERM 400 mA.
4. JEITA warm-zone VREG drop -100 mV instead of the POR -400 mV.
5. Fast-charge timer 8 h.
6. Conservative 0.45 A IINDPM for unclassified non-PD sources.
7. Shutdown mode for long storage (7 uA vs 18 uA typ) versus losing the QON wake.

---

## 5. Summary of findings and ordering impact

None of these blocks ordering the board as designed; the first two block claims, not parts.

1. **TVS2200 versus 28 V:** worst-case clamp 28.0 V (27 C) to 28.35 V (125 C) inside the rated 40 A range; 0 to +0.35 V over the TPS25730 absolute maximum, and TI itself recommends this part. No surge-immunity claim is supportable, and 2 ohm/12 ohm surge levels are outside the part's capability entirely. A possible LC overshoot at U11 (section 2.4, model-based, up to +3 V from 20 V) is unverified and should be measured on the first board.
2. **PPHV capacitance:** the 100 uF maximum is met at every real bias. Effective capacitance at 20 V falls to about 22 uF (16-25 uF) against TI's 47 uF NOM (no MIN published). The Murata 0805 X5R/1206 X5R bias curves are not in the repo; section 3.2's proxy is optimistic. Bench the 20 V load step.
3. **Standby:** electronic-off about 57 uA typ / 105 uA max (state B), ship about 18 / 27 uA, shutdown about 7 / 11 uA. The biggest levers are the BQ25792 itself, the PVDD diode path (22.6 uA typ, only a 13.5 V datasheet figure), and three 1 M resistors (9.7 uA). Pack protection and cell self-discharge are outside this budget and larger.
4. **Inrush:** 0.22 A typ / 0.42 A max at sink-path enable (PPHV + PMID, 3.8 V/ms); the 5 -> 20 V transition current with a closed sink path is an unresolved bench item (up to about 2-3 A, source-limited).
5. **Missing evidence:** TPS61088 PDF absent locally (ISD taken from the TI web page), D7 1N5819HW leakage datasheet not in repo, no Murata DC-bias curves, MAX17048 hibernate entry in ship mode unverified.

## 6. Bench confirmations suggested (additions to the existing plan)

- Ship and electronic-off current on the bench with the real pack at 3.7 V (BQ figures are 8 V); 3V_AO voltage in ship mode (PC13/QON back-feed).
- PVDD_AMP voltage and current with U25 disabled (diode path, TAS shutdown draw at 3.3 V).
- U11 VBUS_IN waveform with a fast step or surge-injection from J1; VBUS_PD during PPHV enable and a 5 -> 20 V request.
- Murata SimSurfing DC-bias export for C100/C111/C101/C108/C112 (GRM21BR61H106KE43L) and C315 (GRM31CR61E476ME44L) at 5-21 V.
