// Final one-shot note cleanup after add_gauge_interface_bom.mjs / tidy_gauge_interface_bom_notes.mjs.
import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const root='/home/chithi/Desktop/DesktopSpeaker';
const xlsx=`${root}/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx`;
const csvPath=`${root}/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv`;
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(xlsx));
const sh=wb.worksheets.getItem('Selected BOM');
sh.getRange('R86:R87').clear({applyTo:'contents'});
const output=await SpreadsheetFile.exportXlsx(wb); await output.save(xlsx);
const rows=sh.getRange('A10:S87').values;
await fs.writeFile(csvPath,rows.map(row=>row.map(v=>v==null?'':`"${String(v).replaceAll('"','""')}"`).join(',')).join('\n')+'\n');
