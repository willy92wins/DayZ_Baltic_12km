"""Smooth the inland water outlines of a water design along their rings (owner decision 06-10: sigma 12 m, each point
moving at most 4 m, area kept): the contour-v2 lakes copy the 6 m staircase of the V29 raster and the OSM ponds and
river bodies are coarse polygons, so the visible shores keep their corners. Rings are resampled at 1 m, smoothed with
a Gaussian of sigma m with wrap (at most an eighth of the ring's length), the shift capped at max_shift; ring points
within contact_m of another drawn inland body (water_v3, contour lakes, streams of the used tier) stay, and the cap
grows linearly back over the next 10 m, so rivers keep meeting lakes and ponds. Navigable and delta features, the contour river bands, the streams and everything inside the
Narva disc keep the V29 rules.
Usage: smooth_water_outlines_v30.py --design IN_DIR --out OUT_DIR [--contour PATH] [--sigma 12] [--max-shift 4]
       [--narva-radius 600] [--contact-m 2.0]
       smooth_water_outlines_v30.py --selftest"""
import argparse
import hashlib
import json
import os
import shutil
import tempfile

import numpy as np
import shapely
from scipy.ndimage import distance_transform_edt, gaussian_filter1d
from shapely.geometry import LinearRing, Point, Polygon, box, mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

from water_common import EV, save_geojson

NARVA_CENTER = (2417.1428225906, 6889.8850822322)      # Narva keeps the V29 rules inside this disc
STREAM_TIER = 2500                                      # streams build_v30_water.py draws
COPIED = ("streams_candidates.geojson", "profiles.npz", "navigable.geojson",
          "navigable_report.json", "navigable_samples.npz", "water_v3_summary.json")


def keep_polygons(geom):
    """Polygonal parts over 1 m2; a MultiPolygon stays multi."""
    parts = [g for g in getattr(geom, "geoms", [geom]) if g.geom_type == "Polygon" and g.area > 1.0]
    if not parts:
        return Polygon()
    return parts[0] if len(parts) == 1 else shapely.MultiPolygon(parts)


def smooth_ring(coords, sigma, max_shift, others, contact_m):
    """Resample a closed ring at 1 m, Gaussian of sigma m with wrap (at most an eighth of the ring's length), the
    shift capped at max_shift; points within contact_m of another body stay, and the cap grows linearly back over
    the next 10 m along the ring."""
    ring = LinearRing(coords)
    L = ring.length
    n = max(int(L // 1.0), 8)
    spacing = L / n
    d = np.linspace(0, L, n, endpoint=False)
    p = np.array([ring.interpolate(v).coords[0] for v in d])
    s = min(sigma, L / 8.0)                             # small rings: at most an eighth of their length
    q = np.column_stack([gaussian_filter1d(p[:, 0], s, mode="wrap"),
                         gaussian_filter1d(p[:, 1], s, mode="wrap")])
    cap = np.full(n, float(max_shift))
    if others is not None and not others.is_empty:
        near = shapely.distance(shapely.points(p), others) <= contact_m
        if near.any():                                  # pinned points, the cap ramps back over 10 m of ring
            # index distance to the nearest pinned point along the closed ring (three copies for the wrap)
            arc = distance_transform_edt(~np.tile(near, 3))[n:2 * n] * spacing
            cap = max_shift * np.clip(arc / 10.0, 0.0, 1.0)
    dv = q - p
    m = np.linalg.norm(dv, axis=1)
    over = m > cap
    if over.any():
        f = cap[over] / np.maximum(m[over], 1e-12)
        q[over] = p[over] + dv[over] * f[:, None]
    return q, np.minimum(m, cap)


def smooth_polygon(poly, sigma, max_shift, others, contact_m):
    """One polygon: exterior and big holes smoothed, islands under 200 m2 kept, area restored with one offset
    of (A0 - A1) / perimeter, twice. Returns the result and the per-ring-point applied shifts."""
    ext, shifts = smooth_ring(poly.exterior.coords, sigma, max_shift, others, contact_m)
    holes = []
    for r in poly.interiors:
        if Polygon(r).area < 200:                       # tiny islands stay
            holes.append(np.asarray(r.coords))
            continue
        h, s = smooth_ring(r.coords, sigma, max_shift, others, contact_m)
        holes.append(h)
        shifts = np.concatenate([shifts, s])
    out = keep_polygons(make_valid(Polygon(ext, holes)))
    area0 = poly.area
    for _ in range(2):                                  # keep the area: one offset, twice
        da = area0 - out.area
        if abs(da) < 1e-9 or out.is_empty or out.length <= 0:
            break
        out = keep_polygons(make_valid(out.buffer(da / out.length, join_style=1)))  # 1 == round
        if out.is_empty:
            break
    return out, shifts


def smooth_feature(geom, sigma, max_shift, others, contact_m):
    """Smooth every polygon part of a feature; if the result is empty or its area differs by more than 15 %,
    retry with half the max shift, then keep the original. Returns (geom, shifts, fallback)."""
    polys = [p for p in getattr(geom, "geoms", [geom]) if p.geom_type == "Polygon"]
    if not polys:
        return geom, np.zeros(1), False
    area0 = geom.area
    fallback = False
    for ms in (max_shift, max_shift / 2.0):
        flat, shifts = [], []
        for p in polys:
            sp, s = smooth_polygon(p, sigma, ms, others, contact_m)
            shifts.append(s)
            flat.extend(list(sp.geoms) if sp.geom_type == "MultiPolygon" else [sp])
        if not flat:
            result = shapely.MultiPolygon()
        elif len(flat) == 1:
            result = flat[0]
        else:
            result = shapely.MultiPolygon(flat)
        if not result.is_empty and abs(result.area - area0) <= 0.15 * max(area0, 1e-9):
            return result, np.concatenate(shifts), fallback
        fallback = True
    return geom, np.zeros(1), fallback                  # both attempts broke: keep as it is


def strict_smooth_feature(geom, sigma, max_shift, others, contact_m):
    """Bound the FINAL outline; retain every island and original water contact.

    Area buffering can erase holes and move pinned points. This mode instead
    attenuates the ring displacement at fixed factors, preserving a feature
    exactly when its constraints cannot all be met. The legacy mode remains
    available to reproduce already built candidates.
    """
    parts = list(getattr(geom, "geoms", [geom]))
    if not geom.is_valid or any(p.geom_type != "Polygon" for p in parts):
        return geom, np.zeros(1), True
    contact_guard = (others.buffer(contact_m + 1.0) if others is not None
                     and not others.is_empty else None)
    candidates, shifts = [], []
    fallback = False
    for poly in parts:
        ring = poly.exterior
        n = max(int(ring.length // 1.0), 8)
        original = np.array([ring.interpolate(v).coords[0]
                             for v in np.linspace(0, ring.length, n, endpoint=False)])
        target, _ = smooth_ring(ring.coords, sigma, max_shift, others, contact_m)
        chosen = None
        for alpha in (1.0, 0.5, 0.25):
            exterior = original + alpha * (target - original)
            proposal = Polygon(exterior, [r.coords for r in poly.interiors])
            if not proposal.is_valid:
                continue
            if contact_guard is not None:
                proposal = proposal.difference(contact_guard).union(poly.intersection(contact_guard))
            if proposal.geom_type != "Polygon" or not proposal.is_valid:
                continue
            if len(proposal.interiors) != len(poly.interiors):
                continue
            if not all(any(Polygon(a).equals(Polygon(b)) for b in proposal.interiors)
                       for a in poly.interiors):
                continue
            if abs(proposal.area - poly.area) > 0.02 * poly.area:
                continue
            # These buffers are inscribed approximations: covers is conservative
            # for the continuous curves, not only sampled or pre-offset points.
            if not poly.boundary.buffer(max_shift, quad_segs=32).covers(proposal.boundary):
                continue
            if not proposal.boundary.buffer(max_shift, quad_segs=32).covers(poly.boundary):
                continue
            chosen = proposal
            shifts.append(np.linalg.norm(exterior - original, axis=1))
            fallback |= alpha < 1.0
            break
        if chosen is None:
            chosen = poly
            shifts.append(np.zeros(1))
            fallback = True
        candidates.append(chosen)
    result = candidates[0] if len(candidates) == 1 else shapely.MultiPolygon(candidates)
    if not result.is_valid:
        return geom, np.zeros(1), True
    return result, np.concatenate(shifts), fallback


def turning(geom):
    """Angles (degrees) at 6 m chords along every ring, the prototype's corner measure."""
    vals = []
    for poly in getattr(geom, "geoms", [geom]):
        if poly.geom_type != "Polygon":
            continue
        for ring in [poly.exterior] + list(poly.interiors):
            n = int(ring.length // 2.0)
            if n < 8:
                continue
            p = np.array([ring.interpolate(v).coords[0] for v in np.arange(n) * 2.0])
            a = p - np.roll(p, 3, axis=0)
            b = np.roll(p, -3, axis=0) - p
            c = (a * b).sum(1) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-9)
            vals.append(np.degrees(np.arccos(np.clip(c, -1, 1))))
    return np.concatenate(vals) if vals else np.array([0.0])


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(design, out, contour_path, sigma, max_shift, narva_radius, contact_m, strict_limits=False):
    if os.path.exists(out):
        raise SystemExit(f"output directory already exists: {out}")
    os.makedirs(out)
    with open(os.path.join(design, "water_v3.geojson"), encoding="utf-8") as f:
        wv = json.load(f)
    with open(contour_path, encoding="utf-8") as f:
        contour = json.load(f)
    with open(os.path.join(design, "streams_candidates.geojson"), encoding="utf-8") as f:
        streams = json.load(f)

    narva = Point(*NARVA_CENTER).buffer(narva_radius)
    wv_geoms = [shape(f["geometry"]) for f in wv["features"]]
    contour_geoms = [shape(f["geometry"]) for f in contour["features"]]
    stream_geoms = [shape(f["geometry"]) for f in streams["features"]]
    # contacts: the water the builder draws (build_v30_water.py): every water_v3 body, the contour LAKES and the
    # streams of the used tier. The contour river bands only carry the V29 levels of the navigable reaches; they lie
    # along whole rivers and would pin every river point.
    lake_idx = [j for j, f in enumerate(contour["features"]) if f["properties"].get("body", "").startswith("lake")]
    used_streams = [k for k, f in enumerate(streams["features"]) if f["properties"].get("tier_m", 0) >= STREAM_TIER]
    keys = ([("wv", i) for i in range(len(wv_geoms))] + [("contour", j) for j in lake_idx]
            + [("streams", k) for k in used_streams])
    all_geoms = wv_geoms + [contour_geoms[j] for j in lake_idx] + [stream_geoms[k] for k in used_streams]

    tree = shapely.STRtree(all_geoms)
    index_of = {k: i for i, k in enumerate(keys)}

    def others_of(key, geom):
        # every drawn inland body near this feature except the feature itself (only those within contact_m of it can
        # pin a point)
        i = index_of[key]
        near = [all_geoms[j] for j in tree.query(geom.buffer(contact_m + 1.0)) if j != i]
        return unary_union(near) if near else None

    stats = {k: {"features": 0, "smoothed": 0, "unchanged_narva": 0, "fallbacks": 0,
                 "shifts": [], "dA": [], "tb": [], "ta": []} for k in ("lake", "pond", "river")}

    def smooth_one(geom, key, kind):
        """Smooth one feature in place of the stats dict; returns the new geometry or None when unchanged."""
        st = stats[kind]
        st["features"] += 1
        if geom.intersects(narva):                      # Narva keeps the V29 rules
            st["unchanged_narva"] += 1
            return None
        builder = strict_smooth_feature if strict_limits else smooth_feature
        new_g, shifts, fallback = builder(geom, sigma, max_shift, others_of(key, geom), contact_m)
        st["smoothed"] += 1
        st["fallbacks"] += int(fallback)
        st["shifts"].append(shifts)
        st["tb"].append(turning(geom))
        st["ta"].append(turning(new_g))
        st["dA"].append((new_g.area - geom.area) / max(geom.area, 1.0))
        return new_g

    out_wv = []
    for i, feat in enumerate(wv["features"]):
        g = wv_geoms[i]
        cls = feat["properties"].get("class", "")
        if cls not in ("river", "pond"):                # navigable and delta_* stay
            out_wv.append((g, feat["properties"]))
            continue
        new_g = smooth_one(g, ("wv", i), cls)
        out_wv.append((g if new_g is None else new_g, feat["properties"]))
    save_geojson(os.path.join(out, "water_v3.geojson"), out_wv)

    for j, feat in enumerate(contour["features"]):
        if not feat["properties"].get("body", "").startswith("lake"):
            continue                                    # the contour river bands stay
        new_g = smooth_one(contour_geoms[j], ("contour", j), "lake")
        if new_g is not None:
            feat["geometry"] = mapping(new_g)
    with open(os.path.join(out, "contour_lakes.geojson"), "wb") as f:
        f.write(json.dumps(contour, ensure_ascii=False).encode("utf-8"))

    for name in COPIED:                                 # byte copies
        shutil.copyfile(os.path.join(design, name), os.path.join(out, name))

    kinds = {}
    for k, st in stats.items():
        shifts = np.concatenate(st["shifts"]) if st["shifts"] else np.zeros(1)
        dA = np.array(st["dA"]) if st["dA"] else np.zeros(1)
        tb = np.concatenate(st["tb"]) if st["tb"] else np.zeros(1)
        ta = np.concatenate(st["ta"]) if st["ta"] else np.zeros(1)
        kinds[k] = {"features": st["features"], "smoothed": st["smoothed"],
                    "unchanged_narva": st["unchanged_narva"], "fallbacks": st["fallbacks"],
                    "shift_p50_p95": [round(float(np.percentile(shifts, q)), 2) for q in (50, 95)],
                    "area_change_p5_p95_pct": [round(float(np.percentile(dA, q)) * 100, 2) for q in (5, 95)],
                    "turn_gt45_before": round(float((tb > 45).mean()), 3),
                    "turn_gt45_after": round(float((ta > 45).mean()), 3),
                    "turn_gt30_before": round(float((tb > 30).mean()), 3),
                    "turn_gt30_after": round(float((ta > 30).mean()), 3)}
    rep = {"params": {"design": os.path.abspath(design), "contour": os.path.abspath(contour_path),
                      "sigma_m": sigma, "max_shift_m": max_shift, "contact_m": contact_m,
                      "strict_final_limits": strict_limits,
                      "narva_center": list(NARVA_CENTER), "narva_radius_m": narva_radius},
           "input_sha256": {"water_v3.geojson": sha256(os.path.join(design, "water_v3.geojson")),
                            "contour": sha256(contour_path),
                            "streams_candidates.geojson": sha256(os.path.join(design, "streams_candidates.geojson"))},
           "kinds": kinds}
    with open(os.path.join(out, "smoothing_report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(kinds, indent=1))


def selftest():
    tmp = tempfile.mkdtemp(prefix="smooth_water_selftest_")
    design = os.path.join(tmp, "design")
    out = os.path.join(tmp, "out")
    contour = os.path.join(design, "contour.geojson")
    os.makedirs(design)
    try:
        cells = []
        for i in range(10):                             # a 6 m staircase blob: a diagonal band of grid cells
            cells.append(box(6 * i, 6 * i, 6 * i + 6, 6 * i + 6))
            cells.append(box(6 * i, 6 * i + 6, 6 * i + 6, 6 * i + 12))
        blob = unary_union(cells)
        sq1 = box(8000.0, 7000.0, 8060.0, 7060.0)       # two ponds that touch along x = 8060
        sq2 = box(8060.0, 7000.0, 8120.0, 7060.0)
        narva_box = box(2300.0, 6800.0, 2500.0, 7000.0)  # well inside the Narva disc
        feats = [(blob, {"class": "river"}), (sq1, {"class": "pond"}),
                 (sq2, {"class": "pond"}), (narva_box, {"class": "river"})]
        save_geojson(os.path.join(design, "water_v3.geojson"), feats)
        lake = box(10000.0, 10000.0, 10120.0, 10120.0)  # far from everything, so the blob smooths fully
        with open(contour, "wb") as f:
            f.write(json.dumps({"type": "FeatureCollection", "features": [
                {"type": "Feature", "properties": {"body": "lake_001", "level_m": 0.0},
                 "geometry": mapping(lake)}]}, ensure_ascii=False).encode("utf-8"))
        with open(os.path.join(design, "streams_candidates.geojson"), "wb") as f:
            f.write(json.dumps({"type": "FeatureCollection", "features": []}).encode("utf-8"))
        for name in COPIED[1:]:                         # dummy side files for the byte copies
            with open(os.path.join(design, name), "wb") as f:
                f.write(b"selftest " + name.encode("utf-8"))

        run(design, out, contour, 12.0, 4.0, 600.0, 2.0)

        with open(os.path.join(design, "water_v3.geojson"), encoding="utf-8") as f:
            src = json.load(f)["features"]
        with open(os.path.join(out, "water_v3.geojson"), encoding="utf-8") as f:
            res = json.load(f)["features"]
        assert [f["properties"]["class"] for f in res] == [f["properties"]["class"] for f in src], "order changed"

        got = shape(res[0]["geometry"])                 # the staircase blob: fewer hard corners, area kept
        tb, ta = turning(blob), turning(got)
        assert (tb > 45).mean() > 0.1 and (ta > 45).mean() < (tb > 45).mean(), "turning share did not drop"
        assert abs(got.area - blob.area) / blob.area < 0.02, "staircase area not kept"

        assert shape(res[1]["geometry"]).distance(shape(res[2]["geometry"])) == 0.0, "the touching ponds separated"

        assert res[3]["geometry"] == src[3]["geometry"], "the Narva feature changed"

        for name in COPIED:
            with open(os.path.join(design, name), "rb") as f:
                a = f.read()
            with open(os.path.join(out, name), "rb") as f:
                b = f.read()
            assert a == b, f"{name} copy differs"
        print("SELFTEST PASS")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--design", help="input design directory")
    ap.add_argument("--out", help="output directory (must not exist)")
    ap.add_argument("--contour", default=os.path.join(EV, "water-surfaces-contour-v2.geojson"))
    ap.add_argument("--sigma", type=float, default=12.0)
    ap.add_argument("--max-shift", type=float, default=4.0)
    ap.add_argument("--narva-radius", type=float, default=600.0)
    ap.add_argument("--contact-m", type=float, default=2.0)
    ap.add_argument("--strict-outline-limits", action="store_true",
                    help="Bound final outlines to max-shift; preserve islands/contacts; area within 2 percent")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return
    if not a.design or not a.out:
        ap.error("--design and --out are required")
    run(a.design, a.out, a.contour, a.sigma, a.max_shift, a.narva_radius, a.contact_m, a.strict_outline_limits)


if __name__ == "__main__":
    main()
