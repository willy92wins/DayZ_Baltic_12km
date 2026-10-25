"""Near-contact census: pond pieces within 3 cells (18 m) of an engine-sea cell, grouped, with the land crest between them
and whether the EV102/EV103 sills raised it. Same masks as census.py."""
import json, sys
import numpy as np
from scipy.ndimage import binary_dilation, label, distance_transform_edt
sys.path.insert(0, __import__("os").path.dirname(__file__))
from census import masks, c2v_any, CLS, SEA, N8

terr, fpp, out = sys.argv[1:4]
z = np.load(terr); H = z["heights"].astype(np.float64)
plane = np.load(fpp)["plane"].astype(np.float64)
covered, VP, touch, seav, seacell, c8, c4, src = masks(H, plane)
dcell = distance_transform_edt(~seacell)            # cells to the nearest sea cell (centre to centre)
near = covered & (dcell <= 3.0)
lab, n = label(binary_dilation(near, np.ones((9, 9), bool)), N8)
narva, res, plat, cls = z["narva"], z["reserve"], z["platform"], z["cls"]
r102, conv = z["ev102_raised"], z["ev96_converted_to_sea"]
PB, _ = label(covered, N8); psize = np.bincount(PB.ravel())
sites = []
for i in range(1, n + 1):
    cm = (lab == i) & near
    if not cm.any():
        continue
    rr, cc = np.nonzero(cm)
    vm = c2v_any(cm); nb = binary_dilation(vm, np.ones((9, 9), bool))
    # land strip between: dry vertices (not touch, H >= SEA) within the neighbourhood
    strip = nb & ~touch & ~seav
    pl = float(np.nanmax(plane[cm]))
    crest_free = float(np.median(H[strip])) - pl if strip.any() else None
    pv = nb & touch & np.isin(cls, (2, 3, 4, 5, 6, 7))
    pcls = np.bincount(cls[pv], minlength=8)
    kind = ("narva" if (nb & narva).any() else
            "lake-outlet" if pcls.sum() and int(np.argmax(pcls)) == 2 else
            "river-to-sea" if pcls.sum() and int(np.argmax(pcls)) in (3, 4, 5, 6) else "other")
    sites.append(dict(id=len(sites) + 1, x=round(6 * cc.mean() + 3, 1), z=round(12282 - 6 * rr.mean() - 3, 1),
                      kind=kind, min_gap_cells=round(float(dcell[cm].min()), 2), near_cells=int(cm.sum()),
                      contact_cells_8=int((cm & c8).sum()), plane_max=pl, pond_cls=CLS[int(np.argmax(pcls))] if pcls.sum() else None,
                      pond_body_cells=int(max(psize[b] for b in np.unique(PB[cm]))),
                      strip_median_over_plane=None if crest_free is None else round(crest_free, 3),
                      ev102_raised=int((nb & r102).sum()), ev96_converted=int((nb & conv).sum()),
                      narva=int((nb & narva).sum()), reserve=int((nb & res).sum()), platform=int((nb & plat).sum())))
hist = {}
for s in sites:
    k = (s["kind"], "sill" if s["ev102_raised"] else "no-sill", "contact" if s["contact_cells_8"] else "gap")
    hist["/".join(k)] = hist.get("/".join(k), 0) + 1
json.dump(dict(schema="dam-near-census.v1", terrain=terr, footprint=fpp, radius_cells=3, sites=len(sites), by_kind=hist, list=sites), open(out, "w"), indent=1)
print(len(sites), json.dumps(hist, indent=1))
for s in sorted(sites, key=lambda s: s["min_gap_cells"])[:40]:
    print(s)
