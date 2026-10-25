"""Despike pass v31 (Guillermo, 2026-10-17: "a los lados del rio hay monticulos poligonales piramidales que suavizar, y lo
mismo con monticulos y rios por todo el mapa"). Lowers isolated peaks and raises isolated pits of the native 6 m mesh on
free land; runs after the kit, bridge, causeway and shore passes and before the last bury_edges_v31.

Mesh: row 0 north, x = 6c, z = 12282 - 6r, NW-SE diagonal: the 6 neighbours of (r, c) are (r+-1, c), (r, c+-1), (r-1, c-1)
and (r+1, c+1). Prominence (as census_pyramids_v31.py): over the small shapes P (vertex, 3 edge pairs, 2 triangles) and
their mesh rings R, peak = min H(P) - max H(R), pit = min H(R) - max H(P); a vertex takes the largest over the shapes
that contain it.

Free domain: every vertex except reserve | platform | narva, any corner of an envelope cell standing below its highest
incident envelope plane + ENV_CLEAR (the footprint, its closure rings, the visible field and the bury check read only
envelope-cell corners, through "below plane" and "below plane + 0.30"; a dry corner kept >= plane + ENV_CLEAR leaves every
one of those predicates, hence the footprint, unchanged), the water mask, vertices below 0.80 m (engine sea 0.75 m),
v31_kit dilated by 2 and v31_bridge_cut | v31_bridge_fill dilated by 3 vertices (kit and bridge seats, legs, abutments,
ramps and decks), every vertex within 15 m of a kit/stones record origin or 30 m of a bridge record origin (--records,
WRP record lists [{model, matrix[12]}]; covers seats of later passes that write no mask), and a 3-vertex map border.
Step (Jacobi, at most ITERS rounds): every free vertex whose peak prominence exceeds T goes down to the mean of its 6
neighbours (never up); every free vertex whose pit prominence exceeds T goes up to that mean (never down). A pair or
triangle mound converges over the rounds (each member sees the other in its mean). Guards on every round:
  islet     a free vertex that is no envelope-cell corner and whose 6 neighbours all stand below the engine sea (0.75 m)
            in the input is a one-vertex islet (EV110 has 12, left by EV95 and the EV96 sea conversion, up to 2.9 m of
            prominence); it is smoothed with the same dry floor as other land. Guillermo's EV112 decision preserves
            these islets: no input dry vertex may become engine-sea bed.
  floor     a lowered vertex never ends below min(its input height, F), F = max(0.80, the highest envelope plane or water
            level within 2 vertices + 0.30, its own highest incident envelope plane + ENV_CLEAR): no dry dip under a
            nearby waterline, no envelope corner brought near the water and no new engine-sea vertex;
  slopes    a triangle may not end steeper than max(35 deg, its input slope); the changed corners of a violating
            triangle are pulled half-way back to the input, up to 30 times, then fully back;
  protected a protected vertex may not end more prominent than max(T, its input prominence) (lowering a free vertex
            beside a frozen or seat spike would sharpen it): the changed free vertices within 2 mesh steps of a
            violating one are pulled half-way back, up to 12 times, then fully back.
Optional corrected-shore guard: --shore-footprint with one or more --shore-mask names preserves both endpoints of native
waterline edges touched by an upstream correction. It uses the visual per-corner field (or sea 0.75), not the roadway
plane. This prevents despike undoing accepted shore/causeway fairing. The ordinary reduction, slope and water gates still
apply without relaxed bands. The input footprint and edit masks must belong to this terrain chain. The islet report
counts free islets; protected islets are checked separately against the approved 12-site inventory.
Only heights change; every other array is copied; v31_despike marks the changed vertices.
Usage: despike_v31.py <in_terrain.npz> <envelope.npy> <out_terrain.npz> <report.json> [--T 0.3] [--iters 60]
       [--records records.json ...] [--shore-footprint footprint.npz --shore-mask NAME ...]
"""
import argparse, hashlib, json, os
import numpy as np
from scipy.ndimage import binary_dilation, grey_dilation

N = 2048
SEA_FLOOR, SHORE_CLEAR, SHORE_REACH, ENV_CLEAR = 0.80, 0.30, 2, 0.35
SEA = 0.75
KIT_BUF, BRIDGE_BUF, BORDER = 2, 3, 3
SLOPE_MAX = 35.0
REC_R_KIT, REC_R_BRIDGE = 15.0, 30.0
TS = (0.3, 0.5, 1.0)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


NB = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]
SHAPES = [[(0, 0)], [(0, 0), (1, 0)], [(0, 0), (0, 1)], [(0, 0), (1, 1)], [(0, 0), (0, 1), (1, 1)], [(0, 0), (1, 0), (1, 1)]]


def rings():
    out = []
    for P in SHAPES:
        R = sorted({(p[0] + d[0], p[1] + d[1]) for p in P for d in NB} - set(P))
        out.append((P, R))
    return out


def prominence(H):
    pad = 3
    Hp = np.pad(H, pad, mode="edge")
    sh = lambda o: Hp[pad + o[0]:pad + o[0] + N, pad + o[1]:pad + o[1] + N]
    peak = np.full((N, N), -np.inf); pit = np.full((N, N), -np.inf)
    for P, R in rings():
        rv = np.stack([sh(q) for q in R]); pv = np.stack([sh(p) for p in P])
        pk = pv.min(0) - rv.max(0); pt = rv.min(0) - pv.max(0)
        for p in P:
            tgt = (slice(max(0, p[0]), N + min(0, p[0])), slice(max(0, p[1]), N + min(0, p[1])))
            src = (slice(max(0, -p[0]), N - max(0, p[0])), slice(max(0, -p[1]), N - max(0, p[1])))
            peak[tgt] = np.maximum(peak[tgt], pk[src]); pit[tgt] = np.maximum(pit[tgt], pt[src])
    return peak, pit


def ring_dilate(m, steps=2):
    for _ in range(steps):
        p = np.pad(m, 1)
        m = m | np.logical_or.reduce([p[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] for dr, dc in NB])
    return m


def mean6(H):
    Hp = np.pad(H, 1, mode="edge")
    return sum(Hp[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] for dr, dc in NB) / 6.0


def tri_slopes(H):
    """Slope (deg) of the upper (NW, NE, SE) and lower (NW, SW, SE) triangle of every cell."""
    NW, NE, SW, SE = H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]
    up = np.degrees(np.arctan(np.hypot((NE - NW) / 6.0, (SE - NE) / 6.0)))
    lo = np.degrees(np.arctan(np.hypot((SE - SW) / 6.0, (SW - NW) / 6.0)))
    return up, lo


def tri_to_vertices(up_bad, lo_bad):
    v = np.zeros((N, N), bool)
    v[:-1, :-1] |= up_bad | lo_bad          # NW
    v[:-1, 1:] |= up_bad                    # NE
    v[1:, 1:] |= up_bad | lo_bad            # SE
    v[1:, :-1] |= lo_bad                    # SW
    return v


def records_mask(paths):
    m = np.zeros((N, N), bool)
    rr, cc = np.mgrid[0:N, 0:N]
    n = 0
    for p in paths or []:
        for r in json.load(open(p)):
            x, zz = r["matrix"][9], r["matrix"][11]
            R = REC_R_BRIDGE if "bridges" in r["model"].lower() else REC_R_KIT
            c0, r0 = int(x // 6), int((12282 - zz) // 6)
            k = int(R // 6) + 2
            sl = (slice(max(0, r0 - k), r0 + k + 1), slice(max(0, c0 - k), c0 + k + 1))
            m[sl] |= np.hypot(6.0 * cc[sl] - x, 12282.0 - 6.0 * rr[sl] - zz) < R
            n += 1
    return m, n


def free_domain(a, env_plane, records=None, shoreline=None):
    H = a["heights"].astype(np.float64)
    envv, vp = env_vertex_plane(env_plane)
    border = np.ones((N, N), bool); border[BORDER:-BORDER, BORDER:-BORDER] = False
    k3 = np.ones((3, 3), bool)
    prot = dict(frozen=a["reserve"] | a["platform"] | a["narva"], envelope_low=envv & (H < vp + ENV_CLEAR), water=a["water"], sea_low=H < SEA_FLOOR,
                kit=binary_dilation(a["v31_kit"], k3, iterations=KIT_BUF),
                bridge=binary_dilation(a["v31_bridge_cut"] | a["v31_bridge_fill"], k3, iterations=BRIDGE_BUF), border=border,
                records=records_mask(records)[0])
    if shoreline is not None:
        prot["shoreline"] = shoreline
    p = np.zeros((N, N), bool)
    for v in prot.values():
        p |= v
    return ~p, prot, envv


def env_vertex_plane(env_plane):
    """(corner-of-an-envelope-cell mask, highest incident envelope plane per vertex or -inf)."""
    env = np.isfinite(env_plane)
    cp = np.where(env, env_plane, -np.inf)
    v = np.zeros((N, N), bool); vp = np.full((N, N), -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            v[dr:dr + N - 1, dc:dc + N - 1] |= env
            vp[dr:dr + N - 1, dc:dc + N - 1] = np.maximum(vp[dr:dr + N - 1, dc:dc + N - 1], cp)
    return v, vp


def lower_floor(a, env_plane):
    envv, vp = env_vertex_plane(env_plane)
    wl = np.where(a["water"], a["level"].astype(np.float64), -np.inf)
    near = grey_dilation(np.maximum(vp, wl), size=(2 * SHORE_REACH + 1, 2 * SHORE_REACH + 1))
    return np.maximum.reduce([np.full((N, N), SEA_FLOOR), np.where(np.isfinite(near), near + SHORE_CLEAR, -np.inf),
                              np.where(envv, vp + ENV_CLEAR, -np.inf)])


def counts(peak, pit, sel):
    return {f"T{t}": dict(peaks=int((sel & (peak > t)).sum()), pits=int((sel & (pit > t)).sum()),
                          vertices=int((sel & ((peak > t) | (pit > t))).sum())) for t in TS}


def shoreline_vertices(H, footprint, edited):
    """Endpoints of native mesh edges intersected by the actual visual waterline.
    Preserve their heights for edges touched by an upstream shoreline correction.
    The footprint must describe the input terrain, checked by the caller's chain.
    """
    f = np.load(footprint, allow_pickle=False)
    plane, field = f["plane"], f["field"]
    if plane.shape != (N-1, N-1) or field.shape != (N-1, N-1, 4):
        raise ValueError("invalid shoreline footprint shape")
    corners = ((0,0),(0,1),(1,0),(1,1))
    wetfield = np.where(np.isfinite(plane)[:,:,None], field, 0.75)
    if not np.isfinite(wetfield).all():
        raise ValueError("nonfinite visual water field")
    delta = np.stack([H[dr:dr+N-1,dc:dc+N-1] for dr,dc in corners], axis=-1)-wetfield
    mask = np.zeros((N,N),bool)
    for ia, ib in ((0,1),(1,3),(3,0),(0,2),(2,3)):
        crosses = (delta[:,:,ia] < 0) != (delta[:,:,ib] < 0)
        da,ca=corners[ia];db,cb=corners[ib]
        crosses &= edited[da:da+N-1,ca:ca+N-1] | edited[db:db+N-1,cb:cb+N-1]
        for k in (ia,ib):
            dr,dc=corners[k];mask[dr:dr+N-1,dc:dc+N-1] |= crosses
    return mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("terrain"); ap.add_argument("envelope"); ap.add_argument("out"); ap.add_argument("report")
    ap.add_argument("--T", type=float, default=0.3); ap.add_argument("--iters", type=int, default=60)
    ap.add_argument("--records", nargs="*", default=[])
    ap.add_argument("--shore-footprint", help="Preserve corrected native visual-waterline endpoints from the input footprint")
    ap.add_argument("--shore-mask", action="append", default=[], help="Bool vertex mask of an upstream corrected shoreline; requires --shore-footprint")
    o = ap.parse_args()
    assert not os.path.exists(o.out) and not os.path.exists(o.report), "fresh outputs required"
    z = np.load(o.terrain); a = {k: z[k] for k in z.files}
    env_plane = np.load(o.envelope).astype(np.float64)
    H0 = a["heights"].astype(np.float64)
    if bool(o.shore_footprint) != bool(o.shore_mask):
        raise ValueError("--shore-footprint and --shore-mask must be supplied together")
    edited = np.zeros(H0.shape, bool)
    for name in o.shore_mask:
        if name not in a or a[name].shape != H0.shape or a[name].dtype != np.bool_:
            raise ValueError("invalid shoreline edit mask: " + name)
        edited |= a[name]
    shore = shoreline_vertices(H0, o.shore_footprint, edited) if o.shore_footprint else None
    free, prot, envv = free_domain(a, env_plane, o.records, shore)
    floor = np.minimum(H0, lower_floor(a, env_plane))
    _p = np.pad(H0, 1, mode="edge")
    islet = free & ~envv & (np.max([_p[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] for dr, dc in NB], axis=0) < SEA) & (H0 >= SEA)
    up0, lo0 = tri_slopes(H0)
    lim_up = np.maximum(SLOPE_MAX, up0) + 1e-6; lim_lo = np.maximum(SLOPE_MAX, lo0) + 1e-6
    pk0, pt0 = prominence(H0)
    cap = np.maximum(np.maximum(pk0, pt0), o.T) + 1e-9
    protected = ~free
    H = H0.copy()
    log = []
    for it in range(o.iters):
        pk, pt = prominence(H)
        m = mean6(H)
        fp = free & (pk > o.T); fq = free & (pt > o.T) & ~fp
        if not (fp.any() or fq.any()):
            break
        Hn = H.copy()
        Hn[fp] = np.maximum(np.minimum(H[fp], m[fp]), floor[fp])
        Hn[fq] = np.maximum(H[fq], m[fq])
        moved = int((np.abs(Hn - H) > 1e-6).sum())
        reverted = 0
        for _ in range(31):
            up, lo = tri_slopes(Hn)
            bad = tri_to_vertices(up > lim_up, lo > lim_lo) & (Hn != H0)
            if not bad.any():
                break
            Hn[bad] = H0[bad] + 0.5 * (Hn[bad] - H0[bad]) if _ < 30 else H0[bad]
            reverted += int(bad.sum())
        Hn = np.where(free, Hn, H0)
        guarded = 0
        for k in range(13):
            pkn, ptn = prominence(Hn)
            viol = protected & (np.maximum(pkn, ptn) > cap)
            if not viol.any():
                break
            back = ring_dilate(viol) & free & (Hn != H0)
            Hn[back] = H0[back] + 0.5 * (Hn[back] - H0[back]) if k < 12 else H0[back]
            guarded += int(back.sum())
        step = float(np.abs(Hn - H).max())
        H = Hn
        log.append(dict(round=it, flagged_peaks=int(fp.sum()), flagged_pits=int(fq.sum()), moved=moved, slope_pullbacks=reverted, protected_pullbacks=guarded,
                        max_step_m=step))
        if moved == 0 or step < 1e-4:
            break
    # final rounding to the stored dtype, then guards measured on the stored heights
    Hf = H.astype(np.float32)
    Hs = Hf.astype(np.float64)
    changed = Hs != H0.astype(np.float32).astype(np.float64)
    up, lo = tri_slopes(Hs)
    pk1, pt1 = prominence(Hs)
    land = ~a["water"] & (H0 >= SEA_FLOOR) & ~prot["envelope_low"]
    a["heights"] = Hf
    a["v31_despike"] = changed | a.get("v31_despike", np.zeros((N, N), bool))
    np.savez(o.out, **a)
    dH = (Hs - H0)[changed]
    rep = dict(schema="despike-v31.v1", input=o.terrain, input_sha256=sha(o.terrain), envelope=o.envelope,
               envelope_sha256=sha(o.envelope), output=o.out, output_sha256=sha(o.out),
               params=dict(T=o.T, iters=o.iters, SEA_FLOOR=SEA_FLOOR, ENV_CLEAR=ENV_CLEAR, SHORE_CLEAR=SHORE_CLEAR, SHORE_REACH=SHORE_REACH,
                           KIT_BUF=KIT_BUF, BRIDGE_BUF=BRIDGE_BUF, BORDER=BORDER, SLOPE_MAX=SLOPE_MAX),
               records=[dict(path=p, sha256=sha(p)) for p in o.records],
               islets=dict(count=int(islet.sum()), policy="preserve_dry", sea_flips=int((islet & (Hs < SEA)).sum()),
                           xz=[[6 * int(c), 12282 - 6 * int(r)] for r, c in np.argwhere(islet)]),
               free_vertices=int(free.sum()), protected_vertices={k: int(v.sum()) for k, v in prot.items()},
               rounds=log, changed=int(changed.sum()), lowered=int((dH < 0).sum()), raised=int((dH > 0).sum()),
               dH_min=float(dH.min(initial=0)), dH_max=float(dH.max(initial=0)),
               dH_abs_p50=float(np.percentile(np.abs(dH), 50)) if dH.size else 0.0,
               dH_abs_p99=float(np.percentile(np.abs(dH), 99)) if dH.size else 0.0,
               changed_outside_free=int((changed & ~free).sum()),
               slope_violations=int(((up > lim_up) | (lo > lim_lo)).sum()),
               protected_sharpened=int((protected & (np.maximum(pk1, pt1) > cap)).sum()),
               before=dict(free=counts(pk0, pt0, free), land=counts(pk0, pt0, land), all=counts(pk0, pt0, np.ones((N, N), bool))),
               after=dict(free=counts(pk1, pt1, free), land=counts(pk1, pt1, land), all=counts(pk1, pt1, np.ones((N, N), bool))))
    rep["shoreline_guard"] = ({"footprint": o.shore_footprint, "sha256": sha(o.shore_footprint), "masks": o.shore_mask, "vertices": int(shore.sum()), "changed": int((changed & shore).sum())} if shore is not None else None)
    with open(o.report, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != "rounds"}, indent=1))
    print("rounds", len(log), log[-3:])


if __name__ == "__main__":
    main()
