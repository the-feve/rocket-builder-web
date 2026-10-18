// Render the served worksheets page to a US Letter PDF (called by build_site.py --pdf).
// node worksheets_pdf.js <worksheets.html> <server/static dir> <out.pdf>
// Needs the playwright package on NODE_PATH and a Chromium in PLAYWRIGHT_BROWSERS_PATH.
// Requests are answered from disk, so no server has to run: /learn/worksheets is the
// page and /static/... comes from server/static (the self-hosted fonts).
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const [page_html, staticDir, out] = process.argv.slice(2);
const TYPES = { '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.png': 'image/png', '.css': 'text/css' };

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.route('**/*', route => {
    const u = new URL(route.request().url());
    if (u.hostname !== 'learn.local') return route.abort();
    if (u.pathname === '/learn/worksheets') return route.fulfill({ body: fs.readFileSync(page_html), contentType: 'text/html' });
    if (u.pathname.startsWith('/static/')) {
      const f = path.join(staticDir, path.normalize(u.pathname.slice(8)));
      if (f.startsWith(staticDir) && fs.existsSync(f))
        return route.fulfill({ body: fs.readFileSync(f), contentType: TYPES[path.extname(f)] || 'application/octet-stream' });
    }
    return route.fulfill({ status: 404, body: '' });
  });
  await page.goto('http://learn.local/learn/worksheets', { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: out, format: 'Letter', printBackground: true, preferCSSPageSize: true });
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
