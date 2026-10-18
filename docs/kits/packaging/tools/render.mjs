// Renders the packaging artwork and dielines to PNG (docs/kits/packaging/*.png).
//
//   node docs/kits/packaging/tools/render.mjs
//
// Uses Playwright with the pre-installed Chromium (CHROMIUM overrides the path).
// Each job loads a page from docs/kits/packaging/ over file://, waits for the
// web fonts, then screenshots the whole sheet or one element (a panel).
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const here = path.dirname(fileURLToPath(import.meta.url));
const dir = path.resolve(here, '..');

function loadPlaywright() {
  const req = createRequire(import.meta.url);
  for (const p of [process.env.PLAYWRIGHT_PATH, 'playwright', '/opt/node-tools/node_modules/playwright']) {
    if (!p) continue;
    try { return req(p); } catch { /* next */ }
  }
  const g = req('child_process').execSync('npm root -g').toString().trim();
  return req(path.join(g, 'playwright'));
}

// [page, output png, { query, clip: CSS selector, scale }]
const jobs = [
  ['tuck-box-starter.html', 'tuck-box-starter-print.png', { query: '?dieline=1', scale: 1.5 }],
  ['tuck-box-starter.html', 'tuck-box-starter-front.png', { clip: '#front', scale: 3 }],
  ['tuck-box-starter.html', 'tuck-box-starter-back.png', { clip: '#wrapback', scale: 2.5 }],
  ['header-card.html', 'header-card-sheet.png', { query: '?dieline=1', scale: 1.5 }],
  ['header-card.html', 'header-card-front.png', { clip: '#c1 .front', scale: 4 }],
  ['header-card.html', 'header-card-back.png', { clip: '#c1 .back', scale: 4, rotate: true }],
  ['tube-wrap-big.html', 'tube-wrap-big-print.png', { query: '?dieline=1', scale: 1.5 }],
  ['tube-wrap-big.html', 'tube-wrap-big-front.png', { clip: '#face1', scale: 3 }],
  ['dieline.html', 'tuck-box-starter-dieline.png', { query: '?f=tuck-box-starter-dieline.svg', scale: 1.5 }],
  ['dieline.html', 'header-card-dieline.png', { query: '?f=header-card-dieline.svg', scale: 1.5 }],
  ['dieline.html', 'tube-wrap-big-dieline.png', { query: '?f=tube-wrap-big-dieline.svg', scale: 1.5 }],
];

const only = process.argv.slice(2);
const { chromium } = loadPlaywright();
const exe = process.env.CHROMIUM;
const browser = await chromium.launch(exe ? { executablePath: exe } : {});
for (const [page, out, o] of jobs) {
  if (only.length && !only.some((s) => out.includes(s))) continue;
  const ctx = await browser.newContext({ deviceScaleFactor: o.scale || 2, viewport: { width: 1700, height: 1700 } });
  const p = await ctx.newPage();
  await p.goto(pathToFileURL(path.join(dir, page)).href + (o.query || ''), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  if (o.rotate) await p.addStyleTag({ content: `${o.clip} { transform: none !important; }` });
  const file = path.join(dir, out);
  if (o.clip) await p.locator(o.clip).screenshot({ path: file });
  else await p.locator('#sheet').screenshot({ path: file });
  console.log('wrote', file);
  await ctx.close();
}
await browser.close();
