"""Negative controls for gate_despike_v31.py: each tampers with a copy of the despike output (or substitutes the input) and
must make the named gate(s) FAIL and the overall verdict FAIL. Prints one line per control and exits 0 only if every
control is detected. n12 runs the gate on its own input fixture and record list (both written next to the control and
removed after the run, like every tampered terrain); every other control keeps the real input and records.
  n11  a protected vertex that already stands > 0.5 m (the despike review's counterexample: G8 v1 only caught
       crossings of 0.5 m): its free ring neighbours go down 0.4 m, so it sharpens without crossing anything.
  n12  a vertex protected ONLY by a record disc (15 m of a kit record origin) sharpens when its two ring neighbours
       outside the disc go down: on a free, dry, flat patch with no envelope and no despike change within 60 m, the
       fixture input has the vertex at base + 1.0, its four ring neighbours inside the disc at base - 1.0 and the two
       outside it at base + 0.4 (prominence 0.6); the output lowers those two to base - 0.2 (prominence 1.2). A
       synthetic kit record 12 m west of the vertex is appended to the record list of both runs.
Usage: neg_controls_despike_v31.py <gate.py> <in.npz> <out.npz> <envelope.npy> <ref_fp.npz> <records.json> <neg_dir>
       --bury-tool .. --bury-ref .. --bury-cover .. --bury-refrep ..
"""
import argparse, json, os, shutil, subprocess, sys
import numpy as np
from scipy.ndimage import binary_dilation

N = 2048
NB6 = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]


def main():
    ap = argparse.ArgumentParser()
    for k in ("gate", "inp", "out", "envelope", "ref_fp", "records", "neg"):
        ap.add_argument(k)
    for k in ("--bury-tool", "--bury-ref", "--bury-cover", "--bury-refrep"):
        ap.add_argument(k)
    o = ap.parse_args()
    os.makedirs(o.neg, exist_ok=False)
    I = dict(np.load(o.inp)); O = dict(np.load(o.out))
    H0 = I["heights"].astype(np.float64); H1 = O["heights"].astype(np.float64)
    sys.path.insert(0, os.path.dirname(os.path.abspath(o.gate)))
    import gate_despike_v31 as g
    envp = np.load(o.envelope); ecell = np.isfinite(envp)
    corner = np.zeros((N, N), bool)
    for dr in (0, 1):
        for dc in (0, 1):
            corner[dr:dr + N - 1, dc:dc + N - 1] |= ecell
    frozen = I["reserve"] | I["platform"] | I["narva"]
    free_now = O["v31_despike"] | False
    changed = H1 != H0
    ctr = (slice(200, -200), slice(200, -200))

    def pick(mask):
        idx = np.argwhere(mask)
        idx = idx[(idx[:, 0] > 200) & (idx[:, 0] < N - 200) & (idx[:, 1] > 200) & (idx[:, 1] < N - 200)]
        return tuple(idx[len(idx) // 2])

    controls = []

    def ctl(name, expect, arrays, inp_arrays=None, records=None):
        controls.append((name, expect, arrays) + (() if inp_arrays is None else (inp_arrays, records)))

    ctl("n1-input-as-output", ["G1_reduction"], dict(I))
    a = dict(O); h = H1.copy(); r, c = pick(I["platform"]); h[r, c] += 0.2; a["heights"] = h.astype(np.float32)
    ctl("n2-platform-raised", ["G5_frozen"], a)
    fp = np.load(o.ref_fp); vis = np.isfinite(fp["plane"])
    vin = np.zeros((N, N), bool); vout = np.zeros((N, N), bool)
    for dr in (0, 1):
        for dc in (0, 1):
            vin[dr:dr + N - 1, dc:dc + N - 1] |= vis; vout[dr:dr + N - 1, dc:dc + N - 1] |= ~vis
    # outer footprint border vertex with an incident cell outside the envelope: closure cannot grow there, so a vertex
    # brought to plane + 0.02 (< EDGE_MARGIN 0.05) is an exposed piece edge that bury must raise
    noenv = np.zeros((N, N), bool)
    for dr in (0, 1):
        for dc in (0, 1):
            noenv[dr:dr + N - 1, dc:dc + N - 1] |= ~ecell
    vP = np.full((N, N), -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            vP[dr:dr + N - 1, dc:dc + N - 1] = np.maximum(vP[dr:dr + N - 1, dc:dc + N - 1], np.where(vis, fp["plane"], -np.inf))
    border = vin & vout & ~frozen & noenv & (H1 > vP + 0.3)
    a = dict(O); h = H1.copy(); r, c = pick(border); h[r, c] = vP[r, c] + 0.02; a["heights"] = h.astype(np.float32)
    ctl("n3-pond-edge-exposed", ["G2_bury"], a)
    flat = ~corner & ~I["water"] & ~frozen & (H0 > 5) & ~changed
    a = dict(O); h = H1.copy(); r, c = pick(flat); h[r, c] += 10.0; a["heights"] = h.astype(np.float32)
    ctl("n4-steep-spike", ["G6_slopes"], a)
    a = dict(O); lv = O["level"].copy(); r, c = pick(np.isfinite(lv)); lv[r, c] += 0.01; a["level"] = lv
    ctl("n5-water-level", ["G4_arrays"], a)
    a = dict(O); h = H1.copy(); r, c = pick(I["v31_kit"]); h[r, c] -= 0.1; a["heights"] = h.astype(np.float32)
    ctl("n6-kit-seat", ["G5_frozen"], a)
    a = dict(O); h = H1.copy(); back = changed & (np.arange(N)[:, None] % 4 == 0); h[back] = H0[back]; a["heights"] = h.astype(np.float32)
    ctl("n7-restore-quarter", ["G1_reduction"], a)
    recs = json.load(open(o.records)); kr = next(x for x in recs if "streambed" in x["model"])
    x, zz = kr["matrix"][9], kr["matrix"][11]
    rr, cc = np.mgrid[0:N, 0:N]
    d = np.hypot(6.0 * cc - x, 12282.0 - 6.0 * rr - zz)
    a = dict(O); h = H1.copy(); r, c = np.unravel_index(np.argmin(np.where((d > 10) & (d < 15), 0, 1) + np.where(I["v31_kit"], 1, 0)), d.shape)
    h[r, c] -= 0.05; a["heights"] = h.astype(np.float32)
    ctl("n8-near-kit-record", ["G7_seats"], a)
    # n9: sharpen a protected vertex by lowering its free ring
    pk, pt = g.prom(H1)
    prot_cand = np.argwhere(frozen & (pk > 0.30) & (pk < 0.5))
    found = None
    for (r, c) in prot_cand:
        h = H1.copy()
        for dr, dc in NB6:
            q = (r + dr, c + dc)
            if not frozen[q]:
                h[q] -= 0.6
        p2, _ = g.prom(h[r - 4:r + 5, c - 4:c + 5])
        if p2[4, 4] > 0.5:
            found = h; break
    assert found is not None, "n9: no protected vertex to sharpen"
    a = dict(O); a["heights"] = found.astype(np.float32)
    ctl("n9-protected-sharpened", ["G8_protected"], a)
    seaish = ~corner & ~I["water"] & ~frozen & (H0 > 0.8) & (H0 < 1.0)
    a = dict(O); h = H1.copy(); r, c = pick(seaish); h[r, c] = 0.7; a["heights"] = h.astype(np.float32)
    ctl("n10-new-sea-vertex", ["G5_frozen"], a)
    # n11: a protected vertex already > 0.5 m sharpens further (no crossing of 0.5 m)
    dom = g.protected_domain(I, np.asarray(envp, np.float64))
    disks = g.record_disks(recs)
    free8 = ~dom["protected"] & ~disks
    # EV112: the former exception swallowed isolated dry islands. Use an actual input island,
    # away from every seat, so G5 must reject its sea flip independently of other protections.
    hp = np.pad(H0, 1, mode="edge")
    nmax = np.maximum.reduce([hp[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] for dr, dc in NB6])
    islets = np.argwhere(free8 & ~corner & (H0 >= 0.80) & (nmax < 0.75))
    assert len(islets), "n13: no independent input island"
    r, c = islets[0]
    a = dict(O); h = H1.copy(); h[r, c] = 0.70; a["heights"] = h.astype(np.float32)
    ctl("n13-islet-sunk", ["G5_frozen"], a)
    m1 = np.maximum(pk, pt)
    info = {}
    found = None
    cand = np.concatenate([np.argwhere(dom["frozen"] & (m1 > 0.5)),
                           np.argwhere(dom["protected"] & ~dom["frozen"] & ~dom["border"] & (m1 > 0.5))])
    for (r, c) in cand:
        if not (10 < r < N - 10 and 10 < c < N - 10):
            continue
        nb = [(r + dr, c + dc) for dr, dc in NB6 if free8[r + dr, c + dc]]
        if not nb:
            continue
        h = H1.copy()
        for q in nb:
            h[q] -= 0.4
        p2, t2 = g.prom(h[r - 6:r + 7, c - 6:c + 7])
        if max(p2[6, 6], t2[6, 6]) > m1[r, c] + 0.1:
            found = h
            info["n11"] = dict(xz=[6 * int(c), 12282 - 6 * int(r)], before=float(m1[r, c]), after=float(max(p2[6, 6], t2[6, 6])),
                               lowered=len(nb))
            break
    assert found is not None, "n11: no protected vertex > 0.5 m with a free ring neighbour"
    a = dict(O); a["heights"] = found.astype(np.float32)
    ctl("n11-protected-gt0p5-sharpened", ["G8_protected"], a)
    # n12: protection by a record disc only (fixture input + synthetic kit record)
    pad = 10
    ok_patch = free8 & ~dom["corner"] & ~I["water"] & (H0 > 5)
    near_change = binary_dilation(changed, np.ones((3, 3), bool), iterations=pad)
    fix = None
    for (r, c) in np.argwhere(ok_patch & ~near_change):
        if not (300 < r < N - 300 and 300 < c < N - 300):
            continue
        sl = (slice(r - pad, r + pad + 1), slice(c - pad, c + pad + 1))
        if ok_patch[sl].all() and not near_change[sl].any() and np.ptp(H0[sl]) < 0.8:
            fix = (int(r), int(c))
            break
    r, c = fix
    base = float(H0[r, c])
    hi, ho = H0.copy(), H1.copy()
    sl = (slice(r - 3, r + 4), slice(c - 3, c + 4))
    hi[sl] = base; ho[sl] = base
    inside = [(-1, 0), (1, 0), (0, -1), (-1, -1)]          # N, S, W, NW: within 15 m of the record 12 m west
    outside = [(0, 1), (1, 1)]                             # E, SE: 18.0 and 19.0 m from it
    for H_ in (hi, ho):
        H_[r, c] = base + 1.0
        for dr, dc in inside:
            H_[r + dr, c + dc] = base - 1.0
    for dr, dc in outside:
        hi[r + dr, c + dc] = base + 0.4; ho[r + dr, c + dc] = base - 0.2
    x_v, z_v = 6.0 * c, 12282.0 - 6.0 * r
    tmpl = next(x_ for x_ in recs if "streambed" in x_["model"])
    syn = dict(model=tmpl["model"], matrix=list(tmpl["matrix"][:9]) + [x_v - 12.0, base, z_v])
    recs12 = list(recs) + [syn]
    pi, po = g.prom(hi[r - 6:r + 7, c - 6:c + 7]), g.prom(ho[r - 6:r + 7, c - 6:c + 7])
    info["n12"] = dict(xz=[x_v, z_v], record_xz=[x_v - 12.0, z_v], before=float(max(pi[0][6, 6], pi[1][6, 6])),
                       after=float(max(po[0][6, 6], po[1][6, 6])),
                       outside_m=[float(np.hypot(6.0 * dc + 12.0, 6.0 * dr)) for dr, dc in outside],
                       inside_m=[float(np.hypot(6.0 * dc + 12.0, 6.0 * dr)) for dr, dc in inside])
    a_in = dict(I); a_in["heights"] = hi.astype(np.float32)
    a = dict(O); a["heights"] = ho.astype(np.float32)
    ctl("n12-record-only-sharpened", ["G8_protected"], a, a_in, recs12)
    print("fixtures", json.dumps(info), flush=True)
    results, allok = [], True
    for name, expect, arrs, *extra in controls:
        d0 = os.path.join(o.neg, name); os.makedirs(d0)
        t = os.path.join(d0, "terrain.npz"); np.savez(t, **arrs)
        inp, rec_path, tmp = o.inp, o.records, [t]
        if extra:
            inp = os.path.join(d0, "input.npz"); np.savez(inp, **extra[0]); tmp.append(inp)
            rec_path = os.path.join(d0, "records.json")
            with open(rec_path, "w", encoding="utf-8") as f:
                json.dump(extra[1], f)
        cmd = [sys.executable, "-I", "-B", o.gate, inp, t, o.envelope, o.ref_fp, rec_path, os.path.join(d0, "gates"),
               "--bury-tool", o.bury_tool, "--bury-ref", o.bury_ref, "--bury-cover", o.bury_cover, "--bury-refrep", o.bury_refrep]
        pr = subprocess.run(cmd, capture_output=True, text=True)
        gj = json.load(open(os.path.join(d0, "gates", "gates.json")))
        failed = sorted(k for k, v in gj.items() if k.startswith("G") and not v["ok"])
        ok = pr.returncode != 0 and gj["overall"] == "FAIL" and all(e in failed for e in expect)
        allok &= ok
        results.append(dict(control=name, expect_fail=expect, failed=failed, overall=gj["overall"], rc=pr.returncode,
                            detected=ok, fixture=info.get(name[:3])))
        print(f"{name}: {'DETECTED' if ok else 'MISSED'}  expect {expect}  failed {failed}", flush=True)
        for f_ in tmp:
            os.remove(f_)
    json.dump(dict(results=results, all_detected=allok), open(os.path.join(o.neg, "negative-controls.json"), "w"), indent=1)
    print("NEGATIVE CONTROLS:", "PASS (all detected)" if allok else "FAIL")
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
