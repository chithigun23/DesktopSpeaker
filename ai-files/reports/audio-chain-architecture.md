# Audio chain architecture (plan sections 7-9)

2026-10-06. Architecture decisions made autonomously under the user's authorization. Paper design only: no capture, simulation or bench test is claimed. Datasheets: TAS5825M SLASEH7F, PCM186x SLAS831D (downloaded to /tmp during this review; copy to `ai-files/datasheets/PCM1862.pdf` at capture), TS5A23157 SCDS165F, TPA6132A2 SLOS597B, TPS61088 ZHCSDP8A (LCSC copy of the Chinese edition; TI blocked the English PDF). "VERIFY" marks items that are not datasheet-backed or not confirmed.

## 0. Decisions in one screen
- **Speaker path:** all three analogue sources feed the **PCM1862's own 4:1 input mux** (USB = VIN1, BT = VIN2, AUX = VIN3). Its I2S output goes to both TAS5825M. Source selection for the speakers is an I2C register write. The TS5A23157s are not in the speaker path.
- **Headphone path:** an **analogue pass-through**. U8 and U9 (TS5A23157) form a 3:1 stereo mux, followed by U10 (TPA6132A2) and J2. In headphone mode the boost, both amplifiers and the ADC are off, so headphone mode costs only tens of mW.
- **Clock master:** the PCM1862 runs as I2S master from its own 24.576 MHz crystal (512 fs, PLL off, 48 kHz, BCK 64 fs). The TAS5825M has no clock output and needs no MCLK; it locks its PLL to SCLK.
- **Amplifiers:** U6 drives front L and front R (stereo BTL). U7 drives the woofer in mono PBTL, fed with (L+R)/2 by its own input mixer. Crossover, EQ and limiter run in each TAS5825M DSP; the MCU loads coefficients over I2C at every power-up.
- **Amplifier supply:** U25 TPS61088 boosts SYS_RAW to PVDD_AMP = 11.9 V. Its current limit is set so the pack never sees more than about 8-9 A, below the BQ25792 battery ratings (6 A RMS, 10 A for 1 s, OCP 9.3 A). This **replaces the 15-20 A burst assumption**.
- **New audio rail:** 3V3_AUDIO from U22 (TPS7A2033, low-noise LDO) fed from 5V_LOGIC. U23 is a load switch that powers the PCM2902C codec (5V_CODEC) only in USB mode.
- **MCU:** change to **STM32G071RBT6 (LQFP64, LCSC C432213)**. The audio chain plus the remaining section 4/5 signals need about 46 GPIO; the G031K8 has 29. The audio parts get their own hardware I2C bus (I2C2) with pull-ups to 3V3_AUDIO.

## 1. Source selection
**Speakers (PCM1862 mux, SLAS831D Table 2).** Each input is wired port → 2.2 uF X7R (series) → 100 R → VINx pin, with 10 nF C0G from the pin to AGND (Fig. 61 anti-alias filter; the 100 R also limits ESD-diode current to well under the 5 mA maximum). The input impedance is 20 kΩ per pin, so the high-pass corner is about 3.6 Hz. Inputs tolerate -1.7 to 5.0 V absolute, so ground-centred sources are fine. ADC1L/ADC1R select register (0x06/0x07) codes:
0x01 = USB, 0x02 = BT, 0x04 = AUX, 0x00 = mute
The ADC input selection resets to USB (0x01). Source changes are click-free because no switch carries a DC step: every input has its own pre-charged capacitor. Firmware sequence:
Soft-mute the TAS5825M volume (ramp at least 6 ms at 48 kHz, SLASEH7F 9.5.3.2) → Write the new input select and PGA gain → Wait 20 ms → Ramp back up.
PGA gains (SLAS831D: -12 to +12 dB in 1 dB steps; full scale 2.1 Vrms single-ended):
- USB, 0.7 Vrms: +6 dB, giving -3.5 dBFS; BT, 0.495-0.742 Vrms: +6 dB. Set BM83 analogue gain so its maximum is 0.742 Vrms; AUX, up to 2 Vrms: 0 dB.
**Headphones (TS5A23157 x2, SCDS165F).** Each switch has its IN1 and IN2 tied together, so one MCU line moves both channels.
- U8: NC1/NC2 = USB L/R, NO1/NO2 = BT L/R, COM1/COM2 → U9 NC1/NC2.
- U9: NO1/NO2 = AUX L/R, COM1/COM2 = HP_L/HP_R.

| HP_SEL_B | HP_SEL_A | Headphone source |
|---|---|---|
| 0 | 0 | USB (reset default; 100 k pull-downs on both lines) |
| 0 | 1 | Bluetooth |
| 1 | x | AUX |

- **Signal range:** the analogue range is 0 to V+ (abs max -0.5 V), so ground-centred sources need re-biasing. Each mux input gets a 1 uF series capacitor and then 100 k to VMID_HP = 1.65 V. VMID_HP comes from a 47 k/47 k divider on 3V3_AUDIO with 4.7 uF (time constant 0.11 s). Usable swing is ±1.65 V, about 1.16 Vrms: enough for BT and USB (≤0.74 Vrms) and typical phones on AUX (≤1 Vrms). Hotter AUX sources clip only on the headphone path; the speaker path still accepts 2.1 Vrms.
- **Series protection:** a 1 k resistor in series at every NC/NO pin keeps ESD-diode current far below the 50 mA rating when a source overdrives or when V+ is off.
- **Supply:** V+ = 3V3_AUDIO. VIH is 0.7 V+, which is 3.36 V at 4.8 V and would fail with the MCU's 3.0 V highs; at 3.3 V supply it is 2.31 V, which works. That is why 5V_LOGIC was rejected for V+.
- **Other figures:** the IN pins tolerate 6.5 V independently of V+, so they are safe while unpowered. Ron is about 10 Ω, THD 0.015% at 3 V into 600 Ω (the load here is ≥13 kΩ, so much better). Switching is break-before-make, so two sources are never shorted together. Supply current is 1 uA.
- **Anti-click (TPA6132A2 7.3.2):** take HP_EN low, change HP_SEL, wait 1 ms, then take HP_EN high (5 ms start-up). Always enable the TPA6132A2 after its source has settled and disable it first.
- **Back-power with rails off:** every path is capacitor-coupled and resistor-limited (1 uF + 1 k on the mux, 2.2 uF + 100 R on the ADC). An external AUX source playing into an unpowered board injects only small AC current. The MCU must hold HP_EN, HP_G0 and HP_G1 low while 3V3_AUDIO is off.

## 2. ADC, clocks, digital format, I2C
**U24 PCM1862DBTR** (TSSOP-30, 103 dB SNR and -87 dB THD+N single-ended, 80 mW active, 0.64 mW software standby). LCSC code and stock are VERIFY.
- **Supplies:** AVDD, DVDD and IOVDD are all 3V3_AUDIO (each specified 3.0-3.6 V). AVDD goes through a ferrite bead (FB200) and has 0.1 uF + 10 uF. DVDD has 0.1 uF + 10 uF; IOVDD 0.1 uF + 1 uF. The LDO pin (internal output) gets 0.1 uF + 10 uF, VREF 1 uF. MicBias is no-connect.
- **No reset pin and no brownout detector (11.3):** 3V3_AUDIO must ramp monotonically. Firmware re-initialises the PCM1862 after every rail enable.
- **Clock:** Y200 24.576 MHz 3225 crystal on XI/XO with 2 × 20 pF C0G (as on the TI EVM; trim to the crystal's CL). Crystals of 15-35 MHz are allowed; XI is a 1.8 V-domain pin, so nothing external may drive it. At 512 fs = 48 kHz the PLL can stay off, which is the lowest-power clock tree (SLAS831D clock-tree tables, 512 fs row: PLL off, SCK direct). SCKI (pin 15) is unused: tie it to DGND (VERIFY).
- **Format:** master mode, I2S, 24-bit data in 32-bit slots, BCK 3.072 MHz (64 fs), LRCK 48 kHz. DOUT, BCK and LRCK each leave through a 33 R series resistor and fan out to both TAS5825M SDIN, SCLK and LRCLK. TAS5825M accepts I2S at 32 or 64 fs (Table 1).
- **Clock halt:** the TAS5825M sends its outputs Hi-Z when the clock halts and recovers by itself without reloading the DSP (9.3.2/9.3.4). PCM1862 standby therefore safely parks the amplifiers.
- **Control pins:** MD0 (26) to GND selects I2C. MS/AD (25) to GND sets address 0x4A. GPIO1/INTA (21) goes to ADC_INT (optional MCU input). GPIO0, GPIO2 and GPIO3 are no-connect. VINL4/VINR4 (27/28) are spare and no-connect.
- **Audio I2C plan (AUD_SCL/AUD_SDA):**

| Address | Device |
|---|---|
| 0x4A | PCM1862 (MS/AD low) |
| 0x4C | U6 TAS5825M (ADR 0 Ω to GND) |
| 0x4D | U7 TAS5825M (ADR 1 kΩ to GND) |

  The addresses do not clash with BQ25792 (0x6B), MAX17048 (0x36) or TPS25730D (0x20).
- **Why a separate audio bus:** TAS5825M digital inputs, SDA/SCL included, are rated -0.5 V to DVDD+0.5 V (SLASEH7F 7.1), and PCM1862 inputs to IOVDD+0.3 V. Unpowered audio parts on the always-on CTRL bus would clamp it. So the audio bus has its own 2.2 k pull-ups to 3V3_AUDIO. They switch off with the rail, and the MCU's FT pins tolerate 3.3 V at VDD = 3.0 V.

## 3. Amplifiers, DSP, boost, power path
**Channel allocation.**
- **U6 (stereo BTL):** channel A = front L, channel B = front R. Assumes 4 Ω full-range drivers of 2-2.5 in, about 10 W each.
- **U7 (PBTL mono):** woofer, 4 Ω, 3-4 in, about 20 W, downward-firing. TAS5825M PBTL allows loads down to 1.6 Ω. A 2 Ω woofer is deliberately avoided: it would double the current.
- **PBTL wiring:** pre-filter, as in TI's PBTL curves (two outputs merged before the inductors, so two inductors instead of four). Set DAMP_PBTL in register 0x02 bit 2. PBTL takes the left I2S frame, so the U7 DSP mixer must form (L+R)/2.
- **VERIFY before capture:** the exact pin pairing (planned OUT_A+‖OUT_B+ and OUT_A-‖OUT_B-) must be checked against SLASEH7F Fig. 156 or the EVM, because the PDF text is font-garbled.
- **PBTL limits:** cycle-by-cycle current limiting is not available in PBTL (9.5.3.3.1). Overcurrent shutdown still works.
- **Firmware rule:** U7 must have DAMP_PBTL = 1 written before it ever leaves Hi-Z.
- **Woofer drive:** U7 is stereo-fed and mono-mixed, so the woofer needs no SDOUT link (10.2.6: "the subwoofer amplifier can accept the same digital input").
**Gain and level.** Analogue gain register 0x54 AGAIN = -8.5 dB (0b10001), so 0 dBFS gives about 11.1 V peak, just under the 11.9 V PVDD (Table 2: 29.5 V peak at 0 dB, 0.5 dB steps). Clip-onset power is about (11.1/√2)²/4 ≈ 15 W per 4 Ω channel. Speaker volume is the TAS digital volume (0x4C), written to both devices together. BT AVRCP volume comes in over UART and is mapped to TAS volume while BM83 gain stays fixed (best SNR). For USB, device buttons send HID vol+/- so the host slider stays in step.
**DSP and loading.** Each device has 2 × 15 biquads, 3-band DRC, AGL, bass enhancement and thermal foldback. Tune both in TI PPC3 with the TAS5825M app. Starting crossover:
- U6: Linkwitz-Riley 4th-order high-pass at about 150 Hz, plus driver EQ and a high-shelf to compensate the 22 uH filter; U7: Linkwitz-Riley 4th-order low-pass at about 150 Hz, plus woofer EQ; Final points depend on the drivers and enclosure.
AGL thresholds set the battery-power ceiling (§3 boost). Export the PPC3 register dumps as C arrays in MCU flash; the G071's 128 KB is ample (dump size VERIFY). There is no EEPROM: host loading over I2C is TI's recommended method (9.4.1), and the SPI-EEPROM option is not used.
**Start-up (9.5.3.1):**
Rails up (order does not matter) → AMP_PDN high, wait ≥5 ms → Start the PCM1862 clocks → Write Hi-Z and DSP enable → Wait ≥5 ms → Load coefficients and settings: FSW 384 kHz, hybrid modulation (DAMP_MOD = 10), PBTL on U7 → Set Play.
**Shutdown (9.5.3.2):** Hi-Z or PDN low, wait ≥6 ms, then take the boost down. **Auto-idle:** if the TAS level meter or the signal falls below threshold for about 10 min, enter Deep Sleep (PVDD 12 uA, DVDD 0.82 mA), then drop the whole chain.
**TAS5825M support parts, per device (Table 66, 10.1):**
- PVDD: 2 × 22 uF 35 V 0805 plus 2 × 0.1 uF 50 V 0402, one pair at pins 3/4 and one at 21/22; DVDD (6): 4.7 uF + 0.1 uF; VR_DIG (7), GVDD (18), AVDD (19): 1 uF each; BST: 0.47 uF X7R 25 V 0603 from each BST pin to its OUT pin (Table 66 uses 0.47 uF; the 10.1.2 text says 0.22 uF); ADR (8): 0 Ω (U6) or 1.00 kΩ 1% (U7) to GND; GPIO0 (9) is set as FAULTZ open-drain and joins the shared AMP_FAULT_N line (10 k pull-up to 3V3_AUDIO); GPIO1 and GPIO2: no-connect. Firmware sets them as outputs (VERIFY the default pin state); PDN (17): shared AMP_PDN through 1 k, 100 k pull-down; PGND (25, 26, 31, 32) and EP to GND.
**Output filter.** 22 uH + 0.68 uF 50 V X7R 0805 to PGND on every output terminal: 4 inductors on U6, 2 on U7.
- 22 uH is chosen over the EVM's 10 uH for idle current: datasheet idle is 20.5 mA versus 29.5 mA at 13.5 V (7.5). TI's minimum for PVDD ≤12 V at 384 kHz is 4.7 uH. Inductor Isat must be at least 4 A. The Ipeak equations give about 2.8 A at 11.1 V peak into 4 Ω, about 1.2 A in clipping, and 7.5 A for OCP. VERIFY a 22 uH, 4 A shielded part with DCR ≤ 50 mΩ, about 12 × 12 mm (for example the Bourns SRP1265A or Sumida CDRH127 class); the 6 inductors are a mechanical cost. Expected front roll-off is about -3 dB near 18 kHz; correct it in the DSP.
**Speaker connectors:** J9 FRONT_L, J10 FRONT_R, J11 WOOFER, JST B2P-VH (2-pin, 3.96 mm, 10 A; the family of the existing JST_VH datasheet). They need a new symbol and footprint; LCSC code VERIFY.
**PVDD boost U25 TPS61088RHLR** (LCSC C87357, stock 3473 at 2026-10-06; 2.7-12 V in, 4.5-12.6 V out, 10 A switch). Pins: 1 VCC, 2 EN, 3 FSW, 4-7 SW, 8 BOOT, 9 VIN, 10 SS, 11/12 NC→GND, 13 MODE, 14-16 VOUT, 17 FB, 18 COMP, 19 ILIM, 20 AGND, 21 PGND/pad.

| Part | Value | Basis |
|---|---|---|
| Output divider | 499 k / 56.0 k, 1% | VREF 1.204 V → 11.93 V; OVP 12.7-13.6 V. TI recommends ≥20 µA divider current; this gives 21 µA. |
| RFREQ (FSW to SW) | 301 k | 500 kHz at 3.6 V in, 12 V out (spec row) |
| RILIM | 150 k | PFM-mode equation 1.19e6/R: 7.9 A typical switch peak, 6.6 A minimum (-1.3 A). With 2.2 µH ripple of about 2.3 A, input current is at most about 8 A. |
| L200 | 2.2 µH, Isat ≥ 12 A, DCR ≤ 8 mΩ | Coilcraft XAL7070-222 or Bourns SRP1265A-2R2 class (VERIFY) |
| SS | 47 nF | about 11 ms soft-start (1.204·C/5 µA); limits inrush to about 0.15 A |
| VCC | 2.2 µF | |
| BOOT to SW | 0.1 µF | |
| VIN | 0.1 µF + 4 × 22 µF 10 V | reuses selected C907991 |
| VOUT | 1 µF + 4 × 22 µF 25 V X7R 1210 + 100 µF 25 V polymer | polymer is for bass bursts (VERIFY) |
| COMP | R5 82 k + C5 6.8 nF to AGND, C8 47 pF | equations 18-20 with Rsense 0.08 Ω, effective Co about 170 µF, crossover 5 kHz (below a 48 kHz right-half-plane zero at 2 A); bench or WEBENCH check required |
| MODE | floating = PFM | DNP 0 Ω to GND as an FPWM option; the ILIM equation then subtracts 1.6 A |

- **Enable:** EN = AMP_BOOST_EN with a 100 k pull-down (EN high ≥1.2 V). Quiescent current is 110 µA from VOUT; shutdown is 1 µA.
- **No load disconnect:** the datasheet describes no output-disconnect function. When disabled, PVDD_AMP ≈ SYS_RAW minus the high-side body-diode drop. TAS5825M stays below its 4.5 V minimum and is held off by PDN. Standby drain on this path is about 25 µA: divider about 6.7 µA at 3.7 V, two TAS in shutdown at 7.8 µA each (7.5), boost 1 µA.
- **Output capability:** at 3.6 V in, 90% efficiency, about 1.9 A out (about 23 W); at 3.0 V worst-case minimum limit, about 1.2 A (15 W). Firmware sets the TAS AGL ceilings so the sum stays within this budget: fronts about 5 W continuous each, woofer about 10 W, short peaks allowed.
- **Power path:** U25 is fed from SYS_RAW, so the BQ25792 NVDC path gives automatic priority. The adapter supplies SYS first, charging is cut back to hold IINDPM, and the battery supplements above the adapter limit. A 5 V/2 A source gives at most 10 W in, minus about 1 W board load. Firmware programs IINDPM per source (existing policy) and, **with no battery present**, caps AGL at about 5 W total. With a battery, peaks come from the pack; worst case is about 8.5 A including other loads (below IBAT_OCP 9.3 A, and the SW101 10 A rating).
- **Not done:** taking PVDD directly from 9-20 V PD was deliberately rejected (more power, but a separate path and a new protection design).

## 4. Headphone output and aux input
**Volume.** The TPA6132A2 has only 4 gain steps (-6, 0, 3, 6 dB on G0/G1). The simplest acceptable scheme is fixed gain with volume set at the source:
- BT: BM83 DAC gain via UART volume commands and AVRCP, driven by the device buttons; USB: HID vol+/- (PCM2902C HID1/HID2, and HID0 for mute) from the MCU, which moves the host volume and the codec's digital volume; AUX: the playing device's own volume, plus G0/G1 steps under MCU control. Default -6 dB (pull-downs) as acoustic-shock protection.
A DAC or digital-pot volume was rejected: it would force the ADC, LDO and DAC to run in headphone mode (about 150 mW versus about 20 mW). Supported loads are 16-300 Ω; output is 25 mW into 16 Ω or 1.1 Vrms into 100 Ω at 1% THD.
**U10 TPA6132A2 pins:**
- INL- (1) and INR- (4) take HP_L/HP_R through 1 µF X7R. Input impedance is 13.2-26.4 kΩ, so the high-pass corner is ≤12 Hz. Input common mode must be -0.5 to 1.5 V, which is why the input caps are needed after the 1.65 V-biased mux; INL+ (2) and INR+ (3) to GND (single-ended, per datasheet); G0 (6) and G1 (7) to HP_G0/HP_G1 with 100 k pull-downs. EN (13) to HP_EN with a 100 k pull-down. VIH is 1.3 V; VDD (14) = 3V3_AUDIO with 1 µF + 0.1 µF; HPVDD (12) 2.2 µF to GND; must not connect to VDD; CPP (11) to CPN (9): 1 µF. HPVSS (8): 2.2 µF; PGND (10) and EP to GND; SGND (15) routes as a separate trace to J2 sleeve (pin 1); OUTL (16) to J2 tip (5), OUTR (5) to J2 ring (2).
**J2 HEAD_OUT (PJ-307).**
- Pin 1 sleeve to GND/SGND. Pin 4 (switched tip) forms HP_DET: 100 k pull-up to 3V3_AUDIO, 1 k series to the MCU. With no plug, the tip spring shorts pin 4 to OUTL, which TPA6132A2 holds near 0 V when disabled (shutdown output impedance 20 Ω per 6.5; VERIFY), so HP_DET reads low. With a plug, pin 4 opens and HP_DET reads high. With the rail off it reads low (no plug), a safe default. Pin 3: no-connect.
**J3 AUX_IN (PJ-307).**
- Tip (5) = AUX_L, ring (2) = AUX_R. Each has a 10 k bleed to GND and feeds both the ADC sheet and the mux. Pin 4 forms AUX_DET: 1 MΩ to 3V_AO with 100 nF to GND, 10 k series to an EXTI pin. No plug reads about 30 mV; plug inserted reads high. This allows auto-select or wake on insertion. Costs about 3 µA while unplugged. Pin 3: no-connect.
**ESD:** D200 (J2 tip/ring) and D201 (J3 tip/ring) are bidirectional 5 V two-line TVS, for example Nexperia PESD5V0S2BT (SOT-23; LCSC VERIFY). The unidirectional TPD2E2U06 is unsuitable for ground-centred signals.
**Insertion behaviour (firmware):**
On HP_DET rising (50 ms debounce): TAS soft-mute, then Hi-Z, then AMP_PDN low, then AMP_BOOST_EN low, then PCM1862 standby. Set HP_SEL to the active source and enable the TPA6132A2 after 5 ms. On removal, reverse the order, disabling the TPA6132A2 first.

## 5. MCU pin budget and decision
Existing captured signals (18, from mcu-pin-allocation.md) plus SWD (2) use 20 of the G031K8's 29 GPIO, leaving 9 free.

| Group | Signals | Count |
|---|---|---|
| Audio (sections 7-9) | AUD_SCL, AUD_SDA, AMP_PDN, AMP_FAULT_N, AMP_BOOST_EN, CODEC_PWR_EN, ADC_INT, HP_SEL_A, HP_SEL_B, HP_EN, HP_G0, HP_G1, HP_DET, AUX_DET | 14 |
| Other open sections | BTN_ADC (resistor ladder), CHG_QON_SENSE, LED_R/G/B (PWM), USB_SRC_DET (ADC), USB_DATA_SEL + USB_DATA_OE_N (TS3USB221A), CODEC_SSPND, USB_HID_MUTE/VOLUP/VOLDN | 12 |

Total is about 46 against 29, so the G031 is short by about 17. **Decision: STM32G071RBT6.** LQFP64 10 × 10 mm, 60 I/O, 128 KB flash, 36 KB RAM. LCSC C432213: 1597 in stock, $2.46 at 1 unit (search snapshot; VERIFY at order). It leaves about 14 spare I/O.
- STM32G0B1 (3 × I2C) was rejected: LCSC stock is 0 for both C2847904 (G0B1CBT6, $7.03) and C2829307 (G0B1RET6).
- The G071 has only I2C1 and I2C2: I2C1 (PB6/PB7) = CTRL, unchanged. **I2C2 = audio** (PB10/PB11 or PB13/PB14, AF6; VERIFY against DS12232). It carries the bulk DSP coefficient loading. The **TPS25730D PD bus becomes software (bit-banged) I2C** on PA11/PA12. It is rare, low-rate status traffic and is powered only with VBUS.
- Rejected alternative: sharing CTRL through a PCA9306 isolator. It would put the charger safety bus at risk from a hung audio device.
- Requirements: FT pins for the audio I2C and every input from 3.3 V domains; ADC-capable pins for BTN_ADC and USB_SRC_DET; EXTI for AMP_FAULT_N, HP_DET, AUX_DET, CHG_INT, PD_PLUG_EVENT, BT_TX_IND and GAUGE_ALRT_N. Keep GAUGE_ALRT_N on a WKUP-capable pin.
- **Capture task (coordinator, separate):** new STM32G071RBT6 symbol, LQFP-64 footprint and STEP (stock KiCad LQFP-64_10x10mm_P0.5mm), MCU.kicad_sym swap, full re-pinning of the 18 existing nets. Check the LQFP64 VDD/VDDA, VSS/VSSA and VREF+ pins and their decoupling in DS12232. Update mcu-pin-allocation.md.
- **Every new MCU output** gets a 100 k pull-down, so OFF is the reset state. **Firmware rule:** no audio-domain line is driven high before 3V3_AUDIO is up.

## 6. Rail map and audio power budget (estimates, battery-referred)

| Rail | Source | Loads | Peak |
|---|---|---|---|
| PVDD_AMP 11.9 V | U25 from SYS_RAW (AMP_BOOST_EN) | U6, U7 | ≤ about 1.9 A out; about 8 A in |
| 3V3_AUDIO | U22 TPS7A2033 (300 mA) from 5V_LOGIC; EN tied to IN, so it is on whenever 5V_LOGIC is | PCM1862 25 mA, 2 × TAS DVDD ≤25.5 mA, TPA6132A2 ≤3 mA + headphone load, mux, VMID 35 µA, pull-ups | speakers about 85 mA; headphones about 40 mA (dissipates 0.13 W) |
| 5V_CODEC | U23 TPS22917 from 5V_LOGIC (CODEC_PWR_EN) | PCM2902C 67 mA maximum | USB mode only |
| 5V_LOGIC | U14 (existing) | U22 + U23 ≤ about 155 mA (0.75 W) | within TPS63802 capability |

Estimated battery-referred consumption:
- **Off or standby** (5V_LOGIC off, boost off): about 25 µA on the PVDD path plus 3 µA AUX_DET. Ship mode or SW101 removes even this.
- **Headphones:** about 20-25 mW (TPA 2.2 mA, PCM1862 standby 0.2 mA, LDO and U14 overhead), plus the source module.
- **Speakers, playing silence:** PVDD about 2 × 0.24 W ÷ 0.85 ≈ 0.57 W; DVDD and ADC about 0.3-0.4 W via LDO and U14. About **0.9-1.0 W in total**.
- **Typical listening** (about 1 W average audio): about 2.2 W, roughly 16 h on a 36 Wh (10 Ah) pack, excluding BT, MCU and codec.
- **Peak:** limited by the boost to about 20-23 W out, under 9 A from the pack.
- **Rejected:** a 1.8 V TAS DVDD would save about 0.1 W but needs the PCM1862 LDO pin driven from 1.8 V and a second rail.

## 7. Risks (priority order)
1. **Pack path current.** Boost current-limit tolerance (switch peak up to about 9.2 A) plus about 0.5 A of other loads approaches BQ25792 IBAT_OCP (9.3 A) and its 6 A RMS rating. AGL limits and firmware battery-voltage-dependent volume caps are mandatory. Q103, SW101 and the SYS copper must be rated for 9 A pulses.
2. **U7 PBTL.** Pin pairing is not confirmed (garbled figure). A BTL default with shorted pre-filter outputs relies on OCSD protection if firmware errs. Mitigate by writing DAMP_PBTL first and by an EVM check. Fallback: post-filter PBTL (4 inductors) or woofer in BTL on channel A.
3. **Boost stability and acoustics.** Compensation values, polymer ESR and inductor are calculated only. PFM bursts may be audible from the inductor or caps, or couple into the audio; the FPWM DNP option costs idle power.
4. **PPC3 tuning access.** The TAS5825M app requires a TI request, and an EVM or prototype is needed for measured tuning. Coefficient-dump size and boot time are unverified.
5. **MCU swap.** New library parts and re-pinning of a captured sheet; G071 pin and AF details must be checked against DS12232. LCSC stock is a snapshot only.
6. **Supply noise.** 5V_LOGIC buck-boost ripple versus PCM1862 analogue performance (LDO PSRR at MHz is limited). FB200 and layout matter. TPA6132A2 has 100 dB PSRR at 217 Hz.
7. **Detection.** HP_DET relies on TPA6132A2 OUTL being low-impedance in shutdown (20 Ω per 6.5); confirm at bring-up. The 1 MΩ AUX_DET node is noise-sensitive; it has a 100 nF filter.
8. **Headphone limits.** AUX headroom on the headphone path is 1.16 Vrms, and there is no device volume for AUX beyond the 4 TPA gain steps.
9. **Thermal and EMI.** The 22 µH 12 mm inductors, speaker-lead EMI and TAS thermal performance (RθJA 24-30 °C/W) need a 4-layer PCB with thermal vias. No layout exists.
10. **Unverified parts.** LCSC codes and stock are unverified for: PCM1862DBTR, TPS7A2033PDBVR, TPS22917DBVR (also its pinout), the 24.576 MHz crystal, the inductors, the polymer cap, PESD5V0S2BT, B2P-VH and the 22 µF 25 V 1210 parts.

## 8. CAPTURE BRIEFS
Coordinator (root) tasks:
- Create 3 child sheets; Move U6, U7 (Amplifiers) and U8, U9, U10, J2, J3 (Headphone_Aux) from the root, keeping reference, value and UUID; Fan USB_AUDIO_L/R and BT_AUDIO_L/R out to both Source_Select_ADC and Headphone_Aux; Connect AUX_L/R from Headphone_Aux to Source_Select_ADC; Re-route the USB_Audio sheet port "5V_LOGIC" from 5V_CODEC; MCU swap per §5; Every new library item is one file per part in the flat folders.
Reference ranges below are free of all existing references (checked across every sheet). Each block follows the readable-schematic skill, with downward ground symbols.
**1. Source_Select_ADC** (references U22, U23, U24, Y200, FB200, C200-C229, R200-R219)
- **Ports, left (in):** 5V_LOGIC, USB_AUDIO_L, USB_AUDIO_R, BT_AUDIO_L, BT_AUDIO_R, AUX_L, AUX_R, CODEC_PWR_EN; **Ports, bidirectional:** AUD_SCL, AUD_SDA; **Ports, right (out):** 3V3_AUDIO, 5V_CODEC, I2S_BCK, I2S_LRCK, I2S_SDATA, ADC_INT.
- **U22 TPS7A2033PDBVR** (VERIFY DBV pins against the U12 TPS7A02 map: IN1, GND2, EN3, NC4, OUT5). IN = 5V_LOGIC with 1 µF; EN tied to IN; OUT = 3V3_AUDIO with 1 µF + 10 µF.
- **U23 TPS22917DBVR** (pinout VERIFY). IN = 5V_LOGIC; ON = CODEC_PWR_EN with 100 k pull-down; OUT = 5V_CODEC with 1 µF; quick output discharge enabled.
- **U24 PCM1862DBTR:** pin connections as in §2. Inputs VIN1 = USB, VIN2 = BT, VIN3 = AUX, each with the 2.2 µF / 100 R / 10 nF C0G network. Y200 24.576 MHz with 2 × 20 pF C0G. 33 R series resistors on DOUT, BCK and LRCK.
- **Audio bus pull-ups:** 2.2 k to 3V3_AUDIO on AUD_SCL/SDA, placed here only. ADC_INT gets a 100 k pull-down.
**2. Headphone_Aux** (references U8, U9, U10, J2, J3, D200, D201, C230-C254, R220-R239)
- **Ports, left (in):** USB_AUDIO_L/R, BT_AUDIO_L/R, 3V3_AUDIO, 3V_AO, HP_SEL_A, HP_SEL_B, HP_EN, HP_G0, HP_G1; **Ports, right (out):** AUX_L, AUX_R, HP_DET, AUX_DET.
- **Mux:** U8/U9 per the §1 truth table. V+ = 3V3_AUDIO with 0.1 µF each. Six input networks of 1 µF series, 100 k to VMID_HP and 1 k series at the pin. VMID_HP is a 47 k/47 k divider with 4.7 µF. 100 k pull-downs on HP_SEL_A/B.
- **U10 and jacks:** U10 per §4 with 1 µF input caps. J2 and J3 contact maps per §4, HP_DET and AUX_DET networks, D200/D201 on tip and ring, 10 k AUX bleed resistors.
**3. Amplifiers** (references U6, U7, U25, L200-L206, J9-J11, C260-C299, R250-R264)
- **Ports, left (in):** SYS_RAW, 3V3_AUDIO, I2S_BCK, I2S_LRCK, I2S_SDATA, AMP_PDN, AMP_BOOST_EN; **Ports, bidirectional:** AUD_SCL, AUD_SDA; **Ports, right (out):** AMP_FAULT_N.
- **U25 TPS61088RHLR:** per the §3 table; L200 2.2 µH. Local net PVDD_AMP, with a PWR_FLAG if ERC needs one.
- **U6 and U7 support parts:** per §3. U6 ADR 0 Ω, U7 ADR 1.00 k. Shared AMP_PDN (1 k series, 100 k pull-down). GPIO0 wired-OR into AMP_FAULT_N (10 k to 3V3_AUDIO).
- **Output filters:** L201-L204 22 µH (U6 A+, A-, B+, B-), L205-L206 22 µH (U7 PBTL merged + and -, pairing VERIFY), 0.68 µF 50 V on each filtered output.
- **Speaker connectors:** J9 FRONT_L (U6 channel A), J10 FRONT_R (U6 channel B), J11 WOOFER (U7), JST B2P-VH. Pin 1 = + , pin 2 = -.
- **Ground:** PGND and AGND tie at the pad. Draw the power stage as a compact left-to-right block: boost → PVDD bus → U6/U7 → filters → connectors.