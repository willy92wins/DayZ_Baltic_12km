"""Validate changed terrain against its candidate while preserving objects/materials."""
import argparse
import json
from pathlib import Path
import numpy as np
import rasterio
from verify_texture_grid_change import read, sha

parser = argparse.ArgumentParser(description=__doc__)
for name in ('baseline', 'candidate', 'asc', 'out'):
    parser.add_argument('--'+name, type=Path, required=True)
parser.add_argument('--without-diagnostic-pond', type=Path)
args = parser.parse_args()
if args.out.exists() or (args.without_diagnostic_pond and args.without_diagnostic_pond.exists()):
    raise ValueError('Fresh output required')
old, new = read(args.baseline), read(args.candidate)
with rasterio.open(args.asc) as dataset:
    expected = dataset.read(1)
actual = np.frombuffer(new['heights'], dtype='<f4').reshape(2048,2048)[::-1,:]
key = lambda obj:(obj['name'].lower(), obj['id'], obj['matrix'])
after_height = 24+2048*2048*4
checks = dict(heights_match_candidate=bool(np.max(abs(expected-actual)) <= .00501),
              header_unchanged=old['bytes'][:24] == new['bytes'][:24],
              texture_indices_and_materials_unchanged=old['bytes'][after_height:old['objects_start']] == new['bytes'][after_height:new['objects_start']],
              all_objects_unchanged=sorted(map(key, old['objects'])) == sorted(map(key, new['objects'])),
              expected_two_objects=len(new['objects']) == 2)
report = dict(status='PASS_NATIVE_CLEARANCE' if all(checks.values()) else 'FAIL',
              checks=checks, candidate_wrp_sha256=sha(new['bytes']),
              baseline_wrp_sha256=sha(old['bytes']), candidate_asc_sha256=sha(args.asc.read_bytes()),
              max_height_error_m=float(np.max(abs(expected-actual))),
              limit='Native serialization only; not compiled/render/water/navigation proof.')
if all(checks.values()) and args.without_diagnostic_pond:
    ponds = [obj for obj in new['objects'] if obj['name'].lower() == 'dz\\water\\ponds\\pond_50x50.p3d']
    if len(ponds) != 1:
        raise ValueError('Expected diagnostic pond')
    pond = ponds[0]
    filtered = new['bytes'][:pond['start']] + new['bytes'][pond['end']:]
    if filtered[:new['objects_start']] != new['bytes'][:new['objects_start']]:
        raise ValueError('Terrain/material changed by object filter')
    args.without_diagnostic_pond.parent.mkdir(parents=True, exist_ok=True)
    args.without_diagnostic_pond.write_bytes(filtered)
    report['filtered'] = dict(sha256=sha(filtered), removed_bytes=pond['end']-pond['start'])
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
