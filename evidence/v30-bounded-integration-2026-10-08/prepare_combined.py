"""Compose two hash-frozen, disjoint candidates; keep V12 metadata unchanged."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/terrain'))
from v30_common import cell_planes

BUILD = Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008')
INPUTS = {
    'base': ('E:/DayZ-Baltic-Build/v30-v12/inland/terrain_inland.npz', '8b3a8c5541403abaf852e14fb4c0651175e6dcaa541f6f8a151f1db04ac7a8a6'),
    'dry': ('E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007/dry-18-corrected/terrain_dry.npz', '164ad4ffbe4177c7615d18e95d12920d4d332612e596377963a54e0281fc608d'),
    'shore': (str(BUILD/'luga-margin/terrain_inland.npz'), '68560a0d9848a425c2671f22238eadea39ffcb203d050cc3e46ddee79d5f5b05'),
}


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def cell_any(mask):
    return mask[:-1, :-1] | mask[:-1, 1:] | mask[1:, :-1] | mask[1:, 1:]


def main():
    out = BUILD/'combined'
    assert not out.exists(), 'Fresh output required'
    data = {}
    for key, (path, expected) in INPUTS.items():
        assert sha(path) == expected, key
        with np.load(path) as f:
            data[key] = dict(f)
    base, dry, shore = [data[k] for k in ('base', 'dry', 'shore')]
    for d in [dry, shore]:
        assert d.keys() == base.keys()
        assert all(np.array_equal(v, d[k], equal_nan=True) for k, v in base.items() if k != 'heights')
    h, dh, sh = [d['heights'] for d in [base, dry, shore]]
    dm, sm = dh != h, sh != h
    assert not np.any(dm & sm), 'Overlapping edits'
    assert not np.any(cell_any(dm) & cell_any(sm)), 'Interacting native cells'
    result = h.copy()
    result[dm] = dh[dm]
    result[sm] = sh[sm]
    wet = (base['cls'] > 0) | base['water']
    water_band = distance_transform_edt(~wet, sampling=6.) <= 36.
    assert np.array_equal(result[water_band], sh[water_band])
    # Every existing failed pond corner must retain exactly the same identity.
    planes = cell_planes(base['cls'], base['level'], sea_cut=.51)
    corner_failures = []
    for rr, cc in [(slice(None, -1), slice(None, -1)), (slice(None, -1), slice(1, None)),
                   (slice(1, None), slice(None, -1)), (slice(1, None), slice(1, None))]:
        water = base['cls'][rr, cc] > 0
        def bad(z):
            return np.isfinite(planes) & np.where(water, z[rr, cc] > planes-.02, z[rr, cc] < planes)
        a, b = bad(h), bad(result)
        assert np.array_equal(a, b), 'Pond failure identities changed'
        corner_failures.append(int(a.sum()))
    depth_bad = (base['cls'] > 0) & (base['level'].astype(float)-h.astype(float) < .1)
    new_depth_bad = (base['cls'] > 0) & (base['level'].astype(float)-result.astype(float) < .1)
    assert np.array_equal(depth_bad, new_depth_bad), 'Depth failure identities changed'
    # Freeze every cell within 12 m of all six tested boat paths, including
    # the 7 m accepted axis error and triangle support beyond sampled positions.
    reference = json.loads((ROOT/'evidence/v30-luga-navigation-2026-10-07/boat-reference.json').read_text())
    c, r = np.meshgrid(np.arange(2047)+.5, np.arange(2047)+.5)
    x, z = c*6., 12282-r*6.
    changed_cells = cell_any(result != h)
    route_checks = []
    for route in reference['cases']:
        p = np.array(route['waypoints_xz'])
        box = (x >= p[:, 0].min()-18) & (x <= p[:, 0].max()+18) & (z >= p[:, 1].min()-18) & (z <= p[:, 1].max()+18)
        rr, cc = np.nonzero(box)
        q = np.column_stack([x[box], z[box]])
        nearest = np.full(len(q), np.inf)
        for a, b in zip(p[:-1], p[1:]):
            d = b-a
            t = np.clip((q-a)@d/(d@d), 0, 1)
            nearest = np.minimum(nearest, np.linalg.norm(q-(a+t[:, None]*d), axis=1))
        mask = nearest <= 12+6/np.sqrt(2)
        count = int(changed_cells[rr[mask], cc[mask]].sum())
        route_checks.append(dict(case=route['case'], cells=int(mask.sum()), changed_cells=count))
    out.mkdir()
    path = out/'terrain_inland.npz'
    np.savez_compressed(path, **{**base, 'heights': result})
    report = dict(status='PASS_COMPOSITION_ONLY', inputs=INPUTS, output_sha256=sha(path),
                  dry_vertices=int(dm.sum()), shore_vertices=int(sm.sum()),
                  shared_vertices=0, shared_native_cells=0, water_band_m=36,
                  pond_corner_failure_identities_exact=corner_failures,
                  depth_failure_identities_exact=int(depth_bad.sum()), boat_route_cells=route_checks,
                  boat_runtime_repeat_required=any(c['changed_cells'] for c in route_checks),
                  limitation='Experimental composition; general gates, packaging, runtime and independent review remain separate.')
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
