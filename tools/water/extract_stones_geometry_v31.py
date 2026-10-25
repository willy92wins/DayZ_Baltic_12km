"""Stones geometry for streambed_kit_v31.py v9, read from the vanilla ODOL files (P:/DZ/water/streambed/misc).

Per model stones_<family>_<kind>.p3d (kind group_1/2/3, bar, bar_curve; stored frame = the frame a world matrix places), from
the visual LOD whose resolution is closest to 1.0 (the LOD the stone check of 17-10 used, scratchpad stones_check.py):
  base      every vertex with y <= the 10th percentile of the LOD's y (the base ring: stones are placed with a yaw only,
            so these are also the lowest 10 % in world y whatever the yaw);
  sample    every k-th vertex (k = ceil(n / 1500)), for the share of the stone standing above visible water;
  all       every visual-LOD vertex at source precision, for the final visibility acceptance test;
  extent    min/max of x, y, z over all vertices; n = vertex count.
Fail-closed like extract_streambed_geometry_v31.py: the source folder must exist and all 15 models must load with
vertices; otherwise nothing is written and the exit code is 1. Written to <out.json>.tmp, renamed when complete.
Usage: extract_stones_geometry_v31.py <out.json> [source_dir]   (default P:/DZ/water/streambed/misc/, the P: subst; needs
       the dayz-p3d-debinarizer odol_reader)
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, r"C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts")
from odol_reader import ODOL

D = "P:/DZ/water/streambed/misc/"
FAMILIES = ("leaf", "moss", "sand")
KINDS = ("group_1", "group_2", "group_3", "bar", "bar_curve")
REQUIRED = [f"{fam}_{kind}" for fam in FAMILIES for kind in KINDS]
SAMPLE_MAX = 1500


def model(name, src):
    o = ODOL.from_file(src + f"stones_{name}.p3d")
    lod = min(o.lods, key=lambda l: abs(l.resolution - 1.0))
    V = np.array([(p.x, p.y, p.z) for p in lod.vertices], float)
    if not len(V):
        raise OSError("no vertices")
    p10 = float(np.percentile(V[:, 1], 10))
    k = max(1, math.ceil(len(V) / SAMPLE_MAX))
    return dict(lod_resolution=float(lod.resolution), n=int(len(V)), base_y_p10=round(p10, 4),
                base=np.round(V[V[:, 1] <= p10], 3).tolist(), sample=np.round(V[::k], 3).tolist(),
                all=V.tolist(),
                extent=dict(x=[round(float(V[:, 0].min()), 3), round(float(V[:, 0].max()), 3)],
                            y=[round(float(V[:, 1].min()), 3), round(float(V[:, 1].max()), 3)],
                            z=[round(float(V[:, 2].min()), 3), round(float(V[:, 2].max()), 3)]))


def main():
    out = sys.argv[1]
    src = sys.argv[2].replace("\\", "/").rstrip("/") + "/" if len(sys.argv) > 2 else D
    if not os.path.isdir(src):
        sys.exit(f"source folder {src} not found (P: subst missing?): nothing written")
    res = dict(schema="streambed-stones-geometry-v31.v1", source=src, odol_reader="dayz-p3d-debinarizer/scripts/odol_reader.py", models={})
    bad = []
    for name in REQUIRED:
        try:
            res["models"][name] = model(name, src)
        except OSError as e:
            bad.append(f"{name}: {e}")
            continue
        m = res["models"][name]
        print(name, "lod", m["lod_resolution"], "n", m["n"], "base", len(m["base"]), "sample", len(m["sample"]), "extent", m["extent"])
    if bad or sorted(res["models"]) != sorted(REQUIRED):
        sys.exit("refused, nothing written: " + "; ".join(bad))
    with open(out + ".tmp", "w", newline="\n") as f:
        json.dump(res, f, separators=(",", ":"))
    os.replace(out + ".tmp", out)


if __name__ == "__main__":
    main()
