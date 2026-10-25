"""Check engine measurements against a frozen independent GIS point reference."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def assess(reference, text):
    lines = text.splitlines()
    if not lines or lines[0] != 'BALTIC_REGIONAL_WATER_V1' or lines[-1] != 'END_BALTIC_REGIONAL_WATER_V1':
        raise ValueError('Missing complete engine log markers')
    meta = dict(line.split('=', 1) for line in lines if '=' in line)
    if set(meta) != {'sea_min', 'sea_max', 'sea_now'}:
        raise ValueError('Invalid sea metadata')
    sea = {key: float(value) for key, value in meta.items()}
    if not all(math.isfinite(v) for v in sea.values()) or not sea['sea_min'] <= sea['sea_now'] <= sea['sea_max']:
        raise ValueError('Invalid sea range')
    expected = {(p['x'], p['z']): p for p in reference['samples']}
    if len(expected) != len(reference['samples']):
        raise ValueError('Duplicate reference points')
    actual = {}
    for line in lines:
        if not line.startswith('G;'):
            continue
        fields = line.split(';')[1:]
        if len(fields) != 7 or fields[3] not in ('true', 'false') or fields[4] not in ('true', 'false'):
            raise ValueError('Malformed sample')
        nums = [float(fields[i]) for i in (0, 1, 2, 5, 6)]
        if not all(math.isfinite(v) for v in nums):
            raise ValueError('Nonfinite sample')
        x, z, height, depth, water_surface = nums
        key = (x, z)
        if key in actual:
            raise ValueError('Duplicate engine point')
        actual[key] = dict(height=height, depth=depth, surface=water_surface,
                           sea=fields[3] == 'true', pond=fields[4] == 'true')
    if actual.keys() != expected.keys():
        raise ValueError('Engine/reference point sets differ')
    error = max(abs(v['height'] - expected[k]['native_height']) for k, v in actual.items())
    if error > .00501:
        raise ValueError(f'Native registration mismatch: {error} m')
    dry = [k for k, p in expected.items() if p['dry_interior']]
    flooded, clearance = [], []
    for key in dry:
        measured = actual[key]
        record = {**expected[key], 'engine': measured}
        # Depth alone can have semantics outside water. Require a water flag too.
        if measured['depth'] > .02 and (measured['sea'] or measured['pond']):
            flooded.append(record)
        if measured['height'] <= sea['sea_max']:
            clearance.append(record)
    status = 'PASS_SAMPLED_DRY_INTERIOR'
    if clearance:
        status = 'FAIL_DRY_LAND_CLEARANCE'
    if flooded:
        status = 'FAIL_DRY_LAND_FLOODING'
    groups = {}
    for item in flooded:
        groups[item['region']] = groups.get(item['region'], 0) + 1
    return dict(status=status, samples=len(actual), reference_dry_samples=len(dry),
                sea_readings=sea, native_max_error_m=error,
                flooded_dry_count=len(flooded), below_max_count=len(clearance),
                flooded_by_region=groups, flooded_dry_samples=flooded,
                clearance_samples=clearance,
                limits=['Stratified points, not flooded area or complete shoreline topology.',
                        'Current runtime sea range; no seasonal/global claim.',
                        'No water classification from satellite color.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--native', type=Path, help='Explicit changed native ASC; GIS classes/points remain frozen')
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Fresh output required')
    reference = json.loads(args.reference.read_text(encoding='utf-8'))
    current_native_sha = reference['native_sha256']
    if args.native:
        import rasterio
        from affine import Affine
        with rasterio.open(args.native) as dataset:
            if dataset.shape != (2048,2048) or dataset.transform != Affine(6,0,200000,0,-6,12288):
                raise ValueError('Changed native ASC grid mismatch')
            heights = dataset.read(1)
        for sample in reference['samples']:
            row, col = int((12282-sample['z'])/6), int(sample['x']/6)
            sample['native_height'] = float(heights[row,col])
        current_native_sha = hashlib.sha256(args.native.read_bytes()).hexdigest()
    result = assess(reference, args.log.read_text(encoding='utf-8'))
    result.update(reference_sha256=hashlib.sha256(args.reference.read_bytes()).hexdigest(),
                  native_sha256=current_native_sha,
                  original_reference_native_sha256=reference['native_sha256'],
                  log_sha256=hashlib.sha256(args.log.read_bytes()).hexdigest())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('flooded_dry_samples', 'clearance_samples')}, indent=2))
    return 0 if result['status'].startswith('PASS') else 1


if __name__ == '__main__':
    raise SystemExit(main())
