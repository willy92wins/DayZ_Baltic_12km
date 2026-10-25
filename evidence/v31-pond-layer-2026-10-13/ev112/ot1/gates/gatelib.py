"""Shared helpers of the EV112 kit gates (v9 rollout; EV110 helpers unchanged except OUT, load() skipping skipped sites
and the stones/chain helpers at the end) (independent of streambed_kit_v31.py: own face transform, point-in-triangle,
terrain interpolation and polyline projection). Faces come from streambed_kit_geometry_v31.json (ODOL roadway LOD and
water proxy LOD0, see extract_streambed_geometry_v31.py); quads are split (0,1,2)+(0,2,3)."""
import json
import numpy as np

ZTOP = 12282.0
WT = "C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c"
GEOM = WT + "/tools/water/streambed_kit_geometry_v31.json"
if not __import__("os").path.exists(GEOM):                      # before the worktree copy exists: the scratch copy
    GEOM = __import__("os").path.join(__import__("os").path.dirname(__file__), "streambed_kit_geometry_v31.json")
B = "E:/DayZ-Baltic-Build/v31-pond-layer-20261013"
OUT = B + "/ev112-ot1-20261018/run-a"
CHAIN = B + "/ev112-ot1-20261018/chain-step1.json"


def terrain_y(H, x, z):
    x = np.asarray(x, float); z = np.asarray(z, float)
    fc_ = x / 6.0; fr_ = (ZTOP - z) / 6.0
    c = np.floor(fc_).astype(int); r = np.floor(fr_).astype(int)
    fc = fc_ - c; fr = fr_ - r
    nw, ne, sw, se = H[r, c], H[r, c + 1], H[r + 1, c], H[r + 1, c + 1]
    return np.where(fc >= fr, nw + fc * (ne - nw) + fr * (se - ne), nw + fr * (sw - nw) + fc * (se - sw))


def model_name(model):
    return model.replace("/", "\\").split("\\")[-1][:-4][len("streambed_"):]


class Piece:
    def __init__(self, rec, models):
        m = rec["matrix"]
        self.M = np.array([m[0:3], m[3:6], m[6:9]], float).T; self.T = np.array(m[9:12], float)
        self.rec = rec; self.name = model_name(rec["model"]); self.kind = self.name.split("_", 1)[1]
        g = models[self.name]; self.g = g
        self.scale = float(np.linalg.norm(self.M[:, 1]))
        self.road = []; self.road_ext = []
        for f in g["road"]:
            v = np.array(f["v"], float) @ self.M.T + self.T
            for j in range(1, len(v) - 1):
                self.road.append(v[[0, j, j + 1]]); self.road_ext.append(f["tex"].startswith("water_ext"))
        self.water = []
        for f in g["water"]:
            v = np.array(f, float) @ self.M.T + self.T
            for j in range(1, len(v) - 1):
                self.water.append(v[[0, j, j + 1]])
        self.road = np.array(self.road); self.road_ext = np.array(self.road_ext); self.water = np.array(self.water)
        allv = np.vstack([self.road.reshape(-1, 3), self.water.reshape(-1, 3)])
        self.lo = allv[:, [0, 2]].min(0); self.hi = allv[:, [0, 2]].max(0)
        self.centre_model = np.array(g["centre"], float)

    def world(self, pm):
        return np.asarray(pm, float) @ self.M.T + self.T


def tri_max(tris, P, out):
    """out = max(out, height of each triangle containing P (plan xz))."""
    for t in tris:
        a, b, c = t[:, [0, 2]]
        lo = np.minimum(np.minimum(a, b), c) - 1e-9; hi = np.maximum(np.maximum(a, b), c) + 1e-9
        m = (P[:, 0] >= lo[0]) & (P[:, 0] <= hi[0]) & (P[:, 1] >= lo[1]) & (P[:, 1] <= hi[1])
        if not m.any():
            continue
        idx = np.nonzero(m)[0]; Q = P[idx]
        v0, v1 = b - a, c - a; d = Q - a
        den = v0[0] * v1[1] - v0[1] * v1[0]
        if abs(den) < 1e-12:
            continue
        u = (d[:, 0] * v1[1] - d[:, 1] * v1[0]) / den; v = (v0[0] * d[:, 1] - v0[1] * d[:, 0]) / den
        ins = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
        y = t[0, 1] + u * (t[1, 1] - t[0, 1]) + v * (t[2, 1] - t[0, 1])
        out[idx[ins]] = np.maximum(out[idx[ins]], y[ins])
    return out


def surface(pieces, P, which):
    P = np.asarray(P, float).reshape(-1, 2); out = np.full(len(P), -np.inf)
    if not len(P):
        return out
    qlo, qhi = P.min(0), P.max(0)
    for p in pieces:
        if p.hi[0] < qlo[0] - 0.01 or p.lo[0] > qhi[0] + 0.01 or p.hi[1] < qlo[1] - 0.01 or p.lo[1] > qhi[1] + 0.01:
            continue                                               # EV112: no query point can fall in this piece (same result)
        m = (P[:, 0] >= p.lo[0] - 0.01) & (P[:, 0] <= p.hi[0] + 0.01) & (P[:, 1] >= p.lo[1] - 0.01) & (P[:, 1] <= p.hi[1] + 0.01)
        if not m.any():
            continue
        idx = np.nonzero(m)[0]; sub = np.full(len(idx), -np.inf)
        tris = {"water": p.water, "road": p.road, "road_ext": p.road[p.road_ext]}[which]
        tri_max(tris, P[idx], sub)
        out[idx] = np.maximum(out[idx], sub)
    return out


def project(V, P):
    """Station of points on the polyline V, first/last segment extended by 40 m (gate copy of the tool's convention)."""
    V = np.asarray(V, float)
    u0 = (V[1] - V[0]) / np.linalg.norm(V[1] - V[0]); u1 = (V[-1] - V[-2]) / np.linalg.norm(V[-1] - V[-2])
    X = np.vstack([V[0] - 40 * u0, V, V[-1] + 40 * u1])
    cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(V, axis=0), axis=1))]; xc = np.r_[-40, cum, cum[-1] + 40]
    P = np.asarray(P, float).reshape(-1, 2); best = np.full(len(P), np.inf); st = np.zeros(len(P))
    for i in range(len(X) - 1):
        a, b = X[i], X[i + 1]; ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        d = np.linalg.norm(P - (a + t[:, None] * ab), axis=1); m = d < best - 1e-9
        best = np.where(m, d, best); st = np.where(m, xc[i] + t * (xc[i + 1] - xc[i]), st)
    return best, st


def at(V, st):
    V = np.asarray(V, float); cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(V, axis=0), axis=1))]
    return np.c_[np.interp(st, cum, V[:, 0]), np.interp(st, cum, V[:, 1])]


def load(run):
    models = json.load(open(GEOM))["models"]
    recs = json.load(open(run + "/kit-records.json")); rep = json.load(open(run + "/kit-report.json"))
    H = np.load(run + "/terrain-kit.npz")["heights"].astype(np.float64)
    sites = {s["site"]: s for s in rep["sites"] if "skipped" not in s}
    pieces = {sid: [Piece(r, models) for r in recs if r["site"] == sid and r["piece"] != "stones"] for sid in sites}
    return models, recs, rep, H, sites, pieces


def resample(C, step):
    seg = np.linalg.norm(np.diff(C, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
    t = np.r_[np.arange(0, s[-1], step), s[-1]]
    return np.c_[np.interp(t, s, C[:, 0]), np.interp(t, s, C[:, 1]), np.interp(t, s, C[:, 2])], t


def chain():
    """The EV112 step-1 command (written once by the integrator of this track; G1 runs it)."""
    return json.load(open(CHAIN))


def stones(run):
    return [r for r in json.load(open(run + "/kit-records.json")) if r["piece"] == "stones"]
