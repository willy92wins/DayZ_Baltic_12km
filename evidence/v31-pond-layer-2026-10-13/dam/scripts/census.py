"""Census of pond/engine-sea contacts on a terrain + footprint. Definitions as sills_and_cones_ev102.py:25,100-107,190-192."""
import json, sys
import numpy as np
from scipy.ndimage import binary_dilation, label
SEA = 0.75
N8 = np.ones((3, 3), bool); S4 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
CLS = ["land", "sea", "lake", "navigable", "delta", "river", "stream", "pond"]   # build_v30_water.py:408-409


def c2v_any(m):
    o = np.zeros((2048, 2048), bool)
    for dr in (0, 1):
        for dc in (0, 1):
            o[dr:dr + 2047, dc:dc + 2047] |= m
    return o


def c2v_max(a):
    o = np.full((2048, 2048), -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            o[dr:dr + 2047, dc:dc + 2047] = np.maximum(o[dr:dr + 2047, dc:dc + 2047], a)
    return o


def cmin(A):
    return np.minimum.reduce([A[:-1, :-1], A[1:, :-1], A[:-1, 1:], A[1:, 1:]])


def masks(H, plane):
    covered = np.isfinite(plane)
    VP = c2v_max(np.where(covered, plane, -np.inf)); touch = np.isfinite(VP)
    seav = (H < SEA) & ~touch                         # sea vertex (sills_and_cones_ev102.py:102)
    seacell = (~covered) & (cmin(H) < SEA)            # cell showing engine sea (:190-191)
    c8 = covered & binary_dilation(seacell, N8)       # EV102 contact metric
    c4 = covered & binary_dilation(seacell, S4)       # edge-sharing contact
    src = touch & binary_dilation(seav, N8)           # sill sources (:107)
    return covered, VP, touch, seav, seacell, c8, c4, src


def main():
    terr, fpp, out = sys.argv[1:4]
    z = np.load(terr); H = z["heights"].astype(np.float64)
    plane = np.load(fpp)["plane"].astype(np.float64)
    covered, VP, touch, seav, seacell, c8, c4, src = masks(H, plane)
    lab, n = label(binary_dilation(c8, np.ones((5, 5), bool)), N8)
    PB, npb = label(covered, N8); psize = np.bincount(PB.ravel())
    SB, nsb = label(seav, S4); ssize = np.bincount(SB.ravel())
    narva, res, plat, cls = z["narva"], z["reserve"], z["platform"], z["cls"]
    conv, r102, lag, kit = z["ev96_converted_to_sea"], z["ev102_raised"], z["v31_lagoon"], z["v31_kit"]
    sites = []
    for i in range(1, n + 1):
        m = (lab == i)
        cm = m & c8
        if not cm.any():
            continue
        rr, cc = np.nonzero(cm)
        vm = c2v_any(cm)
        nb = binary_dilation(vm, np.ones((7, 7), bool))   # +-3 vertices = 18 m
        bodies = np.unique(PB[cm]); planes = np.unique(np.round(plane[cm], 3))
        pv = nb & touch & np.isin(cls, (2, 3, 4, 5, 6, 7))
        pcls = np.bincount(cls[pv], minlength=8) if pv.any() else np.zeros(8, int)
        sv = nb & seav
        scls = np.bincount(cls[sv], minlength=8) if sv.any() else np.zeros(8, int)
        sb = np.unique(SB[sv]); sb = sb[sb > 0]
        sites.append(dict(
            id=len(sites) + 1, x=round(6 * cc.mean() + 3, 1), z=round(12282 - 6 * rr.mean() - 3, 1),
            bbox_x=[int(6 * cc.min()), int(6 * cc.max() + 6)], bbox_z=[int(12282 - 6 * rr.max() - 6), int(12282 - 6 * rr.min())],
            contact_cells_8=int(cm.sum()), contact_cells_4=int((cm & c4).sum()),
            sill_sources=int((nb & src).sum()), planes=[float(p) for p in planes],
            pond_body_cells=[int(psize[b]) for b in bodies],
            pond_cls=CLS[int(np.argmax(pcls))] if pcls.sum() else None,
            pond_cls_hist={CLS[k]: int(v) for k, v in enumerate(pcls) if v},
            sea_cls_hist={CLS[k]: int(v) for k, v in enumerate(scls) if v},
            sea_body_vertices=[int(ssize[b]) for b in sb],
            sea_min_terrain=round(float(H[sv].min()), 3) if sv.any() else None,
            narva_vertices=int((nb & narva).sum()), reserve_vertices=int((nb & res).sum()),
            platform_vertices=int((nb & plat).sum()), ev102_raised_vertices=int((nb & r102).sum()),
            ev96_converted_vertices=int((nb & conv).sum()), lagoon_vertices=int((nb & lag).sum()),
            kit_vertices=int((nb & kit).sum()), step_m=round(float(planes.max()) - SEA, 3)))
    tot = dict(contact_cells_8=int(c8.sum()), contact_cells_4=int(c4.sum()), sill_sources=int(src.sum()),
               sites=len(sites), sea_cells=int(seacell.sum()), covered_cells=int(covered.sum()))
    json.dump(dict(schema="dam-census.v1", terrain=terr, footprint=fpp, totals=tot, sites=sites), open(out, "w"), indent=1)
    print(json.dumps(tot))
    for s in sites:
        print(s["id"], s["x"], s["z"], "c8", s["contact_cells_8"], "c4", s["contact_cells_4"], "planes", s["planes"][:4],
              "body", s["pond_body_cells"][:3], s["pond_cls"], "sea", s["sea_body_vertices"][:3], s["sea_cls_hist"],
              "narva", s["narva_vertices"], "res", s["reserve_vertices"], "plat", s["platform_vertices"],
              "r102", s["ev102_raised_vertices"], "conv", s["ev96_converted_vertices"], "lag", s["lagoon_vertices"], "kit", s["kit_vertices"])


if __name__ == "__main__":
    main()
