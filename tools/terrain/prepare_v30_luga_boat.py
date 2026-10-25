"""Freeze physical boat sectors spanning the existing 23-vertex Luga fix."""
from pathlib import Path
import copy
import hashlib
import json
import sys

import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import substring

from v30_common import cell_planes, tri_sample

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'evidence/v30-luga-boat-2026-10-02'
TERRAIN = Path('E:/DayZ-Baltic-Build/v30-delta-candidate')
MISSION = ROOT / 'missions/BalticV30LugaBoatV1.BalticTrial'
DEPLOYED = Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions') / MISSION.name
WINDOWS = [(24, 230), (5850, 6245), (6280, 6580), (6870, 7020)]


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    assert not OUT.exists() and not MISSION.exists() and not DEPLOYED.exists()
    asc = TERRAIN / 'baltic_terrain_v30.asc'
    npz = TERRAIN / 'terrain_v30.npz'
    assert sha(asc) == '64d4f160b963c28b519a50c9c29564dbe9727facabf7b52d83970eef5b8e6eb4'
    assert sha(npz) == 'a84dfff053523b94717b2068a96845193d01a21f0ea7ff01e0f9111280630081'
    source = ROOT / 'missions/BalticRegionalBoatV3.BalticTrial/init.c'
    assert sha(source) == '66e3515497ece9ace70b782c90acf2bddae378ae854c112f2f473abd6604e1e6'
    parent = ROOT / 'evidence/overnight-2026-10-01/regional-boat-v3/reference.json'
    assert sha(parent) == 'f4d8e84686947a437c88d2328cce9d0c9cac19b9cd5900a22546695e79c93bfb'
    samples = ROOT / 'tests/water_v3/navigable_samples.npz'
    assert sha(samples) == '0c0d65c8373b248e34008bc25f8cf0b12c7374ea5ab296cb4f074be84340d9fd'
    changes = ROOT / 'evidence/v30-offline-followup-2026-10-02/bounded-bed-fix/candidate.json'
    axis = LineString(np.load(samples)['Luga_0'][:, 1:3])
    changed = json.loads(changes.read_text())['changes']
    projection = [axis.project(Point(c['x'], c['z'])) for c in changed]
    assert len(projection) == 23 and all(any(a <= s <= b for a, b in WINDOWS) for s in projection)
    data = np.load(npz)
    h = data['heights'].astype(float)
    planes = cell_planes(data['cls'], data['level'].astype(float))
    cases, rows = [], []
    for sector, (a, b) in enumerate(WINDOWS):
        line = substring(axis, a, b)
        assert line.is_simple and abs(line.length - (b-a)) < 1e-6

        def query(points):
            row = np.floor((12282-points[:, 1])/6).astype(int)
            col = np.floor(points[:, 0]/6).astype(int)
            water = planes[row, col]
            assert np.isfinite(water).all(), 'Uncovered pond cell'
            ground = tri_sample(h, points[:, 0], points[:, 1])
            assert np.min(water-ground) >= 2.99, 'Centerline too shallow'
            return water, ground

        points = np.array([line.interpolate(s).coords[0] for s in
                           np.linspace(0, line.length, int(np.ceil(line.length/4))+1)], dtype=np.float32).astype(float)
        dense = np.array([line.interpolate(s).coords[0] for s in
                          np.linspace(0, line.length, int(np.ceil(line.length/.5))+1)], dtype=np.float32).astype(float)
        water, _ = query(points)
        dense_water, dense_ground = query(dense)
        for reverse in (False, True):
            p = points[::-1] if reverse else points
            w = water[::-1] if reverse else water
            ident = len(cases)
            cases.append(dict(case=ident, river='Luga', sector=sector, reverse=reverse,
                              chainage_window_m=[a, b], axis_length_m=line.length,
                              waypoints_xz=p.tolist(), water_levels=w.tolist(),
                              minimum_dense_nominal_depth_m=float(np.min(dense_water-dense_ground))))
            rows.extend(f'{ident};{i};{x:.9g};{lv:.9g};{z:.9g}' for i, ((x, z), lv) in enumerate(zip(p, w)))
    code = source.read_text()
    assert code.count('baltic_regional_boat_v3.log') == 1 and code.count('m_Case >= 8') == 1
    code = code.replace('baltic_regional_boat_v3.log', 'baltic_v30_luga_boat_v1.log')
    expected = {
        Path('P:/Mods/@DayZ_Baltic_DeltaV30_Nav/Addons/narva_trial.pbo'): '916948ec6590e590edb91218082bf2b0bba8a6f9276c3977b003512f9cc6f525',
        Path('P:/Mods/@DayZ_Baltic_DeltaV30_Nav/Addons/baltic_water_v30.pbo'): 'e9b52b8c4fc07df8bc4854dcd9e144e16875af8006221f16efaa6ab95de56681',
        Path('P:/Mods/@BalticBoatInputProbe/Addons/baltic_boat_input.pbo'): 'c5414ffe385eae5b85e1fe6dfef671db568d50a8eb11c74a3f4346f7c6417b2e'}
    for p, digest in expected.items():
        assert sha(p) == digest, str(p)
    for folder in (MISSION, DEPLOYED):
        folder.mkdir()
        (folder/'init.c').write_bytes(code.encode())
        (folder/'routes.csv').write_bytes(('\n'.join(rows)+'\n').encode('ascii'))
    for name in ('init.c', 'routes.csv'):
        assert (MISSION/name).read_bytes() == (DEPLOYED/name).read_bytes()
    reference = dict(status='FROZEN_BEFORE_ENGINE', terrain=str(asc), terrain_sha256=sha(asc), log_version=2,
                     inputs={str(p): sha(p) for p in (samples, changes, source, parent, npz)},
                     deployment={str(p): digest for p, digest in expected.items()},
                     mission={str(p): sha(p) for p in MISSION.iterdir()}, deployed_mission=str(DEPLOYED),
                     cases=cases, criteria=copy.deepcopy(json.loads(parent.read_text())['criteria']),
                     corrected_vertex_chainages_m=projection,
                     limits=['Eight trips in four Luga sectors, empty vanilla boat; not the whole river.',
                             'Centerline motion does not measure the full 24m cross-section.',
                             'No crew, medium-vessel, full turn, AI locomotion or multiplayer acceptance.'])
    OUT.mkdir()
    (OUT/'reference.json').write_text(json.dumps(reference, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status='PREPARED_NOT_RUN', cases=len(cases), total_distance_m=sum(c['axis_length_m'] for c in cases),
                          minimum_centerline_depth_m=min(c['minimum_dense_nominal_depth_m'] for c in cases),
                          reference_sha256=sha(OUT/'reference.json'))), flush=True)


if __name__ == '__main__':
    main()
