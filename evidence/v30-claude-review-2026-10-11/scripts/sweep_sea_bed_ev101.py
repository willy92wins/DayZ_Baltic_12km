import numpy as np, sys
from scipy.ndimage import binary_dilation, gaussian_filter
a = np.load("E:/DayZ-Baltic-Build/v31-ev100-pond-banks-20261012/terrain-ev100.npz")
H0 = a["heights"].astype(float); cls = a["cls"]
cov = np.load("E:/DayZ-Baltic-Build/v30-shore-sdf-20261011/cover-level-ev98.npy")
touch = np.zeros(H0.shape, bool)
for dr in (0, 1):
    for dc in (0, 1):
        touch[dr:dr+2047, dc:dc+2047] |= np.isfinite(cov)
S = (H0 < 0.75) & ~touch
ring = S & binary_dilation(~S, np.ones((3,3), bool))
frozen = ~S | ring | a["narva"] | ((a["reserve"] | a["platform"]) & ~S)
free = ~frozen
print("ring vertices", int(ring.sum()), "ring deeper than -1:", int((ring & (H0 < -1)).sum()), "deeper than -2:", int((ring & (H0 < -2)).sum()))
def run(sig, it):
    w = gaussian_filter(S.astype(float), sig); H = H0.copy()
    for _ in range(it):
        H = np.where(free, gaussian_filter(np.where(S, H, 0.0), sig) / np.maximum(w, 1e-9), H0)
    nav = free & np.isin(cls, (3, 4))
    cap = np.where(nav & (H0 <= -0.251), -0.251, np.where(nav & (H0 <= -0.2), H0, np.where(H0 < 0.45, 0.45, H0)))
    return np.where(free, np.minimum(H, cap), H0)
def cnt(H, thr):
    inter = rng = 0
    for A, B in ((np.s_[:, 1:], np.s_[:, :-1]), (np.s_[1:, :], np.s_[:-1, :])):
        m = S[A] & S[B] & (np.abs(H[A]-H[B]) > thr) & (np.maximum(H[A], H[B]) > -4)
        r_ = m & (ring[A] | ring[B]); rng += int(r_.sum()); inter += int((m & ~r_).sum())
    return inter, rng
print("base   >0.5", cnt(H0, .5), ">1.0", cnt(H0, 1.0))
for sig, it in ((3, 3), (1.0, 16), (1.0, 30), (1.5, 10), (2.0, 6)):
    H = run(sig, it)
    print(f"sig {sig} it {it}: >0.5 (interior, ring) {cnt(H, .5)}  >1.0 {cnt(H, 1.0)}  mean|dH| {np.abs(H-H0)[free].mean():.3f}")
