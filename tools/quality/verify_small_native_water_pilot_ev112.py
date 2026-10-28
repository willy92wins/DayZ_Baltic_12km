"""Read-only consumer: geometry/topology on the saved candidate, not spline fit.

Does not import the height author. Source domain is frozen and hash-bound before
authoring; final native shoreline is independently checked against every face.
"""
import os
for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_key] = '1'
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import numpy as np
from scipy.ndimage import label
from shapely.geometry import LineString, Polygon

HERE = Path(__file__).resolve().parent
S6 = np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]], bool)
MASK = 'v31_small_water_pilot'


def require(value, reason):
    if not bool(value): raise ValueError(reason)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod); return mod


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4 << 20), b''): h.update(block)
    return h.hexdigest()


def arrays(path):
    with np.load(path, allow_pickle=False) as f: return {k:f[k] for k in f.files}


def topology(before, after):
    """Overlap bijection, including survival; wet AND dry on native diagonal."""
    require(before.shape == after.shape and before.dtype == after.dtype == bool, 'topology_input')
    report = {}
    for name, a, b in [('wet', before, after), ('dry', ~before, ~after)]:
        la, na = label(a, S6); lb, nb = label(b, S6)
        common = a & b
        pairs = np.unique(la[common].astype(np.int64)*(nb+1)+lb[common])
        left, right = pairs//(nb+1), pairs % (nb+1)
        require(len(pairs) == na == nb and len(np.unique(left)) == na and len(np.unique(right)) == nb,
                'component_bijection_'+name)
        report[name] = dict(before=int(na), after=int(nb), overlap_pairs=len(pairs))
    return report


def closed_screen(points):
    """Worst cyclic DP start; checks the closing corner and every closed edge."""
    p = np.asarray(points, float)
    require(p.ndim == 2 and p.shape[1] == 2 and len(p) >= 4 and np.isfinite(p).all(), 'empty_or_invalid_contour')
    require(np.array_equal(p[0], p[-1]), 'unclosed_contour')
    require((np.linalg.norm(np.diff(p, axis=0), axis=1) > 1e-8).all(), 'degenerate_contour')
    require(Polygon(p).is_valid and Polygon(p).area > 0, 'invalid_contour_polygon')
    ring = p[:-1]; worst_turn = worst_line = 0.; max_bad_turns = max_bad_lines = 0
    for i in range(len(ring)):
        q = np.roll(ring, i, axis=0)
        q = np.asarray(LineString(np.vstack([q, q[:1]])).simplify(.25, preserve_topology=False).coords)
        require(len(q) >= 4 and np.array_equal(q[0], q[-1]), 'degenerate_simplification')
        edges = np.diff(q, axis=0); length = np.linalg.norm(edges, axis=1)
        require((length > 0).all(), 'duplicate_simplified_point')
        u = edges/length[:, None]
        turns = np.degrees(np.arccos(np.clip((u*np.roll(u, 1, axis=0)).sum(1), -1, 1)))
        worst_turn = max(worst_turn, float(turns.max())); worst_line = max(worst_line, float(length.max()))
        max_bad_turns = max(max_bad_turns, int((turns >= 45).sum()))
        max_bad_lines = max(max_bad_lines, int((length >= 60).sum()))
    return dict(rotations=len(ring), maximum_turn_deg=worst_turn, longest_straight_m=worst_line,
                maximum_abrupt_turns=max_bad_turns, maximum_long_straights=max_bad_lines)


def footprint_guard(before, after, plane, env):
    require(plane.shape == env.shape == (len(before)-1, len(before)-1), 'pond_shape')
    cells = np.isfinite(plane) | np.isfinite(env)
    for dr, dc in ((0, 0), (0, 1), (1, 0), (1, 1)):
        a = before[dr:dr+len(cells), dc:dc+len(cells)]
        b = after[dr:dr+len(cells), dc:dc+len(cells)]
        require(np.array_equal(a[cells], b[cells]), 'pond_corner_changed')


def delta_guard(before, after, domain):
    require(set(after) == set(before) | {MASK}, 'array_keys')
    h, candidate = before['heights'], after['heights']
    require(candidate.dtype == h.dtype and candidate.shape == h.shape and np.isfinite(candidate).all(), 'height_format')
    for key in before:
        if key != 'heights':
            require(after[key].dtype == before[key].dtype and after[key].shape == before[key].shape and
                    after[key].tobytes() == before[key].tobytes(), 'array_changed_'+key)
    changed = candidate != h
    require(changed.any(), 'unchanged_candidate')
    require(after[MASK].dtype == bool and np.array_equal(after[MASK], changed), 'change_mask')
    require(not (changed & ~domain['allowed']).any(), 'outside_allowed')
    require(not (changed & domain['fixed']).any(), 'protected_height')
    side = domain['side']
    require(not (changed & (side > 0) & (candidate < np.float32(.80))).any(), 'side_dry')
    require(not (changed & (side < 0) & (candidate > np.float32(.70))).any(), 'side_wet')
    return dict(changed=int(changed.sum()), maximum_height_delta_m=float(abs(candidate-h).max()))


def slopes(h):
    # Native face normals; derive gradient from its three vertices.
    nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
    return [np.degrees(np.arctan(np.hypot(ne-nw, se-ne)/6)),
            np.degrees(np.arctan(np.hypot(se-sw, sw-nw)/6))]


def slope_guard(before, after):
    count = 0
    for a, b in zip(slopes(before), slopes(after)):
        count += int((((a <= 35) & (b > 35)) | ((a > 35) & (b-a > .01))).sum())
    require(count == 0, 'slope_regression_'+str(count))
    return dict(regressions=count)


def verify(context_path, candidate_path, output):
    started = time.monotonic(); output = Path(output); output.mkdir(parents=True, exist_ok=False)
    ctx = json.loads(Path(context_path).read_text()); checks = {}; failures = []
    for path, digest in ctx['source_hashes'].items(): require(sha(path) == digest, 'stale_input_'+path)
    before = arrays(ctx['terrain']); after = arrays(candidate_path); domain = arrays(ctx['domain'])
    fp = arrays(ctx['footprint']); saved = arrays(ctx['census'])
    h, c = before['heights'], after['heights']

    def check(name, fn):
        try: checks[name] = dict(status='PASS', result=fn())
        except ValueError as e: checks[name] = dict(status='FAIL', reason=str(e)); failures.append(name)

    check('delta', lambda:delta_guard(before, after, domain))
    check('pond_corners', lambda:footprint_guard(h, c, fp['plane'], fp['env_plane']))
    check('topology', lambda:topology(h < .75, c < .75))
    check('slope', lambda:slope_guard(h, c))
    despike = module('small_despike_consumer', HERE.parent/'terrain/despike_v31.py')

    def prominence():
        old = despike.prominence(h); new = despike.prominence(c); stats = []
        for a, b in zip(old, new):
            count = int(((b > .30) & (b > np.maximum(a, .30))).sum()); stats.append(count)
        require(not any(stats), 'prominence_regression_peak_pit_'+str(stats)); return stats
    check('prominence', prominence)
    shore = module('small_shore_extractor', HERE.parent/'water/shore_ramp_v31.py')
    native = module('small_native_consumer', HERE/'verify_native_shore_census_ev112.py')
    water, present = shore.corner_water(fp['plane'], fp['field'])
    seg = shore.extract_segments(c, water, present, fp['plane']); assembled = shore.chain(seg)
    check('native_segments', lambda:native.segments(c, fp['plane'], fp['field'], seg))
    check('native_chains', lambda:native.chains(seg, assembled))
    old_ids = saved['chain_order'][saved['chain_offsets'][ctx['chain']]:saved['chain_offsets'][ctx['chain']+1]]
    others = np.ones(len(saved['p']), bool); others[old_ids] = False
    n = len(c)-1
    old_faces = (saved['cell'][:, 0]*n+saved['cell'][:, 1])*2+saved['tri']
    new_faces = (seg['cell'][:, 0]*n+seg['cell'][:, 1])*2+seg['tri']

    def untouched():
        order = np.argsort(new_faces); loc = np.searchsorted(new_faces[order], old_faces[others])
        require((loc < len(order)).all(), 'lost_other_shore')
        ix = order[loc]
        require(np.array_equal(new_faces[ix], old_faces[others]), 'lost_other_shore')
        for key in ('p', 'key', 'pond', 'lev'):
            require(np.array_equal(seg[key][ix], saved[key][others]), 'other_shore_changed_'+key)
        return dict(unchanged_other_segments=len(ix))
    check('other_shores', untouched)

    def contour():
        other_faces = old_faces[others]
        choices = [ch for ch in assembled if not np.isin(new_faces[ch['order']], other_faces).any()]
        require(len(choices) == 1 and choices[0]['closed'], 'pilot_contour_identity')
        final = choices[0]['pts']; metrics = closed_screen(final)
        _, wb = shore.wiggle_profile(domain['original'], True, 12., .5)
        _, wa = shore.wiggle_profile(final, True, 12., .5)
        require(len(wa) > 0 and len(wb) > 0 and np.isfinite(wa).all() and np.isfinite(wb).all(), 'wiggle_coverage')
        metrics.update(wiggle_p90_before_m=float(np.percentile(wb, 90)), wiggle_p90_after_m=float(np.percentile(wa, 90)))
        metrics['wiggle_limit_m'] = max(.08, .5*metrics['wiggle_p90_before_m'])
        np.save(output/'final-contour.npy', final)
        (output/'contour-metrics.json').write_text(json.dumps(metrics, indent=2)+'\n')
        require(metrics['maximum_abrupt_turns'] == 0, 'abrupt_turns_'+str(metrics['maximum_abrupt_turns']))
        require(metrics['maximum_long_straights'] == 0, 'long_straights')
        require(metrics['wiggle_p90_after_m'] <= metrics['wiggle_limit_m'], 'wiggle_not_reduced')
        return metrics
    check('closed_contour', contour)
    report = dict(status='REJECTED_OFFLINE' if failures else 'OFFLINE_CANDIDATE_PASS', checks=checks, failures=failures,
                  seconds=time.monotonic()-started, candidate_sha256=sha(candidate_path), context_sha256=sha(context_path),
                  limitations=['No compiled world, object grounding, game, navigation, RAM or human visual acceptance.'])
    (output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('context_path', type=Path)
    ap.add_argument('candidate_path', type=Path); ap.add_argument('output', type=Path)
    result = verify(**vars(ap.parse_args())); print(json.dumps(result))
    raise SystemExit(0 if result['status'] == 'OFFLINE_CANDIDATE_PASS' else 2)
