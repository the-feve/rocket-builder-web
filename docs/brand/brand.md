# Rocket Builder brand guide

_v1, 2026-10-18. Covers the app (rocket.quiverdesignworks.net), kits and packaging, the assembly guide and the curriculum. The core names, colours and fonts are fixed in `docs/expansion_spec_2026-10.md`; this guide adds the details. One-page summary: `brand-sheet.html` (picture: `brand-sheet.png`)._

## The idea

**Fins are fletching.** An arrow flies straight because its feathers sit behind its balance point, and a model rocket flies straight for the same reason. Quiver Design Works already has an arrow in its logo, so the Rocket Builder mark is that arrow's cousin: a rocket flying up and to the right at 45°, with fins drawn as two nested orange chevrons, the same shape as the fletching on the Quiver arrow. This is also the first thing we teach: balance point in front, push point behind, and the rocket flies straight.

The look is **blueprint meets field day**. Blueprint: a quiet grid, thin exact lines, lettered parts, numbers in a tidy technical face. Field day: warm paper, one bright launch orange, a dashed flight arc with launch puffs and a parachute, and short friendly sentences. Keep it flat (no gradients or shine), one accent per surface, and lots of paper.

## Files

| Path | What |
|---|---|
| `logo/rb-mark-{light,dark,mono}.svg` | The mark alone (64 × 64). `light` = for Paper/white, `dark` = for Night, `mono` = one colour (`currentColor`, Night by default). |
| `logo/rb-lockup-horizontal-{light,dark,mono}.svg` | Mark + "Rocket Builder" + "BY QUIVER DESIGN WORKS" (316 × 64). |
| `logo/rb-lockup-stacked-{light,dark,mono}.svg` | Mark above the words (216 × 136). |
| `logo/rb-favicon.svg`, `rb-favicon-light.svg` | 32 × 32 tile for tabs and app icons, no text. PNGs: `rb-favicon-32.png`, `rb-apple-touch-icon-180.png` (full-bleed, iOS rounds it), `rb-icon-512.png`. |
| `tokens.css` | Colours, theme mappings, type scale, radii, line weights, motifs as CSS, opt-in helper classes. |
| `patterns/` | Blueprint grid (tile + panel), flight arc, fletching band; each on Paper and on Night. |
| `illustration/step-sample.svg` | Reference drawing for the guide style below. |
| `src/` | Python scripts that wrote the logo and pattern SVGs (need `pip install fonttools` and the Space Grotesk TTFs in `src/fonts/`). |

Lettering in the logos is Space Grotesk converted to paths, so the SVGs need no font. The flight-arc pattern has one live-text label ("APOGEE") that uses `font-family: Space Grotesk`; convert it to outlines before sending the file to a printer.

## Logo use

- **Pick the variant by background,** not by taste: `light` on Paper or white, `dark` on Night, `mono` for one-colour printing (stamps, laser engraving, one-ink bags, embossing). The mono files use `currentColor`, so inline SVG takes the text colour.
- **Clear space:** keep a margin of **¼ of the mark's height** on every side (16 units on the 64-unit mark). In the lockups that equals about the height of the capital R.
- **Minimum sizes:**
  - Mark: **24 px** on screen, **8 mm** in print. Below that use `rb-favicon.svg` (one thick chevron, no seam line).
  - Horizontal lockup: **56 px tall** on screen (the byline is then about 9 px), **30 mm wide** in print. Smaller than that (for example the app header), use the mark plus "Rocket Builder" in live Space Grotesk 700 and put "by Quiver Design Works" elsewhere.
  - Stacked lockup: **96 px tall** / **20 mm wide**.
- **Next to the Quiver logo:** they share the arrow idea and the letter-spaced uppercase "DESIGN WORKS". Put them side by side with a 1 px vertical rule between them, the Quiver logo at about 70 % of the Rocket Builder lockup's height, both on the same baseline. Quiver's logo stays its own grey; don't recolour it to Night or orange.
- **Don'ts:**
  - Don't rotate the mark. 45° up and to the right is the flight direction; it never points down or left.
  - Don't recolour the fletching. It is always Launch orange (or the single colour in mono).
  - Don't add outlines, glows, drop shadows, gradients or flames.
  - Don't put the full-colour mark on photos or busy patterns. Use a Paper or Night tile behind it, or use mono.
  - Don't put the `light` version on Night or the `dark` one on Paper.
  - Don't stretch, squash or re-typeset the words. Don't swap the byline for "Quiver" alone.
  - Don't make the blueprint grid stronger than the logo; the grid is background only.

## Colour

The seven core values are fixed. Each one has a meaning, and the app, guide, curriculum and packaging all use it the same way, so kids learn it once.

| Colour | Hex | Means | Use it for |
|---|---|---|---|
| Night | `#12203A` | ink | Text, outlines in drawings, dark-theme backgrounds, primary "ink" buttons. |
| Paper | `#F6F1E7` | page | Light-theme background, box stock, guide pages. White (`#FFFDF8`) for fields and cards that lift off Paper. |
| Launch orange | `#F2652B` | **go / launch** | The one call to action per screen (Build, Add to cart, Launch), the fletching, motion arrows in drawings, step numbers. Not for warnings. |
| Sky blue | `#3D8BFD` | **balance point (CG)** | The CG dot, links and focus (use `--rb-sky-700` `#1D5BC4` for text on light), blueprint lines, "Tip" callouts. |
| Signal red | `#E5484D` | **push point (CP), stop** | The CP dot, errors, "Safety" callouts. Text on light uses `--rb-red-700` `#C22E33`. |
| Go green | `#2FB67C` | **stable / OK** | "Stable" badges, checklist ticks, success. Text on light uses `--rb-green-700` `#17754E`. |
| Grey | `#6E6E73` | secondary | Secondary text (4.5 : 1 on Paper), dimension and centre lines, captions. |

Supporting colours (not core, but in `tokens.css`):

- **Ramps:** each colour has a `-700` (text-safe on Paper/white), `-300` (text-safe on Night) and `-100` (soft fill behind a light-theme message). Night has a full ramp (`--rb-night-950` … `-50`) for dark-theme surfaces; `--rb-night-300` `#A9B4C8` ("Mist") is secondary text on Night.
- **Amber** (`--rb-amber-700` `#8A5A00` / `-300` `#F0B44C`) for "check this" warnings, so orange keeps meaning *go*.

Rules of thumb:

- **One orange thing per screen or panel.** If two buttons are orange, one of them is wrong.
- **Blue and red always come as a pair** in stability talk: blue dot in front, red dot behind. Never use red for the CG or blue for the CP, anywhere (app, worksheets, the string-swing test sheet).
- **Text on orange is Night,** never white (white on orange is 3.1 : 1; Night is 5.2 : 1).
- Colour never carries meaning alone: pair it with a word ("Stable", "Balance point") or an icon.

## Typography

- **Space Grotesk** (Google Fonts, OFL): headings, labels, part letters, step numbers and numbers. Weights 500/600/700. Use `font-variant-numeric: tabular-nums` for motor codes, lengths and scores so columns line up (`.rb-num`).
- **Inter** (Google Fonts, OFL): body text and UI. 400 for reading, 600 for buttons and emphasis.
- **Scale:** 1.25 from 16 px: 12 · 14 · 16 · 20 · 25 · 31 · 39 · 49 (`--rb-fs-xs` … `--rb-fs-4xl`). The app stays at 14 px body; print uses 11–12 pt body, 16–20 pt step headings.
- **Labels** are Space Grotesk 600, 12 px, UPPERCASE, letter-spacing 0.08em (`.rb-label`). The byline in the logo uses 0.15em, echoing "DESIGN WORKS" in the Quiver logo.
- Sentence case for headings and buttons ("Build my rocket", not "Build My Rocket"). No all-caps sentences.

## Illustration style (assembly guide, curriculum, packaging)

Line drawings should look like one person drew them all, with one pen. Reference: `illustration/step-sample.svg` and section 06 of the brand sheet.

- **Line weights** (at print size; the sample is drawn at 1 unit = 1 px for a 600 px wide panel):
  - Part outline: **2 px / 0.75 pt**, Night, round joins, filled Paper-white so overlapping parts hide what's behind.
  - Inner and detail edges: **1 px / 0.35 pt** Night.
  - Hidden edges: 1 px Night, **dashed 4 3**.
  - Centre lines: 1 px Grey, dash-dot (14 4 2 4).
  - Motion arrows: **2.5 px Launch orange** with a solid triangular head. One arrow per motion. Glue, marks and "do this here" spots are orange too.
  - Shock cord and string: 1.5 px Night, smooth curves. Parachute canopy: orange fill, Night outline.
- **Views:** flat side views or slightly exploded views along the rocket's axis, rocket horizontal with the nose to the left (in step drawings) or pointing up and right at 45° (on covers and packaging). No perspective, no shading, no gradients. Renders from the generator should be traced or styled to these weights (Night outlines, Paper-white fill).
- **Part letters:** every part gets a capital letter (A nose cone, B body tube, C fin can, D motor block …; repeated small parts get D1, D2). Letters sit in a **chamfered Night tag** with Paper Space Grotesk 700 lettering (`.rb-tag` in CSS; in SVG the tag is a 28 × 26 octagon with 6 px corners). A **1 px Night leader** runs from the tag to the part and ends in a **2.5 px dot** on the part. Leaders are straight, horizontal or vertical where possible, and never cross each other.
- **The same letters everywhere:** parts layout, steps, kit contents list and packaging use the same letters for the same parts.
- **Step numbers:** chamfered orange tag with a Night number (`.rb-step`), next to a one-line instruction heading.
- **Zoom callouts:** a circle (2 px outline) with a magnified detail inside, joined to a small 1 px circle on the main drawing by a 1 px dashed leader.
- **Callout boxes in text:** **Tip** = Sky-100 fill, 4 px Sky left border, Sky-700 label. **Safety** = Red-100 fill, 4 px Red left border, Red-700 label. **Adult step** = same as Safety with the label "Adult step". One callout of each kind per step at most.
- **Guide page header band:** Night bar with the section name in Space Grotesk 700 and a skill level shown as 1–3 orange chevrons (dimmed chevrons for the rest). A thin fletching band (`patterns/fletching-band-*.svg`) can sit under it on covers only.
- **Supply icons:** same 2 px line style, 32 × 32 grid, Night only (orange only for the thing being used up, like glue).

## Voice and tone

Write like a helpful older cousin at a launch field: friendly, sure of the facts, never in a hurry.

- **Short sentences.** One idea each. Aim for a grade 3–5 reading level in the Beginner app text and guides; the curriculum can stretch for grades 5–8.
- **Say what to do,** then why, in that order: "Move the fins back a little. That pulls the push point behind the balance point."
- **Plain words first, the real term second:** "balance point (CG)", "push point (CP)", "stability (calibers)". Teach the real words; don't hide them.
- **Talk to the builder:** "your rocket", "you". Use "we" for Quiver ("We tested this with a C6-5").
- **Safety without fear.** Calm, specific, and the same every time. Say who does it and how: "An adult puts the motor in." "Stand back 5 m. Count down from 5." No skulls, no "DANGER!!!", no scary stories. Follow the NAR safety code and say so.
- **Celebrate, briefly.** "Your rocket will fly straight." is better than "Awesome!!! 🚀". No exclamation marks in instructions; one is fine on a launch-day page.
- **Numbers with units,** always, in metric (the app is in mm), with the motor code as written: `C6-5`, `24 mm`, `1.8 cal`.
- Don't say "simply", "just" or "easy". If it were easy, nobody would need the guide.

## How to apply this to the app (suggestions, nothing changed yet)

The app's colours are already tokens with the same names, so most of this is swapping values. In order of effort:

1. **Tokens.** Link the fonts and `tokens.css`, or copy its *Theme mappings* block over the `:root` blocks in `server/static/index.html`. `--bg --panel --card --ink --muted --line --rowline --field --accent --accent-ink --ok --warn --err --errbg --errline --view-top --view-bot --chip` have direct replacements; new ones are `--cta`/`--cta-ink` (launch orange), `--cg`/`--cp` (the stability dots), `--okbg`, `--warnbg` and `--grid`. Point the existing CG/CP colours at `--cg`/`--cp`: the CG is already `#3d8bfd`, but the CP is `#ff5a5a` today (`CP_COLOR` in the 3D view and inline `style="color:#ff5a5a"` in the guide text), and the stability bar's greens are `#30a46c`/`#7cc68f`; switch them to Signal red `#E5484D` and Go green `#2FB67C` / `--rb-green-300`. Update the two `<meta name="theme-color">` tags to `#FFFDF8` / `#12203A`.
2. **Fonts.** Body stays 14 px but switches to Inter; `header h1`, `legend`, the stability score and all numbers switch to Space Grotesk (`legend` already is uppercase and tracked, so it becomes the `.rb-label` style).
3. **Header.** Replace the `<h1>` text with the mark (`rb-mark-light.svg` / `-dark.svg`, 28 px) plus "Rocket Builder" in Space Grotesk 700, and change "← Quiver Design Works" to "by Quiver Design Works ↗" in Grey. Keep the Rocket/Trebuchet switch as is (Night pill for the current one). Optionally a 3 px fletching band along the bottom edge of the header instead of the 1 px line.
4. **Buttons.** `#build` becomes the one orange button (`--cta` with `--cta-ink` text, 10 px radius, a slight inset bottom shadow). Download buttons keep the outline style. Nothing else is orange.
5. **3D view.** Background: `--view-top`/`--view-bot` are Paper tones in light and Night tones in dark; add the blueprint grid (`background-image: var(--grid)`) behind the canvas, or draw the same grid as the scene's ground plane in three.js at 40 mm major / 8 mm minor.
6. **Stability readout.** Show it as the brand sheet does: a horizontal tube with the blue balance-point dot in front of the red push-point dot, a bracket showing the calibers between them, and a green "Stable" pill.
7. **Favicon.** `<link rel="icon" href="rb-favicon.svg" type="image/svg+xml">`, `rb-favicon-32.png` as fallback, `rb-apple-touch-icon-180.png` as the touch icon.
8. **Tutorial and help.** Step numbers in the quick start use `.rb-step`; Tip/Safety callouts use the guide styles above so the app and printed guide feel like one product.

Everything is free: Google Fonts (OFL), hand-written SVG, plain CSS. No new services or running costs.
