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

## Fit (joint clearances, 2026-10-15)

Details: `HANDOFF.md` (Fit test coupons) and `fit_test/README.md`.

- [x] **(owner)** Print `fit_test/files/fit_test_*.3mf` (P1S, PLA, 2026-10-16); results in `fit_test/README.md`
- [ ] **(owner)** Print the M13 round-2 plate and one full rocket with the new fits; X1C check
- [x] Per-size `fit_joint` / `fit_nose` rule from the results (`params.web_fits`); `shoulder_chamfer` on; pinned test numbers updated
- [x] Disclaimer on the STL download (build notes + both guides; `FIT_NOTE` in `server/app.py`). Original wording: "Joint fits are tuned for Bambu Lab X1C / P1S at default PLA settings. Other printers or settings may need a light sanding of the shoulders (too tight) or a wrap of tape (too loose)."
- [ ] **(owner)** Print `fit_test/files/motor_caps/motor_cap_test.step`, try real motors in each, and measure a spent casing's wall per size (calipers) to replace the estimates in `geometry/rocketgen/data/motor_casings.csv`
- [ ] Separate Fit Test Builder app: kickoff handoff in `docs/fit_test_app_handoff.md` (2026-10-16)
- [ ] Admin option "Print test parts for fitment": one size's socket + plugs, a range of sizes, or the joints of a saved rocket (its tube, fits and nose shoulder) without the full parts. `fit_test.coupons()` is the starting point; serve the 3MF from `/api` behind the admin check.

## Done

- [x] Printer height before rocket height; tutorial button overlap fixed; motor, fins and height in saved names (2026-10-14)
- [x] Beginner heights (and printer) snap to ones that build; built height matches the chosen one (2026-10-14)
- [x] Score advice outside the 1-2 cal sweet spot, with predicted scores (2026-10-14)
- [x] Compare two rockets side by side (scores, summaries, which is better and why) (2026-10-15)
- [x] Launch field size with parachute drift (2026-10-15)
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
