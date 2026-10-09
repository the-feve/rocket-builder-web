# Handoff

_Last updated 2026-10-09 (night). Read this first, then `README.md` (Status) and `docs/web_platform_spec.md`._

## Where things stand

- **PR [the-feve/rocket-builder-web#1](https://github.com/the-feve/rocket-builder-web/pull/1)** (`claude/optimistic-ptolemy-utrlds` → `main`) holds everything since Phase 1. **CI is green** on head `977f3c2`: geometry tests (42), server tests (8), and the Docker image builds, starts and serves a rocket. It waits only on the owner to merge.
- `main` still has only Phase 1 (the geometry engine).
- Not hosted yet. Fly.io account, app `rocket-fevergeon` and volume `rocket_data` (region `sjc`) were created on 2026-10-09; the deploy token and merge are next (steps below).

### What the designer does now (`server/`, FastAPI + one page with a three.js preview)
- Form → build → 3D preview (exploded, section) → ZIP of print-oriented STLs + `build_notes.txt` + `design.json`.
- Dark theme by default, light toggle (remembered in localStorage).
- **Stability check** (`geometry/rocketgen/stability.py`): Barrowman CP, CG from part centroids + loaded motor + recovery allowance. CG (blue) and CP (red) balls on the model. Under 1.0 cal with the chosen motor the ZIP is withheld (409).
- **Auto-sized fins** (`build_stable`): standard fins grow in span and sweep (not root: a longer root moves the CP forward) until the heaviest motor of the size is stable. M24 1.48x, M24L 1.52x, M29 1.91x; M18/M13 unchanged. Rectangular on M29 hits the 2.5x cap at 0.76 cal and is reported unstable. Custom fins are left as typed.
- **Motor picker** (`geometry/rocketgen/flight.py`, ported from OS_Rocket_Builder `tools/motor-picker.html`; data `geometry/rocketgen/data/web_motors.csv`): every Estes motor for the bay flown in a 1-D sim; checks 5x thrust-to-weight, 15 m/s off the rod, 30 m apogee, and stability with that motor's mass. Recommends the closest safe motor to the target altitude, with its delay. Clicking a row re-checks stability with that motor.
- **Saved designs + share links** (`server/designs.py`): SQLite at `ROCKETGEN_DB`; `/d/<id>` links; an edit key per browser stands in for sign-in. "My rockets" list in localStorage.
- **Hosting guards:** `/healthz`; per-address limits (30 new builds / 10 min, 60 saves / hour); 60 s max wait for the build lock (then 503); failed builds logged with parameters; three.js r160 vendored in `server/static/vendor/` (no CDN).
- **Deploy plumbing:** `Dockerfile` (python:3.12-slim-bookworm), `fly.toml` (app `rocket-fevergeon`, region `sjc` (Fly no longer offers `sea`), shared-cpu-1x 1 GB, suspends when idle, volume `rocket_data` at `/data`), `.github/workflows/ci.yml`, `.github/workflows/deploy.yml` (deploys on push to `main`; skips with a notice until `FLY_API_TOKEN` is set).

## Next steps (in order)

1. **Owner: Fly.io setup** (Windows PowerShell):
   1. Sign up at https://fly.io/app/sign-up and add a card under Billing.
   2. Install: `powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"`, reopen PowerShell, `fly auth login`.
   3. `fly apps create rocket-fevergeon` (if the name is taken, pick another and change `app` in `fly.toml`).
   4. `fly volumes create rocket_data --region sjc --size 1 -a rocket-fevergeon` (answer `y` to the single-volume warning). `sea` returned "region sea not found"; use `fly platform regions` for the current list. The app's `primary_region` in `fly.toml` must match the volume's region.
   Steps 1–4 done 2026-10-09 (Google sign-in; no Fly password needed: `fly auth login` uses the browser).
   5. `fly tokens create deploy -a rocket-fevergeon -x 999999h`; copy the whole output including `FlyV1 `. Don't paste it in chat.
   6. GitHub → repo Settings → Secrets and variables → Actions → New repository secret: `FLY_API_TOKEN` = that token.
2. **Owner: merge PR #1.** The deploy runs from the Actions tab (first one ~5–10 min). Then open https://rocket-fevergeon.fly.dev and try a build.
3. **Claude: check the first deploy** (Actions log, `/healthz`, a build, a save + share link surviving a restart, which proves the volume).
4. **After fevergeon.com's DNS moves to Cloudflare** (fevergeon-site `TODO.md` P1): `fly certs add rocket.fevergeon.com -a rocket-fevergeon`, a CNAME `rocket` → `rocket-fevergeon.fly.dev` in Cloudflare, then Cloudflare Access (Zero Trust, free ≤ 50 users, email one-time PIN) in front for the invite-only beta. Note: with the Cloudflare proxy on, Fly's certificate check may need the record DNS-only until the cert issues.
5. **Beta checks:** print and fly one or two rockets; compare 2–3 designs against OpenRocket (stability and apogee). Results go in `geometry/report.md`.
6. **Phase 4:** paid downloads via the shared Stripe account, every Checkout Session tagged `metadata.store = "rocket-builder"` (rules in fevergeon-site `docs/stripe-shared-account.md`); check Washington sales tax on digital goods.

## Decisions log

- 2026-10-08: Phase 2 server moved here from OS_Rocket_Builder (`claude/phase2-web-prototype`). OS_Rocket_Builder's `web/` folder on that branch is redundant and can be deleted.
- 2026-10-08: Dark theme default.
- 2026-10-08: Unstable designs: option (c) chosen: keep the download block, and auto-size standard fins so every motor size's default design is stable. Keep the CG/CP preview and info.
- 2026-10-08: Motor picker built into the designer; motor masses come from its ThrustCurve table (`web_motors.csv`), replacing the earlier rough `web_motor_masses.csv`.
- 2026-10-09: Hosting: Fly.io for the app (persistent volume keeps SQLite simple), Cloudflare for DNS and Access. Cloudflare Containers rejected for now (no persistent disk; would need D1).
- 2026-10-09: Region `sjc` (San Jose): `sea` isn't available on Fly any more.
- 2026-10-09: Invite-only beta via Cloudflare Access rather than building sign-in; real accounts wait for public/paid launch.

## Open items / known limits

- Stability and flight numbers are estimates (Barrowman, 1-D sim, trapezoid fin planform, solid-PLA masses); not yet checked against OpenRocket.
- Motor masses are Estes ThrustCurve values; two are flagged (1/2A6 mass estimated; E9/E12 out of production).
- In-memory caches (last 40 geometries, builds, rate-limit counters) reset on every restart or Fly suspend; only saved designs persist.
- Saved designs have no owner yet (edit key in the browser). Sign-in replaces it when accounts arrive (`owner` column already exists).
- Two cosmetic geometry gaps from Phase 1 remain (leading-edge root fillet, some lug rounds); see `geometry/report.md`.

## Other repos

- **the-feve/fevergeon-site** (Astro on Cloudflare Pages, Quiver Design Works store with Stripe + Pirate Ship export). Live on a Cloudflare preview; DNS not moved; its `TODO.md` has the go-live list. Its Rocket Builder status lines (HANDOFF.md, TODO.md P2) are stale ("Phase 2 next"); update them in that repo's next session. Its default branch is still a `claude/…` branch; merging to `main` is on its P1 list.
- **the-feve/OS_Rocket_Builder**: the FeatureScript reference (`src/RocketGenerator.fs`, latest on `anchor-section`).

## How to run locally

```powershell
cd rocket-builder-web
python -m venv .venv; .venv\Scripts\Activate.ps1
cd server; pip install -r requirements.txt
uvicorn app:app --reload        # http://127.0.0.1:8000
```
Tests: `python -m pytest -q` in `geometry/` (~1.5 min) and in `server/` (~45 s).
