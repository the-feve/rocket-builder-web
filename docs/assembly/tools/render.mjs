// Renders every scene in scenes.js to docs/assembly/images/<name>.png and
// writes the label positions to docs/assembly/images/callouts.js.
//
//   node docs/assembly/tools/render.mjs            # all scenes
//   node docs/assembly/tools/render.mjs layout pad # just these
//
// Needs the meshes from build_meshes.py (docs/assembly/tools/.build/) and
// Playwright (uses the pre-installed Chromium; set CHROMIUM to override).
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../../..');
const outDir = path.resolve(here, '../images');

function loadPlaywright() {
  const req = createRequire(import.meta.url);
  for (const p of [process.env.PLAYWRIGHT_PATH, 'playwright', '/opt/node-tools/node_modules/playwright']) {
    if (!p) continue;
    try { return req(p); } catch { /* next */ }
  }
  const g = req('child_process').execSync('npm root -g').toString().trim();
  return req(path.join(g, 'playwright'));
}

const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.glb': 'model/gltf-binary' };
const server = http.createServer((req, res) => {
  const p = path.join(repo, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(repo) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const { chromium } = loadPlaywright();
const exe = process.env.CHROMIUM || (fs.existsSync('/opt/pw-browsers/chromium') && fs.statSync('/opt/pw-browsers/chromium').isFile() ? '/opt/pw-browsers/chromium' : undefined);
const browser = await chromium.launch({ executablePath: exe, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage();
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.error('[page error]', e.message));
await page.goto(`http://127.0.0.1:${port}/docs/assembly/tools/render.html`);
await page.waitForFunction(() => window.SCENES_READY === true, null, { timeout: 120000 });

const all = await page.evaluate(() => Object.keys(window.SCENES));
const want = process.argv.slice(2).length ? process.argv.slice(2) : all;
fs.mkdirSync(outDir, { recursive: true });
const calloutsFile = path.join(outDir, 'callouts.js');
let callouts = {};
if (fs.existsSync(calloutsFile)) {
  const txt = fs.readFileSync(calloutsFile, 'utf8');
  try { callouts = JSON.parse(txt.slice(txt.indexOf('{'), txt.lastIndexOf('}') + 1)); } catch { callouts = {}; }
}
for (const name of want) {
  const t0 = Date.now();
  const r = await page.evaluate(n => window.renderScene(n), name);
  fs.writeFileSync(path.join(outDir, `${name}.png`), Buffer.from(r.png.split(',')[1], 'base64'));
  callouts[name] = { w: r.w, h: r.h, points: r.points };
  console.log(`${name}.png ${r.w}x${r.h} (${Date.now() - t0} ms)`);
}
fs.writeFileSync(calloutsFile, '// Written by tools/render.mjs: label anchor points (fractions of each image\'s width/height).\n'
  + `window.CALLOUTS = ${JSON.stringify(callouts, null, 1)};\n`);
await browser.close();
server.close();
