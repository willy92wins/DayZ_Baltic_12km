"""Plan-view outline of the visible streambed sheet (flat CalmWater proxy, model y = road + 0.25, x +-7, z +-L/2) where
the terrain lies below it. Baltic (6 m grid, row 0 north) vs Chernarus (7.5 m grid, row 0 south), same method.
Usage: kit_outline.py <baltic terrain npz> <kit-records.json> <out dir>"""
import sys, json
import numpy as np
sys.path.insert(0, r"E:/DayZ-Baltic-Build/vanilla-tricks-20261013/scripts")
from terrain import Terrain, objects
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

tp, recp, out = sys.argv[1:4]
ROAD = {"long_straight": 0.21, "long_straight_2": 0.17, "short_straight": 0.17}
SHEET = 0.25


class Baltic:
    step = 6.0
    def __init__(self, p):
        self.h = np.load(p)["heights"].astype(np.float64)
    def y(self, x, z):
        x = np.asarray(x, float); z = np.asarray(z, float)
        fc_ = x / 6.0; fr_ = (12282.0 - z) / 6.0
        c = np.floor(fc_).astype(int); r = np.floor(fr_).astype(int)
        fc = fc_ - c; fr = fr_ - r
        H = self.h
        nw, ne, sw, se = H[r, c], H[r, c + 1], H[r + 1, c], H[r + 1, c + 1]
        return np.where(fc >= fr, nw + fc * (ne - nw) + fr * (se - ne), nw + fr * (sw - nw) + fc * (se - sw))
    def verts(self, x0, x1, z0, z1):
        cs = np.arange(int(np.ceil(x0 / 6)), int(x1 / 6) + 1); rs = np.arange(int(np.ceil((12282 - z1) / 6)), int((12282 - z0) / 6) + 1)
        C, R = np.meshgrid(cs, rs)
        return 6.0 * C, 12282.0 - 6.0 * R
    def edges(self, x0, x1, z0, z1):
        """Triangle edges: E-W, N-S and the NW-SE diagonal."""
        X, Z = self.verts(x0 - 6, x1 + 6, z0 - 6, z1 + 6)
        segs = []
        for dx, dz in ((6, 0), (0, -6), (6, -6)):
            for a, b in zip(X.ravel(), Z.ravel()):
                segs.append(((a, b), (a + dx, b + dz)))
        return segs


class Chern:
    def __init__(self):
        self.T = Terrain("chernarus"); self.step = self.T.step
    def y(self, x, z):
        return self.T.y(x, z)
    def verts(self, x0, x1, z0, z1):
        s = self.step
        cs = np.arange(int(np.ceil(x0 / s)), int(x1 / s) + 1); rs = np.arange(int(np.ceil(z0 / s)), int(z1 / s) + 1)
        C, R = np.meshgrid(cs, rs)
        return s * C, s * R
    def edges(self, x0, x1, z0, z1):
        s = self.step
        X, Z = self.verts(x0 - s, x1 + s, z0 - s, z1 + s)
        segs = []
        for dx, dz in ((s, 0), (0, s), (-s, s)):     # u+v=1 diagonal joins (c+1,r) and (c,r+1)
            for a, b in zip(X.ravel(), Z.ravel()):
                segs.append(((a, b), (a + dx, b + dz)))
        return segs


def kind(model):
    n = model.replace("/", "\\").split("\\")[-1].replace(".p3d", "")
    return n.split("_", 2)[2]


def pieces_baltic(recs):
    P = []
    for r in recs:
        if r["piece"] == "stones": continue
        m = r["matrix"]; R = np.array([m[0:3], m[3:6], m[6:9]]).T; T = np.array(m[9:12])
        k = kind(r["model"]); P.append((R, T, ROAD[k] + SHEET, 24.0 if k.startswith("long") else 12.0, r["site"]))
    return P


def pieces_chern():
    P = []
    for o in objects("chernarus"):
        s = o["shape"].lower()
        if "\\streambed\\" not in s or "\\misc\\" in s: continue
        k = kind(s)
        if k not in ROAD: continue
        R = np.array([[o["ax_x"], o["ay_x"], o["az_x"]], [o["ax_y"], o["ay_y"], o["az_y"]], [o["ax_z"], o["ay_z"], o["az_z"]]])
        T = np.array([o["x"], o["y"], o["z"]])
        P.append((R, T, ROAD[k] + SHEET, 24.0 if k.startswith("long") else 12.0, "chern"))
    return P


def sheet_at(p, wx, wz):
    """Model (x, z) of the sheet point above world (wx, wz) and its world y."""
    R, T, ys, L, _ = p
    A = np.array([[R[0, 0], R[0, 2]], [R[2, 0], R[2, 2]]])
    bx = wx - T[0] - R[0, 1] * ys; bz = wz - T[2] - R[2, 1] * ys
    inv = np.linalg.inv(A)
    mx = inv[0, 0] * bx + inv[0, 1] * bz; mz = inv[1, 0] * bx + inv[1, 1] * bz
    wy = T[1] + R[1, 0] * mx + R[1, 1] * ys + R[1, 2] * mz
    return mx, mz, wy


def water_mask(ter, P, X, Z):
    """Visible kit water: inside some piece's 14 x L sheet and terrain below that sheet; also bed band mask."""
    ty = ter.y(X, Z)
    wet = np.zeros(X.shape, bool); bed = np.zeros(X.shape, bool); top = np.full(X.shape, -1e9)
    for p in P:
        mx, mz, wy = sheet_at(p, X, Z)
        inside = (np.abs(mx) <= 7.0) & (np.abs(mz) <= p[3] / 2)
        wet |= inside & (ty < wy)
        bed |= (mx >= -2.4) & (mx <= 3.0) & (np.abs(mz) <= p[3] / 2)
        top = np.where(inside, np.maximum(top, wy), top)
    return wet, bed, ty, top


def stats(ter, P, near):
    """Per piece, every 0.5 m along model z (|z| <= L/2 - 1): visible half-widths of the wet run through the axis."""
    xs = np.arange(-7.0, 7.0001, 0.1)
    W, gaps, out_band, n = [], 0, 0, 0
    for p in P:
        R, T, ys, L, _ = p
        for mz in np.arange(-L / 2 + 1, L / 2 - 0.99, 0.5):
            pts = np.array([[mx, ys, mz] for mx in xs]) @ R.T + T
            wx, wz = pts[:, 0], pts[:, 2]
            wet, _, _, _ = water_mask(ter, near(p), wx, wz)
            n += 1
            i0 = len(xs) // 2
            if not wet[i0]:
                gaps += 1; continue
            l = i0
            while l > 0 and wet[l - 1]: l -= 1
            r = i0
            while r < len(xs) - 1 and wet[r + 1]: r += 1
            W.append((xs[l], xs[r]))
            if xs[l] < -2.4 or xs[r] > 3.0: out_band += 1
    W = np.array(W)
    w = W[:, 1] - W[:, 0] if len(W) else np.array([0.0])
    return {"samples": n, "axis_dry_share": round(gaps / max(n, 1), 3),
            "width_p10_50_90": np.percentile(w, [10, 50, 90]).round(2).tolist(),
            "width_std": round(float(w.std()), 2),
            "edge_outside_stone_band_share": round(out_band / max(n, 1), 3),
            "left_p10_50_90": np.percentile(W[:, 0], [10, 50, 90]).round(2).tolist() if len(W) else None,
            "right_p10_50_90": np.percentile(W[:, 1], [10, 50, 90]).round(2).tolist() if len(W) else None}


def neighbours(P):
    C = np.array([p[1][[0, 2]] for p in P])
    def near(p):
        d = np.hypot(*(C - p[1][[0, 2]]).T)
        return [P[i] for i in np.nonzero(d < 30)[0]]
    return near


def panel(ax, ter, P, x0, x1, z0, z1, title, res=0.1):
    xs = np.arange(x0, x1, res); zs = np.arange(z0, z1, res)
    X, Z = np.meshgrid(xs, zs)
    loc = [p for p in P if x0 - 20 < p[1][0] < x1 + 20 and z0 - 20 < p[1][2] < z1 + 20]
    wet, bed, ty, top = water_mask(ter, loc, X, Z)
    img = np.ones(X.shape + (3,)) * np.array([0.80, 0.78, 0.62])
    img[bed] = [0.55, 0.53, 0.50]
    img[wet] = [0.15, 0.45, 0.85]
    img[wet & ~bed] = [0.05, 0.25, 0.65]
    ax.imshow(img, origin="lower", extent=(x0, x1, z0, z1), interpolation="nearest")
    for (a, b) in ter.edges(x0, x1, z0, z1):
        ax.plot([a[0], b[0]], [a[1], b[1]], color="k", lw=0.25, alpha=0.35)
    VX, VZ = ter.verts(x0, x1, z0, z1)
    vy = ter.y(VX + 1e-6, VZ - 1e-6) if isinstance(ter, Baltic) else ter.y(VX + 1e-6, VZ + 1e-6)
    _, _, _, vtop = water_mask(ter, loc, VX, VZ)
    low = vy < vtop
    ax.plot(VX[low], VZ[low], "o", color="red", ms=3)
    ax.plot(VX[~low], VZ[~low], ".", color="k", ms=1.5)
    for p in loc:
        R, T, ys, L, _ = p
        a = T + R @ np.array([0, ys, -L / 2]); b = T + R @ np.array([0, ys, L / 2])
        ax.plot([a[0], b[0]], [a[2], b[2]], color="white", lw=0.6, ls="--")
    ax.set_xlim(x0, x1); ax.set_ylim(z0, z1); ax.set_aspect("equal"); ax.set_title(title, fontsize=9)


B = Baltic(tp); recs = json.load(open(recp))
PB = pieces_baltic(recs)
CH = Chern(); PC = pieces_chern()
RUNSTATS = False
res = {} if not RUNSTATS else {"baltic_kit118": stats(B, [p for p in PB if p[4] == "kit-118"], neighbours(PB)),
       "baltic_kit7": stats(B, [p for p in PB if p[4] == "kit-7"], neighbours(PB)),
       "chernarus_straight": stats(CH, PC[::4], neighbours(PC))}
if RUNSTATS:
    print(json.dumps(res, indent=1)); json.dump(res, open(out + "/kit-outline-stats.json", "w"), indent=1)

# Panels: Guillermo's camera spot on kit-118, then three Chernarus straight runs (different headings vs the grid)
def heading(p):
    return float(np.degrees(np.arctan2(p[0][0, 2], p[0][2, 2]))) % 180
picks = []
for target in (2, 90, 135):
    best = None
    for p in PC[::3]:
        h = heading(p)
        loc = [q for q in PC if np.hypot(*(q[1][[0, 2]] - p[1][[0, 2]])) < 30]
        if len(loc) >= 4 and min(abs(h - target), 180 - abs(h - target)) < 3:
            best = p; break
    if best is not None: picks.append(best)
fig, axs = plt.subplots(1, 1 + len(picks), figsize=(6 * (1 + len(picks)), 6.4))
cx, cz = 8258.0, 9050.0
panel(axs[0], B, PB, cx - 35, cx + 35, cz - 35, cz + 35, "Baltic kit-118 EV109 (camera 8275,9029)")
for ax, p in zip(axs[1:], picks):
    x, z = p[1][0], p[1][2]
    panel(ax, CH, PC, x - 35, x + 35, z - 35, z + 35, f"Chernarus ({x:.0f},{z:.0f}) heading {heading(p):.0f}")
plt.tight_layout(); plt.savefig(out + "/kit-outline.png", dpi=110)
print("ok")
