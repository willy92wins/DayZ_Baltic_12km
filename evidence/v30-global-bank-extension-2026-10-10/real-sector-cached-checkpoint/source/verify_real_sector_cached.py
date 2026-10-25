"""Independent, read-only consumer for the one Narva real-sector ADMM run.

This module is deliberately not an author/solver.  It rebuilds the domain,
physical bounds, objective and D8 constraints from pinned inputs, then checks
the published primal/duals and float32 result.  No candidate is inspected by
the fixture mode.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import sparse

ROOT = Path(r'E:/DayZ-Baltic-Build')
G = ROOT / 'v30-global-bank-extension-20261010'
HERE = G / 'global-operator-prototype/real-sector-preflight'
PLAN = G / 'global-operator-prototype/PLAN_REAL_SECTOR.md'
EV87_PATH = ROOT / 'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
EV88_PATH = ROOT / 'v30-wide-bank-fairing-pilot-20261010/review-independent/verify_ev88q.py'
EV91_PATH = ROOT / 'v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py'
CV_PATH = ROOT / 'v30-global-strict-bank-relief-20261010/review-independent/verify_coverage_contract.py'
LAYER_PATH = G / 'consumer-global/verify_layer.py'
PREP_PATH = HERE / 'prepare_inventory.py'
WATER_PATH = HERE / 'prepare_water_footprint.py'
CIVIL_PATH = HERE / 'civil_inventory.py'
SOLVE_DRIVER = HERE / 'solve_real_sector_cached.py'
PROTO_PATH = G / 'global-operator-prototype/prototype.py'
D8_PATH = G / 'constrained-pilot/d8_sparse_pilot.py'
EV82_PATH = ROOT / 'v30-mixed-bank-incremental-fixed-20261010/author.py'
PBO_READER_PATH = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/playtest/attach_navmesh.py')

B_PATH = ROOT / 'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
O_PATH = ROOT / 'v30-narva-dry-bank-relief-20261010/candidate/terrain.npz'
CONS_PATH = ROOT / 'v30-narva-dry-bank-relief-20261010/constraints.npz'
PRIOR_PATH = ROOT / 'v30-remaining-exact-dry-support-20261009/constraints.npz'
P_PATH = ROOT / 'v30-narva-dry-bank-relief-20261010/candidate/plane.npy'
F_PATH = ROOT / 'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy'
QUEUE_PATH = G / 'queue/queue.json'
CORRIDORS_PATH = Path(r'E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson')
DECISION_PATH = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/evidence/v30-navigation-contract-2026-10-08/decision.json')
DEPLOY_PATH = ROOT / 'v30-mixed-bank-incremental-fixed-20261010/deploy.json'
WRP_PATH = ROOT / 'v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
INDEX_SOURCE = G / 'ev93-face-index/build_face_index.py'
INDEX_DIR = G / 'ev93-face-index/runs/20261010T092417Z-63d4cec3'
INDEX_MANIFEST = INDEX_DIR / 'manifest.json'
INDEX_VERIFICATION = G / 'review-independent/runs/attempt-01/verification.json'
BOUNDS_PATH = ROOT / 'v30-low-water-components-20261009/compiled-instance-bounds.json'
WORLD_MOD = Path(r'P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1')
WATER_MODELS = ROOT / 'v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30'
INVENTORY_DIR = HERE / 'inventory-run-02.json'
INVENTORY_JSON = INVENTORY_DIR / 'inventory.json'
DOMAIN_NPZ = INVENTORY_DIR / 'domain-reasons.npz'
WATER_DIR = HERE / 'water-run-01'
WATER_JSON = WATER_DIR / 'water-support-mask.json'
WATER_NPZ = WATER_DIR / 'water-support-mask.npz'
CIVIL_JSON = HERE / 'civil-run-01.json'
CIVIL_RECEIPT = HERE / 'civil-run-01-receipt.json'

N = 2048
SEA = 0.85
EPS_WATER = 1e-4
MAX_DELTA = 2.0
CELL = 6.0
Z0 = 12282.0
WINDOW = (712, 968, 242, 498)  # half-open global vertex coordinates
CONTEXT = (710, 970, 240, 500)  # 2-vertex fixed halo around WINDOW
FOCUS = (840, 370)
TRIS = ((0, 1, 3), (0, 2, 3))
CORNER_OFFSETS = ((0, 0), (0, 1), (1, 0), (1, 1))

PINS = {
    PLAN: '14f02179312bc25caf76a087cc873122caed30f6092464f1c01ac7572d519749',
    EV87_PATH: '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
    EV88_PATH: '82a988790e6bdfc0289bcb7c32cb0afd1210e07b264d92731aba266bc5980f78',
    EV91_PATH: '5e726b93642f5db531193a8f1d85afabd139c7b9ac3afca4479df793afd53668',
    CV_PATH: '214f0eddda08d84ce18c921fcdbe01298f608c9a5c19b7e5246bb9e71df5dc2b',
    LAYER_PATH: '33050881caaf5e75f288d4122222c15eb326bf146c28a4c723760564457b3dc2',
    PREP_PATH: '239e0632046c84d00f7bcb677a16f7bd5245b10a174c0fe3e99a63d4ff90f6e7',
    WATER_PATH: '9f5f9952aaa23f5d673ec4c8375a2cc0d0759e0634d3093a08e23c50437728f1',
    CIVIL_PATH: '60d1beb2a36739a98fc70dc5a3b29033286e14abbc87461247bc87dd6f48c0c3',
    PROTO_PATH: '5b4b8f08e5205e1f9cc90bcc8e82e61dade45bb82bd22da8ee69303aa4475cc4',
    D8_PATH: '6b5281d9750c30fc5b27171aaec2af59dee88411a66bf5b08e5105866f08252c',
    PBO_READER_PATH: '717b81469e0a799690d1586cd7a4492f079c3b2db626eec7e2815cd15896e062',
    SOLVE_DRIVER: '5e75e0e1d3e3c6938679cd31e87f4f317353e64ff919c471d79d1a04d50f98f9',
    EV82_PATH: '9b7c5374b7c78c3604bb2763ef8b7b4d16dc4bf18fc57091233ad435876cb74b',
    B_PATH: 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    O_PATH: 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c',
    CONS_PATH: 'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
    PRIOR_PATH: '18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370',
    P_PATH: '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
    F_PATH: 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
    QUEUE_PATH: 'cf13887c8de031d65d0a32dab217e8743293103fcd00ea3c07c281c07a6794c9',
    CORRIDORS_PATH: '28866a8cf6ff57f2f825228046164ef939bc22bca9948eb96fe2463da46af343',
    DECISION_PATH: 'd510af67cc4016a0ba7192aa01c070d314b9bc7e49b6256ca6ffaf64fc05b843',
    DEPLOY_PATH: '3c98951f3488eef233d6972621648c84244f9e711c2ff419fd0b8013b427ec00',
    WRP_PATH: '3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6',
    INDEX_SOURCE: 'd1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e',
    INDEX_MANIFEST: 'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
    INDEX_VERIFICATION: 'b498e7d68835b199399655451e5e01ac81acb3149dbb9bf882b94858141521d4',
    BOUNDS_PATH: '863e9539203e59fe77b9c7d4949da3a69b4991249941e15b887b60ff9e81ee62',
    WORLD_MOD / 'Addons/narva_trial.pbo': 'b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c',
    WORLD_MOD / 'Addons/baltic_water_v30.pbo': '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14',
    INVENTORY_JSON: 'a1d656fff3b0bd7b2435893ff5e57a0ca92df2068f0db024291bc1409b8eb967',
    DOMAIN_NPZ: '4a4b3d652c983bc1a6f22dbdf1a359dcb8902591317b5b26126ef02f704abcbf',
    WATER_JSON: '74bb37147e20047c44f0228d464650fb35fb9e41e71cf541c4e994f1032c55c9',
    WATER_NPZ: '6ce282962602557636bafac40b604caa3001a95234551db1beee67975dcd1edf',
    CIVIL_JSON: '1f1670961bd89bfe284ac3175201c1dc2529f6c5b13bb7f4796fab4ac382cd53',
    CIVIL_RECEIPT: 'bbd51127b6479adc31a79c8932eadf1549be3bd2de19429cbb14998abcd20f01',
}


def sha(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load_module(name: str, path: Path, expected_sha: str | None = None):
    if expected_sha is not None and sha(path) != expected_sha:
        raise AssertionError(f'pinned module source changed: {path}')
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot import pinned helper: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def check_readset(extra_expected: dict[Path | str, str] | None = None) -> dict[str, str]:
    actual = {}
    expected_pins = dict(PINS)
    if extra_expected:
        for key,value in extra_expected.items():
            path=Path(key)
            if path in expected_pins and expected_pins[path]!=value:
                raise AssertionError(f'conflicting pinned hashes for {path}')
            expected_pins[path]=value
    for raw, expected in expected_pins.items():
        path = Path(raw)
        got = sha(path)
        actual[str(path)] = got
        if got != expected:
            raise AssertionError(f'readset hash mismatch for {path}: {got} != {expected}')
    return actual


def coeffs(kind: str, r: int, c: int):
    if kind == 'xx':
        return ((r, c, 1.0), (r, c + 1, -2.0), (r, c + 2, 1.0))
    if kind == 'zz':
        return ((r, c, 1.0), (r + 1, c, -2.0), (r + 2, c, 1.0))
    if kind == 'xz':
        return ((r, c, -.25), (r, c + 2, .25), (r + 2, c, .25), (r + 2, c + 2, -.25))
    raise ValueError(kind)


def affected_stencils(shape: tuple[int, int], nodes: np.ndarray) -> list[tuple[str, int, int]]:
    """Enumerate deduplicated second-difference rows touching any variable."""
    h, w = shape
    variables = {tuple(map(int, x)) for x in np.asarray(nodes)}
    candidate = set()
    for r, c in variables:
        for dr in (0,):
            for dc in (-2, -1, 0): candidate.add(('xx', r + dr, c + dc))
        for dr in (-2, -1, 0): candidate.add(('zz', r + dr, c))
        for dr in (-2, -1, 0):
            for dc in (-2, -1, 0): candidate.add(('xz', r + dr, c + dc))
    output = []
    family_order={'xx':0,'zz':1,'xz':2}
    for kind, r, c in sorted(candidate,key=lambda item:(family_order[item[0]],item[1],item[2])):
        terms = coeffs(kind, r, c)
        if min(rr for rr, _, _ in terms) < 0 or max(rr for rr, _, _ in terms) >= h:
            continue
        if min(cc for _, cc, _ in terms) < 0 or max(cc for _, cc, _ in terms) >= w:
            continue
        if any((rr, cc) in variables for rr, cc, _ in terms):
            output.append((kind, r, c))
    return output


def build_objective_matrix(base_local: np.ndarray, nodes_local: np.ndarray):
    """Rebuild EV88 stencil/fidelity least-squares rows without author code."""
    nodes = np.asarray(nodes_local, dtype=np.int32)
    index = {tuple(map(int, rc)): i for i, rc in enumerate(nodes)}
    stencils = affected_stencils(base_local.shape, nodes)
    rows, cols, data, rhs = [], [], [], []
    row = 0
    for kind, r, c in stencils:
        scale = math.sqrt(2.0) if kind == 'xz' else 1.0
        fixed_sum = 0.0
        for rr, cc, coefficient in coeffs(kind, r, c):
            value = float(coefficient) * scale
            j = index.get((rr, cc))
            if j is None:
                fixed_sum += value * float(base_local[rr, cc])
            else:
                rows.append(row); cols.append(j); data.append(value)
        rhs.append(-fixed_sum); row += 1
    for j, (r, c) in enumerate(nodes.tolist()):
        rows.append(row); cols.append(j); data.append(.25)
        rhs.append(.25 * float(base_local[r, c])); row += 1
    A = sparse.csr_matrix((np.asarray(data, np.float64),
                           (np.asarray(rows, np.int32), np.asarray(cols, np.int32))),
                          shape=(row, len(nodes)))
    A.sort_indices()
    return A, np.asarray(rhs, np.float64), stencils


def build_d8_matrix(ev91, base_local: np.ndarray, nodes_local: np.ndarray):
    centers, witnesses, exempt = ev91.independent_d8(base_local, nodes_local)
    index = {tuple(map(int, rc)): i for i, rc in enumerate(np.asarray(nodes_local))}
    rows, cols, data, d = [], [], [], []
    for witness in witnesses:
        center = tuple(map(int, witness['center']))
        neighbor = tuple(map(int, witness['witness']))
        if witness['linear_row'] is None:
            continue
        row = len(d)
        ci, ni = index.get(center), index.get(neighbor)
        if ci is not None:
            rows.append(row); cols.append(ci); data.append(1.0)
        else:
            dval = float(base_local[center])
            rows.append(row); cols.append(ni); data.append(-1.0)
            d.append(-dval)
            continue
        if ni is not None:
            rows.append(row); cols.append(ni); data.append(-1.0)
            d.append(0.0)
        else:
            d.append(float(base_local[neighbor]))
    C = sparse.csr_matrix((np.asarray(data, np.float64),
                           (np.asarray(rows, np.int32), np.asarray(cols, np.int32))),
                          shape=(len(d), len(nodes_local)))
    C.sort_indices()
    return C, np.asarray(d, np.float64), witnesses, exempt, centers


def inward32(value: float, side: str) -> float:
    cast = np.float32(value)
    if side == 'lower' and float(cast) < value:
        cast = np.nextafter(cast, np.float32(np.inf), dtype=np.float32)
    elif side == 'upper' and float(cast) > value:
        cast = np.nextafter(cast, np.float32(-np.inf), dtype=np.float32)
    return float(cast)


def physical_bounds_ev82(original: np.ndarray, current: np.ndarray,
                         levels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Recompute the documented EV82 total-budget interval independently."""
    original = np.asarray(original, np.float64)
    current = np.asarray(current, np.float64)
    levels = np.asarray(levels, np.float64)
    if not (original.shape == current.shape == levels.shape):
        raise ValueError('budget array shapes differ')
    if not (np.isfinite(original).all() and np.isfinite(current).all()
            and np.isfinite(levels).all()):
        raise ValueError('non-finite EV79/B/P/F/SEA inputs')
    floor = np.minimum(original, levels + EPS_WATER)
    lo_raw = np.maximum.reduce((current - MAX_DELTA, floor,
                                np.minimum(original, 1.8), original - MAX_DELTA))
    hi_raw = np.minimum(current + MAX_DELTA, original + MAX_DELTA)
    lower = np.empty(current.shape, np.float64)
    upper = np.empty(current.shape, np.float64)
    for idx in np.ndindex(current.shape):
        lower[idx] = inward32(float(lo_raw[idx]), 'lower')
        upper[idx] = inward32(float(hi_raw[idx]), 'upper')
    return lower, upper


def corner_nodes(cells, r0: int, c0: int, local_shape: tuple[int, int]) -> set[tuple[int, int]]:
    nodes = set()
    nr, nc = local_shape
    for r, c in cells:
        for rr, cc in ((int(r), int(c)), (int(r), int(c)+1),
                       (int(r)+1, int(c)), (int(r)+1, int(c)+1)):
            if r0 <= rr < r0+nr and c0 <= cc < c0+nc:
                nodes.add((rr, cc))
    return nodes


def p9_unknown_cells(p: np.ndarray, corridors: dict, r0: int, c0: int,
                     row_range: tuple[int, int], col_range: tuple[int, int]) -> set[tuple[int, int]]:
    """Positive-area unknown-P cells intersecting any approved corridor geometry."""
    from shapely.geometry import box, shape
    from shapely.ops import unary_union
    rlo, rhi = row_range; clo, chi = col_range
    union = unary_union([shape(f['geometry']) for f in corridors['features']])
    result = set()
    for lr, lc in np.argwhere(~np.isfinite(p)).tolist():
        r, c = r0 + int(lr), c0 + int(lc)
        if r < rlo or r >= rhi or c < clo or c >= chi:
            continue
        cell = box(c*CELL, Z0-(r+1)*CELL, (c+1)*CELL, Z0-r*CELL)
        if union.intersection(cell).area > 0.0:
            result.add((r, c))
    return result


def verify_index_readset() -> dict:
    """Hash-only check; the complete ODOL index is not reloaded by this consumer."""
    manifest = json.loads(INDEX_MANIFEST.read_text(encoding='utf-8'))
    if manifest.get('status') != 'COMPLETE' or int(manifest.get('counts', {}).get('faces', -1)) != 883308:
        raise AssertionError('EV93 face index is not the pinned complete 883,308-face artifact')
    deploy=json.loads(DEPLOY_PATH.read_text(encoding='utf-8'))
    ident=manifest.get('base_identity',{})
    identity_checks={
        'world_pbo':ident.get('world_pbo_sha256')==deploy.get('files',{}).get('narva_trial.pbo')==sha(WORLD_MOD/'Addons/narva_trial.pbo'),
        'water_pbo':ident.get('water_pbo_sha256')==deploy.get('files',{}).get('baltic_water_v30.pbo')==sha(WORLD_MOD/'Addons/baltic_water_v30.pbo'),
        'source_wrp':ident.get('wrp_source_sha256')==sha(WRP_PATH),
        'compiled_oprw':ident.get('compiled_oprw_sha256')==deploy.get('compiled_wrp_sha256'),
        'bounds':ident.get('bounds_sha256')==sha(BOUNDS_PATH),
    }
    if not all(identity_checks.values()):
        raise AssertionError(f'face-index deployed identity mismatch: {identity_checks}')
    observed = []
    for shard in manifest.get('shards', []):
        path = INDEX_DIR / shard['path']
        got = sha(path)
        if got != shard['sha256']:
            raise AssertionError(f'index shard changed: {path}')
        observed.append({'path': str(path), 'sha256': got})
    for model in manifest.get('models', []):
        path = WATER_MODELS / model['basename']
        if sha(path) != model['sha256']:
            raise AssertionError(f'indexed ODOL model changed: {path}')
    return {'manifest_sha256': sha(INDEX_MANIFEST), 'shard_count': len(observed),
            'record_count': int(manifest['counts']['faces']), 'models_rehashed': len(manifest['models']),
            'base_identity_checks':identity_checks,
            'shards_sha256': hashlib.sha256(json.dumps(observed, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}


def reconstruct_static_domain(ev87, bundle, water_arrays, civil_report, inv_arrays):
    b = bundle['B']; cons = bundle['constraints']; prior = bundle['prior']
    heights = np.asarray(b['heights'], np.float32)
    levels = ev87.vertex_levels(bundle['P'], bundle['F'])
    eligible, _ = ev87._ev87_eligible(b, cons, prior, heights.astype(np.float64),
                                       bundle['P'], bundle['F'])
    r0, r1, c0, c1 = WINDOW
    expected_local = np.asarray(inv_arrays['ev87_eligible'], dtype=bool)
    if not np.array_equal(expected_local, eligible[r0:r1, c0:c1]):
        raise AssertionError('saved eligibility inventory differs from independent EV87 reconstruction')
    wm = np.asarray(water_arrays['blocked_vertices'], dtype=bool)
    if wm.shape != (r1-r0, c1-c0):
        raise AssertionError('water-mask shape mismatch')
    # Independently rebuild four-corner freeze from all water reason-bearing cells.
    cell_reasons = np.asarray(water_arrays['cell_reasons'])
    rebuilt = np.zeros_like(wm)
    for lr, lc in np.argwhere(cell_reasons != 0):
        gr, gc = r0-1+int(lr), c0-1+int(lc)
        for rr, cc in ((gr,gc),(gr,gc+1),(gr+1,gc),(gr+1,gc+1)):
            if r0 <= rr < r1 and c0 <= cc < c1:
                rebuilt[rr-r0,cc-c0] = True
    if not np.array_equal(rebuilt, wm):
        raise AssertionError('water mask blocked vertices do not equal union of reasoned-cell corners')
    civil_cells = set()
    for layer in ('road', 'bridge'):
        rows = civil_report.get(layer, {}).get('native_cells_rc_sorted')
        if not isinstance(rows, list):
            raise ValueError(f'civil report lacks {layer} frozen cells')
        civil_cells.update((int(x[0]),int(x[1])) for x in rows)
    civil_nodes = corner_nodes(civil_cells, r0, c0, wm.shape)
    corridors = bundle['corridors']
    p9_cells = p9_unknown_cells(bundle['P'][r0-1:r1, c0-1:c1], corridors,
                                r0-1, c0-1, (r0-1, r1), (c0-1, c1))
    p9_nodes = corner_nodes(p9_cells, r0, c0, wm.shape)
    final_domain = eligible[r0:r1,c0:c1] & ~wm
    for r,c in civil_nodes | p9_nodes:
        final_domain[r-r0,c-c0] = False
    return {'eligible': eligible, 'levels': levels, 'water_local': wm,
            'civil_cells': civil_cells, 'civil_nodes': civil_nodes,
            'p9_cells': p9_cells, 'p9_nodes': p9_nodes,
            'final_local': final_domain, 'levels_local': levels[r0:r1,c0:c1]}


def choose_seed_independent(queue: dict, final_local: np.ndarray):
    r0,r1,c0,c1 = WINDOW
    fr,fc = FOCUS
    if final_local[fr-r0,fc-c0]:
        row=next(x for x in queue['seeds'] if (int(x['row']),int(x['col']))==FOCUS)
        return {'kind':'explicit_focus','seed_id':int(row['seed_id']),'row':fr,'col':fc}
    eligible = [x for x in queue['seeds'] if x.get('state')=='first_layer'
                and r0<=int(x['row'])<r1 and c0<=int(x['col'])<c1
                and final_local[int(x['row'])-r0,int(x['col'])-c0]]
    if not eligible:
        return None
    row=min(eligible,key=lambda x:int(x['first_layer_id']))
    return {'kind':'queue_fallback','seed_id':int(row['seed_id']),
            'first_layer_id':int(row['first_layer_id']),
            'row':int(row['row']),'col':int(row['col'])}


def verify_candidate_local(preflight_path: Path, solve_dir: Path, bundle: dict,
                           modules: dict, hashes_start: dict, extra_pins: dict,
                           author_expected: dict[str,str]):
    ev87,ev88,ev91,layer,cv,civilmod,proto,d8 = (modules[k] for k in
        ('ev87','ev88','ev91','layer','cv','civil','proto','d8'))
    pre=json.loads(preflight_path.read_text(encoding='utf-8'))
    result_path=solve_dir/'solve-result.json'
    result=json.loads(result_path.read_text(encoding='utf-8'))
    if pre.get('status')!='PREFLIGHT_READY_ONLY' or result.get('status')!='SOLUTION_PENDING_INDEPENDENT_CONSUMER':
        raise AssertionError('author stage is not a converged solve pending independent acceptance')
    artifacts={'preflight':(preflight_path.resolve(),sha(preflight_path)),
               'solve_result':(result_path.resolve(),sha(result_path))}
    if Path(result.get('preflight_path','')).resolve()!=preflight_path.resolve() or result.get('preflight_sha256')!=artifacts['preflight'][1]:
        raise AssertionError('solve-result does not bind this exact preflight')
    prep_path=Path(pre['prepared_artifact']['path'])
    if sha(prep_path)!=pre['prepared_artifact']['sha256']:
        raise AssertionError('prepared matrix artifact hash mismatch')
    if Path(result.get('prepared_path','')).resolve()!=prep_path.resolve() or result.get('prepared_sha256')!=pre['prepared_artifact']['sha256']:
        raise AssertionError('solve-result prepared path/hash differs from preflight artifact')
    state_path=solve_dir/'solver-state.npz';candidate_path=solve_dir/'candidate-local.npz'
    expected_artifacts={'prepared':(prep_path.resolve(),pre['prepared_artifact']['sha256']),
                        'solver_state':(state_path.resolve(),result.get('solver_state_sha256')),
                        'candidate_local':(candidate_path.resolve(),result.get('candidate_sha256'))}
    if Path(result.get('solver_state_path','')).resolve()!=state_path.resolve() or Path(result.get('candidate_path','')).resolve()!=candidate_path.resolve():
        raise AssertionError('solve-result points to unexpected solver-state/candidate paths')
    for label,(path,expected) in expected_artifacts.items():
        if not expected or sha(path)!=expected:
            raise AssertionError(f'{label} artifact hash mismatch')
    artifacts.update(expected_artifacts)
    for key in ('source_hashes_start','source_hashes_end'):
        if pre.get(key)!=author_expected:
            raise AssertionError(f'preflight {key} differs from frozen author source map')
    if pre.get('driver_sha256_start_end') != [PINS[SOLVE_DRIVER],PINS[SOLVE_DRIVER]]:
        raise AssertionError('preflight driver source pin differs at start/end')
    if result.get('source_hashes_after')!=author_expected or result.get('driver_sha256_after')!=PINS[SOLVE_DRIVER]:
        raise AssertionError('solve-result reports source or driver drift')
    pbo_before=ev87.pbo_guard(DEPLOY_PATH,WRP_PATH)
    required_pbo=('expected_world_exact','expected_water_exact','deployed_oprw_matches_manifest','staged_source_wrp_identity_exact')
    if not all(pbo_before.get(k) is True for k in required_pbo):
        raise AssertionError(f'deployed PBO/WRP guard failed: {pbo_before}')
    guards=pre.get('deployed_artifact_guard_start_end',[None,None])
    if len(guards)!=2 or pbo_before!=guards[0] or pbo_before!=result.get('pbo_guard_before_solver'):
        raise AssertionError('preflight/solve PBO guard does not match current artifact identity')
    prepared=load_npz(prep_path)
    state=load_npz(state_path);candidate_local=load_npz(candidate_path)
    if not np.array_equal(state['nodes_local'],prepared['nodes_local']):
        raise AssertionError('solver state nodes differ from prepared ordering')
    nodes_local=np.asarray(prepared['nodes_local'],np.int32)
    context_r0,context_r1,context_c0,context_c1=CONTEXT
    nodes_global=nodes_local+np.asarray((context_r0,context_c0),np.int32)
    if not np.array_equal(candidate_local['nodes_local'],nodes_local):
        raise AssertionError('candidate-local nodes differ from independently pinned prepared nodes')
    if candidate_local['heights'].shape!=(260,260) or candidate_local['heights'].dtype!=np.float32:
        raise AssertionError('candidate-local height raster must be float32 260x260')
    if not np.array_equal(candidate_local['source_B_local'],prepared['base_local'],equal_nan=True):
        raise AssertionError('candidate-local source baseline differs from prepared B context')
    variable_local_mask=np.zeros(candidate_local['heights'].shape,dtype=bool)
    variable_local_mask[tuple(np.asarray(prepared['nodes_local'],dtype=np.int32).T)]=True
    if not np.array_equal(candidate_local['heights'][~variable_local_mask],
                          prepared['base_local'][~variable_local_mask]):
        raise AssertionError('candidate-local changed a fixed context vertex')

    # Recompute selector/domain from the frozen source artifacts; do not trust author variables.
    with np.load(DOMAIN_NPZ,allow_pickle=False) as z: inv_arrays={k:z[k] for k in z.files}
    with np.load(WATER_NPZ,allow_pickle=False) as z: water_arrays={k:z[k] for k in z.files}
    civil_report=json.loads(CIVIL_JSON.read_text(encoding='utf-8'))
    road_cells,road_metrics=civilmod.road_sample_cells()
    bridge_cells,bridge_metrics=civilmod.bridge_face_cells()
    road_report_cells={tuple(map(int,x)) for x in civil_report['road']['native_cells_rc_sorted']}
    bridge_report_cells={tuple(map(int,x)) for x in civil_report['bridge']['native_cells_rc_sorted']}
    union_report_cells={tuple(map(int,x)) for x in civil_report['summary']['road_bridge_union_cells_rc_sorted']}
    civil_cells_exact=(road_cells==road_report_cells and bridge_cells==bridge_report_cells
                       and union_report_cells==road_cells|bridge_cells
                       and int(civil_report['summary']['union_cells'])==len(union_report_cells))
    domain=reconstruct_static_domain(ev87,bundle,water_arrays,civil_report,inv_arrays)
    selected=choose_seed_independent(json.loads(QUEUE_PATH.read_text(encoding='utf-8')),domain['final_local'])
    if selected is None or selected!=pre.get('selected_seed'):
        raise AssertionError('author-selected seed differs from independent frozen-mask selection')
    expected_nodes=np.argwhere(domain['final_local'])+np.asarray((WINDOW[0],WINDOW[2]),np.int32)
    if not np.array_equal(nodes_global,expected_nodes):
        raise AssertionError(f'variable domain mismatch: author={len(nodes_global)}, expected={len(expected_nodes)}')

    # Rebuild physical bounds and verify stored ADMM box bounds.
    bfull=np.asarray(bundle['B']['heights'],np.float32)
    ofull=np.asarray(bundle['EV79']['heights'],np.float32)
    levels=domain['levels']
    lo_full,hi_full=physical_bounds_ev82(ofull,bfull,levels)
    lower=lo_full[tuple(nodes_global.T)];upper=hi_full[tuple(nodes_global.T)]
    if not np.array_equal(prepared['lo'],lower) or not np.array_equal(prepared['hi'],upper):
        raise AssertionError('prepared inward float32 bounds differ from independent EV82/PF reconstruction')

    # Independently rebuild objective and D8 CSR, then compare every stored row and RHS.
    A,rhs,stencils=build_objective_matrix(prepared['base_local'],nodes_local)
    C,d,witnesses,exempt,centers=build_d8_matrix(ev91,prepared['base_local'],nodes_local)
    A_saved=sparse.csr_matrix((prepared['A_data'],prepared['A_indices'],prepared['A_indptr']),
                              shape=tuple(map(int,prepared['A_shape'])))
    C_saved=sparse.csr_matrix((prepared['C_data'],prepared['C_indices'],prepared['C_indptr']),
                              shape=tuple(map(int,prepared['C_shape'])))
    if (A.shape!=A_saved.shape or C.shape!=C_saved.shape
            or not np.array_equal(A.indptr,A_saved.indptr) or not np.array_equal(A.indices,A_saved.indices)
            or not np.array_equal(A.data,A_saved.data) or not np.array_equal(rhs,prepared['rhs'])
            or not np.array_equal(C.indptr,C_saved.indptr) or not np.array_equal(C.indices,C_saved.indices)
            or not np.array_equal(C.data,C_saved.data) or not np.array_equal(d,prepared['d'])):
        raise AssertionError('prepared A/C/RHS differs from independent stencil/D8 reconstruction')
    x=np.asarray(state['x64'],np.float64); yb=np.asarray(state['y_box'],np.float64); yd=np.asarray(state['y_d8'],np.float64)
    zb=np.asarray(state['z_box'],np.float64); zd=np.asarray(state['z_d8'],np.float64)
    if any(a.ndim!=1 for a in (x,yb,yd,zb,zd)) or x.shape!=(len(nodes_local),) or yb.shape!=x.shape or zb.shape!=x.shape or yd.shape!=(C.shape[0],) or zd.shape!=yd.shape:
        raise AssertionError('ADMM primal/dual vector dimensions mismatch')
    rho=float(result['diagnostics']['rho'])
    if not math.isfinite(rho) or rho<=0:
        raise AssertionError('invalid final ADMM rho')
    primal_box=float(np.max(np.abs(x-zb),initial=0.0))
    primal_d8=float(np.max(np.abs(C@x-zd),initial=0.0))
    box_feas=float(max(np.max(lower-x,initial=0),np.max(x-upper,initial=0)))
    d8_feas=float(np.max(d-C@x,initial=0.0))
    # y_box/y_d8 saved by the solver are unscaled multipliers (it rescales them on rho changes).
    stationarity=np.asarray(A.T@(A@x-rhs)).reshape(-1)+yb+np.asarray(C.T@yd).reshape(-1)
    stationarity_inf=float(np.max(np.abs(stationarity),initial=0.0))
    diag=result.get('diagnostics',{})
    # Reconstruct the frozen solver's stopping scales from saved primal/dual
    # vectors; a large tolerance written by the producer is not an acceptance gate.
    infnorm=lambda values: float(np.max(np.abs(values),initial=0.0))
    eps_p=1e-10+1e-8*max(infnorm(x),infnorm(C@x),infnorm(zb),infnorm(zd))
    eps_d=1e-10+1e-8*infnorm(yb+np.asarray(C.T@yd).reshape(-1))
    reported_eps_match=(math.isclose(float(diag.get('eps_primal',math.nan)),eps_p,rel_tol=1e-12,abs_tol=1e-18)
                        and math.isclose(float(diag.get('eps_dual',math.nan)),eps_d,rel_tol=1e-12,abs_tol=1e-18))
    dual_sign_bad=int(np.count_nonzero(yd>1e-12))
    box_normal=float(np.max(np.abs(np.clip(zb+yb/rho,lower,upper)-zb),initial=0.0))
    d8_normal=float(np.max(np.abs(np.maximum(zd+yd/rho,d)-zd),initial=0.0))
    kkt_ok=(diag.get('status')=='CONVERGED' and reported_eps_match and math.isfinite(eps_p) and math.isfinite(eps_d)
            and box_feas<=eps_p and d8_feas<=eps_p and primal_box<=eps_p and primal_d8<=eps_p
            and stationarity_inf<=eps_d and dual_sign_bad==0 and box_normal<=1e-10 and d8_normal<=1e-10)

    # Verify the one float32 cast and the closure contract independently: every
    # final variable equals the raw cast or its immediate upward ULP, and closure
    # may only increase the objective within the fixed numerical budget.
    raw32=np.asarray(state['raw_float32'],dtype=np.float32)
    if raw32.shape!=(260,260):
        raise AssertionError('solver raw_float32 raster must be 260x260')
    raw_expected=np.array(prepared['base_local'],dtype=np.float32,copy=True)
    raw_expected[tuple(nodes_local.T)]=x.astype(np.float32)
    if not np.array_equal(raw32,raw_expected):
        raise AssertionError('raw_float32 is not one direct cast of the solver primal over B-fixed context')

    # Compose the candidate in a private in-memory full-grid copy; metadata remains B.
    h_local=np.asarray(candidate_local['heights'],np.float32)
    raw_values=raw32[tuple(nodes_local.T)]
    final_values=h_local[tuple(nodes_local.T)]
    one_ulp=np.nextafter(raw_values,np.float32(np.inf),dtype=np.float32)
    closure_ok=bool(np.all((final_values==raw_values)|((final_values>raw_values)&(final_values<=one_ulp)))
                    and np.array_equal(h_local[~variable_local_mask],prepared['base_local'][~variable_local_mask]))
    raw_x=raw_values.astype(np.float64);final_x=final_values.astype(np.float64)
    raw_objective=.5*float(np.sum((A@raw_x-rhs)**2))
    final_objective=.5*float(np.sum((A@final_x-rhs)**2))
    closure_allowance=1e-7*max(1.0,raw_objective)
    closure_budget_ok=closure_ok and final_objective-raw_objective<=closure_allowance
    h_full=np.array(bfull,copy=True)
    h_full[context_r0:context_r1,context_c0:context_c1]=h_local
    changed=np.argwhere(h_full!=bfull).astype(np.int32)
    if not np.array_equal(changed,nodes_global[np.asarray(h_local[tuple(nodes_local.T)]!=prepared['x0'],bool)]):
        raise AssertionError('changed vertices are not an exact subset/equal set of solver variables')
    if not np.array_equal(h_full[tuple(nodes_global.T)],candidate_local['heights'][tuple(nodes_local.T)]):
        raise AssertionError('full-grid composition differs from solver-local output')
    changed_set={tuple(map(int,rc)) for rc in changed.tolist()}
    # Exact water/civil/P9 freezes: every touched frozen cell preserves all four B corners.
    water_mask=np.asarray(water_arrays['cell_reasons'])!=0
    water_cell_r0,water_cell_c0=WINDOW[0]-1,WINDOW[2]-1
    water_cells={(water_cell_r0+int(r),water_cell_c0+int(c)) for r,c in np.argwhere(water_mask)}
    p9_cells=domain['p9_cells'];protected_cells=water_cells|domain['civil_cells']|p9_cells
    touched_cells=set(ev87._ev87_cells(changed.tolist()))
    protected_changed=changed_set & (domain['civil_nodes']|domain['p9_nodes'])
    for r,c in changed_set:
        for rr in (r-1,r):
            for cc in (c-1,c):
                if (rr,cc) in protected_cells:
                    protected_changed.add((r,c))
    if protected_changed:
        raise AssertionError(f'changed support touches water/civil/P9 freeze: {sorted(protected_changed)[:20]}')
    changed_outside=changed_set-set(map(tuple,nodes_global.tolist()))
    if changed_outside:
        raise AssertionError('candidate changed a nonmutable or out-of-window vertex')

    topology=ev88.topology_check(ev87,bfull.astype(np.float64),h_full.astype(np.float64),
                                  bundle['P'],bundle['F'],touched_cells)
    geom=ev88.local_sector_stats(ev87,bfull.astype(np.float64),h_full.astype(np.float64),changed.tolist())
    p99=ev88.p99_population_gate(ev87,geom['angles_b'],geom['angles_h'],bundle)
    wet_population=ev91.eligible_wet_support_diagnostic(ev88,ev87,bundle,geom['angles_b'],geom['angles_h'])
    del geom['angles_b'];del geom['angles_h']
    x0=np.asarray(prepared['x0'],np.float64)
    xh=h_full[tuple(nodes_global.T)].astype(np.float64)
    residual_b=A@x0-rhs;residual_h=A@xh-rhs
    objective_b=.5*float(residual_b@residual_b);objective_h=.5*float(residual_h@residual_h)
    curvature_rows=len(stencils)
    curvature_b=.5*float(residual_b[:curvature_rows]@residual_b[:curvature_rows])
    curvature_h=.5*float(residual_h[:curvature_rows]@residual_h[:curvature_rows])
    fidelity_b=.5*float(residual_b[curvature_rows:]@residual_b[curvature_rows:])
    fidelity_h=.5*float(residual_h[curvature_rows:]@residual_h[curvature_rows:])
    slope_gate=geom['slopes_le_max35_or_B']
    hinge_gate=geom['no_new_hinges_over_30_touched'] and geom['affected_sector_max_nonworse']
    corridor_b=ev88.corridor_depth_report(bfull,bundle['P'],bundle['corridors'],comparison=h_full)
    corridor_h=ev88.corridor_depth_report(h_full,bundle['P'],bundle['corridors'],comparison=bfull)
    corridor_geometry=all(float(x.get('coverage_error_m2',math.inf))<=1e-5 for x in corridor_h['corridors'])
    affected_depth=ev91.affected_corridor_depth_report(ev88,ev87,bundle,h_full,changed.tolist())
    bed=ev88.high_bed_floor_report(h_full,bundle['B'])
    p9_local_exact=not bool(changed_set & domain['p9_nodes'])
    p9_report=ev91.p9_unknown_preserved(p9_local_exact,corridor_h)
    minimum_check=local_new_minima(bfull,h_full,changed.tolist())
    d8_float32=ev91.check_d8_candidate(h_local,witnesses)
    # Since all compiled physical/visible face-intersection cells are four-corner fixed,
    # their input/output triangle surfaces are bit-identical; no full index reload is needed.
    cell_freeze_exact=all(all(np.asarray(bfull[r+dr,c+dc],dtype=np.float32).tobytes()==np.asarray(h_full[r+dr,c+dc],dtype=np.float32).tobytes()
                              for dr,dc in CORNER_OFFSETS) for r,c in water_cells)

    # Independent source/provenance rehash at end; no source changed during evaluation.
    hashes_end=check_readset(extra_pins)
    if hashes_start!=hashes_end:
        raise AssertionError('consumer source readset drifted during validation')
    artifact_hashes_end={key:sha(path) for key,(path,_) in artifacts.items()}
    if any(artifact_hashes_end[key]!=expected for key,(_,expected) in artifacts.items()):
        raise AssertionError('preflight, prepared, solve-result, state, or candidate changed during consumption')
    pbo_after=ev87.pbo_guard(DEPLOY_PATH,WRP_PATH)
    if pbo_after!=pbo_before or pbo_after!=result.get('pbo_guard_after_solver'):
        raise AssertionError('deployed PBO/WRP identity changed during consumption')
    seed_metric=seed_improved(bfull,h_full,selected,ev87)
    resource=result.get('resource_measurement') or {}
    resource_ok=(not resource.get('limit_violated',True)
                 and int(result.get('available_physical_bytes_before_solver',0))>=3*1024**3
                 and int(resource.get('peak_working_set_bytes',2**63-1))<=1536*1024**2
                 and float(resource.get('elapsed_seconds',math.inf))<=600.0)
    # final_x is the candidate's stored float32 heights promoted to float64;
    # check the actual quantized result against inward-rounded physical bounds.
    candidate_bounds_ok=bool(np.all(final_x>=lower.astype(np.float64)) and np.all(final_x<=upper.astype(np.float64)))
    gates={
        'source_readset_stable': hashes_start==hashes_end,
        'pbo_wrp_deployed_identity_stable':pbo_after==pbo_before,
        'reconstructed_variable_domain_exact':len(nodes_local)==int(pre['system']['variables']),
        'physical_bounds_and_float32_admm_kkt':bool(kkt_ok),
        'float32_bounds_one_ulp_closure_D8':bool(closure_budget_ok and candidate_bounds_ok and box_feas<=eps_p and d8_feas<=eps_p and d8_float32.get('pass',False)),
        'fixed_water_civil_P9_exact_B':not protected_changed and cell_freeze_exact and p9_local_exact and p9_report.get('pass',False),
        'civil_source_cells_rebuilt_and_fixed':bool(civil_cells_exact),
        'P_F_SEA_signs_and_crossings_within_1m':bool(topology['signs_preserved'] and topology['crossings_valid_and_within_1m']),
        'no_new_local_minima':bool(minimum_check['no_new_minima']),
        'objective_strictly_reduced':objective_h<objective_b,
        'global_slope_and_hinge_nonregression':bool(slope_gate and hinge_gate),
        'bank_interior_p99_and_bracket_counts_nonworse':bool(p99['pass']),
        'all_corridor_geometry_covered':bool(corridor_geometry and corridor_b.get('all_covered') and corridor_h.get('all_covered')),
        'affected_known_P_corridor_depth_ge_0_95m':bool(affected_depth['pass']),
        'high_navigable_bed_floor_1m':bool(bed['high_bed_floor_1m_pass']),
        'selected_seed_improved':bool(seed_metric['pass']),
        'solver_resource_limits':bool(resource_ok),
    }
    info={'selected_seed':selected,'variables':int(len(nodes_local)),'changed_vertices':int(len(changed)),
          'A_shape':list(A.shape),'A_nnz':int(A.nnz),'C_shape':list(C.shape),'C_nnz':int(C.nnz),
          'affected_stencils':len(stencils),'stencils_by_kind':{k:sum(x[0]==k for x in stencils) for k in ('xx','zz','xz')},
          'objective':{'B':objective_b,'H':objective_h,'curvature_B':curvature_b,'curvature_H':curvature_h,
                       'fidelity_B':fidelity_b,'fidelity_H':fidelity_h},
          'kkt':{'primal_box_inf':primal_box,'primal_d8_inf':primal_d8,'box_feasibility':box_feas,
                 'd8_feasibility':d8_feas,'stationarity_inf':stationarity_inf,'d8_dual_positive_count':dual_sign_bad,
                 'box_normal_cone_inf':box_normal,'d8_normal_cone_inf':d8_normal,
                 'eps_primal_reconstructed':eps_p,'eps_dual_reconstructed':eps_d,
                 'reported_tolerances_match_reconstruction':reported_eps_match,
                 'solver_reported':{k:diag.get(k) for k in ('iteration','cg_iterations','rho','primal','dual','eps_primal','eps_dual','stationarity')}},
         'topology':{k:v for k,v in topology.items() if not isinstance(v,list)},
         'topology_input_contract':{'baseline_storage_dtype':str(bfull.dtype),
             'candidate_storage_dtype':str(h_full.dtype),'evaluated_layers':['P','F','SEA'],
             'sea_level_m':float(ev88.SEA),'changed_incident_cells':len(touched_cells),
             'note':'topology_check receives B and post-cast H promoted from float32; cells are every grid cell incident to changed vertices'},
          'global_geometry':{k:v for k,v in geom.items() if k not in ('angles_b','angles_h','new_over30_examples_touched')},
          'p99':p99,'eligible_wet_support_diagnostic':wet_population,
          'corridor_depth':{'B':corridor_b,'H':corridor_h},
          'affected_corridor_depth':affected_depth,'high_bed':bed,
          'local_minima':minimum_check,'compiled_cell_freeze':{'water_cells':len(water_cells),'exact_B_corners':cell_freeze_exact},
          'resource_measurement':resource,'float32_closure':{'pass':closure_ok,'budget_pass':closure_budget_ok,
             'raw_cast_objective':raw_objective,'final_float32_objective':final_objective,
             'increase':final_objective-raw_objective,'allowance':closure_allowance,
             'candidate_within_inward_float32_bounds':candidate_bounds_ok},
          'seed_improvement':seed_metric,'civil_reconstruction':{'pass':civil_cells_exact,
             'road_cells':len(road_cells),'bridge_cells':len(bridge_cells),
             'road_sample_metrics':road_metrics,'bridge_object_count':bridge_metrics.get('wrp_object_count')},
          'readset_start':hashes_start,'artifact_hashes_start':{k:v[1] for k,v in artifacts.items()},
          'artifact_hashes_end':artifact_hashes_end,'deployed_pbo_guard':pbo_after,
          'global_surface_claim':'NOT_RUN: no map-wide verifier; this is a sector/offline consumer only'}
    return {'gates':gates,'information':info,'candidate_heights':h_full}


def local_new_minima(before,after,changed_rc):
    """Compare strict 8-neighbour minima only at centers whose neighborhoods changed."""
    centers={(int(r)+dr,int(c)+dc) for r,c in changed_rc for dr in (-1,0,1) for dc in (-1,0,1)}
    b=np.asarray(before);h=np.asarray(after);new=[]
    for r,c in centers:
        if not (0<r<b.shape[0]-1 and 0<c<b.shape[1]-1):
            continue
        bn=[b[r+dr,c+dc] for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc]
        hn=[h[r+dr,c+dc] for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc]
        before_min=all(float(b[r,c])<float(v) for v in bn)
        after_min=all(float(h[r,c])<float(v) for v in hn)
        if after_min and not before_min:new.append([r,c])
    return {'no_new_minima':not new,'new_minima_count':len(new),'examples':new[:50]}


def seed_improved(before, after, selected, ev87):
    r,c=int(selected['row']),int(selected['col'])
    b=np.asarray(before,np.float64); h=np.asarray(after,np.float64)
    bp=float(ev87._ev87_prominence_m(b,r,c))
    hp=float(ev87._ev87_prominence_m(h,r,c))
    return {'pass':bool(math.isfinite(bp) and math.isfinite(hp) and hp < bp),
            'baseline_prominence_m':bp,'candidate_prominence_m':hp,
            'improvement_m':bp-hp,
            'definition':'EV87 pinned local seed prominence; strictly lower candidate value'}


def self_fixtures() -> dict:
    # Exact stencil enumeration/matrix fixture: affine fields have zero curvature;
    # a quadratic field has a known positive xx response.
    b=np.fromfunction(lambda r,c: 7.0+0.5*r-0.25*c,(9,10),dtype=float).astype(np.float32)
    nodes=np.asarray([[4,4],[4,5],[5,4]],np.int32)
    A,rhs,st=build_objective_matrix(b,nodes)
    x=b[tuple(nodes.T)].astype(np.float64)
    assert np.max(np.abs(A@x-rhs))<1e-12
    q=np.fromfunction(lambda r,c: c*c,(9,10),dtype=float).astype(np.float32)
    Aq,rq,sq=build_objective_matrix(q,nodes)
    assert np.any(np.abs(Aq@q[tuple(nodes.T)].astype(np.float64)-rq)>0)
    # Boundary supports are clipped only when their full stencil lies in the raster.
    edge=affected_stencils((5,5),np.asarray([[0,0],[4,4]],np.int32))
    assert all(min(rr for rr,_,_ in coeffs(k,r,c))>=0 and max(rr for rr,_,_ in coeffs(k,r,c))<5
               and min(cc for _,cc,_ in coeffs(k,r,c))>=0 and max(cc for _,cc,_ in coeffs(k,r,c))<5
               for k,r,c in edge)
    # Inward float32 tests at nonrepresentable boundaries.
    lo=inward32(0.1,'lower');hi=inward32(0.1,'upper')
    assert lo>=0.1 and hi<=0.1
    # Physical budget allows upward movement when EV79 is above current B;
    # it must not silently impose H<=B.
    lower,upper=physical_bounds_ev82(np.asarray([2.0]),np.asarray([1.0]),np.asarray([0.85]))
    assert lower[0]>1.0 and upper[0]>1.0 and lower[0]<=upper[0]
    # Compare the independent absolute-bound formula with the pinned step-budget
    # and float32 inward-rounding APIs on nontrivial values.
    author=load_module('verify_fixture_ev82',EV82_PATH,PINS[EV82_PATH])
    d8=load_module('verify_fixture_d8',D8_PATH,PINS[D8_PATH])
    original,current,floor=2.137,1.043,0.9001
    dlo,dhi=author.original_budget_interval(original,current,floor,2.0)
    api_lo=float(d8.inward32_lower(current+dlo));api_hi=float(d8.inward32_upper(current+dhi))
    independent_lo,independent_hi=physical_bounds_ev82(np.asarray([original]),np.asarray([current]),np.asarray([floor]))
    assert api_lo==independent_lo[0] and api_hi==independent_hi[0]
    # Exercise the real topology consumer at the SEA plane using the stored
    # float32 geometry promoted to float64.  One inward movement keeps all
    # crossings within 1 m; flipping a wet endpoint must fail.
    ev87=load_module('verify_fixture_ev87',EV87_PATH,PINS[EV87_PATH])
    ev88=load_module('verify_fixture_ev88',EV88_PATH,PINS[EV88_PATH])
    ev91=load_module('verify_fixture_ev91',EV91_PATH,PINS[EV91_PATH])
    hb=np.asarray([[0.4,1.2],[1.2,0.4]],dtype=np.float32)
    hh=np.asarray([[0.45,1.15],[1.15,0.45]],dtype=np.float32)
    pp=np.zeros((1,1),dtype=np.float64)
    ff=np.full((1,1,4),np.nan,dtype=np.float64)
    topo=ev88.topology_check(ev87,hb.astype(np.float64),hh.astype(np.float64),pp,ff,{(0,0)})
    assert topo['signs_preserved'] and topo['crossings_valid_and_within_1m']
    assert topo['original_crossings_count']>0 and topo['max_crossing_shift_m']<=1.0
    bad=hh.copy();bad[0,0]=np.float32(0.9)
    topo_bad=ev88.topology_check(ev87,hb.astype(np.float64),bad.astype(np.float64),pp,ff,{(0,0)})
    assert not topo_bad['signs_preserved'] and not topo_bad['crossings_valid_and_within_1m']
    # The D8 helper consumes local coordinates; a real positive/negative pair
    # prevents accidentally checking witnesses in global-grid coordinates.
    witness=[{'center':[1,1],'witness':[1,2]}]
    d8_good=np.asarray([[0,0,0],[0,2,1],[0,0,0]],dtype=np.float32)
    d8_bad=np.asarray([[0,0,0],[0,0.5,1],[0,0,0]],dtype=np.float32)
    assert ev91.check_d8_candidate(d8_good,witness)['pass']
    assert not ev91.check_d8_candidate(d8_bad,witness)['pass']
    return {'status':'PASS','objective_rows':int(A.shape[0]),'stencil_rows':len(st),
            'quadratic_response_detected':True,'boundary_support_valid':True,
            'inward_float32_bounds':True,'EV82_upper_allows_raise_when_original_above_B':float(upper[0]),
            'pinned_EV82_D8_bound_parity':True,'real_topology_SEA_positive_negative':True,
            'real_D8_positive_negative_local_coordinates':True}


def verify_preflight_only(preflight_path: Path, bundle: dict, modules: dict,
                          hashes_start: dict, hashes_end: dict,
                          extra_pins: dict, author_expected: dict[str,str]) -> dict:
    """Independent exact reconstruction of the prepared real system, no solve/candidate."""
    ev87,ev88,ev91,civilmod=(modules[k] for k in ('ev87','ev88','ev91','civil'))
    preflight_path=preflight_path.resolve()
    pre=json.loads(preflight_path.read_text(encoding='utf-8'))
    if pre.get('status')!='PREFLIGHT_READY_ONLY':
        raise AssertionError('preflight status is not solver-ready')
    if pre.get('source_hashes_start')!=author_expected or pre.get('source_hashes_end')!=author_expected:
        raise AssertionError('preflight source hash maps do not exactly equal pinned author source inventory')
    if pre.get('driver_sha256_start_end')!=[PINS[SOLVE_DRIVER],PINS[SOLVE_DRIVER]]:
        raise AssertionError('preflight source driver identity is not pinned')
    if hashes_start!=hashes_end:
        raise AssertionError('consumer source readset changed during preflight review')
    prep_ref=pre.get('prepared_artifact') or {}
    prep_path=Path(prep_ref.get('path','')).resolve()
    if not prep_path.is_file() or sha(prep_path)!=prep_ref.get('sha256'):
        raise AssertionError('prepared artifact path/SHA is invalid')
    before_artifacts={'preflight':sha(preflight_path),'prepared':sha(prep_path)}
    prepared=load_npz(prep_path)
    r0,r1,c0,c1=WINDOW
    cr0,cr1,cc0,cc1=CONTEXT
    base_local=np.asarray(prepared['base_local'],np.float32)
    if base_local.shape!=(260,260) or not np.array_equal(
            base_local,bundle['B']['heights'][cr0:cr1,cc0:cc1],equal_nan=True):
        raise AssertionError('prepared Dirichlet context does not exactly match current B')
    with np.load(DOMAIN_NPZ,allow_pickle=False) as z: inv={k:z[k] for k in z.files}
    with np.load(WATER_NPZ,allow_pickle=False) as z: water={k:z[k] for k in z.files}
    civil_report=json.loads(CIVIL_JSON.read_text(encoding='utf-8'))
    domain=reconstruct_static_domain(ev87,bundle,water,civil_report,inv)
    road_cells,road_metrics=civilmod.road_sample_cells()
    bridge_cells,bridge_metrics=civilmod.bridge_face_cells()
    expected_union={tuple(map(int,x)) for x in civil_report['summary']['road_bridge_union_cells_rc_sorted']}
    actual_union=road_cells|bridge_cells
    civil_exact=(road_cells=={tuple(map(int,x)) for x in civil_report['road']['native_cells_rc_sorted']}
                 and bridge_cells=={tuple(map(int,x)) for x in civil_report['bridge']['native_cells_rc_sorted']}
                 and actual_union==expected_union)
    if not civil_exact:
        raise AssertionError('road/bridge cells rebuilt from frozen source geometry differ from civil report')
    queue=json.loads(QUEUE_PATH.read_text(encoding='utf-8'))
    selected=choose_seed_independent(queue,domain['final_local'])
    if selected is None or selected!=pre.get('selected_seed'):
        raise AssertionError('selected seed differs from independent frozen domain and queue policy')
    expected_nodes=np.argwhere(domain['final_local']).astype(np.int32)+np.asarray((r0,c0),np.int32)
    nodes=np.asarray(prepared['nodes_local'],np.int32)
    nodes_global=nodes+np.asarray((cr0,cc0),np.int32)
    if not np.array_equal(nodes_global,expected_nodes):
        raise AssertionError('prepared variable node set/order differs from independently rebuilt domain')
    if not np.array_equal(prepared['x0'],base_local[tuple(nodes.T)].astype(np.float64)):
        raise AssertionError('prepared initial vector is not exact B at variable nodes')
    lower,upper=physical_bounds_ev82(bundle['EV79']['heights'],bundle['B']['heights'],domain['levels'])
    if not np.array_equal(prepared['lo'],lower[tuple(nodes_global.T)]) or not np.array_equal(prepared['hi'],upper[tuple(nodes_global.T)]):
        raise AssertionError('prepared bounds differ from independently reconstructed EV82/P/F inward f32 bounds')
    A,rhs,stencils=build_objective_matrix(base_local,nodes)
    C,d,witnesses,exempt,centers=build_d8_matrix(ev91,base_local,nodes)
    A_saved=sparse.csr_matrix((prepared['A_data'],prepared['A_indices'],prepared['A_indptr']),
                              shape=tuple(map(int,prepared['A_shape'])))
    C_saved=sparse.csr_matrix((prepared['C_data'],prepared['C_indices'],prepared['C_indptr']),
                              shape=tuple(map(int,prepared['C_shape'])))
    matrix_equal=(A.shape==A_saved.shape and C.shape==C_saved.shape
                  and np.array_equal(A.indptr,A_saved.indptr) and np.array_equal(A.indices,A_saved.indices)
                  and np.array_equal(A.data,A_saved.data) and np.array_equal(rhs,prepared['rhs'])
                  and np.array_equal(C.indptr,C_saved.indptr) and np.array_equal(C.indices,C_saved.indices)
                  and np.array_equal(C.data,C_saved.data) and np.array_equal(d,prepared['d']))
    if not matrix_equal:
        raise AssertionError('prepared A/rhs/C/d differ from independent stencil and D8 rebuild')
    decode=lambda key: json.loads(np.asarray(prepared[key],np.uint8).tobytes().decode('utf-8'))
    canonical=lambda value:json.loads(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False))
    if (decode('witnesses_json')!=canonical(witnesses) or decode('exempt_json')!=canonical(exempt)
            or decode('centers_json')!=canonical(centers) or decode('stencils_json')!=canonical(stencils)):
        raise AssertionError('prepared D8 witnesses/exempt/centers or stencil order differs from independent rebuild')
    system=pre.get('system',{});elig=pre.get('eligibility',{})
    expected_dims={'variables':len(nodes),'stencils':len(stencils),'A_shape':list(A.shape),'A_nnz':int(A.nnz),
                   'D8_rows':int(C.shape[0]),'D8_nnz':int(C.nnz),'D8_witnesses':len(witnesses),
                   'D8_exempt_baseline_strict_minima':len(exempt),'local_context_shape':[260,260]}
    if any(system.get(k)!=v for k,v in expected_dims.items()):
        raise AssertionError('preflight summary counts/shapes differ from reconstructed prepared system')
    if elig.get('final_variables')!=len(nodes) or elig.get('water_blocked_vertices')!=int(domain['water_local'].sum()):
        raise AssertionError('preflight eligibility/water counts differ from independently rebuilt domain')
    pbo=ev87.pbo_guard(DEPLOY_PATH,WRP_PATH)
    required=('expected_world_exact','expected_water_exact','deployed_oprw_matches_manifest','staged_source_wrp_identity_exact')
    guards=pre.get('deployed_artifact_guard_start_end')
    if not all(pbo.get(k) is True for k in required) or guards!=[pbo,pbo]:
        raise AssertionError('preflight deployed PBO/OPRW guards do not equal current pinned identities')
    identity=pre.get('input_identity',{})
    expected_identity={'B_sha256':PINS[B_PATH],'EV79_sha256':PINS[O_PATH],
       'P_sha256':PINS[P_PATH],'F_sha256':PINS[F_PATH],
       'OPRW_sha256':pbo['deployed_oprw_entry_sha256'],
       'world_pbo_sha256':pbo['deployed_world_sha256'],
       'water_pbo_sha256':pbo['deployed_water_sha256'],
       'staged_wrp_sha256':pbo['staged_wrp_sha256']}
    if identity!=expected_identity:
        raise AssertionError('preflight input identity differs from pinned inputs/deployed guard')
    # Producer eligibility statistics are explicitly window-local (see its
    # `eligible = eligible_ind[r0:r1,c0:c1]` before writing the report).
    r0,r1,c0,c1=WINDOW
    expected_eligibility={'ev87_count':int(np.count_nonzero(domain['eligible'][r0:r1,c0:c1])),
       'final_variables':len(nodes),'water_blocked_vertices':int(domain['water_local'].sum()),
       'civil_cells_union':len(actual_union),'civil_blocked_vertices':len(domain['civil_nodes']),
       'P9_unknown_cells':len(domain['p9_cells']),'P9_blocked_vertices':len(domain['p9_nodes'])}
    eligibility_mismatches={k:{'reported':pre.get('eligibility',{}).get(k),'rebuilt':v}
        for k,v in expected_eligibility.items() if pre.get('eligibility',{}).get(k)!=v}
    if eligibility_mismatches:
        raise AssertionError(f'preflight domain summary counts differ from independently rebuilt masks: {eligibility_mismatches}')
    hashes_end2=check_readset(extra_pins)
    after_artifacts={'preflight':sha(preflight_path),'prepared':sha(prep_path)}
    if hashes_end2!=hashes_start or after_artifacts!=before_artifacts:
        raise AssertionError('preflight/source artifacts changed during independent review')
    return {'schema':'real-sector-preflight-independent-review.v1','status':'PASS_PREPARED_SYSTEM_RECONSTRUCTED',
            'preflight_path':str(preflight_path),'preflight_sha256':before_artifacts['preflight'],
            'prepared_path':str(prep_path),'prepared_sha256':before_artifacts['prepared'],
            'consumer_path':str(Path(__file__).resolve()),'consumer_sha256':sha(Path(__file__).resolve()),
            'source_hashes_start':hashes_start,'source_hashes_end':hashes_end2,
            'author_source_hashes_exact':author_expected,'selected_seed':selected,
             'domain':{'variables':len(nodes),'eligible_inventory_exact':True,
                       'eligibility_count_scope_rc_half_open':list(WINDOW),'water_corner_mask_exact':True,
                      'civil_cells_exact':civil_exact,'road_cells':len(road_cells),'bridge_cells':len(bridge_cells),
                      'p9_cells':len(domain['p9_cells'])},
            'bounds':{'count':len(nodes),'min_lower':float(np.min(lower[tuple(nodes_global.T)])),
                      'max_upper':float(np.max(upper[tuple(nodes_global.T)])),'exact_inward_float32_match':True},
            'matrices':{'A_shape':list(A.shape),'A_nnz':int(A.nnz),'C_shape':list(C.shape),'C_nnz':int(C.nnz),
                        'stencils':len(stencils),'D8_witnesses':len(witnesses),'exempt_minima':len(exempt),
                        'A_rhs_C_d_and_serialized_rows_exact':matrix_equal},
            'deployed_guard':pbo,'scope':'preflight only; no solver/candidate/render/DayZ acceptance'}


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--preflight',type=Path)
    parser.add_argument('--solve-dir',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--preflight-only-review',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        print(json.dumps(self_fixtures(),sort_keys=True)); return 0
    if args.preflight is None or args.output is None or (not args.preflight_only_review and args.solve_dir is None):
        parser.error('--preflight and --output are required; --solve-dir is required except for --preflight-only-review')
    if args.output.exists(): raise FileExistsError(args.output)
    started=time.perf_counter()
    ev87=load_module('verify_real_sector_ev87',EV87_PATH,PINS[EV87_PATH])
    ev88=load_module('verify_real_sector_ev88',EV88_PATH,PINS[EV88_PATH]); ev88.ev=ev87
    ev91=load_module('verify_real_sector_ev91',EV91_PATH,PINS[EV91_PATH])
    cv=load_module('verify_real_sector_cv',CV_PATH,PINS[CV_PATH]); cv.ev=ev87
    layer=load_module('verify_real_sector_layer',LAYER_PATH,PINS[LAYER_PATH])
    civil=load_module('verify_real_sector_civil',CIVIL_PATH,PINS[CIVIL_PATH])
    proto=load_module('verify_real_sector_proto',PROTO_PATH,PINS[PROTO_PATH])
    d8=load_module('verify_real_sector_d8',D8_PATH,PINS[D8_PATH])
    driver=load_module('verify_real_sector_driver',SOLVE_DRIVER,PINS[SOLVE_DRIVER])
    author_expected={str(Path(driver.SOURCE_PATHS[key])):driver.PINS[key] for key in driver.SOURCE_PATHS}
    if set(driver.PINS)!=set(driver.SOURCE_PATHS):
        raise AssertionError('frozen solver pin labels differ from source-path inventory')
    extra_pins={Path(path):expected for path,expected in civil.PINS.items()}
    extra_pins.update({Path(path):expected for path,expected in author_expected.items()})
    hashes_start=check_readset(extra_pins)
    self_sha_start=sha(Path(__file__).resolve())
    bundle=ev88.checked_sources()
    bundle['prior']=bundle['prior'] if 'prior' in bundle else bundle.get('prior_constraints',{})
    # checked_sources has the exact EV88 schema; preserve all keys and normalize only aliases.
    if 'prior' not in bundle:
        raise AssertionError('EV88 checked_sources did not expose prior constraints array bundle')
    index_readset=verify_index_readset()
    hashes_end=check_readset(extra_pins)
    if args.preflight_only_review:
        review=verify_preflight_only(args.preflight.resolve(),bundle,
          {'ev87':ev87,'ev88':ev88,'ev91':ev91,'civil':civil},hashes_start,hashes_end,
          extra_pins,author_expected)
        self_sha_end=sha(Path(__file__).resolve())
        review['consumer_source_stable']=self_sha_start==self_sha_end
        review['index_readset']=index_readset
        review['status']='PASS_PREPARED_SYSTEM_RECONSTRUCTED' if review['consumer_source_stable'] else 'FAIL_CONSUMER_SOURCE_DRIFT'
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(review,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        print(json.dumps({'status':review['status'],'report':str(args.output),'variables':review['domain']['variables']},sort_keys=True),flush=True)
        return 0 if review['status']=='PASS_PREPARED_SYSTEM_RECONSTRUCTED' else 1
    verified=verify_candidate_local(args.preflight.resolve(),args.solve_dir.resolve(),bundle,
       {'ev87':ev87,'ev88':ev88,'ev91':ev91,'layer':layer,'cv':cv,'civil':civil,'proto':proto,'d8':d8},
       hashes_start,extra_pins,author_expected)
    hashes_end=check_readset(extra_pins)
    self_sha_end=sha(Path(__file__).resolve())
    gates=verified['gates']
    gates['consumer_source_stable']=self_sha_start==self_sha_end
    status='PASS_REAL_SECTOR_OFFLINE' if all(gates.values()) else 'FAIL_REAL_SECTOR'
    report={'schema':'real-sector-consumer.v1','status':status,'scope':'single fixed 256x256 sector; offline geometry and solver KKT; no DayZ/render/global acceptance',
      'consumer_path':str(Path(__file__).resolve()),'consumer_sha256':sha(Path(__file__).resolve()),
      'source_hashes_start':hashes_start,'source_hashes_end':hashes_end,'index_readset':index_readset,
      'consumer_sha256_start':self_sha_start,'consumer_sha256_end':self_sha_end,
      'gates':gates,'information':{k:v for k,v in verified['information'].items()},
      'elapsed_consumer_seconds':time.perf_counter()-started,
      'limits':['No DayZ runtime/render confirmation.','No full-map/global acceptance.','Water mask proves changed support disjoint from its verified face-footprint/crossing cells; index is hash-checked, not reloaded.']}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':status,'gates_failed':[k for k,v in gates.items() if not v],
                      'report':str(args.output),'changed':verified['information']['changed_vertices']},sort_keys=True),flush=True)
    return 0 if status=='PASS_REAL_SECTOR_OFFLINE' else 1


if __name__=='__main__':
    raise SystemExit(main())
