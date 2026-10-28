"""Offline static Geometry diagnostic; never a native collision or map PASS.

The two ODOL frame hypotheses are deliberately not certified engine conventions.
Convex hulls are supersets. Separation proves exclusion only under those hypotheses.
"""
import os
for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_key] = '1'
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy.spatial import ConvexHull, QhullError

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent/'terrain'), str(HERE.parent/'water')]
import deployed_surface_inventory_ev112 as inv
import compiled_dry_road_gate_ev112 as gate
import water_constraint_diagnostic_ev112 as meter
from package_visual_forest_ev112 import compiled_arrays
from streambed_kit_v31 import tri_h

GEOMETRY = float(np.float32(1e13))
PAIRS = ((349, 348), (350, 311), (700, 701), (723, 725), (1425, 1426))
IDS = tuple(x for pair in PAIRS for x in pair)
EPS = np.finfo(float).eps
OFFSETS = ((0., 0.), (.005, 0.), (-.005, 0.), (.02, 0.), (-.02, 0.),
           (0., .005), (0., -.005), (0., .02), (0., -.02))
require = meter.require
dump = meter.dump
sha = meter.sha


def norm(s):
    return s.replace('\\', '/').lower().strip('/')


def geometry_lod(od):
    require(not od.lod_errors and len(od.lods) == len(od.resolutions)
            and all(l.lod_end_ok for l in od.lods), 'incomplete_odol')
    require(all(np.isfinite(l.resolution) for l in od.lods), 'nonfinite_resolution')
    found = [l for l in od.lods if float(l.resolution) == GEOMETRY]
    require(len(found) <= 1, 'duplicate_geometry')
    return found[0] if found else None


def components(vertices, faces, selections):
    """Include every face vertex, even when selected_vertices omits it."""
    v = np.asarray(vertices, float)
    require(v.ndim == 2 and v.shape[1] == 3 and np.isfinite(v).all(), 'vertices')
    fs = []
    for f in faces:
        a = np.asarray(f, np.int64)
        require(a.ndim == 1 and len(a) in (3, 4) and
                ((a >= 0) & (a < len(v))).all(), 'face_indices')
        fs.append(a)
    covered = set()
    groups = []
    for s in selections:
        if not s.name.lower().startswith('component'):
            continue
        fi, vi = list(map(int, s.selected_faces)), list(map(int, s.selected_vertices))
        require(all(0 <= i < len(fs) for i in fi) and
                all(0 <= i < len(v) for i in vi), 'selection_indices')
        ids = set(vi)
        for i in fi:
            ids.update(fs[i].tolist())
        covered.update(fi)
        if ids:
            groups.append((s.name, np.array(sorted(ids), np.int64)))
    residual = sorted(set(range(len(fs))) - covered)
    if residual:
        groups.append(('unassigned_faces', np.unique(np.concatenate([fs[i] for i in residual]))))
    # Vertex-only geometry is not silently empty either.
    used = set(int(i) for _, ids in groups for i in ids)
    extra = sorted(set(range(len(v))) - used)
    if extra:
        groups.append(('unassigned_vertices', np.array(extra, np.int64)))
    return fs, groups


def aabb_world(vertices, matrices):
    """Conservative float64 bounds, inflated only for arithmetic roundoff."""
    v, m = np.asarray(vertices, float), np.asarray(matrices, float).reshape(-1, 12)
    require(v.ndim == 2 and v.shape[1] == 3 and len(v) and
            np.isfinite(v).all() and np.isfinite(m).all(), 'aabb_input')
    lo, hi = v.min(0), v.max(0)
    center, radius = (lo+hi)/2, (hi-lo)/2
    a = m[:, :9].reshape(-1, 3, 3)
    c = np.einsum('i,nij->nj', center, a) + m[:, 9:]
    e = np.einsum('i,nij->nj', radius, np.abs(a))
    err = 64*EPS*(np.einsum('i,nij->nj', np.maximum(abs(lo), abs(hi)),
                          np.abs(a)) + abs(m[:, 9:]) + 1)
    return c-e-err, c+e+err


def separation(vertices, point, transform_error=0.):
    """An approximate hull normal is only a direction; verify against ALL vertices.

    64*eps bounds our short float64 transforms/dot products with slack. It is
    arithmetic uncertainty, not a physical clearance tolerance. Hull inclusion
    is possible occupancy, not proof of a solid interior.
    """
    v, p = np.asarray(vertices, float), np.asarray(point, float)
    require(v.ndim == 2 and v.shape[1] == 3 and len(v) and p.shape == (3,) and
            np.isfinite(v).all() and np.isfinite(p).all() and
            np.isfinite(transform_error) and transform_error >= 0, 'separation_input')
    box = separation_aabb(v, p, transform_error)
    if box['state'] == 'SEPARATED':
        return box
    directions = np.concatenate((np.eye(3), -np.eye(3)))
    degenerate = False
    if len(v) >= 4:
        try:
            directions = np.concatenate((directions, ConvexHull(v).equations[:, :3]))
        except QhullError:
            degenerate = True
    else:
        degenerate = True
    dots = (p-v) @ directions.T
    lower = dots.min(0)
    err = 64*EPS*((abs(p)+abs(v).max(0)+1) @ abs(directions).T)
    err += transform_error*np.abs(directions).sum(1)
    margin = lower-err
    i = int(np.argmax(margin))
    if margin[i] > 0:
        return dict(state='SEPARATED', normal=directions[i].tolist(),
                    verified_min_projection=float(lower[i]), arithmetic_bound=float(err[i]),
                    lower_margin=float(margin[i]), vertices_verified=len(v))
    return dict(state='INCONCLUSIVE_DEGENERATE' if degenerate else 'POSSIBLE_OCCUPANCY',
                arithmetic_bound=float(err.max()), vertices_verified=len(v))


def ray_mesh(vertices, faces):
    triangles, indices, fans, quad = [], [], [], []
    for fi, ids in enumerate(faces):
        for j in range(1, len(ids)-1):
            triangles.append(vertices[np.asarray(ids)[[0, j, j+1]]])
            indices.append(fi)
            fans.append(j-1)
            quad.append(len(ids) != 3)
    return (np.asarray(triangles, float).reshape(-1, 3, 3),
            np.asarray(indices), np.asarray(fans), np.asarray(quad))


def vertical_hits(vertices, faces, x, z, low, high, mesh=None):
    """All triangle-fan contacts; edge/vertical/nonplanar ambiguity stays explicit."""
    hits = []
    triangles, indices, fans, quads = mesh if mesh is not None else ray_mesh(vertices, faces)
    if not len(triangles):
        return hits
    # Filter triangles, not object centers. Padding is solely arithmetic error.
    pad = 64*EPS*max(float(abs(triangles).max()), abs(x), abs(z), 1.)
    q = np.array([x, z])
    xmin = triangles[:, :, [0, 2]].min(1)
    xmax = triangles[:, :, [0, 2]].max(1)
    selected = np.flatnonzero(((q >= xmin-pad) & (q <= xmax+pad)).all(1))
    for k in selected:
            t, fi, fan = triangles[k], int(indices[k]), int(fans[k])
            q = np.array([x, z])
            a, b, c = t[:, [0, 2]]
            u, v, d = b-a, c-a, q-a
            det = u[0]*v[1]-u[1]*v[0]
            scale = max(float(abs(t).max()), abs(x), abs(z), 1.)
            tol = 64*EPS*scale
            if abs(det) <= tol*max(np.linalg.norm(u)+np.linalg.norm(v), 1.):
                if ((q >= t[:, [0, 2]].min(0)-tol) &
                    (q <= t[:, [0, 2]].max(0)+tol)).all():
                    hits.append(dict(face=fi, fan=fan, state='INCONCLUSIVE_VERTICAL_OR_DEGENERATE'))
                continue
            wb = (d[0]*v[1]-d[1]*v[0])/det
            wc = (u[0]*d[1]-u[1]*d[0])/det
            bary = np.array([1-wb-wc, wb, wc])
            btol = tol*max(np.linalg.norm(u)+np.linalg.norm(v), 1.)/abs(det)*8
            if bary.min() < -btol:
                continue
            y = float(bary @ t[:, 1])
            if not low-tol <= y <= high+tol:
                continue
            hits.append(dict(face=fi, fan=fan, height=y, bary=bary.tolist(),
                             state='AMBIGUOUS_EDGE_OR_FACE' if bary.min() <= btol or quads[k] else 'FACE_INTERIOR',
                             quad_fan_conditional=bool(quads[k])))
    return hits


def select_points(selected, original, H):
    a = {x['id']: x for x in selected}
    b = {x['id']: x for x in original}
    require(len(a) == len(selected) and len(b) == len(original), 'duplicate_source_id')
    require(set(IDS) <= a.keys() & b.keys(), 'missing_central_id')
    points = []
    for ident in IDS:
        e = a[ident]['expected']
        require(e == b[ident]['expected'] and a[ident]['original_states'] == b[ident]['states'],
                'original_central_changed')
        h, bed = e['ground'], e['effective_bed']
        for slot, (dx, dz) in enumerate(OFFSETS):
            x, z = map(float, np.float32([e['x']+dx, e['z']+dz]))
            require(slot != 0 or (x == e['x'] and z == e['z']), 'central_float32_changed')
            low = float(np.float32(max(h, bed)+2))
            terrain = float(tri_h(H, x, z))
            points.append(dict(id=ident, slot=slot, x=x, z=z,
                               nominal_offset=[dx, dz], effective_offset=[x-e['x'], z-e['z']],
                               H=h, B=bed, terrain_at_offset=terrain, low_y=low,
                               high_y=float(np.float32(h+100)), end_y=float(np.float32(h-10)),
                               terrain_clearance=low-terrain, original_states=b[ident]['states']))
    require(len(points) == 90 and len({(p['id'], p['slot']) for p in points}) == 90,
            'point_coverage')
    return points


def bind_packages(paths):
    """Caller fixes packages first. Duplicate virtual paths are never overwritten."""
    bindings, packages = {}, []
    for path in paths:
        path = Path(path)
        with path.open('rb') as f:
            props, entries = inv.pbo_table(f, path.stat().st_size)
        prefix = norm(props.get('prefix', ''))
        require(prefix, 'missing_pbo_prefix:'+str(path))
        packages.append(dict(path=str(path), sha256=sha(path), prefix=prefix))
        for entry in entries:
            if not entry['name'].endswith(('.p3d', '.wrp')):
                continue
            name = prefix+'/'+entry['name']
            require(name not in bindings, 'ambiguous_package_path:'+name)
            bindings[name] = dict(package=str(path), entry=entry)
    return bindings, packages


def payload(binding):
    p, e = Path(binding['package']), binding['entry']
    require(e['mime'] == 0 and e['size'] <= 32*1024**2, 'payload_format_or_budget')
    with p.open('rb') as f:
        f.seek(e['offset'])
        b = inv.exact(f, e['size'])
    return b


def model_geometry(name, bindings, backend):
    require(name in bindings, 'unbound_model:'+name)
    raw = payload(bindings[name])
    od = backend.from_bytes(raw, strict=True)
    lod = geometry_lod(od)
    v = gate.xyz(lod.vertices) if lod else np.empty((0, 3))
    fs, groups = components(v, [f.vertex_indices for f in lod.faces] if lod else [],
                            lod.named_selections if lod else [])
    center = gate.xyz([od.model_info.bounding_center])[0]
    proxies = []
    # Inspect every LOD, so absence of Geometry cannot hide a proxy child.
    for l in od.lods:
        for p in l.proxies:
            child = norm(p.model)
            child += '' if child.endswith('.p3d') else '.p3d'
            if child not in proxies:
                proxies.append(child)
    metadata = dict(name=name, sha256=hashlib.sha256(raw).hexdigest(),
                    package=bindings[name]['package'], entry=bindings[name]['entry']['name'],
                    geometry_resolution=lod.resolution if lod else None,
                    vertices=len(v), faces=len(fs), components=len(groups), proxies=proxies,
                    center=center.tolist(),
                    header={k:gate.xyz([getattr(od.model_info, k)])[0].tolist()
                            for k in ('bbox_min', 'bbox_max', 'bounding_center', 'geometry_center')},
                    lod_bounds={k:gate.xyz([getattr(lod, k)])[0].tolist()
                                for k in ('b_min', 'b_max', 'b_center')} if lod else None,
                    decoded_bounds=[v.min(0).tolist(), v.max(0).tolist()] if len(v) else None)
    return v, fs, groups, center, metadata


def empty_proxy_tree(name, bindings, backend, stack=()):
    """Only certify a proxy subtree empty; do not invent its transform."""
    if name in stack or len(stack) >= 16:
        return False, [dict(name=name, reason='proxy_cycle_or_depth')]
    try:
        v, fs, groups, center, meta = model_geometry(name, bindings, backend)
    except Exception as exc:
        return False, [dict(name=name, reason=str(exc))]
    evidence = [meta]
    empty = len(v) == 0 and len(fs) == 0
    for child in meta['proxies']:
        child_empty, rows = empty_proxy_tree(child, bindings, backend, stack+(name,))
        empty &= child_empty
        evidence.extend(rows)
    return empty, evidence


def origin_state(proofs, unknown, terrain_clearance):
    if unknown:
        return 'INCONCLUSIVE_COVERAGE'
    if not np.isfinite(terrain_clearance) or terrain_clearance <= 64*EPS*16384:
        return 'INCONCLUSIVE_TERRAIN'
    if any(p['state'] != 'SEPARATED' for p in proofs):
        return 'POSSIBLE_OCCUPANCY_OR_CONTACT'
    return 'CLEAR_UNDER_FRAME_HYPOTHESES'


def proxy_coverage(name, children, instance_count, bindings, backend):
    unknown, evidence = [], []
    for child in children:
        empty, records = empty_proxy_tree(child, bindings, backend, (name,))
        evidence.extend(records)
        if not empty:
            unknown.append(dict(name=name, child=child, instances=instance_count,
                                reason='nonempty_or_unresolved_proxy_frame'))
    return unknown, evidence


def compare_snapshots(scene, order, starts, snapshots):
    """Search the full model population, not only ray candidates.

    Matching serialized coordinates after float32 roundtrip is descriptive; it
    identifies neither a native object ID nor a complete animated pose.
    """
    names = {norm(n): i for i, n in enumerate(scene['names'])}
    rows = []
    for snap in snapshots:
        for obj in snap['measured']['objects']:
            shape = norm(obj['shape'])
            position = np.asarray(obj['pos'], float)
            require(position.shape == (3,) and np.isfinite(position).all(), 'snapshot_position')
            result = dict(id=snap['id'], round=snap['round'], model=shape,
                          native_position=position.tolist())
            if not obj['valid']:
                result['state'] = 'INVALID_NATIVE_OBJECT'
            elif shape not in names:
                result['state'] = 'MODEL_NOT_IN_WRP'
            else:
                i = names[shape]
                indices = order[starts[i]:starts[i+1]]
                positions = np.asarray(scene['mat'][indices, 9:], float)
                deltas = positions-position
                distances = np.linalg.norm(deltas, axis=1)
                require(len(indices) > 0, 'snapshot_model_without_instances')
                j = int(np.argmin(distances))
                identical = np.all(positions.astype(np.float32) == position.astype(np.float32), axis=1)
                matches = scene['ids'][indices[identical]].astype(int).tolist()
                result.update(nearest_instance=int(scene['ids'][indices[j]]),
                              nearest_delta=float(distances[j]), coordinate_residual=deltas[j].tolist(),
                              matching_float32_instance_ids=matches, searched_instances=len(indices),
                              state='MATCHED_FLOAT32_POSITION' if len(matches) == 1 else
                              'AMBIGUOUS_FLOAT32_POSITION' if matches else 'NO_FLOAT32_POSITION_MATCH')
            rows.append(result)
    return rows


def central_comparison(native, hits):
    result = []
    for ident in IDS:
        n = native[ident]
        result.append(dict(id=ident, nominal_xz=[n['expected']['x'], n['expected']['z']],
                           original_states=n['states'], H=n['expected']['ground'],
                           B=n['expected']['effective_bed'],
                           native={k:n['measured'][k] for k in
                                   ('ground', 'rv', 'rv_pos', 'rv_shapes', 'rv_normal',
                                    'bullet', 'bullet_pos', 'bullet_shape', 'bullet_normal')},
                           model_contacts=[h for h in hits if h['id'] == ident and h['slot'] == 0]))
    return dict(status='DESCRIPTIVE_NO_FRAME_OR_NATIVE_CERTIFICATION', rows=result,
                limits=['All model contacts retained, not nearest-to-expected selection.',
                        'Static terrain NPZ is separate; model contacts do not include terrain.',
                        'Historical vanilla identity, animation and Bullet equivalence unproved.'])


def run(config_path, output):
    config = json.loads(config_path.read_text(encoding='utf-8'))
    for p, digest in config['pins'].items():
        require(sha(p) == digest, 'input_changed:'+p)
    bindings, packages = bind_packages(config['packages'])
    require({p['path']:p['sha256'] for p in packages} == config['package_pins'],
            'package_identity')
    wrp_path = Path(config['wrp'])
    wrp = wrp_path.read_bytes()
    wb = bindings[config['world_virtual_path']]
    with Path(wb['package']).open('rb') as f:
        e = wb['entry']
        require(e['mime'] == 0, 'compressed_world')
        f.seek(e['offset'])
        require(hashlib.sha256(inv.exact(f, e['size'])).hexdigest() ==
                hashlib.sha256(wrp).hexdigest(), 'world_payload_mismatch')
    scene, reader_info = compiled_arrays(wrp, config['anchor'])
    catalog = json.loads(Path(config['catalog']).read_text())
    counts = np.bincount(scene['mi'], minlength=len(scene['names']))
    require(len(scene['ids']) == 2578398 and len(scene['names']) == 5509 and
            len(catalog) == len(counts), 'scene_count')
    for i, row in enumerate(catalog):
        require(row['index'] == i and norm(row['name']) == norm(scene['names'][i]) and
                row['instances'] == int(counts[i]), 'scene_catalog_mismatch')
    original = json.loads(Path(config['original']).read_text())
    selected = json.loads(Path(config['selected']).read_text())
    H = np.load(config['terrain'])['heights']
    require(H.shape == (2048, 2048) and np.isfinite(H).all(), 'terrain_domain')
    points = select_points(selected, original['rows'], H)
    native = {p['id']:p for p in original['rows'] if p['id'] in IDS}
    b1 = json.loads(Path(config['b1']).read_text())['details']
    snapshots = [x for x in b1 if x['id'] in IDS]
    require(Counter((p['id'], p['round']) for p in snapshots) ==
            Counter((ident, r) for ident in IDS for r in range(3)), 'B1_snapshot_coverage')
    backend = gate.read_backend(Path(config['reader']))
    order = np.argsort(scene['mi'], kind='stable')
    starts = np.r_[0, np.cumsum(counts)]
    qlo = np.array([min(p['x'] for p in points), min(p['end_y'] for p in points),
                    min(p['z'] for p in points)])
    qhi = np.array([max(p['x'] for p in points), max(p['high_y'] for p in points),
                    max(p['z'] for p in points)])
    proofs = [[] for _ in points]
    hitrows, poses, models, unknown, proxy_evidence = [], [], [], [], []
    for i, rawname in enumerate(scene['names']):
        name = norm(rawname)
        try:
            v, fs, groups, center, meta = model_geometry(name, bindings, backend)
        except Exception as exc:
            unknown.append(dict(name=name, instances=int(counts[i]), reason=str(exc)))
            continue
        models.append(meta)
        missing, records = proxy_coverage(name, meta['proxies'], int(counts[i]), bindings, backend)
        proxy_evidence.extend(records)
        unknown.extend(missing)
        if not len(v):
            continue
        variants = (('raw', v), ('plus_bounding_center', v+center))
        local_union = np.concatenate([vs for _, vs in variants])
        indices = order[starts[i]:starts[i+1]]
        for start in range(0, len(indices), 65536):
            rows = indices[start:start+65536]
            lo, hi = aabb_world(local_union, scene['mat'][rows])
            relevant = ((hi >= qlo) & (lo <= qhi)).all(1)
            for row in rows[relevant]:
                matrix = np.asarray(scene['mat'][row], float)
                ident = int(scene['ids'][row])
                pose = dict(id=ident, model=name, matrix=matrix.tolist(),
                            terrain_at_translation=float(tri_h(H, matrix[9], matrix[11])),
                            frame_bounds={})
                poses.append(pose)
                for frame, local in variants:
                    world = inv.transform(local, matrix)
                    pose['frame_bounds'][frame] = [world.min(0).tolist(), world.max(0).tolist()]
                    mesh = ray_mesh(world, fs)
                    terr = float((64*EPS*(np.abs(local).max(0) @
                                 np.abs(matrix[:9].reshape(3, 3)) + abs(matrix[9:])+1)).max())
                    for pi, p in enumerate(points):
                        lowpt = np.array([p['x'], p['low_y'], p['z']])
                        # A whole-model AABB is an adequate exclusion certificate.
                        lo0, hi0 = world.min(0)-terr, world.max(0)+terr
                        outside = bool(((lowpt < lo0) | (lowpt > hi0)).any())
                        if outside:
                            # No hull allocation for distant components; all vertices checked.
                            s = separation_aabb(world, lowpt, terr)
                            s.update(instance=ident, model=name, frame=frame, component='whole_model')
                            proofs[pi].append(s)
                        else:
                            for component, vi in groups:
                                s = separation(world[vi], lowpt, terr)
                                s.update(instance=ident, model=name, frame=frame, component=component)
                                proofs[pi].append(s)
                        # Retain every contact; never pick the closest to a desired height.
                        if (world[:, 0].min()-terr <= p['x'] <= world[:, 0].max()+terr and
                            world[:, 2].min()-terr <= p['z'] <= world[:, 2].max()+terr):
                            for hit in vertical_hits(world, fs, p['x'], p['z'], p['end_y'], p['high_y'], mesh):
                                hit.update(id=p['id'], slot=p['slot'], instance=ident, model=name, frame=frame)
                                hitrows.append(hit)
    for p, ss in zip(points, proofs):
        p['state'] = origin_state(ss, unknown, p['terrain_clearance'])
        p['proofs'] = ss
    pose_matches = compare_snapshots(scene, order, starts, snapshots)
    for p, digest in config['pins'].items():
        require(sha(p) == digest, 'input_changed_during_run:'+p)
    require(all(sha(p) == h for p, h in config['package_pins'].items()), 'packages_changed_during_run')
    dump(output/'models.json', models)
    dump(output/'proxy-evidence.json', proxy_evidence)
    dump(output/'poses.json', poses)
    dump(output/'points.json', points)
    dump(output/'hits.json', hitrows)
    dump(output/'snapshot-pose-comparison.json', pose_matches)
    dump(output/'native-central.json', list(native.values()))
    dump(output/'central-comparison.json', central_comparison(native, hitrows))
    report = dict(status='OFFLINE_DIAGNOSTIC_ONLY', scene_instances=len(scene['ids']),
                  scene_models=len(scene['names']), decoded_models=len(models), reader=reader_info,
                  coverage_unknown=unknown, candidate_instances=len(poses),
                  points=len(points), central_points=len(IDS), origin_states=dict(Counter(p['state'] for p in points)),
                  contacts=len(hitrows),
                  contacts_by_frame={f:sum(h['frame'] == f for h in hitrows)
                                     for f in ('raw', 'plus_bounding_center')},
                  proofs_by_frame={f:dict(Counter(s['state'] for ss in proofs for s in ss if s['frame'] == f))
                                   for f in ('raw', 'plus_bounding_center')},
                  snapshot_position_states=dict(Counter(p['state'] for p in pose_matches)),
                  packages=packages, resources=meter.memory(),
                  limits=['Two model-frame hypotheses, not certified native frames.',
                          'In a frame without contacts, separation can rely exclusively on AABB exclusion.',
                          'Terrain clearance is relative to pinned NPZ, not decoded WRP heights; tri_h is shared with original expected.ground.',
                          'No equivalence to Bullet, animation, or dynamic scene occupancy.',
                          'Unknown unbounded models/proxies block every origin.',
                          'B1 vanilla identity was not sealed; snapshot comparison is descriptive.',
                          'Original47FAIL21uncertain unchanged; no water/product/global acceptance.',
                          'No game run, map mutation, tree pruning, or tolerance change.'])
    dump(output/'report.json', report)
    return report


def separation_aabb(vertices, point, transform_error=0.):
    v, p = np.asarray(vertices, float), np.asarray(point, float)
    err = 64*EPS*(abs(p)+abs(v).max(0)+1)+transform_error
    gaps = np.r_[p-v.max(0)-err, v.min(0)-p-err]
    i = int(np.argmax(gaps))
    return dict(state='SEPARATED' if gaps[i] > 0 else 'INCONCLUSIVE_NUMERICAL',
                axis=i % 3, direction=1 if i < 3 else -1,
                lower_margin=float(gaps[i]), vertices_verified=len(v))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(exist_ok=False, parents=True)
    meter.MAX_SECONDS = 300
    meter.MAX_BYTES = 2*1024**3
    meter.STARTED = time.monotonic()
    stop = meter.bounded(args.output)
    try:
        report = run(args.config, args.output)
        require(report['resources']['seconds'] <= 300 and
                max(report['resources']['peak_commit_bytes'], report['resources']['peak_resident_bytes']) <= meter.MAX_BYTES,
                'resource_budget')
        print(json.dumps({k:report[k] for k in ('status', 'scene_instances', 'decoded_models',
                                               'candidate_instances', 'origin_states', 'contacts', 'resources')}))
    except Exception as exc:
        dump(args.output/'failure.json', dict(status='INCONCLUSIVE_INSTRUMENT', error=str(exc), resources=meter.memory()))
        raise
    finally:
        stop.set()


if __name__ == '__main__':
    main()
