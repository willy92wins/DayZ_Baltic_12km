"""BALTIC-017 (Guillermo, 2026-10-11): lower the dry rim of the two large lakes to the surrounding terrain, never below
lake level + FLOOR_M, lake level unchanged.

For each lake (pond body of cls 2 containing an anchor vertex): rim = dry vertices within RIM_M of the lake's wet vertices.
Surroundings = normalized Gaussian (sigma SIG_M) of dry heights in the ring RING_IN..RING_OUT metres from the lake.
target = max(level + FLOOR_M, surroundings); new = min(H, target) blended: full up to FADE_IN, linear to 0 at RIM_M.
Never edits wet, reserve, platform or narva vertices; never raises a vertex.
Usage: lower_lake_rims_v31.py <in.npz> <out.npz> <report.json>
"""
import json, sys
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, label

LAKES = {"sw": (622.4, 840.0), "se": (10436.5, 308.2)}
FLOOR_M, RIM_M, FADE_IN, RING_IN, RING_OUT, SIG_M = 0.30, 24.0, 18.0, 36.0, 72.0, 24.0
COVER = "E:/DayZ-Baltic-Build/v30-shore-sdf-20261011/cover-level-ev98.npy"


def main():
    src, dst, rep_path = sys.argv[1:4]
    z = np.load(src)
    arrays = {k: z[k].copy() for k in z.files}
    H = arrays["heights"].astype(np.float64)
    cls, lvl = arrays["cls"], arrays["level"]
    W = arrays["water"] | (cls > 0)
    frozen = arrays["reserve"] | arrays["platform"] | arrays["narva"]
    Hn = H.copy()
    global VPLANE
    cov = np.load(COVER)
    VPLANE = np.full((2048, 2048), -np.inf)
    cc = np.where(np.isfinite(cov), cov, -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            VPLANE[dr:dr + 2047, dc:dc + 2047] = np.maximum(VPLANE[dr:dr + 2047, dc:dc + 2047], cc)
    report = dict(schema="lake-rims-v31.v1", params=dict(FLOOR_M=FLOOR_M, RIM_M=RIM_M, FADE_IN=FADE_IN, RING=[RING_IN, RING_OUT], SIG_M=SIG_M), lakes={})
    lab, _ = label(W & (cls == 2), np.ones((3, 3)))
    for name, (x, zz) in LAKES.items():
        r, c = int(round(2047 - zz / 6)), int(round(x / 6))
        win = lab[max(0, r - 3):r + 4, max(0, c - 3):c + 4]
        ids = np.unique(win[win > 0])
        assert len(ids) >= 1, name
        lake = np.isin(lab, ids)
        L = float(np.nanmedian(lvl[lake]))
        d = distance_transform_edt(~lake) * 6.0
        dry = ~W
        # keep the first vertex ring around ANY water unchanged: every waterline crossing keeps both endpoints,
        # so the visible water outline and topology cannot change (isolated wet specks stay isolated)
        from scipy.ndimage import binary_dilation
        bank_ring = binary_dilation(W, np.ones((3, 3)))
        rim = dry & (d > 0) & (d <= RIM_M) & ~frozen & ~bank_ring
        ring = dry & (d >= RING_IN) & (d <= RING_OUT)
        num = gaussian_filter(np.where(ring, H, 0.0), SIG_M / 6.0)
        den = gaussian_filter(ring.astype(np.float64), SIG_M / 6.0)
        surround = np.where(den > 1e-3, num / np.maximum(den, 1e-3), np.inf)
        # floor: every water level within RIM_M of the vertex (other ponds/streams may sit higher than this lake)
        wl = np.where(W & np.isfinite(lvl), lvl, -np.inf).astype(np.float64)
        wl = np.maximum(wl, VPLANE)  # actual pond-piece planes (can sit above the level array)
        from scipy.ndimage import maximum_filter
        near_max = maximum_filter(wl, size=2 * int(RIM_M / 6) + 1, mode="constant", cval=-np.inf)
        floor = np.maximum(L, near_max) + FLOOR_M
        target = np.maximum(floor, surround)
        fade = np.clip((RIM_M - d) / (RIM_M - FADE_IN), 0, 1)
        lowered = np.minimum(H, target)
        new = H + fade * (lowered - H)
        sel = rim & (new < H)
        before_p90 = float(np.percentile(H[rim & (d <= 12)] - L, 90))
        Hn[sel] = new[sel]
        after_p90 = float(np.percentile(Hn[rim & (d <= 12)] - L, 90))
        report["lakes"][name] = dict(anchor=[x, zz], level=round(L, 3), rim_vertices=int(rim.sum()), lowered_vertices=int(sel.sum()),
                                     lowering_m_q50_90_max=[round(float(v), 3) for v in np.quantile((H - Hn)[sel], [.5, .9, 1])] if sel.any() else None,
                                     rim0_12_p90_above_level_before=round(before_p90, 3), after=round(after_p90, 3),
                                     min_rim_above_level_after=round(float((Hn[rim] - L).min()), 3))
    ch = Hn != H
    assert not (ch & W).any() and not (ch & frozen).any() and not (Hn > H + 1e-9).any()
    arrays["heights"] = Hn.astype(np.float32)
    arrays["v31_lake_rim_lowered"] = ch
    np.savez(dst, **arrays)
    report["changed_vertices"] = int(ch.sum())
    open(rep_path, "w").write(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
