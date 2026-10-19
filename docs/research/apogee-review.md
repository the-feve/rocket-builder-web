# Apogee Components review: suggested changes for Rocket Builder

_2026-10-19. Sources: Apogee how-to pages, Peak of Flight (PoF) newsletters and videos, checked against our code, assembly guide and kit docs. Apogee writes for paper-tube kits; this report applies their advice only where it carries over to printed parts._

## 1. Recommended changes, ranked

**1. Round the ejection delay down, not to the nearest.** *Safety. Effort: small.*
- Apogee: between two delays, beginners round down. Beginners' rockets fly less straight and reach apogee early; late ejection is the dangerous case ([PoF #520](https://www.apogeerockets.com/education/downloads/Newsletter520.pdf)). Late ejections also overload elastic cords ([#348](https://www.apogeerockets.com/education/downloads/Newsletter348.pdf)). Apogee also limits deployment speed to 50 mph, about 22 m/s ([#625](https://www.apogeerockets.com/education/downloads/Newsletter625.pdf)).
- Now: `flight.simulate` picks `min(delays, key=abs(d - coast))` from a vertical sim with no wind, and the launch page warns at 25 m/s.
- Change: pick the longest delay that is ≤ the coast time (the shortest delay if none is). Lower the warning to 22 m/s.

**2. Replace the "shake test" for the nose with a measured breakout test.** *Flight success. Effort: small.*
- Apogee: too loose and the nose separates on boost, shredding the chute; too tight and the rocket comes down ballistic. With the rocket nose-down, drop weights in from the tail end until the nose falls out. The target total mass (nose plus weights) is ≈ 74 g × bore area in in² ([#675](https://www.apogeerockets.com/education/downloads/Newsletter675.pdf); BT-20 gives 25–35 g, BT-50 45–60 g).
- Now: "shake gently: the nose should stay on; a gentle pull should take it off."
- Change: our motor tube's ring blocks weights from the tail, so test at step 2, before B is glued. Tie a scrap of cord to the nose's tie bar, push the nose into B, hold B nose-down and hang a zip bag on the cord. Add coins until the nose pulls out; count nose + bag + coins. Print a per-size target in `build_notes.txt` and the guide. Totals for our bores: M13 (13.4 mm) **≈ 14–18 g**, M18 (18.4 mm) **≈ 25–35 g**, M24 (24.4 mm) **≈ 45–60 g**, M29 (29.4 mm) **≈ 70–90 g**. A US nickel is 5.0 g, so the Starter kit (nose 6.4 g) wants about 4–5 nickels. Keep the existing fixes: tape if it is too loose, sand if it is too tight.

**3. Make sure the chute can get past the anchor strap (minimum-diameter bodies).** *Flight success. Effort: small (guide), medium (app check).*
- Apogee: the chute "must fit loosely in its compartment", and too much wadding "could cause a blockage that prevents it from deploying" ([#184](https://www.apogeerockets.com/education/downloads/Newsletter184.pdf)).
- Now: the default bodies are minimum diameter (bore = motor size), and the strap leaves only 58 % of the bore open on M13 (70 % on M18). The Mini kit's bore is 13.4 mm, yet the app still suggests a 12 in chute for it.
- Change:
  - Add a slide-out test to guide step 8: pack the chute, take the nose off, tip the rocket, and everything should slide out past the strap without poking.
  - Make a streamer the default suggestion on M13, and on any build whose bore is under ~16 mm. The kit already ships a streamer.

**4. Shock cord: at least 3× the rocket's length, never under 36 in, and check it every flight.** *Safety. Effort: small.*
- Apogee:
  - Most kits ship cords that are too short. Use elastic three times the rocket's length, and never less than 36 in ([#368](https://www.apogeerockets.com/education/downloads/Newsletter368.pdf)).
  - Elastic singes and ages: tug both ends before every flight ([#591](https://www.apogeerockets.com/education/downloads/Newsletter591.pdf), which also gives 40× diameter for non-stretch cord).
  - Never put CA on a knot: it wicks into the cord and makes it brittle ([#424](https://www.apogeerockets.com/education/downloads/Newsletter424.pdf)).
- Now: the guide says "2–3 times as long". The kits actually ship 3, 4 and 5 ft, which is fine.
- Change:
  - Guide: "at least 3× the rocket's height and at least 36 in (90 cm)".
  - Print the computed length in `build_notes.txt`.
  - Preflight: "tug the cord; replace it if fuzzy, singed or stiff".
  - Step 4/5: "don't glue the knots".

**5. Add a snap swivel to the parachute and to each kit.** *Flight success. Effort: small (≈ $0.05–0.10 a kit).*
- Apogee: "Every parachute needs one of these." Size 14 suits chutes up to 12 in and size 10 suits 18–24 in. A swivel stops line twist, makes swapping a chute quick ([#184](https://www.apogeerockets.com/education/downloads/Newsletter184.pdf), [#368](https://www.apogeerockets.com/education/downloads/Newsletter368.pdf)).
- Now: the guide makes the swivel optional ("or clip on a small snap swivel"), and the kit BOM has none.
- Change: put one in the BOM, tie it to the shroud lines when the chute is made, and show it in step 6. See §2 on where to attach it.

**6. Use Apogee's standard fold.** *Flight success. Effort: small (guide text and a drawing).*
See §2. The guide's fold is close, but it skips the step that wraps the lines inside the canopy and the "fits loosely" check.

**7. Size the wadding to the bore, and add an optional wrap.** *Effort: small.*
- Apogee:
  - Use a loose ball about one body diameter long, below the chute ([Video #469](https://www.apogeerockets.com/Advanced_Construction_videos/Rocketry_Video_469)). Too little melts the chute; too much blocks it (#184).
  - Optional extra protection: wrap a small (~3¼ in) square around the bottom of the rolled chute. A full square can keep the chute from opening ([#424](https://www.apogeerockets.com/education/downloads/Newsletter424.pdf)).
- Now: "3–4 squares (more for wide rockets)".
- Change: "loosely crumpled, filling about 1–2 body widths of tube; never packed hard". Mention the optional small wrap.

**8. Treat the string-swing test as a demo only.** *Effort: small.* Apogee says it "can give wrong answers" ([Rocket Stability](https://www.apogeerockets.com/Tech/Rocket_Stability) → PoF #53). The kit doc's booth demo is fine; nothing should call it proof of safety. The guide's balance-point check is the go/no-go.

## 2. Specific checks

- **Shock cord length and mount.** Length: see #4. Elastic is fine at these sizes if it is inspected (#591). Apogee's own kits use Kevlar (100 lb up to C, 300 lb for D–G) for heat resistance, not because elastic fails. Our strap sits at the top of the body, far from the motor, so the cord misses the hottest gas and there is no Kevlar "zipper" risk.
- **Parachute attachment (the owner's question).** Yes, Apogee does it the owner's way: in Video #469 the chute's apex is passed through the nose cone's eyelet and back through itself (a lark's head), which is easy to replace. But PoF #368 recommends something better: a loop knot in the cord 1/3 of the way down from the nose, with the chute on a snap swivel, because a nose-mounted chute lets the nose "swing in and out of the shroud lines" at ejection. Our guide already uses the 1/3 loop, so keep it and add the swivel (#5). If someone prefers the nose method, lark's-head the chute onto the cord right next to the nose knot, not onto our tie bar: the bar's recess is sized for one cord pass only.
- **Folding and packing (the clear standard method, from #184 and Video #469).**
  1. Lay it flat; pull the lines straight and even.
  2. Fold in half three times, so all lines meet in one bundle and the canopy is a thin wedge.
  3. Lay the lines along the middle third; fold both sides over them.
  4. Zig-zag fold to the bay's length; wrap the lines once or twice, loosely.
  5. Wadding, then chute, then zig-zagged cord. It must slide in and out freely. Store chutes unfolded.
- **Making kit chutes (#368, #184):** knife and straightedge, not scissors; plastic (not paper) reinforcement rings; punched holes; square knots; lines about as long as the chute is wide.
- **Wadding.** See #7.
- **Motor retention.** Fine. Apogee prefers positive retention to hooks: hooks bend, and a motor that comes out at ejection means the chute stays in and the rocket comes down ballistic ([Motor Retention](https://www.apogeerockets.com/How-To/Motor_Retention)). Our screw cap with the 1.75 mm lip is the right answer for minimum-diameter bodies.
- **Launch lugs.** Fine. The 4.0 mm bore matches the standard 1/8 in lug (~5/32 in ID). Two short, spaced lugs lined up with the rod while the glue sets is the usual practice. Lugs add real drag ([launch-lug-drag.pdf](https://www.apogeerockets.com/downloads/PDFs/launch-lug-drag.pdf)), so short, rounded ones are right.
- **Nose cone fit.** See #2. Apogee says vent holes and shear pins are for high power only; leakage around the joint is enough at our sizes (#675).
- **Fin fillets.** Fine. Apogee says fillets "should be used on every rocket" for strength and lower drag, with the trade-off of extra weight at the tail ([#514](https://www.apogeerockets.com/education/downloads/Newsletter514.pdf)). The printed 3.5 mm root fillet does both.
- **Stability.** Fine. Apogee holds 1 caliber as the safety minimum, because the computed CP could be off. Over-stable rockets weathercock into the wind ([#594](https://www.apogeerockets.com/education/downloads/Newsletter594.pdf)). That matches our 1–2 cal advice, the withheld ZIP under 1 cal, and fins sized for the heaviest motor.
- **Ejection delay:** #1. **Minimum diameter:** recovery volume (#3); retention is fine.
- **Weight.** Apogee has no fixed weight targets. Its limits are thrust-to-weight ≥ 5 (less for flat-thrust motors), at least 30 mph (13.4 m/s) off the rod and deployment under 50 mph (#625). We already use 5×, 15 m/s and a 4.5 m/s descent; Apogee rates 14 ft/s (4.3 m/s) as like "a 3 ft drop" (#184). Only the 22 m/s deployment limit is new (#1).

## 3. Fine as-is

Screw-on cap, 4.0 mm lugs and standoff, elastic cord and strap, the 1/3-down chute loop, printed root fillets, 1–2 cal stability per motor, 5:1 thrust-to-weight and rod-speed checks, chute sizing to ~4.5 m/s, the streamer hint, "never glue the nose", and the balance-point preflight.

## 4. For the curriculum author (grades 3–8)

From the owner's link, [Teach with Model Rockets](https://www.apogeerockets.com/Teach-with-Model-Rockets?m=quickside), and the pages it links to:

- **Ready-made lessons for grades 5–8** (free PDFs, about 3 days each; they assume Apogee bulk kits, so adapt them to printed or paper rockets):
  - [Rockets and the Third Law](https://www.apogeerockets.com/downloads/PDFs/58-1.pdf)
  - [Rocket Optimization](https://www.apogeerockets.com/downloads/PDFs/58-2.pdf)
  - [Fins and Finish Lines](https://www.apogeerockets.com/downloads/PDFs/58-3.pdf)
  - [The Optimum Descent Challenge](https://www.apogeerockets.com/downloads/PDFs/58-4.pdf)
  - The 9–12 set, which includes [Calculating Stability](https://www.apogeerockets.com/ed), has worksheets such as [WS-DropTest](https://www.apogeerockets.com/downloads/PDFs/WS-DropTest.pdf).
- **Standards.** Apogee uses the old National Science Education Standards, not NGSS; map ours to 3-PS2-1, MS-PS2-2, MS-ETS1-1…4.
- **Handouts.** The free [Rocketry Reservoir](https://www.apogeerockets.com/downloads/PDFs/Rocketry_Education_Pack.pdf): 100 pages of handouts, quizzes, teacher notes, certificates, colouring pages. Good for the under-12 track; link, don't copy.
- **Launch-day running.**
  - Apogee's booklet [Conducting a Safe and Scientific Launch with Large Groups](https://www.apogeerockets.com/Rocket_Books_Videos/Pamphlets_Reports/Conducting_A_Safe_Scientific_Launch_in_Large_Group_Settings).
  - [Teaching Tips](https://www.apogeerockets.com/Edu/Teaching_Tips): two pads, launch and recovery crews, the adult installs igniters.
- **Lesson ideas we can borrow directly.**
  - **Predict, fly, compare** (the "three-flight method", [#685](https://www.apogeerockets.com/education/downloads/Newsletter685.pdf)): write the app's prediction down *before* flying, then change one thing; free [Flight Record sheet](https://www.apogeerockets.com/Rocket_Books_Videos/Data_Sheets/Flight_Record_Data_Sheet).
  - **Nickel breakout test** (#2): coins until the nose drops; force = pressure × area (grades 5–8).
  - **Drop-test descent** (#184, 58-4): time indoor drops of chutes and streamers; "14 ft/s is like jumping off a 3 ft wall" (grades 3–5).
- **Schools.** Apogee offers phone help, POs, bulk packs and a [grant program](https://www.apogeerockets.com/Rocketry_Grant_Program); its school safety content is just the NAR code. Keep our rule: motors 12+ with an adult.
