# rocketgen

The Rocket Builder geometry engine for the web version: a Python/build123d port of `src/RocketGenerator.fs`. See `../docs/web_platform_spec.md` for the plan and `report.md` for what's ported and what OpenCascade can't do yet.

## Setup

```
cd geometry
pip install -e ".[test]"        # build123d pulls in OpenCascade (OCP)
pip install matplotlib          # only for --png previews
```

## Use

```
python -m rocketgen.cli --motor M18 --fins swept --out out/m18_swept --png
python -m pytest -q
```

Run the CLI with `--help` to see every option.

Output in `--out`:
- one STL per part (`Aft`, `Seg_2`…, `Anchor_Seg`, `Nose`, `Motor_Cap`, `Rod_Standoff`), each in print orientation on z = 0;
- `assembled.stl`, with every part in its stacked position;
- with `--png`, preview renders.

From Python:

```python
from rocketgen.build import build_rocket
from rocketgen.params import DesignParams
from rocketgen.fins import FinShape

rocket = build_rocket(DesignParams(motor="M18", fin_shape=FinShape.SWEPT))
print(rocket.summary(), rocket.notes)
part = rocket.parts[0]   # .assembled / .local (build123d Solids), .volume
```

## Layout

| Module | FeatureScript counterpart |
|---|---|
| `params.py` | dialog defaults/bounds, `computeDerivedValues`, `threadGeometry` |
| `fins.py` | `finParams`, `finDimensions`, `finOutline`, `finLowestZWithin` |
| `aft.py` | `buildAftSegment`, `findFinRootEdges` |
| `thread.py` | `sweepThreadRidge`, `buildThreadedBoss`, `buildThreadedCap` |
| `body.py` | `buildBodySegment`, `buildNoseCone`, `noseRadiusAt` |
| `lugs.py` | `lugGeometry`, `buildRodStandoff`, `planForwardLug`, `buildOneLug`, `lugEdgeFillets` |
| `anchor.py` | `anchorStrapGeometry`, `buildAnchorStrap` |
| `build.py` | the feature's main body (segmentation, placement), `reportMass` |
| `geom.py` | shared helpers, including `fillet_checked` |
| `export.py`, `cli.py` | STL/PNG output, command line |

Units are mm. Motor and settings data are in `rocketgen/data/*.csv`, copied from OS_Rocket_Builder's `data/` (the Onshape Variable Studios); keep them in sync.
