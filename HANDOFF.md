# Handoff

_Last updated 2026-10-09 (night). Read this first, then `README.md` (Status) and `docs/web_platform_spec.md`._

## Where things stand

- **PR [the-feve/rocket-builder-web#1](https://github.com/the-feve/rocket-builder-web/pull/1)** (`claude/optimistic-ptolemy-utrlds` → `main`) holds everything since Phase 1. **CI is green** on head `977f3c2`: geometry tests (42), server tests (8), and the Docker image builds, starts and serves a rocket. It waits only on the owner to merge.
- `main` still has only Phase 1 (the geometry engine).
- **Live since 2026-10-09: https://rocket-fevergeon.fly.dev** (Fly app `rocket-fevergeon`, region `sjc`, volume `rocket_data` mounted at `/data`). PR #1 is merged; pushes to `main` deploy automatically. Checked after the first deploy: `/healthz`, an M24 build (24.7 s cold, stable 1.13 cal, recommends C11), preview GLB, the STL ZIP, saving a design and its `/d/<id>` share link (test design `WNePTzVr`). The machine auto-suspends after about 7 idle minutes; a cold boot takes about 17 s before uvicorn answers.

### What the designer does now (`server/`, FastAPI + one page with a three.js preview)
- Form → build → 3D preview (exploded, section) → ZIP of print-oriented STLs + `build_notes.txt` + `design.json`.
- Dark theme by default, light toggle (remembered in localStorage).
- **Stability check** (`geometry/rocketgen/stability.py`): Barrowman CP, CG from part centroids + loaded motor + recovery allowance. CG (blue) and CP (red) balls on the model. Under 1.0 cal with the chosen motor the ZIP is withheld (409).
- **Auto-sized fins** (`build_stable`): standard fins grow in span and sweep (not root: a longer root moves the CP forward) until the heaviest motor of the size is stable. M24 1.48x, M24L 1.52x, M29 1.91x; M18/M13 unchanged. Rectangular on M29 hits the 2.5x cap at 0.76 cal and is reported unstable. Custom fins are left as typed.
- **Motor picker** (`geometry/rocketgen/flight.py`, ported from OS_Rocket_Builder `tools/motor-picker.html`; data `geometry/rocketgen/data/web_motors.csv`): every Estes motor for the bay flown in a 1-D sim; checks 5x thrust-to-weight, 15 m/s off the rod, 30 m apogee, and stability with that motor's mass. Recommends the closest safe motor to the target altitude, with its delay. Clicking a row re-checks stability with that motor.
- **Saved designs + share links** (`server/designs.py`): SQLite at `ROCKETGEN_DB`; `/d/<id>` links; an edit key per browser stands in for sign-in. "My rockets" list in localStorage.
- **Advanced: wall thickness and Body OD offset (2026-10-09):** *Wall thickness* (0.8-3 mm, default 1.5 from the settings CSV) sets the body tubes, nose cone and motor mount (`DesignParams.wall`); the stock tube is the motor bay + 2 walls. *Body OD offset* replaces the absolute Body OD: radial mm over the stock tube (5 = +10 mm diameter), shown live as "Body OD … (stock … + 2 × …)" under the field. The server turns it into `body_od_override`; designs saved with the old override still build and open as the matching offset.
- **Nose insert and cord strap (2026-10-09, after the owner's first prints/preview):** nose shoulder 30% shorter than body joints; the anchor strap is now a straight bar across the bore (wall to wall) with the cord gap behind it and a 45-degree pointed arch underneath (prints without supports). Details in `geometry/report.md` (Deliberate differences).
- **Beginner / Advanced modes (2026-10-09):** Beginner is the default (remembered in localStorage). It shows motor size, printer max height, **overall height** (nose tip to fin tips / motor cap), nose shape (no fineness) and three fin shapes (swept, delta, trapezoid; default trapezoid; no custom fins). Every other field is sent as the default. The server turns `overall_length` into `body_length` with `rocketgen.build.body_length_for` (exact, using `overall_length()`, which matches `Balance.length`); if auto-sized fins change how far they trail below the tail, `_build_to_length` rebuilds once. Switching modes carries the design over (body length ↔ overall height from the last build); Beginner resets the advanced fields. A saved design with `overall_length` opens in Beginner, any other in Advanced.
- **Build prompts (2026-10-09):** any change shows "Settings changed. Press Build…" above Build (and greys out the ZIP until rebuilt); a progress bar on the 3D view eases toward 95% while building (builds report no progress) with elapsed seconds.
- **User guide (2026-10-10):** before the first build the 3D view shows a guide (`#guide` in `index.html`): how to use the app, Beginner vs Advanced, each report section (stability margin, motor picker columns and pass criteria, parts, build notes, key dimensions), and what OpenRocket is and what to check in it. A **Key terms** glossary (2026-10-10, owner wants it educational) explains stability (CG, CP, calibers, margin, with a diagram, Barrowman), motors (size, the C6-5 code, thrust/impulse, thrust-to-weight), flight (rod speed, apogee, ejection delay, Cd, field size) and recovery/parts. It hides after a build; the **Guide** button reopens it, and the report's "OpenRocket" link jumps to that section. Keep it in step when the UI, the pass criteria (`flight.py`, `stability.py`) or the report change.
- **Design files (2026-10-09):** *Download file* saves `<name>.rocket.json` (`format`, `schemaVersion`, `name`, `mode`, `params`); *Open file* loads it, or the `design.json` from an STL ZIP, as an unsaved design and builds it.
- **Save flow (2026-10-09):** *New rocket* resets to defaults, asks for a name and saves. *Save* overwrites your own design silently. On an unsaved design, a shared one, or *Save as new*, it asks for a name first (copies suggest "<name> (copy)"). A status label shows *Not saved yet* / *Saved · yours to edit* / *Shared design*, and save messages are coloured, with errors caught. The owner found the old flow unclear: saving kept the shared design's name and showed only a small grey line.
- **Hosting guards:** `/healthz`; per-address limits (30 new builds / 10 min, 60 saves / hour); 60 s max wait for the build lock (then 503); failed builds logged with parameters; three.js r160 vendored in `server/static/vendor/` (no CDN).
- **Deploy plumbing:** `Dockerfile` (python:3.12-slim-bookworm), `fly.toml` (app `rocket-fevergeon`, region `sjc` (Fly no longer offers `sea`), shared-cpu-1x 1 GB, suspends when idle, volume `rocket_data` at `/data`), `.github/workflows/ci.yml`, `.github/workflows/deploy.yml` (deploys on push to `main`; skips with a notice until `FLY_API_TOKEN` is set).

## Next steps (in order)

0. **Pending merge (2026-10-10):** the Key terms glossary is committed on `claude/confident-wozniak-6hvero` (8c3b0ba) but not yet merged or deployed. Open a PR to `main` and merge it once CI passes; the merge deploys to Fly.
1. **Owner: Fly.io setup** (Windows PowerShell):
   1. Sign up at https://fly.io/app/sign-up and add a card under Billing.
   2. Install: `powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"`, reopen PowerShell, `fly auth login`.
   3. `fly apps create rocket-fevergeon` (if the name is taken, pick another and change `app` in `fly.toml`).
   4. `fly volumes create rocket_data --region sjc --size 1 -a rocket-fevergeon` (answer `y` to the single-volume warning). `sea` returned "region sea not found"; use `fly platform regions` for the current list. The app's `primary_region` in `fly.toml` must match the volume's region.
   Steps 1–4 done 2026-10-09 (Google sign-in; no Fly password needed: `fly auth login` uses the browser).
   5. `fly tokens create deploy -a rocket-fevergeon -x 999999h`; copy the whole output including `FlyV1 `. Don't paste it in chat.
   6. GitHub → repo Settings → Secrets and variables → Actions → New repository secret: `FLY_API_TOKEN` = that token.
2. ~~Merge PR #1~~ and ~~check the first deploy~~: done 2026-10-09. The first deploy run skipped itself (green, 8 s) because `FLY_API_TOKEN` had been added to the fevergeon-site repo by mistake; once it was on this repo, a manual run of `deploy.yml` deployed.
3. **Still to confirm:** a saved design surviving a full restart (`fly apps restart rocket-fevergeon`, then open `/d/WNePTzVr`). Suspend/resume doesn't prove it; the volume mount in the boot log is good evidence.
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
- 2026-10-09: The deploy workflow passes (green) when the token is missing; check that the run actually ran `flyctl deploy`, not just a green tick.
- 2026-10-09: Saving stays server-side (SQLite on the Fly volume) with per-browser edit keys until accounts arrive; a download/open design-file option is a possible extra (design.json is already in the ZIP).
- 2026-10-09: Invite-only beta via Cloudflare Access rather than building sign-in; real accounts wait for public/paid launch.

## Open items / known limits

- Stability and flight numbers are estimates (Barrowman, 1-D sim, trapezoid fin planform, solid-PLA masses); not yet checked against OpenRocket.
- Motor masses are Estes ThrustCurve values; two are flagged (1/2A6 mass estimated; E9/E12 out of production).
- In-memory caches (last 40 geometries, builds, rate-limit counters) reset on every restart or Fly suspend; only saved designs persist.
- Saved designs have no owner yet (edit key in the browser). Sign-in replaces it when accounts arrive (`owner` column already exists).
- Two cosmetic geometry gaps from Phase 1 remain (leading-edge root fillet, some lug rounds); see `geometry/report.md`.

## Other repos

- **the-feve/fevergeon-site** (Astro on Cloudflare Pages, Quiver Design Works store with Stripe + Pirate Ship export). Live on a Cloudflare preview; DNS not moved; its `TODO.md` has the go-live list. Its Rocket Builder status lines were updated on 2026-10-09 to point at the live Fly app. Its default branch is still a `claude/…` branch; merging to `main` is on its P1 list.
- **the-feve/OS_Rocket_Builder**: the FeatureScript reference (`src/RocketGenerator.fs`, latest on `anchor-section`).

## How to run locally

```powershell
cd rocket-builder-web
python -m venv .venv; .venv\Scripts\Activate.ps1
cd server; pip install -r requirements.txt
uvicorn app:app --reload        # http://127.0.0.1:8000
```
Tests: `python -m pytest -q` in `geometry/` (~1.5 min) and in `server/` (~45 s).
