"""Local repair of road platforms against the road gate (Codex's definition), on the final vertex heights.

Stations whose cross, grade or chord value exceeds the repair threshold are grouped with their neighbours (+-12 m
along the chain); for each group the heights of every vertex under the group's gate samples are re-solved as a small
quadratic programme: stay as close as possible to the current heights, with every gate sample of every station in
the group inside a margin below the gate limits. Samples use the native NW-SE triangles, as the gate.
Usage: repair_roads_v30.py <terrain.npz> [--rounds 3]; rewrites heights in place (key "heights") and prints a report.
"""
import json
import sys

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.sparse import coo_matrix, diags, identity, vstack as svstack
from scipy.sparse.linalg import splu

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")
from verify_roads_v30 import LIMITS, NARVA, road_chains  # noqa: E402

N = 2048
MARGIN = {"cross_half": 0.0125, "grade": 0.061, "chord": 0.025}
TRIGGER = {"cross": 0.026, "grade": 0.0625, "chord": 0.026}
OFFSETS = np.arange(-4, 4.01, .5)


def bary(x, z):
    """Vertex (row, col) triples and weights of the native triangle under each point."""
    c = np.clip(np.asarray(x) / 6.0, 0, N - 1.000001)
    r = np.clip((12282 - np.asarray(z)) / 6.0, 0, N - 1.000001)
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    fc, fr = c - c0, r - r0
    up = fc >= fr
    # upper: nw + fc*(ne-nw) + fr*(se-ne) -> weights nw:1-fc, ne:fc-fr, se:fr
    # lower: nw + fr*(sw-nw) + fc*(se-sw) -> weights nw:1-fr, sw:fr-fc, se:fc
    ra = np.stack([r0, np.where(up, r0, r0 + 1), r0 + 1], 1)
    ca = np.stack([c0, np.where(up, c0 + 1, c0), c0 + 1], 1)
    wa = np.stack([np.where(up, 1 - fc, 1 - fr), np.where(up, fc - fr, fr - fc), np.where(up, fr, fc)], 1)
    return ra, ca, wa


def stations(p):
    station = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    s = np.linspace(0, station[-1], int(np.ceil(station[-1])) + 1)
    q = np.column_stack([np.interp(s, station, p[:, d]) for d in (0, 1)])
    tangent = np.gradient(q, axis=0)
    normal = np.column_stack([-tangent[:, 1], tangent[:, 0]]) / np.linalg.norm(tangent, axis=1)[:, None]
    return s, q, normal, station[-1]


def chain_values(h, s, q, normal):
    pts = q[None, :, :] + OFFSETS[:, None, None] * normal[None, :, :]
    ra, ca, wa = bary(pts[..., 0].ravel(), pts[..., 1].ravel())
    elev = (h[ra, ca] * wa).sum(1).reshape(len(OFFSETS), len(s))
    centre = elev[8]
    cross = np.ptp(elev, axis=0)
    grade = np.r_[np.abs(np.diff(centre) / np.diff(s)), 0]
    chord = np.zeros(len(s))
    if len(s) > 6:
        chord[3:-3] = np.abs(centre[3:-3] - (centre[:-6] + centre[6:]) / 2)
    return cross, grade, chord


def solve_group(h, s, q, normal, idx, fixed=None):
    """Re-solve the vertices under the samples of stations idx (contiguous, one chain)."""
    pts = q[idx][None, :, :] + OFFSETS[:, None, None] * normal[idx][None, :, :]
    ra, ca, wa = bary(pts[..., 0].ravel(), pts[..., 1].ravel())
    flat = ra * N + ca
    verts, inv = np.unique(flat.ravel(), return_inverse=True)
    inv = inv.reshape(flat.shape)
    nv, ns = len(verts), len(idx)
    is_fixed = fixed.ravel()[verts] if fixed is not None else np.zeros(nv, bool)
    nsamp = len(OFFSETS) * ns
    rows = np.repeat(np.arange(nsamp), 3)
    smat = coo_matrix((wa.ravel(), (rows, inv.ravel())), shape=(nsamp, nv)).tocsr()   # sample = smat @ hv
    centre = smat[8 * ns:9 * ns]
    blocks, lo, hi = [], [], []
    for o in range(len(OFFSETS)):
        if o == 8:
            continue
        blocks.append(smat[o * ns:(o + 1) * ns] - centre)
        lo.append(np.full(ns, -MARGIN["cross_half"]))
        hi.append(np.full(ns, MARGIN["cross_half"]))
    ds = np.diff(s[idx])
    blocks.append(centre[1:] - centre[:-1])
    lo.append(-MARGIN["grade"] * ds)
    hi.append(MARGIN["grade"] * ds)
    if ns > 6:
        blocks.append(centre[3:-3] - 0.5 * (centre[:-6] + centre[6:]))
        lo.append(np.full(ns - 6, -MARGIN["chord"]))
        hi.append(np.full(ns - 6, MARGIN["chord"]))
    a = svstack(blocks).tocsr()
    lo, hi = np.concatenate(lo), np.concatenate(hi)
    h0 = h.ravel()[verts].astype(float)
    if is_fixed.any():
        const = a[:, np.flatnonzero(is_fixed)] @ h0[is_fixed]
        lo, hi = lo - const, hi - const
        a = a[:, np.flatnonzero(~is_fixed)]
        verts, h0 = verts[~is_fixed], h0[~is_fixed]
        nv = len(verts)
        if nv == 0:
            return verts, h0, 0.0
    # ADMM on min |x - h0|^2 with lo <= A x <= hi (small, so a fixed rho converges quickly).
    rho, sigma, alpha = 50.0, 1e-6, 1.6
    pm = identity(nv, format="csr")
    lu = splu((pm + sigma * identity(nv) + rho * (a.T @ a)).tocsc())
    x, z, y = h0.copy(), a @ h0, np.zeros(a.shape[0])
    for it in range(20000):
        xt = lu.solve(sigma * x + h0 + a.T @ (rho * z - y))
        zt = a @ xt
        x = alpha * xt + (1 - alpha) * x
        zr = alpha * zt + (1 - alpha) * z
        zn = np.clip(zr + y / rho, lo, hi)
        y = y + rho * (zr - zn)
        z = zn
        if it % 50 == 49:
            ax = a @ x
            if np.max(np.maximum(ax - hi, lo - ax)) < 2e-4:
                break
    return verts, x, float(np.abs(x - h0).max())


def repair(h, water, rounds=3, log=print, fixed=None):
    wd = distance_transform_edt(~water) * 6
    report = {"rounds": []}
    for rnd in range(rounds):
        groups = 0
        moved = 0.0
        flagged_total = 0
        for number, p in enumerate(road_chains()):
            if len(p) < 4:
                continue
            s, q, normal, length = stations(p)
            rr = np.clip(np.rint((12282 - q[:, 1]) / 6).astype(int), 0, N - 1)
            cc = np.clip(np.rint(q[:, 0] / 6).astype(int), 0, N - 1)
            valid = (wd[rr, cc] > LIMITS["water_clear_m"]) & (np.linalg.norm(q - NARVA, axis=1) > LIMITS["narva_clear_m"]) \
                & (s > LIMITS["end_margin_m"]) & (s < length - LIMITS["end_margin_m"])
            cross, grade, chord = chain_values(h, s, q, normal)
            flag = valid & ((cross > TRIGGER["cross"]) | (grade > TRIGGER["grade"]) | (chord > TRIGGER["chord"]))
            if not flag.any():
                continue
            flagged_total += int(flag.sum())
            # Contiguous groups of flagged stations, padded by 12 m and kept inside the chain.
            pad = np.convolve(flag.astype(int), np.ones(25, int), mode="same") > 0
            edges = np.flatnonzero(np.diff(np.r_[0, pad.astype(int), 0]))
            for a0, a1 in zip(edges[::2], edges[1::2]):
                idx = np.arange(max(a0, 0), min(a1, len(s)))
                if len(idx) < 3:
                    continue
                verts, x, dmax = solve_group(h, s, q, normal, idx, fixed)
                hv = h.reshape(-1)
                hv[verts] = x.astype(h.dtype)
                groups += 1
                moved = max(moved, dmax)
        report["rounds"].append({"round": rnd, "flagged_stations": flagged_total, "groups": groups, "max_change_m": round(moved, 4)})
        log(json.dumps(report["rounds"][-1]))
        if flagged_total == 0:
            break
    return h, report


def main():
    path = sys.argv[1]
    data = dict(np.load(path))
    h = data["heights"].astype("float64")
    h, report = repair(h, data["water"].astype(bool), rounds=int(sys.argv[sys.argv.index("--rounds") + 1]) if "--rounds" in sys.argv else 3,
                       fixed=data["narva"].astype(bool) if "narva" in data else None)
    data["heights"] = h.astype("float32")
    np.savez_compressed(path, **data)
    print(json.dumps(report))


if __name__ == "__main__":
    main()
