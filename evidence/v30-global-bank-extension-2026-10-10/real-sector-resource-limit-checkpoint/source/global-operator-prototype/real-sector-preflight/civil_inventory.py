#!/usr/bin/env python
"""Read-only, conservatively complete road/bridge support inventory.

This module uses the nine current B WRP placements and projects every
face-bearing LOD of the installed bridge model. LOD semantics are deliberately
not guessed: the result is a conservative union of visual/collision/roadway
candidate footprints, not a claim that one selected LOD is the engine's exact
collision surface. It does not solve or write terrain.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box

ROOT = Path(r'E:/DayZ-Baltic-Build')
G = ROOT / 'v30-global-bank-extension-20261010'
HERE = G / 'global-operator-prototype/real-sector-preflight'
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
PLAN = G / 'global-operator-prototype/PLAN_REAL_SECTOR.md'
DEPLOY = ROOT / 'v30-mixed-bank-incremental-fixed-20261010/deploy.json'
WORLD_PBO = Path(r'P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons/narva_trial.pbo')
WATER_PBO = Path(r'P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons/baltic_water_v30.pbo')
WRP = ROOT / 'v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
WRP_READER = W / 'tools/terrain/wrp0wzd.py'
ROAD_CHECKER = W / 'tools/terrain/verify_roads_v30.py'
ROAD_REFERENCE = Path(r'P:/DayZ_Baltic_12km_dev/tests/regional_foundation_roads_v6/reference.npz')
ROAD_CHAINS = W / 'evidence/regional-foundation-v1/road-grade-chains-v6.json'
BRIDGE_P3D = Path(r'P:/DZ/structures/roads/bridges/bridge_metal_25.p3d')
ODOL_READER = Path(r'C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts/odol_reader.py')
EV87 = ROOT / 'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
PBO_READER = W / 'tools/playtest/attach_navmesh.py'
INDEX_MANIFEST = ROOT / 'v30-global-bank-extension-20261010/ev93-face-index/runs/20261010T092417Z-63d4cec3/manifest.json'
INDEX_VERIFICATION = ROOT / 'v30-global-bank-extension-20261010/review-independent/runs/attempt-01/verification.json'

PINS = {
    str(PLAN): '14f02179312bc25caf76a087cc873122caed30f6092464f1c01ac7572d519749',
    str(DEPLOY): '3c98951f3488eef233d6972621648c84244f9e711c2ff419fd0b8013b427ec00',
    str(WORLD_PBO): 'b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c',
    str(WATER_PBO): '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14',
    str(WRP): '3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6',
    str(WRP_READER): '8b85cec46ba72851a4ec829c5b0adcc88727ee852c3f699ab7a15e31b50fee2a',
    str(ROAD_CHECKER): '2be9af6502077230028e5501de3b5c06cb2855c544deebf6147c22ceb9f9b8f8',
    str(ROAD_REFERENCE): '94ecbca61bd5ba9ba61f89b765b043676a4a65703729a0b69009ae233984a1c2',
    str(ROAD_CHAINS): 'b31fb7d72398981ee98132ce59eab48c4aa404043718475fbb2725b13de1b824',
    str(BRIDGE_P3D): 'baf79ddd19e08cdcdbec99b15043a319d6b958a1b7884082c2ae069cf3f3cee2',
    str(ODOL_READER): '688aaa90aa3caa1c8d036b6a573babd3d455086bdcd426e6e5ae04e3a93e8d4f',
    str(EV87): '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
    str(PBO_READER): '717b81469e0a799690d1586cd7a4492f079c3b2db626eec7e2815cd15896e062',
    str(INDEX_MANIFEST): 'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
    str(INDEX_VERIFICATION): 'b498e7d68835b199399655451e5e01ac81acb3149dbb9bf882b94858141521d4',
}
N, CELL, Z0 = 2048, 6.0, 12282.0
WINDOW = (712, 968, 242, 498)
BRIDGE_NAME = r'dz\structures\roads\bridges\bridge_metal_25.p3d'


def sha(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def check_pins() -> dict[str, str]:
    got = {p: sha(p) for p in PINS}
    bad = [f'{p}: {got[p]} != {want}' for p, want in PINS.items() if got[p] != want]
    if bad:
        raise RuntimeError('civil input pin mismatch: ' + '; '.join(bad))
    return got


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot load verified module: {path}')
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def sector_bounds() -> tuple[float, float, float, float]:
    r0, r1, c0, c1 = WINDOW
    return c0 * CELL, Z0 - r1 * CELL, c1 * CELL, Z0 - r0 * CELL


def cells_for_world_point(x: float, z: float) -> set[tuple[int, int]]:
    """Cells owning the sample; include both sides when it lies on a grid edge."""
    cf, rf = x / CELL, (Z0 - z) / CELL
    def axis_cells(v: float) -> tuple[int, ...]:
        n = round(v)
        if abs(v - n) <= 1e-7:
            return (int(n) - 1, int(n))
        return (math.floor(v),)
    rows, cols = axis_cells(rf), axis_cells(cf)
    r0, r1, c0, c1 = WINDOW
    return {(r, c) for r in rows for c in cols
            if r0 - 1 <= r < r1 and c0 - 1 <= c < c1}


def road_sample_cells() -> tuple[set[tuple[int, int]], dict]:
    road_data = np.load(ROAD_REFERENCE, allow_pickle=False)
    if 'xy' not in road_data:
        raise ValueError('road reference has no xy array')
    roads = road_data['xy']
    chain_doc = json.loads(ROAD_CHAINS.read_text(encoding='utf-8'))
    chains = chain_doc.get('chains')
    if not isinstance(chains, list):
        raise ValueError('road chain schema missing chains list')
    x0, z0, x1, z1 = sector_bounds()
    offsets = np.arange(-4.0, 4.0001, 0.5)
    cells: set[tuple[int, int]] = set()
    local_chains = []
    total_stations = total_samples = 0
    for chain_id, indices in enumerate(chains):
        points = roads[np.asarray(indices, dtype=np.int64)]
        if len(points) < 4:
            continue
        x0, z0, x1, z1 = sector_bounds()
        if (points[:, 0].max() < x0 - 11 or points[:, 0].min() > x1 + 11
                or points[:, 1].max() < z0 - 11 or points[:, 1].min() > z1 + 11):
            continue
        station = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
        if station[-1] <= 0:
            continue
        s = np.linspace(0.0, station[-1], int(np.ceil(station[-1])) + 1)
        q = np.column_stack([np.interp(s, station, points[:, d]) for d in (0, 1)])
        tangent = np.gradient(q, axis=0)
        norm = np.linalg.norm(tangent, axis=1)
        if np.any(norm <= 0):
            raise ValueError(f'zero tangent on chain {chain_id}; cannot invent a normal')
        normal = np.column_stack([-tangent[:, 1], tangent[:, 0]]) / norm[:, None]
        sample_count = 0
        for i, center in enumerate(q):
            cross = center[None, :] + normal[i][None, :] * offsets[:, None]
            # Include a 7m station halo for grade/chord comparisons at the sector edge.
            if not any((x0 - 7 <= x <= x1 + 7 and z0 - 7 <= z <= z1 + 7) for x, z in cross):
                continue
            for x, z in cross:
                point_cells = cells_for_world_point(float(x), float(z))
                if point_cells:
                    cells.update(point_cells)
                    sample_count += 1
        if sample_count:
            local_chains.append({'chain_id': int(chain_id), 'station_count': int(len(q)),
                                 'cross_samples_in_sector_halo': int(sample_count),
                                 'chain_length_m': float(station[-1])})
            total_stations += len(q)
            total_samples += sample_count
    return cells, {'source_chains': len(chains), 'intersecting_chains': local_chains,
                   'intersecting_chain_count': len(local_chains), 'stations_on_intersecting_chains': int(total_stations),
                   'lateral_samples_inside_sector_halo': int(total_samples),
                   'native_cells_rc_sorted': [list(x) for x in sorted(cells)],
                   'sample_rule': 'verify_roads_v30 station interpolation at 1m and offsets -4..4m every 0.5m; no bridge/water station exclusions',
                   'cell_rule': 'exact owning grid cell; both adjacent cells on an exact grid line'}


def bridge_face_cells() -> tuple[set[tuple[int, int]], dict]:
    wrp_reader = load_module('sector_wrp0wzd', WRP_READER)
    wrp = wrp_reader.read(WRP)
    objects = sorted((o for o in wrp['objects'] if o['name'].lower() == BRIDGE_NAME),
                     key=lambda o: int(o['id']))
    ids = [int(o['id']) for o in objects]
    if len(objects) != 9 or len(set(ids)) != 9:
        raise ValueError(f'expected nine unique current bridge WRP objects, found {len(objects)}')

    odol_dir = ODOL_READER.parent
    sys.path.insert(0, str(odol_dir))
    from odol_reader import ODOL
    model = ODOL.from_file(str(BRIDGE_P3D))
    lod_inventory = []
    face_lods = []
    for lod_index, lod in enumerate(model.lods):
        vertices = np.asarray([[v.x, v.y, v.z] for v in lod.vertices], dtype=np.float64)
        faces = [tuple(int(i) for i in face.vertex_indices) for face in lod.faces]
        if not np.isfinite(vertices).all():
            raise ValueError(f'nonfinite bridge vertices in LOD {lod_index}')
        if any(not face or min(face) < 0 or max(face) >= len(vertices) for face in faces):
            raise ValueError(f'invalid face topology in bridge LOD {lod_index}')
        lod_inventory.append({'lod_index': lod_index, 'resolution_read': float(lod.resolution),
                              'resolution_float32': float(np.float32(lod.resolution)),
                              'vertex_count': int(len(vertices)), 'face_count': int(len(faces))})
        if faces:
            face_lods.append((lod_index, float(lod.resolution), vertices, faces))
    if not face_lods:
        raise ValueError('bridge P3D has no face-bearing LOD')
    x0, z0, x1, z1 = sector_bounds()
    sector = box(x0 - CELL, z0 - CELL, x1 + CELL, z1 + CELL)
    cells: set[tuple[int, int]] = set()
    touched_faces_by_object_lod = {}
    conservative_projection_faces = 0
    object_inventory = []
    for obj in objects:
        matrix = np.asarray(obj['matrix'], dtype=np.float64)
        if matrix.shape != (12,) or not np.isfinite(matrix).all():
            raise ValueError(f'bridge WRP transform malformed for id {obj["id"]}')
        rotation = matrix[:9].reshape(3, 3)
        position = matrix[9:12]
        object_cells: set[tuple[int, int]] = set()
        lod_touched = {}
        for lod_index, resolution, local, faces in face_lods:
            world = position[None, :] + local @ rotation
            touched = 0
            for face in faces:
                coords = world[np.asarray(face, dtype=np.int64)][:, (0, 2)]
                if len(coords) >= 3:
                    geom = Polygon(coords)
                    if not geom.is_valid:
                        geom = geom.convex_hull
                        conservative_projection_faces += 1
                    elif geom.area == 0.0:
                        geom = LineString(coords).convex_hull
                        conservative_projection_faces += 1
                elif len(coords) == 2:
                    geom = LineString(coords)
                else:
                    geom = Polygon()
                if geom.is_empty or not geom.intersects(sector):
                    continue
                touched += 1
                minx, minz, maxx, maxz = geom.bounds
                c0 = max(0, WINDOW[2] - 1, math.floor(minx / CELL) - 1)
                c1 = min(N - 2, WINDOW[3] - 1, math.floor(maxx / CELL) + 1)
                r0 = max(0, WINDOW[0] - 1, math.floor((Z0 - maxz) / CELL) - 1)
                r1 = min(N - 2, WINDOW[1] - 1, math.floor((Z0 - minz) / CELL) + 1)
                for r in range(r0, r1 + 1):
                    for c in range(c0, c1 + 1):
                        cell = box(c * CELL, Z0 - (r + 1) * CELL,
                                   (c + 1) * CELL, Z0 - r * CELL)
                        if geom.intersects(cell):
                            object_cells.add((r, c))
            lod_touched[str(lod_index)] = {'resolution_read': resolution,
                                          'face_count_intersecting_sector_plus_6m': touched}
        cells.update(object_cells)
        touched_faces_by_object_lod[str(obj['id'])] = lod_touched
        object_inventory.append({'wrp_object_id': int(obj['id']), 'wrp_name': obj['name'],
                                 'wrp_matrix12': [float(x) for x in matrix],
                                 'position_xyz_m': [float(x) for x in position],
                                 'union_native_cells': int(len(object_cells))})
    return cells, {
        'wrp_object_count': len(objects), 'wrp_object_ids_sorted': ids,
        'objects': object_inventory, 'lod_inventory': lod_inventory,
        'face_bearing_lod_indices_projected': [x[0] for x in face_lods],
        'faces_intersecting_sector_plus_6m_by_object_lod': touched_faces_by_object_lod,
        'faces_using_conservative_projected_hull': int(conservative_projection_faces),
        'native_cells_intersecting_projected_face_bearing_lods': int(len(cells)),
        'native_cells_rc_sorted': [list(x) for x in sorted(cells)],
        'transform_contract': 'world = WRP position + local P3D vertices @ row-major WRP 3x3; source serialization is float32 WRP matrix',
        'coverage_policy': 'union of every face-bearing P3D LOD for every matching WRP object; no LOD labeled as exact collision/physical semantics',
        'limitations': ['offline projected model-face union; not an in-game collision readback',
                        'union conservatively freezes cell intersections from visual, roadway, shadow, or other face-bearing LODs',
                        'X/Z projection discards Y and can overprotect bridge-deck and support-beam footprints'],
    }


def pbo_and_index_guard() -> dict:
    ev87 = load_module('civil_inventory_ev87_guard', EV87)
    guard = ev87.pbo_guard(DEPLOY, WRP)
    required = ('expected_world_exact', 'expected_water_exact',
                'deployed_oprw_matches_manifest', 'staged_source_wrp_identity_exact')
    if not all(guard.get(key) is True for key in required):
        raise ValueError(f'EV87 PBO/OPRW guard failed: {guard}')
    deploy = json.loads(DEPLOY.read_text(encoding='utf-8'))
    manifest = json.loads(INDEX_MANIFEST.read_text(encoding='utf-8'))
    verification = json.loads(INDEX_VERIFICATION.read_text(encoding='utf-8'))
    base = manifest.get('base_identity', {})
    if manifest.get('status') != 'COMPLETE' or manifest.get('schema') != 'ev93.face-range-index.v1':
        raise ValueError('EV93 index manifest is not the pinned complete schema')
    checks = {
        'manifest_world_pbo_matches_deploy': base.get('world_pbo_sha256') == deploy['files']['narva_trial.pbo'],
        'manifest_water_pbo_matches_deploy': base.get('water_pbo_sha256') == deploy['files']['baltic_water_v30.pbo'],
        'manifest_compiled_oprw_matches_deploy': base.get('compiled_oprw_sha256') == deploy.get('compiled_wrp_sha256'),
        'manifest_source_wrp_matches_pinned_wrp': base.get('wrp_source_sha256') == sha(WRP),
        'verification_status': verification.get('status') == 'PASS_INDEX_AND_SAMPLED_EXPOSURE',
        'verification_manifest_sha_matches': verification.get('manifest_sha256') == sha(INDEX_MANIFEST),
        'verification_index_face_count': verification.get('index_face_count') == manifest.get('counts', {}).get('faces'),
    }
    if not all(checks.values()):
        raise ValueError(f'EV93 index/deployed OPRW identity guard failed: {checks}')
    return {'ev87_pbo_guard': guard, 'index_manifest_sha256': sha(INDEX_MANIFEST),
            'index_verification_sha256': sha(INDEX_VERIFICATION),
            'manifest_base_identity': base, 'index_face_counts': manifest.get('counts'),
            'checks': checks}


def build_report() -> dict:
    before = check_pins()
    deploy = json.loads(DEPLOY.read_text(encoding='utf-8'))
    if deploy.get('files', {}).get('narva_trial.pbo') != before[str(WORLD_PBO)]:
        raise ValueError('deployment manifest world PBO hash does not match deployed PBO')
    if deploy.get('files', {}).get('baltic_water_v30.pbo') != before[str(WATER_PBO)]:
        raise ValueError('deployment manifest water PBO hash does not match deployed PBO')
    if deploy.get('terrain_sha256') != 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0':
        raise ValueError('deployment manifest B terrain identity mismatch')
    compiled_identity = pbo_and_index_guard()
    road_cells, road = road_sample_cells()
    bridge_cells, bridge = bridge_face_cells()
    cells = sorted(road_cells | bridge_cells)
    r0, r1, c0, c1 = WINDOW
    vertices = set()
    for r, c in cells:
        vertices.update(((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)))
    local_vertices = [[r, c] for r, c in sorted(vertices)
                      if r0 <= r < r1 and c0 <= c < c1]
    after = check_pins()
    if before != after:
        raise RuntimeError('civil source readset changed during inventory')
    return {
        'status': 'PREPARED_CIVIL_SUPPORT_INVENTORY_ONLY',
        'source_hashes_before_after': {'before': before, 'after': after},
        'window_rc_half_open': list(WINDOW),
        'road': road,
        'bridge': bridge,
        'compiled_identity': compiled_identity,
        'summary': {'road_cells_in_sector_halo': len(road_cells),
                    'bridge_cells_in_sector_halo': len(bridge_cells),
                    'road_bridge_union_cells_rc_sorted': [list(x) for x in cells],
                    'union_cells': len(cells), 'sector_vertices_frozen_by_cell_support': len(local_vertices),
                    'sector_vertices_frozen_rc_sorted': local_vertices},
        'limits': ['road samples intentionally include stations normally omitted near Narva bridge/water',
                   'cell support is conservative and identifies vertices to freeze; it does not prove grade PASS',
                   'no solver, engine run or terrain write occurred'],
    }


def fixtures() -> dict:
    assert cells_for_world_point(1800.0, Z0 - 4800.0) == {(799, 299), (799, 300), (800, 299), (800, 300)}
    assert cells_for_world_point(1801.0, Z0 - 4800.0) == {(799, 300), (800, 300)}
    return {'grid_edge_assigns_both_cells': 'PASS', 'interior_grid_point_ownership': 'PASS'}


def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--self-test', action='store_true')
    group.add_argument('--report-out', type=Path)
    args = ap.parse_args()
    if args.self_test:
        print(json.dumps({'status': 'PASS_CIVIL_FIXTURES', 'fixtures': fixtures()}, sort_keys=True))
        return 0
    report = build_report()
    out = args.report_out.resolve()
    if out.exists():
        raise FileExistsError(f'refuse overwrite: {out}')
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = out.with_suffix(out.suffix + '.tmp')
    temp.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temp.replace(out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
