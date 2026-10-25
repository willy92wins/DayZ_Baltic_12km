"""Mechanical gates of the despike pass (despike_v31.py). Independent of the tool: the prominence metric is recomputed here
with scipy.ndimage min/max filters (the tool and the census shift arrays), and the protected domain is rebuilt from the
INPUT terrain and the envelope. Prints one PASS/FAIL line per gate and an overall line; exit code 0 only if all pass.

G1 reduction  free-domain vertices with small-shape prominence (peak or pit) > 0.5 m and > 1.0 m: after <= 10 % of before.
G2 bury       tools/water/bury_edges_v31.py on the output (same reference inputs as the EV110 chain): no new exposed edge
              and 0 heights changed by bury.
G3 footprint  the footprint bury computed on the output (fp0) equals the reference footprint array by array (env_plane,
              plane, visible, field; NaN = NaN): pond pieces, their planes and the visible field are unchanged.
G4 arrays     every array of the output except heights and v31_despike is byte-identical to the input (level, water,
              masks); heights unchanged at every envelope-cell corner below its plane + 0.35 m.
G5 frozen     0 height changes in reserve | platform | narva, in v31_kit dilated 2, in v31_bridge_cut | v31_bridge_fill
              dilated 3, in the water mask, on the 3-vertex border and below 0.80 m; engine-sea class (H < 0.75) unchanged
              including one-vertex islets of the input (Guillermo's EV112 decision). All flips reject the candidate;
              islet flips are also counted separately.
G6 slopes     every triangle (NW-SE split) after <= max(35 deg, before) + 1e-3 deg.
G7 seats      0 changed vertices within 15 m of a kit/stones record origin or 30 m of a bridge record origin.
G8 protected  no protected vertex gets sharper: on every vertex of the protected domain above OR within 15 m of a
              kit/stones record origin or 30 m of a bridge record origin (the G7 discs; a pass may change nothing there,
              but lowering the free ring beside it would sharpen it), max(peak, pit) after <= max(G8_FLOOR, before) +
              G8_TOL. G8_FLOOR = 0.3 m (the lowest census threshold; below it a shape is not a pyramid at any reported
              threshold); G8_TOL = 1e-5 m (float32 spacing is 7.6e-6 m at the highest EV110 vertex, 117.93 m; any
              sharpening that matters is >= 1 cm). Reported too: vertices that cross 0.5 m and the largest excess.
Usage: gate_despike_v31.py <in.npz> <out.npz> <envelope.npy> <ref_footprint.npz> <records.json> <work_dir>
       --bury-tool <bury_edges_v31.py> --bury-ref <ref_terrain.npz> --bury-cover <cover.npy> --bury-refrep <fp-report.json>
       [--skip-bury]
"""
import argparse, hashlib, json, os, subprocess, sys
import numpy as np
from scipy.ndimage import maximum_filter, minimum_filter, binary_dilation

N = 2048
G8_FLOOR, G8_TOL = 0.3, 1e-5
REC_R_KIT, REC_R_BRIDGE = 15.0, 30.0


def record_disks(recs):
    """Vertices within REC_R_* of a record origin (G7 radii), rebuilt here from the record list."""
    m = np.zeros((N, N), bool)
    for r in recs:
        x, zz = float(r["matrix"][9]), float(r["matrix"][11])
        R = REC_R_BRIDGE if "bridges" in r["model"].lower() else REC_R_KIT
        c0, r0 = int(round(x / 6.0)), int(round((12282.0 - zz) / 6.0))
        k = int(np.ceil(R / 6.0)) + 1
        rs, cs = np.arange(max(0, r0 - k), min(N, r0 + k + 1)), np.arange(max(0, c0 - k), min(N, c0 + k + 1))
        if not len(rs) or not len(cs):
            continue
        d = np.hypot(6.0 * cs[None, :] - x, 12282.0 - 6.0 * rs[:, None] - zz)
        m[rs[0]:rs[-1] + 1, cs[0]:cs[-1] + 1] |= d < R
    return m


def fp_of(offsets):
    f = np.zeros((7, 7), bool)
    for dr, dc in offsets:
        f[3 + dr, 3 + dc] = True
    return f


NB6 = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]
SHAPES = [[(0, 0)], [(0, 0), (1, 0)], [(0, 0), (0, 1)], [(0, 0), (1, 1)], [(0, 0), (0, 1), (1, 1)], [(0, 0), (1, 0), (1, 1)]]


def prom(H):
    peak = np.full(H.shape, -np.inf); pit = np.full(H.shape, -np.inf)
    for P in SHAPES:
        R = {(p[0] + d[0], p[1] + d[1]) for p in P for d in NB6} - set(P)
        fP, fR, fBack = fp_of(P), fp_of(R), fp_of([(-p[0], -p[1]) for p in P])
        pk = minimum_filter(H, footprint=fP, mode="nearest") - maximum_filter(H, footprint=fR, mode="nearest")
        pt = minimum_filter(H, footprint=fR, mode="nearest") - maximum_filter(H, footprint=fP, mode="nearest")
        peak = np.maximum(peak, maximum_filter(pk, footprint=fBack, mode="constant", cval=-np.inf))
        pit = np.maximum(pit, maximum_filter(pt, footprint=fBack, mode="constant", cval=-np.inf))
    return peak, pit


def slopes(H):
    a, b, c, d = H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]   # NW NE SW SE
    s1 = np.degrees(np.arctan(np.hypot((b - a) / 6, (d - b) / 6)))
    s2 = np.degrees(np.arctan(np.hypot((d - c) / 6, (c - a) / 6)))
    return s1, s2


def protected_domain(I, envp):
    """Protected domain rebuilt from the INPUT arrays and the envelope (no record discs; G7/G8 add those)."""
    H0 = I["heights"].astype(np.float64)
    ecell = np.isfinite(envp)
    corner = np.zeros((N, N), bool); vplane = np.full((N, N), -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            sl = (slice(dr, dr + N - 1), slice(dc, dc + N - 1))
            corner[sl] |= ecell
            vplane[sl] = np.maximum(vplane[sl], np.where(ecell, envp, -np.inf))
    env_low = corner & (H0 < vplane + 0.35)
    frozen = I["reserve"] | I["platform"] | I["narva"]
    k3 = np.ones((3, 3), bool)
    kit = binary_dilation(I["v31_kit"], k3, iterations=2)
    bridge = binary_dilation(I["v31_bridge_cut"] | I["v31_bridge_fill"], k3, iterations=3)
    border = np.ones((N, N), bool); border[3:-3, 3:-3] = False
    protected = frozen | env_low | I["water"] | (H0 < 0.80) | kit | bridge | border
    return dict(protected=protected, corner=corner, env_low=env_low, frozen=frozen, kit=kit, bridge=bridge, border=border)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for k in ("inp", "out", "envelope", "ref_fp", "records", "work"):
        ap.add_argument(k)
    ap.add_argument("--bury-tool"); ap.add_argument("--bury-ref"); ap.add_argument("--bury-cover"); ap.add_argument("--bury-refrep")
    ap.add_argument("--skip-bury", action="store_true")
    o = ap.parse_args()
    os.makedirs(o.work, exist_ok=False)
    zi, zo = np.load(o.inp), np.load(o.out)
    I = {k: zi[k] for k in zi.files}; O = {k: zo[k] for k in zo.files}
    H0 = I["heights"].astype(np.float64); H1 = O["heights"].astype(np.float64)
    ch = H1 != H0
    envp = np.load(o.envelope).astype(np.float64)
    dom = protected_domain(I, envp)
    protected, corner, env_low = dom["protected"], dom["corner"], dom["env_low"]
    frozen, kit, bridge, border = dom["frozen"], dom["kit"], dom["bridge"], dom["border"]
    free = ~protected
    res = {}
    # G1
    p0, q0 = prom(H0); p1, q1 = prom(H1)
    g1 = {}
    ok1 = True
    for t in (0.3, 0.5, 1.0):
        b = int((free & ((p0 > t) | (q0 > t))).sum()); a = int((free & ((p1 > t) | (q1 > t))).sum())
        g1[f"T{t}"] = dict(before=b, after=a, drop=round(1 - a / b, 4) if b else None)
        if t in (0.5, 1.0):
            ok1 &= b > 0 and a <= 0.10 * b
    res["G1_reduction"] = dict(ok=bool(ok1), **g1)
    # G8
    recs = json.load(open(o.records))
    disks = record_disks(recs)
    prot8 = protected | disks
    m0 = np.maximum(p0, q0); m1 = np.maximum(p1, q1)
    excess = np.where(prot8, m1 - np.maximum(G8_FLOOR, m0), -np.inf)
    sharp = excess > G8_TOL
    cross = prot8 & (m1 > 0.5) & (m0 <= 0.5)
    worst = np.argwhere(sharp)
    worst = worst[np.argsort(-excess[sharp], kind="stable")][:20] if len(worst) else worst
    res["G8_protected"] = dict(ok=int(sharp.sum()) == 0 and int(cross.sum()) == 0, sharpened=int(sharp.sum()),
                               new_crossings_0p5=int(cross.sum()), floor_m=G8_FLOOR, tol_m=G8_TOL,
                               max_excess_m=float(excess.max()), protected_vertices=int(prot8.sum()),
                               record_disk_vertices=int(disks.sum()), record_only_vertices=int((disks & ~protected).sum()),
                               before_gt_0p5=int((prot8 & (m0 > 0.5)).sum()), after_gt_0p5=int((prot8 & (m1 > 0.5)).sum()),
                               sharpened_xz=[[6 * int(c), 12282 - 6 * int(r), round(float(m0[r, c]), 4), round(float(m1[r, c]), 4)]
                                             for r, c in worst])
    # G4
    diff_arrays = [k for k in set(I) | set(O) if k not in ("heights", "v31_despike") and
                   (k not in I or k not in O or I[k].dtype != O[k].dtype or I[k].tobytes() != O[k].tobytes())]
    res["G4_arrays"] = dict(ok=not diff_arrays and int((ch & env_low).sum()) == 0, differing_arrays=diff_arrays,
                            env_low_changed=int((ch & env_low).sum()), level_identical="level" not in diff_arrays)
    # G5
    parts = dict(frozen=frozen, kit=kit, bridge=bridge, water=I["water"], border=border, below_0p80=H0 < 0.80)
    cnt = {k: int((ch & v).sum()) for k, v in parts.items()}
    hp = np.pad(H0, 1, mode="edge")
    nmax = np.max([hp[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] for dr, dc in NB6], axis=0)
    islet = free & ~corner & (nmax < 0.75) & (H0 >= 0.75)
    flips = (H0 < 0.75) != (H1 < 0.75)
    sea_flip = int(flips.sum())
    res["G5_frozen"] = dict(ok=all(v == 0 for v in cnt.values()) and sea_flip == 0 and int((ch & protected).sum()) == 0,
                            changed_in=cnt, sea_class_flips=sea_flip, sea_class_flips_non_islet=int((flips & ~islet).sum()),
                            islet_flips=int((flips & islet).sum()), islets_in_input=int(islet.sum()), changed_protected=int((ch & protected).sum()),
                            changed_total=int(ch.sum()))
    # G6
    a1, a2 = slopes(H0); b1, b2 = slopes(H1)
    v1 = b1 > np.maximum(35.0, a1) + 1e-3; v2 = b2 > np.maximum(35.0, a2) + 1e-3
    res["G6_slopes"] = dict(ok=int(v1.sum() + v2.sum()) == 0, violations=int(v1.sum() + v2.sum()),
                            max_increase_over_limit_deg=float(max(np.max(b1 - np.maximum(35, a1), initial=-99), np.max(b2 - np.maximum(35, a2), initial=-99))))
    # G7
    idx = np.argwhere(ch)
    xz = np.stack([6.0 * idx[:, 1], 12282.0 - 6.0 * idx[:, 0]], 1)
    near = 0; mind = np.inf
    for r in recs:
        R = 30.0 if "bridges" in r["model"].lower() else 15.0
        if len(xz):
            d = np.hypot(xz[:, 0] - r["matrix"][9], xz[:, 1] - r["matrix"][11])
            near += int((d < R).sum()); mind = min(mind, float(d.min()))
    res["G7_seats"] = dict(ok=near == 0 and len(recs) > 0, records=len(recs), changed_within_radius=near, min_distance_m=mind)
    # G2 / G3
    if o.skip_bury:
        res["G2_bury"] = dict(ok=False, status="NOT_RUN"); res["G3_footprint"] = dict(ok=False, status="NOT_RUN")
    else:
        rep = os.path.join(o.work, "bury-report.json")
        cmd = [sys.executable, "-I", o.bury_tool, o.out, o.bury_ref, o.bury_cover, o.envelope, o.bury_refrep,
               os.path.join(o.work, "terrain-buried.npz"), os.path.join(o.work, "bury-work"), rep]
        pr = subprocess.run(cmd, capture_output=True, text=True)
        br = json.load(open(rep)) if os.path.exists(rep) else {}
        res["G2_bury"] = dict(ok=pr.returncode == 0 and br.get("final_new_exposed") == [] and br.get("changed_vs_input") == 0,
                              rc=pr.returncode, final_new_exposed=br.get("final_new_exposed"), changed_vs_input=br.get("changed_vs_input"),
                              passes=[dict(p=x["pass_"], exposed=x["exposed"], new=len(x["new"])) for x in br.get("passes", [])])
        f0 = np.load(os.path.join(o.work, "bury-work", "fp0", "footprint.npz")); fr = np.load(o.ref_fp)
        same = {k: bool(np.array_equal(f0[k], fr[k], equal_nan=f0[k].dtype.kind == "f")) for k in fr.files}
        res["G3_footprint"] = dict(ok=all(same.values()) and set(f0.files) == set(fr.files), arrays=same)
    allok = all(v["ok"] for v in res.values())
    res["inputs"] = dict(inp=o.inp, inp_sha256=sha(o.inp), out=o.out, out_sha256=sha(o.out), envelope_sha256=sha(o.envelope),
                         ref_fp_sha256=sha(o.ref_fp), records_sha256=sha(o.records))
    res["overall"] = "PASS" if allok else "FAIL"
    json.dump(res, open(os.path.join(o.work, "gates.json"), "w"), indent=1)
    for k, v in res.items():
        if k.startswith("G"):
            print(f"{k}: {'PASS' if v['ok'] else 'FAIL'}  " + json.dumps({kk: vv for kk, vv in v.items() if kk != 'ok'}))
    print("OVERALL:", res["overall"])
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
