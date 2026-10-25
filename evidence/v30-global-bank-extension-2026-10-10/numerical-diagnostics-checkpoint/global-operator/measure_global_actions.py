"""One-shot, matrix-free action benchmark. Never runs a solver or writes terrain."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time

import numpy as np

HERE = Path(__file__).resolve().parent
PROTO = HERE.parent
INPUT_H = Path(r'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\build-wide-slope\candidate\terrain.npz')
MASKS = PROTO / 'global-sizing-ev95' / 'run-05' / 'masks.npz'
RECEIPT = PROTO / 'global-sizing-ev95' / 'run-05' / 'preflight.json'
OPERATOR = HERE / 'structured_operator.py'
FIXTURE_REPORT = HERE / 'fixture-report.json'
REVIEW = HERE / 'independent-review.json'
RUN_DIR = HERE / 'measurement' / 'run-01'
REPORT = RUN_DIR / 'measurement.json'
MARKER = RUN_DIR / 'bench-invocation.started.json'

PINS = {
    str(INPUT_H): '40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
    str(MASKS): '8f5959308923263538440d29dd93960c5331bc8f13c88b61590380c17d6cdfff',
    str(RECEIPT): 'b6507c73af2181860c13a04ed1814a1a508d0448cd9b63520854aad029ae0f95',
    str(OPERATOR): 'd3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a',
    str(FIXTURE_REPORT): '8b877d0fbce0566b8c6691f75bc7c0b2a0d9c98eeee24deca2bdcd6166833c28',
}
OPERATOR_SHA = PINS[str(OPERATOR)]
FIXTURE_SHA = PINS[str(FIXTURE_REPORT)]
REVIEW_STATUS = 'PASS_STRUCTURED_OPERATOR_INDEPENDENT_REVIEW'
MIN_FREE_BYTES = 6 * 1024**3
NUMERIC_BUDGET_S = 120.0


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
        ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
        ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
        ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
        ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
    ]


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ('cb', ctypes.c_ulong), ('PageFaultCount', ctypes.c_ulong),
        ('PeakWorkingSetSize', ctypes.c_size_t), ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t), ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t), ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t), ('PeakPagefileUsage', ctypes.c_size_t),
        ('PrivateUsage', ctypes.c_size_t),
    ]


ctypes.windll.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
ctypes.windll.kernel32.GetCurrentProcess.argtypes = []
ctypes.windll.kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MEMORYSTATUSEX)]
ctypes.windll.kernel32.GlobalMemoryStatusEx.restype = ctypes.c_int
ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), ctypes.c_ulong
]
ctypes.windll.psapi.GetProcessMemoryInfo.restype = ctypes.c_int


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_pinned_sources(pins):
    """Rehash every frozen source artifact before any implementation import."""
    observed={}
    for raw_path,expected in pins.items():
        path=Path(raw_path).resolve()
        data=path.read_bytes()
        actual=sha256_bytes(data)
        if actual!=str(expected).lower():
            raise RuntimeError(f'frozen source pin mismatch: {path}')
        observed[str(path)]=actual
    return observed


def load_verified_operator(operator_path: Path, expected_sha: str):
    """Execute exactly the bytes whose digest was checked, avoiding import TOCTOU."""
    path=operator_path.resolve()
    data=path.read_bytes()
    actual=sha256_bytes(data)
    if actual!=expected_sha.lower():
        raise RuntimeError('operator source changed before verified load')
    module_name='ev95_verified_structured_operator'
    spec=importlib.util.spec_from_loader(module_name,loader=None,origin=str(path))
    if spec is None:
        raise ImportError('cannot construct verified operator module spec')
    module=importlib.util.module_from_spec(spec)
    module.__file__=str(path)
    exec(compile(data,str(path),'exec'),module.__dict__)
    if not callable(getattr(module,'build_operators',None)):
        raise RuntimeError('verified operator module has no build_operators API')
    return module.build_operators,actual


def memory_status():
    s = MEMORYSTATUSEX()
    s.dwLength = ctypes.sizeof(s)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s)):
        raise OSError('GlobalMemoryStatusEx failed')
    return {'total_physical_bytes': int(s.ullTotalPhys), 'available_physical_bytes': int(s.ullAvailPhys)}


def process_peak_working_set():
    c = PROCESS_MEMORY_COUNTERS_EX()
    c.cb = ctypes.sizeof(c)
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(c), c.cb):
        raise OSError('GetProcessMemoryInfo failed')
    return int(c.PeakWorkingSetSize)


class ResourceWatchdog:
    """Samples free RAM and deadline; abort is observed only at safe call boundaries."""
    def __init__(self, started, interval_s=.25):
        self.started=float(started)
        self.interval=float(interval_s)
        self.stop_event=threading.Event()
        self.failure_event=threading.Event()
        self.failure=None
        self.samples=[]
        self.thread=threading.Thread(target=self._sample_loop,name='matrix-free-resource-watchdog',daemon=True)

    def _latch(self, why):
        if not self.failure_event.is_set():
            self.failure=why
            self.failure_event.set()

    def _sample_loop(self):
        while not self.stop_event.wait(self.interval):
            try:
                available=memory_status()['available_physical_bytes']
                elapsed=time.perf_counter()-self.started
                self.samples.append({'elapsed_seconds':elapsed,'available_physical_bytes':available})
                if available<MIN_FREE_BYTES:
                    self._latch('available physical memory fell below 6 GiB')
                if elapsed>NUMERIC_BUDGET_S:
                    self._latch('120-second total measurement budget exceeded')
            except Exception as exc:
                self._latch(f'memory monitor failed: {type(exc).__name__}: {exc}')

    def start(self):
        self.thread.start()
        return self

    def check_boundary(self, label):
        if self.failure_event.is_set():
            raise RuntimeError(f'{label}: {self.failure}')
        elapsed=time.perf_counter()-self.started
        if elapsed>NUMERIC_BUDGET_S:
            self._latch('120-second total measurement budget exceeded')
            raise TimeoutError(f'{label}: numeric budget exceeded at return boundary')

    def close(self):
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join(timeout=2.0)
        return {'sample_interval_seconds':self.interval,'sample_count':len(self.samples),
                'minimum_available_physical_bytes':min((s['available_physical_bytes'] for s in self.samples),default=None),
                'failure':self.failure,'samples':self.samples}


def deterministic_vector(n: int, tag: int) -> np.ndarray:
    if int(n) < 0:
        raise ValueError('negative vector length')
    v = np.arange(int(n), dtype=np.float64)
    np.remainder(v, 4093.0, out=v)
    np.add(v, float(tag * 137), out=v)
    np.remainder(v, 4093.0, out=v)
    np.subtract(v, 2046.0, out=v)
    np.multiply(v, 1.0/2046.0, out=v)
    return v


def vector_digest_and_norm(v: np.ndarray):
    if v.dtype != np.float64 or v.ndim != 1 or not v.flags.c_contiguous or not np.isfinite(v).all():
        raise ValueError('benchmark vectors/results must be finite contiguous float64 vectors')
    digest = hashlib.sha256(memoryview(v).cast('B')).hexdigest()
    norm = float(np.linalg.norm(v))
    if not np.isfinite(norm):
        raise ValueError('non-finite norm')
    return digest, norm


def persistent_array_estimate_bytes(shape, variables, a_rows, c_rows, g_rows):
    h, w = map(int, shape)
    n = int(variables)
    stencil_anchors = int(a_rows) - n
    # Arrays actually retained by MatrixFreeOperators (float64/int32 layout).
    parts = {
        'base_float64': 8*h*w,
        'variable_index_grid_int32': 4*h*w,
        'variables_rc_int32': 8*n,
        'A_anchor_rc_int32': 8*stencil_anchors,
        'rhs_a_float64': 8*a_rows,
        'C_centers_witnesses_int32': 8*c_rows,
        'd_c_float64': 8*c_rows,
        'k_g_float64': 8*g_rows,
        'three_diagonals_float64': 24*n,
    }
    return parts, int(sum(parts.values()))


def exact_structural_nnz(op):
    idx = op.index_grid
    counts = {'A': op.n}
    for rc, kind in ((op.xx_rc,'xx'),(op.zz_rc,'zz'),(op.xz_rc,'xz')):
        r,c=rc[:,0],rc[:,1]
        if kind=='xx': taps=((r,c),(r,c+1),(r,c+2))
        elif kind=='zz': taps=((r,c),(r+1,c),(r+2,c))
        else: taps=((r,c),(r,c+2),(r+2,c),(r+2,c+2))
        counts['A'] += sum(int(np.count_nonzero(idx[rr,cc]>=0)) for rr,cc in taps)
    flat=idx.ravel()
    counts['C']=int(np.count_nonzero(flat[op.d8_centers]>=0)+np.count_nonzero(flat[op.d8_witnesses]>=0))
    h,w=op.base.shape
    if h<2 or w<2:
        counts['G']=0
    else:
        # Each component row has two endpoint entries; count only variable endpoints.
        # G endpoint pairs in CP row order: (NW,NE), (NE,SE), (SW,SE), (NW,SW).
        counts['G']=sum(int(np.count_nonzero(idx[rr,cc]>=0)) for rr,cc in (
            (slice(0,h-1),slice(0,w-1)), (slice(0,h-1),slice(1,w)),
            (slice(0,h-1),slice(1,w)), (slice(1,h),slice(1,w)),
            (slice(1,h),slice(0,w-1)), (slice(1,h),slice(1,w)),
            (slice(0,h-1),slice(0,w-1)), (slice(1,h),slice(0,w-1))))
    return counts


def review_gate(review_path: Path, expected_sha: str, readset_start=None):
    if not review_path.is_file():
        raise RuntimeError(f'independent review missing: {review_path}')
    review_bytes=review_path.read_bytes()
    actual_sha=sha256_bytes(review_bytes)
    if actual_sha != expected_sha.lower():
        raise RuntimeError('independent review hash does not match supplied pin')
    data=json.loads(review_bytes.decode('utf-8-sig'))
    if data.get('status') != REVIEW_STATUS:
        raise RuntimeError('independent review status is not the required PASS')
    if data.get('operator_sha256') != OPERATOR_SHA or data.get('fixture_report_sha256') != FIXTURE_SHA:
        raise RuntimeError('independent review does not bind this operator and fixture report')
    driver_sha=sha256_file(Path(__file__).resolve())
    if data.get('measurement_driver_sha256') != driver_sha:
        raise RuntimeError('independent review does not bind this measurement driver')
    if readset_start is not None:
        review_key=str(review_path.resolve())
        if readset_start.get(review_key)!=actual_sha:
            raise RuntimeError('independent review SHA differs from initial read-set')
        for raw_path,expected in PINS.items():
            key=str(Path(raw_path).resolve())
            if readset_start.get(key)!=expected.lower():
                raise RuntimeError(f'initial read-set does not contain the frozen pin: {key}')
        driver_key=str(Path(__file__).resolve())
        if readset_start.get(driver_key)!=driver_sha:
            raise RuntimeError('measurement driver SHA differs from initial read-set')
    return data, actual_sha


def require_free_reserve(extra_bytes: int, phase: str):
    available=memory_status()['available_physical_bytes']
    if available-int(extra_bytes)<MIN_FREE_BYTES:
        raise MemoryError(f'{phase}: projected free memory would fall below the 6 GiB reserve')
    return available


def readset(paths):
    return {str(Path(p).resolve()):sha256_file(Path(p)) for p in paths}


def validate_inputs(h_path, masks_path, receipt_path, h_sha, masks_sha, receipt_sha, start_readset):
    required={str(p.resolve()):sha for p,sha in ((h_path,h_sha),(masks_path,masks_sha),(receipt_path,receipt_sha))}
    if any(start_readset.get(path)!=sha for path,sha in required.items()):
        raise RuntimeError('input file hash does not match frozen benchmark pin')
    receipt=json.loads(receipt_path.read_text(encoding='utf-8-sig'))
    if receipt.get('status')!='READ_ONLY_RESOURCE_PREFLIGHT_COMPLETE':
        raise RuntimeError('resource receipt status mismatch')
    if receipt['identity']['EV95_sha256'] != h_sha:
        raise RuntimeError('resource receipt does not identify EV95 height archive')
    if receipt['masks_artifact']['sha256'] != masks_sha or Path(receipt['masks_artifact']['path']).resolve()!=masks_path.resolve():
        raise RuntimeError('resource receipt does not identify the masks input')
    return receipt


def write_json_atomic(path: Path, data):
    tmp=path.with_name(path.name+'.tmp')
    if tmp.exists():
        raise FileExistsError(tmp)
    tmp.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    os.replace(tmp,path)


def run_benchmark(review_path: Path, review_sha: str):
    source_paths=[Path(p) for p in PINS]+[review_path,Path(__file__).resolve()]
    source_readset_start=readset(source_paths)
    pinned_start=verify_pinned_sources(PINS)
    if any(source_readset_start.get(path)!=sha for path,sha in pinned_start.items()):
        raise RuntimeError('frozen source bytes drifted during initial identity check')
    review, review_hash=review_gate(review_path,review_sha,source_readset_start)
    if source_readset_start.get(str(review_path.resolve()))!=review_hash:
        raise RuntimeError('review file drifted between gate and initial read-set')
    build_operators,loaded_operator_sha=load_verified_operator(OPERATOR,OPERATOR_SHA)
    if loaded_operator_sha!=pinned_start[str(OPERATOR.resolve())]:
        raise RuntimeError('loaded operator bytes differ from initial pinned bytes')
    if RUN_DIR.exists() or MARKER.exists() or REPORT.exists():
        raise FileExistsError(f'one-shot output already exists: {RUN_DIR}')
    RUN_DIR.mkdir(parents=True,exist_ok=False)
    marker={'schema':'ev95.matrix-free-actions-bench.v1','state':'STARTED','operator_sha256':OPERATOR_SHA,
            'fixture_report_sha256':FIXTURE_SHA,'review_path':str(review_path.resolve()),'review_sha256':review_hash,
            'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'solve_executed':False,'terrain_written':False}
    with MARKER.open('x',encoding='utf-8') as f:
        f.write(json.dumps(marker,indent=2,allow_nan=False)+'\n')

    started=time.perf_counter()
    watcher=None
    status='ERROR'
    report={'schema':'ev95.matrix-free-actions-bench.v1','status':status,'solve_executed':False,'terrain_written':False,
            'input_paths':{'heights':str(INPUT_H),'masks':str(MASKS),'resource_receipt':str(RECEIPT)},
            'review':{'path':str(review_path.resolve()),'sha256':review_hash,'status':review.get('status')},
            'operator_sha256':OPERATOR_SHA,'fixture_report_sha256':FIXTURE_SHA,'action_counts':{},'actions':{}}
    try:
        report['source_readset_start']=source_readset_start
        report['pinned_source_readset_start']=pinned_start
        input_ids={'H':PINS[str(INPUT_H)],'masks':PINS[str(MASKS)],'receipt':PINS[str(RECEIPT)]}
        receipt=validate_inputs(INPUT_H,MASKS,RECEIPT,input_ids['H'],input_ids['masks'],input_ids['receipt'],report['source_readset_start'])
        counts=receipt['operator_counts']['EV95_delta_variable']
        shape=[2048,2048]
        per_array,persistent=persistent_array_estimate_bytes(shape,counts['variables'],counts['A']['rows'],counts['C']['rows'],counts['G']['rows'])
        max_output=8*max(counts['A']['rows'],counts['C']['rows'],counts['G']['rows'])
        scratch_reserve=512*1024**2
        estimate=int(persistent+scratch_reserve+2*max_output+8*counts['variables']+8*np.prod(shape))
        mem_before=memory_status()
        report['resource_gate']={'available_before_bytes':mem_before['available_physical_bytes'],'required_free_reserve_bytes':MIN_FREE_BYTES,
                                 'persistent_arrays_estimate_bytes':persistent,'persistent_array_bytes':per_array,
                                 'largest_operator_output_bytes':max_output,'scratch_reserve_bytes':scratch_reserve,
                                 'estimated_peak_increment_bytes':estimate,'available_after_estimate_bytes':mem_before['available_physical_bytes']-estimate,
                                 'gate_pass':bool(mem_before['available_physical_bytes']-estimate>=MIN_FREE_BYTES)}
        if not report['resource_gate']['gate_pass']:
            status='ABORT_MEMORY_GUARD'
            raise RuntimeError('insufficient free memory for conservative estimated peak while retaining 6 GiB')
        watcher=ResourceWatchdog(started).start()

        # The timer covers input materialization, operator construction, and all six actions.
        with np.load(INPUT_H,allow_pickle=False) as z:
            h32=z['heights']
        if h32.shape!=tuple(shape) or h32.dtype!=np.float32 or not np.isfinite(h32).all():
            raise ValueError('EV95 heights must be finite float32 (2048,2048)')
        H=np.asarray(h32,dtype=np.float64)
        if not np.array_equal(H,np.asarray(h32,dtype=np.float64)):
            raise AssertionError('EV95 height conversion changed source values')
        del h32
        with np.load(MASKS,allow_pickle=False) as z:
            mask=z['ev95_variable']
        if mask.shape!=tuple(shape) or mask.dtype!=np.uint8 or np.any((mask!=0)&(mask!=1)):
            raise ValueError('ev95_variable mask shape/dtype/value mismatch')
        n=int(np.count_nonzero(mask))
        if n!=counts['variables']:
            raise ValueError('EV95 variable mask count does not match receipt')
        mask_controls={}
        with np.load(MASKS,allow_pickle=False) as z:
            expected_controls={
                'eligible_before_guards':int(receipt['domain']['EV87_eligible_before_global_guards']),
                'ev95_delta_fixed_variable':int(receipt['domain']['EV95_delta_fixed_sensitivity_after_guards']),
                'retained_499_halo2':int(receipt['identity']['retained_halo2_vertices']),
            }
            eligible=z['eligible_before_guards']
            fixed_sensitivity=z['ev95_delta_fixed_variable']
            for key,a in (('eligible_before_guards',eligible),('ev95_delta_fixed_variable',fixed_sensitivity)):
                if a.shape!=tuple(shape) or a.dtype!=np.uint8 or np.any((a!=0)&(a!=1)):
                    raise RuntimeError(f'{key} mask shape/dtype/value mismatch')
            if int(np.count_nonzero(eligible))!=expected_controls['eligible_before_guards']:
                raise RuntimeError('eligible-before-guards count differs from receipt')
            if int(np.count_nonzero(fixed_sensitivity))!=expected_controls['ev95_delta_fixed_variable']:
                raise RuntimeError('fixed-delta sensitivity mask count differs from receipt')
            retained=z['retained_499_halo2']
            if retained.shape!=tuple(shape) or retained.dtype!=np.uint8 or np.any((retained!=0)&(retained!=1)):
                raise RuntimeError('retained halo mask shape/dtype/value mismatch')
            if int(np.count_nonzero(retained))!=expected_controls['retained_499_halo2']:
                raise RuntimeError('retained 499-window halo count differs from receipt')
            if np.any((retained!=0)&(mask!=0)):
                raise RuntimeError('EV95 variable mask overlaps the 499 retained-window halo')
            # Every named guard must remain fixed in this measurement scenario.
            for key in ('p9_unknown_nodes','water_bbox_nodes','civil_nodes','water_shore_partial_nodes'):
                g=z[key]
                if g.shape!=tuple(shape) or g.dtype!=np.uint8 or np.any((g!=0)&(g!=1)):
                    raise RuntimeError(f'{key} mask shape/dtype/value mismatch')
                overlap=int(np.count_nonzero((g!=0)&(mask!=0)))
                if overlap:
                    raise RuntimeError(f'EV95 variable mask overlaps fixed guard {key}: {overlap}')
                mask_controls[key]={'count':int(np.count_nonzero(g)),'variable_overlap':overlap}
            focus=tuple(map(int,receipt['identity']['focus_rc']))
            if tuple(shape)==(2048,2048) and mask[focus[0],focus[1]]!=0:
                raise RuntimeError('explicit focus is unexpectedly variable')
            reason=z['reason_bits']
            if int(reason[focus[0],focus[1]]) & 512 == 0:
                raise RuntimeError('explicit focus reason bit is missing from fixed-mask receipt')
            mask_controls.update({'focus_rc':list(focus),'focus_variable':False,
                                  'focus_reason_bit_512':True,'retained_halo_count':int(np.count_nonzero(retained)),
                                  'eligible_before_guards_count':expected_controls['eligible_before_guards'],
                                  'fixed_delta_sensitivity_count':expected_controls['ev95_delta_fixed_variable']})
        r,c=np.nonzero(mask)
        variables=np.column_stack((r,c)).astype(np.int32,copy=False)
        del r,c,mask
        operator=build_operators(H,variables)
        del H,variables
        watcher.check_boundary('operator construction')
        if [operator.n_a,operator.n_c,operator.n_g,operator.n] != [counts['A']['rows'],counts['C']['rows'],counts['G']['rows'],counts['variables']]:
            raise RuntimeError('matrix-free row or variable count differs from receipt')
        nnz=exact_structural_nnz(operator)
        if nnz!={k:int(counts[k]['nnz']) for k in ('A','C','G')}:
            raise RuntimeError(f'matrix-free structural nnz mismatch: {nnz}')
        report['operator_counts']={'variables':operator.n,'A':{'rows':operator.n_a,'nnz':nnz['A']},
                                   'C':{'rows':operator.n_c,'nnz':nnz['C']},'G':{'rows':operator.n_g,'nnz':nnz['G']},
                                   'fixed_vertices':int(np.prod(shape))-operator.n}
        report['mask_control_checks']=mask_controls
        x=deterministic_vector(operator.n,tag=1)
        xsha,xnorm=vector_digest_and_norm(x)
        report['probe_x']={'length':len(x),'sha256':xsha,'norm':xnorm,
                           'definition':'float64: ((arange(n) mod 4093 + 137) mod 4093 - 2046)/2046'}
        actions={'A':(operator.matvec_a,operator.rmatvec_a,operator.n_a,11),
                 'C':(operator.matvec_c,operator.rmatvec_c,operator.n_c,23),
                 'G':(operator.matvec_g,operator.rmatvec_g,operator.n_g,37)}
        for name,(mv,rmv,m,tag) in actions.items():
            watcher.check_boundary(f'{name} action start')
            if time.perf_counter()-started>NUMERIC_BUDGET_S:
                status='ABORT_TIME_BUDGET';raise TimeoutError('120-second total benchmark budget exceeded')
            grid_bytes=8*int(np.prod(shape))
            n_bytes=8*operator.n
            y_bytes=8*m
            out_bytes=8*m
            require_free_reserve(y_bytes+out_bytes+grid_bytes+n_bytes+512*1024**2,f'{name} matvec allocation')
            y=deterministic_vector(m,tag)
            ysha,ynorm=vector_digest_and_norm(y)
            t0=time.perf_counter();out=mv(x);mv_s=time.perf_counter()-t0
            report['action_counts'][name]={'matvec':1,'rmatvec':0}
            out_sha,out_norm=vector_digest_and_norm(out)
            lhs=float(np.dot(out,y));del out
            peak_after_mv=process_peak_working_set()
            free_after_mv=memory_status()['available_physical_bytes']
            if free_after_mv<MIN_FREE_BYTES:
                status='ABORT_MEMORY_RESERVE';raise MemoryError(f'{name} matvec left less than 6 GiB free')
            watcher.check_boundary(f'{name} matvec return')
            require_free_reserve(y_bytes+grid_bytes+n_bytes+128*1024**2,f'{name} rmatvec allocation')
            t0=time.perf_counter();adj=rmv(y);rmv_s=time.perf_counter()-t0
            report['action_counts'][name]={'matvec':1,'rmatvec':1}
            adj_sha,adj_norm=vector_digest_and_norm(adj)
            rhs=float(np.dot(x,adj));del adj
            peak_after_rmv=process_peak_working_set()
            free_after_rmv=memory_status()['available_physical_bytes']
            watcher.check_boundary(f'{name} rmatvec return')
            abs_err=abs(lhs-rhs);rel_err=abs_err/max(1.0,abs(lhs),abs(rhs))
            result={'rows':m,'input_y_sha256':ysha,'input_y_norm':ynorm,'matvec_count':1,'rmatvec_count':1,
                    'matvec_seconds':mv_s,'matvec_output_sha256':out_sha,'matvec_output_norm':out_norm,
                    'rmatvec_seconds':rmv_s,'rmatvec_output_sha256':adj_sha,'rmatvec_output_norm':adj_norm,
                    'dot_matvec_y':lhs,'dot_x_rmatvec':rhs,'adjoint_abs_error':abs_err,'adjoint_relative_error':rel_err,
                    'peak_working_set_after_matvec_bytes':peak_after_mv,'peak_working_set_after_rmatvec_bytes':peak_after_rmv,
                    'available_physical_after_matvec_bytes':free_after_mv,'available_physical_after_rmatvec_bytes':free_after_rmv,
                    'y_definition':f'float64: ((arange(m) mod 4093 + {tag*137}) mod 4093 - 2046)/2046'}
            if rel_err>1e-10:
                status='FAIL_ADJOINT_IDENTITY';raise ArithmeticError(f'{name} global adjoint identity failed: {rel_err}')
            report['actions'][name]=result
            del y
            if free_after_rmv<MIN_FREE_BYTES:
                status='ABORT_MEMORY_RESERVE';raise MemoryError(f'{name} rmatvec left less than 6 GiB free')
            if time.perf_counter()-started>NUMERIC_BUDGET_S:
                status='ABORT_TIME_BUDGET';raise TimeoutError('120-second total benchmark budget exceeded')
        status='PASS_GLOBAL_MATRIX_FREE_ACTION_MEASUREMENT'
    except Exception as exc:
        report['error']={'type':type(exc).__name__,'message':str(exc)}
        if isinstance(exc,TimeoutError): status='ABORT_TIME_BUDGET'
        elif isinstance(exc,MemoryError): status='ABORT_MEMORY_GUARD'
        elif watcher is not None and watcher.failure is not None:
            status='ABORT_RESOURCE_WATCHDOG'
        elif status=='ERROR': status='ERROR'
    finally:
        if watcher is not None:
            report['resource_watchdog']=watcher.close()
        report['status']=status
        report['elapsed_total_seconds']=time.perf_counter()-started
        report['numeric_budget_seconds']=NUMERIC_BUDGET_S
        try:
            report['source_readset_end']=readset(source_paths)
            report['source_readset_stable']=report.get('source_readset_start')==report['source_readset_end']
            if not report['source_readset_stable'] and report['status']=='PASS_GLOBAL_MATRIX_FREE_ACTION_MEASUREMENT':
                report['status']='FAIL_SOURCE_DRIFT'
        except Exception as exc:
            report['source_readset_end_error']=f'{type(exc).__name__}: {exc}'
            if report['status']=='PASS_GLOBAL_MATRIX_FREE_ACTION_MEASUREMENT': report['status']='FAIL_SOURCE_REHASH'
        try:
            report['process_peak_working_set_bytes']=process_peak_working_set()
        except Exception as exc:
            report['process_peak_working_set_error']=f'{type(exc).__name__}: {exc}'
            if report['status']=='PASS_GLOBAL_MATRIX_FREE_ACTION_MEASUREMENT':
                report['status']='ERROR_PEAK_MEMORY_READ'
        report['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        write_json_atomic(REPORT,report)
        marker['state']='FINISHED'
        marker['finished_utc']=report['finished_utc']
        marker['report_sha256']=sha256_file(REPORT)
        write_json_atomic(MARKER,marker)
    return report


def self_test():
    v=deterministic_vector(17,3)
    sha,norm=vector_digest_and_norm(v)
    assert len(sha)==64 and np.isfinite(norm) and np.array_equal(v,deterministic_vector(17,3))
    try: vector_digest_and_norm(np.array([np.nan],dtype=np.float64))
    except ValueError: pass
    else: raise AssertionError('non-finite probe accepted')
    parts,total=persistent_array_estimate_bytes((11,132),100,300,400,500)
    assert total==sum(parts.values()) and total>0
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        operator_pin=root/'operator.py'; operator_pin.write_bytes(b'value=1\n')
        fixture_pin=root/'fixture.json'; fixture_pin.write_bytes(b'{"fixture":1}\n')
        expected_operator=sha256_file(operator_pin);expected_fixture=sha256_file(fixture_pin)
        pins_fixture={str(operator_pin):expected_operator,str(fixture_pin):expected_fixture}
        assert len(verify_pinned_sources(pins_fixture))==2
        operator_pin.write_bytes(b'value=2\n')
        try: verify_pinned_sources(pins_fixture)
        except RuntimeError: pass
        else: raise AssertionError('altered operator source accepted before start')
        operator_pin.write_bytes(b'value=1\n')
        fixture_pin.write_bytes(b'{"fixture":2}\n')
        try: verify_pinned_sources(pins_fixture)
        except RuntimeError: pass
        else: raise AssertionError('altered fixture report accepted before start')
        op=root/'operator.py'; op.write_bytes(b'def build_operators(): return 17\n')
        fn,loaded=load_verified_operator(op,sha256_file(op))
        assert fn()==17 and loaded==sha256_file(op)
        op.write_bytes(b'def build_operators(): return 18\n')
        try: load_verified_operator(op,loaded)
        except RuntimeError: pass
        else: raise AssertionError('altered operator bytes loaded')
        drv=Path(__file__).resolve()
        p=root/'review.json'
        review_data={'status':REVIEW_STATUS,'operator_sha256':OPERATOR_SHA,
                     'fixture_report_sha256':FIXTURE_SHA,
                     'measurement_driver_sha256':sha256_file(drv)}
        p.write_text(json.dumps(review_data),encoding='utf-8')
        review_sha=sha256_file(p)
        pins={str(root/'operator.pin'):OPERATOR_SHA,str(root/'fixture.pin'):FIXTURE_SHA}
        fake_start={str(p.resolve()):review_sha,str(drv):review_data['measurement_driver_sha256'],
                    **{str(Path(k).resolve()):v for k,v in pins.items()}}
        old_pins=PINS.copy()
        try:
            PINS.clear();PINS.update(pins)
            review_gate(p,review_sha,fake_start)
            mutated=dict(fake_start);mutated[str(p.resolve())]='0'*64
            try: review_gate(p,review_sha,mutated)
            except RuntimeError: pass
            else: raise AssertionError('review/read-set SHA mismatch accepted')
            p.write_text(json.dumps({**review_data,'changed':True}),encoding='utf-8')
            try: review_gate(p,review_sha,fake_start)
            except RuntimeError: pass
            else: raise AssertionError('review modified after read-set accepted')
        finally:
            PINS.clear();PINS.update(old_pins)
    mem=memory_status();peak=process_peak_working_set()
    assert mem['available_physical_bytes']>0 and peak>0
    print(json.dumps({'status':'PASS_BENCH_HELPER_FIXTURES','probe_sha256':sha,'probe_norm':norm,
                      'estimate_fixture_bytes':total,'memory_api':'GlobalMemoryStatusEx/GetProcessMemoryInfo PASS',
                      'current_process_peak_working_set_bytes':peak,'exclusive_run_dir':str(RUN_DIR)},indent=2))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--review-sha256')
    ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args()
    if args.self_test:
        self_test();return
    if not args.review_sha256:
        raise SystemExit('benchmark refused: pass the independent review report SHA256')
    report=run_benchmark(REVIEW,args.review_sha256)
    print(json.dumps({'status':report['status'],'report':str(REPORT),'elapsed_total_seconds':report.get('elapsed_total_seconds')},indent=2))
    if report['status']!='PASS_GLOBAL_MATRIX_FREE_ACTION_MEASUREMENT':
        raise SystemExit(1)


if __name__=='__main__':
    main()
