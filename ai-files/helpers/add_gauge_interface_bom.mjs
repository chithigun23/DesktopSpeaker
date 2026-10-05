// One-shot historical authoring helper for Q104/C126/U21/R126/R127. Guarded against duplicate reruns.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const root='/home/chithi/Desktop/DesktopSpeaker';
const xlsx=`${root}/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx`;
const csvPath=`${root}/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv`;
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(xlsx));
const sh=wb.worksheets.getItem('Selected BOM');

// Guard against a concurrent or repeated integration of these references.
const current=sh.getRange('A11:A87').values.flat().map(x=>String(x??''));
if(current.some(x=>/\b(U21|Q104|C126|R126|R127)\b/.test(x))) throw new Error('At least one requested reference is already in the active BOM.');
const qIndex=sh.getRange('A11:A87').values.findIndex(x=>String(x[0]??'').split(',').map(t=>t.trim()).includes('Q100'));
if(qIndex<0) throw new Error('Expected Q100 shared NMOS row changed.');
const qRow=qIndex+11;
const capIndex=sh.getRange('D11:D87').values.findIndex(x=>x[0]==='CL10B104KB8NNNC');
if(capIndex<0) throw new Error('Existing 100nF 0603 row not found.');
const capRow=capIndex+11;

// Move existing footnotes down to free two BOM rows. Copy bottom-up to preserve each row's style and contents.
for(let r=91;r>=86;r--) sh.getRange(`A${r+2}:S${r+2}`).copyFrom(sh.getRange(`A${r}:S${r}`),'all');
sh.getRange('A86:S87').clear({applyTo:'contents'});

// Reuse the selected MOSFET and decoupling capacitor orders.
sh.getRange(`A${qRow}`).values=[['Q100, Q104']];
sh.getRange(`B${qRow}`).values=[['Charger CE and gauge-enable NMOS']];
sh.getRange(`F${qRow}`).values=[[2]];
sh.getRange(`A${capRow}`).values=[[String(sh.getRange(`A${capRow}`).values[0][0])+', C126']];
sh.getRange(`B${capRow}`).values=[['100nF / 10V-or-higher 0603 decoupling; supervisor C126']];
sh.getRange(`F${capRow}`).values=[[8]];

// U21 uses the selected TI supervisor; R126/R127 share the exact same 1M 0603 Yageo line.
sh.getRange('A86:S86').copyFrom(sh.getRange('A82:S82'),'all');
sh.getRange('A86:S86').values=[[
  'U21','Gauge undervoltage supervisor','Texas Instruments','TPS3839G33DBZR','C485802',
  1,1,1,null,1,0.439,null,null,3444,'Listing snapshot',46300,'2026-10-05',
  'LCSC snapshot 2026-10-05: 3,444 in stock; $0.439 at 1+. DBZ/SOT-23-3. TI datasheet: https://www.ti.com/lit/ds/symlink/tps3839.pdf.',
  'https://www.lcsc.com/product-detail/C485802.html'
]];
sh.getRange('A87:S87').copyFrom(sh.getRange('A81:S81'),'all');
sh.getRange('A87:S87').values=[[
  'R126, R127','Gauge signal-switch and supervisor gate pull-up/pull-down resistors','YAGEO','RC0603FR-071ML','C105578',
  2,100,100,null,100,0.0056,null,null,359600,'Listing snapshot',46300,'2026-10-05',
  'LCSC snapshot 2026-10-05: 359,600 in stock; $0.0056 at MOQ 100. Official YAGEO datasheet: https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-071ML.',
  'https://www.lcsc.com/product-detail/C105578.html'
]];

const end=87;
for(let r=11;r<=end;r++){
 sh.getRange(`I${r}`).formulas=[[`=IF(OR(D${r}="",G${r}="",H${r}=""),"",IF(COUNTIF($D$11:D${r},D${r})>1,0,ROUNDUP(MAX(SUMIF($D$11:$D$${end},D${r},$F$11:$F$${end}),G${r})/H${r},0)*H${r}))`]];
 sh.getRange(`L${r}`).formulas=[[`=IF(K${r}="","",ROUND(F${r}*K${r},4))`]];
 sh.getRange(`M${r}`).formulas=[[`=IF(OR(K${r}="",I${r}="",N${r}=""),"",IF(N${r}>=I${r},ROUND(I${r}*K${r},4),""))`]];
}
sh.getRange('E4:E5').formulas=[[`=ROUND(SUM(L11:L${end}),2)`],[`=ROUND(SUM(M11:M${end}),2)`]];
sh.getRange('G4').values=[['BOM updated 2026-10-05 with gauge undervoltage supervisor and isolation controls; stock/prices are listing snapshots.']];
sh.getRange('G5').values=[['MOQ orders consolidated by MPN; repeat rows show order quantity 0.']];
sh.getRange('G6').values=[['Partial subtotal excludes unpriced parts, unverified stock, pack, switches, speakers and open audio selections; not full product cost.']];
sh.getRange('A86:F87').format.wrapText=true;
sh.getRange('R86:R87').format.wrapText=true;
sh.getRange('A86:S87').format.rowHeight=54;
sh.getRange('K11:M87').setNumberFormat('$0.0000');
sh.getRange('L11:M87').setNumberFormat('$0.00');
sh.getRange('P11:P87').setNumberFormat('yyyy-mm-dd');
wb.recalculate();

// Formula and content reconciliation limited to edited rows and totals.
const scan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:200},summary:'Gauge interface BOM formula scan'});
await fs.writeFile(`${root}/ai-files/reports/gauge-interface-bom-formula-scan.ndjson`,scan.ndjson+'\n');
const formulaErrors=Number(scan.ndjson.match(/matched (\d+) entries/)?.[1]??0);
if(formulaErrors) throw new Error(`Formula error scan found ${formulaErrors} errors`);
const rows=sh.getRange(`A10:S${end}`).values;
const csv=rows.map(row=>row.map(v=>v==null?'':`"${String(v).replaceAll('"','""')}"`).join(',')).join('\n')+'\n';
const out=await SpreadsheetFile.exportXlsx(wb); await out.save(xlsx); await fs.writeFile(csvPath,csv);
const totals=sh.getRange('E4:E5').values;
const report={date:'2026-10-05',scope:'Only requested active BOM refs Q104/C126/U21/R126/R127; draft charger/PD candidate parts excluded.',added:[{references:'U21',manufacturer:'Texas Instruments',mpn:'TPS3839G33DBZR',lcsc:'C485802',fittedQty:1,moq:1,stock:3444,unitUsdAt1:0.439},{references:'R126, R127',manufacturer:'YAGEO',mpn:'RC0603FR-071ML',lcsc:'C105578',fittedQty:2,moq:100,multiple:100,stock:359600,unitUsdAt100:0.0056,datasheet:'https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-071ML'}],merged:[{references:sh.getRange(`A${qRow}`).values[0][0],mpn:'2N7002,215',lcsc:'C65189',fittedQty:2},{references:sh.getRange(`A${capRow}`).values[0][0],mpn:'CL10B104KB8NNNC',lcsc:'C1591',fittedQty:8}],partialFittedSubtotalUsd:totals[0][0],inStockOrderSubtotalUsd:totals[1][0],formulaErrorMatches:formulaErrors};
await fs.writeFile(`${root}/ai-files/reports/gauge-interface-bom-reconciliation.json`,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
