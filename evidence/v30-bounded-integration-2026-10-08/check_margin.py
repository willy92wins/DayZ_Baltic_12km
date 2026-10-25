"""Accept against frozen stations and native faces, independently of the producer."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools/terrain'), str(ROOT/'tools/water')]
from v30_common import cell_planes
from audit_waterline_v30 import measure
spec = importlib.util.spec_from_file_location('scope', ROOT/'evidence/v30-luga-navigation-2026-10-07/check_scope.py')
scope = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scope)
BUILD = Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008')
PREVIOUS = Path('E:/DayZ-Baltic-Build/v30-luga-navigation-20261007')
BASE = Path('E:/DayZ-Baltic-Build/v30-v12/inland/terrain_inland.npz')
CANDIDATE = BUILD/'luga-margin/terrain_inland.npz'
REPORT_DIR = BUILD/'verification-r2'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def margin_violations(base, candidate, planes):
    bad = np.zeros(planes.shape, bool)
    # Direct cell-corner comparisons, not the producer's nearest-plane field.
    for rows, cols in [(slice(None, -1), slice(None, -1)), (slice(None, -1), slice(1, None)),
                       (slice(1, None), slice(None, -1)), (slice(1, None), slice(1, None))]:
        a = base[rows, cols].astype(float)
        b = candidate[rows, cols].astype(float)
        bad |= np.isfinite(planes) & (2*np.abs(b-a) > np.abs(a-planes))
    return int(bad.sum())


def steeper_faces(base, candidate, cls):
    def slopes(h):
        h = h.astype(float)
        nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
        return [np.degrees(np.arctan(np.hypot(ne-nw, se-ne)/6)),
                np.degrees(np.arctan(np.hypot(se-sw, sw-nw)/6))]
    land = cls == 0
    touch = [land[:-1, :-1] | land[:-1, 1:] | land[1:, 1:],
             land[:-1, :-1] | land[1:, :-1] | land[1:, 1:]]
    return sum(int(np.count_nonzero(m & (new > np.maximum(old, 35)+1e-4)))
               for old, new, m in zip(slopes(base), slopes(candidate), touch))


def station_gates(a, b, missing):
    return dict(no_new_missing=len(missing) == 0, missing_count=b['missing'] <= a['missing'],
                p90=b['offset_p90_m'] <= a['offset_p90_m'], zigzag=b['zigzag_rms_m'] < a['zigzag_rms_m'])


def main():
    report_path = REPORT_DIR/'margin-verification.json'
    assert not REPORT_DIR.exists(), 'Preserve prior report'
    REPORT_DIR.mkdir()
    assert sha(BASE) == '8b3a8c5541403abaf852e14fb4c0651175e6dcaa541f6f8a151f1db04ac7a8a6'
    assert sha(CANDIDATE) == '68560a0d9848a425c2671f22238eadea39ffcb203d050cc3e46ddee79d5f5b05'
    with np.load(BASE) as f: base = dict(f)
    with np.load(CANDIDATE) as f: new = dict(f)
    old = np.load(PREVIOUS/'luga-scoped/terrain_inland.npz')['heights']
    masks_path = Path('E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007/luga-frozen-masks.npz')
    with np.load(masks_path) as f: masks = dict(f)
    h, nh = base['heights'], new['heights']
    planes = cell_planes(base['cls'], base['level'], sea_cut=.51)
    checks = dict(metadata_exact=all(np.array_equal(v, new[k], equal_nan=True) for k, v in base.items() if k != 'heights'),
                  corridor_exact=np.array_equal(h[masks['corridor']], nh[masks['corridor']]),
                  outside_allowed_exact=np.array_equal(h[~masks['allowed']], nh[~masks['allowed']]),
                  no_expanded_delta=not np.any((h == old) & (h != nh)),
                  foreign_water_faces_exact=scope.faces_unchanged(h, nh, base['cls']) == 0,
                  margin_bound=margin_violations(h, nh, planes) == 0,
                  no_steeper_land_faces=steeper_faces(h, nh, base['cls']) == 0)
    mutated = nh.copy()
    vertex = tuple(np.argwhere(base['cls'] == 2)[0])
    mutated[vertex] += .1
    negatives = dict(prior_margin_rejected=margin_violations(h, old, planes) > 0,
                     foreign_face_mutation_rejected=scope.faces_unchanged(h, mutated, base['cls']) > 0,
                     baseline_rejected_by_sector_gate=True)
    station_reports = {}
    inputs = {str(p): sha(p) for p in [BASE, CANDIDATE, masks_path, PREVIOUS/'luga-scoped/terrain_inland.npz']}
    for label in ['frozen', 'interleaved_1m']:
        path = PREVIOUS/f'stations-{label}.npz'
        inputs[str(path)] = sha(path)
        with np.load(path) as f: s = dict(f)
        p, n, rid, keep = (s[k] for k in ['points', 'normal', 'ring_id', 'keep'])
        scope.previous.NORMAL = n
        _, before = measure(str(BASE), p, n, np.full(len(p), 'river'), rid, np.ones(len(p), bool))
        _, after = measure(str(CANDIDATE), p, n, np.full(len(p), 'river'), rid, np.ones(len(p), bool))
        checks[label+'_reference_exact'] = np.array_equal(before, s['before'], equal_nan=True)
        sector_results = {}
        for sector, selected in dict(all=keep, west=keep & (p[:, 0] < 5000),
                                     central=keep & (p[:, 0] >= 5000) & (p[:, 0] < 8000), east=keep & (p[:, 0] >= 8000)).items():
            a = scope.previous.stats(p, rid, before, selected)
            b = scope.previous.stats(p, rid, after, selected)
            missing = np.flatnonzero(selected & np.isfinite(before) & ~np.isfinite(after))
            gates = station_gates(a, b, missing)
            checks.update({label+'_'+sector+'_'+key: bool(value) for key, value in gates.items()})
            sector_results[sector] = dict(before=a, after=b, checks=gates, new_missing_indices=missing.tolist())
            unchanged = scope.previous.stats(p, rid, s['before'], selected)
            negatives['baseline_rejected_by_sector_gate'] &= not all(station_gates(a, unchanged, []).values())
        station_reports[label] = sector_results
        np.savez_compressed(REPORT_DIR/f'stations-{label}.npz', **{**s, 'after': after})
    checks = {k: bool(v) for k, v in checks.items()}
    report = dict(status='PASS_OFFLINE_SHORE_ONLY' if all(checks.values()) and all(negatives.values()) else 'FAIL',
                  checks=checks, negative_controls=negatives, by_station_set=station_reports, inputs_sha256=inputs)
    report_path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(status=report['status'], failed=[k for k, v in checks.items() if not v],
                         frozen=station_reports['frozen']['all'], interleaved=station_reports['interleaved_1m']['all']), indent=2))
    return 0 if report['status'].startswith('PASS') else 1


if __name__ == '__main__':
    sys.exit(main())
