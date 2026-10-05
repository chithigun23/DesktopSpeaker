// Guarded: Headphone_Aux parts (D200/D201 row, shared-family quantity updates) and Source_Select_ADC cleanups
// (Y200 caps 22 pF, LCSC codes reused from existing rows or found by 4 search lookups). Run from project root.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx';
const csvPath='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sh=wb.worksheets.getItem('Selected BOM');
const FIRST=98;
if(String(sh.getRange('A97').values[0][0])!=='R209, R210') throw new Error('unexpected layout');
const refs=sh.getRange('A11:A97').values.map(r=>String(r[0]));
if(refs.some(x=>x.includes('D200'))) throw new Error('already applied');
let last=0; for(let r=FIRST;r<=140;r++){ const v=sh.getRange(`A${r}`).values[0][0]; if(v!==null&&v!=='') last=r; }
const saved=sh.getRange(`A${FIRST}:S${last}`).values;
const HA='Headphone_Aux sheet, 2026-10-06. ';
const U='Unverified: price/stock not checked at this BOM freeze.';
const rows=[
 ['D200, D201','Headphone jack / AUX_IN jack ESD, 2-line bidirectional 5 V (SOT-23)','DOWO (Nexperia PESD5V0S2BT equivalent)','PESD5V0S2BT','C5380400',2,5,5,null,5,null,null,null,null,'LCSC number from search 2026-10-06; price/stock unverified',46300,'2026-10-06',HA+'LCSC C5380400 is the DOWO PESD5V0S2BT listing; the Nexperia original was not stock-checked. Pin 3 common (search summary of Nexperia datasheet): VERIFY. Footprint DesktopSpeaker:PESD5V0S2BT (stock SOT-23).','https://www.lcsc.com/product-detail/C5380400.html'],
];
const N=rows.length;
sh.getRange(`A${FIRST+N}:S${last+N}`).copyFrom(sh.getRange(`A${FIRST}:S${last}`),'all');
sh.getRange(`A${FIRST+N}:S${last+N}`).values=saved;
for(let i=0;i<N;i++){ sh.getRange(`A${FIRST+i}:S${FIRST+i}`).copyFrom(sh.getRange('A97:S97'),'all'); sh.getRange(`A${FIRST+i}:S${FIRST+i}`).clear({applyTo:'contents'}); sh.getRange(`A${FIRST+i}:S${FIRST+i}`).values=[rows[i]]; }
const end=97+N;
const note=(r,t)=>{ const c=sh.getRange(`R${r}`); const old=c.values[0][0]; c.values=[[ (old?String(old)+' ':'')+t ]]; };
for(let r=11;r<=97;r++){
  const a=String(sh.getRange(`A${r}`).values[0][0]); const d=String(sh.getRange(`D${r}`).values[0][0]);
  const add=(more,n)=>{ sh.getRange(`A${r}`).values=[[a+', '+more]]; sh.getRange(`F${r}`).values=[[Number(sh.getRange(`F${r}`).values[0][0])+n]]; note(r,HA+'Added '+more+'.'); };
  if(d==='CL21B105KBFNNNE') add('C230, C231, C232, C233, C234, C235, C239, C240, C241, C245',10);
  else if(d==='CL10B104KB8NNNC') add('C237, C238, C242, C246',4);
  else if(d==='CL31B475KBHNNNE') add('C236',1);
  else if(d==='RC0603FR-07100KL' && a.startsWith('R152')) add('R220, R221, R222, R223, R224, R225, R234, R235, R236, R237, R238, R239',12);
  else if(d==='RC0603FR-071KL') add('R226, R227, R228, R229, R230, R231, R240',7);
  else if(d==='RC0603FR-0747KL') add('R232, R233',2);
  else if(d==='RC0603FR-0710KL' && a.startsWith('R11,')) add('R242, R243, R244',3);
  else if(d==='RC0603FR-071ML') add('R241',1);
  else if(d==='CL21B225KAFNNNE'){ add('C243, C244',2); sh.getRange(`E${r}`).values=[['C19110']]; sh.getRange(`O${r}`).values=[['LCSC number from search 2026-10-06; price/stock unverified']]; sh.getRange(`S${r}`).values=[['https://www.lcsc.com/product-detail/C19110.html']]; }
  else if(d==='CL10C200JB8NNNC'){ sh.getRange(`B${r}`).values=[['Crystal load capacitors 22 pF C0G 0603']]; sh.getRange(`D${r}`).values=[['CL10C220JB8NNNC']]; sh.getRange(`E${r}`).values=[['C1653']]; sh.getRange(`O${r}`).values=[['LCSC number from search 2026-10-06 (JLCPCB C1653 page); price/stock unverified']]; sh.getRange(`R${r}`).values=[['Source_Select_ADC sheet. Changed from 20 pF 2026-10-06: 2 x 22 pF in series plus ~3 pF stray gives about 14 pF for the 15 pF crystal. Unverified: price/stock not checked.']]; sh.getRange(`S${r}`).values=[['https://www.lcsc.com/product-detail/C1653.html']]; }
  else if(d==='RC0603FR-07100RL' && a.startsWith('R200')){ sh.getRange(`E${r}`).values=[['C105588']]; sh.getRange(`K${r}`).values=[[0.0024]]; sh.getRange(`N${r}`).values=[[2943700]]; sh.getRange(`O${r}`).values=[['LCSC code and price reused from the R112 row (same MPN)']]; sh.getRange(`S${r}`).values=[['https://www.lcsc.com/product-detail/C105588.html']]; }
  else if(d==='RC0603FR-072K2L'){ sh.getRange(`E${r}`).values=[['C114662']]; sh.getRange(`O${r}`).values=[['LCSC number from search 2026-10-06; price/stock unverified']]; sh.getRange(`S${r}`).values=[['https://www.lcsc.com/product-detail/C114662.html']]; }
  else if(d==='GRM1885C1H103JA01D'||d==='RC0603FR-0733RL') note(r,'LCSC code still open: no lookups left in the Headphone_Aux task budget.');
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
