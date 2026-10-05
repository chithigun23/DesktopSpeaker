// Guarded: U3 -> STM32G071RBT6 (C432213), adds C163 (VREF+ 100nF), C164 (VREF+ 1uF), R113 (QON sense 100k). Run from project root.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx';
const csvPath='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sh=wb.worksheets.getItem('Selected BOM');
const FIRST=86;
if(String(sh.getRange('A85').values[0][0])!=='J8') throw new Error('unexpected layout');
const refs=sh.getRange('A11:A85').values.map(r=>String(r[0]));
if(refs.some(x=>x.includes('C164'))) throw new Error('already applied');
let last=0; for(let r=FIRST;r<=140;r++){ const v=sh.getRange(`A${r}`).values[0][0]; if(v!==null&&v!=='') last=r; }
const N=1;
const saved=sh.getRange(`A${FIRST}:S${last}`).values;
sh.getRange(`A${FIRST+N}:S${last+N}`).copyFrom(sh.getRange(`A${FIRST}:S${last}`),'all');
sh.getRange(`A${FIRST+N}:S${last+N}`).values=saved;
sh.getRange(`A${FIRST}:S${FIRST}`).copyFrom(sh.getRange('A85:S85'),'all'); sh.getRange(`A${FIRST}:S${FIRST}`).clear({applyTo:'contents'});
sh.getRange(`A${FIRST}:S${FIRST}`).values=[['C164','MCU VREF+ 1uF (DS12232 fig. 13)','Samsung Electro-Mechanics','CL10A105KB8NNNC','C15849',1,10,10,null,10,null,null,null,null,'Stock/price unverified',46300,'2026-10-06','LCSC code from memory of the Samsung 1uF 0603 family; verify code, voltage rating and DC-bias at order.','https://www.lcsc.com/product-detail/C15849.html']];
const end=85+N;
for(let r=11;r<=85;r++){
  const a=String(sh.getRange(`A${r}`).values[0][0]); const d=String(sh.getRange(`D${r}`).values[0][0]);
  const add=(more,n)=>{ sh.getRange(`A${r}`).values=[[a+', '+more]]; sh.getRange(`F${r}`).values=[[Number(sh.getRange(`F${r}`).values[0][0])+n]]; };
  if(a==='U3') sh.getRange(`A${r}:S${r}`).values=[['U3','System control (LQFP64; 128 KB flash, 36 KB RAM)','ST','STM32G071RBT6','C432213',1,1,1,null,1,2.46,null,null,1597,'Search snapshot 2026-10-06 (architecture doc); verify at order',46300,'2026-10-06','Replaces STM32G031K8T6 (C432203): audio chain needs about 46 GPIO. Price/stock not re-verified.','https://www.lcsc.com/product-detail/C432213.html']];
  else if(d==='CL10B104KB8NNNC') add('C163',1);
  else if(d==='RC0603FR-07100KL' && a.startsWith('R152')) add('R113',1);
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
const all=s2.getRange(`A10:S${last+N}`).values;
const q=v=>v===null||v===undefined||v===''?'':'"'+String(v).replace(/"/g,'""')+'"';
await fs.writeFile(csvPath, all.map(r=>r.map(q).join(',')).join('\n')+'\n');
console.log('E4,E5', JSON.stringify(s2.getRange('E4:E5').values), 'rows', all.length);
