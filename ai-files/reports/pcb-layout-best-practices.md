# PCB layout best practices: DesktopSpeaker checklists (2026-10-07)

Short checklists for reviewing and routing this board. Each one is taken from the datasheet or app-note layout sections listed with it. (DS) = vendor datasheet text. (AN) = application note. (rule) = this project's own number, not a vendor limit. Local datasheets live in `ai-files/datasheets/`. The longer project rules are in `pcb-layout-rules-audio.md`, and this file does not repeat them.

## 1. Boost converter TPS61088 (U25): hot loop
- **Output capacitor first (AN SLVA773 step 1).** In a boost the high di/dt loop is on the output side: low-side FET, then the synchronous FET, then VOUT, then Cout, then PGND. Place low-ESR ceramics (DS: 22-100 uF) right at VOUT/PGND with short, wide copper on the same layer. A bulk or polymer cap may sit farther away and be reached through vias, but only in addition to the local ceramics.
- Put the inductor next to SW. Keep the SW copper as small as the current allows. Keep FB/COMP/ILIM/SS parts and traces away from SW and never route them parallel to it (AN step 2/4, DS 11.1: "minimize the length and area of all traces connected to the SW pin").
- Place the input cap close to VIN and GND. Its ground, Cout's ground and the IC PGND together form the power ground. The VIN pin itself may be fed through a via, because its current is small (AN step 3, DS).
- Join signal ground (AGND, FB/COMP returns) to power ground at one point near PGND. No power current may flow through the signal ground (AN step 5).
- Solder the thermal pad to a large ground area with thermal vias under it (DS 11.1). Use as much GND copper as possible on the inner and bottom layers.
- One via per amp when a power path has to change layer (AN step 1).
- Sources: TI SLVA773 https://www.ti.com/lit/pdf/slva773 ; TPS61088 layout guidelines https://www.ti.com/document-viewer/TPS61088-Q1/datasheet/layout-guidelines-slvse528754 ; local `datasheets/tps61088-layout-excerpt.txt`.

## 2. Buck-boost charger BQ25792 (U4) (DS sec. 12, priority order)
1. SYS caps first, then PMID, then VBUS, each with a **0.1 uF 0402/0201 closer than the 10 uF**. Make every cap-to-pin and cap-to-GND connection on the **top layer**, as a small loop.
2. Inductor terminals as close to SW1/SW2 as possible. Use the **minimum SW copper area** that still carries the inductor current, and keep parasitic capacitance to other copper low. SW nodes do not go on inner or bottom layers (rule, from the DS intent).
3. REGN and bootstrap caps next to the IC with the shortest traces. BAT caps close to BAT and GND.
4. Thermal vias directly under the power FETs. Size via count to current.
5. **Route BATP away from SW1/SW2.**
- Source: local `datasheets/BQ25792.txt` lines 6886-6936, and the BQ25798EVM (BMS034) layout.

## 3. USB-C PD sink TPS25730D (U11) and high-current USB-C
- VBUS pours with at least 6 vias (0.2 mm hole / 0.4 mm pad, DS) top to bottom. VBUS_IN and PPHV need at least 15 such vias.
- CC caps on the same side as the IC and close to CC1/CC2. No via between the CC pin and its cap: the via comes after the cap.
- Do not connect the bottom DRAIN pads. Keep the high-speed data path simple.
- Connector practice (rule): tie all four VBUS pins and all four GND pins with wide copper at the connector. Put the TVS within a few mm of the connector with a short GND. Put CC/D+/D- ESD at the connector. Run VBUS as a pour, not a track: at 3 A on 1 oz outer copper this means at least 1.4 mm for a 10 K rise (IPC-2221) and much wider on 0.5 oz inner layers.
- Sources: local `datasheets/TPS25730.txt` sec. 9.4, `TPS25730EVM_Users_Guide.pdf`, `USB_TypeC_Spec_R2.0_2019.pdf`.

## 4. USB 2.0 data (J1 to PCM2902C U2; full speed)
- 90 ohm differential +-10-15 %, routed as a **coupled pair** on one layer next to a solid GND plane. Never route over a plane split or slot.
- No stubs. Test points go in series and symmetric. The USB-C A6/B6 and A7/B7 bridges stay at the connector and as short as possible.
- Keep vias to a minimum, and add any via to both lines. Match lengths (rule 0.5 mm here; USB 2.0 HS commonly 1.25 mm, so FS is tolerant).
- Place ESD at the connector and series resistors at the device.
- Keep the pair at least 3x its gap from other signals, with GND stitching on both sides.
- Sources: https://embeddedhardwaredesign.com/usb2-0-pcb-layout-guidelines/ ; TI TUSB4041 layout section (USB2 rules, via alldatasheet mirror); PL2561 guideline https://www.prolific.com.tw/wp-content/uploads/2025/07/PL2561_PCB-Layout-Guideline_v1.1.pdf

## 5. Class-D amplifiers TAS5825M (U6, U7) and LC output filter
- PVDD small bypass caps (0.1/1 uF) **no farther from the PVDD pins than in the DS layout example**. Farther caps cause output ringing that can exceed abs-max and damage the device (DS 12.1.2). Each device gets its own set. Place at least 22 uF low-ESL bulk near each device.
- BST caps directly at the BST/OUT pins. DVDD/AVDD/GVDD/VR_DIG caps close (DS 12.1).
- Thermal (DS 12.1.3): pad no smaller than the package addendum, via array per the addendum or denser, **no thermal relief on thermal vias**, vias in columns radiating outward, and contiguous ground copper from the ground pins. Keep away from the board edge and other heat sources. Route traces perpendicular to the device. Passives point their narrow end toward the IC. Use a 70-80 % aperture array stencil.
- Output filter (TI TPA31xx layout pages, same physics): keep the loop OUT pin -> inductor/ferrite -> filter cap -> PGND **as small as possible**, because its area sets how well it radiates. Place the filter close to the outputs and ground the caps to power ground near the amp. Join AGND and PGND at the thermal pad as a star.
- Pre-filter OUT nodes are switch nodes: short (rule <= 3 mm to the inductor), wide, top layer, no vias, solid GND beneath.
- Sources: local `datasheets/TAS5825M.txt` sec. 12 ; https://www.ti.com/document-viewer/lit/html/SLOS528F/layout ; https://www.ti.com/document-viewer/TPA3112D1/datasheet/layout

## 6. Audio ADC PCM1862 (U24), USB codec PCM2902C (U2), mixed-signal ground
- One common ground plane, no AGND/DGND split. Partition by placement: analog pins and lines away from digital ones. Digital return currents (clocks) must stay away from AGND and the inputs (PCM1862 DS 12.1/12.1.1).
- Decoupling caps **on the same layer as the device with no vias between cap and pin** (PCM1862 DS).
- Ground pour or traces between input traces for crosstalk (PCM1862 DS).
- PCM2902C: tie AGNDC/AGNDP/AGNDX/DGND/DGNDU to the one plane at the device, within 0.1 V of each other. Decouple VDDI. Keep the crystal short with its ground at AGNDX (DS).
- Crystals (ST AN2867 general rules): crystal and load caps within a few mm of the XI/XO pins, F.Cu only, no vias, a GND guard around them, no other signal under or beside them.
- Sources: local `datasheets/PCM1862.txt` sec. 12, `PCM2902C.txt`; ST AN2867 https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm8afals-stm32-mcus-and-mpus-stmicroelectronics.pdf

## 7. I2S / clocks
- Short and point to point. Series resistor of 22-33 ohm at the source. Route on the top layer over solid GND with a guard or at least 3x spacing. Never run parallel to analog lines, and keep at least 5 mm away (rule). Avoid vias. Keep away from switch nodes and inductors. Test points go in line, not as long stubs.
- Source: project rule set `pcb-layout-rules-audio.md` sec. 2; PCM1862 DS partitioning.

## 8. STM32G071 (U3)
- 100 nF at each VDD pin plus 4.7 uF bulk. VDDA/VREF+ 100 nF + 1 uF. GND via at each cap (ST AN5096 sec. 5.4, DS power scheme).
- NRST: 100 nF to GND close to the pin (10 nF allowed for low standby current) to stop parasitic resets (AN5096).
- BOOT0 shares PA14-BOOT0 with SWCLK on G0. The SWD header connects directly. Keep SWD traces short and away from switch nodes.
- Pull up, pull down or drive every unused pin (AN5096).
- Sources: https://www.st.com.cn/resource/zh/application_note/an5096-getting-started-with-stm32g0-mcus-hardware-development-stmicroelectronics.pdf ; local `datasheets/STM32G071x8_xB.txt`.

## 9. BM83 Bluetooth module (U1)
- No copper on **any** layer under the antenna (keep-out figure 7-4). The antenna must not be surrounded by ground. Keep external metal at least 15 mm from the antenna. Best placement is at the board edge or overhanging it.
- Continuous GND plane at least the size of the module (32 x 15 mm) directly under it (FCC/ISED condition). **No trace routing on the top layer under the module.** Stitch ground vias around the module (rule <= 3 mm near RF).
- Sources: local `datasheets/BM83_Bluetooth_Stereo_Audio_Module.txt` ch. 7.2.

## 10. Thermal, current and vias
- Trace width from IPC-2221 (external k 0.048, internal k 0.024): 1 oz outer at a 10 K rise needs about 0.3 mm for 1 A, 1.4 mm for 3 A, 3.6 mm for 6 A, 6.2 mm for 9 A. The JLC default 0.5 oz inner layer needs about 2.5x the outer width. For anything above about 2 A, use pours, not tracks.
- Via current: a 0.3 mm via carries about 1 A and a 0.4 mm via about 1.5-2 A (rule). Use arrays.
- Thermal pads: vias with no relief, connected to inner and bottom copper areas kept free of signal tracks.
- Sources: IPC-2221 formula (no free primary link; standard); TI SLVA773 (1 via per amp).

## 11. JLC 4-layer manufacturability
- 1 oz outer: minimum track and space 0.10/0.10 mm. Minimum via drill 0.15 mm (0.2-0.3 mm preferred). Annular ring >= 0.15-0.2 mm. Hole to hole 0.2 mm (vias).
- Via-in-pad: unfilled vias in SMD pads wick solder, which causes opens, voids and tombstoning, and is worse for hand-soldered 0402s. JLC makes **POFV (epoxy-filled, plated over) free only on 6-20 layer boards**. On 4 layers it is a paid option you must request. Otherwise put the via beside the pad on a short trace (dogbone).
- Tent vias. Keep silk off pads. Teardrops on track-to-pad and track-to-via joints (KiCad Edit > Teardrops, GUI only in 10.0.6).
- Sources: https://jlcpcb.com/capabilities/pcb-capabilities ; https://jlcpcb.com/blog/Free-Via-in-Pad-on-6-20-Layer-PCBs-with-POFV ; https://www.lcsc.com/blog/qfn-pcb-layout-guide/ ; KiCad 10 manual https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html

## 12. General routing hygiene (review checklist)
- No acute (< 90 degree) joints. Avoid 90 degree joints on power and RF nets. Remove micro-segment staircases. Make every stub intentional.
- Every signal on F.Cu has unbroken In1 GND below it. Look for slots formed by merged antipads of via rows. B.Cu/In2 signals need a nearby reference plane too.
- Keep inner power-island layers for planes. Signals must not cut islands into fragments.
- Rule relaxations must be narrow, by area or courtyard and never by width alone, and each one needs a recorded reason.
