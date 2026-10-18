# Kit test prints

Print-ready files for the three kits proposed in `../README.md` (Kit designs), to print, weigh and fly-test before any kit is sold. Each is the kit's fixed Beginner design (printer max height 256 mm, 3 trapezoid fins, tangent-ogive nose, PLA, auto-sized fins), built with the **4.0 mm launch lug bore** (1/8 in rod) and the elastic shock-cord clearances (`geometry/rocketgen/params.py`, `SHOCK_CORDS`), on 2026-10-18.

| Kit | Folder | Motor | Height | Printed mass (solid) | Stability | Recommended motor (app) | Other motors that pass | Chute | Tallest part |
|---|---|---|---|---|---|---|---|---|---|
| Starter | [`starter-m18/`](starter-m18/README.md) | M18 | 300 mm | 44.0 g | 1.15 cal | B6-4, 143 m | B4-6, C5-3, C6-7 | 12 in | 204 mm (D) |
| Big | [`big-m24/`](big-m24/README.md) | M24 | 360 mm | 70.7 g | 1.14 cal | C11-5, 199 m | D12-7 | 15 in | 241 mm (D) |
| Mini | [`mini-m13/`](mini-m13/README.md) | M13 | 190 mm | 23.4 g | 1.14 cal | A10-3, 113 m | none | 12 in or streamer | 113 mm (D) |

Stability is the margin with the heaviest motor of the size and the default recovery allowance. All three match the kit README's numbers to within 0.1 g and 2 m; nothing had to be adjusted.

Each folder has:

- one STL per printed part, lettered as in the assembly guide (`docs/assembly/`): `A_nose`, `B_anchor_section`, `D_fin_can`, `E_motor_cap`, `F_rod_standoff` (C, a middle body section, isn't in these designs). Each rests on z = 0 in its print orientation.
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
