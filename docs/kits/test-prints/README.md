# Kit test prints

> **2026-10-19 (round 3):** the shock-cord strap is now inside the top of the body tube; the separate anchor section is gone. Reprint everything. Starter and Mini are now one body print (the fin can D, with the strap in its top); Big is the fin can D plus the top body section B (the old anchor section's length, renamed). Each kit README has the details.
>
> **2026-10-18:** the motor cap (E) now has a 2.5 mm retention lip over the motor's cardboard casing, so the nozzle hole is the motor diameter less 5 mm (it was less 6.35 mm). Reprint **E** only: the lighter cap moved the other parts by about 0.02 mm, too little to matter.

Print-ready files for the three kits proposed in `../README.md` (Kit designs), to print, weigh and fly-test before any kit is sold. Each is the kit's fixed Beginner design (printer max height 256 mm, 3 trapezoid fins, tangent-ogive nose, PLA, auto-sized fins), built with the **4.0 mm launch lug bore** (1/8 in rod) and the elastic shock-cord clearances (`geometry/rocketgen/params.py`, `SHOCK_CORDS`); regenerated 2026-10-19 (round 3: the cord strap in the top body piece).

| Kit | Folder | Motor | Height | Printed mass (solid) | Stability | Recommended motor (app) | Other motors that pass | Chute | Tallest part |
|---|---|---|---|---|---|---|---|---|---|
| Starter | [`starter-m18/`](starter-m18/README.md) | M18 | 300 mm | 41.9 g | 1.15 cal | B6-4, 149 m | B4-4, C5-3, C6-5 | 12 in | 234 mm (D) |
| Big | [`big-m24/`](big-m24/README.md) | M24 | 360 mm | 69.7 g | 1.15 cal | C11-5, 201 m | D12-5 | 15 in | 240 mm (D) |
| Mini | [`mini-m13/`](mini-m13/README.md) | M13 | 190 mm | 21.9 g | 1.14 cal | A3-4, 141 m | A10-3 | 12 in or streamer | 139 mm (D) |

Stability is the margin with the heaviest motor of the size and the default recovery allowance. Nothing had to be adjusted. The kit README's table (`../README.md`, Kit designs) predates round 3: Starter is now 1.6 g lighter (one joint fewer; the auto-sized fins grew a little, scale 1.20, as the weight moved aft), Mini 1.0 g lighter (and an A3-4 now flies it best), Big unchanged.

Each folder has:

- one STL per printed part, lettered as in the assembly guide (`docs/assembly/`): `A_nose`, `B_top_body_section` (Big only: the top body piece, with the cord strap), `D_fin_can` (on Starter and Mini the whole body tube, with the cord strap in its top), `E_motor_cap`, `F_rod_standoff` (C, a middle body section, isn't in these designs). Each rests on z = 0 in its print orientation.
- `<kit>-rocket.zip`: the app's own Download (the same STLs under the app's part names, plus `build_notes.txt`, `design.json` and the licence).
- `design.json`: the design in the app's saved-design format; load it with **Open file** in the app.
- `README.md`: parameters, parts (print height and solid mass), print settings, motors, parachute, shock cord and assembly order.
- `preview.png`: the parts laid out.

## Regenerating

After any geometry change, from the repo root:

```
pip install -e geometry -r server/requirements.txt matplotlib   # once (matplotlib only for the previews)
python docs/kits/test-prints/tools/make_test_prints.py           # all three, ~1 min with previews
python docs/kits/test-prints/tools/make_test_prints.py --no-preview starter-m18
```

The script drives the server's own endpoints in-process (FastAPI `TestClient`: `/api/heights`, `/api/build`, `/api/builds/{id}/rocket.zip`), so the files match what the app gives for the same design. It stops if a height isn't one the app allows, a build fails, the rocket is unstable or a part is taller than the printer. The kit definitions are `KITS` at the top of the script.
