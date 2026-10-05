# MCU pin allocation (STM32G031K8T6, LQFP32)

2026-10-06. Planning plus capture brief. Datasheet DS12992 Rev 1 (`datasheets/STM32G031x4_x6_x8.pdf`) Table 12/13. The placed MCU reference is **U3** (not U1). No firmware or hardware test is claimed.

## Supply, reset, boot, debug

- VDD range 1.7-3.6 V (power scheme fig. quotes 1.55 V). The 3V_AO rail (U12 TPS7A0230, 3.0 V nominal, USB-priority or pack input) fits; below about 3.0 V input it sags but stays in range. The LQFP32 has one VDD/VDDA pin (4) and one VSS/VSSA pin (5): VDDA = VDD and VREF+ is internal, so ADC reference is the sagging 3V_AO (use VREFINT calibration). Datasheet fig. 13: 100 nF plus 4.7 uF at VDD/VDDA, close to the pin.
- NRST (pin 6): internal pull-up (no external pull-up needed), 100 nF to GND per fig. 24, wired to the SWD header. NRST_MODE option must stay "reset input" (PF2 is otherwise a GPIO).
- BOOT0 is PA14-BOOT0, shared with SWCLK. Factory option nBOOT_SEL=1 ignores the pin (boots flash; empty flash falls into the ROM loader). 100 k pull-down kept on the line so a later nBOOT_SEL=0 boots flash by default; entering the bootloader then needs the header/option bytes (no jumper captured).
- SWD: J7 Tag-Connect TC2030-IDC (1 3V_AO, 2 SWDIO PA13, 3 NRST, 4 SWCLK PA14, 5 GND, 6 SWO nc) and J6 4-pin 2.54 mm header (1 SWDIO, 2 SWCLK, 3 NRST, 4 GND). Firmware must not remap PA13/PA14 or enter a mode that disables SWD without a startup delay.
- PA11/PA12: LQFP32 bonds PA11 (22) and PA12 (23) as real pins and PA9/PA10 on pins 19/21. SYSCFG PA11_RMP/PA12_RMP must stay 0 (the [PA9]/[PA10] bracket is the small-package remap).

## Allocation (captured now)

| Signal | Dir (MCU) | Pin | Function / notes |
|---|---|---|---|
| CTRL_SDA, CTRL_SCL | bidir | PB7 (31), PB6 (30) | I2C1 AF6, FT_f. Bus: BQ25792 0x6B, MAX17048 0x36 (behind gauge isolation switches). Pull-ups R120/R121 4.7 k to 3V_AO already in Fuel_Gauge_Power: not duplicated. |
| PDCTRL_SDA, PDCTRL_SCL | bidir | PA12 (23), PA11 (22) | I2C2 AF6, FT_f; only I2C2 location on LQFP32. TPS25730D 0x20. |
| CHG_ENABLE | out | PC6 (20) | R107 100 k pull-down (net reaches Q100 gate): reset keeps charge off. High = enabled. |
| CHG_SYS_ENABLE | out | PA10 (21) | R111 100 k pull-down to Q102 gate: reset keeps ILIM_HIZ asserted (conversion off). |
| CHG_INT | in | PC15 (3) | BQ INT, open-drain, R106 10 k to 3V_AO. Edge/EXTI. |
| GAUGE_ALRT_N | in | PA0 (7, WKUP1) | MAX17048 ALRT through isolation switch U17, R122 47 k to 3V_AO. WKUP1 allows standby wake. |
| PD_PLUG_EVENT | in | PC14 (2) | TPS25730D open-drain, R16 100 k to LDO_3V3 (1 = attached; 0 when VBUS absent). EXTI wake from Stop. |
| PD_SINK_EN | in | PB9 (1) | TPS25730D open-drain, R17 100 k to LDO_3V3 (0 = sink path enabled). Status only. |
| BT_PWR_EN | out | PA8 (18) | U15 EN, R152 100 k pull-down. |
| BT_FORCE_PWM | out | PA9 (19) | U15 MODE, R153 100 k pull-down (default PFM). |
| BT_UART_TX | out | PA2 (9) | USART2_TX AF1 to BM83 P8_6 RXD via R182 10 k (Bluetooth sheet). Drive low before BT_PWR_EN goes low. Pin moved to the right side of the symbol. |
| BT_UART_RX | in | PA3 (10) | USART2_RX AF1 (or LPUART1_RX) from BM83 P8_5 TXD via R186 1 k. FT_ea, 5 V tolerant. |
| BT_MFB | out | PB3 (27) | BM83 PWR(MFB) wake/power key via R183 10 k, R184 100 k pull-down on the module side. Costs the SWO option (J7 pin 6 was already nc). |
| BT_RST_N | out | PB4 (28) | BM83 RST_N via R185 1 k; drive open-drain (low only), module has the pull-up. |
| BT_TX_IND | in | PB8 (32) | BM83 P0_0 UART_TX_IND (Host mode) via R187 1 k; EXTI wake. Pin moved to the left side of the symbol. FT_f. Firmware enables internal pull-down. |
| 5V_LOGIC_EN | out | PB5 (29) | U14 EN, R142 100 k pull-down. U14 MODE is hard-tied to SYS_RAW (no MCU mode pin). |

Verified against the child sheets: port names/directions above match `USB_PD`, `Battery_Charger`, `Fuel_Gauge_Power`, `Bluetooth_Power` and `Logic_Audio_Power` hierarchical labels and the baseline netlist.

## Voltage domains and I2C choices

- PDCTRL pull-ups (R14/R15 10 k) go to LDO_3V3 (3.3 V, present only with VBUS). Keep them there: pulling to 3V_AO would back-feed the TPS25730D with its LDO off. FT_f pins tolerate 3.3 V at VDD = 3.0 V (abs max VDD+4.0 V, input spec min(VDD+3.6, 5.5)); the MCU only pulls low. VIL 0.3 VDD (0.9 V) vs TPS25730D VOL is acceptable but check at bring-up.
- Unpowered behaviour: no VBUS means LDO_3V3 is off, both PD lines float and the TPS25730D is dead. Firmware should keep I2C2 disabled (pins analog or input no-pull) until PD_PLUG_EVENT = 1; the pull-ups only exist while the PD chip is present. 3V_AO is up whenever VBUS is (U20 USB-priority), so LDO_3V3 pulling the pins with VDD = 0 should not occur except in the first ms of attach (still <= 4 V).
- PD_PLUG_EVENT and PD_SINK_EN are driven 0 to 3.3 V: inside the same FT limit.
- The gauge CTRL bus is isolated below the 3.08 V supervisor threshold (U21/Q104): expect NACKs from the MAX17048 when 3V_AO sags.
- 2N7002 gates (Q100/Q102) at 3.0 V are at a marginal enhancement level; the loads are 100 k pull-ups so acceptable. At VDD below about 2.5 V enables may fail to assert: safe state is OFF.

## Safe reset states

All GPIO are floating inputs in reset (and SWD pins keep SWD function). The external pull-downs R107, R111, R142, R152, R153 define OFF for every captured output: no pin needs an MCU-defined state at reset. Firmware order: drive all five outputs low (push-pull) before enabling I2C traffic, per replacement-power-control-contract.md. Inputs have external pull-ups already.

## Reserved for later (left no-connect on the sheet)

| Pin | Reserved use | Note |
|---|---|---|
| PA4 (11), PA5 (12) | codec / source selects for TS5A23157 (x2) | |
| PA6 (13), PA7 (14) | amp PDN / FAULT (two TAS5825M; may need more) | |
| PA1 (8) | volume/source button ADC ladder | analog |
| PB0 (15) | headphone detect | ADC_IN8 |
| PB1 (16) | USB-A source-detect placeholder | ADC_IN9 |
| PB2 (17) | spare / amp mute | |
| PB6/PB7 alt | spare (I2C1 alternates) | |
| PA15 (26), PB2 (17), PB8 now used | PA15: LEDs; audio I2C needs two pins: PB2 + PA15 (or share CTRL) | PB3/PB4 now BT_MFB/BT_RST_N, PB8 BT_TX_IND |
| PC14/15 | if LSE ever needed they are used by CHG_INT/PD_PLUG_EVENT now: no crystal planned | |

The budget is tight: 29 GPIO, 17 captured or fixed (SWD included), about 17 wanted later. Audio I2C (TAS5825M x2, PCM1862) has no hardware instance left (I2C1 = CTRL, I2C2 = PD): use a bit-banged bus on PB3/PB4 or share CTRL after isolating powered-off parts. Open question for the user.

## Not captured (no net exists)

- QON/button sense: SW100 drives only BQ QON inside Battery_Charger; there is no port. A future `CHG_QON_SENSE` port plus a divider/open-drain buffer would be needed. No pin assigned beyond the button ladder.
- USB-source detection: no net exists; PB1 reserved.
- Remaining PD outputs (CAP_MIS, PLUG_FLIP, DBG_ACC) are no-connect on the PD sheet.

## Bluetooth update (2026-10-06)

BM83 nets captured in `Bluetooth.kicad_sch`: BT_UART_TX (PA2), BT_UART_RX (PA3), BT_MFB (PB3), BT_RST_N (PB4), BT_TX_IND (PB8). The MCU symbol swapped PA2 and PB8 positions so outputs stay right and inputs left; MCU ports: left BT_TX_IND, BT_UART_RX; right BT_MFB, BT_RST_N, BT_UART_TX. Power-off ACK is a UART message (no pin). GPIO budget is now 5 tighter: spare PB2, PA15 (LEDs), PB1/PB0/PA1 analogue, PA4-PA7. Open: audio I2C pins.
