# Rocket Builder: to do

Ordering, payment and the data they collect. Ticked items are done; **(owner)** items need
Matthew (accounts, keys, decisions); the rest is code. Details of what's built are in
`HANDOFF.md` (Print orders, Accounts).

## Switch ordering on (owner, Fly secrets)

Set with `fly secrets set -a rocket-fevergeon NAME=value …` (never in chat or git):

- [ ] **(owner)** `ROCKETGEN_ADMIN_EMAILS`: the owner's account email(s) for `/admin`; then create that account on the site
- [ ] **(owner)** `ROCKETGEN_COUPON_CODES`: comma-separated codes that make an order free (needed for any order until payment exists)
- [ ] **(owner)** `ROCKETGEN_SYNC_TOKEN`: long random string; the same value as `ROCKET_SYNC_TOKEN` on the PC
- [ ] **(owner)** PC sync: `tools/README.md` (save the token with `setx`, test `sync_orders.py`, add the Task Scheduler task)
- [ ] **(owner)** Place a test order with a coupon; check the folder in `C:\RocketOrders`, the `/admin` page and the email

## Email (Resend)

- [ ] **(owner)** Resend account (free tier); create an API key
- [ ] **(owner)** Verify the sending domain `quiverdesignworks.net` in Resend (DNS records in Cloudflare)
- [ ] **(owner)** Set `RESEND_API_KEY`, `ROCKETGEN_NOTIFY_TO` (owner's email), `ROCKETGEN_MAIL_FROM` (e.g. `Rocket Builder <orders@quiverdesignworks.net>`)
- [ ] Order confirmation email to the customer (needs the verified domain)
- [ ] Status emails to the customer: printing, shipped (with tracking)
- [ ] Password reset by email (accounts currently have no reset)

## Payment (Stripe)

- [ ] **(owner)** Pricing: per rocket, by part height or filament mass; colour and quantity rules; minimum order
- [ ] **(owner)** Shipping: flat rate or by weight; US only to start?
- [ ] Stripe Checkout on the shared account; every Checkout Session tagged `metadata.store = "rocket-builder"` (rules in the-feve/quiverdesignworks-site `docs/stripe-shared-account.md`)
- [ ] Webhook (`checkout.session.completed`) marks the order paid; only paid (or couponed) orders reach the print queue, the folder and the sync
- [ ] Move coupons to Stripe promotion codes (percent / amount off, expiry, usage limits); keep a free code for beta testers
- [ ] Price shown in the order form before paying; receipt from Stripe
- [ ] Refunds and cancellation: who can cancel, and until which status
- [ ] **(owner)** Sales tax: Washington sales tax applies to physical goods shipped in WA; check with an accountant (and whether Stripe Tax is worth it)
- [ ] Remove the "coupon required" rule once payment works

## Orders and fulfilment

- [ ] Tracking number field on `/admin`, shown under *My orders* and in the shipped email
- [ ] Address checks (ZIP format, state list); non-US addresses later
- [ ] Owner notes on an order; reprint flag
- [ ] Print queue view by batch (all parts for the day, total filament and print height)
- [ ] Capacity: pause ordering, or show a lead time, when the queue is long
- [ ] Backups of the Fly volume (`/data`: designs, accounts, orders and order files), e.g. a nightly copy to R2/S3

## Supplies page

- [ ] **(owner)** Photos: add your own photos of the gear you use to `server/static/gear/` and set `"photo"` on those items in `server/gear.json`
- [ ] Live Amazon product images (and prices) through the Creators API once the Associates account qualifies (10 qualifying sales in 30 days); register under Associates Central → Tools → Creators API, then fetch images server-side and cache them no longer than Amazon allows
- [x] Motors for 13, 24 and 29 mm added (2026-10-14; checked in stock on Amazon): 1/2A3-4T, A3-4T, A3-6T, A10-3T, C6-7, C11-3, D12-3, F15-4
- [ ] Not on Amazon (unavailable) on 2026-10-14: D12-5, D12-7, C11-5, C11-7, E16-x, 1/4A3-3T; re-check, and add them with `"motors"` tags when listed (D12-5 especially). E9/E12 (24 mm long) are out of production
- [ ] **(owner)** Re-check the list every few months (`checked` in gear.json): discontinued items, better picks

## Data and legal (needed before opening ordering to the public)

- [ ] **(owner)** Privacy policy page: what's stored (email, designs, shipping addresses, order history), why, how long, how to delete; Stripe holds card data
- [ ] **(owner)** Terms of sale: printed parts are a kit, motors are bought separately, flying follows the NAR safety code, liability
- [ ] **(owner)** COPPA review: the site is used by children; accounts are for 13+ or a parent/guardian (checkbox at sign-up). Confirm with a lawyer that this is enough, and that ordering stays grown-up only
- [ ] Delete my account (and its designs and orders) from the account panel
- [ ] Remove shipping addresses from old shipped orders after N months
- [ ] **(owner)** Product liability check before charging money (see `docs/web_platform_spec.md`, Legal and safety)

## Done

- [x] Printer height before rocket height; tutorial button overlap fixed; motor, fins and height in saved names (2026-10-14)
- [x] Beginner heights (and printer) snap to ones that build; built height matches the chosen one (2026-10-14)
- [x] Score advice outside the 1-2 cal sweet spot, with predicted scores (2026-10-14)
- [x] Compare two rockets side by side (scores, summaries, which is better and why) (2026-10-15)
- [x] Launch field size with parachute drift (2026-10-15)
- [x] Launch simulator page: liftoff, ejection, parachute drift in a wind the user sets, field size for it (2026-10-15)
- [x] Launch simulator inside the 3D view (*▶ Watch it launch*), printer picker, Sources and references page, rocket + trebuchet sections on the supplies page (2026-10-15)
- [ ] Prices on the supplies page once the Amazon Creators/PA API is available (10 qualifying sales in 30 days); not before (Associates policy)
- [x] Paid print orders through Stripe Checkout on the shared account, shipped via the store's Pirate Ship CSV (2026-10-15)
- [x] Shipping estimate from packed weight and box (2026-10-15)
- [x] Personal-use file license in downloads, STL headers, /terms and by the download/order buttons (2026-10-15)
- [ ] Owner: have the file license wording (`server/terms.py`) checked by a lawyer before paid launch
- [ ] Owner: Stripe restricted key + webhook + `ROCKETGEN_PUBLIC_URL` on Fly (HANDOFF Next steps 7), then one real order and refund
- [x] Order folder / file names: motor size and a customer code (2026-10-14)
- [x] Suggested parachute size from the rocket's mass (2026-10-14)
- [x] Drag handle between the 3D view and the report (2026-10-14)
- [x] Print-order portal with coupon codes; order folders with batch sheet; `/admin`; PC sync script (2026-10-14)
- [x] Accounts (email + password), saved rockets per account, skip-tutorial setting (2026-10-14)
- [x] Order Rocket Supplies page at /ordersupplies (Amazon affiliate list, drawings per item), linked from the header, the score and the welcome (2026-10-14)

## Assembly guide, kits and brand (2026-10-18, owner decisions)

- [x] ~~**(owner)** Body joints~~ (2026-10-18: medium CA such as Starbond Medium, adult only; guide updated). Was: glue them (the guide says thin CA) so the aft section can't separate at ejection, or tape / push-fit? Which glue for PETG and ASA?
- [x] ~~**(owner)** Shock cord for kits~~ (2026-10-18: braided elastic, 1/8 in on M13/M18, 1/4 in on M24/M29; strap and nose recess resized). Was: the slot behind the anchor strap is ~2.5 mm deep, so the guide says Kevlar or braided cord up to 2 mm, 2–3× the rocket's length. Confirm type and length.
- [ ] **(owner)** Nose fit (0.02 mm clearance): guide says sand if tight, a wrap of tape if loose. Confirm.
- [ ] **(owner)** Shorter motors than the bay length rattle: add motor spacers to the guide?
- [ ] **(owner)** Placeholders in the guide and packaging: skill level, age grade, kit numbers, QR codes, UPC (GS1, about $30 per product).
- [x] ~~**(owner)** Kit age grade~~ (2026-10-18: 12+ confirmed; curriculum under 12 is paper only). Was: the packaging says "Ages 12+" to stay a general-use product. Marketing kits to younger kids (Beginner mode, the curriculum) could make them children's products (CPSIA testing, certificate, tracking labels). Confirm with a professional; see `docs/kits/README.md`.
- [ ] **(owner)** Test-fly the three kit designs and weigh real prints before printing boxes (packaging numbers come from solid-PLA estimates).
- [x] ~~**(owner)** Apply the brand to the app~~ (done 2026-10-18) (`docs/brand/brand.md` → *How to apply this to the app*)?
- [ ] Leading-edge root fillet still doesn't build on the kit designs (known; `geometry/report.md`).
- [ ] **(owner)** Print a test strap and nose (M18) and thread your elastic before the next kit batch; a PETG scrap-joint pull test with medium CA.
- [x] ~~Fonts self-hosted~~ (2026-10-18). Still open: 3D part colours use the old palette.
