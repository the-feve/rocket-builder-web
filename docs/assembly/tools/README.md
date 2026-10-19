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
  (anchor strap position and slot, nose tie bar, motor bay, thread, launch-lug line) and each part's
  **fillet edges** (`fillet_edges()`: the tangent edges where a fillet meets the body or fin, found in
  the B-rep: two faces meeting tangentially where one bulges out past the shared tangent plane, so
  convex roundings, split faces and bores are left out; edges under 4 mm are skipped). STL output
  is untouched.
- `render.html` + `scenes.js`: three.js (the app's vendored copy, `server/static/vendor/three/`) in
  headless Chromium. Line-art look: flat brand fills, outlines found from normal, depth and
  object-id edges in a post pass, 2x supersampled. Section views use clipping planes; the cut
  faces show as flat Night-100. The things that aren't printed (shock cord, knots, parachute,
  wadding, motor, igniter, plug, launch rod, blast plate, arrows) are simple added geometry.
- **Dashed lines** (`addDashes` in `scenes.js`): smooth fillets have no outline, so their tangent
  edges are drawn dashed on every render that shows the part (the fin-root fillets on D, the lug
  fillets). Dashes are thin tubes cut to a screen-space pattern (so they look the same in every
  view), lifted just off the surface and depth-tested, in the colour pass only; lines too short for
  two dashes are dropped. `dashed(polylines)` in `scene_defs.js` draws other dashed lines the same
  way (the parachute fold lines).
- **Cord** (`rope()`): a smooth Catmull-Rom tube of constant radius with a braid pattern and flat cut
  ends; knots are drawn as two snug turns round the long part (`wraps()`), as tied in steps 4 and 5.
  `strapRig`, `noseRig` and `larks` (the parachute's lark's head on the cord just under the nose knot)
  are shared by steps 4–6, the overview and the packing drawing.
- `scene_defs.js`: one entry per drawing (camera, which parts, how far each is pulled apart, and
  the labelled points). Labels are not baked into the PNGs: `render.mjs` writes each scene's
  points to `images/callouts.js`, and the guide draws the part tags over the images with
  SVG (so the text stays sharp and in Space Grotesk). Each `<figure data-img data-tags>` in the
  guide picks the points and the tag offsets.
- Style follows `docs/brand/brand.md` (Illustration style): Paper-white fills, Night outlines, no
  shading, nose to the left in step drawings, Night shock cord, orange canopy and motion arrows.

Drawings are not to scale unless they say so: the overview (`recovery`) shortens the cord with a
break mark, and in `chute_fold` only picture 4 (roll next to B) is real size. The parachute is
hitched to the cord, not the tie bar, in the drawings (an 18 mm rocket): the M13/M18 tie-bar recess
leaves room for one cord pass only (`body.nose_recess`); 24 mm and up have room for both.

To check a render by eye, composite it onto paper (the PNGs are transparent): the page previews
from `make_pdf.mjs --png` do this.
