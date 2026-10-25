"""Freeze V12 routes and hashes before the empty-boat engine test. Never launches."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
from shapely.geometry import shape
from shapely.ops import substring

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/terrain'))
from v30_common import tri_sample, cell_planes

OUT = Path(__file__).resolve().parent
BUILD = Path('E:/DayZ-Baltic-Build/v30-luga-navigation-20261007')
NPZ = Path('E:/DayZ-Baltic-Build/v30-v12/inland/terrain_inland.npz')
AXES = ROOT.parents[2] / 'evidence/regional-foundation-v1/fairways-main-game.json'
SOURCE = ROOT / 'missions/BalticV30LugaBoatV1.BalticTrial/init.c'
MISSION = ROOT / 'missions/BalticV12NavigationV1.BalticTrial'
DEPLOYED = Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions') / MISSION.name
LOG = 'baltic_v12_navigation_v1.log'
# Fixed geographical sectors, selected before engine outcomes. Same route in both directions.
SECTORS = [('Narva spawn west', 12, 15, 145), ('Luga upper', 34, 5000, 5140), ('Luga low water', 34, 12800, 12940)]


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    ref_path = OUT / 'boat-reference.json'
    asc = BUILD / 'v12-reference.asc'
    for path in (ref_path, asc, MISSION, DEPLOYED):
        assert not path.exists(), f'Preserve prior evidence: {path}'
    expected = {
        NPZ: '8b3a8c5541403abaf852e14fb4c0651175e6dcaa541f6f8a151f1db04ac7a8a6',
        Path('P:/Mods/@DayZ_Baltic_V12Candidate/Addons/narva_trial.pbo'): 'f0813174748ef648ccfcfdee82c375a2becf7e1691b6a310c6ef07dcf720cccf',
        Path('P:/Mods/@DayZ_Baltic_V12Candidate/Addons/baltic_water_v30.pbo'): '07c5295f112746d621e96324467b1d54fccc415a785c227feb245f59adff503f',
        Path('P:/Mods/@BalticBoatInputProbe/Addons/baltic_boat_input.pbo'): 'c5414ffe385eae5b85e1fe6dfef671db568d50a8eb11c74a3f4346f7c6417b2e',
    }
    for path, digest in expected.items():
        assert sha(path) == digest, str(path)
    data = np.load(NPZ)
    h = data['heights']
    planes = cell_planes(data['cls'], data['level'], sea_cut=.51)
    features = json.loads(AXES.read_text())['features']
    cases, rows = [], []
    for label, idx, lo, hi in SECTORS:
        line = substring(shape(features[idx]['geometry']), lo, hi)
        assert line.is_simple and abs(line.length - (hi-lo)) < 1e-6

        def points(step):
            return np.array([line.interpolate(d).coords[0] for d in
                             np.linspace(0, line.length, int(np.ceil(line.length/step))+1)], dtype=np.float32).astype(float)

        def query(p):
            r = np.floor((12282-p[:, 1])/6).astype(int)
            c = np.floor(p[:, 0]/6).astype(int)
            water = planes[r, c]
            assert np.isfinite(water).all(), 'Missing water cell'
            ground = tri_sample(h, p[:, 0], p[:, 1])
            assert np.min(water-ground) >= .999, 'Shallow reference route'
            return water, ground

        pts, dense = points(4), points(.5)
        water, _ = query(pts)
        dw, dh = query(dense)
        for reverse in (False, True):
            p = pts[::-1] if reverse else pts
            w = water[::-1] if reverse else water
            ident = len(cases)
            cases.append(dict(case=ident, river=label, feature_index=idx, reverse=reverse,
                              chainage_window_m=[lo, hi], length_m=float(line.length),
                              waypoints_xz=p.tolist(), water_levels=w.tolist(),
                              dense_nominal_depth_min_m=float(np.min(dw-dh)),
                              water_range_m=[float(dw.min()), float(dw.max())]))
            rows.extend(f'{ident};{i};{x:.9g};{lv:.9g};{z:.9g}' for i, ((x, z), lv) in enumerate(zip(p, w)))
    code = SOURCE.read_text(encoding='utf-8')
    for old, new in [('baltic_v30_luga_boat_v1.log', LOG), ('m_Case >= 8', 'm_Case >= 6')]:
        assert code.count(old) == 1
        code = code.replace(old, new)
    for folder in (MISSION, DEPLOYED):
        folder.mkdir()
        (folder/'init.c').write_text(code, encoding='utf-8', newline='\n')
        (folder/'routes.csv').write_text('\n'.join(rows)+'\n', encoding='ascii', newline='\n')
    for name in ('init.c', 'routes.csv'):
        assert (MISSION/name).read_bytes() == (DEPLOYED/name).read_bytes()
    with asc.open('x', encoding='ascii', newline='\n') as stream:
        stream.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(stream, h, fmt='%.9g')
    ref = dict(status='FROZEN_BEFORE_ENGINE', log_version=2, log=LOG,
               terrain=str(asc), terrain_sha256=sha(asc),
               inputs={str(p): sha(p) for p in [NPZ, AXES, SOURCE, Path(__file__)]},
               deployment={str(p): digest for p, digest in expected.items() if p.suffix == '.pbo'},
               mission={str(p): sha(p) for p in MISSION.iterdir()}, deployed_mission=str(DEPLOYED),
               cases=cases,
               criteria=dict(max_sample_dt_s=.8, max_step_m=3, max_health_loss=1, max_axis_distance_m=7,
                             max_endpoint_distance_m=6, max_waypoint_distance_m=7, max_ground_error_m=.002,
                             min_powered_motion_s=5),
               limits=['Empty vanilla boat in three fixed V12 sectors, both directions.',
                       'Centerline motion does not accept the full river width, crew, turns or whole world.',
                       'Nominal offline water cells do not prove runtime water coverage.',
                       'No terrain, water addon or controller changes during this test.'])
    ref_path.write_text(json.dumps(ref, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status='PREPARED_NOT_RUN', cases=len(cases),
                          total_distance_m=sum(c['length_m'] for c in cases),
                          min_nominal_depth_m=min(c['dense_nominal_depth_min_m'] for c in cases),
                          reference_sha256=sha(ref_path)), indent=2))


if __name__ == '__main__':
    main()
