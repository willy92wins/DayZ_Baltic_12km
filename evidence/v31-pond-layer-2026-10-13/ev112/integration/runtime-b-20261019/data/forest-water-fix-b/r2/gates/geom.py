"""Exact geometry for the G1/G4 gates (independent of the placer's raster and ring sampling).

disc_min: exact minimum over a disc of the planar terrain (NW-SE triangles) minus a per-cell reference level. On each
triangle the function is linear, so its minimum over (disc intersected with triangle) is reached at a triangle vertex
inside the disc, at an edge-circle intersection, at the circle point opposite the gradient, or at the centre."""
import math
import sys

import numpy as np

N, ZTOP = 2048, 12282


def _tri_vertices(r, c, upper):
    x0, z0 = 6.0 * c, ZTOP - 6.0 * r
    nw = (x0, z0)
    se = (x0 + 6.0, z0 - 6.0)
    mid = (x0 + 6.0, z0) if upper else (x0, z0 - 6.0)
    return nw, mid, se


def disc_min(H, px, pz, R, level_fn):
    """Minimum over the disc of h - level, level_fn(r, c) -> per-cell level array (NaN = cell not concerned).
    Returns +inf where no concerned cell meets the disc."""
    px, pz, R = np.asarray(px, float), np.asarray(pz, float), np.asarray(R, float)
    n = len(px)
    best = np.full(n, np.inf)
    k = int(math.ceil(float(R.max()) / 6.0)) + 1 if n else 0
    r0 = np.floor((ZTOP - pz) / 6.0).astype(int)
    c0 = np.floor(px / 6.0).astype(int)
    for dr in range(-k, k + 1):
        for dc in range(-k, k + 1):
            r, c = r0 + dr, c0 + dc
            inside_map = (r >= 0) & (r <= N - 2) & (c >= 0) & (c <= N - 2)
            rr, cc = np.clip(r, 0, N - 2), np.clip(c, 0, N - 2)
            lvl = level_fn(rr, cc)
            con = inside_map & np.isfinite(lvl)
            # cell square to disc distance pre-check
            cx0, cz1 = 6.0 * cc, ZTOP - 6.0 * rr
            ddx = np.maximum(np.maximum(cx0 - px, 0), px - cx0 - 6.0)
            ddz = np.maximum(np.maximum((cz1 - 6.0) - pz, 0), pz - cz1)
            con &= np.hypot(ddx, ddz) <= R
            if not con.any():
                continue
            idx = np.flatnonzero(con)
            for upper in (True, False):
                (ax, az), (bx, bz), (qx, qz) = _tri_vertices(rr[idx], cc[idx], upper)
                ha = H[rr[idx], cc[idx]]
                hb = H[rr[idx], cc[idx] + 1] if upper else H[rr[idx] + 1, cc[idx]]
                hq = H[rr[idx] + 1, cc[idx] + 1]
                ax, az = np.broadcast_to(ax, idx.shape).astype(float), np.broadcast_to(az, idx.shape).astype(float)
                bx, bz = np.broadcast_to(bx, idx.shape).astype(float), np.broadcast_to(bz, idx.shape).astype(float)
                qx, qz = np.broadcast_to(qx, idx.shape).astype(float), np.broadcast_to(qz, idx.shape).astype(float)
                # plane through the three vertices: h = h0 + gx (x - ax) + gz (z - az)
                det = (bx - ax) * (qz - az) - (qx - ax) * (bz - az)
                gx = ((hb - ha) * (qz - az) - (hq - ha) * (bz - az)) / det
                gz = ((bx - ax) * (hq - ha) - (qx - ax) * (hb - ha)) / det
                P, Z, Rr, L = px[idx], pz[idx], R[idx], lvl[idx]
                cands = [(ax, az), (bx, bz), (qx, qz), (P, Z)]
                gn = np.hypot(gx, gz)
                cands.append((P - Rr * np.where(gn > 0, gx / np.where(gn > 0, gn, 1), 0), Z - Rr * np.where(gn > 0, gz / np.where(gn > 0, gn, 1), 0)))
                for (ux, uz), (vx, vz) in (((ax, az), (bx, bz)), ((bx, bz), (qx, qz)), ((qx, qz), (ax, az))):
                    dx, dz = vx - ux, vz - uz
                    fx, fz = ux - P, uz - Z
                    A_ = dx * dx + dz * dz
                    B_ = 2 * (fx * dx + fz * dz)
                    C_ = fx * fx + fz * fz - Rr * Rr
                    disc = B_ * B_ - 4 * A_ * C_
                    sq = np.sqrt(np.maximum(disc, 0))
                    for sgn in (-1, 1):
                        t = (-B_ + sgn * sq) / (2 * A_)
                        t = np.where(disc >= 0, t, -1.0)
                        cands.append((ux + np.clip(t, 0, 1) * dx, uz + np.clip(t, 0, 1) * dz))
                for (cx, cz) in cands:
                    # inside triangle (barycentric, tolerance) and inside disc
                    l1 = ((bz - qz) * (cx - qx) + (qx - bx) * (cz - qz)) / ((bz - qz) * (ax - qx) + (qx - bx) * (az - qz))
                    l2 = ((qz - az) * (cx - qx) + (ax - qx) * (cz - qz)) / ((bz - qz) * (ax - qx) + (qx - bx) * (az - qz))
                    l3 = 1 - l1 - l2
                    ok = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9) & (np.hypot(cx - P, cz - Z) <= Rr + 1e-9)
                    val = ha + gx * (cx - ax) + gz * (cz - az) - L
                    best[idx] = np.where(ok, np.minimum(best[idx], val), best[idx])
    return best


def h_at(H, x, z):
    c = np.clip(np.asarray(x, float) / 6.0, 0, N - 1.000001)
    r = np.clip((ZTOP - np.asarray(z, float)) / 6.0, 0, N - 1.000001)
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    fc, fr = c - c0, r - r0
    nw, ne, sw, se = H[r0, c0], H[r0, c0 + 1], H[r0 + 1, c0], H[r0 + 1, c0 + 1]
    return np.where(fc >= fr, nw + fc * (ne - nw) + fr * (se - ne), nw + fr * (sw - nw) + fc * (se - sw))


def road_segments():
    sys.path.insert(0, r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\tools\terrain")
    from verify_roads_v30 import road_chains
    A, B = [], []
    for p in road_chains():
        p = np.asarray(p, float)
        if len(p) < 2:
            continue
        A.append(p[:-1]); B.append(p[1:])
    return np.vstack(A), np.vstack(B)


def seg_distance(px, pz, A, B, reach):
    from scipy.spatial import cKDTree
    mid = (A + B) / 2
    half = np.hypot(*(B - A).T) / 2
    tree = cKDTree(mid)
    d = np.full(len(px), np.inf)
    lists = tree.query_ball_point(np.c_[px, pz], r=reach + half.max())
    for i, L in enumerate(lists):
        if not L:
            continue
        a, b = A[L], B[L]
        e = b - a
        t = np.clip(((px[i] - a[:, 0]) * e[:, 0] + (pz[i] - a[:, 1]) * e[:, 1]) / np.maximum((e * e).sum(1), 1e-12), 0, 1)
        d[i] = np.hypot(px[i] - a[:, 0] - t * e[:, 0], pz[i] - a[:, 1] - t * e[:, 1]).min()
    return d


def poly_distance(px, pz, poly):
    poly = np.asarray(poly, float)
    d = np.full(len(px), np.inf)
    ins = np.zeros(len(px), bool)
    for (xa, za), (xb, zb) in zip(poly, np.roll(poly, -1, axis=0)):
        ex, ez = xb - xa, zb - za
        t = np.clip(((px - xa) * ex + (pz - za) * ez) / max(ex * ex + ez * ez, 1e-12), 0, 1)
        d = np.minimum(d, np.hypot(px - xa - t * ex, pz - za - t * ez))
        cond = (za > pz) != (zb > pz)
        xi = xa + (pz - za) * (xb - xa) / (zb - za if zb != za else 1e-12)
        ins ^= cond & (px < xi)
    return np.where(ins, 0.0, d)


def flagged_cell_distance(mask, px, pz, reach):
    """Distance to the union of 6 m cells with any flagged corner."""
    cm = mask[:-1, :-1] | mask[1:, :-1] | mask[:-1, 1:] | mask[1:, 1:]
    rr, cc = np.nonzero(cm)
    if not rr.size:
        return np.full(len(px), np.inf)
    from scipy.spatial import cKDTree
    cxm, czm = 6.0 * cc + 3.0, ZTOP - 6.0 * rr - 3.0
    tree = cKDTree(np.c_[cxm, czm])
    d = np.full(len(px), np.inf)
    for i, L in enumerate(tree.query_ball_point(np.c_[px, pz], r=reach + 4.25)):
        if not L:
            continue
        x0, z1 = cxm[L] - 3.0, czm[L] + 3.0
        ddx = np.maximum(np.maximum(x0 - px[i], 0), px[i] - x0 - 6.0)
        ddz = np.maximum(np.maximum(z1 - 6.0 - pz[i], 0), pz[i] - z1)
        d[i] = np.hypot(ddx, ddz).min()
    return d
