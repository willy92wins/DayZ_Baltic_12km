"""Verify a fresh V3 Buldozer observation, without fitting its registration."""
from pathlib import Path
import argparse
import hashlib
import json
import os

import numpy as np
import rasterio

parser = argparse.ArgumentParser()
for name in ("log", "native", "before", "out"):
    parser.add_argument("--" + name, type=Path, required=True)
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)


def samples(text, prefix, columns, count):
    values = np.array([[float(v) for v in line.split(";")[1:]]
                       for line in text.splitlines() if line.startswith(prefix + ";")])
    if values.shape != (count, columns) or not np.isfinite(values).all():
        raise ValueError(f"Incomplete or invalid {prefix}: {values.shape}")
    return values


text = args.log.read_text()
if text.splitlines()[0] != "NARVA_OBSERVER_V3":
    raise ValueError("Expected the final V3 native observer")
grid = samples(text, "G", 3, 289)
profile = samples(text, "P", 5, 289)
ends = samples(text, "E", 6, 34)
before = samples(args.before.read_text(), "P", 5, 289)
with rasterio.open(args.native) as src:
    native = src.read(1)
    if native.shape != (2048, 2048):
        raise ValueError("Wrong terrain size")


def interpolate(x, north, legacy=False):
    # Fixed contract measured by V2, not refitted to the V3 data.
    col = x / 6
    row = ((12288 if legacy else 12282) - north) / 6
    ci, ri = np.floor(col).astype(int), np.floor(row).astype(int)
    a, b = col - ci, row - ri
    z00, z10 = native[ri, ci], native[ri, ci + 1]
    z01, z11 = native[ri + 1, ci], native[ri + 1, ci + 1]
    return np.where(b <= a, z00*(1-a) + z10*(a-b) + z11*b,
                    z00*(1-b) + z01*(b-a) + z11*a)


grid_error = np.abs(interpolate(grid[:, 0], grid[:, 1]) - grid[:, 2])
distance = profile[:, 0]
# Enforce log rounds coordinates; reproduce the declared sample positions.
px = 2417.143 + .988364361 * distance
pz = 6889.885 - .152104866 * distance
profile_error = np.abs(interpolate(px, pz) - profile[:, 3])
legacy_error = np.abs(interpolate(grid[:, 0], grid[:, 1], True) - grid[:, 2])
deck = profile[np.abs(distance) <= 12.25, 4]
end_results = []
for d in (-12.5, 12.5):
    e = ends[ends[:, 0] == d]
    if len(e) != 17 or not np.array_equal(e[:, 1], np.arange(-4, 4.01, .5)):
        raise ValueError("Incomplete landing coverage")
    end_results.append({"distance_m": d, "samples": len(e), "width_m": 8,
                        "terrain_min_m": float(e[:, 4].min()),
                        "terrain_max_m": float(e[:, 4].max()),
                        "max_gap_to_deck_m": float(np.abs(e[:, 4] - 2).max()),
                        "surface_query_max_error_m": float(np.abs(e[:, 5] - 2).max())})
metadata = dict(line.split("=", 1) for line in text.splitlines() if "=" in line)
objects = []
for line in text.splitlines():
    if line.startswith('shape='):
        objects.append({'shape': line.split('=', 1)[1]})
    elif objects and '=' in line and line.startswith(('position=', 'orientation=', 'raw_roadway_')):
        key, value = line.split('=', 1)
        objects[-1][key] = value
bridges = [obj for obj in objects if obj['shape'].replace('\\', '/').lower() ==
           'dz/structures/roads/bridges/bridge_metal_25.p3d']
checks = {
    "one_expected_bridge": len(bridges) == 1,
    "fixed_registration_grid": bool(grid_error.max() <= .00501),
    "fixed_registration_profile": bool(profile_error.max() <= .0051),
    "reject_old_ui_northing": bool(legacy_error.max() > .1),
    "deck_at_2m": bool(np.max(np.abs(deck - 2)) <= .00501),
    "both_landings_8m": all(e["max_gap_to_deck_m"] <= .01 and
                            e["surface_query_max_error_m"] <= .01 for e in end_results),
}
result = {
    "status": "PASS_NATIVE_HEIGHTS" if all(checks.values()) else "FAIL",
    "checks": checks, "grid_samples": len(grid), "profile_samples": len(profile),
    "grid_max_error_m": float(grid_error.max()),
    "profile_max_error_m": float(profile_error.max()),
    "negative_old_registration_max_error_m": float(legacy_error.max()),
    "endpoints": end_results,
    "water_observation": {k: metadata.get(k) for k in
                          ("sea_level", "center_is_sea", "center_is_pond", "center_water_depth")},
    "native_objects": objects,
    "sha256": {k: hashlib.sha256(getattr(args, k).read_bytes()).hexdigest()
               for k in ("log", "native", "before")},
    "limits": ["Native surface queries, not player traversal or vehicle collision.",
               "Local Narva registration only; no global terrain correction.",
               "Pond hidden during observation; no elevated inland-water pass."]
}
(args.out / "engine-validation-v3.json").write_text(json.dumps(result, indent=2) + "\n")
os.environ.setdefault("MPLCONFIGDIR", str(args.out / "mpl-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 1, figsize=(11, 7), dpi=150, sharex=True)
for ax, p, label in zip(axes, (before, profile), ("Antes: desnivel en el acceso este", "Después: lectura del terreno corregido")):
    ax.plot(p[:, 0], p[:, 3], color="#a86b35", label="Terreno: SurfaceY")
    ax.plot(p[:, 0], p[:, 4], color="#164260", lw=2, label="Superficie: SurfaceRoadY")
    ax.axhline(0, color="#61b1c8", ls=":", label="Referencia marina 0 m")
    ax.axvspan(-12.5, 12.5, color="#aab8c5", alpha=.15)
    ax.set(ylabel="Cota nativa (m)", title=label, ylim=(-2, 2.5))
    ax.grid(alpha=.2)
    ax.legend(loc="lower right", fontsize=8)
axes[-1].set_xlabel("Distancia al centro (m), oeste → este")
fig.suptitle("Narva · contraste independiente de alturas en Buldozer")
fig.tight_layout()
fig.savefig(args.out / "accesos-antes-despues.png")
plt.close(fig)
print(json.dumps(result, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
