// Render one lesson picture to a PNG at 2x, to check a drawing by eye.
//   node docs/curriculum/tools/render_art.js docs/curriculum/art/e1-balloon-rocket.svg out.png
// Needs the playwright package on NODE_PATH and a Chromium in PLAYWRIGHT_BROWSERS_PATH.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [src, out] = process.argv.slice(2);
  const svg = fs.readFileSync(src, 'utf8');
  const fonts = path.resolve(__dirname, '../../../server/static/fonts');
  const face = (name, file) => `@font-face{font-family:"${name}";src:url(file://${fonts}/${file}) format("woff2")}`;
  const html = `<!doctype html><style>${face('Inter', 'inter.woff2')}${face('Space Grotesk', 'space-grotesk.woff2')}
    body{margin:0;background:#FFFDF8;display:inline-block}svg{display:block}</style>${svg}`;
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  await page.setContent(html);
  await page.evaluate(() => document.fonts.ready);
  await (await page.$('svg')).screenshot({ path: out });
  await browser.close();
})();
