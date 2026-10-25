"""Render the V29 water/colour audit: two overview maps and zoomed crops at native 6 m pixels."""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from PIL import Image

R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
A = sys.argv[1]
L = np.load(os.path.join(A, "layers.npz"))
S = json.load(open(os.path.join(A, "summary.json"), encoding="utf-8"))
sat = np.array(Image.open(os.path.join(R, "source", "sat_preview.png")).convert("RGB"))
ref, built, painted, streams = L["reference"], L["built"], L["painted"], L["streams"]
centre = L["centre"].astype(float)


def hillshade(h, az=315, alt=45):
    gy, gx = np.gradient(h, 6.0)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    a, z = np.radians(az), np.radians(90 - alt)
    s = np.cos(z) * np.cos(slope) + np.sin(z) * np.sin(slope) * np.cos(a - aspect)
    return np.clip(s, 0, 1)


shade = (110 + 120 * hillshade(centre * 4)).astype(np.uint8)  # relief exaggerated only for readability
base = np.dstack([shade] * 3)

# Map 1: reference vs built water.
m1 = base.copy()
m1[ref & built] = (70, 130, 210)
m1[built & ~ref] = (255, 150, 0)
m1[ref & ~built] = (225, 30, 30)
m1[streams & ~built & ~ref] = (150, 40, 190)
Image.fromarray(m1).save(os.path.join(A, "map1-reference-vs-built.png"))

# Map 2: painted water in the satellite vs built water.
m2 = base.copy()
m2[painted & built] = (70, 130, 210)
m2[painted & ~built] = (230, 0, 200)
m2[built & ~painted] = (255, 210, 0)
Image.fromarray(m2).save(os.path.join(A, "map2-painted-vs-built.png"))


def overview(img, title, legend, name, labels=()):
    fig, ax = plt.subplots(figsize=(11, 11.6), dpi=110)
    ax.imshow(img, extent=(0, 12288, 0, 12288), interpolation="lanczos")
    for x, z, t in labels:
        ax.annotate(t, (x, z), xytext=(x + 150, z + 150), fontsize=8, color="black",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.85), arrowprops=dict(arrowstyle="-", lw=0.6))
    ax.set_title(title, fontsize=11)
    ax.legend(handles=legend, loc="lower left", fontsize=8, framealpha=0.9)
    ax.set_xlabel("X del juego (m)")
    ax.set_ylabel("Z del juego (m)")
    fig.tight_layout()
    fig.savefig(os.path.join(A, name))
    plt.close(fig)


seen, labels = set(), []
for m in S["missing_top"]:
    key = (m["name"] or m["type"])
    if m["name"] and key not in seen and m["built_fraction"] < 0.2:
        seen.add(key)
        labels.append((m["x"], m["z"], m["name"]))
overview(m1, "V29 — agua de referencia (OSM) frente a agua construida (mar + 407 superficies interiores)",
         [Patch(color=np.array(c) / 255, label=t) for c, t in [((70, 130, 210), "referencia y construida"),
                                                                ((225, 30, 30), "en la referencia, NO construida"),
                                                                ((255, 150, 0), "construida, no en la referencia"),
                                                                ((150, 40, 190), "río-línea OSM sin agua")]],
         "overview1-reference-vs-built.png", labels[:12])
overview(m2, "V29 — azul pintado en el satélite frente a agua construida",
         [Patch(color=np.array(c) / 255, label=t) for c, t in [((70, 130, 210), "pintado y con agua"),
                                                                ((230, 0, 200), "pintado de azul pero SECO"),
                                                                ((255, 210, 0), "agua sin pintar (fondo verde/beige)")]],
         "overview2-painted-vs-built.png")

# Crops at native resolution: satellite as painted + categories, 6 m per pixel, nearest neighbour.
CROPS = [
    ("spb-neva-delta", 8100, 9700, 1500),
    ("narva-south", 1900, 5600, 1200),
    ("oredezh-reserve", 7300, 6300, 1200),
    ("volkhov-ilmen", 11000, 1300, 1288),
    ("luga-lakes", 5200, 4300, 1200),
]


def crop(arr, x0, z0, size):
    c0, c1 = int(x0 // 6), int((x0 + size) // 6)
    r0, r1 = int((12288 - (z0 + size)) // 6), int((12288 - z0) // 6)
    return arr[r0:r1, c0:c1]


for name, x0, z0, size in CROPS:
    fig, axes = plt.subplots(1, 2, figsize=(15, 7.8), dpi=100)
    ext = (x0, x0 + size, z0, z0 + size)
    axes[0].imshow(crop(sat, x0, z0, size), extent=ext, interpolation="nearest")
    rb = crop(built, x0, z0, size).astype(float)
    axes[0].contour(np.flipud(rb), levels=[0.5], colors="black", linewidths=0.7,
                    extent=ext, origin="lower")
    axes[0].set_title("Satélite tal cual (6 m/px) · línea negra = borde del agua construida", fontsize=9)
    cat = crop(m1, x0, z0, size)
    axes[1].imshow(cat, extent=ext, interpolation="nearest")
    axes[1].set_title("Azul: ref.+construida · Rojo: falta · Naranja: sobra · Morado: río-línea sin agua", fontsize=9)
    for ax in axes:
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Z (m)")
    fig.suptitle(f"{name} — {size / 1000:.1f} km de lado", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(A, f"crop-{name}.png"))
    plt.close(fig)
print("rendered", sorted(f for f in os.listdir(A) if f.endswith(".png")))
