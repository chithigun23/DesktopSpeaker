// Adds a separate "Candidate fixes" sheet (and CSV) for the TPS25730D/BQ25792 candidate fixes.
// Existing 'Selected BOM' rows are NOT modified; candidate rows replace/augment them at integration.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const name='Candidate fixes';
let sh; try{sh=wb.worksheets.getItem(name);}catch(e){sh=wb.worksheets.add(name);}
const head=['Reference (candidate)','Function','Manufacturer','MPN','LCSC part','Fitted qty','MOQ','Unit USD (tier)','Stock qty (2026-10-05 listing)','Footprint','Note'];
const L=(c)=>`https://www.lcsc.com/product-detail/${c}.html`;
const rows=[
['C2','TPS25730D CVBUS 4.7uF/50V X7R 1210 (was 1uF)','Samsung Electro-Mechanics','CL32B475KBUYNNE','C170099',1,5,0.1367,57880,'DesktopSpeaker:PD_C_1210','Alt: GRM32ER71H475KA88L C86052'],
['C6','TPS25730D CLDO_3V3 22uF/10V X7R 0805 (was 10uF)','Murata','GRM21BZ71A226ME15L','C907991',1,5,0.2543,132900,'DesktopSpeaker:PD_C_0805','Same MPN as SYS caps'],
['C113, C114, C115','BQ25792 VBUS/PMID/SYS 100nF/50V X7R 0402 bypass','Murata','GRM155R71H104KE14D','C77020',3,100,0.007,777000,'DesktopSpeaker:PD_C_0402 (new, ai-files/candidates/PD_C_0402.kicad_mod)','Replaces mismatched CL21B104KBCNNNC (0805)'],
['D7','TPS25730D VBUS-to-GND Schottky (TI 8.5)','Diodes Incorporated','1N5819HW-7-F','C82544',1,10,0.057,137330,'DesktopSpeaker:PD_D_SOD123','40V/1A SOD-123; IR max ~1 mA at 40V, lower at 20V; alt B5819W SL C8598'],
['R14, R15, R18','TPS25730D I2C SDA/SCL pull-ups to LDO_3V3 (R14,R15); pin 36 to GND (R18) 10k 1%','YAGEO','RC0603FR-0710KL','C98220',3,100,0.0034,7736700,'DesktopSpeaker:PD_R_0603',''],
['R16, R17, R103','TPS25730D PLUG_EVENT/SINK_EN 100k pull-ups (R16,R17); BQ25792 R103 CE pull-up now 100k (was 10k)','YAGEO','RC0603FR-07100KL','C14675',3,100,0.0026,7987300,'DesktopSpeaker:PD_R_0603','R103 stays in Selected BOM row "R103, R106" as 10k until integration'],
];
const data=[head,...rows.map(r=>[...r.slice(0,10),r[10]])];
sh.getRange(`A1:K${data.length}`).values=data;
sh.getRange('A9').values=[['Candidate-only rows; not in Selected BOM subtotals. Prices/stock are LCSC listing snapshots (2026-10-05). LCSC URL = https://www.lcsc.com/product-detail/<LCSC part>.html']];
const out=await SpreadsheetFile.exportXlsx(wb);await out.save(path);
const csv=data.map(r=>r.map(v=>`"${String(v??'').replaceAll('"','""')}"`).join(',')).join('\n')+'\n';
await fs.writeFile('ai-files/bom/candidate_fixes_BOM.csv',csv);
console.log('ok');
