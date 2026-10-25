"""Read-only recheck of the V11/V12 handoff; writes only its own review JSON.

Run with the project's GIS Python. No terrain, PBO, game or reference is modified.
"""
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
BUILD = Path('E:/DayZ-Baltic-Build')
OUT = Path(__file__).with_name('recheck.json')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    paths = {v: BUILD / f'v30-{v}/inland/terrain_inland.npz' for v in ('v11', 'v12')}
    with np.load(paths['v11']) as az, np.load(paths['v12']) as bz:
        a, b = dict(az), dict(bz)
    ha, hb = a['heights'].astype(float), b['heights'].astype(float)
    level = b['level'].astype(float)
    changed = hb != ha
    nav = b['cls'] == 3
    # Preserve the producer's float32 boundary; float64(0.8) would include the
    # float32 representation of 0.8 as if it were above the cut.
    inland = nav & (level > float(np.float32(0.8)))
    depth = level - hb
    checks = {
        'same_fields': a.keys() == b.keys(),
        'finite_heights': bool(np.isfinite(ha).all() and np.isfinite(hb).all()),
        'all_other_arrays_identical': all(np.array_equal(a[k], b[k], equal_nan=True)
                                          for k in a if k != 'heights'),
        'no_changes_outside_navigable': not bool((changed & ~nav).any()),
        'never_lowered': not bool((hb < ha).any()),
        'nonempty_change': bool(changed.any()),
        'changed_vertices_keep_1m_nominal': bool((depth[changed] >= 1.0 - 1e-6).all()),
    }
    shallow = inland & (depth < 1.0 - 1e-6)
    receipt_path = BUILD / 'v30-v12/deploy-receipt.json'
    deployed = []
    for entry in json.loads(receipt_path.read_text(encoding='utf8')):
        path = Path(entry['deployed_to'])
        actual = sha(path)
        deployed.append({'path': str(path), 'sha256': actual,
                         'matches_receipt': actual.lower() == entry['sha256'].lower(),
                         'bytes_match': path.stat().st_size == entry['bytes']})
    checks['deployed_hashes_and_sizes_match'] = all(x['matches_receipt'] and x['bytes_match']
                                                  for x in deployed) and len(deployed) == 2
    reports = {}
    for v in ('v11', 'v12'):
        directory = BUILD / f'v30-{v}'
        gate = json.loads((directory / f'verify-{v}.json').read_text(encoding='utf8'))
        roads = json.loads((directory / f'roads-{v}.json').read_text(encoding='utf8'))
        reports[v] = {'recorded_terrain_status': gate['status'],
                      'recorded_depth_fail': gate['water_depth']['fail'],
                      'recorded_piece_fail': gate['pieces']['fail'],
                      'recorded_shore_faces_over_35': gate['slopes']['shore_triangles_over_35'],
                      'recorded_roads_status': roads['status'],
                      'recorded_roads_samples': roads['samples']}
        checks[f'{v}_terrain_hash_matches_recorded_gate'] = sha(paths[v]) == gate['terrain_sha256']
    result = {
        'reviewed_head': '4382029394f27f7e256fe410eee71285134b449b',
        'status': 'PASS_DELTA_AND_DEPLOY_ONLY' if all(checks.values()) else 'FAIL',
        'checks': checks,
        'changed_vertices': int(changed.sum()),
        'max_raise_m': float((hb - ha).max()),
        'changed_depth_min_median_max': np.percentile(depth[changed], [0, 50, 100]).tolist(),
        'all_inland_navigable_vertices': int(inland.sum()),
        'inland_navigable_vertices_below_1m': int(shallow.sum()),
        'below_1m_vertices_changed_in_v12': int((shallow & changed).sum()),
        'inland_navigable_bed_under_0p85': int((inland & (hb < 0.85)).sum()),
        'deployed': deployed,
        'recorded_reports_not_rerun': reports,
        'source_sha256': {str(p): sha(p) for p in [*paths.values(), receipt_path, Path(__file__)]},
        'limits': ['No new in-game run; no rendering or navigation acceptance.',
                   'All navigable-class vertices include banks and excluded Narva; shallow vertices do not by themselves prove a blocked fairway.',
                   'The whole-network minimum depth is not proved by the minimum on changed vertices.',
                   'Recorded gate counts are not proof of identical failing sample identities.'],
    }
    data = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    json.loads(data)
    OUT.write_text(data, encoding='utf8', newline='\n')
    assert OUT.read_text(encoding='utf8') == data
    print(data)
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == '__main__':
    main()
