// node route_p1_png.mjs IN.svg OUT.png WIDTH [x y w h in svg px fraction 0..1 of the image]
import sharp from '/home/chithi/Desktop/DesktopSpeaker/ai-files/helpers/node_modules/sharp/dist/index.cjs';
const [,, inp, out, wd, fx, fy, fw, fh] = process.argv;
let img = sharp(inp, {density: 300});
const meta = await img.metadata();
if (fx !== undefined) {
  img = sharp(inp, {density: 300}).extract({left: Math.round(meta.width*fx), top: Math.round(meta.height*fy), width: Math.round(meta.width*fw), height: Math.round(meta.height*fh)});
}
await img.resize({width: parseInt(wd)}).flatten({background: '#ffffff'}).png().toFile(out);
