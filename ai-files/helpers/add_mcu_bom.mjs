// Guarded: adds MCU-sheet parts (C160-C162, R160, J6) once; preserves all other rows.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx';
const csvPath='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sh=wb.worksheets.getItem('Selected BOM');
let last=0; for(let r=77;r<=120;r++){ if(sh.getRange(`A${r}`).values[0][0]!==null && sh.getRange(`A${r}`).values[0][0]!=='') last=r; }
const refs=sh.getRange('A11:A76').values.map(r=>String(r[0]));
if(refs.some(x=>x.includes('J6'))) throw new Error('already applied');
// shift notes block down by 2 rows (rows 77..last -> 79..last+2)
sh.getRange(`A${79}:S${last+2}`).copyFrom(sh.getRange(`A77:S${last}`),'all');
for(let r=77;r<=78;r++){ sh.getRange(`A${r}:S${r}`).copyFrom(sh.getRange('A76:S76'),'all'); sh.getRange(`A${r}:S${r}`).clear({applyTo:'contents'}); }
const end=78;
sh.getRange('A77:S77').values=[['C161','MCU VDD/VDDA 4.7uF bulk (DS12992 fig. 13)','Samsung Electro-Mechanics','CL10A475KO8NNNC','C19666',1,10,10,null,10,0.0298,null,null,138390,'Listing snapshot, 2026-10-06',46300,'2026-10-06','LCSC listing 4.7uF/16V X5R 0603; DC-bias derating at 3.0 V not checked.','https://www.lcsc.com/product-detail/C19666.html']];
sh.getRange('A78:S78').values=[['J6','MCU SWD header 1x5 2.54 mm','XYECONN','XY-MTP254-1X5','C54110162',1,10,10,null,10,0.0267,null,null,1830,'Listing snapshot, 2026-10-06',46300,'2026-10-06','1x5 straight THT header; footprint PinHeader_1x05_P2.54mm_Vertical (stock KiCad STEP). Pin order 1 SWDIO 2 SWCLK 3 NRST 4 3V_AO 5 GND.','https://www.lcsc.com/product-detail/C54110162.html']];
// Re-sync R10 and C182/C183 selections (present in the CSV from 2026-10-06 but missing in the XLSX).
for(let r=11;r<=76;r++){
  const a=String(sh.getRange(`A${r}`).values[0][0]);
  if(a==='R10') sh.getRange(`A${r}:S${r}`).values=[['R10','PD 200k 1% resistor','YAGEO','RC0603FR-07200KL','C105604',1,100,100,100,100,0.0024,0.0024,0.24,null,'Listing snapshot',46300,'2026-10-06','','https://www.lcsc.com/product-detail/C105604.html']];
  if(a==='C182, C183') sh.getRange(`A${r}:S${r}`).values=[['C182, C183','TPS25730D CC1/CC2 330pF C0G filters','Samsung Electro-Mechanics','CL10C331JB8NNNC','C1578',2,100,100,100,100,0.0089,0.0178,0.89,null,'Listing snapshot',46300,'2026-10-06','','https://www.lcsc.com/product-detail/C1578.html']];
}
// extend existing shared rows
for(let r=11;r<=76;r++){
  const d=String(sh.getRange(`D${r}`).values[0][0]);
  if(d==='CL10B104KB8NNNC'){ const a=String(sh.getRange(`A${r}`).values[0][0]); sh.getRange(`A${r}`).values=[[a+', C160, C162']]; sh.getRange(`F${r}`).values=[[Number(sh.getRange(`F${r}`).values[0][0])+2]]; }
  if(String(sh.getRange(`A${r}`).values[0][0])==='R152, R153, R154'){ sh.getRange(`A${r}`).values=[['R152, R153, R154, R160']]; sh.getRange(`B${r}`).values=[['100k EN / MODE / bleeder / BOOT0 pull-down resistors']]; sh.getRange(`F${r}`).values=[[4]]; }
}
for(let r=11;r<=end;r++){
 sh.getRange(`I${r}`).formulas=[[`=IF(OR(D${r}="",G${r}="",H${r}=""),"",IF(COUNTIF($D$11:D${r},D${r})>1,0,ROUNDUP(MAX(SUMIF($D$11:$D$${end},D${r},$F$11:$F$${end}),G${r})/H${r},0)*H${r}))`]];
 sh.getRange(`L${r}`).formulas=[[`=IF(K${r}="","",ROUND(F${r}*K${r},4))`]];
 sh.getRange(`M${r}`).formulas=[[`=IF(OR(K${r}="",I${r}="",N${r}=""),"",IF(N${r}>=I${r},ROUND(I${r}*K${r},4),""))`]];
}
sh.getRange('E4:E5').formulas=[[`=ROUND(SUM(L11:L${end}),2)`],[`=ROUND(SUM(M11:M${end}),2)`]];
const out=await SpreadsheetFile.exportXlsx(wb); await out.save(path);
// CSV: same layout as before (header + data rows)
const wb2=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const s2=wb2.worksheets.getItem('Selected BOM');
const rows=s2.getRange(`A10:S${end}`).values;
const q=v=>v===null||v===undefined||v===''?'':'"'+String(v).replace(/"/g,'""')+'"';
await fs.writeFile(csvPath, rows.map(r=>r.map(q).join(',')).join('\n')+'\n');
console.log('E4,E5', JSON.stringify(s2.getRange('E4:E5').values), 'rows', rows.length);
