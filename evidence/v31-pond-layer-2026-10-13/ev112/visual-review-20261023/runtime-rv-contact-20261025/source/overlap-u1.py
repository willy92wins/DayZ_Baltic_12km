"""Candidate horizontal Minkowski overlap for identified RV vertex misses.

Only Geometry changes. This author is not an acceptance verifier; run the saved
collision overlay, compiled-model verifier and unchanged server probe afterwards.
"""
if not __debug__:
    raise RuntimeError('Authoring requires assertions enabled')
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys

import numpy as np
from scipy.spatial import ConvexHull

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--models', nargs='+', required=True)
    parser.add_argument('--expected-author-sha256', required=True)
    args = parser.parse_args()
    original, output = args.original, args.output
    assert sha(original / 'author-report.json') == args.expected_author_sha256
    author = json.loads((original / 'author-report.json').read_text())
    requested = set(args.models)
    assert len(requested) == len(args.models)
    assert all(Path(name).name == name and '/' not in name and '\\' not in name
               for name in requested)
    assert requested <= {i['model'].split('\\')[-1] for i in author['instances']}
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
        geo = py3d.LOD()
        geo.resolution = old.resolution
        geo.properties.update(old.properties)
        volumes = []
        mass_before = mass_after = 0.
        for index, (label, selection) in enumerate(old.selections.items(), 1):
            assert label == f'Component{index:04d}'
            points = list(selection.points)
            points_before = len(geo.points)
            part = expanded_component([p.coords for p in points])
            volumes.append(add_component(py3d, geo, part, index))
            mass = sum(p.mass for p in points)
            each = mass / (len(geo.points) - points_before)
            for p in geo.points[points_before:]:
                p.mass = each
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
        assert np.array_equal(delta_min, [-1/512, 0, -1/512])
        assert np.array_equal(delta_max, [1/512, 0, 1/512])
        assert len(saved[1].selections) == inst['collision_components']
        assert abs(mass_before - mass_after) < 1e-6
        reports.append(dict(model=name, components=len(geo.selections),
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
                  models=reports, unchanged_models=len(author['instances'])-len(reports),
                  original_author_sha256=args.expected_author_sha256,
                  script_sha256=sha(__file__))
    (output / 'overlap-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
