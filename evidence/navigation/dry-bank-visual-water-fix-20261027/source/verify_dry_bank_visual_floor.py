"""Saved-file consumer for the EV112 dry-bank experiment; never imports its author.

Contract: plans/ev112-dry-bank-domain-pilot-20261027.md. A preservation pass
alone does not accept a candidate. Geometry and dry freeboard are offline only.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np

SOURCE_SHA = '9d8caf0fb75d2bd34f71b877ecd3f71079898fbc01c28e67ddab0bf8dca50063'

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def identical(a, b):
    return a.shape == b.shape and a.dtype == b.dtype and a.tobytes() == b.tobytes()

def load(path):
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key].copy() for key in data.files}

def check_sources(context):
    for path, expected in context['hashes'].items():
        if sha(path) != expected:
            raise ValueError('input identity mismatch: ' + path)

def reconstruct(context, arrays):
    """From frozen baseline sources, not the pilot's free mask or report."""
    paths = context['paths']
    w = Path(context['worktree'])
    sys.path[:0] = [str(w/'tools/water'), str(w/'tools/terrain')]
    import streambed_kit_v31 as kit
    from shape_repair_constraints_ev112 import s3_road_guard
    base = load(paths['base'])
    ground_grid = load(paths['support'])['heights'].astype(float)
    names = ('reserve', 'platform', 'narva', 'v31_bridge_cut', 'v31_bridge_fill',
             'v31_dam', 'v31_causeway', 'v31_shore_ramp')
    protected = np.logical_or.reduce([base[name] for name in names])
    road_guard, refs = s3_road_guard()
    if refs != read(paths['author_report'])['road_reference_hashes']:
        raise ValueError('road reference mismatch')
    if any(context['hashes'].get(path) != value for path, value in refs.items()):
        raise ValueError('unbound road reference')
    protected |= road_guard
    for name in ('v31_road_repair', 'v31_road_mesh_repair', 'v31_continuous_pilot'):
        if name in base:
            protected |= base[name]
    protected |= kit.c2v(np.isfinite(load(paths['footprint'])['plane']))
    rr, cc = np.indices(protected.shape)
    protected |= np.hypot(cc*6.-10397.4, 12282-rr*6.-9421.9) <= 60
    bed = arrays['bed']
    terrain = kit.tri_h(ground_grid, bed[:,:,0], bed[:,:,2])
    touched = kit.tri_h(protected.astype(float), bed[:,:,0], bed[:,:,2]) > 0
    qs = np.unique(np.r_[np.arange(-18, 19, dtype=float), -2.25, 2.25])
    if bed.shape != (1663, len(qs), 3):
        raise ValueError('unexpected source dimensions')
    station = arrays['station']
    cap = np.broadcast_to((np.minimum(station, station[-1]-station) <= 6)[:,None], bed.shape[:2])
    wet = np.broadcast_to((abs(qs) <= 2.25)[None,:], bed.shape[:2])
    border = np.broadcast_to((abs(qs) == 18)[None,:], bed.shape[:2])
    floor = terrain+.02
    original = bed[:,:,1]
    if not np.array_equal(arrays['water'][:,0,1], arrays['water'][:,1,1]):
        raise ValueError('water bank Y mismatch')
    water = np.broadcast_to(arrays['water'][:,0,1,None], original.shape)
    floor = np.where(original >= water+.025, np.maximum(floor, water+.025), floor)
    # Fixed infeasible points are part of the contract, including new q3/q4.
    infeasible = (floor > original) | (np.ceil(floor*512) > np.floor(original*512))
    eligible = ~(cap | wet | border | touched | infeasible)
    return dict(cap=cap, wet=wet, border=border, protected=touched,
                infeasible=infeasible, eligible=eligible, floor=floor, qs=qs)

def geometry(bed):
    """Independent formula: discrete energy plus slopes in actual XZ metres."""
    y = bed[:,:,1]
    second = [np.diff(y, n=2, axis=axis) for axis in (0, 1)]
    mixed = np.diff(np.diff(y, axis=0), axis=1)
    energy = float(.5*(sum(np.square(v).sum() for v in second)+2*np.square(mixed).sum()))
    slopes = {}
    for axis, label in ((0, 'longitudinal_max'), (1, 'transverse_max')):
        distance = np.linalg.norm(np.diff(bed[:,:,[0,2]], axis=axis), axis=2)
        if np.any(distance <= 1e-9):
            raise ValueError('collapsed edge')
        slopes[label] = float(np.max(abs(np.diff(y, axis=axis))/distance))
    # Actual strip diagonal: NW,SW,SE and NW,SE,NE (author strip_faces:150).
    corners = (bed[:-1,:-1], bed[1:,:-1], bed[1:,1:], bed[:-1,1:])
    face_slopes = []
    for a, b, c in ((0,1,2), (0,2,3)):
        normal = np.cross(corners[b]-corners[a], corners[c]-corners[a])
        if np.any(abs(normal[:,:,1]) <= 1e-12):
            raise ValueError('collapsed XZ triangle')
        face_slopes.append(float(np.max(np.linalg.norm(normal[:,:,[0,2]],axis=2)/abs(normal[:,:,1]))))
    slopes['face_max'] = max(face_slopes)
    return dict(discrete_energy=energy, slopes=slopes)

def distribution(values):
    return dict(count=int(values.size), minimum=float(values.min()), maximum=float(values.max()),
                quantiles=dict(zip(('p01','p05','p25','p50','p75','p95','p99'),
                                   map(float, np.quantile(values, [.01,.05,.25,.5,.75,.95,.99])))))

def verify(baseline, candidate, context):
    check_sources(context)
    if sha(baseline) != SOURCE_SHA:
        raise ValueError('baseline is not the original source')
    a, b = load(baseline), load(candidate)
    if set(a) != set(b) or any(a[k].shape != b[k].shape or a[k].dtype != b[k].dtype for k in a):
        raise ValueError('array keys, shape or dtype changed')
    if not all(np.isfinite(v).all() for v in list(a.values())+list(b.values())):
        raise ValueError('nonfinite array')
    masks = reconstruct(context, a)
    ay, by = a['bed'][:,:,1], b['bed'][:,:,1]
    preservation = {k+'_exact': identical(a[k], b[k]) for k in a if k != 'bed'}
    preservation['bed_xz_exact'] = identical(a['bed'][:,:,[0,2]], b['bed'][:,:,[0,2]])
    for name in ('cap','wet','border','protected','infeasible'):
        mask = masks[name]
        preservation[name+'_exact'] = identical(a['bed'][mask], b['bed'][mask])
    allowed = masks['eligible']
    preservation['excluded_exact'] = identical(a['bed'][~allowed], b['bed'][~allowed])
    before, after = geometry(a['bed']), geometry(b['bed'])
    gates = dict(preservation=all(preservation.values()),
                 quantization=bool(np.array_equal(by, np.rint(by*512)/512)),
                 bounds=bool(np.all(by[allowed] >= masks['floor'][allowed]) and np.all(by <= ay)),
                 changed=bool(np.any(by != ay)),
                 energy_strictly_lower=after['discrete_energy'] < before['discrete_energy'],
                 slopes_nonincreasing=all(after['slopes'][k] <= v for k,v in before['slopes'].items()))
    freeboard = {}
    for q in (-4.,-3.,3.,4.):
        col = int(np.flatnonzero(masks['qs']==q)[0])
        freeboard[str(q)] = dict(baseline=distribution(ay[:,col]-a['water'][:,0,1]),
                                 candidate=distribution(by[:,col]-a['water'][:,0,1]))
    check_sources(context)
    return dict(status='OFFLINE_CANDIDATE_ONLY' if all(gates.values()) else 'REJECTED_OFFLINE',
                gates=gates, preservation=preservation, baseline_sha256=sha(baseline),
                candidate_sha256=sha(candidate), baseline=before, candidate=after,
                changed_points=int(np.count_nonzero(by != ay)),
                counts={k:int(masks[k].sum()) for k in ('cap','wet','border','protected','infeasible','eligible')},
                delta_range_m=[float((by-ay).min()),float((by-ay).max())], freeboard_q3_q4=freeboard,
                sources_unchanged=True, limits=['Saved-array offline result; no native, visual, P14, navigation or RAM acceptance.',
                'The 0.025 m dry floor is experimental, not a wave or native-water guarantee.'])

def main():
    parser = argparse.ArgumentParser()
    for name in ('baseline','candidate','context','output'):
        parser.add_argument('--'+name, required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    try:
        result = verify(args.baseline,args.candidate,read(args.context))
    except Exception as error:
        result = dict(status='REJECTED_INVALID_INPUT',error=type(error).__name__+': '+str(error))
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(result['status'])
    return 0 if result['status']=='OFFLINE_CANDIDATE_ONLY' else 2

if __name__ == '__main__':
    sys.exit(main())
