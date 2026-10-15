# Fit test coupons

Short test pieces that copy only the joints of a rocket, so the clearances can be tuned without printing whole rockets. Made by `geometry/rocketgen/fit_test.py` from the same profiles as the real parts (`rocketgen/body.py`).

**Why:** the first M18 print (2026-10-15) was far too tight to assemble. Every shoulder was built with `fit_slip` = **0.02 mm** radial from `rocket_global_settings.csv`, for body joints and the nose alike. That value came from the CAD and doesn't allow for FDM: holes print small, outer walls print large, and the first layers flare out ("elephant foot") right at the shoulder's bottom edge.

## What's on each plate

`files/fit_test_<size>.3mf`: one plate per tube size (currently committed: M13, M18, M24, M29; make BT60 with `--sizes BT60`), 9 separate objects, sized for an X1C / P1S plate.

| Size | Body OD / ID (mm) | Used by |
|---|---|---|
| M13 | 16.4 / 13.4 | M13 rockets |
| M18 | 21.4 / 18.4 | M18 rockets |
| M24 | 27.4 / 24.4 | M24 and M24L rockets |
| M29 | 32.4 / 29.4 | M29 rockets |
| BT60 | 41.6 / 38.6 | M24 / M29 with the BT60 custom tube |

- **Socket** (with the size on its flag): the top of a body segment, i.e. its bore and the 45° countersink. It prints upright like a real segment. Both J and N plugs go into it.
- **J05, J10, J15, J20**: body-joint shoulders (full length, glued in the real rocket) at **0.05 / 0.10 / 0.15 / 0.20 mm radial** clearance.
- **N15, N20, N25, N30**: nose shoulders (30% shorter, must slide out at ejection) at **0.15 / 0.20 / 0.25 / 0.30 mm** radial clearance.
- Every plug has a **0.5 mm 45° chamfer** on its bottom outer edge. It takes off the elephant foot and helps the plug find the socket. The real parts don't have it yet; it gets switched on together with the chosen fits.
- Plugs print **closed end down, cup open upward** (owner's change, 2026-10-15: shoulder-down stood on a thin edge). The label is recessed 0.6 mm into the closed end and reads from below. Because the shoulder now prints at the top, the chamfer acts only as a lead-in; the real parts still print shoulder-down, so judge them with that in mind.

Radial clearance means per side, so the diameter gap is twice the number on the label.

## Print settings

Use the same settings you'd use for a real rocket: Bambu Studio, the PLA you use for rockets, 0.20 mm Standard, default elephant foot compensation, no supports. If you can, print the M18 plate on **both** the X1C and the P1S, so we can tell whether one value works on both printers. Write down which printer and filament each plate was printed with.

## How to judge each plug

Test each plug in its socket, square, with finger pressure only:

| | Too tight | Right | Too loose |
|---|---|---|---|
| **J (glued joint)** | needs twisting or force, or won't seat on the countersink | slides all the way to the seat with light pressure, no side-to-side wobble | rocks or rattles when seated |
| **N (nose)** | any drag at all, or sticks partway in | slides in and out freely and seats flush; held upside down it **just** stays in, and a light shake drops it | falls out when you turn it over, or wobbles visibly |

The nose plug is lighter than a real nose cone, so pick the loosest N plug that still passes the upside-down check. A wrap of tape can always tighten a loose nose; nothing fixes one that's too tight.

## Results (fill in)

| Size | Printer | Filament | Best J | Best N | Notes |
|---|---|---|---|---|---|
| M13 | P1S | PLA | J15–J20 (J20 good slip fit, fine with glue; J15 a little tight but works; J10 needs excessive force; J05 won't go in) | below N15 (N15 slips but is too loose for a cone; N20–N30 all too loose). Nose should feel like J20 | Round 1, 2026-10-16. The shorter nose shoulder feels looser at the same clearance. Round 2: `files/round2/` |
| M18 | P1S | PLA | J20 (best, a little more slip); J15 good, would work; J10 / J05 won't go in | between N15 and N20 (N15 a snug bit too tight, N20 a little too loose; N25 / N30 far too loose) | Round 1, 2026-10-16 |
| M24 | P1S | PLA | between J15 and J20 (J15 a little snug, J20 slips but a little loose; J10 / J05 too tight) | N15 about right (N20 a bit loose; N25 / N30 too loose) | Round 1, 2026-10-16 |
| M29 | P1S | PLA | between J15 and J20 (J15 correct, J20 a smidge loose; J10 / J05 far too tight) | N15 best (N20–N30 too loose) | Round 1, 2026-10-16 |
| BT60 | | | | | |

If the best plug is at the end of a range (J05 too loose, or J20 / N30 still too tight), regenerate with a wider range, for example:

```
cd geometry
python -m rocketgen.fit_test --sizes M18 --joint 0.2 0.25 0.3 --nose 0.3 0.35 0.4 --out ../fit_test/files
```

(`--out` also writes one STL per coupon to `files/stl/`; those are not committed.)

## Outcome (2026-10-16)

Set as the website defaults in `geometry/rocketgen/params.py` (`web_fits`): **body joints 0.18 mm, nose 0.15 mm, 0.12 mm for a nose shoulder under 8 mm** (M13), plus the 0.5 mm shoulder chamfer. The nose needs less clearance than a joint for the same feel because its shoulder is 30% shorter. Still to check: M13 round 2 (`files/round2/`), the X1C, and one full rocket printed with the new fits.
