# RT-8 schematic patch proposals (for the coordinator; not applied)

RT-8 did not edit any schematic. The board keeps every pad net of RT-7. The items below are nets that stay unrouted on RT-8 after honest attempts. Each one comes with the smallest schematic or placement change that would let the board close. Until the coordinator applies a patch, each such net still counts as one DRC unconnected item, and it appears on the "accepted unrouted" list in `ai-files/reports/routing-rt8.md`.

## P1. CHG_INT (U4-21 BQ25792 /INT to U3-5 PC15): make it not required

**Why it cannot be routed.** U4-21 sits between two things:
- the BAT_INT finger (zone edge x - y = 32.515) on its north and east sides;
- the PROG/BTST2/BATP fan-out on its south side.

A 0.5/0.2 fine via at the pin would come within 0.05 mm of PROG, and it would cut into the thinned BAT finger. BAT_INT is at 2.889 mOhm against a 2.9 mOhm budget. RT-7 searched with 4 million hr7 nodes and found no exit. RT-8 repeated the escape search from U4-21 with F/B/In2 and fine vias (`work-route8/t/jCI.log`); its result is recorded in the RT-8 report.

**Function without the wire.** The BQ25792 sets every INT cause in the status and flag registers:
- REG1B-REG1F: CHARGER_STATUS_0..4;
- REG20/21: FAULT_STATUS;
- REG22-REG27: the FLAG registers.

The charge policy (`ai-files/reports/charge-policy-2026-11-02.md`, section 3, and the CE gate in section 3, item 2) already runs the charger from the MCU over I2C (CTRL_SCL/CTRL_SDA). It also covers an MCU failure in hardware: CE defaults off and the charger watchdog is disabled. Firmware polls the status and flag registers instead of waiting on the INT edge:
- every 250 ms while a source is attached or a charge is running;
- every 2 s otherwise;
- the FLAG registers are clear-on-read, so a poll loses no events.

The cost is up to 250 ms of latency on charger events. Every event is already supervised by the charger itself (safety timer, TS, TREG), so this latency is not a safety path.

**Exact schematic edit (minimal, two ends):**

1. `DesktopSpeaker-kicad/Battery_Charger.kicad_sch`:
   - delete the local label `CHG_INT` at (198.12, 139.7) (uuid `0eff06d6-bebd-4b7d-9aad-90ee8b5ef5ae`), which is the label on the U4 pin-21 wire;
   - put a no-connect flag on U4 pin 21 (BQ25792 /INT is open drain, so leaving it unconnected is allowed);
   - delete the remote label `CHG_INT` at (381.0, 180.34) (uuid `0cbd59ef-...`) and the hierarchical label `CHG_INT` at (391.16, 180.34) (uuid `a4c33d60-...`).
2. `DesktopSpeaker-kicad/DesktopSpeaker.kicad_sch` (root):
   - delete the sheet pin `CHG_INT` of sheet Battery_Charger (219.71, 195.58) and its label at (224.79, 195.58);
   - delete the sheet pin `CHG_INT` of sheet MCU (320.04, 162.56) and its label at (314.96, 162.56).
3. `DesktopSpeaker-kicad/MCU.kicad_sch`:
   - delete the hierarchical label `CHG_INT` at (45.72, 87.63) (uuid `01baa7fc-...`);
   - leave U3 pin 5 (PC15) on its R106 10 k pull-up to 3V_AO, renamed by a local label such as `PC15_SPARE`. This follows AN5096: unused pins pulled up, and it keeps R106 on the board, so the BOM and the PCB do not change.
4. Update `ai-files/reports/mcu-pin-allocation.md`: PC15 becomes a spare input (EXTI no longer used). Then run ERC (expect 0 new errors) and update the PCB from the schematic. The only net change is that U4-21 leaves net CHG_INT. The RT-8 board needs no copper change: the R106-2 to U3-5 stub stays as it is.

The alternative, which keeps the wire, is a BAT_INT re-plan: widen the SYS/BAT finger elsewhere first to win copper margin, then place a CHG_INT via at the pin. That is a power-path redesign and was not attempted.

## P2. 3V_AO to R241 (AUX_TIPSW pull-up): give it a local always-on source, or keep the net and add a board lane

**Why it is open.** R241-1 at (188.42, 38.6) is 65-70 mm from the nearest 3V_AO copper (U3/J7). A two-leg search failed: leg 1 (R241 → In2 at (155.5, 61)) exhausted 6M nodes, and leg 2's start point is not routable (exp 0). The In2 islands USB_VBUS_IN2 and VBUS_PD_IN2 form a wall between x 135 and 153 from y 27 to y 130, so the path must change to B.Cu for about 18 mm.

**Minimal schematic option:** keep R241 but connect its top end to a 3V_AO test-pad pair, so a short F.Cu jumper wire can be fitted at assembly. This option is not recommended.

**Preferred option, no schematic change:** route a dedicated 0.3 mm B.Cu lane along y 56-58 under the U2 codec area (PWR_3V is exempt from BKO_CODEC). This needs about 2 mm of the codec's B.Cu GND pour; it is a layout task for RT-9.

## P3. Nets left open by RT-8 that need a placement change, not a schematic change

These are listed for completeness; the details are in the RT-8 report, section 6.
- **PDCTRL_SDA (U3-44).** The north escape row is limited by the foreign BT_AUDIO_L diagonal (x − y = 64.5) 2.5 mm north of the pin row. Only two of CODEC_PWR_EN, PDCTRL_SCL and PDCTRL_SDA fit.
  - Remedy: re-route BT_AUDIO_L along y 62.5 east of x 128.8 (audio net, length change under 1 mm).
  - Alternative: move U3 and its support parts 1.5 mm south.
- **NRST to J7-3.** The B.Cu/In2 space under the package is used by the N-S and E-W via-first nets. The J7 branch needs to reach pin 12 on the south row from the north.
  - Remedy: connect J7-3 to the NRST copper of the J6 branch with a B.Cu lane west of J7 (about 25 mm).
  - Alternative: swap the NRST and SWCLK pads on the TC2030 footprint. That is a footprint pin-map change and is not recommended.
