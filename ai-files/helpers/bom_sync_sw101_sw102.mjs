// One-shot (guarded): BOM xlsx rows SW101/SW102 after the 2026-10-12 sourcing pass (CSV already patched by the coordinator).
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const path='/home/chithi/Desktop/DesktopSpeaker/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx';
const bak='/home/chithi/Desktop/DesktopSpeaker/ai-files/backups/DesktopSpeaker_LCSC_Starter_BOM.xlsx.pre-sw-sync';
try { await fs.access(bak); console.log('already applied (backup exists)'); process.exit(0);} catch {}
await fs.copyFile(path,bak);
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sh=wb.worksheets.getItem('Selected BOM'); const r=sh.getUsedRange(); const v=r.values;
const upd={
 SW101:{2:'CW Industries',3:'GRB112B802BR1',4:'',10:5.09,11:5.09,13:7073,14:'Digi-Key 2349683, 7073 in stock at 2026-10-12, $5.09; 20 A 14 VDC SPST round rocker, 20.2 mm hole, 0.187 in fastons, IP65, red LED (lamp pin unused on the 1S rail); snap-in panel 1.5-2.5 mm so the 4 mm lid needs a local pocket (CAD); replaces KCD1-201-R (stock 0). Not an LCSC part; wired, not assembled.',16:'2026-10-12',17:'Substituted 2026-10-12 from reports/sourcing-2026-10-12.md (coordinator, self-approved). Previous: SHOU HAN KCD1-201-R C5884429, stock 0.',18:'https://www.digikey.com/en/products/detail/cw-industries/GRB112B802BR1/2349683'},
 SW102:{3:'EC11E18244AU',4:'C202365',10:2.2213,11:2.2213,13:398,14:'In stock (398 at 2026-10-12); substitute for EC11E15244G1 (C370970, stock 0): same EC11E vertical body, 20 mm flat shaft, push switch 0.5 mm travel, 18/36 pulses/detents instead of 15/30 (firmware counts per detent unchanged); footprint equivalence by series, body drawing not re-read; see reports/sourcing-2026-10-12.md',16:'2026-10-12',17:'Substituted 2026-10-12 (coordinator, self-approved). Previous: EC11E15244G1 C370970, stock 0.',18:'https://www.lcsc.com/product-detail/C202365.html'}};
let n=0;
for (let i=0;i<v.length;i++){ const ref=v[i][0]; if (upd[ref]) { for (const [c,val] of Object.entries(upd[ref])) { const col=String.fromCharCode(65+Number(c)); sh.getRange(`${col}${i+1}`).values=[[val]]; } n++; } }
const out=await SpreadsheetFile.exportXlsx(wb); await out.save(path); console.log('rows updated',n);
