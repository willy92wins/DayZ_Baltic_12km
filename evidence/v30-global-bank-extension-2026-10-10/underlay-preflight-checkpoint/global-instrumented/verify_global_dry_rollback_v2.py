"""Independent post-solve verifier for the frozen EV95 global dry rollback.

This module never imports the rollback author/core and never writes terrain.
It writes only a JSON acceptance report. Any unprovable required contract is
reported FAIL or INCONCLUSIVE; no author receipt field is treated as a gate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(r"E:/DayZ-Baltic-Build")
G = ROOT / "v30-global-bank-extension-20261010"
PROTO = G / "global-operator-prototype"
HERE = PROTO / "global-dry-rollback/postsolve-consumer/instrumented-v2"
SELF = HERE / "verify_global_dry_rollback_v2.py"
PLAN_PATH = HERE / "PLAN.md"
TEST_PATH = HERE / "test_verify_global_dry_rollback_v2.py"
RECOVERY = PROTO / "global-dry-rollback-frozen-recovery/run-01"
BASE = G / "build-wide-slope/candidate/terrain.npz"
BOUNDS = PROTO / "global-dry-solve/prepared-01/bounds.npz"
BOUNDS_RECEIPT = PROTO / "global-dry-solve/prepared-01/receipt.json"
BOUNDS_REVIEW = PROTO / "global-dry-solve/prepared-01/independent-review.json"
BOUNDS_PLAN = PROTO / "GLOBAL_DRY_SOLVE_PLAN.md"
BOUNDS_PREPARER = PROTO / "prepare_global_dry_bounds.py"
ROUNDING = PROTO / "global-sizing-ev95/audit_rounding_direction.py"
MASKS = PROTO / "global-sizing-ev95/run-05/masks.npz"
PREFLIGHT = PROTO / "global-sizing-ev95/run-05/preflight.json"
WATER_GUARD = PROTO / "global-water-guard-ev95/run-01/water-guard.npz"
WATER_GUARD_RECEIPT = PROTO / "global-water-guard-ev95/run-01/inventory.json"
CIVIL_MASK = PROTO / "global-civil-ev95/run-01/civil-mask.npz"
CIVIL_RECEIPT = PROTO / "global-civil-ev95/run-01/inventory.json"
WATER_GUARD_PREPARE = PROTO / "global-water-guard-ev95/prepare.py"
CIVIL_PREPARE = PROTO / "global-civil-ev95/prepare.py"
CIVIL_SOURCE = PROTO / "real-sector-preflight/civil_inventory.py"
DEPLOY = G / "build-wide-slope/deploy.json"
STAGE = G / "build-wide-slope/stage.json"
EV79_DIR = ROOT / "v30-narva-dry-bank-relief-20261010/candidate"
EV79 = EV79_DIR / "terrain.npz"
P_PATH = EV79_DIR / "plane.npy"
F_PATH = EV79_DIR / "visible-field.npy"
EV87 = ROOT / "v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py"
EV88 = ROOT / "v30-wide-bank-fairing-pilot-20261010/review-independent/verify_ev88q.py"
CV = ROOT / "v30-global-strict-bank-relief-20261010/review-independent/verify_coverage_contract.py"
LAYER = G / "consumer-global/verify_layer.py"
FACE_BUILDER = G / "ev93-face-index/build_face_index.py"
FACE_RUN = G / "ev93-face-index/runs/20261010T092417Z-63d4cec3"
FACE_MANIFEST = FACE_RUN / "manifest.json"
FACE_VERIFICATION = G / "review-independent/runs/attempt-01/verification.json"
AO = PROTO / "global-dry-unconstrained-screen/a-only/a_only_operator.py"
SCREEN = PROTO / "global-dry-unconstrained-screen/run-01/receipt.json"
B_WRP = ROOT / "v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp"
WORKTREE = Path(r"C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290")
WRP_READER = WORKTREE / "tools/terrain/wrp0wzd.py"
MEMORY = PROTO / "global-structured-operator/measure_global_actions.py"
MODEL_DIR = ROOT / "v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30"

PINNED = {
    str(BASE): "40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a",
    str(BOUNDS): "b0c4499776148b080049a528807e31a62d5fd11ba90fcaae5a7881124cde81fb",
    str(BOUNDS_RECEIPT): "9e55afb4b736a3b558d3e631c62fa94c98a0ae2bb7da4e5513850375758869f3",
    str(BOUNDS_REVIEW): "d454b78bf8721a9f6477001bb1e5ba77ed4716fc1fdd03232a6084cc6612bf85",
    str(BOUNDS_PLAN): "a3ab6e74ca13f723989c1e55b3c474df01274f616acab471089fd5e636cafe8e",
    str(BOUNDS_PREPARER): "5052a025a853f42d6dde7fb799ffd3776b3b925d7f23de10cf86d2fb48b987bb",
    str(ROUNDING): "4878c338027e6febd9c2f813dc99c5d009d369bc898c370c7153f74635dd7784",
    str(MASKS): "8f5959308923263538440d29dd93960c5331bc8f13c88b61590380c17d6cdfff",
    str(EV79): "dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c",
    str(P_PATH): "768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0",
    str(F_PATH): "f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c",
    str(EV87): "964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27",
    str(EV88): "82a988790e6bdfc0289bcb7c32cb0afd1210e07b264d92731aba266bc5980f78",
    str(CV): "214f0eddda08d84ce18c921fcdbe01298f608c9a5c19b7e5246bb9e71df5dc2b",
    str(LAYER): "33050881caaf5e75f288d4122222c15eb326bf146c28a4c723760564457b3dc2",
    str(FACE_BUILDER): "d1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e",
    str(FACE_MANIFEST): "c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c",
    str(FACE_VERIFICATION): "b498e7d68835b199399655451e5e01ac81acb3149dbb9bf882b94858141521d4",
    str(AO): "f1e8ddd9258f72004ecf34da1284ec0b0c295cb77e5b963ecaf24cf82ff9401f",
    str(SCREEN): "f66d7d49cfee0d6bb0844210177e5be7810e1d07970d4a404ecbe9f4c257828d",
    str(PREFLIGHT): "b6507c73af2181860c13a04ed1814a1a508d0448cd9b63520854aad029ae0f95",
    str(WATER_GUARD): "997a1510ffd7194cf7f25fc9a26a1fed9c580586d63952f0dfd70fce565c1926",
    str(WATER_GUARD_RECEIPT): "39e26373fee324e8b0e7334dd8333d3fb7373b9cc55c226350e2c607b592ce82",
    str(CIVIL_MASK): "46faaf22e2cfefc8137e2b555227a985cfe212265694f1bce106281937c9ffe3",
    str(CIVIL_RECEIPT): "cdebbbce50644407642e791388e44c40b15499041844607650b885d1bc618856",
    str(WATER_GUARD_PREPARE): "815b631f9fe25b85ceebd68a609647a782f4e6a1b996f777c49fd5304cc05e9a",
    str(CIVIL_PREPARE): "23be055e1a18b981b812d80c445e7c56a4a4d07eb1f0e59e56c60eac155bb038",
    str(CIVIL_SOURCE): "60d1beb2a36739a98fc70dc5a3b29033286e14abbc87461247bc87dd6f48c0c3",
    str(DEPLOY): "f5a9c8185812e0b77a804ef9811e0405b5a7969f8ccfc19b85cc29d23cac03ca",
    str(STAGE): "b04b066d99f9c22a4fffd77c66762d3e9e744dfa2bbf20d8508f076845571dda",
    str(B_WRP): "3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6",
    str(WRP_READER): "8b85cec46ba72851a4ec829c5b0adcc88727ee852c3f699ab7a15e31b50fee2a",
    str(MEMORY): "a05a5f47b775567105c3e588e7106b4b365b58d259f018dca4f243f57d2da37b",
}
EXPECTED_CANDIDATE = "1bd6b67dc7cfa340c762f878776de157c74c368a7a836484c8f7271c276d1795"
EXPECTED_RECEIPT = "1b06ba46cfc1a8539cc21ccd8fb1b43c0cb1ed3fbd85cd18dcb9233c376cd866"
EXPECTED_ROLLBACK_SOURCE = "434cb69fb8940816812d870d57e1cb7bb13f7530958b3d676bdc3ba911e9cd12"
EXPECTED_ROLLBACK_CORE = "de195463fc937986c02a7b1ca3b0b67714760d818e21561093dc90c53c029ec4"
EXPECTED_ROLLBACK_PLAN = "b50f2f3be3ff08de8df1f838391568436c77c9606009792df966a12ec4effe55"
EXPECTED_ROLLBACK_REVIEW = "20b9b31a09333d63caa86cf1207beb7bc6a23dd1872364c98ee134da0a90eb4f"
EXPECTED_B = "40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a"
EXPECTED_FACE_IDS = "90a3a43d0b70ea85847a781c8a2023170e5b1d5c19215d0e10893ac2a714becc"
EXPECTED_BASE_TERRAIN = "f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0"
EXPECTED_WORLD_PBO = "b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c"
EXPECTED_WATER_PBO = "3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14"
N = 2048
CELL = 6.0
SEA = 0.85
CHUNK = 96
HASH_WORKERS = 8
MAX_SECONDS = 600.0
MAX_PEAK_BYTES = 3 * 1024**3
MIN_FREE_BYTES = 6 * 1024**3
ACTIVE_VERIFIED: dict[str, str] = {}
ACTIVE_RECORDER: "PhaseRecorder | None" = None


def sha(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


class PhaseRecorder:
    """Durable phase markers plus bounded resource/hash metrics for V2 only."""
    def __init__(self, output_path: Path, started: float):
        self.output_path = output_path
        self.started = started
        self.rows: list[dict] = []
        self.current = "admission"
        self.resource_probe = None
        self.last_mark_time = started
        self.last_mark_cpu = time.process_time()
        self.progress_path = output_path.with_suffix(output_path.suffix + ".progress.json")
        self.lock = threading.Lock()

    def mark(self, name: str, state: str = "complete", **details) -> None:
        now=time.perf_counter();cpu_now=time.process_time()
        row = {"phase": name, "state": state, "elapsed_seconds": now-self.started,
               "interval_wall_seconds":now-self.last_mark_time,
               "interval_process_cpu_seconds":cpu_now-self.last_mark_cpu, **details}
        self.last_mark_time=now;self.last_mark_cpu=cpu_now
        if self.resource_probe is not None:
            try: row["memory"] = self.resource_probe()
            except Exception as exc: row["memory_probe_error"] = f"{type(exc).__name__}: {exc}"
        with self.lock:
            self.current = name
            self.rows.append(row)
            payload = {"schema":"global-dry-rollback.instrumented-v2.progress.v1",
                       "last_phase":name,"phase_state":state,"elapsed_seconds":row["elapsed_seconds"],
                       "phases":self.rows}
            self.progress_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.progress_path.with_suffix(self.progress_path.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, sort_keys=True)
                f.write("\n")
            os.replace(tmp, self.progress_path)

    def metrics(self) -> list[dict]:
        return list(self.rows)


def _hash_one(path_text: str) -> tuple[str, int, float]:
    path = Path(path_text)
    h = hashlib.sha256()
    size = 0
    began = time.perf_counter()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
            size += len(block)
    return h.hexdigest(), size, time.perf_counter()-began


def hash_many(paths, recorder: PhaseRecorder | None = None, phase: str = "hash") -> tuple[dict[str,str], dict]:
    """Hash each normalized path once per batch, with eight bounded readers."""
    canonical = sorted({str(Path(p).resolve()) for p in paths})
    wall0 = time.perf_counter()
    cpu0 = time.process_time()
    with ThreadPoolExecutor(max_workers=HASH_WORKERS, thread_name_prefix="consumer-hash") as pool:
        rows = list(pool.map(_hash_one, canonical))
    wall = time.perf_counter()-wall0
    cpu = time.process_time()-cpu0
    result = {p: row[0] for p,row in zip(canonical, rows)}
    sizes = [row[1] for row in rows]
    elapsed = [row[2] for row in rows]
    total_bytes = int(sum(sizes))
    metric = {"phase":phase,"unique_paths":len(canonical),"bytes_hashed":total_bytes,
              "wall_seconds":wall,"process_cpu_seconds":cpu,
              "throughput_bytes_per_second":total_bytes/max(wall,1e-12),
              "cpu_to_wall_ratio":cpu/max(wall,1e-12),
              "max_file_seconds":max(elapsed,default=0.0),
              "median_file_seconds":float(np.median(elapsed)) if elapsed else 0.0,
              "workers":HASH_WORKERS}
    if recorder is not None:
        recorder.mark(phase, "complete", **{k:v for k,v in metric.items() if k != "phase"})
    return result, metric


def validate_admission_paths(paths) -> list[str]:
    """Fail closed on any missing path before beginning a hash batch."""
    canonical=sorted({str(Path(p).resolve()) for p in paths})
    missing=[p for p in canonical if not Path(p).is_file()]
    if missing:
        raise FileNotFoundError("admission input missing: "+", ".join(missing[:8]))
    return canonical


def load_module(name: str, path: Path, expected: str):
    actual = ACTIVE_VERIFIED.get(str(path.resolve())) or sha(path)
    if actual != expected:
        raise ValueError(f"pinned helper drift: {path}: {actual} != {expected}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load independent helper {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def inward_float32(raw: np.ndarray, lower: bool) -> np.ndarray:
    raw64 = np.asarray(raw, dtype=np.float64)
    out = raw64.astype(np.float32)
    wrong = out.astype(np.float64) < raw64 if lower else out.astype(np.float64) > raw64
    out[wrong] = np.nextafter(out[wrong], np.float32(np.inf if lower else -np.inf))
    return out


def exact_domain_identity(base: np.ndarray, candidate: np.ndarray, variables: np.ndarray,
                          protected: dict[str, np.ndarray], expected_count: int | None = 2_712_136,
                          focus_rc: tuple[int,int] | None = (840,370)) -> dict:
    if base.dtype != np.float32 or candidate.dtype != np.float32 or base.ndim!=2 or base.shape[0]!=base.shape[1] or candidate.shape != base.shape:
        raise ValueError("terrain heights must be square float32 grids")
    rc = np.asarray(variables)
    if rc.dtype != np.int32 or rc.ndim!=2 or rc.shape[1]!=2 or (expected_count is not None and len(rc)!=expected_count):
        raise ValueError("variable coordinates do not match the expected row-major domain")
    n=base.shape[0]
    if np.any(rc<0) or np.any(rc>=n):raise ValueError("variable coordinate outside terrain")
    domain = np.zeros((n, n), dtype=bool)
    domain[rc[:, 0], rc[:, 1]] = True
    if int(domain.sum()) != len(rc):
        raise ValueError("variable coordinates contain duplicates")
    changed = candidate != base
    fixed_changes = changed & ~domain
    protected_changes = {k: int(np.count_nonzero(changed & np.asarray(v, dtype=bool))) for k, v in protected.items()}
    focus_unchanged = True if focus_rc is None else bool(candidate[focus_rc] == base[focus_rc])
    return {
        "variable_count": int(domain.sum()), "changed_vertices": int(changed.sum()),
        "fixed_changes": int(fixed_changes.sum()), "protected_changes": protected_changes,
        "focus_unchanged": focus_unchanged,
        "changed_rc": np.argwhere(changed).astype(np.int32), "domain": domain,
        "pass": not fixed_changes.any() and not any(protected_changes.values()) and focus_unchanged,
    }


def rebuild_levels(p: np.ndarray, f: np.ndarray) -> np.ndarray:
    n=p.shape[0]+1 if p.ndim==2 else -1
    if p.dtype != np.float64 or f.dtype != np.float64 or p.shape != (n-1, n-1) or f.shape != (n-1, n-1, 4):
        raise ValueError("P/F must be the original binary64 samples")
    if np.isinf(p).any() or np.isinf(f).any():
        raise ValueError("P/F infinities are invalid; NaN alone means absent")
    levels = np.full((n, n), SEA, dtype=np.float64)
    pn = np.nan_to_num(p, nan=SEA)
    for k, (dr, dc) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
        face = np.maximum(SEA, np.maximum(pn, np.nan_to_num(f[:, :, k], nan=SEA)))
        view = levels[dr:dr+n-1, dc:dc+n-1]
        np.maximum(view, face, out=view)
    return levels


def rebuild_bounds(ev95: np.ndarray, ev79: np.ndarray, o: np.ndarray,
                   p: np.ndarray, f: np.ndarray, variables: np.ndarray,
                   expected_lo: np.ndarray, expected_hi: np.ndarray) -> dict:
    levels = rebuild_levels(p, f)
    o64=np.asarray(o,dtype=np.float64)
    lo64 = np.maximum.reduce((ev95.astype(np.float64)-2.0,
                              np.minimum(o64, levels+1e-4),
                              np.minimum(o64, 1.8), o64-2.0))
    hi64 = np.minimum(ev95.astype(np.float64)+2.0, o64+2.0)
    lo32, hi32 = inward_float32(lo64, True), inward_float32(hi64, False)
    rc = variables.astype(np.int64)
    ri, ci = rc[:, 0], rc[:, 1]
    exact = np.array_equal(lo32[ri, ci], expected_lo) and np.array_equal(hi32[ri, ci], expected_hi)
    base_values = ev95[ri, ci]
    return {"levels": levels, "lo": lo32, "hi": hi32,
            "formula_matches_prepared": bool(exact),
            "candidate_within_bounds": bool(np.all(expected_lo <= base_values) and np.all(base_values <= expected_hi)),
            "min_baseline_clearance": float(np.min(ev95.astype(np.float64)-levels)),
            "min_lower_clearance": float(np.min(expected_lo.astype(np.float64)-levels[ri, ci])),
            "pass": bool(exact and np.all(expected_lo <= base_values) and np.all(base_values <= expected_hi))}


def direct_changed_water_clearance(base: np.ndarray, candidate: np.ndarray,
                                   changed_rc: np.ndarray, levels: np.ndarray) -> dict:
    rc=np.asarray(changed_rc,dtype=np.int64)
    if not len(rc):
        return {"changed_vertices":0,"baseline_nonpositive_samples":0,"candidate_nonpositive_samples":0,"pass":True}
    r,c=rc[:,0],rc[:,1]
    b=base[r,c].astype(np.float64)-levels[r,c]
    h=candidate[r,c].astype(np.float64)-levels[r,c]
    return {"changed_vertices":int(len(rc)),"minimum_baseline_clearance_m":float(np.min(b)),
      "minimum_candidate_clearance_m":float(np.min(h)),
      "baseline_nonpositive_samples":int(np.count_nonzero(b<=0.0)),
      "candidate_nonpositive_samples":int(np.count_nonzero(h<=0.0)),
      "pass":bool(np.all(b>0.0) and np.all(h>0.0))}


def check_d8_no_new_strict_minima(base: np.ndarray, candidate: np.ndarray,
                                  chunk_rows: int = CHUNK) -> dict:
    n=base.shape[0]
    if base.ndim!=2 or base.shape[1]!=n or candidate.shape!=base.shape:raise ValueError("D8 grids must be same-size squares")
    bmin0 = np.ones((n-2, n-2), dtype=bool)
    bmin1 = np.ones_like(bmin0)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == dc == 0:
                continue
            bnb = base[1+dr:n-1+dr, 1+dc:n-1+dc]
            hnb = candidate[1+dr:n-1+dr, 1+dc:n-1+dc]
            bmin0 &= base[1:-1, 1:-1] < bnb
            bmin1 &= candidate[1:-1, 1:-1] < hnb
    new = bmin1 & ~bmin0
    return {"baseline_strict_minima": int(bmin0.sum()), "candidate_strict_minima": int(bmin1.sum()),
            "new_strict_minima": int(new.sum()), "examples_rc": (np.argwhere(new)[:20] + 1).tolist(),
            "pass": not new.any()}


def check_d8_witness_order(base: np.ndarray, candidate: np.ndarray) -> dict:
    """Independently reproduce the frozen baseline-minimum witness ordering."""
    n=base.shape[0]
    if base.ndim!=2 or base.shape[1]!=n or candidate.shape!=base.shape:raise ValueError("D8 grids must be same-size squares")
    best=np.full((n,n),np.inf,dtype=np.float32)
    witness=np.full((n,n),-1,dtype=np.int32)
    offsets=(( -1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
    rows=np.arange(n,dtype=np.int32)[:,None]
    cols=np.arange(n,dtype=np.int32)[None,:]
    for dr,dc in offsets:
        r0=max(0,-dr);r1=min(n,n-dr);c0=max(0,-dc);c1=min(n,n-dc)
        target=best[r0:r1,c0:c1]
        neighbor=base[r0+dr:r1+dr,c0+dc:c1+dc]
        take=neighbor<target
        if np.any(take):
            target[take]=neighbor[take]
            ids=(rows[r0:r1]+dr)*n+(cols[:,c0:c1]+dc)
            dest=witness[r0:r1,c0:c1]
            dest[take]=ids[take]
    centers=np.flatnonzero((witness>=0)&(base>=best))
    wi=witness.ravel()[centers]
    after=candidate.ravel()
    bad=after[centers]<after[wi]
    return {"baseline_nonstrict_centers":int(len(centers)),"candidate_witness_violations":int(np.count_nonzero(bad)),
            "example_center_witness_flat":[[int(centers[i]),int(wi[i])] for i in np.flatnonzero(bad)[:20]],
            "pass":not np.any(bad)}


def _dihedral(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.degrees(np.arctan2(np.linalg.norm(np.cross(a,b),axis=-1),np.einsum("...i,...i->...",a,b)))


def collect_edge_angles(ev87, heights: np.ndarray, chunk_rows: int = CHUNK, check=None) -> dict[str,np.ndarray]:
    """Exact EV87 edge-angle families, filled in bounded normal chunks."""
    nmap=heights.shape[0]
    if heights.ndim!=2 or heights.shape[1]!=nmap:raise ValueError("angle grid must be square")
    diag=np.empty((nmap-1,nmap-1),dtype=np.float64)
    vertical=np.empty((nmap-1,nmap-2),dtype=np.float64)
    horizontal=np.empty((nmap-2,nmap-1),dtype=np.float64)
    for r0 in range(0,nmap-1,int(chunk_rows)):
        r1=min(nmap-1,r0+int(chunk_rows)); n=r1-r0
        # One extra terrain row supplies the lower-cell normals for horizontal edges.
        stop=min(nmap,r1+2)
        a,b=ev87.triangle_normals(heights[r0:stop].astype(np.float64,copy=False))
        q=min(n,a.shape[0]-1)
        diag[r0:r1]=_dihedral(a[:n],b[:n])
        vertical[r0:r1]=_dihedral(a[:n,:-1],b[:n,1:])
        if q:
            horizontal[r0:r0+q]=_dihedral(b[:q],a[1:q+1])
        if check is not None:check()
    return {"diag":diag,"vertical":vertical,"horizontal":horizontal}


def p99_nonregression(ev87, angles_b: dict[str,np.ndarray], angles_h: dict[str,np.ndarray],
                      base_arrays: dict[str,np.ndarray], constraints: dict[str,np.ndarray]) -> dict:
    populations=ev87._ev87_populations(base_arrays,constraints)
    result={}
    for name,pop in populations.items():
        old_parts=[];new_parts=[]
        for kind in ("diag","vertical","horizontal"):
            mask=np.logical_and.reduce(ev87.edge_vertex_slices(pop,kind))
            old_parts.append(np.asarray(angles_b[kind][mask],dtype=np.float64))
            new_parts.append(np.asarray(angles_h[kind][mask],dtype=np.float64))
        old=np.concatenate(old_parts);new=np.concatenate(new_parts)
        if not old.size or old.shape!=new.shape:
            raise ValueError(f"empty or misaligned p99 population: {name}")
        thr=ev87._ev87_thresholds(old)
        old_count=[int(np.count_nonzero(old<=thr["q0"])),int(np.count_nonzero(old<=thr["q1"]))]
        new_count=[int(np.count_nonzero(new<=thr["q0"])),int(np.count_nonzero(new<=thr["q1"]))]
        old_stats=ev87.summaries(old_parts);new_stats=ev87.summaries(new_parts)
        old99=old_stats["p99"];new99=new_stats["p99"]
        old30=old_stats["above30"];new30=new_stats["above30"]
        ok=new99<=old99+1e-4 and new30<=old30 and all(n>=o for o,n in zip(old_count,new_count))
        result[name]={"count":int(old.size),"baseline_p99_deg":old99,"candidate_p99_deg":new99,
          "brackets_deg":[thr["q0"],thr["q1"]],"baseline_bracket_counts":old_count,
          "candidate_bracket_counts":new_count,"baseline_above30":old30,"candidate_above30":new30,"pass":bool(ok)}
    return {"by_population":result,"pass":all(x["pass"] for x in result.values())}


def check_face_fields(ev87, base: np.ndarray, candidate: np.ndarray,
                      radii: np.ndarray, base_arrays: dict[str,np.ndarray],
                      constraints: dict[str,np.ndarray], chunk_rows: int = CHUNK,
                      check=None) -> dict:
    nmap=base.shape[0]
    if base.ndim!=2 or base.shape[1]!=nmap or candidate.shape!=base.shape:raise ValueError("face grid must be same-size squares")
    ncell = nmap - 1
    rad = np.asarray(radii, dtype=np.float64).reshape((ncell, ncell, 2))
    cone_bad = slope_bad = radius_rebuild_bad = 0
    max_slope_delta = -math.inf
    sector_size=64
    for r0 in range(0, ncell, int(chunk_rows)):
        r1 = min(ncell, r0 + int(chunk_rows))
        b = base[r0:r1+1].astype(np.float64, copy=False)
        h = candidate[r0:r1+1].astype(np.float64, copy=False)
        # Same triangle split and operation order as EV87.triangle_normals.
        bn0, bn1 = ev87.triangle_normals(b)
        hn0, hn1 = ev87.triangle_normals(h)
        bs0 = np.degrees(np.arctan2(np.hypot(bn0[..., 0], bn0[..., 2]), np.abs(bn0[..., 1])))
        bs1 = np.degrees(np.arctan2(np.hypot(bn1[..., 0], bn1[..., 2]), np.abs(bn1[..., 1])))
        hs0 = np.degrees(np.arctan2(np.hypot(hn0[..., 0], hn0[..., 2]), np.abs(hn0[..., 1])))
        hs1 = np.degrees(np.arctan2(np.hypot(hn1[..., 0], hn1[..., 2]), np.abs(hn1[..., 1])))
        slope_bad += int(np.count_nonzero(hs0 > np.maximum(bs0, 35.0)+1e-4))
        slope_bad += int(np.count_nonzero(hs1 > np.maximum(bs1, 35.0)+1e-4))
        max_slope_delta = max(max_slope_delta, float(np.max(hs0-np.maximum(bs0, 35.0))),
                              float(np.max(hs1-np.maximum(bs1, 35.0))))
        # Rebuild each prepared face radius independently from EV95 and 35 degrees.
        bnw,bne,bsw,bse=b[:-1,:-1],b[:-1,1:],b[1:,:-1],b[1:,1:]
        bg0=np.sqrt((bne-bnw)**2+(bne-bse)**2)
        bg1=np.sqrt((bse-bsw)**2+(bnw-bsw)**2)
        floor=6.0*math.tan(math.radians(35.0))
        expected_r0=np.maximum(floor,bg0);expected_r1=np.maximum(floor,bg1)
        radius_rebuild_bad+=int(np.count_nonzero(expected_r0!=rad[r0:r1,:,0]))
        radius_rebuild_bad+=int(np.count_nonzero(expected_r1!=rad[r0:r1,:,1]))
        # Candidate raw rise/run vector norms must stay inside the independent radii.
        nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
        g0 = np.sqrt((ne-nw)**2 + (ne-se)**2)
        g1 = np.sqrt((se-sw)**2 + (nw-sw)**2)
        cone_bad += int(np.count_nonzero(g0 > rad[r0:r1, :, 0]))
        cone_bad += int(np.count_nonzero(g1 > rad[r0:r1, :, 1]))
        if check is not None:check()
    del rad
    # Persist only scalar angle fields, never all full-map normal vectors.
    angles_b=collect_edge_angles(ev87,base,chunk_rows,check)
    angles_h=collect_edge_angles(ev87,candidate,chunk_rows,check)
    new30 = 0
    max_rows=max(v.shape[0] for v in angles_b.values())
    max_cols=max(v.shape[1] for v in angles_b.values())
    sector_b = np.zeros((math.ceil(max_rows/sector_size), math.ceil(max_cols/sector_size)), dtype=np.float64)
    sector_h = np.zeros_like(sector_b)
    for kind in angles_b:
        ab, ah = np.asarray(angles_b[kind]), np.asarray(angles_h[kind])
        new30 += int(np.count_nonzero((ab <= 30.0) & (ah > 30.0)))
        for sr in range(math.ceil(ab.shape[0]/sector_size)):
            r0, r1 = sr*sector_size, min(ab.shape[0], (sr+1)*sector_size)
            for sc in range(math.ceil(ab.shape[1]/sector_size)):
                c0, c1 = sc*sector_size, min(ab.shape[1], (sc+1)*sector_size)
                if r0 < r1 and c0 < c1:
                    sector_b[sr, sc] = max(sector_b[sr, sc], float(np.max(ab[r0:r1, c0:c1])))
                    sector_h[sr, sc] = max(sector_h[sr, sc], float(np.max(ah[r0:r1, c0:c1])))
    p99=p99_nonregression(ev87,angles_b,angles_h,base_arrays,constraints)
    return {"face_cone_violations": cone_bad, "slope_violations": slope_bad,
            "max_slope_over_baseline_or_35_deg": max_slope_delta,
            "new_hinges_over_30": new30,
            "sector_max_nonregression": bool(np.all(sector_h <= sector_b+1e-4)),
            "max_sector_delta_deg": float(np.max(sector_h-sector_b)),
            "p99_nonregression":p99,
            "radius_reconstruction_mismatches":radius_rebuild_bad,
            "pass": bool(cone_bad == 0 and slope_bad == 0 and radius_rebuild_bad == 0 and new30 == 0 and bool(np.all(sector_h <= sector_b+1e-4)) and p99["pass"])}


def rectangle_union(ranges: np.ndarray, n_cells: int) -> np.ndarray:
    """Rasterize inclusive cell rectangles using a 2-D difference array."""
    rr=np.asarray(ranges,dtype=np.int32)
    if rr.ndim!=2 or rr.shape[1]!=4:raise ValueError("cell ranges must be int32 [n,4]")
    if rr.size and (np.any(rr<0) or np.any(rr[:,0]>rr[:,1]) or np.any(rr[:,2]>rr[:,3]) or np.any(rr[:,1]>=n_cells) or np.any(rr[:,3]>=n_cells)):
        raise ValueError("invalid/off-grid inclusive cell range")
    diff=np.zeros((n_cells+1,n_cells+1),dtype=np.int32)
    r0,r1,c0,c1=rr.T if len(rr) else (np.empty(0,np.int32),)*4
    for r,c,v in ((r0,c0,1),(r1+1,c0,-1),(r0,c1+1,-1),(r1+1,c1+1,1)):
        np.add.at(diff,(r,c),v)
    counts=diff.cumsum(0,dtype=np.int32).cumsum(1,dtype=np.int32)[:-1,:-1]
    if np.any(counts<0):raise AssertionError("negative rectangle overlap count")
    return counts>0


def validate_face_identity(manifest: dict, deploy: dict) -> None:
    if manifest.get("schema")!="ev93.face-range-index.v1" or manifest.get("status")!="COMPLETE":
        raise ValueError("face-range index is not a complete supported schema")
    if manifest.get("water_object_ids_sha256")!=EXPECTED_FACE_IDS or int(manifest.get("object_count",-1))!=18024:
        raise ValueError("face-index compiled water identity digest/count changed")
    if int(manifest.get("counts",{}).get("faces",-1))!=883308:
        raise ValueError("face-index water face inventory count changed")
    base_identity=manifest.get("base_identity",{})
    expected_identity={"terrain_sha256":EXPECTED_BASE_TERRAIN,
        "wrp_source_sha256":PINNED[str(B_WRP)],
        "world_pbo_sha256":EXPECTED_WORLD_PBO,
        "water_pbo_sha256":EXPECTED_WATER_PBO}
    for key,wanted in expected_identity.items():
        if base_identity.get(key)!=wanted:
            raise ValueError(f"compiled-face index base identity mismatch: {key}")
    if (deploy.get("baseline_world_pbo_sha256")!=EXPECTED_WORLD_PBO or
        deploy.get("baseline_water_pbo_sha256")!=EXPECTED_WATER_PBO or
        deploy.get("baseline_terrain_sha256")!=EXPECTED_BASE_TERRAIN):
        raise ValueError("pinned EV95 deploy receipt does not agree with indexed compiled-water base")


def compare_water_topology(base: np.ndarray, candidate: np.ndarray, p: np.ndarray,
                           f: np.ndarray, corner_offsets, tris,
                           chunk_rows: int = CHUNK, check=None) -> dict:
    """Compare exact P/F/SEA corner signs and triangle masks in bounded chunks."""
    n=base.shape[0]
    if base.shape!=(n,n) or candidate.shape!=base.shape or p.shape!=(n-1,n-1) or f.shape!=(n-1,n-1,4):
        raise ValueError("water-topology inputs have inconsistent grids")
    sign_changes={"P":0,"F":0,"SEA":0}
    face_changes={"P":0,"F":0,"SEA":0}
    for r0 in range(0,n-1,int(chunk_rows)):
        r1=min(n-1,r0+int(chunk_rows))
        corners_b=[base[r0+dr:r1+dr,dc:dc+n-1].astype(np.float64,copy=False) for dr,dc in corner_offsets]
        corners_h=[candidate[r0+dr:r1+dr,dc:dc+n-1].astype(np.float64,copy=False) for dr,dc in corner_offsets]
        pseg=p[r0:r1]
        fseg=f[r0:r1]
        for name,levels in (("P",[pseg]*4),("F",[fseg[:,:,i] for i in range(4)]),
                            ("SEA",[np.full(pseg.shape,SEA,dtype=np.float64)]*4)):
            sb=[];sh=[]
            for i,level in enumerate(levels):
                valid=np.isfinite(level)
                if name=="SEA":valid[:]=True
                sb.append(valid & (level>corners_b[i]))
                sh.append(valid & (level>corners_h[i]))
                sign_changes[name]+=int(np.count_nonzero(sb[-1]!=sh[-1]))
            for tri in tris:
                fb=np.logical_or.reduce([sb[i] for i in tri])
                fh=np.logical_or.reduce([sh[i] for i in tri])
                if name=="F":
                    valid=np.logical_and.reduce([np.isfinite(fseg[:,:,i]) for i in tri])
                    fb &= valid;fh &= valid
                face_changes[name]+=int(np.count_nonzero(fb!=fh))
        if check is not None:check()
    return {"sign_changed_samples_by_surface":sign_changes,
            "native_triangle_mask_changes_by_surface":face_changes,
            "pass":not any(sign_changes.values()) and not any(face_changes.values())}


def reconstruct_civil_mask(civil_source, civil_npz: dict, stage: dict) -> dict:
    """Rebuild the global road/bridge protection from pinned source geometry."""
    if stage.get("status")!="STAGED_EV95_WIDE_HEIGHTS_ONLY" or stage.get("objects_and_materials_exact") is not True:
        raise ValueError("staged world object identity is not the frozen EV95 state")
    civil_source.WINDOW=(0,N,0,N)
    roads,road_report=civil_source.road_sample_cells()
    xy=np.load(civil_source.ROAD_REFERENCE,allow_pickle=False)["xy"]
    chains=json.loads(civil_source.ROAD_CHAINS.read_text(encoding="utf-8"))["chains"]
    short=[]
    for chain_id,chain in enumerate(chains):
        if len(chain)>=4:continue
        if len(chain)<2:raise ValueError("isolated road node lacks an explicit protection rule")
        pts=xy[np.asarray(chain,dtype=np.int64)]
        station=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
        if station[-1]<=0:raise ValueError("zero-length short road chain")
        samples=np.linspace(0.,station[-1],int(np.ceil(station[-1]))+1)
        q=np.column_stack([np.interp(samples,station,pts[:,d]) for d in (0,1)])
        for x,z in q:roads.update(civil_source.cells_for_world_point(float(x),float(z)))
        short.append(int(chain_id))
    bridges,bridge_report=civil_source.bridge_face_cells()
    def cell_mask(cells):
        valid=np.asarray(sorted((r,c) for r,c in cells if 0<=r<N-1 and 0<=c<N-1),dtype=np.int32).reshape(-1,2)
        out=np.zeros((N-1,N-1),dtype=bool)
        if len(valid):out[tuple(valid.T)]=True
        return out
    road_mask=cell_mask(roads)
    from scipy.ndimage import binary_dilation
    road_guard=binary_dilation(road_mask,structure=np.ones((3,3),dtype=bool))
    bridge_mask=cell_mask(bridges)
    cells=road_guard|bridge_mask
    vertices=np.zeros((N,N),dtype=bool)
    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):
        vertices[dr:dr+N-1,dc:dc+N-1]|=cells
    actual={"fixed_vertices":vertices,"road_sample_cells":road_mask,
            "road_guard_cells":road_guard,"bridge_cells":bridge_mask}
    exact={k:bool(np.array_equal(actual[k],np.asarray(civil_npz[k],dtype=bool))) for k in actual}
    return {"mask_arrays_exact":exact,"short_chain_ids_added":short,
            "road_sample_cells":int(road_mask.sum()),"road_guard_cells":int(road_guard.sum()),
            "bridge_cells":int(bridge_mask.sum()),"fixed_vertices":int(vertices.sum()),
            "road_report":road_report,"bridge_report":bridge_report,
            "pass":all(exact.values()) and len(short)==5}


def validate_face_index_water_guard(ev87, face_reader, manifest: dict, run_dir: Path,
                                    changed_mask: np.ndarray, water_guard: dict,
                                    masks: dict, source_paths: dict[str,str], check=None,
                                    deploy: dict | None = None,
                                    verified_hashes: dict[str,str] | None = None) -> dict:
    """Rebuild the inclusive face-bbox union and prove its vertex guard unchanged."""
    if deploy is None:raise ValueError("deploy receipt is required to bind compiled-water identity")
    validate_face_identity(manifest,deploy)
    # Re-enumerate actual WRP water IDs with the pinned parser.
    wrp_reader=load_module("postsolve_wrp_reader",WRP_READER,PINNED[str(WRP_READER)])
    wrp=wrp_reader.read(str(B_WRP))
    water_ids=sorted(int(o["id"]) for o in wrp["objects"] if "baltic_water_v30" in o["name"].replace("\\","/").lower())
    actual_ids=hashlib.sha256(np.asarray(water_ids,dtype="<i4").tobytes()).hexdigest()
    if len(water_ids)!=18024 or len(set(water_ids))!=18024 or actual_ids!=EXPECTED_FACE_IDS:
        raise ValueError("source WRP water object IDs do not reproduce the indexed identity digest")
    indexed_ids=set();total=0;per_kind={"physical":0,"visible":0};range_parts=[];degenerate=0
    for shard in manifest["shards"]:
        path=run_dir/shard["path"]
        actual=(verified_hashes or {}).get(str(path.resolve())) or sha(path)
        if actual!=shard["sha256"]:raise ValueError(f"face-index shard drift: {path}")
        source_paths[str(path.resolve())]=shard["sha256"]
        with np.load(path,allow_pickle=False) as z:arrays={k:z[k] for k in z.files}
        face_reader.FaceRangeIndex._validate_arrays(arrays,int(shard["records"]),path)
        total+=len(arrays["kind"]);degenerate+=int(arrays["degenerate"].sum())
        per_kind["physical"]+=int(np.count_nonzero(arrays["kind"]==0));per_kind["visible"]+=int(np.count_nonzero(arrays["kind"]==1))
        indexed_ids.update(map(int,np.unique(arrays["object_id"])))
        range_parts.append(arrays["cell_range_rc"])
        if check is not None:check()
    ranges=np.concatenate(range_parts,axis=0)
    if total!=883308 or total!=sum(per_kind.values()) or degenerate!=0 or indexed_ids!=set(water_ids):
        raise ValueError("face shards do not reproduce the complete water model inventory")
    if per_kind!={"physical":358577,"visible":524731}:
        raise ValueError("physical/visible face counts differ from the frozen index")
    model_records=manifest.get("models",[])
    if len(model_records)!=int(manifest.get("model_count",len(model_records))):
        raise ValueError("face-index model inventory count mismatch")
    for rec in model_records:
        name=rec.get("basename");expected=rec.get("sha256")
        path=MODEL_DIR/str(name)
        actual=(verified_hashes or {}).get(str(path.resolve())) or sha(path)
        if not name or not expected or actual!=expected:
            raise ValueError(f"compiled water model changed or is missing: {name}")
        source_paths[str(path.resolve())]=expected
        if check is not None:check()
    valid=np.all(ranges>=0,axis=1)
    if not np.all(valid):raise ValueError("off-grid face range prevents exact guard proof")
    r0,r1,c0,c1=ranges.T
    if np.any(r0>r1)|np.any(c0>c1)|np.any(r1>=N-1)|np.any(c1>=N-1):
        raise ValueError("face range is malformed or outside native cells")
    # Rebuild the inclusive bbox union with the same corner-difference identity,
    # then independently compare it with the frozen water guard's cell mask.
    union=rectangle_union(ranges,N-1)
    guard_cells=np.asarray(water_guard["face_bbox_cells"],dtype=bool)
    if guard_cells.shape!=(N-1,N-1) or not np.array_equal(union,guard_cells):
        raise ValueError("reconstructed compiled-face bbox union differs from frozen guard")
    vertex_guard=np.zeros((N,N),dtype=bool)
    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):
        vertex_guard[dr:dr+N-1,dc:dc+N-1]|=union
    if not np.array_equal(vertex_guard,water_guard["fixed_vertices"]):
        raise ValueError("compiled-face vertex guard differs from frozen guard")
    if not np.array_equal(vertex_guard,masks["water_bbox_nodes"]):
        raise ValueError("sizing water-bbox mask differs from reconstructed compiled face support")
    changed_touches=int(np.count_nonzero(changed_mask&vertex_guard))
    return {"objects":len(water_ids),"object_id_digest":actual_ids,"faces":total,"by_kind":per_kind,
      "degenerate_faces":degenerate,"bbox_guard_cells":int(union.sum()),"fixed_vertices":int(vertex_guard.sum()),
      "changed_guard_vertices":changed_touches,"model_count":len(model_records),
      "pass":changed_touches==0}


def run(receipt_path: Path, output_path: Path) -> dict:
    started = time.perf_counter()
    recorder = PhaseRecorder(output_path, started)
    global ACTIVE_RECORDER
    ACTIVE_RECORDER = recorder
    phase_metrics: list[dict] = []
    if not __debug__:
        raise RuntimeError("optimized Python is forbidden")
    receipt_path = receipt_path.resolve()
    if receipt_path != (RECOVERY / "receipt.json").resolve():
        raise ValueError("only the frozen-recovery run-01 receipt is allowed")
    if not receipt_path.exists(): raise FileNotFoundError(receipt_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    candidate_path = Path(receipt.get("candidate_path", "")).resolve()
    if candidate_path != (RECOVERY / "candidate-terrain.npz").resolve():
        raise ValueError("receipt candidate path is not the frozen-recovery artifact")
    if receipt.get("status") != "PENDING_INDEPENDENT_CONSUMER" or receipt.get("acceptance_status") != "PENDING_INDEPENDENT_CONSUMER" or receipt.get("terrain_written") is not True:
        raise ValueError("rollback is not an independently consumable terminal candidate")
    if receipt.get("candidate_sha256") != EXPECTED_CANDIDATE:
        raise ValueError("recovery candidate SHA mismatch")
    expected_receipt_fields={"source_sha256":EXPECTED_ROLLBACK_SOURCE,"core_sha256":EXPECTED_ROLLBACK_CORE,
        "plan_sha256":EXPECTED_ROLLBACK_PLAN,"review_sha256":EXPECTED_ROLLBACK_REVIEW}
    for key,wanted in expected_receipt_fields.items():
        if receipt.get(key)!=wanted:raise ValueError(f"recovery lineage mismatch: {key}")
    if receipt.get("source_readset_equal") is not True or receipt.get("source_readset_start") != receipt.get("source_readset_end"):
        raise ValueError("author source readset is not stable")
    author_readset=receipt.get("source_readset_start",{})
    if not isinstance(author_readset,dict) or not author_readset:
        raise ValueError("recovery receipt has no source readset")
    validate_admission_paths((receipt_path,candidate_path,SELF,PLAN_PATH,TEST_PATH))

    # Read only the small source manifests needed to discover every dependency.
    # They are all rehashed together below before any terrain evaluation.
    ev88_actual, ev88_metric = hash_many([EV88, MEMORY], recorder, "discover_ev88_and_memory_source")
    phase_metrics.append(ev88_metric)
    if ev88_actual[str(EV88.resolve())] != PINNED[str(EV88)]:
        raise ValueError(f"frozen source drift: {EV88}")
    if ev88_actual[str(MEMORY.resolve())] != PINNED[str(MEMORY)]:
        raise ValueError(f"frozen source drift: {MEMORY}")
    global ACTIVE_VERIFIED
    ACTIVE_VERIFIED = dict(ev88_actual)
    memory=load_module("postsolve_memory",MEMORY,PINNED[str(MEMORY)])
    early_free=int(memory.memory_status()["available_physical_bytes"])
    if early_free < MIN_FREE_BYTES+MAX_PEAK_BYTES:
        raise MemoryError("admission requires the 6-GiB reserve plus 3-GiB process allowance")
    recorder.mark("early_resource_admission", "complete", available_physical_bytes=early_free,
                  minimum_required_bytes=MIN_FREE_BYTES+MAX_PEAK_BYTES)
    ev88_discovery = load_module("postsolve_ev88_discovery", EV88, PINNED[str(EV88)])
    bundle_discovery = ev88_discovery.checked_sources()
    preflight_discovery = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    water_doc_discovery = json.loads(WATER_GUARD_RECEIPT.read_text(encoding="utf-8"))
    civil_doc_discovery = json.loads(CIVIL_RECEIPT.read_text(encoding="utf-8"))
    face_manifest_discovery = json.loads(FACE_MANIFEST.read_text(encoding="utf-8"))
    manifest_shards = [FACE_RUN / row["path"] for row in face_manifest_discovery.get("shards", [])]
    manifest_models = [MODEL_DIR / str(row.get("basename", "")) for row in face_manifest_discovery.get("models", [])]
    if not manifest_shards or not manifest_models or any(not p.name for p in manifest_models):
        raise ValueError("face-index manifest cannot enumerate its complete inputs")

    all_inputs = set(map(str, PINNED.keys()))
    all_inputs.update(str(Path(p).resolve()) for p in author_readset)
    all_inputs.update(str(Path(p).resolve()) for p in bundle_discovery["hashes"])
    all_inputs.update(str(Path(p).resolve()) for p in preflight_discovery.get("source_readset_start", {}))
    for doc in (water_doc_discovery, civil_doc_discovery):
        all_inputs.update(str(Path(p).resolve()) for p in doc.get("source_pins_start", {}))
    all_inputs.update(str(p.resolve()) for p in (receipt_path,candidate_path,SELF,PLAN_PATH,TEST_PATH))
    all_inputs.update(str(p.resolve()) for p in manifest_shards+manifest_models)
    all_inputs.update(str(Path(p).resolve()) for p in author_readset)
    canonical_inputs=validate_admission_paths(all_inputs)
    start_set, start_metric = hash_many(canonical_inputs, recorder, "complete_source_start_hash")
    phase_metrics.append(start_metric)

    expected_all: dict[str,str] = {}
    expected_all.update({str(Path(p).resolve()):v for p,v in PINNED.items()})
    expected_all.update({str(Path(p).resolve()):v for p,v in author_readset.items()})
    expected_all.update({str(Path(p).resolve()):v for p,v in bundle_discovery["hashes"].items()})
    expected_all.update({str(Path(p).resolve()):v for p,v in preflight_discovery.get("source_readset_start",{}).items()})
    for doc in (water_doc_discovery,civil_doc_discovery):
        expected_all.update({str(Path(p).resolve()):v for p,v in doc.get("source_pins_start",{}).items()})
    expected_all.update({str(p.resolve()):v for p,v in zip(manifest_shards,[x["sha256"] for x in face_manifest_discovery["shards"]])})
    expected_all.update({str(p.resolve()):v for p,v in zip(manifest_models,[x["sha256"] for x in face_manifest_discovery["models"]])})
    expected_all[str(receipt_path)] = EXPECTED_RECEIPT
    expected_all[str(candidate_path)] = EXPECTED_CANDIDATE
    for p in (SELF,PLAN_PATH,TEST_PATH): expected_all[str(p.resolve())] = start_set[str(p.resolve())]
    for p,wanted in expected_all.items():
        if p not in start_set:
            raise ValueError(f"source dependency missing from complete start readset: {p}")
        if start_set[p] != wanted:
            raise ValueError(f"source pin mismatch before evaluation: {p}: {start_set[p]} != {wanted}")
    ACTIVE_VERIFIED = dict(start_set)
    recorder.mark("source_start_set_validated", "complete", unique_paths=len(start_set),
                  expected_paths=len(expected_all), hash_metrics=phase_metrics)

    # Recheck after the comprehensive source hash and before allocating terrain grids.
    if int(memory.memory_status()["available_physical_bytes"]) < MIN_FREE_BYTES+MAX_PEAK_BYTES:
        raise MemoryError("admission requires the 6-GiB reserve plus 3-GiB process allowance")
    def resource_check():
        if time.perf_counter()-started > MAX_SECONDS:
            raise TimeoutError("600-second independent consumer budget exceeded")
        peak=int(memory.process_peak_working_set())
        free=int(memory.memory_status()["available_physical_bytes"])
        if peak>MAX_PEAK_BYTES:raise MemoryError("consumer exceeded 3-GiB process peak")
        if free<MIN_FREE_BYTES:raise MemoryError("consumer breached 6-GiB physical-memory reserve")
        return {"elapsed_seconds":time.perf_counter()-started,"peak_working_set_bytes":peak,
                "available_physical_bytes":free}
    recorder.resource_probe = lambda: {"peak_working_set_bytes":int(memory.process_peak_working_set()),
                                       "available_physical_bytes":int(memory.memory_status()["available_physical_bytes"])}

    ev87 = load_module("postsolve_ev87", EV87, PINNED[str(EV87)])
    ev88 = ev88_discovery
    layer = load_module("postsolve_layer", LAYER, PINNED[str(LAYER)])
    ao = load_module("postsolve_a_only", AO, PINNED[str(AO)])
    bundle=bundle_discovery
    recorder.mark("helpers_loaded", "complete", helper_count=5)
    resource_check()

    recorder.mark("terrain_arrays_started", "started")
    with np.load(BASE, allow_pickle=False) as z:
        base_arrays = {k: z[k].copy() for k in z.files}
    with np.load(candidate_path, allow_pickle=False) as z:
        candidate_arrays = {k: z[k].copy() for k in z.files}
    if set(base_arrays) != set(candidate_arrays):
        raise ValueError("candidate NPZ member set changed")
    for key, value in base_arrays.items():
        if key != "heights" and (candidate_arrays[key].dtype != value.dtype or candidate_arrays[key].shape != value.shape or candidate_arrays[key].tobytes() != value.tobytes()):
            raise ValueError(f"non-height terrain metadata changed: {key}")
    base, candidate = base_arrays["heights"], candidate_arrays["heights"]
    with np.load(BOUNDS, allow_pickle=False) as z:
        variables=z["variables_rc"].copy(); lower=z["lower_float32"].copy(); upper=z["upper_float32"].copy(); radii=z["face_radii"].copy()
    with np.load(MASKS, allow_pickle=False) as z:
        masks={k:z[k].astype(bool) for k in ("retained_499_halo2","p9_unknown_nodes","water_bbox_nodes","civil_nodes","water_shore_partial_nodes")}
        variable_mask=z["ev95_variable"].astype(bool)
    preflight=json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    recorder.mark("terrain_and_mask_inputs_loaded", "complete", base_shape=list(base_arrays["heights"].shape),
                  candidate_shape=list(candidate_arrays["heights"].shape))
    if preflight.get("status")!="PREFLIGHT_READY_GLOBAL_DRY_DOMAIN" and preflight.get("status")!="PREFLIGHT_READY_GLOBAL_DRY_BOUNDS":
        # Status wording varied between report revisions; identity fields are
        # the actual frozen contract and are checked below.
        if preflight.get("identity",{}).get("retained_windows")!=499:
            raise ValueError("global sizing preflight is not the frozen 499-window state")
    ident=preflight.get("identity",{});dom=preflight.get("domain",{})
    if (ident.get("EV95_sha256")!=EXPECTED_B or ident.get("retained_windows")!=499 or
        ident.get("retained_halo2_vertices")!=217438 or ident.get("focus_rc")!=[840,370] or
        ident.get("retained_artifact_count")!=998 or dom.get("EV95_delta_variable_after_guards")!=2712136):
        raise ValueError("sizing preflight identity/retained scope mismatch")
    if preflight.get("source_readset_start")!=preflight.get("source_readset_end"):
        raise ValueError("global sizing preflight has source drift")
    for p,expected in preflight["source_readset_start"].items():
        actual=ACTIVE_VERIFIED.get(str(Path(p).resolve()), "")
        if actual!=expected:raise ValueError(f"sizing-preflight source drift: {p}")
    domain=exact_domain_identity(base,candidate,variables,masks)
    if not np.array_equal(domain["domain"],variable_mask):
        raise ValueError("coordinate list and frozen variable mask disagree")
    changed=domain.pop("changed_rc")
    domain_mask=domain.pop("domain")
    domain["receipt_changed_count_matches"]=domain["changed_vertices"]==int(receipt.get("changed_vertices",-1))
    domain["pass"]=domain["pass"] and domain["receipt_changed_count_matches"]
    changed_mask=candidate!=base
    recorder.mark("domain_and_preflight", "complete", variable_count=len(variables),
                  changed_vertices=int(changed_mask.sum()))
    resource_check()
    # Independently reconstruct physical box from original binary64 P/F and EV79/O.
    recorder.mark("physical_geometry_started", "started")
    ev79=bundle["EV79"]["heights"]
    o=ev79
    p=np.load(P_PATH,allow_pickle=False,mmap_mode="r"); f=np.load(F_PATH,allow_pickle=False,mmap_mode="r")
    bounds=rebuild_bounds(base,ev79,o,p,f,variables,lower,upper)
    recorder.mark("physical_bounds_rebuilt", "complete", variables=len(variables))
    values=candidate[variables[:,0],variables[:,1]]
    bounds["candidate_inside_box"]=bool(np.all(values>=lower) and np.all(values<=upper))
    bounds["pass"] = bounds["pass"] and bounds["candidate_inside_box"]
    water_clearance=direct_changed_water_clearance(base,candidate,changed,bounds["levels"])
    bounds["pass"] = bounds["pass"] and water_clearance["pass"]
    recorder.mark("water_topology_started", "started")
    water_topology=compare_water_topology(base,candidate,p,f,ev87.CORNER_OFFSETS,ev87.TRIS,check=resource_check)
    bounds["pass"] = bounds["pass"] and water_topology["pass"]
    resource_check()
    recorder.mark("physical_bounds_water_topology", "complete", water_topology_pass=bool(water_topology["pass"]))

    recorder.mark("d8_started", "started")
    d8=check_d8_no_new_strict_minima(base,candidate)
    d8["witness_order"]=check_d8_witness_order(base,candidate)
    d8["pass"]=d8["pass"] and d8["witness_order"]["pass"]
    resource_check()
    recorder.mark("d8_minima", "complete", pass_gate=bool(d8["pass"]))
    recorder.mark("face_fields_started", "started")
    face=check_face_fields(ev87,base,candidate,radii,base_arrays,bundle["constraints"],check=resource_check)
    resource_check()
    recorder.mark("native_faces_and_sectors", "complete", pass_gate=bool(face["pass"]))
    # Verify independent precomputed civil and compiled-water guard lineage.
    with np.load(WATER_GUARD,allow_pickle=False) as z:water_guard={k:z[k].copy() for k in z.files}
    with np.load(CIVIL_MASK,allow_pickle=False) as z:civil_mask={k:z[k].copy() for k in z.files}
    water_doc=json.loads(WATER_GUARD_RECEIPT.read_text(encoding="utf-8"));civil_doc=json.loads(CIVIL_RECEIPT.read_text(encoding="utf-8"))
    if water_doc.get("status")!="PREPARED_CONSERVATIVE_GLOBAL_WATER_GUARD_ONLY" or water_doc.get("mask_sha256")!=PINNED[str(WATER_GUARD)]:
        raise ValueError("compiled-water guard receipt does not bind its mask")
    if civil_doc.get("status")!="PREPARED_GLOBAL_CIVIL_MASK_ONLY" or civil_doc.get("mask_sha256")!=PINNED[str(CIVIL_MASK)]:
        raise ValueError("civil guard receipt does not bind its mask")
    for doc,label in ((water_doc,"water guard"),(civil_doc,"civil guard")):
        if doc.get("source_pins_start")!=doc.get("source_pins_end"):
            raise ValueError(f"{label} preparation had source drift")
        for p,wanted in doc["source_pins_start"].items():
            actual=ACTIVE_VERIFIED.get(str(Path(p).resolve()), "")
            if actual!=wanted:raise ValueError(f"{label} lineage drift: {p}")
    civil_source=load_module("postsolve_civil_source",CIVIL_SOURCE,PINNED[str(CIVIL_SOURCE)])
    civil_source_pins=civil_source.check_pins()
    if any(civil_doc["source_pins_start"].get(p)!=v for p,v in civil_source_pins.items()):
        raise ValueError("civil source pins do not match the source's own declared input set")
    stage_doc=json.loads(STAGE.read_text(encoding="utf-8"))
    civil_reconstruction=reconstruct_civil_mask(civil_source,civil_mask,stage_doc)
    recorder.mark("civil_mask_reconstructed", "complete", pass_gate=bool(civil_reconstruction["pass"]))
    if not np.array_equal(civil_mask["fixed_vertices"],masks["civil_nodes"]):
        raise ValueError("civil protection mask differs from the frozen global domain guard")
    if int(civil_mask["fixed_vertices"].sum())!=100215 or int(water_guard["fixed_vertices"].sum())!=523044:
        raise ValueError("civil or compiled-water mask cardinality changed")
    # Reconstruct exact P9 unknown-corridor vertices from the pinned P array,
    # 19 corridor polygons, and independent EV87 geometry helpers.
    p9_cells,p9_nodes,p9_by_feature=layer.global_p9_unknown_vertices(ev87,bundle)
    p9_exact=np.zeros((N,N),dtype=bool)
    if p9_nodes:p9_exact[tuple(np.asarray(sorted(p9_nodes),dtype=np.int64).T)]=True
    if not np.array_equal(p9_exact,masks["p9_unknown_nodes"]):
        raise ValueError("P9 unknown-corridor node mask differs from independent corridor reconstruction")
    resource_check()
    recorder.mark("p9_reconstructed", "complete", cells=len(p9_cells), nodes=len(p9_nodes))
    # The critical compiled support proof is reconstructed from every face range.
    manifest=json.loads(FACE_MANIFEST.read_text(encoding="utf-8"))
    verification=json.loads(FACE_VERIFICATION.read_text(encoding="utf-8"))
    deploy=json.loads(DEPLOY.read_text(encoding="utf-8"))
    if verification.get("status")!="PASS_INDEX_AND_SAMPLED_EXPOSURE" or verification.get("manifest_sha256")!=PINNED[str(FACE_MANIFEST)]:
        raise ValueError("compiled-water index verification report does not bind the manifest")
    recorder.mark("compiled_support_started", "started", models=len(manifest.get("models",[])),
                  shards=len(manifest.get("shards",[])))
    face_reader=load_module("postsolve_face_index_reader",FACE_BUILDER,PINNED[str(FACE_BUILDER)])
    compiled=validate_face_index_water_guard(ev87,face_reader,manifest,FACE_RUN,changed_mask,water_guard,masks,start_set,
                                             check=resource_check,deploy=deploy,verified_hashes=ACTIVE_VERIFIED)
    resource_check()
    recorder.mark("civil_p9_compiled_support", "complete", compiled_face_pass=bool(compiled["pass"]))
    # Require the frozen protected masks plus actual indexed face bounds to prove dry-only support.
    water_support={name:int(np.count_nonzero(changed_mask & mask)) for name,mask in masks.items() if name in ("water_bbox_nodes","water_shore_partial_nodes","p9_unknown_nodes","civil_nodes","retained_499_halo2")}
    water_masks_pass=not any(water_support.values()) and water_clearance["pass"]
    # Independent original A-only objective: report only after exact domain and source checks.
    screen=json.loads(SCREEN.read_text(encoding="utf-8"))
    op=ao.build_a_only(base,variables)
    baseline_values=base[variables[:,0],variables[:,1]].astype(np.float64)
    candidate_values=values.astype(np.float64)
    baseline_residual=op.matvec_a(baseline_values)-op.rhs_a
    candidate_residual=op.matvec_a(candidate_values)-op.rhs_a
    cost_b=float(np.dot(baseline_residual,baseline_residual));cost_h=float(np.dot(candidate_residual,candidate_residual))
    objective={"baseline_cost":cost_b,"candidate_cost":cost_h,"strict_improvement":cost_h<cost_b,
               "baseline_matches_screen":abs(cost_b-float(screen["objective_baseline"]))<=1e-8*max(1.,abs(cost_b)),
               "pass":cost_h<cost_b and abs(cost_b-float(screen["objective_baseline"]))<=1e-8*max(1.,abs(cost_b))}
    recorder.mark("objective", "complete", pass_gate=bool(objective["pass"]))

    # Re-hash every input after the independent calculations.
    end_set, end_metric = hash_many(start_set.keys(), recorder, "complete_source_end_hash")
    phase_metrics.append(end_metric)
    readset_equal=end_set==start_set
    resource_final=resource_check()
    gates={"domain_exact":bool(domain["pass"]),"physical_bounds_and_water_clearance":bool(bounds["pass"]),
           "d8_no_new_minima":bool(d8["pass"]),"face_slope_hinge_sector":bool(face["pass"]),
           "protected_water_p9_civil_retained":water_masks_pass and civil_reconstruction["pass"],
           "compiled_water_face_support":bool(compiled["pass"]),"original_objective_strict_improvement":bool(objective["pass"]),
           "source_readset_start_end_equal":readset_equal}
    status="PASS_GLOBAL_DRY_ROLLBACK_CANDIDATE" if all(gates.values()) else "FAIL_OR_INCONCLUSIVE_GLOBAL_DRY_ROLLBACK"
    report={"schema":"global-dry-rollback.independent-consumer.v1","status":status,
        "candidate_path":str(candidate_path),"candidate_sha256":end_set[str(candidate_path)],
        "recovery_receipt_path":str(receipt_path),"recovery_receipt_sha256":end_set[str(receipt_path)],
        "source_pins_start":start_set,"source_pins_end":end_set,"gates":gates,
        "domain":domain,"resource":resource_final,
        "bounds":{k:v for k,v in bounds.items() if k not in ("levels","lo","hi")},
        "d8":d8,"shape":face,"water":{"protected_mask_changes":water_support,"changed_water_clearance":water_clearance,
            "p_f_sea_sign_and_face_topology":water_topology,
            "p9_reconstructed_cells":len(p9_cells),"p9_features_with_unknown_cells":len(p9_by_feature),"compiled_face_bbox":compiled},
        "civil_independent_reconstruction":civil_reconstruction,
        "objective":objective,"elapsed_seconds":time.perf_counter()-started,"source_readset_equal":readset_equal,
        "instrumentation":{"hash_workers":HASH_WORKERS,"hash_batches":phase_metrics,
          "phases":recorder.metrics(),"last_phase":"complete_source_end_hash",
          "hash_bytes_total":int(sum(m["bytes_hashed"] for m in phase_metrics)),
          "unique_hashes_per_batch":{m["phase"]:m["unique_paths"] for m in phase_metrics}},
        "limitations":["No deployment/build/native-runtime claims.",
          "A compiled-water bbox touching any changed vertex is fail-closed; exact ODOL clipping is not substituted.",
          "P9 corridor geometry is re-enumerated through the pinned global consumer helper; its corridor definitions remain the governing source contract."]}
    output_path.parent.mkdir(parents=True,exist_ok=True)
    with output_path.open("x",encoding="utf-8") as stream:
        stream.write(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out=args.out.resolve()
    if not args.out.is_relative_to((HERE/"runs").resolve()):
        print(json.dumps({"status":"ERROR_INDEPENDENT_CONSUMER","error":"report output must stay under consumer runs directory"}))
        return 1
    try:
        result=run(args.receipt,args.out)
        print(json.dumps({"status":result["status"],"gates":result["gates"],"candidate_sha256":result["candidate_sha256"]},sort_keys=True))
        return 0 if result["status"]=="PASS_GLOBAL_DRY_ROLLBACK_CANDIDATE" else 1
    except Exception as exc:
        error={"schema":"global-dry-rollback.independent-consumer.v1","status":"ERROR_INDEPENDENT_CONSUMER",
               "error":f"{type(exc).__name__}: {exc}","acceptance_claim":False}
        if ACTIVE_RECORDER is not None:
            try: ACTIVE_RECORDER.mark(ACTIVE_RECORDER.current, "error", error=error["error"])
            except Exception: pass
            error["instrumentation"]={"last_phase":ACTIVE_RECORDER.current,
                                      "phases":ACTIVE_RECORDER.metrics(),
                                      "progress_path":str(ACTIVE_RECORDER.progress_path),
                                      "hash_workers":HASH_WORKERS}
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with args.out.open("x",encoding="utf-8") as stream:
            stream.write(json.dumps(error,indent=2,sort_keys=True)+"\n")
        print(json.dumps(error,sort_keys=True))
        return 1


if __name__=="__main__":
    raise SystemExit(main())
