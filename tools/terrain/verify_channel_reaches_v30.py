"""Gate re-check aware of the vanilla channel reaches (BALTIC-015 candidates).

verify_terrain_v30's water_depth and pieces rules, except that the reach cells whose pond planes the channel fit removed
(<fit>/axes.json removed_cells) are judged against the vanilla piece surface instead of a plane that the engine no
longer has: wet vertices touching those cells must lie under a piece, land vertices there must not lie below one.
Usage: verify_channel_reaches_v30.py <terrain npz> <fit dir> <sea_cut> <out json>
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon, box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'terrain'))
sys.path.insert(0, str(ROOT / 'tools' / 'water'))
from v30_common import N, cell_planes  # noqa: E402
import engine_water_model as ewm  # noqa: E402

NARVA = (2417.1428225906, 6889.8850822322)


def retained_pond_faces(fit, manifest, domain):
    """Read actual horizontal faces intersecting the domain; reject unknown poses."""
    sys.path.insert(0, r'C:\Users\guill\DayZ-Modding-Knowledge-Pack\tools\py3d')
    import py3d
    models = {p['name']: p for p in manifest['model_list']}
    cache, result = {}, []
    for pose in manifest['poses']:
        if 'origin' not in pose:
            continue
        if set(pose) - {'model', 'origin', 'band', 'area_m2', 'clipped_from'}:
            raise ValueError('Unsupported retained pond pose; orientation cannot be ignored')
        name = Path(pose['model'].replace('\\', '/')).stem
        model = models[name]
        ox, oy, oz = pose['origin']
        a, b, c, d = model['bounds_rel']
        if not box(ox+a, oz+b, ox+c, oz+d).intersects(domain):
            continue
        if name not in cache:
            path = fit/'water/source/baltic_water_v30'/f'{name}.p3d'
            if hashlib.sha256(path.read_bytes()).hexdigest() != model['sha256']:
                raise ValueError(f'Changed water model: {path}')
            with path.open('rb') as stream:
                p3d = py3d.P3D(stream)
            roadway = [lod for lod in p3d.lods if 2.9e15 < lod.resolution < 3.1e15]
            if len(roadway) != 1:
                raise ValueError(f'Expected one roadway LOD: {path}')
            lod = roadway[0]
            cache[name] = [np.asarray([lod.points[v.point_index].coords for v in f.vertices], dtype=float)
                           for f in lod.faces]
        for xyz in cache[name]:
            if not np.isfinite(xyz).all() or np.ptp(xyz[:, 1]) > 1e-6:
                raise ValueError(f'Invalid horizontal pond face: {name}')
            world = xyz + np.asarray(pose['origin'])
            poly = Polygon(world[:, [0, 2]])
            if not poly.is_valid or poly.area <= 0:
                raise ValueError(f'Invalid pond footprint: {name}')
            if poly.intersects(domain):
                result.append((poly, float(world[0, 1]), pose['model']))
    return result


def check_face_coverage(wet_faces, actual_surface):
    """Area difference, so a hole between 6 m grid vertices cannot disappear."""
    missing = [face.difference(actual_surface) for face in wet_faces]
    missing = [p for p in missing if p.area > 1e-6]
    return dict(fully_wet_native_faces=len(wet_faces), uncovered_faces=len(missing),
                uncovered_area_m2=float(sum(p.area for p in missing)),
                examples=[dict(area_m2=float(p.area), x=float(p.representative_point().x),
                               z=float(p.representative_point().y)) for p in missing[:12]])


def actual_reach_geometry(t, fit, manifest, axes, pieces):
    removed = sorted({tuple(rc) for reach in axes.values() for rc in reach['removed_cells']})
    cells = [box(c*6, 12282-(r+1)*6, (c+1)*6, 12282-r*6) for r, c in removed]
    domain = shapely.union_all(cells)
    # Prove that the matrices being evaluated occur in the built manifest.
    declared = sorted((p['type'], tuple(p['matrix'])) for reach in axes.values() for p in reach['pieces'])
    emitted = sorted((p['type'], tuple(p['matrix'])) for p in manifest['poses'] if 'matrix' in p)
    if declared != emitted:
        raise ValueError('Channel axes and emitted water poses disagree')
    retained = retained_pond_faces(fit, manifest, domain)
    pond_union = shapely.union_all([p[0] for p in retained])
    centers = [dict(row=r, col=c, x=c*6+3, z=12282-r*6-3) for r, c in removed
               if pond_union.covers(shapely.Point(c*6+3, 12282-r*6-3))]
    projections = [p[0] for p in retained]
    for piece in pieces:
        for face in piece.faces:
            poly = Polygon(piece.w[face][:, [0, 2]])
            if poly.area > 1e-9:
                projections.append(poly)
    water_union = shapely.union_all(projections)
    wet_faces = []
    for r, c in removed:
        for dr, dc in ((0, 1), (1, 0)):
            rc = [(r,c), (r+dr,c+dc), (r+1,c+1)]
            if all(t['cls'][u,v] > 0 for u,v in rc):
                wet_faces.append(Polygon([(6*v,12282-6*u) for u,v in rc]))
    coverage = check_face_coverage(wet_faces, water_union)
    return dict(removed_centers_still_under_pond=len(centers), remaining_pond_centers=centers,
                retained_faces=len(retained), manifest_matrices_match=True, coverage=coverage,
                limits=['Projected roadway faces and fully wet native triangles in removed cells only.',
                        'Mixed shore faces still have vertex checks, not complete area/depth certification.',
                        'Source MLOD hashes are checked here; deployed ODOL parity needs a separate receipt.'])


def retained_pond_surface(fit, manifest, x, z):
    """Actual retained roadway faces at a channel junction, not an absent old plane.

    A vertex touching a removed cell may also belong to an adjacent pond. Check
    the authored MLOD and its recorded hash; a bounding-box hit is insufficient.
    """
    sys.path.insert(0, r'C:\Users\guill\DayZ-Modding-Knowledge-Pack\tools\py3d')
    import py3d
    models = {p['name']: p for p in manifest['model_list']}
    best, hits = None, []
    for pose in manifest['poses']:
        if 'origin' not in pose:
            continue  # Vanilla pieces are evaluated by engine_water_model.
        if set(pose) - {'model', 'origin', 'band', 'area_m2', 'clipped_from'}:
            raise ValueError('Unsupported retained pond pose; orientation cannot be ignored')
        name = Path(pose['model'].replace('\\', '/')).stem
        model = models[name]
        ox, oy, oz = pose['origin']
        a, b, c, d = model['bounds_rel']
        if not (ox+a <= x <= ox+c and oz+b <= z <= oz+d):
            continue
        path = fit/'water/source/baltic_water_v30'/f'{name}.p3d'
        if hashlib.sha256(path.read_bytes()).hexdigest() != model['sha256']:
            raise ValueError(f'Changed water model: {path}')
        with path.open('rb') as stream:
            p3d = py3d.P3D(stream)
        roadway = [lod for lod in p3d.lods if 2.9e15 < lod.resolution < 3.1e15]
        if len(roadway) != 1:
            raise ValueError(f'Expected one roadway LOD: {path}')
        lod = roadway[0]
        for face in lod.faces:
            xyz = np.asarray([lod.points[v.point_index].coords for v in face.vertices], dtype=float)
            if np.ptp(xyz[:, 1]) > 1e-6:
                raise ValueError(f'Retained pond is not horizontal: {path}')
            if ewm.inside(xyz[:, [0, 2]], x-ox, z-oz):
                y = float(oy+xyz[0, 1])
                best = y if best is None else max(best, y)
                hits.append(dict(model=pose['model'], sha256=model['sha256'], level_m=y))
                break
    return best, hits


def main():
    path, fit, sea_cut, out = sys.argv[1], Path(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    t = np.load(path)
    h, cls, level = t['heights'].astype(float), t['cls'], t['level'].astype(float)
    axes = json.loads((fit / 'axes.json').read_text(encoding='utf-8'))
    removed = np.zeros((N - 1, N - 1), bool)
    for reach in axes.values():
        for r, c in reach['removed_cells']:
            removed[r, c] = True
    pieces = [ewm.Piece(p['type'], p['matrix']) for reach in axes.values() for p in reach['pieces']]
    c_, r_ = np.meshgrid(np.arange(N), np.arange(N))
    zone = np.hypot(c_ * 6.0 - NARVA[0], 12282 - r_ * 6.0 - NARVA[1]) <= 600
    water = cls > 0
    plane = cell_planes(cls, level, sea_cut=sea_cut)
    plane[removed] = np.nan
    czone = zone[:-1, :-1] | zone[:-1, 1:] | zone[1:, :-1] | zone[1:, 1:]
    rv = np.zeros((N, N), bool)                      # vertices touching a removed reach cell
    for dr in (0, 1):
        for dc in (0, 1):
            rv[dr:dr + N - 1, dc:dc + N - 1] |= removed
    surf = np.full((N, N), np.nan)
    for r, c in zip(*np.nonzero(rv)):
        best = None
        for p in pieces:
            v = p.visual(6.0 * c, 12282.0 - 6.0 * r)
            if v is not None and (best is None or v[0] > best):
                best = v[0]
        if best is not None:
            surf[r, c] = best
    res = {'terrain': path, 'sea_cut': sea_cut, 'removed_cells': int(removed.sum()), 'reach_vertices': int(rv.sum())}
    m = water & ~zone & ~rv
    res['water_depth_fail_outside_reaches'] = int(((level - h) < 0.10)[m].sum())
    wbad = lbad = 0
    for dr in (0, 1):
        for dc in (0, 1):
            hh, ww = h[dr:dr + N - 1, dc:dc + N - 1], water[dr:dr + N - 1, dc:dc + N - 1]
            cov = np.isfinite(plane) & ~czone
            wbad += int((cov & ww & (hh > plane - 0.02)).sum())
            lbad += int((cov & ~ww & (hh < plane)).sum())
    res['pieces_fail_outside_removed_cells'] = {'water_corner': wbad, 'land_corner': lbad}
    under = np.isfinite(surf)
    res['reach_vertices_under_pieces'] = int(under.sum())
    res['reach_wet_depth_below_piece_m_min'] = round(float(np.min((surf - h)[under & water])), 3) if (under & water).any() else None
    res['reach_wet_shallower_than_0_02_under_piece'] = int(((surf - h) < 0.02)[under & water].sum())
    res['reach_land_below_piece_surface'] = int(((h < surf) & under & ~water).sum())
    res['reach_wet_without_piece'] = int((rv & water & ~under).sum())
    # Keep the old count as a vanilla-only diagnostic. Count holes against the
    # union actually built: sloped pieces plus retained horizontal junctions.
    manifest = json.loads((fit/'water/pieces.json').read_text(encoding='utf-8'))
    junctions, missing = [], []
    for r, c in zip(*np.nonzero(rv & water & ~under)):
        y, hits = retained_pond_surface(fit, manifest, 6.0*c, 12282.0-6.0*r)
        row = dict(row=int(r), col=int(c), x=int(6*c), z=int(12282-6*r),
                   ground_m=float(h[r, c]), pond_level_m=y, models=hits)
        if y is None or y-h[r, c] < .02:
            missing.append(row)
        else:
            junctions.append(row)
    res['retained_pond_junctions'] = junctions
    res['reach_wet_without_water_surface'] = len(missing)
    res['missing_water_surface_points'] = missing
    geometry = actual_reach_geometry(t, fit, manifest, axes, pieces)
    res['actual_faces'] = geometry
    # A dry reach vertex must also stay above any retained pond at the junction.
    retained_land = []
    for r, c in zip(*np.nonzero(rv & ~water)):
        y, hits = retained_pond_surface(fit, manifest, 6.0*c, 12282.0-6.0*r)
        if y is not None and h[r,c] < y:
            retained_land.append(dict(row=int(r),col=int(c),ground_m=float(h[r,c]),pond_level_m=y,models=hits))
    res['reach_land_below_retained_pond'] = retained_land
    checks = [res['water_depth_fail_outside_reaches'], wbad, lbad,
              res['reach_wet_shallower_than_0_02_under_piece'], res['reach_land_below_piece_surface'], len(missing),
              len(retained_land), geometry['removed_centers_still_under_pond'], geometry['coverage']['uncovered_faces']]
    res['status'] = 'FAIL' if any(checks) else 'PASS_SCOPED_CHANNEL_WATER_GEOMETRY'
    res['terrain_sha256'] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    res['water_manifest_sha256'] = hashlib.sha256((fit/'water/pieces.json').read_bytes()).hexdigest()
    res['limits'] = ['Scoped vertices and fully wet faces; no global coverage, wave, visual or boat-motion acceptance.',
                     'reach_wet_without_piece is the historical vanilla-only count, not a hole count.']
    Path(out).write_text(json.dumps(res, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(res, indent=1))
    return 2 if any(checks) else 0


if __name__ == '__main__':
    raise SystemExit(main())
