"""EV112 causeway gates, measured independently of causeway_v31.py on its output. Exit 0 PASS, 1 FAIL, 2 PENDING (every
mechanical gate passes, but an excluded cluster has no recorded approval).

The acceptance inventory is fixed here (INVENTORY, frozen 2026-10-17 on the EV110 terrain d25e9428...), not taken from the
producer: the spec file must hold exactly these clusters, classes and intervals, the report must list exactly the
causeways of the inventory (a missing, duplicated or unexpected id FAILS) and its input/output hashes must be the files
given here. The geometry is measured on the gate's own road axis (the raw chain of verify_roads_v30.road_chains,
densified to 0.25 m and smoothed with a 20 m moving average), not on the producer's axes. Shared code: only the exact
waterline geometry and the wiggle metric of tools/water/shore_ramp_v31.py (extract_segments, chain, canonical,
wiggle_profile: 12 m Savitzky-Golay, 0.5 m samples).
Gates
  G0 inventory  spec content = INVENTORY and its basis hash = the before terrain; report: schema, treated ids = the
                inventory causeways (no missing / duplicate / unexpected id), chain and interval per id, input terrain
                and output terrain hashes = the files given here, all 8 cluster ids classified as in the inventory.
  G1 run        per causeway side, over the whole frozen interval [s0, s1] (no core, no margin): the shoreline nearest
                to the road at each 1 m station; wiggle p90 <= 0.03 m; station coverage >= 0.98 inside
                [s0 + R_END, s1 - R_END] and every station gap touches an end of [s0, s1] and is <= R_END m long (the
                junction fillets may take the water away from the last stations).
  G1L links     per causeway side and end, stations s_end +- LINK_W m: waterline samples in triangles with a changed
                vertex; wiggle p90 <= 0.06 m (the grid floor of an exact R = 40 m fillet is 0.045, measured on
                synthetic circles 17-10; review 1 measured 0.080-0.215 on the round-1 links).
  G2 width      w = left + right offset of that shoreline; w_c = median over the middle half of the run: a contiguous
                stretch with |w - w_c| <= 0.5 m covers >= 0.75 of the run; no station narrower than w_c - 0.5 m;
                going out from that stretch, each side's offset never falls by more than 0.25 m (the links may only
                widen: fillets).
  G3 frozen     0 changed vertices on platform, narva, v31_kit, v31_bridge_cut, v31_bridge_fill, v31_lagoon; every other
                array byte-identical; v31_causeway = exactly the changed vertices.
  G4 edges      0 new exposed footprint border vertices; bury_edges_v31 on the after terrain changes 0 heights and leaves
                0 new exposed vertices (with --bury-ref-*).
  G5 sea        engine-sea components (H < 0.75, native triangle edges E-W, N-S, NW-SE) correspond one to one.
  G6 ponds      cover inside the envelope; 0 new footprint cells with a corner under the sea; regenerated footprint
                arrays identical to the before footprint.
  G7 slope      0 changed triangles crossing 35 deg (<= 35 before, > 35 after) or steepening above it.
  G8 clusters   every non-causeway cluster: 0 changed vertices within 150 m; the gate's own bilateral census on the
                before terrain finds no run >= 60 m within 200 m (the classification is re-measured, not trusted);
                approval recorded in the spec, else PENDING.
Usage: gate_causeway.py <before.npz> <before_fp.npz> <after.npz> <cover.npy> <envelope.npy> <report.json> <spec.json>
       <work_dir> <out.json> [--tools DIR] [--bury-ref-terrain T.npz --bury-ref-fp-report R.json]
"""
import argparse, hashlib, json, os, subprocess, sys
import numpy as np
from scipy.ndimage import label, uniform_filter1d
from scipy.spatial import cKDTree

INVENTORY = {
    "basis_sha256": "d25e9428ed39cebcef0c3b3885e23d8e397b67261846775ecdbc238fdde520e6",
    "causeway": {"c0": (104, 890.0, 1507.0), "c1": (62, 87.0, 475.0)},
    "other": {"c2": "road along a sea channel", "c3": "stream crossing", "c4": "road along a sea channel",
              "c5": "coastal road with a pond inland", "c6": "river junction crossing", "c7": "pond river beside the road"},
    "centres": {"c0": (7286, 10693), "c1": (6789, 10357), "c2": (10235, 9398),
                "c3": (8568, 10414), "c4": (10417, 9426), "c5": (8227, 10468),
                "c6": (3588, 6867), "c7": (9678, 2661)},
}
# OT7 repeats the same frozen census on the verified kit -> bridges -> dam -> shores chain.
# This is a specific input binding, not an arbitrary replacement of the acceptance basis.
EV112_SHORES = {
    "before": "b6242dce1a6bec491a346914e7ab2e1b2684bba06a55de887f9592db4163a48a",
    "before_fp": "9874f0605d295d6ec5e4f0cc9e745dc9578415a1036ea9ca99f07f509d64e3ca",
    "cover": "9253ae323a9f04252604dda33224464e8b1e394c6d4b8c64bcf40782172ee16e",
    "envelope": "cc45e2ef667ae2ba78de4c11283c648d2293c53303148f9247361b639a0e73a6",
}
SEA, SLOPE = 0.75, 35.0
WIG_MAX, COVER_MIN, R_END = 0.03, 0.98, 40.0
LINK_W, LINK_WIG_MAX = 60.0, 0.06
WIDTH_TOL, CORE_MIN, MONO_TOL = 0.5, 0.75, 0.25
CL_TOUCH_R, CL_CENSUS_R, CL_L_MIN, CL_REACH, CL_GAP = 150.0, 200.0, 60.0, 30.0, 5
S6 = np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]], bool)


def approval_granted(value):
    """Only an explicit boolean true grants approval; nonempty containers are not consent."""
    return value is True or (isinstance(value, dict) and value.get("approved") is True)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def c2v(m):
    out = np.zeros((m.shape[0] + 1, m.shape[1] + 1), bool)
    for dr in (0, 1):
        for dc in (0, 1):
            out[dr:dr + m.shape[0], dc:dc + m.shape[1]] |= m
    return out


def c2v_max(val):
    out = np.full((val.shape[0] + 1, val.shape[1] + 1), -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            sl = (slice(dr, dr + val.shape[0]), slice(dc, dc + val.shape[1]))
            out[sl] = np.maximum(out[sl], val)
    return out


def exposed(H, plane):
    fp = np.isfinite(plane)
    vin = c2v(fp)
    vout = c2v(~fp) | np.pad(np.zeros((H.shape[0] - 2, H.shape[1] - 2), bool), 1, constant_values=True)
    vP = c2v_max(np.where(fp, plane, -np.inf))
    return vin & vout & (H < vP + 0.05)


def slopes(h):
    nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
    return (np.degrees(np.arctan(np.hypot((ne - nw) / 6.0, (ne - se) / 6.0))),
            np.degrees(np.arctan(np.hypot((se - sw) / 6.0, (nw - sw) / 6.0))))


def tri_level(H, plane, x, z):
    """Terrain on the native triangles and the water level (pond plane on footprint cells, sea elsewhere)."""
    c, r = np.asarray(x, float) / 6.0, (6.0 * 2047 - np.asarray(z, float)) / 6.0
    c0 = np.clip(np.floor(c).astype(int), 0, 2046); r0 = np.clip(np.floor(r).astype(int), 0, 2046)
    fc, fr = c - c0, r - r0
    nw, ne, sw, se = H[r0, c0], H[r0, c0 + 1], H[r0 + 1, c0], H[r0 + 1, c0 + 1]
    h = np.where(fc >= fr, nw + fc * (ne - nw) + fr * (se - ne), nw + fr * (sw - nw) + fc * (se - sw))
    p = plane[r0, c0]
    return h, np.where(np.isfinite(p), p, SEA)


class Axis:
    """The gate's road axis: raw chain densified to 0.25 m, 20 m moving average; station = raw arc length."""

    def __init__(self, raw):
        s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(raw, axis=0).T))]
        t = np.arange(0, s[-1], 0.25)
        q = np.column_stack([np.interp(t, s, raw[:, 0]), np.interp(t, s, raw[:, 1])])
        self.p = np.column_stack([uniform_filter1d(q[:, 0], 81, mode="nearest"), uniform_filter1d(q[:, 1], 81, mode="nearest")])
        self.s = t
        g = np.gradient(self.p, axis=0)
        self.g = g / np.hypot(*g.T)[:, None]
        self.tree = cKDTree(self.p)

    def __call__(self, q):
        d, j = self.tree.query(q)
        v = q - self.p[j]
        cr = self.g[j, 0] * v[:, 1] - self.g[j, 1] * v[:, 0]
        return self.s[j], np.where(cr >= 0, d, -d), (j > 0) & (j < len(self.p) - 1)


def waterline(sr, H, W, fp, plane, r0, r1, c0, c1):
    seg = sr.extract_segments(H, W, fp, plane, r0, r1, c0, c1)
    seg = sr.subseg(seg, ~seg["pond"])
    qs, vs = [], []
    for c in sr.chain(seg):
        q, v = sr.wiggle_profile(sr.canonical(c["pts"], c["closed"]), c["closed"], 12.0, 0.5)
        qs.append(q); vs.append(v)
    return seg, np.vstack(qs), np.concatenate(vs)


def bilateral_runs(H, plane, raw, x, z):
    """Gate's own census near (x, z): runs of dry road stations (1 m) with water within CL_REACH m on both sides."""
    s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(raw, axis=0).T))]
    t = np.arange(0, s[-1], 1.0)
    q = np.column_stack([np.interp(t, s, raw[:, 0]), np.interp(t, s, raw[:, 1])])
    near = np.hypot(q[:, 0] - x, q[:, 1] - z) <= CL_CENSUS_R
    if near.sum() < 2:
        return []
    g = np.gradient(q, axis=0); g /= np.maximum(np.hypot(*g.T), 1e-9)[:, None]
    n = np.column_stack([-g[:, 1], g[:, 0]])
    offs = np.arange(0.5, CL_REACH + 1e-9, 0.5)
    wet = {}
    for sg in (1, -1):
        P = q[:, None, :] + sg * offs[None, :, None] * n[:, None, :]
        h, lev = tri_level(H, plane, P[..., 0], P[..., 1])
        wet[sg] = (h < lev).any(1)
    h, lev = tri_level(H, plane, q[:, 0], q[:, 1])
    ok = wet[1] & wet[-1] & (h >= lev)
    idx = np.nonzero(ok)[0]
    runs = []
    if len(idx):
        a = b = idx[0]
        for i in idx[1:]:
            if i - b - 1 <= CL_GAP:
                b = i
            else:
                runs.append((a, b)); a = b = i
        runs.append((a, b))
    return [(float(t[a]), float(t[b])) for a, b in runs if near[a:b + 1].any()]


def main():
    ap = argparse.ArgumentParser()
    for k in ("before", "before_fp", "after", "cover", "envelope", "report", "spec", "work", "out"):
        ap.add_argument(k)
    ap.add_argument("--tools", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..",
                                                    "tools"))           # evidence/v31-pond-layer-2026-10-13/ev112/causeway
    ap.add_argument("--bury-ref-terrain"); ap.add_argument("--bury-ref-fp-report")
    ap.add_argument("--ev112-shores-chain", action="store_true",
                    help="Bind to the frozen OT7 shores inputs; census and all mechanical criteria remain unchanged")
    a = ap.parse_args()
    tools = os.path.abspath(a.tools)
    sys.path.insert(0, os.path.join(tools, "water")); sys.path.insert(0, os.path.join(tools, "terrain"))
    import shore_ramp_v31 as sr
    from verify_roads_v30 import road_chains
    os.makedirs(a.work, exist_ok=False)
    py = sys.executable
    fails, pending = [], []
    res = dict(inputs=dict(before=a.before, before_sha256=sha(a.before), after=a.after, after_sha256=sha(a.after),
                           report=a.report, report_sha256=sha(a.report), spec=a.spec, spec_sha256=sha(a.spec)),
               inventory=INVENTORY)
    # ---- G0 inventory and report
    spec = json.load(open(a.spec, encoding="utf-8"))
    rep = json.load(open(a.report, encoding="utf-8"))
    g0 = []
    sids = [c.get("id") for c in spec.get("clusters", [])]
    want = sorted(list(INVENTORY["causeway"]) + list(INVENTORY["other"]))
    if sorted(sids) != want or len(sids) != len(set(sids)):
        g0.append(f"spec cluster ids {sids} != inventory {want}")
    if spec.get("basis", {}).get("terrain_sha256") != INVENTORY["basis_sha256"]:
        g0.append("spec basis terrain hash differs from the inventory")
    if a.ev112_shores_chain:
        chain_hashes = {name: sha(getattr(a, name)) for name in EV112_SHORES}
        res["chain_binding"] = dict(name="EV112 shores 2026-10-18", expected=EV112_SHORES, actual=chain_hashes)
        for name, expected in EV112_SHORES.items():
            if chain_hashes[name] != expected:
                g0.append(f"EV112 shores chain {name} hash differs from the frozen input")
    elif res["inputs"]["before_sha256"] != INVENTORY["basis_sha256"]:
        g0.append(f"before terrain {res['inputs']['before_sha256'][:12]} is not the inventory basis: re-freeze the inventory")
    for c in spec.get("clusters", []):
        i = c.get("id")
        if i in INVENTORY["centres"] and (c.get("x"), c.get("z")) != INVENTORY["centres"][i]:
            g0.append(f"spec {i}: coordinates differ from the frozen inventory {INVENTORY['centres'][i]}")
        if i in INVENTORY["causeway"]:
            if c.get("class") != "causeway" or (c.get("chain"), float(c.get("s0", -1)), float(c.get("s1", -1))) != INVENTORY["causeway"][i]:
                g0.append(f"spec {i}: {c.get('class')} chain {c.get('chain')} {c.get('s0')}-{c.get('s1')} != inventory {INVENTORY['causeway'][i]}")
        elif i in INVENTORY["other"] and c.get("class") != INVENTORY["other"][i]:
            g0.append(f"spec {i}: class {c.get('class')} != inventory {INVENTORY['other'][i]}")
    tids = [t.get("id") for t in rep.get("treated", [])]
    if sorted(tids) != sorted(INVENTORY["causeway"]):
        g0.append(f"report treated ids {tids} != inventory causeways {sorted(INVENTORY['causeway'])} (missing, duplicate or unexpected)")
    for t in rep.get("treated", []):
        i = t.get("id")
        if i in INVENTORY["causeway"] and (t.get("chain"), float(t.get("s0", -1)), float(t.get("s1", -1))) != INVENTORY["causeway"][i]:
            g0.append(f"report {i}: chain/interval differ from the inventory")
    if rep.get("inputs", {}).get("terrain_sha256") != res["inputs"]["before_sha256"]:
        g0.append("report input terrain hash is not the before terrain")
    if rep.get("output", {}).get("terrain_sha256") != res["inputs"]["after_sha256"]:
        g0.append("report output terrain hash is not the after terrain")
    if rep.get("inputs", {}).get("spec_sha256") != res["inputs"]["spec_sha256"]:
        g0.append("report spec hash is not the spec given here")
    rcl = {c.get("id"): c for c in rep.get("clusters", [])}
    if sorted(rcl) != want or len(rep.get("clusters", [])) != len(want):
        g0.append(f"report clusters {sorted(rcl)} != inventory {want}")
    for i in want:
        if i in rcl and (rcl[i].get("verdict") == "causeway") != (i in INVENTORY["causeway"]):
            g0.append(f"report cluster {i}: verdict {rcl[i].get('verdict')}")
    res["G0"] = g0
    fails += [f"G0 {m}" for m in g0]
    # ---- terrain and footprints
    zb, za = np.load(a.before), np.load(a.after)
    Hb, Ha = zb["heights"].astype(np.float64), za["heights"].astype(np.float64)
    ch = za["heights"] != zb["heights"]
    fpdir = os.path.join(a.work, "fp-after")
    subprocess.run([py, "-I", os.path.join(tools, "water", "pond_footprint_v31.py"), a.after, a.cover, fpdir, a.envelope],
                   check=True, stdout=subprocess.DEVNULL)
    fb, fa = np.load(a.before_fp), np.load(os.path.join(fpdir, "footprint.npz"))
    plb, pla = fb["plane"].astype(np.float64), fa["plane"].astype(np.float64)
    Wb, fpb_ = sr.corner_water(plb, fb["field"].astype(np.float64))
    Wa, fpa_ = sr.corner_water(pla, fa["field"].astype(np.float64))
    chains = road_chains()
    # ---- G1, G1L, G2 per inventory causeway (whatever the report says)
    per = []
    for cid, (chn, s0, s1) in sorted(INVENTORY["causeway"].items()):
        ax = Axis(chains[chn])
        m = (ax.s >= s0 - LINK_W - 20) & (ax.s <= s1 + LINK_W + 20)
        r0 = max(int((sr.ZTOP - (ax.p[m, 1].max() + 90)) / 6), 0); r1 = min(int((sr.ZTOP - (ax.p[m, 1].min() - 90)) / 6) + 1, sr.NC)
        c0 = max(int((ax.p[m, 0].min() - 90) / 6), 0); c1 = min(int((ax.p[m, 0].max() + 90) / 6) + 1, sr.NC)
        e = dict(id=cid, chain=chn, interval=[s0, s1])
        nb = int(round(s1 - s0)) + 1
        inner = {}
        for tag, H, W, fp, pl in (("before", Hb, Wb, fpb_, plb), ("after", Ha, Wa, fpa_, pla)):
            seg, q, v = waterline(sr, H, W, fp, pl, r0, r1, c0, c1)
            cel = seg["cell"]
            chc = ch[cel[:, 0], cel[:, 1]] | ch[cel[:, 0] + 1, cel[:, 1]] | ch[cel[:, 0], cel[:, 1] + 1] | ch[cel[:, 0] + 1, cel[:, 1] + 1]
            qchg = chc[cKDTree(seg["p"].mean(1)).query(q)[1]]
            sq, uq, okq = ax(q)
            for sg, nm in ((1, "left"), (-1, "right")):
                sel = okq & (np.sign(uq) == sg) & (sq >= s0 - 0.5) & (sq <= s1 + 0.5)
                b = np.clip(np.round(sq[sel] - s0).astype(int), 0, nb - 1)
                oq = np.abs(uq[sel])
                inn = np.full(nb, np.inf)
                np.minimum.at(inn, b, oq)
                near = oq <= inn[b] + 1.0
                vv = v[sel][near]; fin = np.isfinite(vv)
                cov = np.isfinite(inn)
                k0, k1 = int(R_END), nb - int(R_END)
                gaps, i = [], 0
                while i < nb:
                    if not cov[i]:
                        j = i
                        while j + 1 < nb and not cov[j + 1]:
                            j += 1
                        gaps.append((i, j)); i = j + 1
                    else:
                        i += 1
                bad_gaps = [[s0 + g[0], s0 + g[1]] for g in gaps if not (g[0] == 0 or g[1] == nb - 1) or g[1] - g[0] + 1 > R_END]
                r = dict(samples=int(near.sum()), wiggle_p90=round(float(np.percentile(vv[fin], 90)), 4) if fin.any() else None,
                         wiggle_max=round(float(vv[fin].max()), 4) if fin.any() else None,
                         coverage=round(float(cov.mean()), 4), coverage_inner=round(float(cov[k0:k1].mean()), 4),
                         gaps=[[s0 + g[0], s0 + g[1]] for g in gaps], bad_gaps=bad_gaps)
                for end, sc in (("link_s0", s0), ("link_s1", s1)):
                    ml = okq & (np.sign(uq) == sg) & (np.abs(sq - sc) <= LINK_W) & qchg & np.isfinite(v)
                    r[end] = dict(samples=int(ml.sum()), wiggle_p90=round(float(np.percentile(v[ml], 90)), 4) if ml.any() else None,
                                  wiggle_max=round(float(v[ml].max()), 4) if ml.any() else None)
                e[f"{nm}_{tag}"] = r
                if tag == "after":
                    inner[nm] = inn
                    if r["wiggle_p90"] is None or r["wiggle_p90"] > WIG_MAX:
                        fails.append(f"G1 {cid} {nm}: wiggle p90 {r['wiggle_p90']} > {WIG_MAX} over {s0}-{s1}")
                    if r["coverage_inner"] < COVER_MIN or bad_gaps:
                        fails.append(f"G1 {cid} {nm}: coverage inside {r['coverage_inner']} < {COVER_MIN} or gaps {bad_gaps}")
                    for end in ("link_s0", "link_s1"):
                        p = r[end]["wiggle_p90"]
                        if p is not None and p > LINK_WIG_MAX:
                            fails.append(f"G1L {cid} {nm} {end}: wiggle p90 {p} > {LINK_WIG_MAX}")
        w = inner["left"] + inner["right"]
        fin = np.isfinite(w)
        mid = w[nb // 4:3 * nb // 4]
        if not np.isfinite(mid).any():
            fails.append(f"G2 {cid}: no width in the middle of the run")
            per.append(e); continue
        wc = float(np.median(mid[np.isfinite(mid)]))
        K = fin & (np.abs(w - wc) <= WIDTH_TOL)
        best, cur, bs = 0, 0, 0
        for i, kv in enumerate(K):
            cur = cur + 1 if kv else 0
            if cur > best:
                best, bs = cur, i - cur + 1
        narrow = int((fin & (w < wc - WIDTH_TOL)).sum())
        drop = {}
        for nm in ("left", "right"):
            o, d = inner[nm], 0.0
            for rng in (range(bs + best, nb), range(bs - 1, -1, -1)):
                run = -np.inf
                for i in rng:
                    if np.isfinite(o[i]):
                        run = max(run, o[i]); d = max(d, run - o[i])
            drop[nm] = round(d, 4)
        e["width"] = dict(median=round(wc, 4), core=[s0 + bs, s0 + bs + best - 1], core_frac=round(best / nb, 4),
                          narrower_stations=narrow, outward_drop_max=drop, min=round(float(w[fin].min()), 3),
                          max=round(float(w[fin].max()), 3), finite=round(float(fin.mean()), 4))
        if best / nb < CORE_MIN:
            fails.append(f"G2 {cid}: constant-width stretch {best / nb:.3f} of the run < {CORE_MIN}")
        if narrow:
            fails.append(f"G2 {cid}: {narrow} stations narrower than {wc:.2f} - {WIDTH_TOL}")
        for nm, d in drop.items():
            if d > MONO_TOL:
                fails.append(f"G2 {cid} {nm}: offset falls {d} m going out from the constant-width stretch")
        per.append(e)
    res["causeways"] = per
    # ---- G3
    frozen = {n: int((ch & zb[n]).sum()) for n in ("platform", "narva", "v31_kit", "v31_bridge_cut", "v31_bridge_fill",
                                                     "v31_lagoon") if n in zb.files}
    res["G3_frozen_changed"] = frozen
    if any(frozen.values()):
        fails.append(f"G3 frozen vertices changed: {frozen}")
    for n in zb.files:
        if n != "heights" and not np.array_equal(zb[n], za[n], equal_nan=zb[n].dtype.kind == "f"):
            fails.append(f"G3 array {n} differs")
    extra = sorted(set(za.files) - set(zb.files))
    res["G3_new_arrays"] = extra
    if extra != ["v31_causeway"] or not np.array_equal(za["v31_causeway"], ch):
        fails.append(f"G3 output arrays: new {extra}, v31_causeway must be exactly the changed vertices")
    # ---- G4
    eb, ea = exposed(Hb, plb), exposed(Ha, pla)
    res["G4_new_exposed"] = int((ea & ~eb).sum())
    if res["G4_new_exposed"]:
        fails.append(f"G4 {res['G4_new_exposed']} new exposed border vertices")
    if a.bury_ref_terrain:
        bw = os.path.join(a.work, "bury")
        subprocess.run([py, "-I", os.path.join(tools, "water", "bury_edges_v31.py"), a.after, a.bury_ref_terrain, a.cover,
                        a.envelope, a.bury_ref_fp_report, os.path.join(a.work, "bury-terrain.npz"), bw,
                        os.path.join(a.work, "bury-report.json")], check=True, stdout=subprocess.DEVNULL)
        br = json.load(open(os.path.join(a.work, "bury-report.json")))
        res["G4_bury"] = dict(final_new_exposed=br["final_new_exposed"], changed_vs_input=br["changed_vs_input"])
        if br["final_new_exposed"] or br["changed_vs_input"]:
            fails.append(f"G4 bury_edges: {res['G4_bury']}")
    # ---- G5
    wb, wa = Hb < SEA, Ha < SEA
    Lb, nb_ = label(wb, S6); La, na_ = label(wa, S6)
    both = wb & wa
    pr = np.unique(np.stack([Lb[both], La[both]], 1), axis=0)
    cb = np.bincount(pr[:, 0], minlength=nb_ + 1)[1:]; ca = np.bincount(pr[:, 1], minlength=na_ + 1)[1:]
    topo = dict(before=int(nb_), after=int(na_), created=int((ca == 0).sum()), removed=int((cb == 0).sum()),
                split=int((cb > 1).sum()), merged=int((ca > 1).sum()))
    res["G5_sea_topology"] = topo
    if topo["created"] or topo["removed"] or topo["split"] or topo["merged"]:
        fails.append(f"G5 sea topology {topo}")
    # ---- G6
    cover = np.isfinite(np.load(a.cover)); env = np.isfinite(np.load(a.envelope))
    fpb, fpa = np.isfinite(plb), np.isfinite(pla)
    cminb = np.minimum.reduce([Hb[:-1, :-1], Hb[:-1, 1:], Hb[1:, :-1], Hb[1:, 1:]])
    cmina = np.minimum.reduce([Ha[:-1, :-1], Ha[:-1, 1:], Ha[1:, :-1], Ha[1:, 1:]])
    same = {n: bool(np.array_equal(fb[n], fa[n], equal_nan=True)) for n in ("plane", "field", "env_plane", "visible")}
    res["G6"] = dict(cover_outside_envelope=int((cover & ~env).sum()), footprint_identical=same,
                     new_pond_cells_over_sea=int((fpa & (cmina < SEA) & ~(fpb & (cminb < SEA))).sum()))
    if res["G6"]["cover_outside_envelope"] or res["G6"]["new_pond_cells_over_sea"] or not all(same.values()):
        fails.append(f"G6 ponds {res['G6']}")
    # ---- G7
    a0, b0 = slopes(Hb); a1, b1 = slopes(Ha)
    ca_ = ch[:-1, :-1] | ch[:-1, 1:] | ch[1:, 1:]; cb_ = ch[:-1, :-1] | ch[1:, :-1] | ch[1:, 1:]
    bad = 0
    for s0_, s1_, m in ((a0, a1, ca_), (b0, b1, cb_)):
        over0 = s0_ > SLOPE
        bad += int(((~over0 & (s1_ > SLOPE)) | (over0 & (s1_ > s0_ + 0.01)))[m].sum())
    res["G7_slope_crossings"] = bad
    res["max_changed_slope_deg"] = round(float(max(a1[ca_].max(initial=0), b1[cb_].max(initial=0))), 3)
    if bad:
        fails.append(f"G7 {bad} changed triangles cross {SLOPE} deg")
    # ---- G8 non-causeway clusters
    rr, cc = np.nonzero(ch)
    cx, cz = 6.0 * cc, 6.0 * 2047 - 6.0 * rr
    g8 = []
    for c in spec.get("clusters", []):
        if c.get("id") not in INVENTORY["other"]:
            continue
        x, z = INVENTORY["centres"][c["id"]]
        touched = int((np.hypot(cx - x, cz - z) <= CL_TOUCH_R).sum())
        longest, where = 0.0, None
        for k, raw in enumerate(chains):
            if len(raw) < 2 or np.min(np.hypot(raw[:, 0] - x, raw[:, 1] - z)) > CL_CENSUS_R + 50:
                continue
            for s_a, s_b in bilateral_runs(Hb, plb, raw, x, z):
                if s_b - s_a > longest:
                    longest, where = s_b - s_a, dict(chain=k, s0=s_a, s1=s_b)
        st = "PASS" if (not touched and longest < CL_L_MIN) else "FAIL"
        if st == "PASS" and not approval_granted(c.get("approval")):
            st = "PENDING"
        g8.append(dict(id=c["id"], cls=c["class"], changed_within_150m=touched, longest_bilateral_run_m=longest,
                       longest_run=where, approval=c.get("approval"), status=st))
        if touched:
            fails.append(f"G8 {c['id']}: {touched} changed vertices within {CL_TOUCH_R} m")
        if longest >= CL_L_MIN:
            fails.append(f"G8 {c['id']}: bilateral run {longest} m >= {CL_L_MIN}: it is a causeway")
        if st == "PENDING":
            pending.append(f"G8 {c['id']} ({c['class']}): excluded from the causeway rule, approval not recorded")
    res["G8_clusters"] = g8
    res["changed_vertices"] = int(ch.sum())
    res["fails"], res["pending"] = fails, pending
    res["verdict"] = "FAIL" if fails else ("PENDING" if pending else "PASS")
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(dict(verdict=res["verdict"], fails=fails, pending=pending), indent=1))
    sys.exit(1 if fails else (2 if pending else 0))


if __name__ == "__main__":
    main()
