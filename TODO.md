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

## Data and legal (needed before opening ordering to the public)

- [ ] **(owner)** Privacy policy page: what's stored (email, designs, shipping addresses, order history), why, how long, how to delete; Stripe holds card data
- [ ] **(owner)** Terms of sale: printed parts are a kit, motors are bought separately, flying follows the NAR safety code, liability
- [ ] **(owner)** COPPA review: the site is used by children; accounts are for 13+ or a parent/guardian (checkbox at sign-up). Confirm with a lawyer that this is enough, and that ordering stays grown-up only
- [ ] Delete my account (and its designs and orders) from the account panel
- [ ] Remove shipping addresses from old shipped orders after N months
- [ ] **(owner)** Product liability check before charging money (see `docs/web_platform_spec.md`, Legal and safety)

## Done

- [x] Print-order portal with coupon codes; order folders with batch sheet; `/admin`; PC sync script (2026-10-14)
- [x] Accounts (email + password), saved rockets per account, skip-tutorial setting (2026-10-14)
- [x] Gear link to fevergeon.com/cad/rocket-builder/gear/ (the Amazon affiliate gear list), with the Associates disclosure (2026-10-14)
