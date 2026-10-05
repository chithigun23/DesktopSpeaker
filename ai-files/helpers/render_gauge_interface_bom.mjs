import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const root='/home/chithi/Desktop/DesktopSpeaker';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(`${root}/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx`));
for(const [tag,range] of [['gauge-interface-bom-render','A74:S87'],['gauge-interface-bom-totals-render','A2:M8']]){
 const image=await wb.render({sheetName:'Selected BOM',range,scale:1.15,format:'png'});
 await fs.writeFile(`${root}/ai-files/reports/${tag}.png`,new Uint8Array(await image.arrayBuffer()));
}
