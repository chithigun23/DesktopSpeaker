# DesktopSpeaker bench bring-up sheet (first boards, R6q / R8 fab set)

2026-10-12. Read-only on the KiCad project. Sources: `ai-files/HANDOVER.md` (HO), netlist exported from the current schematic with KiCad 10.0.6 (`kicad-cli sch export netlist`, all pin/net facts below come from it), datasheets in `ai-files/datasheets/` (DS), `reports/bq25792-ilim-startup-review.md`, `reports/replacement-power-control-contract.md`, `reports/project-review-fable.md` (sections MINORS and e), `reports/mcu-pin-allocation.md`, `reports/bluetooth-notes.md`, `reports/sync-y200-c275.md`, `fab/ORDER-NOTES.md`, `bom/DesktopSpeaker_JLC_BOM.csv`.

Numbers marked **(est.)** are my estimates; **TBD** means a datasheet value or a firmware decision is missing. Everything else names its source. No firmware exists: steps that need register access say which registers and values to use, and what tool to use.

Rule for every step: record the measured value in the log column of section 7. If a STOP condition hits, remove power, write down what you saw and do not go on to the next stage.

---

## 0. Equipment, tools and safety

### 0.1 Equipment
| Item | Use |
|---|---|
| Bench supply, 2 channels, 0-20 V / 0-5 A or more, with current limit (CC) | ch1 = "pack" at J5, ch2 = VBUS through a USB-C breakout |
| USB-C breakout with CC1 on a 56 kΩ Rp to VBUS (Default USB) | 5 V legacy source without PD. **Without an Rp the TPS25730D sees no attach and leaves the sink path off.** |
| USB-C PD tester (inline meter that decodes PDO/RDO; trigger mode is optional) + PD chargers: one 5 V-only, one 5/9 V, one 5/9/15/20 V 60 W or more | Stage A contract checks |
| DMM with diode test and µA range (a 10 Ω shunt or a µCurrent-type adapter for the ship-mode current) | all stages |
| Scope, 4 ch, 100 MHz or more, 10x probes with spring ground tips; a current probe if available; a **differential probe** for the speaker outputs | |
| ST-Link V2/V3 (or J-Link) + OpenOCD / STM32CubeProgrammer | SWD on J6 (or J7 with a TC2030-IDC cable) |
| I2C adapter at 3.0-3.3 V logic: Bus Pirate, FT232H (open-drain, `pyftdi`), or a CH341A in I2C mode | register access before firmware |
| Electronic load (constant current, 0-3 A at 12 V or more) | PVDD and rail load tests |
| Power resistors: 8 Ω 25 W x2, 4 Ω 50 W x1 (dummy speaker loads; actual driver impedances are TBD, plan.md section 9), 32 Ω for the headphone test | |
| Resistors for the TS window: 2.2 k, 4.7 k, 10 k, 22 k, 33 k (1 %) and one 103AT-2 thermistor | Stage C |
| Thermocouple or IR camera | U4, L1, Q103, U25, L200, U6, U7, U11 |
| Protected test pack (2P 21700, PCM, 10 k NTC per HO line 512; not yet sourced) with an inline fuse (est. 7.5 A blade) and a J5 harness with a TS break-out | Stage B2 onward |
| Near-field H probe (optional) | EMI spot checks |

### 0.2 Supply settings per stage
| Stage | Supply | Voltage | Current limit | Notes |
|---|---|---|---|---|
| 1 | none | - | - | unpowered checks only |
| A1 | ch2 via the USB-C breakout | 5.00 V | 150 mA | no pack, SW101 open |
| A2 | PD charger via the PD tester | contract | charger | no pack |
| B1 | ch1 at J5 (1 = PACK+, 3 = GND), 10 k from J5.2 to J5.3 | 3.70 V | 1.0 A (watch the first second: SYS capacitors charge through Q103) | no USB |
| B2 | real protected pack via fuse | pack | fuse (est. 7.5 A) | no USB |
| C | real pack (a plain bench supply cannot sink charge current; use the pack, a 2-quadrant supply, or ch1 with an electronic load in parallel that sinks more than ICHG) + PD charger | | | |
| D | real pack (preferred) or ch1 at 3.7-4.2 V with **8 A or more** | | | PVDD at 1-2 A load draws about 3.6-7 A from the pack (est., section 5.3) |

### 0.3 Hard limits (never exceed, any stage)
- Pack input (J5.1) never above **4.40 V** (est.): SYS_RAW feeds TPS63802 U14/U15 (VIN 5.5 V max, DS TPS63802), TPS2116 U20 VIN2 (1.6-5.5 V, HO line 395) and 3V8_BT follows; BM83 BAT_IN abs max 4.3 V (`reports/bluetooth-notes.md` line 7) is behind U15 and stays safe only while U15 regulates.
- **No reverse-polarity protection on J5.** Check the harness polarity with the DMM before every mating: J5.1 PACK+, J5.2 TS/NTC, J5.3 GND (netlist; HO line 443).
- VBUS (TP1) never above 24 V peak (est.): TPS25730D VBUS_IN/PPHV recommended 0-22 V, abs 28 V (DS TPS25730 lines 531, 589); the TVS2200 clamp can exceed 28 V at full rated surge (HO line 30). The board requests up to 20 V (section 2.2).
- Speaker outputs are BTL: never connect a scope ground or a grounded load to J9/J10/J11; measure with a differential probe or two probes and math.
- Do not inject a 3.3 V clock into U24 XI: XI abs max 2.1 V (DS PCM1862 line 648).
- J4 pin 1 is **LDO_3V3, an output** of U11 (5 mA total budget, DS TPS25730 line 596). Use it only as the adapter's logic reference; never drive it, never power an adapter from it.

### 0.4 Parts that get hot
U4 BQ25792 and L1 (charging; U4 PGND pin 27 via loading, HO lines 23, 576), Q103 CSD17579Q3A (battery current), U25 TPS61088 and L200 (PVDD), U6/U7 TAS5825M and L201-L206 (fable M8: case temperature at 2 x 10 W for 10 min), U11 TPS25730D (3 A sink path), U19 TPS7B8450 at 20 V input (dissipation (VBUS - 5 V) x I_AUX), R170 2.2 Ω.

### 0.5 Debug and I2C access points (netlist)
| Header / TP | Pins | Bus / use |
|---|---|---|
| J6 (1x4 2.54 mm) | 1 SWDIO, 2 SWCLK, 3 NRST, 4 GND. **No VTref pin**: connect the ST-Link VTref/T_VCC to TP4 (3V_AO). | SWD |
| J7 (TC2030-IDC footprint, not fitted) | 1 3V_AO, 2 SWDIO, 3 NRST, 4 SWCLK, 5 GND, 6 nc | SWD alternative |
| J4 (1x4) | 1 LDO_3V3 (ref only), 2 PDCTRL_SCL, 3 PDCTRL_SDA, 4 GND | **PD bus only**: TPS25730D at 0x20 (DS TPS25730 Table 8-3). Pull-ups R14/R15 10 k to LDO_3V3, present only with VBUS. |
| TP15 CTRL_SDA, TP16 CTRL_SCL, GND TP25 | | **Charger/gauge bus**: BQ25792 0x6B (DS line 3205), MAX17048 0x36 (behind U13/U16, only connected when BAT_PACK > about 3.1 V). Pull-ups R120/R121 4.7 k to 3V_AO. Use 3.0 V logic. |
| TP17 AUD_SDA, TP18 AUD_SCL, GND TP24/TP26 | | **Audio bus**: PCM1862 0x4A (MS/AD = GND, DS Table 21: 0x94 8-bit), TAS5825M U6 0x4C (ADR = GND), U7 0x4D (ADR 1 k to GND, R261) (DS TAS5825M Table 5). Pull-ups R209/R210 2.2 k to 3V3_AUDIO. |
| J8 (1x5) | 1 BT_RST_M, 2 BT_SYS_CFG (P3_4), 3 BT_RXD_M, 4 BT_TXD_M, 5 GND | BM83 test mode / Config Tool |

Using an external I2C adapter while there is no firmware: hold the MCU halted (`reset halt` over SWD) so its I2C pins stay in the reset analog state. The STM32 GPIO addresses below are from memory of RM0444 (**verify**): RCC_IOPENR 0x4002 1034 (bit0 A, bit1 B, bit2 C, bit3 D), GPIOA 0x5000 0000, GPIOB 0x5000 0400, GPIOC 0x5000 0800, MODER offset 0x00, BSRR offset 0x18 (set = bit n, reset = bit n+16). Driving an enable pin by SWD (OpenOCD `mww`), example PA10 = CHG_SYS_ENABLE: `mww 0x40021034 0x0F` (clocks A-D), `mww 0x50000018 0x04000000` (PA10 low first), `mww 0x50000000 <MODER with bits 21:20 = 01>` (read it with `mdw` first; reset value per RM0444 is 0xEBFFFFFF, giving 0xEBDFFFFF), then `mww 0x50000018 0x00000400` for high. A target reset returns every enable to its pull-down default, which is the safe state. Better: write a minimal bring-up firmware (SWD + RTT console) that does the same register writes; the I2C sequences below are the specification for it.

MCU enable pins used below (`reports/mcu-pin-allocation.md`, netlist): PA10 CHG_SYS_ENABLE, PC6 CHG_ENABLE, PA1 5V_LOGIC_EN, PC7 CODEC_PWR_EN, PA8 BT_PWR_EN, PD4 BT_FORCE_PWM, PA7 AMP_BOOST_EN, PA6 AMP_PDN, PA15 HP_EN, PC0 HP_SEL_A, PD1 HP_SEL_B, PC3 HP_G0, PA4 HP_G1, PB3 BT_MFB, PB4 BT_RST_N (open-drain low only). All have 100 k pull-downs (R111, R107, R142, R212, R152, R153, R255, R259, R236, R234, R235, R237, R238, R184 module side).

---

## 1. Bare board, unpowered

Measure with the DMM resistance range, red lead on the test point, black on the nearest GND TP (TP23 PD area, TP25 MCU, TP26 centre, TP27 charger, TP24 amplifiers). Readings on capacitive rails rise for seconds; record the value after 5 s. Then reverse the leads and record again. Values are the passive DC paths found in the netlist; IC leakage lowers them **(est.)**.

| Step | Point (net) | DC path to GND in the netlist | Expected after 5 s | STOP if |
|---|---|---|---|---|
| 1.1 | TP1 USB_VBUS | D6 TVS2200, D7 1N5819HW (cathode on VBUS), C2/C184/C316, U11 VBUS_IN, U19 | > 100 kΩ (est.); reversed leads in diode mode: **0.15-0.35 V** (D7 forward, est.) | < 1 kΩ, or no diode reading when reversed (D7 missing/reversed) |
| 1.2 | VBUS_PD at C315 (no TP) | U11 PPHV, U4 VBUS/VAC1/VAC2, C100/C111/C313/C315 | > 100 kΩ (est.) | < 1 kΩ |
| 1.3 | TP5 LDO_3V3 | R10 200 k + R11 10 k (ADCIN4 divider) = 210 kΩ, in parallel with U11 | 100-210 kΩ (est.) | < 10 kΩ |
| 1.4 | TP11 REGN | R100+R101 = 35.33 kΩ (TS divider) ∥ R108+R109 = 280 kΩ ∥ R103/R110 paths | **about 31 kΩ** (35.33 ∥ 280) | < 20 kΩ or > 40 kΩ (missing R100/R101/R108/R109) |
| 1.5 | TP2 SYS_RAW | U4 SYS, U14/U15/U25 VIN, U20 VIN2, many 22 µF caps | > 10 kΩ (est.) | < 100 Ω |
| 1.6 | TP3 BAT_PACK | U5 VDD, U21 VDD, R112 100 Ω to BATP, Q103 drain | > 100 kΩ (est.) | < 1 kΩ |
| 1.7 | TP4 3V_AO | MCU, R241 1 M + J3 switched tip + R243 10 k, R126 1 M, pull-ups to open-drain nets | 10 kΩ-1 MΩ (est.) | < 1 kΩ |
| 1.8 | TP6 3V3_AUDIO | R232+R233 = 94 kΩ (VMID) ∥ R239 path ∥ ICs | 30-94 kΩ (est.) | < 5 kΩ |
| 1.9 | TP7 5V_LOGIC | R140+R141 = 87.8 kΩ ∥ U22/U23 inputs | 40-88 kΩ (est.) | < 5 kΩ |
| 1.10 | TP8 5V_CODEC | R170 2.2 Ω to U2 VBUS, C170/C225 | > 10 kΩ (est.) | < 1 kΩ |
| 1.11 | TP9 3V8_BT | R150+R151 = 695 kΩ ∥ R154 100 kΩ = 87.4 kΩ ∥ BM83 BAT_IN | 40-88 kΩ (est.) | < 5 kΩ |
| 1.12 | TP10 PVDD_AMP | R250+R251 = 555 kΩ ∥ U6/U7 PVDD; C275 100 µF makes it climb slowly | 100-555 kΩ (est.) | < 1 kΩ |
| 1.13 | USB_AUX_5V at C5 | R124+R125 = 280 kΩ ∥ U20 | 100-280 kΩ (est.) | < 10 kΩ |
| 1.14 | Diode-mode paths (red → black): TP2 SYS_RAW → TP10 PVDD_AMP | U25 high-side body diode (synchronous boost, no load disconnect, est.) | 0.3-0.7 V (est.) | short (< 0.05 V) or open in both directions |
| 1.15 | BAT_INT (C106 +) → TP3 BAT_PACK | Q103 body diode (source BAT_INT, drain BAT_PACK) | 0.4-0.8 V (est.) | short |
| 1.16 | TP3 → TP2, TP1 → TP2, TP1 → TP10, TP2 → TP4 | no direct paths | no short (> 1 kΩ) | < 100 Ω |

Polarity and orientation (visual, then DMM):
- 1.17 C275 (Panasonic EEHZA1E101XP hybrid polymer, 100 µF 25 V, THT `CP_Elec_8x10`): pad 1 = "+" = PVDD_AMP, pad 2 = GND (netlist). The "+" and chamfer are on the pad 1 (-X) side, band on the right (`reports/sync-y200-c275.md` line 104). STOP if reversed.
- 1.18 D7 1N5819HW: cathode band to USB_VBUS (pin 1), anode GND. D6 TVS2200 (WSON, pin 1 GND, pins 4-6 VBUS), D5 ESDA25L (3 = GND), D1 TPD2E2U06 (4 = GND), D200/D201 PESD5V0S2BT (3 = common GND; pinout from a search summary, HO line 486: VERIFY on the part marking).
- 1.19 Pin-1 marks: U1 BM83, U3, U4, U6, U7, U11, U24, U25 (TPS61088 pin-1 orientation of the model not verified, HO line 498), J1 (ORDER-NOTES checklist 3).
- 1.20 SW101 (CW GRB112B802BR1, panel rocker, wired with fastons): continuity between the two wired terminals in ON, open in OFF; the LED terminal is unused (HO line 61 of the R6q section). STOP if the "OFF" position conducts.
- 1.21 SW100: QON node (SW100 pad 1, R113) to GND: open; pressed: < 1 Ω.

Short checks on fine-pitch parts (magnifier, then DMM on the adjacent nets):
- 1.22 **J1 USB-C**: CC1 (A5) and CC2 (B5) to USB_VBUS > 1 MΩ (a bridge would put 20 V on CC). CC1/CC2 to GND: the U11 dead-battery Rd and C182/C183 make this DMM-dependent, expect kΩ range (est.); STOP if < 1 kΩ. D+ (A6/B6) / D- (A7/B7) to VBUS and to each other: > 1 MΩ.
- 1.23 U11 TPS25730D (REF 40-pin WQFN): VBUS_IN 23-25 vs PPHV 20-22 (they are separate nets: open while unpowered); CC1 28 / CC2 29 vs RESERVED 26/27 (GND) and DRAIN 30.
- 1.24 U4 BQ25792 (VQFN-29): SW1 (28) and SW2 (26) to GND (27) not shorted; VBUS (2/3) vs BTST1 (4) and REGN (5); SDA/SCL (15/14) vs TS (16).
- 1.25 U6/U7 TAS5825M (VQFN-32): OUT_x to PVDD and to GND not shorted (OUT nets read through L201-L206 at J9/J10/J11: each J pin to GND > 1 kΩ, est.).
- 1.26 U24 PCM1862 (TSSOP-30), U3 LQFP64, U2 SSOP-28, U14/U15 TPS63802 (DLA 0.5 mm), U25 TPS61088 (RHL), U10 TPA6132A2, U20 SOT-583, U19 WSON-8, U8/U9 VSSOP-10, BM83 module castellations: visual bridge check. Via-in-pad joints R10.2, R224.1, C215.1 may wick solder (HO line 17): inspect.
- 1.27 R256 (U25 MODE to GND) must be **unfitted** (DNP; ORDER-NOTES "Not assembled"). Netlist: R256 pin 1 = Net-(U25-MODE), pin 2 = GND.

---

## 2. Stage A: USB only, no pack (SW101 OFF, J5 unplugged)

Expected power path (netlist): J1 VBUS → D6/D7 → U11 VBUS_IN → U11 PPHV (sink switch) → VBUS_PD → U4 BQ25792. In parallel U19 TPS7B8450 (5.0 V, EN = VBUS) → USB_AUX_5V → U20 TPS2116 VIN1 (priority) → U12 TPS7A0230 (3.0 V) → 3V_AO → MCU. Before firmware, CHG_SYS_ENABLE is low (R111), so Q102 is off, Q101 is on and ILIM_HIZ is held near 0 V: BQ25792 does not switch (DS BQ25792 pin table line 401: below 0.75 V the converter stops, REGN stays on) and **SYS_RAW stays at about 0 V with no battery**. The charger also caches a 100 mA ILIM clamp at POR (review report).

### 2.1 Legacy 5 V through the Rp breakout (A1)
| Step | Connect / do | Measure | Expected | STOP if |
|---|---|---|---|---|
| A1.1 | ch2 5.00 V / 150 mA into the breakout, plug into J1 | supply current | settles at 5-20 mA (est.: TPS25730 VBUS LDO + BQ REGN + U19 + blank MCU) | > 50 mA, or CC limit reached |
| A1.2 | | TP1 USB_VBUS | 5.00 V minus cable drop | < 4.5 V |
| A1.3 | | TP5 LDO_3V3 | 3.3 V (TPS25730 VBUS LDO; exact tolerance TBD) | < 3.0 V or > 3.6 V (ADCIN abs 4 V) |
| A1.4 | | VBUS_PD at C315 | ≈ TP1 (sink switch closed; AlwaysEnableSink, DS Table 8-3) | 0 V after 1 s: sink path did not close (check FAULT_IN pin 18 = high via R13) |
| A1.5 | | TP11 REGN | 4.6-5.0 V (DS BQ25792 VREGN at VBUS 5 V), about 150 ms after VBUS (DS 9.3.4 step 5) | absent: BQ not powered |
| A1.6 | | ILIM_HIZ (R109 top / U4 pin 17) | < 0.1 V (Q101 on) | > 0.75 V: converter may start; check Q101/Q102/R110/R111 |
| A1.7 | | CE_N (R103 / U4 pin 13) | ≈ REGN (charge disabled) | < 1.3 V |
| A1.8 | | USB_AUX_5V at C5 | 4.7-5.0 V at a 5 V input (dropout; est.); TPS7B84 ±0.75 % when VBUS ≥ about 5.5 V | < 4.0 V |
| A1.9 | | U20 PR1 (R124/R125 node) | 1.79 V nominal (5.0 x 100/280); U20 selects VIN1 above VREF 0.92-1.08 V (DS TPS2116 line 318), i.e. USB_AUX_5V above 2.58-3.02 V | < 1.1 V |
| A1.10 | | TP4 3V_AO | 2.955-3.045 V (TPS7A02 ±1.5 %, DS line 298) | outside 2.9-3.1 V |
| A1.11 | | TP2 SYS_RAW | about 0 V (< 0.3 V, est.: HIZ held, no battery) | > 1 V: converter is switching without permission (Q101/ILIM_HIZ fault) |
| A1.12 | | TP3 BAT_PACK, TP6, TP7, TP8, TP9 | 0 V (est. < 0.1 V) | any rail up |
| A1.13 | | TP10 PVDD_AMP | ≈ 0 V (follows SYS_RAW through the U25 body diode, est.) | > 1 V |
| A1.14 | | PD_PLUG_EVENT (R16), PD_SINK_EN (R17) | PLUG_EVENT high ≈ LDO_3V3 (open drain, 1 = connection present); SINK_EN **low** (DS pin table: 0 = sink path enabled; the net name is misleading) | PLUG_EVENT low with a cable attached |
| A1.15 | **Blank-MCU pin check**, before any SWD session: measure each enable at its pull-down: PA10 (R111), PC6 (R107), PA1 (R142), PA7 (R255), PA6 (R259), PA8 (R152), PC7 (R212) | DC voltage | all < 0.3 V | any > 1 V. A blank STM32G0 may run its ROM bootloader (empty-flash boot) and enable internal pull-ups on bootloader pins (USART1 RX = PA10 = CHG_SYS_ENABLE, SPI pins on PA4-PA7; **TBD: confirm in ST AN2606, not in ai-files**). If any enable floats up: hold NRST low (J6.3 to J6.4) for all later stage-A work and flash a safe-state firmware first. |
| A1.16 | ST-Link on J6 (VTref to TP4), "connect under reset" | IDCODE / device ID | SW-DP Cortex-M0+; DBGMCU DEV_ID 0x460 for STM32G07x (**verify RM0444**); read option bytes and record nBOOT_SEL/nBOOT0/nBOOT1 (allocation doc assumes nBOOT_SEL = 1) | no SWD connection: check NRST (TP19 ≈ 3.0 V when released), SWCLK has R160 100 k pull-down |
| A1.17 | Flash a safe-state image (all enables driven low, I2C pins input) or keep the core halted | TP4, supply current | 3V_AO unchanged; current change < 10 mA (est.) | |
| A1.18 | I2C on J4 (adapter VIO = J4.1, not powered from it) | scan PD bus | ACK at 0x20 only | no ACK: R14/R15 pull-ups, ADCIN decoding |
| A1.19 | Read U11 0x34 ACTIVE_CONTRACT_PDO and 0x35 ACTIVE_CONTRACT_RDO (TRM SLVUCJ7: first byte returned is the byte count) | | **no PD contract** with a legacy Rp source: both cleared/zero (expected, est.) | non-zero contract from a non-PD source |
| A1.20 | I2C on TP15/TP16 (MCU halted) | scan CTRL bus | 0x6B ACKs (BQ25792). **0x36 must NOT ACK** (gauge isolated: U21 sees BAT_PACK = 0 V, Q104 off, GAUGE_ISO_N pulled to 3V_AO by R126, TS5A3167 switches open) | 0x36 ACK with no pack (isolation failure) |
| A1.21 | Read BQ25792 REG48 (Part info) | | bits 5:3 PN = 001 (BQ25792), i.e. (REG48 & 0x38) = 0x08 (DS 9.5.1.57); DEV_REV TBD | other PN |
| A1.22 | Read REG1B, REG1C, REG20, REG21, REG14, REG00, REG01-02, REG03-04, REG06-07, REG0F, REG10 | | REG1B bit0 VBUS_PRESENT = 1; REG14 = 0x16 (POR, SFET_PRESENT 0, EN_IINDPM 1, EN_EXTILIM 1); REG00 VSYSMIN = 0x04 (3.5 V, 1S from PROG R102 4.7 k = 750 kHz/1S, DS Table 9-1); VREG = 0x01A4 (4.20 V); ICHG = 0x00C8 (2 A, 1S default, DS Table 9-2); REG10 = 0x85 (watchdog 40 s); REG0F = 0xA2. IINDPM: 3 A POR, may be rewritten by D+/D- detection (U4 D+/D- are unconnected on this board), so record it. | VSYSMIN/VREG show 2S/3S values: PROG resistor wrong |

Leave the board for 60 s: the BQ watchdog (40 s) expires because nobody services it. Expected: REG1B bit5 WD_STAT = 1; nothing switches (ILIM_HIZ still low). This is the normal state before firmware.

### 2.2 PD contract (A2)
U11 configuration from the netlist and DS TPS25730 Tables 8-1/8-3/8-5/8-6: ADCIN1 = GND → code 0 → minimum 5 V; ADCIN2 = LDO_3V3 → code 7 → **maximum 20 V**, I2C address 0x20, AlwaysEnableSink; ADCIN3 = GND → 0, ADCIN4 = R11/(R10+R11) = 10/210 = 0.0476 → code 1 → **operating current 0 A, maximum current 3 A**. So the board asks for the source's PD contract inside 5-20 V, at up to 3 A. This matches the user decision "5/9/15/20 V, EPR out of scope" (plan.md line 10) and HO bench order item 1. (It does **not** match a "5/9 V only" profile; see Inconsistencies.)

| Step | Source | Expected on the PD tester | Expected at TP1 / VBUS_PD | STOP if |
|---|---|---|---|---|
| A2.1 | 5 V-only PD charger | contract 5 V, RDO max current 3 A or the PDO limit, CapabilityMismatch = 0 | 4.75-5.25 V | contract refused / hard resets repeating |
| A2.2 | 5/9 V charger | 9 V fixed PDO selected (highest voltage inside the window is my expectation; the selection rule is not stated in the local DS: **TBD**) | 8.55-9.45 V | > 10 V |
| A2.3 | 5/9/15/20 V charger, **only after A2.1-A2.2 pass and the scope is armed (A2.6)** | 20 V PDO, current ≤ 3 A | 19.0-21.0 V; VBUS_PD within about 0.1 V of TP1 at light load | any EPR (28/36/48 V), AVS or PPS contract; TP1 > 21.5 V steady |
| A2.4 | each source | I2C read of U11 0x34: ActivePDO (32-bit little endian): fixed PDO bits 19:10 = voltage in 50 mV, bits 9:0 = max current in 10 mA. Example 20 V / 3 A: bits 19:0 = 0x6412C. 0x35 RDO: bits 30:28 object position, bit 26 CapabilityMismatch = 0; the 3 A (0x12C) maximum should appear in a current field (exact field mapping for "operating 0 A" TBD) | matches the tester | tester and register disagree |
| A2.5 | each source | BQ25792 REG35 VBUS_ADC (enable ADC first: REG2E = 0x80) and REG37/39 VAC1/VAC2 | within 2 % of TP1 (est.) | |
| A2.6 | scope: ch1 TP1, ch2 VBUS_PD (C315), ch3 TP5 LDO_3V3, ch4 current probe on VBUS if available. 5 V/div, 1 ms/div (then 100 µs/div), trigger TP1 rising 3 V, normal mode | attach waveform (cold plug), then a 5 → 20 V renegotiation (unplug/replug the 20 V charger) | monotonic rise, overshoot < 10 % (est.); VBUS_PD follows after the sink switch turn-on (tPPHV_ON 1.5-2.1 ms, DS line 823); inrush charge into about 50-97 µF nominal on PPHV (C315 47 µF + C100/C111 + PMID bank behind U4) | **TP1 > 24 V peak**, VBUS_PD > 22 V, ringing that crosses 0 V, LDO_3V3 brown-out during attach |
| A2.7 | 20 V contract, idle 10 min | U11, U19, D6 temperatures | U19 (TPS7B84) warm only: (20 - 5) V x I_AUX ≈ 0.05-0.2 W (est.) | any part > 60 °C at idle (est.) |
| A2.8 | Stage A idle current at each contract | PD tester current | 5-20 mA at 5 V; less at 20 V (est.) | > 50 mA with all enables low |

Not tested here: BQ watchdog policy, charging (stage C), audio rails (stage D).

---

## 3. Stage B: pack only, no USB

### 3.1 Bench supply as pack (B1)
Setup: ch1 3.70 V / 1.0 A at J5.1 (+) and J5.3 (-) via the harness, 10 k from J5.2 to J5.3, SW101 OFF first, USB unplugged, ST-Link attached (VTref TP4).

| Step | Do | Measure | Expected | STOP if |
|---|---|---|---|---|
| B1.1 | supply on, SW101 OFF | ch1 current; TP3 | < 10 µA (est.: PACK_RAW has only SW101 and J5 on it); TP3 0 V | > 100 µA with SW101 OFF |
| B1.2 | SW101 ON | ch1 current peak, then steady | short inrush (SYS caps, about 250 µF, est.) then 1-6 mA with a blank or halted MCU (est.) | CC limit sustained > 100 ms |
| B1.3 | | TP3 BAT_PACK | 3.70 V | - |
| B1.4 | | Q103 gate (Net-(Q103-G), U4 SDRV pin 24) | ≈ BAT + 5 V ≈ 8.7 V (DS 9.3.12: charge pump about 5 V above battery, 100 nA drive; high-impedance node: use 10 MΩ DMM, reading sags, est.) | < 5 V: ship FET not enhanced |
| B1.5 | | TP2 SYS_RAW | ≈ 3.65-3.70 V (BATFET + ship FET on, battery-only mode, DS 9.3.3) | < 3.4 V at light load |
| B1.6 | | TP4 3V_AO | 2.955-3.045 V (U20 now on VIN2 = SYS_RAW) | |
| B1.7 | | TP10 PVDD_AMP | ≈ SYS_RAW - 0.3...0.7 V (U25 body diode, boost off, est.) | > SYS_RAW |
| B1.8 | | TP11 REGN | ≈ 0 V (REGN stays off on battery only, DS 9.3.3) | |
| B1.9 | | QON node (SW100 pad 1) and CHG_QON_SENSE (PC13 side of R113) | 3.2 V typ (DS VQON) up to 3.6-3.8 V (pin table); PC13 side the same (no current) | < 1.3 V (VIH_QON min) |
| B1.10 | | U21 RESET (Q104 gate), GAUGE_ISO_N | RESET high ≈ BAT_PACK (BAT above 3.003-3.126 V, HO line 425); GAUGE_ISO_N ≈ 0 V | GAUGE_ISO_N high at 3.7 V |
| B1.11 | I2C on TP15/TP16 (MCU halted) | scan | 0x6B and **0x36** ACK | 0x36 missing |
| B1.12 | MAX17048 reads (register map from the MAX17048 PDF; the local txt is not machine-readable: **verify**): VERSION 0x08, VCELL 0x02, SOC 0x04, CONFIG 0x0C, STATUS 0x1A | | VERSION 0x001x; VCELL 78.125 µV/LSB: 3.700 V → 0xB900 (±1 %, est.); CONFIG 0x971C at POR; STATUS RI bit set after first power | VCELL off by > 50 mV |
| B1.13 | BQ25792 with ADC on (REG2E = 0x80): REG3B VBAT_ADC (VBATP via R112), REG3D VSYS_ADC, REG3F TS_ADC | | VBAT 3700 mV (0x0E74) ± 1 % (est.); TS 58.9 % (10 k: 30.1 ∥ 10 = 7.51 k against 5.23 k; register ≈ 0x025C at 0.0977 %/LSB); TS reads only with REGN on, so it may read 0 on battery only (est.) | VBAT differs from DMM by > 50 mV |
| B1.14 | Lower ch1 slowly to 3.00 V, then back to 3.70 V | 0x36 ACK, GAUGE_ISO_N | gauge drops off the bus between 3.13 and 3.00 V (U21 falling threshold) and returns on the way up (+ hysteresis) | MCU resets above 3.0 V (3V_AO dropout, est.: U12 dropout small at 3 V) |
| B1.15 | Battery-only quiescent with the MCU in reset (NRST held low) | ch1 current (µA range) | BQ IQ_BAT_ON 17 µA typ / 24 µA max (at VBAT 8 V, ADC off, DS line 563) + MAX17048 (active about 23 µA, hibernate 3-5 µA, est.) + U21 + R127 about 4.35 µA (HO line 427) + MCU in reset (TBD, STM32 datasheet) + regulators off (U14/U15 about 0.15 µA, HO plan line 189). Estimate 40-80 µA with the MCU held in reset; the firmware Stop-mode figure is TBD | > 500 µA with all enables low |

### 3.2 Ship mode, QON wake, system reset (needs I2C writes)
| Step | Do | Expected | STOP if |
|---|---|---|---|
| B2.1 | REG14 = 0x96 (SFET_PRESENT = 1, IBAT_REG 5 A default, EN_IINDPM 1, EN_EXTILIM 1). Read back. POR default 0 locks SDRV_CTRL (DS REG14) | reads 0x96 | write does not stick |
| B2.2 | REG11 = 0x44 (AUTO_INDET_EN 1 as POR, SDRV_CTRL = 10 ship mode, SDRV_DLY = 0 → 10 s delay). Release the MCU/adapter within 10 s | after 10 s: Q103 gate → 0 V, SYS_RAW collapses, 3V_AO → 0 V, MCU off | SYS stays up (ship request ignored: check SFET_PRESENT) |
| B2.3 | ship-mode current (µA range on ch1) | BQ IQ_BAT_OFF 11 µA typ / 16 µA max (DS line 567, at 8 V) + gauge (hibernate 3-5 µA or active about 23 µA, est.) + U21/R127 about 4.35 µA → **about 18-45 µA (est.)** | > 100 µA |
| B2.4 | QON node voltage in ship mode | 3V_AO is off, so PC13 is unpowered and R113 (100 k) loads the 200 k internal pull-up through PC13's protection path: expect 1.0-2.0 V (est.) | **< 0.4 V (VIL_QON)**: the button tap holds QON low and the board will wake/reset by itself. Fix: higher R113 or a diode; record |
| B2.5 | press SW100 < 0.5 s | stays in ship mode (tSM_EXIT 1 s typ with WKUP_DLY = 0, DS 9.3.12.2) | wakes on a short tap |
| B2.6 | press SW100 1.5 s | exits ship mode: Q103 on, SYS_RAW back, 3V_AO back, MCU boots; SDRV_CTRL reads 00 | no wake after 3 s press |
| B2.7 | ship mode again, then plug USB (stage A source) | exits ship mode on adapter plug-in (DS 9.3.12.2) | |
| B2.8 | in normal mode hold SW100 12 s | system power reset: ship FET off about 350 ms (tRST 10 s typ, tRST_SFET 350 ms, DS 9.3.12.3), SYS dips, MCU resets, then everything returns | board stays off |
| B2.9 | Optional shutdown mode: REG11 = 0x42 (SDRV_CTRL = 01), no USB | pack current 0.5 µA typ / 0.7 µA (BQ ISD_BAT) + gauge + U21; wakes only on USB plug-in (QON does not wake it) | |
| B2.10 | SW101 OFF while running | TP3 → 0 V, board off; pack current → 0 (only SW101/harness leakage). Turn ON again: board restarts like B1.2 | arcing/heating at SW101 terminals |

### 3.3 Real pack (B3)
Repeat B1.1-B1.13 and B2.2-B2.6 with the protected pack through the fuse (TS from the pack NTC). Expected TS ≈ 58.9 % at 25 °C with a 103AT-type NTC. **STOP** if the pack's PCM trips on SW101 ON (inrush), or if VCELL disagrees with the DMM by more than 20 mV.

---

## 4. Stage C: charging (pack + USB)

Policy (HO lines 407-409, `reports/bq25792-ilim-startup-review.md`, `reports/replacement-power-control-contract.md`): hold HIZ (CHG_SYS_ENABLE low) during configuration, disable the watchdog and the auto-detection/ICO/HVDCP rewrites, set and read back IINDPM with EN_EXTILIM cleared, set SFET_PRESENT, then release HIZ, then enable charge as a separate last step. ICHG at most 3 A on the bench (HO line 23, fable M2).

Setup: real pack (or 2-quadrant supply) on J5, PD charger via the tester (start with 9 V), ST-Link + I2C adapter on TP15/TP16, thermocouple on U4, second on L1 or the U4 PGND via area (U4 pin 27 region, between C311/C312), third on Q103.

### 4.1 Register sequence (BQ25792 at 0x6B; 16-bit registers are two bytes starting at the lower address, high byte first: **verify against DS 9.5 on the first read**)
| # | Register write | Value | Why (DS section) | Read back / expect |
|---|---|---|---|---|
| C1 | (precondition) PA10 CHG_SYS_ENABLE low, PC6 CHG_ENABLE low | - | contract table "Hardware defaults" | ILIM_HIZ < 0.1 V, CE_N ≈ REGN |
| C2 | read REG48, REG1B, REG1C, REG20, REG21 | - | identity, VBUS/PG present, no fault | PN = 1; REG1B PG_STAT may be 1; REG20/21 = 0 |
| C3 | REG10 (read-modify-write): WATCHDOG[2:0] = 000 | 0x80 if it read 0x85 | REG10: watchdog expiry resets ICHG to the PROG default (2 A), EN_CHG, EN_IINDPM, AUTO_INDET_EN | bits 2:0 = 000 |
| C4 | REG11 | 0x00 | AUTO_INDET_EN = 0, HVDCP_EN = 0, EN_9V/EN_12V = 0, SDRV_CTRL = 00 | 0x00 |
| C5 | REG0F | 0x82 | EN_CHG = 0 (second interlock beside CE), EN_ICO = 0, EN_HIZ = 0, EN_TERM = 1 | 0x82 |
| C6 | REG14 | 0x94 | SFET_PRESENT = 1, EN_IINDPM = 1, **EN_EXTILIM = 0** (the cached 100 mA pin clamp is otherwise kept; review report) | 0x94 |
| C7 | REG06-07 IINDPM | 0x0032 (500 mA) for the first run | 10 mA/LSB, range 100-3300 mA | 0x0032 |
| C8 | REG01-02 VREG | 0x01A4 (4.20 V) unless the pack datasheet asks for less; the plugged-in ageing policy (for example 4.10 V = 0x019A) is **TBD** (plan.md line 45) | 10 mV/LSB, 1S range 3.0-4.99 V | as written |
| C9 | REG03-04 ICHG | 0x0032 (0.5 A) | 10 mA/LSB | 0x0032 |
| C10 | REG00 VSYSMIN | leave 0x04 (3.5 V) | 250 mV/LSB + 2.5 V | 0x04 |
| C11 | REG2E ADC | 0x80 | ADC_EN, continuous, 15-bit | 0x80 |
| C12 | read all of C3-C11 again, REG05 VINDPM (auto-set on plug-in, 100 mV/LSB; TBD what value it picks at 9/20 V) | - | contract step 6 | every value as written; STOP if any differs |
| C13 | **release HIZ**: PA10 high | - | | ILIM_HIZ 1.64-1.86 V (0.357 x REGN, REGN 4.6-5.2 V); SYS_RAW ≈ VBAT + 50-200 mV (est.); REG1B PG_STAT = 1; IBUS (REG31) small (< 100 mA) |
| C14 | **enable charge**: REG0F = 0xA2 (EN_CHG = 1), then PC6 high (CE low) | - | | REG1C CHG_STAT = 3 (fast charge) or 2 (pre-charge if VBAT < VBAT_LOWV); IBAT (REG33, 1 mA/LSB) 0.45-0.55 A (est. ±10 %) |

Fault response for every C-step: if anything is wrong, drop PA10 and PC6 low first (hardware stops conversion and charge), then debug.

### 4.2 Charge-current steps and thermals
| Step | Source | ICHG / IINDPM | Expected | STOP if |
|---|---|---|---|---|
| C15 | 9 V | ICHG 0.5 A (0x0032), IINDPM 0.5 A | IBAT ≈ 0.5 A; IBUS ≈ 0.25 A at 9 V (est., about 90 % efficiency); U4/L1 < 15 °C rise | IBAT > 0.6 A; REG20/21 fault bits |
| C16 | 9 V | ICHG 1.0 A (0x0064), IINDPM 1.0 A (0x0064) | IBAT ≈ 1.0 A, IBUS ≈ 0.5 A (est.); 10 min soak, U4 rise < 25 °C (est.) | U4 case > 70 °C |
| C17 | 9 V or 20 V | ICHG 3.0 A (0x012C), IINDPM 2.0 A (0x00C8) at 9 V or 1.0 A at 20 V (input power ≈ 3 A x 4 V / 0.9 ≈ 13 W, est.) | IBAT ≈ 3.0 A (CC); 15 min soak: record U4, L1, PGND via area, Q103, U11 | **U4 case > 85 °C** or TDIE (REG41, 0.5 °C/LSB) > 100 °C (est.; TREG thermal regulation default 120 °C, REG16), L1 > 85 °C, IBAT oscillating |
| C18 | 5 V (5 V-only source) | ICHG 1.0 A, IINDPM 1.5 A | VINDPM may limit on a weak cable: REG1B VINDPM_STAT / IINDPM_STAT, record VBUS at U4 | VBUS_PD < 4.3 V with charge still increasing |
| C19 | Watchdog test (optional): REG10 WATCHDOG = 0x4 (20 s), do not service | after 20 s: REG1B WD_STAT = 1; ICHG resets to 2 A and EN_CHG = 1 (DS REG03/REG0F "reset by WATCHDOG"); **IINDPM and EN_EXTILIM do not reset** (review report) | document; firmware must disable or service the watchdog | |
| C20 | REG_RST test (optional), PA10 low first: REG09 read-modify-write with bit 6 REG_RST = 1 (REG09 POR 0x05 → 0x45; DS Table for REG09) | IINDPM back to 3 A and EN_EXTILIM back to 1: configuration lost; repeat C3-C12 | | |
| C21 | Unplug USB during charge | SYS stays on from the pack (battery supplement); IINDPM grant must be revoked by firmware on re-plug (contract table) | SYS dropout |
| C22 | ICO (optional): EN_ICO stays 0 in this policy; to characterise a weak source set REG0F bit 4 = 1 and FORCE_ICO, read REG19 ICO_ILIM | | |

### 4.3 TS / NTC window (DS BQ25792 7.x and REG17/REG18; divider R100 5.23 k REGN-TS, R101 30.1 k TS-GND, matching TI RT1/RT2 5.24 k/30.31 k, DS 9.3.9.5)
Break the pack NTC lead out of J5.2 and put each resistor from J5.2 to J5.3, with charging enabled at 0.5 A:

| Resistor | TS % of REGN (calculated) | Region (thresholds DS lines 996-1057, REG18 POR) | Expected charger action |
|---|---|---|---|
| 10 k (25 °C) | 58.9 % | normal (between VT3 44.8 % and VT2 68.4 %) | charge at ICHG |
| 22 k (≈ 5 °C) | 70.8 % | COOL (VT2 68.4 % to VT1 73.3 %) | ICHG x 20 % (REG17 JEITA_ISETC POR 01b) → about 0.1 A |
| 33 k (< 0 °C) | 75.1 % | COLD (above VT1 73.3 %) | charge suspended, REG1F TS_COLD_STAT = 1 |
| open | 85.2 % | COLD | suspended (a missing NTC must never allow charging) |
| 4.7 k (≈ 47 °C) | 43.7 % | WARM (VT3 44.8 % to VT5 34.2 %) | VREG - 400 mV (REG17 JEITA_VSET POR 3h), ICHG unchanged |
| 2.2 k (> 60 °C) | 28.2 % | HOT (below VT5 34.2 %) | suspended, TS_HOT_STAT = 1 |
| 103AT-2 at room, then warmed by hand / heat gun, then chilled | about 59 % at 25 °C, 73 % at 0 °C, 34 % at 60 °C | transitions at about 0, 10, 45, 60 °C | flags follow |

STOP if any COLD/HOT case still charges. Record REG3F TS_ADC for each row (expected within ±1 % of the table, est.).

---

## 5. Stage D: audio

Power from the real pack (USB optional). Firmware or SWD pokes needed for every enable. Order follows the bench order (HO lines 37-47, items 4-9).

### 5.1 Logic and audio rails
| Step | Do | Measure | Expected | STOP if |
|---|---|---|---|---|
| D1 | PA1 5V_LOGIC_EN high | TP7 5V_LOGIC | 4.824 V nominal (0.5 V x (1 + 78.7/9.1); FB ±1 %, DS TPS63802 line 318); HO DC bound 4.60-5.06 V (HO line 322 section) | > 5.10 V (PCM2902C 5.25 V max with margin) or < 4.6 V |
| D2 | | TP6 3V3_AUDIO (U22 TPS7A2033, EN tied to IN, comes up with 5V_LOGIC) | 3.25-3.35 V (±1.5 %, DS TPS7A20) | > 3.45 V |
| D3 | | ripple on TP7 and TP6, 20 MHz BW, spring ground | TP7 < 50 mVpp (est.; MODE tied to SYS_RAW = forced PWM, HO line 315); TP6 < 10 mVpp (est.) | TP7 > 150 mVpp |
| D4 | PC7 CODEC_PWR_EN high | TP8 5V_CODEC | ≈ TP7 minus < 50 mV (TPS22917 on); slew with CT open is fast (inrush into C170/C175/C225, est.) | TP7 dips > 300 mV at switch-on |
| D5 | PA8 BT_PWR_EN high (BT_FORCE_PWM low = PFM) | TP9 3V8_BT | 3.819 V nominal (604 k/91 k); 3.74-3.90 V (est.) | **> 4.2 V** (BM83 BAT_IN max, abs 4.3 V) |
| D6 | all three on, idle | pack current | TBD (record; feeds the standby budget, plan.md line 54) | |

### 5.2 PCM1862 and the 24.576 MHz crystal (U24 at 0x4A, AUD bus)
Y200 is YXC X322524576MOB4SI, CL 12 pF, ESR 50 Ω max, with C226/C227 15 pF C0G (HO line 18; `reports/sync-y200-c275.md` lines 37-57). The PCM1862 oscillator gm is not published: start-up is a bring-up risk (that report, line 57).

| Step | Do | Expected | STOP / action |
|---|---|---|---|
| D7 | 3V3_AUDIO on (D2); scan TP17/TP18 | 0x4A ACKs; 0x4C/0x4D also ACK once U6/U7 are powered and PDN is high (D16) | no 0x4A: U24 supply/MS-AD strap |
| D8 | write page 0 (reg 0x00 = 0x00); 0x20 = 0x91 (SCK_XI_SEL = 10 XTAL, MST_MODE = 1, CLKDET_EN = 1; DS Table 54); 0x26 = 0x07 (SCK/8 → BCK 3.072 MHz); 0x27 = 0x3F (BCK/64 → LRCK 48 kHz); 0x0B = 0x44 (I2S 24-bit, POR); 0x06 = 0x41 and 0x07 = 0x41 (ADC1 L/R = VIN1 = USB audio; 0x42 = VIN2 = BT, 0x44 = VIN3 = AUX, DS Table 32 and plan.md line 96). The master-mode divider settings are my reading of DS Tables 58-60: **verify against DS Table 7** | TP12 I2S_BCK 3.072 MHz, TP14 I2S_LRCK 48.000 kHz, TP13 I2S_SDATA toggling with audio; reg 0x72 STATE = 0x0F (Run); reg 0x75 CLK_ERR_STAT = 0x00 | no BCK/LRCK within 100 ms |
| D9 | LRCK frequency with the scope counter | 48.000 kHz ± 0.005 % (±50 ppm: about ±15-20 ppm load mismatch + 10 ppm tolerance + 20 ppm temperature, sync report line 53) | outside ±100 ppm: trim C226/C227 |
| D10 | start-up robustness: 20 power cycles of 3V3_AUDIO (D1 off/on), also with the board cold (freezer spray on Y200) | clocks every time | any failure: try 12 pF or 10 pF caps; do not probe XO with a 10x probe while judging start-up (the probe loads it); never drive XI with 3.3 V |

### 5.3 PVDD boost U25 TPS61088 (R256 DNP = MODE floating = PFM; grounded = forced PWM, fable MINORS citing TI SLVSCM8D)
Values (HO line 494): VOUT = 1.204 x (1 + 499/56) = 11.93 V in PWM, about 12.0 V in PFM (1.212 V ref), OVP min 12.7 V; fsw 494-504 kHz (R252 301 k); ILIM 150 k = 7.93 A typ / 6.63 A min; soft-start 47 nF = 11.3 ms. The TPS61088 datasheet PDF is missing (HO line 27): SW-node abs max and the MODE pin internal bias are **TBD**.

| Step | Do | Measure | Expected | STOP if |
|---|---|---|---|---|
| D11 | PA7 AMP_BOOST_EN high, no load (AMP_PDN low) | TP10 PVDD_AMP; scope on Net-(U25-SW) at L200 pin 2 (short ground spring) | ramp about 11 ms to 11.9-12.0 V; SW node in PFM bursts at no load (est.) | **> 12.5 V**, or PVDD oscillating > 300 mVpp |
| D12 | e-load 1.0 A on PVDD (clip at C275 terminals) | TP10, pack current, SW node | 11.8-12.0 V; pack current ≈ 12 W / 0.9 / 3.7 V ≈ 3.6 A (est.); SW 494-504 kHz | droop > 0.5 V; U25/L200 > 80 °C after 5 min |
| D13 | load step 0.2 → 1.0 A (e-load dynamic mode, 100 Hz) | PVDD transient | settles < 200 µs, no ringing beyond 2 cycles (est.; compensation is calculated only, HO line 494) | sustained oscillation |
| D14 | 1.5 A, then 2.0 A for **≤ 2 s** | TP10, pack current | at 3.7 V in, 2 A needs about 7.2 A in, above the 6.63-7.93 A switch limit, so PVDD sags or the converter limits: **expected by design** (HO line 494: about 1.2-1.5 A at low pack voltage). Keep battery current ≤ 6 A RMS / 8 A for 1 s (HO line 15, BAT_INT limit) | pack PCM trip, Q103 > 80 °C, J5/SW101 heating |
| D15 | PFM audibility: speakers connected (or dummy loads + listening near L200), idle, amplifier in Play with zero input | listen; scope PVDD ripple | inaudible: keep R256 DNP. Audible ticking/hiss tied to PFM bursts: fit R256 = 0R (0402, RC0402FR-070RL) for forced PWM; record the idle pack-current increase (TBD) | |

### 5.4 TAS5825M U6 (BTL front L/R, 0x4C) and U7 (PBTL woofer, 0x4D)
Order (DS TAS5825M 9.5.3.1, fable e6): 3V3_AUDIO up, PVDD up (D11), PCM1862 clocks running (D8), then AMP_PDN high, wait ≥ 5 ms, then I2C. Loads: 8 Ω 25 W on J9 (U6 OUT_A, FRONT_L) and J10 (U6 OUT_B, FRONT_R), 4 Ω 50 W on J11 (U7 PBTL); actual driver impedances TBD.

| Step | Write (both devices unless stated) | Expected | STOP if |
|---|---|---|---|
| D16 | PA6 AMP_PDN high (R257/R258 1 k, R259 pull-down), wait 5 ms | 0x4C and 0x4D ACK; TP20 AMP_FAULT_N ≈ 3.3 V (R262 10 k pull-up, GPIO0 is an input at POR) | no ACK |
| D17 | 0x00 = 0x00 (page 0), 0x7F = 0x00 (book 0) | - | |
| D18 | **U7 only**: 0x02 DEVICE_CTRL_1 = 0x04 (DAMP_PBTL = 1, BD mode, 384 kHz). Must be written before U7 leaves Hi-Z (HO line 493; PBTL pairing per DS Fig. 159). U6: leave 0x02 = 0x00 (BTL) | read back 0x04 / 0x00 | |
| D19 | 0x60 GPIO_CTRL = 0x01 (GPIO0 output), 0x61 GPIO0_SEL = 0x0B (FAULTZ). Never select a CMOS GPIO0 mode on both devices: they are wired-OR | TP20 stays high | TP20 low with no fault |
| D20 | 0x4C DIG_VOL = 0x60 (-24 dB; 0x30 = 0 dB, 0.5 dB/step, DS 9.6.1.17) | - | |
| D21 | 0x03 DEVICE_CTRL2 = 0x02 (Hi-Z, DSP enabled), wait 5 ms, then 0x03 = 0x03 (Play) | 0x68 POWER_STATE reports Play (value encoding TBD); 0x70/0x71/0x72 fault registers 0x00 | any fault bit; TP20 low |
| D22 | idle, no input | each output terminal ≈ PVDD/2 DC (est.), differential DC < 50 mV (est.); idle pack current TBD | differential DC > 0.2 V |
| D23 | 1 kHz sine via USB audio or AUX, raise DIG_VOL step by step to 1 W per channel (8 Ω: 2.83 Vrms differential) | clean sine, no clipping; THD visibly low (scope FFT) | fault, clipping below 1 W, thermal warning (0x73) |
| D24 | 2 x 10 W (8.9 Vrms into 8 Ω) for 10 min (fable M8) | U6/U7 case temperature recorded; TAS RthJA 24-30 K/W (fable M8) | case > 100 °C (est.) or thermal foldback |
| D25 | U7 PBTL into 4 Ω, 10 W, then up to the PVDD/boost limit | power limited by PVDD 11.9 V and the boost current limit (D14) | fault |
| D26 | fault test without shorting outputs: switch the boost off (PA7 low) while in Play so PVDD falls to about SYS_RAW | TP20 goes low (PVDD UV fault), fault registers 0x71/0x72 report it; boost on again and write 0x78 FAULT_CLEAR (bit 7, est.) to recover | fault not reported |
| D27 | shutdown order: 0x03 = 0x02 (Hi-Z), wait ≥ 6 ms, AMP_PDN low, then AMP_BOOST_EN low (DS 9.5.3.2) | no pop above the noise floor (est.) | |

### 5.5 USB audio (U2 PCM2902C)
| Step | Do | Expected | STOP if |
|---|---|---|---|
| D28 | 5V_LOGIC and 5V_CODEC on (D1, D4); connect J1 to a PC (the PC is also the power source; PD contract as in A2) | U2 VBUS (after R170 2.2 Ω) ≈ TP8; D+ pulled up to VDDI 3.3 V through R173 1.5 k: the host enumerates "USB Audio" VID 0x08BB, PID 0x29C0 or 0x29C2 (DS PCM2902C lines 1245-1246); bMaxPower 100 mA (HO line 288) | no enumeration: R171/R172, Y170 12 MHz (U2 XTI/XTO, C177/C178 33 pF), D+ pull-up |
| D29 | total VBUS current during enumeration (PD tester) | record. The whole-board 100 mA host budget is an open item (contract "Remaining hardware gates"): exceeding 100 mA before configuration is a compliance finding, not a hardware STOP | |
| D30 | play 1 kHz at -20 dBFS | U2 VOUTL/VOUTR → USB_AUDIO_L/R (C186/C187) about 0.1 Vrms (est.); I2S data at TP13 with ADC on VIN1 | |

### 5.6 Bluetooth BM83 (U1)
Sequence (`reports/bluetooth-notes.md` lines 18-22): BT_PWR_EN high, wait for 3V8_BT; keep BT_MFB/BT_UART_TX low, BT_RST_N released (hi-Z); pulse MFB high about 400 ms; release RST_N about 20 ms; send UART Power-On, expect ACK (retry up to 5 x in 1 s). Off: Power-Off command, ACK, all MCU lines low, RST_N low **before** SYS_PWR falls to 2.7 V, then BT_PWR_EN low; 3V8_BT ramp-down > 640 µs.

| Step | Measure | Expected | STOP if |
|---|---|---|---|
| D31 | U1 pin 25 VDD_IO, pin 24 SYS_PWR (module outputs, do not drive) | VDD_IO 3.0-3.6 V (DS BM83); SYS_PWR follows BAT_IN (value TBD) | VDD_IO present while 3V8_BT is off (back-powering through the 10 k/1 k series resistors) |
| D32 | UART at TP21 (MCU TX) / TP22 (module TX) | Host-mode baud **TBD** (Config Tool setting, plan.md line 91); ACK frames on TP22 | no response after MFB pulse: check MFB polarity (unverified) |
| D33 | pairing with a phone, play audio | BT_AUDIO_L/R (C194/C195) single-ended about 0.5-1 Vrms at full volume (TBD, DAC level item 8 of the HO bench order) | |
| D34 | power-off ramp: scope 3V8_BT and BT_RST_N | RST_N low before SYS_PWR < 2.7 V; 3V8_BT decays over > 640 µs (R154 100 k bleeder plus module load) | RST_N still high when SYS_PWR crosses 2.7 V |
| D35 | RF: RSSI at 1 m with the amplifiers in Play at 2 x 5 W | no dropouts (est.) | link drops when the class-D runs |

### 5.7 Headphone / aux (U8/U9 TS5A23157 mux, U10 TPA6132A2, J2/J3 PJ-307)
Note: the analogue mux is TS5A23157 (U8/U9). The TS5A3167 parts (U13/U16/U17) are the gauge I2C/ALRT isolation switches, not part of this path.

| Step | Do | Expected | STOP if |
|---|---|---|---|
| D36 | 3V3_AUDIO on, no plugs | HP_DET (PB1) low (switched tip closes to the TPA6132 OUTL at 0 V DC; R239 100 k pull-up); AUX_DET (PB2) about 30 mV (R241 1 M vs R243 10 k) (allocation doc) | HP_DET high with no plug |
| D37 | insert a plug in J2, then in J3 | HP_DET → 3.3 V; AUX_DET → about 3.0 V | no change: PJ-307 switched-contact mapping (pin 4 switched tip) not re-measured (HO line 486) |
| D38 | HP_SEL_A/B both low (pull-down default) → USB to headphones; A high → BT; B high → AUX (HO line 484) | source selected as expected with 1 kHz on each source | wrong source |
| D39 | HP_EN high with a 32 Ω load, G0/G1 low (default gain per allocation doc: -6 dB) | output present; scope the turn-on and turn-off pop at OUTL | pop > 10 mVpk (est. target) → firmware ordering (mute first) |
| D40 | speaker mute on HP insert is firmware only (HO line 484) | firmware puts TAS in Hi-Z when HP_DET goes high | |

---

## 6. Thermal and EMI spot checks
| Step | Condition | Measure | Expected / limit |
|---|---|---|---|
| T1 | charge 3 A, 15 min (C17) | U4, L1, PGND via area, Q103 | record; STOP limits as C17 |
| T2 | PD 20 V / 3 A sink (charging plus load) | U11 case | TBD (RPPHV 24 mΩ typ at 125 °C conditions, DS line 765: about 0.2 W at 3 A, est.) |
| T3 | PVDD 1 A for 10 min (D12) | U25, L200 | < 80 °C (est.) |
| T4 | 2 x 10 W, 10 min (D24) | U6, U7, L201-L206 | record (fable M8) |
| T5 | standby, pack only, MCU in Stop (firmware TBD) | pack current | TBD; preliminary arithmetic about 40-80 µA (B1.15) |
| T6 | ship mode | pack current | about 18-45 µA (est., B2.3) |
| E1 | near-field probe over L1/U4 SW1/SW2, L200/U25 SW, U14/U15, L201-L206 | spectrum 150 kHz-30 MHz | no unexpected peaks besides 750 kHz (BQ PWM, PROG), 494-504 kHz (U25), 384 kHz (TAS FSW_SEL 000), TPS63802 fsw (TBD) and their harmonics |
| E2 | AM radio 0.5-1.6 MHz near the enclosure in Play | audible interference | record |
| E3 | BM83 link quality in Play (D35) | | record |

---

## 7. Pass/fail summary (fill in per board)
| Stage | Item | Pass criterion | Board 1 | Board 2 |
|---|---|---|---|---|
| 1 | Rail resistances, diode paths, polarity, CC-VBUS isolation | 1.1-1.27 | | |
| A | 5 V legacy: rails, HIZ held, SYS 0 V, 3V_AO 3.0 V | A1.1-A1.14 | | |
| A | Blank MCU safe, SWD attach, I2C IDs (0x20, 0x6B, no 0x36) | A1.15-A1.22 | | |
| A | PD 5 / 9 / 20 V contracts, no EPR/PPS, VBUS waveform < 24 V | A2.1-A2.8 | | |
| B | Battery-only power-up, gauge readback, isolation threshold | B1.1-B1.15 | | |
| B | Ship mode entry/exit, QON timing, system reset, SW101 | B2.1-B2.10 | | |
| B | Real pack | B3 | | |
| C | Register sequence and readback | C1-C14 | | |
| C | 0.5 / 1 / 3 A charge, thermals | C15-C18 | | |
| C | Watchdog / REG_RST behaviour documented | C19-C20 | | |
| C | TS window (7 cases) | 4.3 | | |
| D | 5V_LOGIC, 3V3_AUDIO, 5V_CODEC, 3V8_BT | D1-D6 | | |
| D | PCM1862 clocks, crystal start-up x 20 | D7-D10 | | |
| D | PVDD no load / 1 A / step / limit; R256 decision | D11-D15 | | |
| D | TAS5825M BTL + PBTL into dummy loads, thermal | D16-D27 | | |
| D | USB enumeration | D28-D30 | | |
| D | BM83 sequence, pairing, power-off ramp | D31-D35 | | |
| D | Headphone / aux detection, mux, pop | D36-D40 | | |
| 6 | Thermal / EMI | T1-T6, E1-E3 | | |

---

## 8. Open values (TBD) and firmware needs
- Firmware or SWD pokes are required from A1.17 onward for every enable; I2C writes for B2, C1-C22, D8, D16-D27, D32. Minimum toolset: ST-Link + OpenOCD and a 3.0-3.3 V I2C adapter on TP15/TP16 (CTRL), TP17/TP18 (AUD) or J4 (PD), with the MCU halted. A small bring-up firmware (SWD/RTT shell) is the cleaner option.
- STM32G071 empty-flash bootloader pin states (AN2606, not in ai-files); DEV_ID 0x460 and the RCC/GPIO addresses (RM0444, not in ai-files).
- TPS25730D: PDO selection rule inside the 5-20 V window; RDO current-field mapping for "operating 0 A / maximum 3 A"; LDO_3V3 tolerance.
- BQ25792: VINDPM auto value at 9/20 V; SYS level above VBAT in battery-supplement mode; DEV_REV value.
- MAX17048 register values from the PDF (local text is unreadable).
- TPS61088 datasheet (missing): SW-node abs max, MODE pin bias, shutdown/load-disconnect behaviour (the body-diode path SYS_RAW → PVDD is assumed).
- TAS5825M POWER_STATE encoding (0x68), FAULT_CLEAR bit, AGAIN choice for PVDD 11.9 V.
- PCM1862 master-mode divider set (verify DS Table 7) and crystal start-up margin.
- BM83 Host-mode baud, MFB polarity, SYS_PWR level, DAC output level.
- Driver impedances, TPA6132A2 pop target, standby budget with real firmware, plugged-in VREG policy, final charge-current cap (3 A vs 4 A, see below).

## 9. Inconsistencies found (handover / brief / schematic)
1. **PD voltage range.** The schematic configures TPS25730D for 5-20 V (ADCIN2 tied to LDO_3V3 = code 7) and 3 A maximum (ADCIN4 10 k/210 k = code 1), matching plan.md line 10 (5/9/15/20 V) and the HO bench order item 1 ("5/9/15/20 V"). The bring-up brief's "request 5/9 V; 15/20 V must not happen", and the stale HO "USB PD section" (lines 106-116: "program and read back a two-PDO 5 V/9 V profile", STUSB4500) do not apply to the active hardware. The HO "Selected major parts" table (lines 84-104) still lists STUSB4500/BQ25895/STL9P3LLH6.
2. **J4 power.** HO line 112 (STUSB4500-era USB PD section) says J4 uses external programmer logic power; in the schematic J4 pin 1 is LDO_3V3, an output of U11 (5 mA budget). J4 also reaches only the PD bus; the charger and gauge are on the CTRL bus (TP15/TP16).
3. **Charge-current cap.** HO line 23 recommends a 3 A firmware cap (U4 PGND pin 27 vias); HO R6n section (line 576) says "a firmware default of about 4 A is recommended until bench temperature checks". This sheet uses ≤ 3 A.
4. **TP13/TP14.** HO "Rotary encoder and test points" (line 562) lists TP12-14 as BCK/LRCK/SDATA; after the R6e swap (HO line 570) and in the netlist TP13 = I2S_SDATA, TP14 = I2S_LRCK.
5. **Mux part.** The brief names TS5A3167 for the headphone/aux mux; the mux is U8/U9 TS5A23157. TS5A3167 (U13/U16/U17) isolates the gauge bus.
6. **PPHV bulk.** HO "Corrected sink-bulk interpretation" (line 399) assumes about 50 µF nominal (2 x 10 µF VBUS + 3 x 10 µF PMID). The schematic adds C315 47 µF 25 V on VBUS_PD (added with C311-C316, not recorded in HO), giving about 97 µF nominal against the TPS25730 CPPHV maximum of 100 µF (DS line 647). DC bias at 20 V lowers the effective value a lot, so it is probably fine, but check the attach inrush (A2.6) and record the decision.
7. **Standby budget.** The HO/plan figure of 35-37 µA (plan.md lines 163, 189) is BQ25895-era; the BQ25792 numbers are IQ_BAT_ON 17/24 µA and ship 11/16 µA (at VBAT 8 V), and the gauge and U21 stay on BAT_PACK in ship mode.
8. **Naming trap (not an error).** PD_SINK_EN reads **low** when the sink path is enabled (TPS25730 SINK_EN: 0 = enabled).
