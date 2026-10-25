from __future__ import annotations
import ctypes
from ctypes import wintypes
import hashlib, json, math, time
from pathlib import Path
import numpy as np

OUT = Path(r'E:/DayZ-Baltic-Build/v30-water-render-discriminator-20261010/coarse-terrain-sensitivity-ev95')
Z0 = 12282.0
NATIVE_STEP = 6.0
PATCH_STEP = 1.5
COARSE_STEPS = (2.0, 4.0, 8.0, 16.0, 32.0)
TIME_BUDGET_S = 180.0
MEMORY_BUDGET_BYTES = 512 * 1024 * 1024
B_PATH = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
EV95_PATH = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz')
P_PATH = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/build-focal/candidate/plane.npy')
F_PATH = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/build-focal/candidate/visible-field.npy')
PAIRS_PATH = Path(r'E:/DayZ-Baltic-Build/v30-water-object-boundaries-20261010/exact-pairs.json')
EXPECTED = {
    str(B_PATH): 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    str(EV95_PATH): '40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
    str(P_PATH): '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
    str(F_PATH): 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
    str(PAIRS_PATH): '3ead735f0008ec8fd7f20aedc0c0980f0e25eaf20061fb3943f71907d9224932',
}
OBJECT_IDS = (16812770, 16812771, 16812805, 16812815)

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t), ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t), ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t), ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t), ('PeakPagefileUsage', ctypes.c_size_t),
        ('PrivateUsage', ctypes.c_size_t),
    ]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def memory_bytes() -> tuple[int, int]:
    psapi = ctypes.WinDLL('Psapi.dll', use_last_error=True)
    kernel32 = ctypes.WinDLL('Kernel32.dll', use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    proc = kernel32.GetCurrentProcess()
    counters = PROCESS_MEMORY_COUNTERS_EX()
    counters.cb = ctypes.sizeof(counters)
    ok = psapi.GetProcessMemoryInfo(proc, ctypes.byref(counters), counters.cb)
    if not ok:
        raise ctypes.WinError()
    return int(counters.WorkingSetSize), int(counters.PeakWorkingSetSize)


def sample_tri(grid: np.ndarray, row_coord: np.ndarray, col_coord: np.ndarray) -> np.ndarray:
    """Sample a NW-SE triangular grid; coordinates are fractional array indices."""
    r = np.asarray(row_coord, dtype=np.float64)
    c = np.asarray(col_coord, dtype=np.float64)
    if r.shape != c.shape:
        raise ValueError('row/column coordinate shapes differ')
    ri = np.floor(r).astype(np.int64)
    ci = np.floor(c).astype(np.int64)
    if np.any(ri < 0) or np.any(ci < 0) or np.any(ri + 1 >= grid.shape[0]) or np.any(ci + 1 >= grid.shape[1]):
        raise ValueError('sample outside triangular grid')
    v = r - ri
    u = c - ci
    nw = grid[ri, ci].astype(np.float64)
    ne = grid[ri, ci + 1].astype(np.float64)
    sw = grid[ri + 1, ci].astype(np.float64)
    se = grid[ri + 1, ci + 1].astype(np.float64)
    upper = v <= u
    out = np.empty(r.shape, dtype=np.float64)
    out[upper] = nw[upper] * (1.0 - u[upper]) + ne[upper] * (u[upper] - v[upper]) + se[upper] * v[upper]
    lower = ~upper
    out[lower] = nw[lower] * (1.0 - v[lower]) + se[lower] * u[lower] + sw[lower] * (v[lower] - u[lower])
    return out


def sample_native(height: np.ndarray, x: np.ndarray, z: np.ndarray) -> np.ndarray:
    return sample_tri(height, (Z0 - np.asarray(z)) / NATIVE_STEP, np.asarray(x) / NATIVE_STEP)


def sample_cell_f(field: np.ndarray, x: np.ndarray, z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Sample F inside each 6 m cell, never blending values across cell boundaries."""
    rcoord = (Z0 - np.asarray(z, dtype=np.float64)) / NATIVE_STEP
    ccoord = np.asarray(x, dtype=np.float64) / NATIVE_STEP
    ri = np.floor(rcoord).astype(np.int64)
    ci = np.floor(ccoord).astype(np.int64)
    if np.any(ri < 0) or np.any(ci < 0) or np.any(ri >= field.shape[0]) or np.any(ci >= field.shape[1]):
        raise ValueError('F sample outside native cell grid')
    v = rcoord - ri
    u = ccoord - ci
    corners = field[ri, ci, :].astype(np.float64)
    upper = v <= u
    out = np.full(u.shape, np.nan, dtype=np.float64)
    ok_upper = upper & np.isfinite(corners[..., 0]) & np.isfinite(corners[..., 1]) & np.isfinite(corners[..., 3])
    out[ok_upper] = (corners[..., 0][ok_upper] * (1-u[ok_upper]) +
                     corners[..., 1][ok_upper] * (u[ok_upper]-v[ok_upper]) +
                     corners[..., 3][ok_upper] * v[ok_upper])
    ok_lower = (~upper) & np.isfinite(corners[..., 0]) & np.isfinite(corners[..., 2]) & np.isfinite(corners[..., 3])
    out[ok_lower] = (corners[..., 0][ok_lower] * (1-v[ok_lower]) +
                     corners[..., 3][ok_lower] * u[ok_lower] +
                     corners[..., 2][ok_lower] * (v[ok_lower]-u[ok_lower]))
    return out, np.stack((ri, ci), axis=-1)


def sample_p_cell(plane: np.ndarray, cell_rc: np.ndarray) -> np.ndarray:
    rc = np.asarray(cell_rc, dtype=np.int64)
    return plane[rc[..., 0], rc[..., 1]].astype(np.float64)


def bbox_world(obj: dict) -> tuple[float, float, float, float]:
    matrix = np.asarray(obj['wrp_matrix_3x3_plus_xyz'], dtype=np.float64)
    if matrix.shape != (12,) or not np.array_equal(matrix[:9], np.eye(3, dtype=np.float64).reshape(-1)):
        raise ValueError(f'non-identity WRP transform requires explicit bbox corner transform for object {obj["id"]}')
    pos = np.asarray(obj['wrp_position_xyz'], dtype=np.float64)
    bmin = np.asarray(obj['model_info']['bbox_min_visual'], dtype=np.float64)
    bmax = np.asarray(obj['model_info']['bbox_max_visual'], dtype=np.float64)
    if pos.shape != (3,) or not np.array_equal(pos, matrix[9:12]):
        raise ValueError(f'WRP origin mismatch for object {obj["id"]}')
    return (float(pos[0] + bmin[0]), float(pos[0] + bmax[0]),
            float(pos[2] + bmin[2]), float(pos[2] + bmax[2]))


def sample_axes(bounds: tuple[float, float, float, float]) -> tuple[np.ndarray, np.ndarray]:
    xmin, xmax, zmin, zmax = bounds
    # Sampling centers are anchored to 0.75 + k*1.5 m, avoiding native 6 m cell seams.
    kx0 = math.ceil((xmin - 0.75) / PATCH_STEP)
    kx1 = math.floor((xmax - 0.75) / PATCH_STEP)
    kz0 = math.ceil((Z0 - zmax - 0.75) / PATCH_STEP)
    kz1 = math.floor((Z0 - zmin - 0.75) / PATCH_STEP)
    xs = 0.75 + np.arange(kx0, kx1 + 1, dtype=np.float64) * PATCH_STEP
    zs = Z0 - (0.75 + np.arange(kz0, kz1 + 1, dtype=np.float64) * PATCH_STEP)
    return xs, zs


def coarse_surface(height: np.ndarray, x: np.ndarray, z: np.ndarray, step: float) -> np.ndarray:
    qcol = np.asarray(x, dtype=np.float64) / step
    qrow = (Z0 - np.asarray(z, dtype=np.float64)) / step
    c0 = int(np.floor(qcol.min())) - 1
    c1 = int(np.floor(qcol.max())) + 1
    r0 = int(np.floor(qrow.min())) - 1
    r1 = int(np.floor(qrow.max())) + 1
    rows = np.arange(r0, r1 + 1, dtype=np.int64)
    cols = np.arange(c0, c1 + 1, dtype=np.int64)
    xx, rr = np.meshgrid(cols.astype(np.float64) * step, rows.astype(np.float64) * step)
    zz = Z0 - rr
    sampled = sample_native(height, xx, zz)
    return sample_tri(sampled, qrow - r0, qcol - c0)


def stats(values: np.ndarray) -> dict:
    v = np.asarray(values, dtype=np.float64)
    v = v[np.isfinite(v)]
    if not len(v):
        return {'count': 0, 'min_m': None, 'median_m': None, 'p95_m': None, 'max_m': None, 'mean_m': None}
    return {'count': int(len(v)), 'min_m': float(np.min(v)), 'median_m': float(np.median(v)),
            'p95_m': float(np.quantile(v, .95)), 'max_m': float(np.max(v)), 'mean_m': float(np.mean(v))}


def summarize(h_native: np.ndarray, h_coarse: np.ndarray, p: np.ndarray, f: np.ndarray, mask: np.ndarray) -> dict:
    result = {'samples_in_visual_bbox': int(np.count_nonzero(mask))}
    for surface_name, surface in (('P_cell_plane', p), ('F_cell_corner_triangles', f)):
        valid = mask & np.isfinite(surface)
        submerged = valid & (h_native < surface)
        elevated = submerged & (h_coarse > surface)
        uplift = h_coarse[elevated] - surface[elevated]
        signed = h_coarse[submerged] - surface[submerged]
        result[surface_name] = {
            'finite_surface_samples': int(np.count_nonzero(valid)),
            'native_below_surface_samples': int(np.count_nonzero(submerged)),
            'coarse_above_surface_given_native_below': int(np.count_nonzero(elevated)),
            'fraction_coarse_above_given_native_below': (float(np.count_nonzero(elevated) / np.count_nonzero(submerged)) if np.any(submerged) else None),
            'coarse_minus_surface_where_native_below_m': stats(signed),
            'positive_uplift_coarse_minus_surface_m': stats(uplift),
        }
    return result


def fixtures() -> dict:
    # Exact affine plane is reproduced by the same NW-SE triangular interpolation at both resolutions.
    rr, cc = np.indices((15, 17), dtype=np.float64)
    xgrid = cc * 6.0
    zgrid = 120.0 - rr * 6.0
    affine = 2.3 + 0.125 * xgrid - 0.075 * zgrid
    xs = np.array([9.25, 31.75, 48.25, 72.25], dtype=np.float64)
    zs = np.array([109.25, 93.75, 68.25, 49.75], dtype=np.float64)
    exact = 2.3 + 0.125 * xs - 0.075 * zs
    sampled = sample_tri(affine, (120.0-zs)/6.0, xs/6.0)
    assert np.allclose(sampled, exact, rtol=0, atol=1e-12)
    step = 12.0
    rows = np.arange(0, 7, dtype=np.float64)
    cols = np.arange(0, 8, dtype=np.float64)
    coarse_xx, coarse_rr = np.meshgrid(cols*step, rows*step)
    coarse = sample_tri(affine, coarse_rr/6.0, coarse_xx/6.0)
    q = sample_tri(coarse, (120.0-zs)/step, xs/step)
    assert np.allclose(q, exact, rtol=0, atol=1e-12)
    # Per-cell F values stay separate at a seam; no cross-cell averaging is performed.
    ff = np.full((2, 2, 4), np.nan, dtype=np.float64)
    ff[0, 0, :] = 3.0
    ff[0, 1, :] = 9.0
    f_west, _ = sample_cell_f(ff, np.array([6.0-1e-6]), np.array([Z0-3.0]))
    f_east, _ = sample_cell_f(ff, np.array([6.0+1e-6]), np.array([Z0-3.0]))
    assert abs(f_west[0]-3.0) < 1e-12 and abs(f_east[0]-9.0) < 1e-12
    # Reject out-of-grid coordinates rather than clipping/extrapolating.
    try:
        sample_tri(np.zeros((3, 3), np.float64), np.array([0.0]), np.array([-0.01]))
    except ValueError:
        outside_rejected = True
    else:
        raise AssertionError('outside-grid sample was accepted')
    return {'affine_native_exact': True, 'affine_resampled_coarse_exact': True,
            'F_cell_seam_not_averaged': True, 'outside_grid_rejected': outside_rejected}


def run() -> dict:
    started = time.perf_counter()
    process_peak = memory_bytes()[1]
    input_start = {name: sha(Path(name)) for name in EXPECTED}
    for name, want in EXPECTED.items():
        if input_start[name] != want:
            raise ValueError(f'input SHA mismatch: {name}: {input_start[name]} != {want}')
    pairs = json.loads(PAIRS_PATH.read_text(encoding='utf-8-sig'))
    objs = []
    for oid in OBJECT_IDS:
        rec = pairs['objects'][str(oid)]
        bounds = bbox_world(rec)
        objs.append({'id': oid, 'wrp_model': rec['wrp_model'], 'bbox_world_xz_m': list(bounds), 'bounds': bounds,
                     'bbox_visual_local_xz_m': [rec['model_info']['bbox_min_visual'][0], rec['model_info']['bbox_min_visual'][2],
                                                rec['model_info']['bbox_max_visual'][0], rec['model_info']['bbox_max_visual'][2]],
                     'wrp_position_xyz': rec['wrp_position_xyz']})
    union = (min(o['bounds'][0] for o in objs), max(o['bounds'][1] for o in objs),
             min(o['bounds'][2] for o in objs), max(o['bounds'][3] for o in objs))
    xs, zs = sample_axes(union)
    xx, zz = np.meshgrid(xs, zs)
    xflat, zflat = xx.ravel(), zz.ravel()
    point_count = len(xflat)
    if point_count > 10000:
        raise ValueError(f'ROI sample count unexpectedly large: {point_count}')
    sample_mask = {}
    for o in objs:
        xmin, xmax, zmin, zmax = o['bounds']
        sample_mask[str(o['id'])] = ((xflat >= xmin) & (xflat <= xmax) & (zflat >= zmin) & (zflat <= zmax))
    with np.load(B_PATH, allow_pickle=False) as arc:
        B = np.array(arc['heights'], copy=True)
    with np.load(EV95_PATH, allow_pickle=False) as arc:
        E = np.array(arc['heights'], copy=True)
    if B.shape != (2048, 2048) or E.shape != B.shape:
        raise ValueError(f'unexpected terrain height shapes {B.shape} {E.shape}')
    P = np.load(P_PATH, mmap_mode='r', allow_pickle=False)
    F = np.load(F_PATH, mmap_mode='r', allow_pickle=False)
    if P.shape != (B.shape[0]-1, B.shape[1]-1) or F.shape != (B.shape[0]-1, B.shape[1]-1, 4):
        raise ValueError(f'unexpected P/F shape {P.shape} {F.shape}')
    b_native = sample_native(B, xflat, zflat)
    e_native = sample_native(E, xflat, zflat)
    f_surface, cell_rc = sample_cell_f(F, xflat, zflat)
    p_surface = sample_p_cell(P, cell_rc)
    arrays = {'x_m': xflat, 'z_m': zflat, 'cell_rc': cell_rc,
              'P_cell_m': p_surface, 'F_triangular_cell_m': f_surface,
              'B_native_m': b_native, 'EV95_native_m': e_native}
    per_state = {}
    for state, height, native in (('B', B, b_native), ('EV95', E, e_native)):
        state_rec = {'objects': {}, 'aggregate_unique_bbox_union': {}, 'steps': list(COARSE_STEPS)}
        coarse_by_step = {}
        for step in COARSE_STEPS:
            if time.perf_counter() - started > TIME_BUDGET_S:
                raise TimeoutError(f'numeric budget exceeded before step {step}')
            coarse = coarse_surface(height, xflat, zflat, step)
            coarse_by_step[step] = coarse
            arrays[f'{state}_coarse_{int(step)}m'] = coarse
            step_rec = {'objects': {}}
            for oid, mask in sample_mask.items():
                step_rec['objects'][oid] = summarize(native, coarse, p_surface, f_surface, mask)
            step_rec['aggregate_unique_bbox_union'] = summarize(native, coarse, p_surface, f_surface,
                np.logical_or.reduce(list(sample_mask.values())))
            state_rec['objects'][str(step)] = step_rec['objects']
            state_rec['aggregate_unique_bbox_union'][str(step)] = step_rec['aggregate_unique_bbox_union']
            ws, peak = memory_bytes(); process_peak = max(process_peak, peak)
            if ws > MEMORY_BUDGET_BYTES or process_peak > MEMORY_BUDGET_BYTES:
                raise MemoryError(f'memory cap exceeded: working_set={ws} peak={process_peak}')
        per_state[state] = state_rec
        del coarse_by_step
    input_end = {name: sha(Path(name)) for name in EXPECTED}
    if input_start != input_end:
        raise ValueError('input readset changed during analysis')
    elapsed = time.perf_counter() - started
    if elapsed > TIME_BUDGET_S:
        raise TimeoutError(f'numeric budget exceeded: {elapsed:.3f}s')
    ws, peak = memory_bytes(); process_peak = max(process_peak, peak)
    if ws > MEMORY_BUDGET_BYTES or process_peak > MEMORY_BUDGET_BYTES:
        raise MemoryError(f'memory cap exceeded at end: working_set={ws} peak={process_peak}')
    np.savez_compressed(OUT / 'samples.npz', **arrays)
    return {
        'schema': 'coarse-terrain-sensitivity.ev95.v1',
        'status': 'OFFLINE_SAMPLED_SENSITIVITY_NOT_ENGINE_LOD_OR_CAUSALITY',
        'source_hashes_start': input_start, 'source_hashes_end': input_end,
        'source_hashes_unchanged': input_start == input_end,
        'coordinate_contract': {'world_x': 'x=6*c', 'world_z': 'z=12282-6*r', 'native_cell_m': 6.0,
            'native_and_resampled_triangles': 'NW-SE diagonal; sample barycentric interpolation on the selected triangle',
            'coarse_lattice_anchor': 'x=0, z=12282; values resampled from the native triangular B/EV95 surface',
            'P': 'one P value per native cell, selected by half-open cell index; never blended between cells',
            'F': 'NW,NE,SW,SE samples interpolated only within that native cell triangle; no across-cell averaging',
            'patch_samples': '1.5m grid at x=0.75+1.5k, z=12282-(0.75+1.5j), avoiding native cell seams'},
        'objects': [{k:v for k,v in o.items() if k != 'bounds'} for o in objs],
        'roi_envelope_bbox_xz_m': list(union), 'patch_grid_shape_zx': [int(len(zs)),int(len(xs))],
        'sample_count_roi_envelope_grid': int(point_count),
        'sample_count_union_of_object_bbox_masks': int(np.count_nonzero(np.logical_or.reduce(list(sample_mask.values())))),
        'object_bbox_sample_counts': {k:int(np.count_nonzero(v)) for k,v in sample_mask.items()},
        'steps_m': list(COARSE_STEPS), 'results': per_state,
        'interpretation_limits': [
            'Per-object masks use the reported local visual bbox transformed by the WRP position. A bbox is not an exact P3D face footprint; samples can include empty portions, and separate object summaries may overlap.',
            'This evaluates sampled height envelopes only. It does not emulate terrain LOD selection, screen-space sampling, Z ordering, material/shader behavior, or runtime water waves.',
            'B and EV95 are separate numerical baselines; no EV73 screenshot or visual symptom is transferred to either.',
            'P and F are sampled fields and not exact runtime water intersections. Positive coarse-minus-F means the sampled coarse terrain is higher than that F surface at that point, not proof that the engine renders it in front.'
        ],
        'validation': {'fixtures': fixtures(), 'elapsed_seconds': float(elapsed),
            'time_budget_seconds': TIME_BUDGET_S, 'memory_working_set_bytes': int(ws),
            'memory_peak_working_set_bytes': int(process_peak), 'memory_budget_bytes': MEMORY_BUDGET_BYTES,
            'numeric_status': 'PASS_WITHIN_BUDGET'},
        'samples_path': str(OUT / 'samples.npz'), 'samples_note': 'Contains coordinates, cell IDs, P/F and native/coarse H samples for B and EV95.'
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report_path = OUT / 'report.json'
    samples_path = OUT / 'samples.npz'
    if report_path.exists() or samples_path.exists():
        raise FileExistsError('refusing to overwrite an earlier coarse-terrain sensitivity run')
    fixture_result = fixtures()
    if not all(fixture_result.values()):
        raise AssertionError(fixture_result)
    report = run()
    report['source_code_path'] = str(Path(__file__).resolve())
    report['source_code_sha256'] = sha(Path(__file__))
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'report': str(report_path),
                      'samples': str(samples_path), 'source_sha256': report['source_code_sha256'],
                      'elapsed_seconds': report['validation']['elapsed_seconds'],
                      'peak_working_set_bytes': report['validation']['memory_peak_working_set_bytes']}, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())