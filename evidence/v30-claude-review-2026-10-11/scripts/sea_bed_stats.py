import numpy as np
z = np.load("E:/DayZ-Baltic-Build/v31-ev100-pond-banks-20261012/terrain-ev100.npz")
H = z["heights"].astype(float); cls = z["cls"]
for k in range(8):
    m = cls == k
    if m.any() and k: print("cls", k, "n", int(m.sum()), "H q05/25/50/75/95", np.round(np.quantile(H[m], [.05,.25,.5,.75,.95]), 2), "share at -2.55:", round(float((np.abs(H[m]+2.55) < 0.02).mean()), 3))
sea = H < 0.75
# depth cliffs between neighbouring sea vertices
jump = np.zeros_like(H)
for a, b in ((np.s_[:, 1:], np.s_[:, :-1]), (np.s_[1:, :], np.s_[:-1, :])):
    both = sea[a] & sea[b]
    d = np.where(both, np.abs(H[a] - H[b]), 0)
    jump[a] = np.maximum(jump[a], d); jump[b] = np.maximum(jump[b], d)
print("sea vertices", int(sea.sum()), " with a >1.0 m step to a sea neighbour:", int((jump > 1.0).sum()), " >2.0 m:", int((jump > 2.0).sum()))
# bank cliffs: sea vertex deeper than -1.5 next to dry vertex above 0.95
dry = H > 0.95
cliff = np.zeros_like(sea)
for a, b in ((np.s_[:, 1:], np.s_[:, :-1]), (np.s_[1:, :], np.s_[:-1, :])):
    cliff[a] |= sea[a] & (H[a] < -1.5) & dry[b]; cliff[b] |= sea[b] & (H[b] < -1.5) & dry[a]
print("bank cliffs (sea < -1.5 m next to land > 0.95 m):", int(cliff.sum()), "by cls", np.bincount(cls[cliff].astype(int), minlength=8).tolist())
# SPB window
r0, r1, c0, c1 = int(2047-11200/6), int(2047-8800/6), int(7500/6), int(9900/6)
print("SPB window: cliffs", int(cliff[r0:r1, c0:c1].sum()), " depth steps >1 m", int((jump[r0:r1, c0:c1] > 1).sum()))
