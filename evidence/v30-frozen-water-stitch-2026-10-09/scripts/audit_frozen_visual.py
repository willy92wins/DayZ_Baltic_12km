"""Consumer of a proposed visible water field using the packaged water source.

Measures native triangle areas, topology, dry-land incursions and visible offsets.
It does not author geometry and cannot certify compiled LODs or native rendering.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components

W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B = Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
OUT = Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path[:0] = [str(B), str(W/'tools/terrain')]
from audit_pond_topology import triangle_areas
from audit_visible_field_domain import clip, area, UNIT, controls as area_controls
from v30_common import cell_planes


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_identity(path, expected):
    if sha(path) != expected:
        raise ValueError('Input does not match its independently frozen identity: '+str(path))


def positive_interval(a, b):
    cross = np.clip(-a/np.where(np.abs(b-a)>1e-12, b-a, 1), 0, 1)
    lo = np.where((a<=0)&(b>0), cross, 0.)
    hi = np.where((a>0)&(b<=0), cross, 1.)
    hi = np.where((a<=0)&(b<=0), 0., hi)
    return lo, hi


def overlap_length(a, b):
    al, ah = positive_interval(a[:, 0], a[:, 1])
    bl, bh = positive_interval(b[:, 0], b[:, 1])
    return np.maximum(0, np.minimum(ah, bh)-np.maximum(al, bl))


def domain(h, p, field=None):
    valid = np.isfinite(p)
    rr, cc = np.nonzero(valid)
    ids = np.full(p.shape, -1, np.int32)
    ids[rr, cc] = np.arange(len(rr))
    ground = np.c_[h[rr, cc], h[rr, cc+1], h[rr+1, cc], h[rr+1, cc+1]]
    corners = np.repeat(p[rr, cc, None], 4, axis=1) if field is None else field[rr, cc]
    depth = corners-ground
    triangles = np.stack([depth[:, [0, 1, 3]], depth[:, [0, 2, 3]]], axis=1).reshape(-1, 3)
    areas = triangle_areas(triangles)
    active = areas>1e-8
    lookup = np.full(len(active), -1, np.int32)
    lookup[active] = np.arange(active.sum())
    ix = np.flatnonzero(np.max(depth[:, [0, 3]], axis=1)>1e-7)
    lefts, rights = [ix*2], [ix*2+1]
    contacts = []
    for axis in (0, 1):
        if axis == 0:
            r, c = np.nonzero(valid[:-1]&valid[1:])
            a, b = ids[r, c], ids[r+1, c]
            da, db = depth[a][:, [2, 3]], depth[b][:, [0, 1]]
            fa, fb = a*2+1, b*2
        else:
            r, c = np.nonzero(valid[:, :-1]&valid[:, 1:])
            a, b = ids[r, c], ids[r, c+1]
            da, db = depth[a][:, [1, 3]], depth[b][:, [0, 2]]
            fa, fb = a*2, b*2+1
        length = overlap_length(da, db)
        keep = length>1e-8
        lefts.append(fa[keep]); rights.append(fb[keep])
        contacts.append(length)
    a, b = lookup[np.concatenate(lefts)], lookup[np.concatenate(rights)]
    keep = (a>=0)&(b>=0)
    graph = sparse.coo_matrix((np.ones(keep.sum(), np.uint8), (a[keep], b[keep])),
                              shape=(int(active.sum()), int(active.sum()))).tocsr()
    number, labels = connected_components(graph, directed=False)
    body_area = np.bincount(labels, weights=areas[active], minlength=number)
    all_labels = np.full(len(active), -1, np.int32)
    all_labels[active] = labels
    return dict(labels=all_labels, areas=areas, body_area=body_area, triangles=triangles,
                corners=corners, cells=(rr, cc), contacts=contacts)


def visible_error(depth, delta, areas):
    result = np.max(np.where(depth>0, np.abs(delta), 0), axis=1)
    for i, j in ((0, 1), (1, 2), (2, 0)):
        crossing = (depth[:, i]>0)!=(depth[:, j]>0)
        di, dj = depth[crossing, i], depth[crossing, j]
        error = delta[crossing, i]+di/(di-dj)*(delta[crossing, j]-delta[crossing, i])
        result[crossing] = np.maximum(result[crossing], np.abs(error))
    result[areas<=1e-10] = 0
    return result


def topology_gate(before, after, overlap):
    good = (overlap>1e-8)&(before['labels']>=0)&(after['labels']>=0)
    pairs = np.c_[before['labels'][good], after['labels'][good]]
    unique, inverse = np.unique(pairs, axis=0, return_inverse=True)
    weights = np.bincount(inverse, weights=overlap[good])
    retained = np.bincount(before['labels'][good], weights=overlap[good],
                          minlength=len(before['body_area']))
    significant_old = before['body_area']>=1
    significant_new = after['body_area']>=1
    forwards = {}; reverse = {}
    for (a, b), w in zip(unique, weights):
        if w>1e-8 and significant_new[b]:
            forwards.setdefault(int(a), set()).add(int(b))
            if significant_old[a]: reverse.setdefault(int(b), set()).add(int(a))
    failed = []
    for ident in np.flatnonzero(significant_old):
        matches = forwards.get(int(ident), set())
        ratio = retained[ident]/before['body_area'][ident]
        if len(matches)!=1 or ratio<.9-1e-9:
            failed.append(dict(component=int(ident), area=float(before['body_area'][ident]),
                               retained_area=float(retained[ident]), ratio=float(ratio),
                               significant_descendants=sorted(matches)))
    merged = {str(k): sorted(v) for k, v in reverse.items() if len(v)>1}
    new = [int(i) for i in np.flatnonzero(significant_new) if int(i) not in reverse]
    return dict(before_significant=int(significant_old.sum()), after_significant=int(significant_new.sum()),
                failed_original=failed, merged=merged, new_significant=new,
                pass_gate=not failed and not merged and not new)


def controls():
    controls = area_controls()
    assert np.allclose(triangle_areas(np.array([[1., -1, -1]])), [4.5])
    opposite = domain(np.array([[2., 0.], [0., 2.]]), np.ones((1, 1)))
    assert len(opposite['body_area']) == 2
    p = np.ones((2, 2)); h = np.zeros((3, 3))
    baseline = domain(h, p)
    split_h = h.copy(); split_h[:, 1] = 3
    split = domain(split_h, p)
    cut = topology_gate(baseline, split, split['areas'])
    merge = topology_gate(split, baseline, split['areas'])
    assert not cut['pass_gate'] and not merge['pass_gate']
    return controls+['opposite_corners_two_bodies', 'cut_channel_rejected', 'merged_bodies_rejected']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--field', type=Path, default=B/'frozen-field-reference/field.npy')
    parser.add_argument('--output', type=Path, default=OUT/'field-audit.json')
    args = parser.parse_args()
    assert not args.output.exists(), 'Preserve previous evidence.'
    checks = controls()
    terrain = B/'measured-bank-bed-r2/terrain.npz'
    water = Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
    manifest = Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/water/pieces.json')
    assert sha(terrain)=='e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c'
    expected_water = 'e0d35db0a7a26f9ec055d57f0c9573a1dd2c27911ec8b084274283f5884cffd1'
    verify_identity(water, expected_water)
    rejected = False
    try: verify_identity(terrain, expected_water)
    except ValueError: rejected = True
    assert rejected, 'The current terrain must fail the frozen-water identity gate.'
    assert sha(manifest)=='77d030e28a414fa738aa57d452ff56d02c1599811caa9455d2fb23dae1900d62'
    t, source = np.load(terrain), np.load(water)
    h = t['heights'].astype(float)
    p = cell_planes(source['cls'], source['level'], sea_cut=json.loads(manifest.read_text())['sea_cutoff_m'])
    field_path = args.field
    field = np.load(field_path)
    assert np.array_equal(p, np.load(B/'frozen-field-reference/plane.npy'), equal_nan=True)
    assert np.isfinite(field[np.isfinite(p)]).all()
    before = domain(h, p)
    after = domain(h, p, field)
    print('Native domains complete', flush=True)
    db, da = before['triangles'], after['triangles']
    delta = da-db
    changed = np.max(np.abs(delta), axis=1)>1e-10
    overlap = np.minimum(before['areas'], after['areas'])
    mixed = changed & (np.min(db, axis=1)<0) & (np.min(da, axis=1)<0) & (overlap>0)
    for n, i in enumerate(np.flatnonzero(mixed)):
        overlap[i] = area(clip(clip(UNIT, db[i]), da[i]))
        if (n+1)%5000 == 0: print('Clipped mixed faces', n+1, flush=True)
    old_error = visible_error(db, delta, before['areas'])
    new_error = visible_error(da, delta, after['areas'])
    gained = np.maximum(0, after['areas']-overlap)
    lost = np.maximum(0, before['areas']-overlap)
    rr, cc = before['cells']
    classes = np.c_[t['cls'][rr, cc], t['cls'][rr, cc+1], t['cls'][rr+1, cc], t['cls'][rr+1, cc+1]]
    dry = np.stack([np.all(classes[:, [0, 1, 3]]==0, axis=1),
                    np.all(classes[:, [0, 2, 3]]==0, axis=1)], axis=1).ravel()
    topology = topology_gate(before, after, overlap)
    contacts = []
    for axis, (a, b) in enumerate(zip(before['contacts'], after['contacts'])):
        contacts.append(dict(axis=axis, newly_joined=int(((a<=1e-8)&(b>1e-8)).sum()),
                             lost_contacts=int(((a>1e-8)&(b<=1e-8)).sum())))
    gates = dict(topology=topology['pass_gate'], visible_delta=bool(max(old_error.max(), new_error.max())<=.35001),
                 no_dry_face_flood=float(gained[dry].sum())<=1e-8,
                 no_new_join=not any(c['newly_joined'] for c in contacts),
                 no_lost_contact=not any(c['lost_contacts'] for c in contacts))
    report = dict(status='PASS_SOURCE_FIELD_ONLY' if all(gates.values()) else 'FAIL_FROZEN_SOURCE_FIELD',
                  source_identities={str(path): sha(path) for path in (terrain, water, manifest, field_path)},
                  gates=gates, topology=topology, contacts=contacts, controls=checks+['wrong_water_source_rejected'],
                  all_grid_cells=int(p.size), changed_faces=int(changed.sum()),
                  gained_area_m2=float(gained.sum()), lost_area_m2=float(lost.sum()),
                  dry_face_new_area_m2=float(gained[dry].sum()),
                  maximum_old_visible_delta_m=float(old_error.max()), maximum_new_visible_delta_m=float(new_error.max()),
                  buried_corner_delta_m=float(np.nanmax(np.abs(field-p[:, :, None]))),
                  limits=['Only source geometry; current 538 stitched LODs, ODOL halos and engine remain separate checks.',
                          'The unchanged terrain hash does not identify water eligibility. Frozen water source and manifest are separately pinned.',
                          'Area gain/loss includes mixed shore faces. All original significant components are checked, not a cell-graph approximation.'])
    path = args.output
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    with path.with_suffix('.faces.csv').open('w', newline='', encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['row','col','tri','x','z','dry','gained_m2','lost_m2','old_visible_delta','new_visible_delta'])
        for i in np.flatnonzero(changed):
            cell, tri = divmod(int(i), 2);r,c=int(rr[cell]),int(cc[cell])
            writer.writerow([r,c,tri,c*6,12282-r*6,bool(dry[i]),gained[i],lost[i],old_error[i],new_error[i]])
    print(json.dumps(report, indent=2))


if __name__=='__main__': main()
