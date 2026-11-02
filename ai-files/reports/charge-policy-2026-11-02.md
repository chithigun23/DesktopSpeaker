# Charge current policy and battery (2026-11-02)

Owner's question: "we want to use USB PD so the charge current should be fairly high; look at the chosen battery and decide what is safe, reliable and fast (in that order)."

Scope: decision, register policy and hardware/PCB check. **Result: firmware-only.** No schematic, BOM, library or `.kicad_pcb` file was changed, so no ERC run was needed. This report supersedes the "ICHG ceiling 3 A / default 2 A" proposal in `power-analysis-2026-11-01.md` section 4 and the "ICHG at most 3 A" line in `firmware-system-spec-2026-11-01.md` section 3.2.

Labels: **[DS]** = read in a local datasheet (file, section/page). **[FIG]** = read off a datasheet plot (about ±1 % efficiency). **[EST]** = my arithmetic or model. **[UNVERIFIED]** = not read in a primary document.

---

## 0. Decisions at a glance

| Item | Decision | Register value |
|---|---|---|
| Fast-charge current ICHG | **4.0 A** (0.4C for the 10 Ah pack, 2.0 A per cell) | REG03 = 0x0190 |
| What limits it in practice | Input-power cap **17 W** (charger output stage, not the PD contract). Real charge current about **3.6-3.9 A** with the product idle, about 3.2 A while playing at typical level. The BQ25792 thermal loop limits it further from 15-20 V sources if U4 runs hot. | REG06 per contract (section 4) |
| Charge voltage VREG | **4.10 V default** ("longevity"), **4.16 V maximum** ("full"). Never 4.20 V. | REG01 = 0x019A / 0x01A0 |
| Recharge threshold | 200 mV below VREG (POR) | REG0A = 0x23 |
| Termination ITERM | **480 mA** (0.05C per cell) | REG09 = 0x0C |
| Pre-charge IPRECHG | **480 mA** up to 71.4 % of VREG (2.93 V at 4.10 V) | REG08 = 0xCC |
| Cold / cool / warm / hot | Below about 1 °C: suspend (fixed T1). 1-10 °C: 20 % of ICHG (0.8 A). 10-45 °C: full current. **Above about 45 °C: suspend** (not the POR "VREG − 400 mV"). Firmware also suspends below 3 °C. | REG18 = 0x54, REG17 = 0x02 |
| IC thermal regulation | **TREG 100 °C** (POR 120 °C), TSHUT 130 °C (POR 150 °C) | REG16 = 0x90 |
| Safety timer | 8 h (counts at half rate in DPM/TREG, so up to 16 h); 24 h for sources under 15 W | REG0E = 0x3B / 0x3F |
| Charger watchdog | Disabled; hardware CE default-off covers an MCU failure | REG10 = 0x00 |
| Battery discharge OCP | **Enable** (9.3 A). It is off at POR, and the audio budget already assumes it is active. | REG14 = 0x95 |
| Hardware value changes | None needed | - |
| PCB (RT-2) | Charge current alone is fine. For the 2x margin, which also covers the 6 A RMS discharge, fix two items: (1) **BAT_U4PIN_F finger** at U4-22/23 and (2) **R102 notch** in the BAT_INT_F strip. Optional: join the B.Cu BAT_PACK pieces and flare SW1/SW2 at U4-26/28. See section 7. | - |

Charge time [EST, section 5]: about 2.8 h from empty to termination at 4.10 V with a 9 V or higher source (20-80 % in about 1.5-1.7 h). With 4.16 V, add about 0.1 h. From a 5 V/3 A PD source: about 3.2 h. If TREG throttles at 20 V, expect about 3.3 h.

---

## 1. The chosen battery pack

**Pack (as specified; not yet purchased).** `HANDOVER.md` "Mechanical CAD and pack decision (2026-10-06)", `reports/battery-pack-rfq.md`, `bom/hardware-buy-list.csv` row 32.
- 1S2P 21700, 10 Ah nominal, 3.6 V. Preferred cells are Samsung INR21700-50S; Molicel P45B "or equivalent" is also acceptable.
- Protection board (PCM) as requested in the RFQ: overcharge 4.25 V, over-discharge 2.5-2.8 V, discharge at least 10 A continuous (20 A for 1 s), **charge current up to 5 A**, storage drain under 10 µA.
- NTC 10 kΩ, B25/85 about 3435 K (103AT type), glued to a cell.
- 230 mm leads, 18 AWG for PACK+/PACK−, into a Micro-Fit 43645-0300 housing.
- Status: RFQ only. The real PCM charge-OCP and OV values and the real NTC are **unknown** until a quote and datasheet arrive. The CM Batteries web listing gives "charge 2 A std / 5 A max" (`reports/sourcing-2026-10-12.md` section 4) [UNVERIFIED, web listing].

**Cell: Samsung INR21700-50S.**

Source: Samsung SDI "The Highest Capacity High Power 21700 50S" (2021, slide 3 "Specification"), saved as `datasheets/Samsung_INR21700-50S_SDI_introduction_2021.pdf` (+ `.txt`). This is a Samsung SDI deck downloaded from a distributor mirror (salespot.com.ua), not the formal product specification.

| Parameter | Cell | 2P pack | Source |
|---|---|---|---|
| Capacity | 5,000 mAh typ (0.2C); 4,800 mAh min (10 A) | 10 Ah | [DS] deck p.3 |
| Nominal voltage | 3.60 V | 3.6 V | [DS] deck p.3 |
| Charge voltage | 4.2 V (CC-CV test conditions) | 4.2 V | [DS] deck p.3 notes 1-2 |
| Standard charge current | **2.5 A (0.5C)**, CC-CV 4.2 V, 250 mA cut-off, 150 min | 5.0 A | [DS] deck p.3 |
| Maximum charge current | **6.0 A** (CC-CV 6 A, 4.2 V, 100 mA cut-off, 100 min) | 12 A | [DS] deck p.3 |
| Discharge end voltage | 2.5 V | | [DS] deck p.3 |
| Maximum discharge | 25 A without temperature cut-off; 45 A with 80 °C cut-off | | [DS] deck p.3 |
| Internal resistance | AC ≤ 14 mΩ (avg 10.0), DC ≤ 22 mΩ (avg 16.3 at 100 % SOC) | about 8 mΩ | [DS] deck p.3, p.5 |
| Cycle-life test | charge 6 A / 4.2 V: 60 % after 250 cycles (25 A discharge) | | [DS] deck p.3 |
| Charge temperature | **0-45 °C, cell surface** | | **[UNVERIFIED for 50S]**: from Samsung sibling specs INR21700-50E v0.2 §3.16 and INR21700-50G v0.1 §3.14, saved as `datasheets/Samsung_INR21700-50E_spec_v0.2_sibling.pdf` (chipdip.ru mirror) and `..._50G_spec_v0.1_sibling.pdf` (forum mirror). The formal 50S specification could not be downloaded (404/403). |
| Discharge temperature | −20 to 60 °C (siblings) | | [UNVERIFIED for 50S] |

If Molicel P45B or another cell is delivered, re-check standard/max charge current and the charge temperature window against its datasheet. 4 A is 0.44C for 4.5 Ah cells, which is within the usual standard charge rate for 21700 power cells [UNVERIFIED].

---

## 2. Decisions and reasons (safe, then reliable, then fast)

### 2.1 ICHG = 4.0 A

**Safe:**
- 2.0 A per cell is 80 % of Samsung's *standard* charge (2.5 A) and 33 % of its maximum (6 A).
- It is 80 % of the 5 A PCM charge rating requested in the RFQ.
- It is 80 % of the BQ25792 fast-charge maximum (5 A, SLUSDG1C §8.3).
- Accuracy at 4 A in buck mode is −5.5/+2.5 % (§8.5 p.12), so the actual current is at most 4.10 A.

**Reliable:**
- 0.4C keeps cell heating negligible: about 64 mW per cell at the 16 mΩ DC IR.
- It sits well below the 6 A rate that Samsung used for cycling.
- L1 at about 4 A sees 67 % of its 6 A Irms.
- The binding stresses (U4 junction, converter output current) are handled separately by TREG and the input-power cap, not by a lower ICHG.

**Fast:**
- ICHG is near the 17 W input cap, so raising it further gains nothing.
- 5 A would sit exactly at the cell's standard rate, the PCM spec and the IC maximum, with no tolerance margin.

The earlier 3.0 A ceiling would add about 0.65 h per full charge.

### 2.2 Input-power cap 17 W (this is what "PD power" actually buys)

The BQ25792's switch output (ISW) is rated **5 A maximum** (§8.3), and that current is SYS load plus charge current.

The charger regulates ICHG but does **not** limit SYS load. A 60 W contract with IINDPM 3 A and loud playback would push the converter to about 9 A. That exceeds the rating and trips the cycle-by-cycle limits: Q1/Q4 7.5 A minimum (§8.5 p.15-16).

The only control is the input limit. Firmware sets IINDPM so that P_in ≤ 17 W, which equals 4.5 A × 3.6 V / 0.95 [EST]:
- Even with VSYS at 3.3 V and a 95 % efficiency upper bound, ISW stays below 4.9 A.
- IINDPM accuracy is never above the setting (§8.5 p.13: 3.0 A set gives 2.72-2.92 A).

Consequences:
- **Any PD source of 18 W or more charges at the same rate.** 15/20 V contracts add switching loss and no speed.
- During loud playback the charge current falls first. Above about 15 W of SYS demand, the battery supplements (NVDC). This is inherent to a 1S NVDC charger with a 5 A output stage.

### 2.3 VREG 4.10 V default, 4.16 V maximum

**Safe:**
- BQ25792 charge-voltage accuracy at VREG = 4.2 V is **−0.45 / +0.95 %** (§8.5 p.11; note: `power-analysis-2026-11-01.md` said no 1S figure exists, but it does).
- A 4.20 V setting can therefore regulate at up to 4.240 V. That is above the cell's 4.2 V and within about 10 mV of a 4.25 V PCM trip (a typical ±25 mV OV tolerance would make it 4.225 V [UNVERIFIED]).
- 4.16 V × 1.0095 = 4.200 V.
- The figure is specified for TJ −40 to 85 °C. At TREG 100 °C it is unspecified, which is another reason for margin.

**Reliable:**
- A desk speaker spends most of its life on the dock. Floating at 4.10 V rather than 4.2 V reduces calendar ageing.
- The 4.10 V capacity of about 90 % is a generic NMC estimate [UNVERIFIED for 50S; my curve, section 5].

**Fast/capacity:**
- A "full" mode at 4.16 V (about 96 %) is for travel.
- The MAX17048 will read about 85-90 % at 4.10 V. Firmware maps CHG_STAT = 111 to 100 %, as already noted in the power analysis.

### 2.4 Termination 480 mA, recharge 200 mV

- Samsung's standard-charge cut-off is 250 mA per cell (deck p.3 note 1), which is 500 mA for the pack. The nearest code is 480 mA, which is also the tabulated accuracy point (±14 %, §8.5 p.12).
- Termination is suspended automatically while in IINDPM, VINDPM or TREG (§9.3.9.3). If loud playback holds the charger in IINDPM at the end of charge, it stays in CV at VREG. That is safe.
- The 200 mV recharge window (POR) gives a 3.90-4.10 V rest band while docked and avoids micro-cycling.

### 2.5 Pre-charge 480 mA

- The POR value of 120 mA is 0.012C. Precharge from 2.5 V to 2.93 V on 10 Ah can need 0.1-0.3 Ah [EST], so it could hit the 2 h pre-charge timer.
- 480 mA is 0.048C per cell, which is gentle for a deeply discharged cell.
- A pack that is still below 2.93 V after 2 h at 0.48 A (about 1 Ah) has a fault, and the timer then correctly stops it.
- Below 2.25 V the fixed 100 mA trickle applies (§9.3.9.2).
- U4 dissipation in BATFET-LDO mode is (3.7 − 2.5) × 0.48 = 0.58 W at most [EST].
- In SYSMIN regulation the charger clamps charge to 2 A regardless of ICHG (§9.3.9.2), giving up to (3.7 − 3.0) × 2 = 1.4 W in the BATFET. TREG covers this.

### 2.6 Temperature (TS / JEITA)

TS network R100 5.23 k (REGN to TS) / R101 30.1 k (TS to GND) matches TI's 5.24 k / 30.31 k for a 103AT. Computed with B = 3435 and the comparator limits of §8.5 p.15 [EST]:

| Threshold | Setting | Trip temperature (103AT) | Window from comparator tolerance | Action |
|---|---|---|---|---|
| T1 (fixed) | 73.3 % REGN | 1.0 °C (resume 3.7 °C) | −1.0 to 2.8 °C | suspend |
| T2 TS_COOL | 10 °C (POR) | 10.3 °C | | 1-10 °C: ICHG × 20 % = 0.8 A (0.08C/cell), JEITA_ISETC = 1 (POR) |
| T3 TS_WARM | 45 °C (POR) | 44.4 °C (resume 42.6 °C) | 43.7-45.1 °C | **suspend**: JEITA_VSET = 0, JEITA_ISETH = 0 (POR would charge to VREG − 400 mV at full ICHG up to 60 °C, outside the cell's 45 °C limit) |
| T5 (fixed) | 34.2 % REGN | 59.9 °C | | suspend (not reached; T3 already suspends) |

- Cell limit 0-45 °C: the hardware suspends at or below 45 °C. On the cold side the T1 tolerance reaches −1 °C, but only at 0.8 A. **Firmware also clears CE when the TS ADC reads below 3 °C** (resume above 5 °C).
- If the pack ships with a B = 3950 NTC, all thresholds move in the safe direction: T1 3.9 °C, T3 41.8 °C, T5 54.9 °C. With B = 3380 they stay within 0.4 °C. No NTC network change is needed.
- An open NTC reads 85 % (cold) and a shorted NTC reads 0 (hot); both suspend. **Never set TS_IGNORE.**
- Firmware derating (reliability, not safety): when TS ≥ 40 °C, ICHG = 2.0 A; restore below 37 °C. This avoids repeated 45 °C suspend cycles in a warm enclosure.

### 2.7 Thermal regulation, timers, watchdog, OCP

**TREG 100 °C.** TREG is a closed loop on the die (§9.3.13.2). At 100 °C it keeps Tj 25 °C below the 125 °C recommended maximum (§8.3) and leaves margin for the unspecified TREG accuracy. It is what makes ICHG 4.0 A safe from a 20 V source on an uncharacterised board. TSHUT 130 °C (110 min / 150 max) is a backstop above TREG.

**CHG_TMR 8 h with TMR2X.**
- Expected fast-charge duration is about 3 h, so the timer gives about 2.7× headroom; in DPM/TREG it becomes 16 h.
- For sources whose budget gives under 1.5 A of charge, set 24 h instead. For example, the 5 V/0.5 A fallback charges at about 0.2 A, which is maintenance only.

**Watchdog disabled (REG10 = 0x00).**
- On watchdog expiry the charger reloads POR values for ICHG, ITERM, IPRECHG, VRECHG, TREG/TSHUT and **JEITA** (§9.5.1 reset notes). The POR JEITA lets charging continue at 45-60 °C, which is less safe than the configured state.
- MCU failure is already covered: reset or brown-out releases CHG_ENABLE and the R107 pull-down returns CE high (charge off), per `replacement-power-control-contract.md`.
- Firmware re-reads the policy registers every 5 s (firmware spec 3.2). A mismatch is handled as REG_RST.

**EN_BATOC = 1.**
- Battery discharge OCP (IBAT_OCP 9.3 A min, §8.5 p.13) is **disabled at POR** and locked until SFET_PRESENT = 1 (REG14 description).
- `audio-chain-architecture.md` already assumes the 9.3 A OCP exists. Enable it after SFET_PRESENT.
- Bench-check that the boost peaks (up to about 8.5 A) do not trip it.

---

## 3. Register table (BQ25792, 1S, PROG 4.7 kΩ = 750 kHz)

Write with CHG_SYS_ENABLE (ILIM_HIZ held low) and CHG_ENABLE (CE off) still asserted, per `replacement-power-control-contract.md` steps 1-7. 16-bit registers are written MSB first.

| Reg | Field(s) | Value | Hex | POR | Reset by | Note |
|---|---|---|---|---|---|---|
| 0x10 | VAC_OVP = 26 V, WATCHDOG = off | | **0x00** | 0x85 | REG_RST | write first |
| 0x14 | SFET_PRESENT = 1, EN_IBAT = 0, IBAT_REG = 5 A, EN_IINDPM = 1, EN_EXTILIM = 0 | | **0x94**, read back, then **0x95** (EN_BATOC = 1) | 0x16 | EN_IBAT/IBAT_REG/EN_IINDPM/EN_BATOC by WD and REG_RST; EN_EXTILIM by REG_RST | EN_EXTILIM = 0 is required to exceed the 100 mA ILIM_HIZ clamp latched at POR (`bq25792-ilim-startup-review.md`). Use 0xB5 if IBAT discharge ADC reading is wanted. |
| 0x11 | FORCE_INDET 0, AUTO_INDET_EN 0, EN_12V/9V 0, HVDCP_EN 0, SDRV_CTRL idle, SDRV_DLY 0 | | **0x00** | 0x40 | REG_RST | ship/shutdown entry handled elsewhere |
| 0x0F | EN_AUTO_IBATDIS 1, EN_CHG 1, EN_ICO 0, EN_HIZ 0, EN_TERM 1 | | **0xA2** | 0xA2 | | CE pin remains the charge gate |
| 0x00 | VSYSMIN 3.5 V | 3500 mV | **0x04** | 0x04 (1S) | REG_RST | keep POR |
| 0x01 | VREG | 4.10 V / 4.16 V | **0x019A** / 0x01A0 | 0x01A4 (4.20 V) | REG_RST | firmware clamp: never above 0x01A0 |
| 0x03 | ICHG | 4.00 A | **0x0190** | 0x00C8 (2 A) | WD, REG_RST | bring-up ladder 0x0064 → 0x00C8 → 0x012C → 0x0190 (section 8) |
| 0x05 | VINDPM | per contract | see section 4 | measured at plug-in | not reset | TI rule: contract − 1.4 V (≥ 7 V), 4.4 V at 5 V |
| 0x06 | IINDPM | per contract | see section 4 | 0x012C | REG_RST | min(contract − 0.10 A, floor(17 W / V)) |
| 0x08 | VBAT_LOWV = 71.4 %, IPRECHG 480 mA | | **0xCC** | 0xC3 | IPRECHG: WD, REG_RST | |
| 0x09 | ITERM 480 mA | | **0x0C** | 0x05 | WD, REG_RST | |
| 0x0A | CELL 1S, TRECHG 1024 ms, VRECHG 200 mV | | **0x23** | 0x23 | | never change CELL (it resets ICHG/VSYSMIN/VREG) |
| 0x0E | TOPOFF off, trickle/pre/fast timers on, CHG_TMR 8 h, TMR2X 1 | | **0x3B** (0x3F = 24 h for sources under 15 W) | 0x3D | WD, REG_RST | |
| 0x16 | TREG 100 °C, TSHUT 130 °C, pull-downs off | | **0x90** | 0xC0 | WD, REG_RST | |
| 0x17 | JEITA_VSET suspend, JEITA_ISETH suspend, JEITA_ISETC 20 % | | **0x02** | 0x7A | WD, REG_RST | warm zone = suspend |
| 0x18 | TS_COOL 10 °C, TS_WARM 45 °C, BHOT 60 °C, BCOLD −10 °C, TS_IGNORE 0 | | **0x54** | 0x54 | WD, REG_RST | keep POR, write anyway |
| 0x2E | ADC_EN 1, continuous, 14-bit | | **0x90** while VBUS is present; **0x00** on battery | 0x30 | REG_RST | ADC on costs about 0.5 mA (power analysis 1.2); it is needed for the TS/TDIE/VSYS rules |

Dynamic firmware rules (in addition to the contract document):
1. **IINDPM/VINDPM on every contract change** (read TPS25730 0x34/0x35): lower first, then raise. A non-PD or unknown source gets 0.40 A.
2. **CE gate:** enable only when all of these hold: readbacks match; TS status is normal or cool; TS ADC > 3 °C; a pack is present (VBAT ADC > 2.0 V or TS in range).
3. **Derating:**
   - TS ≥ 40 °C → ICHG 2.0 A.
   - TDIE ADC (REG41) ≥ 95 °C for over 30 s → ICHG −0.5 A per step, minimum 1.0 A. Step back up below 85 °C.

   This is optional smoothing; TREG is the safety loop.
4. **Mode:** 4.10 V default, 4.16 V "full" on user request. Revert to 4.10 V after the next termination plus 24 h on the dock (product choice, can be dropped).

---

## 4. Power budget at each source (section 2.2 rule; efficiency from [FIG] SLUSDG1C Fig. 8-1, 1S, VBAT 4 V, 750 kHz, 2.2 µH)

P to SYS assumes VSYS = 3.8 V (mid charge). The I_chg columns are charge current at the stated total SYS load: 0.3 W = product off and charging; 1 W = speaker on, quiet; 2.5 W = typical listening (`audio-chain-architecture.md` 6); 8 W = loud; 25 W = peaks. Negative values mean the battery supplements. These are estimates.

| Source contract | VINDPM | IINDPM | P_in max | P to SYS | I_chg @0.3 W | @1 W | @2.5 W | @8 W | @25 W |
|---|---|---|---|---|---|---|---|---|---|
| 5 V non-PD / unknown (0.5 A assumed) | 4.4 V (0x2C) | 0.40 A (0x028) | 2.0 W | 1.9 W | 0.42 | 0.24 | −0.16 (bat) | −1.61 (bat) | −6.1 (bat) |
| 5 V 1.5 A (PD 5 V PDO only; Type-C Rp is not readable) | 4.4 V (0x2C) | 1.40 A (0x08C) | 7.0 W | 6.6 W | 1.66 | 1.48 | 1.09 | −0.36 (bat) | −4.8 (bat) |
| 5 V 3 A (PD) | 4.4 V (0x2C) | 2.90 A (0x122) | 14.5 W | 13.2 W | 3.39 | 3.20 | 2.81 | 1.36 | −3.1 (bat) |
| 9 V 2 A (18 W) | 7.6 V (0x4C) | 1.88 A (0x0BC) | 16.9 W | 15.0 W | 3.87 | 3.68 | 3.29 | 1.84 | −2.6 (bat) |
| 9 V 3 A (27 W) | 7.6 V (0x4C) | 1.88 A (0x0BC) | 16.9 W | 15.0 W | 3.87 | 3.68 | 3.29 | 1.84 | −2.6 (bat) |
| 12 V 3 A (36 W) | 10.6 V (0x6A) | 1.41 A (0x08D) | 16.9 W | 14.8 W | 3.83 | 3.64 | 3.25 | 1.80 | −2.7 (bat) |
| 15 V 3 A (45 W) | 13.6 V (0x88) | 1.13 A (0x071) | 16.9 W | 14.7 W | 3.79 | 3.61 | 3.21 | 1.77 | −2.7 (bat) |
| 20 V 2.25 A (45 W) | 18.6 V (0xBA) | 0.85 A (0x055) | 17.0 W | 14.5 W | 3.74 | 3.56 | 3.16 | 1.72 | −2.8 (bat) |
| 20 V 3 A (60 W) | 18.6 V (0xBA) | 0.85 A (0x055) | 17.0 W | 14.5 W | 3.74 | 3.56 | 3.16 | 1.72 | −2.8 (bat) |

- The board asks for 5-20 V at up to 3 A (TPS25730D ADCIN2 tied to LDO_3V3 = 20 V maximum; HANDOVER "PD" line). It is assumed to take the highest voltage the source offers [UNVERIFIED: the TPS25730 datasheet §8.3.11-8.3.14 does not state the selection rule]. So 15/20 V is the normal case with a laptop charger.
- The 0.10 A IINDPM margin covers the TPS25730, U19/USB_AUX and 3V_AO draws upstream of the charger (contract step 6).
- Input path loss (TPS25730 PPHV 16/19 mΩ at 25 °C, 24/29 mΩ at 125 °C, as quoted in `5-20v-pd-front-end-review.md`): 0.24 W at 5 V/2.9 A, 0.10 W at 9 V/1.88 A, 0.02 W at 20 V/0.85 A [EST]. All are far below its 7 A path rating.

---

## 5. Thermal and loss estimate (charging, 1 W SYS load, at the cap)

Basis: total converter loss from [FIG] Fig. 8-1. L1 loss = Irms² × 18 mΩ (SRN6045TA-2R2Y DCR 15 mΩ ±20 %, `Bourns_SRN6045TA.txt`) + 0.10 W core [ASSUMED]. A further 0.15 W is copper and capacitor ESR [ASSUMED]. The rest is in U4. RθJA is 44.2 °C/W (JEDEC, §8.4); "30 °C/W" is an [ASSUMED] well-poured 4-layer layout. ΨJT = 0.5 °C/W, so the U4 top-case temperature on the bench is Tj within about 1 °C.

| Source | Converter output current | Converter efficiency | Total loss | L1 | U4 | ΔTj (44.2 °C/W) | ΔTj (30 °C/W) | Tj at 35 °C inside the enclosure |
|---|---|---|---|---|---|---|---|---|
| 5 V 3 A | 3.47 A | 0.908 | 1.33 W | 0.32 W | 0.86 W | +38 °C | +26 °C | 61-73 °C |
| 9 V | 3.95 A | 0.886 | 1.92 W | 0.38 W | 1.39 W | +62 °C | +42 °C | 77-97 °C |
| 12 V | 3.90 A | 0.877 | 2.08 W | 0.38 W | 1.55 W | +69 °C | +47 °C | 82-104 °C |
| 15 V | 3.87 A | 0.868 | 2.24 W | 0.37 W | 1.71 W | +76 °C | +51 °C | 86-111 °C |
| 20 V | 3.82 A | 0.854 | 2.48 W | 0.37 W | 1.96 W | +87 °C | +59 °C | 94-122 °C |

What this means:
- At JEDEC-class thermal resistance, TREG (100 °C) will throttle charging from 12-20 V sources. From 20 V it settles near **3.1 A** [EST: U4 loss ≈ 1.47 W at 3.1 A]. At 9 V nearly the full 3.9 A remains.
- Higher VBUS costs about 0.6 W more in U4 at 20 V than at 9 V. This is the case for open question 3.
- **L1** at 3.95 A: Irms is 66 % of 6 A, so the temperature rise is about 17 °C plus core loss (Bourns rates 40 °C at Irms).
  - Peak current at the 4.9 A worst case is about 6.2 A, from nominal ripple 1.9 A pp at 20 V, 2.7 A pp at L −30 %. That is below Isat 9.5 A typ and below the 7.5 A minimum cycle-by-cycle limit.
  - 750 kHz with 2.2 µH is the TI-required pair (§10.2.2.1). **No inductor change is needed.**
- **Q103** CSD17579Q3A (gate at BAT + 5 V typ from SDRV, §9.3.12): RDS(on) 11.8 typ / 14.2 max at VGS 4.5 V (DS table).
  - At 4.1 A × 14.2 mΩ × 1.4 hot [ASSUMED] it dissipates 0.33 W.
  - That is +20 °C at TI's 60 °C/W (1 in² 2 oz), and probably +25-35 °C on this board's smaller pour [EST].
  - At 6 A RMS discharge it rises to 0.7 W, which belongs to the audio power budget.
- **Charge times** [EST]: CC-CV simulation with a generic NMC OCV curve [ASSUMED], 40 mΩ between BATP and the cells, ITERM 0.48 A:

| ICHG actual | VREG | 0 → termination | 20-80 % | End SOC (rel. 4.19 V OCV) |
|---|---|---|---|---|
| 4.0 A | 4.10 V | 2.75 h | 1.52 h | 90 % |
| 4.0 A | 4.16 V | 2.87 h | 1.50 h | 96 % |
| 3.5 A (typical, input-capped) | 4.10 V | 3.02 h | 1.72 h | 90 % |
| 3.0 A (old proposal / TREG at 20 V) | 4.10 V | 3.40 h | 2.00 h | 90 % |

---

## 6. Hardware check (is anything to change?)

| Item | Requirement | Present | Verdict |
|---|---|---|---|
| ICHG setting mechanism | I2C REG03 only. The BQ25792 has no charge-current resistor. PROG sets only cell count and fsw (§9.3.2, Table 9-1). | R102 4.7 kΩ = 1S, 750 kHz | OK, keep: 750 kHz has the higher efficiency and matches the 2.2 µH L1 |
| ILIM_HIZ | Pin clamp latched at POR; with Q101 holding HIZ it reads as 100 mA | R108 180 k / R109 100 k / R110, Q101 | OK. Firmware clears EN_EXTILIM (contract). No value change. |
| TS / NTC | 103AT network | R100 5.23 k, R101 30.1 k | OK (section 2.6). No change. |
| Sense resistor | Internal RSNS 6 mΩ VBUS-PMID (§8.5 p.15); no external charge sense | - | n/a |
| Fuel gauge shunt | MAX17048 is voltage-based (ModelGauge); no shunt on the board | - | n/a |
| L1 SRN6045TA-2R2Y | ≥ 4.9 A worst output with ripple; Isat > 6.2 A | Irms 6.0 A typ (40 °C rise), Isat 9.5 A typ (−30 % L) | OK, no change |
| Q100-Q102, Q104 (2N7002) | logic only (CE inversion, ILIM_HIZ gate, gauge isolation) | - | no charge current |
| Q103 CSD17579Q3A (ship FET in the battery path) | 4.1 A charge, 6 A RMS / 10 A peak discharge | 30 V, ID 20 A (package limit), 14.2 mΩ max at 4.5 V | OK; dissipation in section 5 |
| BQ25792 BAT/SYS | charge ≤ 5 A; ISW ≤ 5 A; IBAT 6 A RMS / 10 A 1 s | 4.1 A charge; ISW ≤ 4.9 A by the cap | OK, with the 17 W cap |
| TPS25730D path | ≤ 7 A continuous | ≤ 2.9 A | OK |
| J5 Molex 43650-0300 | ≥ 2× the 4.1 A charge current | 8.5 A per contact | OK [UNVERIFIED: LCSC/Molex listing value per HANDOVER; the local PDF is an LXW clone drawing rated 5 A] |
| SW101 GRB112B802BR1 | ≥ 2× charge | 20 A / 14 VDC | OK [UNVERIFIED: Digi-Key listing per HANDOVER; no local datasheet] |
| Harness | 2 × 230 mm 18 AWG | about 9.6 mΩ total [EST, 20.9 mΩ/m] | OK; 0.16 W at 4.1 A |
| J1 USB-C TYPE-C-31-M-12 | ≤ 2.9 A at 5 V | rating not legible in the local PDF | [UNVERIFIED]; same as before this decision |

**Conclusion: no resistor, current-limit or NTC value needs to change. The policy is firmware-only.**

---

## 7. PCB: battery-path copper on `ai-files/pcb/work-route2/RT-2.kicad_pcb` (read-only)

### 7.1 Method

`helpers/copper_path_export.py` exports the filled zones, tracks, pads and vias of each net with pcbnew (AppImage python3.11). `helpers/copper_path_solve.py` then rasterises each copper layer (0.05 mm cells on the U4/SW nets, 0.1 mm on BAT_PACK/GND) and treats vias and PTH barrels as resistors. It solves the potential between the source pads and the sink pads and reports:
- the path resistance;
- the maximum sheet current (A per mm of copper width);
- the "equivalent width" (I / sheet current) at hotspots.

Inputs and assumptions:
- Copper thickness from the board stackup: F/B 35 µm, In1/In2 **15.2 µm**.
- Barrel plating 20 µm [ASSUMED]; resistivity at 20 °C.

Width criterion [EST, IPC-2221 external-layer formula I = 0.048 ΔT^0.44 A^0.725]:
- Design current 8.2 A (2× the 4.1 A maximum charge) at ΔT ≤ 20 °C, which is the same as 6 A RMS (BQ25792 battery rating) at ΔT ≤ 10 °C.
- That needs **≥ 3.5-3.6 mm of 1-oz outer copper**.
- 0.5-oz inner copper counts as 0.43× its width.
- Short pin-escape necks (≤ 0.3 mm long) next to a pad are exempt because they are as wide as the IC pins themselves.

### 7.2 Measured

Current path: U4-22/23 → BAT_INT (BAT_U4PIN_F + BAT_INT_F on F.Cu, BAT_INT_IN2) → Q103 → BAT_PACK → SW101-1 → PACK_RAW → J5-1; return J5-3 → GND.

| Net / segment | Copper | R (20 °C) | At 4.1 A | At 6 A | Narrowest | Verdict |
|---|---|---|---|---|---|---|
| BAT_INT, U4-22/23 → Q103-1/2/3 | F.Cu 144 mm²; In2 163 mm² (only near Q103; 5 % of the loss); 39 × 0.8/0.4 vias (≤ 0.39 A each at 6 A) | **3.32 mΩ** | 14 mV, 56 mW | 20 mV, 120 mW | **Finger 0.60 mm** for x 153.77-154.75 (0.98 mm beyond the pad toe), then 1.44 mm at x 154.9. Strip 3.45 mm (y 119.45-122.90) from x 155 to 164, **2.73 mm at x 159.6-161.6**. ≥ 4.2 mm near Q103. | **Fix 1 + Fix 2** |
| BAT_PACK, Q103-5..9 → SW101-1 | In2 BAT_PACK_IN2 (0.5 oz, 14-33 mm wide); F.Cu only at Q103; B.Cu BAT_PACK_B = 2 dead-end pieces (x 173-196 / y 112.8-119 and x 201-212 / y 91-96.4) carrying no current | **4.16 mΩ** | 17 mV, 70 mW | 25 mV, 150 mW | equivalent 3.4 mm of 0.5 oz (= 1.5 mm 1 oz) only at radial crowding into SW101-1 / J5 holes and the Q103 via field; bulk ≥ 14 mm | Pass (wide pour); Fix 3 optional |
| PACK_RAW, SW101-2 → J5-1 | F.Cu PACK_RAW_F 202 mm² only | 0.99 mΩ | 4 mV, 17 mW | 6 mV, 36 mW | 2.5 mm equivalent at the PTH pad entries | Pass |
| GND return, J5-3 → U4 GND/C104-C107 | all layers | 0.85 mΩ | 3.5 mV, 14 mW | 5 mV, 31 mW | worst via 1.12 A at 6 A (0.77 A at 4.1 A) | Pass |
| SW1 / SW2, U4-28/26 → L1 | 0.2 mm F.Cu tracks from the pin (about 0.7 mm beyond the toe), then 0.29-0.42 mm, 0.9-1.2 mm, 2.3 mm to L1 | 3.84 / 4.31 mΩ | 65 / 72 mW at 4.1 A | | pin-width limited (pads 0.2 × 1.0 mm) | Pass; Fix 4 recommended |

Board total for the battery path: 9.3 mΩ, which is 38 mV / 0.16 W at 4.1 A. **Nothing here endangers 4 A charging.** The finger's self-heating is under 1 °C because it is short [EST: 1-D fin]. The fixes below provide the 2× margin and better heat spreading from U4. A 1 mm × 0.6 mm neck adds about 120 °C/W in series with the BAT-pin heat path [EST].

### 7.3 Required changes (for the routing owner; no `.kicad_pcb` was edited)

**Fix 1: BAT_U4PIN_F (zone uuid 019a336f-…, net /Battery_Charger/BAT_INT, F.Cu, priority 9) at U4 pads 22/23.**
- Today the pour reaches the pads through the rectangle x 153.3-155.0, y 120.885-121.485. That is 0.60 mm wide and runs 0.98 mm beyond the pad toe at x = 153.77.
- Required:
  - 0.6 mm wide for no more than **0.3 mm** beyond the toe (to x ≤ 154.05);
  - **≥ 1.6 mm by x = 154.05** (about y 119.75-121.485);
  - **≥ 2.5 mm by x = 154.8** (about y 119.65-122.2);
  - merging into the ≥ 3.45 mm body at x = 155.3.
  - Use 45° edges.
- How: free the lanes held for U4-24 (Net-(Q103-G)), U4-21 (/CHG_INT; a no-connect since 2026-11-02, patch P1, so this lane is free) and U4-20 (/Battery_Charger/PROG):
  - U4-24: 0.2 mm stub north-east to a fine via (0.45/0.2, allowed in NECK_U4), centred about (153.65, 120.2), then B.Cu to Q103-4.
  - U4-21 and U4-20: leave the toe and go south-east, parallel to the existing BTST2 escape. Keep 0.2 mm clearance (neck rule); BTST2 is the SWITCH class.
- Simulated result [EST]: BAT_INT 3.32 → **2.82 mΩ**; the 0.6 mm section shrinks to the unavoidable 0.28 mm at the pins.

**Fix 2: R102 (PROG 4.7 k, pads at (159.4, 122.64) and (160.6, 122.64)) and its GND track/via sit inside the BAT_INT_F strip.** They pull the strip's south edge to y 122.18, leaving 2.73 mm at x 159.6-161.6. Move R102 and its GND connection out of the strip (south of y 123.3) or next to U4-20, which shortens the PROG trace anyway. The strip must then be **≥ 3.45 mm** (y 119.45-122.90) everywhere from x 155.0 to 164.0. The north edge is fixed by the 0.4 mm POWER_HI clearance to the SYS_RAW vias at (157.3/158.5, 118.65).

**Fix 3 (optional; halves BAT_PACK resistance):** join the two B.Cu BAT_PACK_B pieces with a ≥ 4 mm corridor:
- route roughly (194, 115) → (198.5, 110.5) → (198.5, 97.5) → (202.5, 93.5);
- it cuts through GND_BCU there; In1 stays a solid GND reference;
- connect it at SW101-1 (PTH, B.Cu pad) and to the Q103 drain via field (≥ 8 × 0.8/0.4).
- Simulated [EST]: 4.16 → **2.36 mΩ**, In2 hotspot 1.77 → 0.98 A/mm at 6 A.
- It is worth doing for the 6-10 A discharge path. For charging alone it is not needed.

**Fix 4 (recommended, U4 thermal):** replace the 0.2 mm F.Cu stubs U4-28 → (151.2, 119.3) and U4-26 → (151.95, 119.3) with pour fingers that start at full pad width at the toe (y 119.985) and fan out at 45°:
- ≥ 0.6 mm by y 119.5;
- ≥ 0.9 mm by y 118.9;
- ≥ 2.3 mm from y 117.0 to L1.

Keep U4-27 PGND's escape between them, and keep the SW copper area small (TI layout rule 5). Simulated [EST]: SW1 3.84 → 3.0 mΩ and SW2 4.31 → 3.1 mΩ, which removes about 35 mW of copper heat right at U4 at 4 A.

**Also relevant (already open in HANDOVER):** the U4 PGND thermal-via area is still unchecked. TI rule 8: thermal vias under the power MOSFETs. Section 5 shows that U4's RθJA, not ICHG, decides whether 4 A is sustained from 15-20 V. That item matters more than Fixes 1-4.

---

## 8. Bench bring-up (adds to `bench-bringup-plan.md`)

1. Write the register set (section 3) and read it back. Confirm the 750 kHz PWM_FREQ readback (REG13 bit 5 = 1).
2. Step ICHG: 1.0 → 2.0 → 3.0 → 4.0 A, each from 9 V and from 20 V PD, with the lid closed at about 25-30 °C room temperature, 30 min per step. Record:
   - U4 top case (≈ Tj), L1, Q103, J5, the pack surface;
   - IBAT and IBUS from the ADC;
   - TREG_STAT.

   Pass criteria: U4 ≤ 95 °C without TREG at 9 V; L1 ≤ 85 °C; Q103 ≤ 80 °C; pack ≤ 40 °C; J5 rise ≤ 15 °C.
3. Loud playback while charging at 20 V: IBUS must not exceed the IINDPM setting, there must be no CONV_OCP flag, and charge current must fall before the battery supplements.
4. JEITA: put the NTC in a warm bath at 43/46 °C (warm suspend expected at about 44.4 °C) and use a resistor substitution for 0/2/5/12 °C. Check the firmware gate below 3 °C.
5. Measure the VREG accuracy at 4.16 V with a 4-wire meter at the cell terminals after termination; it must be ≤ 4.200 V.
6. EN_BATOC: run boost peaks at low VBAT to confirm there is no IBAT_OCP trip at 8.5 A.
7. Depleted pack: pre-charge at 480 mA from 2.5 V, and check the 2 h pre-charge timer behaviour.

---

## 9. Residual risks

1. **Cell charge-temperature window and charge-voltage tolerance for the 50S are not read in Samsung's formal 50S specification.** The values come from sibling-cell specs and the SDI deck. Low impact, because the design stays inside the strictest sibling values.
2. **The pack PCM is unknown.** If its charge-OCP is below about 4.5 A, ICHG 4 A will trip it intermittently. Firmware must then cap ICHG at 80 % of the PCM charge rating. If its OV threshold is below 4.21 V, use VREG 4.10 V only.
3. **U4 thermal on the real board is unknown.** From 15-20 V the charger may sit in TREG (100 °C) for most of a charge. That is safe by design, but it is slower (about 3.1 A) and puts heat into the enclosure next to the pack (JEITA protects the cell).
4. The 17 W cap relies on firmware writing IINDPM after every contract change, and on the ILIM_HIZ/Q101 HIZ hold until then (contract). A firmware bug that leaves IINDPM at POR (3 A) on a 20 V contract would allow the converter to exceed its 5 A output rating under loud playback. It would then hit the cycle-by-cycle limits; that is protection, not damage, but it is unproven.
5. Efficiencies come from TI's typical curve with a different inductor (WE-LHMI 74437346022). The L1 core loss and the copper loss are assumptions.
6. The PD selection rule (highest voltage) is unverified. If the TPS25730 picks 9 V, the thermal outlook improves.
7. TREG accuracy is not tabulated in the datasheet (typical values only).

## 10. Open questions that need the owner

1. **Pack quote:** when the vendor answers, confirm three things: PCM charge-OCP ≥ 5 A (RFQ already asks for it), OV threshold and tolerance (want ≥ 4.225 V minimum), and the NTC part (103AT / B 3435). Also confirm the cell model: 50S or P45B. No decision is needed now; ICHG 4 A stands unless the PCM is weaker.
2. **Default float:** 4.10 V default with a 4.16 V "full" mode is my decision. Override it if run time matters more than cell life; 4.16 V is the hard ceiling either way.
3. **Optional hardware:** cap PD at 9 V or 15 V by replacing the direct ADCIN2-to-LDO_3V3 tie of U11 with a divider (TPS25730 Table 8-5 codes 1/5). This adds two resistors, which is a connection change, so I did not make it.
   - Charge speed is the same (the 17 W cap is reached at 9 V/2 A).
   - U4 loss drops about 0.6 W (20 → 9 V), and the TVS2200-vs-28 V and PPHV bias-derating concerns in `power-analysis-2026-11-01.md` become smaller.
   - The cost: VBUS current is higher at 9 V (1.9 A instead of 0.85 A).

## 11. Sources

**Local datasheets:**
- `datasheets/BQ25792.pdf/.txt` (SLUSDG1C): §8.1, §8.3, §8.4, §8.5 pp.9-16, Fig. 8-1 (p.20), §9.3.2, §9.3.4.3, §9.3.9.2-9.3.9.5, §9.3.12, §9.3.13.2, §9.5.1 REG00-REG18, REG2E, §10.2.2.1, §12.1
- `Bourns_SRN6045TA.txt` (2R2Y row)
- `CSD17579Q3A.txt` (electrical table, §5.2)
- `TPS25730.txt` (§8.3.10-8.3.15)
- `TPS25730_TRM.pdf` (0x33 TX_SINK_CAPS: writes do not change the request)
- `Samsung_INR21700-50S_SDI_introduction_2021.pdf` (new)
- `Samsung_INR21700-50E_spec_v0.2_sibling.pdf` and `Samsung_INR21700-50G_spec_v0.1_sibling.pdf` (new; siblings, not the 50S)

**Project reports:** `HANDOVER.md`, `reports/battery-pack-rfq.md`, `reports/sourcing-2026-10-12.md`, `reports/power-analysis-2026-11-01.md`, `reports/firmware-system-spec-2026-11-01.md`, `reports/replacement-power-control-contract.md`, `reports/bq25792-ilim-startup-review.md`, `reports/bq25792-l1-envelope.md`, `reports/audio-chain-architecture.md`, `reports/5-20v-pd-front-end-review.md`, `reports/routing-s0b-usb-template.md`.

**PCB:** `ai-files/pcb/work-route2/RT-2.kicad_pcb` (read only). Reproduce with:

```
~/Applications/kicad.AppImage python3.11 ai-files/helpers/copper_path_export.py RT-2.kicad_pcb geo.json "/Battery_Charger/BAT_INT,/Fuel_Gauge_Power/BAT_PACK,/Battery_Charger/PACK_RAW"
<venv python with numpy+shapely> ai-files/helpers/copper_path_solve.py geo.json /Battery_Charger/BAT_INT "U4:22,U4:23" "Q103:1,Q103:2,Q103:3" 148,104,178,128 0.05 6.0 20
```

**Not obtained:** the Samsung INR21700-50S formal product specification (imrbatteries.com 404, nkon.nl 403).
