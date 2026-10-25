"""Census of isolated peaks and pits ("pyramids") on the native 6 m triangle mesh (Guillermo, 2026-10-17: "a los lados del
rio hay monticulos poligonales piramidales que suavizar, y lo mismo con monticulos y rios por todo el mapa").

Mesh: 2048^2 vertices, row 0 north, x = 6c, z = 12282 - 6r, native NW-SE diagonal, so each vertex has 6 neighbours:
(r-1,c) (r+1,c) (r,c-1) (r,c+1) (r-1,c-1) (r+1,c+1). Vanilla arrays (vanilla-tricks data) have row 0 south; their NW-SE
diagonal neighbours are (r+1,c-1) (r-1,c+1).

Metric (strict small-shape prominence). Shapes P: the single vertex, the 3 edge pairs and the 2 triangles anchored at a
vertex; ring R = mesh neighbours of P outside P. peak(P) = min H(P) - max H(R); pit(P) = min H(R) - max H(P). A vertex's
peak (pit) prominence is the largest over the shapes that contain it. A single vertex standing s m above all 6 neighbours
gives s; a plane, a ridge, a crease or any slope with no strict local extremum gives <= 0. A "pyramid" is a vertex whose
peak or pit prominence exceeds T. Calibration: the same metric on Chernarus (7.5 m) and Livonia (6.25 m) land.

Attribution: the metric is evaluated on every terrain of the EV chain; a pyramid of the final terrain is attributed to
the stage where its prominence last crossed T (stage = the pass that wrote that terrain), and the stage with its largest
increase is reported too.

Protected domain (where a despike pass may not change heights): reserve | platform | narva, every corner of an envelope
cell standing below the highest incident envelope plane + ENV_CLEAR (wet or near-wet: the footprint, its closure rings,
the visual field and the bury check depend on exactly those predicates), the water mask, vertices below 0.80 m (engine sea 0.75 m), v31_kit dilated by KIT_BUF and v31_bridge_cut |
v31_bridge_fill dilated by BRIDGE_BUF, and a 3-vertex map border. Everything else is the free domain D.

Usage: census_pyramids_v31.py <terrain.npz> <envelope.npy> <out_dir> [--chain chain.json] [--vanilla <data_dir>]
       [--T 0.5] [--no-render] [--domain-terrain <npz>] [--no-chain]
Writes census.json, pyramids.csv (every vertex over 0.3 m on land and in water), sites.csv, map.png, stages.json.
Every threshold, sort and count uses the unrounded prominence; rounding is for the CSV/JSON text only, and the per-pass
attribution sums are asserted equal to the exact census counts (review 1: rounding first lost three vertices at 0.5004).
"""
import argparse, csv, hashlib, json, os, sys
import numpy as np
from scipy.ndimage import binary_dilation, label, find_objects

N = 2048
TS = (0.3, 0.5, 1.0)
KIT_BUF, BRIDGE_BUF, BORDER = 2, 3, 3
SEA_FLOOR = 0.80
ENV_CLEAR = 0.35
E = "E:/DayZ-Baltic-Build/"
B = E + "v31-pond-layer-20261013/"
DEFAULT_CHAIN = [
    ("ev95", E + "v30-global-bank-extension-20261010/build-wide-slope/candidate/terrain.npz", "EV95 base (Astra)"),
    ("ev96", E + "v30-water-two-colour-fix-20261011/terrain-ev96.npz", "fix_two_colour_water_v30 (bed raise / sea conversion)"),
    ("ev97", E + "v30-dry-relief-smoothing-20261011/terrain-ev97.npz", "smooth_dry_land_ev97 (sigma 12 m dry land)"),
    ("ev98", E + "v30-pond-sea-separation-20261011-b/terrain-ev98.npz", "separate_pond_sea_v30 (EV98 bed raise)"),
    ("ev99", E + "v31-ev99-shore-lakes-20261012/terrain-ev99.npz", "EV99 shore lakes / lake rims"),
    ("ev100", E + "v31-ev100-pond-banks-20261012/terrain-ev100.npz", "EV100 pond banks"),
    ("ev101", E + "v31-ev101-sea-bed-20261012/terrain-ev101.npz", "smooth_sea_bed_ev101"),
    ("ev102", E + "v31-ev102-sills-cones-20261012/terrain-ev102.npz", "sills_and_cones_ev102 (sills, road cones)"),
    ("ev103", E + "v31-ev103-sills-cones-20261012/terrain-ev103.npz", "EV103 sills/cones fix"),
    ("map1", B + "terrain-map1.npz", "EV106 map-wide pond shore pass (p1map-builder)"),
    ("map1lag", B + "terrain-map1-lag.npz", "lagoons_v31 (020 lagoons)"),
    ("ev106", B + "terrain-ev106.npz", "bury_edges_v31 (EV106)"),
    ("ev107", B + "bridges/terrain-ev107.npz", "bridges_v31 pilot 015-15"),
    ("ev110kit", B + "ev110/kit/terrain-kit.npz", "streambed_kit_v31 v8"),
    ("ev110br", B + "ev110/bridges/terrain-br.npz", "bridges_v31 v5 (cuts, end fit, legs)"),
    ("ev110", B + "ev110/terrain-ev110.npz", "shore_ramp_v31 (+ bury, 0 changes)"),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def nbr_offsets(north_up=True):
    d = [(-1, -1), (1, 1)] if north_up else [(1, -1), (-1, 1)]
    return [(-1, 0), (1, 0), (0, -1), (0, 1)] + d


def shapes(north_up=True):
    nb = nbr_offsets(north_up)
    out = [((0, 0),)] + [((0, 0), d) for d in (nb[1], nb[3], nb[5])]
    out += ([((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 0), (1, 1))] if north_up else
            [((0, 0), (0, 1), (-1, 1)), ((0, 0), (-1, 0), (-1, 1))])
    res = []
    for P in out:
        Ps, R = set(P), set()
        for p in P:
            for d in nb:
                q = (p[0] + d[0], p[1] + d[1])
                if q not in Ps:
                    R.add(q)
        res.append((list(P), sorted(R)))
    return res


def prominence(H, north_up=True):
    """(peak, pit, peak_shape, pit_shape) per vertex; edge-padded border."""
    pad, n = 3, H.shape
    Hp = np.pad(H.astype(np.float64), pad, mode="edge")
    sh = lambda o: Hp[pad + o[0]:pad + o[0] + n[0], pad + o[1]:pad + o[1] + n[1]]
    peak = np.full(n, -np.inf); pit = np.full(n, -np.inf)
    spk = np.full(n, -1, np.int8); spt = np.full(n, -1, np.int8)
    for si, (P, R) in enumerate(shapes(north_up)):
        rv = np.stack([sh(q) for q in R]); pv = np.stack([sh(p) for p in P])
        pk = pv.min(0) - rv.max(0); pt = rv.min(0) - pv.max(0)
        for p in P:
            tgt = (slice(max(0, p[0]), n[0] + min(0, p[0])), slice(max(0, p[1]), n[1] + min(0, p[1])))
            src = (slice(max(0, -p[0]), n[0] - max(0, p[0])), slice(max(0, -p[1]), n[1] - max(0, p[1])))
            b = pk[src] > peak[tgt]
            peak[tgt] = np.where(b, pk[src], peak[tgt]); spk[tgt] = np.where(b, si, spk[tgt])
            b = pt[src] > pit[tgt]
            pit[tgt] = np.where(b, pt[src], pit[tgt]); spt[tgt] = np.where(b, si, spt[tgt])
    return peak, pit, spk, spt


def env_vertices(env_plane):
    """(corner-of-an-envelope-cell mask, highest incident envelope plane per vertex or -inf)."""
    env = np.isfinite(env_plane)
    cp = np.where(env, env_plane, -np.inf)
    v = np.zeros((N, N), bool); vp = np.full((N, N), -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            v[dr:dr + N - 1, dc:dc + N - 1] |= env
            vp[dr:dr + N - 1, dc:dc + N - 1] = np.maximum(vp[dr:dr + N - 1, dc:dc + N - 1], cp)
    return v, vp


def protected_masks(z, env_plane):
    H = z["heights"].astype(np.float64)
    border = np.ones((N, N), bool); border[BORDER:-BORDER, BORDER:-BORDER] = False
    envv, vp = env_vertices(env_plane)
    m = dict(frozen=z["reserve"] | z["platform"] | z["narva"], envelope_low=envv & (H < vp + ENV_CLEAR), water=z["water"].copy(),
             sea_low=H < SEA_FLOOR,
             kit=binary_dilation(z["v31_kit"], np.ones((3, 3), bool), iterations=KIT_BUF) if "v31_kit" in z else np.zeros((N, N), bool),
             bridge=binary_dilation(z["v31_bridge_cut"] | z["v31_bridge_fill"], np.ones((3, 3), bool), iterations=BRIDGE_BUF)
             if "v31_bridge_cut" in z else np.zeros((N, N), bool),
             border=border)
    prot = np.zeros((N, N), bool)
    for v in m.values():
        prot |= v
    return m, prot


def hillshade(Hc, step, az=315.0, alt=35.0):
    gy, gx = np.gradient(Hc, step)
    # row increases southward: dz/dnorth = -gy
    dzdx, dzdn = gx, -gy
    slope = np.arctan(np.hypot(dzdx, dzdn)); aspect = np.arctan2(-dzdx, -dzdn)
    a, e = np.radians(az), np.radians(alt)
    # light vector from azimuth (clockwise from north), elevation
    lx, ln, lz = np.sin(a) * np.cos(e), np.cos(a) * np.cos(e), np.sin(e)
    nx, nn, nz = -dzdx, -dzdn, np.ones_like(dzdx)
    norm = np.sqrt(nx * nx + nn * nn + 1)
    return np.clip((nx * lx + nn * ln + nz * lz) / norm, 0, 1)


def planar_upsample(H, r0, c0, nr, nc, k):
    """Exact planar-triangle surface (NW-SE split) of vertices [r0, r0+nr] x [c0, c0+nc], k samples per 6 m cell."""
    f = (np.arange(nr * k) + 0.5) / k; g = (np.arange(nc * k) + 0.5) / k
    FR, FC = np.meshgrid(f, g, indexing="ij")
    r = np.floor(FR).astype(int); c = np.floor(FC).astype(int); fr = FR - r; fc = FC - c
    NW = H[r0 + r, c0 + c]; NE = H[r0 + r, c0 + c + 1]; SW = H[r0 + r + 1, c0 + c]; SE = H[r0 + r + 1, c0 + c + 1]
    up = NW + fc * (NE - NW) + fr * (SE - NE)
    lo = NW + fr * (SW - NW) + fc * (SE - SW)
    return np.where(fc >= fr, up, lo)


def crop_rgb(H, water, r, c, half, k=6, marks=()):
    r0, c0 = max(0, r - half), max(0, c - half)
    nr = min(N - 1, r + half) - r0; nc = min(N - 1, c + half) - c0
    S = planar_upsample(H, r0, c0, nr, nc, k)
    hs = 0.55 * hillshade(S, 6.0 / k, 315, 35) + 0.45 * hillshade(S, 6.0 / k, 45, 25)
    rgb = np.stack([hs, hs, hs], -1)
    wm = np.repeat(np.repeat(water[r0:r0 + nr, c0:c0 + nc], k, 0), k, 1)
    rgb[wm] = rgb[wm] * np.array([0.55, 0.7, 1.0])
    for (mr, mc, col) in marks:
        yy, xx = int((mr - r0 + 0.0) * k), int((mc - c0 + 0.0) * k)
        for d in range(-k, k + 1):
            for (y, x) in ((yy + d, xx - k), (yy + d, xx + k), (yy - k, xx + d), (yy + k, xx + d)):
                if 0 <= y < rgb.shape[0] and 0 <= x < rgb.shape[1]:
                    rgb[y, x] = col
    return (rgb * 255).astype(np.uint8), (r0, c0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("terrain"); ap.add_argument("envelope"); ap.add_argument("out")
    ap.add_argument("--chain"); ap.add_argument("--vanilla", default=E + "vanilla-tricks-20261013/data/")
    ap.add_argument("--T", type=float, default=0.5); ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--domain-terrain", help="compute the protected domain on this terrain (the despike input) instead")
    ap.add_argument("--no-chain", action="store_true", help="skip the attribution through the chain")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=False)
    T = a.T
    _z = np.load(a.terrain); z = {k: _z[k] for k in _z.files}; zfiles = list(z)
    H = z["heights"].astype(np.float64)
    env_plane = np.load(a.envelope)
    if a.domain_terrain:
        _d = np.load(a.domain_terrain); zd = {k: _d[k] for k in _d.files}
    else:
        zd = z
    masks, prot = protected_masks(zd, env_plane)
    free = ~prot
    land = ~zd["water"] & (zd["heights"] >= SEA_FLOOR) & ~masks["envelope_low"]
    peak, pit, spk, spt = prominence(H)
    M = np.maximum(peak, pit)
    rep = dict(schema="census-pyramids-v31.v1", terrain=a.terrain, terrain_sha256=sha(a.terrain), envelope=a.envelope,
               envelope_sha256=sha(a.envelope), T=T, buffers=dict(kit=KIT_BUF, bridge=BRIDGE_BUF, border=BORDER, sea_floor=SEA_FLOOR),
               metric="strict small-shape prominence (single, 3 edge pairs, 2 triangles) on the NW-SE 6-ring")
    # vanilla calibration
    cal = {}
    for w, lbl in (("chernarus", "Chernarus"), ("enoch", "Livonia")):
        Hv = np.load(os.path.join(a.vanilla, w + "_height.npy")).astype(np.float64)
        meta = json.load(open(os.path.join(a.vanilla, w + "_meta.json")))
        lv = Hv > meta["sea"]["level"] + 0.5
        lv[:3] = lv[-3:] = False; lv[:, :3] = lv[:, -3:] = False
        pkv, ptv, _, _ = prominence(Hv, north_up=False)
        km2 = lv.sum() * meta["step"] ** 2 / 1e6
        cal[lbl] = dict(step=meta["step"], land_km2=round(km2, 1),
                        **{f"T{t}": dict(peaks=int((lv & (pkv > t)).sum()), pits=int((lv & (ptv > t)).sum()),
                                         per_km2=round(float((lv & ((pkv > t) | (ptv > t))).sum() / km2), 3)) for t in TS})
    km2b = land.sum() * 36 / 1e6
    cal["Baltic EV110 land"] = dict(step=6.0, land_km2=round(km2b, 1),
                                    **{f"T{t}": dict(peaks=int((land & (peak > t)).sum()), pits=int((land & (pit > t)).sum()),
                                                     per_km2=round(float((land & (M > t)).sum() / km2b), 3)) for t in TS})
    rep["calibration"] = cal
    # counts by mask
    def cnt(sel):
        return {f"T{t}": dict(peaks=int((sel & (peak > t)).sum()), pits=int((sel & (pit > t)).sum())) for t in TS}
    rep["counts"] = dict(all=cnt(np.ones((N, N), bool)), land=cnt(land), free_domain=cnt(free),
                         protected={k: cnt(v) for k, v in masks.items()})
    # attribution through the chain
    chain = [("final", a.terrain, "census terrain")] if a.no_chain else (json.load(open(a.chain)) if a.chain else DEFAULT_CHAIN)
    sel = M > 0.3
    idx = np.argwhere(sel)
    vals = np.zeros((len(chain), len(idx)))
    stages = []
    prevH = None
    for si, (name, path, desc) in enumerate(chain):
        Hs = np.load(path)["heights"].astype(np.float64)
        pks, pts, _, _ = prominence(Hs)
        vals[si] = np.maximum(pks, pts)[idx[:, 0], idx[:, 1]]
        changed = int((Hs != prevH).sum()) if prevH is not None else None
        stages.append(dict(stage=name, path=path, desc=desc, sha256=sha(path), changed_vs_prev=changed,
                           **{f"pyramids_T{t}": int(((pks > t) | (pts > t)).sum()) for t in TS},
                           **{f"land_pyramids_T{t}": int((land & ((pks > t) | (pts > t))).sum()) for t in TS}))
        prevH = Hs
        print("stage", name, stages[-1]["pyramids_T0.5"], flush=True)
    assert np.allclose(vals[-1], M[idx[:, 0], idx[:, 1]]), "last chain stage must be the census terrain"
    names = [s[0] for s in chain]

    def creator(col, t):
        above = col > t
        if not above[-1]:
            return None
        k = len(col) - 1
        while k > 0 and above[k - 1]:
            k -= 1
        return names[k]
    jump = np.argmax(np.diff(vals, axis=0, prepend=vals[:1] * 0 + vals[:1]), axis=0)
    rows = []
    for j, (r, c) in enumerate(idx):
        rows.append(dict(x=6 * int(c), z=12282 - 6 * int(r), r=int(r), c=int(c), H=round(float(H[r, c]), 3),
                         kind="peak" if peak[r, c] >= pit[r, c] else "pit", prom=round(float(M[r, c]), 3), prom_m=float(M[r, c]),
                         shape=int(spk[r, c] if peak[r, c] >= pit[r, c] else spt[r, c]),
                         creator_T03=creator(vals[:, j], 0.3), creator_T=creator(vals[:, j], T), max_jump_stage=names[int(jump[j])],
                         land=bool(land[r, c]), free=bool(free[r, c]),
                         masks="|".join(k for k, v in masks.items() if v[r, c]) +
                         ("|" if any(v[r, c] for v in masks.values()) else "") +
                         "|".join(k for k in zfiles if z[k].dtype == bool and k not in ("water",) and z[k][r, c])))
    rows.sort(key=lambda d: (-d["prom_m"], d["r"], d["c"]))
    with open(os.path.join(a.out, "pyramids.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[k for k in rows[0].keys() if k != "prom_m"], extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    over = [d for d in rows if d["prom_m"] > T]
    assert len(over) == int((M > T).sum()), "attribution rows != exact census count"
    by = {}
    for d in over:
        key = ("free" if d["free"] else "protected") + ":" + (d["creator_T"] or "?")
        by[key] = by.get(key, 0) + 1
    rep["attribution_T"] = dict(sorted(by.items(), key=lambda kv: -kv[1]))
    byl = {}
    for d in over:
        if d["land"]:
            byl[d["creator_T"]] = byl.get(d["creator_T"], 0) + 1
    rep["attribution_T_land"] = dict(sorted(byl.items(), key=lambda kv: -kv[1]))
    assert sum(by.values()) == int((M > T).sum()) and sum(byl.values()) == int((land & (M > T)).sum()), "attribution sums"
    rep["attribution_check"] = dict(all=int((M > T).sum()), land=int((land & (M > T)).sum()), sum_all=sum(by.values()),
                                    sum_land=sum(byl.values()))
    rep["stages"] = stages
    # sites: 8-connected clusters of vertices over T
    lab, nl = label(binary_dilation(M > T, np.ones((3, 3), bool)) & (M > -np.inf), np.ones((3, 3), bool))
    lab = np.where(M > T, lab, 0)
    sites = []
    for k, slc in enumerate(find_objects(lab), 1):
        if slc is None:
            continue
        m = lab[slc] == k
        if not m.any():
            continue
        sub = M[slc]; i = np.argmax(np.where(m, sub, -np.inf)); rr, cc = np.unravel_index(i, sub.shape)
        r, c = slc[0].start + rr, slc[1].start + cc
        d = next(x for x in over if x["r"] == r and x["c"] == c)
        sites.append(dict(site=k, x=d["x"], z=d["z"], r=int(r), c=int(c), vertices=int(m.sum()), max_prom=d["prom"], kind=d["kind"],
                          creator=d["creator_T"], land=d["land"], free=d["free"], masks=d["masks"]))
    sites.sort(key=lambda s: (-float(M[s["r"], s["c"]]), s["r"], s["c"]))
    with open(os.path.join(a.out, "sites.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sites[0].keys())); w.writeheader(); w.writerows(sites)
    rep["sites_T"] = dict(total=len(sites), land=sum(s["land"] for s in sites), free=sum(s["free"] for s in sites),
                          top20=sites[:20], top_free20=[s for s in sites if s["free"]][:20])
    with open(os.path.join(a.out, "census.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    if not a.no_render:
        from PIL import Image, ImageDraw
        k = 2
        Hs = H[::k, ::k]
        hs = hillshade(Hs, 6.0 * k)
        img = np.stack([hs] * 3, -1) * 0.8 + 0.2
        img[z["water"][::k, ::k]] = img[z["water"][::k, ::k]] * np.array([0.5, 0.65, 1.0])
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
        pal = {}
        cols = [(230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 240, 240),
                (240, 50, 230), (210, 245, 60), (250, 190, 212), (0, 128, 128), (170, 110, 40), (128, 0, 0), (128, 128, 0),
                (0, 0, 128), (255, 255, 255)]
        for i, nme in enumerate(names):
            pal[nme] = cols[i % len(cols)]
        for d in reversed(over):
            col = pal.get(d["creator_T"], (0, 0, 0)); rad = 1 + min(4, int(d["prom_m"] * 2))
            x, y = d["c"] / k, d["r"] / k
            if d["free"]:
                dr.ellipse([x - rad, y - rad, x + rad, y + rad], fill=col)
            else:
                dr.ellipse([x - rad, y - rad, x + rad, y + rad], outline=col)
        y0 = 8
        for nme in names:
            if any(d["creator_T"] == nme for d in over):
                dr.rectangle([8, y0, 20, y0 + 10], fill=pal[nme]); dr.text((24, y0 - 1), f"{nme} {sum(d['creator_T'] == nme for d in over)}", fill=(0, 0, 0))
                y0 += 14
        dr.text((8, y0 + 4), f"pyramids > {T} m: filled = free domain, ring = protected", fill=(0, 0, 0))
        im.save(os.path.join(a.out, "map.png"))
    print(json.dumps({k: v for k, v in rep.items() if k not in ("stages", "sites_T")}, indent=1))
    print(json.dumps(rep["sites_T"]["top20"][:10], indent=1))


if __name__ == "__main__":
    main()
