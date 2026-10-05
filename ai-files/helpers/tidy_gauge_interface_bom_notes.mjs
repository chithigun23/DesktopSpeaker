import fs from 'node:fs/promises'; import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const root='/home/chithi/Desktop/DesktopSpeaker', xlsx=`${root}/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx`, csvPath=`${root}/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.csv`;
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(xlsx)); const sh=wb.worksheets.getItem('Selected BOM');
sh.getRange('R86').values=[['TI datasheet; LCSC listing snapshot dated 2026-10-05.']];
sh.getRange('R87').values=[['YAGEO 0603 1MΩ ±1%; official datasheet and LCSC listing snapshot dated 2026-10-05.']];
wb.recalculate(); const output=await SpreadsheetFile.exportXlsx(wb); await output.save(xlsx);
const csv=sh.getRange('A10:S87').values.map(row=>row.map(v=>v==null?'':`"${String(v).replaceAll('"','""')}"`).join(',')).join('\n')+'\n'; await fs.writeFile(csvPath,csv);
