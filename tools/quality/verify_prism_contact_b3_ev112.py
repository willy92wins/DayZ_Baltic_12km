"""Independent saved-file B3 consumer. Never imports or calls the B3 author."""
import os
import time
STARTED = time.monotonic()
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[_key] = '1'
import argparse
import json
from pathlib import Path
import struct
import sys
import numpy as np
from shapely.geometry import Polygon, Point
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'water'))
from review_compact_collision_v31 import load, vertices, overlay
from mesh_quality_v31 import closed_component

def require(ok, reason):
    if not bool(ok):
        raise ValueError(reason)

def original_controls(original, targets, origin):
    retained = [row['expected'] for row in original['rows'] if row['id'] in (700, 723)]
    wanted = [dict(id=v['id'], x=v['x'], z=v['z']) for v in retained]
    require(len(retained) == 2 and {v['id']: v['expect'] for v in retained} == {700: 'dry', 723: 'wet'} and
            targets == wanted and origin == [8262., 7., 8934.], 'original_controls_changed')

def components(lod):
    xyz = np.asarray([p.coords for p in lod.points], float)
    pids = {id(p): i for i, p in enumerate(lod.points)}
    fids = {id(f): i for i, f in enumerate(lod.faces)}
    groups, used_points, used_faces, used_normals = {}, [], [], []
    for label, sel in lod.selections.items():
        ids, fs = [pids[id(p)] for p in sel.points], [fids[id(f)] for f in sel.faces]
        require(len(ids) == 6 and len(fs) == 8, 'component_family')
        pairs = {}
        for i in ids:
            pairs.setdefault(tuple(xyz[i, [0, 2]]), []).append(i)
        require(len(pairs) == 3 and all(len(v) == 2 for v in pairs.values()), 'vertical_pairing')
        top = []
        for pair in pairs.values():
            lo, hi = sorted(pair, key=lambda i: xyz[i, 1])
            require(abs(xyz[hi, 1] - xyz[lo, 1] - 180 / 512) <= 1e-6, 'thickness')
            top.append(hi)
        tri = vertices(lod, [lod.faces[i] for i in fs])
        closure = closed_component(tri)
        require(closure['closed'] and closure['signed_volume'] < 0, 'closed_winding')
        ns = []
        for fi, t in zip(fs, tri):
            face = lod.faces[fi]
            require(len(face.vertices) == 3 and all(v.point_index in ids for v in face.vertices), 'face_membership')
            nids = {v.normal_index for v in face.vertices}
            require(len(nids) == 1, 'normal_mapping')
            ni = next(iter(nids))
            n = np.cross(t[1] - t[0], t[2] - t[0])
            require(np.linalg.norm(n) > 1e-9, 'degenerate_face')
            n /= np.linalg.norm(n)
            require(np.linalg.norm(n - lod.facenormals[ni]) <= 1e-6, 'normal_error')
            require(((xyz[ids] - t[0]) @ n).min() >= -1e-6, 'nonconvex')
            ns.append(ni)
        groups[label] = dict(ids=ids, faces=fs, normals=ns, top=top,
                             polygon=Polygon(xyz[top][:, [0, 2]]))
        used_points += ids
        used_faces += fs
        used_normals += ns
    require(sorted(used_points) == list(range(len(lod.points))) and
            sorted(used_faces) == list(range(len(lod.faces))) and
            sorted(used_normals) == list(range(len(lod.facenormals))), 'unique_assignment')
    require(np.isfinite(xyz).all(), 'nonfinite')
    return xyz, groups

def verify(source, candidate, targets, origin, expected_selection, with_overlay=True):
    oh, ol, ob = load(source)
    nh, nl, nb = load(candidate)
    require(oh == nh == struct.pack('<4sII', b'MLOD', 257, 4), 'mlod_header')
    require(all(ob[i] == nb[i] for i in (0, 2, 3)), 'non_geometry_changed')
    require(len(ob[1]) == len(nb[1]) and ob[1][:28] == nb[1][:28], 'geometry_layout_changed')
    for lod in (ol[1], nl[1]):
        require(struct.unpack_from('<4s6I', ob[1]) ==
                (b'P3DM', 28, 256, len(lod.points), len(lod.facenormals), len(lod.faces), 0), 'lod_layout')
    old, groups = components(ol[1])
    new, newgroups = components(nl[1])
    require(set(groups) == set(newgroups), 'component_set_changed')
    origin = np.asarray(origin, float)
    require(origin.shape == (3,) and np.isfinite(origin).all(), 'origin')
    require(len(targets) > 0 and len({t['id'] for t in targets}) == len(targets), 'target_ids')
    local_targets = [Point(t['x'] - origin[0], t['z'] - origin[2]) for t in targets]
    require(all(np.isfinite([t['x'], t['z']]).all() for t in targets), 'target_finite')
    selected = sorted(k for k, g in groups.items() if any(g['polygon'].distance(t) <= 1 / 512 for t in local_targets))
    require(selected == sorted(expected_selection) and selected, 'selection_mismatch')
    require(np.array_equal(old.min(0), new.min(0)) and np.array_equal(old.max(0), new.max(0)), 'bbox_changed')
    mask = np.zeros(len(ob[1]), bool)
    details = []
    for label in selected:
        g, h = groups[label], newgroups[label]
        require(g['ids'] == h['ids'] and g['faces'] == h['faces'] and g['top'] == h['top'], 'component_members_changed')
        for i in g['ids']:
            mask[28 + 16*i:28 + 16*i + 12] = True
        for i in g['normals']:
            start = 28 + 16*len(old) + 12*i
            mask[start:start + 12] = True
        p, q = old[g['top']], new[g['top']]
        footprint = h['polygon']
        require(footprint.is_valid and footprint.area > g['polygon'].area and
                all(footprint.contains(Point(v[[0, 2]])) for v in p), 'no_strict_expansion')
        # Check the prescribed radial motion by cross product and length;
        # this is not an invocation of the author's transformation.
        radial = p[:, [0, 2]] - p[:, [0, 2]].mean(0)
        move = q[:, [0, 2]] - p[:, [0, 2]]
        lengths = np.linalg.norm(radial, axis=1)
        errors = np.abs(np.linalg.norm(move, axis=1) - lengths / lengths.max() / 512)
        spacing = np.abs(np.spacing(q[:, [0, 2]].astype('<f4')).astype(float))
        quant = np.linalg.norm(spacing / 2, axis=1)
        cross = np.abs(radial[:, 0]*move[:, 1] - radial[:, 1]*move[:, 0])
        require((errors <= quant + 1e-12).all() and
                (cross <= lengths*quant + 1e-12).all() and (np.sum(radial*move, axis=1) > 0).all(), 'operator_outside_contract')
        # Barycentric plane independently reconstructed from source corner vectors.
        u, v = p[1] - p[0], p[2] - p[0]
        ab = np.linalg.solve(np.column_stack((u[[0, 2]], v[[0, 2]])), (q[:, [0, 2]] - p[0, [0, 2]]).T).T
        expected_y = p[0, 1] + ab[:, 0]*u[1] + ab[:, 1]*v[1]
        plane_error = float(np.max(np.abs(q[:, 1] - expected_y)))
        require(plane_error <= 1e-6, 'plane_error')
        for i in h['ids']:
            if i not in h['top']:
                j = next(j for j in h['top'] if np.array_equal(new[i, [0, 2]], new[j, [0, 2]]))
                require(abs(new[i, 1] - (expected_y[h['top'].index(j)] - 180/512)) <= 1e-6, 'base_plane_error')
        slope = np.linalg.solve(np.stack((u[[0, 2]], v[[0, 2]])), [u[1], v[1]])
        rounding_bound = np.abs(np.spacing(q[:, 1].astype('<f4')).astype(float))/2 + (spacing/2) @ np.abs(slope)
        details.append(dict(component=label, plane_error_m=plane_error,
                            predicted_float32_error_bound_m=float(rounding_bound.max()),
                            maximum_radial_move_m=float(np.linalg.norm(move, axis=1).max())))
    a, b = np.frombuffer(ob[1], np.uint8), np.frombuffer(nb[1], np.uint8)
    require(np.array_equal(a[~mask], b[~mask]), 'unauthorized_bytes_changed')
    contacts = []
    for target, pt in zip(targets, local_targets):
        worlds = []
        locals_ = []
        world_point = Point(np.asarray([target['x'], target['z']], '<f4').astype(float))
        for label in selected:
            g = newgroups[label]
            poly = g['polygon']
            if poly.contains(pt):
                locals_.append((poly.boundary.distance(pt), label))
            coords = (new[g['top']][:, [0, 2]] + origin[[0, 2]]).astype('<f4').astype(float)
            world_poly = Polygon(coords)
            if world_poly.is_valid and world_poly.area > 0 and world_poly.contains(world_point):
                worlds.append((world_poly.boundary.distance(world_point), label))
        require(locals_ and worlds, 'contact_not_strict_interior:' + str(target['id']))
        margin, witness = max(worlds)
        ulp = float(np.max(np.abs(np.spacing(np.asarray([target['x'], target['z']], '<f4')))))
        contacts.append(dict(id=target['id'], local_margin_m=max(locals_)[0],
                             world_float32_margin_m=margin, world_ulp_m=ulp, margin_ulps=margin/ulp,
                             witness_component=witness, frame='MLOD_PLUS_ORIGIN_FLOAT32_NOT_ENGINE_CERTIFIED'))
    report = dict(status='OFFLINE_CANDIDATE_ONLY', selected_components=selected,
                  contacts=contacts, components=details, protected_bytes_exact=True,
                  unchanged_other_lods=True, geometry_counts=[len(old), len(ol[1].faces), len(groups)])
    if with_overlay:
        bed = vertices(ol[0], [f for f in ol[0].faces if 'water_streambed.rvmat' not in f.material])
        tri = vertices(nl[1], nl[1].faces)
        normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        roof = tri[normals[:, 1] < -1e-10]
        reference = overlay(bed, bed, vertical_limit=1e-6, horizontal_limit=0.)
        require(all(reference['checks'].values()) and
                max(abs(reference['minimum_pair_height_error_m']), abs(reference['maximum_height_error_m'])) <= 1e-6, 'source_not_single_valued')
        contact = overlay(bed, roof)
        require(all(contact['checks'].values()), 'visual_overlay_failed')
        report.update(overlay=contact, source_self_overlay=reference)
    else:
        report['status'] = 'TEST_ONLY_OVERLAY_NOT_CHECKED'
    return report

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('contract', type=Path)
    ap.add_argument('candidate', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    import water_constraint_diagnostic_ev112 as meter
    args.output.mkdir(exist_ok=False)
    meter.STARTED = STARTED
    meter.MAX_SECONDS = 180
    stop = meter.bounded(args.output)
    try:
        c = json.loads(args.contract.read_bytes())
        require(c['source'] in c['pins'] and c['original_result'] in c['pins'], 'unpinned_core_input')
        for path, digest in c['pins'].items():
            require(meter.sha(path) == digest, 'input_changed:' + path)
        original = json.loads(Path(c['original_result']).read_bytes())
        original_controls(original, c['targets'], c['origin'])
        candidate_sha = meter.sha(args.candidate)
        report = verify(c['source'], args.candidate, c['targets'], c['origin'], c['selected_components'])
        for path, digest in c['pins'].items():
            require(meter.sha(path) == digest, 'input_changed_after:' + path)
        require(meter.sha(args.candidate) == candidate_sha, 'candidate_changed')
        report.update(contract_sha256=meter.sha(args.contract), candidate_sha256=candidate_sha, measurement=meter.memory())
        meter.dump(args.output / 'report.json', report)
        print(json.dumps({k: report[k] for k in ('status', 'contacts', 'measurement')}))
    except ValueError as exc:
        report = dict(status='REJECTED_OFFLINE', reason=str(exc), measurement=meter.memory())
        meter.dump(args.output / 'report.json', report)
        print(json.dumps(report))
        raise SystemExit(1)
    except Exception as exc:
        meter.dump(args.output / 'failure.json', dict(status='INCONCLUSIVE_CONSUMER', error=str(exc), measurement=meter.memory()))
        raise
    finally:
        stop.set()

if __name__ == '__main__':
    sys.path.insert(0, str(HERE))
    main()
