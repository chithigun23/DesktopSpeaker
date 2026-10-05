// Guarded: Amplifiers sheet BOM rows (U25, L200-L206, J9-J11, boost/TAS/filter passives) and shared-family quantity updates.
// Preserves all other rows. Run from project root. Prices/stock are unverified unless the notes say otherwise.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx';
const csvPath='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sh=wb.worksheets.getItem('Selected BOM');
const FIRST=99;
if(String(sh.getRange('A98').values[0][0])!=='D200, D201') throw new Error('unexpected layout');
const refs=sh.getRange('A11:A98').values.map(r=>String(r[0]));
if(refs.some(x=>x.includes('U25'))) throw new Error('already applied');
let last=0; for(let r=FIRST;r<=140;r++){ const v=sh.getRange(`A${r}`).values[0][0]; if(v!==null&&v!=='') last=r; }
const saved=sh.getRange(`A${FIRST}:S${last}`).values;
const AM='Amplifiers sheet, 2026-10-06. ';
const OPEN='LCSC code open: not found in the Amplifiers task lookup budget; price/stock unverified.';
const UNV='LCSC number from search 2026-10-06; price/stock unverified.';
// [ref, function, mfr, mpn, lcsc, qty, moq, mult, order, tier, unit, fitted, orderUsd, stock, avail, accessed, cache, notes, url]
const row=(ref,fn,mfr,mpn,lcsc,qty,price,stock,avail,note)=>[ref,fn,mfr,mpn,lcsc,qty,price!=null?1:null,price!=null?1:null,null,price!=null?1:null,price??null,null,null,stock??null,avail,46300,'2026-10-06',AM+note,lcsc?`https://www.lcsc.com/product-detail/${lcsc}.html`:null];
const rows=[
 row('U25','PVDD boost converter 11.9 V (VQFN-20)','TI','TPS61088RHLR','C87357',1,4.9,1199,'EasyEDA/LCSC API 2026-10-06; verify at order','499k/56k feedback, 301k RFREQ, 150k ILIM. Pad map and 3D from the EasyEDA official package; verify against TI RHL0020A before PCB.'),
 row('L200','Boost inductor 2.2uH, Isat 19.6 A, Irms 17.8 A, 6.3 mohm','Coilcraft','XAL7070-222MEC','',1,null,null,OPEN,'Not stocked at LCSC per search; alternatives: Cyntec PIMB104T-2R2MS (datasheet table 2, 18 A / 12 A) or Bourns SRP1265A-2R2M class. Stock KiCad XAL7070 footprint (7.5 x 7.2 mm).'),
 row('L201, L202, L203, L204, L205, L206','Speaker output filter inductors 22uH, 5.0 A Isat (peak 2.8 A at 11.1 V into 4 ohm)','Sunlord','MWSA1265S-220MT','',6,null,null,OPEN,'Isat 5.0 A from the MWSA1265S series datasheet text; the 22 uH value row and its LCSC code were not confirmed. Stock KiCad MWSA1265S footprint (13.45 x 12.6 x 6.5 mm). OCP trips at about 7.5 A; confirm the saturation margin against measured peak.'),
 row('J9, J10, J11','Speaker connectors FRONT_L, FRONT_R, WOOFER (JST VH 2-pin, 10 A)','JST','B2P-VH(LF)(SN)','C160315',3,0.2404,20650,'EasyEDA/LCSC API 2026-10-06; verify at order','Pin 1 +, pin 2 -. No 3D model linked (downloaded STEP axes not verified).'),
 row('C271, C272, C273, C274, C277, C279, C290, C292','PVDD_AMP 22uF 25V X7R 1210 (boost output and TAS5825M PVDD)','Samsung Electro-Mechanics','CL32B226KAJNNNE','C309062',8,0.1742,9300,'Search snapshot 2026-10-06; verify at order','25 V rating on 11.9 V; X7R loses roughly half its capacitance at this bias. TAS datasheet lists 22 uF 35 V 0805: 1210 25 V used instead.'),
 row('C285, C286, C287, C288, C298, C299, C300, C301','TAS5825M bootstrap 0.47uF 25V X7R 0603','Samsung Electro-Mechanics','CL10B474KA8NNNC','',8,null,null,OPEN,'Table 66 value 0.47 uF 16 V; 25 V part selected for margin.'),
 row('C302, C303, C304, C305, C306, C307','Output filter 0.68uF 50V X7R 0805','Samsung Electro-Mechanics','CL21B684KBFVPNE','C472832',6,null,null,'LCSC number from search 2026-10-06; price/stock unverified','Variant suffix per the LCSC listing; confirm voltage/dielectric on the datasheet.'),
 row('C268','Boost COMP capacitor 6.8nF X7R 0603','Samsung Electro-Mechanics','CL10B682KB8NNNC','',1,null,null,OPEN,'Calculated compensation, bench check required.'),
 row('C269','Boost COMP capacitor 47pF C0G 0603','Samsung Electro-Mechanics','CL10C470JB8NNNC','',1,null,null,OPEN,'Calculated compensation, bench check required.'),
 row('C275','PVDD_AMP bulk 100uF 25V polymer/hybrid (8x10 mm)','Panasonic','EEH-ZA1E101P','',1,null,null,OPEN+' VERIFY part.','Bass-burst reservoir; part type not verified.'),
 row('R250','Boost feedback upper resistor 499k 1%','YAGEO','RC0603FR-07499KL','',1,null,null,OPEN,'VOUT = 1.204 V x (1 + 499k/56k) = 11.93 V.'),
 row('R251','Boost feedback lower resistor 56k 1%','YAGEO','RC0603FR-0756KL','',1,null,null,OPEN,''),
 row('R252','Boost RFREQ 301k 1%','YAGEO','RC0603FR-07301KL','',1,null,null,OPEN,'About 494 kHz at 3.6 V in.'),
 row('R253','Boost ILIM 150k 1%','YAGEO','RC0603FR-07150KL','',1,null,null,OPEN,'7.9 A typical, 6.6 A minimum peak limit (PFM).'),
 row('R254','Boost COMP resistor 82k 1%','YAGEO','RC0603FR-0782KL','',1,null,null,OPEN,''),
 row('R260 (R256 DNP)','TAS5825M U6 ADR 0 ohm (R256 = boost MODE option, not fitted)','YAGEO','RC0603FR-070RL','',1,null,null,OPEN,'R256 is DNP: fit to force PWM mode.'),
];
const N=rows.length;
sh.getRange(`A${FIRST+N}:S${last+N}`).copyFrom(sh.getRange(`A${FIRST}:S${last}`),'all');
sh.getRange(`A${FIRST+N}:S${last+N}`).values=saved;
for(let i=0;i<N;i++){ sh.getRange(`A${FIRST+i}:S${FIRST+i}`).copyFrom(sh.getRange('A98:S98'),'all'); sh.getRange(`A${FIRST+i}:S${FIRST+i}`).clear({applyTo:'contents'}); sh.getRange(`A${FIRST+i}:S${FIRST+i}`).values=[rows[i]]; }
const end=98+N;
const note=(r,t)=>{ const c=sh.getRange(`R${r}`); const o=c.values[0][0]; c.values=[[ (o?String(o)+' ':'')+t ]]; };
for(let r=11;r<=98;r++){
  const a=String(sh.getRange(`A${r}`).values[0][0]); const d=String(sh.getRange(`D${r}`).values[0][0]);
  const add=(more,n)=>{ sh.getRange(`A${r}`).values=[[a+', '+more]]; sh.getRange(`F${r}`).values=[[Number(sh.getRange(`F${r}`).values[0][0])+n]]; note(r,AM+'Added '+more+'.'); };
  if(d==='CL21B105KBFNNNE') add('C270, C282, C283, C284, C295, C296, C297',7);
  else if(d==='CL10B104KB8NNNC') add('C260, C267, C276, C278, C281, C289, C291, C294',8);
  else if(d==='CL21B225KAFNNNE') add('C265',1);
  else if(d==='CC0603KRX7R9BB473') add('C266',1);
  else if(d==='CL10A475KO8NNNC') add('C280, C293',2);
  else if(d==='GRM21BZ71A226ME15L' && a.startsWith('C6,')) add('C261, C262, C263, C264',4);
  else if(d==='RC0603FR-07100KL' && a.startsWith('R152')) add('R255, R259',2);
  else if(d==='RC0603FR-0710KL' && a.startsWith('R11,')) add('R262',1);
  else if(d==='RC0603FR-071KL') add('R257, R258, R261',3);
  else if(d==='GRM1885C1H103JA01D'||d==='RC0603FR-0733RL') note(r,'LCSC code still open after the Amplifiers lookup (search returned distributor listings only).');
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
