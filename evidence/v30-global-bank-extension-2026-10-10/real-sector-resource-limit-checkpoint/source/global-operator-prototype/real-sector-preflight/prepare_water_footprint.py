"""Build only the conservative compiled-water/P/F blocking mask for the real-sector pilot.

The production path loads the pinned EV93 face index exactly once, queries the
one-cell incident-cell halo of the frozen 256x256 vertex window, and clips every
physical/visible face's XZ projection against both native NW-SE triangles.
This module does not select a seed, solve, alter heights, or certify the map.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon

ROOT = Path(r'E:/DayZ-Baltic-Build')
G = ROOT / 'v30-global-bank-extension-20261010'
HERE = G / 'global-operator-prototype/real-sector-preflight'
PLAN = G / 'global-operator-prototype/PLAN_REAL_SECTOR.md'
EV87 = ROOT / 'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
B = ROOT / 'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
P = ROOT / 'v30-narva-dry-bank-relief-20261010/candidate/plane.npy'
F = ROOT / 'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy'
INDEX_SOURCE = G / 'ev93-face-index/build_face_index.py'
INDEX_RUN = G / 'ev93-face-index/runs/20261010T092417Z-63d4cec3'
INDEX_MANIFEST = INDEX_RUN / 'manifest.json'
INDEX_VERIFICATION = G / 'review-independent/runs/attempt-01/verification.json'

PINS = {
    str(PLAN): '14f02179312bc25caf76a087cc873122caed30f6092464f1c01ac7572d519749',
    str(EV87): '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
    str(B): 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    str(P): '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
    str(F): 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
    str(INDEX_SOURCE): 'd1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e',
    str(INDEX_MANIFEST): 'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
    str(INDEX_VERIFICATION): 'b498e7d68835b199399655451e5e01ac81acb3149dbb9bf882b94858141521d4',
}

N = 2048
CELL = 6.0
Z0 = 12282.0
WINDOW = (712, 968, 242, 498)  # half-open vertex bounds
# A cell touching any vertex in WINDOW has cell indices [r0-1,r1-1] and
# [c0-1,c1-1], inclusive. This is the exact one-cell incident-cell halo.
CELL_WINDOW = (WINDOW[0] - 1, WINDOW[1] - 1,
               WINDOW[2] - 1, WINDOW[3] - 1)  # inclusive [r0,r1,c0,c1]
TRIS = ((0, 1, 3), (0, 2, 3))  # verified EV87 order NW,NE,SW,SE; NW-SE split
CORNER_OFFSETS = ((0, 0), (0, 1), (1, 0), (1, 1))

# Cell-reason bits. These describe why the four cell corners are frozen.
PHYSICAL_FACE = 1 << 0
VISIBLE_FACE = 1 << 1
DEGENERATE_PHYSICAL = 1 << 2
DEGENERATE_VISIBLE = 1 << 3
P_CROSS_OR_CONTACT = 1 << 4
F_CROSS_OR_CONTACT = 1 << 5
F_PARTIAL = 1 << 6
REASON_NAMES = {
    PHYSICAL_FACE: 'compiled_physical_face_xz_intersection',
    VISIBLE_FACE: 'compiled_visible_face_xz_intersection',
    DEGENERATE_PHYSICAL: 'degenerate_physical_face_conservative_bbox_freeze',
    DEGENERATE_VISIBLE: 'degenerate_visible_face_conservative_bbox_freeze',
    P_CROSS_OR_CONTACT: 'P_surface_native_triangle_crossing_or_contact',
    F_CROSS_OR_CONTACT: 'F_surface_native_triangle_crossing_or_contact',
    F_PARTIAL: 'F_triangle_partially_unknown',
}
KINDS = ('physical', 'visible')


def sha(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot load pinned source: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_pins() -> dict[str, str]:
    observed = {}
    for raw, expected in PINS.items():
        actual = sha(raw)
        if actual != expected:
            raise AssertionError(f'input pin mismatch {raw}: {actual} != {expected}')
        observed[raw] = actual
    return observed


def incident_cell_window(vertex_window=WINDOW):
    """Return inclusive cells touching any vertex in a half-open node window."""
    r0, r1, c0, c1 = map(int, vertex_window)
    if not (0 <= r0 < r1 < N and 0 <= c0 < c1 < N):
        raise ValueError(f'invalid half-open vertex window: {vertex_window}')
    return (r0 - 1, r1 - 1, c0 - 1, c1 - 1)


def cell_corner_heights(heights, r, c):
    return np.asarray((heights[r, c], heights[r, c + 1],
                       heights[r + 1, c], heights[r + 1, c + 1]), dtype=np.float64)


def crossing_or_contact(levels, ground, tri):
    """Exact sign crossing/contact predicate used for a native triangle."""
    ids = np.asarray(tri, dtype=np.intp)
    delta = np.asarray(levels, dtype=np.float64)[ids] - np.asarray(ground, dtype=np.float64)[ids]
    if not np.isfinite(delta).all():
        raise ValueError('crossing predicate requires three finite triangle samples')
    return bool(np.any(delta == 0.0) or (np.min(delta) < 0.0 and np.max(delta) > 0.0))


def cell_water_reason(ground, p_value, f_values):
    """Return P/F shore/contact/partial reason bits; fully same-sign cells do not freeze."""
    ground = np.asarray(ground, dtype=np.float64)
    f_values = np.asarray(f_values, dtype=np.float64)
    if ground.shape != (4,) or f_values.shape != (4,):
        raise ValueError('cell corner arrays must have four NW,NE,SW,SE values')
    if not np.isfinite(ground).all():
        raise ValueError('B terrain corners must be finite')
    reason = 0
    if np.isfinite(p_value):
        p_levels = np.full(4, float(p_value), dtype=np.float64)
        if any(crossing_or_contact(p_levels, ground, tri) for tri in TRIS):
            reason |= P_CROSS_OR_CONTACT
    elif np.isinf(p_value):
        raise ValueError('P infinity is invalid; only NaN encodes unknown')

    for tri in TRIS:
        vals = f_values[np.asarray(tri, dtype=np.intp)]
        finite = np.isfinite(vals)
        if finite.any() and not finite.all():
            reason |= F_PARTIAL
        elif finite.all() and crossing_or_contact(f_values, ground, tri):
            reason |= F_CROSS_OR_CONTACT
        elif np.isinf(vals).any():
            raise ValueError('F infinity is invalid; only NaN encodes unknown')
    return reason


def _checked_cell_range(cell_range, cell_window):
    rmin, rmax, cmin, cmax = map(int, cell_range)
    # The index's off-map sentinel is exactly four -1s. Mixed sentinels could
    # conceal an unbounded/invalid support and therefore fail closed.
    if (rmin, rmax, cmin, cmax) == (-1, -1, -1, -1):
        return None
    if min(rmin, rmax, cmin, cmax) < 0 or rmax < rmin or cmax < cmin:
        raise AssertionError(f'malformed non-sentinel face cell range: {cell_range}')
    if rmax > N - 2 or cmax > N - 2:
        raise AssertionError(f'face cell range exceeds native grid: {cell_range}')
    wr0, wr1, wc0, wc1 = cell_window
    lo_r, hi_r = max(rmin, wr0), min(rmax, wr1)
    lo_c, hi_c = max(cmin, wc0), min(cmax, wc1)
    if lo_r > hi_r or lo_c > hi_c:
        return ()
    return (lo_r, hi_r, lo_c, hi_c)


def face_intersected_cells(xyz, degenerate, cell_range, cell_window, ev87):
    """Exact XZ face-vs-native-triangle hit set, with conservative degenerate fallback.

    Y is intentionally ignored: even buried compiled support freezes its cell.
    Topological `intersects` counts edge/point touches, protecting both adjacent
    cells at a shared boundary. Degenerate projections freeze their bounded bbox.
    """
    clipped_range = _checked_cell_range(cell_range, cell_window)
    if clipped_range is None or clipped_range == ():
        return set(), bool(degenerate)
    rmin, rmax, cmin, cmax = clipped_range
    if degenerate:
        return {(r, c) for r in range(rmin, rmax + 1)
                for c in range(cmin, cmax + 1)}, True

    xyz = np.asarray(xyz, dtype=np.float64)
    if xyz.shape != (3, 3) or not np.isfinite(xyz).all():
        raise ValueError('indexed face xyz must be finite float64[3,3]')
    face_xz = Polygon(xyz[:, (0, 2)])
    if not face_xz.is_valid or face_xz.area <= 0.0:
        raise AssertionError('nondegenerate index record has invalid/zero XZ polygon')
    hits = set()
    for r in range(rmin, rmax + 1):
        for c in range(cmin, cmax + 1):
            corners = ev87.cell_xy(r, c)
            for tri in TRIS:
                tri_poly = Polygon(corners[np.asarray(tri, dtype=np.intp)])
                if face_xz.intersects(tri_poly):
                    hits.add((r, c))
                    break
    return hits, False


def make_masks(heights, p, f, face_arrays, ev87, vertex_window=WINDOW):
    """Compose cell reason bits and the corresponding four-corner vertex freeze."""
    r0, r1, c0, c1 = map(int, vertex_window)
    cell_window = incident_cell_window(vertex_window)
    cr0, cr1, cc0, cc1 = cell_window
    cell_shape = (cr1 - cr0 + 1, cc1 - cc0 + 1)
    cell_reasons = np.zeros(cell_shape, dtype=np.uint16)
    face_counts = np.zeros(cell_shape + (2,), dtype=np.uint32)

    required_arrays = {'kind', 'object_id', 'model_id', 'face_id', 'xyz', 'area_xz',
                       'cell_range_rc', 'degenerate'}
    if set(face_arrays) != required_arrays | {'plane_y_xz'}:
        raise ValueError(f'EV93 query schema mismatch: {sorted(face_arrays)}')
    nfaces = len(face_arrays['kind'])
    if any(len(face_arrays[k]) != nfaces for k in required_arrays):
        raise ValueError('EV93 query fields are not row-aligned')
    identities = np.column_stack((face_arrays['kind'], face_arrays['object_id'],
                                  face_arrays['model_id'], face_arrays['face_id']))
    if len({tuple(map(int, row)) for row in identities.tolist()}) != nfaces:
        raise AssertionError('duplicate object/kind/model/face identity in query result')

    degenerate_faces = {'physical': 0, 'visible': 0}
    degenerate_cells = {'physical': set(), 'visible': set()}
    face_hits_total = {'physical': 0, 'visible': 0}
    for i in range(nfaces):
        kind_code = int(face_arrays['kind'][i])
        if kind_code not in (0, 1):
            raise AssertionError(f'unknown indexed kind code {kind_code}')
        kind = KINDS[kind_code]
        is_degenerate = bool(face_arrays['degenerate'][i])
        if float(face_arrays['area_xz'][i]) <= 0.0 and not is_degenerate:
            raise AssertionError('zero-area XZ face is not marked degenerate')
        hits, used_fallback = face_intersected_cells(
            face_arrays['xyz'][i], is_degenerate, face_arrays['cell_range_rc'][i], cell_window, ev87)
        if used_fallback:
            degenerate_faces[kind] += 1
            degenerate_cells[kind].update(hits)
        bit = PHYSICAL_FACE if kind == 'physical' else VISIBLE_FACE
        deg_bit = DEGENERATE_PHYSICAL if kind == 'physical' else DEGENERATE_VISIBLE
        for r, c in hits:
            ix = (r - cr0, c - cc0)
            cell_reasons[ix] |= bit
            if is_degenerate:
                cell_reasons[ix] |= deg_bit
            face_counts[ix + (kind_code,)] += 1
        face_hits_total[kind] += len(hits)

    # P is scalar per cell; F is four native corner samples. No blanket finite
    # mask: only a P/F shoreline/contact or a partial F triangle freezes these cells.
    p_counts = {'cross_or_contact': 0}
    f_counts = {'cross_or_contact': 0, 'partial': 0}
    for r in range(cr0, cr1 + 1):
        ground = cell_corner_heights(heights, r, 0)  # overwritten per column below
        for c in range(cc0, cc1 + 1):
            ground = cell_corner_heights(heights, r, c)
            reason = cell_water_reason(ground, p[r, c], f[r, c])
            cell_reasons[r - cr0, c - cc0] |= np.uint16(reason)
            if reason & P_CROSS_OR_CONTACT:
                p_counts['cross_or_contact'] += 1
            if reason & F_CROSS_OR_CONTACT:
                f_counts['cross_or_contact'] += 1
            if reason & F_PARTIAL:
                f_counts['partial'] += 1

    vertex_reasons = np.zeros((r1 - r0, c1 - c0), dtype=np.uint16)
    for r in range(cr0, cr1 + 1):
        for c in range(cc0, cc1 + 1):
            reason = cell_reasons[r - cr0, c - cc0]
            if reason == 0:
                continue
            for vr, vc in ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)):
                if r0 <= vr < r1 and c0 <= vc < c1:
                    vertex_reasons[vr - r0, vc - c0] |= reason
    blocked = vertex_reasons != 0
    counts = {
        'vertex_window_shape': list(blocked.shape),
        'incident_cell_window_shape': list(cell_reasons.shape),
        'incident_cells_with_any_reason': int(np.count_nonzero(cell_reasons)),
        'blocked_vertices_in_window': int(np.count_nonzero(blocked)),
        'cell_reason_cells': {name: int(np.count_nonzero(cell_reasons & bit))
                              for bit, name in REASON_NAMES.items()},
        'face_cell_hits_including_kind_counts': face_hits_total,
        'degenerate_faces_bbox_frozen': degenerate_faces,
        'degenerate_candidate_cells_frozen': {k: len(v) for k, v in degenerate_cells.items()},
        'P_contact_cells': p_counts['cross_or_contact'],
        'F_contact_cells': f_counts['cross_or_contact'],
        'F_partial_cells': f_counts['partial'],
        'fully_unknown_F_cells_not_frozen_by_unknown_alone': True,
        'fully_finite_same_sign_P_or_F_cells_not_frozen_by_finiteness_alone': True,
    }
    return {
        'cell_reasons': cell_reasons,
        'face_counts': face_counts,
        'vertex_reasons': vertex_reasons,
        'blocked_vertices': blocked,
        'cell_window_inclusive': list(cell_window),
        'vertex_window_half_open': list(vertex_window),
        'counts': counts,
    }


def reusable_direct_smoke_evidence(path=INDEX_VERIFICATION):
    """Validate an already completed three-cell direct-vs-index report; no index reload."""
    report = json.loads(Path(path).read_text(encoding='utf-8'))
    if report.get('status') != 'PASS_INDEX_AND_SAMPLED_EXPOSURE':
        raise AssertionError('pinned EV93/direct exposure smoke report is not PASS')
    if report.get('manifest_sha256') != PINS[str(INDEX_MANIFEST)]:
        raise AssertionError('prior exposure smoke report refers to another index manifest')
    required = ((832, 362), (840, 362), (847, 362))
    samples = report.get('sampled_cells', {})
    output = []
    r0, r1, c0, c1 = incident_cell_window()
    for r, c in required:
        if not (r0 <= r <= r1 and c0 <= c <= c1):
            raise AssertionError(f'reused smoke cell is outside the pilot incident-cell halo: {(r,c)}')
        row = samples.get(f'{r},{c}')
        if row is None:
            raise AssertionError(f'prior direct/index smoke report lacks {(r,c)}')
        for kind in KINDS:
            entry = row.get(kind, {})
            if entry.get('pass_existing_0_002m2_coverage_tolerance') is not True or \
               float(entry.get('symmetric_difference_m2', float('inf'))) != 0.0:
                raise AssertionError(f'prior direct/index exposure smoke did not pass at {(r,c)}/{kind}')
        output.append({'cell_rc': [r, c], 'physical_direct_vs_index_symdiff_m2': 0.0,
                       'visible_direct_vs_index_symdiff_m2': 0.0,
                       'provenance': 'reused from pinned EV93 verification; not rerun in this mask task'})
    return output


def _fixture_face(xz, y=-10.0):
    xyz = np.zeros((3, 3), dtype=np.float64)
    xyz[:, 0] = np.asarray(xz, dtype=np.float64)[:, 0]
    xyz[:, 1] = float(y)
    xyz[:, 2] = np.asarray(xz, dtype=np.float64)[:, 1]
    return xyz


def fixtures():
    """Small geometry and water-mask controls; no map/index loading."""
    for path, wanted in ((EV87, PINS[str(EV87)]), (INDEX_SOURCE, PINS[str(INDEX_SOURCE)])):
        if sha(path) != wanted:
            raise AssertionError(f'fixture helper source pin mismatch: {path}')
    ev = load_module('water_footprint_fixture_ev87', EV87)
    index_module = load_module('water_footprint_fixture_index', INDEX_SOURCE)
    # Different signs on a native triangle means the water/ground contour crosses.
    assert cell_water_reason(np.asarray([0, 1, 1, 1]), .5, np.full(4, np.nan)) & P_CROSS_OR_CONTACT
    assert cell_water_reason(np.asarray([0, 1, 1, 1]), np.nan,
                             np.full(4, .5)) & F_CROSS_OR_CONTACT
    # Exact zero is a contact and freezes; all-positive fully wet and all-negative dry do not.
    assert cell_water_reason(np.full(4, .5), .5, np.full(4, np.nan)) & P_CROSS_OR_CONTACT
    assert cell_water_reason(np.full(4, .5), np.nan,
                             np.full(4, .5)) & F_CROSS_OR_CONTACT
    assert not (cell_water_reason(np.zeros(4), 1.0, np.full(4, np.nan)) & P_CROSS_OR_CONTACT)
    assert not (cell_water_reason(np.full(4, 2.0), 1.0, np.full(4, np.nan)) & P_CROSS_OR_CONTACT)
    assert not (cell_water_reason(np.zeros(4), np.nan, np.ones(4)) & F_CROSS_OR_CONTACT)
    # F partial triangles freeze; all-unknown F alone does not.
    assert cell_water_reason(np.zeros(4), np.nan,
                             np.asarray([1.0, np.nan, np.nan, 1.0])) & F_PARTIAL
    assert not (cell_water_reason(np.zeros(4), np.nan, np.full(4, np.nan)) & F_PARTIAL)
    # A buried nondegenerate face is still support. It touches the left cell only at
    # x=6, so the exact topological predicate freezes both sides of that shared edge.
    boundary_face = _fixture_face(((6.0, Z0-1.0), (6.0, Z0-5.0), (8.0, Z0-3.0)), y=-100.0)
    range_two_cells = np.asarray([0, 0, 0, 1], dtype=np.int32)
    hits, fallback = face_intersected_cells(boundary_face, False, range_two_cells,
                                             (0, 0, 0, 1), ev)
    assert hits == {(0, 0), (0, 1)} and not fallback
    # A face wholly within one cell is included even though its Y is far below any
    # plausible terrain; the mask is support-based, not current exposure-based.
    buried = _fixture_face(((1, Z0-1), (4, Z0-1), (2, Z0-4)), y=-1000.0)
    buried_hits, _ = face_intersected_cells(buried, False, [0, 0, 0, 0], (0, 0, 0, 0), ev)
    assert buried_hits == {(0, 0)}
    # Degenerate projections freeze their bounded bbox cells conservatively.
    deg = _fixture_face(((1, Z0-1), (3, Z0-3), (5, Z0-5)))
    deg_hits, was_fallback = face_intersected_cells(deg, True, [0, 1, 0, 1], (0, 1, 0, 1), ev)
    assert was_fallback and deg_hits == {(r, c) for r in (0, 1) for c in (0, 1)}
    assert face_intersected_cells(deg, True, [-1, -1, -1, -1], (0, 1, 0, 1), ev)[0] == set()
    # Border cells are in the exact one-cell incident halo; the far cells are not.
    assert incident_cell_window((1, 3, 1, 3)) == (0, 2, 0, 2)
    try:
        _checked_cell_range([-1, 2, 0, 2], (0, 3, 0, 3))
    except AssertionError:
        pass
    else:
        raise AssertionError('mixed sentinel cell range was not rejected')
    try:
        _checked_cell_range([0, N - 1, 0, 1], (0, 3, 0, 3))
    except AssertionError:
        pass
    else:
        raise AssertionError('out-of-grid cell range was not rejected')

    # Exercise the real FaceRangeIndex.query_window API and the production mask
    # composition on a tiny in-memory shard. This does not open/load the full index.
    tiny = index_module.empty_arrays()
    face0 = _fixture_face(((1, Z0-1), (4, Z0-1), (2, Z0-4)), y=-100.0)
    face1 = _fixture_face(((13, Z0-13), (16, Z0-13), (14, Z0-16)), y=-100.0)
    tiny = {
        'kind': np.asarray([0, 1], dtype=np.uint8),
        'object_id': np.asarray([501, 502], dtype=np.int32),
        'model_id': np.asarray([7, 7], dtype=np.uint32),
        'face_id': np.asarray([11, 12], dtype=np.uint32),
        'xyz': np.asarray([face0, face1], dtype=np.float64),
        'plane_y_xz': np.zeros((2, 3), dtype=np.float64),
        'area_xz': np.asarray([3.0, 3.0], dtype=np.float64),
        'cell_range_rc': np.asarray([[0, 0, 0, 0], [2, 2, 2, 2]], dtype=np.int32),
        'degenerate': np.zeros(2, dtype=np.uint8),
    }
    real_api_index = object.__new__(index_module.FaceRangeIndex)
    real_api_index._shards = [({'records': 2}, tiny)]
    queried = real_api_index.query_window(0, 2, 0, 2)
    assert queried['object_id'].tolist() == [501, 502]
    heights = np.full((4, 4), 20.0, dtype=np.float32)
    p = np.full((3, 3), np.nan, dtype=np.float32)
    f = np.full((3, 3, 4), np.nan, dtype=np.float32)
    combined = make_masks(heights, p, f, queried, ev, vertex_window=(1, 3, 1, 3))
    assert combined['cell_reasons'][0, 0] & PHYSICAL_FACE
    assert combined['cell_reasons'][2, 2] & VISIBLE_FACE
    assert combined['blocked_vertices'][0, 0] and combined['blocked_vertices'][1, 1]
    return {
        'p_crossing_contact_freeze': True,
        'f_crossing_contact_freeze': True,
        'same_sign_finite_levels_not_blanket_frozen': True,
        'f_partial_nan_freeze_and_all_nan_nonfreeze': True,
        'shared_cell_boundary_touch_freezes_both_cells': True,
        'buried_compiled_face_still_freezes': True,
        'degenerate_bbox_conservative_freeze': True,
        'offmap_degenerate_sentinel_ignored': True,
        'window_border_incident_cell_halo': True,
        'malformed_mixed_sentinel_fail_closed': True,
        'out_of_grid_index_range_fail_closed': True,
        'real_ev87_geometry_and_face_index_query_api_mask_composition': True,
    }


def build_water_footprint(out_dir: Path) -> dict:
    """Read-only production pass. Requires an explicit fresh output directory."""
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise FileExistsError(f'output directory must be new: {out_dir}')
    source_before = sha(Path(__file__).resolve())
    input_hashes_start = verify_pins()
    plan = json.loads(INDEX_MANIFEST.read_text(encoding='utf-8'))
    verify = json.loads(INDEX_VERIFICATION.read_text(encoding='utf-8'))
    if plan.get('schema') != 'ev93.face-range-index.v1' or plan.get('status') != 'COMPLETE':
        raise AssertionError('EV93 index is not complete')
    if plan.get('base_identity', {}).get('terrain_sha256') != PINS[str(B)]:
        raise AssertionError('EV93 index terrain identity does not match pinned B')
    if verify.get('index_face_count') != 883308 or verify.get('status') != 'PASS_INDEX_AND_SAMPLED_EXPOSURE':
        raise AssertionError('pinned EV93 index verification is not the approved complete run')
    smoke = reusable_direct_smoke_evidence()

    t0 = time.perf_counter()
    ev87 = load_module('water_footprint_ev87', EV87)
    index_module = load_module('water_footprint_index', INDEX_SOURCE)
    with np.load(B, allow_pickle=False) as archive:
        if 'heights' not in archive.files:
            raise AssertionError('pinned B terrain NPZ has no heights')
        heights = archive['heights']
    p = np.load(P, allow_pickle=False)
    f = np.load(F, allow_pickle=False)
    if heights.shape != (N, N) or heights.dtype != np.float32:
        raise AssertionError('B height grid shape/dtype mismatch')
    if p.shape != (N - 1, N - 1) or f.shape != (N - 1, N - 1, 4):
        raise AssertionError('P/F grid shape mismatch')
    if p.dtype != np.float64 or f.dtype != np.float64:
        raise AssertionError(f'P/F dtype mismatch: P={p.dtype}, F={f.dtype}; expected float64')
    if np.isinf(p).any() or np.isinf(f).any():
        raise AssertionError('P/F contain infinity; only NaN encodes unknown')
    # One complete index load, one inclusive query over all cells incident to the
    # frozen vertex window, one reverify after clipping. No per-cell shard reload.
    t_index = time.perf_counter()
    index = index_module.FaceRangeIndex(INDEX_RUN)
    index_load_seconds = time.perf_counter() - t_index
    if index._manifest_sha != PINS[str(INDEX_MANIFEST)]:
        raise AssertionError('loaded FaceRangeIndex manifest pin mismatch')
    r0, r1, c0, c1 = CELL_WINDOW
    t_query = time.perf_counter()
    face_arrays = index.query_window(r0, r1, c0, c1)
    query_seconds = time.perf_counter() - t_query
    t_clip = time.perf_counter()
    masks = make_masks(heights, p, f, face_arrays, ev87)
    clip_and_water_mask_seconds = time.perf_counter() - t_clip
    t_reverify = time.perf_counter()
    index.reverify()
    if sha(Path(__file__).resolve()) != source_before:
        raise AssertionError('water-footprint source changed while running')
    input_hashes_end = verify_pins()
    if input_hashes_start != input_hashes_end:
        raise AssertionError('pinned input readset changed during mask construction')
    reverify_seconds = time.perf_counter() - t_reverify
    total_seconds = time.perf_counter() - t0

    # This routine is intentionally not run before integrator review. If invoked,
    # it creates only a report + mask artifact under a new caller-specified folder.
    out_dir.mkdir(parents=True, exist_ok=False)
    mask_path = out_dir / 'water-support-mask.npz'
    np.savez(mask_path,
             cell_reasons=masks['cell_reasons'],
             face_counts=masks['face_counts'],
             vertex_reasons=masks['vertex_reasons'],
             blocked_vertices=masks['blocked_vertices'])
    report = {
        'status': 'WATERSUPPORT_MASK_ONLY',
        'scope': 'compiled physical/visible XZ support + P/F crossing/contact/partial cells; no seed/solver/candidate/map verdict',
        'window_vertex_rc_half_open': list(WINDOW),
        'incident_cell_rc_inclusive': list(CELL_WINDOW),
        'grid': {'N': N, 'cell_m': CELL, 'Z0_m': Z0,
                 'native_corner_order': ['NW', 'NE', 'SW', 'SE'],
                 'native_triangles': [list(x) for x in TRIS],
                 'boundary_touch': 'topological intersection freezes both incident cells',
                 'degenerate_face': 'freeze all in-window cells from its validated inclusive bbox; off-map all-minus-one sentinel has no in-window support'},
        'index_load': {'loads': 1, 'queries': 1, 'query_window_inclusive': list(CELL_WINDOW),
                       'candidate_face_records': int(len(face_arrays['kind'])),
                       'complete_face_count': int(plan['counts']['faces']),
                       'manifest_sha256': PINS[str(INDEX_MANIFEST)],
                       'approx_arrays_resident_bytes': int(plan['counts']['faces'] * 134),
                       'approximation_note': 'sum of row-aligned NumPy array bytes only; excludes Python/allocator overhead and the query result copy',
                       'phase_seconds': {
                           'source_arrays_and_helpers_read': float(max(0.0, t_index - t0)),
                           'complete_index_load_once': float(index_load_seconds),
                           'single_halo_query': float(query_seconds),
                           'exact_xz_triangle_clipping_and_PF_mask': float(clip_and_water_mask_seconds),
                           'index_reverify_and_input_readset': float(reverify_seconds),
                           'total_before_output_write': float(total_seconds),
                       }},
        'reason_bits': {str(bit): name for bit, name in REASON_NAMES.items()},
        'counts': masks['counts'],
        'reused_real_direct_vs_index_smoke': smoke,
        'smoke_source': {'path': str(INDEX_VERIFICATION), 'sha256': PINS[str(INDEX_VERIFICATION)],
                         'meaning': 'existing verified three-cell direct ODOL-vs-index exposure evidence; not rerun here'},
        'pins_start': input_hashes_start,
        'pins_end': input_hashes_end,
        'source_sha256_start': source_before,
        'source_sha256_end': sha(Path(__file__).resolve()),
        'mask_artifact': {'path': str(mask_path), 'sha256': sha(mask_path)},
        'exclusions_from_this_mask': [
            'P9 corridor unknown cells remain governed by the existing P9 protection mask, not recreated here',
            'SEA floor is a height-bound contract, not a shoreline/contact mask in this artifact',
            'no water surface is declared safe, dry, or visually correct',
        ],
    }
    report_path = out_dir / 'water-support-mask.json'
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--self-test', action='store_true')
    group.add_argument('--mask-out', type=Path,
                       help='future production mode: write only WATERSUPPORT_MASK_ONLY into a fresh path')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps({'status': 'PASS_WATER_MASK_FIXTURES', 'fixtures': fixtures(),
                          'reused_real_direct_smoke': reusable_direct_smoke_evidence()}, sort_keys=True))
        return 0
    report = build_water_footprint(args.mask_out)
    print(json.dumps({'status': report['status'], 'mask_artifact': report['mask_artifact'],
                      'counts': report['counts']}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
