# Gauge undervoltage isolation proposal

Status: candidate only; root owns integration. No active schematic, root hierarchy, shared libraries or BOM changed.

## Recommended circuit

- U21: **TPS3839G33DBZR**, TI, LCSC **C485802**, DBZ/SOT-23-3. TI datasheet Rev. D pin map: pin 1 GND, pin 2 active-low push-pull RESET, pin 3 VDD. G33 is nominal 3.08 V, guaranteed falling threshold 3.003–3.126 V. Suffixes matter: K33 is 2.93 V; L30 is 2.63 V.
- U21 VDD from BAT_PACK after pack switch SW101, GND to board GND; C126 100 nF directly from VDD to GND. TPS3839 supply current is 150 nA typical / 500 nA maximum. RESET is specified valid for VDD >0.6 V; below 0.6 V its state is undefined.
- Keep U13/U16/U17 TS5A3167 VCC pin 5 on 3V_AO. Tie active-low IN pin 4 together as `GAUGE_SW_EN_N`; R126=1 MΩ from 3V_AO to this node. This defaults the switches off while AO is absent or ramping.
- Q104: existing project **2N7002** device; drain to `GAUGE_SW_EN_N`, source to GND, gate from U21 RESET pin 2. R127=1 MΩ gate-to-source pulldown. Above the supervisor threshold, RESET high turns Q104 on and pulls the switch IN pins low. Below threshold, RESET low releases the node and R126 turns the signal switches off. R127 draws 3–4.2 µA from BAT_PACK while the pack is connected (36.8 mAh/year at 4.2 V, 0.37% of a 10 Ah pack); this is removed by opening physical pack switch SW101. A 10 MΩ alternative reduces connected-pack draw but gives weaker default-off behavior while RESET is undefined below 0.6 V, so it is not the recommendation.
- If BAT is absent and USB/AO is live, supervisor RESET is valid low down to 0.6 V. Below that its state is undefined, but it is powered from BAT and cannot be driven above the BAT domain. The Nexperia 2N7002 has minimum VGS(th)=1.0 V at 25°C, and R127 biases Q104 toward ground; verify powered-off startup in hardware. With AO off while BAT is present, the supervisor may keep Q104 on, but TS5A3167 VCC, AO-side pullups, and IN all sit at 0 V. MAX17048-side SCL/SDA are inputs and ALRT is open drain; confirm these NC-side nets have no other BAT-powered pullups in the integrated schematic.

## Threshold, drive, and qualification

MAX17048 electrical characteristics specify VDD 2.5–4.5 V. G33's minimum falling threshold is 3.003 V, 503 mV above the gauge's minimum supply. TPS3839 Rev. D guarantees RESET VOH ≥ VDD−0.4 V for VDD=1.2–3.3 V at 0.5 mA. At the minimum G33 threshold this gives 2.603 V RESET high. Nexperia specifies 2N7002 VGS(th) max 2.5 V at Tj=25°C, so the room-temperature nominal-static margin is 103 mV. R127's 1 MΩ load is only ~3 µA at this voltage, far below the supervisor's VOH test load.

Cold drive is not fully guaranteed by those limits: Nexperia lists a 2.75 V maximum threshold at Tj=−55°C, and does not state a maximum at the supervisor's −40°C operating endpoint. Treat this combination as a nominal-temperature prototype choice pending reset/gate qualification across the intended temperature range, or replace Q104 with a device whose minimum threshold remains above 0.6 V while its maximum threshold is comfortably below the worst-case RESET high. Nexperia specifies gate leakage max 100 nA at ±15 V, 25°C; a stronger pull-down also improves the below-0.6-V undefined-output state.

The reset delay is 120–350 ms after voltage recovers above threshold plus hysteresis; falling propagation delay is 20 µs. Validate battery collapse/ripple and gauge restart timing. The cutoff isolates the measurement signals; it does not cut the system battery rail.

R126=1 MΩ costs approximately 3 µA from 3V_AO while enabled, plus TS input leakage. Add this and supervisor current to the low-power budget. AO-off behavior relies on TS5A3167 powered-off isolation. The circuit has no BAT-to-AO sensing or logic input.

## Candidate assets

- `TPS3839G33DBZR.kicad_sym`: individual candidate symbol; coordinates match root helper: VDD3 at (0,+7.62), GND1 at (0,-7.62), RESET2 at (+10.16,0), body ±7.62×±5.08 mm.
- `TPS3839G33DBZR.kicad_mod`: individual DBZ SOT-23-3 footprint. TI DBZ pin map agrees with standard SOT-23: pad 1 upper-left, pad 2 lower-left, pad 3 right-center.
- `TPS3839G33DBZ_SOT23.step`: generic SOT-23 model copied from the project's 2N7002 model; not a TI-specific model. The footprint points to this candidate-local model. Move under flat active `3d` folder and update model path only if root activates the candidate.
- Q104 uses existing project 2N7002 assets.

Sources: [Nexperia 2N7002 datasheet Rev. 7 §7](https://assets.nexperia.com/documents/data-sheet/2N7002.pdf); [TI TPS383x datasheet Rev. D §§5–7, 8.1, 9.2](https://www.ti.com/lit/ds/symlink/tps3839.pdf); [TI G33DBZR product page](https://www.ti.com/product/TPS3839/part-details/TPS3839G33DBZR); [LCSC C485802 listing](https://www.lcsc.com/product-detail/C485802.html).
