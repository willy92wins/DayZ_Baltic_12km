"""Boat consumer over the R1 reach of the vanilla channel pilot (plans/v30-vanilla-channel-water-pilot.md, step 5).

Same mission as missions/BalticV30LugaBoatV1.BalticTrial (empty Boat_01_Orange driven by the
@BalticBoatInputProbe addon, outward and reverse) with its own log and two cases; waypoints every 4 m on
the R1 design axis inside the reach, water level = the pilot surface. Writes the mission, the terrain ASC
the verifier samples (tools/navigation/verify_regional_boat_consumer.py) and a reference with the
historical criteria. Never launches. Usage:
  prepare_vanilla_channel_boat.py --fit <fit dir> --mission <dir> --reference <json> --asc <out.asc>
"""
from pathlib import Path
import argparse
import hashlib
import json
import math

import numpy as np
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'missions' / 'BalticV30LugaBoatV1.BalticTrial' / 'init.c'
LOG = 'baltic_vanilla_channel_boat_v1.log'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--fit', type=Path, required=True)
    ap.add_argument('--mission', type=Path, required=True)
    ap.add_argument('--reference', type=Path, required=True)
    ap.add_argument('--asc', type=Path, required=True)
    a = ap.parse_args()
    for p in (a.mission, a.reference, a.asc):
        assert not p.exists(), f'Preserve prior evidence: {p}'
    ax = json.loads((a.fit / 'axes.json').read_text(encoding='utf-8'))['R1']
    s, x, z, surf = (np.array(ax[k]) for k in ('s', 'x', 'z', 'surface'))
    keep = (s >= ax['s_lo'] + 10) & (s <= ax['s_hi'] - 10)
    line = LineString(np.column_stack([x[keep], z[keep]]))
    d = np.linspace(0, line.length, math.ceil(line.length / 4) + 1)
    pts = np.array([line.interpolate(v).coords[0] for v in d])
    lev = np.interp(np.array([LineString(np.column_stack([x, z])).project(__import__('shapely').geometry.Point(p)) for p in pts]), s, surf)
    text = SOURCE.read_text(encoding='utf-8')
    for old, new in (('baltic_v30_luga_boat_v1.log', LOG), ('if (m_Case >= 8)', 'if (m_Case >= 2)')):
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    rows, cases = [], []
    for case, reverse in ((0, False), (1, True)):
        order = np.arange(len(pts))[::-1] if reverse else np.arange(len(pts))
        for seq, j in enumerate(order):
            rows.append(f'{case};{seq};{pts[j, 0]:.9g};{lev[j]:.9g};{pts[j, 1]:.9g}')
        cases.append({'case': case, 'river': 'Narva_28 (R1)', 'reverse': reverse, 'waypoints_xz': pts[order].tolist(),
                      'water_levels': lev[order].tolist(), 'length_m': float(line.length)})
    terrain = np.load(a.fit / 'terrain_pilot.npz')['heights']
    a.asc.parent.mkdir(parents=True, exist_ok=True)
    with a.asc.open('x', encoding='ascii', newline='\n') as stream:
        stream.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(stream, terrain, fmt='%.9g')
    a.mission.mkdir(parents=True)
    (a.mission / 'init.c').write_text(text, encoding='utf-8', newline='\n')
    (a.mission / 'routes.csv').write_text('\n'.join(rows) + '\n', encoding='ascii')
    ref = {'status': 'FROZEN_BEFORE_ENGINE', 'log_version': 2, 'log': LOG, 'terrain': str(a.asc), 'terrain_sha256': sha(a.asc),
           'mission': {str(p): sha(p) for p in sorted(a.mission.iterdir())}, 'source_mission_sha256': sha(SOURCE),
           'fit_axes_sha256': sha(a.fit / 'axes.json'), 'cases': cases,
           'criteria': {'max_sample_dt_s': 0.8, 'max_step_m': 3, 'max_health_loss': 1, 'max_axis_distance_m': 7,
                        'max_endpoint_distance_m': 6, 'max_waypoint_distance_m': 7, 'max_ground_error_m': 0.002,
                        'min_powered_motion_s': 5},
           'limits': ['Empty boat on one pilot reach, both directions.', 'Requires @BalticBoatInputProbe in the run.',
                      'No crew, turn or whole-river acceptance.']}
    a.reference.write_text(json.dumps(ref, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in ref.items() if k != 'cases'} | {'waypoints': len(pts), 'length_m': round(line.length, 1)}, indent=1))


if __name__ == '__main__':
    main()
