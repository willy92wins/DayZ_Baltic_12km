"""Check a genuine TB terrain export against an independent analytic plane."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import numpy as np


def read_asc(path):
    with path.open(encoding='ascii') as stream:
        header = dict(line.split() for line in [next(stream) for _ in range(6)])
        data = np.loadtxt(stream)
    return {k.lower(): float(v) for k, v in header.items()}, data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    fixture = a.repo / 'tests/vertex_sampling_probe'
    actual_path = a.repo / 'tb/vertex_sampling_probe/plane_tb_export.asc'
    header, actual = read_asc(actual_path)
    _, candidate = read_asc(fixture / 'plane_tb_vertices.asc')
    _, uncorrected = read_asc(fixture / 'plane_gis_centres.asc')
    expected_header = {'ncols': 128, 'nrows': 128, 'xllcorner': 200000,
                       'yllcorner': 0, 'cellsize': 6, 'nodata_value': -9999}
    assert header == expected_header, header
    assert actual.shape == (128, 128) and np.isfinite(actual).all()
    row, col = np.indices(actual.shape)
    # This analytic oracle does not import the adapter or its implementation.
    oracle = 100 + col + (768 - row * 6) / 12
    interior_error = np.abs(actual[1:, 1:] - oracle[1:, 1:])
    negative_error = np.abs(uncorrected[1:, 1:] - oracle[1:, 1:])
    tolerance = .0051  # TB ASCII exporter writes two decimal places.
    verdict = bool(np.max(interior_error) <= tolerance and
                   np.min(negative_error) > tolerance and
                   np.max(np.abs(actual-candidate)) <= tolerance)
    fixture_expected = json.loads((fixture/'expected.json').read_text())
    controls = [dict(c, tb_export_z=float(actual[c['row'], c['col']]))
                for c in fixture_expected['controls']]
    report = {
        'verdict': 'PASS' if verdict else 'FAIL',
        'consumer': 'Actual Terrain Builder import, Rebuild terrain, Save, Export terrain ASC',
        'position_contract_source': 'mesh-registration.json: four UI positives and four negatives in prior asymmetric fixture',
        'not_measured': 'No second UI XY measurement or in-game height measurement in this analytic fixture',
        'header': header, 'all_samples': int(actual.size),
        'interior_samples': int(interior_error.size),
        'interior_max_error_vs_analytic_m': float(np.max(interior_error)),
        'all_samples_max_error_vs_candidate_m': float(np.max(np.abs(actual-candidate))),
        'negative_control_min_error_m': float(np.min(negative_error)),
        'negative_control_max_error_m': float(np.max(negative_error)),
        'tolerance_m': tolerance, 'controls': controls,
        'edge_policy': 'Top/left clamped in candidate; excluded from analytic PASS. No real-world boundary adequacy claim.',
        'edge_max_error_vs_analytic_m': float(max(np.abs(actual[0]-oracle[0]).max(), np.abs(actual[:,0]-oracle[:,0]).max())),
        'production': 'NOT_APPLIED; assess coastline, nodata and boundary effects before production use',
        'sha256': {str(p.relative_to(a.repo)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in [actual_path, fixture/'plane_tb_vertices.asc', fixture/'plane_gis_centres.asc']}}
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out/'vertex-sampling-roundtrip.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    shutil.copy2(actual_path, a.out/actual_path.name)
    print(json.dumps(report, indent=2))
    if not verdict:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
