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
11. *(2026-10-14)* Which overall heights build is decided entirely by the plan checks (`plan_rocket`: segment split, aft segment vs fin root and motor bay socket, forward lug, nose vs printer), so `height_ranges` can answer without OpenCascade. Real builds at every segment-count transition (M13–M29, printers 150/200/250 mm, ±1 mm) all succeeded; the only failing heights are below the minimum. Near that minimum, auto-sized fins trail further below the tail, so the corrected body length can drop the aft segment under the socket limit (M29 at 276 mm: fins grew 2.5x and the fallback build came out 311 mm). So the website's ranges require a height to plan at fin scale 1 **and** at `MAX_FIN_SCALE`; the checks only get stricter as fins grow.

## Deliberate differences from the FeatureScript (owner's requests, 2026-10-09)

- **Nose insert 30% shorter:** `Derived.nose_shoulder_len = max(0.7 x shoulder_len, 7 mm)` for the nose only; body-to-body joints keep the full shoulder. The anchor section's length (`sec_len`) and the nose placement use it; overall length is unaffected (the tip is still nose_len above the body top).
- **Shock-cord strap rotated 90 degrees and simplified:** a straight bar across the bore (a chord from wall to wall), standing off the wall at its middle by the cord gap (2.5 mm at first; 3.6 mm since 2026-10-18, below), so the cord drops in from the open top behind the bar (the FeatureScript's bar runs vertically with the cord threaded sideways). Seen from the axis its underside is a 45-degree pointed arch springing from the wall at both ends, where the bar thins to nothing against the curved wall, with 2 mm of bar above the apex and the apex rounded (1.5 mm, `APEX_FILLET`, a ~2 mm bridge) so it is not a stress riser: it prints upright without supports (`test_anchor_strap_prints_without_supports`). Bar 2 mm thick; ends run half a wall into the wall.
- **Shock-cord clearances sized for elastic (2026-10-18, owner: "Kevlar likely won't ever be an option"):** `params.SHOCK_CORDS` holds the cord per motor size: flat braided elastic 1/8 in (3.2 mm) x ~1 mm on M13/M18 and 1/4 in (6.4 mm) x ~1.2 mm on M24/M29, and round 1/8 in (~3.2 mm) at every size. `shock_cord(mtr_d)["pass_d"]` = max(round cord, flat cord doubled back) + 0.4 mm print margin = **3.6 mm** at every size. Used for:
  - the **anchor strap's slot** (bar to wall, at the middle): 2.5 -> 3.6 mm. Slot across: M13 11.9, M18 14.6, M24 17.3, M29 19.3 mm (was 10.4-16.4). The bar moves 1.1 mm toward the axis, so the open bore in front of it (for the parachute) drops to 58 % of the bore on M13 (was 66 %), 70 % M18, 77 % M24, 81 % M29; the strap's arch is a little longer, and the anchor section 0.2-1.0 mm taller.
  - the **nose tie bar's recess** (`body.nose_recess`): opening radius >= bar/2 + pass_d (4.6 mm), dome >= bar + pass_d (5.6 mm), so the cord goes up beside the 2 x 2 mm bar and over it. Before, M13 had 0.7 mm over the bar and M18 2.7 mm: no elastic would go round. M13 and M18 change (M13 nose +0.08 g); M24/M29 already had room. On M13 the dome's outside now reaches past mid-wall, so the cap runs up the shoulder wall and fuses into it instead of stopping at a flat ring; the dome height steps up 0.1 mm at a time when its outside would graze the wall (a near-tangent union). A thick wall on a small motor (M13 at 3 mm) leaves too narrow a shoulder: the recess gets the widest opening it can hold (2.2 mm beside the bar) and the build notes say to use flat cord.
  - Tests: `test_anchor_strap_fits_the_shock_cord` (slot depth and width for each cord, >= 55 % of the bore open), `test_nose_tie_bar_has_room_for_the_cord` (a 3 mm cord bent round the bar clears the nose; the nose is one valid solid; shoulder slices keep the plain wall). The old M13 and M18 noses fail the cord probe (45 and 8 mm3 of overlap).
- **Launch lug bore 4.0 mm on a 1/8 in rod (2026-10-18, owner: printed lugs fit "a little too snug"):** `lugs.LUG_BORE_CLEARANCE` = 0.4125 mm radial (was 0.3 mm, a 3.775 mm bore). Other rods get the same clearance per side (6.35 mm rod -> 7.175 mm bore). Knock-on: the ring and the stem's ring flare grow 0.11 mm in radius, `center_r` would move out 0.11 mm where the ring sets it (it doesn't at minimum diameter: the motor cap sets it on M13-M29, so the rod line is unchanged there), and the forward lug's 45-degree ramp is 0.23 mm taller. The cap clearance is unchanged (it is set by the rod or the standoff, not the bore), and so is the rod standoff clip (`standoff_ri` = rod radius - fit_press, snug on purpose). Test: `test_lug_bore_is_4mm_for_eighth_inch_rod` (a 3.98 mm probe passes through both lugs of the built aft, a 4.1 mm one doesn't).

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
- **Slimmer motor cap (2026-10-19, owner's 2026-10-16 request, ported from `claude/epic-einstein-4im4l4`):** cap wall 1.2 mm (three 0.4 mm perimeters, was the FeatureScript's 1.6) and grip ribs 0.4 mm proud (was 0.6). The cap is 0.8 mm smaller across and 1.2 mm less across the ribs; swept fins let it sit higher (hang 12.76, was 13.41), and the launch rod line moves in where the cap sets it.
- **Motor cap lip 1.75 mm (2026-10-19, owner: the hole still looked small; an 18 mm casing wall is about 2.5 mm, lip should be 1.5-2 mm):** `CAP_LIP` 1.75, nozzle hole = motor diameter - 3.5 mm (M13 9.5, M18 14.5, M24 20.5, M29 25.5). Was:
- **Motor cap lip 2.5 mm (2026-10-18):** `params.CAP_LIP`: the cap's floor reaches 2.5 mm in from the motor's OD, covering the cardboard casing (owner, from printed tests). The FeatureScript's 1/8 in lip left too small a nozzle hole. Test `test_motor_cap_lip_covers_the_casing`. (The unmerged `claude/epic-einstein-4im4l4` branch tried a casing-wall-only lip of about 1 mm and a slimmer cap; not taken.)
- **Printed joint fits (2026-10-18, owner: first M13 and M18 kit prints "way too tight"):** the settings CSV's `fit_slip` 0.02 mm is a CAD value; printed shoulders came out far too tight. `params.web_fits()` now sets the defaults from the fit-test coupons (Bambu P1S, PLA, 2026-10-15/16, ported from the `claude/epic-einstein-4im4l4` branch): body joints 0.18 mm radial (0.15 a little snug, 0.20 a little loose on M18-M29), nose 0.15. Short nose shoulders (under `SHORT_NOSE_SHOULDER` = 8 mm, i.e. M13) grip harder per mm: joint 0.16, nose 0.14 (0.12 too tight, 0.15 too loose). The nose has its own clearance (`DesignParams.nose_clearance`, `Derived.fit_nose / nose_shoulder_od / nose_joint_rise`), and every shoulder's bed edge has a 0.5 mm 45-degree chamfer (`shoulder_chamfer`, `body.shoulder_foot`) for elephant's foot. `GENERATOR_VERSION` 0.2.0. Tests `test_printed_fit_defaults`, `test_shoulder_chamfer`. `fit_slip` in the CSV is no longer read.
