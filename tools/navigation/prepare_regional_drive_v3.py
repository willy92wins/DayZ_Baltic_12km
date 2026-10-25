"""Freeze the six existing sedan journeys on V29 before running the engine.

Reuse the exercised V2 controller and terminal braking. Only the case count,
log filename, coast target speed and terrain sample heights differ. Existing
acceptance thresholds and route XY stay exact; no new Enforce API is added.
"""
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys
import numpy as np
import rasterio
from waterway_common import sample

ROOT = Path(__file__).resolve().parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    previous = ROOT/'evidence/foundation-followup-2026-10-01/regional-drive-v1/reference.json'
    terminal = ROOT/'evidence/foundation-followup-2026-10-01/regional-drive-v2/reference.json'
    source = ROOT/'missions/BalticRegionalDriveV2.BalticTrial/init.c'
    asc = ROOT/'tests/regional_road_network_v29/baltic_road_network_v29.asc'
    assert sha(previous) == 'da2ee73678e31ec46c87faaf4e52e5320c4f0f65265e4ff5b9a15db7ccefccad'
    assert sha(terminal) == 'f943ddc3dbbe50ab28efa26d85c60b14bc8b23908e3b1647949af49eb5cb2b45'
    assert sha(source) == 'a2a3b3c6a6a70465f5a89094493cfee95f180d981a01035342796f6289ea0de9'
    assert sha(asc) == 'ed6cdaa5a1b9100a6f74041e9338f1c21f100a6686f596c73f79f33c4b8662c6'
    ref = json.loads(previous.read_text(encoding='utf-8'))
    assert ref['criteria'] == json.loads(terminal.read_text())['criteria']
    ev = ROOT/'evidence/foundation-followup-2026-10-01/regional-drive-v3'
    mission = ROOT/'missions/BalticRegionalDriveV3.BalticTrial'
    assert not ev.exists() and not mission.exists()
    with rasterio.open(asc) as ds:
        h = ds.read(1)
    cases = copy.deepcopy(ref['cases'])
    geometry = []
    changed = 0
    for original, case in zip(ref['cases'], cases):
        points = np.array(original['route_xyz'])
        xy = points[:, [0, 2]]
        y = sample(h, xy[:, 0]+200000, xy[:, 1]).astype('float32').astype(float)
        changed += int(np.count_nonzero(y != points[:, 1]))
        points[:, 1] = y
        case['route_xyz'] = points.tolist()
        assert np.array_equal(points[:, [0, 2]], np.array(original['route_xyz'])[:, [0, 2]])
        delta = np.gradient(xy, axis=0)
        normals = np.column_stack([-delta[:, 1], delta[:, 0]]) / np.linalg.norm(delta, axis=1)[:, None]
        across = np.array([sample(h, xy[:, 0]+normals[:, 0]*v+200000, xy[:, 1]+normals[:, 1]*v) for v in (-4., 0., 4.)])
        grade = float(np.max(abs(np.diff(y)/np.linalg.norm(np.diff(xy, axis=0), axis=1))))
        cross = float(np.ptp(across, axis=0).max())
        geometry.append(dict(case=case['case'], maximum_grade=grade, maximum_cross_height_m=cross,
                             full_width_gate_pass=grade <= .065 and cross <= .03))
    code = source.read_text(encoding='utf-8')
    assert code.count('m_Case>=2') == 1 and code.count('float desiredSpeed=9.722222;') == 1
    code = code.replace('baltic_regional_drive_v2', 'baltic_regional_drive_v3').replace('m_Case>=2', 'm_Case>=6')
    code = code.replace('float desiredSpeed=9.722222;', 'float desiredSpeed=9.722222;\n                if (m_Case<2) desiredSpeed=6.944444;')
    ev.mkdir(); mission.mkdir()
    (mission/'init.c').write_text(code, encoding='utf-8')
    (mission/'routes.csv').write_text(''.join(f"{c['case']};{i};{p[0]:.9g};{p[1]:.9g};{p[2]:.9g}\n" for c in cases for i, p in enumerate(c['route_xyz'])), encoding='ascii')
    lint = subprocess.run([sys.executable, '-X', 'utf8',
                           'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',
                           str(mission)], capture_output=True, text=True)
    (ev/'lint.json').write_text(lint.stdout, encoding='utf-8')
    check = json.loads(lint.stdout)
    assert not check['errors'] and check['info']['files_scanned'] == 1
    inputs = [previous, terminal, source, asc, ROOT/'tests/regional_road_network_v29/independent-consumer.json', ROOT/'tools/navigation/BalticDriveInput.c']
    ref = {key: ref[key] for key in ('criteria', 'bridge', 'input_pbo_sha256', 'placement_api')}
    ref.update(status='FROZEN_ROAD_V29_SIX_JOURNEYS_NOT_RUN', terrain=str(asc), terrain_sha256=sha(asc),
               cases=cases, route_geometry=geometry, inputs={str(p): sha(p) for p in inputs},
               mission={str(p): sha(p) for p in mission.iterdir()}, log_name='baltic_regional_drive_v3.log',
               reference_xy_unchanged=True, changed_height_samples=changed,
               scope='Six previous journeys, coast/hills/south, 25/35kmh target, empty vanilla sedan.',
               limits=['Frozen route XY and original physical criteria; new terrain and V2 terminal controller.',
                       'Geometry does not prove contact, health, driving or stopping; no runtime result yet.',
                       'No physical road pieces, human handling, whole network or multiplayer load accepted.',
                       'Require deployed world/WRP/NM identity before this mission is run.'])
    (ev/'reference.json').write_text(json.dumps(ref, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status=ref['status'], cases=len(cases), changed_height_samples=changed,
                          geometry=geometry, reference_sha256=sha(ev/'reference.json'))))


if __name__ == '__main__':
    main()
