import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const root='/home/chithi/Desktop/DesktopSpeaker';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(`${root}/ai-files/bom/DesktopSpeaker_LCSC_Starter_BOM.xlsx`));
const result=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:200},summary:'Active gauge interface BOM formula scan'});
await fs.writeFile(`${root}/ai-files/reports/gauge-interface-bom-formula-scan.ndjson`,result.ndjson+'\n');
const matches=Number(result.ndjson.match(/matched (\d+) entries/)?.[1]??0);
console.log(JSON.stringify({matches,resultPath:'ai-files/reports/gauge-interface-bom-formula-scan.ndjson'}));
