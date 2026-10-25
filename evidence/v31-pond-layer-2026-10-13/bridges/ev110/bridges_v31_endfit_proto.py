"""BALTIC-015 (Guillermo, 2026-10-11: vanilla bridges by width): place a vanilla bridge where a road crosses a stream on a
dry embankment, open the channel under its span and seal that channel into the v31 pond envelope.

Per site (JSON list: id, x, z, road bearing deg, model, level, water bearing deg, width m, optional spans = 1 or 2):
  model     DZ\\structures\\roads\\bridges\\<model>.p3d, read from its ODOL: length axis (X for wood, Z for metal), roadway
            end heights at +-half length, centre of the roadway in model coordinates.
  pose      length axis along the road bearing, pitched so both roadway ends sit on the road terrain (world = position +
            R . ODOL vertex, the convention of the WRP records; matrix = local X, Y, Z axes as columns, then position).
            Each end height is the road terrain on the axis, or, where the terrain under the deck end strip (full deck
            width at the end, END_IN m inward, less the deck's rise along its pitch) stands higher, that terrain +
            END_CLEAR: a deck wider than the road
            (bridge_metal_25: 14.2 m) sat with one corner a few cm inside a cross-sloped road (Guillermo, 15-10, 015-8).
            With spans = 2 (the 015 plan's 'bridge_metal_25 x2') two copies stand end to end on one straight pitched line
            between the two outer roadway ends; each span's centre height is interpolated on that line.
  channel   q = distance to the water axis through the site, t = distance along it: H = min(H, bed + BANK (|q| - W/2)) for
            |t| <= CUT_T, bed = max(1.0, level - 0.5); this may lower reserve/platform vertices, but only under the deck
            (|s| <= flat half-span along the road), which is the explicit exception of the plan.
  seals     cells within W/2 + 6 m of the water axis and |t| <= CUT_T take the stream level in the envelope.
  corridor  the road reserve band is often far wider than the deck (015-16: 24 m against 8 m), so the channel is opened
            through the whole band under the deck's length (frozen vertices with |s| <= flat half-span, any lateral offset;
            limiting it to the deck width left the shoulders as dams). The cut reaches, on each side separately,
            max(25 m, the far end of the frozen run met along the water axis + 6 m, the first point where the terrain within
            3 m of the axis is below the stream level + 4 m), capped at 60 m: a fixed 25 m stopped short of the band on
            oblique or wide crossings (015-4) and of the water beyond the EV102 road cones (015-13/16/40: water resumed at
            ~30 m), leaving dams and, against them, sealed pond edges.
  link      the inventory's water bearing is a chord: where no water lies on the straight axis on one side within 60 m,
            the channel is also carved (same width and banks, frozen vertices untouched) and sealed along a straight
            segment from the axis just beyond the frozen run to the nearest wet vertex of an envelope cell at the stream
            level on that side (015-16 north, 015-40 south: the natural channel ran 6-12 m beside the axis).
  end fit   each outer end has a seat, read from the visual LOD: bridge_metal_25 its pier block (flush with the end, 3.4 m
            along, 17.7 m across, top 1.7 m under the roadway), the wood bridges their ramp underside (roadway - RAMP_T)
            up to the first pile row (~4.2 m). On the planar triangles the terrain must not lie below the seat on its
            footprint and faces (inner face included), nor below a 1:CONE (h:v) wing slope falling from it up to END_RING m
            to its sides, nor below what the source gave there; where the cut breaks that, it is undone vertex by vertex
            (largest weight first, never above the source). Kept: every vertex the cut left below the stream level and,
            on channels narrower than a cell (W < 6 m), their grid neighbours, so the water keeps its path and width.
            The flat-half-span cut and the oblique channel had left planar triangles that fell 4-5 m within one cell of
            the end and bared the block's inner corner beside the deck (Guillermo, 15-10, 015-13); Chernarus keeps the
            metal_25 inner face buried (5 bridges, <= 0.8 m bare).
  slopes    a changed triangle steeper than max(35 deg, before) has its highest vertex lowered in 0.1 m steps when that
            vertex is neither channel floor (|q| <= W/2 from the axis or a link) nor frozen nor held by the end fit, and
            lies within 2 vertices of the edit (80 passes): the wall is laid back; the channel floor, the frozen
            embankment and the end fit never move. Steep faces where the frozen embankment meets the
            channel under the deck (the abutments) stay: the bridge stands over them, as in Chernarus.
  sea mode  when the water on the axis within CUT_T is engine sea (terrain < 0.75 m outside every envelope cell; EV96 turned
            many low reaches into sea), the bed is SEA_BED below the sea and no seal is written: the engine sea fills the
            channel, so no pond piece ever covers sea water (the two-colour rule of 11-10).
Usage: bridges_v31.py <terrain.npz> <envelope.npy> <sites.json> <out_terrain.npz> <out_envelope.npy> <records.json> <report.json>
"""
import json, math, sys
import numpy as np
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
from odol_reader import ODOL

BANK, CUT_T, BED_MIN, ZTOP = 0.5, 25.0, 1.0, 12282
END_IN, END_CLEAR = 2.0, 0.02
CONE, END_RING, RAMP_T = 1.5, 8.0, 0.28                                            # wing slope h:v and reach; wood ramp depth
SEA, SEA_BED = 0.75, 0.0
DZ = "P:/DZ/structures/roads/bridges"


def model_info(name):
    od = ODOL.from_file(f"{DZ}/{name}.p3d")
    road = min(od.lods, key=lambda l: abs(l.resolution - 3e15))
    v = np.array([(p.x, p.y, p.z) for p in road.vertices])
    ax = 0 if np.ptp(v[:, 0]) >= np.ptp(v[:, 2]) else 2
    lat = 2 - ax
    lo, hi = v[:, ax].min(), v[:, ax].max()
    ends = [float(v[np.abs(v[:, ax] - e) < 0.6, 1].max()) for e in (lo, hi)]
    c_lat = (v[:, lat].max() + v[:, lat].min()) / 2
    end_w = max(float(np.abs(v[(np.abs(v[:, ax] - e) < 0.6) & (v[:, 1] >= y - 0.3), lat] - c_lat).max()) for e, y in zip((lo, hi), ends))
    w = np.array([(p.x, p.y, p.z) for p in min(od.lods, key=lambda l: abs(l.resolution - 1.0)).vertices])   # visual LOD
    seats = []                                                                        # per end: length a_in, half width, height
    for e, y, inw in ((lo, ends[0], 1.0), (hi, ends[1], -1.0)):
        a = (w[:, ax] - e) * inw
        deep = (w[:, 1] < y - 2) & (a > -0.5) & (a < (hi - lo) / 2)                     # pier block or pile bottoms
        if not deep.any():                                                            # nothing reaches the ground: no seat
            seats.append(dict(a_in=0.0, hw=0.0, a_k=[0.0, 1.0], y_k=[y - 99.0, y - 99.0])); continue
        if a[deep].min() < 0.5:                                                       # pier block flush with the end: its top
            cols = {(round(p[0], 2), round(p[2], 2)) for p in w[deep]}
            top = max(p[1] for p in w if (round(p[0], 2), round(p[2], 2)) in cols)
            seats.append(dict(a_in=float(a[deep].max()), hw=float(np.abs(w[deep, lat] - c_lat).max()), a_k=[0.0, 1.0], y_k=[top, top]))
        else:                                                                         # ramp on the ground to the first piles
            ra = (v[:, ax] - e) * inw; a_k = np.linspace(0.0, float(a[deep].min()), 5)
            prof = sorted((float(x), float(v[np.abs(ra - x) < 0.01, 1].max())) for x in set(np.round(ra, 2)) if x >= -0.01)
            seats.append(dict(a_in=float(a_k[-1]), hw=end_w, a_k=a_k.tolist(), y_k=(np.interp(a_k, *zip(*prof)) - RAMP_T).tolist()))
    return dict(axis=ax, half=(hi - lo) / 2, centre_len=(hi + lo) / 2, centre_lat=c_lat,
                end_y=ends, deck_max=float(v[:, 1].max()), width=float(np.ptp(v[:, lat])), end_half_w=end_w, seats=seats)


def tri_h(H, x, z):
    c, r = x / 6, (ZTOP - z) / 6
    c0, r0 = int(c), int(r); fc, fr = c - c0, r - r0
    nw, ne, sw, se = H[r0, c0], H[r0, c0 + 1], H[r0 + 1, c0], H[r0 + 1, c0 + 1]
    return nw + fc * (ne - nw) + fr * (se - ne) if fc >= fr else nw + fr * (sw - nw) + fc * (se - sw)


def tri_w(x, z):
    """Vertex rows, cols (n, 3) and planar weights (n, 3) of world points, NW-SE split as in tri_h."""
    c, r = x / 6, (ZTOP - z) / 6
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int); fc, fr = c - c0, r - r0
    up = fc >= fr
    rows = np.stack([r0, np.where(up, r0, r0 + 1), r0 + 1], 1); cols = np.stack([c0, np.where(up, c0 + 1, c0), c0 + 1], 1)
    return rows, cols, np.stack([np.where(up, 1 - fc, 1 - fr), np.where(up, fc - fr, fr - fc), np.where(up, fr, fc)], 1)


def main():
    tpath, epath, spath, out_t, out_e, rec_path, rep_path = sys.argv[1:8]
    z = np.load(tpath); arrays = {k: z[k].copy() for k in z.files}
    H0 = arrays["heights"].astype(np.float64); H = H0.copy()
    env = np.load(epath).astype(np.float64); env_new = env.copy()
    records, rep = [], []
    core = np.zeros(H.shape, bool)                                                     # channel floor: never raised
    seat_floor = np.full(H.shape, -np.inf)                                             # end fit: the slope guard stops here
    for s in json.load(open(spath)):
        m = model_info(s["model"])
        b = math.radians(s["bearing"]); d = np.array([math.sin(b), 0.0, math.cos(b)])
        C = np.array([s["x"], 0.0, s["z"]])
        n_sp = int(s.get("spans", 1)); half_all = n_sp * m["half"]
        e1, e2 = C - half_all * d, C + half_all * d
        nl = np.array([d[2], 0.0, -d[0]])                                                  # horizontal, across the road
        a1, a2 = tri_h(H0, e1[0], e1[2]), tri_h(H0, e2[0], e2[2])
        k_pitch = (a2 - a1) / (2 * half_all)                                                # deck rise per metre from e1
        def end_h(e, inward, rise):
            strip = max(tri_h(H0, *(e + a * inward + l * nl)[[0, 2]]) - a * rise for a in np.linspace(0.0, END_IN, 5)
                        for l in np.linspace(-m["end_half_w"], m["end_half_w"], 9))
            return strip + END_CLEAR
        h1, h2 = max(a1, end_h(e1, d, k_pitch)), max(a2, end_h(e2, -d, -k_pitch))
        phi = math.atan2(h2 - h1, 2 * half_all)
        f = np.array([d[0] * math.cos(phi), math.sin(phi), d[2] * math.cos(phi)])          # model length axis
        u = np.array([-d[0] * math.sin(phi), math.cos(phi), -d[2] * math.sin(phi)])         # model up
        if m["axis"] == 0:
            X, Y = f, u; Z = np.cross(X, Y)
        else:
            Z, Y = f, u; X = np.cross(Y, Z)
        Rm = np.stack([X, Y, Z], axis=1)                                                     # columns = local axes
        y_end = (m["end_y"][0] + m["end_y"][1]) / 2
        local_c = np.zeros(3); local_c[m["axis"]] = m["centre_len"]; local_c[2 - m["axis"]] = m["centre_lat"]
        span_pos = []
        for k in range(n_sp):
            frac = (2 * k + 1) / (2 * n_sp)                                                   # 0..1 along e1 -> e2
            Ck = C + (-half_all + (2 * k + 1) * m["half"]) * d
            pos = Ck - Rm @ np.array([local_c[0], 0.0, local_c[2]])
            pos[1] = h1 + frac * (h2 - h1) - y_end * math.cos(phi)
            matrix = [*X.tolist(), *Y.tolist(), *Z.tolist(), *pos.tolist()]
            records.append(dict(site=s["id"], span=k, model=f"dz\\structures\\roads\\bridges\\{s['model']}.p3d", matrix=matrix))
            span_pos.append(pos)
        pos = np.mean(span_pos, axis=0)
        # channel and seals
        wb = math.radians(s["water_bearing"]); wd = np.array([math.sin(wb), math.cos(wb)])
        wn = np.array([-wd[1], wd[0]])
        W = float(s["width"])
        flat = half_all - 6.5
        deck_half_w = m["width"] / 2 + 1.0
        frz = arrays["reserve"] | arrays["platform"] | arrays["narva"]
        run_end, cut_side, run_side, wet_side = 0.0, {}, {}, {}
        for sgn in (-1, 1):                                                            # per side: frozen run, first water
            last, gap = 0.0, 0.0
            for tt in np.arange(0.0, 60.0, 1.0):
                xx, zz = s["x"] + sgn * tt * wd[0], s["z"] + sgn * tt * wd[1]
                if frz[int(round((ZTOP - zz) / 6)), int(round(xx / 6))]:
                    last, gap = tt, 0.0
                else:
                    gap += 1.0
                    if gap > 3.0 and tt > 3.0:
                        break
            first_wet = 0.0
            for tt in np.arange(4.0, 60.0, 1.0):
                xx, zz = s["x"] + sgn * tt * wd[0], s["z"] + sgn * tt * wd[1]
                if min(tri_h(H0, xx + u * wd[1], zz - u * wd[0]) for u in (-3.0, -1.5, 0.0, 1.5, 3.0)) < float(s["level"]) - 0.01:
                    first_wet = tt; break
            run_end = max(run_end, last); run_side[sgn] = last; wet_side[sgn] = first_wet
            cut_side[sgn] = max(CUT_T, min(max(last + 6.0, first_wet + 4.0), 60.0))
        cut_t = max(cut_side.values())
        k = int((cut_t + 30) / 6) + 2
        rc, cc = int((ZTOP - s["z"]) / 6), int(s["x"] / 6)
        R_, C_ = np.mgrid[rc - k:rc + k + 1, cc - k:cc + k + 1]
        X_, Z_ = 6.0 * C_ - s["x"], (ZTOP - 6.0 * R_) - s["z"]
        t = X_ * wd[0] + Z_ * wd[1]; q = X_ * wn[0] + Z_ * wn[1]
        envv = np.full(H.shape, False)
        fin = np.isfinite(env)
        for dr in (0, 1):
            for dc in (0, 1):
                envv[dr:dr + 2047, dc:dc + 2047] |= fin
        in_t = (t >= -cut_side[-1]) & (t <= cut_side[1])
        axis = (np.abs(q) <= W / 2) & in_t
        sub0 = (slice(rc - k, rc + k + 1), slice(cc - k, cc + k + 1))
        sea_mode = bool((axis & ~envv[sub0] & (H0[sub0] < SEA)).any()) and not bool((axis & envv[sub0]).any())
        L = SEA if sea_mode else float(s["level"])
        bed = SEA_BED if sea_mode else max(BED_MIN, L - 0.5)
        sroad = X_ * d[0] + Z_ * d[2]
        target = bed + BANK * np.maximum(np.abs(q) - W / 2, 0)
        zone = in_t
        sub = (slice(rc - k, rc + k + 1), slice(cc - k, cc + k + 1))
        frozen = (arrays["reserve"] | arrays["platform"] | arrays["narva"])[sub]
        slat = X_ * d[2] - Z_ * d[0]                                                       # lateral offset from the road axis
        deck = (np.abs(sroad) <= flat) & (np.abs(slat) <= deck_half_w)
        allowed = zone & (~frozen | (np.abs(sroad) <= flat))
        hs = H[sub].copy()
        new = np.where(allowed, np.minimum(hs, target), hs)
        envl = np.zeros(H.shape, bool)                                                  # vertices of envelope cells at L
        fl = np.isfinite(env) & (np.abs(env - L) < 0.05)
        for dr in (0, 1):
            for dc in (0, 1):
                envl[dr:dr + 2047, dc:dc + 2047] |= fl
        links = []
        for sgn in (-1, 1):
            if wet_side[sgn] or sea_mode:
                continue
            cand = envl[sub] & (H0[sub] < L - 0.01) & (sgn * t > max(run_side[sgn], 6.0)) & ~frozen & (np.hypot(X_, Z_) <= 60.0)
            if not cand.any():
                continue
            i = int(np.argmin(np.where(cand, np.hypot(X_, Z_), np.inf)))
            tgt = np.array([X_.flat[i], Z_.flat[i]]); st = np.array(wd) * sgn * (run_side[sgn] + 3.0)
            ab = tgt - st; tt_ = np.clip(((X_ - st[0]) * ab[0] + (Z_ - st[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
            dl = np.hypot(X_ - (st[0] + tt_ * ab[0]), Z_ - (st[1] + tt_ * ab[1]))
            new = np.where(~frozen & (dl <= W / 2 + 8.0), np.minimum(new, bed + BANK * np.maximum(dl - W / 2, 0)), new)
            links.append(dict(side=sgn, start=(st + [s["x"], s["z"]]).round(1).tolist(), target=(tgt + [s["x"], s["z"]]).round(1).tolist()))
            core[sub] |= (dl <= W / 2) & ~frozen
        # end fit: on each outer end seat and its 1:CONE flanks the cut terrain must not lie below the seat or the source
        px, pz, py = [], [], []; tp = math.tan(phi)
        for (e_, inw, h_e, y_e), st in zip(((e1, 1.0, h1, m["end_y"][0]), (e2, -1.0, h2, m["end_y"][1])), m["seats"]):
            aa, ll = np.meshgrid(np.r_[np.arange(-0.15, st["a_in"], 0.5), st["a_in"] + 0.15], np.arange(-st["hw"] - END_RING, st["hw"] + END_RING + 0.01, 0.5))
            r_ = np.hypot(np.maximum(np.maximum(-aa, aa - st["a_in"]), 0), np.maximum(np.abs(ll) - st["hw"], 0))
            ok = r_ <= END_RING; ac = np.clip(aa[ok], 0, st["a_in"])
            px.append(e_[0] + inw * aa[ok] * d[0] + ll[ok] * nl[0]); pz.append(e_[2] + inw * aa[ok] * d[2] + ll[ok] * nl[2])
            py.append(h_e + inw * tp * ac + np.interp(ac, st["a_k"], st["y_k"]) - y_e - r_[ok] / CONE)
        rr, cl, wt = tri_w(np.concatenate(px), np.concatenate(pz)); rr, cl = rr - (rc - k), cl - (cc - k)
        py = np.minimum(np.concatenate(py), (hs[rr, cl] * wt).sum(1))                  # never more than the source gave
        cut0, dry = new.copy(), new >= L                                               # wet vertices keep their cut
        if W < 6.0:                                                                    # channel narrower than a cell: so do their neighbours
            wet = ~dry
            dry[1:, :] &= ~wet[:-1, :]; dry[:-1, :] &= ~wet[1:, :]; dry[:, 1:] &= ~wet[:, :-1]; dry[:, :-1] &= ~wet[:, 1:]
            dry[1:, 1:] &= ~wet[:-1, :-1]; dry[:-1, :-1] &= ~wet[1:, 1:]
        for _ in range(20):                                                            # undo the cut, largest weight first
            dfc = py - (new[rr, cl] * wt).sum(1)
            mw = np.where(dry[rr, cl] & (new[rr, cl] < hs[rr, cl] - 1e-6), wt, 0.0)
            j = np.argmax(mw, 1); wj = mw[np.arange(len(j)), j]; bad = (dfc > 0.01) & (wj > 0.05)
            if not bad.any():
                break
            vr, vc = rr[bad, j[bad]], cl[bad, j[bad]]
            np.maximum.at(new, (vr, vc), np.minimum(new[vr, vc] + dfc[bad] / wj[bad], hs[vr, vc]))
        held = new > cut0
        tch = np.zeros(new.shape, bool); tch[rr[wt > 0], cl[wt > 0]] = True
        seat_floor[sub] = np.where(tch & dry, np.maximum(seat_floor[sub], new), seat_floor[sub])
        core[sub] |= (np.abs(q) <= W / 2) & zone & allowed & ~held
        H[sub] = new
        cR, cC = np.mgrid[rc - k:rc + k, cc - k:cc + k]
        cx, cz = 6.0 * cC + 3 - s["x"], (ZTOP - 6.0 * cR - 3) - s["z"]
        ct, cq = cx * wd[0] + cz * wd[1], cx * wn[0] + cz * wn[1]
        seal = (np.abs(cq) <= W / 2 + 6) & (ct >= -cut_side[-1]) & (ct <= cut_side[1])
        for lk in links:
            st = np.array(lk["start"]) - [s["x"], s["z"]]; tg = np.array(lk["target"]) - [s["x"], s["z"]]; ab = tg - st
            tt_ = np.clip(((cx - st[0]) * ab[0] + (cz - st[1]) * ab[1]) / max(ab @ ab, 1e-9), 0, 1)
            seal |= np.hypot(cx - (st[0] + tt_ * ab[0]), cz - (st[1] + tt_ * ab[1])) <= W / 2 + 6
        es = env_new[rc - k:rc + k, cc - k:cc + k]
        block = np.isfinite(es) & (np.abs(es - L) > 0.05)
        if not sea_mode:
            env_new[rc - k:rc + k, cc - k:cc + k] = np.where(seal & ~block, L, es)
        under = deck & (np.abs(q) <= W / 2)                                                  # channel inside the deck footprint
        rep.append(dict(site=s["id"], model=s["model"], spans=n_sp, cut_t=round(cut_t, 1), cut_up_down=[round(cut_side[1], 1), round(cut_side[-1], 1)], frozen_run_m=run_end, links=links, water="sea" if sea_mode else "pond", pitch_deg=round(math.degrees(phi), 3), ends_road_y=[round(h1, 3), round(h2, 3)], ends_lift=[round(h1 - a1, 3), round(h2 - a2, 3)],
                        position=[round(v, 3) for v in pos], deck_road_mid=round(pos[1] + (m["deck_max"] if m["axis"] == 0 else y_end), 2), level=L, bed=bed,
                        cut_vertices=int((new < hs).sum()), cut_frozen_vertices=int(((new < hs) & frozen).sum()), end_fit_restored=int(held.sum()),
                        end_fit_short_m=round(float(max(0.0, (py - (new[rr, cl] * wt).sum(1)).max())), 2),
                        max_cut_m=round(float((hs - new).max()), 2), channel_ground_max_under_deck=round(float(new[under].max()), 2) if under.any() else None,
                        seal_cells=0 if sea_mode else int((seal & ~block).sum())))
    def tri_slopes(A_):
        nw, ne, sw, se = A_[:-1, :-1], A_[:-1, 1:], A_[1:, :-1], A_[1:, 1:]
        return (np.degrees(np.arctan(np.hypot((ne - nw) / 6.0, (ne - se) / 6.0))),
                np.degrees(np.arctan(np.hypot((se - sw) / 6.0, (nw - sw) / 6.0))))
    frz_all = arrays["reserve"] | arrays["platform"] | arrays["narva"]
    s0 = tri_slopes(H0); guard = 0; stuck = set()
    from scipy.ndimage import binary_dilation
    near = binary_dilation(H != H0, np.ones((3, 3), bool), iterations=2)
    for it in range(80):                                                               # lay back walls in 0.1 m steps
        s1 = tri_slopes(H); ch = H != H0; low = np.zeros(H.shape, bool)
        for (a0, a1), cor in zip(zip(s0, s1), (((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 1), (1, 0)))):
            chc = np.zeros(a0.shape, bool)
            for dr, dc in cor:
                chc |= ch[dr:dr + 2047, dc:dc + 2047]
            for r, c in np.argwhere(chc & (a1 > np.maximum(35.0, a0) + 1e-4)):
                top_v = max(((r + dr, c + dc) for dr, dc in cor), key=lambda v: H[v])
                if not core[top_v] and not frz_all[top_v] and near[top_v] and H[top_v] - 0.1 >= seat_floor[top_v] - 1e-6:
                    low[top_v] = True
                else:
                    stuck.add((int(r), int(c)))
        if not low.any():
            break
        H = np.where(low, H - 0.1, H); guard += int(low.sum()); stuck = set()
    arrays["heights"] = H.astype(np.float32)
    arrays["v31_bridge_cut"] = (H != H0) | arrays.get("v31_bridge_cut", np.zeros(H.shape, bool))   # keep earlier bridges' cuts
    np.savez(out_t, **arrays); np.save(out_e, env_new.astype(np.float32))
    json.dump(records, open(rec_path, "w"), indent=1)
    json.dump(dict(schema="bridges-v31.v5", params=dict(BANK=BANK, CUT_T=CUT_T, BED_MIN=BED_MIN, END_IN=END_IN, END_CLEAR=END_CLEAR, CONE=CONE, END_RING=END_RING, RAMP_T=RAMP_T), sites=rep, slope_guard_steps=guard, slope_stuck_triangles=len(stuck)),
              open(rep_path, "w", newline="\n"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
