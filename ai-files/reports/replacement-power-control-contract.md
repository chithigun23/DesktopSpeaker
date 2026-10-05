# Replacement power-control contract

Implementation brief for TPS25730D/BQ25792 replacement,2026-10-05. This records required hardware defaults and register sequencing; it is not implemented or measured firmware. Datasheet sources: local BQ25792.pdf §§9.3.4.3,9.3.12,9.4 andREG06/REG14; TPS25730 interface/TRM; automatic-usb-source-policy.md.

## Hardware defaults

- CHG_SYS_ENABLE low through an external pull-down keeps Q101 asserting ILIM_HIZ; MCU reset/high impedance must stop input conversion.
- CHG_ENABLE low through an external pull-down leaves CE high and charge disabled independently of SYS conversion.
- Audio/codec/BT power enables default low. Battery-only SYS power is separate from enabling USB conversion.
- Physical SW101 interrupts protected-pack positive before BAT_PACK; external Q103 provides electronic battery disconnection in series. QON is a wake signal, not a load-current switch.

## Required startup ordering

1. Hold both charger enables low. USB_AUX supply may boot controller before SYS conversion. Establish reset/brownout state and valid logic rail before I2C.
2. Read BQ identity/status; keep CE disabled. Configure PROG-consistent1S profile, charge voltage/current, VSYSMIN and thermal/NTC limits. Nominal1A charging is provisional until the purchased pack is matched.
3. Set REG14 SFET_PRESENT=1 and read it back before requesting electronic ship mode. POR default0 locks ship-control fields. Do not mistake default idle SDRV behavior for configured ship control.
4. Disable charger watchdog or implement an explicit service/recovery policy; disable autonomous DPDM/ICO/HVDCP limit rewrites while host owns source permission. EN_IINDPM must remain enabled.
5. Establish source capability from an actual PD contract and cable/current limit, or validated BC1.2 classification. Non-PD Type-C Rp current is not documented through TPS25730 interfaces; use conservative fallback until separate classification is implemented. A5V fallback does not grant2A.
6. Budget TOTAL connector draw, including upstream PD/AUX/detection loads and charger input-limit tolerance. Program/read back source-specific IINDPM while HIZ remains asserted. If raising above the cached100mA clamp, clear EN_EXTILIM deliberately; its removal means there is no claimed independent analog ceiling.
7. Release CHG_SYS_ENABLE only after valid source/voltage/register readbacks and adequate power budget. Enable CE as a separate last step. Charge reduction precedes shedding audio load.

## Mandatory exceptional states

| Event | Required response |
|---|---|
| MCU reset/BOR | Hardware drops enables; restart full qualification. |
| Adapter detach or changed contract | Revoke current grant and reduce/disable input conversion before using the new grant; do not retain old limits. Battery supplement may keep SYS alive. |
| BQ REG_RST | Restore both gates low and repeat configuration; REG06IINDPM andREG14EN_EXTILIM reset. |
| Watchdog event | Re-read/reapply affected control bits; IINDPM andEN_EXTILIM do not simply reset onwatchdog, but other controls do. |
| Unknown/SDP source | No automatic2A/500mA grant. Leave HIZ asserted if whole-product conservative current cannot be enforced. |
| USB suspend | Shed input-powered audio/detection loads and enforce total suspend budget, includingPD/AUX; this is not solved by a100mA charger setting. |
| Electronic off onUSB | Disable audio/BT/codec and charge per plugged-in policy; ship mode alone does not guarantee USB SYS off. |

## Remaining hardware gates

BQ minimum programmed IINDPM100mA plus AUX/PD consumption does not establish a100mA total-host budget. PCM2902C advertises100mA; powering a battery-absent codec from SYS while holding conversion off can create a bootstrap deadlock. Complete either a bounded total-input limiter/bootstrap architecture or a carefully verified permitted low-current startup path; do not claim general battery-absent SDP audio support from the current draft. Dedicated D+/D− route selection and voltage-domain isolation remain required and are not captured yet. Interface ports reserve those functions without connecting unfinished audio/MCU blocks.

## Prototype evidence needed

Capture coldstart/no battery, depleted pack, input collapse/recontract, MCU reset, REG_RST, suspend/resume and ship/QON wake waveforms. Verify register readback/order and total connector current, not just IINDPM. Bench work is a release gate; no tests or USB compliance results are claimed here.
