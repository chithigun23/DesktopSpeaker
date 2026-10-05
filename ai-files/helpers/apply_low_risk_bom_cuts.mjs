// Guarded: apply the 2026-10-06 low-risk BOM cuts (reports/bom-reduction-audit.md) to the Selected BOM. Run from project root.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx', csvPath='ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv';
const REMOVED=['C185','C113','C114','C115','C121','C143','C151','C163','C164','C242','R260'];
const FN={ // normalised value text per MPN (only text; no part merged or removed)
 'CL21B106KPQNNNE':'10uF X7R 10V 0805 hand-solder (C_0805_2012Metric)',
 'GRM155R71H104KE14D':'100nF X7R 0402 hand-solder (C_0402_1005Metric)',
 'GRM21BZ71A226ME15L':'22uF X7R 10V 0805 hand-solder (C_0805_2012Metric)',
 'CL21B105KBFNNNE':'1uF X7R 50V 0805 hand-solder (C_0805_2012Metric)',
 'CL05A105KO5NNNC':'1uF X7R 10V 0402 hand-solder (C_0402_1005Metric)',
 'RC0402FR-07100RL':'100R 0402 hand-solder (R_0402_1005Metric)',
 'RC0402FR-07100KL':'100k 1% 0402 hand-solder (R_0402_1005Metric)',
 'RC0402FR-0710KL':'10k 1% 0402 hand-solder (R_0402_1005Metric)',
 'RC0402FR-070RL':'0R DNP 0402 hand-solder (R_0402_1005Metric)',
 'GRM155R71H473KA12D':'47nF X7R 50V 0402 hand-solder (C_0402_1005Metric)',
 'GRM1555C1H331JA01D':'330pF C0G (CC1/CC2 filters) 0402 hand-solder (C_0402_1005Metric)',
 'GRM21BR61H106KE43L':'10uF X7R 50V 0805 hand-solder (C_0805_2012Metric)'};
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sh=wb.worksheets.getItem('Selected BOM');
const FIRST=11, LAST=102;
if(String(sh.getRange('A100').values[0][0])!=='R260 (R256 DNP)') throw new Error('unexpected layout / already applied');
const rows=sh.getRange(`A${FIRST}:S${LAST}`).values;
const refRe=/\b[A-Z]+\d+\b/g, rm=new Set(REMOVED); const hit=new Set();
for(let i=0;i<rows.length;i++){
  const r=rows[i], s=String(r[0]);
  const refs=(s.match(refRe)||[]); const removedHere=refs.filter(x=>rm.has(x));
  const mpnKey=r[3];
  if(FN[mpnKey]&&/hand-solder/.test(String(r[1]))) r[1]=FN[mpnKey];
  if(!removedHere.length) continue;
  removedHere.forEach(x=>hit.add(x));
  const dnp=/\(R256 DNP\)/.test(s)?['R256']:[];
  const keep=s.replace(/\(.*?\)/g,'').split(',').map(t=>t.trim()).filter(t=>t&&!rm.has(t));
  r[0]=(keep.join(', ')+(dnp.length?(keep.length?' ':'')+'(R256 DNP)':'')).trim();
  r[5]=keep.length;
  let n=String(r[17]||'');
  for(const x of removedHere){ n=n.replace(new RegExp(`, ${x}\\b`,'g'),'').replace(new RegExp(`\\b${x}, `,'g','')); }
  r[17]=(n+` Low-risk BOM cut 2026-10-06: removed ${removedHere.join(', ')} (reports/bom-reduction-audit.md).`).trim();
}
if(hit.size!==REMOVED.length) throw new Error('not all removed refs found: '+REMOVED.filter(x=>!hit.has(x)));
// every active ref once check
const all=rows.flatMap(r=>String(r[0]).replace(/\(.*?\)/g,'').split(',').map(s=>s.trim()).filter(Boolean));
const dup=all.filter((x,i)=>all.indexOf(x)!==i); if(dup.length) throw new Error('duplicate refs '+dup);
if(all.some(x=>rm.has(x))) throw new Error('removed ref remains');
sh.getRange(`A${FIRST}:S${LAST}`).values=rows.map(r=>r.map((x,j)=>(j===8||j===11||j===12)?null:x));
for(let r=FIRST;r<=LAST;r++){
 sh.getRange(`I${r}`).formulas=[[`=IF(OR(D${r}="",G${r}="",H${r}=""),"",IF(COUNTIF($D$11:D${r},D${r})>1,0,ROUNDUP(MAX(SUMIF($D$11:$D$${LAST},D${r},$F$11:$F$${LAST}),G${r})/H${r},0)*H${r}))`]];
 sh.getRange(`L${r}`).formulas=[[`=IF(K${r}="","",ROUND(F${r}*K${r},4))`]];
 sh.getRange(`M${r}`).formulas=[[`=IF(OR(K${r}="",I${r}="",N${r}=""),"",IF(N${r}>=I${r},ROUND(I${r}*K${r},4),""))`]];
}
sh.getRange('G4').values=[['BOM updated 2026-10-06: all R/C repackaged to hand-solder 0402 (0805 for large/high-voltage capacitors); low-risk cuts applied (C113-C115, C121, C143, C151, C163, C164, C185, C242, R260 removed); many passive MPNs/LCSC codes unverified, so subtotal is partial.']];
const o=await SpreadsheetFile.exportXlsx(wb); await o.save(path);
const wb2=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const s2=wb2.worksheets.getItem('Selected BOM');
const vals=s2.getRange(`A10:S${LAST}`).values;
const q=v=>v===null||v===undefined||v===''?'':'"'+String(v).replace(/"/g,'""')+'"';
await fs.writeFile(csvPath, vals.map(r=>r.map(q).join(',')).join('\n')+'\n');
console.log('E4,E5',JSON.stringify(s2.getRange('E4:E5').values),'total fitted qty',vals.slice(1).reduce((a,r)=>a+(Number(r[5])||0),0));
