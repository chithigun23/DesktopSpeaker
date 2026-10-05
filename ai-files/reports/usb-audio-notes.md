# USB audio notes (PCM2902C, 2026-10-06)

Sheet `USB_Audio.kicad_sch` (root page 8). Datasheet SBFS039 (`datasheets/PCM2902C.pdf`), circuit follows Figure 39 (simple bus-powered configuration). No bench or USB compliance testing is claimed.

## Supply choice
- VBUS pin (3) is fed from `5V_LOGIC` (U14 TPS63802, nominal 4.82 V, conservative DC range 4.60-5.06 V per `codec-rail-dc-review.json`) through R170 2.2 R plus C170 1 uF, as in the datasheet. Datasheet VBUS range 4.35-5.25 V; 56 mA typ / 67 mA max operating, 250 uA suspend (at VBUS = 5 V).
- Rejected: raw connector VBUS (5-20 V PD would destroy it), USB_AUX_5V (U19, intended only for MCU bootstrap; the replacement-power contract says not to feed the codec from it), SYS_RAW (battery voltage, below 4.35 V).
- Consequence: the codec is powered only when the MCU sets `5V_LOGIC_EN`. Its D+ pull-up (R173 1.5 k to the internal 3.3 V VDDI) is the USB attach signal, so the MCU controls when the host sees the device. Firmware must keep 5V_LOGIC off on DCP/unknown sources, and the later TS3USB221A mux must isolate D+/D- until the source is classified (policy in `automatic-usb-source-policy.md`).
- DATASHEET FINDING: the PCM2902C has no internal D+ pull-up; Figure 39 shows an external 1.5 k from D+ (connector side of the 22 R) to VDDI. SEL0/SEL1 are tied to VDDI (must be high). HID0-2 have internal pull-downs (unused, no-connect). There is no reset pin (internal POR at VBUS about 2.5 V, about 700 us).

## Pin treatment
- D+/D-: 22 R series (R171/R172). D+ pull-up R173 to VDDI. Ports USB_DP/USB_DN are bidirectional.
- Decoupling: VDDI, VCCXI, VCCP2I, VCCP1I 1 uF each (datasheet: must be < 2 uF), VCCCI and VCOM 10 uF. All grounds (DGNDU, DGND, AGNDC, AGNDP, AGNDX) join the single GND.
- Clock: 12 MHz crystal Y170 (YXC X322512MSB4SI, C9002, 20 pF load), 1 M R174 across XTI/XTO, 22 pF C177/C178 to GND (datasheet 10-33 pF). With about 3 pF stray this gives roughly 14 pF CL, below the crystal's 20 pF rating; frequency error is likely tens of ppm against the 500 ppm allowance, but tune at bring-up (33 pF would match better). Crystal pad usage (1/3 crystal, 2/4 GND) and the crystal datasheet are unverified.
- Unused: DIN, DOUT, SSPND (reserved for a later MCU suspend input), VINL/VINR (no ADC use planned), HID0-2 (mute/volume could later be driven from the MCU at 3.0 V logic, VIH 2.52 V).

## Analogue output
- VOUTL/VOUTR: 0.6 VCCCI Vpp (about 2.0 Vpp, 0.7 Vrms) centred on 0.5 VCCCI (about 1.65 V), load >= 10 k AC-coupled. 4.7 uF coupling caps C186/C187 (X7R 1206, same part as C5) and 100 k bleed resistors R175/R176 to GND give a defined DC level and a high-pass corner below 1 Hz at 100 k (about 3 Hz at 10 k). Ports `USB_AUDIO_L` / `USB_AUDIO_R` are outputs; the downstream stage must provide its own bias. Not connected to any mux yet (the two root stubs show as dangling labels).

## USB connector path
- J1 A6/B6 = DP1/DP2 (USB_DP) and A7/B7 = DN1/DN2 (USB_DN), joined through labels (A7 sits between A6 and B6). D1 TPD2E2U06 IO1 = USB_DP, IO2 = USB_DN, GND to ground, NC pins flagged. D1 library pin types were changed from unspecified to passive/power_in/no_connect so ERC pin_to_pin warnings do not appear.
- Shield: J1 EH pins 1-4 are tied directly to GND (no RC), as already drawn. With no metal chassis this is the simple choice; if an enclosure connection is added, consider 1 M parallel 4.7 nF.
- FINDING (fixed): in the baseline netlist the root J1 grounds/shield were on a root-local net `/GND` that was separate from the global `GND` used by every child sheet (labels vs power symbols). The new D1 ground symbol joins them, so J1 ground now reaches system ground. Please confirm this is intended.
- Tap point for the later source mux: insert the TS3USB221A common port on root nets USB_DP/USB_DN and rename the sheet ports/branch B (for example USB_AUDIO_DP/DN); no mux added.

## USB power budget interaction
- PCM2902C descriptor is fixed bus-powered, bMaxPower 100 mA. Since the codec runs from 5V_LOGIC (battery or converted VBUS), the host does not see it as a separate load, so the 100 mA claim is not an enforced limit; the whole-board input limit still comes from the charger IINDPM (BQ25792 minimum 100 mA) plus U19/PD-controller consumption. Codec 56-67 mA at 5 V is about 0.3-0.35 W: about 80-100 mA at 3.6 V battery referred to U14, a heavy share of a 100 mA SDP budget, so SDP-limited operation will need battery supplementing.
- Suspend: the codec alone is 250 uA (limit for a bus-powered device is 2.5 mA), but 5V_LOGIC (U14, divider, amplifier loads) is not USB-suspend-aware. Firmware should read SSPND (reserved, not wired) or detect bus idle and drop 5V_LOGIC_EN, then re-enable on resume; PCM2902C does not support remote wake-up.
- Open: battery-absent bootstrap (U14 runs from SYS_RAW; the codec must not be enabled before the input limit is programmed), and whether a descriptor stating "bus powered" is acceptable with a battery-powered rail (USB-IF compliance not assessed).

## Open qualification items
1. Crystal datasheet/pinout and load-capacitor tuning; stock and price of C9002, C1653.
2. LCSC codes/prices for R170 (2.2 R) and R171/R172 (22 R) not found in the 5 permitted lookups.
3. Ceramic 10 uF/1 uF DC-bias behaviour on VCCCI/VCOM/VDDI (datasheet drawing uses polarized 10 uF on VCCCI/VCOM and requires 1 uF parts < 2 uF effective).
4. Ripple on 5V_LOGIC (PFM/forced PWM) versus codec analogue performance; DS performance quoted with a REG103-class low-noise supply.
5. Source detection and D+/D- mux, 5V_LOGIC_EN sequencing, SSPND/HID to MCU (pins reserved in `mcu-pin-allocation.md` are not changed).
6. Larger-MCU swap remains a separate task.
