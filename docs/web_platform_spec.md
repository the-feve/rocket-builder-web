# Rocket Builder Web: platform spec and plan

_Draft 1, 2026-10-07. Status: proposal. Nothing here is built yet._

## 1. Goal

Rocket Builder Web is a standalone website, with no Onshape account or link, where someone can:

1. Sign in.
2. Design a 3D-printable model rocket from a guided set of choices (motor, body, fins, nose, lugs, material), with a live 3D preview.
3. Download print-ready STL files for every part.
4. Optionally pay to have the rocket printed and shipped.

It is meant to become a paid service.

The Onshape FeatureScript generator (`src/RocketGenerator.fs`) stays the **reference design**: it is where the geometry is proven. The website re-implements the same geometry on a CAD kernel we can run ourselves.

## 2. The one big decision: geometry engine

Everything the generator does today relies on Onshape's Parasolid kernel:
- revolves
- booleans
- fillets (fin roots, tips and lugs)
- helical sweeps (the motor-cap thread)

Off Onshape we need our own kernel. The options:

| Option | What it is | Fillets / threads | Runs where | Verdict |
|---|---|---|---|---|
| **build123d / CadQuery (OpenCascade)** | Python B-rep CAD, same modelling style as FeatureScript (sketch, revolve, extrude, boolean, fillet, sweep) | Real fillets, helix sweeps, STEP and STL export | Server (Linux container) | **Recommended for v1.** It's the closest match to the FeatureScript, so the port is mostly a translation. |
| replicad / opencascade.js | The same OpenCascade kernel compiled to WebAssembly | Same as above | In the browser | Good later option for instant preview with no server cost. The WASM bundle is large (~10–30 MB) and slower to debug. |
| Manifold | Fast, robust mesh booleans (WASM or Python) | No true fillets; they would have to be built into the profiles by hand | Either | Too much rework of the fillet logic. Possibly useful later as a fast preview engine. |
| OpenSCAD | Script-based mesh CSG | Fillets are awkward | Server | No. |
| Keep Onshape as a hidden backend via its API | Our FeatureScript, driven by the API | As today | Onshape | No. It goes against "no Onshape link", has API cost and rate limits, and makes Onshape's terms a dependency of the business. |

**Recommendation:**
- **Engine:** port the generator to **build123d on the server**.
- **Preview:** the browser asks for a build and shows the returned mesh (GLB) with three.js.
- **Source of truth:** a single geometry code path produces both the preview and the STLs.

**Expected friction:**
- OpenCascade fillets can be as fussy as the Onshape ones were. The solid-first build order, the tail-extension-then-trim trick and the other workarounds in `FeatureScript_Reference_Notes.md` are likely to carry over.
- The Phase 0 spike (§6) exists to find out early.

## 3. What the user sees (v1)

1. **Landing page:** what it is, example rockets, pricing.
2. **Sign up / sign in:** email magic link or Google.
3. **Designer:**
   - **Left panel:** the same groups as today's feature dialog.
     - Motor (M13 / M18 / M24 / M24L / M29)
     - Body length / diameter
     - Fins (shape, count, size, fillets)
     - Nose (shape, fineness)
     - Launch lugs (+ standoff)
     - Material
     - Printer max height
   - **Right panel:** 3D preview with part colours, exploded-view toggle and a section-view toggle.
   - **Live readouts:** estimated mass, part list, and stability (§5.3).
   - **Validation messages:** the same `regenError` cases, worded for a user.
4. **My rockets:** saved designs, duplicate, rename, share link.
5. **Download:**
   - a ZIP of one STL per part, already in print orientation;
   - a one-page PDF/HTML print sheet (orientation, suggested settings, assembly order, motor fit notes);
   - optionally an OpenRocket `.ork` file so users can simulate the flight.
6. **Order a print:** pick material and colour, see the price and lead time, then pay. The order is tracked on an "Orders" page.

**Explicitly not in v1:**
- free-form CAD editing
- user-uploaded parts
- multi-stage rockets
- motor sales

## 4. Architecture

```
Browser (Next.js + React + three.js / react-three-fiber)
   │  design params (JSON)            ▲ GLB preview, ZIP/STL links
   ▼                                   │
API (Next.js route handlers or FastAPI)
   │  enqueue build {params, generatorVersion}
   ▼
Geometry worker(s)  — Python + build123d in a Docker image
   │  writes GLB + STL ZIP, keyed by hash(params + generatorVersion)
   ▼
Object storage (Cloudflare R2 or S3)       Postgres (users, designs, orders)
                                           Stripe (checkout, tax, webhooks)
```

The stack, part by part (the choices are swappable; this is a sensible low-ops default):

| Concern | Choice | Why |
|---|---|---|
| Frontend | Next.js (React, TypeScript) + react-three-fiber | Common, well documented, easy to host |
| Auth, DB and storage in one | **Supabase** (Postgres + Auth + Storage) | One service instead of three while small. Clerk + Neon + R2 is the alternative. |
| Geometry worker | Python 3.12 + build123d + FastAPI, in a Docker container on Fly.io or Render | OpenCascade needs a real Linux box. It scales by adding machines. |
| Job queue | Start synchronous (one request, one build, ~2–10 s). Add a Redis/RQ queue once there are concurrent users. | Avoids building infrastructure before it's needed |
| Caching | Same params + same generator version = reuse the stored output | Repeat previews and downloads cost nothing |
| Payments | Stripe Checkout + Stripe Tax + webhooks | Handles cards, receipts and sales tax/VAT |
| Email | Resend or Postmark | Order confirmations and magic links |
| Hosting | Vercel (frontend) + Fly.io (worker) + Supabase | Each has a free or cheap tier to start |

**Generator versioning:**
- Every saved design stores `generatorVersion` and a `schemaVersion` for its parameters.
- Old designs re-download exactly as they were, and can be offered "upgrade to latest".

**Rough running cost before revenue:** about $0–50/month (domain, small worker machine, free tiers). Stripe takes about 2.9% + 30¢ per payment.

## 5. Geometry port plan (the core work)

### 5.1 Approach

- Port function by function from `src/RocketGenerator.fs` into a Python package, `rocketgen/`:
  - `params.py`: a parameters schema (pydantic) and derived values. This mirrors `computeDerivedValues` and the dialog bounds and defaults.
  - `motors.py`: the motor and tube library. Today it's the Variable Studio data in `data/*.csv`; it becomes a JSON/CSV table versioned in the repo.
  - `fins.py`, `aft.py`, `thread.py`, `body.py`, `nose.py`, `lugs.py`, `anchor.py`: one module per feature group, each named after its FeatureScript counterpart.
  - `build.py`: `build_rocket(params) -> {part_name: Solid}`, plus mass and notes.
  - `export.py`: STL (and STEP) per part in print orientation, GLB for preview, ZIP bundle.
- Keep the FeatureScript's comments that explain **why** (gotchas, owner decisions), not the dated revision history.
- Units are mm throughout, as today.

### 5.2 Proving parity with Onshape (golden tests)

The owner exports reference data from Onshape for a fixed set of configurations (no API calls):
- **Configurations:** M18 min-diameter Clipped delta; M18 Swept; M13; M24 at a larger body OD (inner mount); 4 fins; each nose shape once.
- **Per configuration:** one STL per part, and the mass report line from the feature banner.

For each configuration, the Python tests check:
- part count and names;
- per-part volume within 1%;
- bounding box within 0.1 mm;
- key dimensions (bay ID, shoulder OD, thread pitch, motor hang-out) exactly;
- optionally, the mesh distance between the Onshape STL and the new STL within 0.05 mm.

These tests become the regression suite for every future change. Ideally the Onshape generator is frozen once parity is reached; otherwise every change has to be made twice.

### 5.3 New features the website needs (not in the generator today)

1. **Stability (CG / CP) check.** This is the most important safety feature for a public tool.
   - CP from the Barrowman equations (nose + fins; the body contributes nothing).
   - CG from part masses + motor mass + an estimate for recovery hardware.
   - Shown in calibers, with a hard block or strong warning below 1.0 cal, the same way OpenRocket reports it.
   - The motor library needs loaded and empty motor masses added.
2. **OpenRocket `.ork` export** (XML), so users can run full flight simulations.
3. **Print orientation and print sheet:** each part rotated to its intended print direction (all parts already print shoulder-down or tail-down without supports), plus suggested slicer settings.
4. **Input guard rails:** sensible bounds so the generator can't be asked for something unbuildable or absurd. Every geometry failure must produce a friendly message, never a 500 error.

## 6. Phased roadmap

Each phase ends with something the owner can try.

| Phase | Output | Rough size |
|---|---|---|
| **0. Spike** | A Python repo that builds an M18 min-diameter rocket with build123d and writes STLs: <br>• body segment with joint taper<br>• nose (tangent ogive) with shoulder<br>• aft segment with trapezoid fins and **root fillets**<br>• **threaded boss + cap**<br>Volumes compared against `data/derived_printed_dimensions.csv` and hand-computed values. <br>**Decision point:** if OpenCascade can't do the fillets or the thread reliably, go back to §2. | 2–4 evenings |
| **1. Parity** | Every feature from the FeatureScript (all fin shapes, nose shapes, lugs + standoff, anchor section, segmentation, mass), passing the golden tests | 2–4 weeks part-time |
| **2. Local web prototype** | The designer page running locally: form → build → 3D preview → ZIP download. No accounts. | 1–2 weeks |
| **3. Hosted beta** | Deployed with sign-in, saved designs and share links. Free, invite-only. Stability check in. | 1–2 weeks |
| **4. Paid downloads** | Stripe. Pricing to be decided (see §8). | ~1 week |
| **5. Print service** | Order flow, an admin page to manage the print queue, shipping labels. Start with the owner printing in-house; add partner fulfilment if volume grows. | 2–3 weeks |
| **6. Nice to have** | `.ork` export, in-browser WASM preview, more motors, decals/colours, multi-stage | ongoing |

## 7. Business and legal checklist

These need real answers before charging money. They are questions, not legal advice; a short consult with a lawyer (product liability) and an accountant (sales tax, business entity) is worth it before Phase 4.

- **Liability for user-designed rockets.**
  - Terms of service and a disclaimer covering flying.
  - Follow the NAR Model Rocket Safety Code, and require users to accept it.
  - The stability check (§5.3) is both a safety feature and a liability one.
  - Consider product liability insurance before selling physical prints.
- **No motors or ejection charges sold.** The service sells plastic parts and files only. Many places restrict motor sales by age and by shipping method; we stay out of that.
- **Trademarks:** don't use "Estes" or other brand names in the product name or marketing. Motor sizes (13/18/24/29 mm) are fine.
- **Sales tax / VAT:** Stripe Tax covers digital downloads and physical goods. A business entity (e.g. an LLC) is advisable.
- **Privacy:** store only email, designs and orders. Payment data stays with Stripe. A privacy policy is required.
- **Print quality claims:** downloaded STLs are printed on the user's own machine, so promise nothing about how they fly. Prints from the service need a material and quality standard of our own.

## 8. Decisions needed from the owner

1. **Who it's for first:** hobbyists with their own printers (download business), people without printers (print business), or both from day one?
2. **Pricing model for downloads.** Options:
   - free to design, pay per download (e.g. $3–5 per rocket);
   - subscription for unlimited downloads;
   - free downloads, with revenue from prints only.
3. **Print fulfilment:** print it yourself at first, or use a print-on-demand partner (e.g. Craftcloud or JLC3DP)? Self-printing is simplest and keeps quality control.
4. **Materials and regions offered** for prints (PETG/ASA/PLA; US-only shipping at first?).
5. **The Onshape version** after parity: freeze it, or keep both in sync?
6. **Name and domain.**
7. **Repo layout:** a new repo (`rocket-builder-web`) for the website and the Python generator, keeping this repo as the Onshape reference. Recommended.

## 9. What can run overnight in the cloud (Phase 0)

A cloud agent can do Phase 0 unattended. Both branches must be pushed to GitHub first; today nothing is. Beyond that, it only needs this repo and a Linux box with `pip install build123d`. It cannot see or use Onshape, so it checks itself against the CSV and hand-computed volumes, not against Onshape renders.

The brief for that run:

1. Create `web/geometry/` (or a new repo, if the owner prefers): a Python package with `pyproject.toml`, `pytest`, and `build123d`.
2. Port, from `src/RocketGenerator.fs` **on the `anchor-section` branch** (the latest generator; it has the joint taper and lug stem, which `main` doesn't yet):
   - `computeDerivedValues` for M18 at minimum diameter
   - `buildBodySegment` (with the 8° inner taper)
   - `buildNoseCone` (tangent ogive)
   - `buildAftSegment` (trapezoid fins, root fillet, solid-first then cavity cut)
   - `threadGeometry` + `buildThreadedBoss` + `buildThreadedCap`
3. Export STLs per part, and a `report.md` with the volume of each part and anything that failed or needed a workaround.
4. Write tests that check the derived dimensions against `data/derived_printed_dimensions.csv` (M18-BT20 row), and that every part is a single closed solid.
5. Do **not** touch `src/RocketGenerator.fs` or `HANDOFF.md`. Work on a new branch and open a draft PR for review in the morning.

The owner's morning check:
- Open the STLs in a slicer or viewer.
- Read `report.md`.
- Decide whether build123d is the right engine (the §6 Phase 0 decision point).
