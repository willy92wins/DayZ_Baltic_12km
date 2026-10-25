"""Render the water V3 design over relief V30 for Guillermo's phase-1 gate: overview with stream tiers and crops."""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from shapely.geometry import shape

W, AUDIT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
relief = np.load(os.path.join(R, "tests", "relief_v30", "relief_v30_mix.npz"))["new"].astype(float)
built = np.load(os.path.join(AUDIT, "layers.npz"))["built"]
old_channel = shape(json.load(open(os.path.join(R, "evidence", "regional-foundation-v1", "river-engineering-game.json"), encoding="utf-8"))["features"][0]["geometry"])
bodies = json.load(open(os.path.join(W, "water_v3.geojson"), encoding="utf-8"))["features"]
streams = json.load(open(os.path.join(W, "streams_candidates.geojson"), encoding="utf-8"))["features"]
prof = np.load(os.path.join(W, "profiles.npz"))
EXT = (0, 12288, 0, 12288)
COL = {"navigable": "#0b3d91", "delta_navigable": "#0b3d91", "delta_branch": "#1f5fbf", "delta_harbour": "#1f5fbf",
       "river": "#2b8cff", "pond": "#d63bd6", 4000: "#00a6a6", 2500: "#3fd0d0", 1500: "#9ee8e8"}


def hill(h):
    gy, gx = np.gradient(h, 6.0)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, zen = np.radians(315), np.radians(50)
    hs = np.clip(np.cos(zen) * np.cos(slope) + np.sin(zen) * np.sin(slope) * np.cos(az - aspect), 0, 1)
    rgb = np.dstack([0.62 + 0.33 * hs] * 3)
    rgb[h < 0.8] = (0.55, 0.68, 0.80)
    return rgb


def draw(ax, geom, color, lw=0.0, alpha=1.0, fill=True):
    polys = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
    for p in polys:
        if p.geom_type != "Polygon" or p.is_empty:
            continue
        x, z = p.exterior.xy
        if fill:
            ax.fill(x, z, color=color, alpha=alpha, lw=lw)
        else:
            ax.plot(x, z, color=color, lw=lw, alpha=alpha)


def deep_cuts():
    pts = []
    for f in streams + [b for b in bodies if b["properties"]["class"] == "river"]:
        key = f["properties"].get("id")
        if key and key in prof.files:
            a = prof[key]
            cut = a[:, 3] - a[:, 5]
            sel = cut > 5.0
            pts.append(a[sel][:, 1:3])
    return np.vstack(pts) if pts else np.zeros((0, 2))


base = hill(relief)
cuts = deep_cuts()


def render(name, ext, figsize, title, show_old=False):
    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    x0, x1, z0, z1 = ext
    c0, c1, r0, r1 = int(x0 / 6), int(x1 / 6), int((12288 - z1) / 6), int((12288 - z0) / 6)
    ax.imshow(base[r0:r1, c0:c1], extent=ext, interpolation="lanczos")
    if show_old:
        draw(ax, old_channel, "#ff8c00", lw=0.8, fill=False)
    for tier in (1500, 2500, 4000):
        for f in streams:
            if f["properties"]["tier_m"] == tier:
                draw(ax, shape(f["geometry"]), COL[tier])
    for f in bodies:
        draw(ax, shape(f["geometry"]), COL.get(f["properties"]["class"], "k"))
    if len(cuts):
        sel = (cuts[:, 0] >= x0) & (cuts[:, 0] <= x1) & (cuts[:, 1] >= z0) & (cuts[:, 1] <= z1)
        ax.scatter(cuts[sel, 0], cuts[sel, 1], s=1.5, c="red", zorder=5)
    ax.set_xlim(x0, x1)
    ax.set_ylim(z0, z1)
    ax.set_title(title, fontsize=11)
    legend = [Patch(color=COL["navigable"], label="navegable 30–60 m"), Patch(color=COL["delta_branch"], label="delta del Neva"),
              Patch(color=COL["river"], label="ríos con nombre 8–20 m"), Patch(color=COL[4000], label="arroyos ≥4 km"),
              Patch(color=COL[2500], label="arroyos 2,5–4 km"), Patch(color=COL[1500], label="arroyos 1,5–2,5 km"),
              Patch(color=COL["pond"], label="lagunas nuevas ≥300 m²"), Patch(color="red", label="corte >5 m (revisar)")]
    if show_old:
        legend.append(Patch(color="#ff8c00", label="canal actual V29"))
    ax.legend(handles=legend, loc="lower left", fontsize=7, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"water-{name}.png"))
    plt.close(fig)


render("overview", EXT, (13, 13.2), "Diseño del agua V3 sobre el relieve V30 (mezcla)")
render("spb-delta", (8000, 9700, 9600, 10900), (13, 10.2), "Delta del Neva: brazos e islas", show_old=True)
render("luga", (4800, 6600, 4400, 5800), (13, 10.4), "Luga: cauce navegable natural frente al canal actual", show_old=True)
render("narva", (1300, 2900, 5200, 7400), (10, 13.4), "Narva y frontera", show_old=True)
render("volkhov-ilmen", (10600, 12288, 800, 3400), (10.5, 15), "Vóljov, Msta y Shelón hacia Ilmen")
render("reserve", (6800, 9400, 3400, 6800), (11, 13.8), "Reserva y Oredezh")
print("rendered")
