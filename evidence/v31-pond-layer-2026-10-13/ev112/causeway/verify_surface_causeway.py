"""Surface layers over the causeway changes: PASS/FAIL (exit 1 on FAIL), written apart from patch_surface_v31.py.

Inputs: the target terrain (the one the WRP will be compiled from), its regenerated footprint, the patch manifest of
patch_surface_v31.py (run with --include-changed v31_causeway) and an output folder.
  S1 binding   manifest terrain_sha256 = sha256 of the given terrain, footprint_sha256 = the given footprint, the manifest
               records --include-changed v31_causeway; the terrain carries v31_causeway.
  S2 coverage  every 1 m pixel centre of every native cell with a v31_causeway corner, dilated by one cell, is examined in
               every layer tile that holds it (tile layout of build_surface_v30: x0 = 384 a - 64, z_top = 12288 - 384 b
               + 64, 512 px): the final layer (patched PNG if the manifest changed it, else the shipped source PNG) must
               equal the generator's output for the target terrain (manifest regen/) there, in both s_ and m_ layers.
               Mismatching pixels = 0 (no stale shoreline, bed or road paint left on the changed ground).
  S3 files     every changed layer: PNG and PAA exist with the manifest sha256; the PAA differs from the shipped entry.
Reported, not gated: the 3 px ring just outside the patched zone, regenerated vs shipped (seam), and renders of the
satellite layer before/after with the exact waterline of the target terrain.
Not checked here: the compiled WRP (bind the package to the EV112 WRP in the chain's surface gates) and the in-game look.
Usage: verify_surface_causeway.py <terrain.npz> <footprint.npz> <manifest.json> <out_dir> [--tools DIR]
"""
import argparse, hashlib, json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation

TILE, STEP, OVER = 512, 384, 64


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def tile_of_world(x, z):
    """Every (a, b, j, i) tile pixel whose centre is the world point (x, z) (pixel centres at .5 m)."""
    out = []
    for a in range(32):
        j = x - (STEP * a - OVER) - 0.5
        if not (0 <= j < TILE):
            continue
        for b in range(32):
            i = (2048 * 6 - STEP * b + OVER) - z - 0.5
            if 0 <= i < TILE:
                out.append((a, b, int(round(j)), int(round(i))))
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ("terrain", "footprint", "manifest", "out"):
        ap.add_argument(k)
    ap.add_argument("--tools", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tools"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=False)
    fails, res = [], {}
    m = json.load(open(a.manifest, encoding="utf-8"))
    pdir = Path(a.manifest).parent
    # S1
    s1 = dict(terrain_sha256=sha(a.terrain), manifest_terrain_sha256=m.get("terrain_sha256"),
              footprint_sha256=sha(a.footprint), manifest_footprint_sha256=m.get("footprint_sha256"),
              include_changed=m.get("include_changed", {}).get("arrays"))
    res["S1"] = s1
    if s1["terrain_sha256"] != s1["manifest_terrain_sha256"]:
        fails.append("S1 the manifest describes another terrain")
    if s1["footprint_sha256"] != s1["manifest_footprint_sha256"]:
        fails.append("S1 the manifest describes another footprint")
    if not s1["include_changed"] or "v31_causeway" not in s1["include_changed"]:
        fails.append("S1 the patch was not run with --include-changed v31_causeway")
    z = np.load(a.terrain)
    if "v31_causeway" not in z.files:
        fails.append("S1 the terrain has no v31_causeway")
        mark = np.zeros((2048, 2048), bool)
    else:
        mark = z["v31_causeway"]
    # S2
    cells = mark[:-1, :-1] | mark[:-1, 1:] | mark[1:, :-1] | mark[1:, 1:]
    cells = binary_dilation(cells, np.ones((3, 3), bool))
    rows, cols = np.nonzero(cells)
    recs = {tuple(r["tile"]): r for r in m["records"]}
    cache = {}

    def layers(a_, b_):
        if (a_, b_) not in cache:
            out = {}
            for prefix, suffix in (("s", "lco"), ("m", "lca")):
                stem = f"{prefix}_{a_:03d}_{b_:03d}_{suffix}"
                regen = pdir / "regen" / "layers" / f"{stem}.png"
                rec = recs.get((a_, b_))
                if rec is None or not regen.exists():
                    out[prefix] = None
                    continue
                lay = rec["layers"][prefix]
                final = pdir / "layers" / f"{stem}.png" if lay.get("changed_px") else Path(lay["source_png"])
                out[prefix] = (np.asarray(Image.open(final)), np.asarray(Image.open(regen)), np.asarray(Image.open(lay["source_png"])))
            cache[(a_, b_)] = out
        return cache[(a_, b_)]

    off = np.arange(6) + 0.5
    n_px, mism, missing_tile = 0, {"s": 0, "m": 0}, 0
    bad_where = []
    for r, c in zip(rows, cols):
        for ox in off:
            for oz in off:
                x, zz = 6.0 * c + ox, 12282.0 - 6.0 * r - oz
                hits = tile_of_world(x, zz)
                for a_, b_, j, i in hits:
                    L = layers(a_, b_)
                    for prefix in ("s", "m"):
                        if L[prefix] is None:
                            missing_tile += 1
                            continue
                        fin, reg, _ = L[prefix]
                        n_px += 1
                        if not np.array_equal(fin[i, j], reg[i, j]):
                            mism[prefix] += 1
                            if len(bad_where) < 20:
                                bad_where.append([a_, b_, j, i, prefix])
    res["S2"] = dict(cells=int(cells.sum()), pixel_layer_checks=n_px, mismatching=mism, tiles_not_patched=missing_tile,
                     first_mismatches=bad_where)
    if mism["s"] or mism["m"] or missing_tile or n_px == 0:
        fails.append(f"S2 stale or unpatched pixels on the changed ground: {mism}, tiles not patched {missing_tile}")
    # S3
    s3 = []
    for e in m.get("entries", []):
        ok = os.path.exists(e["file"]) and sha(e["file"]) == e["sha256"] and e["sha256"] != e["base_sha256"]
        png = e["file"][:-4] + ".png"
        rec_png = None
        for rec in m["records"]:
            for lay in rec["layers"].values():
                if lay.get("entry") == e["entry"]:
                    rec_png = lay.get("png_sha256")
        ok = ok and os.path.exists(png) and sha(png) == rec_png
        s3.append(dict(entry=e["entry"], ok=bool(ok)))
    res["S3"] = dict(entries=len(s3), bad=[x["entry"] for x in s3 if not x["ok"]])
    if res["S3"]["bad"] or not s3:
        fails.append(f"S3 layer files: {res['S3']['bad']}")
    # seam ring (reported): 3 px outside the patched zone in the patched tiles, regenerated vs shipped
    ring = []
    for rec in m["records"]:
        a_, b_ = rec["tile"]
        L = layers(a_, b_)
        if L["s"] is None:
            continue
        fin, reg, base = L["s"]
        changed = np.any(fin != base, axis=-1)
        if not changed.any():
            continue
        dil = binary_dilation(changed, np.ones((3, 3), bool), iterations=3) & ~binary_dilation(changed, np.ones((3, 3), bool))
        d = np.abs(reg.astype(int) - base.astype(int)).max(-1)[dil]
        ring.append(dict(tile=[a_, b_], ring_px=int(dil.sum()), regen_vs_shipped_max=int(d.max(initial=0)),
                         regen_vs_shipped_p90=float(np.percentile(d, 90)) if d.size else 0.0))
    res["seam_ring_report"] = ring
    # renders: islet before (shipped) / after (final) satellite with the target waterline
    try:
        sys.path.insert(0, os.path.join(os.path.abspath(a.tools), "water"))
        import shore_ramp_v31 as sr
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
        H = z["heights"].astype(np.float64)
        f = np.load(a.footprint); pl = f["plane"].astype(np.float64)
        W, fp = sr.corner_water(pl, f["field"].astype(np.float64))
        for name, (x0, x1, z0, z1) in (("islet", (6600, 7700, 10080, 10820)), ("c1-mainland", (6650, 6900, 10080, 10300)),
                                        ("c0-east", (7450, 7700, 10620, 10860)), ("c0-islet", (6880, 7120, 10540, 10720))):
            img = {k: np.zeros((int(z1 - z0), int(x1 - x0), 3), np.uint8) for k in ("shipped", "final")}
            for rec in m["records"]:
                a_, b_ = rec["tile"]
                L = layers(a_, b_)
                if L["s"] is None:
                    continue
                fin, reg, base = L["s"]
                tx0, tz1 = STEP * a_ - OVER, 2048 * 6 - STEP * b_ + OVER
                for k, arr in (("shipped", base), ("final", fin)):
                    jx0, jx1 = max(int(x0 - tx0), 0), min(int(x1 - tx0), TILE)
                    iz0, iz1 = max(int(tz1 - z1), 0), min(int(tz1 - z0), TILE)
                    if jx1 <= jx0 or iz1 <= iz0:
                        continue
                    ox_, oz_ = int(tx0 + jx0 - x0), int(z1 - (tz1 - iz0))
                    img[k][oz_:oz_ + iz1 - iz0, ox_:ox_ + jx1 - jx0] = arr[iz0:iz1, jx0:jx1, :3]
            r0, r1 = int((12282 - z1) / 6), int((12282 - z0) / 6) + 1
            c0, c1 = int(x0 / 6), int(x1 / 6) + 1
            seg = sr.extract_segments(H, W, fp, pl, r0, r1, c0, c1)
            fig, axs = plt.subplots(1, 2, figsize=(22, 22 * (z1 - z0) / (x1 - x0) / 2 + 1.5))
            for axp, k in zip(axs, ("shipped", "final")):
                axp.imshow(img[k], extent=(x0, x1, z0, z1), interpolation="nearest")
                axp.add_collection(LineCollection(seg["p"], colors="#ff3050", linewidths=0.6))
                axp.set_xlim(x0, x1); axp.set_ylim(z0, z1); axp.set_aspect("equal")
                axp.set_title(f"{k} satellite layer, red: exact waterline of the target terrain")
            plt.tight_layout(); plt.savefig(os.path.join(a.out, f"surface-{name}.png"), dpi=70); plt.close()
        res["renders"] = sorted(p for p in os.listdir(a.out) if p.endswith(".png"))
    except Exception as ex:                       # renders are evidence, not a gate
        res["renders_error"] = repr(ex)
    res["fails"] = fails
    res["verdict"] = "FAIL" if fails else "PASS"
    res["not_checked"] = ["compiled WRP binding (EV112 WRP not built here)", "in-game look"]
    with open(os.path.join(a.out, "verify-surface.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(dict(verdict=res["verdict"], fails=fails, S2=res["S2"], S3=res["S3"]), indent=1))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
