// Integrates the TPS25730D USB_PD and BQ25792 Battery_Charger candidates into the Selected BOM (2026-10-05).
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const root='/home/chithi/Desktop/DesktopSpeaker';
const xlsx=`${root}/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx`;
const csvPath=`${root}/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv`;
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(xlsx));
const sh=wb.worksheets.getItem('Selected BOM');
const oldEnd=87;
let rows=sh.getRange(`A11:S${oldEnd}`).values.map(r=>[...r]);
const foot=sh.getRange('A88:A92').values.map(r=>r[0]);
const URL=c=>`https://www.lcsc.com/product-detail/${c}.html`;
const byRef=k=>{const i=rows.findIndex(r=>r[0]===k); if(i<0) throw new Error('row not found: '+k); return i;};
const del=k=>rows.splice(byRef(k),1);
const price=(ref,fn,mfr,mpn,lcsc,qty,moq,unit,stock,note)=>[ref,fn,mfr,mpn,lcsc,qty,moq,moq,null,moq,unit,null,null,stock,'Listing snapshot',46300,'2026-10-05',note??null,URL(lcsc)];
const open=(ref,fn,mfr,mpn,lcsc,qty,note)=>[ref,fn,mfr,mpn,lcsc,qty,null,null,null,null,null,null,null,null,'Stock/price unverified',null,null,note,lcsc?URL(lcsc):null];
const set=(k,row)=>{rows[byRef(k)]=row;};
const ins=(afterKey,row)=>rows.splice(byRef(afterKey)+1,0,row);

// obsolete STUSB4500 / old PD stage / BQ25895 rows
for(const k of ['Q1, Q2','C1, C3','R1','R2','R6, R9','R13','R11','U18','D4','D7, D9','D8','R4','R180','R181','R182','C10','C181','C108','C109','C101','R142x'].filter(k=>k!=='R142x')) del(k);
set('U4',open('U4','Battery charger, 5-20 V 1S buck-boost','TI','BQ25792RQMR','C2862876',1,'Replaces BQ25895. Review snapshot: US$2.0489 (1+), 4,970 in stock; not re-verified at this BOM freeze, so excluded from priced subtotal.'));
rows[byRef('U4')].splice(10,1,null);
set('U11',open('U11','USB-C PD 5-20 V sink controller','TI','TPS25730DREFR','C22438973',1,'Replaces STUSB4500 and Q1/Q2/U18/U19-front-end parts. Review snapshot: US$3.0105 (1+), 381 in stock; not re-verified.'));
set('Q100, Q104',price('Q100, Q101, Q102, Q104','Charger CE, ILIM_HIZ and gauge-enable NMOS','Nexperia','2N7002,215','C65189',4,20,0.0183,274640));
set('C2',price('C2','TPS25730D CVBUS 4.7uF / 50V X7R 1210','Samsung Electro-Mechanics','CL32B475KBUYNNE','C170099',1,5,0.1367,57880,'Alt: GRM32ER71H475KA88L C86052'));
set('C4, C6, C180',price('C184','1uF / 50V capacitor; effective capacitance open','Samsung Electro-Mechanics','CL21B105KBFNNNE','C28323',1,10,0.0403,1363910,'CL21B105KBFNNNE; effective capacitance at bias not proven.'));
// R10 is now 200k with no MPN selected
set('R10, R55',open('R10','PD 200k 1% resistor (MPN open)',null,null,null,1,'Sheet value 200k 1%; MPN/LCSC unselected.'));
set('R103, R106',price('R106','Charger INT pull-up 10k','YAGEO','RC0603FR-0710KL','C98220',1,100,0.0035,11102500));
// 10k group on USB_PD
ins('R106',price('R11, R13, R14, R15, R18','TPS25730D 10k 1% resistors (CC/ADC, I2C pull-ups R14/R15, pin 36 R18)','YAGEO','RC0603FR-0710KL','C98220',5,100,0.0034,7736700));
// 100k groups
ins('R107',price('R103, R109, R110, R111','Charger 100k pull-up/down resistors','YAGEO','RC0603FR-07100KL','C14675',4,100,0.0036,7813400));
ins('R107',price('R12, R16, R17','TPS25730D 100k pull-ups / VIN_3V3 resistor','YAGEO','RC0603FR-07100KL','C14675',3,100,0.0036,7813400));
set('R102',price('R102','Charger 4.7k resistor','YAGEO','RC0603FR-074K7L','C99782',1,100,0.0011,1575400));
ins('R102',price('R108','Charger 180k threshold resistor','YAGEO','RC0603FR-07180KL','C123419',1,100,0.0012,null));
ins('R108',price('R112','Charger 100R resistor','YAGEO','RC0603FR-07100RL','C105588',1,100,0.0024,2943700));
// capacitors
set('C100',price('C100, C101, C108, C111, C112','BQ25792 VBUS/PMID 10uF / 50V X7R 1210 bank','Samsung Electro-Mechanics','CL32B106KBJNNNE','C138687',5,1,0.1571,183897,'Review snapshot 2026-10-05; effective capacitance at bias per bq25792 ceramic review.'));
set('C102',price('C102, C109, C181, C185','10uF / 10V X7R 0805 capacitors (charger REGN/PD CVIN_3V3)','Samsung Electro-Mechanics','CL21B106KPQNNNE','C32635',4,10,0.093,230700));
set('C103',price('C103, C110','47nF X7R / 50V bootstrap capacitors','YAGEO','CC0603KRX7R9BB473','C107093',2,50,0.0077,1537650));
ins('C103, C110',price('C113, C114, C115','BQ25792 VBUS/PMID/SYS 100nF/50V X7R 0402 bypass','Murata','GRM155R71H104KE14D','C77020',3,100,0.007,777000,'Footprint DesktopSpeaker:PD_C_0402 (no 3D model)'));
ins('C113, C114, C115',open('C182, C183','TPS25730D CC1/CC2 330pF C0G filters (MPN open)',null,null,null,2,'Unselected 0603 C0G part.'));
// 22uF row gains C6
const i21=byRef('C104, C105, C107, C140, C141, C142, C150, C152, C153, C154'); rows[i21][0]='C6, C104, C105, C107, C140, C141, C142, C150, C152, C153, C154'; rows[i21][5]=11;
ins('C113, C114, C115',price('D7','TPS25730D VBUS-to-GND Schottky','Diodes Incorporated','1N5819HW-7-F','C82544',1,10,0.057,137330,'40V/1A SOD-123; leakage not bench-checked; alt B5819W SL C8598'));
ins('L1',open('Q103','Ship FET (pack disconnect)','Texas Instruments','CSD17579Q3A','C97376',1,'Price/stock not verified.'));
// order qty: shared MPN lookup
const end=10+rows.length;
sh.getRange(`A11:S${oldEnd+6}`).clear({applyTo:'contents'});
if(end>oldEnd) for(let r=oldEnd+1;r<=end;r++) sh.getRange(`A${r}:S${r}`).copyFrom(sh.getRange(`A${oldEnd}:S${oldEnd}`),'formats');
sh.getRange(`A11:S${end}`).values=rows;
for(let r=11;r<=end;r++){
 sh.getRange(`I${r}`).formulas=[[`=IF(OR(D${r}="",G${r}="",H${r}=""),"",IF(COUNTIF($D$11:D${r},D${r})>1,0,ROUNDUP(MAX(SUMIF($D$11:$D$${end},D${r},$F$11:$F$${end}),G${r})/H${r},0)*H${r}))`]];
 sh.getRange(`L${r}`).formulas=[[`=IF(K${r}="","",ROUND(F${r}*K${r},4))`]];
 sh.getRange(`M${r}`).formulas=[[`=IF(OR(K${r}="",I${r}="",N${r}=""),"",IF(N${r}>=I${r},ROUND(I${r}*K${r},4),""))`]];
}
const fl=[...new Set(foot.filter(Boolean))]; 
fl.forEach((t,i)=>sh.getRange(`A${end+2+i}`).values=[[t]]);
for(let r=end+2+fl.length;r<=oldEnd+7;r++) sh.getRange(`A${r}:S${r}`).clear({applyTo:'all'});
sh.getRange(`A${end+2+fl.length}`).values=[['U4/U11/Q103 prices are review-time snapshots or unverified; C2/C6/D7/R10/C182/C183 per candidate review; TPS25730D 5-20 V integration 2026-10-05.']];
sh.getRange('E4:E5').formulas=[[`=ROUND(SUM(L11:L${end}),2)`],[`=ROUND(SUM(M11:M${end}),2)`]];
sh.getRange('G4').values=[['BOM updated 2026-10-05: TPS25730D USB_PD and BQ25792 charger integrated; stock/prices are listing snapshots or marked unverified.']];
sh.getRange('K11:M'+end).setNumberFormat('$0.0000');
sh.getRange('L11:M'+end).setNumberFormat('$0.00');
sh.getRange('P11:P'+end).setNumberFormat('yyyy-mm-dd');
// candidate-fix rows now merged
try{ wb.worksheets.getItem('Candidate fixes').delete(); }catch(e){ console.log('no candidate sheet delete: '+e.message); }
wb.recalculate();
const errs=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'scan'});
console.log(errs.ndjson.slice(0,300));
const out=await SpreadsheetFile.exportXlsx(wb); await out.save(xlsx);
const vals=sh.getRange(`A10:S${end}`).values;
await fs.writeFile(csvPath,vals.map(r=>r.map(v=>v==null?'':`"${String(v).replaceAll('"','""')}"`).join(',')).join('\n')+'\n');
console.log('end',end,'E4:E5',JSON.stringify(sh.getRange('E4:E5').values));
