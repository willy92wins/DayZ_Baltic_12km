"""B3 author: fixed triangular dilation, Geometry XYZ/normals only; no acceptance."""
import os
import time
STARTED = time.monotonic()
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[_key] = '1'
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'water'))
from review_compact_collision_v31 import load
from overlap_stream_collision_v31 import selected_components

DELTA = 1 / 512
THICKNESS = 180 / 512

def require(ok, reason):
    if not bool(ok):
        raise ValueError(reason)

def dilate(points):
    """Strict six-point vertical prism, retaining indices; result already float32."""
    p = np.asarray(points, float)
    require(p.shape == (6, 3) and np.isfinite(p).all(), 'prism_shape')
    pairs = {}
    for i, v in enumerate(p):
        pairs.setdefault(tuple(v[[0, 2]]), []).append(i)
    require(len(pairs) == 3 and all(len(v) == 2 for v in pairs.values()), 'vertical_pairs')
    pairs = [sorted(v, key=lambda i: p[i, 1]) for v in pairs.values()]
    top = [b for a, b in pairs]
    require(all(p[b, 1] - p[a, 1] == THICKNESS for a, b in pairs), 'prism_thickness')
    xz = p[top][:, [0, 2]]
    plane = np.linalg.solve(np.column_stack((xz, np.ones(3))), p[top, 1])
    centre = xz.mean(0)
    radius = np.linalg.norm(xz - centre, axis=1).max()
    require(radius > 0, 'zero_radius')
    expanded = (centre + (1 + DELTA / radius) * (xz - centre)).astype('<f4')
    result = p.copy()
    for (a, b), q in zip(pairs, expanded):
        y = np.float32(np.dot(plane, [*q, 1]))
        result[[a, b], 0] = q[0]
        result[[a, b], 2] = q[1]
        result[b, 1] = y
        result[a, 1] = np.float32(float(y) - THICKNESS)
    return result.astype('<f4')

def author(source, targets, origin):
    header, lods, blobs = load(source)
    require(header == struct.pack('<4sII', b'MLOD', 257, 4), 'mlod_header')
    lod = lods[1]
    require(struct.unpack_from('<4s6I', blobs[1]) ==
            (b'P3DM', 28, 256, len(lod.points), len(lod.facenormals), len(lod.faces), 0), 'lod_layout')
    selected = selected_components(lod, targets, origin, contact_only=True)
    pidx = {id(p): i for i, p in enumerate(lod.points)}
    fidx = {id(f): i for i, f in enumerate(lod.faces)}
    xyz = np.array([p.coords for p in lod.points])
    new = xyz.copy()
    allowed_points, allowed_faces = set(), set()
    for label in selected:
        group = lod.selections[label]
        ids = [pidx[id(p)] for p in group.points]
        fs = [fidx[id(f)] for f in group.faces]
        require(len(ids) == 6 and len(fs) == 8, 'unsupported_component')
        require(not allowed_points.intersection(ids) and not allowed_faces.intersection(fs), 'shared_component_members')
        new[ids] = dilate(xyz[ids])
        allowed_points.update(ids)
        allowed_faces.update(fs)
    output = bytearray(blobs[1])
    for i in sorted(allowed_points):
        struct.pack_into('<3f', output, 28 + 16 * i, *new[i])
    normals_seen = set()
    for fi in sorted(allowed_faces):
        face = lod.faces[fi]
        require(len(face.vertices) == 3, 'nontriangle')
        ns = {v.normal_index for v in face.vertices}
        require(len(ns) == 1 and not normals_seen.intersection(ns), 'normal_sharing')
        ni = next(iter(ns))
        normals_seen.add(ni)
        t = new[[v.point_index for v in face.vertices]]
        n = np.cross(t[1] - t[0], t[2] - t[0])
        require(np.linalg.norm(n) > 1e-9, 'degenerate_face')
        n /= np.linalg.norm(n)
        struct.pack_into('<3f', output, 28 + 16 * len(lod.points) + 12 * ni, *n)
    blobs[1] = bytes(output)
    return header + b''.join(blobs), dict(status='WRITTEN_PENDING_INDEPENDENT_CONSUMER',
        selected_components=sorted(selected), changed_points=len(allowed_points), changed_faces=len(allowed_faces))

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('contract', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    import water_constraint_diagnostic_ev112 as meter
    args.output.mkdir(exist_ok=False)
    meter.STARTED = STARTED
    meter.MAX_SECONDS = 60
    stop = meter.bounded(args.output)
    try:
        c = json.loads(args.contract.read_bytes())
        require(c['source'] in c['pins'], 'unpinned_source')
        for path, digest in c['pins'].items():
            require(meter.sha(path) == digest, 'input_changed:' + path)
        blob, report = author(Path(c['source']), c['targets'], c['origin'])
        require(report['selected_components'] == sorted(c['selected_components']), 'selection_changed')
        target = args.output / 'candidate.p3d'
        target.write_bytes(blob)
        report.update(source_sha256=meter.sha(c['source']), candidate_sha256=meter.sha(target),
                      contract_sha256=meter.sha(args.contract), measurement=meter.memory())
        for path, digest in c['pins'].items():
            require(meter.sha(path) == digest, 'input_changed_after:' + path)
        meter.dump(args.output / 'report.json', report)
        print(json.dumps(report))
    except Exception as exc:
        meter.dump(args.output / 'failure.json', dict(status='INCONCLUSIVE_AUTHOR', error=str(exc), measurement=meter.memory()))
        raise
    finally:
        stop.set()

if __name__ == '__main__':
    sys.path.insert(0, str(HERE))
    main()
