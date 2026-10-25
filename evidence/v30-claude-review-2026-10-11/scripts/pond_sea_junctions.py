import numpy as np, json
from scipy.ndimage import binary_dilation, label, minimum_filter
z = np.load("E:/DayZ-Baltic-Build/v31-ev100-pond-banks-20261012/terrain-ev100.npz")
H = z["heights"].astype(float); cls = z["cls"]
cov = np.load("E:/DayZ-Baltic-Build/v30-shore-sdf-20261011/cover-level-ev98.npy")
C = np.isfinite(cov)
# cell min height over its 4 vertices
cmin = np.minimum.reduce([H[:-1,:-1], H[1:,:-1], H[:-1,1:], H[1:,1:]])
sea_cell = (~C) & (cmin < 0.75)          # engine sea visible over this cell
k = np.ones((3,3), bool)
contact = C & binary_dilation(sea_cell, k)   # piece cells touching sea cells
lab, n = label(contact, k)
out = []
for i in range(1, n+1):
    m = lab == i
    rr, cc = np.nonzero(m)
    lv = cov[m]
    # cell class (vertex NW of the cell)
    cl = np.bincount(cls[rr, cc].astype(int), minlength=8)
    out.append(dict(x=round(6*(cc.mean()+0.5)), z=round(6*(2047-rr.mean()-0.5)), cells=int(m.sum()),
                    level=[round(float(lv.min()),2), round(float(lv.max()),2)], cls=cl.tolist()))
out.sort(key=lambda d: -d["cells"])
print("junction groups", n, "contact cells", int(contact.sum()))
for d in out[:40]: print(d)
# near the player
px, pz = 8697, 10023
near = [d for d in out if abs(d["x"]-px) < 900 and abs(d["z"]-pz) < 900]
print("near player:", len(near))
for d in near: print(d)
json.dump(out, open("junctions.json","w"))
