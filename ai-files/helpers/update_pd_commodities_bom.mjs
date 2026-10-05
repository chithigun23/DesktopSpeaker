import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';

const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sh=wb.worksheets.getItem('Selected BOM');

// Find rows for R10 and C182/C183
let r10Row=null, c182Row=null;
for(let r=11;r<=100;r++){
  const ref=String(sh.getRange(`A${r}`).values[0][0]??'');
  if(ref.includes('R10'))r10Row=r;
  if(ref.includes('C182'))c182Row=r;
}

console.log(`R10 at row ${r10Row}, C182/C183 at row ${c182Row}`);

// Update R10: YAGEO RC0603FR-07200KL C105604
if(r10Row){
  const row=sh.getRange(`A${r10Row}:S${r10Row}`).values[0];
  row[2]='YAGEO';
  row[3]='RC0603FR-07200KL';
  row[4]='C105604';
  row[6]=100; // MOQ
  row[7]=100; // Multiple
  row[9]=100; // Tier qty
  row[10]=0.0024; // Unit price
  row[13]=''; // Stock
  row[14]='Listing snapshot';
  row[15]=46300;
  row[16]='2026-10-06';
  row[18]='https://www.lcsc.com/product-detail/C105604.html';
  sh.getRange(`A${r10Row}:S${r10Row}`).values=[row];
  console.log('Updated R10');
}

// Update C182/C183: Samsung CL10C331JB8NNNC C1578
if(c182Row){
  const row=sh.getRange(`A${c182Row}:S${c182Row}`).values[0];
  row[2]='Samsung Electro-Mechanics';
  row[3]='CL10C331JB8NNNC';
  row[4]='C1578';
  row[6]=100; // MOQ
  row[7]=100; // Multiple
  row[9]=100; // Tier qty
  row[10]=0.0089; // Unit price
  row[13]=''; // Stock
  row[14]='Listing snapshot';
  row[15]=46300;
  row[16]='2026-10-06';
  row[18]='https://www.lcsc.com/product-detail/C1578.html';
  sh.getRange(`A${c182Row}:S${c182Row}`).values=[row];
  console.log('Updated C182/C183');
}

// Update formulas for order qty in column I
if(r10Row) sh.getRange(`I${r10Row}`).formulas=[[`=IF(OR(D${r10Row}="",G${r10Row}="",H${r10Row}=""),"",IF(COUNTIF($D$11:D${r10Row},D${r10Row})>1,0,ROUNDUP(MAX(SUMIF($D$11:$D$100,D${r10Row},$F$11:$F$100),G${r10Row})/H${r10Row},0)*H${r10Row}))`]];
if(c182Row) sh.getRange(`I${c182Row}`).formulas=[[`=IF(OR(D${c182Row}="",G${c182Row}="",H${c182Row}=""),"",IF(COUNTIF($D$11:D${c182Row},D${c182Row})>1,0,ROUNDUP(MAX(SUMIF($D$11:$D$100,D${c182Row},$F$11:$F$100),G${c182Row})/H${c182Row},0)*H${c182Row}))`]];

const out=await SpreadsheetFile.exportXlsx(wb);
await out.save(path);
console.log('XLSX updated successfully');
