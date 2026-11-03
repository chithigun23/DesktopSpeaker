# Battery pack RFQ (draft for the user to send; 1S4P version 2026-11-03, first draft 1S2P 2026-10-12)

Send to: Keeppower (keeppower.com.cn sales), CM Batteries (cmbatteries.com), or any pack assembler; see `sourcing-2026-10-12.md` section 4 for the candidates found (they were found for 1S2P; ask them for the 1S4P version below).

2026-11-03: the owner chose **1S4P** (4 x Samsung INR21700-50S, 20 Ah, about 72 Wh). Basis: `battery-4p-feasibility-2026-11-03.md` (sections 1.5, 2.4, 2.7, 2.8, 3.2), CAD v15 (`ai-files/cad/v15/`), `charge-policy-2026-11-02.md` section 12. Compared with the 1S2P draft, these items changed: cell count (1), protection with over-current trip window and per-cell fusing (2), NTC position (3), lead length (4), outline and PCM position (5), cell matching and welding (6), documents including UN38.3 (7). The 1S2P draft is kept at the end as history.

2026-11-03 (review fixes, `review-fixes-2026-11-03.md`; finding M5 and S5 of `project-review-cad-completeness-2026-11-03.md`): added **secondary protection** to item 2 (a 15 A fuse in PACK+ at the PCM output and a thermal cut-off of about 85 C on the cells), asked for the fuse/TCO part numbers in item 7, and reduced the **maximum thickness from 23.0 to 22.3 mm** (the usable thickness of the printed cradle; CAD v16 confirms the value). Lead length about 180 mm, the 1S4P cell spec, per-cell fusing, the dimensioned drawing and UN38.3 documents are unchanged. The 23.0 mm figure is superseded everywhere.

---
Subject: Quote request: 1S4P 21700 Li-ion pack, 20 Ah, with protection PCM, per-cell fusing, PACK+ fuse, thermal cut-off and NTC, qty 2-5 (prototype), ship to Australia

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

   **Secondary protection (required):**
   - **one 15 A fuse in PACK+** at the PCM output (for example a Littelfuse NANO2 453-series 0453015 15 A SMD fuse, or an equivalent with a higher breaking capacity). It must carry 10 A continuously and 20 A for 1 s without opening, and its **interrupting rating at 5 V DC must exceed the pack's short-circuit current** (several hundred amperes for a 4P 21700 brick); please send its time-current curve and interrupting rating;
   - **one thermal cut-off (TCO) or resettable thermal mini-breaker of about 85 C**, in thermal contact with the cells and in series with PACK+ (for example a Bourns/Komatsulite NR85AB0 high-current A-type mini-breaker, 85 +-5 C, or equivalent), rated for at least 15 A DC breaking, with a **hold (non-trip) current of at least 10 A at 45 C ambient** (bimetal breakers also trip on self-heating);
   - please state the part numbers and ratings of both. If you cannot fit them inside the pack, tell me; I will then fit an inline 15 A fuse in the PACK+ lead myself.
3. **Thermistor:** one 10 kOhm NTC at 25 C, B25/85 about 3435 K (103AT-2 type), **glued between the two middle cells at mid-length**. Bring it out on its own lead (the charger reads it directly).
4. **Leads and connector:** three wires leaving the PCM top edge: 18 AWG for PACK+ and PACK- (**thin-wall insulation, outside diameter 1.7 mm or less**, so the Micro-Fit 43030-0038 crimp, rated for insulation up to 1.85 mm, closes on it), 24-26 AWG for the NTC, **about 180 mm long**. Terminate them in a Molex Micro-Fit 3.0 receptacle housing 43645-0300 (genuine Molex, please) with female crimp terminals: 43030-0038 (18 AWG) for the power leads and 43030-0007 (24 AWG) for the NTC lead.
   - Pin 1 = PACK+, pin 2 = NTC, pin 3 = PACK-.
   - The NTC's other end is tied to PACK- inside the pack.
5. **Outline:** four cells side by side in one row (axes parallel), PCM across the **positive end**.
   - **Maximum 87.0 x 75.0 x 22.3 mm** (across the four cells x along the cell axis including the PCM x thickness), including heat-shrink wrap, insulation rings, the PCM, the fuse and the thermal cut-off. **The 22.3 mm thickness is a hard limit**: the pack sits in a printed cradle between the drivers and an internal wall.
   - Please send a dimensioned drawing with the quote, including the PCM position, the fuse and TCO positions and the lead exit.
6. **Cell matching and assembly:**
   - all four cells of the same model and production lot, matched in capacity (within about 2 %) and DC resistance (within about 1 mOhm);
   - every cell within 10 mV open-circuit voltage before the first weld;
   - spot-welded 0.15-0.2 mm pure nickel; no soldering on the cans;
   - insulation ring on each positive end; fish paper at the ends; heat-shrink overall.
7. **Documents and compliance:** cell datasheet (with mass), PCM specification (part number and all cut-off values and delays), the per-cell fusing method, the PACK+ fuse and thermal cut-off part numbers and ratings, a dimensioned drawing, a UN38.3 test summary for this pack, an MSDS, and the shipping method you use for lithium batteries to Australia.

Thank you.
---

Notes for the user
- The charger TS network on the board is designed for a 10 k NTC with B about 3435 K; a different beta changes the charge-temperature window (handover, TS divider; `charge-policy-2026-11-02.md` section 2.6).
- J5 on the board is Molex 43650-0300 (pins 1 PACK+, 2 TS, 3 GND). The local datasheet is an LXW H3000S14 clone drawing rated 5 A; the genuine Molex part is listed at 8.5 A per contact [UNVERIFIED]. Order genuine Molex housings and crimps for J5 and its mate (buy list lines 7-8).
- Why 12-20 A: the lower limit sits above the BQ25792 9.3 A battery OCP and the 8 A amplifier-boost peaks. The upper limit is what J5 and the 18 AWG harness can carry for the trip time. A "4P" PCM advertised for 20-30 A is acceptable only if its trip point is inside this window.
- Why per-cell fusing: with four cells in parallel, three healthy cells feed an internal short in the fourth. Many consumer 1S packs omit the links, so ask explicitly.
- Why the 15 A fuse and the 85 C cut-off (2026-11-03 review, M5): a 4P 21700 brick can source far more than 100 A. If the PCM MOSFETs fail short, nothing else in the pack limits the current; the board side has only the BQ25792 battery OCP (9.3 A) and no fuse. 15 A sits above the 8.5 A amplifier peaks and the 9.3 A board limit, inside the 12-20 A PCM window, and below what J5 (8.5 A per contact genuine, UNVERIFIED) and the 18 AWG leads survive for a fuse clearing time. Fallback if the vendor declines: an inline 15 A mini-blade holder in the PACK+ lead (the 180 mm lead has about 49 mm of slack over the 131 mm CAD route); the buy list carries it as an optional line.
- Why 22.3 mm (2026-11-03 review, S5): the cradle arcs are cut for the 21.75 mm modelled brick with 0.275 mm radial clearance, so the usable thickness is about 22.3 mm. A 23.0 mm pack would sit about 1.3 mm higher and looser and cut the clearance under the ND65 magnets from 5.29 to about 4 mm. Re-cut the cradle from the vendor drawing before printing.
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
