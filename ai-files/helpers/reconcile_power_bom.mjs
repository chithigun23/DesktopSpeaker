import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
console.log((await wb.inspect({kind:'workbook,sheet,table',maxChars:2500,tableMaxRows:2,tableMaxCols:6})).ndjson);
const sh=wb.worksheets.getItem('Selected BOM');
if(process.argv.includes('--passives')) {
 const data=JSON.parse(await fs.readFile('ai-files/reports/bom-passive-input.json','utf8'));
 let end=77;
 if(sh.getRange('A78').values[0][0]!=='C181'){
  const notes=sh.getRange('A79:S85').values;
  sh.getRange('A82:S88').copyFrom(sh.getRange('A79:S85'),'all');
  sh.getRange('A82:S88').values=notes;sh.getRange('A79:S81').clear({applyTo:'contents'});
  const additions=[['C181','eFuse startup-ramp 22nF50VX7R0603'],['C108','Additional PMID22uF25V1210'],['C109','Additional REGN10uF10V0805']];
  for(let i=0;i<3;i++){
   sh.getRange(`A${78+i}:S${78+i}`).copyFrom(sh.getRange('A61:S61'),'all');
   sh.getRange(`A${78+i}:S${78+i}`).values=[[additions[i][0],additions[i][1],null,null,null,1,null,null,null,null,null,null,null,null,'MPN open',null,null,null,null]];
  }
 }
 end=80;
 for(let r=11;r<=end;r++){
  const refs=String(sh.getRange(`A${r}`).values[0][0]??'').match(/\b[A-Z]+\d+\b/g)??[];
  const records=refs.map(ref=>data.byRef[ref]);
  if(!records.length||records.some(q=>!q))continue;
  if(new Set(records.map(q=>q.mpn)).size!==1)throw new Error('Mixed MPN row '+r);
  const q=records[0];const row=sh.getRange(`A${r}:S${r}`).values[0];
  row[2]=q.manufacturer;row[3]=q.mpn;row[4]=q.lcsc;
  if(q.moq_pcs!=null)row[6]=q.moq_pcs;
  if(q.order_multiple_pcs!=null)row[7]=q.order_multiple_pcs;
  if(q.quoted_tier_qty_pcs!=null)row[9]=q.quoted_tier_qty_pcs;
  if(q.unit_price_usd_at_tier!=null)row[10]=q.unit_price_usd_at_tier;
  if(q.stock_pcs!=null)row[13]=q.stock_pcs;
  row[14]=q.unit_price_usd_at_tier==null?'Selected; price/stock open':'Listing snapshot';
  row[15]=46300;row[16]='2026-10-05';row[18]=q.listing;
  sh.getRange(`A${r}:S${r}`).values=[row];
 }
 // Use one price and one MOQ order per MPN; retain circuit-specific rows.
 const groups=new Map();
 for(let r=11;r<=end;r++){
  const row=sh.getRange(`A${r}:S${r}`).values[0];if(!row[3])continue;
  if(!groups.has(row[3]))groups.set(row[3],[]);groups.get(row[3]).push({r,row});
 }
 for(const rows of groups.values()){
  const priced=rows.find(q=>typeof q.row[10]==='number');if(!priced)continue;
  for(const {r} of rows){
   for(const col of [6,7,9,10,13,14,15,16])if(priced.row[col]!=null)sh.getRangeByIndexes(r-1,col,1,1).values=[[priced.row[col]]];
  }
 }
 for(let r=11;r<=end;r++){
  sh.getRange(`I${r}`).formulas=[[`=IF(OR(D${r}="",G${r}="",H${r}=""),"",IF(COUNTIF($D$11:D${r},D${r})>1,0,ROUNDUP(MAX(SUMIF($D$11:$D$${end},D${r},$F$11:$F$${end}),G${r})/H${r},0)*H${r}))`]];
  sh.getRange(`L${r}`).formulas=[[`=IF(K${r}="","",ROUND(F${r}*K${r},4))`]];
  sh.getRange(`M${r}`).formulas=[[`=IF(OR(K${r}="",I${r}="",N${r}=""),"",IF(N${r}>=I${r},ROUND(I${r}*K${r},4),""))`]];
 }
 sh.getRange('E4:E5').formulas=[[`=ROUND(SUM(L11:L${end}),2)`],[`=ROUND(SUM(M11:M${end}),2)`]];
 sh.getRange('G4').values=[['Power passive selections updated2026-10-05; prices/stock are listing snapshots.']];
 sh.getRange('G5').values=[['MOQ orders consolidated by MPN; repeat rows show order quantity0.']];
 sh.getRange('B35').values=[['4.7uF50VX7R1206 VDD capacitor; effective-capacitance review open']];
 sh.getRange('B69').values=[['3.3k1206 discharge resistor; thermal/pulse qualification open']];
 sh.getRange('G6').values=[['Partial subtotal excludes unpriced parts, pack/switches, speakers and unresolved audio selections.']];
 sh.getRange('A83').values=[['U18 links a derived STEP with corrected exposed pad; manufacturer exact model remains unavailable.']];
 const open=wb.worksheets.getItem('Open selections');
 open.getRange('A9:E9').values=[['Remaining power passive/header/switch selections',null,null,'Partial','Captured resistors/decouplers selected; C103, headers/switches and final capacitor qualification remain open.']];
 open.getRange('E11').values=[['Regulator captured; full PFM/TCR/transient upper bound against codec5.25V maximum remains open.']];
 open.getRange('A16:E16').values=[['PMID capacitor qualification','CL32B226KAJNNNE','C309062','Selected; qualification open','C101/C108 now in BOM. Typical9V estimate17.60uF with tolerance/temp factors; not guaranteed.']];
 open.getRange('D16').format.wrapText=true;open.getRange('A16:H16').format.rowHeight=30;
 sh.getRange('A78:F80').format.wrapText=true;sh.getRange('A78:S80').format.rowHeight=42;
 sh.getRange('K11:M80').setNumberFormat('$0.0000');sh.getRange('P11:P80').setNumberFormat('yyyy-mm-dd');
 wb.recalculate();
 const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},summary:'final formula error scan'});
 await fs.writeFile('ai-files/reports/bom-passive-formula-scan.ndjson',errors.ndjson);
 const values=sh.getRange('A10:S80').values;
 const csv=values.map(row=>row.map(v=>v==null?'':`"${String(v).replaceAll('"','""')}"`).join(',')).join('\n')+'\n';
 const out=await SpreadsheetFile.exportXlsx(wb);await out.save(path);
 await fs.writeFile('ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv',csv);
 const totals=sh.getRange('E4:E5').values;
 await fs.writeFile('ai-files/reports/bom-reconciliation.json',JSON.stringify({date:'2026-10-05',fittedSubtotal:Math.round(totals[0][0]*100)/100,orderSubtotal:Math.round(totals[1][0]*100)/100,totalRows:70,pricedRows:values.slice(1).filter(r=>typeof r[10]==='number').length,orderConsolidatedByMPN:true,notCompleteProductCost:true},null,2));
 console.log('Passive BOM totals',totals);
 for(const [tag,range] of [['passive-selections','A68:M80'],['passive-totals','A2:M8']]){
  const img=await wb.render({sheetName:'Selected BOM',range,scale:1.2,format:'png'});await fs.writeFile(`ai-files/reports/bom-${tag}.png`,new Uint8Array(await img.arrayBuffer()));
 }
}
if(process.argv.includes('--open-preview')){
 const img=await wb.render({sheetName:'Open selections',range:'A7:H16',scale:1.2,format:'png'});await fs.writeFile('ai-files/reports/bom-open-selections.png',new Uint8Array(await img.arrayBuffer()));
}
if(process.argv.includes('--format')) {
 sh.getRange('A11:F77').format.wrapText=true;
 sh.getRange('A11:F77').format.verticalAlignment='center';
 sh.getRange('A11:S77').format.rowHeight=36;
 sh.getRange('A30:S30').format.rowHeight=96;
 sh.getRange('A58:S58').format.rowHeight=72;
 sh.getRange('B30').values=[['Charger / regulated-rail 22uF bulk capacitors']];
 sh.getRange('K62:K77').setNumberFormat('$0.0000');
 sh.getRange('L62:M77').setNumberFormat('$0.00');
 sh.getRange('P62:P77').setNumberFormat('yyyy-mm-dd');
 wb.recalculate();const output=await SpreadsheetFile.exportXlsx(wb);await output.save(path);
 const csv=sh.getRange('A10:S77').values.map(row=>row.map(v=>v==null?'':`"${String(v).replaceAll('"','""')}"`).join(',')).join('\n')+'\n';await fs.writeFile('ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv',csv);
}
if(process.argv.includes('--codec')) {
 // Guarded codec-rail reconciliation: update only U14, L2, R140, R141 and split R142.
 // Existing formulas and values outside these rows are retained; shared MPN order consolidation is recomputed below.
 const end=81;
 const put=(r,fields)=>{const row=sh.getRange(`A${r}:S${r}`).values[0];for(const [col,val] of Object.entries(fields))row[Number(col)]=val;sh.getRange(`A${r}:S${r}`).values=[row];};
 // Guarded D4/C103 source integration. Hidden schematic metadata is owned elsewhere;
 // preserve the existing displayed component ratings in the BOM's source mapping.
 for(const [r,ref,mpn,lcsc] of [[42,'D4','1N4148W-7-F','C83528'],[47,'C103','CC0603KRX7R9BB473','C107093']]){
  const old=sh.getRange(`A${r}:E${r}`).values[0];
  if(old[0]!==ref || (old[3] && old[3]!==mpn) || (old[4] && old[4]!==lcsc)) throw new Error(`${ref} BOM source guard: unexpected selection ${JSON.stringify(old)}`);
 }
 put(42,{0:'D4',1:'PD support diode; 1N4148W type',2:'Diodes Incorporated',3:'1N4148W-7-F',4:'C83528',5:1,6:20,7:20,9:20,10:0.0293,13:231360,14:'Listing snapshot',15:46300,16:'2026-10-05',17:'In stock 231,360; $0.0293 at MOQ 20. Datasheet: 100V VRRM, SOD-123, 300mA, low leakage.',18:'https://www.lcsc.com/product-detail/C83528.html'});
 put(47,{0:'C103',1:'Charger 47nF X7R / 10V minimum bootstrap capacitor',2:'YAGEO',3:'CC0603KRX7R9BB473',4:'C107093',5:1,6:50,7:50,9:50,10:0.0077,13:1537650,14:'Listing snapshot',15:46300,16:'2026-10-05',17:'In stock 1,537,650; $0.0077 at MOQ 50. Exact 47nF 50V X7R ±10%, 0603. Datasheet has no guaranteed DC-bias curve.',18:'https://www.lcsc.com/product-detail/Multilayer-Ceramic-Capacitors-MLCC-SMD-SMT_YAGEO-CC0603KRX7R9BB473_C107093.html'});
 put(31,{0:'U14',1:'5 V codec logic buck-boost regulator',2:'Texas Instruments',3:'TPS63802DLAR',4:'C2845237',5:1,6:1,7:1,9:1,10:0.9773,13:16705,14:'Listing snapshot',15:46299,16:'2026-10-04',17:'Same selected part and listing snapshot as U15; stock/price snapshot, not quote.',18:'https://www.lcsc.com/product-detail/C2845237.html'});
 put(63,{0:'L2',1:'0.47uH codec buck-boost inductor',2:'Coilcraft',3:'XFL4015-471MEC',4:'C18221164',5:1,6:1,7:1,9:1,10:4.2515,13:2773,14:'Listing snapshot',15:46299,16:'2026-10-04',17:'Same MPN as L3; listing stock and tier are shared.',18:'https://www.lcsc.com/product-detail/C18221164.html'});
 const oldD7=sh.getRange('A66:E66').values[0];
 if(!(['D7','D7, D9'].includes(oldD7[0])) || oldD7[2]!=='Diodes Incorporated' || oldD7[3]!=='BZT52C12-7-F' || oldD7[4]!=='C124196') throw new Error('D7 merge guard: unexpected selected part '+JSON.stringify(oldD7));
 put(66,{0:'D7, D9',1:'PMOS gate 12V clamp',2:'Diodes Incorporated',3:'BZT52C12-7-F',4:'C124196',5:2,17:'D7 and D9 use the same clamp; retained the existing 2026-10-04 listing snapshot price and MOQ.'});
 const oldR140=sh.getRange('C70:E70').values[0];
 if(!(['Stackpole Electronics','UNI-ROYAL','SAE'].includes(oldR140[0])) || !(['RMCF0603FT787K','0603WAF7873T5E','1RC0603F7872'].includes(oldR140[1]))) throw new Error('R140 source guard: unexpected existing selection '+JSON.stringify(oldR140));
 put(70,{0:'R140',1:'78.7k 1% codec feedback divider resistor',2:'SAE',3:'1RC0603F7872',4:'C54531588',5:1,6:100,7:100,9:100,10:0.002,13:4700,14:'Listing snapshot',15:46300,16:'2026-10-05',17:'In stock 4,700; tier $0.002 at 100+. Datasheet confirms 0603, ±1%, ±100ppm/°C and −55 to +155°C.',18:'https://www.lcsc.com/product-detail/C54531588.html'});
 const r71=sh.getRange('A71:S71').values[0];sh.getRange('A81:S81').copyFrom(sh.getRange('A71:S71'),'all');
 const oldR141=sh.getRange('C71:E71').values[0];
 if(oldR141[0]!=='YAGEO' || !(['AC0603FR-0791KL','RC0603FR-079K1L'].includes(oldR141[1]))) throw new Error('R141 source guard: unexpected existing selection '+JSON.stringify(oldR141));
 put(71,{0:'R141',1:'9.1k 1% codec feedback divider resistor',2:'YAGEO',3:'RC0603FR-079K1L',4:'C114639',5:1,6:100,7:100,9:100,10:0.0034,13:296500,14:'Listing snapshot',15:46300,16:'2026-10-05',17:'In stock 296,500; tier $0.0034 at 100+. 0603, ±1%, ±100ppm/°C, −55 to +155°C. Distinct MPN from R151.',18:'https://www.lcsc.com/product-detail/C114639.html'});
 put(81,{0:'R142',1:'100k EN pulldown resistor',2:'YAGEO',3:'RC0603FR-07100KL',4:'C14675',5:1,6:100,7:100,9:100,10:0.0036,13:7813400,14:'Listing snapshot',15:46300,16:'2026-10-05',17:'Existing selected resistor; separated from R141 after divider value change.',18:'https://www.lcsc.com/product-detail/C14675.html'});
 // Retain copied row style for split R142 and extend the existing formula ranges by one row.
 for(let r=11;r<=end;r++){
  sh.getRange(`I${r}`).formulas=[[`=IF(OR(D${r}="",G${r}="",H${r}=""),"",IF(COUNTIF($D$11:D${r},D${r})>1,0,ROUNDUP(MAX(SUMIF($D$11:$D$${end},D${r},$F$11:$F$${end}),G${r})/H${r},0)*H${r}))`]];
  sh.getRange(`L${r}`).formulas=[[`=IF(K${r}="","",ROUND(F${r}*K${r},4))`]];
  sh.getRange(`M${r}`).formulas=[[`=IF(OR(K${r}="",I${r}="",N${r}=""),"",IF(N${r}>=I${r},ROUND(I${r}*K${r},4),""))`]];
 }
 sh.getRange('E4:E5').formulas=[[`=SUM(L11:L${end})`],[`=SUM(M11:M${end})`]];
 sh.getRange('G4').values=[['Codec power rows reconciled 2026-10-05; all stock/prices are listing snapshots.']];
 sh.getRange('G6').values=[['Partial subtotal excludes open D8, battery, speakers and audio selections; not full product cost.']];
 sh.getRange('A71:F71').format.wrapText=true;sh.getRange('A81:F81').format.wrapText=true;sh.getRange('A81:S81').format.rowHeight=36;
 sh.getRange('K11:M81').setNumberFormat('$0.0000');sh.getRange('L11:M81').setNumberFormat('$0.00');sh.getRange('P11:P81').setNumberFormat('yyyy-mm-dd');
 const os=wb.worksheets.getItem('Open selections');
 os.getRange('D11:E11').values=[['Open','Forced-PWM DC estimate: 4.60004–5.05869V (nominal 4.82418V), including resistor/reference limits and ±100nA feedback bias. Startup uses PFM; startup excursion, ripple, load-step and overshoot still need PCM2902C qualification.']];
 os.getRange('A9:E9').values=[['Remaining power passive/header/switch selections',null,null,'Partial','D4 and C103 selected; headers, switches and effective-capacitance qualification remain open.']];
 os.getRange('E11').format.wrapText=true;os.getRange('A11:H11').format.rowHeight=42;
 wb.recalculate();
 const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},summary:'codec BOM formula error scan'});
 await fs.writeFile('ai-files/reports/codec-bom-formula-scan.ndjson',errors.ndjson);
 const totals=sh.getRange('E4:E5').values;
 const output=await SpreadsheetFile.exportXlsx(wb);await output.save(path);
 const bomRows=sh.getRange(`A10:S${end}`).values;
 const csv=bomRows.map(row=>row.map(v=>v==null?'':`"${String(v).replaceAll('"','""')}"`).join(',')).join('\n')+'\n';
 await fs.writeFile('ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv',csv);
 const unpricedRefs=[...new Set(bomRows.slice(1).filter(row=>row[0] && (row[10]==null || row[10]==='')).flatMap(row=>String(row[0]).match(/\b[A-Z]+\d+\b/g)??[]))];
 await fs.writeFile('ai-files/reports/codec-bom-reconciliation.json',JSON.stringify({date:'2026-10-05',fittedSubtotalUsd:Math.round(totals[0][0]*10000)/10000,fittedSubtotalDisplayedUsd:Math.round(totals[0][0]*100)/100,orderSubtotalUsd:Math.round(totals[1][0]*10000)/10000,orderSubtotalDisplayedUsd:Math.round(totals[1][0]*100)/100,unpricedRefs,otherOpenUnpricedRefs:unpricedRefs,newlyUnpricedRefs:[],electricalQualificationOpen:['C103 effective capacitance under BTST-SW DC bias has no guaranteed value from the YAGEO datasheet simulation; confirm effective capacitance need during charger qualification'],excludedProductItems:['PACK','battery','speakers','open audio selections'],notCompleteProductCost:true,changes:['U14 mapped to selected TPS63802DLAR C2845237 same as U15','L2 mapped to Coilcraft XFL4015-471MEC C18221164 same as L3','R140 changed to SAE 1RC0603F7872 C54531588 (78.7kΩ); in-stock listing snapshot captured','R141 changed to YAGEO RC0603FR-079K1L C114639 (9.1kΩ); in-stock listing snapshot; distinct from R151','R142 retained YAGEO RC0603FR-07100KL C14675','D7 and D9 merged as two BZT52C12-7-F clamps; existing listing snapshot retained','D4 selected Diodes Incorporated 1N4148W-7-F C83528; MOQ/multiple 20','C103 selected YAGEO CC0603KRX7R9BB473 C107093; MOQ/multiple 50; effective DC-bias capacitance remains unqualified']},null,2));
 await fs.writeFile('ai-files/reports/codec-resistor-sourcing.json',JSON.stringify({date:'2026-10-05',rows:[{ref:'R140',manufacturer:'SAE',mpn:'1RC0603F7872',lcsc:'C54531588',value_ohm:78700,package:'0603',tolerance_percent:1,tcr_ppm_per_c:100,temperature_c:[-55,155],power_w:0.1,voltage_v:75,stock_pcs:4700,moq_pcs:100,multiple_pcs:100,price_usd_at_100:0.002,tiers_usd:{100:0.002,1000:0.0015,5000:0.0013,10000:0.0012,50000:0.001},listing:'https://www.lcsc.com/product-detail/C54531588.html',datasheet:'../datasheets/SAE_C54531588_1RC0603F7872.pdf'},{ref:'R141',manufacturer:'YAGEO',mpn:'RC0603FR-079K1L',lcsc:'C114639',value_ohm:9100,package:'0603',tolerance_percent:1,tcr_ppm_per_c:100,temperature_c:[-55,155],power_w:0.1,voltage_v:75,stock_pcs:296500,moq_pcs:100,multiple_pcs:100,price_usd_at_100:0.0034,tiers_usd:{100:0.0034,1000:0.0028,5000:0.0025,10000:0.0024,50000:0.0022},listing:'https://www.lcsc.com/product-detail/C114639.html',datasheet:'../datasheets/YAGEO_C114639_RC0603FR-079K1L.pdf'}],basis:'Current LCSC product-page listings and manufacturer-family datasheets captured 2026-10-05. Stock/price are listing snapshots, not quotes.'},null,2));
 console.log('Codec BOM totals',totals);
 for(const [tag,range] of [['codec-parts','A30:S33'],['codec-d7-clamp','A66:S66'],['codec-resistors','A70:S73'],['codec-resistor-split','A79:S81'],['codec-d4-c103','A40:O48'],['codec-totals','A2:M8']]){const img=await wb.render({sheetName:'Selected BOM',range,scale:1.2,format:'png'});await fs.writeFile(`ai-files/reports/${tag}.png`,new Uint8Array(await img.arrayBuffer()));}
}
if(process.argv.includes('--u19')) {
 // Guarded U19 addition: append one new selected physical reference after existing 70 BOM rows;
 // preserve every existing row, source field, note, style, and consolidation ordering.
 const end=82;
 if(sh.getRange('A81').values[0][0]!=='R142') throw new Error('U19 guard: expected existing final BOM row R142');
 if(sh.getRange('D82').values[0][0]) throw new Error('U19 guard: target row 82 is not empty');
 const row=[
  'U19','USB PD controller 5.0V VDD LDO','Texas Instruments','TPS7B8450QWDRBRQ1','C3751394',
  1,1,1,null,1,1.3452,null,null,1,'Listing snapshot',46300,'2026-10-05',
  'LCSC snapshot 2026-10-05: 1 pc in stock; $1.3452 at 1+, MOQ/multiple 1 (standard pack 3000; LCSC allows single-piece purchase). Stock is thin and may sell before ordering. TI TPS7B84-Q1: fixed 5V, 150mA, 40V input; startup/surge/dropout and thermal qualification open. Datasheet: ../datasheets/TPS7B84-Q1.pdf.',
  'https://www.lcsc.com/product-detail/C3751394.html'
 ];
 sh.getRange('A82:S82').copyFrom(sh.getRange('A65:S65'),'all');
 sh.getRange('A82:S82').values=[row];
 for(let r=11;r<=end;r++){
  sh.getRange(`I${r}`).formulas=[[`=IF(OR(D${r}="",G${r}="",H${r}=""),"",IF(COUNTIF($D$11:D${r},D${r})>1,0,ROUNDUP(MAX(SUMIF($D$11:$D$${end},D${r},$F$11:$F$${end}),G${r})/H${r},0)*H${r}))`]];
  sh.getRange(`L${r}`).formulas=[[`=IF(K${r}="","",ROUND(F${r}*K${r},4))`]];
  sh.getRange(`M${r}`).formulas=[[`=IF(OR(K${r}="",I${r}="",N${r}=""),"",IF(N${r}>=I${r},ROUND(I${r}*K${r},4),""))`]];
 }
 sh.getRange('E4:E5').formulas=[[`=ROUND(SUM(L11:L${end}),2)`],[`=ROUND(SUM(M11:M${end}),2)`]];
 sh.getRange('G4').values=[['BOM updated 2026-10-05 with U19; all stock/prices are listing snapshots.']];
 sh.getRange('G6').values=[['Partial subtotal excludes unpriced parts, pack, switches, speakers and open audio selections; not full product cost.']];
 sh.getRange('B35').values=[['4.7uF / 50V U19 input capacitor; prove effective capacitance meets TI minimum at worst DC bias/tolerance/temp.']];
 sh.getRange('A82:F82').format.wrapText=true;sh.getRange('A82:S82').format.rowHeight=54;
 sh.getRange('K82:M82').setNumberFormat('$0.0000');sh.getRange('L82:M82').setNumberFormat('$0.00');sh.getRange('P82').setNumberFormat('yyyy-mm-dd');
 const os=wb.worksheets.getItem('Open selections');
 os.getRange('A11:H11').values=[['USB PD controller VDD source LDO','TPS7B8450QWDRBRQ1','C3751394','Selected; qualification open','U19 supplies nominal 5V from raw PD VBUS. Verify surge/transient coordination, dropout at low 5V input, thermal dissipation, and C5 effective capacitance versus TI minimum.',null,null,'https://www.lcsc.com/product-detail/C3751394.html']];
 os.getRange('A11:E11').format.wrapText=true;os.getRange('A11:H11').format.rowHeight=60;
 wb.recalculate();
 const scan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:200},summary:'U19 BOM formula error scan'});
 const scanRows=scan.ndjson.split('\n').filter(Boolean);
 const scanMatchCount=Number(scan.ndjson.match(/matched (\d+) entries/)?.[1]??scanRows.length);
 const totals=sh.getRange('E4:E5').values;
 const fittedExact=sh.getRange(`L11:L${end}`).values.flat().reduce((a,v)=>a+(typeof v==='number'?v:0),0);
 const orderExact=sh.getRange(`M11:M${end}`).values.flat().reduce((a,v)=>a+(typeof v==='number'?v:0),0);
 const report={date:'2026-10-05',newPhysicalReference:'U19',manufacturer:'Texas Instruments',mpn:'TPS7B8450QWDRBRQ1',lcsc:'C3751394',function:'Fixed 5.0V, 150mA, 40V input LDO supplying USB-PD VDD from raw PD VBUS',lcscSnapshot:{accessed:'2026-10-05',stockPcs:1,unitPriceUsd:1.3452,priceTierQty:1,moqPcs:1,multiplePcs:1,standardPackPcs:3000,source:'https://www.lcsc.com/product-detail/C3751394.html',note:'One unit shown in stock, one-piece purchase accepted; recheck at purchase.'},datasheet:'../datasheets/TPS7B84-Q1.pdf',fittedSubtotalUsd:totals[0][0],fittedSubtotalExactUsd:fittedExact,orderSubtotalUsd:totals[1][0],orderSubtotalExactUsd:orderExact,bomPhysicalRows:72,openQualifications:['Raw PD surge/transient coordination at U19 input remains unverified.','Regulator dropout/output level at minimum 5V input and thermal dissipation remain open.','C5 must retain TI-required effective capacitance at worst DC bias, tolerance and temperature; verify minimum.'],formulaScan:{matches:scanMatchCount,summary:scan.ndjson},render:{parts:'vdd-ldo-bom-parts.png',openSelections:'vdd-ldo-open-selections.png',totals:'vdd-ldo-bom-totals.png'}};
 const img1=await wb.render({sheetName:'Selected BOM',range:'A80:S82',scale:1.1,format:'png'});await fs.writeFile('ai-files/reports/vdd-ldo-bom-parts.png',new Uint8Array(await img1.arrayBuffer()));
 const img2=await wb.render({sheetName:'Selected BOM',range:'A2:M8',scale:1.2,format:'png'});await fs.writeFile('ai-files/reports/vdd-ldo-bom-totals.png',new Uint8Array(await img2.arrayBuffer()));
 const img3=await wb.render({sheetName:'Open selections',range:'A9:H12',scale:1.2,format:'png'});await fs.writeFile('ai-files/reports/vdd-ldo-open-selections.png',new Uint8Array(await img3.arrayBuffer()));
 const output=await SpreadsheetFile.exportXlsx(wb);await output.save(path);
 const csv=sh.getRange(`A10:S${end}`).values.map(r=>r.map(v=>v==null?'':`"${String(v).replaceAll('"','""')}"`).join(',')).join('\n')+'\n';
 await fs.writeFile('ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv',csv);
 await fs.writeFile('ai-files/reports/vdd-ldo-bom-update.json',JSON.stringify(report,null,2)+'\n');
 console.log('U19 BOM update',JSON.stringify({totals,formulaErrorMatches:scanRows.length}));
}
if(!process.argv.includes('--review')&&!process.argv.includes('--format')&&!process.argv.includes('--passives')&&!process.argv.includes('--codec')&&!process.argv.includes('--u19')) {
if(sh.getRange('D25').values[0][0]!=='TMUX1511PWR')throw new Error('One-shot reconciliation already applied; use --review.');
const fresh=(ref,fn,maker,mpn,id,qty,moq,mult,price,stock)=>[
 ref,fn,maker,mpn,id,qty,moq??null,mult??null,null,moq??null,price??null,null,null,stock??null,
 stock==null?'Stock/price unverified':'Listing snapshot',stock==null?null:46299,stock==null?null:'2026-10-04',null,
 `https://www.lcsc.com/product-detail/${id}.html`];
const open=(ref,fn,qty)=>[ref,fn,null,null,null,qty,null,null,null,null,null,null,null,null,'MPN open',null,null,null,null];
sh.getRange('A25:S25').values=[fresh('U13, U16, U17','Low-current gauge signal isolation','TI','TS5A3167DBVR','C128416',3,5,5,.3187,11755)];
sh.getRange('A28:S28').values=[fresh('D6','Raw VBUS 22V standoff TVS','TI','TVS2200DRVR','C523793',1,5,5,.4672,3285)];
sh.getRange('A30').values=[['C104, C105, C107, C140, C141, C142, C150, C152, C153, C154']];
sh.getRange('F30').values=[[10]];
sh.getRange('A33:B33').values=[['C2','100nF / 50V capacitor']];sh.getRange('F33').values=[[1]];
sh.getRange('A34:B34').values=[['C4, C6, C180','1uF / 50V capacitor; effective capacitance open']];sh.getRange('F34').values=[[3]];
sh.getRange('B35').values=[['4.7uF / 50V capacitor; effective capacitance open']];
sh.getRange('A37:B37').values=[['R2','1k resistor']];sh.getRange('F37').values=[[1]];
sh.getRange('A58:B58').values=[['C120, C121, C130, C131, C132, C143, C151','100nF / 10V-or-higher 0603 decoupling']];sh.getRange('F58').values=[[7]];
const added=[
 fresh('U15','3.8V Bluetooth buck-boost','TI','TPS63802DLAR','C2845237',1,1,1,.9773,16705),
 fresh('L2','5V boost 1uH inductor','Bourns','SRN6045TA-1R0Y','C3013497',1),
 fresh('L3','Bluetooth buck-boost 0.47uH inductor','Coilcraft','XFL4015-471MEC','C18221164',1,1,1,4.2515,2773),
 fresh('U18','USB input hardware overvoltage cutoff','TI','TPS26600PWPR','C544399',1,1,1,1.6339,4931),
 fresh('D7','PMOS gate 12V clamp','Diodes Incorporated','BZT52C12-7-F','C124196',1,10,10,.0771,26150),
 fresh('D8','Protected VBUS clamp; manufacturer-specific','Taiwan Semiconductor','SMA6J10A M2G','C2444429',1),
 open('C10','100nF / 25V capacitor',1),open('R4','3.3k 1206 discharge resistor; pulse-rated MPN open',1),
 open('R140','732k 1% feedback resistor',1),open('R141, R142','100k regulator feedback / EN resistors',2),
 open('R150','604k 1% feedback resistor',1),open('R151','91k 1% feedback resistor',1),
 open('R152, R153, R154','100k EN / MODE / bleeder resistors',3),
 open('R180','100k 1% OVP divider resistor',1),open('R181','12.1k 1% OVP divider resistor',1),open('R182','5.36k 1% current-limit resistor',1)
];
const end=61+added.length;
sh.getRange(`A${end+2}:S${end+8}`).copyFrom(sh.getRange('A63:S69'),'all');
sh.getRange('A63:S69').clear({applyTo:'contents'});
for(let i=0;i<added.length;i++)sh.getRange(`A${62+i}:S${62+i}`).copyFrom(sh.getRange('A61:S61'),'all');
sh.getRange(`A62:S${end}`).values=added;
for(let r=11;r<=end;r++){
 sh.getRange(`I${r}`).formulas=[[`=IF(OR(G${r}="",H${r}=""),"",ROUNDUP(MAX(F${r},G${r})/H${r},0)*H${r})`]];
 sh.getRange(`L${r}`).formulas=[[`=IF(K${r}="","",ROUND(F${r}*K${r},2))`]];
 sh.getRange(`M${r}`).formulas=[[`=IF(OR(K${r}="",I${r}="",N${r}=""),"",IF(N${r}>=I${r},ROUND(I${r}*K${r},2),""))`]];
}
sh.getRange('E4:E5').formulas=[[`=SUM(L11:L${end})`],[`=SUM(M11:M${end})`]];
sh.getRange('G4').values=[['Power circuitry reconciled 2026-10-04; listing prices/stock are snapshots.']];
sh.getRange('G6').values=[['Partial subtotal excludes unpriced passives, L2/D8, battery, speakers and open audio selections.']];
sh.getRange(`A${end+3}`).values=[['New power rows replace obsolete TMUX1511 and SMBJ10A selections. U18 exact STEP remains open.']];
const os=wb.worksheets.getItem('Open selections');
os.getRange('B12').values=[['BM83 downstream signal isolation and shutdown sequencing remain open; regulator captured.']];
wb.recalculate();
const totals=sh.getRange('E4:E5').values;
console.log('Reconciled totals',JSON.stringify(totals));
const output=await SpreadsheetFile.exportXlsx(wb);await output.save(path);
const csv=sh.getRange(`A10:S${end}`).values.map(row=>row.map(v=>v==null?'':`"${String(v).replaceAll('"','""')}"`).join(',')).join('\n')+'\n';
await fs.writeFile('ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv',csv);
await fs.writeFile('ai-files/reports/bom-reconciliation.json',JSON.stringify({date:'2026-10-04',fittedSubtotal:totals[0][0],orderSubtotal:totals[1][0],pricedRows:sh.getRange(`K11:K${end}`).values.filter(r=>typeof r[0]==='number').length,totalRows:end-10,unverifiedStock:['C3013497','C2444429'],notCompleteProductCost:true},null,2));
}
if(!process.argv.includes('--u19')){
for(const [tag,range] of [['new-power','A62:F67'],['replaced-power','A24:F31'],['totals','A2:M8']]){
 try{const preview=await wb.render({sheetName:'Selected BOM',range,scale:1.2,format:'png'});await fs.writeFile(`ai-files/reports/bom-${tag}.png`,new Uint8Array(await preview.arrayBuffer()));}catch(e){console.log('Preview failed',tag,e.message);}
}
const state={};
for(let i=0;i<wb.worksheets.items.length;i++){
  const sh=wb.worksheets.getItemAt(i);
  state[sh.name]={values:sh.getUsedRange().values,formulas:sh.getUsedRange().formulas};
}
await fs.writeFile('ai-files/reports/bom-reconcile-input.json',JSON.stringify(state,null,2));
try {
 const before=await wb.render({sheetName:'Selected BOM',range:'A1:F12',scale:1.5,format:'png'});
 await fs.writeFile('ai-files/reports/bom-before-reconcile.png',new Uint8Array(await before.arrayBuffer()));
} catch(error) { console.log('Render unavailable:',error.message); }
}
