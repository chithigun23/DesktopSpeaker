// Guarded: adds Source_Select_ADC parts (U22-U24, Y200, FB200, C200-C227, R200-R212) once. Run from project root.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx';
const csvPath='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sh=wb.worksheets.getItem('Selected BOM');
const FIRST=87;
if(String(sh.getRange('A86').values[0][0])!=='C164') throw new Error('unexpected layout');
const refs=sh.getRange('A11:A86').values.map(r=>String(r[0]));
if(refs.some(x=>x.includes('U24'))) throw new Error('already applied');
let last=0; for(let r=FIRST;r<=140;r++){ const v=sh.getRange(`A${r}`).values[0][0]; if(v!==null&&v!=='') last=r; }
const saved=sh.getRange(`A${FIRST}:S${last}`).values;
const U='Unverified: LCSC code/price/stock not checked at this BOM freeze.';
const SS='Source_Select_ADC sheet, 2026-10-06. ';
const rows=[
 ['U24','Audio ADC 4:1 input, I2S master (TSSOP-30)','TI','PCM1862DBTR','C544647',1,1,1,null,1,null,null,null,null,'LCSC number from search 2026-10-06; price/stock unverified',46300,'2026-10-06',SS+'Datasheet SLAS831D.','https://www.lcsc.com/product-detail/C544647.html'],
 ['U22','3V3_AUDIO 300 mA ultra-low-noise LDO','TI','TPS7A2033PDBVR','C2862740',1,1,1,null,1,null,null,null,null,'LCSC number from search 2026-10-06; price/stock unverified',46300,'2026-10-06',SS+'A TECH PUBLIC TPS7A2033PDBVR-TP clone is listed as C49452001; TI part chosen.','https://www.lcsc.com/product-detail/C2862740.html'],
 ['U23','5V_CODEC load switch (SOT-23-6)','TI','TPS22917DBVR','C2681320',1,1,1,null,1,null,null,null,null,'LCSC number from search 2026-10-06; price/stock unverified',46300,'2026-10-06',SS+'Pinout checked against SLVSDW8B.','https://www.lcsc.com/product-detail/C2681320.html'],
 ['Y200','24.576 MHz crystal for PCM1862 (3225-4P, CL 15 pF)','Lucki','L327S240P11L','C5261154',1,1,1,null,1,null,null,null,null,'LCSC number from search 2026-10-06; price/stock unverified',46300,'2026-10-06',SS+'Datasheet not retrieved; pad usage 1/3 assumed. Two 20 pF caps give about 13 pF CL; trim at bring-up.','https://www.lcsc.com/product-detail/C5261154.html'],
 ['FB200','AVDD ferrite bead 600 ohm @100 MHz 0603','Murata','BLM18AG601SN1D','C19330',1,10,10,null,10,null,null,null,null,'LCSC number from search 2026-10-06; price/stock unverified',46300,'2026-10-06',SS+'0.5 A, 380 mOhm DCR (search snapshot).','https://www.lcsc.com/product-detail/C19330.html'],
 ['C200, C201, C202, C203, C204, C205','Input AC-coupling 2.2uF X7R 0805','Samsung Electro-Mechanics','CL21B225KAFNNNE','',6,10,10,null,10,null,null,null,null,'LCSC code not looked up',46300,'2026-10-06',SS+U+' Check voltage rating and DC-bias.',''],
 ['C206, C207, C208, C209, C210, C211','Input anti-alias 10nF C0G 0603','Murata','GRM1885C1H103JA01D','',6,10,10,null,10,null,null,null,null,'LCSC code not looked up',46300,'2026-10-06',SS+U,''],
 ['C226, C227','Crystal load capacitors 20 pF C0G 0603','Samsung Electro-Mechanics','CL10C200JB8NNNC','',2,100,100,null,100,null,null,null,null,'LCSC code not looked up',46300,'2026-10-06',SS+U,''],
 ['R200, R201, R202, R203, R204, R205','Input series 100 ohm 1% 0603','YAGEO','RC0603FR-07100RL','',6,100,100,null,100,null,null,null,null,'LCSC code not looked up',46300,'2026-10-06',SS+U,''],
 ['R206, R207, R208','I2S series 33 ohm 1% 0603','YAGEO','RC0603FR-0733RL','',3,100,100,null,100,null,null,null,null,'LCSC code not looked up',46300,'2026-10-06',SS+U,''],
 ['R209, R210','Audio I2C pull-ups 2.2k 1% 0603','YAGEO','RC0603FR-072K2L','',2,100,100,null,100,null,null,null,null,'LCSC code not looked up',46300,'2026-10-06',SS+U,''],
];
const N=rows.length;
sh.getRange(`A${FIRST+N}:S${last+N}`).copyFrom(sh.getRange(`A${FIRST}:S${last}`),'all');
sh.getRange(`A${FIRST+N}:S${last+N}`).values=saved;
for(let i=0;i<N;i++){ sh.getRange(`A${FIRST+i}:S${FIRST+i}`).copyFrom(sh.getRange('A86:S86'),'all'); sh.getRange(`A${FIRST+i}:S${FIRST+i}`).clear({applyTo:'contents'}); sh.getRange(`A${FIRST+i}:S${FIRST+i}`).values=[rows[i]]; }
const end=86+N;
for(let r=11;r<=86;r++){
  const a=String(sh.getRange(`A${r}`).values[0][0]); const d=String(sh.getRange(`D${r}`).values[0][0]);
  const add=(more,n)=>{ sh.getRange(`A${r}`).values=[[a+', '+more]]; sh.getRange(`F${r}`).values=[[Number(sh.getRange(`F${r}`).values[0][0])+n]]; };
  if(d==='CL21B105KBFNNNE') add('C212, C220, C221, C222, C224, C225',6);
  else if(d==='CL21B106KPQNNNE') add('C214, C216, C218, C223',4);
  else if(d==='CL10B104KB8NNNC') add('C213, C215, C217, C219',4);
  else if(d==='RC0603FR-07100KL' && a.startsWith('R152')) add('R211, R212',2);
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
