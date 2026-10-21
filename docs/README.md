# Docs: what to open

GitHub shows `.html` files as code. To review the visual ones, open the **PDF** beside each (GitHub previews PDFs in the browser), or download the HTML and open it on your computer.

| What | PDF | Source |
|---|---|---|
| Brand sheet (logos, colours, type) | [brand/brand-sheet.pdf](brand/brand-sheet.pdf) · [PNG](brand/brand-sheet.png) | [brand/brand.md](brand/brand.md) |
| Assembly guide (8 pages, Letter) | [assembly/assembly-guide.pdf](assembly/assembly-guide.pdf) | `assembly/assembly-guide.html` |
| Lessons, elementary (grades 3–5) worksheets (15 pages, Letter) | [../server/static/learn/elementary/worksheets.pdf](../server/static/learn/elementary/worksheets.pdf) | [curriculum/elementary/](curriculum/elementary/README.md), also live at https://rocket.quiverdesignworks.net/learn/elementary/ |
| Lessons, middle school (grades 6–8) worksheets (22 pages, Letter) | [../server/static/learn/middle/worksheets.pdf](../server/static/learn/middle/worksheets.pdf) | [curriculum/middle/](curriculum/middle/README.md), also live at https://rocket.quiverdesignworks.net/learn/middle/ |
| Washington standards map (WSSLS / WA Science 2026) | — | [curriculum/standards.md](curriculum/standards.md) |
| Apogee review: suggested changes | — | [research/apogee-review.md](research/apogee-review.md) |
| Starter kit tuck box, print art (11 × 17 in) | [kits/packaging/tuck-box-starter.pdf](kits/packaging/tuck-box-starter.pdf) | `kits/packaging/tuck-box-starter.html` |
| Starter kit tuck box, dieline | [kits/packaging/tuck-box-starter-dieline.pdf](kits/packaging/tuck-box-starter-dieline.pdf) | `.svg` |
| Mini kit header card, print art (Letter) | [kits/packaging/header-card.pdf](kits/packaging/header-card.pdf) | `kits/packaging/header-card.html` |
| Mini kit header card, dieline | [kits/packaging/header-card-dieline.pdf](kits/packaging/header-card-dieline.pdf) | `.svg` |
| Big kit tube wrap, print art (17 × 11 in) | [kits/packaging/tube-wrap-big.pdf](kits/packaging/tube-wrap-big.pdf) | `kits/packaging/tube-wrap-big.html` |
| Big kit tube wrap, dieline | [kits/packaging/tube-wrap-big-dieline.pdf](kits/packaging/tube-wrap-big-dieline.pdf) | `.svg` |

Also: the kit plan, costs and research in [kits/README.md](kits/README.md); the kit test prints in [kits/test-prints/](kits/test-prints/README.md). Print the packaging PDFs at **100% / actual size**, not "fit to page".

Rebuild after editing the HTML: packaging PDFs come from headless Chromium's print (`page.pdf` with the page's own `@page` size); the worksheets PDFs from `curriculum/tools/build_site.py --pdf`; the assembly guide from `assembly/tools/make_pdf.mjs`.
