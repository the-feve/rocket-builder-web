"""Output: one STL per part in print orientation, an assembled STL for
viewing, and optional PNG previews (needs matplotlib)."""

from __future__ import annotations

from pathlib import Path

from build123d import Compound, export_stl

from .build import Rocket

PART_COLORS = [  # same defaults as PART_COLORS in the FeatureScript
    (0.85, 0.25, 0.20), (0.20, 0.45, 0.85), (0.95, 0.75, 0.15),
    (0.30, 0.70, 0.35), (0.60, 0.35, 0.75), (0.95, 0.50, 0.15),
]


def export_parts(rocket: Rocket, out_dir: Path, tolerance: float = 0.01, angular_tolerance: float = 0.1) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for part in rocket.parts:
        path = out_dir / f"{part.name}.stl"
        export_stl(part.local, path, tolerance=tolerance, angular_tolerance=angular_tolerance)
        paths.append(path)
    path = out_dir / "assembled.stl"
    export_stl(Compound([p.assembled for p in rocket.parts]), path, tolerance=tolerance, angular_tolerance=angular_tolerance)
    paths.append(path)
    return paths


def _mesh(shape, tol=0.05):
    verts, tris = shape.tessellate(tol, 0.2)
    return [(v.X, v.Y, v.Z) for v in verts], tris


def render_png(shapes_colors, path: Path, elev=15, azim=-60, px=900, title: str | None = None):
    """Shaded z-buffer render of [(shape, rgb), ...], orthographic. Previews
    only; needs numpy and matplotlib (for writing the PNG)."""
    import math

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    a, e = math.radians(azim), math.radians(elev)
    # Camera basis: view direction toward the origin from (azim, elev).
    fwd = -np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    right = np.cross(fwd, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    light = -fwd + 0.6 * up - 0.4 * right
    light /= np.linalg.norm(light)

    meshes = []
    for shape, rgb in shapes_colors:
        if shape is None:  # e.g. a part wholly on the cut-away side of a section
            continue
        v, t = _mesh(shape)
        meshes.append((np.array(v), np.array(t), np.array(rgb)))
    allv = np.vstack([m[0] for m in meshes])
    sx, sy = allv @ right, allv @ up
    span = max(sx.max() - sx.min(), sy.max() - sy.min()) * 1.05
    scale = px / span
    cx, cy = (sx.max() + sx.min()) / 2, (sy.max() + sy.min()) / 2
    W = H = px
    zbuf = np.full((H, W), np.inf)
    img = np.ones((H, W, 3))
    for v, t, rgb in meshes:
        X = (v @ right - cx) * scale + W / 2
        Y = H / 2 - (v @ up - cy) * scale
        Z = v @ fwd
        tv = v[t]
        n = np.cross(tv[:, 1] - tv[:, 0], tv[:, 2] - tv[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        n[(n @ fwd) > 0] *= -1  # two-sided lighting (section faces, inside walls)
        shade = 0.30 + 0.70 * np.clip(n @ light, 0, 1)
        for k, (i0, i1, i2) in enumerate(t):
            xs, ys, zs = X[[i0, i1, i2]], Y[[i0, i1, i2]], Z[[i0, i1, i2]]
            x0, x1 = max(int(xs.min()), 0), min(int(xs.max()) + 1, W - 1)
            y0, y1 = max(int(ys.min()), 0), min(int(ys.max()) + 1, H - 1)
            if x1 < x0 or y1 < y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(d) < 1e-12:
                continue
            w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
            w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not inside.any():
                continue
            z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            hit = inside & (z < sub)
            sub[hit] = z[hit]
            img[y0:y1 + 1, x0:x1 + 1][hit] = np.clip(rgb * shade[k], 0, 1)
    fig = plt.figure(figsize=(W / 100, H / 100 + (0.4 if title else 0)), dpi=100)
    ax = fig.add_axes([0, 0, 1, H / (H + (40 if title else 0))])
    ax.imshow(img)
    ax.set_axis_off()
    if title:
        fig.text(0.5, 0.985, title, ha="center", va="top", fontsize=12)
    fig.savefig(path)
    plt.close(fig)


def half(shape):
    """The half with y <= 0, for section views looking at the cut face (from +y)."""
    from build123d import Box, Pos

    from .geom import as_shape
    return as_shape(shape.intersect(Pos(0, -500, 0) * Box(2000, 1000, 2000)))


def render_rocket(rocket: Rocket, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    col = lambda i: PART_COLORS[i % len(PART_COLORS)]  # noqa: E731
    parts = rocket.parts
    paths = [out_dir / "assembled.png", out_dir / "aft_closeup.png", out_dir / "section.png", out_dir / "aft_section.png"]
    render_png([(p.assembled, col(i)) for i, p in enumerate(parts)], paths[0], elev=10, azim=-60, px=1000,
               title="Assembled")
    aft, cap = parts[0], parts[-1]
    render_png([(aft.assembled, col(0)), (cap.assembled, col(len(parts) - 1))], paths[1], elev=-25, azim=-40,
               title="Aft + motor cap, from below")
    render_png([(half(p.assembled), col(i)) for i, p in enumerate(parts)], paths[2], elev=0, azim=90, px=1000,
               title="Half section")
    from build123d import Box, Pos
    window = Pos(0, 0, 25) * Box(200, 200, 90)
    from .geom import as_shape
    render_png([(as_shape(half(aft.assembled).intersect(window)), col(0)), (half(cap.assembled), col(len(parts) - 1))],
               paths[3], elev=0, azim=90, title="Aft section, z < 70 mm")
    return paths
