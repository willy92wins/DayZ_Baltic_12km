"""Visible streambed proxy water at world 1 m pixel centres (row 0 north).

Reads the actual staged f32 object poses and the extracted vanilla water faces.
Terrain burial is evaluated on the native NW-SE triangles by the caller. This
mask supplies water context; existing full object hulls retain exact exclusions.
"""
import numpy as np


def rasterize(objects, models, heights, terrain_height):
    mask = np.zeros((12288, 12288), dtype=bool)
    pieces = triangles = 0
    for obj in objects:
        name = obj['name'].replace('/', '\\').lower()
        if '\\streambed\\streambed_' not in name or 'stones' in name:
            continue
        key = name.rsplit('\\', 1)[1][len('streambed_'):-4]
        geom = models[key]  # unknown streambed model fails closed
        matrix = np.asarray(obj['matrix'], dtype=float)
        if matrix.shape != (12,) or not np.isfinite(matrix).all() or not geom['water']:
            raise ValueError('invalid streambed pose or empty water geometry: ' + name)
        rotation, translation = matrix[:9].reshape(3, 3).T, matrix[9:]
        pieces += 1
        for face in geom['water']:
            vertices = np.asarray(face, dtype=float) @ rotation.T + translation
            if len(vertices) < 3 or not np.isfinite(vertices).all():
                raise ValueError('invalid water face: ' + name)
            for k in range(1, len(vertices) - 1):
                v = vertices[[0, k, k + 1]]
                xmin, zmin = v[:, [0, 2]].min(axis=0)
                xmax, zmax = v[:, [0, 2]].max(axis=0)
                c0, c1 = max(0, int(np.floor(xmin))), min(12282, int(np.ceil(xmax)))
                r0, r1 = max(6, int(np.floor(12288-zmax))), min(12288, int(np.ceil(12288-zmin)))
                if c1 <= c0 or r1 <= r0:
                    continue
                X, Z = np.meshgrid(np.arange(c0, c1)+.5, 12288-np.arange(r0, r1)-.5)
                a, b, c = v[:, [0, 2]]
                ab, ac = b-a, c-a
                det = ab[0]*ac[1]-ab[1]*ac[0]
                if abs(det) < 1e-12:
                    continue
                u = ((X-a[0])*ac[1]-(Z-a[1])*ac[0])/det
                w = (ab[0]*(Z-a[1])-ab[1]*(X-a[0]))/det
                inside = (u >= -1e-9) & (w >= -1e-9) & (u+w <= 1+1e-9)
                level = v[0,1]+u*(v[1,1]-v[0,1])+w*(v[2,1]-v[0,1])
                ground = terrain_height(heights, X, Z)
                mask[r0:r1, c0:c1] |= inside & (level > ground)
                triangles += 1
    return mask, dict(pieces=pieces, triangles=triangles, visible_pixels=int(mask.sum()))
