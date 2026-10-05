// Guarded: J6 -> 1x4 header, C177/C178 -> 33 pF, R170-R172 LCSC numbers, Y170 note. Preserves other rows.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx', csvPath='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sh=wb.worksheets.getItem('Selected BOM');
const col=sh.getRange('A11:A130').values.map(r=>String(r[0]));
const row=a=>{const i=col.findIndex(x=>x===a); if(i<0) throw new Error('missing '+a); return 11+i;};
const set=(r,c,v)=>{sh.getRange(`${c}${r}`).values=[[v]];};
let r=row('J6'); if(String(sh.getRange(`D${r}`).values[0][0])!=='XY-MTP254-1X5') throw new Error('already applied');
const unv='LCSC number from search; price/stock unverified';
set(r,'B','MCU SWD header 1x4 2.54 mm (J7 Tag-Connect TC2030 is PCB pads only, no BOM part)');set(r,'C','Ckmtw');set(r,'D','B-2100S04P-A110');set(r,'E','C124378');
set(r,'K',null);set(r,'N',null);set(r,'O',unv);set(r,'S','https://www.lcsc.com/product-detail/C124378.html');
set(r,'R','1x4 straight THT header; footprint PinHeader_1x04_P2.54mm_Vertical (stock KiCad STEP). Pin order 1 SWDIO 2 SWCLK 3 NRST 4 GND. Programmer cable TC2030-IDC (legged footprint J7) is a tool, not fitted.');
r=row('C177, C178'); set(r,'B','Crystal load capacitors 33 pF C0G 0603');set(r,'D','CL10C330JB8NNNC');set(r,'E','C1663');set(r,'S','https://www.lcsc.com/product-detail/C1663.html');
set(r,'O','Search snapshot: from ~0.0026 USD, ~517,700 in stock (unverified)');
set(r,'R','33 pF + ~3 pF stray each side gives ~19.5 pF effective vs 20 pF crystal rating (DS: 10-33 pF).');
r=row('R170'); set(r,'E','C112307');set(r,'O','LCSC number from JLCPCB/LCSC listing; price/stock unverified');set(r,'S','https://www.lcsc.com/product-detail/C112307.html');set(r,'R','Yageo RC0603FR-072R2L, 2.2 ohm 1% 0603.');
r=row('R171, R172'); set(r,'E','C107701');set(r,'O','Search snapshot: from ~0.0018 USD, ~216,200 in stock (unverified)');set(r,'S','https://www.lcsc.com/product-detail/C107701.html');set(r,'R','Yageo RC0603FR-0722RL, 22 ohm 1% 0603.');
r=row('Y170'); set(r,'R',String(sh.getRange(`R${r}`).values[0][0]).replace('22 pF load caps give ~14 pF CL, below the 20 pF rating: tune at bring-up.','33 pF load caps (C177/C178) give ~19.5 pF effective CL incl. stray, vs 20 pF rating.'));
const end=130; let last=0; for(let k=11;k<=end;k++){const v=sh.getRange(`A${k}`).values[0][0]; if(v!==null&&v!=='') last=k;}
const out=await SpreadsheetFile.exportXlsx(wb); await out.save(path);
const s2=(await SpreadsheetFile.importXlsx(await FileBlob.load(path))).worksheets.getItem('Selected BOM');
const all=s2.getRange(`A10:S${last}`).values;
const q=v=>v===null||v===undefined||v===''?'':'"'+String(v).replace(/"/g,'""')+'"';
await fs.writeFile(csvPath, all.map(x=>x.map(q).join(',')).join('\n')+'\n');
console.log('E4,E5',JSON.stringify(s2.getRange('E4:E5').values),'last',last);
