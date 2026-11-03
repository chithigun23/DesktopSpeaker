# Battery pack RFQ (draft for the user to send; 1S4P version 2026-11-03, first draft 1S2P 2026-10-12)

Send to: Keeppower (keeppower.com.cn sales), CM Batteries (cmbatteries.com), or any pack assembler; see `sourcing-2026-10-12.md` section 4 for the candidates found (they were found for 1S2P; ask them for the 1S4P version below).

2026-11-03: the owner chose **1S4P** (4 x Samsung INR21700-50S, 20 Ah, about 72 Wh). Basis: `battery-4p-feasibility-2026-11-03.md` (sections 1.5, 2.4, 2.7, 2.8, 3.2), CAD v15 (`ai-files/cad/v15/`), `charge-policy-2026-11-02.md` section 12. Compared with the 1S2P draft, these items changed: cell count (1), protection with over-current trip window and per-cell fusing (2), NTC position (3), lead length (4), outline and PCM position (5), cell matching and welding (6), documents including UN38.3 (7). The 1S2P draft is kept at the end as history.

---
Subject: Quote request: 1S4P 21700 Li-ion pack, 20 Ah, with protection PCM, per-cell fusing and NTC, qty 2-5 (prototype), ship to Australia

Hello,

I need a custom 1S4P lithium-ion pack for a portable desktop speaker prototype. Please quote 2 and 5 pieces, with lead time and shipping to Australia (postcode on request), and tell me which of the items below you cannot meet.

1. **Cells:** 4 x 21700, 5000 mAh each, high-rate type (Samsung INR21700-50S preferred; Molicel P45B or equivalent acceptable), all four connected in parallel: 1S4P, 3.6 V nominal, 20 Ah, about 72 Wh.
2. **Protection board (PCM/BMS)** on the pack:
   - over-charge 4.25 V; over-discharge 2.5-2.8 V;
   - continuous discharge 10 A or more, 20 A for 1 s;
   - **discharge over-current trip between 12 A and 20 A**, with a delay of 10 ms or more (please state the trip value and delay; a board that trips above 20 A is not acceptable);
   - charge current limit 5 A or more;
   - short-circuit protection; self-consumption below 10 uA in storage.

   No fuel gauge is needed (the product has its own). Please also fit **per-cell fusing**: a fusible nickel link (slotted strip) or fuse wire on the positive end of each cell. Please state how it is made and its rating.
3. **Thermistor:** one 10 kOhm NTC at 25 C, B25/85 about 3435 K (103AT-2 type), **glued between the two middle cells at mid-length**. Bring it out on its own lead (the charger reads it directly).
4. **Leads and connector:** three wires leaving the PCM top edge: 18 AWG for PACK+ and PACK-, 24-26 AWG for the NTC, **about 180 mm long**. Terminate them in a Molex Micro-Fit 3.0 receptacle housing 43645-0300 (genuine Molex, please) with female crimp terminals: 43030-0038 (18 AWG) for the power leads and 43030-0007 (24 AWG) for the NTC lead.
   - Pin 1 = PACK+, pin 2 = NTC, pin 3 = PACK-.
   - The NTC's other end is tied to PACK- inside the pack.
5. **Outline:** four cells side by side in one row (axes parallel), PCM across the **positive end**.
   - **Maximum 87.0 x 75.0 x 23.0 mm** (across the four cells x along the cell axis including the PCM x thickness), including heat-shrink wrap, insulation rings and the PCM.
   - Please send a dimensioned drawing with the quote, including the PCM position and the lead exit.
6. **Cell matching and assembly:**
   - all four cells of the same model and production lot, matched in capacity (within about 2 %) and DC resistance (within about 1 mOhm);
   - every cell within 10 mV open-circuit voltage before the first weld;
   - spot-welded 0.15-0.2 mm pure nickel; no soldering on the cans;
   - insulation ring on each positive end; fish paper at the ends; heat-shrink overall.
7. **Documents and compliance:** cell datasheet (with mass), PCM specification (part number and all cut-off values and delays), the fusing method, a UN38.3 test summary for this pack, an MSDS, and the shipping method you use for lithium batteries to Australia.

Thank you.
---

Notes for the user
- The charger TS network on the board is designed for a 10 k NTC with B about 3435 K; a different beta changes the charge-temperature window (handover, TS divider; `charge-policy-2026-11-02.md` section 2.6).
- J5 on the board is Molex 43650-0300 (pins 1 PACK+, 2 TS, 3 GND). The local datasheet is an LXW H3000S14 clone drawing rated 5 A; the genuine Molex part is listed at 8.5 A per contact [UNVERIFIED]. Order genuine Molex housings and crimps for J5 and its mate (buy list lines 7-8).
- Why 12-20 A: the lower limit sits above the BQ25792 9.3 A battery OCP and the 8 A amplifier-boost peaks. The upper limit is what J5 and the 18 AWG harness can carry for the trip time. A "4P" PCM advertised for 20-30 A is acceptable only if its trip point is inside this window.
- Why per-cell fusing: with four cells in parallel, three healthy cells feed an internal short in the fourth. Many consumer 1S packs omit the links, so ask explicitly.
- Enclosure: the CAD v15 cradle takes 87.4 x 75.7 mm in plan (cells on a 21.7 mm pitch). The PCM sits at the rear end, 1.0 mm from the woofer-chamber partition, which is the rear stop. The J5 leads are routed in CAD v15 at about 131 mm (out of the PCM top edge through a wrap slit, pads about 3 mm apart), so 180 mm leaves slack. A hook-and-loop strap of at least 350 mm holds the brick (buy list line 24).
- Shipping: 72 Wh nominal is below the 100 Wh airline limit, but UN38.3 documents are still required to ship it.
- Cost: no price yet. The buy-list pack line is a placeholder, outside every subtotal.

---

## History: 1S2P draft (2026-10-12, superseded 2026-11-03)

Subject: Quote request: 1S2P 21700 Li-ion pack, 10 Ah, with protection PCM and NTC, qty 2-5 (prototype), ship to Australia

1. Cells: 2 x 21700, 5000 mAh each, high-rate type (Samsung INR21700-50S preferred; Molicel P45B or equivalent acceptable), matched, parallel (1S2P, 3.6 V nominal, 10 Ah).
2. Protection board (PCM/BMS) on the pack: over-charge 4.25 V, over-discharge 2.5-2.8 V, over-current with continuous discharge rating 10 A or more (peak 20 A for 1 s), charge current up to 5 A, short-circuit protection, low self-consumption (below 10 uA in storage). No fuel gauge needed (the product has its own).
3. Thermistor: 10 kOhm NTC at 25 C, B25/85 about 3435 K (103AT-2 type), glued to a cell and brought out on its own lead (the charger reads it directly).
4. Leads and connector: three wires, 18 AWG for PACK+ and PACK-, 24-26 AWG for the NTC, 230 mm long (the harness route inside the enclosure is about 230 mm), terminated in a Molex Micro-Fit 3.0 receptacle housing 43645-0300 with female crimp terminals 43030-0038 (18 AWG) for the power leads and 43030-0007 (24 AWG) for the NTC lead, pin 1 = PACK+, pin 2 = NTC, pin 3 = PACK- (the NTC's other end is tied to PACK- inside the pack).
5. Outline: cells side by side, PCM at one end; maximum 73 x 44 x 22 mm including heat-shrink wrap. Please send a dimensioned drawing with the quote.
6. Labels and compliance: cell datasheet, PCM specification (part number and cut-off values), UN38.3 test summary if available, and the shipping method you use for lithium batteries to Australia.

Notes at the time: the TS network expects a 10 k / B 3435 NTC; J5 is Molex 43650-0300 (pins 1 PACK+, 2 TS, 3 GND) and its mating housing and crimps were not yet in the BOM; the cradle assumed bare-cell diameter 21.7 plus a 0.3 mm gap, and a wrapped 44 mm wide pack still fitted (`cad-v11-print-ready.md`, pack section).
