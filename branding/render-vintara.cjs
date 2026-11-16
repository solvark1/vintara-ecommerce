// Optional asset regeneration: requires the sharp package. PNGs are committed in assets.
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
(async () => {
 const dir = path.join(__dirname, 'assets', 'vintara');
 for (const name of fs.readdirSync(dir).filter(n => /^vin-\d+\.svg$/.test(n))) {
  await sharp(path.join(dir,name)).png().toFile(path.join(dir,name.replace('.svg','.png')));
 }
 for (const name of fs.readdirSync(dir).filter(n => /^vin-\d+\.png$/.test(n))) fs.copyFileSync(path.join(dir,name),path.join(dir,'terra-'+name));
 console.log('18 wine PNGs rendered.');
})().catch(e=>{console.error(e.message);process.exit(1)});
