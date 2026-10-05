// Guarded: rebuild passive rows of the Selected BOM from ai-files/reports/passive-repackage-map.json (merged by new MPN).
// Non-passive rows and C275 (polymer, unchanged) are preserved in order. Run from project root.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx', csvPath='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv';
const map=JSON.parse(await fs.readFile('ai-files/reports/passive-repackage-map.json','utf8'));
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sh=wb.worksheets.getItem('Selected BOM');
const FIRST=11, LASTOLD=114;
if(String(sh.getRange('A114').values[0][0])!=='R260 (R256 DNP)') throw new Error('unexpected layout / already applied');
const rows=sh.getRange(`A${FIRST}:S${LASTOLD}`).values;
const isPas=s=>s.split(',').every(t=>/^(R|C|FB)\d+/.test(t.trim()));
const keep=[], oldByMpn={};
for(const r of rows){ if(isPas(String(r[0])) && r[3]!=='EEH-ZA1E101P'){ (oldByMpn[r[3]] ||= r); } else keep.push(r); }
const nat=(a,b)=>{const f=s=>[s[0]==='F'?'FB':s[0],parseInt(s.replace(/\D/g,''))]; const x=f(a),y=f(b); return x[0]<y[0]?-1:x[0]>y[0]?1:x[1]-y[1];};
const groups={};
for(const [ref,p] of Object.entries(map)) (groups[p.mpn] ||= {p,refs:[],vals:new Set(),oldfp:new Set(),oldm:new Set()}, groups[p.mpn]).refs.push(ref);
for(const [ref,p] of Object.entries(map)){ const g=groups[p.mpn]; g.vals.add(p.value); g.oldfp.add(p.old_fp.replace('PD_','')); g.oldm.add(p.old_mpn||'(none)'); }
const PK={'R_0402':'0402','C_0402':'0402','C_0805':'0805'};
const NEWPRICE={C60491:[0.001,726500],C60490:[0.0005,5338600],C29266:[0.0023,4764100]};
const newRows=[];
const names=Object.keys(groups).sort((a,b)=>{const ra=groups[a].refs[0],rb=groups[b].refs[0]; return nat(ra,rb)});
for(const mpn of names){
  const g=groups[mpn], p=g.p; g.refs.sort(nat);
  const pkg=p.fp.startsWith('R_0402')||p.fp.startsWith('C_0402')?'0402':'0805';
  const dnp=g.refs.filter(r=>r==='R256');
  const fitted=g.refs.length-dnp.length;
  const refStr=g.refs.filter(r=>r!=='R256').join(', ')+(dnp.length?' (R256 DNP)':'');
  const fn=[...g.vals].sort().join(' / ')+` ${pkg} hand-solder (${p.fp.replace(/_Pad.*/,'')})`;
  const old=oldByMpn[mpn];
  const note=`Passive repackage 2026-10-06 (hand-solder policy): was ${[...g.oldfp].join('/')} using ${[...g.oldm].join(', ')}. See reports/passive-repackage-2026-10-06.md. `;
  let row;
  if(old){
    row=[...old]; row[0]=refStr; row[1]=fn; row[5]=fitted; row[17]=note+(old[17]||'');
  } else {
    const np=NEWPRICE[p.lcsc];
    row=[refStr,fn,p.mfr,mpn,p.lcsc||null,fitted,np?100:null,np?100:null,null,np?100:null,np?np[0]:null,null,null,np?np[1]:null,
      p.lcsc?(np?'LCSC search 2026-10-06 (price is the quoted tier, stock as listed); re-verify at order':'LCSC number from family knowledge; unverified; price/stock unverified'):'LCSC code open: MPN from family knowledge, not looked up; price/stock unverified',46300,'2026-10-06',note+'MPN not stock-checked unless an LCSC code with price is shown.',p.lcsc?`https://www.lcsc.com/product-detail/${p.lcsc}.html`:null];
  }
  row[2]=old?row[2]:p.mfr; newRows.push(row);
}
const out=[...keep,...newRows];
// refs check: every row unique ref
const all=out.flatMap(r=>String(r[0]).replace(/\(.*?\)/g,'').split(',').map(s=>s.trim()).filter(Boolean));
const dup=all.filter((x,i)=>all.indexOf(x)!==i); if(dup.length) throw new Error('duplicate refs '+dup);
const end=FIRST+out.length-1;
sh.getRange(`A${FIRST}:S${LASTOLD}`).clear({applyTo:'contents'});
for(let i=0;i<out.length;i++){
  const r=FIRST+i; if(r>LASTOLD) sh.getRange(`A${r}:S${r}`).copyFrom(sh.getRange(`A${LASTOLD}:S${LASTOLD}`),'all');
  const v=out[i].map((x,j)=>(j===8||j===11||j===12)?null:x);
  sh.getRange(`A${r}:S${r}`).values=[v];
}
for(let r=end+1;r<=LASTOLD;r++) sh.getRange(`A${r}:S${r}`).clear({applyTo:'all'});
for(let r=FIRST;r<=end;r++){
 sh.getRange(`I${r}`).formulas=[[`=IF(OR(D${r}="",G${r}="",H${r}=""),"",IF(COUNTIF($D$11:D${r},D${r})>1,0,ROUNDUP(MAX(SUMIF($D$11:$D$${end},D${r},$F$11:$F$${end}),G${r})/H${r},0)*H${r}))`]];
 sh.getRange(`L${r}`).formulas=[[`=IF(K${r}="","",ROUND(F${r}*K${r},4))`]];
 sh.getRange(`M${r}`).formulas=[[`=IF(OR(K${r}="",I${r}="",N${r}=""),"",IF(N${r}>=I${r},ROUND(I${r}*K${r},4),""))`]];
}
sh.getRange('E4:E5').formulas=[[`=ROUND(SUM(L${FIRST}:L${end}),2)`],[`=ROUND(SUM(M${FIRST}:M${end}),2)`]];
sh.getRange('G4').values=[['BOM updated 2026-10-06: all R/C repackaged to hand-solder 0402 (0805 for large/high-voltage capacitors); many new passive MPNs and LCSC codes are unverified, so subtotal is partial.']];
const o=await SpreadsheetFile.exportXlsx(wb); await o.save(path);
const wb2=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const s2=wb2.worksheets.getItem('Selected BOM');
const vals=s2.getRange(`A10:S${end}`).values;
const q=v=>v===null||v===undefined||v===''?'':'"'+String(v).replace(/"/g,'""')+'"';
await fs.writeFile(csvPath, vals.map(r=>r.map(q).join(',')).join('\n')+'\n');
console.log('rows',out.length,'passive rows',newRows.length,'E4,E5',JSON.stringify(s2.getRange('E4:E5').values));
