// Prints docs/assembly/assembly-guide.html to assembly-guide.pdf (US Letter).
//   node docs/assembly/tools/make_pdf.mjs [--png <dir>]
// --png also saves one PNG per page (for checking the layout).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const here = path.dirname(fileURLToPath(import.meta.url));
const guide = path.resolve(here, '../assembly-guide.html');
const req = createRequire(import.meta.url);
let pw;
for (const p of [process.env.PLAYWRIGHT_PATH, 'playwright', '/opt/node22/lib/node_modules/playwright']) {
  if (!p) continue;
  try { pw = req(p); break; } catch { /* next */ }
}
if (!pw) pw = req(path.join(req('child_process').execSync('npm root -g').toString().trim(), 'playwright'));

const exe = process.env.CHROMIUM || (fs.existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined);
const browser = await pw.chromium.launch({ executablePath: exe });
const page = await browser.newPage({ viewport: { width: 816, height: 1056 } });
page.on('pageerror', e => console.error('[page error]', e.message));
await page.goto(pathToFileURL(guide).href, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.emulateMedia({ media: 'print' });
await page.evaluate(() => window.dispatchEvent(new Event('resize')));
await page.waitForTimeout(300);
await page.pdf({ path: path.resolve(here, '../assembly-guide.pdf'), format: 'Letter', printBackground: true,
                 margin: { top: 0, right: 0, bottom: 0, left: 0 }, preferCSSPageSize: true });
console.log('assembly-guide.pdf written');
const i = process.argv.indexOf('--png');
if (i > 0) {
  const dir = process.argv[i + 1];
  fs.mkdirSync(dir, { recursive: true });
  const pages = await page.$$('section.page');
  for (let k = 0; k < pages.length; k++) {
    await pages[k].screenshot({ path: path.join(dir, `page-${k + 1}.png`) });
  }
  console.log(`${pages.length} page PNGs in ${dir}`);
}
await browser.close();
