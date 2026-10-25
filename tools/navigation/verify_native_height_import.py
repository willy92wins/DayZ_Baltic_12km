"""Compare the literal TB WRP with the frozen Narva ASC and previous native world.

This intermediate gate concerns terrain persistence, before replacing bridge
objects. It must not be reported as acceptance of the final object layout.
Native reader: tools/playtest/verify_texture_grid_change.py:read.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np
import rasterio

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
    asc = ROOT / 'tests/narva_navigation_v3/narva_navigation_v1.asc'
    base = ROOT / 'tb/regional_clearance_v1/baltic_regional_objects_restored_v1.wrp'
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    if sha(asc) != 'c1f23f24808cb6f1ff858f47a378f6bdf8211387f63c110a12ff72fd3bd82d3c':
        raise ValueError('Frozen source ASC changed')
    if sha(base) != '313600cbbe77f161368133acfd9c7347a683dacadc695bc2149db6388a0552ef':
        raise ValueError('Frozen baseline changed')
    old, new = read(base), read(args.wrp)
    with rasterio.open(asc) as dataset:
        expected = dataset.read(1)
    actual = np.frombuffer(new['heights'], dtype='<f4').reshape(2048, 2048)[::-1]
    before = np.frombuffer(old['heights'], dtype='<f4').reshape(2048, 2048)[::-1]
    delta = np.abs(actual.astype('float64') - expected.astype('float64'))
    delta_path = ROOT / 'tests/narva_navigation_v3/delta.npz'
    if sha(delta_path) != '2bfe335babc7bfd01c89d9b381117ef4f5fc463a0e565182dc915547077ebe22':
        raise ValueError('Frozen edit ledger changed')
    with np.load(delta_path) as edits:
        intended = np.zeros(before.shape, dtype=bool)
        intended[edits['row'], edits['col']] = True
        if not np.array_equal(before[intended], edits['before']):
            raise ValueError('Edit ledger is not based on the canonical native world')
        target_edits = edits['after'].copy()
    after_height = 24 + actual.size * 4
    # Original objects are reported for diagnosis; their replacement is a
    # separate later gate, so no pose tolerance hides an incomplete bridge.
    key = lambda o: (o['name'], o['id'], o['matrix'])
    checks = {
        'all_1242_edits_equal_frozen_delta': bool(np.array_equal(actual[intended], target_edits)),
        'finite_heights': bool(np.isfinite(actual).all()),
        'untouched_vertices_equal_baseline': bool(np.array_equal(actual[~intended], before[~intended])),
        'native_header_unchanged': old['bytes'][:24] == new['bytes'][:24],
        'texture_grid_materials_unchanged': old['bytes'][after_height:old['objects_start']] == new['bytes'][after_height:new['objects_start']],
    }
    report = {
        'status': 'PASS_NATIVE_HEIGHT_IMPORT' if all(checks.values()) else 'FAIL',
        'checks': checks,
        'wrp': str(args.wrp), 'wrp_sha256': sha(args.wrp),
        'asc_sha256': sha(asc), 'baseline_wrp_sha256': sha(base),
        'delta_sha256': sha(delta_path),
        'samples': int(actual.size), 'intended_changed_vertices': int(intended.sum()),
        'differing_from_ASC': int(np.count_nonzero(delta)),
        'max_height_error_m': float(delta.max()),
        'strict_ASC_equality': bool(np.array_equal(actual, expected)),
        'ASCII_difference_note': 'Four eastern edge float32 values differ by 2.98e-8m from ASC; those native values are unchanged from the canonical baseline. Acceptance uses the frozen 1242-edit ledger and exact preservation of every other native vertex, without a relaxed tolerance.',
        'original_object_records_exact': sorted(map(key, old['objects'])) == sorted(map(key, new['objects'])),
        'objects': [dict(name=o['name'], id=o['id'], matrix=struct.unpack('<12f', bytes.fromhex(o['matrix']))) for o in new['objects']],
        'limits': ['Intermediate height gate only; object replacement and save/reopen proof are separate.',
                   'No compiled world, render, navmesh or regional boat acceptance implied.'],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
