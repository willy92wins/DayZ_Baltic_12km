"""Candidate horizontal Minkowski overlap for identified RV vertex misses.

Only Geometry changes. This author is not an acceptance verifier; run the saved
collision overlay, compiled-model verifier and unchanged server probe afterwards.
"""
if not __debug__:
    raise RuntimeError('Authoring requires assertions enabled')
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np
from scipy.spatial import ConvexHull
from shapely.geometry import MultiPoint, Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_compact_collision_v31 import load, py3d
from compact_stream_collision_v31 import add_component


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expanded_component(points, half_side=1 / 512):
    """Convex hull of four translated copies; original hull is contained."""
    p = np.asarray(points, float)
    if p.ndim != 2 or p.shape[1] != 3 or not np.isfinite(p).all():
        raise ValueError('Finite 3D component points required')
    offsets = np.array([[-half_side, 0, -half_side], [-half_side, 0, half_side],
                        [half_side, 0, -half_side], [half_side, 0, half_side]])
    cloud = np.unique((p[:, None] + offsets).reshape(-1, 3), axis=0)
    hull = ConvexHull(cloud)
    used = hull.vertices
    inverse = np.full(len(cloud), -1, int)
    inverse[used] = np.arange(len(used))
    return dict(points=cloud[used], faces=inverse[hull.simplices], volume=float(hull.volume))


def selected_components(lod, targets, origin, *, minimal_bbox_anchors=False, contact_only=False):
    """Contact footprints plus four bbox extrema keep the existing WRP centre."""
    xyz = np.array([p.coords for p in lod.points])
    lo, hi = xyz[:, [0, 2]].min(0), xyz[:, [0, 2]].max(0)
    chosen = {}
    anchors = {}
    if minimal_bbox_anchors and contact_only:
        raise ValueError('Contact-only selection cannot request bbox anchors')
    if minimal_bbox_anchors:
        for axis in range(2):
            for side, extreme in (('min', lo[axis]), ('max', hi[axis])):
                eligible = []
                for label, selection in lod.selections.items():
                    values = np.array([v.coords for v in selection.points])[:, [0, 2]][:, axis]
                    if np.any(values == extreme):
                        eligible.append((len(selection.points), label))
                assert eligible, 'Missing bounding-box anchor'
                anchors[min(eligible)[1]] = True
    for label, selection in lod.selections.items():
        p = np.array([v.coords for v in selection.points])[:, [0, 2]]
        reasons = []
        if not contact_only and (label in anchors if minimal_bbox_anchors else
                np.any(p.min(0) == lo) or np.any(p.max(0) == hi)):
            reasons.append('bbox_extremum')
        footprint = MultiPoint(p + np.array(origin)[[0, 2]]).convex_hull
        if any(footprint.distance(Point(t['x'], t['z'])) <= 1 / 512 for t in targets):
            reasons.append('contact_footprint')
        if reasons:
            chosen[label] = reasons
    assert any('contact_footprint' in why for why in chosen.values())
    return chosen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--models', nargs='+', required=True)
    parser.add_argument('--expected-author-sha256', required=True)
    parser.add_argument('--contact-targets', type=Path,
                        help='Optional model-keyed world XZ targets; expand local components and bbox anchors only')
    parser.add_argument('--minimal-bbox-anchors', action='store_true',
                        help='Use the smallest component at each bbox extremum instead of the whole perimeter')
    parser.add_argument('--contact-only', action='store_true',
                        help='Expand contact components only; reject any change to existing geometry bounds')
    args = parser.parse_args()
    original, output = args.original, args.output
    assert sha(original / 'author-report.json') == args.expected_author_sha256
    author = json.loads((original / 'author-report.json').read_text())
    # These pilots are authored in local axes and deployed by translation only.
    records = json.loads((original / 'records.json').read_text())
    assert {r['model'] for r in records} == {i['model'] for i in author['instances']}
    assert all(r['matrix'][:9] == [1,0,0,0,1,0,0,0,1] for r in records), 'Rotated pilots unsupported'
    requested = set(args.models)
    assert len(requested) == len(args.models)
    assert all(Path(name).name == name and '/' not in name and '\\' not in name
               for name in requested)
    assert requested <= {i['model'].split('\\')[-1] for i in author['instances']}
    targets = json.loads(args.contact_targets.read_text()) if args.contact_targets else None
    if args.contact_only and (targets is None or args.minimal_bbox_anchors):
        parser.error('--contact-only requires targets and excludes --minimal-bbox-anchors')
    if targets is not None:
        assert set(targets) == requested
        assert all(v and all(np.isfinite([t['x'], t['z']]).all() for t in v) for v in targets.values())
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(original / 'source/baltic_stream_pilot',
                    output / 'source/baltic_stream_pilot')
    for path in original.glob('*-surfaces.npz'):
        shutil.copyfile(path, output / path.name)
    cache = output / 'geometry-cache'
    cache.mkdir()
    reports = []
    for inst in author['instances']:
        name = inst['model'].split('\\')[-1]
        source = original / 'source/baltic_stream_pilot' / name
        assert sha(source) == inst['sha256']
        if name not in requested:
            continue
        header, lods, blobs = load(source)
        old = lods[1]
        assert py3d.classify_lod_resolution(old.resolution) == 'geometry'
        chosen = (selected_components(old, targets[name], inst['origin'],
                                      minimal_bbox_anchors=args.minimal_bbox_anchors,
                                      contact_only=args.contact_only) if targets is not None
                  else {label: ['whole_model'] for label in old.selections})
        geo = py3d.LOD()
        geo.resolution = old.resolution
        geo.properties.update(old.properties)
        volumes = []
        mass_before = mass_after = 0.
        for index, (label, selection) in enumerate(old.selections.items(), 1):
            assert label == f'Component{index:04d}'
            points = list(selection.points)
            points_before = len(geo.points)
            xyz = np.array([p.coords for p in points])
            if label in chosen:
                part = expanded_component(xyz)
            else:
                lookup = {p: i for i, p in enumerate(points)}
                faces = np.array([[lookup[v.point] for v in f.vertices] for f in selection.faces])
                assert faces.shape[1] == 3
                part = dict(points=xyz, faces=faces, volume=float(ConvexHull(xyz).volume))
            volumes.append(add_component(py3d, geo, part, index))
            mass = sum(p.mass for p in points)
            each = mass / (len(geo.points) - points_before)
            for i, p in enumerate(geo.points[points_before:]):
                p.mass = each if label in chosen else points[i].mass
            mass_before += mass
            mass_after += each * (len(geo.points) - points_before)
        one = py3d.P3D()
        one.lods.append(geo)
        temp = cache / (name + '.geometry')
        one.save(str(temp))
        new_data = header + blobs[0] + temp.read_bytes()[12:] + blobs[2] + blobs[3]
        dest = output / 'source/baltic_stream_pilot' / name
        dest.write_bytes(new_data)
        _, saved, saved_blobs = load(dest)
        assert all(saved_blobs[i] == blobs[i] for i in (0, 2, 3))
        old_xyz = np.array([p.coords for p in old.points])
        new_xyz = np.array([p.coords for p in saved[1].points])
        delta_min = new_xyz.min(0) - old_xyz.min(0)
        delta_max = new_xyz.max(0) - old_xyz.max(0)
        assert np.array_equal(delta_min, [0, 0, 0] if args.contact_only else [-1/512, 0, -1/512])
        assert np.array_equal(delta_max, [0, 0, 0] if args.contact_only else [1/512, 0, 1/512])
        assert len(saved[1].selections) == inst['collision_components']
        assert abs(mass_before - mass_after) < 1e-6
        for label, original_selection in old.selections.items():
            before_mass = sum(p.mass for p in original_selection.points)
            after_mass = sum(p.mass for p in saved[1].selections[label].points)
            assert abs(before_mass - after_mass) <= max(1e-6, abs(before_mass)*1e-6)
            if label not in chosen:
                np.testing.assert_array_equal([p.coords for p in original_selection.points],
                                              [p.coords for p in saved[1].selections[label].points])
        reports.append(dict(model=name, components=len(geo.selections),
                            expanded_components=chosen,
                            before_faces=len(old.faces), after_faces=len(geo.faces),
                            before_bytes=source.stat().st_size, after_bytes=len(new_data),
                            geometry_bbox_centre_exact=True, non_geometry_lods_byte_exact=True,
                            mass_before=mass_before, mass_after=mass_after))
        inst['sha256'] = sha(dest)
        inst['signed_collision_volume'] = float(sum(volumes))
    assert len(reports) == len(requested)
    (output / 'author-report.json').write_text(json.dumps(author, indent=2) + '\n')
    report = dict(status='CANDIDATE_REQUIRES_INDEPENDENT_OVERLAY_BINARY_AND_ENGINE',
                  half_side_m=1/512, maximum_horizontal_displacement_m=2**.5/512,
                  minimal_bbox_anchors=args.minimal_bbox_anchors,
                  contact_only=args.contact_only,
                  models=reports, unchanged_models=len(author['instances'])-len(reports),
                  original_author_sha256=args.expected_author_sha256,
                  contact_targets_sha256=sha(args.contact_targets) if args.contact_targets else None,
                  script_sha256=sha(__file__))
    (output / 'overlap-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
