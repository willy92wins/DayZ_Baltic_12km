#!/usr/bin/env python
"""Independent offline EV90 consumer. No solver, author import, or map writes."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import traceback
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box, shape

Q = Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010')
HERE = Q/'next-method-consumer'
PRE_DIR = Q/'next-method-preflight'
PRE = PRE_DIR/'preflight.json'
PRE_SCRIPT = PRE_DIR/'ev90_preflight.py'
PLAN = Q/'next-method-plan.md'
AUTHOR_DIR = Q/'ev90-author'
CANDIDATE = AUTHOR_DIR/'candidate-terrain.npz'
RECEIPT = AUTHOR_DIR/'authoring.json'
AUTHOR_SOURCE = AUTHOR_DIR/'author_ev90.py'

ROOT = Path(r'E:/DayZ-Baltic-Build')
EV88_PATH = Q/'review-independent/verify_ev88q.py'
EV87_PATH = ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
CV_PATH = ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_coverage_contract.py'
CV_POLICY = ROOT/'v30-global-strict-bank-relief-20261010/coverage-contract-proposal.md'
SHAPE_PATH = HERE/'shape_contract.py'
FIXTURE_PATH = HERE/'test_ev90_consumer.py'

PINNED = {
    str(PLAN): '3bde2ce8460f6374830f8ec4ca302e06b7c9a904f36c8778826799ffd6cdd7ea',
    str(PRE_SCRIPT): '5892e917335ca2d8caa427f04f48ba8acbd8e16a5e1b400be596d5dd636afb7f',
    str(PRE): '8c8ec80cbb7029f510c832adf90a8871e385fbd8ec52ee5043d5ea24e1099d63',
    str(AUTHOR_SOURCE): 'c8ee41f14c332bf9a5849ee7a6454e82043ccc5e06a866bd018df817f819ad7e',
    str(EV88_PATH): '82a988790e6bdfc0289bcb7c32cb0afd1210e07b264d92731aba266bc5980f78',
    str(EV87_PATH): '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
    str(CV_PATH): '214f0eddda08d84ce18c921fcdbE01298f608c9a5c19b7e5246bb9e71df5dc2b'.lower(),
    str(CV_POLICY): '6964ca97226512764720eb1a25f41ab65e191cfda318ea07ad39bb1f4c0b6463',
    str(SHAPE_PATH): '8cd9d0fbea03c05e5ae53a31676d79ec2364be83c055213446f6c8599245d533',
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def load_pinned(name, path, wanted):
    got = sha(path)
    if got != wanted:
        raise AssertionError(f'pinned helper changed: {path}: {got} != {wanted}')
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot load helper {path}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def inward32_lower(value):
    x = float(value)
    v = np.float32(x)
    if not np.isfinite(v):
        raise ValueError('non-finite lower bound')
    if float(v) < x:
        v = np.nextafter(v, np.float32(np.inf))
    if float(v) < x:
        raise AssertionError('float32 lower bound did not round inward')
    return float(v)


def inward32_upper(value):
    x = float(value)
    v = np.float32(x)
    if not np.isfinite(v):
        raise ValueError('non-finite upper bound')
    if float(v) > x:
        v = np.nextafter(v, np.float32(-np.inf))
    if float(v) > x:
        raise AssertionError('float32 upper bound did not round inward')
    return float(v)


def _rings(geom):
    parts = [geom] if geom.geom_type == 'Polygon' else list(getattr(geom, 'geoms', []))
    for part in parts:
        if part.geom_type != 'Polygon' or part.is_empty:
            continue
        yield np.asarray(part.exterior.coords[:-1], dtype=np.float64)
        for ring in part.interiors:
            yield np.asarray(ring.coords[:-1], dtype=np.float64)


def _max_affine(coeff, points, geom):
    values = geom.eval_affine(coeff, np.asarray(points, dtype=np.float64))
    return float(np.max(values))


def local_cells(ev):
    r0, r1, c0, c1 = ev.WINDOW
    return {(r, c) for r in range(r0, r1-1) for c in range(c0, c1-1)}


def scan_compiled_fields(ev, geom, bundle):
    """Rebuild nominal above/unknown cell sets from the pinned WRP and exact ODOL LODs."""
    cells = local_cells(ev)
    wrp, objects, models, model_hashes = geom.compiled_objects(
        ev.B_WRP, ev.W, cells, ev.MODEL_DIR, ev.BOUNDS)
    p, f = bundle['P'], bundle['F']
    above = {'physical': set(), 'visible': set()}
    unknown = {'physical': set(), 'visible': set()}
    records = {'physical': [], 'visible': []}
    face_cell_tests = {'physical': 0, 'visible': 0}
    faces_seen = {'physical': 0, 'visible': 0}
    target = {'physical': float(np.float32(3e15)), 'visible': float(np.float32(1.0))}
    r0, r1, c0, c1 = ev.WINDOW
    for obj, matrix, _bounds in objects:
        name = obj['name'].replace('\\', '/').split('/')[-1]
        model = models[name]
        tx, ty, tz = map(float, matrix[9:12])
        for kind, resolution in target.items():
            lods = [x for x in model.lods if x.resolution == resolution]
            if len(lods) != 1:
                raise AssertionError(f'nonunique {kind} LOD for {name}')
            lod = lods[0]
            faces_seen[kind] += len(lod.faces)
            verts = lod.vertices
            for face_index, face in enumerate(lod.faces):
                ids = list(face.vertex_indices)
                if len(ids) != 3:
                    raise AssertionError(f'non-triangle compiled face {name}:{face_index}')
                xyz = np.asarray([[verts[i].x+tx, verts[i].y+ty, verts[i].z+tz] for i in ids], dtype=np.float64)
                xz = xyz[:, (0, 2)]
                poly = Polygon(xz)
                if not poly.is_valid:
                    raise AssertionError(f'invalid face polygon {name}:{face_index}')
                if poly.area <= 1e-12:
                    continue
                face_coeff = geom.affine_coeff(xz, xyz[:, 1])
                xmin, zmin = xz.min(axis=0)
                xmax, zmax = xz.max(axis=0)
                cr0 = max(c0, int(math.floor(xmin/ev.CELL)))
                cr1 = min(c1-2, int(math.floor(np.nextafter(xmax, -math.inf)/ev.CELL)))
                rr0 = max(r0, int(math.floor((ev.Z0-zmax)/ev.CELL)))
                rr1 = min(r1-2, int(math.floor(np.nextafter(ev.Z0-zmin, -math.inf)/ev.CELL)))
                for r in range(rr0, rr1+1):
                    for c in range(cr0, cr1+1):
                        cell = (r, c)
                        if cell not in cells:
                            continue
                        cellpoly = box(c*ev.CELL, ev.Z0-(r+1)*ev.CELL,
                                       (c+1)*ev.CELL, ev.Z0-r*ev.CELL)
                        overlap = poly.intersection(cellpoly)
                        if overlap.is_empty or overlap.area <= 0.0:
                            continue
                        face_cell_tests[kind] += 1
                        if kind == 'physical':
                            level = float(p[r, c])
                            if not math.isfinite(level):
                                unknown[kind].add(cell)
                                records[kind].append({'cell': cell, 'face': face_index, 'object': name,
                                    'triangle': None, 'reason': 'P_nan', 'face_coeff': face_coeff,
                                    'intersection': overlap})
                                continue
                            if _max_affine(face_coeff, [pt for ring in _rings(overlap) for pt in ring], geom)-level > 1e-5:
                                above[kind].add(cell)
                        else:
                            xy = geom.cell_xy(r, c)
                            for ti, tri in enumerate(ev.TRIS):
                                tri_ids = np.asarray(tri, dtype=int)
                                piece = overlap.intersection(Polygon(xy[tri_ids]))
                                if piece.is_empty or piece.area <= 0.0:
                                    continue
                                fv = np.asarray(f[r, c, tri_ids], dtype=np.float64)
                                if not np.isfinite(fv).all():
                                    unknown[kind].add(cell)
                                    records[kind].append({'cell': cell, 'face': face_index, 'object': name,
                                        'triangle': ti, 'reason': 'F_unknown', 'face_coeff': face_coeff,
                                        'intersection': piece})
                                    continue
                                field_coeff = geom.affine_coeff(xy[tri_ids], fv)
                                pts = [pt for ring in _rings(piece) for pt in ring]
                                if _max_affine(face_coeff-field_coeff, pts, geom) > 2e-5:
                                    above[kind].add(cell)
    return {'above': above, 'unknown': unknown, 'unknown_records': records,
            'objects': len(objects), 'models': len(models), 'model_hashes': model_hashes,
            'face_cell_tests': face_cell_tests, 'faces_seen': faces_seen,
            'wrp_objects': len(wrp['objects'])}


def p9_unknown_cells(ev, bundle):
    data = bundle['corridors']
    p = bundle['P']
    cells = set()
    by_feature = []
    r0, r1, c0, c1 = ev.WINDOW
    local = local_cells(ev)
    for index, feature in enumerate(data['features']):
        geom = shape(feature['geometry'])
        hits = []
        area = 0.0
        for r, c in sorted(local):
            if np.isfinite(p[r, c]):
                continue
            cell = box(c*ev.CELL, ev.Z0-(r+1)*ev.CELL, (c+1)*ev.CELL, ev.Z0-r*ev.CELL)
            piece = geom.intersection(cell)
            if not piece.is_empty and piece.area > 0.0:
                hits.append((r, c)); area += float(piece.area)
        if hits:
            cells.update(hits)
            by_feature.append({'feature_index': index,
                'river': feature.get('properties', {}).get('river'),
                'unknown_cells_rc': [list(x) for x in hits], 'intersection_area_m2': area})
    return cells, by_feature


def partial_f_cells(ev, bundle):
    f = bundle['F']
    out = set()
    for r, c in local_cells(ev):
        vals = np.asarray(f[r, c], dtype=np.float64)
        for tri in ev.TRIS:
            count = int(np.isfinite(vals[list(tri)]).sum())
            if 0 < count < 3:
                out.add((r, c))
    return out


def cell_vertices(cell):
    r, c = map(int, cell)
    return ((r,c),(r,c+1),(r+1,c),(r+1,c+1))


def classify_f_triangle(samples):
    finite = int(np.isfinite(np.asarray(samples, dtype=np.float64)).sum())
    return 'known' if finite == 3 else 'all_nan' if finite == 0 else 'partial'


def affine_clearance(face_values, ground_values, barycentric_weights):
    """Clearance of affine face/ground at one point in a triangle."""
    w=np.asarray(barycentric_weights,dtype=np.float64)
    face=np.asarray(face_values,dtype=np.float64);ground=np.asarray(ground_values,dtype=np.float64)
    if w.shape!=(3,) or np.any(w<0.0) or not np.isclose(float(w.sum()),1.0,rtol=0.0,atol=1e-14):
        raise ValueError('barycentric weights must be nonnegative and sum to one')
    if face.shape!=(3,) or ground.shape!=(3,) or not np.isfinite(face).all() or not np.isfinite(ground).all():
        raise ValueError('finite affine triangle vertex heights required')
    return float(w @ (ground-face))


def reconstruct_domain(ev, bundle, scan, p9_cells, partial_cells):
    base = ev.reconstruct_domain(bundle)
    base_vars = [tuple(map(int, x)) for x in base['variables']]
    freeze_cells = set().union(*scan['above'].values()) | set(p9_cells) | set(partial_cells)
    r0, r1, c0, c1 = ev.CORE
    frozen_nodes = set()
    for r, c in freeze_cells:
        for node in ((r,c),(r,c+1),(r+1,c),(r+1,c+1)):
            if r0 <= node[0] < r1 and c0 <= node[1] < c1:
                frozen_nodes.add(node)
    variables = [node for node in base_vars if node not in frozen_nodes]
    expected_nodes = [tuple(map(int, x)) for x in json.loads(PRE.read_text(encoding='utf-8'))
                      ['domain_and_bound_analysis']['eligible_after_face_freeze_nodes']]
    if variables != expected_nodes:
        raise AssertionError(f'preflight mutable-node reconstruction differs: {len(variables)} vs {len(expected_nodes)}')
    if len(variables) != 85:
        raise AssertionError(f'EV90 domain size changed: {len(variables)}')
    lower_raw = np.asarray(base['lower'], dtype=np.float64).copy()
    upper_raw = np.asarray(base['upper'], dtype=np.float64).copy()
    # The existing EV88 helper returns node bounds in the 13x13 CORE coordinates.
    for r, c in variables:
        ir, ic = r-r0, c-c0
        lower_raw[ir,ic] = inward32_lower(lower_raw[ir,ic])
        upper_raw[ir,ic] = inward32_upper(upper_raw[ir,ic])
    base.update({'variables': np.asarray(variables, dtype=np.int32),
                 'variables_set': set(variables), 'frozen_cells': freeze_cells,
                 'frozen_nodes': frozen_nodes, 'lower': lower_raw, 'upper': upper_raw,
                 'above_cells': scan['above'], 'unknown_cells': scan['unknown'],
                 'p9_unknown_cells': set(p9_cells), 'partial_f_cells': set(partial_cells)})
    base['stencils'] = ev.stencil_records(variables=variables)
    base['collar_stencils'] = [x for x in base['stencils'] if x['collar']]
    base['variables_sha256_le_i32'] = hashlib.sha256(np.asarray(variables, dtype='<i4').tobytes()).hexdigest()
    return base


def reconstruct_bounds(ev, bundle, domain):
    cross = ev.reconstruct_crossings(bundle, domain)
    lower, upper = cross['lower'], cross['upper']
    cr0, cr1, cc0, cc1 = ev.CORE
    for r, c in domain['variables_set']:
        i, j = r-cr0, c-cc0
        lower[i,j] = inward32_lower(lower[i,j])
        upper[i,j] = inward32_upper(upper[i,j])
    if np.any(lower > upper):
        raise AssertionError('crossing constraints yield an empty float32 interval')
    cross['lower'], cross['upper'] = lower, upper
    return cross


def _ground_coeff_for(geom, heights, r, c, tri):
    xy = geom.cell_xy(r,c); ids = np.asarray(tri, dtype=int)
    vals = geom.corner_values(heights, r, c)[ids]
    return geom.affine_coeff(xy[ids], vals)


def certify_unknown_faces(ev, geom, bundle, scan, domain, candidate=None):
    b = np.asarray(bundle['B']['heights'], dtype=np.float64)
    h = b if candidate is None else np.asarray(candidate, dtype=np.float64)
    lower = domain['lower']; cr0, cr1, cc0, cc1 = ev.CORE
    lower_global = {}
    for r, c in domain['variables_set']:
        lower_global[(r,c)] = float(lower[r-cr0,c-cc0])
    results = {'physical': [], 'visible': []}
    unresolved = []
    for kind, records in scan['unknown_records'].items():
        for rec in records:
            r,c = rec['cell']; tri_id = rec['triangle']
            if kind == 'physical':
                # P is constant per cell; split over the native triangles for an affine certificate.
                tri_ids = range(len(ev.TRIS))
            else:
                tri_ids = (tri_id,)
            for ti in tri_ids:
                tri = ev.TRIS[ti]; ids = np.asarray(tri, dtype=int)
                xy = geom.cell_xy(r,c)[ids]
                piece = rec['intersection']
                if kind == 'physical':
                    piece = piece.intersection(Polygon(xy))
                    if piece.is_empty or piece.area <= 0.0:
                        continue
                points = [pt for ring in _rings(piece) for pt in ring]
                if not points:
                    continue
                face = rec['face_coeff']
                by_state = {}
                for label, heights in (('B', b), ('candidate', h)):
                    g = _ground_coeff_for(geom, heights, r, c, tri)
                    min_clear = float(np.min(geom.eval_affine(g, points)-geom.eval_affine(face, points)))
                    by_state[label] = min_clear
                # The lower envelope uses L32 for mutable nodes and B for every fixed node.
                corner_h = geom.corner_values(b, r, c).astype(np.float64)
                for k in tri:
                    node = (r+geom.CORNER_OFFSETS[k][0], c+geom.CORNER_OFFSETS[k][1])
                    if node in lower_global:
                        corner_h[k] = lower_global[node]
                gmin = geom.affine_coeff(xy, corner_h[ids])
                min_l32 = float(np.min(geom.eval_affine(gmin, points)-geom.eval_affine(face, points)))
                item = {'cell': [r,c], 'object': rec['object'], 'face': rec['face'],
                    'native_triangle': int(ti), 'reason': rec['reason'],
                    'min_clearance_m': by_state, 'min_clearance_L32_m': min_l32,
                    'area_m2': float(piece.area)}
                results[kind].append(item)
                p9_exact = False
                if kind == 'physical' and (r,c) in domain['p9_unknown_cells']:
                    p9_exact = all(np.array_equal(h[tuple(node)], b[tuple(node)])
                                   for node in cell_vertices((r,c)))
                item['p9_unknown_preserved_exact_B'] = p9_exact
                if p9_exact:
                    continue
                if by_state['B'] < 0.0 or by_state['candidate'] < 0.0 or min_l32 < 0.0:
                    unresolved.append(item)
    return {'by_kind': results, 'unresolved': unresolved}


def verify_preflight(ev, bundle):
    report = json.loads(PRE.read_text(encoding='utf-8'))
    if report.get('status') != 'PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW':
        raise AssertionError(f'preflight not ready: {report.get("status")}')
    if report.get('pins', {}).get('preflight_script_sha256') != sha(PRE_SCRIPT):
        raise AssertionError('preflight script pin mismatch')
    if report.get('pins', {}).get('next_method_plan_sha256') != sha(PLAN):
        raise AssertionError('preflight plan pin mismatch')
    geom = load_pinned('ev90_preflight_ev87', EV87_PATH, PINNED[str(EV87_PATH)])
    scan = scan_compiled_fields(ev, geom, bundle)
    expected_above = report['cell_classification']['above_P_or_F_by_kind']
    expected_unknown = report['cell_classification']['unknown_field_overlap_by_kind']
    for kind in ('physical','visible'):
        if sorted(map(list, scan['above'][kind])) != expected_above[kind]:
            raise AssertionError(f'{kind} high-face cell inventory differs from pinned preflight')
        if sorted(map(list, scan['unknown'][kind])) != expected_unknown[kind]:
            raise AssertionError(f'{kind} unknown-face cell inventory differs from pinned preflight')
    if scan['objects'] != report['compiled_scan']['selected_object_count'] or scan['models'] != report['compiled_scan']['selected_models']:
        raise AssertionError('compiled WRP object/model local inventory differs from preflight')
    if scan['face_cell_tests'] != report['compiled_scan']['positive_area_face_cell_tests']:
        raise AssertionError('compiled face/cell test counts differ from preflight')
    for path, digest in report['inputs_sha256'].items():
        if sha(path) != digest:
            raise AssertionError(f'preflight input hash changed: {path}')
    p9, p9_detail = p9_unknown_cells(ev, bundle)
    partial = partial_f_cells(ev, bundle)
    domain = reconstruct_domain(ev, bundle, scan, p9, partial)
    crossing = reconstruct_bounds(ev, bundle, domain)
    expected = report['domain_and_bound_analysis']
    bounds_by_node = {tuple(x['node_rc']): x['interval_float32_inward_m']
                      for x in expected['final_float32_intervals_for_eligible_nodes']}
    for r,c in domain['variables_set']:
        actual = [float(crossing['lower'][r-ev.CORE[0],c-ev.CORE[2]]),
                  float(crossing['upper'][r-ev.CORE[0],c-ev.CORE[2]])]
        if actual != list(map(float,bounds_by_node[(r,c)])):
            raise AssertionError(f'float32 crossing interval mismatch at {(r,c)}: {actual} vs {bounds_by_node[(r,c)]}')
    if p9 != {tuple(x) for x in report['cell_classification']['P9_unknown_cells_preserved']}:
        raise AssertionError('P9 unknown-cell set differs from preflight')
    unknown_cert = certify_unknown_faces(ev=ev, geom=geom, bundle=bundle, scan=scan,
                                         domain=domain, candidate=None)
    if unknown_cert['unresolved']:
        raise AssertionError('compiled faces in unknown fields fail B/L32 burial certificate')
    if report['unknown_field_lower_envelope_checks']['unresolved']:
        raise AssertionError('preflight lists unresolved unknown-field faces')
    return {'report': report, 'scan': scan, 'domain': domain, 'crossings': crossing,
            'p9_unknown_by_feature': p9_detail, 'unknown_certificate': unknown_cert}


def verify_authoring_receipt(receipt_path, candidate_path, pre):
    rec = json.loads(Path(receipt_path).read_text(encoding='utf-8'))
    if rec.get('status') != 'AUTHORED_PENDING_INDEPENDENT_CONSUMER':
        raise AssertionError('author receipt status is not pending independent consumer')
    if Path(rec.get('candidate_path','')).resolve() != Path(candidate_path).resolve():
        raise AssertionError('author receipt candidate path mismatch')
    digest = sha(candidate_path)
    if rec.get('candidate_sha256') != digest:
        raise AssertionError('author receipt candidate hash mismatch')
    if rec.get('preflight_sha256') != sha(PRE) or rec.get('plan_sha256') != sha(PLAN):
        raise AssertionError('author receipt not bound to exact current preflight and plan')
    pins = rec.get('source_pins', {})
    required = dict(pre['report']['inputs_sha256'])
    required.update({str(PRE): sha(PRE), str(PLAN): sha(PLAN), str(PRE_SCRIPT): sha(PRE_SCRIPT),
                     str(AUTHOR_SOURCE): PINNED[str(AUTHOR_SOURCE)]})
    if any(pins.get(k) != v for k,v in required.items()):
        raise AssertionError('author receipt source pins differ from independent source set')
    solver = rec.get('solver', {})
    if solver.get('method') != 'scipy.optimize.lsq_linear/BVLS' or solver.get('calls') != 1:
        raise AssertionError('receipt does not identify the single planned BVLS call')
    if solver.get('success') is not True or solver.get('status') != 1 or solver.get('hard_timeout_s') != 120:
        raise AssertionError(f'BVLS receipt not successful: {solver}')
    return rec


def candidate_representation(candidate_path, bundle, domain, crossings, receipt):
    with np.load(candidate_path, allow_pickle=False) as z:
        candidate = {k: z[k] for k in z.files}
    base = bundle['B']
    if set(candidate) != set(base):
        raise AssertionError(f'candidate array key set differs from B: {set(candidate)^set(base)}')
    h32 = np.asarray(candidate['heights'])
    b32 = np.asarray(base['heights'])
    if h32.shape != (2048,2048) or h32.dtype != np.float32 or not np.isfinite(h32).all():
        raise AssertionError('candidate heights must be finite float32 2048x2048')
    for key in set(base)-{'heights'}:
        if not np.array_equal(candidate[key], base[key], equal_nan=True):
            raise AssertionError(f'candidate changed non-height source field {key}')
    changed = np.argwhere(h32 != b32)
    changed_rc = [tuple(map(int,x)) for x in changed]
    variables = domain['variables_set']
    changes_inside_domain = all(x in variables for x in changed_rc)
    if not changes_inside_domain:
        raise AssertionError('candidate changed a protected, collar, or non-domain vertex')
    if len(changed_rc) != int(receipt.get('changed_vertices', -1)):
        raise AssertionError('author receipt changed-vertex count mismatch')
    cr0,cr1,cc0,cc1 = (834,847,364,377)
    lower,upper=crossings['lower'],crossings['upper']
    h64=h32.astype(np.float64)
    bounds_pass = True
    for r,c in variables:
        value=float(h32[r,c]);lo=float(lower[r-cr0,c-cc0]);hi=float(upper[r-cr0,c-cc0])
        if not lo <= value <= hi:
            bounds_pass = False
            raise AssertionError(f'exact float32 bound violation at {(r,c)}: {value} not in [{lo},{hi}]')
    return candidate, h32, changed_rc, {'changes_inside_domain':changes_inside_domain,'bounds_pass':bounds_pass}


def verify_high_cells_unchanged(ev, h32, b32, pre):
    scan = pre['scan']; protected = set().union(*scan['above'].values())
    nodes=set()
    r0,r1,c0,c1=ev.CORE
    for r,c in protected:
        for node in ((r,c),(r,c+1),(r+1,c),(r+1,c+1)):
            if r0<=node[0]<r1 and c0<=node[1]<c1:
                nodes.add(node)
    bad=[list(x) for x in sorted(nodes) if h32[x] != b32[x]]
    return {'pass':not bad,'cells':len(protected),'vertices':len(nodes),'changed_vertices':bad}


def _violation_key(v):
    return (v['kind'], tuple(v['cell']), int(v['triangle']), v['object'], tuple(v['face_indices']))


def compare_face_violations(bad_pair):
    """Do not promote inherited B violations; reject new or numerically worse H faces."""
    from collections import defaultdict
    old=defaultdict(list);new=defaultdict(list)
    for v in bad_pair.get('B',[]):old[_violation_key(v)].append(v)
    for v in bad_pair.get('candidate',[]):new[_violation_key(v)].append(v)
    regressions=[]
    for key,items in new.items():
        before=sorted(old.get(key,[]),key=lambda x:(x['area_m2'],x['max_excess_m']))
        after=sorted(items,key=lambda x:(x['area_m2'],x['max_excess_m']))
        if len(after)>len(before):
            regressions.extend({'reason':'new_face_violation','key':list(key),'candidate':v} for v in after[len(before):])
            continue
        for bv,hv in zip(before,after):
            if hv['area_m2']>bv['area_m2'] or hv['max_excess_m']>bv['max_excess_m']:
                regressions.append({'reason':'existing_face_violation_worsened','key':list(key),
                                    'baseline':bv,'candidate':hv})
    return {'pass':not regressions,'baseline_count':len(bad_pair.get('B',[])),
            'candidate_count':len(bad_pair.get('candidate',[])),
            'new_or_worsened':regressions}


def coverage_contract_ev90(ev, ev87, cv, hb, hh, bundle, changed_rc, source_hashes, frozen_cells):
    """EV88 coverage computation with EV90's inherited-defect/non-regression contract.

    The only acceptance-policy change from the pinned helper is replacing its
    absolute `not bad_height` gate with a per-face B/H no-new-or-worse comparison;
    all area, support, unknown-F, bounds-inventory, and PBO checks retain the
    pinned helper predicates.
    """
    p=bundle['P'];f=bundle['F'];cells=ev87._ev87_cells(changed_rc)
    unknown_masks,unknown_totals=cv.classify_unknown_f(hb,hh,f)
    scan_cells=cells|unknown_masks['changed_cells']
    bounds=cv.validate_bounds_inventory(ev.B_WRP,ev.BOUNDS,ev.W)
    if not bounds['name_xz_rotation_bounds_exact']:
        raise AssertionError('compiled WRP water inventory differs from pinned bounds/names/XZ/rotation')
    exp_pair,support,meta,bad_pair,unknown_static=cv.exposed_pair_and_support(
        hb,hh,p,f,scan_cells,ev.B_WRP,ev.W,ev.MODEL_DIR,ev.BOUNDS,unknown_masks)
    pbo=ev87.pbo_guard(ev.B_DEPLOY,ev.B_WRP)
    if not all(pbo[k] for k in ('expected_world_exact','expected_water_exact',
        'deployed_oprw_matches_manifest','staged_source_wrp_identity_exact',
        'source_and_compiled_payload_are_distinct_artifacts')):
        raise AssertionError(f'compiled WRP/PBO identity guard failed: {pbo}')
    gates={}
    changed_partial=int(unknown_totals.get('changed_partial',0))
    uncertain=int(unknown_static.get('with_contact_or_exposed_or_unproven_intersection',0))
    gates['no_changed_partial_F_triangles']=changed_partial==0
    gates['unknown_F_changed_faces_absent_or_buried_in_B_and_H']=uncertain==0
    violation_comparison=compare_face_violations(bad_pair)
    gates['no_new_or_worsened_compiled_face_height_violation']=violation_comparison['pass']
    metrics={};designs={}
    for kind,field in (('physical','physical'),('visible','visible')):
        designB=cv.make_design(hb,p,f,cells,field);designH=cv.make_design(hh,p,f,cells,field)
        designs[kind]={'B':designB,'H':designH}
        holes={'B':[],'H':[]}
        for r,c in sorted(cells):
            support_poly=support[kind][(r,c)]
            if field=='visible':
                xy=cv.cell_xy(r,c);known=[]
                for tri in cv.TRIS:
                    if np.isfinite(f[r,c,np.asarray(tri,dtype=int)]).all():known.append(Polygon(xy[list(tri)]))
                from shapely.ops import unary_union
                known_domain=unary_union(known) if known else Polygon()
                dB=designB[(r,c)].intersection(known_domain);dH=designH[(r,c)].intersection(known_domain)
            else:dB=designB[(r,c)];dH=designH[(r,c)]
            holes['B'].append(float(dB.difference(support_poly).area));holes['H'].append(float(dH.difference(support_poly).area))
        holes_pass=cv.coverage_holes_pass(holes['B'],holes['H'])
        residualB=cv.design_and_residual(hb,p,f,cells,field,exp_pair['B'][kind],designB)
        residualH=cv.design_and_residual(hh,p,f,cells,field,exp_pair['candidate'][kind],designH)
        residual_pass=all(residualB[k]<=cv.AREA_LIMIT and residualH[k]<=cv.AREA_LIMIT for k in
            ('missing_outside_band_total_m2','missing_outside_band_max_cell_m2',
             'growth_outside_band_total_m2','growth_outside_band_max_cell_m2'))
        by_side={side:[x for x in violations if x['kind']==kind] for side,violations in bad_pair.items()}
        gates[f'{kind}_nominal_footprint_supported_le_1e_7m2']=holes_pass
        gates[f'{kind}_compiled_residual_outside_height_band_le_0_002m2']=residual_pass
        metrics[kind]={'support_hole_total_m2':{'B':sum(holes['B']),'H':sum(holes['H'])},
            'support_hole_max_cell_m2':{'B':max(holes['B'],default=0.0),'H':max(holes['H'],default=0.0)},
            'exposure_residual_B':residualB,'exposure_residual_H':residualH,
            'height_violation_count':{side:len(vals) for side,vals in by_side.items()},
            'height_violation_examples':{side:vals[:25] for side,vals in by_side.items()}}
    gates['no_new_partial_or_unresolved_face_exposure']=changed_partial==0 and uncertain==0
    for model_name,digest in meta.get('model_hashes',{}).items():
        model_path=ev.MODEL_DIR/model_name;actual=sha(model_path)
        if actual!=digest:raise AssertionError(f'compiled water model changed during ODOL scan: {model_name}')
        source_hashes[str(model_path)]=actual
    frozen_nodes=set()
    r0,r1,c0,c1=ev.CORE
    for r,c in frozen_cells:
        for node in cell_vertices((r,c)):
            if r0<=node[0]<r1 and c0<=node[1]<c1:frozen_nodes.add(node)
    return {'gates':gates,'metrics':metrics,'unknown_F':unknown_totals,
        'unknown_face_intersections':unknown_static,'face_violation_nonregression':violation_comparison,
        'scanned_cells':len(scan_cells),'changed_support_cells':len(cells),
        'frozen_high_and_corridor_cells':len(frozen_cells),'frozen_nodes':len(frozen_nodes),
        'compiled':meta,'bounds_inventory':bounds,'pbo_guard':pbo,
        'absolute_inherited_height_violations':{'B':len(bad_pair.get('B',[])),
            'candidate':len(bad_pair.get('candidate',[]))}}


def affected_corridor_depth_report(ev, ev87, bundle, h, changed_rc):
    """Exact nominal P depth on P-known corridor triangles intersecting changed support cells."""
    from shapely.geometry import shape
    p=bundle['P'];changed_cells=ev87._ev87_cells(changed_rc);out=[]
    for fi,feature in enumerate(bundle['corridors']['features']):
        geom=shape(feature['geometry']);rows=[];unknown_area=0.0
        for r,c in sorted(changed_cells):
            xy=ev87.cell_xy(r,c)
            cell=box(c*ev.CELL,ev.Z0-(r+1)*ev.CELL,(c+1)*ev.CELL,ev.Z0-r*ev.CELL)
            if not geom.intersects(cell):continue
            corridor_cell=geom.intersection(cell)
            if corridor_cell.is_empty or corridor_cell.area<=0:continue
            level=float(p[r,c])
            for ti,tri in enumerate(ev.TRIS):
                ids=np.asarray(tri,dtype=int);tri_poly=Polygon(xy[ids])
                part=corridor_cell.intersection(tri_poly)
                if part.is_empty or part.area<=1e-12:continue
                if not math.isfinite(level):
                    unknown_area+=float(part.area);continue
                values=ev87.corner_values(h,r,c)[ids]
                depth=ev.triangle_depth_min(part,xy[ids],values,level)
                rows.append({'cell':[r,c],'triangle':ti,'area_m2':float(part.area),
                    'minimum_nominal_depth_m':depth})
        depths=[x['minimum_nominal_depth_m'] for x in rows if x['minimum_nominal_depth_m'] is not None]
        out.append({'feature_index':fi,'river':feature.get('properties',{}).get('river'),
            'affected_known_triangles':len(rows),'affected_known_area_m2':sum(x['area_m2'] for x in rows),
            'minimum_affected_nominal_depth_m':min(depths) if depths else None,
            'affected_unknown_P_area_m2':unknown_area,'triangles':rows})
    tested=[x['minimum_affected_nominal_depth_m'] for x in out if x['minimum_affected_nominal_depth_m'] is not None]
    return {'pass':all(x>=.95 for x in tested),'tested_known_triangles':sum(x['affected_known_triangles'] for x in out),
        'features_with_affected_known_support':sum(x['affected_known_triangles']>0 for x in out),
        'minimum_affected_known_depth_m':min(tested) if tested else None,
        'unknown_area_in_changed_corridor_support_m2':sum(x['affected_unknown_P_area_m2'] for x in out),
        'by_feature':out,
        'scope':'Only known-P native triangles in corridor geometry intersecting cells incident to changed vertices.'}


def minimum_context_report(before, after, new_minima):
    b=np.asarray(before,dtype=np.float32);h=np.asarray(after,dtype=np.float32);out=[]
    for r,c in new_minima:
        nbr=[]
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr or dc:
                    nbr.append({'rc':[r+dr,c+dc],'B_m':float(b[r+dr,c+dc]),'H_m':float(h[r+dr,c+dc])})
        out.append({'rc':[r,c],'B_m':float(b[r,c]),'H_m':float(h[r,c]),'neighbors':nbr,
            'minimum_margin_H_m':float(min(x['H_m'] for x in nbr)-h[r,c])})
    return out


def p9_unknown_preserved(local_exact, corridor_rows):
    rows=corridor_rows.get('corridors',[])
    corridor_exact=all(
        (row.get('unknown_P_area_changed_between_pair_m2') or 0.0) <= 1e-12 and
        row.get('unknown_P_max_triangle_vertex_delta_m') == 0.0
        for row in rows)
    return {'pass':bool(local_exact and corridor_exact),
            'local_unknown_cell_corners_exact_B':bool(local_exact),
            'all_corridor_unknown_area_and_triangle_corners_exact_B':bool(corridor_exact),
            'features':len(rows)}


def evaluate(candidate_path=CANDIDATE, receipt_path=RECEIPT):
    source_hashes={str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
    source_hashes[str(FIXTURE_PATH)]=sha(FIXTURE_PATH)
    for path,want in PINNED.items():
        got=sha(path)
        if got!=want:raise AssertionError(f'consumer source/input pin mismatch: {path}: {got} != {want}')
        source_hashes[path]=got
    ev=load_pinned('ev88_ev90_helpers',EV88_PATH,PINNED[str(EV88_PATH)])
    bundle=ev.checked_sources()
    source_hashes.update(bundle['hashes'])
    source_hashes[str(PRE)]=sha(PRE);source_hashes[str(PRE_SCRIPT)]=sha(PRE_SCRIPT);source_hashes[str(PLAN)]=sha(PLAN)
    source_hashes[str(AUTHOR_SOURCE)]=sha(AUTHOR_SOURCE)
    pre=verify_preflight(ev,bundle)
    receipt=verify_authoring_receipt(receipt_path,candidate_path,pre)
    source_hashes[str(candidate_path)]=sha(candidate_path);source_hashes[str(receipt_path)]=sha(receipt_path)
    candidate, h32, changed_rc, representation=candidate_representation(candidate_path,bundle,pre['domain'],pre['crossings'],receipt)
    b32=np.asarray(bundle['B']['heights']); b=b32.astype(np.float64); h=h32.astype(np.float64)
    ev87=ev.import_file('ev90_frozen_ev87',EV87_PATH)
    cv=ev.import_file('ev90_frozen_coverage',CV_PATH);cv.ev=ev87
    if sha(EV87_PATH)!=PINNED[str(EV87_PATH)] or sha(CV_PATH)!=PINNED[str(CV_PATH)]:
        raise AssertionError('frozen geometry/coverage helper changed after import')
    domain=pre['domain'];cross=pre['crossings'];cells=ev87._ev87_cells(changed_rc)
    high=verify_high_cells_unchanged(ev,h32,b32,pre)
    topology=ev.topology_check(ev87,b,h,bundle['P'],bundle['F'],cells)
    stencil_b,_=ev.stencil_energy(b,domain['stencils']);stencil_h,_=ev.stencil_energy(h,domain['stencils'])
    collar_b,_=ev.stencil_energy(b,domain['collar_stencils']);collar_h,_=ev.stencil_energy(h,domain['collar_stencils'])
    shape=load_pinned('ev90_shape_contract',SHAPE_PATH,PINNED[str(SHAPE_PATH)])
    shape_result=shape.evaluate_shape(b32,h32,ev.WINDOW,(840,370))
    local_b=ev.local_mesh_angles(b,(840,370),radius=2);local_h=ev.local_mesh_angles(h,(840,370),radius=2)
    focus_hinge=local_b['max_incident_hinge_deg']-local_h['max_incident_hinge_deg']>=2.0
    collar_mask=np.ones((ev.WINDOW[1]-ev.WINDOW[0],ev.WINDOW[3]-ev.WINDOW[2]),dtype=bool)
    r0,r1,c0,c1=ev.WINDOW;cr0,cr1,cc0,cc1=ev.CORE
    collar_mask[cr0-r0:cr1-r0,cc0-c0:cc1-c0]=False
    tb=np.asarray(b[r0:r1,c0:c1]);th=np.asarray(h[r0:r1,c0:c1])
    ab=dict(ev87.edge_angles(tb));ah=dict(ev87.edge_angles(th));collar_angles={}
    for kind in ab:
        mask=ev87.incident_any(collar_mask,kind)
        vb=ab[kind][mask];vh=ah[kind][mask]
        collar_angles[kind]={'count':int(vb.size),'B_max_deg':float(vb.max()) if vb.size else None,
            'H_max_deg':float(vh.max()) if vh.size else None,
            'nonworse':not vb.size or float(vh.max())<=float(vb.max())+1e-4}
    global_geom=ev.local_sector_stats(ev87,b,h,changed_rc)
    p99=ev.p99_population_gate(ev87,global_geom['angles_b'],global_geom['angles_h'],bundle)
    del global_geom['angles_b'];del global_geom['angles_h']
    corridor_b=ev.corridor_depth_report(b,bundle['P'],bundle['corridors'],comparison=h)
    corridor_h=ev.corridor_depth_report(h,bundle['P'],bundle['corridors'],comparison=b)
    bed=ev.high_bed_floor_report(h,bundle['B'])
    corridor_affected=affected_corridor_depth_report(ev,ev87,bundle,h,changed_rc)
    corridor_geometry_covered = all(x['coverage_error_m2'] <= 1e-5 for x in corridor_h['corridors'])
    sources={}
    compiled=coverage_contract_ev90(ev,ev87,cv,b,h,bundle,changed_rc,sources,domain['frozen_cells'])
    # Verify unknown compiled faces across every preflight face/cell intersection on B and H.
    unknown_certificate=certify_unknown_faces(ev=ev, geom=ev87, bundle=bundle,
        scan=pre['scan'], domain=domain, candidate=h)
    # Static all-NaN P9 is exact B globally because only 85 local nodes can change and local P9 nodes are frozen.
    p9_vertices=set()
    for r,c in domain['p9_unknown_cells']:
        p9_vertices.update(((r,c),(r,c+1),(r+1,c),(r+1,c+1)))
    p9_exact=all(np.array_equal(h32[n],b32[n]) for n in p9_vertices)
    p9_preserved=p9_unknown_preserved(p9_exact,corridor_h)
    gates={
        'high_field_excess_cells_four_corners_exact_B':high['pass'],
        'all_candidate_changes_inside_reconstructed_float32_domain':representation['changes_inside_domain'],
        'exact_float32_EV79_and_crossing_bounds':representation['bounds_pass'],
        'P9_unknown_cells_exact_B':p9_preserved['pass'],
        'compiled_unknown_faces_buried_in_B_H_and_L32':not unknown_certificate['unresolved'],
        'known_layer_signs_and_crossings_preserved':topology['signs_preserved'] and topology['crossings_valid_and_within_1m'],
        'shape_contract':all(shape_result['gates'].values()),
        'focus_max_incident_hinge_reduced_2deg':focus_hinge,
        'fixed_stencil_energy_reduced_25pct':stencil_h<=.75*stencil_b,
        'collar_stencil_energy_nonworse':collar_h<=collar_b+1e-12,
        'collar_hinge_maxima_nonworse':all(x['nonworse'] for x in collar_angles.values()),
        'global_slopes_hinges_and_sectors_nonworse':global_geom['slopes_le_max35_or_B'] and global_geom['no_new_hinges_over_30_touched'] and global_geom['affected_sector_max_nonworse'],
        'global_bank_interior_p99_and_counts_nonworse':p99['pass'],
        'all_19_corridors_geometry_covered':corridor_geometry_covered,
        'affected_known_P_corridor_triangles_min_depth_ge_0_95m':corridor_affected['pass'],
        'all_P_unknown_corridor_area_exact_B':p9_preserved['all_corridor_unknown_area_and_triangle_corners_exact_B'],
        'high_navigable_bed_floor_1m':bed['high_bed_floor_1m_pass'],
    }
    gates.update(compiled['gates'])
    # Preserve absolute inherited failures as separate evidence, not hidden false gates.
    report={
        'status':'PASS_EV90_OFFLINE_CONSUMER' if all(gates.values()) else 'FAIL_EV90_OFFLINE_CONSUMER',
        'gates':{k:bool(v) for k,v in gates.items()},
        'information':{
            'candidate_sha256':sha(candidate_path),'changed_vertices':len(changed_rc),'changed_vertices_rc':changed_rc,
            'representation_checks':representation,
            'mutable_vertices':len(domain['variables_set']),'high_cell_exactness':high,
            'shape_contract':shape_result,'focus_hinge_deg':{'B':local_b['max_incident_hinge_deg'],'H':local_h['max_incident_hinge_deg']},
            'stencil_energy':{'B':stencil_b,'H':stencil_h,'collar_B':collar_b,'collar_H':collar_h},
            'collar_hinges':collar_angles,'global_geometry':global_geom,'p99':p99,
            'p99_population_scope':'Existing EV87 bank/interior populations; excludes 65,955 eligible wet-support nodes (2.21%); not whole-map or all-eligible-node p99.',
            'corridor_depth':{'B':corridor_b,'H':corridor_h},'affected_corridor_depth':corridor_affected,
            'high_bed_floor':bed,
            'unknown_face_certificate':unknown_certificate,'compiled_representation':compiled,
            'p9_unknown_global':{'unknown_cells_local':len(domain['p9_unknown_cells']),
                'unknown_area_by_feature_B':corridor_b['corridors'],'unknown_area_by_feature_H':corridor_h['corridors'],
                **p9_preserved},
            'inherited_open_status':'FAIL_WITH_INHERITED_OPEN',
            'new_minimum8_context':minimum_context_report(b32,h32,shape_result['new_minima8']),
            'runtime_limit':'Static/offline validation only; no DayZ render, wave, visibility, or acceptance.'},
        'inputs':{**source_hashes, str(candidate_path):sha(candidate_path), str(receipt_path):sha(receipt_path),
            str(PRE):sha(PRE),str(PRE_SCRIPT):sha(PRE_SCRIPT),str(PLAN):sha(PLAN),
            **{p:sha(p) for p in sources}},
        'baseline_preflight':{'status':pre['report']['status'],'mutable_count':len(domain['variables_set']),
            'preflight_sha256':sha(PRE),'script_sha256':sha(PRE_SCRIPT)},
    }
    for path,digest in report['inputs'].items():
        if sha(path)!=digest:
            raise AssertionError(f'input changed during EV90 consumer: {path}')
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',type=Path,default=CANDIDATE)
    ap.add_argument('--receipt',type=Path,default=RECEIPT)
    ap.add_argument('--output',type=Path,default=HERE/'ev90-review.json')
    args=ap.parse_args()
    report={'status':'ERROR_EV90_CONSUMER','gates':{},'information':{}}
    try:
        report=evaluate(args.candidate,args.receipt)
    except Exception as exc:
        report={'status':'ERROR_EV90_CONSUMER','gates':{},'error':repr(exc),
                'traceback':traceback.format_exc()}
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'false_gates':[k for k,v in report.get('gates',{}).items() if not v],
        'error':report.get('error'),'output':str(args.output)}))
    if report['status']=='ERROR_EV90_CONSUMER':raise SystemExit(2)
    if report['status']!='PASS_EV90_OFFLINE_CONSUMER':raise SystemExit(1)


if __name__=='__main__':
    main()
