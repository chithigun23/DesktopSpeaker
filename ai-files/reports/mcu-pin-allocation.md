# MCU pin allocation (STM32G071RBT6, LQFP64)

2026-10-06. U3 changed from STM32G031K8T6 (LQFP32) to **STM32G071RBT6 (LQFP64 10 x 10 mm, LCSC C432213)** as decided in `audio-chain-architecture.md` section 5. Datasheet DS12232 Rev 2 (`datasheets/STM32G071x8_xB.pdf`, Table 12 pin table, Tables 13/14 alternate functions). Reference **U3** and its root instance are unchanged. No firmware or hardware test is claimed. Symbol `kicad-library/schematic/STM32G071RBT6.kicad_sym` (pin names and numbers from Table 12), footprint `STM32G071RBT6.kicad_mod` (stock KiCad LQFP-64_10x10mm_P0.5mm, 64 pads, 0.5 mm pitch, pad span 11.35 mm, 1.55 x 0.3 mm pads, pin 1 top-left), STEP `3d/STM32G071RBT6.step` (stock KiCad model, 12 x 12 mm over leads, 1.5 mm high). The G031 library files stay in the library but are no longer used by any sheet.

## Supply, reset, boot, debug

- VDD 1.7-3.6 V. LQFP64 has **one** VDD/VDDA pin (8) and one VSS/VSSA pin (9), plus VBAT (6) and VREF+ (7). All are fed from 3V_AO (U12 TPS7A0230, 3.0 V nominal, USB-priority or pack input); the supply sags with the pack, so ADC readings need VREFINT calibration. Single pins: nothing to stack natively (the power pins are electrically distinct pads).
- Decoupling (DS12232 fig. 13): VDD/VDDA 100 nF (C160) + 4.7 uF (C161); VREF+ 100 nF (C163) + 1 uF (C164) with VREFBUF off and VREF+ tied to VDDA (the datasheet allows VREF+ = VDDA when VDDA is 2.0 V or more; below that VREF+ must equal VDDA, which it does). VBAT tied directly to VDD (no backup cell, LSE and RTC unused). PC14/PC15 are used as GPIO (no crystal planned).
- NRST (12, PF2-NRST): internal pull-up, 100 nF (C162) to GND, wired to J6/J7. NRST_MODE option must stay "reset input".
- BOOT0 is PA14-BOOT0 (46) shared with SWCLK. nBOOT_SEL=1 ignores the pin. R160 100 k pull-down kept on the SWCLK line.
- SWD: PA13 SWDIO (45), PA14 SWCLK (46). J7 TC2030-IDC (1 3V_AO, 2 SWDIO, 3 NRST, 4 SWCLK, 5 GND, 6 SWO nc) and J6 4-pin header unchanged. PA13/PA14 must not be remapped. SWO (PB3) is not available because PB3 is BT_MFB.
- PA11/PA12 (pins 43/44) are named PA11[PA9] / PA12[PA10]: SYSCFG PA11_RMP/PA12_RMP must stay 0 (default).

## Allocation (captured: nets exist on the sheet)

| Signal | Dir (MCU) | Pin | Function / notes |
|---|---|---|---|
| CTRL_SDA | bidir | PB7 (61) | I2C1_SDA AF6, FT_fa. Pull-ups R120/R121 on Fuel_Gauge_Power (3V_AO). |
| CTRL_SCL | bidir | PB6 (60) | I2C1_SCL AF6, FT_fa. BQ25792 0x6B, MAX17048 0x36 (behind isolation switches). |
| PDCTRL_SDA | bidir | PA12 (44) | **Software (bit-banged) I2C**, open-drain output, FT_f. Pull-ups R14/R15 10 k to LDO_3V3 on the PD sheet. TPS25730D 0x20. |
| PDCTRL_SCL | bidir | PA11 (43) | Same; FT_f. Keep both pins analog/input no-pull until PD_PLUG_EVENT = 1 (the pull-ups exist only with VBUS). |
| CHG_ENABLE | out | PC6 (38) | R107 100 k pull-down, High = charge enabled. |
| CHG_SYS_ENABLE | out | PA10 (42) | R111 100 k pull-down: reset keeps ILIM_HIZ asserted. |
| CHG_INT | in | PC15 (5) | BQ INT, open-drain, R106 10 k to 3V_AO. EXTI. |
| GAUGE_ALRT_N | in | PA0 (17, WKUP1) | MAX17048 ALRT via U17, R122 47 k to 3V_AO. Standby wake. |
| PD_PLUG_EVENT | in | PC14 (4) | TPS25730D open-drain, R16 100 k to LDO_3V3. EXTI wake from Stop. |
| PD_SINK_EN | in | PB9 (63) | TPS25730D open-drain, R17 100 k to LDO_3V3. Status only. |
| CHG_QON_SENSE | in | PC13 (3, WKUP2) | New. See QON section. |
| BT_PWR_EN | out | PA8 (36) | U15 EN, R152 100 k pull-down. |
| BT_FORCE_PWM | out | PA9 (37) | U15 MODE, R153 100 k pull-down. |
| 5V_LOGIC_EN | out | PB5 (59) | U14 EN, R142 100 k pull-down. |
| BT_UART_TX | out | PA2 (19) | USART2_TX AF1 to BM83 via R182. Drive low before BT_PWR_EN goes low. |
| BT_UART_RX | in | PA3 (20) | USART2_RX AF1 from BM83 via R186. |
| BT_MFB | out | PB3 (57) | BM83 MFB via R183 (R184 100 k pull-down on the module side). |
| BT_RST_N | out | PB4 (58) | BM83 RST_N via R185; drive open-drain (low only). |
| BT_TX_IND | in | PB8 (62) | BM83 P0_0 via R187; EXTI wake; internal pull-down in firmware. |
| AUD_SDA | bidir | PB11 (31) | Captured 2026-10-06: I2C2_SDA AF6, FT_fa, to Source_Select_ADC (PCM1862 0x4A; TAS5825M later). Pull-up R210 2.2 k to 3V3_AUDIO there.
| AUD_SCL | bidir | PB10 (30) | I2C2_SCL AF6; pull-up R209 2.2 k to 3V3_AUDIO. PB13/PB14 stay LEDs.
| CODEC_PWR_EN | out | PC7 (39) | Captured: U23 TPS22917 ON, R212 100 k pull-down on Source_Select_ADC (high = 5V_CODEC on).
| ADC_INT | in | PC5 (26) | Captured: PCM1862 GPIO1/INTA, R211 100 k pull-down (optional input; configure the GPIO as INTA in firmware).
| HP_SEL_A, HP_SEL_B | out | PC0 (13), PC1 (14) | Captured 2026-10-06: TS5A23157 U8/U9 IN1+IN2 (via Headphone_Aux, 100 k pull-downs R234/R235: USB default).
| HP_EN | out | PC2 (15) | Captured: TPA6132A2 EN, R236 100 k pull-down on Headphone_Aux.
| HP_G0, HP_G1 | out | PC3 (16), PA4 (21) | Captured: TPA6132A2 gain, R237/R238 100 k pull-downs (default -6 dB). PA4 is TT_a: fine as an output.
| HP_DET | in | PB1 (28) | Captured: J2 switched tip, 100 k (R239) pull-up to 3V3_AUDIO, 1 k (R240) series. EXTI. Reads low with no plug or with the audio rail off.
| AUX_DET | in | PB2 (29) | Captured: J3 switched tip, 1 M (R241) to 3V_AO, 100 nF (C246), 10 k (R242) series. About 30 mV unplugged, high when a plug is inserted.
| AMP_PDN | out | PA6 (23) | Captured 2026-10-06: shared U6/U7 PDN via 1 k each (R257/R258), 100 k pull-down R259 on Amplifiers. Drive high only after 3V3_AUDIO is up; wait 5 ms before clocks.
| ENC_A, ENC_B, ENC_SW | in | PC8 (48), PC9 (49), PC10 (64) | Captured 2026-10-06: SW102 Alps EC11E encoder + push switch on MCU sheet. ENC_A/ENC_B/ENC_SW, EXTI or timer, internal pull-up (enable GPIO pull-ups; encoder common, switch return and shield to GND). 10 nF debounce caps C308/C309/C310 to GND; switch is active low. |
| AMP_BOOST_EN | out | PA7 (24) | Captured: U25 TPS61088 EN, R255 100 k pull-down.
| AMP_FAULT_N | in | PC4 (25) | Captured: U6/U7 GPIO0 (open drain FAULTZ, wired-OR), R262 10 k pull-up to 3V3_AUDIO on Amplifiers. EXTI. Firmware must set GPIO0 to FAULTZ; default pin state to be verified.

All captured pins are 5 V tolerant FT variants. Pin moves versus the G031 are numbering only; every non-MCU pin group of each net is unchanged (netlist compared).

## Reserved for open sections (labelled no-connect on the MCU sheet; the audio, headphone and amplifier signals are in the captured table)

| Signal | Dir | Pin | Notes |
|---|---|---|---|
| USB_SRC_DET | in | PB0 (27) | ADC_IN8 (analog). |
| BTN_ADC | in | PA1 (18) | ADC_IN1, resistor-ladder buttons. |
| LED_R, LED_G, LED_B | out | PB13 (33), PB14 (34), PB15 (35) | TIM1_CH1N/CH2N/CH3N AF2 PWM (set MOE). |
| USB_DATA_SEL, USB_DATA_OE_N | out | PD0 (50), PD1 (51) | TS3USB221A; OE_N needs an external pull-up (disabled by default), SEL a pull-down. |
| CODEC_SSPND | out | PD2 (52) | PCM2902C suspend status/control. |
| USB_HID_MUTE, USB_HID_VOLUP, USB_HID_VOLDN | out | PD3 (53), PD4 (54), PD5 (55) | PCM2902C HID0/HID1/HID2 drive, pull-downs. |

Spare GPIO (10, unlabelled no-connect): PA5 (22), PA15 (47), PB12 (32), PC11 (1), PC12 (2), PD6 (56), PD8 (40), PD9 (41), PF0 (10), PF1 (11). Budget: 60 I/O = 38 captured + NRST + 11 reserved + 10 spare.

## Constraints checked

- **SWD/BOOT0**: PA13/PA14 reserved for SWD, BOOT0 on PA14 as before (nBOOT_SEL=1 ignores it).
- **ADC**: BTN_ADC PA1 (ADC_IN1) and USB_SRC_DET PB0 (ADC_IN8) are ADC channels; PA0-PA7, PB0-PB2, PB10-PB12, PC4/PC5 are FT_a/TT_a analog-capable if more are needed. ADC reference is the sagging VDDA.
- **FT tolerance**: every input from a 3.3 V domain (LDO_3V3 PD lines, 3V3_AUDIO lines, QON about 3.6-3.8 V) lands on an FT pin (5.5 V limit; absolute maximum VDD + 4.0 V). The only TT pin used is PA4, an output. The MCU only pulls low on I2C lines.
- **Alternate functions** (Tables 13/14): I2C1 SCL/SDA PB6/PB7 AF6; I2C2 SCL/SDA PB10/PB11 AF6; USART2 TX/RX PA2/PA3 AF1; TIM1_CH1N/2N/3N on PB13/14/15 AF2; WKUP1 PA0, WKUP2 PC13 (Table 12 additional functions).
- **Wake**: GAUGE_ALRT_N (PA0, WKUP1), CHG_QON_SENSE (PC13, WKUP2); other EXTI inputs wake from Stop only.
- **Safe reset states**: every GPIO is a floating input in reset (SWD pins keep SWD). Captured outputs have external 100 k pull-downs (R107, R111, R142, R152, R153): OFF in reset. Every reserved output must get a pull-down (OE_N: pull-up) when captured, as in the architecture doc; no pin needs an MCU-defined state at reset. Firmware: no audio-domain line driven high before 3V3_AUDIO is up.
- **PD bus is software I2C**: the TPS25730D is rare, low-rate status traffic; I2C2 hardware is reserved for the audio bus (DSP coefficient loading).

## Voltage domains and I2C notes (carried over)

- PDCTRL pull-ups go to LDO_3V3 (present only with VBUS). Pulling to 3V_AO would back-feed the TPS25730D with its LDO off. VIL = 0.3 VDD (0.9 V) versus TPS25730D VOL: check at bring-up.
- No VBUS means LDO_3V3 is off, both PD lines float and the TPS25730D is dead: keep the software bus idle until PD_PLUG_EVENT = 1. 3V_AO is up whenever VBUS is, so a pull-up with VDD = 0 occurs only briefly at attach.
- The CTRL bus is isolated below the 3.08 V supervisor threshold: expect NACKs from the MAX17048 when 3V_AO sags.
- 2N7002 gates (Q100/Q102) at 3.0 V are marginal; the loads are 100 k pull-ups so acceptable. At VDD below about 2.5 V enables may fail to assert: safe state is OFF.

## CHG_QON_SENSE (new)

BQ25792 QON (pin 12, DI): internal pull-up through about 200 k to a typical 3.6-3.8 V with VBUS and VBAT above 5 V (3.2 V typical otherwise); VIH 1.3 V, VIL 0.4 V; low for tSM_EXIT (15 ms or 1 s) wakes from ship mode, 10 s low resets system power. SW100 pulls it to GND. The sense taps the QON net with **R113 100 k in series** into an MCU input, which is high impedance (nA leakage, internal pull-up disabled): the BQ pin sees an additional 100 k only on an input of at most 100 nA, so the pull-up voltage and logic thresholds are not disturbed. No divider or diode is needed: the pin is a pure input at 3.6-3.8 V, inside the FT limit of PC13 (FT, 5.5 V). Polarity: high when idle, low while the button is pressed (active-low). The signal exists on both the Battery_Charger hierarchy (output port) and the MCU sheet (input, PC13/WKUP2) and is wired in the root through matching labels. Idle level in ship mode is not characterised here: verify at bring-up.

## Not captured (no net exists)

- USB-source detection: PB0 reserved, no net yet.
- Remaining PD outputs (CAP_MIS, PLUG_FLIP, DBG_ACC) are no-connect on the PD sheet.
