import numpy as np, sys, json
from scipy.ndimage import label, binary_dilation, find_objects
cov = np.load("E:/DayZ-Baltic-Build/v30-shore-sdf-20261011/cover-level-ev98.npy")
VP = np.full((2048, 2048), -np.inf); cc = np.where(np.isfinite(cov), cov, -np.inf)
for dr in (0, 1):
    for dc in (0, 1):
        VP[dr:dr+2047, dc:dc+2047] = np.maximum(VP[dr:dr+2047, dc:dc+2047], cc)
WPL = np.where(np.isfinite(VP), VP, 0.75)
a = np.load(sys.argv[1]); b = np.load(sys.argv[2])
H0 = a["heights"]; H1 = b["heights"]; road = a["reserve"] | a["platform"]; touch = np.isfinite(VP); cls = a["cls"]
w0 = H0 < WPL; w1 = H1 < WPL
s4 = np.array([[0,1,0],[1,1,1],[0,1,0]])
L1, n1 = label(w1, s4); L0, _ = label(w0, s4)
sz1 = np.bincount(L1.ravel())
dried = w0 & ~w1
D, nd = label(dried, np.ones((3, 3)))
res = []
for i, sl in enumerate(find_objects(D), 1):
    sl2 = tuple(slice(max(0, s.start - 2), s.stop + 2) for s in sl)
    m = D[sl2] == i
    ring = binary_dilation(m, np.ones((3, 3), bool))
    labs = [l for l in np.unique(L1[sl2][ring]) if l and sz1[l] >= 9]
    if len(labs) < 2: continue
    bodies = {}
    for l in labs:
        bodies.setdefault(int(np.bincount(L0[L1 == l]).argmax()), []).append(int(sz1[l]))
    for bdy, parts in bodies.items():
        if len(parts) >= 2:
            rr, c_ = np.nonzero(m); rr = rr + sl2[0].start; c_ = c_ + sl2[1].start
            near_road = bool(road[max(0, rr.min()-4):rr.max()+5, max(0, c_.min()-4):c_.max()+5].any())
            res.append(dict(x=int(6*c_.mean()), z=int(6*(2047-rr.mean())), dried=int(m.sum()), by="cone" if near_road else "sill",
                            parts=sorted(parts, reverse=True), cls=np.bincount(cls[rr, c_].astype(int), minlength=8).tolist()))
res.sort(key=lambda d: -d["parts"][1])
print(len(res), "cut sites")
for d in res: print(d)
json.dump(res, open(sys.argv[3], "w"), indent=1)
