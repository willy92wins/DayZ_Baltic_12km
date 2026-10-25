"""Review the bounded wave-margin edit against design and frozen consumers."""
from pathlib import Path
import argparse
import json

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation
from shapely.geometry import shape

from audit_fairway_triangles_v30 import records, save, sha
from review_pond_recovery_v30 import face_angles
from v30_common import cell_planes, grid_xz, raster_vertices, tri_sample, vertex_plane_bounds

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('E:/DayZ-Baltic-Build/v30-watercourse-continuity/terrain_v30.npz')
SOURCE_SHA = '40d8cfd9874e9260464f9e3c38c07d81a15c8aed374083a52c98f042c0161c2e'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    assert not args.out.exists() and sha(SOURCE) == SOURCE_SHA
    old, new = np.load(SOURCE), np.load(args.candidate)
    a, b = old['heights'].astype(float), new['heights'].astype(float)
    changed = a != b
    x, z = grid_xz()
    diagnostic_path = Path('E:/DayZ-Baltic-Build/v30-water-temporal-v2/reference.json')
    diagnostic = json.loads(diagnostic_path.read_text())
    points = [p for p in diagnostic['points'] if p['role'] == 'frozen_shallow_failure']
    envelope = np.zeros_like(changed)
    for p in points:
        envelope |= np.hypot(x-p['x'], z-p['z']) < 24
    design = json.loads((ROOT/'tests/water_v3/water_v3.geojson').read_text())['features']
    narva_exception = raster_vertices([shape(design[i]['geometry']) for i in (98,376,408,409)]).astype(bool)
    fixed = old['platform'] | old['reserve'] | old['beach'] | (old['narva'] & ~narva_exception)
    fixed |= np.load(ROOT/'tests/regional_outline_v1/reference.npz')['reserve'].astype(bool)
    planes = cell_planes(old['cls'], old['level'])
    corridors = []
    for path in (ROOT/'evidence/v30-offline-followup-2026-10-02/corridors.geojson',
                 ROOT/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson'):
        for f in json.loads(path.read_text())['features']:
            if f['properties'].get('kind', 'corridor24m') != 'corridor24m':
                continue
            ids = np.unique(records(shape(f['geometry']), planes)['ids'])
            mask = np.zeros_like(changed)
            mask.ravel()[ids] = True
            fixed |= binary_dilation(mask)
            corridors.append(bool(np.array_equal(a.ravel()[ids], b.ravel()[ids])))
    worse, fresh = 0, 0
    for angle_a, angle_b in zip(face_angles(a), face_angles(b)):
        worse += int(((angle_b > 35.0001) & (angle_b > angle_a+.0001)).sum())
        fresh += int(((angle_b > 35.0001) & (angle_a <= 35.0001)).sum())
    lo, _ = vertex_plane_bounds(planes)
    parent_path = Path('E:/DayZ-Baltic-Build/v30-continuity-dedup-package/runtime-fixture/reference.json')
    parent = json.loads(parent_path.read_text())
    assert parent['terrain_sha256'] == SOURCE_SHA
    dry_checks, shallow = [], []
    for p in parent['points']:
        old_y = float(tri_sample(a, p['x'], p['z']))
        new_y = float(tri_sample(b, p['x'], p['z']))
        assert abs(old_y-p['expected_ground_m']) < 1e-6
        if p['kind'] == 'dry':
            plane = p['pond_plane_m'] if p['pond_plane_m'] is not None else 1.
            dry_checks.append(new_y >= plane + .05)
        if p['id'] in {q['id'] for q in points}:
            shallow.append(dict(id=p['id'], before_m=p['pond_plane_m']-old_y,
                                after_m=p['pond_plane_m']-new_y))
    roads_path = args.candidate.parent/'road-gates-historical.json'
    roads = json.loads(roads_path.read_text())
    checks = dict(nonempty=bool(changed.any()), finite=bool(np.isfinite(b).all()),
                  only_local_water_changed=not bool((changed & (~envelope | (old['cls'] == 0))).any()),
                  fixed_terrain_exact=not bool((changed & fixed).any()),
                  dry_vertices_exact=bool(np.array_equal(a[old['cls']==0],b[old['cls']==0])),
                  lowering_within_45cm=bool(np.all(b <= a) and (a-b).max() <= .450001),
                  altered_depth_within_120cm=bool(np.all(b[changed] >= lo[changed]-1.200001)),
                  all_23_channels_exact=len(corridors)==23 and all(corridors),
                  no_new_or_worsened_steep_faces=worse==0,
                  all_frozen_dry_samples_still_dry=len(dry_checks)==463 and all(dry_checks),
                  all_13_shallow_samples_deepened=len(shallow)==13 and all(p['after_m']>=.181-1e-6 for p in shallow),
                  historical_roads_pass=roads['status']=='PASS' and roads['samples']==76536 and roads['chains']==100,
                  road_provenance_exact=roads['terrain_sha256']==sha(args.candidate)
                    and roads['sources'].get(roads['water_spec'].split('::')[0])=='365c2a9400be80791e38c0c406152c87247e663205f1bc818604f05ea150c360')
    for key in old.files:
        if key != 'heights':
            checks['metadata_exact_'+key] = bool(np.array_equal(old[key],new[key],equal_nan=True))
    with rasterio.open(args.candidate.parent/'baltic_terrain_v30.asc') as ds:
        checks['asc_exact'] = bool(np.array_equal(ds.read(1),new['heights']))
        checks['asc_grid_exact'] = ds.shape==(2048,2048) and ds.transform.a==6 and ds.transform.e==-6 and ds.bounds.left==200000 and ds.bounds.bottom==0
    report = dict(status='PASS_LOCAL_WAVE_MARGIN_GEOMETRY' if all(checks.values()) else 'FAIL',
                  checks=checks, source_sha256=SOURCE_SHA, candidate_sha256=sha(args.candidate),
                  changed_vertices=int(changed.sum()), max_lower_m=float((a-b).max()),
                  new_steep_faces=fresh,new_or_worsened_steep_faces=worse, shallow=shallow,
                  required_nominal_depth_m=.181,
                  inputs={str(p):sha(p) for p in (SOURCE,args.candidate,parent_path,diagnostic_path,roads_path,Path(__file__))},
                  limits=['No engine, visual or updated navmesh acceptance from this offline review.',
                          'Dry samples keep frozen coordinates and classification; they are not all land pixels.'])
    save(args.out, report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('inputs','shallow')},indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
