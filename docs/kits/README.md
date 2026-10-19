# Rocket Builder kits: lineup, costs, packaging and research

> **Review the packaging as PDFs** (GitHub shows HTML as code): [tuck box](packaging/tuck-box-starter.pdf), [header card](packaging/header-card.pdf), [tube wrap](packaging/tube-wrap-big.pdf), and their dielines (`packaging/*-dieline.pdf`). Print at 100% / actual size. All docs: [../README.md](../README.md).

_2026-10-18, stream E of `docs/expansion_spec_2026-10.md`. Proposal for selling complete 3D-printed model rocket kits (motors not included) in local stores, at farmers markets and in the online store (quiverdesignworks.net/store/). Nothing here changes the app, the shop or the store; the online product entries at the end are a draft._

**Read this first (the short version)**

- **Lineup:** Starter kit (18 mm, tuck box) **$29.99**, Big kit (24 mm, mailing tube) **$39.99**, Mini kit (13 mm, bag with header card) **$16.99**, Classroom 6-pack (6 Starter rockets) **$99**. Wholesale at half of retail; the classroom pack is sold direct only.
- **Parts and packaging cost per kit:** about $1.90 (Mini), $4.65 (Starter) and $7.75 (Big), including a snap swivel (2026-10-19). Adding the owner's time at $20/h brings it to about $5.25, $11.35 and $15.10.
- **Safest compliance route:** label and market every kit **"Ages 12+, adults handle motors and launching"**. Sell it as a hobby and STEM kit for teens, adults and families, never as a kid's toy. That keeps it a general-use product, not a CPSIA children's product, so no lab testing and no Children's Product Certificate. This conflicts with the app's Beginner mode (grades 3–7) and the curriculum (grades 5–8); see **Compliance** below. A lawyer should confirm it before the first sale.
- **Two things the generator found:** A8-3 motors are **too weak** for the printed 18 mm Starter rocket, and only the **A10-3T** works for the 13 mm Mini. Both rockets are heavier than paper Estes rockets. Recommend B6-4, B4-6 and C6-7 for the Starter; the app's own supply page suggests "start low with an A", so update that too.
- **Packaging files:** `packaging/`. Each format has a dieline SVG, print-ready artwork (HTML) and PNG previews. They use the brand kit in `docs/brand/`.

## Contents

1. [Kit designs](#kit-designs) (what the generator says about each rocket)
2. [Lineup and prices](#lineup-and-prices)
3. [Bill of materials per kit](#bill-of-materials-per-kit)
4. [Packaging per channel](#packaging-per-channel) and [packaging files](#packaging-files)
5. [Packaging suppliers and unit costs](#packaging-suppliers-and-unit-costs)
6. [Farmers-market display](#farmers-market-display)
7. [Making the first 10 kits](#making-the-first-10-kits)
8. [Selling in local stores](#selling-in-local-stores)
9. [Selling online](#selling-online) (draft `products.json` entries)
10. [Research: how other kits are packaged and priced](#research-comparable-kits)
11. [Compliance and labels](#compliance-and-labels) (and what to confirm with a professional)
12. [AI and low-cost design tools](#ai-and-low-cost-design-tools)
13. [Sources](#sources)

---

## Kit designs

Each kit is one fixed design from Rocket Builder: Beginner settings, **printer max height 256 mm** (Bambu A1/P1S/X1C), trapezoid fins, tangent-ogive nose, 3 fins, PLA, auto-sized fins for stability. I built them with `rocketgen` (`build_stable`) and flew them with `flight.simulate` on 2026-10-18. Masses are the generator's solid-PLA estimate; **weigh the real prints and re-run the app before printing the boxes**, because the heights and motor list on the packaging come from these numbers.

| Kit | Motor | Overall height | Body OD | Printed mass | Stability | Parts (print orientation, mm) | Chute (app) |
|---|---|---|---|---|---|---|---|
| Mini | M13 | 190 mm | 16.4 mm | 23.3 g | 1.14 cal | Aft 46×53×113, Anchor 16×16×38, Nose 16×16×58, Motor cap, Rod standoff | streamer OK (< 40 g); 12 in chute |
| Starter | M18 | 300 mm | 21.4 mm | 44.0 g | 1.15 cal | Aft 53×61×205, Anchor 21×21×43, Nose 21×21×74, Motor cap, Rod standoff | 12 in |
| Big | M24 | 360 mm | 27.4 mm | 70.6 g | 1.14 cal | Aft 77×89×242, Anchor 27×27×52, Nose 27×27×95, Motor cap, Rod standoff | 15 in |

Simulated flights (rocket + recovery allowance, `flight.simulate`; "no" = the app rejects it):

| Kit | Motor | Apogee | Delay (app) | App verdict |
|---|---|---|---|---|
| Mini | 1/2A3 | 43 m / 141 ft | 2 | no: slow off the rod |
| Mini | A3 | 131 m / 431 ft | 4 | no: slow off the rod |
| Mini | **A10-3T** | **111 m / 365 ft** | 3 | **OK** |
| Starter | A8 | 57 m / 187 ft | 3 | no: too heavy, slow off the rod |
| Starter | **B6-4** | **142 m / 465 ft** | 4 | **OK (first flight)** |
| Starter | **B4-6** | **177 m / 582 ft** | 6 | **OK** |
| Starter | C5-3 | 307 m / 1,008 ft | 3 | OK (out of production at Estes; not listed on the box) |
| Starter | **C6-7** | **355 m / 1,164 ft** | 7 | **OK** |
| Big | **C11-5** | **198 m / 650 ft** | 5 | **OK (first flight)** |
| Big | **D12-7** | **418 m / 1,370 ft** | 7 | **OK** |

Notes:

- Taller versions are heavier and fly worse: a 250 mm M13 rocket is too heavy for every M13 motor, and the Starter at 340 mm loses the B6-4. Keep these heights.
- The part letters on the packaging match the assembly guide (`docs/assembly/tools/scene_defs.js`): A nose, B anchor section, C middle body section (not in these designs), D fin can, E motor cap, F rod standoff, G shock cord, H parachute or streamer, I wadding.
- **Fly-test every design on every motor printed on its package** (and log the results in `geometry/report.md`) before selling.

## Lineup and prices

Four products. The Starter is the hero product: 18 mm motors are the easiest to find, and the box looks like the kits people know.

| Kit | Who it's for | Packaging | Retail | Wholesale (50 %) | Parts + packaging | + labour ($20/h) | Margin direct* | Margin wholesale |
|---|---|---|---|---|---|---|---|---|
| **Mini** (13 mm, A10-3T) | impulse buy, small fields, market | 4 × 12 in bag + header card | **$16.99** | $8.50 | $1.84 | $5.17 (10 min) | $11.23 (66 %) | $3.33 (39 %) |
| **Starter** (18 mm, B6-4 / B4-6 / C6-7) | first rocket, gift, stores | tuck-end box 2.5 × 2.5 × 8.75 in | **$29.99** | $15.00 | $4.56 | $11.23 (20 min) | $17.83 (59 %) | $3.77 (25 %) |
| **Big** (24 mm, C11-5 / D12-7) | step up, older teens and adults | 4 × 12 in kraft tube ("the quiver") | **$39.99** | $20.00 | $7.66 | $14.99 (22 min) | $23.81 (60 %) | $5.01 (25 %) |
| **Classroom 6-pack** (6 Starters, bagged, teacher sheet) | teachers, home-school co-ops, scout leaders (adults) | one shipping carton | **$99** ($16.50 each) | direct only | $21.86 | $53.86 (96 min) | $41.97 (42 %) | n/a |

\* Direct margin after card fees (Square or Stripe, about 2.6–2.9 % + 15–30¢). Online orders also pay the store's flat $8 US shipping (`store.json`), which roughly covers USPS Ground Advantage for these weights.

Why these prices:

- **Comparable kits:** Estes Alpha III $19.99–24.99 (bulk-pack single $12.29), Estes Big Daddy (24 mm) $34.99–40.10, Quest Skill 1 kits $13.99–21.49, Estes Mosquito (13 mm) $10.99, Alpha III 12-pack $144.99 ($12.08 a rocket). Ours are printed, pre-coloured, need no paint, and come with a free design app, so they sit a little above Estes, like a premium E2X-style kit.
- **Same price logic as printed-rocket orders:** `server/shop.json` prices a one-off print at $12 + 15¢/g, so the Starter's parts alone would be $19.00 and the Big's $23.00. Each kit adds about $10–17 for the recovery parts, box and instructions, which keeps kits and print orders consistent. The Mini is set at $16.99 so it isn't cheaper than its own print order ($15.50).
- **Wholesale is thin with labour counted** (about $3.30–5.00 a kit). It's still worth it for reach, but only with batch production (10+ kits per session) and the tube and box bought in quantity. Consignment at 65–70 % to the maker is better if a shop agrees.

## Bill of materials per kit

Unit costs at about 25–100 kits. Filament $20/kg PLA (`gear.json` lists Sunlu PLA 1 kg) at 2¢/g, plus 15 % for purge, brims and failed prints. Printer time at $0.25/h (electricity about 1¢/h, nozzle, plate and belt wear, and depreciation; an assumption, not measured). Print times are estimates: check the slicer.

| Item | Mini | Starter | Big | Notes |
|---|---|---|---|---|
| Printed parts A, B, D, E, F (+15 %) | 26.8 g · $0.54 | 50.6 g · $1.01 | 81.2 g · $1.62 | generator mass |
| Printer time | ~1.5 h · $0.38 | ~3 h · $0.75 | ~5 h · $1.25 | assumption |
| G shock cord: braided flat elastic, 1/8 in (3 mm) for 13 and 18 mm, 1/4 in (6 mm) for 24 mm (sewing-supply elastic, roughly $0.03–0.06/ft by the roll) | 1/8 in, 3 ft · $0.12 | 1/8 in, 4 ft · $0.16 | 1/4 in, 5 ft · $0.30 | ties through the anchor strap, as the assembly guide draws it; the generator's cord slots are being sized for these widths. Not heat-proof: the wadding protects it, and it's a cheap spare |
| H recovery | streamer · $0.05 | 12 in chute · $0.30 | 15 in chute · $0.35 | homemade chutes: 1 mil plastic, nylon line, hole reinforcements (store-bought 12 in: $5.49 retail) |
| Snap swivel (added 2026-10-19, Apogee review #5): size 14 for chutes and streamers up to about 12 in; size 12 for the Big kit's 15 in chute (Apogee: 14 up to 12 in, 10 for 18–24 in). Fishing snap swivels in packs of 50–100, about $0.05–0.10 each | size 14 · $0.08 | size 14 · $0.08 | size 12 · $0.08 | clips round the cord below the nose knot (13/18 mm) or to the nose's tie bar (24 mm and up); the parachute's lines are lark's-headed to its eye, so swapping a chute is unclip and clip (assembly guide step 6) |
| I wadding (Estes 2274, 75 sheets ≈ $7) | 3 · $0.27 | 4 · $0.36 | 6 · $0.54 | Estes kits leave this out; including a starter amount makes it "complete" |
| Waterproof decal sheet (inkjet vinyl, $13–17 per 25 sheets, 4–6 kits a sheet) | $0.15 | $0.20 | $0.25 | printed at home |
| Quick-start card (QR to the full assembly guide) | 1 sheet B&W · $0.10 | 2 sheets colour · $0.40 | $0.40 | the full guide is stream D (`docs/assembly`) |
| Small zip bag for small parts (2 × 3 in) | $0.03 | $0.03 | $0.03 | |
| Package | bag + header card · $0.20 | tuck box + tissue + glue · $1.35 | tube + wrap · $2.92 | see the suppliers table |
| **Total, parts and packaging** | **$1.92** | **$4.64** | **$7.74** | |
| Owner's time (print removal, QC, chute, packing) | 10 min | 20 min | 22 min | batches of 10 |

**Not included, on purpose** (the same as Estes): motors, igniters, launch pad and controller, and **glue**. Cyanoacrylate glue carries its own hazard-labelling rules, and motors and igniters are regulated and best bought by an adult from a hobby store.

**Launch lug:** printed (the rod standoff F, 1/8 in rod), so none to buy.

## Packaging per channel

| Channel | Mini | Starter | Big | Why |
|---|---|---|---|---|
| Farmers market | bag + header card on a pegboard | tuck box standing on a shelf | tube standing up | cheap; boxes and tubes survive handling |
| Local store | bag on a peg hook | tuck box (shelf, or a hang tab later) | tube | stores want a shelf- or peg-ready pack with the age grade, warnings and a barcode |
| Online store | bag inside a 12 × 3 × 3 in box | tuck box inside a 12 × 3 × 3 in box (ULINE S-16721, $0.73) | the tube is the shipping box | no extra mailer for the Big |
| Classroom pack | – | 6 Starters in 6 × 12 in bags, 12 × 10 × 6 in carton | – | the teacher unpacks |

**Why three formats:** each is the cheapest one that works for its kit. The Mini's fins are small enough to ride in a bag with a card backer. The Starter fits a box that prints on one **11 × 17 in** sheet at home or at a print shop, so there's no die or minimum order. The Big's fin can is 89 mm across its fins, which needs a 3.5 in box, and that no longer fits a common sheet. A 4 × 12 in kraft tube fits it, ships as is, and is literally a quiver of rockets.

## Packaging files

All in `packaging/`. Open an HTML file in Chrome and print at 100 % ("Actual size"), with "Background graphics" on. Add `?dieline=1` to the address to lay the cut and fold lines over the art.

| File | What |
|---|---|
| `tuck-box-starter.html` | Print file, 11 × 17 in: front, side 1 (contents, what you need, specs), back (steps, safety, preflight, QR), side 2 (design your own, where to fly, warnings, maker, batch, UPC), lids |
| `tuck-box-starter-dieline.svg` / `.png` | Reverse tuck-end box, 2.5 × 2.5 × 8.75 in inside, flat 10.5 × 15 in: cut, fold, bleed and safe-area lines, labelled |
| `tuck-box-starter-print.png`, `-front.png`, `-back.png` | Previews: the whole sheet with the dieline, the front panel, and the three other panels |
| `header-card.html` | Print file, US Letter, two fold-over header cards (4 × 3.5 in folded) for a 4 × 12 in bag; no bleed, so a home printer and a paper trimmer work. `?ivory=1` drops the Paper tint, for ivory cardstock |
| `header-card-dieline.svg` / `.png` | Cut, fold, euro-slot and staple marks, crop marks |
| `header-card-sheet.png`, `-front.png`, `-back.png` | Previews |
| `tube-wrap-big.html` | Print file, 17 × 11 in: a 13.57 × 9.5 in wrap for a 4 in ID kraft tube, three faces (front, contents, steps + labels) and a glue overlap |
| `tube-wrap-big-dieline.svg` / `.png`, `tube-wrap-big-print.png`, `-front.png` | Dieline and previews |
| `kit.css`, `kit.js` | Shared styles (they import `docs/brand/tokens.css`) and the hero line drawing, drawn from the real kit dimensions |
| `tools/dielines.py` | Writes the three dieline SVGs; change box sizes here (`pip install shapely` for the bleed line) |
| `tools/render.mjs` | Renders all the PNGs with Playwright: `node docs/kits/packaging/tools/render.mjs` |
| `dieline.html` | Small viewer the renderer uses for the dieline PNGs |

**Before printing for real:**

- **Swap the placeholders.** The QR box needs a real QR code; any free generator works, with `https://rocket.quiverdesignworks.net/` or a guide URL once stream D publishes it. The UPC box needs a GS1 barcode, or delete it until a store asks for one.
- **Batch line.** Write or stamp the batch number and month on each kit (`RB-S-2611-01`, …).
- **Check the numbers.** Re-check the heights, weights and altitudes after weighing real prints.
- **Convert the logos for an offset printer.** The logo SVGs are already outlines. The art uses live Google Fonts: a print shop that wants a PDF can take Chrome's "Save as PDF", which embeds the fonts.

**Making the box by hand:** print on 80–100 lb cover (about 16–18 pt), cut on the magenta lines with a craft knife and steel rule (a cardboard template from the first one speeds this up), score the dashed lines with a bone folder or an empty ballpoint, then glue the flap inside side 2 with a glue stick or double-sided tape. About 4 minutes a box.

**Brand use:** Night bands with the blueprint grid, Paper panels, orange fins (fletching), the one orange "first flight" motor chip, Space Grotesk and Inter, part letters in chamfered tags, the fletching band along the bottom, and the dashed flight arc. Rule followed: Night text on orange, never white. The hero is a flat side view in the guide's line weights. The front of the narrow box shows the rocket straight up rather than at 45° (the brand's cover angle) because the panel is only 2.5 in wide; the header card uses 45°.

## Packaging suppliers and unit costs

Prices from the suppliers' pages as cached in July–October 2026; check before ordering. "Shop" means a local print shop (or FedEx Office or Staples online).

| Item | 25 units | 100 units | 500 units | Notes |
|---|---|---|---|---|
| **Poly bag 4 × 12 in, 2 mil** (ULINE S-1003) | $35 carton of 1,000 (≈ $0.04 each, but $35 up front) | same | $0.035 | or a 100-pack on Amazon for a few dollars |
| **Header card**, home printed on 65–80 lb cover, 2 per Letter sheet | ≈ $0.15 | ≈ $0.15 | ≈ $0.10 (shop, cut) | paper about $0.08–0.10 a sheet + ink |
| **Tuck box**, 11 × 17 in cover stock, full colour one side | shop ≈ $1.00–1.50 a sheet (one university FedEx rate sheet: $1.40 for 12 × 18 cardstock) | ≈ $1.00 (ask the shop for a quantity price) | custom-printed and die-cut from a carton printer (Arka, Packlane, PakFactory): roughly $0.60–1.50, needs a quote | hand cutting about 4 min each until a die-cut run makes sense |
| Home tabloid inkjet (if owned) | ≈ $0.80 (paper + ink) | same | – | only if a wide-format printer is already there |
| **Kraft mailing tube 4 × 12 in with caps** (ULINE S-6242) | $2.17 | $2.11 | $1.88 | carton of 25 |
| Tube wrap, 11 × 17 in colour on paper or label stock | ≈ $0.60–1.00 | ≈ $0.60 | ≈ $0.40 | glue stick or double tape |
| **Shipping box 12 × 3 × 3 in** (ULINE S-16721) | $0.73 | ≈ $0.68 | ≈ $0.59 | bundle of 25; fits the tuck box or the bag |
| **Custom-printed boxes**: Packlane (cardstock product boxes, 25 minimum, online quote), Arka (10 minimum, "from $0.99"), EcoEnclose (100 minimum for branded; plates from $95), Packwire (folding cartons 500 minimum) | $3–10 each | $1.50–4 | $0.60–1.50 | worth it only after the kits sell; a plate or die costs money up front |
| **UPC barcode** (GS1 US single GTIN) | $30 one-time per product (no renewal) | | | only if a store asks; a company prefix (10+ products) is about $250 |

**Cheapest workable route (recommended):** home-printed header cards; Starter boxes printed at a local shop on 11 × 17 in cover stock and hand-cut; ULINE tubes and 12 × 3 × 3 in boxes in cartons of 25; poly bags in a 1,000 carton (they keep). Move to a custom die-cut box from Arka or Packlane only when 100+ Starters a season are selling.

## Farmers-market display

Budget about **$60–120**, most of it reusable. Check first that the market takes non-food makers. The Ellensburg Farmers Market site (Saturdays 9 am – 1 pm) lists a vendor application but no category list or fee. Ask about booth fees, insurance and whether they want a WA business licence number.

- **Table and cloth:** the market's 6 ft table or your own, with a Night (navy) cloth or a navy flat sheet ($10–15).
- **Riser:** a 1 × 8 pine board on two bricks or a cut-down crate. Stand the Starter boxes and Big tubes upright, front out, in a row like a quiver of arrows.
- **Peg display for Minis:** a 2 × 4 ft pegboard ($12–15) on a cheap tabletop easel or clamped to the canopy leg, with 6 in peg hooks ($8).
- **The demo (the thing that stops people):** one built rocket of each kit on a launch rod in a wood block (**no motor**, ever), and a **string-swing stability test**. Tie a string at the rocket's balance point and swing it round your head, and it flies nose-first. Let kids try it and say the brand line: *fins are fletching*. A sectioned or exploded rocket shows the anchor strap and cord.
- **Design-your-own corner:** a tablet or old laptop showing rocket.quiverdesignworks.net, and a QR code sign ("Design your own rocket, free").
- **Signs:** one tabloid poster on Night (logo, "3D-printed model rocket kits, designed in Ellensburg"), price cards, an "Ages 12+ · motors sold separately" note, and a "Where do I get motors?" card that sends people to local hobby stores and the supply page.
- **Payments and leads:** Stripe or Square tap-to-pay on a phone, a small cash box, and a clipboard sign-up for a "launch day" email (a free group launch at a local field is the best seller of all, but launch away from the market and follow the NAR code).
- **Don't** bring motors or igniters, and don't launch at the market.

## Making the first 10 kits

Start with **10 Starter kits** (the hero), then 10 Minis for the market. About 30 printer-hours and 4 owner-hours for the first 10 Starters.

1. **Freeze the design.** In Rocket Builder (Beginner: M18, printer 256 mm, height 300 mm, trapezoid fins), build, save the design file and the STLs. Keep them with the kit SKU (`RB-KIT-M18`).
2. **Test-fly** two prints on B6-4, B4-6 and C6-7. Weigh the parts, check the app's altitude, delay and parachute, and update the box numbers if they changed.
3. **Order supplies** (about $95 up front, most of it lasting 25–75 kits): 1/8 in braided flat elastic, about 50–100 yd (~$8–12; plus a roll of 1/4 in for the Big kit), 1 mil plastic drop cloth (~$5), nylon line (~$5), hole reinforcement labels (~$3), Estes wadding 75 sheets (~$7), snap swivels size 14 ×100 and size 12 ×25 (~$8–10), inkjet vinyl decal sheets (~$14), 65–110 lb cover cardstock (~$15), ULINE 12 × 3 × 3 in boxes ×25 (~$18), 2 × 3 in zip bags ×100 (~$5). Optional: GS1 barcode ($30).
4. **Print the parts** for 10 rockets: full plates of the same part, PLA, one colour per batch. Number the batch.
5. **Make 10 parachutes** from a 12 in hexagon template (cut 10 at once from stacked plastic), with six lines and reinforcements. About 6 minutes each. Cut 10 × 4 ft of cord, count out 4 wadding sheets per kit, and print and trim the decals.
6. **Print the quick-start cards** (stream D's assembly guide, first page or two, with the QR code).
7. **Print 10 boxes** at a print shop from `tuck-box-starter.html` (Save as PDF, 11 × 17 in, 100 % scale, cover stock), with the QR and barcode placeholders replaced. Cut, score and glue them.
8. **QC each kit:** dry-fit A, B and D, screw cap E on fully, check the fins and the standoff for print defects, and tick the parts against the box list.
9. **Pack:** fin can D upright, nose and anchor beside it, small parts in the zip bag, then chute with its snap swivel, cord, wadding, decals and card. Close the box and write the batch number and month on side 2.
10. **Photograph** two kits and one built rocket by a window or in a $20 light box for the store listing and social posts. Make the mockups with the AI tools below.
11. **Sell:** two farmers-market Saturdays, then the online store, then approach one or two local shops with the results.

## Selling in local stores

- **Who:** toy and game stores, hobby shops, science and nature stores, museum and planetarium gift shops, and bookstores with a STEM shelf. Call or visit with a finished Starter and a one-page price sheet.
- **Terms:** wholesale at 50 % of retail with a minimum of 6 per kit, or consignment at 65–70 % to the maker if they'd rather not buy (common for local makers, but more bookkeeping). Offer a free counter display: a shipping carton cut down and wrapped with the tube-wrap art.
- **What they'll ask for:** a barcode (GS1), the age grade and warnings (on the package), a certificate of insurance (product liability), sometimes a W-9, and how to reorder.

## Selling online

Kit listings would go in quiverdesignworks-site `src/data/products.json` (prices, weights and names are read on the server; the browser sends only SKUs). **Draft only, not applied.** It also needs a category in `src/data/store.json → categories`: `{ "slug": "rocket-kits", "name": "Rocket Kits" }`. Fields follow the existing products. `weightOz` is per item (the store adds `packagingOz: 4` per order), and `boxIn` is the shipping box in inches (the order desk keeps the biggest one in the order for the Pirate Ship CSV). Images go under `public/images/kits/`. Keep `active: false` until the photos and the first batch are ready.

Weights: Mini ≈ 42 g with bag and card (1.5 oz, listed as 2), Starter ≈ 97 g with box (3.4 oz → 4), Big ≈ 285 g with the tube (10 oz), Classroom ≈ 430 g of kits (15 oz) plus a 12 × 10 × 6 in carton. Weigh the real ones.

```json
[
  {
    "active": false,
    "categories": ["rocket-kits"],
    "slug": "rocket-builder-starter-kit",
    "name": "Rocket Builder Starter kit (18 mm)",
    "seoDescription": "3D-printed model rocket kit for 18 mm B and C motors. Pre-printed parts, no painting. Ages 12+. Motors not included.",
    "description": "<p>A 30 cm (11.8 in) model rocket, 3D-printed in Ellensburg, WA, and designed with <a href=\"https://rocket.quiverdesignworks.net/\">Rocket Builder</a>. Pre-printed parts and no painting: about an hour to build.</p><p><strong>In the box:</strong> nose cone, anchor section, fin can with motor mount, screw-on motor cap, launch-lug standoff, 4 ft of 1/8 in braided elastic shock cord, 12 in parachute with snap swivel, 4 sheets of recovery wadding, waterproof decals and a quick-start card. The full step-by-step guide is online.</p><p><strong>Flies on 18 mm motors:</strong> B6-4 (first flight), B4-6, C6-7; up to about 355 m (1,160 ft).</p><p><strong>You also need:</strong> motors, igniters, a launch pad with a 1/8 in rod and an electric launch controller, and super glue. <strong>Motors not included.</strong></p><p>Ages 12+. Adults handle motors and launching. Follow the NAR Model Rocket Safety Code. WARNING: CHOKING HAZARD – Small parts. Not for children under 3 yrs.</p>",
    "fulfillment": "self",
    "images": ["/images/kits/starter-1.jpg", "/images/kits/starter-2.jpg", "/images/kits/starter-built.jpg"],
    "variants": [
      { "sku": "RB-KIT-M18", "label": "", "priceCents": 2999, "weightOz": 4, "boxIn": { "length": 12, "width": 3, "height": 3 }, "soldOut": false }
    ]
  },
  {
    "active": false,
    "categories": ["rocket-kits"],
    "slug": "rocket-builder-big-kit",
    "name": "Rocket Builder Big kit (24 mm)",
    "seoDescription": "3D-printed model rocket kit for 24 mm C and D motors, packed in a kraft tube. Ages 12+. Motors not included.",
    "description": "<p>A 36 cm (14 in) model rocket for D motors, 3D-printed in Ellensburg, WA, and packed in its own quiver (a 4 x 12 in kraft tube).</p><p><strong>In the tube:</strong> nose cone, anchor section, fin can with motor mount, screw-on motor cap, launch-lug standoff, 5 ft of 1/4 in braided elastic shock cord, 15 in parachute with snap swivel, 6 sheets of recovery wadding, waterproof decals and a quick-start card.</p><p><strong>Flies on 24 mm motors:</strong> C11-5 (first flight), D12-7; up to about 420 m (1,370 ft). Needs a field at least 150 m (500 ft) across for D motors.</p><p><strong>Motors not included.</strong> You also need igniters, a launch pad with a 1/8 in rod, a launch controller and super glue.</p><p>Ages 12+. Adults handle motors and launching. WARNING: CHOKING HAZARD – Small parts. Not for children under 3 yrs.</p>",
    "fulfillment": "self",
    "images": ["/images/kits/big-1.jpg", "/images/kits/big-built.jpg"],
    "variants": [
      { "sku": "RB-KIT-M24", "label": "", "priceCents": 3999, "weightOz": 10, "boxIn": { "length": 12.5, "width": 4.25, "height": 4.25 }, "soldOut": false }
    ]
  },
  {
    "active": false,
    "categories": ["rocket-kits"],
    "slug": "rocket-builder-mini-kit",
    "name": "Rocket Builder Mini kit (13 mm)",
    "seoDescription": "Small 3D-printed model rocket kit for 13 mm A10-3T motors. Flies in a 30 m field. Ages 12+. Motors not included.",
    "description": "<p>A 19 cm (7.5 in) mini rocket, 3D-printed in Ellensburg, WA. Flies about 110 m (365 ft) on an A10-3T and needs only a 30 m (100 ft) field.</p><p><strong>In the bag:</strong> nose cone, anchor section, fin can, motor cap, launch-lug standoff, 3 ft of 1/8 in elastic shock cord, streamer with snap swivel, 3 sheets of wadding, decals and a quick-start card.</p><p><strong>Motors not included</strong> (13 mm A10-3T). Ages 12+. Adults handle motors and launching. WARNING: CHOKING HAZARD – Small parts. Not for children under 3 yrs.</p>",
    "fulfillment": "self",
    "images": ["/images/kits/mini-1.jpg"],
    "variants": [
      { "sku": "RB-KIT-M13", "label": "", "priceCents": 1699, "weightOz": 2, "boxIn": { "length": 12, "width": 3, "height": 3 }, "soldOut": false }
    ]
  },
  {
    "active": false,
    "categories": ["rocket-kits"],
    "slug": "rocket-builder-classroom-6-pack",
    "name": "Rocket Builder classroom 6-pack (18 mm)",
    "seoDescription": "Six 3D-printed Starter rocket kits for a class or club, with a teacher sheet. For ages 12+ with an adult leader. Motors not included.",
    "description": "<p>Six Starter rockets (18 mm), each bagged with its parts, elastic shock cord, 12 in parachute with snap swivel and wadding, plus a teacher sheet linking to the free Rocket Builder lessons. For middle- and high-school groups (ages 12+) led by an adult who handles all motors and launching.</p><p><strong>Motors not included.</strong> Flies on B6-4, B4-6 and C6-7.</p><p>WARNING: CHOKING HAZARD – Small parts. Not for children under 3 yrs.</p>",
    "fulfillment": "self",
    "images": ["/images/kits/classroom-1.jpg"],
    "variants": [
      { "sku": "RB-KIT-M18-6PK", "label": "", "priceCents": 9900, "weightOz": 22, "boxIn": { "length": 12, "width": 10, "height": 6 }, "soldOut": false }
    ]
  }
]
```

Store notes: the store charges flat US shipping ($8) and $25 international (`store.json → shipping.zones`). Shipping rocket kits **without motors** abroad is fine as far as hazmat goes, but check each country's toy and consumer rules before enabling `intl` for kits; the simplest is a US-only note in the description at first. Stripe's automatic tax handles WA sales tax online; `productTaxCode` stays general tangible goods.

## Research: comparable kits

**Packaging.** Estes and Quest sell beginner kits in **printed boxes or bags with a header card** to hang on peg hooks. Bulk "no fancy packaging" singles come in clear bags, about 30 % cheaper (eRockets: Alpha III bulk single $12.29 vs $19.99–24.99 boxed; Quest Astra III bulk $17.89 vs $21.99 MSRP). Classroom bulk packs come in plain cartons: Alpha III 12-pack $144.99 (STEMfinity), Estes Viking bulk pack $94.99 (Walmart).

**What's on the package** (Estes, Quest):

- **Skill level.** Estes uses E2X (easy, pre-coloured, about 1 hour), then Levels 1–5 (Beginner, Intermediate, Advanced, Expert, Master), from more painting, gluing and sanding up to 3+ day builds. Quest uses Skill Level 1+ and calls one-piece fin-can kits "quick kits", 30–45 minutes. Ours are closest to E2X / Skill 1. The brand shows the skill as 1–3 orange chevrons, labelled "Skill 1 · about 1 hour".
- **Recommended motors,** often with the first-flight motor highlighted (Alpha III lists 1/2A6-2, A8-3, A8-5, B4-4, B6-4, B6-6, C6-5, C6-7), and the projected maximum altitude (Alpha III: about 1,100 ft on a C).
- **"Engines sold separately" / "motors not included"** in plain words, plus "Requires assembly" and a list of what you also need (glue, launch system).
- **Age grade:** Estes's catalogue says model rocketry is "recommended for ages 10 and up with adult supervision for those under 12". Retail titles often say "12 years and up". Some kits (Estes Luna Bug at Target) show "13 years and up" plus the CPSC small-parts choking warning.
- **In the box:** body tube or fin can, nose cone, fins (molded or laser-cut), engine mount, shock cord and mount, a 12 in plastic parachute (beginner kits), a launch lug, self-stick decals and instructions. Not included: motors, igniters, wadding, glue and the launch system. Launch *sets* add a pad and controller (Alpha III launch set $35.99).

**Price points.** 13 mm minis about $11 (Mosquito). Skill 1 18 mm kits $14–25 (Quest America $13.99–17.91, Seeker $21.49; Estes Alpha III $19.99–24.99). 24 mm "big" kits $35–40 (Big Daddy). Classroom 12-packs about $12 a rocket.

## Compliance and labels

**This is research, not legal advice.** The points marked _Confirm_ need a product-safety lawyer or consultant before the first sale. A one-hour consult is a good use of a small budget. The lowest-risk route is below.

### The safest simple route

**Decision (owner, 2026-10-18): all kits are labelled "Ages 12+".** The points below assume it; the open question for the professional is only how the kits are marketed next to the app's Beginner mode and the curriculum.

1. **Age grade every kit "Ages 12+".** Put "Adults handle motors and launching" or "Launching requires adult supervision" beside it. Market the kits as a hobby and STEM product for teens, adults, families, makers and educators, not as a toy for kids. No cartoon characters, no "for kids", no grade levels under 7 in kit copy or photos. (The Estes convention of "10+ with adult supervision under 12" is used by a large company that can test; we stay at 12+.)
2. **Add the standard small-parts warning anyway:** "WARNING: CHOKING HAZARD – Small parts. Not for children under 3 yrs." It isn't legally required for a 12+ general-use product (see below), but it's free and expected by stores.
3. **Mark a batch number, month, maker and city** on every package ("Quiver Design Works LLC, Ellensburg, WA, USA · Batch … · Made 11/2026"). That is what a CPSIA tracking label needs. It costs nothing, helps with any recall, and is already on the artwork.
4. **No motors, igniters or glue in the kit.** Point to the NAR Model Rocket Safety Code on the package.
5. **No unqualified "Made in USA".** Use "Designed and 3D-printed in Ellensburg, WA" (already on the artwork).
6. **Get product liability insurance** before stores and markets, and keep the file licence and safety terms the app already has (`server/terms.py`, not yet lawyer-reviewed).

### Details

| Topic | What applies | What we do | Confidence |
|---|---|---|---|
| **Children's product or general use** (CPSIA) | A "children's product" is one "designed or intended primarily for children 12 years of age or younger". CPSC weighs four factors together: the maker's statement and label, how it is marketed, how consumers see it, and its Age Determination Guidelines. A 12+ label is "only one of the factors". Products for 9–12 year-olds are not automatically children's products, and "scientific equipment" like microscopes and telescopes is listed as general use. Kits "designed and primarily intended for children 12 years of age or younger" make every item in them a children's product. | Label 12+ and market to teens and adults. **Conflict to resolve:** the app's Beginner mode is "aimed at grades 3–7" and the curriculum (stream C) is grades 5–8. Selling a kit *with* that curriculum, or with "for kids" copy, pushes it towards a children's product. Keep kit marketing separate, or decide to go the children's-product route. | Medium. _Confirm_ |
| **If it is a children's product** | A Children's Product Certificate based on testing by a CPSC-accepted third-party lab (for example lead in substrate and in any paint, phthalates in plasticised parts, and the ASTM F963 toy standard as it applies); permanent tracking labels on the product and package; age grading. Small Batch Manufacturer registration (gross revenue under about $1.4 million) relieves some "Group B" tests, but never "Group A" ones, and never the tracking labels. | Avoid this route at first. If the owner wants a "Grades 5–8 classroom kit" later, budget for lab quotes (typically hundreds to a few thousand dollars per product: get quotes) and register as a small batch manufacturer. | Medium. _Confirm_ |
| **Small-parts rules** (16 CFR 1501 and 1500.19/.20) | Small parts are **banned** in products for children under 3. Products for ages 3–6 with small parts need the choking-hazard warning. A 12+ general-use kit needs neither. | Add the warning voluntarily (as Estes does on some kits). Parts E and F and the cap are small parts. | High |
| **Motors** | Model rocket motors are exempt from the "banned hazardous substance" rules under 16 CFR 1500.85(a)(8), with conditions. NAR code: certified, commercially made motors only. | We don't sell motors; the package says "Motors not included" and names the motors. | High |
| **Model rocket definition** (NFPA 1122, NAR code) | Up to 1,500 g at liftoff and up to 125 g of propellant; no metal body parts or fins. NAR code: stand 15 ft back for D motors and smaller, wait 60 s after a misfire with the key out, rod within 30° of vertical, wind under 20 mph, site sizes A 100 ft, B 200 ft, C 400 ft, D 500 ft. | Our largest kit is 71 g of PLA plus a 44 g D12, well inside. The box and tube text follow these numbers. | High |
| **Country of origin** | US law doesn't require a "Made in USA" label on domestic goods. If you *claim* it unqualified on a label, the product must be "all or virtually all" made in the US (FTC Made in USA Labeling Rule, 16 CFR 323). Filament, parachute plastic and elastic are likely imported. | Use "Designed and 3D-printed in Ellensburg, WA, USA", no "Made in USA". | Medium. _Confirm_ the wording |
| **Washington State** | A WA business licence with a UBI and sales-tax collection apply to retail sales, including at markets (a free temporary certificate exists for up to two events a year, per a third-party guide). The WA Children's Safe Products Act (RCW 70.240, WAC 173-334) asks makers of *children's* products to report chemicals of concern, another reason to stay general use. The WA fireworks rules (WAC 212-17-015) exclude model rockets and motors, and we don't sell motors anyway. Ellensburg may need a city endorsement on the state licence. | The LLC presumably has a UBI already: add the market's location for tax reporting, collect sales tax at the market (Kittitas County / Ellensburg rate), check the city endorsement. | Medium. _Confirm_ with WA DOR / the city |
| **Insurance** | Markets and stores often ask for general and product liability insurance with a certificate. | Get quotes for an LLC policy covering products sold; it also covers the printed-rocket orders. | – |
| **Online to California** | Prop 65 warnings: businesses with fewer than 10 employees are exempt. | Nothing to add now. | High |
| **Barcode** | Not a legal requirement; stores may require one. | GS1 US single GTIN, $30 per product, once. | High |

**Questions for the professional:** (1) Is a 12+ labelled kit general use given the app and curriculum aim younger? What marketing must we avoid? (2) Is "Designed and 3D-printed in Ellensburg, WA" fine? (3) Do we need anything for the classroom pack sold to teachers of grades 7–8? (4) Liability wording on the package and the online listing, and does `server/terms.py` cover physical kits? (5) WA and Ellensburg licence and tax steps for market sales.

## AI and low-cost design tools

The strongest **instruction** imagery will come from the app's own renders (stream D, `docs/assembly/images/`). Those are accurate and on-brand, and any AI image of our parts would be wrong in detail. So the AI tools are for **packaging mockups, lifestyle and marketing photos, social posts and market signs**.

Two rules for any AI image:

- **Don't show a product that doesn't exist.** Mockups must use our real artwork or a real photo of the kit. Composite real product photos onto AI backgrounds, rather than letting the AI draw the rocket.
- **Purely AI-generated images can't be copyrighted** (US Copyright Office, Jan 2025 report: prompts alone are not enough). So the logo and key art stay human-made, as the brand kit is.

| Tool | Good for here | Price (2026, check) | Free tier | Commercial use of outputs | Verdict |
|---|---|---|---|---|---|
| **Canva** (Magic Design, Magic Media, Mockups, Brand Kit) | Market signs, price cards, social posts, store listing images, quick mockups, flyers for launch days; upload `tokens.css` colours and the logo as a Brand Kit (Pro) | Pro about $15–18/mo or $120–180/yr (sources disagree) | Yes, with AI caps | Canva's AI Product Terms: you own your outputs (except where they include Canva's licensed content); outputs may not be unique | **Top pick:** free tier covers most of it; one month of Pro for a Brand Kit and background remover when needed |
| **Pacdora** | 3D mockups of *our* box and tube from the dieline (upload artwork), dieline library, product shots for the listing before printing | Lite about $9–18/mo; Pro about $17–29/mo (sources disagree) | Yes, watermarked, personal-use licence | Commercial use needs a paid plan | **Top pick for packaging:** one month of Lite when it's time for listing images |
| **Adobe Express / Firefly** | Generative fill and backgrounds ("rocket kit on a picnic table at a launch field"), remove backgrounds from real kit photos, resize for social | Express Premium $9.99/mo (250 credits); Firefly Standard $9.99/mo | Yes (limited credits) | Adobe markets Firefly as "commercially safe" (trained on licensed content) | **Top pick for photos:** composite real kit photos into scenes |
| Ideogram | Images with readable text (posters, social cards) | Plus $15–20/mo | Yes, but images are public | Allowed on all tiers per third parties; free images are public | Optional |
| Recraft | Vector illustrations in a locked brand style (icons, spot drawings), real SVG output | about $10–12/mo | Yes, but free images are public, owned by Recraft, **no commercial licence** | Paid plans only | Good for icons later; don't use the free tier for anything you sell |
| Midjourney | Moody lifestyle and hero imagery | Basic $10/mo; private (Stealth) mode only on Pro $60/mo | No | Allowed on paid plans (Pro required above $1M revenue) | Skip: images are public on cheap plans, and it can't show our real product |
| Kittl | Badges, labels, retro-style type for stickers and decals | Pro about $10–15/mo | Yes, personal use only | Pro and up | Optional for decal sheets |
| Looka | AI logo and brand kit | Logo $20–65 one-time; Brand Kit about $96/yr | Design free, pay to download | Yes, on purchase | **Not needed:** the brand kit already exists (`docs/brand/`) |
| Scribe / Tango / Guidde | Step-by-step guides from screen recordings: good for a "How to design your rocket in the app" walkthrough or video | Scribe free (web only), Tango free (few shared guides), Guidde free (25 videos) | Yes | Yes | Nice-to-have for an *app* walkthrough; not for building the kit |
| Gamma | Quick decks or one-page sites: a wholesale "line sheet" for stores, a teacher overview | Plus about $8–10/mo | 400 one-time credits | Yes | Optional: a one-page line sheet in Canva works too |
| **Inkscape** (free, open source) | Edit the dieline SVGs, convert text to outlines for printers, make the QR and barcode layers | Free | – | Yours | **Use it** for print files |
| **Blender** (free) | Photo-real renders of the kit from the generator's STLs, a turntable video | Free | – | Yours | Best "product photo" before the first print run |
| Figma (free Starter) | Layouts, social templates, shared with a collaborator | Free (limited files) | – | Yours | Optional; Canva covers this for one person |
| Phone + free editor (CapCut, Clipchamp) | 15–30 s launch and build videos for social | Free | – | Yours | Real launch videos beat any AI video |

**Top three for this budget:** **Canva free** (signs, posts, listing images; Pro for one month when building the brand kit), **Pacdora** (one paid month for true-to-dieline 3D box and tube mockups), and **Adobe Express / Firefly** (commercially safe generative backgrounds around real kit photos). Plus free **Inkscape** and **Blender** for the print files and renders.

## Sources

Comparable kits and packaging

- eRockets, Estes Alpha III kit EST 1256 (price, contents, recommended motors): https://www.erockets.biz/estes-flying-model-rocket-kit-alpha-iii-est-1256/
- eRockets, Alpha III bulk single, no fancy packaging: https://www.erockets.biz/estes-flying-model-rocket-kit-alpha-iii-single-bulk-pack-kit-no-fancy-packaging-est-1751bk
- eRockets, Alpha III launch set EST 1427: https://erockets.biz/estes-flying-model-rocket-launch-set-alpha-iii-est-1427
- eRockets, Quest Astra III bulk single: https://www.erockets.biz/quest-flying-model-rocket-kit-astra-3-single-bulk-pack-kit-no-fancy-packaging-qst-6110bk/
- Quest Aerospace, Seeker Q1611: https://questaerospace.com/products/product_6475c4bd-e535-3406-b178-2a7831b65d37
- Walmart, Quest Payloader One (Skill 1, 12+): https://www.walmart.com/ip/40468946
- STEMfinity, Alpha III bulk pack (12): https://stemfinity.com/collections/middle-school/products/alpha-iii%C2%AE-bulk-pack-12-pk
- Walmart, Alpha III classroom bulk pack: https://www.walmart.com/ip/Estes-Alpha-III-Rockets-Classroom-Bulk-Pack/37290418
- Ward's Science, Estes Big Daddy: https://www.wardsci.com/us/en/product/43631722/estes-big-daddy-model-rocket
- eRockets, Big Daddy EST 2162: https://www.erockets.biz/estes-flying-model-rocket-kit-big-daddy-est-2162-oop/
- eRockets, Mini Mosquito EST 1345: https://www.erockets.biz/estes-flying-model-rocket-kit-mosquito-est-1345-oop/
- Estes skill levels resource: https://cdn.shopify.com/s/files/1/0869/9363/3572/files/estesskilllevelsresource.pdf
- Estes 2025 catalogue (ages 10+, supervision under 12): https://b2b.estesrockets.com/cdn/shop/files/2025-Estes-Catalog.pdf
- Target, Estes Luna Bug (13+, choking warning): https://www.target.com/p/estes-816-luna-bug-rocket-building-kit-intermediate-mini-flying-rocket-model-kit/-/A-1008829252
- Hobby Etc, Estes 12 in parachute: https://store.hobbyetc.com/parts/view/86924
- Hobby Etc, Estes shock cords and mount pack: https://store.hobbyetc.com/parts/view/123057

Compliance

- CPSC, Children's products (definition, factors, kits): https://www.cpsc.gov/business--manufacturing/business-education/childrens-products/
- Federal Register 2010, final rule interpreting "children's product": https://www.gpo.gov/fdsys/pkg/FR-2010-04-20/pdf/2010-8431.pdf
- CPSC, Small parts for toys and children's products: https://cpsc.gov/Business--Manufacturing/Business-Education/Business-Guidance/Small-Parts-for-Toys-and-Childrens-Products
- CPSC, Small parts and choking hazard labelling FAQs: https://cpsc.gov/FAQ/Small-Parts-and-Choking-Hazard-Labeling-FAQs
- CPSC, Children's Product Certificate: https://www.cpsc.gov/FAQ/Children’s-Product-Certificate
- CPSC, Tracking label FAQ: https://www.cpsc.gov/FAQ/Tracking-Label
- CPSC, Small batch manufacturers and third-party testing: https://cpsc.gov/Business--Manufacturing/Small-Business-Resources/Small-Batch-Manufacturers-and-Third-Party-
- CPSC, Business Desktop Reference Guide (Sep 2023): https://www.cpsc.gov/s3fs-public/CPSC-Business-Desktop-Reference-Guide-Sep-2023.pdf
- 16 CFR 1500.85 exemptions (model rocket motors, (a)(8)): https://www.law.cornell.edu/cfr/text/16/1500.85
- NAR Model Rocket Safety Code: https://nar.org/ModelRocketSafetyCode (text checked via https://stormthecastle.com/model-rockets/rocket-safety-code.htm)
- California AB 467 (1,500 g model rocket, NFPA 1122 reference): https://www.leginfo.ca.gov/pub/15-16/bill/asm/ab_0451-0500/ab_467_bill_20150707_enrolled.htm
- FTC Made in USA Labeling Rule (16 CFR 323): https://www.ftc.gov/made-in-usa-rule
- WAC 212-17-015 (fireworks rules exclude model rockets): https://lawfilesext.leg.wa.gov/Law/WACArchive/2020/htm/WAC%20212%20%20TITLE/WAC%20212%20-%2017%20%20CHAPTER/WAC%20212%20-%2017%20-015.htm
- RCW 70.77 (fireworks): https://app.leg.wa.gov/Rcw/dispo.aspx?Cite=70.77
- WA Children's Safe Products reporting rule, WSR 17-07-131: https://lawfilesext.leg.wa.gov/law/wsr/2017/07/17-07-131.htm
- Craft-fair licence guide for Washington (third party): https://www.thecraftmap.com/vendor-guides/craft-fair-permits/washington
- Prop 65, exemptions: https://www.p65warnings.ca.gov/faq/businesses/are-any-businesses-exempt-proposition-65
- GS1 US single GTIN pricing (via barcode.graphics): https://www.barcode.graphics/gs1-lowers-minimum-quantity-for-upc-gtins/
- Ellensburg Farmers Market: https://ellensburgfarmersmarket.com/

Packaging suppliers

- ULINE 4 × 12 in 2 mil poly bags S-1003: https://www.uline.com/Product/Detail/S-1003/Flat-Poly-Bags/4-x-12-2-Mil-Industrial-Poly-Bags
- ULINE 12 × 3 × 3 in long box S-16721: https://www.uline.com/Product/Detail/S-16721/Corrugated-Boxes-200-Test/12-x-3-x-3-Long-Corrugated-Boxes
- ULINE kraft mailing tube 4 × 12 in S-6242: https://www.uline.com/Product/Detail/S-6242/Kraft-Mailing-Tubes/Kraft-Mailing-Tubes-with-End-Caps-4-x-12-080-thick
- Packlane product boxes: https://packlane.com/products/product-boxes
- EcoEnclose custom boxes: https://www.ecoenclose.com/shop/custom-shipping-boxes
- Arka (10-box minimum, pricing claims): https://www.arka.com/blogs/news/top-packaging-companies
- Packwire FAQ (minimums): https://packwire.com/faq
- Folding carton cost range (vendor guide): https://gonextpage.com/how-much-do-custom-folding-cartons-cost/
- FedEx Office university rate sheet (12 × 18 cardstock): https://research.stonybrook.edu/commcms/aux/services/fedex-pricing
- GPO Express pricing guide May 2026 (12 × 18 cover reference): https://www.gpo.gov/docs/default-source/gpoexpress-pdf-files/gpoexpress-pricing-guide_may-1-2026.pdf
- Inkjet vinyl sticker paper prices: https://www.walmart.com/ip/Koala-Printable-Vinyl-Sticker-Paper-for-Inkjet-Printers-20-Sheets-Glossy-White-Waterproof-Stickers-Paper-8-5x11-Inch-Tear-Resistant/709606730
- Shock cord by the foot (Ripstop by the Roll): https://ripstopbytheroll.com/products/shock-cord

AI and design tools

- Canva AI Product Terms: https://www.canva.com/policies/ai-product-terms
- Canva pricing 2026 (third party): https://piktochart.com/blog/canva-pricing-2026-costs-raised/
- Adobe Express pricing: https://www.adobe.com/ara/express/pricing?tab=4 and Capterra summary https://www.capterra.com/p/174232/adobe-express/pricing/
- Adobe Firefly pricing (third party): https://aiproductivity.ai/pricing/adobe-firefly/
- Recraft pricing and licence (third party): https://www.eesel.ai/blog/recraft-ai-pricing
- Ideogram pricing (third party): https://www.krea.ai/blog/what-is-ideogram-ai-features-pricing-and-alternatives-in-2026
- Midjourney pricing (third party): https://www.krea.ai/blog/is-midjourney-free-pricing-video-and-free-alternatives-in-2026
- Pacdora pricing and dielines: https://www.toolworthy.ai/tool/pacdora and https://pacdora.com/resource/paper-boxes-packaging
- Kittl pricing (third party): https://www.wearefounders.uk/kittl-pricing-2026-every-plan-explained/
- Looka pricing (third party): https://pricingsaas.com/companies/looka
- Scribe vs Tango vs Guidde (third party): https://dubble.so/compare/scribe-vs-tango-vs-guidde
- Gamma pricing (third party): https://www.eesel.ai/en/blog/gamma-pricing
- US Copyright Office AI report part 2, summary: https://www.jonesday.com/en/insights/2025/02/copyrightability-of-ai-outputs-us-copyright-office-analyzes-human-authorship-requirement

Many tool prices come from third-party summaries that disagree with each other; check each vendor's pricing page before paying.
