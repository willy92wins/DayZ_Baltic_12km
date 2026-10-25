"""BALTIC-020 (Guillermo, 2026-10-11: "acabar en laguna pequeña", radius >= 12-18 m, >= ~300 m2): a round terminal lagoon
at every inland river/stream end, as a terrain layer plus envelope seals for the v31 pond layer.

Ends: the inland_end entries of the 2026-10-11 survey (ends_v2_pieces.json), level L re-read from the nearest covered cell
of the current cover. Skipped (listed): ends with water at another level within R + RIM_M, whose disc/rim touches a
reserve/platform/narva vertex, or that would be perched (terrain below L + PERCH_FREE within R + PERCH_M outside the
inflow channel: the valley continues below the lagoon, which would need a dam; Guillermo rejected perched lakes, 017). Terrain, with d = distance to the end and s = SLOPE:
  inside  d <  R:            H = min(H, max(bed, L + s (d - R)))     bed = max(1.0, L - depth), depth 0.5 stream / 1.2 river
  rim     R <= d <= R+RIM_M: H = max(H, L + s (d - R))               except wet vertices and their neighbours (no channel is narrowed)
  outer   R <= d <= R+OUT_M: H = min(H, L + OUT_FREE + OUT_SLOPE (d - R))   (a 1:2 funnel where the end meets a slope;
                             a vertex touching a piece is not cut below its plane + OUT_FREE)
so the water line runs on the circle (linear in d across it), the inflow channel stays open and no wall is left.
Seals: cells with a corner within R + 6 m get plane L in the envelope unless they hold a base cell of another plane.
Usage: lagoons_v31.py <terrain.npz> <cover.npy> <envelope.npy> <ends.json> <out_terrain.npz> <out_envelope.npy> <report.json>
"""
import json, sys
import numpy as np
from scipy.ndimage import distance_transform_edt

R_STREAM, R_RIVER, RIM_M, SLOPE = 12.0, 15.0, 9.0, 0.15
PERCH_M, PERCH_FREE = 24.0, 0.30                  # skip when terrain within R..R+24 m (outside the inflow) is below L + 0.30
OUT_FREE, OUT_SLOPE, OUT_M = 0.30, 0.5, 15.0          # outer cap: no terrain above L + 0.30 + 0.5 (d - R) within R + 15 m
DEPTH = {6: 0.5, 5: 1.2, 3: 1.2}
BED_MIN, ZTOP = 1.0, 12282


def tri_slopes(H):
    nw, ne, sw, se = H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]
    return (np.degrees(np.arctan(np.hypot((ne - nw) / 6.0, (ne - se) / 6.0))),
            np.degrees(np.arctan(np.hypot((se - sw) / 6.0, (nw - sw) / 6.0))))


def offending(H, H0, s0, limit=35.0):
    """Corners of native triangles with a changed corner steeper than max(limit, base) (as sills_and_cones_ev102.py)."""
    ch = H != H0
    s1 = tri_slopes(H)
    out = np.zeros(H.shape, bool)
    for (a0, a1), corners in zip(zip(s0, s1), (((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 1), (1, 0)))):
        chc = np.zeros(a0.shape, bool)
        for dr, dc in corners:
            chc |= ch[dr:dr + 2047, dc:dc + 2047]
        bad = chc & (a1 > np.maximum(limit, a0))
        for dr, dc in corners:
            out[dr:dr + 2047, dc:dc + 2047] |= bad
    return out


def main():
    tpath, cpath, epath, endpath, out_t, out_e, rep_path = sys.argv[1:8]
    z = np.load(tpath); arrays = {k: z[k].copy() for k in z.files}
    H0 = arrays["heights"].astype(np.float64); H = H0.copy()
    frozen = arrays["reserve"] | arrays["platform"] | arrays["narva"]
    cover = np.load(cpath).astype(np.float64); env = np.load(epath).astype(np.float64)
    base = np.isfinite(cover)
    _, (ri, ci) = distance_transform_edt(~base, return_indices=True)
    vp = np.full(H.shape, np.nan)                                   # vertex plane (max of incident covered cells)
    cc = np.where(base, cover, -np.inf)
    t = np.full(H.shape, -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            t[dr:dr + 2047, dc:dc + 2047] = np.maximum(t[dr:dr + 2047, dc:dc + 2047], cc)
    vp = np.where(np.isfinite(t), t, np.nan)
    wet0 = np.isfinite(vp) & (H0 < vp)
    from scipy.ndimage import binary_dilation
    nearwet = binary_dilation(wet0 | (H0 < 0.75), np.ones((3, 3), bool))
    ends = [e for e in json.load(open(endpath, encoding="utf-8")) if e["cat"] == "inland_end"]
    done, skipped = [], []
    env_new = env.copy()
    for e in ends:
        r, c = int(e["row"]), int(e["col"])
        cr, cc_ = min(r, 2046), min(c, 2046)
        L = float(cover[ri[cr, cc_], ci[cr, cc_]])
        cls = int(e["cls"]); R = R_STREAM if cls == 6 else R_RIVER
        bed = max(BED_MIN, L - DEPTH.get(cls, 1.2))
        k = int(np.ceil((R + max(RIM_M, OUT_M) + 6) / 6))
        r0, r1, c0, c1 = max(0, r - k), min(2048, r + k + 1), max(0, c - k), min(2048, c + k + 1)
        yy, xx = np.mgrid[r0:r1, c0:c1]
        d = 6.0 * np.hypot(yy - r, xx - c)
        disc, rim = d < R, (d >= R) & (d <= R + RIM_M)
        sub = (slice(r0, r1), slice(c0, c1))
        other = np.isfinite(vp[sub]) & (np.abs(vp[sub] - L) > 0.05) & (d <= R + RIM_M) & wet0[sub]
        why = []
        if other.any(): why.append(f"other-level water ({int(other.sum())} vertices)")
        if (frozen[sub] & (d <= R + RIM_M)).any(): why.append("frozen in disc or rim")
        if bed >= L - 0.05: why.append("no depth above bed 1.0")
        k2 = int(np.ceil((R + PERCH_M) / 6))
        q0, q1, p0_, p1_ = max(0, r - k2), min(2048, r + k2 + 1), max(0, c - k2), min(2048, c + k2 + 1)
        qy, qx = np.mgrid[q0:q1, p0_:p1_]
        dq = 6.0 * np.hypot(qy - r, qx - c)
        inflow = np.isfinite(vp[q0:q1, p0_:p1_])                     # the stream's own piece vertices
        low = (dq >= R) & (dq <= R + PERCH_M) & ~inflow & (H0[q0:q1, p0_:p1_] < L + PERCH_FREE)
        if low.any(): why.append(f"perched: {int(low.sum())} vertices below level + {PERCH_FREE} within R + {PERCH_M:.0f} m")
        rec = dict(x=6 * c, z=6 * (2047 - r), cls=cls, level=round(L, 3), R=R, bed=round(bed, 3))
        if why:
            skipped.append({**rec, "why": why}); continue
        target = L + SLOPE * (d - R)
        hs = H[sub].copy()
        inside = np.minimum(hs, np.maximum(bed, target))
        outside = np.where(nearwet[sub], hs, np.maximum(hs, target))          # never raise next to existing water
        new = np.where(disc, inside, np.where(rim, outside, hs))
        cap = L + OUT_FREE + OUT_SLOPE * (d - R)
        # a vertex outside the disc that touches a piece keeps its piece edge buried: never cut below plane + OUT_FREE
        vps = vp[sub]
        cap = np.where(np.isfinite(vps), np.maximum(cap, np.minimum(hs, vps + OUT_FREE)), cap)
        new = np.where((d >= R) & (d <= R + OUT_M) & ~frozen[sub], np.minimum(new, cap), new)
        H[sub] = new
        # seals: cells with a corner within R + 6 m
        rr0, rr1, cc0, cc1 = max(0, r - k), min(2047, r + k), max(0, c - k), min(2047, c + k)
        cy, cx = np.mgrid[rr0:rr1, cc0:cc1]
        dmin = 6.0 * np.min([np.hypot(cy + dy - r, cx + dx - c) for dy in (0, 1) for dx in (0, 1)], axis=0)
        seal = dmin <= R + 6.0
        blk = base[rr0:rr1, cc0:cc1] & (np.abs(cover[rr0:rr1, cc0:cc1] - L) > 1e-4)
        env_sub = env_new[rr0:rr1, cc0:cc1]
        env_new[rr0:rr1, cc0:cc1] = np.where(seal & ~blk, L, env_sub)
        done.append({**rec, "dug_vertices": int((disc & (new < hs + 0)).sum()), "max_dig_m": round(float((hs - new).max()), 2),
                     "rim_raised": int((rim & (new > hs)).sum()), "outer_lowered": int(((d >= R) & (new < hs)).sum()), "seal_cells": int((seal & ~blk).sum())})
    # slope guard: halve the change at corners of offending triangles; after 12 passes drop it
    H = H.astype(np.float32).astype(np.float64)
    s0 = tri_slopes(H0); guard = 0
    for it in range(13):
        bad = offending(H, H0, s0)
        if not bad.any():
            break
        fix = bad & (H != H0); guard += int(fix.sum())
        H = np.where(fix, H0 if it == 12 else H0 + 0.5 * (H - H0), H).astype(np.float32).astype(np.float64)
    assert not offending(H, H0, s0).any()
    ch = H != H0
    assert not (ch & frozen).any()
    arrays["heights"] = H.astype(np.float32); arrays["v31_lagoon"] = ch
    np.savez(out_t, **arrays); np.save(out_e, env_new.astype(np.float32))
    rep = dict(schema="lagoons-v31.v1", params=dict(PERCH_M=PERCH_M, PERCH_FREE=PERCH_FREE, R_STREAM=R_STREAM, R_RIVER=R_RIVER, RIM_M=RIM_M, SLOPE=SLOPE, OUT_FREE=OUT_FREE, OUT_SLOPE=OUT_SLOPE, OUT_M=OUT_M, DEPTH=DEPTH, BED_MIN=BED_MIN),
               ends_inland=len(ends), built=len(done), slope_guard_vertex_fixes=guard, skipped=len(skipped), changed_vertices=int(ch.sum()),
               envelope_cells_added=int((np.isfinite(env_new) & ~np.isfinite(env)).sum()),
               envelope_cells_replanned=int((np.isfinite(env) & np.isfinite(env_new) & (env != env_new)).sum()),
               lagoons=done, skipped_list=skipped)
    json.dump(rep, open(rep_path, "w"), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if not k.endswith("_list") and k != "lagoons"}, indent=1))


if __name__ == "__main__":
    main()
