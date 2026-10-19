# Rockets and Model Rocketry: free lessons for grades 3–8

_Two tracks built on Washington's K–12 Science Learning Standards. Goes with **Rocket Builder by Quiver Design Works** (https://rocket.quiverdesignworks.net), a free web app for designing 3D-printable model rockets. On the web at rocket.quiverdesignworks.net/learn._

## Pick a track

| | **Elementary, grades 3–5** | **Middle school, grades 6–8** |
|---|---|---|
| Lessons | 8 lessons, about 45 minutes each | 9 lessons, about 55–60 minutes each, plus a launch day |
| Rockets students fly | Balloon, straw and stomp rockets (paper and air only) | Paper rockets in class, then a 3D-printed rocket on a real motor, **launched by an adult** |
| Rocket Builder | A class tool on a projector or tablets, Beginner mode, on screen only | Beginner, then Advanced; download and print (12+) |
| 3D-printed rocket | Optional instructor demo | Designed, printed, built and flown |
| Big ideas | Pushes and pulls, gravity, patterns, fins, fair tests, parachutes, speed and energy | Newton's laws, net force and mass, stability, drag, impulse and energy, design with a model, kinetic energy, measuring height |
| Standards | 3-PS2-1, 3-PS2-2, 4-PS3-1, 5-PS2-1, 3-5-ETS1-1 to 3 | MS-PS2-1, MS-PS2-2, MS-PS2-4, MS-PS3-1, MS-PS3-2, MS-PS3-5, MS-ETS1-1 to 4 |

> **Model rocket motors and Rocket Builder kits are rated 12+.** Under 12, students fly paper and air rockets only and use Rocket Builder on screen. In the middle-school track, **adults handle all rocket motors and igniters**, every time, following the NAR Model Rocket Safety Code.

**Mixed ages or home school?** Run the elementary lessons together, and give older students the middle-school worksheets and the printed rocket. Each track has its own safety page.

## Files

| File | What it is |
|---|---|
| `README.md` | This page (the source of the /learn chooser) |
| `standards.md` | For parents and teachers: the Washington standards, the full PE text, WA Science 2026 codes, math and ELA crosswalks, sources and further resources (/learn/teachers) |
| `elementary/README.md`, `middle/README.md` | Each track's overview: lessons at a glance, the standards map (lesson × PE, SEP, CCC), materials, Rocket Builder use |
| `elementary/lesson-01.md` … `lesson-08.md`, `middle/lesson-01.md` … `lesson-09.md` | One lesson plan each: standards, "I can…" objectives, words, materials, steps, a check for understanding with answers, and teacher notes |
| `elementary/safety.md`, `middle/safety.md` | Paper-rocket safety; the NAR code summary and launch day rules |
| `elementary/worksheets.html`, `middle/worksheets.html` | Printable worksheets (US Letter). Built by `tools/gen_ws.py` |
| `tools/gen_ws.py` | Builds the worksheets: `python3 docs/curriculum/tools/gen_ws.py elementary docs/curriculum/elementary/worksheets.html` (and `middle`) |
| `tools/build_site.py` | Builds the web pages in `server/static/learn/` from these files, and runs `gen_ws.py` for both tracks. `pip install markdown`, then `python3 docs/curriculum/tools/build_site.py --pdf` from the repo root (`--pdf` also renders `server/static/learn/elementary/worksheets.pdf` and `…/middle/worksheets.pdf` with Playwright: needs node, the `playwright` package on `NODE_PATH` and `PLAYWRIGHT_BROWSERS_PATH`). Commit the generated files. |
| `tools/worksheets_pdf.js` | The Playwright step behind `--pdf` |

## Web addresses

`/learn/` (chooser) · `/learn/teachers` · `/learn/elementary/` and `/learn/elementary/lesson-01` … `lesson-08`, `safety`, `worksheets`, `worksheets.pdf` · `/learn/middle/` and `/learn/middle/lesson-01` … `lesson-09`, `safety`, `worksheets`, `worksheets.pdf`. The old 10-day unit's addresses redirect to the middle-school track: `/learn/day-01` … `day-08` → `lesson-01` … `lesson-08`, `day-09` → `lesson-08`, `day-10` → `lesson-09`; `/learn/safety` and `/learn/worksheets(.pdf)` → the middle-school pages.

## History

- 2026-10-19: restructured into an elementary and a middle-school track around the Washington standards (owner's request), replacing the 2026-10-18 10-day unit for grades 3–8. The middle-school track is that unit, simplified and tightened from 10 days to 9 lessons.
