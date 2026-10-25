"""Classify fixed rays against packed float32 triangles; diagnostic, not engine acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Point, Polygon


def classify(triangles, x, z):
    point = Point(float(np.float32(x)), float(np.float32(z)))
    q = np.array(point.coords[0])
    ulp = float(max(abs(np.spacing(np.float32(v))) for v in q))
    contacts = []
    nearest_vertex = float('inf')
    for tri in triangles:
        p = np.asarray(tri, dtype=np.float32).astype(float)
        nearest_vertex = min(nearest_vertex, float(np.linalg.norm(p[:, [0, 2]]-q, axis=1).min()))
        polygon = Polygon(p[:, [0, 2]])
        if polygon.area <= 1e-12 or not polygon.covers(point):
            continue
        normal = np.cross(p[1]-p[0], p[2]-p[0])
        if abs(normal[1]) <= 1e-8 * np.linalg.norm(normal):
            continue  # Almost vertical faces do not provide a stable height diagnostic.
        y = p[0, 1] - (normal[0]*(q[0]-p[0, 0])+normal[2]*(q[1]-p[0, 2])) / normal[1]
        contacts.append((float(y), float(polygon.boundary.distance(point))))
    if not contacts:
        return dict(classification='outside', world_ulp_m=ulp, nearest_vertex_xz_m=nearest_vertex)
    top = max(y for y, _ in contacts)
    top_clearance = max(d for y, d in contacts if abs(y-top) <= 1e-7)
    return dict(classification='interior_one_ulp' if top_clearance >= ulp else 'boundary_or_sub_ulp',
                top_y_m=top, top_triangle_best_edge_clearance_m=top_clearance,
                world_ulp_m=ulp, nearest_vertex_xz_m=nearest_vertex, intersected_triangles=len(contacts))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('pilot', type=Path)
    ap.add_argument('records', type=Path)
    ap.add_argument('targets', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--reader-root', required=True)
    args = ap.parse_args()
    sys.path.insert(0, args.reader_root)
    from odol_reader import ODOL
    import odol_reader
    records = {r['model'].split('\\')[-1]: r for r in json.loads(args.records.read_text())}
    targets = json.loads(args.targets.read_text())
    results = []
    for name, rays in targets.items():
        assert Path(name).name == name and '\\' not in name
        path = args.pilot/'temp/baltic_stream_pilot'/name
        od = ODOL.from_file(str(path), strict=True)
        assert not getattr(od, 'lod_errors', {}) and len(od.lods) == 4
        geo = min(od.lods, key=lambda l: abs(l.resolution-1e13))
        for section in geo.sections:
            assert -1 <= section.texture_index < len(geo.textures)
            assert -1 <= section.material_index < len(geo.materials)
        matrix = records[name]['matrix']
        assert matrix[:9] == [1,0,0,0,1,0,0,0,1]
        xyz = (np.array([(v.x,v.y,v.z) for v in geo.vertices])+matrix[9:]).astype(np.float32)
        triangles = []
        for face in geo.faces:
            ids = list(face.vertex_indices)
            assert len(ids) == 3, 'Only triangle geometry is supported by this diagnostic'
            triangles.append(xyz[ids])
        for ray in rays:
            results.append(dict(model=name, point_id=ray['id'], odol_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                **classify(triangles, ray['x'], ray['z'])))
    report = dict(status='DIAGNOSTIC_ONLY', results=results,
                  records_sha256=hashlib.sha256(args.records.read_bytes()).hexdigest(),
                  targets_sha256=hashlib.sha256(args.targets.read_bytes()).hexdigest(),
                  reader_sha256=hashlib.sha256(Path(odol_reader.__file__).read_bytes()).hexdigest(),
                  limitation='Float32 triangle geometry; does not establish the internal RV intersection algorithm or client contact.')
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
