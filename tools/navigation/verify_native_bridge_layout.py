"""Check TB bridge poses against the frozen design; never changes the WRP.

The position threshold is the existing runtime-candidate gate (0.5 mm).
Reopening, compilation and consumer tests are independent evidence.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/playtest'))
from verify_texture_grid_change import read


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wrp', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Fresh evidence output required')
    design_path = ROOT / 'tests/narva_navigation_v3/design.json'
    design_bytes = design_path.read_bytes()
    if hashlib.sha256(design_bytes).hexdigest() != '686678c58e06525383252061f2fa76ee99eada0b51bcb6f96322ad51ccea5e30':
        raise ValueError('Frozen bridge design changed')
    world = read(args.wrp)
    design = json.loads(design_bytes)
    targets = sorted(design['bridge_objects'], key=lambda o: o['x'])
    objects = sorted(world['objects'], key=lambda o: struct.unpack('<12f', bytes.fromhex(o['matrix']))[9])
    checks = {
        'exactly_three_objects': len(objects) == 3,
        'only_bridge_metal_25': all(o['name'].replace('\\', '/').lower() == targets[0]['model'] for o in objects),
        'unique_object_ids': len({o['id'] for o in objects}) == len(objects),
    }
    poses = []
    for obj, target in zip(objects, targets):
        matrix = np.array(struct.unpack('<12f', bytes.fromhex(obj['matrix'])))
        angle = np.deg2rad(target['yaw_deg'])
        rotation = np.array([np.cos(angle), 0, -np.sin(angle), 0, 1, 0, np.sin(angle), 0, np.cos(angle)])
        expected = np.array([target['x'], target['engine_origin_y_candidate'], target['z']])
        error = matrix[9:] - expected
        poses.append({'id': obj['id'], 'model': obj['name'], 'matrix': matrix.tolist(),
                      'position_error_xyz_m': error.tolist(),
                      'position_within_0_5mm': bool(np.isfinite(matrix).all() and np.max(abs(error)) <= .0005),
                      'rotation_scale_error': float(np.max(abs(matrix[:9] - rotation))),
                      'rotation_scale_match': bool(np.isfinite(matrix).all() and np.max(abs(matrix[:9] - rotation)) <= 1e-6),
                      'predicted_deck_y': float(matrix[10] + 8.05488395690918)})
    checks['poses_match_frozen_design'] = len(poses) == 3 and all(p['position_within_0_5mm'] and p['rotation_scale_match'] for p in poses)
    report = {'status': 'PASS_NATIVE_BRIDGE_LAYOUT' if all(checks.values()) else 'FAIL',
              'checks': checks, 'wrp_sha256': hashlib.sha256(world['bytes']).hexdigest(),
              'poses': poses, 'limits': ['Native records only; save/reopen, compiled geometry and engine tests are separate.']}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
