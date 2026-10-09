# Geometry port report (Phase 0 spike + Phase 1)

_2026-10-08. Ported from `src/RocketGenerator.fs` on the `anchor-section` branch of OS_Rocket_Builder (spec: `docs/web_platform_spec.md` §6, §9)._

## Phase 1 status (feature parity)

Every feature of the FeatureScript is now ported. Two exceptions, both cosmetic:
- the leading-edge root fillet (left for later, owner's call 2026-10-08);
- some lug rounds, below.

| Feature | Result |
|---|---|
| Launch lugs: Two / Aft only / None; rod line pushed out to clear the motor cap | Works. The forward lug is placed by fraction of the body and moved onto one part (on `Seg_2` for long bodies). |
| Forward lug 45° underside | Works |
| Lug rounds | **Partly.** Rounded on the lug block alone, before the union: top edges 0.6 mm (1 mm won't build), forward underside 1 mm. Not built: the concave edges where the lug meets the body, and the 3 mm underside-to-body fillet. On the merged part OpenCascade failed these at every radius tried (0.25 to 3 mm). |
| Rod standoff (C-clip, reaches pad clearance below the lowest point) | Works, as a separate part `Rod_Standoff` |
| Anchor strap inside the anchor section (bar, cord gap, 4 rounded bends, 0.6 mm side round) | Works; every round builds |

Pictures: `report/lug_aft.png`, `report/lug_fwd.png`, `report/anchor.png`.

Phase 1 OpenCascade findings, added to the list below as items 7 to 9.

## Phase 3: stability (`stability.py`)

Not in the FeatureScript. CP: Barrowman, nose X = L − V/A_base (exact for every profile; the tangent-parabola "parabolic" nose is 0.467 L, not the 0.5 L in the usual table), fins as a trapezoid (tip radius and the hanging-tip flat ignored). CG: part centroids, the motor resting on the cap's face, recovery one caliber under the nose shoulder; the rod standoff is left out (it stays on the pad). Motor masses in `data/web_motor_masses.csv` are the heaviest common motor per size, rounded up, and approximate.

Margins at the defaults (clipped delta, 3 fins, 250 mm, loaded heaviest motor): M13 2.7, M18 1.07, M24 0.32, M24L 0.26, M29 −0.02; M18 swept 0.84, rectangular 0.10, 4 fins 1.13. The printed parts are solid PLA and the aft segment carries most of the mass, so the bigger motors at minimum diameter need custom (larger) fins or a lighter motor. Not yet compared against OpenRocket: worth doing for two or three designs.

Auto-size (`build_stable`): scaling the whole fin made things worse (a longer root grows the fin forward from the tail and moves the CP forward: M24 went from 0.32 to 0.02 cal at 2.5x), so only span and sweep are scaled. The scale comes from a prediction (CP of the scaled fins, CG with the blades' planform mass swapped) aimed at 1.15 cal, then one rebuild. Results with the heaviest motor: M24 1.48x → 1.13 cal, M24L 1.52x, M29 1.91x, rectangular M18 1.37x, swept M18 1.10x; M18 clipped delta and M13 unchanged. Rectangular fins on M29 hit the 2.5x limit at 0.76 cal (no sweep to grow) and are reported unstable.

# Phase 0 (spike)

## Verdict

**build123d / OpenCascade can do this job. Recommend going on to Phase 1 with it**, with one open item (the leading-edge root fillet, below).

| Feature | Result |
|---|---|
| Body segments (8° inner taper, 45° joint chamfers, socket countersink) | Works. Volume matches the Pappus hand calculation to 1e-6. |
| Nose (all 5 profiles), shoulder cap with spherical recess, tie bar | Works |
| Aft: solid-first build, fins, cavity cut last | Works, same build order as the FeatureScript |
| Fin **tip** corner fillet (6.5 mm) | Works |
| Fin **root** fillet (3.5 mm, the two long side edges) | Works on all 5 fin shapes and 3/4/5 fins. On Swept/Delta it runs down to the trailing edge below the tail, then the tube extension is trimmed at exactly the OD with no fallback needed (same trick as Onshape). |
| **Leading-edge** root fillet (1 mm) | **Not built.** Left sharp with a note, the same non-fatal path the FeatureScript has. See "Open item". |
| Threaded boss + cap (helix sweep, 45° lead-in, 60° chamfers, grip ribs) | Works. Swept ridge volume matches Pappus to 0.1 %. Cap and boss don't touch (intersection volume < 0.01 mm³) and engage the full 3 turns. |
| Inner motor mount (larger body OD): mount tube, 45° bulkhead, floor, ribs | Works |
| Segmentation + anchor section length | Works (anchor strap itself not ported, see "Not ported") |
| Mass estimate | Works (volume × material density, as `reportMass`) |

Build time: about **2.5 s per rocket** (M18, 4 parts) on this container, plus about 5 s to write STLs. That's fine for "click → preview" with a short spinner; caching by parameters (spec §4) covers repeats.

Configurations built, all as valid single solids per part:
- M18 at minimum diameter: all 5 fin shapes; 3, 4 and 5 fins; all 5 noses; body length 250 and 400 (an extra `Seg_2`).
- M13, M24, M24L and M29 at minimum diameter.
- M18 at a 33.7 mm OD and M24 at 41.6 mm OD, both with the inner mount.

Masses (PLA, solid, Phase 0 parts only): M18 Clipped delta 43.5 g, M18 Swept 44.3 g, M18 at 33.7 mm OD 89.3 g.

## Pictures

Rendered by `rocketgen` itself (`--png`). Section views cut on the plane y = 0.

- `report/m18_clipped_delta/`: the default rocket. `assembled.png`, `section.png` (whole rocket, half section), `aft_section.png` (motor bay, engine stop, thread), `aft_closeup.png` (from below).
- `report/m18_swept/`: fins hanging below the tail; the root fillet runs to the trailing edge.
- `report/m18_trapezoid_od33.7/`: larger body with the inner motor mount, bulkhead, floor and rib.

Sample STLs (print orientation, one per part, plus `assembled.stl`): `examples/m18_clipped_delta/`.

## Things OpenCascade does differently from Onshape (would go in the FeatureScript reference notes, web section)

1. **A concave fillet can come back "valid" but wrong.** One fillet over both the side and leading-edge root edges reported success and passed `is_valid`, but had a whole 3 mm slice of the tube missing. Every fillet in the aft is now checked: the volume must grow, and slices through the fin root must keep at least the solid tube's area (`fillet_checked`). The tests also slice the finished aft every 2.5 mm.
2. **Thread ridge corner on the base cylinder.** With the ridge profile's flank corner exactly on the boss surface, the swept edge lies *on* that cylinder and the union fails (Null shape). Fix: the 45° flanks run on 0.1 mm into the base. The ridge outside the boss is unchanged.
3. **Coincident cones.** The grip ribs' trimming cones exactly matched the cap's chamfer cones, and the union returned an invalid solid. Fix: the trimming cones sit 0.01 mm inside the cap.
4. **Helix sweeps need Frenet framing** (`is_frenet=True`) to keep the profile in the axial plane.
5. `Shape.intersect` returns a list in build123d 0.13; `geom.as_shape` collapses it.
6. The OD cylinder is split at its seam (angle 0), so fin 0's root edges come in two pieces. Harmless, but edge counts differ from Onshape.
7. **Tessellate before trusting `is_valid`.** A lug round passed `is_valid`, then failed it once its faces had been meshed, and the STL export broke on that face. `try_fillet` now meshes first, then checks validity, and `build_rocket` refuses to return an unsound part.
8. **No booleans after a cosmetic fillet on the same part.** A union after a lug round produced an invalid solid. Lugs are now rounded on their own block before the union.
9. `Face.radius` can be `None` on a cylinder; `is_cylinder_r` asks OpenCascade (`BRepAdaptor_Surface`) instead.

10. *(2026-10-09)* A cut face lying exactly on the bore cylinder (the strap's cord channel, first drawn to radius ri) made the union with the body segment an unsound solid, but only where the bore is straight (with the strap shifted up out of the inner taper). Reach 0.05 mm into the wall instead. Both pieces were valid alone.

## Deliberate differences from the FeatureScript (owner's requests, 2026-10-09)

- **Nose insert 30% shorter:** `Derived.nose_shoulder_len = max(0.7 x shoulder_len, 7 mm)` for the nose only; body-to-body joints keep the full shoulder. The anchor section's length (`sec_len`) and the nose placement use it; overall length is unaffected (the tip is still nose_len above the body top).
- **Shock-cord strap rotated 90 degrees and simplified:** a straight bar across the bore (a chord from wall to wall), standing 2.5 mm off the wall at its middle, so the cord drops in from the open top behind the bar (the FeatureScript's bar runs vertically with the cord threaded sideways). Seen from the axis its underside is a 45-degree pointed arch springing from the wall at both ends, where the bar thins to nothing against the curved wall, with 2 mm of bar above the apex: it prints upright without supports (`test_anchor_strap_prints_without_supports`). Bar 2 mm thick; cord gap 10-16 mm across (M13-M29); ends run half a wall into the wall.

## Open item: leading-edge root fillet

After the main root fillet, the fin's sloping leading face caps the fillet ends. Its edge with the tube becomes a chain of split pieces (10 edges for 3 fins). Tried:
- sequential, as in the FeatureScript: fails at 0.2 to 1 mm;
- after `clean()`: fails;
- leading edge first, then the side fillet: the side fillet fails;
- both in one fillet call with per-edge radii: "succeeds" but drops slices (item 1 above);
- one radius on all three: same.

Options for Phase 1:
- (a) Build that corner blend directly: sweep a concave fillet profile along the leading-face/tube curve and union it.
- (b) Round the fin's leading root corner in the fin planform before the union, then run the side fillet only.
- (c) Accept a sharp leading corner on the web version.

(a) is closest to the Onshape result. Owner's call on whether it matters enough.

## Not done yet

- STEP export and per-part colours as file properties: Phase 2, with the web preview (GLB).
- Golden tests against Onshape exports (spec §5.2).

## Data notes

- `data/derived_printed_dimensions.csv` only matches on `bay_id`. Its `body_od`/`body_id` assume the old 1.2 mm wall (now 1.5 mm), its `shoulder_len` predates the "−4 mm" change, and `bay_len` predates the threaded cap (the motor hang-out now comes from 3 thread turns). The tests check `bay_id` against the CSV and the rest against the current formulas by hand. The CSV should be regenerated, or dropped in favour of `rocketgen` output.
- The motor and settings libraries are read from `data/*.csv`, so this repo stays the one source.

## Not checked against Onshape yet

Nothing is compared with Onshape exports yet (spec §5.2 golden tests). That needs the owner to export STLs and the mass line for the listed configurations.
