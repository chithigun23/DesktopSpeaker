// Guarded: adds Bluetooth sheet parts (C190-C195, R180-R187, J8) once; preserves other rows. Run from project root.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx';
const csvPath='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sh=wb.worksheets.getItem('Selected BOM');
const FIRST=84; // first row after the last data row (R173 at 83)
if(String(sh.getRange('A83').values[0][0])!=='R173') throw new Error('unexpected layout');
let last=0; for(let r=FIRST;r<=140;r++){ const v=sh.getRange(`A${r}`).values[0][0]; if(v!==null&&v!=='') last=r; }
const refs=sh.getRange('A11:A83').values.map(r=>String(r[0]));
if(refs.some(x=>x.includes('R185'))) throw new Error('already applied');
const N=2;
sh.getRange(`A${FIRST+N}:S${last+N}`).copyFrom(sh.getRange(`A${FIRST}:S${last}`),'all');
for(let r=FIRST;r<FIRST+N;r++){ sh.getRange(`A${r}:S${r}`).copyFrom(sh.getRange('A83:S83'),'all'); sh.getRange(`A${r}:S${r}`).clear({applyTo:'contents'}); }
const end=83+N;
const rows=[
 ['R185, R186, R187','BM83 RST_N series (R185) and UART_TXD / P0_0 TX_IND series (R186, R187) 1 kohm 1% 0603','YAGEO','RC0603FR-071KL','C22548',3,100,100,null,100,0.0011,null,null,9947200,'Search-result price/stock, 2026-10-06',46300,'2026-10-06','Bluetooth sheet; LCSC number from search result, price/stock not re-verified.','https://www.lcsc.com/product-detail/C22548.html'],
 ['J8','BM83 test/programming header 1x5 2.54 mm (RST_N, P3_4, UART RX/TX, GND)','XYECONN','XY-MTP254-1X5','C54110162',1,10,10,null,10,null,null,null,null,'Stock/price unverified',46300,'2026-10-06','Bluetooth sheet; part number carried from the earlier 1x5 SWD header selection, not re-verified.','https://www.lcsc.com/product-detail/C54110162.html'],
];
rows.forEach((v,i)=>{ sh.getRange(`A${FIRST+i}:S${FIRST+i}`).values=[v]; });
for(let r=11;r<=83;r++){
  const a=String(sh.getRange(`A${r}`).values[0][0]); const d=String(sh.getRange(`D${r}`).values[0][0]);
  const add=(more,n)=>{ sh.getRange(`A${r}`).values=[[a+', '+more]]; sh.getRange(`F${r}`).values=[[Number(sh.getRange(`F${r}`).values[0][0])+n]]; };
  if(d==='CL21B105KBFNNNE') add('C192, C193',2);
  else if(d==='CL21B106KPQNNNE') add('C190',1);
  else if(d==='CL31B475KBHNNNE') add('C194, C195',2);
  else if(d==='CL10B104KB8NNNC') add('C191',1);
  else if(d==='RC0603FR-0710KL' && a.startsWith('R11,')) add('R182, R183',2);
  else if(d==='RC0603FR-07100KL' && a.startsWith('R152')) add('R180, R181, R184',3);
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
