# Firmware system specification: states, sequencing, mute timing, audio architecture, controls

2026-11-01. Paper specification for the firmware author. No firmware exists and nothing here was measured on hardware. Read-only on `DesktopSpeaker-kicad/`, `plan.md` and `HANDOVER.md`. Closes the open plan items in sections 4 (defined UI, sequencing/fault, QON), 7 (source-change mute timing, stereo/woofer/DSP architecture), 8 (headphone mute/insertion timing) and 9 (mute/fault/shutdown sequence, driver limits).

Labels used throughout:
- **DS** = taken from a local datasheet this session (cited). **FIG** = read from a rendered datasheet figure. **CALC** = my arithmetic from datasheet/T&S numbers. **PROPOSAL** = design choice that needs user approval. **BENCH** = value to confirm on the first board. **MISSING** = a signal the spec needs that does not exist in the netlist.
- Nets and MCU pins come from `mcu-pin-allocation.md`, the `*.kicad_sch` hierarchical labels (grep of `MCU.kicad_sch`: every signal below except ENC_A/B/SW, which are local labels, is a hierarchical label there) and the bench plan. `kicad-cli` was not on the PATH in this session, so no fresh netlist export was made; connectivity facts were taken from schematic text and the existing reports.

Source files: `AGENTS.md`, `plan.md` sections 4, 7-10, `HANDOVER.md`, `reports/mcu-pin-allocation.md`, `replacement-power-control-contract.md`, `usb-audio-notes.md`, `audio-chain-architecture.md`, `bluetooth-notes.md`, `bench-bringup-plan.md`, `cad/mechanical-parts.md`, `reports/sourcing-2026-10-12.md`, datasheets TAS5825M, PCM1862, TPA6132A2, TS5A23157, BM83, STM32G071, BQ25792, TPS25730 (+TRM), TPS63802, TPS7A20.

---

## 0. Findings that change the plan (read first)

1. **ND65-4 is the front driver, not the woofer.** `cad/mechanical-parts.md`: fronts = 2 x Dayton ND65-4 (2.5 in full-range, Fs 89.5 Hz, Xmax 3.5 mm, 15 W RMS, Re 3.5 ohm); woofer = Tang Band W3-2052SC (3 in, Fs 59 Hz, Qts 0.49, Xmax 5 mm, 15 W RMS, Re 4.3 ohm, 0.525 L sealed, no maker datasheet). The ND65-4 PDF in `ai-files/cad/parts/` therefore protects the fronts only; the woofer limits come from the Parts Express table.
2. **PCM1862 input-select codes.** `audio-chain-architecture.md` lists 0x01/0x02/0x04; the datasheet (Table 32) says bit 6 of registers 0x06/0x07 is reserved "always write 1". Correct codes: **0x41 = VIN1 (USB), 0x42 = VIN2 (BT), 0x44 = VIN3 (AUX), 0x40 = no selection (mute)**. The bench plan (D8) already uses 0x41/0x42/0x44. Never write a multi-bit code (it analogue-mixes inputs: that is the hardware source-conflict path).
3. **U7 woofer mono sum depends on a TAS5825M DSP feature I could not verify.** The datasheet says PBTL takes only the **left I2S frame** (9.4.2.2) and SAP_CTRL3 (0x35) only routes L, R or zero to a channel: there is no L+R option there. The PCM1862 datasheet says L+R mono mixes "can only be done in the digital mixer, post ADC" and that feeds both amps. So (L+R)/2 for U7 must come from the TAS5825M DSP process flow (PPC3 input mixer). The local datasheet text never mentions a mixer; verify in the PPC3 flow before freezing the design (risk R1, section 5.2).
4. **BM83 power-off timing in `bluetooth-notes.md` is shorter than Figure 6-9.** Rendered FIG 6-9: after the power-off ACK wait about 2 s, then drive RST_N low (all MCU/BM83 lines low), then at least 1 s before BAT_IN (3V8_BT) drops. Power-on: RST_N is low through the BAT_IN ramp, MFB goes high, RST_N is released 400 ms after MFB rises, Power-On ACK comes about 20 ms later. Section 3.4 uses the figure.
5. **No indicator of any kind exists** (see section 1.2): no LED, no buzzer, no display, BQ25792 STAT (pin 1) is a no-connect, BM83 LED1/LED2 are no-connects, the MCU LED_G/B pins are reserved text only (LED_R lost PB13 to PDCTRL_SDA on 2026-11-02; proposed PA2). The user has no feedback channel except BT audio through the phone. This is the main UI gap.
6. PA1 is **5V_LOGIC_EN** since the r6e swap (not the button ladder). The ladder net BTN_ADC (PA3, ADC_IN3) is reserved text only: **there is no button ladder in the netlist**.

---

## 1. Signal inventory

### 1.1 Signals that exist (MCU U3 STM32G071RBT6, 3V_AO domain, all outputs have external pull-downs so reset = off)

| Net | Dir | Pin | Part / ref | Use in this spec |
|---|---|---|---|---|
| CHG_SYS_ENABLE | out | PA10 | R111 100k PD, Q101 -> BQ25792 ILIM_HIZ | High releases the input clamp (source conversion on) |
| CHG_ENABLE | out | PC6 | R107 100k PD -> BQ25792 CE | High = charge allowed |
| ~~CHG_INT~~ | - | PC15 is spare (net PC15_SPARE, R106 10k to 3V_AO) | - | **Removed 2026-11-02 (patch P1):** BQ25792 /INT (U4-21) is a no-connect. Poll the BQ25792 status and flag registers (REG1B-REG27) every 250 ms while a source is attached or a charge runs, every 2 s otherwise; FLAG registers are clear-on-read, so no event is lost (latency up to 250 ms, not a safety path) |
| CHG_QON_SENSE | in | PC13 (WKUP2) | R113 100k from BQ QON | SW100 state, active low |
| GAUGE_ALRT_N | in | PA0 (WKUP1) | U17, R122 47k | MAX17048 alert, active low |
| CTRL_SDA / CTRL_SCL | bidir | PB7 / PB6 (I2C1) | R120/R121 4.7k | BQ25792 0x6B, MAX17048 0x36 (behind U13/U16, only when BAT_PACK above about 3.1 V) |
| PDCTRL_SDA / SCL | bidir | **PB13** / PA11 (soft I2C; SDA moved from PA12 on 2026-11-02, patch P4) | R14/R15 10k to LDO_3V3 | TPS25730D 0x20, only valid when VBUS present |
| PD_PLUG_EVENT | in | PC14 (EXTI) | R16 100k to LDO_3V3 | 1 = Type-C connection present (DS TPS25730 pin 37) |
| PD_SINK_EN | in | PB9 | R17 | **Low = sink path enabled** (DS pin 19) |
| 5V_LOGIC_EN | out | PA1 | R142 -> U14 TPS63802 EN | 5V_LOGIC; also powers U22 -> 3V3_AUDIO |
| CODEC_PWR_EN | out | PC7 | R212 -> U23 TPS22917 ON | 5V_CODEC (PCM2902C, USB audio) |
| BT_PWR_EN | out | PA8 | R152 -> U15 TPS63802 EN | 3V8_BT (BM83 BAT_IN) |
| BT_FORCE_PWM | out | PD4 | R153 -> U15 MODE | Low = PFM, high = forced PWM |
| BT_UART_TX / RX | out / in | PD5 / PD6 (USART2 AF0) | R182 / R186 | BM83 host UART |
| BT_MFB | out | PB3 | R183, R184 100k PD | BM83 power key (polarity unverified, BENCH) |
| BT_RST_N | out (open-drain, low only) | PB4 | R185 1k | BM83 reset |
| BT_TX_IND | in | PB8 (EXTI) | R187 | BM83 P0_0, high = module will send UART |
| AUD_SDA / AUD_SCL | bidir | PB11 / PB10 (I2C2) | R210/R209 2.2k to **3V3_AUDIO** | PCM1862 0x4A, U6 0x4C, U7 0x4D |
| ADC_INT | in | PC5 (EXTI) | R211 100k PD | PCM1862 GPIO1/INTA (Energysense) |
| AMP_BOOST_EN | out | PA7 | R255 -> U25 TPS61088 EN | PVDD_AMP 11.9 V |
| AMP_PDN | out | PA6 | R257/R258 1k, R259 PD | U6 and U7 PDN (shared) |
| AMP_FAULT_N | in | PC4 (EXTI) | R262 10k to **3V3_AUDIO** | U6/U7 GPIO0 FAULTZ wired-OR |
| HP_SEL_A / HP_SEL_B | out | PC0 / PD1 | R234/R235 PD | TS5A23157 U8/U9: 00 USB, 01 BT, 1x AUX |
| HP_EN | out | PA15 | R236 PD | TPA6132A2 EN |
| HP_G0 / HP_G1 | out | PC3 / PA4 | R237/R238 PD | TPA6132A2 gain, 00 = -6 dB |
| HP_DET | in | PB1 (EXTI) | R239 100k to **3V3_AUDIO**, R240 1k | J2 switched tip; high = plug in |
| AUX_DET | in | PB2 (EXTI) | R241 1M to 3V_AO, C246 100n, R242 10k | J3 switched tip; about 30 mV unplugged, 3.0 V plugged |
| ENC_A / ENC_B / ENC_SW | in | PC8 / PC9 / PC10 | SW102 EC11E18244AU, C308-C310 10 nF | Encoder (internal pull-ups) and push (active low) |
| NRST, SWDIO, SWCLK | | | J6 (all three); J7 SWDIO/SWCLK only (J7 pin 3 NRST not connected since 2026-11-02, patch P5: connect-under-reset only over J6) | debug |

Rails and their controls: **3V_AO** always on (U12 from U20 TPS2116: USB_AUX_5V via U19 when VBUS present, else SYS_RAW). **5V_LOGIC** U14, EN = PA1. **3V3_AUDIO** U22 TPS7A2033 with EN tied to IN: it is on exactly when 5V_LOGIC is on; there is **no separate enable**. **5V_CODEC** U23, PC7. **3V8_BT** U15, PA8. **PVDD_AMP** U25, PA7 (no load disconnect: with the boost off PVDD_AMP follows SYS_RAW minus a diode drop, which is below the TAS5825M 4.5 V minimum and PDN holds the amps in shutdown). Pack path: SW101 (physical), Q103 (BQ25792 SDRV ship FET), BQ25792 U4.

### 1.2 Signals that the spec needs and that do NOT exist (MISSING)

| Needed | Why | Status in netlist | Workaround used here |
|---|---|---|---|
| Status indicator (LED / buzzer) | UI feedback: power, source, pairing, battery, fault | **None.** MCU PB14/PB15 are reserved text only (LED_G/B, TIM1_CH2N/3N; PB13 is PDCTRL_SDA since 2026-11-02, LED_R proposed on PA2 TIM2_CH3); BQ25792 STAT pin 1 NC; BM83 LED1/LED2 NC; no LED part in the BOM | Section 6.3: phone shows battery via BM83 (UNVERIFIED command), otherwise no feedback. Recommend adding an RGB LED (hardware change, user decision) |
| Button ladder (BTN_ADC, PA3) | extra buttons | Reserved text only | Use encoder push + SW100 only |
| USB host presence / enumeration (USB_SRC_DET PB0) | auto-select USB, decide to power codec | Reserved only | Heuristic from TPS25730 reg 0x34 (section 2.5) plus Energysense |
| PCM2902C SSPND (CODEC_SSPND PD2) | USB suspend/resume, idle detect | Reserved only | PCM1862 Energysense loss timeout |
| PCM2902C HID mute/vol (USB_HID_*, PC2/PA9/PB5) | sync host volume | Reserved only | None: the encoder cannot move the host volume slider (headphone+USB volume limited to TPA gain steps) |
| TS3USB221A D+/D- mux (USB_DATA_SEL/OE_N) | isolate data until source classified | **Not in the design**: J1 D+/D- go straight to PCM2902C (USB_Audio.kicad_sch note) | The D+ pull-up R173 comes from 5V_CODEC: CODEC_PWR_EN is the only attach control |
| Power-good for 5V_LOGIC, 3V3_AUDIO, 3V8_BT, PVDD_AMP | confirm rails before the next step | U14/U15 PG pins are no-connects; none for U22/U25 | Fixed delays plus I2C readbacks (PCM1862 ACK, TAS PVDD_ADC register 0x5E) |
| QON press-time input with timing | long-press gestures | Exists as CHG_QON_SENSE (PC13), polarity and ship-mode idle level not characterised (bench B2.4) | Use it with the caveats in section 6 |
| Amp mute pin (TAS GPIO1 MUTE) | hardware mute | TAS GPIO1/GPIO2 are no-connects; PDN is the only hard control | Soft mute over I2C only (arch doc: "mute is firmware only") |
| Battery presence / PG for charger | battery-absent handling | Via BQ25792 registers over I2C only | Read status registers |

Nothing else the spec uses is missing. In particular AMP_FAULT_N, GAUGE_ALRT_N, PD_PLUG_EVENT, PD_SINK_EN, HP_DET, AUX_DET, ADC_INT and the encoder lines all exist and are wired through the root hierarchy. CHG_INT was removed on 2026-11-02 (patch P1): the BQ25792 is polled.

---

## 2. Power states (plan section 4, "startup/shutdown sequencing, fault handling, external-power charge policy")

### 2.1 States

| State | Meaning | MCU |
|---|---|---|
| **S0 OFF/SHIP** | Battery-only deep off: BQ25792 ship mode (SDRV_CTRL) or SW101 open. 3V_AO is dead unless VBUS is present. | unpowered |
| **S1 STANDBY** | "Off" as the user sees it, and the only off state that exists while VBUS is present. Everything switched is off. | Stop mode |
| **S2 AWAKE-IDLE** | User-awake, no audio. Logic and BT up, amplifiers off. | Run / Sleep |
| **S3 PLAYING** | Audio output active, speaker (3a) or headphone (3b). | Run |
| **C CHARGING overlay** | Orthogonal flag valid in S1, S2, S3 whenever VBUS is valid and granted. Not a state of its own. | |
| **F FAULT** | Latched sub-states F-AMP, F-CHG, F-PD, F-BATT, F-THERM; they sit on top of S1/S2 and force amplifiers off. | |

With VBUS present, "off" is S1 (3V_AO is kept alive by U19/U20, so the MCU cannot be fully off and ship mode alone does not remove SYS; `replacement-power-control-contract.md`, "Electronic off on USB").

### 2.2 What is on in each state (1 = high/on)

| Control | S0 | S1 | S2 | S3a speaker | S3b headphone | Note |
|---|---|---|---|---|---|---|
| 3V_AO | off (dead) / on if VBUS | 1 | 1 | 1 | 1 | |
| 5V_LOGIC_EN PA1 (also 3V3_AUDIO) | 0 | 0 | 1 | 1 | 1 | |
| CODEC_PWR_EN PC7 (5V_CODEC) | 0 | 0 | 1 only if VBUS granted and USB candidate, else 0 | same as S2 | same as S2 | Keep on across source changes: the PCM2902C output coupling caps need seconds to settle (section 4.1) |
| BT_PWR_EN PA8 (3V8_BT), BT_FORCE_PWM PD4 | 0, 0 | 0, 0 | 1, 0 (PFM) | 1, 0 (PWM while A2DP streams if BENCH shows it helps) | same | BM83 stays on across source changes |
| AMP_BOOST_EN PA7 | 0 | 0 | 0 | 1 | 0 | |
| AMP_PDN PA6 | 0 | 0 | 0 | 1 | 0 | |
| U6 / U7 TAS5825M state | off | off | off | Play (U6 BTL, U7 PBTL) | off | |
| PCM1862 | off | off | Sleep with Energysense armed | Active, master, clocks running | Standby (0x70) | |
| HP_EN PA15 / HP_G0 PC3 / HP_G1 PA4 | 0 | 0 | 0 | 0 | 1 / gain | 0 whenever 3V3_AUDIO is off |
| HP_SEL_A PC0 / HP_SEL_B PD1 | 0 | 0 | active source | active source | active source | |
| CHG_SYS_ENABLE PA10 / CHG_ENABLE PC6 | 0 / 0 | grant-dependent | grant-dependent | grant-dependent | grant-dependent | Overlay C; contract steps in section 3.2 |
| MCU I2C2 (AUD) pins | n/a | analog (hi-Z) | active | active | active | Never leave I2C2 driven while 3V3_AUDIO is off |

Interrupt masks follow the rails: **AMP_FAULT_N (PC4) and HP_DET (PB1) are pulled to 3V3_AUDIO, so they read low whenever 5V_LOGIC is off.** EXTI for both must be masked outside S2/S3 and unmasked only after the rail is stable (HP_DET after 50 ms, AMP_FAULT_N after GPIO0 is configured and faults are cleared).

### 2.3 Transitions

| From -> to | Condition | Action (sequence reference) |
|---|---|---|
| reset -> INIT | any reset | All enables fall to their pull-downs in hardware. Firmware: read BQ25792 identity/status with CE and SYS gates low (contract steps 1-3), read CHG_QON_SENSE (PC13), PD_PLUG_EVENT. If PC13 is low at boot (button held), go to S2 (ship-mode wake by QON); otherwise S1 |
| S0 -> S1/S2 | QON low for at least 1 s (BQ25792 tSM_EXIT 1 s, DS 9.3.12.2; hardware, MCU not running), or VBUS plug (exits ship) | MCU cold boots: INIT |
| S1 -> S2 | Wake: SW100 press (PC13 falling) held 1.0 s, or SW102 push (PC10), or AUX_DET rising (PB2) (BT cannot wake the system: BM83 is off in S1) | Rail sequence 3.3, BT sequence 3.4 |
| S2 -> S3a | (a) audio event: PCM1862 Energysense resume on ADC_INT (PC5) naming the input (SIGDET_STAT 0x32), or BM83 A2DP start over UART; (b) user play gesture; and HP_DET low; and power grant allows | Amplifier sequence 3.5 |
| S2 -> S3b | Same events with HP_DET high | Headphone sequence 4.3 |
| S3 -> S2 | Idle timer (section 2.4), user stop, HP insert/remove transition, source change fault recovery | Amplifier shutdown 3.6 / headphone off 4.4 |
| S2 -> S1 | User off gesture; or idle timeout; or VBUS lost and critical battery | BT shutdown 3.4, rail off 3.7, then arm wake sources |
| S1 -> S0 | (a) deep-off gesture on battery (PROPOSAL: hold SW100 5 s while in S1 or S2), (b) critical battery with no VBUS (section 2.5), (c) low-battery latch | Write REG14 = 0x96 (SFET_PRESENT = 1) and read it back, then REG11 SDRV_CTRL = ship (bench B2.1/B2.2 values 0x96 / 0x44), 10 s delay (SDRV_DLY = 0), MCU parks in Stop with every enable low. SW101 off is the manual equivalent |
| any -> F-x | section 3.8 | |
| S3 stays S3 | VBUS attach/detach/contract change | battery supplements SYS (NVDC); grant revoked then re-granted (section 3.2); never retain a stale IINDPM |

Standby wake sources (Stop mode): PC13 WKUP2 (QON), PA0 WKUP1 (GAUGE_ALRT_N), EXTI on PC14 (PD_PLUG_EVENT), PC10 (ENC_SW), PB2 (AUX_DET). HP_DET, AMP_FAULT_N and BT_TX_IND cannot wake (their rails are off); ENC_A/B need not wake (a rotation alone should not turn the speaker on).

### 2.4 Timers and thresholds (PROPOSAL, user decision)

| Parameter | Proposed | Reason |
|---|---|---|
| Amplifiers off after Energysense loss and no A2DP stream (S3 -> S2) | 3 min | Playing silence costs about 0.9-1.0 W (`audio-chain-architecture.md` section 6); 3 min keeps pause/skip instant |
| S2 -> S1 on battery, no BT link and no input | 20 min | |
| S2 -> S1 on external power | 60 min | |
| Standby -> ship | no timer | Standby is about 35-40 uA on the pack (BQ25792 17/24 uA, gauge, U21, MCU Stop) against ship 18-45 uA (bench plan B2.3): negligible for a 10 Ah pack (and for the 20 Ah 1S4P pack chosen on 2026-11-03), so ship mode is for deep-off and critical battery only |
| Battery polling | MAX17048 every 30 s in S2/S3, plus ALRT; BQ25792 status/flag registers polled every 250 ms with a source attached or charging, every 2 s otherwise (no CHG_INT since 2026-11-02) | |

### 2.5 Battery policy and USB-host heuristic

SOC thresholds (MAX17048 over CTRL bus; the gauge is reachable only while BAT_PACK is above about 3.08 V (U21), and the pack is not yet selected, so tune to the pack). The MAX17048 register facts below (CONFIG 0x0C with ATHD in bits 4:0 where the empty threshold is (32 - ATHD)%, VALRT 0x14, STATUS 0x1A, CRATE 0x16) are from my knowledge of the part: the local PDF text is unreadable (HANDOVER open item), so verify against the real datasheet.

| Level | SOC / voltage | Action |
|---|---|---|
| Normal | above 20% | Full AGL ceiling (section 5.4) |
| LOW1 | 20% or below | Warn (indicator if any); AGL ceiling -3 dB |
| LOW2 | 10% or below | Warn; ceiling -6 dB; fronts about 3 W, woofer about 5 W |
| CRIT | 5% or below, or VCELL below 3.30 V averaged over 10 s under load | Mute, stop amps, then S1. If VBUS absent: S0 (ship) at 3% or VCELL below 3.20 V unloaded |
| Re-arm | SOC 15% or above, or VBUS present | |

Set ATHD for 10% so the first alert arrives on GAUGE_ALRT_N; clear CONFIG.ALRT after reading STATUS.

**Pack 1S4P (2026-11-03).** The pack is now selected: 1S4P, 4 x Samsung INR21700-50S, 20 Ah nominal, about 72 Wh (`charge-policy-2026-11-02.md` section 12, `battery-4p-feasibility-2026-11-03.md`). Firmware constants that follow from it:
- Capacity constant **20 Ah** for time-to-empty, the UI and charge-time estimates (was 10 Ah).
- MAX17048: SOC needs no change (ModelGauge is voltage-based and has no capacity register). If the default HIBRT is used, set **HibThr 0x40 (HIBRT 0x4030)** instead of the default 0x80, and halve any other CRATE (%/h) threshold, because CRATE for a given current falls by 2/n [DS MAX17048 HIBRT, via the feasibility report §2.6; the local PDF text is still unreadable here, so verify against the real datasheet].
- The SOC thresholds in the table above are percentages and stay as they are. In time, each band is twice as long as with 10 Ah.
- Run time [EST, 85 % efficiency, 4.20 V-equivalent full charge; 4.10 V default float in brackets]: about 12.2 h (11.0) at 5 W, 6.1 h (5.5) at 10 W, 3.1 h (2.8) at 20 W average.

Battery absent or invalid (BQ25792 VBAT status): cap audio at about 5 W total (arch doc section 3 "Power path") and do not start the codec from SYS until the input limit is programmed (the battery-absent bootstrap deadlock in the contract is an open hardware gate; do not claim battery-absent SDP audio).

**USB-host presence heuristic (replaces the missing USB_SRC_DET).** On attach read TPS25730 register 0x34 ACTIVE_CONTRACT_PDO (DS TRM Table 2-8): bytes 5-6 "firstPDOControlBits" carry bits 29:20 of the source's first PDO; bit 6 of that field is PDO bit 26 "USB Communications Capable". Hosts set it, wall chargers normally do not. If set and the contract is granted, power the codec (CODEC_PWR_EN) so the host can enumerate; otherwise keep the codec off. The PCM2902C and Energysense then prove actual USB audio. Also read 0x35 ACTIVE_CONTRACT_RDO bit 24 (NoUSBSuspend) once and log it. BENCH: confirm with a PC, a PD wall charger and a power bank.

---

## 3. Startup, shutdown and fault sequencing (plan sections 4 and 9)

All delays are minimums. "Wait" values with no datasheet figure are my margins and are marked BENCH.

### 3.1 Reset and boot
1. All enables are low by hardware (R107, R111, R142, R152, R153, R212, R236, R255, R259 and the HP pull-downs). BT_RST_N, I2C2 and the PD software bus pins start as inputs.
2. Configure clocks, IWDG (2 s), set every output pin to its low state, then enable GPIO clocks for peripherals. Keep PA11/PB13 (PDCTRL) analog (PA12 is a spare no-connect: analog) and I2C2 (PB10/PB11) analog until their rails exist. PA11_RMP/PA12_RMP stay 0; PA13/PA14 stay SWD.
3. Set UCPD_DBDIS (PWR_CR3) before driving any FT_d pin high. `mcu-pin-allocation.md` lists PD1 (HP_SEL_B), PA9, PA10 (CHG_SYS_ENABLE), PC6 (CHG_ENABLE), PB0, PD3 as FT_d pins with the UCPD dead-battery pull-down (about 5.1 k) active at reset: harmless while they are low, but it would load a high output until DBDIS is set. Verify the pin list against RM0444 (BENCH).
4. Read BQ25792 identity/status over CTRL (0x6B) before anything else.

### 3.2 Charger / external power sequence (from `replacement-power-control-contract.md`; summarised, not duplicated)
Order, with CHG_SYS_ENABLE and CHG_ENABLE both low until step 7: (1) establish logic rail and reset state; (2) read identity, keep CE off, set 1S profile, VREG, ICHG (cap 3 A until the U4 PGND via area is checked, HANDOVER line 24), VSYSMIN, TS limits; (3) REG14 SFET_PRESENT = 1 and read back; (4) disable the charger watchdog, set AUTO_INDET_EN = 0 and HVDCP_EN = 0, keep EN_IINDPM; every 5 s read back EN_IINDPM, IINDPM, ICHG, VREG and treat a mismatch as REG_RST (drop both gates, reconfigure); (5) source capability from the PD contract (reg 0x34/0x35); a non-PD Rp-only source gets a conservative **500 mA** fallback (the PD controller does not report Type-C Rp current; 5 V fallback does not grant 2 A); (6) budget total connector draw including U19 and the PD controller, program and read back IINDPM while HIZ is asserted; (7) release CHG_SYS_ENABLE only after valid source/voltage/readbacks, then enable CE last. **Charge current is reduced before audio is shed.**

Events:
- **PD_PLUG_EVENT (PC14) rising**: start the soft I2C bus, read status. **Falling or PD_SINK_EN (PB9) rising (sink path disabled)**: revoke the grant, drop CHG_ENABLE then CHG_SYS_ENABLE, park PA11/PB13 as analog (LDO_3V3 pull-ups vanish with VBUS), continue on battery. Contract change: same revoke then re-read; do not use old limits.
- **BQ25792 poll** (replaces the CHG_INT EXTI since 2026-11-02, patch P1; every 250 ms with a source attached or charging, every 2 s otherwise): read the BQ25792 flag registers (read clears). Respond: VBUS OVP/UVLO or power-good loss -> as detach; charge done -> log; TS fault or thermal regulation -> disable CE and retry after 60 s; safety timer expiry -> disable CE, latch F-CHG until detach/re-plug or user gesture; watchdog expiry or VSYS/IBAT OCP -> as REG_RST (reapply configuration).
- **Charge policy (PROPOSAL)**: charge to 4.20 V by default, with a "plugged-in mostly" option at 4.10 V (battery longevity, plan section 2); recharge when 100-200 mV below VREG; ICHG 4.0 A (superseded 2026-11-02, see reports/charge-policy-2026-11-02.md; was: at most 3 A); for the 1S4P pack (2026-11-03, charge-policy section 12) ITERM 1000 mA (REG09 0x19), IPRECHG 720 mA (REG08 0xD2), safety timer 12 h (REG0E 0x3D) for sources of 15 W or more and 24 h (0x3F) below, and an expected charge time of about 5.1 h from empty at 9 V or higher PD (3.3 h for 20-80 %) [EST]; TS/NTC windows per the final pack (one 103AT-type NTC between the two middle cells, network unchanged); in S3 with a weak source, lower ICHG before AGL.

### 3.3 Rail up (S1 -> S2)
1. Confirm SOC and grant allow it (section 2.5).
2. 5V_LOGIC_EN = 1 (PA1). U14 TPS63802 ramps in about 0.3 ms (DS Tramp 224 us plus Tdelay), U22 TPS7A2033 adds 0.75-1.15 ms (DS tSTR). **Wait at least 10 ms** (BENCH: TP7 4.82 V nominal, TP6 3.3 V). 3V3_AUDIO must ramp monotonically: PCM1862 has no reset and no brownout detector (`audio-chain-architecture.md` section 2). Re-initialise the PCM1862 after every rail enable.
3. Enable I2C2 (PB10/PB11 AF6). Read PCM1862 at 0x4A; retry every 5 ms for 50 ms. No ACK: stay in S2 without audio and raise a fault.
4. Sample HP_DET (PB1) after 50 ms of stable 3V3_AUDIO, then unmask its EXTI.
5. CODEC_PWR_EN = 1 only if the host heuristic or user source = USB (section 2.5). Do not toggle it afterwards.
6. BT sequence 3.4.
7. Put the PCM1862 into Sleep with Energysense armed (INTA on ADC_INT, active high push-pull, polarity/pulse via INT_PLS, mask in INT_EN 0x60; INT_STAT 0x61, SIGDET_STAT 0x32; clear per datasheet 9.3.15.2).

### 3.4 BM83 sequencing (DS BM83 Figs 6-9, 6-11, 6-12, rendered; `bluetooth-notes.md`)
Power on:
1. Preconditions: BT_UART_TX (PD5) low, BT_MFB (PB3) low, **BT_RST_N (PB4) driven low** (open-drain low; the figure shows RST_N low through the BAT_IN ramp). BT_FORCE_PWM low.
2. BT_PWR_EN = 1 (PA8). 3V8_BT ramps (U15 same family as U14). **Wait at least 10 ms** (figure: SYS_PWR follows BAT_IN by 1 ms, then an idle interval). Check TP9 3V8_BT stays under 4.2 V (BM83 BAT_IN abs max 4.3 V).
3. BT_MFB = 1. **400 ms after MFB rises release BT_RST_N** (hi-Z). **About 20 ms later** expect the Power-On ACK on BT_UART_RX (PD6). Keep MFB high until the ACK, then low.
4. No ACK within 1 s: retry up to 5 times within 1 s (Fig 6-12 NACK path), then declare BT failed and continue without it.
5. Configure in host mode (baud, MFB polarity, TX_IND are Config Tool items, BENCH). Never drive PD5/PB3 high before 3V8_BT is up (back-power through R182/R183, `bluetooth-notes.md`).

Power off:
1. Mute the source path first (section 4). Send the Power-Off UART command, wait for the ACK (5 s timeout -> force step 3).
2. **Wait about 2 s after the ACK** (FIG 6-9), keeping BT_UART_TX and BT_MFB low.
3. Drive BT_RST_N low. RST_N must be fully low before SYS_PWR can fall to 2.7 V (DS 6.2).
4. **At least 1 s after RST_N goes low** (FIG 6-9) set BT_PWR_EN = 0. Ramp-down must exceed 640 us (DS Fig 6-11; R154 100k bleeder, BENCH). Wait at least 1 s before another BT_PWR_EN rising edge.
5. Emergency (CRIT battery, VBUS lost with no battery): send Power-Off, wait 200 ms for the ACK at most, RST_N low, BT_PWR_EN low. Abrupt MCU reset (IWDG/BOR) drops BT_PWR_EN with RST_N high: accepted, module POR, BENCH.

### 3.5 Speaker amplifier start (S2 -> S3a). Order is dictated by DS TAS5825M 9.5.3.1 and `audio-chain-architecture.md`
Preconditions: 3V3_AUDIO valid (section 3.3 step 2 done), HP_DET low, grant OK, active source selected, **source-module settle done** (section 4.1), PCM1862 woken but not yet clocking (slave default, no BCK/LRCK).
1. AMP_BOOST_EN = 1 (PA7). U25 soft-start 47 nF is about 11.3 ms (bench D11). **Wait at least 25 ms.** PVDD must be at or above 4.5 V before PDN rises; PVDD_AMP is checked again by register in step 7.
2. AMP_PDN = 1 (PA6). **Wait at least 5 ms** (DS: after PDN high, "wait 5 ms at least, then start SCLK, LRCLK"). Use 10 ms.
3. U6 (0x4C) and U7 (0x4D) ACK check; page 0 (0x00 = 0x00), book 0 (0x7F = 0x00).
4. **U7: DEVICE_CTRL_1 (0x02) = 0x06** (FSW 384 kHz, DAMP_PBTL = 1, hybrid modulation), **U6: 0x02 = 0x02** (BTL, hybrid). Read both back. **DAMP_PBTL must be written and verified before U7 leaves Hi-Z** (it is in Deep Sleep after PDN, so writing is allowed). The bench plan uses 0x04 (BD) for first light; hybrid is the arch-doc choice (idle current). BENCH.
5. Start the clocks: PCM1862 master mode (24.576 MHz crystal, 512 fs, BCK 64 fs; bench D8 register set), with PCM1862 mute bits MUTE_CH1_L/R (0x71 bits 0/1) set and input select written (0x41/0x42/0x44). BCK/LRCK start. Read PCM1862 STATE (0x72) = Run, CLK_ERR (0x75) = 0 and TAS FS_MON (0x37)/BCK_MON (0x38)/CLKDET_STATUS (0x39) once clocks are stable. **Wait at least 10 ms of stable clocks.**
6. Both amps: DEVICE_CTRL_2 (0x03) = **0x0A** (DIS_DSP = 0 DSP on, MUTE = 1, CTRL_STATE = Hi-Z). **Wait at least 5 ms** (DS step 5).
7. Read PVDD_ADC (0x5E): PVDD = value / 8.428 V (DS Table 39); require at least 10.5 V (value 89 or more) on both; otherwise abort to step 12 (F-AMP).
8. GPIO0: 0x60 GPIO_CTRL = 0x01 (GPIO0 output), 0x61 GPIO0_SEL = 0x0B (FAULTZ) on **both** devices (they are wired-OR; never use a CMOS GPIO0 mode). Clear faults: 0x78 FAULT_CLEAR bit 7 = 1. Read 0x70-0x73, require zero. Unmask AMP_FAULT_N (PC4 falling).
9. Load the DSP coefficient dump (PPC3 export) and registers: AGAIN 0x54 (arch doc -8.5 dB so 0 dBFS is about 11.1 V peak), ramp control 0x4E, DIG_VOL 0x4C. I2C2 speed: 100 kHz for bring-up, 400 kHz after BENCH (AUD_SDA routed length 278 mm, R209/R210 2.2k). Dump size unverified.
10. DEVICE_CTRL_2 (0x03) = **0x0B** (Play, MUTE still set). Wait 10 ms.
11. Unmute per section 4.2 step 5: clear PCM1862 mute, wait, clear TAS MUTE (0x03 = 0x03).
12. On any failed readback: DEVICE_CTRL_2 = Hi-Z, AMP_PDN = 0, AMP_BOOST_EN = 0 and raise F-AMP.
Total from step 1 to audible output: about 150-250 ms plus coefficient load.

### 3.6 Speaker amplifier stop (S3a -> S2), DS 9.5.3.2
1. TAS soft mute: 0x03 MUTE = 1 on both. **Wait 10 ms** (full-range ramp at the default 0.5 dB per FS update is at most 5.3 ms at 48 kHz, CALC; DS example says at least 6 ms).
2. 0x03 = 0x02 (Hi-Z) on both. **Wait at least 6 ms** (DS).
3. Mask AMP_FAULT_N EXTI. PCM1862 mute then Sleep or Standby (0x70): the TAS sees a clock halt (it goes Hi-Z by itself and recovers by itself, DS 9.3.4, which is why the order here is Hi-Z first).
4. AMP_PDN = 0 (PA6). Wait 1 ms.
5. AMP_BOOST_EN = 0 (PA7). Boost off after PDN, never before (`bench plan D27`).
6. Re-arm Energysense (PCM1862 Sleep).

### 3.7 Rail down (S2 -> S1)
1. Amps stopped (3.6), HP_EN = 0 then HP_G0/G1/HP_SEL = 0, BT shutdown (3.4), CODEC_PWR_EN = 0.
2. Mask HP_DET and AMP_FAULT_N EXTI, set I2C2 pins analog (the powered-down audio parts must not clamp or be held by the MCU).
3. 5V_LOGIC_EN = 0 last. Arm the standby wake sources, Stop.
Restart minimum: wait at least 500 ms after 5V_LOGIC_EN falls before raising it again (PCM1862 monotonic ramp requirement; BENCH TP6 discharge time).

### 3.8 Fault handling
| Source | Detect | Response |
|---|---|---|
| **AMP_FAULT_N** (PC4, active low, only while 3V3_AUDIO up and GPIO0 configured) | EXTI falling | Read 0x70 CHAN_FAULT (DC, OC per channel), 0x71 GLOBAL_FAULT1 (clock error etc.), 0x72 GLOBAL_FAULT2 (PVDD UV/OV, thermal shutdown), 0x73 WARNING (OTW) on both devices. The TAS has already put the affected outputs in Hi-Z (DS). Clock error with PCM1862 running: log, auto-recovers, no escalation. PVDD UV: boost or battery sag, re-run the whole start sequence once. OC/DC: full stop (3.6 steps 1-5), 0x78 clear, retry up to 3 times at 0.5 s, 2 s, 5 s with the whole 3.5 sequence, then latch F-AMP: amps off, require user gesture (hold) or detach to clear. Thermal shutdown: wait at least 10 s and OTW clear, one retry. PBTL has no cycle-by-cycle limit (DS 9.5.3.3.1); overcurrent shutdown only |
| TAS thermal warning (0x73 OTW) | polled every 1 s in S3 | Let thermal foldback (DS 9.4.4) act; log; if persistent, reduce ceiling one step |
| ~~CHG_INT~~ (PC15 spare) | none: BQ25792 polled (250 ms / 2 s) | Section 3.2 |
| **GAUGE_ALRT_N** (PA0) | falling | Read STATUS (RI reset indicator: re-init gauge model; VL/VH voltage; HD empty-threshold) then SOC policy (2.5); clear ALRT bit |
| **PD events** (PC14, PB9) | EXTI | Section 3.2 |
| Gauge unreachable | I2C NACK | Expected when BAT_PACK below about 3.08 V: treat as CRIT if the last SOC was 15% or less, else keep last value |
| Watchdog / brownout | IWDG | Hardware drops all enables; boot INIT; nothing is retained (no backup cell; store the last source in flash only if wanted) |
| PCM1862 no ACK, TAS no ACK | I2C | S2 without audio, F-AMP, retry on next user gesture |

---

## 4. Source-change mute timing and source conflict prevention (plan sections 7 and 8)

### 4.0 Single-owner rule (how two sources are prevented from conflicting)
- One variable `active_source` in {USB, BT, AUX} and one `output_mode` in {SPK, HP}. **Only one function writes PCM1862 registers 0x06/0x07 and HP_SEL_A/B** (HP_SEL both low = USB is the reset default, PC0/PD1 pull-downs R234/R235).
- Hardware exclusivity: the speaker path is one PCM1862 mux (single-bit codes only: 0x41, 0x42, 0x44; reject any write with more than one of bits 2:0 set); the headphone path is two TS5A23157 stages with break-before-make (tBBM at least 0.5 ns, DS), truth table HP_SEL_B/A: 00 USB, 01 BT, 1x AUX (never leave HP_SEL_B = 1 and HP_SEL_A = 1 as a "BT" request: B = 1 means AUX).
- Speakers and headphone amplifier never run together: HP_EN = 1 requires AMP_PDN = 0 (and TAS in shutdown), and AMP_PDN = 1 requires HP_EN = 0. Both amplifiers are enabled in a single function that checks `output_mode`.
- Source modules stay powered across source changes (codec, BM83); a source change touches only the two selectors. Sources that are powered but unselected are electrically inert (each input has its own AC-coupling capacitor and the PCM1862 mux is exclusive).
- Auto-switching: a playing source keeps priority. A newcomer (BT stream start, USB audio detected, AUX plug) is switched in only if the current source has been silent (Energysense loss) for 5 s, or the event is AUX_DET rising (explicit user action), or the user selects it. AUX_DET falling while AUX is active reverts to the previous source.
- In S2 the PCM1862 is in Sleep and Energysense scans **all eight inputs** (DS 9.3.11.2: 50/100/200 Hz detect intervals of 160/80/40 ms per channel, then one flag naming the channel in SIGDET_STAT): use it to choose which source woke the system. For BT use the BM83 A2DP UART event, which arrives earlier.

### 4.1 Settling times that must precede any unmute (CALC, BENCH)
- **Source module powered up**: the PCM2902C and BM83 outputs are AC-coupled with 4.7 uF and a 100 k bleed (C186/C187/C194/C195, R175/R176/R180/R181): a DC step of about VCCCI/2 = 1.65 V appears at power-up and decays with tau = 100 k x 4.7 uF = 0.47 s. After CODEC_PWR_EN rises (codec) or the Power-On ACK (BM83) **keep every output muted for at least 2.5 s (5 tau)**. This is why the modules stay powered across source changes.
- **Headphone mux node**: VMID_HP = 47k/47k with 4.7 uF (tau = 0.11 s) and six 1 uF / 100 k input nodes (tau about 0.1 s). After a cold 3V3_AUDIO enable, **HP_EN must not rise before 500 ms** (about 4-5 tau).
- **PCM1862 input pins**: unselected inputs are not documented as pre-biased (DS: input pins are designed to bias to AVDD/2; unselected behaviour not stated). If an unselected pin floats, selecting it connects a 20 k input to a bias with a 2.2 uF series cap discharged at 0 V (tau 44 ms, 5 tau = 220 ms). **Default after changing 0x06/0x07: wait 250 ms before unmuting. BENCH: if the scope shows no step on I2S_SDATA/TP13 at selection, reduce to the 20 ms of `audio-chain-architecture.md`.**

### 4.2 Speaker path source change (S3a, USB/BT/AUX in any order)
| t | Action | Why |
|---|---|---|
| 0 | TAS soft mute both: 0x03 MUTE = 1 (U6, U7) | Volume ramp is smooth (DS Table 10: "smoothly ramped down/up to avoid pop/click"); default ramp is 5.3 ms or less at 48 kHz |
| +10 ms | PCM1862 MUTE_CH1_L/R (0x71 bits 1:0) = 1 | PCM1862 fades on DOUT with zero-cross detection (DS 9.3.13: about 48 / fIN, forced after 8192/fS = 171 ms if no zero cross, then 48/fS = 1 ms) |
| +12 ms | Write 0x06/0x07 = new code (0x41/0x42/0x44) and the PGA gain for the new source (arch doc: USB +6 dB, BT +6 dB, AUX 0 dB). PGA steps need the DSP clocked: the PCM1862 is master, so this is satisfied | No switch carries a DC step; muted while the input RC settles |
| +12 ms + 250 ms (4.1) | PCM1862 MUTE bits = 0 | Fade-in as above |
| +20 ms later | TAS MUTE = 0 (both) and restore DIG_VOL | Source is already settled; ramp up 5.3 ms or less |
Total about 300 ms (about 70 ms once 4.1 is shortened by BENCH). Volume state, not the TAS mute bit, is what the encoder changes (section 6).

### 4.3 Headphone insertion (HP_DET rising while S3a or S2) and entry to headphone mode
Detection: HP_DET (PB1) is pulled to 3V3_AUDIO through R239 100k and is high with a plug (tip switch opens). **Debounce: insertion = high for 50 ms** (`audio-chain-architecture.md`). Removal while HP_EN is high needs a different rule: with no plug the switched tip connects to the TPA6132A2 OUTL, which an active amplifier drives with audio, so HP_DET follows the signal (centred on 0 V, peaks that can pass the 0.9 V VIL). With a plug present HP_DET is a steady 3.3 V. **Removal rule: any three or more low samples in a 20 ms window sampled at 1 kHz = removed** (a steady plug never reads low). BENCH with the real jack (open item in plan section 8).
Sequence (speaker -> headphone):
1. TAS MUTE = 1 (both), wait 10 ms.
2. TAS Hi-Z (0x03 = 0x02), wait at least 6 ms; AMP_PDN = 0; wait 1 ms; AMP_BOOST_EN = 0. PCM1862 to Standby (0x70) (headphone mode keeps ADC, boost and amps off: about 20-25 mW, arch doc).
3. HP_SEL_A/B = active source. Wait 5 ms (tBBM is nanoseconds; the margin covers the 1 uF coupling nodes).
4. HP_G0/HP_G1 = chosen gain (default 00 = -6 dB, acoustic-shock protection). Check 4.1: 3V3_AUDIO on for at least 500 ms and, for USB/BT, source settled 2.5 s.
5. HP_EN = 1. **Wait at least 5 ms** (TPA6132A2 tON 5 ms, DS). The amplifier's own pop suppression covers turn-on; DS 7.3.2: "Activate the TPA6132A2 after all audio sources have been activated and their output voltages have settled".
Removal (headphone -> speaker): HP_EN = 0, wait 10 ms (shutdown with pop suppression; output impedance in shutdown 20 ohm, DS), then the speaker start sequence 3.5 with an unmute ramp.

### 4.4 Headphone source change (S3b)
1. HP_EN = 0 (TPA6132A2 deactivates **before** the source changes, DS 7.3.2). Wait 10 ms.
2. Change HP_SEL_A/B (single write of both pins; break-before-make is inside the TS5A23157). Wait at least 5 ms (arch doc says 1 ms; 5 ms adds margin for the node networks).
3. HP_EN = 1. Wait 5 ms. No DC step exists across the switch because all six inputs sit at VMID_HP through their own 1 uF / 100 k networks and the TPA input caps hold 1.65 V either way (TPA input impedance in shutdown 10 k to ground, DS). The output follows the new source after the 5 ms start-up.
4. Never change HP_SEL with HP_EN high.

### 4.5 Other mute cases
- User mute: TAS MUTE bit in speaker mode, HP_EN low in headphone mode.
- Volume changes use TAS DIG_VOL (0x4C, 0.5 dB steps, ramped by the device); no mute needed.
- Aux plug/unplug on an unselected AUX: no action. AUX unplug on the active AUX: section 4.2 to the previous source.
- BT disconnect/silence and USB host sleep: handled by Energysense loss (3 min then S2).
- Any F-x fault or the CRIT battery path: 3.6 without the 3 min wait.

---

## 5. Audio architecture decision (PROPOSAL, needs user approval)

### 5.1 Where the processing lives
The MCU never sees audio: PCM1862 -> I2S (I2S_BCK, I2S_LRCK, I2S_SDATA, no MCU pin) -> both TAS5825M. So **all filtering and limiting must be in the TAS5825M DSP** (2 x 15 biquads, 3-band DRC, full-band AGL, bass enhancement, thermal foldback, PVDD tracking, spatializer; DS 9.3.7 and features list; process flows selectable in PPC3). The MCU does only: coefficient loading at power-up (`audio-chain-architecture.md` section 3, no EEPROM), volume mapping, mute, ceiling selection, source select, monitoring. The PCM1862 has no DSP beyond gain and mixer (it cannot do the crossover).

### 5.2 Channel plan (as built)
- U6 stereo BTL: OUT_A = FRONT_L (J9), OUT_B = FRONT_R (J10). Fronts are high-passed in U6.
- U7 mono **PBTL**, pre-filter, pairing OUT_A+(2)/OUT_A-(30) and OUT_B+(23)/OUT_B-(27) (verified from SLASEH7F Fig 159, `plan.md` section 9): drives the woofer J11. U7 takes the **left frame only** (DS 9.4.2.2), so the DSP must form the mono sum into the left channel (R1 below). Low-passed in U7.
- Level matching: front 83 dB (2.83 V, 1 m) with two drivers coherent at low frequency is about 89 dB; woofer 78.3 dB. The woofer needs about 10 dB more drive than the fronts at the crossover (CALC). Start: mono sum (L+R)/2 in the mixer, then set U7 AGAIN (0x54) 4-6 dB higher than U6's -8.5 dB and trim by measurement, with the AGL ceiling protecting the woofer. Use U7 ceiling first (below).
- **Risk R1 (unverified):** the mono sum in the DSP. If the chosen PPC3 flow has no input mixer, fall back to the L+R mix in the PCM1862 digital mixer only if both amps then receive mono (not acceptable for the fronts); there is no clean hardware fallback (U6 SDOUT, TAS GPIO1/2 and PCM1862 DOUT2/GPIO are no-connects). Decide the PPC3 flow before bring-up.

### 5.3 Crossover and EQ (starting values, tune by measurement)
Enclosure assumptions: fronts share the 2.025 L main chamber (about 1.0 L effective each), woofer 0.525 L sealed (`cad/volumes.md`).
| Driver | Parameter | Computed (CALC, sealed alignment) |
|---|---|---|
| ND65-4 | Fs 89.5, Qts 0.61, Vas 0.53 L, Xmax 3.5 mm | fc about 111 Hz, Qtc about 0.76, in 1.0 L effective |
| W3-2052SC | Fs 59, Qts 0.49, Vas 0.595 L, Xmax 5 mm | fc about 86 Hz, Qtc about 0.72 |
Proposal: **Linkwitz-Riley 4th order, default 150 Hz, allowed range 120-200 Hz** (2 biquads each side).
- Lower bound 120 Hz: at the maximum drive of 11.1 V peak the ND65-4 would reach 6.6 mm at 100 Hz and 3.8 mm at 150 Hz unfiltered (lumped model with back-EMF, k about 1130 N/m, Mms 2.5 g; Xmax 3.5 mm). With an LR4 high-pass the worst case is about 2.8 mm at 120 Hz crossover and about 1.9 mm at 150 Hz. 150 Hz leaves headroom for EQ boosts.
- Upper bound about 200 Hz: the downward-firing mono woofer becomes localisable above that. The woofer is specified to 800 Hz, so it is not the limit.
- The woofer's sealed roll-off is about 86 Hz: do not boost below 60 Hz. Add a 2nd-order subsonic high-pass at 45 Hz on U7. Expect modest bass: excursion-limited SPL at 1 m in half-space is about 83 dB at 60 Hz and about 92 dB at 100 Hz for the woofer, about 90 dB at 150 Hz per front driver (CALC, ignores thermal limits).
- Front EQ: compensate the 22 uH output filter roll-off (about -3 dB near 18 kHz, arch doc) with a high shelf; driver EQ from measurement.
- Loudness: **static** curve only in the first release (a low shelf of 2-3 dB around 100 Hz and a high shelf of 1-2 dB around 8 kHz when the user is below -30 dB). A volume-dependent loudness curve needs runtime biquad updates (register 0x5C BQ_WR_CTRL1 exists, DS, but glitch behaviour is not documented): defer until the bench shows it clean.

### 5.4 Driver protection
| Layer | Proposal |
|---|---|
| Excursion (fronts) | LR4 high-pass at 150 Hz (above). No excursion model exists in the datasheet: the PPC3 "Smart Amp" process flow (thermal and excursion protection, DS features) would add one but needs driver parameters and a flow choice: option only, user decision |
| Excursion (woofer) | CALC: at 11.1 V peak the woofer stays about 4.1 mm or less (40 Hz worst case, Xmax 5 mm), so the 45 Hz subsonic filter plus AGL is enough; thermal is the limit: 11.1 V peak into 4.3 ohm is 14.3 W, at the 15 W RMS rating |
| Level (AGL) | Full-band AGL on both devices. Power into 4 ohm for a sine at L dBFS (0 dBFS = 11.1 V peak): 0 dBFS = 15.4 W, -3 dB = 7.7 W, -6 dB = 3.85 W, -9 dB = 1.9 W. Starting ceilings per `audio-chain-architecture.md` section 3: fronts about 5 W continuous (about -5 dBFS), woofer about 10 W (about -2 dBFS), short peaks allowed. SOC bands lower these by 3 dB (LOW1) and 6 dB (LOW2) and no-battery mode caps the total at about 5 W: keep three AGL coefficient sets (FULL, -3, -6) selected by writing a few registers at transitions only |
| Supply | Enable PVDD tracking (dynamic headroom) if the PPC3 flow offers it: PVDD sag from boost current limit then lowers gain automatically (TAS reads PVDD with its own ADC, reg 0x5E) |
| Thermal | TAS thermal foldback (DS 9.4.4, OTW levels in 0x73) plus the MCU 1 s poll |
| Fault | DC detect and overcurrent shutdown fault paths: section 3.8 |
| Transients | The mute/Hi-Z-before-PDN/boost sequences (3.5, 3.6, 4.3) avoid cone slams |
| Volume cap | Firmware never exceeds the SOC-dependent maximum volume index, and never writes DIG_VOL above 0 dB (0x30) |

Open driver items: the W3-2052SC has no maker datasheet (Parts Express table only, `reports/sourcing-2026-10-12.md`); the ND65-4 data above are maker values. Measure impedance and response on the first build before freezing the filters.

---

## 6. Controls and indicators (plan section 4, "define buttons, indicators, volume/source control and battery display")

### 6.1 Inputs that exist
| Control | Ref | Net / pin | Notes |
|---|---|---|---|
| Volume encoder | SW102 Alps EC11E18244AU | ENC_A PC8, ENC_B PC9 | 18 pulses, 36 detents per turn (2 quadrature edges per detent, x4 mode counts), internal pull-ups, 10 nF C308/C309 debounce. PC8/PC9 are TIM1_CH1/CH2 (AF2, DS Table 14) so the encoder can use TIM1 encoder mode with the input filter; if the RGB LED PWM (TIM1_CH1N/2N/3N on PB13-15) is ever added, switch the encoder to EXTI/state-table decoding because TIM1 is shared |
| Encoder push | SW102 | ENC_SW PC10 | Active low, C310 10 nF; EXTI wake from Stop |
| QON button | SW100 TE 1977066-1 | CHG_QON_SENSE PC13 (WKUP2) via R113 | Also wired to the BQ25792 QON: hardware ship-mode wake (1 s) and **system power reset at 10 s hold** (DS 9.3.12.3, bench B2.8 12 s). Tap and hold timing here must never rely on holds above about 8 s |
| Pack switch | SW101 | none | Physical disconnect, not readable |
| (BTN_ADC ladder) | none | PA3 reserved | Not present |
Debounce: 20 ms for both buttons, encoder decoded with the hardware filter.

### 6.2 Proposed gestures (PROPOSAL, needs user decision)
| Control | Gesture | Action |
|---|---|---|
| Encoder rotate | each detent | Volume +/- one step. 40 indexes, index 0 = mute, indexes 1-40 = -58.5 dB ... 0 dB in 1.5 dB steps: DIG_VOL (0x4C) = 0x30 + 2 x attenuation(dB), so -58.5 dB = 0xA5, written to U6 and U7 together; fast turns (more than 10 detents/s) take 2 indexes per detent. The index is capped by the SOC band. Bluetooth: also send the AVRCP absolute-volume command so the phone slider follows (command set not in the local files, UNVERIFIED) |
| Encoder rotate (headphone mode) | each detent | Only the TPA6132A2 gain exists (-6/0/+3/+6 dB on HP_G0/HP_G1) plus BM83 volume for BT; USB and AUX have no source volume (HID not wired). Proposal: limit the encoder to -6, 0 and +3 dB, +6 dB only behind a long-press confirmation; default -6 dB |
| Encoder push | short | Mute toggle |
| Encoder push | double | Next source USB -> BT -> AUX (skip AUX if AUX_DET low, skip USB if the host heuristic is false) |
| Encoder push | hold 1 s | BT pairing mode (BM83 UART command, UNVERIFIED) |
| SW100 | tap (below 0.6 s) | Play/pause (BT: AVRCP; other sources: mute toggle) |
| SW100 | hold 1.0 s | Power toggle S1 <-> S2/S3 (the hardware itself wakes from ship at this duration, so the gesture is the same everywhere) |
| SW100 | hold 5 s | Deep off to S0 (ship) on battery; on USB it only goes to S1 |
| SW100 | hold 10-12 s | Hardware system reset (BQ25792), documented, not firmware |
| AUX_DET / HP_DET | plug events | Section 4: AUX in = switch to AUX, AUX out = revert; HP in/out = speaker<->headphone |

### 6.3 Battery display and indicators
- **No LED, display or buzzer exists (section 1.2).** Proposed minimum hardware change: an RGB LED on PA2/PB14/PB15 (TIM2_CH3 + TIM1_CH2N/3N PWM, 3.0 V logic; PB13 is PDCTRL_SDA since 2026-11-02) with series resistors and a mechanical window; this is not in the netlist and is a user decision. Suggested patterns if added: white solid on, amber blinking low battery (LOW1), red blinking CRIT, blue slow pulse pairing, red double blink fault, green charging complete.
- Without the LED: battery level to the phone through BM83 (HFP battery indicator / UART battery command, UNVERIFIED in the local files) only.
- Battery SOC bands: section 2.5.

---

## 7. Decisions needed from the user
1. Add a status LED (RGB on PA2/PB14/PB15) or accept no on-device feedback.
2. Crossover default 150 Hz and the LR4 slopes; whether the PPC3 "Smart Amp" excursion flow is wanted (needs TI tooling access).
3. Idle timers: 3 min amps off; S2 -> S1 20 min battery / 60 min external; no standby-to-ship timer.
4. SOC thresholds (20/10/5%, 3% ship) and AGL ceiling steps (-3/-6 dB); charge target 4.20 V vs 4.10 V "plugged-in mostly".
5. Gestures in section 6.2, especially SW100 tap = play/pause and SW100 hold 5 s = deep off.
6. Headphone volume: only four TPA gain steps (default -6 dB, cap at 0 dB without confirmation); USB host volume cannot be moved from the speaker.
7. Whether to wire the missing USB_SRC_DET / CODEC_SSPND / HID signals in a respin, or keep the PD-bit heuristic and Energysense.

## 8. Bench verification list (new items from this spec; the first-board plan is `bench-bringup-plan.md`)
1. TP6/TP7 ramp and discharge times after PA1 (sets the 10 ms and 500 ms waits).
2. PCM1862 DC step at input selection (sets 20 ms vs 250 ms, section 4.1) and unselected-pin bias.
3. DC step and decay at CODEC_PWR_EN and at BM83 power-on (sets the 2.5 s).
4. HP_DET removal behaviour with the real PJ-307 while the TPA6132A2 is playing (section 4.3 rule); AUX_DET timing (R241 1 M x C246 100 nF: about 120 ms to 70% on insertion).
5. TAS5825M: PVDD_ADC scale (11.9 V = 100), POWER_STATE encoding, PBTL mono-sum flow in PPC3, whether hybrid mode (0x02 = 0x02/0x06) works with the 22 uH filters, I2C speed on the 278 mm AUD bus.
6. BM83: MFB polarity, power-on/off timing against Fig 6-9 (RST_N low during ramp, 400 ms, 2 s, 1 s), UART baud, battery command, AVRCP volume.
7. QON sense idle level in ship mode (bench B2.4), and PC13 behaviour during the 10 s reset.
8. MAX17048 registers (local PDF unreadable).
9. TPS25730 "USB Communications Capable" host heuristic (reg 0x34) on a PC, a wall PD adapter and a power bank (section 2.5).
