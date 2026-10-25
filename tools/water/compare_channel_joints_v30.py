#!/usr/bin/env python3
"""compare_channel_joints_v30.py

Measures how consecutive water channel pieces are chained (joint offsets and
footprint overlap) for two sets of placed pieces: vanilla DayZ Chernarus
pieces (from a survey log) and our Baltic map's fitted pieces (from a fit's
axes.json). Writes OUTDIR/joints.json plus overview images OUTDIR/ours.png
and OUTDIR/vanilla.png.

Only stdlib + numpy + shapely 2.x + matplotlib (Agg). No network, no writes
outside OUTDIR.

Written by GLM-5.3-Flash (GX10 lane D, 04-10); receiver changes: every piece
carries its library edge frames (the delivered file never attached them and
stopped with KeyError), and the model-to-world transform takes R, U, F as rows
(it was transposed; the self-test adds a turned asymmetric wedge that catches it). Joint heading compares
A's exit with B's entry, as vanilla_channel_pieces.py calibrate() does (it compared the two exits; found by
the gpt-6-astra council lane, 04-10); with it the vanilla joints and headings match the library calibration.

CLI:
    python compare_channel_joints_v30.py --library L.json --survey S.log \
        --axes A.json --out OUTDIR [--vanilla-views x:z:half,...]
    python compare_channel_joints_v30.py --selftest --out OUTDIR
"""

import argparse
import hashlib
import json
import math
import os
import sys
import time

import numpy as np
import shapely
from shapely import STRtree
from shapely.geometry import MultiPolygon, Polygon

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DEFAULT_VIEWS = "655:2409:150,1094:5707:150"


# --------------------------------------------------------------------------- #
# Survey helpers (verified conventions, used verbatim)
# --------------------------------------------------------------------------- #

def vec(t):
    return np.array([float(v) for v in t.strip('<> ').split(',')])


def basis(yaw_deg, up):
    a = math.radians(yaw_deg)
    fh = np.array([math.sin(a), 0.0, math.cos(a)])
    up = up / np.linalg.norm(up)
    fwd = fh - (fh @ up) * up
    fwd /= np.linalg.norm(fwd)
    right = np.cross(up, fwd)
    if right @ np.array([math.cos(a), 0.0, -math.sin(a)]) < 0:
        right = -right
    return right, up, fwd


# --------------------------------------------------------------------------- #
# Input loading
# --------------------------------------------------------------------------- #

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_library(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_vanilla(path, lib):
    pieces = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            f = line.rstrip("\r\n").split(";")
            if len(f) < 6 or f[0] != "O":
                continue
            stem = f[2].split("\\")[-1][:-4]
            if stem not in lib["pieces"]:
                continue
            spec = lib["pieces"][stem]
            pos = vec(f[3])
            yaw = float(vec(f[4])[0])
            up = vec(f[5])
            R, U, F = basis(yaw, up)
            pieces.append({"set": "vanilla", "type": stem,
                           "family": spec["family"], "scale": 1.0,
                           "R": R, "U": U, "F": F, "P": pos})
    return pieces


def load_ours(path, lib):
    with open(path, "r", encoding="utf-8") as fh:
        axes = json.load(fh)
    out = {}
    for reach, data in axes.items():
        lst = []
        for pc in data.get("pieces", []):
            m = pc["matrix"]
            R = np.array(m[0:3], dtype=float)
            U = np.array(m[3:6], dtype=float)
            F = np.array(m[6:9], dtype=float)
            P = np.array(m[9:12], dtype=float)
            lst.append({"set": reach, "type": pc["type"],
                        "family": lib["pieces"][pc["type"]]["family"],
                        "scale": float(pc["scale"]),
                        "R": R, "U": U, "F": F, "P": P})
        out[reach] = lst
    return out


# --------------------------------------------------------------------------- #
# Step 1: edge frames in world
# --------------------------------------------------------------------------- #

def edge_frames(pieces):
    """Return (Qs, hs, Qe, he, P) arrays over the piece list."""
    Qs, hs, Qe, he, Ps = [], [], [], [], []
    for p in pieces:
        R, U, F, P = p["R"], p["U"], p["F"], p["P"]
        for edge, QL, hL in ((p["_start"], Qs, hs), (p["_end"], Qe, he)):
            mid = edge["mid"]
            h = math.radians(edge["heading_deg"])
            Q = P + mid[0] * R + edge["y"] * U + mid[1] * F
            d = math.sin(h) * R + math.cos(h) * F
            QL.append(Q)
            hL.append(math.degrees(math.atan2(d[0], d[2])))
        Ps.append(P)
    return (np.array(Qs), np.array(hs), np.array(Qe), np.array(he),
            np.array(Ps))


# --------------------------------------------------------------------------- #
# Step 2: joint matching (existing calibration rule)
# --------------------------------------------------------------------------- #

def find_joints(pieces):
    Qs, hs, Qe, he, Ps = edge_frames(pieces)
    n = len(pieces)
    joints = []
    if n == 0:
        return joints
    pxz = Ps[:, [0, 2]]
    idx = np.arange(n)
    for i in range(n):
        d2 = ((pxz - pxz[i]) ** 2).sum(axis=1)
        cand = np.where((d2 < 1600.0) & (idx != i))[0]
        if cand.size == 0:
            continue
        dv = Qs[cand] - Qe[i]
        h = math.radians(he[i])
        s, c = math.sin(h), math.cos(h)
        along = dv[:, 0] * s + dv[:, 2] * c
        across = dv[:, 0] * c - dv[:, 2] * s
        dh = np.abs((hs[cand] - he[i] + 180.0) % 360.0 - 180.0)
        err = np.hypot(along, across) + dh / 4.0
        k = int(np.argmin(err))
        if err[k] < 12.0:
            j = int(cand[k])
            joints.append({
                "a": i, "b": j,
                "types": [pieces[i]["type"], pieces[j]["type"]],
                "along": float(along[k]), "across": float(across[k]),
                "dh": float(dh[k]), "level": float(dv[k, 1]),
                "mx": float((Qe[i][0] + Qs[j][0]) / 2.0),
                "mz": float((Qe[i][2] + Qs[j][2]) / 2.0),
            })
    return joints


# --------------------------------------------------------------------------- #
# Step 3: footprints
# --------------------------------------------------------------------------- #

def footprint(p):
    v = np.asarray(p["_v"], dtype=float)
    tri = np.asarray(p["_tri"], dtype=np.int64)
    M = np.vstack([p["R"], p["U"], p["F"]])
    w = v @ M + p["P"]
    pts = w[:, [0, 2]]
    rings = np.stack([pts[tri[:, 0]], pts[tri[:, 1]],
                      pts[tri[:, 2]], pts[tri[:, 0]]], axis=1)
    polys = shapely.polygons(rings)
    keep = shapely.area(polys) >= 1e-9
    if not keep.any():
        return Polygon()
    return shapely.make_valid(shapely.union_all(polys[keep]))


def with_footprints(pieces, lib):
    for p in pieces:
        spec = lib["pieces"][p["type"]]
        p["_v"] = spec["mesh"]["v"]
        p["_tri"] = spec["mesh"]["tri"]
        p["_start"], p["_end"] = spec["start"], spec["end"]
        p["_fp"] = footprint(p)


# --------------------------------------------------------------------------- #
# Step 4: per-joint overlap
# --------------------------------------------------------------------------- #

def attach_overlaps(joints, pieces, lib):
    for j in joints:
        A, B = pieces[j["a"]], pieces[j["b"]]
        j["ov"] = float(shapely.intersection(A["_fp"], B["_fp"]).area)
        wa = lib["pieces"][A["type"]]["width"] * A["scale"]
        wb = lib["pieces"][B["type"]]["width"] * B["scale"]
        den = 0.5 * (wa + wb)
        j["olen"] = j["ov"] / den if den > 0 else 0.0


# --------------------------------------------------------------------------- #
# Step 5: layered area per group
# --------------------------------------------------------------------------- #

def layered(geoms):
    """Return (covered_m2, multi_m2, [intersection geometries])."""
    if not geoms:
        return 0.0, 0.0, []
    covered = float(shapely.union_all(list(geoms)).area)
    inter = []
    if len(geoms) > 1:
        tree = STRtree(list(geoms))
        ii, jj = tree.query(list(geoms), predicate="intersects")
        m = ii < jj
        ii, jj = ii[m], jj[m]
        if ii.size:
            ga = np.asarray(geoms, dtype=object)[ii]
            gb = np.asarray(geoms, dtype=object)[jj]
            inter = [g for g in shapely.intersection(ga, gb) if g.area > 0]
    multi = float(shapely.union_all(inter).area) if inter else 0.0
    return covered, multi, inter


# --------------------------------------------------------------------------- #
# Stats / JSON records
# --------------------------------------------------------------------------- #

def pct(vals, ps):
    if not vals:
        return None
    return [round(float(x), 3)
            for x in np.percentile(np.asarray(vals, dtype=float), ps)]


def pct_max(vals, ps):
    if not vals:
        return None
    a = np.asarray(vals, dtype=float)
    return [round(float(x), 3) for x in np.percentile(a, ps)] + \
        [round(float(a.max()), 3)]


def make_stats(pieces, joints, covered, multi):
    scales = [p["scale"] for p in pieces]
    return {
        "pieces": len(pieces),
        "joints": len(joints),
        "scale_p50": round(float(np.median(scales)), 3) if scales else None,
        "along_m_p10_p50_p90": pct([j["along"] for j in joints], [10, 50, 90]),
        "across_m_p10_p50_p90": pct([j["across"] for j in joints], [10, 50, 90]),
        "heading_deg_p50_p90": pct([j["dh"] for j in joints], [50, 90]),
        "level_m_abs_p50_p90": pct([abs(j["level"]) for j in joints], [50, 90]),
        "overlap_m2_p50_p90_max": pct_max([j["ov"] for j in joints], [50, 90]),
        "overlap_len_m_p50_p90_max": pct_max([j["olen"] for j in joints], [50, 90]),
        "gap_m_p50_p90_max": pct_max([max(0.0, j["along"]) for j in joints], [50, 90]),
        "covered_m2": round(covered, 3),
        "multi_m2": round(multi, 3),
        "multi_share": round(multi / covered, 6) if covered > 0 else 0.0,
    }


def json_joint(j):
    return {
        "a": j["a"], "b": j["b"], "types": j["types"],
        "mid_xz": [round(j["mx"], 3), round(j["mz"], 3)],
        "along_m": round(j["along"], 3),
        "across_m": round(j["across"], 3),
        "heading_deg": round(j["dh"], 3),
        "level_m": round(j["level"], 3),
        "overlap_m2": round(j["ov"], 3),
        "overlap_len_m": round(j["olen"], 3),
        "gap_m": round(max(0.0, j["along"]), 3),
    }


# --------------------------------------------------------------------------- #
# Views
# --------------------------------------------------------------------------- #

def parse_views(spec):
    views = []
    for tok in spec.split(","):
        x, z, half = (float(v) for v in tok.split(":"))
        views.append((x, z, half))
    return views


def make_view(x, z, half, vanilla, vjoints):
    inside = [i for i, p in enumerate(vanilla)
              if abs(p["P"][0] - x) <= half and abs(p["P"][2] - z) <= half]
    geoms = [vanilla[i]["_fp"] for i in inside]
    covered, multi, inter = layered(geoms)
    jinside = [j for j in vjoints
               if abs(j["mx"] - x) <= half and abs(j["mz"] - z) <= half]
    view = {"center": [x, z], "half_m": half, "pieces": len(inside),
            "joints": len(jinside), "covered_m2": round(covered, 3),
            "multi_m2": round(multi, 3),
            "multi_share": round(multi / covered, 6) if covered > 0 else 0.0}
    return view, [vanilla[i] for i in inside], jinside, inter


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #

def polys_of(g):
    if g is None or g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    if isinstance(g, MultiPolygon):
        return list(g.geoms)
    if hasattr(g, "geoms"):
        out = []
        for s in g.geoms:
            out.extend(polys_of(s))
        return out
    return []


def draw_panel(ax, pieces, inter_geoms, joints, title, xlim, ylim):
    for p in pieces:
        for g in polys_of(p["_fp"]):
            xs, ys = g.exterior.xy
            ax.fill(xs, ys, color="lightblue", alpha=0.5, lw=0)
            ax.plot(xs, ys, color="0.3", lw=0.5)
    for g in inter_geoms:
        for pg in polys_of(g):
            xs, ys = pg.exterior.xy
            ax.fill(xs, ys, color="red", alpha=0.6, lw=0)
    if joints:
        ax.plot([j["mx"] for j in joints], [j["mz"] for j in joints],
                "k.", markersize=3)
        for j in joints:
            ax.text(j["mx"], j["mz"], f"{round(j['olen'], 1)}", fontsize=6)
    ax.set_title(title, fontsize=9)
    ax.set_aspect("equal")
    if xlim is not None:
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)


def share_pct(multi, covered):
    return 100.0 * multi / covered if covered > 0 else 0.0


def plot_ours(path, ours, reach_joints, reach_layered):
    reaches = list(ours.keys())
    fig, axs = plt.subplots(1, len(reaches), figsize=(18, 7), dpi=90,
                            squeeze=False)
    for ax, reach in zip(axs[0], reaches):
        pieces = ours[reach]
        covered, multi, inter = reach_layered[reach]
        if pieces:
            b = shapely.bounds([p["_fp"] for p in pieces])
            xlim = (float(b[:, 0].min()) - 20.0, float(b[:, 2].max()) + 20.0)
            ylim = (float(b[:, 1].min()) - 20.0, float(b[:, 3].max()) + 20.0)
        else:
            xlim = ylim = None
        title = f"{reach}: {len(pieces)} pieces, multi {share_pct(multi, covered):.1f}%"
        draw_panel(ax, pieces, inter, reach_joints[reach], title, xlim, ylim)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_vanilla(path, view_data):
    n = max(1, len(view_data))
    fig, axs = plt.subplots(1, n, figsize=(18, 7), dpi=90, squeeze=False)
    for ax, entry in zip(axs[0], view_data):
        if entry is None:
            ax.set_axis_off()
            continue
        view, pieces, jinside, inter = entry
        x, z, half = view["center"][0], view["center"][1], view["half_m"]
        title = (f"vanilla {x:g}:{z:g} +/-{half:g} m: {view['pieces']} pieces, "
                 f"multi {share_pct(view['multi_m2'], view['covered_m2']):.1f}%")
        draw_panel(ax, pieces, inter, jinside, title,
                   (x - half, x + half), (z - half, z + half))
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Shared pipeline pieces used by both the real run and the self-test
# --------------------------------------------------------------------------- #

def prepare_pieces(pieces, lib):
    with_footprints(pieces, lib)


def joints_with_overlaps(pieces, lib):
    joints = find_joints(pieces)
    attach_overlaps(joints, pieces, lib)
    return joints


def run_compute(lib, vanilla, ours, view_specs, t0):
    """Returns (result_dict, view_plot_data)."""
    prepare_pieces(vanilla, lib)
    for lst in ours.values():
        prepare_pieces(lst, lib)

    # vanilla joints over the whole survey; grouped by A's family
    vjoints = joints_with_overlaps(vanilla, lib)
    groups = {}
    for gname, fam in (("vanilla_river", "river"), ("vanilla_stream", "stream")):
        gpieces = [p for p in vanilla if p["family"] == fam]
        gjoints = [j for j in vjoints if vanilla[j["a"]]["family"] == fam]
        covered, multi, _ = layered([p["_fp"] for p in gpieces])
        groups[gname] = make_stats(gpieces, gjoints, covered, multi)

    ours_joints = {}
    reach_joints = {}
    reach_layered = {}
    for reach, rpieces in ours.items():
        rjoints = joints_with_overlaps(rpieces, lib)
        reach_joints[reach] = rjoints
        ours_joints[reach] = [json_joint(j) for j in rjoints]
        covered, multi, inter = layered([p["_fp"] for p in rpieces])
        reach_layered[reach] = (covered, multi, inter)
        groups[reach] = make_stats(rpieces, rjoints, covered, multi)

    view_data = []
    views_json = []
    for (x, z, half) in view_specs:
        view, vpieces, jinside, inter = make_view(x, z, half, vanilla, vjoints)
        view_data.append((view, vpieces, jinside, inter))
        views_json.append(view)

    result = {
        "inputs": {
            "library": lib["_path"], "library_sha256": lib["_sha"],
            "survey": lib["_survey_path"], "survey_sha256": lib["_survey_sha"],
            "axes": lib["_axes_path"], "axes_sha256": lib["_axes_sha"],
        },
        "groups": groups,
        "ours_joints": ours_joints,
        "vanilla_views": views_json,
        "seconds": round(time.time() - t0, 3),
    }
    return result, view_data, reach_joints, reach_layered


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #

def selftest(outdir):
    lib = {"pieces": {"box_10_20": {
        "family": "river", "width": 10.0,
        "mesh": {"v": [[-5, 0, -10], [5, 0, -10], [5, 0, 10], [-5, 0, 10]],
                 "tri": [[0, 1, 2], [0, 2, 3]]},
        "start": {"mid": [0, -10], "heading_deg": 0, "width": 10, "y": 0},
        "end": {"mid": [0, 10], "heading_deg": 0, "width": 10, "y": 0},
    }}}

    def placed(px, py, pz):
        return {"set": "T", "type": "box_10_20", "family": "river",
                "scale": 1.0,
                "R": np.array([1.0, 0.0, 0.0]),
                "U": np.array([0.0, 1.0, 0.0]),
                "F": np.array([0.0, 0.0, 1.0]),
                "P": np.array([px, py, pz], dtype=float)}

    ours = {"T": [placed(0, 0, 0), placed(0, 0, 20), placed(0, 0, 36)]}
    t0 = time.time()
    prepare_pieces(ours["T"], lib)
    tjoints = joints_with_overlaps(ours["T"], lib)

    def get(a, b):
        for j in tjoints:
            if j["a"] == a and j["b"] == b:
                return j
        raise AssertionError(f"missing joint {a}->{b}")

    jAB = get(0, 1)
    assert abs(jAB["along"]) < 1e-6, jAB["along"]
    assert jAB["ov"] < 1e-6, jAB["ov"]

    jBC = get(1, 2)
    assert abs(jBC["along"] - (-4.0)) < 1e-6, jBC["along"]
    assert abs(jBC["ov"] - 40.0) < 1e-6, jBC["ov"]
    assert abs(jBC["olen"] - 4.0) < 1e-6, jBC["olen"]

    covered, multi, _ = layered([p["_fp"] for p in ours["T"]])
    assert abs(multi - 40.0) < 1e-6, multi
    assert abs(covered - 560.0) < 1e-6, covered

    # An asymmetric wedge turned 90 degrees (forward = +x, right = -z) catches a transposed model-to-world transform:
    # model (5, 0, 0) -> world (100, -5), model (0, 0, 10) -> world (110, 0).
    lib["pieces"]["wedge"] = dict(lib["pieces"]["box_10_20"], mesh={"v": [[0, 0, 0], [5, 0, 0], [0, 0, 10]], "tri": [[0, 1, 2]]})
    turned = dict(placed(100, 0, 0), type="wedge", R=np.array([0.0, 0.0, -1.0]), F=np.array([1.0, 0.0, 0.0]))
    prepare_pieces([turned], lib)
    assert np.allclose(turned["_fp"].bounds, (100.0, -5.0, 110.0, 0.0)), turned["_fp"].bounds

    # Two 30-degree bends chained: A exits at heading 30, B (turned 30) enters at 30 and exits at 60. The joint
    # heading compares A's exit with B's ENTRY (0 here); exit-against-exit would report 30.
    lib["pieces"]["bend30"] = dict(lib["pieces"]["box_10_20"], end={"mid": [0, 10], "heading_deg": 30, "width": 10, "y": 0})
    a30 = math.radians(30)
    bend_a = dict(placed(500, 0, 0), type="bend30")
    rb = np.array([math.cos(a30), 0.0, -math.sin(a30)])
    fb = np.array([math.sin(a30), 0.0, math.cos(a30)])
    bend_b = dict(placed(500.0, 0.0, 20.0), type="bend30", R=rb, F=fb)
    bend_b["P"] = np.array([500.0, 0.0, 10.0]) + 10.0 * fb
    prepare_pieces([bend_a, bend_b], lib)
    jb = [j for j in find_joints([bend_a, bend_b]) if j["a"] == 0 and j["b"] == 1]
    assert jb and abs(jb[0]["dh"]) < 1e-6, jb

    empty = make_stats([], [], 0.0, 0.0)
    result = {
        "inputs": {"library": "", "library_sha256": None,
                   "survey": "", "survey_sha256": None,
                   "axes": "", "axes_sha256": None},
        "groups": {"vanilla_river": empty, "vanilla_stream": empty,
                   "T": make_stats(ours["T"], tjoints, covered, multi)},
        "ours_joints": {"T": [json_joint(j) for j in tjoints]},
        "vanilla_views": [],
        "seconds": round(time.time() - t0, 3),
    }
    with open(os.path.join(outdir, "joints.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    print("SELFTEST PASS")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def parse_args():
    ap = argparse.ArgumentParser(
        description="Compare joint chaining / footprint overlap of water "
                    "channel pieces: vanilla survey vs our fit.")
    ap.add_argument("--library")
    ap.add_argument("--survey")
    ap.add_argument("--axes")
    ap.add_argument("--out", required=True)
    ap.add_argument("--vanilla-views", default=DEFAULT_VIEWS)
    ap.add_argument("--selftest", action="store_true")
    return ap.parse_args()


def ensure_out(path):
    if os.path.exists(path):
        sys.exit(f"error: output directory already exists: {path}")
    os.makedirs(path)


def main():
    args = parse_args()
    ensure_out(args.out)
    if args.selftest:
        selftest(args.out)
        return
    if not (args.library and args.survey and args.axes):
        sys.exit("error: --library, --survey and --axes are required "
                 "(unless --selftest)")

    t0 = time.time()
    lib = load_library(args.library)
    lib["_path"] = args.library
    lib["_sha"] = sha256_of(args.library)
    lib["_survey_path"] = args.survey
    lib["_survey_sha"] = sha256_of(args.survey)
    lib["_axes_path"] = args.axes
    lib["_axes_sha"] = sha256_of(args.axes)

    vanilla = load_vanilla(args.survey, lib)
    ours = load_ours(args.axes, lib)
    views = parse_views(args.vanilla_views)

    result, view_data, reach_joints, reach_layered = run_compute(
        lib, vanilla, ours, views, t0)

    with open(os.path.join(args.out, "joints.json"), "w",
              encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    plot_ours(os.path.join(args.out, "ours.png"), ours,
              reach_joints, reach_layered)
    plot_vanilla(os.path.join(args.out, "vanilla.png"), view_data)
    print(f"done: {result['groups']['vanilla_river']['pieces']} vanilla + "
          f"{sum(len(v) for v in ours.values())} fitted pieces, "
          f"wrote joints.json, ours.png, vanilla.py".replace("vanilla.py", "vanilla.png"))


if __name__ == "__main__":
    main()
