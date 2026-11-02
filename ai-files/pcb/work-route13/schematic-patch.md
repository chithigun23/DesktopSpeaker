# RT-13 schematic-patch proposals (NOT applied)

Agent "RT-13 final automated routing round", 2026-11-03. Nothing here has been applied to `DesktopSpeaker-kicad/`.
Each item is the smallest schematic change that removes a connection the automated round could not route after
honest attempts (logs in `t/`). The owner decides; the layout alternative (GUI route) is given in
`ai-files/reports/routing-rt13.md` section 5 for every item.

## P1. TP20 (AMP_FAULT_N test point): delete it, or allow it to move

- Connection: TP20-1 (110.16, 149.65) to the AMP_FAULT_N copper at U6-9 / R262-2 (111.50, 124.95).
- Why it fails: TP20 sits south of BKO_U6 (x 95-125, y 114-144), between the U6 speaker-output inductors
  (L202 / L204) and the TP10 PVDD pad, over the In2 PVDD pour. Inside BKO_U6 only F.Cu is allowed for
  AMP_FAULT_N, and the U6 F.Cu side is full (PVDD, SPK_OUT, the I2S/I2C bundle). Router: 2.57 M nodes, no path
  (`t/p1/j_tp20.log`). TP20 is not in the movable list.
- Proposal (minimal): delete TP20 from the Amplifiers sheet. AMP_FAULT_N stays probe-able at R262-2, U3-25 and
  the new U3-25 -> U7-9 run (F.Cu, exposed at the U7 neck). No function is lost (TP20 has no other net).
- Alternative (no schematic change): allow TP20 to move into the free F.Cu area north of BKO_U6, e.g. near
  (112.5, 112.5), and connect it there to the AMP_FAULT_N route that will reach R262 (see P2 / GUI row).

## P2. R262 (AMP_FAULT_N pull-up at U6): allow a 2-3 mm move, or drop the U6-side pull-up

- Connection: R262-2 / U6-9 group to the rest of AMP_FAULT_N (now U3-25 + U7-9).
- Why it fails: R262 (RT-12 position (111.505, 124.35), -90) is boxed: LRCK vertical/diagonal west, R262-1 and its
  3V3_AUDIO stub north/east, C282 / U6-VR_DIG south-east, U6-9 south. A trace that leaves R262-2 must pass between
  the LRCK diagonal (x + y = 233.4) and the R262-1 pad corner; it needs x + y >= 234.32 for the 0.4 mm clock
  clearance and <= 234.12 for the pad clearance (no lane). R262 is not in the RT-13 movable list.
- Proposal A (layout, preferred): add R262 to the movable list; move it 2.5 mm north-east to about (113.6, 119.8)
  (free F.Cu between the LRCK y 117.0 run and C280-2), keep pin 1 on 3V3_AUDIO (via to the In2 3V3 track is
  allowed inside BKO_U6 for the PWR_3V class), and route U6-9 -> R262-2 on F.Cu north of the 3V3 stub.
- Proposal B (schematic): the TAS5825M FAULTZ pins of U6 and U7 are open-drain and already pulled up at the MCU
  side if the STM32 internal pull-up is enabled. Removing R262 and enabling the internal pull-up on U3-25 removes the
  boxed part; U6-9 would then be routed directly (still needs one F.Cu lane out of BKO_U6, the same as A).

## P3. ILIM_HIZ (U4-17 / R108-2 to Q101-3 / R109-1): no schematic change proposed

- The block is layout, not netlist: the ILIM pin column is fenced by SW2 (1.0 mm switch-node rule), the BTST2/PROG
  escapes and the TS_SENSE / U4-BATP B.Cu pair that runs 0.85-1.05 mm apart from U4 to x 164. See GUI row 13.
- If the owner prefers a netlist change: move the HIZ pull-down (Q101 + R109, sheet Battery_Charger) next to R108
  (about (156, 128)) and run the Q101 gate (Q101-G, a rule-21 slow net) instead of ILIM_HIZ across the board.
  That turns a fenced analogue pin net into a slow gate net that may use In2.
