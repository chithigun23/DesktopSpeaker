import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';

const root='/home/chithi/Desktop/DesktopSpeaker';
const xlsx=`${root}/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx`;
const csvPath=`${root}/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv`;
const netlist=`${root}/ai-files/reports/usb-aux-logic-integrated.xml`;
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(xlsx));
const sh=wb.worksheets.getItem('Selected BOM');
const end=85;

// Create candidate rows once, preserving footnotes on subsequent runs.
const rowsAlreadyAdded=sh.getRange('A83:A85').values.map(r=>r[0]).join(',')==='U20,R124,R125';
if(!rowsAlreadyAdded){
 sh.getRange('A86:S91').copyFrom(sh.getRange('A83:S88'),'all');
 sh.getRange('A83:S85').clear({applyTo:'contents'});
 for(let r=83;r<=85;r++) sh.getRange(`A${r}:S${r}`).copyFrom(sh.getRange('A82:S82'),'all');
}

// Add the two newly selected lines; R125 reuses the existing C14675 mapping on its separate circuit row.
if(!rowsAlreadyAdded) sh.getRange('A83:S83').values=[[
  'U20','USB and system logic priority mux','Texas Instruments','TPS2116DRLR','C3235557',1,null,null,null,null,null,null,null,null,'Stock/price unverified',null,null,
  'Selected MPN/LCSC mapping; current stock and price not verified.', 'https://www.lcsc.com/product-detail/C3235557.html'
]];
if(!rowsAlreadyAdded) sh.getRange('A84:S84').values=[[
  'R124','180k 1% USB-priority threshold divider resistor','YAGEO','RC0603FR-07180KL','C123419',1,100,100,null,100,0.0012,null,null,null,'Stock unverified; price snapshot',46300,'2026-10-05',
  'Observed listing tier: $0.0012 at MOQ100. Product page may be stale; stock is unverified.', 'https://www.lcsc.com/product-detail/C123419.html'
]];
if(!rowsAlreadyAdded) sh.getRange('A85:S85').values=[[
  'R125','100k PR1 divider resistor','YAGEO','RC0603FR-07100KL','C14675',1,100,100,null,100,0.0036,null,null,7813400,'Listing snapshot',46300,'2026-10-05',
  'Reuse same selected MPN/LCSC mapping as existing 100k BOM rows; no additional MOQ order.', 'https://www.lcsc.com/product-detail/C14675.html'
]];

// U19 also supplies the mux's USB auxiliary logic rail.
sh.getRange('B82').values=[['USB auxiliary 5V / PD controller VDD LDO']];

// Extend shared capacitor references and quantities using the already-selected C122/C123 part.
let capRow=null;
for(let r=11;r<=82;r++) if(sh.getRange(`D${r}`).values[0][0]==='LMK107B7105KA-T') capRow=r;
if(!capRow) throw new Error('Could not find existing C122/C123 1uF capacitor row.');
sh.getRange(`A${capRow}`).values=[['C122, C123, C124, C125']];
sh.getRange(`F${capRow}`).values=[[4]];

// Keep one shared order per MPN while retaining one row per functional selection.
for(let r=11;r<=end;r++){
 sh.getRange(`I${r}`).formulas=[[`=IF(OR(D${r}="",G${r}="",H${r}=""),"",IF(COUNTIF($D$11:D${r},D${r})>1,0,ROUNDUP(MAX(SUMIF($D$11:$D$${end},D${r},$F$11:$F$${end}),G${r})/H${r},0)*H${r}))`]];
 sh.getRange(`L${r}`).formulas=[[`=IF(K${r}="","",ROUND(F${r}*K${r},4))`]];
 sh.getRange(`M${r}`).formulas=[[`=IF(OR(K${r}="",I${r}="",N${r}=""),"",IF(N${r}>=I${r},ROUND(I${r}*K${r},4),""))`]];
}
sh.getRange('E4:E5').formulas=[[`=ROUND(SUM(L11:L${end}),2)`],[`=ROUND(SUM(M11:M${end}),2)`]];
sh.getRange('G4').values=[['BOM updated 2026-10-05 with active USB auxiliary mux; stock/prices are listing snapshots or marked unverified.']];
sh.getRange('G5').values=[['MOQ orders consolidated by MPN; repeat rows show order quantity 0.']];
sh.getRange('G6').values=[['Partial subtotal excludes unpriced parts, unverified stock, pack, switches, speakers and open audio selections; not full product cost.']];
sh.getRange('A83:F85').format.wrapText=true;
sh.getRange('R83:R85').format.wrapText=true;
sh.getRange('A83:S85').format.rowHeight=48;
sh.getRange('K11:M85').setNumberFormat('$0.0000');
sh.getRange('L11:M85').setNumberFormat('$0.00');
sh.getRange('P11:P85').setNumberFormat('yyyy-mm-dd');

wb.recalculate();
const formulaErrors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:200},summary:'USB auxiliary BOM formula error scan'});
await fs.writeFile(`${root}/ai-files/reports/usb-aux-bom-formula-scan.ndjson`,formulaErrors.ndjson+'\n');
const errors=Number(formulaErrors.ndjson.match(/matched (\d+) entries/)?.[1]??0);
const rows=sh.getRange(`A10:S${end}`).values;
const csv=rows.map(row=>row.map(v=>v==null?'':`"${String(v).replaceAll('"','""')}"`).join(',')).join('\n')+'\n';
const output=await SpreadsheetFile.exportXlsx(wb); await output.save(xlsx);
await fs.writeFile(csvPath,csv);
for(const [tag,range] of [['usb-aux-bom-changed-parts','A80:F85'],['usb-aux-bom-order-pricing','I80:O85'],['usb-aux-bom-totals','A2:M8']]){
 const image=await wb.render({sheetName:'Selected BOM',range,scale:1.15,format:'png'});
 await fs.writeFile(`${root}/ai-files/reports/${tag}.png`,new Uint8Array(await image.arrayBuffer()));
}

const capQty=sh.getRange(`F${capRow}`).values[0][0];
const subtotal=sh.getRange('E4:E5').values;
const bomRefs=[];
for(const row of rows.slice(1)) bomRefs.push(...String(row[0]??'').split(',').map(x=>x.trim()).filter(Boolean));
const {execFileSync}=await import('node:child_process');
const py=`import xml.etree.ElementTree as E,json; r=E.parse(${JSON.stringify(netlist)}).getroot(); out=[];
for c in r.findall('.//components/comp'):
 p={x.get('name'):x.get('value','') for x in c.findall('./property')}; out.append({'ref':c.get('ref'),'mpn':p.get('MPN',''),'lcsc':p.get('LCSC','')})
print(json.dumps(out))`;
const netComps=JSON.parse(execFileSync('python3',['-c',py],{encoding:'utf8'}));
const netRefs=netComps.map(c=>c.ref);
const missing=netRefs.filter(r=>!bomRefs.includes(r));
const bomByRef=new Map(); for(const row of rows.slice(1)) for(const ref of String(row[0]??'').split(',').map(x=>x.trim()).filter(Boolean)) bomByRef.set(ref,{mpn:row[3]??'',lcsc:row[4]??''});
const identityCheck={mpn:{checked:0,matched:0,mismatches:[],unresolved:[]},lcsc:{checked:0,matched:0,mismatches:[],unresolved:[]}};
for(const c of netComps){const b=bomByRef.get(c.ref); for(const [key,field] of [['mpn','mpn'],['lcsc','lcsc']]){const value=c[field]; if(!value||value==='TBD') continue; identityCheck[key].checked++; const bomValue=b?.[field]??''; if(!bomValue) identityCheck[key].unresolved.push(c.ref); else if(value!==bomValue) identityCheck[key].mismatches.push({reference:c.ref,netlist:value,bom:bomValue}); else identityCheck[key].matched++; }}
const newPartIdentityChecks=['U20','R124','R125','C124','C125'].map(ref=>({reference:ref,bom:bomByRef.get(ref),netlist:netComps.find(c=>c.ref===ref)}));
const report={date:'2026-10-05',scope:'Active USB auxiliary mux milestone only; draft BQ25792/TPS25730 not included.',netlistPhysicalReferences:netRefs.length,bomPhysicalReferences:bomRefs.filter(r=>r!=='PACK').length,nonphysicalBomRows:bomRefs.filter(r=>r==='PACK'),missingNetlistReferences:missing,identityCheck,newPartIdentityChecks,newReferences:['U20','C124','C125','R124','R125'],reusedCapacitor:{references:'C122, C123, C124, C125',mpn:'LMK107B7105KA-T',lcsc:'C92806',fittedQuantity:capQty},newLines:[{reference:'U20',mpn:'TPS2116DRLR',lcsc:'C3235557',stockPrice:'unverified; excluded from priced totals'},{reference:'R124',mpn:'RC0603FR-07180KL',lcsc:'C123419',moq:100,observedTierUnitUsd:0.0012,stock:'unverified; listing page may be stale'},{reference:'R125',mpn:'RC0603FR-07100KL',lcsc:'C14675',note:'reused mapping; no new MOQ order'}],fittedSubtotalUsd:subtotal[0][0],inStockOrderSubtotalUsd:subtotal[1][0],formulaErrorMatches:errors,coveragePass:missing.length===0&&identityCheck.mpn.mismatches.length===0&&identityCheck.lcsc.mismatches.length===0,rendered:['usb-aux-bom-changed-parts.png','usb-aux-bom-order-pricing.png','usb-aux-bom-totals.png'],limitations:['U20 stock/price not verified.','R124 listing page may be stale; stock unverified.','Priced fitted estimate includes selected but unverified-stock R124 pricing; in-stock order subtotal excludes unverified stock.','Partial subtotals are not product cost.']};
await fs.writeFile(`${root}/ai-files/reports/usb-aux-bom-reconciliation.json`,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
