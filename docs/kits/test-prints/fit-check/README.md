# Quick fit checks

Short slices of the real parts, so a round of fit testing is a short print instead of a whole kit. One folder per motor size. Each piece has a code engraved on its outside wall, size then piece: 13-1 is the M13 nose bottom, 24-4 the M24 joint shoulder. Each has a single **3MF** with the four pieces laid out on one plate, the four STLs, a preview and a README with the CAD diameters.

| Piece | What it is | Test |
|---|---|---|
| 1 nose bottom (engraved NN-1) | the nose's shoulder (with its tie bar) and a few mm of cone | push into 2: slides in by hand, comes out with a firm pull |
| 2 top section (NN-2) | the top of the body tube: the nose's socket with the shock-cord strap inside (no separate anchor section) | |
| 3 joint socket (NN-3) | the top of a lower body piece (taller rockets printed in pieces) | |
| 4 joint shoulder (NN-4) | the bottom of the piece above it | push into 3: a snug slide you'd glue |

Current fits (per side): body joint 0.22 mm, nose 0.18 mm; M13 0.19 / 0.17. Rebuild after a fit change with `python docs/kits/test-prints/tools/make_fit_checks.py`.
