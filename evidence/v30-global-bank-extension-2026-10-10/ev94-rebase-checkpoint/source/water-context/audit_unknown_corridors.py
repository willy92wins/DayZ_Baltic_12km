#!/usr/bin/env python
"""Read-only EV94 corridor audit against exact compiled EV93 water faces."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from shapely.geometry import GeometryCollection, LineString, Polygon, box, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree


G = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
OUT = G / 'unknown-p-audit'
INDEX_RUN = G / 'ev93-face-index/runs/20261010T092417Z-63d4cec3'
INDEX_MANIFEST = INDEX_RUN / 'manifest.json'
INDEX_BUILDER = G / 'ev93-face-index/build_face_index.py'
STAGE = G / 'build-focal/stage.json'
STAGE_SOURCE = G / 'build-focal/stage.py'
EV94_ROOT = G / 'build-focal'
H_PATH = EV94_ROOT / 'candidate/terrain.npz'
P_PATH = EV94_ROOT / 'candidate/plane.npy'
F_PATH = EV94_ROOT / 'candidate/visible-field.npy'
CORRIDORS = Path(r'E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson')
EV88_SOURCE = Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/review-independent/verify_ev88q.py')
EV88_REPORT = G / 'global-operator-prototype/real-sector-preflight/order-closure/consumer-run-01/review.json'

EXPECTED = {
    str(INDEX_MANIFEST): 'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
    str(INDEX_BUILDER): 'd1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e',
    str(STAGE): 'cc394869cf45f60315eea5b13a99b2f79d80135bee5ee32879b3900ecaa86610',
    str(H_PATH): '30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1',
    str(P_PATH): '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
    str(F_PATH): 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
    str(CORRIDORS): '28866a8cf6ff57f2f825228046164ef939bc22bca9948eb96fe2463da46af343',
    str(EV88_REPORT): 'a9112811a7d23fee0fe94735683174d3d3f67e2200a7519b7633c247b82b10fa',
    str(EV88_SOURCE): '82a988790e6bdfc0289bcb7c32cb0afd1210e07b264d92731aba266bc5980f78',
}
EXPECTED_UNKNOWN_M2 = {'Narva_23': 238.74576643431396, 'Luga_0': 752.2621866095913}
GRID_N = 2048
CELL = 6.0
Z0 = 12282.0
TRIS = ((0, 1, 3), (0, 2, 3))
MAX_SECONDS_AFTER_INDEX_LOAD = 300.0
MAX_UNIQUE_CANDIDATE_FACES = 250_000
AREA_EPS = 1e-12


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical_sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot import {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def corridor_candidate_cells(geom, bounds):
    """EV88 row-strip enumeration, copied from its pinned implementation."""
    r0, r1, c0, c1 = bounds
    xmin, _, xmax, _ = geom.bounds
    cells = []
    for r in range(r0, r1):
        ztop = Z0 - r * CELL
        zbottom = ztop - CELL
        row_piece = geom.intersection(box(xmin, zbottom, xmax, ztop))
        if row_piece.is_empty:
            continue
        parts = [row_piece] if row_piece.geom_type == 'Polygon' else [
            q for q in getattr(row_piece, 'geoms', []) if q.geom_type == 'Polygon' and q.area > AREA_EPS
        ]
        candidate_cols = set()
        for part in parts:
            px0, _, px1, _ = part.bounds
            pc0 = max(c0, int(math.floor(px0 / CELL)))
            pc1 = min(c1, int(math.ceil(px1 / CELL)))
            candidate_cols.update(range(pc0, pc1))
        for c in sorted(candidate_cols):
            cellbox = box(c * CELL, zbottom, (c + 1) * CELL, ztop)
            if geom.intersects(cellbox) and geom.intersection(cellbox).area > AREA_EPS:
                cells.append((r, c))
    return cells


def cell_triangles(r: int, c: int, heights: np.ndarray):
    """Return world XZ triangle polygons and affine H coefficients in X,Z."""
    xy = np.asarray([
        [c * CELL, Z0 - r * CELL],
        [(c + 1) * CELL, Z0 - r * CELL],
        [c * CELL, Z0 - (r + 1) * CELL],
        [(c + 1) * CELL, Z0 - (r + 1) * CELL],
    ], dtype=np.float64)
    hv = np.asarray([heights[r, c], heights[r, c + 1], heights[r + 1, c], heights[r + 1, c + 1]], dtype=np.float64)
    result = []
    for ti, indices in enumerate(TRIS):
        tri_xy = xy[list(indices)]
        tri_h = hv[list(indices)]
        coeff = np.linalg.solve(np.column_stack((tri_xy[:, 0], tri_xy[:, 1], np.ones(3))), tri_h)
        result.append((ti, Polygon(tri_xy), tri_xy, coeff))
    return result


def polygon_vertices(geom) -> np.ndarray:
    geoms = [geom] if geom.geom_type == 'Polygon' else [g for g in getattr(geom, 'geoms', []) if g.geom_type == 'Polygon']
    coords = []
    for poly in geoms:
        coords.extend(np.asarray(poly.exterior.coords[:-1], dtype=np.float64).tolist())
        for ring in poly.interiors:
            coords.extend(np.asarray(ring.coords[:-1], dtype=np.float64).tolist())
    return np.asarray(coords, dtype=np.float64).reshape((-1, 2))


def affine_range(coeff: np.ndarray, geom) -> tuple[float, float]:
    xy = polygon_vertices(geom)
    if len(xy) == 0:
        raise ValueError('nonempty positive-area polygon has no vertices')
    values = xy @ coeff[:2] + coeff[2]
    return float(values.min()), float(values.max())


def face_geometry(xyz: np.ndarray, area_xz: float):
    xy = np.asarray(xyz[:, [0, 2]], dtype=np.float64)
    if area_xz > 0.0:
        poly = Polygon(xy)
        if not poly.is_valid or poly.area <= 0.0:
            raise AssertionError('positive-area indexed face is not a valid polygon')
        return poly
    return GeometryCollection()


def geometry_contact(patch, xyz):
    points = np.asarray(xyz[:, [0, 2]], dtype=np.float64)
    edges = [LineString([points[i], points[(i + 1) % 3]]) for i in range(3)]
    return any(patch.intersects(edge) for edge in edges)


def overlap_summary(patch, records, deadline=None):
    """Exact union and >=2-layer region; per-face geometry stays local to a patch."""
    if not records:
        return {
            'covered_area_m2': 0.0,
            'uncovered_area_m2': float(patch.area),
            'overlap_ge2_area_m2': 0.0,
            'face_layers': [],
            'pairwise_overlaps': [],
        }
    covered = GeometryCollection()
    overlap = GeometryCollection()
    for record_number, rec in enumerate(records):
        if deadline is not None and record_number % 64 == 0:
            check_budget(deadline, 'face union')
        g = rec['geometry']
        current_overlap = covered.intersection(g)
        if not current_overlap.is_empty and current_overlap.area > AREA_EPS:
            overlap = unary_union([overlap, current_overlap])
        covered = unary_union([covered, g])

    # Tree-based exact pairs avoid O(n^2) comparisons for tiled ODOL meshes.
    tree = STRtree([rec['geometry'] for rec in records])
    pairs = tree.query([rec['geometry'] for rec in records], predicate='intersects')
    pair_reports = []
    layered_ids = set()
    for pair_number, (i, j) in enumerate(zip(pairs[0].tolist(), pairs[1].tolist())):
        if deadline is not None and pair_number % 256 == 0:
            check_budget(deadline, 'face overlap pairs')
        if i >= j:
            continue
        common = records[i]['geometry'].intersection(records[j]['geometry'])
        if common.is_empty or common.area <= AREA_EPS:
            continue
        low_i, high_i = affine_range(records[i]['plane'], common)
        low_j, high_j = affine_range(records[j]['plane'], common)
        # Difference between affine surface heights is also affine; evaluate at polygon vertices.
        delta_coeff = records[i]['plane'] - records[j]['plane']
        dmin, dmax = affine_range(delta_coeff, common)
        pair_reports.append({
            'face_i': records[i]['face_key'], 'face_j': records[j]['face_key'],
            'overlap_area_m2': float(common.area),
            'face_i_y_range_m': [low_i, high_i], 'face_j_y_range_m': [low_j, high_j],
            'y_i_minus_y_j_range_m': [dmin, dmax],
        })
        layered_ids.add(i)
        layered_ids.add(j)

    face_layers = []
    for i, rec in enumerate(records):
        y0, y1 = affine_range(rec['plane'], rec['geometry'])
        c0, c1 = affine_range(rec['plane'] - rec['ground_plane'], rec['geometry'])
        face_layers.append({
            'face_key': rec['face_key'],
            'intersection_area_m2': float(rec['geometry'].area),
            'face_y_range_m': [y0, y1],
            'face_minus_ground_range_m': [c0, c1],
            'terrain_relation': 'above_ground' if c0 > 0 else ('below_ground' if c1 < 0 else 'crosses_or_touches_ground'),
            'participates_in_positive_area_overlap': i in layered_ids,
        })
    return {
        'covered_area_m2': float(covered.area),
        'uncovered_area_m2': float(patch.difference(covered).area),
        'overlap_ge2_area_m2': float(overlap.area),
        'face_layers': face_layers,
        'pairwise_overlaps': pair_reports,
    }


def lookup_serialized_patch(patches, key_json):
    """Resolve a JSON-list key against the tuple-keyed in-memory patch map."""
    return patches[tuple(key_json)]


def check_budget(deadline, where):
    if time.monotonic() > deadline:
        raise TimeoutError(f'post-index audit time limit reached during {where}')


def build_unknown_patches_with_h(features, p, h):
    patches = {}
    by_feature = {}
    for feature in features:
        river = feature.get('properties', {}).get('river')
        if river not in EXPECTED_UNKNOWN_M2:
            continue
        geom = shape(feature['geometry'])
        xmin, zmin, xmax, zmax = geom.bounds
        c0 = max(0, int(math.floor(xmin / CELL)))
        c1 = min(GRID_N - 1, int(math.ceil(xmax / CELL)))
        r0 = max(0, int(math.floor((Z0 - zmax) / CELL)))
        r1 = min(GRID_N - 1, int(math.ceil((Z0 - zmin) / CELL)))
        all_cells = corridor_candidate_cells(geom, (r0, r1, c0, c1))
        unknown_cells = [(r, c) for r, c in all_cells if not np.isfinite(p[r, c])]
        area = 0.0
        feature_patches = []
        for r, c in unknown_cells:
            cell = box(c * CELL, Z0 - (r + 1) * CELL, (c + 1) * CELL, Z0 - r * CELL)
            corridor_in_cell = geom.intersection(cell)
            for ti, tri, tri_xy, ground_plane in cell_triangles(r, c, h):
                patch = corridor_in_cell.intersection(tri)
                if patch.is_empty or patch.area <= AREA_EPS:
                    continue
                key = (river, r, c, ti)
                patches[key] = {'geometry': patch, 'ground_plane': ground_plane}
                feature_patches.append(key)
                area += float(patch.area)
        expected_area = EXPECTED_UNKNOWN_M2[river]
        if abs(area - expected_area) > 1e-6:
            raise AssertionError(f'{river}: unknown-P area drift {area:.15g} vs pinned {expected_area:.15g}')
        by_feature[river] = {
            'unknown_area_m2': area,
            'unknown_cells': [list(x) for x in sorted(set((r, c) for r, c in unknown_cells))],
            'patch_keys': [list(k) for k in feature_patches],
        }
    if set(by_feature) != set(EXPECTED_UNKNOWN_M2):
        raise AssertionError(f'target corridor IDs mismatch: {sorted(by_feature)}')
    return patches, by_feature


def group_row_runs(cells):
    rows = defaultdict(list)
    for r, c in cells:
        rows[int(r)].append(int(c))
    runs = []
    for r in sorted(rows):
        cols = sorted(set(rows[r]))
        if not cols:
            continue
        start = prev = cols[0]
        for c in cols[1:]:
            if c != prev + 1:
                runs.append((r, start, prev))
                start = c
            prev = c
        runs.append((r, start, prev))
    return runs


def identify_stage_water_pbo(stage_obj):
    inputs = stage_obj.get('ev94_composition_input_hashes', {})
    matches = [(Path(path), value) for path, value in inputs.items() if Path(path).name.lower() == 'baltic_water_v30.pbo']
    if len(matches) != 1:
        raise AssertionError(f'expected exactly one pinned EV94 water PBO, found {len(matches)}')
    return matches[0]


def validate_identity(stage_obj, manifest):
    if stage_obj.get('status') != 'STAGED_EV94_HEIGHTS_ONLY' or stage_obj.get('objects_and_materials_exact') is not True:
        raise AssertionError('EV94 stage does not assert height-only staging and byte-exact objects/materials')
    if int(stage_obj.get('objects', -1)) != 18033:
        raise AssertionError('EV94 staged WRP object count is not the pinned 18,033')
    if stage_obj.get('source_wrp_sha256') != manifest['base_identity']['wrp_source_sha256']:
        raise AssertionError('EV94 stage source WRP does not match the WRP used by EV93 index')
    if stage_obj.get('terrain_sha256') != sha(H_PATH):
        raise AssertionError('EV94 stage terrain hash disagrees with current terrain.npz')
    if stage_obj.get('native_probe_inputs', {}).get('plane.npy', {}).get('sha256') != sha(P_PATH):
        raise AssertionError('EV94 staged P field is not the pinned copy')
    if stage_obj.get('native_probe_inputs', {}).get('visible-field.npy', {}).get('sha256') != sha(F_PATH):
        raise AssertionError('EV94 staged F field is not the pinned copy')
    staged_wrp = EV94_ROOT / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    if sha(staged_wrp) != stage_obj.get('staged_wrp_sha256'):
        raise AssertionError('staged EV94 WRP bytes differ from stage.json')
    source_wrp = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp')
    if sha(source_wrp) != manifest['base_identity']['wrp_source_sha256']:
        raise AssertionError('index source WRP no longer matches the original source WRP')
    water_pbo, water_hash = identify_stage_water_pbo(stage_obj)
    if water_hash != manifest['base_identity']['water_pbo_sha256'] or sha(water_pbo) != water_hash:
        raise AssertionError('EV94 water PBO is not byte-identical to the PBO pinned by the index')
    if int(manifest.get('object_count', -1)) != 18024:
        raise AssertionError('EV93 index object count changed')
    # Source-level audit of stage.py confirms the receipt is backed by byte equality over all WRP objects.
    stage_source = STAGE_SOURCE.read_text(encoding='utf-8')
    required = [
        "len(after['objects']) == len(baseline['objects']) == 18033",
        "[obj['bytes'] for obj in baseline['objects']] == [obj['bytes'] for obj in after['objects']]",
    ]
    if any(snippet not in stage_source for snippet in required):
        raise AssertionError('stage.py no longer implements exact object-record identity check')
    return {
        'stage_source_wrps': 'same source_wrp_sha256 as face index',
        'staged_wrp': {'path': str(staged_wrp), 'sha256': sha(staged_wrp)},
        'source_wrp': {'path': str(source_wrp), 'sha256': sha(source_wrp)},
        'staged_object_records': 18033,
        'indexed_water_objects': 18024,
        'not_selected_by_water_name_predicate': 9,
        'selection_rule': "builder selects WRP names containing 'baltic_water_v30' and requires exact bijection with 18,024 bounds records",
        'water_pbo': {'path': str(water_pbo), 'sha256': water_hash},
        'terrain_sha256': stage_obj['terrain_sha256'],
        'P_sha256': sha(P_PATH),
        'F_sha256': sha(F_PATH),
        'stage_source_sha256': sha(STAGE_SOURCE),
        'stage_source_evidence_lines': [92, 99],
    }


def self_test():
    # Half of a 6x6 cell, with two coincident faces at different elevations.
    patch = box(0.0, 0.0, 6.0, 6.0)
    half = box(0.0, 0.0, 3.0, 6.0)
    ground = np.asarray([0.0, 0.0, 0.0])
    recs = [
        {'geometry': half, 'plane': np.asarray([0.0, 0.0, 2.0]), 'ground_plane': ground, 'face_key': [0, 10, 1]},
        {'geometry': half, 'plane': np.asarray([0.0, 0.0, 1.0]), 'ground_plane': ground, 'face_key': [0, 11, 1]},
    ]
    summary = overlap_summary(patch, recs)
    assert abs(summary['covered_area_m2'] - 18.0) < 1e-10
    assert abs(summary['uncovered_area_m2'] - 18.0) < 1e-10
    assert abs(summary['overlap_ge2_area_m2'] - 18.0) < 1e-10
    assert len(summary['pairwise_overlaps']) == 1
    assert summary['pairwise_overlaps'][0]['y_i_minus_y_j_range_m'] == [1.0, 1.0]
    assert all(layer['terrain_relation'] == 'above_ground' for layer in summary['face_layers'])

    # Broadphase bbox can overlap a patch while the actual face does not.
    patch2 = box(0.0, 0.0, 1.0, 1.0)
    triangle = Polygon([(0.8, 1.2), (1.2, 0.8), (1.2, 1.2)])
    assert triangle.bounds[0] <= patch2.bounds[2] and triangle.bounds[2] >= patch2.bounds[0]
    assert triangle.intersection(patch2).area == 0.0
    # Independent clearance controls, both signs.
    assert affine_range(np.asarray([0.0, 0.0, 2.0]), patch)[0] == 2.0
    assert affine_range(np.asarray([0.0, 0.0, -1.0]), patch)[1] == -1.0
    return {
        'positive_two_layer_half_coverage': True,
        'negative_bbox_only_exact_clip': True,
        'positive_clearance_control': True,
        'negative_buried_clearance_control': True,
        'overlap_summary': summary,
    }


def current_input_hashes():
    paths = list(EXPECTED) + [str(STAGE_SOURCE), str(EV88_SOURCE)]
    stage_obj = json.loads(STAGE.read_text(encoding='utf-8'))
    water_path, _ = identify_stage_water_pbo(stage_obj)
    paths += [str(water_path), str(EV94_ROOT / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'),
              str(Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'))]
    return {p: sha(Path(p)) for p in sorted(set(paths))}


def run_audit():
    started = time.monotonic()
    report = {
        'schema': 'ev93.unknown-p-corridor-audit.v1',
        'status': 'RUNNING',
        'scope': ['Narva_23', 'Luga_0'],
        'interpretation': 'P NaN is unknown field data; face coverage is independently tested; no P/H is written.',
        'limits': {'seconds_after_index_load': MAX_SECONDS_AFTER_INDEX_LOAD, 'unique_candidate_faces': MAX_UNIQUE_CANDIDATE_FACES},
        'phase_seconds': {},
        'results': {},
    }
    source_hashes_start = current_input_hashes()
    report['source_hashes_start'] = source_hashes_start
    report['audit_source_sha256_start'] = sha(Path(__file__))
    for path, expected_hash in EXPECTED.items():
        actual_hash = source_hashes_start.get(path)
        if actual_hash != expected_hash:
            raise AssertionError(f'input pin mismatch: {path}: {actual_hash} != {expected_hash}')
    manifest = json.loads(INDEX_MANIFEST.read_text(encoding='utf-8'))
    stage_obj = json.loads(STAGE.read_text(encoding='utf-8'))
    identity = validate_identity(stage_obj, manifest)
    report['ev94_index_identity'] = identity

    t0 = time.monotonic()
    with np.load(H_PATH, allow_pickle=False) as archive:
        heights = archive['heights'].copy()
    p = np.load(P_PATH, mmap_mode='r')
    if heights.shape != (GRID_N, GRID_N) or heights.dtype != np.float32 or p.shape != (GRID_N - 1, GRID_N - 1):
        raise AssertionError(f'unexpected H/P schema: H={heights.shape}/{heights.dtype}, P={p.shape}/{p.dtype}')
    features = json.loads(CORRIDORS.read_text(encoding='utf-8'))['features']
    patches, feature_info = build_unknown_patches_with_h(features, p, heights)
    report['feature_inputs'] = feature_info
    report['phase_seconds']['load_and_build_unknown_masks'] = time.monotonic() - t0

    t0 = time.monotonic()
    index_module = load_module('ev93_face_range_index_unknown_p_audit', INDEX_BUILDER)
    index = index_module.FaceRangeIndex(INDEX_RUN)
    index_load_seconds = time.monotonic() - t0
    report['phase_seconds']['index_load_and_shard_validation'] = index_load_seconds
    if index.manifest.get('status') != 'COMPLETE' or len(index.manifest.get('shards', [])) != 9:
        raise AssertionError('EV93 index is not complete with the expected shard count')
    audit_clock = time.monotonic()

    all_cells = sorted(set((int(k[1]), int(k[2])) for k in patches))
    candidates = {}
    by_cell = defaultdict(dict)
    query_calls = 0
    scanned_candidates = 0
    for r, c0, c1 in group_row_runs(all_cells):
        if time.monotonic() - audit_clock > MAX_SECONDS_AFTER_INDEX_LOAD:
            raise TimeoutError('post-index audit time limit reached while querying candidate faces')
        rows = index.query_window(r, r, c0, c1, kind=None)
        query_calls += 1
        scanned_candidates += int(len(rows['kind']))
        for j in range(len(rows['kind'])):
            kind = int(rows['kind'][j])
            key = (kind, int(rows['object_id'][j]), int(rows['model_id'][j]), int(rows['face_id'][j]))
            if key not in candidates:
                candidates[key] = {name: rows[name][j].copy() if isinstance(rows[name][j], np.ndarray) else rows[name][j].item() for name in rows}
                if len(candidates) > MAX_UNIQUE_CANDIDATE_FACES:
                    raise OverflowError('unique candidate-face budget exceeded')
            rec = candidates[key]
            cr = rec['cell_range_rc']
            for c in range(c0, c1 + 1):
                if int(cr[0]) <= r <= int(cr[1]) and int(cr[2]) <= c <= int(cr[3]):
                    by_cell[(r, c)][key] = rec

    report['query'] = {
        'unknown_cells': len(all_cells),
        'row_run_queries': query_calls,
        'candidate_rows_returned_including_duplicates': scanned_candidates,
        'unique_candidate_faces_both_lods': len(candidates),
        'unique_candidate_faces_by_lod': {
            'physical': sum(k[0] == 0 for k in candidates),
            'visible': sum(k[0] == 1 for k in candidates),
        },
    }

    t0 = time.monotonic()
    per_feature = {}
    for river, info in feature_info.items():
        summary = {kind: {'unknown_area_m2': 0.0, 'covered_area_m2': 0.0, 'uncovered_area_m2': 0.0,
                          'overlap_ge2_area_m2': 0.0, 'face_patch_intersections': 0,
                          'degenerate_candidates': 0, 'zero_area_contacts': 0, 'faces': {}, 'cells': {}}
                   for kind in ('physical', 'visible')}
        for key_list in info['patch_keys']:
            # JSON-friendly feature_info stores keys as lists; the patch map uses tuples.
            key = tuple(key_list)
            _, r, c, ti = key
            patch_data = lookup_serialized_patch(patches, key_list)
            check_budget(audit_clock + MAX_SECONDS_AFTER_INDEX_LOAD, 'exact patch clipping')
            patch = patch_data['geometry']
            ground_plane = patch_data['ground_plane']
            for lod_name, lod_kind in (('physical', 0), ('visible', 1)):
                clipped_records = []
                degenerate = 0
                contacts = 0
                for face_number, (face_key, rec) in enumerate(by_cell[(r, c)].items()):
                    if face_number % 128 == 0:
                        check_budget(audit_clock + MAX_SECONDS_AFTER_INDEX_LOAD, 'face intersections')
                    if face_key[0] != lod_kind:
                        continue
                    xyz = rec['xyz']
                    if int(rec['degenerate']):
                        degenerate += 1
                        if geometry_contact(patch, xyz):
                            contacts += 1
                        continue
                    poly = face_geometry(xyz, float(rec['area_xz']))
                    clipped = patch.intersection(poly)
                    if clipped.is_empty or clipped.area <= AREA_EPS:
                        if poly.intersects(patch):
                            contacts += 1
                        continue
                    clipped_records.append({
                        'geometry': clipped,
                        'plane': np.asarray(rec['plane_y_xz'], dtype=np.float64),
                        'ground_plane': ground_plane,
                        'face_key': [int(face_key[1]), int(face_key[2]), int(face_key[3])],
                    })
                ov = overlap_summary(patch, clipped_records, audit_clock + MAX_SECONDS_AFTER_INDEX_LOAD)
                target = summary[lod_name]
                target['unknown_area_m2'] += float(patch.area)
                target['covered_area_m2'] += ov['covered_area_m2']
                target['uncovered_area_m2'] += ov['uncovered_area_m2']
                target['overlap_ge2_area_m2'] += ov['overlap_ge2_area_m2']
                target['face_patch_intersections'] += len(clipped_records)
                target['degenerate_candidates'] += degenerate
                target['zero_area_contacts'] += contacts
                cell_tri = target['cells'].setdefault(f'{r},{c}', {'row': r, 'col': c, 'triangles': {}})['triangles'].setdefault(str(ti), {
                    'unknown_area_m2': float(patch.area), 'covered_area_m2': 0.0, 'uncovered_area_m2': 0.0,
                    'overlap_ge2_area_m2': 0.0, 'zero_area_contacts': 0, 'degenerate_candidates': 0,
                    'faces': [], 'pairwise_overlaps': [],
                })
                cell_tri['covered_area_m2'] = ov['covered_area_m2']
                cell_tri['uncovered_area_m2'] = ov['uncovered_area_m2']
                cell_tri['overlap_ge2_area_m2'] = ov['overlap_ge2_area_m2']
                cell_tri['zero_area_contacts'] = contacts
                cell_tri['degenerate_candidates'] = degenerate
                cell_tri['faces'] = ov['face_layers']
                cell_tri['pairwise_overlaps'] = ov['pairwise_overlaps']
                for layer in ov['face_layers']:
                    fkey = tuple(layer['face_key'])
                    old = target['faces'].get(':'.join(map(str, fkey)))
                    if old is None:
                        target['faces'][':'.join(map(str, fkey))] = {
                            'object_id': fkey[0], 'model_id': fkey[1], 'face_id': fkey[2],
                            'patch_intersection_area_sum_m2': layer['intersection_area_m2'],
                            'face_y_range_m': layer['face_y_range_m'],
                            'face_minus_ground_range_m': layer['face_minus_ground_range_m'],
                            'terrain_relation_by_patch': [layer['terrain_relation']],
                            'participates_in_overlap': layer['participates_in_positive_area_overlap'],
                            'cells': [[r, c, ti]],
                        }
                    else:
                        old['patch_intersection_area_sum_m2'] += layer['intersection_area_m2']
                        old['face_y_range_m'] = [min(old['face_y_range_m'][0], layer['face_y_range_m'][0]), max(old['face_y_range_m'][1], layer['face_y_range_m'][1])]
                        old['face_minus_ground_range_m'] = [min(old['face_minus_ground_range_m'][0], layer['face_minus_ground_range_m'][0]), max(old['face_minus_ground_range_m'][1], layer['face_minus_ground_range_m'][1])]
                        old['terrain_relation_by_patch'].append(layer['terrain_relation'])
                        old['participates_in_overlap'] = old['participates_in_overlap'] or layer['participates_in_positive_area_overlap']
                        old['cells'].append([r, c, ti])
        per_feature[river] = summary
    report['phase_seconds']['exact_clipping_and_overlap'] = time.monotonic() - t0
    report['results'] = per_feature

    physical_gap = sum(x['physical']['uncovered_area_m2'] for x in per_feature.values())
    physical_covered = sum(x['physical']['covered_area_m2'] for x in per_feature.values())
    physical_overlap = sum(x['physical']['overlap_ge2_area_m2'] for x in per_feature.values())
    report['classification'] = {
        'P_unknown_total_m2': sum(EXPECTED_UNKNOWN_M2.values()),
        'physical_compiled_face_union_m2': physical_covered,
        'physical_no_face_gap_m2': physical_gap,
        'physical_overlap_ge2_m2': physical_overlap,
        'visible_compiled_face_union_m2': sum(x['visible']['covered_area_m2'] for x in per_feature.values()),
        'visible_no_face_gap_m2': sum(x['visible']['uncovered_area_m2'] for x in per_feature.values()),
        'interpretation': 'P-unknown area is classified by exact static face footprint and face-vs-H elevation; runtime water behavior remains untested.',
    }

    index.reverify()
    source_hashes_end = current_input_hashes()
    report['source_hashes_end'] = source_hashes_end
    report['source_hashes_unchanged'] = source_hashes_start == source_hashes_end
    report['audit_source_sha256_end'] = sha(Path(__file__))
    report['audit_source_unchanged'] = report['audit_source_sha256_start'] == report['audit_source_sha256_end']
    report['phase_seconds']['total_after_index_load'] = time.monotonic() - audit_clock
    report['elapsed_total_seconds'] = time.monotonic() - started
    if not report['source_hashes_unchanged'] or not report['audit_source_unchanged']:
        report['status'] = 'INCONCLUSIVE_INPUT_DRIFT'
    elif report['phase_seconds']['total_after_index_load'] > MAX_SECONDS_AFTER_INDEX_LOAD:
        report['status'] = 'INCONCLUSIVE_TIME_BUDGET'
    elif len(candidates) > MAX_UNIQUE_CANDIDATE_FACES:
        report['status'] = 'INCONCLUSIVE_FACE_BUDGET'
    else:
        report['status'] = 'COMPLETE_STATIC_GEOMETRY_AUDIT'
    report['report_sha_note'] = 'The report does not include its own hash; hash the emitted file externally.'
    out_path = OUT / 'unknown-p-audit.json'
    out_path.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'report': str(out_path), 'unknown_m2': report['classification']['P_unknown_total_m2'],
                      'physical_gap_m2': physical_gap, 'physical_covered_m2': physical_covered,
                      'physical_overlap_ge2_m2': physical_overlap, 'candidate_faces': len(candidates),
                      'elapsed_s': report['elapsed_total_seconds']}, ensure_ascii=False))
    return 0 if report['status'] == 'COMPLETE_STATIC_GEOMETRY_AUDIT' else 2


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--self-test', action='store_true')
    group.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    return run_audit()


if __name__ == '__main__':
    raise SystemExit(main())
