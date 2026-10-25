"""Judge a server probe of the dam points (probe_points_dam_v31.py, schema dam-probe-points.v2) on both sides of the dam.
Log rows (missions/BalticBridgeProbeV2.BalticTrial/init.c:81-88): P;id;ground;sea;pond;surface;depth;roadY;objects with
ground = SurfaceY, sea = SurfaceIsSea, pond = SurfaceIsPond, surface = GetWaterSurfaceHeightNoFakeWave from ground + 100,
depth = GetWaterDepth at ground + 0.01, roadY = SurfaceRoadY3D from ground + 30 (UNDER).
Sea level L: the probe measures it. L = median 'surface' of the always_sea, pond-free points that report sea; at least
MIN_SEA_REF of them, spread <= 0.02 m, L within [0.45, 1.05] (the modelled 0.5-1.0 tide), else FAIL (indeterminate).
Per point (fail closed on a missing row, a duplicate id or a non-finite value):
  every point     |ground - terrain_y| <= 0.01 (the staged terrain is the one the points were made on);
  crest           |roadY - expect_roadway_y| <= 0.02 (the walkway: roadway triangles of the staged records);
  pond 'wet'      depth > 0, pond flag, |surface - plane| <= 0.05, no sea flag (upstream: pond water at its plane);
  pond 'none'     no pond-level water: not (depth > 0 and surface > L + 0.05); and no pond flag where the cell is not in
                  the footprint at all (the flag is not judged on a footprint cell whose plane lies under the ground);
  sea, if not wet terrain < L - 0.05: sea flag and |surface - L| <= 0.05; terrain < L - 0.10: depth > 0;
                  terrain > L + 0.05: no sea flag; terrain > L + 0.10 and pond 'none': depth <= 0 (dry).
'edge' pond points and the +-0.05 m sea band are not judged on those fields. Exit 0 only if every check passes.
Usage: eval_dam_probe_v31.py <points.json> <probe.log> <out.json> [--id-offset N]"""
import json, math, sys
import numpy as np

MIN_SEA_REF, L_RANGE = 3, (0.45, 1.05)


def rows(path, off):
    out, dup, bad = {}, [], []
    for line in open(path, encoding="utf-8"):
        a = line.strip().split(";")
        if a[0] != "P":
            continue
        if len(a) != 9:
            bad.append(line.strip()); continue
        i = int(a[1]) - off
        v = dict(ground=float(a[2]), sea=a[3] == "true", pond=a[4] == "true", surface=float(a[5]), depth=float(a[6]),
                 roadY=float(a[7]), objects=int(a[8]))
        if not all(math.isfinite(v[k]) for k in ("ground", "surface", "depth", "roadY")):
            bad.append(line.strip()); continue
        if i in out:
            dup.append(i)
        out[i] = v
    return out, dup, bad


def judge(pts, R):
    res = dict(points=len(pts), rows=len(R))
    missing = [p["id"] for p in pts if p["id"] not in R]
    refs = [R[p["id"]]["surface"] for p in pts if p["id"] in R and p["tide_class"] == "always_sea" and p["pond_class"] == "none"
            and R[p["id"]]["sea"]]
    L = float(np.median(refs)) if refs else None
    res.update(missing=missing[:20], n_missing=len(missing), sea_refs=len(refs), sea_level=L,
               sea_ref_spread=None if not refs else round(max(refs) - min(refs), 4))
    tide_ok = len(refs) >= MIN_SEA_REF and res["sea_ref_spread"] <= 0.02 and L_RANGE[0] <= L <= L_RANGE[1]
    fails = []
    for p in pts:
        v = R.get(p["id"])
        if v is None or not tide_ok:
            continue
        t, why = p["terrain_y"], []
        if abs(v["ground"] - t) > 0.01:
            why.append(f"ground {v['ground']:.3f} != {t:.3f}")
        if p["kind"] == "crest" and abs(v["roadY"] - p["expect_roadway_y"]) > 0.02:
            why.append(f"roadY {v['roadY']:.3f} != {p['expect_roadway_y']:.3f}")
        if p["pond_class"] == "wet":
            if not (v["depth"] > 0 and v["pond"] and abs(v["surface"] - p["plane"]) <= 0.05 and not v["sea"]):
                why.append(f"wet expected at plane {p['plane']}: depth {v['depth']:.3f} pond {v['pond']} surface {v['surface']:.3f} sea {v['sea']}")
        else:
            if p["pond_class"] == "none":
                if v["depth"] > 0 and v["surface"] > L + 0.05:
                    why.append(f"pond-level water {v['surface']:.3f} where none expected")
                if not p["cell_in_footprint"] and v["pond"]:
                    why.append("pond flag outside the footprint")
            if t < L - 0.05:
                if not v["sea"] or abs(v["surface"] - L) > 0.05:
                    why.append(f"sea expected (terrain {t:.3f} < L {L:.3f}): sea {v['sea']} surface {v['surface']:.3f}")
                if t < L - 0.10 and not v["depth"] > 0:
                    why.append(f"sea depth expected > 0, got {v['depth']:.3f}")
            elif t > L + 0.05:
                if v["sea"]:
                    why.append(f"sea flag on terrain {t:.3f} > L {L:.3f}")
                if t > L + 0.10 and p["pond_class"] == "none" and v["depth"] > 0:
                    why.append(f"dry expected, depth {v['depth']:.3f}")
        if why:
            fails.append(dict(id=p["id"], kind=p["kind"], x=p["x"], z=p["z"], pond_class=p["pond_class"], tide_class=p["tide_class"], why=why))
    res.update(tide_determined=tide_ok, failures=fails[:40], n_failures=len(fails),
               by_kind={k: dict(n=sum(p["kind"] == k for p in pts), failed=sum(f["kind"] == k for f in fails))
                        for k in sorted({p["kind"] for p in pts})})
    res["pass"] = bool(tide_ok and not missing and not fails)
    return res


def main():
    a = sys.argv[1:]
    off = 0
    if "--id-offset" in a:
        i = a.index("--id-offset"); off = int(a[i + 1]); a = a[:i] + a[i + 2:]
    pp, logp, outp = a[:3]
    P = json.load(open(pp))
    if P.get("schema") != "dam-probe-points.v2":
        raise SystemExit("eval_dam_probe_v31: refused: points.json is not schema dam-probe-points.v2")
    R, dup, bad = rows(logp, off)
    res = judge(P["points"], R)
    res.update(duplicates=dup[:20], bad_rows=bad[:5], n_bad_rows=len(bad))
    res["pass"] = bool(res["pass"] and not dup and not bad)
    json.dump(res, open(outp, "w", newline="\n"), indent=1)
    print("dam probe", "PASS" if res["pass"] else "FAIL", "L", res["sea_level"], "refs", res["sea_refs"], "missing", res["n_missing"],
          "failures", res["n_failures"], res["by_kind"])
    sys.exit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main()
