"""Lower bounded wet-bank patches after the independent temporal engine probe.

No water metadata, dry ground, objects or prior reference is rewritten. The
radial patches remain authoring, not proof of engine water or navmesh behavior.
"""
from pathlib import Path
import argparse
import json

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, minimize
from shapely.geometry import shape

from audit_fairway_triangles_v30 import save, sha
from finish_shores_v30 import protect_corridors
from v30_common import cell_planes, grid_xz, raster_vertices, tri_sample, vertex_plane_bounds

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('E:/DayZ-Baltic-Build/v30-watercourse-continuity/terrain_v30.npz')
SOURCE_SHA = '40d8cfd9874e9260464f9e3c38c07d81a15c8aed374083a52c98f042c0161c2e'
REFERENCE = Path('E:/DayZ-Baltic-Build/v30-water-temporal-v2/reference.json')
PARENT_REFERENCE = Path('E:/DayZ-Baltic-Build/v30-continuity-dedup-package/runtime-fixture/reference.json')
DESIGN = ROOT/'tests/water_v3'
NATURE = ROOT/'tests/regional_outline_v1/reference.npz'
IDS = {362, 363, 416, 524, 548, 642, 765, 882, 1176, 1185, 1224, 1274, 1312}
PARAMS = dict(nominal_margin_m=.201, full_radius_m=9., outer_radius_m=24.,
              max_lower_m=.45, altered_bed_depth_max_m=1.20,
              constrained_minimum_margin_m=.181, solver_iterations_max=250)


def retain_dry_and_face_constraints(original, desired, points, parent_reference=PARENT_REFERENCE):
    """Project the radial edit onto frozen dry samples and native face limits.

    scipy definitions verified in installed optimize/_minimize.py:54 and
    _constraints.py:139,253. This solver edits only the existing proposal's
    variables; it cannot recruit dry vertices or a larger neighbourhood.
    """
    ids = np.flatnonzero(desired)
    lookup = {int(v): i for i, v in enumerate(ids)}

    def row_at(x, z):
        c, r = x/6., (12282-z)/6.
        i, j = int(r), int(c)
        fr, fc = r-i, c-j
        corners = [(i,j,1-fc),(i,j+1,fc-fr),(i+1,j+1,fr)] if fc>=fr else [
            (i,j,1-fr),(i+1,j,fr-fc),(i+1,j+1,fc)]
        row = np.zeros(len(ids))
        for a,b,w in corners:
            k = lookup.get(a*2048+b)
            if k is not None:
                row[k] += w
        return row

    rows, lower, upper = [], [], []
    for p in points:
        rows.append(row_at(p['x'], p['z']))
        depth = p['pond_plane_m']-float(tri_sample(original,p['x'],p['z']))
        lower.append(PARAMS['constrained_minimum_margin_m']-depth)
        upper.append(np.inf)
    parent = parent_reference
    for p in json.loads(parent.read_text())['points']:
        if p['kind'] != 'dry':
            continue
        row = row_at(p['x'], p['z'])
        if not row.any():
            continue
        plane = p['pond_plane_m'] if p['pond_plane_m'] is not None else 1.
        rows.append(row)
        lower.append(-np.inf)
        upper.append(p['expected_ground_m']-plane-.05001)
    touched = set()
    for index in ids:
        r,c = divmod(int(index),2048)
        for dr,dc in ((0,0),(-1,0),(0,-1),(-1,-1)):
            if 0<=r+dr<2047 and 0<=c+dc<2047:
                touched.add((r+dr,c+dc))
    dx, dy, gx, gy, ceilings = [], [], [], [], []
    for r,c in sorted(touched):
        for triple in ((r*2048+c,r*2048+c+1,(r+1)*2048+c+1),
                       (r*2048+c,(r+1)*2048+c,(r+1)*2048+c+1)):
            ra,rb,rc = [np.eye(1,len(ids),lookup[v]).ravel() if v in lookup else np.zeros(len(ids)) for v in triple]
            ha,hb,hc = original.ravel()[list(triple)]
            dx.append(rb-ra); dy.append(rc-rb)
            gx.append(hb-ha); gy.append(hc-hb)
            ceilings.append(max((hb-ha)**2+(hc-hb)**2,(6*np.tan(np.radians(35)))**2))
    dx,dy,gx,gy,ceilings = map(np.asarray,(dx,dy,gx,gy,ceilings))
    # Faces without a mutable corner impose constant inequalities, including
    # exactly zero slack on old steep faces. They cannot constrain the edit.
    variable_face = np.any(dx != 0,axis=1) | np.any(dy != 0,axis=1)
    constant_faces = int((~variable_face).sum())
    dx,dy,gx,gy,ceilings = (v[variable_face] for v in (dx,dy,gx,gy,ceilings))
    target = desired.ravel()[ids]
    def slope_margin(v):
        return ceilings-(gx-dx@v)**2-(gy-dy@v)**2
    def slope_jacobian(v):
        return 2*(gx-dx@v)[:,None]*dx+2*(gy-dy@v)[:,None]*dy
    # A read-only LP certificate proved the previous profile is feasible;
    # supply that feasible start instead of the dry-bank-violating radial field.
    matrix = np.asarray(rows)
    count = len(points)
    start = linprog(np.r_[np.zeros(len(target)),-1.],
                    A_ub=np.vstack((np.column_stack((-matrix[:count],np.ones(count))),
                                    np.column_stack((matrix[count:],np.zeros(len(matrix)-count))))),
                    b_ub=np.r_[PARAMS['constrained_minimum_margin_m']-np.asarray(lower[:count]),upper[count:]],
                    bounds=[(0,float(v)) for v in target]+[(None,None)],method='highs')
    if not start.success or start.x[-1] < PARAMS['constrained_minimum_margin_m']:
        raise ValueError(('No linearly feasible shore margin',start.message))
    seed = start.x[:-1]
    if slope_margin(seed).min() < -1e-8:
        raise ValueError('Linear seed violates native face constraints')
    fit = minimize(lambda v: float(np.sum((v-target)**2)), seed,
                   jac=lambda v: 2*(v-target), method='SLSQP',
                   bounds=Bounds(np.zeros_like(target),target),
                   constraints=[LinearConstraint(matrix,lower,upper),
                       dict(type='ineq',fun=slope_margin,jac=slope_jacobian)],
                   options=dict(maxiter=PARAMS['solver_iterations_max'],ftol=1e-12))
    if not fit.success:
        raise ValueError(('Bounded shore constraints did not converge',fit.message))
    result = np.zeros_like(desired)
    result.ravel()[ids] = fit.x
    return result, dict(iterations=int(fit.nit),variables=len(ids),point_constraints=len(rows),
                        face_constraints=len(ceilings),constant_faces_omitted=constant_faces,
                        feasible_start_depth_m=float(start.x[-1]),message=str(fit.message),
                        frozen_dry_reference_sha256=sha(parent))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--constrained', action='store_true')
    ap.add_argument('--source', type=Path, default=SOURCE)
    ap.add_argument('--source-sha', default=SOURCE_SHA)
    ap.add_argument('--reference', type=Path, default=REFERENCE)
    ap.add_argument('--parent-reference', type=Path, default=PARENT_REFERENCE)
    ap.add_argument('--nature', type=Path, default=NATURE)
    ap.add_argument('--design', type=Path, default=DESIGN)
    ap.add_argument('--skip-moved-points', action='store_true',
                    help='leave out the frozen points whose ground is no longer the reference ground (a rebuilt design '
                         'moved the water there) and list them in the report')
    args = ap.parse_args()
    assert not args.out.exists() and (args.source_sha == 'any' or sha(args.source) == args.source_sha)
    reference = json.loads(args.reference.read_text())
    assert args.source_sha == 'any' or reference['terrain_sha256'] == args.source_sha
    points = [p for p in reference['points'] if p['role'] == 'frozen_shallow_failure']
    assert {p['id'] for p in points} == IDS and len(points) == 13
    terrain = np.load(args.source)
    original = terrain['heights'].astype(float)
    moved = []
    if args.skip_moved_points:
        moved = sorted(p['id'] for p in points
                       if abs(float(tri_sample(original, p['x'], p['z']))-p['expected_ground_m']) >= 1e-6)
        points = [p for p in points if p['id'] not in moved]
        assert points, 'Every frozen point moved'
    cls = terrain['cls']
    planes = cell_planes(cls, terrain['level'])
    minimum, _ = vertex_plane_bounds(planes)
    _, corridor, _, corridor_paths = protect_corridors(planes)
    nature_path = args.nature
    nature = np.load(nature_path)['reserve'].astype(bool)
    design_path = args.design/'water_v3.geojson'
    features = json.loads(design_path.read_text(encoding='utf-8'))['features']
    pond_polygons = [shape(features[i]['geometry']) for i in (98, 376, 408, 409)]
    assert all(features[i]['properties']['class'] == 'pond' for i in (98, 376, 408, 409))
    narva_exception = raster_vertices(pond_polygons).astype(bool) & (cls == 7)
    x, z = grid_xz()
    fixed = terrain['platform'] | terrain['reserve'] | terrain['beach'] | nature | corridor
    fixed |= terrain['narva'] & ~narva_exception
    fixed |= (x < 12) | (z < 12) | (x > 12270) | (z > 12270)
    allowed = (cls > 0) & np.isfinite(minimum) & ~fixed
    lowering = np.zeros_like(original)
    domain = np.zeros_like(allowed)
    patches = []
    for p in points:
        distance = np.hypot(x-p['x'], z-p['z'])
        local = allowed & (distance < PARAMS['outer_radius_m'])
        # The already-approved body stays fixed in XY and water level. Do not
        # deepen a different neighbouring water plane through the radial halo.
        local &= np.abs(terrain['level'].astype(float)-p['pond_plane_m']) <= .10
        blend = np.clip((PARAMS['outer_radius_m']-distance) /
                        (PARAMS['outer_radius_m']-PARAMS['full_radius_m']), 0, 1)
        blend = blend**3 * (10 + blend * (-15 + 6*blend))
        blend[~local] = 0
        basis = float(tri_sample(blend, p['x'], p['z']))
        assert basis > 0, (p['id'], 'No mutable wet support in native face')
        ground = float(tri_sample(original, p['x'], p['z']))
        assert abs(ground-p['expected_ground_m']) < 1e-6
        amplitude = max(0., PARAMS['nominal_margin_m']-(p['pond_plane_m']-ground)) / basis
        assert amplitude <= PARAMS['max_lower_m'], (p['id'], amplitude)
        patch = amplitude*blend
        # Preserve deeper existing beds. A vertex is lowered only while its
        # resulting depth remains within the explicit local excavation bound.
        capacity = np.maximum(original-minimum+PARAMS['altered_bed_depth_max_m'], 0)
        patch = np.minimum(patch, np.nan_to_num(capacity, nan=0.))
        lowering = np.maximum(lowering, patch)  # overlapping patches never add
        domain |= local
        patches.append(dict(id=p['id'], x=p['x'], z=p['z'], amplitude_m=amplitude,
                            wet_support_weight=basis, eligible_vertices=int(local.sum())))
    solver = None
    if args.constrained:
        lowering, solver = retain_dry_and_face_constraints(original,lowering,points,args.parent_reference)
    candidate = (original-lowering).astype('float32')
    changed = candidate != terrain['heights']
    assert changed.any() and not (changed & ~domain).any() and not (changed & fixed).any()
    assert not (changed & (cls == 0)).any()
    assert np.all(candidate <= original) and (original-candidate).max() <= .450001
    for p, patch in zip(points, patches):
        patch['ground_before_m'] = float(tri_sample(original, p['x'], p['z']))
        patch['ground_after_m'] = float(tri_sample(candidate, p['x'], p['z']))
        patch['nominal_depth_after_m'] = p['pond_plane_m']-patch['ground_after_m']
        requested = PARAMS['constrained_minimum_margin_m'] if args.constrained else PARAMS['nominal_margin_m']
        assert patch['nominal_depth_after_m'] >= requested-1e-6
    args.out.mkdir(parents=True)
    dest = args.out/'terrain_v30.npz'
    with dest.open('xb') as stream:
        np.savez_compressed(stream, **{k: candidate if k == 'heights' else terrain[k] for k in terrain.files})
    asc = args.out/'baltic_terrain_v30.asc'
    with asc.open('x', encoding='ascii', newline='\n') as stream:
        stream.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(stream, candidate, fmt='%.9g')
    with (args.out/'wave_margin_masks.npz').open('xb') as stream:
        np.savez_compressed(stream, domain=domain, changed=changed, fixed=fixed,
                            narva_exception=narva_exception, source=terrain['heights'][changed],
                            target=candidate[changed], ids=np.flatnonzero(changed))
    report = dict(status='BUILT_PENDING_GROUPED_GATES', params=PARAMS, patches=patches, solver=solver,
                  source_sha256=sha(args.source) if args.source_sha == 'any' else args.source_sha,
                  candidate_sha256=sha(dest), asc_sha256=sha(asc),
                  changed_vertices=int(changed.sum()), max_lower_m=float((original-candidate).max()),
                  inputs={str(p): sha(p) for p in (args.source, args.reference, nature_path, design_path,
                      *corridor_paths, Path(__file__), Path(cell_planes.__code__.co_filename),
                      Path(protect_corridors.__code__.co_filename))},
                  limits=['Local bed authoring only; no whole-map water or visual acceptance.',
                          'No metadata or object change; old frozen findings stay preserved.',
                          'Physical navigation must be regenerated for the changed terrain.'])
    if args.skip_moved_points:
        report['moved_points_skipped'] = moved
    save(args.out/'build.json', report)
    print(json.dumps({k: report[k] for k in ('status', 'changed_vertices', 'max_lower_m',
                                           'candidate_sha256', 'asc_sha256')}, indent=2))


if __name__ == '__main__':
    main()
