"""Camera poses for the before/after shore views of the shore-crossing candidate (BALTIC-007 / -015).

Shore views: visible pond water (terrain below the plane of its cell, 2 m grid, native triangles) before and after the
shore fit; per 120 m tile, the area where it differs. The tiles with the largest difference, at least --spacing apart and
outside Narva, each get one view along their main shore from the land side (camera 9 m above the water, 20 m inland and
30 m back along the shore, looking 20 m ahead on the shore). Mouth views: per re-profiled mouth component
(profile_river_mouths_v30.py report), from 8 m above mean tide near its sea side, looking 80 m upstream.
Appends to --base (the pilot's 19 poses) and writes --out.
Usage: choose_shore_poses_v30.py --before <npz> --after <npz> --mouths <dir> --base <json> --out <json>
                                 [--count 8] [--spacing 900] [--sea-cut 0.51]
"""
from pathlib import Path
import argparse
import json
import sys

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'terrain'))
from v30_common import N, POND_CLASSES, cell_planes, tri_sample  # noqa: E402

NARVA = (2417.1428225906, 6889.8850822322)
NAMES = {2: 'lake', 3: 'navigable', 5: 'river', 6: 'stream', 7: 'pond'}
TILE = 120


def visible_diff(h0, h1, planes):
    """Per 120 m tile: m2 where visible pond water differs, and the centroid of that difference."""
    nt = int(np.ceil(12282 / TILE))
    area = np.zeros((nt, nt)); sx = np.zeros((nt, nt)); sz = np.zeros((nt, nt))
    xs = np.arange(1.0, 12282.0, 2.0)
    for j0 in range(0, len(xs), 1024):
        z = 12282.0 - xs[j0:j0 + 1024]
        X, Z = np.meshgrid(xs, z)
        ci = np.clip(((12282 - Z) // 6).astype(int), 0, N - 2)
        cj = np.clip((X // 6).astype(int), 0, N - 2)
        wl = planes[ci, cj]
        ok = np.isfinite(wl)
        v0 = ok & (tri_sample(h0, X, Z) < np.where(ok, wl, 0))
        v1 = ok & (tri_sample(h1, X, Z) < np.where(ok, wl, 0))
        d = v0 ^ v1
        ti, tj = (Z[d] // TILE).astype(int), (X[d] // TILE).astype(int)
        np.add.at(area, (ti, tj), 4.0)
        np.add.at(sx, (ti, tj), 4.0 * X[d])
        np.add.at(sz, (ti, tj), 4.0 * Z[d])
    return area, sx / np.maximum(area, 1), sz / np.maximum(area, 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('before', 'after', 'mouths', 'base', 'out'):
        ap.add_argument('--' + k, type=Path, required=True)
    ap.add_argument('--count', type=int, default=8)
    ap.add_argument('--spacing', type=float, default=900.0)
    ap.add_argument('--sea-cut', type=float, default=0.51)
    a = ap.parse_args()
    b, t = np.load(a.before), np.load(a.after)
    cls, level = t['cls'], t['level'].astype(float)
    planes = cell_planes(cls, level, sea_cut=a.sea_cut)
    area, cx, cz = visible_diff(b['heights'].astype(float), t['heights'].astype(float), planes)
    pond = np.isin(cls, POND_CLASSES)
    chosen = []
    for flat in np.argsort(-area, axis=None):
        ti, tj = np.unravel_index(flat, area.shape)
        if area[ti, tj] <= 0:
            break
        p = np.array([cx[ti, tj], cz[ti, tj]])
        if np.hypot(p[0] - NARVA[0], p[1] - NARVA[1]) < 800 or any(np.hypot(*(p - q['p'])) < a.spacing for q in chosen):
            continue
        r, c = int(round((12282 - p[1]) / 6)), int(round(p[0] / 6))
        win = (slice(max(r - 4, 0), r + 5), slice(max(c - 4, 0), c + 5))
        wr, wc = np.nonzero(pond[win])
        lr, lc = np.nonzero(cls[win] == 0)
        if not len(wr) or not len(lr):
            continue
        wr, wc, lr, lc = wr + win[0].start, wc + win[1].start, lr + win[0].start, lc + win[1].start
        to_land = np.array([6.0 * lc.mean() - 6.0 * wc.mean(), (12282.0 - 6.0 * lr.mean()) - (12282.0 - 6.0 * wr.mean())])
        n_land = to_land / max(np.linalg.norm(to_land), 1e-6)
        tan = np.array([-n_land[1], n_land[0]])
        near = planes[max(r - 4, 0):r + 4, max(c - 4, 0):c + 4]
        if not np.isfinite(near).any():
            continue
        wl = float(np.nanmax(near))
        cam, look = p + 20 * n_land - 30 * tan, p + 20 * tan
        kinds = [int(v) for v in cls[wr, wc]]
        chosen.append({'p': p, 'pose': {'name': f'SHORE{len(chosen)}_{NAMES[max(set(kinds), key=kinds.count)]}',
                                        'cam_pos': [round(float(cam[0]), 2), round(wl + 9.0, 2), round(float(cam[1]), 2)],
                                        'look_at': [round(float(look[0]), 2), round(wl, 2), round(float(look[1]), 2)],
                                        'visible_change_m2': round(float(area[ti, tj]), 1)}})
        if len(chosen) >= a.count:
            break
    poses = json.loads(a.base.read_text(encoding='utf-8'))['poses']
    poses = [{k: p[k] for k in ('name', 'cam_pos', 'look_at')} for p in poses]
    poses += [q['pose'] for q in chosen]
    # mouths: sea side of each re-profiled component, looking upstream along its new levels
    tm = np.load(a.mouths / 'terrain_mouths.npz')
    m_rep = json.loads((a.mouths / 'report.json').read_text(encoding='utf-8'))
    low = np.isin(cls, POND_CLASSES) & (np.nan_to_num(tm['level'].astype(float), nan=99) <= 0.80)
    lab, _ = ndimage.label(low, structure=np.ones((3, 3)))
    seaside = ndimage.binary_dilation(np.isin(cls, (1, 4)), structure=np.ones((3, 3)))
    k_mouth = 0
    for comp in m_rep['components']:
        if comp['status'] != 're-profiled':
            continue
        r0, c0 = int(round((12282 - comp['z']) / 6)), int(round(comp['x'] / 6))
        # float32 levels of exactly 0.80 drop out of the mask: match by size within 3 %
        ids = [i for i in np.unique(lab[max(r0 - 60, 0):r0 + 60, max(c0 - 60, 0):c0 + 60])
               if i and abs((lab == i).sum() - comp['vertices']) <= 0.03 * comp['vertices']]
        if not ids:
            continue
        m = lab == ids[0]
        sr, sc = np.nonzero(m & seaside)
        lr, lc = np.nonzero(m)
        s = np.array([6.0 * sc.mean(), 12282.0 - 6.0 * sr.mean()])
        k = np.argmax(tm['level'][lr, lc])
        up = np.array([6.0 * lc[k], 12282.0 - 6.0 * lr[k]])
        d = (up - s) / max(np.linalg.norm(up - s), 1e-6)
        cam, look = s - 30 * d, s + 80 * d
        poses.append({'name': f'MOUTH{k_mouth}', 'cam_pos': [round(float(cam[0]), 2), 8.75, round(float(cam[1]), 2)],
                      'look_at': [round(float(look[0]), 2), 0.75, round(float(look[1]), 2)]})
        k_mouth += 1
    a.out.write_text(json.dumps({'poses': poses}, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'poses': len(poses), 'visible_change_m2_total': round(float(area.sum()), 1),
                      'shore': [q['pose'] for q in chosen], 'mouths': k_mouth}, indent=1))


if __name__ == '__main__':
    main()
