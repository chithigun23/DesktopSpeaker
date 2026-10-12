# Battery pack RFQ (draft for the user to send, 2026-10-12)

Send to: Keeppower (keeppower.com.cn sales), CM Batteries (cmbatteries.com), or any pack assembler; see `sourcing-2026-10-12.md` section 4 for the candidates found.

---
Subject: Quote request: 1S2P 21700 Li-ion pack, 10 Ah, with protection PCM and NTC, qty 2-5 (prototype), ship to Australia

Hello,

I need a custom 1S2P lithium-ion pack for a portable desktop speaker prototype. Please quote 2 and 5 pieces, with lead time and shipping to Australia (postcode on request), and tell me which of the items below you cannot meet.

1. Cells: 2 x 21700, 5000 mAh each, high-rate type (Samsung INR21700-50S preferred; Molicel P45B or equivalent acceptable), matched, parallel (1S2P, 3.6 V nominal, 10 Ah).
2. Protection board (PCM/BMS) on the pack: over-charge 4.25 V, over-discharge 2.5-2.8 V, over-current with continuous discharge rating 10 A or more (peak 20 A for 1 s), charge current up to 5 A, short-circuit protection, low self-consumption (below 10 uA in storage). No fuel gauge needed (the product has its own).
3. Thermistor: 10 kOhm NTC at 25 C, B25/85 about 3435 K (103AT-2 type), glued to a cell and brought out on its own lead (the charger reads it directly).
4. Leads and connector: three wires, 18 AWG for PACK+ and PACK-, 24-26 AWG for the NTC, 230 mm long (the harness route inside the enclosure is about 230 mm), terminated in a Molex Micro-Fit 3.0 receptacle housing 43645-0300 with female crimp terminals 43030-0038 (18 AWG) for the power leads and 43030-0007 (24 AWG) for the NTC lead, pin 1 = PACK+, pin 2 = NTC, pin 3 = PACK- (the NTC's other end is tied to PACK- inside the pack).
5. Outline: cells side by side, PCM at one end; maximum 73 x 44 x 22 mm including heat-shrink wrap. Please send a dimensioned drawing with the quote.
6. Labels and compliance: cell datasheet, PCM specification (part number and cut-off values), UN38.3 test summary if available, and the shipping method you use for lithium batteries to Australia.

Thank you.
---

Notes for the user
- The charger TS network on the board is designed for a 10 k NTC with B about 3435 K; a different beta changes the charge-temperature window (handover, TS divider).
- J5 on the board is Molex 43650-0300 (pins 1 PACK+, 2 TS, 3 GND); the mating housing 43645-0300 and crimps are not in the BOM yet.
- Enclosure cradle assumes bare-cell diameter 21.7 plus a 0.3 mm gap; a wrapped pack of 44 mm width still fits (see `cad-v11-print-ready.md`, pack section).
