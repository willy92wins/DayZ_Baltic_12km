import numpy as np, json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
z = np.load("E:/DayZ-Baltic-Build/v31-ev101-sea-bed-20261012/terrain-ev101.npz")
H = z["heights"].astype(float); plat = z["platform"] | z["reserve"]
cov = np.load("E:/DayZ-Baltic-Build/v30-shore-sdf-20261011/cover-level-ev98.npy")
J = json.load(open("junctions.json"))[:12]
fig, axs = plt.subplots(3, 4, figsize=(20, 15))
for ax, j in zip(axs.ravel(), J):
    x, zz = j["x"], j["z"]; R = 250
    c0, c1 = max(0, int((x-R)/6)), min(2046, int((x+R)/6)); r0, r1 = max(0, int(2047-(zz+R)/6)), min(2046, int(2047-(zz-R)/6))
    h = H[r0:r1, c0:c1]; cv = cov[r0:r1, c0:c1]; pl = plat[r0:r1, c0:c1]
    img = np.zeros(h.shape + (3,))
    land = h >= 0.75
    img[land] = [0.4, 0.6, 0.3]; img[~land] = [0.7, 0.72, 0.75]
    img[pl & land] = [0.9, 0.85, 0.7]
    img[np.isfinite(cv)] = [0.15, 0.35, 0.9]
    ax.imshow(img, extent=[6*c0, 6*c1, 6*(2047-r1), 6*(2047-r0)], interpolation="nearest")
    ax.set_title(f"({x},{zz}) cells {j['cells']} lvl {j['level']}")
fig.savefig("cand_grid.png", dpi=55, bbox_inches="tight")
