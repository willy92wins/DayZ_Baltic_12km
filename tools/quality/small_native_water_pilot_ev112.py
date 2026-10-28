"""One offline height candidate for a closed native sea body; no integration.

Prepare freezes a domain before authoring. Generate uses it once and never
retries parameters. The independent consumer owns topology and acceptance.
"""
import os
for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_key] = '1'
import argparse
import importlib.util
import json
from pathlib import Path
import time
import numpy as np
from scipy.ndimage import binary_dilation
from shapely.geometry import Polygon, LineString, MultiLineString, Point, box

HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


shore = load_module('small_shore', HERE.parent/'water/shore_ramp_v31.py')
MASK = 'v31_small_water_pilot'
PROTECTED = ('platform', 'reserve', 'narva', 'v31_kit', 'v31_bridge_cut',
             'v31_lagoon', 'v31_dam', 'v31_shore_ramp', 'v31_causeway',
             'v31_despike', 'v31_continuous_pilot', 'v31_narva_seaward',
             'v31_road_repair', 'v31_road_mesh_repair', 'v31_shape_repair')


def require(value, message):
    if not bool(value):
        raise ValueError(message)


def arrays(path):
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key] for key in data.files}


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def side_requirements(h, protected):
    """B-strict: unanimous native-neighbour side, conflicts unconstrained."""
    fixed = np.where(protected & (abs(h-.75) > .1), np.sign(h-.75), 0)
    positive = binary_dilation(fixed > 0, shore.S6)
    negative = binary_dilation(fixed < 0, shore.S6)
    return np.where(~protected & (positive != negative), np.where(positive, 1, -1), 0).astype(np.int8)


def prepare(terrain, footprint, census, target_file, inventory, geometry_report, output, chain_id):
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    for path, digest in ((terrain, '815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'),
                         (footprint, '084171b0e29df5c220f9d5aab42a3dc683a2f70a07579f08cd930dfd109e716b'),
                         (census, 'b6612009ff531ef2f3932240ea52cf0660bce97f7904b7d667f962ce0fd95847')):
        require(shore.sha(path) == digest, 'reviewed_baseline_'+str(path))
    t = arrays(terrain); f = arrays(footprint); s = arrays(census); g = arrays(target_file)
    h = t['heights']; n = len(h)
    require(h.shape == (2048, 2048) and h.dtype == np.float32, 'native_grid')
    require(MASK not in t, 'already_authored')
    require(0 <= chain_id < len(s['closed']) and s['closed'][chain_id], 'closed_body_required')
    ids = s['chain_order'][s['chain_offsets'][chain_id]:s['chain_offsets'][chain_id+1]]
    original = s['chain_points'][s['point_offsets'][chain_id]:s['point_offsets'][chain_id+1]]
    require(np.array_equal(original, g['original']), 'target_source_contour')
    require(not s['pond'][ids].any() and np.all(s['lev'][ids] == .75), 'native_sea_only')
    target = g['target']; poly = Polygon(target); old = Polygon(original)
    require(poly.is_valid and poly.area > 0 and old.is_valid and old.area > 0, 'invalid_polygon')
    # Vertex displacement bounds the whole piecewise-linear target only if each
    # segment is checked too; shapely Hausdorff below is supplemented by 0.1m
    # samples and a half-sample conservative margin.
    q, _ = shore.resample(np.vstack([target, target[:1]]), .1, True)
    displacement = max(old.boundary.distance(Point(p)) for p in q) + .05
    require(displacement <= 9., 'target_displacement')
    fixed = np.zeros(h.shape, bool)
    for key in PROTECTED:
        require(key in t and t[key].dtype == bool and t[key].shape == h.shape, 'protection_'+key)
        fixed |= t[key]
    for key in t:
        if key.startswith(('v31_bridge_', 'v31_lattice')) or key == 'v31_kit':
            require(t[key].dtype == bool and t[key].shape == h.shape, 'protection_type_'+key)
            fixed |= binary_dilation(t[key], np.ones((3, 3), bool))
    # Protect every current and potential pond corner, even outside this ROI.
    fixed |= shore.c2v(np.isfinite(f['plane']) | np.isfinite(f['env_plane']))
    rr, cc = np.indices(h.shape)
    for crossing in json.loads(Path(inventory).read_text(encoding='utf-8')):
        fixed |= np.hypot(cc*6-crossing['x'], 12282-rr*6-crossing['z']) < 60
    del rr, cc
    others = np.ones(len(s['p']), bool); others[ids] = False
    cellmask = np.zeros((n-1, n-1), bool)
    cells = s['cell'][others]; cellmask[cells[:, 0], cells[:, 1]] = True
    fixed |= binary_dilation(shore.c2v(cellmask), shore.S6)
    keys = s['chain_keys'][s['point_offsets'][chain_id]:s['point_offsets'][chain_id+1]]
    pin = fixed.ravel()[keys//(n*n)] & fixed.ravel()[keys % (n*n)]
    require(pin[:-1].mean() <= .20, 'fixed_fraction')
    station = shore.arclen(original)
    ss = np.unique(np.r_[np.arange(0, station[-1], 1.), station[:-1][pin[:-1]]])
    sample = np.column_stack([np.interp(ss, station, original[:, k]) for k in (0, 1)])
    pins = np.isin(ss, station[:-1][pin[:-1]])
    regenerated = shore.smooth_pinned(sample, pins, True, 12.)
    require(regenerated.shape == target.shape and np.max(abs(regenerated-target)) <= 1e-9,
            'reviewed_target_changed')
    otherline = MultiLineString(s['p'][others].tolist())
    lo = np.array(poly.bounds[:2])-15; hi = np.array(poly.bounds[2:])+15
    r0, r1 = max(0, int((12282-hi[1])//6)), min(n, int((12282-lo[1])//6)+2)
    c0, c1 = max(0, int(lo[0]//6)), min(n, int(hi[0]//6)+2)
    rr, cc = np.mgrid[r0:r1, c0:c1]; xy = np.column_stack([cc.ravel()*6, 12282-rr.ravel()*6])
    pts = [Point(p) for p in xy]
    distance = np.array([poly.boundary.distance(p) for p in pts]).reshape(rr.shape)
    sign = np.array([-1 if poly.contains(p) else 1 for p in pts]).reshape(rr.shape)
    otherdistance = np.array([otherline.distance(p) for p in pts]).reshape(rr.shape)
    local = (distance <= 15) & ~fixed[rr, cc] & (otherdistance >= distance)
    allowed = np.zeros(h.shape, bool); allowed[rr, cc] = local
    # Exact whole-cell proof, not corner-only or object-origin proximity.
    for r in range(max(0, r0-1), min(n-1, r1)):
        for c in range(max(0, c0-1), min(n-1, c1)):
            if np.isfinite(f['plane'][r, c]):
                square = box(c*6, 12282-(r+1)*6, (c+1)*6, 12282-r*6)
                require(poly.distance(square) > 15., 'active_pond_in_domain')
    bounds_report = json.loads(Path(geometry_report).read_text())
    require(not bounds_report['water_geometry_overlaps'] and not bounds_report['unknown_models'], 'stream_water_overlap')
    require(np.allclose(bounds_report['bounds'], [*lo, *hi], rtol=0, atol=1e-9), 'bound_report_domain')
    require(bounds_report['counts']['pilot_water'] == 201 and bounds_report['counts']['vanilla_stream_water'] == 6352,
            'source_water_inventory')
    for path, digest in bounds_report['inputs'].items():
        require(shore.sha(path) == digest, 'changed_water_geometry_'+path)
    # All other contours (including nested islands) are frozen. Containment
    # must hold for the polygon, not merely an island centroid.
    islands = []
    for i, closed in enumerate(s['closed']):
        if i == chain_id or not closed: continue
        ring = s['chain_points'][s['point_offsets'][i]:s['point_offsets'][i+1]]
        if len(ring) >= 4 and old.contains(Polygon(ring)):
            require(poly.contains(Polygon(ring)), 'target_excludes_island'); islands.append(i)
    od = np.array([old.boundary.distance(p) for p in pts]).reshape(rr.shape)
    fit = local & (od > 0) & (od <= 9)
    require(fit.any() and local.any(), 'empty_fit_domain')
    slope = float(np.clip(np.median(abs(h[rr, cc][fit]-.75)/od[fit]), .05, .35))
    domain = output/'domain.npz'
    np.savez_compressed(domain, allowed=allowed, fixed=fixed, side=side_requirements(h, fixed),
                        rows=rr, cols=cc, distance=distance, signed_distance=distance*sign,
                        original=original, target=target)
    paths = [terrain, footprint, census, target_file, inventory, geometry_report, domain,
             Path(__file__), HERE/'verify_small_native_water_pilot_ev112.py',
             HERE/'verify_native_shore_census_ev112.py', HERE/'shape_patterns_ev112.py',
             HERE.parent/'water/shore_ramp_v31.py', HERE.parent/'terrain/despike_v31.py']
    context = dict(status='PREPARED_NOT_AUTHORED', chain=chain_id, terrain=str(terrain), footprint=str(footprint),
                   census=str(census), domain=str(domain), source_hashes={str(p):shore.sha(p) for p in paths},
                   slope=slope, islands=islands, allowed_vertices=int(allowed.sum()),
                   maximum_target_displacement_bound_m=displacement, pin_fraction=float(pin[:-1].mean()))
    write_json(output/'context.json', context)
    return context


def generate(context_path, output):
    started = time.monotonic(); context = json.loads(Path(context_path).read_text())
    for path, digest in context['source_hashes'].items():
        require(shore.sha(path) == digest, 'stale_input_'+path)
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    data = arrays(context['terrain']); d = arrays(context['domain']); h = data['heights']
    require(MASK not in data, 'already_authored')
    rr, cc = d['rows'], d['cols']; dist = d['distance']; sd = d['signed_distance']
    t = np.clip((dist-9)/6, 0, 1); blend = 1-t*t*(3-2*t)
    proposed = h[rr, cc]*(1-blend) + (.75+context['slope']*sd)*blend
    side = d['side'][rr, cc]
    proposed = np.where(side > 0, np.maximum(proposed, .80), proposed)
    proposed = np.where(side < 0, np.minimum(proposed, .70), proposed).astype(np.float32)
    free = d['allowed'][rr, cc]; result = h.copy(); result[rr[free], cc[free]] = proposed[free]
    data['heights'] = result; data[MASK] = result != h
    require(data[MASK].any(), 'unchanged_candidate')
    np.savez_compressed(output/'candidate.npz', **data)
    report = dict(status='CANDIDATE_UNVALIDATED', changed=int(data[MASK].sum()), seconds=time.monotonic()-started,
                  sha256=shore.sha(output/'candidate.npz'), context_sha256=shore.sha(context_path))
    report['annuli'] = []
    for lo, hi in ((0, 9), (9, 15)):
        selected = (dist >= lo) & (dist <= hi) & free & data[MASK][rr, cc]
        delta = abs(result[rr, cc][selected]-h[rr, cc][selected])
        report['annuli'].append(dict(inner_m=lo, outer_m=hi, changed=int(selected.sum()),
                                    maximum_delta_m=float(delta.max()) if len(delta) else 0.))
    write_json(output/'generation.json', report)
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='action', required=True)
    p = sub.add_parser('prepare')
    for name in ('terrain', 'footprint', 'census', 'target_file', 'inventory', 'geometry_report', 'output'):
        p.add_argument(name, type=Path)
    p.add_argument('--chain-id', type=int, required=True)
    g = sub.add_parser('generate'); g.add_argument('context_path', type=Path); g.add_argument('output', type=Path)
    args = vars(ap.parse_args()); action = args.pop('action')
    print(json.dumps((prepare if action == 'prepare' else generate)(**args)))
