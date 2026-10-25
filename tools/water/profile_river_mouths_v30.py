"""River mouths down to the sea (BALTIC-015 variant): re-profile the water that relies on the engine sea.

The engine sea is tidal (0.50-1.00 m). Pond-class water at or below the 0.80 m sea cut has no pond piece and shows the
sea, so the first plane upstream ends 0.30 m above the low-tide sea. Per 8-connected component of that water touching
the sea or the delta: geodesic distance inside the component from its sea/delta side (D_s) and from its side on the
first planes (D_u, pond-class water above the cut); level = LOW + (CUT - LOW) * D_s / (D_s + D_u). With the candidate
sea cut (--new-cut, 0.51 m) the planes then step down 25 mm at a time to 0.525 m.
Beds: a wet vertex of the components goes down to min(level - 0.101, new adjacent planes - 0.0501) when it is higher,
and to min(level - 0.101, 0.45) where it still has no plane (wet at low tide); protected vertices (24 m channel corridors, road platforms
and reserves, Narva) never move and are reported if they would need it. Classes unchanged; other vertices unchanged.
Usage: profile_river_mouths_v30.py --terrain <npz> --out <dir> [--new-cut 0.51]
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'terrain'))
from v30_common import POND_CLASSES, cell_planes, vertex_plane_bounds  # noqa: E402
from finish_shores_v30 import protect_corridors  # noqa: E402

LOW, CUT = 0.50, 0.80
N = 2048
EIGHT = np.ones((3, 3), bool)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geodesic(mask, seeds):
    """Distance in metres inside mask (8-connected grid, 6 m and 6*sqrt(2) steps) to the nearest seed."""
    idx = -np.ones(mask.shape, np.int64)
    rr, cc = np.nonzero(mask)
    idx[rr, cc] = np.arange(len(rr))
    rows, cols, wts = [], [], []
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        r2, c2 = rr + dr, cc + dc
        ok = (r2 >= 0) & (r2 < N) & (c2 >= 0) & (c2 < N)
        ok[ok] = mask[r2[ok], c2[ok]]
        rows.append(idx[rr[ok], cc[ok]]); cols.append(idx[r2[ok], c2[ok]])
        wts.append(np.full(ok.sum(), 6.0 * (2 ** 0.5 if dr and dc else 1.0)))
    g = coo_matrix((np.concatenate(wts), (np.concatenate(rows), np.concatenate(cols))), shape=(len(rr),) * 2).tocsr()
    d = dijkstra(g, directed=False, indices=idx[seeds & mask], min_only=True)
    out = np.full(mask.shape, np.inf)
    out[rr, cc] = d
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--terrain', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--new-cut', type=float, default=0.51)
    a = ap.parse_args()
    assert not a.out.exists(), 'fresh output required'
    t = dict(np.load(a.terrain))
    cls, level, h = t['cls'], t['level'].astype(float), t['heights'].astype(float)
    pond = np.isin(cls, POND_CLASSES)
    low = pond & (np.nan_to_num(level, nan=99.0) <= CUT)
    lab, n = ndimage.label(low, structure=EIGHT)
    sea_side = ndimage.binary_dilation(np.isin(cls, (1, 4)), structure=EIGHT)
    up_side = ndimage.binary_dilation(pond & (np.nan_to_num(level, nan=-1.0) > CUT), structure=EIGHT)
    new_level = level.copy()
    comps = []
    for k in range(1, n + 1):
        m = lab == k
        s, u = m & sea_side, m & up_side
        rr, cc = np.nonzero(m)
        info = {'vertices': int(m.sum()), 'x': round(float(6 * cc.mean()), 1), 'z': round(float(12282 - 6 * rr.mean()), 1),
                'old_level_m': [round(float(level[m].min()), 3), round(float(level[m].max()), 3)],
                'sea_side': int(s.sum()), 'plane_side': int(u.sum())}
        if not s.any() or not u.any():
            info['status'] = 'skipped: needs both a sea/delta side and a plane side'
            comps.append(info)
            continue
        ds, du = geodesic(m, s), geodesic(m, u)
        ok = m & np.isfinite(ds) & np.isfinite(du)
        new_level[ok] = LOW + (CUT - LOW) * ds[ok] / np.maximum(ds[ok] + du[ok], 1e-9)
        info.update(status='re-profiled', unreached=int((m & ~ok).sum()),
                    new_level_m=[round(float(new_level[ok].min()), 3), round(float(new_level[ok].max()), 3)],
                    length_m=round(float(np.max(ds[ok] + du[ok])), 1))
        comps.append(info)
    changed_level = np.isfinite(level) & (np.abs(new_level - level) > 1e-9)

    # beds under the new planes (and wet at low tide where there is still no plane)
    planes = cell_planes(cls, new_level, sea_cut=a.new_cut)
    pmin, _ = vertex_plane_bounds(planes)
    _, corridor, _, _ = protect_corridors(planes)
    fixed = corridor | t['platform'] | t['reserve'] | t['narva']
    target = np.minimum(new_level - 0.101, np.where(np.isfinite(pmin), pmin - 0.0501, 0.45))  # margin over the 0.10 gate
    need = changed_level & (h > target + 1e-9)
    new_h = h.copy()
    move = need & ~fixed
    new_h[move] = target[move]
    blocked = need & fixed
    old_planes = cell_planes(cls, level)
    t2 = dict(t)
    t2['heights'] = new_h.astype(t['heights'].dtype)
    t2['level'] = new_level.astype(t['level'].dtype)
    a.out.mkdir(parents=True)
    dest = a.out / 'terrain_mouths.npz'
    np.savez_compressed(dest, **t2)
    report = {
        'status': 'BUILT_PENDING_WATER_PATCH_AND_GATES', 'low_m': LOW, 'cut_m': CUT, 'new_cut_m': a.new_cut,
        'components': comps, 'levels_changed': int(changed_level.sum()),
        'beds_lowered': int(move.sum()), 'max_bed_lowering_m': round(float((h - new_h).max()), 3),
        'beds_blocked_by_protection': int(blocked.sum()),
        'blocked_sample': [[int(r), int(c), round(float(h[r, c] - target[r, c]), 3)] for r, c in zip(*np.nonzero(blocked))][:20],
        'plane_cells_old': int(np.isfinite(old_planes).sum()), 'plane_cells_new': int(np.isfinite(planes).sum()),
        'plane_cells_changed': int((np.nan_to_num(old_planes, nan=-9) != np.nan_to_num(planes, nan=-9)).sum()),
        'new_plane_min_m': round(float(np.nanmin(planes[np.isnan(old_planes) & np.isfinite(planes)])), 3)
        if (np.isnan(old_planes) & np.isfinite(planes)).any() else None,
        'terrain_sha256': sha(a.terrain), 'output_sha256': sha(dest), 'tool_sha256': sha(__file__),
        'limits': ['Levels and beds only in the re-profiled components; classes unchanged.',
                   'Consumers must use the same sea cut (pieces, fitter, gates).']}
    (a.out / 'report.json').write_text(json.dumps(report, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'blocked_sample'}, indent=1))


if __name__ == '__main__':
    main()
