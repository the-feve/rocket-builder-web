# Expansion spec: guide, tutorial, brand, curriculum, assembly guide, kits

_2026-10-18. Owner request in one prompt, split into workstreams that can run in parallel. Each stream writes only in its own folder, so they don't collide._

| # | Stream | Where | Depends on |
|---|---|---|---|
| A | App: guide, tutorial and Advanced help changes | `server/static/index.html` | none |
| B | Brand kit | `docs/brand/` | none (sets the core tokens below) |
| C | Home-school curriculum (grades 5–8, 1–2 weeks) | `docs/curriculum/` | B for styling only |
| D | Assembly guide for printed rockets | `docs/assembly/` | B for styling; renders from `geometry/` |
| E | Kit packaging + AI design tool research | `docs/kits/` | B for styling |

## A. App changes (Rocket Builder, `server/static/index.html`)

1. **Motor sizing summary.** Explain the motor classes (1/4A to F) and the four motor sizes (M13, M18, M24, M29) in plain words: what each typically does for a 3D-printed rocket (altitude range), and the field it needs (NAR minimum field side, from `geometry/rocketgen/flight.py → FIELD_M`). Both in the quick start (inside the expandable section in 4) and in the full guide's *Motors* section.
2. **Restart tutorial button** next to the Beginner / Advanced switch.
3. **Advanced mode help pop-ups:** an ⓘ button on each Advanced section heading (Motor, Body, Fits and joints, Fins, Nose, Launch lugs, Material, Flight) that opens a detailed description of every option in it.
4. **Quick start opens with "How it works" only.** The stability-score explainer and the new motor summary move into a collapsed section, *More on rocket sizing and rating systems*.
5. **Darker greying during the tutorial,** and less text: steps that aren't current show only their heading; their explanations are hidden. Shorten the Beginner explanations for young readers.

## Brand core (stream B owns the details; everyone uses these)

- **Names:** *Rocket Builder* (the app and kits), *by Quiver Design Works*. Keep the existing names; don't invent a new product name.
- **Idea:** *fins are fletching.* Quiver = a quiver of arrows; a rocket's fins do the same job as an arrow's feathers. Blueprint grid and a dashed flight arc as supporting motifs.
- **Core colours (fixed hex values):**
  - Night (ink) `#12203A`
  - Paper `#F6F1E7`
  - Launch orange `#F2652B`
  - Sky blue `#3D8BFD` (already the CG dot colour in the app)
  - Signal red `#E5484D` (CP dot / warnings)
  - Go green `#2FB67C` (stable / OK)
  - Grey `#6E6E73`
- **Type (free Google Fonts):** Space Grotesk (headings), Inter (body). Numbers and part codes may use Space Grotesk's tabular figures.
- Assets live in `docs/brand/` (logo SVGs, `tokens.css`, `brand.md`, a one-page brand sheet). Other streams link to `docs/brand/tokens.css` and the logo files; if a file isn't there yet, use the values above.

## C. Curriculum

1–2 weeks, home-school style, about grades 5–8. Daily lessons with objectives, materials (cheap, household where possible), hands-on activities, worksheets, and a short check for understanding. Topics: Newton's laws, forces (thrust, weight, drag, lift), stability (CG/CP, with the string-swing test), impulse and motor codes, altitude estimation (inclinometer + trig), parachutes and descent, data and graphs, safety (NAR code), design iteration with Rocket Builder, launch day. Two tracks: with a 3D printer / with paper rockets only. Safety: adults handle motors and igniters.

## D. Assembly guide

Printable (US Letter) guide for after the parts are printed: tools and supplies row, parts layout with letter codes, numbered steps with drawings, motor prep and igniter install, recovery packing, preflight checklist, safety code. Images rendered from the generator itself (partially exploded views), with the shock cord, parachute and their attachment (cord through the anchor strap in the anchor section, to the nose shoulder; parachute on the cord; wadding/baffle) drawn in. Inspired by Estes kit instructions (header band with skill level, supply icons, lettered parts, step drawings, safety callouts) but not copying their layout.

## E. Kits and packaging

Complete kits for local stores, farmers markets and the online store: kit contents and BOM with costs, two or three packaging formats (e.g. header-card bag, tuck box, mailer tube) with dielines, front/back panel artwork, required labels and warnings, price points, and a farmers-market display idea. Plus research on AI design tools for walkthroughs, imagery, packaging mockups and branding, with costs (owner's budget is tight). Selling a kit online later means a product entry in quiverdesignworks-site `src/data/products.json`; not part of this pass.

## Status

- [x] A app changes (2026-10-18)
- [x] B brand kit (not applied to the app yet)
- [x] C curriculum
- [x] D assembly guide (owner questions in TODO.md)
- [x] E kits and packaging (owner decisions in TODO.md)
