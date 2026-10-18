# Assembly guide: drawings and PDF

The drawings in `../images/` are rendered from the rocket generator itself, so they can be
regenerated when the geometry changes. Three steps, from the repo root:

```
pip install -e geometry trimesh               # once: rocketgen (build123d/OpenCascade) + GLB export
python docs/assembly/tools/build_meshes.py    # builds the example rockets -> tools/.build/{m18,m24}.glb + .json (~20 s)
node docs/assembly/tools/render.mjs           # renders every scene -> images/*.png + images/callouts.js
node docs/assembly/tools/make_pdf.mjs         # prints assembly-guide.html -> assembly-guide.pdf
```

`render.mjs name1 name2` renders only those scenes; `make_pdf.mjs --png <dir>` also saves one PNG
per page for checking the layout. Both use Playwright with the pre-installed Chromium
(`/opt/pw-browsers/chromium`, or set `CHROMIUM`); never run `playwright install`.

## How it works

- `build_meshes.py`: the example rockets (`ROCKETS`: the Beginner default M18 with trapezoid fins,
  and an M24 at 480 mm with two body sections) are built with `rocketgen.stability.build_stable`.
  Each part goes into a GLB in its assembled position (named as in the app: `Aft`, `Seg_2`,
  `Anchor_Seg`, `Nose`, `Motor_Cap`, `Rod_Standoff`), plus a JSON of the dimensions the drawings need
  (anchor strap position and slot, nose tie bar, motor bay, thread, launch-lug line).
- `render.html` + `scenes.js`: three.js (the app's vendored copy, `server/static/vendor/three/`) in
  headless Chromium. Line-art look: flat brand fills, outlines found from normal, depth and
  object-id edges in a post pass, 2x supersampled. Section views use clipping planes; the cut
  faces show as flat Night-100. The things that aren't printed (shock cord, knots, parachute,
  wadding, motor, igniter, plug, launch rod, blast plate, arrows) are simple added geometry.
- `scene_defs.js`: one entry per drawing (camera, which parts, how far each is pulled apart, and
  the labelled points). Labels are not baked into the PNGs: `render.mjs` writes each scene's
  points to `images/callouts.js`, and the guide draws the part tags over the images with
  SVG (so the text stays sharp and in Space Grotesk). Each `<figure data-img data-tags>` in the
  guide picks the points and the tag offsets.
- Style follows `docs/brand/brand.md` (Illustration style): Paper-white fills, Night outlines, no
  shading, nose to the left in step drawings, Night shock cord, orange canopy and motion arrows.

Drawings are not to scale (the parachute, cord and wadding are drawn small).
