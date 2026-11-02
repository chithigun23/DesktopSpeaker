# RT-9 schematic patch proposals (for the coordinator; not applied)

RT-9 did not edit any schematic. The board keeps every pad net of RT-8 (gates4 `pad_net_diff []`). The RT-8 proposals stay valid:
- P1 CHG_INT not required (accepted unrouted by the coordinator);
- P2 3V_AO to R241;
- P3 placement items.

They are in `ai-files/pcb/work-route8/schematic-patch.md`. RT-9 adds P4 and P5.

## P4. PDCTRL_SDA: move from U3 pin 44 (PA12) to U3 pin 33 (PB13)

**Why the current pin cannot be routed.** U3-44 sits between SWDIO (pin 45) and PDCTRL_SCL (pin 43) at 0.5 mm pitch.

The In2 5V_LOGIC trunk (w 2.0 / 1.0 / 0.4) runs diagonally 1-2 mm north of pins 40-48. Because of it, no via fits within about 1.2 mm of these pins, so every north-row pin must stay on F.Cu until it is past the trunk.

The column north of pin 44 must also carry the SWDIO J7 branch, which is the only lane around the east side of the J7 NPTH hole (124.64, 66.59). East of pin 44, the SCL, CODEC_PWR_EN, BT_PWR_EN, CHG_QON_SENSE and PD_PLUG_EVENT lanes fill F, B and In2 up to BT_AUDIO_L.

Searches on the final board:
- `t/jD1.log`: from U3-44, exp 2;
- `t/jD2.log`, `t/jD3.log`: from the U11 side, 1.1-1.2 M nodes, no path.

Over all the 24 + 24 + 40 + 24 corridor orders tried, SDA and SCL never both fit together with the five other corridor nets.

**Proposed edit.** `MCU.kicad_sch`: move the `PDCTRL_SDA` label from U3 pin 44 (PA12) to pin 33 (PB13).
- PB13 is a no-connect in the current schematic (`unconnected-(U3-PB13-Pad33)`). The LED_R allocation in `mcu-pin-allocation.md` is out of date.
- PA12 becomes a spare. Pin 44 gets a no-connect flag, or a pull-down per AN5096.
- The bus is bit-banged (`mcu-pin-allocation.md`: "Software (bit-banged) I2C, open-drain output, FT_f"), so no alternate function is needed.
- PB13 is a 5 V-tolerant I/O, which matters because the R14 pull-up goes to LDO_3V3.
- Update `ai-files/reports/mcu-pin-allocation.md` and the firmware pin map.

**Verified route** (probe on the final board, with the U3-33 pad net set to PDCTRL_SDA in a copy of the geometry; `t/jSDA33.log`, plan `t/pSDA33.json`): 14.8 mm, 4 vias, exact 0/45/90:

| layer | segments |
|---|---|
| F.Cu | (131.75, 70.825)-(132.15, 70.425)-(132.15, 68.725) |
| B.Cu | (132.15, 68.725)-(134.5, 66.375) |
| F.Cu | (134.5, 66.375)-(134.5, 64.825)-(133.95, 64.275) |
| In2.Cu | (133.95, 64.275)-(135.4, 62.825)-(135.4, 58.775) |
| F.Cu | (135.4, 58.775)-(135.4, 58.025), into U11-8 |

Pins 34, 35, 37, 40 and 41 were probed the same way and have no exit (exp 0-410).

## P5. NRST to J7-3 (TC2030 pin 3)

**Why it is open.** J7-3 (122.1, 63.415) sits between the other five TC2030 pads. Its only exit is north, through the 0.8 mm gap between the J7 NPTH holes at y 61.51.

North of that gap the region is closed off by:
- BT_AUDIO_R (F.Cu y 59.565, B.Cu to x 130.6);
- the BT_AUDIO_L diagonal;
- the BT bundle at x 113-119;
- the J7 holes.

NRST copper is 20-40 mm away, south and east of U3. hr8 runs on the final board (`t/jN1-3.log`, F/B/In2 and F/B only) stop after 21-61 k nodes: the reachable pocket around J7-3 is closed.

**Options:**
- (a) **Recommended, schematic:** do not connect J7-3. Leave TC2030 pin 3 as a no-connect and keep NRST on J6 (pin 3), which is routed.
  - SWD over J7 still works with a software or system reset (SYSRESETREQ).
  - Only "connect under reset" needs NRST; for that, use J6.
  - Edit: in `MCU.kicad_sch`, remove the NRST label or wire at J7 pin 3 and add a no-connect flag.
- (b) Layout, next run: rip the BT bundle at x 113-119, y 55-75 (BT_TX_IND, BT_RST_N, BT_MFB, BT_UART_RX/TX, BT_FORCE_PWM), then route NRST from the J7 north gap west of J7 on B.Cu down to the NRST copper south of U3 (C162/TP19), about 35 mm. This is not attempted, because it puts 6 routed BT nets at risk.
