// Guarded: adds USB_Audio sheet parts (R170-R176, C170-C178, C186/C187, Y170) once; preserves other rows.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx';
const csvPath='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sh=wb.worksheets.getItem('Selected BOM');
let last=0; for(let r=79;r<=130;r++){ const v=sh.getRange(`A${r}`).values[0][0]; if(v!==null&&v!=='') last=r; }
const refs=sh.getRange('A11:A78').values.map(r=>String(r[0]));
if(refs.some(x=>x.includes('Y170'))) throw new Error('already applied');
const N=5;
sh.getRange(`A${79+N}:S${last+N}`).copyFrom(sh.getRange(`A79:S${last}`),'all');
for(let r=79;r<79+N;r++){ sh.getRange(`A${r}:S${r}`).copyFrom(sh.getRange('A78:S78'),'all'); sh.getRange(`A${r}:S${r}`).clear({applyTo:'contents'}); }
const end=78+N;
const note='USB_Audio sheet, 2026-10-06; price/stock unverified unless stated.';
const rows=[
 ['Y170','12 MHz crystal for PCM2902C (3225-4P, CL 20 pF, +/-10 ppm)','YXC','X322512MSB4SI','C9002',1,10,10,null,10,0.0371,null,null,312110,'Listing snapshot, 2026-10-06',46300,'2026-10-06','Search-result snapshot; datasheet not retrieved. Pads 1/3 crystal, 2/4 GND assumed (generic 3225-4P) - verify. 22 pF load caps give ~14 pF CL, below the 20 pF rating: tune at bring-up.','https://www.lcsc.com/product-detail/C9002.html'],
 ['C177, C178','Crystal load capacitors 22 pF C0G 0603','Samsung Electro-Mechanics','CL10C220JB8NNNC','C1653',2,100,100,null,100,null,null,null,null,'LCSC number from search result; price/stock unverified',46300,'2026-10-06','DS: 10-33 pF depending on crystal.','https://www.lcsc.com/product-detail/C1653.html'],
 ['R170','PCM2902C VBUS filter 2.2 ohm 1% 0603','YAGEO','RC0603FR-072R2L','',1,100,100,null,100,null,null,null,null,'LCSC number not found',46300,'2026-10-06','Part number follows the family; LCSC code and price still to be looked up.',''],
 ['R171, R172','USB D+/D- 22 ohm series resistors 0603','YAGEO','RC0603FR-0722RL','',2,100,100,null,100,null,null,null,null,'LCSC number not found',46300,'2026-10-06','Alternative seen in search: UNI-ROYAL 0603WAJ0220T5E / C1203 (22 ohm, 5%).',''],
 ['R173','D+ pull-up 1.5 kohm 1% 0603 (to VDDI)','YAGEO','RC0603FR-071K5L','C114668',1,100,100,null,100,0.0009,null,null,507200,'Listing snapshot, 2026-10-06',46300,'2026-10-06','Search-result price/stock.','https://www.lcsc.com/product-detail/C114668.html'],
];
rows.forEach((v,i)=>{ sh.getRange(`A${79+i}:S${79+i}`).values=[v]; });
for(let r=11;r<=78;r++){
  const a=String(sh.getRange(`A${r}`).values[0][0]); const d=String(sh.getRange(`D${r}`).values[0][0]);
  const add=(more,n)=>{ sh.getRange(`A${r}`).values=[[a+', '+more]]; sh.getRange(`F${r}`).values=[[Number(sh.getRange(`F${r}`).values[0][0])+n]]; };
  if(d==='CL21B105KBFNNNE') add('C170, C171, C172, C173, C174',5);
  else if(d==='CL21B106KPQNNNE') add('C175, C176',2);
  else if(d==='CL31B475KBHNNNE') add('C186, C187',2);
  else if(d==='RC0603FR-07100KL' && a.startsWith('R152')) add('R175, R176',2);
  else if(d==='RC0603FR-071ML') add('R174',1);
}
for(let r=11;r<=end;r++){
 sh.getRange(`I${r}`).formulas=[[`=IF(OR(D${r}="",G${r}="",H${r}=""),"",IF(COUNTIF($D$11:D${r},D${r})>1,0,ROUNDUP(MAX(SUMIF($D$11:$D$${end},D${r},$F$11:$F$${end}),G${r})/H${r},0)*H${r}))`]];
 sh.getRange(`L${r}`).formulas=[[`=IF(K${r}="","",ROUND(F${r}*K${r},4))`]];
 sh.getRange(`M${r}`).formulas=[[`=IF(OR(K${r}="",I${r}="",N${r}=""),"",IF(N${r}>=I${r},ROUND(I${r}*K${r},4),""))`]];
}
sh.getRange('E4:E5').formulas=[[`=ROUND(SUM(L11:L${end}),2)`],[`=ROUND(SUM(M11:M${end}),2)`]];
const out=await SpreadsheetFile.exportXlsx(wb); await out.save(path);
const wb2=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const s2=wb2.worksheets.getItem('Selected BOM');
const all=s2.getRange(`A10:S${end}`).values;
const q=v=>v===null||v===undefined||v===''?'':'"'+String(v).replace(/"/g,'""')+'"';
await fs.writeFile(csvPath, all.map(r=>r.map(q).join(',')).join('\n')+'\n');
console.log('E4,E5', JSON.stringify(s2.getRange('E4:E5').values), 'rows', all.length);
