"""Shared evaluation harness for shoreline candidates on top of EV98 (fixed before any candidate is built).

Usage: eval_shore.py <candidate.npz> <out.json> [--base terrain-ev98.npz] [--cover cover-level-ev98.npy]

Model. Vertex grid H (2048x2048, 6 m, row 0 = north). Cell (r, c) has corners (r,c),(r,c+1),(r+1,c),(r+1,c+1) and the
native NW-SE diagonal. A covered cell draws a pond plane at cover[r, c]; any other cell shows the engine sea where the
terrain dips below it (SEA = 0.75 m, crest SEA_CREST = 0.95 m).

Gates (all must hold; thresholds are fixed here and must not be tuned per candidate):
  frozen      no change on reserve | platform vertices.
  band        every changed vertex lies within BAND_M of the base waterline (base wet/dry boundary).
  pond_bed    a vertex below the max plane of its covered incident cells has height >= SEA_CLEAR (1.0 m).
  piece_edge  every corner of an uncovered cell that touches a covered cell stays >= that plane + EDGE_MARGIN,
              unless the base already violated it at that vertex (no new exposed piece edges / dry holes).
  new_sea     uncovered cells whose min corner drops below SEA_CREST in the candidate but not in the base must be
              8-connected to cells that already did in the base (sea may advance only along existing coast).
  slope       every triangle with a changed corner has slope <= max(35 deg, its base slope) + 0.01.
Metrics (base and candidate, whole map and St Petersburg window): waterline length; sawtooth = local maxima of
turning over 12 m above 60 deg per km; corners = local maxima of turning over 30 m above 45 deg per km.
"""
import argparse, json, sys
import numpy as np
from scipy.ndimage import binary_dilation, label, distance_transform_edt, maximum_filter1d
import contourpy

SEA, SEA_CREST, SEA_CLEAR = 0.75, 0.95, 1.0
BAND_M, EDGE_MARGIN = 24.0, 0.05
SPB = (7800.0, 10200.0, 9000.0, 11000.0)  # x0, x1, z0, z1


def cell_corners(a):
    return a[:-1, :-1], a[:-1, 1:], a[1:, :-1], a[1:, 1:]  # NW, NE, SW, SE


def vertex_plane(cover):
    """Max covered plane over the (up to 4) cells incident to each vertex; NaN where none is covered."""
    p = np.full((2048, 2048), -np.inf)
    c = np.where(np.isfinite(cover), cover, -np.inf)
    p[:-1, :-1] = np.maximum(p[:-1, :-1], c); p[:-1, 1:] = np.maximum(p[:-1, 1:], c)
    p[1:, :-1] = np.maximum(p[1:, :-1], c); p[1:, 1:] = np.maximum(p[1:, 1:], c)
    return np.where(np.isfinite(p), p, np.nan)


def tri_slopes(H):
    nw, ne, sw, se = cell_corners(H.astype(np.float64))
    # triangle A = NW, NE, SE ; triangle B = NW, SE, SW (6 m legs)
    ga = np.hypot((ne - nw) / 6, (ne - se) / 6)
    gb = np.hypot((se - sw) / 6, (nw - sw) / 6)
    return np.degrees(np.arctan(ga)), np.degrees(np.arctan(gb))


def waterline_metrics(H, vplane, window=None):
    lw = np.where(np.isfinite(vplane), vplane, SEA)
    f = H.astype(np.float64) - lw
    out = dict(length_km=0.0, sawtooth=0, corners=0)
    gen = contourpy.contour_generator(z=f, name='serial', line_type=contourpy.LineType.Separate)
    for cnt in gen.lines(0.0):
        c, r = cnt[:, 0], cnt[:, 1]
        x, z = c * 6.0, (2047 - r) * 6.0
        if window is not None:
            x0, x1, z0, z1 = window
            keep = (x >= x0) & (x <= x1) & (z >= z0) & (z <= z1)
            if keep.sum() < 4:
                continue
            x, z = x[keep], z[keep]
        seg = np.hypot(np.diff(x), np.diff(z))
        s = np.r_[0, np.cumsum(seg)]
        if s[-1] < 40:
            continue
        t = np.arange(0, s[-1], 3.0)
        xi, zi = np.interp(t, s, x), np.interp(t, s, z)
        out["length_km"] += s[-1] / 1000
        for w, thr, key in ((12.0, 60.0, "sawtooth"), (30.0, 45.0, "corners")):
            k = int(round(w / 2 / 3.0))
            if len(t) <= 2 * k + 1:
                continue
            d1 = np.arctan2(zi[k:-k] - zi[:-2 * k], xi[k:-k] - xi[:-2 * k])
            d2 = np.arctan2(zi[2 * k:] - zi[k:-k], xi[2 * k:] - xi[k:-k])
            turn = np.degrees(np.abs(np.angle(np.exp(1j * (d2 - d1)))))
            peak = (turn == maximum_filter1d(turn, 2 * k + 1)) & (turn > thr)
            out[key] += int(peak.sum())
    L = max(out["length_km"], 1e-9)
    out["sawtooth_per_km"] = round(out["sawtooth"] / L, 3)
    out["corners_per_km"] = round(out["corners"] / L, 3)
    out["length_km"] = round(out["length_km"], 3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate"); ap.add_argument("out")
    ap.add_argument("--base", default="E:/DayZ-Baltic-Build/v30-pond-sea-separation-20261011-b/terrain-ev98.npz")
    ap.add_argument("--cover", default="E:/DayZ-Baltic-Build/v30-shore-sdf-20261011/cover-level-ev98.npy")
    a = ap.parse_args()
    b = np.load(a.base); c = np.load(a.candidate)
    H0 = b["heights"].astype(np.float64); H1 = c["heights"].astype(np.float64)
    cover = np.load(a.cover)
    frozen = b["reserve"] | b["platform"]
    vp = vertex_plane(cover)
    ch = H1 != H0
    gates = {}
    gates["frozen"] = int((ch & frozen).sum())
    wet0 = np.where(np.isfinite(vp), H0 < vp, H0 < SEA)
    edge = wet0 ^ binary_dilation(wet0, np.ones((3, 3)))
    dist = distance_transform_edt(~(edge | (wet0 & binary_dilation(~wet0, np.ones((3, 3)))))) * 6.0
    gates["band"] = int((ch & (dist > BAND_M)).sum())
    under0, under1 = np.isfinite(vp) & (H0 < vp), np.isfinite(vp) & (H1 < vp)
    gates["pond_bed"] = int((under1 & (H1 < SEA_CLEAR - 1e-6) & ~(under0 & (H0 < SEA_CLEAR - 1e-6))).sum())
    covered = np.isfinite(cover)
    touch = np.full(cover.shape, -np.inf)
    cpad = np.pad(np.where(covered, cover, -np.inf), 1, constant_values=-np.inf)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr or dc:
                touch = np.maximum(touch, cpad[1 + dr:1 + dr + 2047, 1 + dc:1 + dc + 2047])
    rim = ~covered & np.isfinite(touch)
    viol0 = np.zeros((2048, 2048), bool); viol1 = np.zeros((2048, 2048), bool)
    for (dr, dc) in ((0, 0), (0, 1), (1, 0), (1, 1)):
        sl = (slice(dr, dr + 2047), slice(dc, dc + 2047))
        viol0[sl] |= rim & (H0[sl] < touch + EDGE_MARGIN)
        viol1[sl] |= rim & (H1[sl] < touch + EDGE_MARGIN)
    gates["piece_edge"] = int((viol1 & ~viol0).sum())
    mn0 = np.minimum.reduce(cell_corners(H0)); mn1 = np.minimum.reduce(cell_corners(H1))
    sea0 = ~covered & (mn0 < SEA_CREST); sea1 = ~covered & (mn1 < SEA_CREST)
    lab, _ = label(sea1, np.ones((3, 3)))
    ok = np.unique(lab[sea0]); ok = ok[ok > 0]
    new = sea1 & ~sea0
    gates["new_sea"] = int((new & ~np.isin(lab, ok)).sum())
    sa0, sb0 = tri_slopes(H0); sa1, sb1 = tri_slopes(H1)
    cch = np.maximum.reduce(cell_corners(ch.astype(np.uint8))).astype(bool)
    bad = cch & (((sa1 > np.maximum(35, sa0) + 0.01)) | ((sb1 > np.maximum(35, sb0) + 0.01)))
    gates["slope"] = int(bad.sum())
    passed = all(v == 0 for v in gates.values())
    res = dict(schema="shore-eval.v1", candidate=a.candidate, base=a.base, gates_violations=gates, gates_pass=passed,
               changed_vertices=int(ch.sum()), max_abs_change_m=round(float(np.abs(H1 - H0).max()), 3),
               metrics=dict(base_map=waterline_metrics(H0, vp), cand_map=waterline_metrics(H1, vp),
                            base_spb=waterline_metrics(H0, vp, SPB), cand_spb=waterline_metrics(H1, vp, SPB)))
    open(a.out, "w").write(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
