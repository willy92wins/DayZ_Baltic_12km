#!/usr/bin/env python3.11
"""Classify every standing water body of a DayZ terrain grid by connectivity.

For each body of the census (cls 2/7, per rounded cm level, 8-connected,
>= 4 vertices; the labelling is rebuilt here and cross-checked against
census_perched_water_v30.find_bodies) the tool determines:

- members: contour lakes (properties.body starts with "lake") and design ponds
  (properties.class == "pond") that contain at least one body vertex;
- raster contacts: vertices 8-adjacent to the body, not in it, with cls > 0,
  grouped by neighbour kind (sea/delta/navigable/river/stream/standing) with
  the level difference body level - neighbour level and the other body ids;
- design connection: the union of the member polygons (or the vertex convex
  hull buffered by 3 m) buffered by 3 m intersects a navigable/river/delta
  polygon, a used stream polygon (tier_m >= 2500) or the extra channel, or a
  profile first/last sample lies within 9 m of it;
- category (first match): moat (member lake_093/lake_096/lake_099) > big
  (area_m2 >= --big-area) > connected > accidental (raster contact, not
  design-connected) > isolated;
- action: moat -> exception_owner_decision (level kept); big -> decide_apart
  (level kept); perched_m < --perched-min -> keep; connected ->
  lower_with_river (proposed level null; contact_flowing_level_max reported);
  isolated or accidental with dike_m > --dike-lower -> lower_to_ring with
  proposed = round(min(level_m, ring_p25_m - --ring-margin), 2); else review.
  Accidental bodies also get separate=true and separate_vertices = number of
  their non-standing raster contact vertices.  Every body reports ring p10
  and p50 of the census ring (EDT in metres, (ring_in, ring_out] on land) and
  dike_after_est_m = max(0, proposed + 0.35 - ring_p10) for a finite proposed
  level.

CLI:
    python classify_perched_water_v30.py --terrain T.npz --out OUTDIR
        [--root R] [--channel "x,z;x,z;..." --channel-width W] [--big-area A]
        [--perched-min P] [--dike-lower D] [--ring-margin M]
        [--ring-in 12] [--ring-out 36]
    python classify_perched_water_v30.py --selftest --out OUTDIR

Outputs (OUTDIR must not exist): classification.json, classification.csv,
map.png.

Written by GLM-5.3-Flash (GX10 lane G, 04-10). Receiver changes (Claude, 04-10): the body level table is sized by
the number of bodies (a last body without contacts raised IndexError), design polygons without an id take their
name or class (the delta ones read 'None'), each body records rep_xz (its vertex nearest the centroid, to find it
again on another terrain), and the self-test compares float32 levels with a 1e-4 tolerance and accepts NaN where
the JSON writes null.
"""

import argparse
import csv
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage

from shapely import contains_xy, distance as sh_distance, points as sh_points
from shapely.geometry import LineString, MultiPoint, box, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import census_perched_water_v30 as cen

DEFAULT_ROOT = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
NARVA_BRIDGE_XZ = (2417.1428225906, 6889.8850822322)  # bridge centre, reference only
MOAT_LAKES = ("lake_093", "lake_096", "lake_099")     # owner decision 04-10

# cls code -> contact slot (cls 2 and 7 share the "standing" slot)
KIND_SLOT = np.zeros(8, dtype=np.int64)
KIND_SLOT[1], KIND_SLOT[2], KIND_SLOT[3] = 1, 2, 3
KIND_SLOT[4], KIND_SLOT[5], KIND_SLOT[6], KIND_SLOT[7] = 4, 5, 6, 2
SLOT_NAME = ("", "sea", "standing", "navigable", "delta", "river", "stream")
SLOT_ORDER = (1, 4, 3, 5, 6, 2)  # sea, delta, navigable, river, stream, standing
FLOW_SLOTS = (3, 5, 6)           # navigable, river, stream
STANDING_SLOT = 2

CATEGORY_ORDER = ("moat", "big", "connected", "accidental", "isolated")
CATEGORY_CODE = {name: i + 1 for i, name in enumerate(CATEGORY_ORDER)}

CSV_COLS = (
    "id", "class", "vertices", "area_m2", "level_m", "centroid_x", "centroid_z",
    "perched_m", "dike_m", "ring_p10_m", "ring_p25_m", "ring_median_m",
    "member_lakes", "member_ponds", "contacts", "connected_to", "category",
    "action", "proposed_level_m", "level_change_m", "separate",
    "separate_vertices", "contact_flowing_level_max", "dike_after_est_m",
)


# ----------------------------------------------------------------------------
# Body raster (exact replica of the cen.find_bodies labelling loop)
# ----------------------------------------------------------------------------

def build_body_raster(cls, level):
    """Replicate cen.find_bodies' loop: per rounded cm level, STRUCT8 labels,
    >= MIN_VERTICES, ids 1..n in loop order.  Returns (raster int32, segs)."""
    cls = np.asarray(cls)
    level = np.asarray(level)
    standing = (cls == 2) | (cls == 7)
    rounded = np.round(level.astype(np.float64) * 100.0) / 100.0
    body_id_r = np.zeros(cls.shape, dtype=np.int32)
    segs = []
    bid = 0
    for lvl in np.unique(rounded[standing]):
        mask = standing & (rounded == lvl)
        labels, n = ndimage.label(mask, structure=cen.STRUCT8)
        if n == 0:
            continue
        counts = np.bincount(labels.ravel())
        for i in range(1, n + 1):
            if counts[i] < cen.MIN_VERTICES:
                continue
            rr, cc = np.nonzero(labels == i)
            bid += 1
            body_id_r[rr, cc] = bid
            segs.append((rr, cc))
    return body_id_r, segs


# ----------------------------------------------------------------------------
# Raster contacts (vectorised over the 8 neighbour offsets)
# ----------------------------------------------------------------------------

def raster_contacts(cls, level, body_id_r, body_levels):
    """Per body: dict slot -> {count, ids, levels, diff} for 8-adjacent
    vertices outside the body with cls > 0.  Each contact vertex is counted
    once per body regardless of how many body vertices touch it."""
    H, W = cls.shape
    bid = body_id_r
    offs = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
    owners, kinds, lvls, nbrs, flats = [], [], [], [], []
    for dr, dc in offs:
        ra0, ra1 = max(0, -dr), H - max(0, dr)
        ca0, ca1 = max(0, -dc), W - max(0, dc)
        if ra1 <= ra0 or ca1 <= ca0:
            continue
        wA = ca1 - ca0
        A = bid[ra0:ra1, ca0:ca1]
        Bc = cls[ra0 + dr:ra1 + dr, ca0 + dc:ca1 + dc]
        Bl = level[ra0 + dr:ra1 + dr, ca0 + dc:ca1 + dc]
        Bb = bid[ra0 + dr:ra1 + dr, ca0 + dc:ca1 + dc]
        m = (A > 0) & (Bc > 0) & (Bb != A)
        if not m.any():
            continue
        loc = np.flatnonzero(m)
        r = loc // wA + ra0
        c = loc % wA + ca0
        owners.append(A[m])
        kinds.append(Bc[m])
        lvls.append(Bl[m])
        nbrs.append(Bb[m])
        flats.append((r + dr) * W + (c + dc))
    out = {}
    if not owners:
        return out
    owner = np.concatenate(owners).astype(np.int64)
    slot = KIND_SLOT[np.concatenate(kinds).astype(np.int64)]
    lvl = np.concatenate(lvls).astype(np.float64)
    nbr = np.concatenate(nbrs)
    flat = np.concatenate(flats)
    # one record per (body, contact vertex)
    _, first = np.unique(owner * (H * W) + flat, return_index=True)
    owner, slot, lvl, nbr = owner[first], slot[first], lvl[first], nbr[first]
    lvl_of = np.full(max(int(owner.max()), len(body_levels)) + 1, np.nan)
    for b, L in enumerate(body_levels, start=1):
        lvl_of[b] = L
    gkey = owner * 10 + slot
    order = np.argsort(gkey, kind="stable")
    gk = gkey[order]
    uniq, starts = np.unique(gk, return_index=True)
    bounds = np.append(starts, gk.size)
    for gi in range(uniq.size):
        sel = order[bounds[gi]:bounds[gi + 1]]
        b = int(uniq[gi] // 10)
        s = int(uniq[gi] % 10)
        lv = lvl[sel]
        ok = np.isfinite(lv)
        diff = None
        if ok.any():
            d = lvl_of[b] - lv[ok]
            diff = (float(np.min(d)), float(np.median(d)), float(np.max(d)))
        ids = sorted(int(v) for v in np.unique(nbr[sel]) if v > 0)
        out.setdefault(b, {})[s] = {
            "count": int(sel.size), "ids": ids, "levels": lv[ok], "diff": diff,
        }
    return out


def contacts_json(con_b):
    """Contacts of one body as a JSON-ready dict keyed by kind name."""
    j = {}
    for s in SLOT_ORDER:
        r = con_b.get(s)
        if r is None:
            continue
        entry = {"vertices": r["count"], "body_ids": r["ids"]}
        if r["diff"] is None:
            entry["level_diff_m"] = None
        else:
            mn, md, mx = r["diff"]
            entry["level_diff_m"] = {"min": mn, "median": md, "max": mx}
        j[SLOT_NAME[s]] = entry
    return j


# ----------------------------------------------------------------------------
# Geometry helpers
# ----------------------------------------------------------------------------

def collect_members(tree, geoms, names, x, z, found, out_geoms):
    """Add member polygons that contain at least one of the body vertices."""
    if tree is None:
        return
    env = box(float(x.min()) - 1.0, float(z.min()) - 1.0,
              float(x.max()) + 1.0, float(z.max()) + 1.0)
    for i in tree.query(env):
        if contains_xy(geoms[i], x, z).any():
            found.add(names[i])
            out_geoms.append(geoms[i])


def ring_p10(rr, cc, heights, cls, ring_in, ring_out, vertex_m):
    """p10 of the census ring: land vertices with EDT distance from the body
    in (ring_in, ring_out], computed on a padded window exactly as in
    cen._body_stats."""
    rr = np.asarray(rr)
    cc = np.asarray(cc)
    pad_v = int(math.ceil(ring_out / vertex_m)) + 2
    H, W = cls.shape
    r0 = max(0, int(rr.min()) - pad_v)
    r1 = min(H, int(rr.max()) + 1 + pad_v)
    c0 = max(0, int(cc.min()) - pad_v)
    c1 = min(W, int(cc.max()) + 1 + pad_v)
    B_win = np.zeros((r1 - r0, c1 - c0), dtype=bool)
    B_win[rr - r0, cc - c0] = True
    dist = ndimage.distance_transform_edt(~B_win, sampling=vertex_m)
    ring = (cls[r0:r1, c0:c1] == 0) & (dist > ring_in) & (dist <= ring_out)
    h = heights[r0:r1, c0:c1].astype(np.float64)[ring]
    if h.size == 0:
        return float("nan")
    return float(np.percentile(h, 10))


# ----------------------------------------------------------------------------
# Classification core (shared by the real run and the self-test)
# ----------------------------------------------------------------------------

def _fin(v):
    return v is not None and math.isfinite(v)


def classify(heights, cls, level, layers, params):
    """Run the whole classification.  Returns (records, body_id_raster)."""
    vertex_m = float(params["vertex_m"])
    z0 = float(params["z0"])

    bodies, _ = cen.find_bodies(cls, heights, level, params["ring_in"],
                                params["ring_out"], params["perched_min"], 0.50)
    body_id_r, segs = build_body_raster(cls, level)
    if len(bodies) != len(segs):
        raise SystemExit("body labelling mismatch: census %d vs raster %d"
                         % (len(bodies), len(segs)))
    for i, s in enumerate(bodies):
        if int(segs[i][0].size) != int(s["vertices"]):
            raise SystemExit("body %d vertex mismatch: raster %d vs census %d"
                             % (i + 1, segs[i][0].size, s["vertices"]))
    n = len(bodies)
    print("bodies: %d" % n)

    con = raster_contacts(cls, level, body_id_r, [float(s["level_m"]) for s in bodies])

    lake_names = [nm for nm, _ in layers["lakes"]]
    lake_geoms = [g for _, g in layers["lakes"]]
    pond_names = [nm for nm, _ in layers["ponds"]]
    pond_geoms = [g for _, g in layers["ponds"]]
    flow_ids = [nm for nm, _ in layers["flowing"]]
    flow_geoms = [g for _, g in layers["flowing"]]
    stream_ids = [nm for nm, _ in layers["streams"]]
    stream_geoms = [g for _, g in layers["streams"]]
    lake_tree = STRtree(lake_geoms) if lake_geoms else None
    pond_tree = STRtree(pond_geoms) if pond_geoms else None
    flow_tree = STRtree(flow_geoms) if flow_geoms else None
    stream_tree = STRtree(stream_geoms) if stream_geoms else None
    ex, ez, ep = layers["profile_ends"]
    end_pts = (sh_points(np.column_stack([np.asarray(ex, dtype=np.float64),
                                          np.asarray(ez, dtype=np.float64)]))
               if len(ex) else None)

    records = []
    for i in range(n):
        s = bodies[i]
        bid = i + 1
        rr, cc = segs[i]
        x = vertex_m * cc.astype(np.float64)
        z = z0 - vertex_m * rr.astype(np.float64)

        # rule 1: members
        member_lakes, member_ponds, member_geoms = set(), set(), []
        collect_members(lake_tree, lake_geoms, lake_names, x, z,
                        member_lakes, member_geoms)
        collect_members(pond_tree, pond_geoms, pond_names, x, z,
                        member_ponds, member_geoms)

        # rule 3: design connection
        if member_geoms:
            M = unary_union(member_geoms)
        else:
            M = MultiPoint(np.column_stack([x, z])).convex_hull.buffer(3.0)
        Mb = M.buffer(3.0)
        connected_to = set()
        if flow_tree is not None:
            for j in flow_tree.query(Mb, predicate="intersects"):
                connected_to.add(flow_ids[j])
        if stream_tree is not None:
            for j in stream_tree.query(Mb, predicate="intersects"):
                connected_to.add(stream_ids[j])
        if end_pts is not None:
            d = sh_distance(M, end_pts)
            for pid, dd in zip(ep, d):
                if dd <= 9.0:
                    connected_to.add(pid)

        # rule 2 contacts (already computed globally)
        con_b = con.get(bid, {})

        # rule 4: category, first match
        if any(nm in MOAT_LAKES for nm in member_lakes):
            cat = "moat"
        elif float(s["area_m2"]) >= params["big_area"]:
            cat = "big"
        elif connected_to:
            cat = "connected"
        elif con_b:
            cat = "accidental"
        else:
            cat = "isolated"

        # rule 5: action and proposed level
        L = float(s["level_m"])
        perched_eff = float(s["perched_m"]) if _fin(s["perched_m"]) else 0.0
        dike_eff = float(s["dike_m"]) if _fin(s["dike_m"]) else 0.0
        if cat == "moat":
            action, prop = "exception_owner_decision", L
        elif cat == "big":
            action, prop = "decide_apart", L
        elif perched_eff < params["perched_min"]:
            action, prop = "keep", L
        elif cat == "connected":
            action, prop = "lower_with_river", float("nan")
        elif cat in ("isolated", "accidental") and dike_eff > params["dike_lower"]:
            rp = float(s["ring_p25_m"]) if _fin(s["ring_p25_m"]) else L
            action = "lower_to_ring"
            prop = round(min(L, rp - params["ring_margin"]), 2)
        else:
            action, prop = "review", L

        flow_max = float("nan")
        if cat == "connected":
            for sl in FLOW_SLOTS:
                r = con_b.get(sl)
                if r is not None and r["levels"].size:
                    flow_max = max(flow_max, float(np.max(r["levels"])))

        sep_v = 0
        if cat == "accidental":
            sep_v = sum(r["count"] for sl, r in con_b.items() if sl != STANDING_SLOT)

        p10 = ring_p10(rr, cc, heights, cls, params["ring_in"],
                       params["ring_out"], vertex_m)
        dike_after = float("nan")
        if math.isfinite(prop) and math.isfinite(p10):
            dike_after = max(0.0, prop + 0.35 - p10)

        k_rep = int(np.argmin((x - float(s["cx"])) ** 2 + (z - float(s["cz"])) ** 2))
        records.append({
            "id": bid,
            "class": s["class"],
            "vertices": int(s["vertices"]),
            "area_m2": float(s["area_m2"]),
            "level_m": L,
            "centroid_xz": [float(s["cx"]), float(s["cz"])],
            "rep_xz": [float(x[k_rep]), float(z[k_rep])],   # the body vertex nearest the centroid
            "perched_m": float(s["perched_m"]),
            "dike_m": float(s["dike_m"]),
            "ring_p10_m": p10,
            "ring_p25_m": (float(s["ring_p25_m"])
                           if s["ring_p25_m"] is not None else float("nan")),
            "ring_median_m": (float(s["ring_median_m"])
                              if s["ring_median_m"] is not None else float("nan")),
            "member_lakes": sorted(member_lakes),
            "member_ponds": sorted(member_ponds),
            "contacts": contacts_json(con_b),
            "connected_to": sorted(connected_to),
            "category": cat,
            "action": action,
            "proposed_level_m": prop,
            "level_change_m": (prop - L) if math.isfinite(prop) else None,
            "separate": cat == "accidental",
            "separate_vertices": sep_v,
            "contact_flowing_level_max": flow_max,
            "dike_after_est_m": dike_after,
        })
    return records, body_id_r


# ----------------------------------------------------------------------------
# Output helpers
# ----------------------------------------------------------------------------

def py_value(v):
    """JSON-safe conversion; floats rounded to 3 decimals, NaN/inf -> null."""
    if isinstance(v, dict):
        return {k: py_value(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [py_value(x) for x in v]
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        f = float(v)
        return round(f, 3) if math.isfinite(f) else None
    return v


def totals(records):
    cat, act = {}, {}
    for r in records:
        for d, key in ((cat, r["category"]), (act, r["action"])):
            t = d.setdefault(key, {"count": 0, "area_m2": 0.0})
            t["count"] += 1
            t["area_m2"] += float(r["area_m2"])
    for d in (cat, act):
        for t in d.values():
            t["area_m2"] = round(t["area_m2"], 3)
    return {"category": cat, "action": act}


def csv_row(r):
    return {
        "id": r["id"], "class": r["class"], "vertices": r["vertices"],
        "area_m2": r["area_m2"], "level_m": r["level_m"],
        "centroid_x": r["centroid_xz"][0], "centroid_z": r["centroid_xz"][1],
        "perched_m": r["perched_m"], "dike_m": r["dike_m"],
        "ring_p10_m": r["ring_p10_m"], "ring_p25_m": r["ring_p25_m"],
        "ring_median_m": r["ring_median_m"],
        "member_lakes": r["member_lakes"], "member_ponds": r["member_ponds"],
        "contacts": r["contacts"], "connected_to": r["connected_to"],
        "category": r["category"], "action": r["action"],
        "proposed_level_m": r["proposed_level_m"],
        "level_change_m": r["level_change_m"],
        "separate": r["separate"], "separate_vertices": r["separate_vertices"],
        "contact_flowing_level_max": r["contact_flowing_level_max"],
        "dike_after_est_m": r["dike_after_est_m"],
    }


def csv_cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return "" if not math.isfinite(v) else "%.3f" % v
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, dict):
        return ";".join("%s:%d" % (k, d["vertices"]) for k, d in sorted(v.items()))
    if isinstance(v, (list, tuple)):
        return ";".join(str(x) for x in v)
    return str(v)


def write_map(heights, cls, body_id_r, records, path, vertex_m, z0):
    k = 4
    n = len(records)
    cat_lookup = np.zeros(n + 1, np.uint8)
    lr_lookup = np.zeros(n + 1, np.uint8)
    for r in records:
        cat_lookup[r["id"]] = CATEGORY_CODE[r["category"]]
        if r["action"] == "lower_to_ring":
            lr_lookup[r["id"]] = 1
    cat_s = cat_lookup[body_id_r][::k, ::k]
    lr_s = lr_lookup[body_id_r][::k, ::k]
    hm = np.where(cls == 0, heights.astype(np.float64), np.nan)[::k, ::k]
    colours = np.array([
        [0.00, 0.00, 0.00, 0.00],
        [0.48, 0.18, 0.55, 0.90],   # moat
        [0.84, 0.15, 0.16, 0.90],   # big
        [0.12, 0.47, 0.71, 0.90],   # connected
        [1.00, 0.62, 0.00, 0.90],   # accidental
        [0.17, 0.63, 0.17, 0.90],   # isolated
    ])
    rgb = colours[cat_s][..., :3].copy()
    alpha = colours[cat_s][..., 3:]
    mask_lr = lr_s != 0
    rgb[mask_lr] = (rgb[mask_lr] * 0.4 + 0.6)  # brighten lower_to_ring bodies
    rgba = np.concatenate([rgb, alpha], axis=-1)
    fig, ax = plt.subplots(figsize=(12, 12), dpi=100)
    ax.imshow(np.ma.masked_invalid(hm), cmap="Greys", interpolation="nearest")
    ax.imshow(rgba, interpolation="nearest")
    handles = [Patch(facecolor=colours[i][:3], label=name)
               for i, name in enumerate(CATEGORY_ORDER, start=1)]
    handles.append(Patch(facecolor="white", edgecolor="black",
                         label="bright = lower_to_ring"))
    ax.legend(handles=handles, loc="upper right", fontsize=8)
    ax.set_title("standing water classification, %d bodies "
                 "(vertex %.0f m, downsampled x4)" % (n, vertex_m))
    ax.set_xlabel("column c (x = %.0f c)" % vertex_m)
    ax.set_ylabel("row r (z = %.0f - %.0f r)" % (z0, vertex_m))
    fig.savefig(path)
    plt.close(fig)


def write_outputs(out_dir, records, inputs, params, heights, cls, body_id_r):
    os.makedirs(out_dir)
    doc = {
        "inputs": py_value(inputs),
        "params": py_value(params),
        "totals": py_value(totals(records)),
        "bodies": [py_value(r) for r in records],
    }
    with open(os.path.join(out_dir, "classification.json"), "w",
              encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    with open(os.path.join(out_dir, "classification.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_COLS)
        for r in records:
            row = py_value(csv_row(r))
            w.writerow([csv_cell(row[c]) for c in CSV_COLS])
    write_map(heights, cls, body_id_r, records,
              os.path.join(out_dir, "map.png"),
              float(params["vertex_m"]), float(params["z0"]))
    print("outputs written to %s" % out_dir)


# ----------------------------------------------------------------------------
# Design layer loading
# ----------------------------------------------------------------------------

def load_geojson(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_channel(text):
    pts = []
    for tok in text.split(";"):
        part = tok.split(",")
        if len(part) != 2:
            raise SystemExit("bad --channel point: %r" % tok)
        pts.append((float(part[0]), float(part[1])))
    if len(pts) < 2:
        raise SystemExit("--channel needs at least two x,z points")
    return np.array(pts, dtype=np.float64)


def build_layers(root, channel, channel_width):
    """Load the design layers; returns (layers, inputs)."""
    paths = {
        "contour_lakes": os.path.join(root, "evidence", "regional-foundation-v1",
                                      "water-surfaces-contour-v2.geojson"),
        "water_design": os.path.join(root, "tests", "water_v3", "water_v3.geojson"),
        "streams": os.path.join(root, "tests", "water_v3", "streams_candidates.geojson"),
        "profiles": os.path.join(root, "tests", "water_v3", "profiles.npz"),
    }
    inputs = {}
    lakes, ponds, flowing, streams = [], [], [], []
    for f in load_geojson(paths["contour_lakes"])["features"]:
        nm = str(f.get("properties", {}).get("body", ""))
        if nm.startswith("lake"):
            lakes.append((nm, shape(f["geometry"])))
    for f in load_geojson(paths["water_design"])["features"]:
        pr = f.get("properties", {})
        k = pr.get("class")
        if k == "pond":
            ponds.append((str(pr.get("osm_id")), shape(f["geometry"])))
        elif k in ("navigable", "river", "delta_branch", "delta_harbour",
                   "delta_navigable"):
            flowing.append((str(pr.get("id") or pr.get("name") or k), shape(f["geometry"])))
    for f in load_geojson(paths["streams"])["features"]:
        pr = f.get("properties", {})
        if float(pr.get("tier_m", -1.0)) >= 2500.0:
            streams.append((str(pr.get("id")), shape(f["geometry"])))
    if channel is not None:
        if not channel_width:
            raise SystemExit("--channel requires --channel-width")
        geom = LineString(parse_channel(channel)).buffer(
            channel_width / 2.0, cap_style="flat")
        flowing.append(("channel", geom))
    ex, ez, ep = [], [], []
    pf = np.load(paths["profiles"])
    for key in pf.files:
        a = np.asarray(pf[key], dtype=np.float64)
        if a.ndim == 2 and a.shape[0] >= 1 and a.shape[1] >= 5:
            ex += [float(a[0, 1]), float(a[-1, 1])]
            ez += [float(a[0, 2]), float(a[-1, 2])]
            ep += [str(key), str(key)]
    inputs["terrain"] = None  # filled by the caller
    for key, p in paths.items():
        inputs[key] = {"path": p, "sha256": cen.sha256_file(p)}
    layers = {"lakes": lakes, "ponds": ponds, "flowing": flowing,
              "streams": streams, "profile_ends": (ex, ez, ep)}
    return layers, inputs


# ----------------------------------------------------------------------------
# Self-test (synthetic 120 x 120 grid, no files read)
# ----------------------------------------------------------------------------

def run_selftest(out_dir):
    vertex_m, z0 = 6.0, 12282.0
    H = W = 120
    heights = np.full((H, W), 5.0, dtype=np.float32)
    cls = np.zeros((H, W), dtype=np.uint8)
    level = np.full((H, W), np.nan, dtype=np.float32)

    def rect(x0, x1, zb, zt):
        return {"type": "Polygon",
                "coordinates": [[[x0, zb], [x1, zb], [x1, zt], [x0, zt], [x0, zb]]]}

    def stamp(r0, r1, c0, c1, klass, lvl):
        cls[r0:r1, c0:c1] = klass
        level[r0:r1, c0:c1] = lvl

    # big lake (100 vertices = 3600 m2 >= big_area 2000), rows 20-29, cols 20-29
    stamp(20, 30, 20, 30, 2, 6.2)
    # connected lake (36 vertices = 1296 m2 < 2000), rows 40-45, cols 40-45
    stamp(40, 46, 40, 46, 2, 6.0)
    # accidental pond, rows 60-63, cols 60-63; river raster one vertex east
    stamp(60, 64, 60, 64, 7, 5.8)
    cls[60:64, 64] = 5
    level[60:64, 64] = 5.5
    heights[59, 59:65] = 6.3   # bank of the accidental pond (dike 1.3)
    heights[64, 59:65] = 6.3
    heights[60:64, 59] = 6.3
    # moat lake_093, rows 90-93, cols 90-93
    stamp(90, 94, 90, 94, 2, 5.5)
    # shallow pond, rows 100-103, cols 40-43 (perched 0.2 -> keep)
    stamp(100, 104, 40, 44, 7, 5.2)
    # isolated diked pond, rows 30-35, cols 80-85 (perched 1.2, dike 1.5)
    stamp(30, 36, 80, 86, 7, 6.5)
    B = np.zeros((H, W), dtype=bool)
    B[30:36, 80:86] = True
    dist = ndimage.distance_transform_edt(~B, sampling=vertex_m)
    heights[(~B) & (dist > 12.0) & (dist <= 36.0) & (cls == 0)] = 5.3
    bank = ndimage.binary_dilation(B, structure=cen.STRUCT8) & ~B & (cls == 0)
    heights[bank] = 6.8

    lakes = [("lake_200", shape(rect(117, 177, 12105, 12165))),
             ("lake_101", shape(rect(237, 273, 12009, 12045))),
             ("lake_093", shape(rect(537, 561, 11721, 11745)))]
    ponds = [("osm_123", shape(rect(237, 261, 11661, 11685)))]
    flowing = [("Narva_0", shape(rect(271, 300, 12009, 12045))),
               ("river_023", shape(rect(400, 440, 11900, 12100)))]
    # stream_0001 has tier_m < 2500 and overlaps the shallow pond: must be ignored
    streams = [("stream_0255", shape(rect(600, 640, 11800, 11850)))]
    prof = {
        "river_023": np.array([[0, 402, 11905, 0, 5.5],
                               [0, 420, 12000, 0, 5.5],
                               [0, 438, 12095, 0, 5.5]]),
        "stream_0255": np.array([[0, 605, 11810, 0, 5.4],
                                 [0, 635, 11840, 0, 5.4]]),
    }
    ex = [402, 438, 605, 635]
    ez = [11905, 12095, 11810, 11840]
    ep = ["river_023", "river_023", "stream_0255", "stream_0255"]
    layers = {"lakes": lakes, "ponds": ponds, "flowing": flowing,
              "streams": streams, "profile_ends": (ex, ez, ep)}
    params = {"root": None, "big_area": 2000.0, "perched_min": 0.30,
              "dike_lower": 1.0, "ring_margin": 0.05, "ring_in": 12,
              "ring_out": 36, "channel": None, "channel_width": None,
              "vertex_m": vertex_m, "z0": z0}

    records, body_id_r = classify(heights, cls, level, layers, params)

    by_level = {round(r["level_m"], 2): r for r in records}
    expected = {
        5.2: ("isolated", "keep", 5.2),
        5.5: ("moat", "exception_owner_decision", 5.5),
        5.8: ("accidental", "lower_to_ring", 4.95),
        6.0: ("connected", "lower_with_river", None),
        6.2: ("big", "decide_apart", 6.2),
        6.5: ("isolated", "lower_to_ring", 5.25),
    }
    assert len(records) == 6, len(records)
    for lvl, (cat, act, prop) in expected.items():
        r = by_level[lvl]
        assert r["category"] == cat, (lvl, r["category"], cat)
        assert r["action"] == act, (lvl, r["action"], act)
        p = r["proposed_level_m"]
        if prop is None:
            assert p is None or not math.isfinite(p), (lvl, p)          # NaN in records, null in JSON
        else:
            assert p is not None and abs(p - prop) < 1e-4, (lvl, p, prop)   # levels are float32
    assert by_level[5.5]["member_lakes"] == ["lake_093"]
    assert by_level[6.2]["member_lakes"] == ["lake_200"]
    assert by_level[5.2]["member_ponds"] == ["osm_123"]
    assert by_level[6.0]["connected_to"] == ["Narva_0"]
    assert by_level[6.0]["contacts"] == {}
    assert not math.isfinite(by_level[6.0]["contact_flowing_level_max"])
    assert by_level[5.8]["separate"] is True
    assert by_level[5.8]["separate_vertices"] == 4
    assert by_level[5.8]["contacts"]["river"]["vertices"] == 4
    assert by_level[5.8]["connected_to"] == []
    assert abs(by_level[6.5]["dike_after_est_m"] - 0.3) < 1e-3
    assert abs(by_level[6.5]["ring_p10_m"] - 5.3) < 1e-6

    inputs = {"terrain": {"path": "<selftest: synthetic 120x120 grid>",
                          "sha256": None}}
    write_outputs(out_dir, records, inputs, params, heights, cls, body_id_r)
    print("SELFTEST PASS")


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Classify standing water bodies of a DayZ terrain grid.")
    ap.add_argument("--terrain", default=None, help="terrain NPZ")
    ap.add_argument("--out", required=True, help="output folder (must not exist)")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="project root folder")
    ap.add_argument("--channel", default=None, help="extra navigable channel x,z;x,z;...")
    ap.add_argument("--channel-width", type=float, default=None,
                    help="channel width in metres")
    ap.add_argument("--big-area", type=float, default=1.5e6)
    ap.add_argument("--perched-min", type=float, default=0.30)
    ap.add_argument("--dike-lower", type=float, default=1.0)
    ap.add_argument("--ring-margin", type=float, default=0.05)
    ap.add_argument("--ring-in", type=int, default=12)
    ap.add_argument("--ring-out", type=int, default=36)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    # the output folder is checked before any computation
    if os.path.exists(args.out):
        raise SystemExit("output folder already exists: %s" % args.out)

    if args.selftest:
        run_selftest(args.out)
        return

    if not args.terrain:
        raise SystemExit("--terrain is required without --selftest")
    if args.channel is not None and not args.channel_width:
        raise SystemExit("--channel requires --channel-width")

    heights, cls, level = cen.load_terrain(args.terrain)
    layers, inputs = build_layers(args.root, args.channel, args.channel_width)
    inputs["terrain"] = {"path": args.terrain, "sha256": cen.sha256_file(args.terrain)}
    params = {"root": args.root, "big_area": args.big_area,
              "perched_min": args.perched_min, "dike_lower": args.dike_lower,
              "ring_margin": args.ring_margin, "ring_in": args.ring_in,
              "ring_out": args.ring_out, "channel": args.channel,
              "channel_width": args.channel_width,
              "vertex_m": cen.VERTEX_M, "z0": cen.Z0}
    records, body_id_r = classify(heights, cls, level, layers, params)
    write_outputs(args.out, records, inputs, params, heights, cls, body_id_r)


if __name__ == "__main__":
    main()
