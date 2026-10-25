"""EV101 (Guillermo, 2026-10-12): smooth the engine-sea bed so depth has no plateaus with sharp edges.

Engine sea is tinted by depth; Astra's flat floors (delta -2.55 m, shelves -0.4 m, gulf -12 m) meet in one or two
6 m cells, so each plateau shows its own colour and the boundary follows the grid ("two colours, polygonal joint").

Sea vertices S = H < SEA and not touching a pond-piece cell. Frozen: every non-S vertex, the first S ring around them
(so every waterline crossing keeps both endpoints and the shoreline is bit-identical), narva, and reserve/platform
where dry (submerged bridge reserve is smoothed).
Free vertices take a normalized Gaussian of H over S (sigma SIG cells, frozen ring included as data), repeated ITER
times with the frozen values restored after each pass, then clamped:
  navigable (cls 3/4) deeper than NAV_OUT: new <= NAV_OUT  (draft stays >= 1.0 m, out of the 0.95-1.0 band)
  navigable in (NAV_OUT, NAV_MIN]:        new <= old       (stays navigable)
  any other free vertex below AWASH:       new <= AWASH     (never exposed by the wave trough)
  any other free vertex at/above AWASH:    new <= old
Usage: smooth_sea_bed_ev101.py <in.npz> <cover.npy> <out.npz> <report.json>
"""
import json, sys
import numpy as np
from scipy.ndimage import binary_dilation, gaussian_filter

SEA, AWASH, NAV_MIN, NAV_OUT = 0.75, 0.45, -0.20, -0.251
SIG, ITER = 1.5, 10
NAV_CLS = (3, 4)


def steps(H, S, thr):
    n = 0
    for a, b in ((np.s_[:, 1:], np.s_[:, :-1]), (np.s_[1:, :], np.s_[:-1, :])):
        n += int((S[a] & S[b] & (np.abs(H[a] - H[b]) > thr)).sum())
    return n


def main():
    src, cover_path, dst, rep_path = sys.argv[1:5]
    z = np.load(src)
    arrays = {k: z[k].copy() for k in z.files}
    H0 = arrays["heights"].astype(np.float64)
    cls = arrays["cls"]
    cov = np.load(cover_path)
    covered_cell = np.isfinite(cov)
    touch = np.zeros(H0.shape, bool)
    for dr in (0, 1):
        for dc in (0, 1):
            touch[dr:dr + 2047, dc:dc + 2047] |= covered_cell
    S = (H0 < SEA) & ~touch
    ring = S & binary_dilation(~S, np.ones((3, 3), bool))
    # reserve/platform freeze only where dry: under the sea there is no road surface, and a frozen submerged bridge
    # reserve would keep its plateau edge exactly at the crossings; narva stays frozen everywhere
    frozen = ~S | ring | arrays["narva"] | ((arrays["reserve"] | arrays["platform"]) & ~S)
    free = ~frozen
    w = gaussian_filter(S.astype(np.float64), SIG)
    H = H0.copy()
    for _ in range(ITER):
        num = gaussian_filter(np.where(S, H, 0.0), SIG)
        sm = num / np.maximum(w, 1e-9)
        H = np.where(free, sm, H0)
    nav = free & np.isin(cls, NAV_CLS)
    cap = np.where(nav & (H0 <= NAV_OUT), NAV_OUT,
          np.where(nav & (H0 <= NAV_MIN), H0,
          np.where(H0 < AWASH, AWASH, H0)))
    H = np.where(free, np.minimum(H, cap), H0)
    ch = H != H0
    assert not (ch & frozen).any() and not (H[S] >= SEA).any()
    assert not (nav & (H0 <= NAV_MIN) & (H > NAV_MIN)).any()
    win = np.s_[int(2047 - 11200 / 6):int(2047 - 8800 / 6), int(7500 / 6):int(9900 / 6)]
    rep = dict(schema="ev101-sea-bed.v1", params=dict(SEA=SEA, AWASH=AWASH, NAV_MIN=NAV_MIN, NAV_OUT=NAV_OUT, SIG_cells=SIG,
                                                      ITER=ITER, NAV_CLS=list(NAV_CLS)),
               sea_vertices=int(S.sum()), frozen_ring=int(ring.sum()), free=int(free.sum()), changed=int(ch.sum()),
               raised=int((H > H0).sum()), lowered=int((H < H0).sum()),
               change_m_q01_50_99=[round(float(v), 3) for v in np.quantile((H - H0)[ch], [.01, .5, .99])],
               nav_capped=int((nav & (H == cap) & ch).sum()))
    for thr in (0.5, 1.0, 2.0):
        rep[f"steps_gt_{thr}"] = dict(map_before=steps(H0, S, thr), map_after=steps(H, S, thr),
                                      spb_before=steps(H0[win], S[win], thr), spb_after=steps(H[win], S[win], thr))
    arrays["heights"] = H.astype(np.float32)
    arrays["ev101_sea_bed_smoothed"] = ch
    np.savez(dst, **arrays)
    open(rep_path, "w").write(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
