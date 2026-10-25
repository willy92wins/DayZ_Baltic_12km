"""Prepared one-build/one-action memory measurement; do not run before review."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import threading
import time

import numpy as np

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
PROTO = PARENT.parent
OP_DIR = PROTO / "global-structured-operator"
PREP = PROTO / "global-dry-solve" / "prepared-01"
TERRAIN = PROTO.parent / "build-wide-slope" / "candidate" / "terrain.npz"
RUN = HERE / "measurement" / "run-01"
PLAN = HERE / "PLAN.md"
FIXTURES = HERE / "fixture-report.json"
FIXTURE_SOURCE = HERE / "test_a_only_operator.py"
SOURCE = HERE / "a_only_operator.py"
FUSED = OP_DIR / "optimized-normal" / "fused_normal.py"
MEMORY = OP_DIR / "measure_global_actions.py"
SCREEN = PARENT / "screen.py"
SCREEN_REVIEW = PARENT / "independent-review.json"

PINNED = {
    TERRAIN: "40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a",
    OP_DIR / "structured_operator.py": "d3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a",
    FUSED: "19a3e3a493f643702e66aaf265c705739535d386412f74659369d7746117ffaa",
    MEMORY: "a05a5f47b775567105c3e588e7106b4b365b58d259f018dca4f243f57d2da37b",
    PREP / "bounds.npz": "b0c4499776148b080049a528807e31a62d5fd11ba90fcaae5a7881124cde81fb",
    PREP / "receipt.json": "9e55afb4b736a3b558d3e631c62fa94c98a0ae2bb7da4e5513850375758869f3",
    PREP / "independent-review.json": "d454b78bf8721a9f6477001bb1e5ba77ed4716fc1fdd03232a6084cc6612bf85",
    SCREEN: "1dd4b4fe3b2c081298639e120e95a0ba278aa23a1d81aae7c80850d688dd6459",
    SCREEN_REVIEW: "70b2a5cfd499eea904527d7548faa026ec4361ae0406551ee22ec120d1fa1611",
}
MIN_FREE = 6 * 1024**3
MAX_PEAK = 1 * 1024**3
BUDGET_S = 120.0


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024**2), b""):
            h.update(block)
    return h.hexdigest()


def load_pinned(path, name, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise RuntimeError(f"pinned source changed: {path}")
    spec = importlib.util.spec_from_loader(name, loader=None, origin=str(path))
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = str(path)
    sys.modules[name] = mod
    exec(compile(data, str(path), "exec"), mod.__dict__)
    return mod


class Guard:
    def __init__(self, memory_module, started):
        self.mem = memory_module
        self.started = started
        self.samples = []
        self.failure = None
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._watch, daemon=True)

    def sample(self):
        row = {"elapsed_s": time.perf_counter()-self.started,
               "peak_working_set_bytes": self.mem.process_peak_working_set(),
               "available_physical_bytes": self.mem.memory_status()["available_physical_bytes"]}
        self.samples.append(row)
        if row["elapsed_s"] > BUDGET_S: raise TimeoutError("120s measurement budget")
        if row["peak_working_set_bytes"] > MAX_PEAK: raise MemoryError("1 GiB process peak cap")
        if row["available_physical_bytes"] < MIN_FREE: raise MemoryError("6 GiB free RAM floor")
        return row

    def _watch(self):
        while not self.stop_event.wait(.25):
            try: self.sample()
            except Exception as e:
                self.failure = self.failure or f"{type(e).__name__}: {e}"
                return

    def check(self):
        if self.failure: raise RuntimeError(self.failure)
        return self.sample()

    def start(self): self.thread.start()
    def close(self):
        self.stop_event.set()
        if self.thread.is_alive(): self.thread.join(timeout=2.0)


def run(review_path: Path, review_sha: str):
    started = time.perf_counter()
    if not __debug__: raise RuntimeError("optimized Python is not permitted")
    review_path = review_path.resolve()
    if sha(review_path) != review_sha.lower(): raise RuntimeError("review pin mismatch")
    review = json.loads(review_path.read_text(encoding="utf-8-sig"))
    if review.get("status") != "PASS_A_ONLY_FIXTURES" or review.get("source_sha256") != sha(SOURCE):
        raise RuntimeError("A-only source is not independently reviewed")
    if review.get("plan_sha256") != sha(PLAN) or review.get("fixture_report_sha256") != sha(FIXTURES):
        raise RuntimeError("A-only plan/fixtures are not pinned by review")
    if review.get("driver_sha256") != sha(Path(__file__).resolve()):
        raise RuntimeError("A-only benchmark driver is not independently reviewed")
    for path, expected in PINNED.items():
        if sha(path) != expected:
            raise RuntimeError(f"Pinned input/source hash mismatch: {path}")
    read_paths = [*PINNED, SOURCE, PLAN, FIXTURES, FIXTURE_SOURCE, review_path, Path(__file__).resolve()]
    readset = {str(Path(p).resolve()): sha(p) for p in read_paths}
    if sha(FIXTURE_SOURCE) != review.get("fixture_source_sha256"):
        raise RuntimeError("fixture source pin mismatch")

    mem = load_pinned(MEMORY, "a_only_verified_memory", PINNED[MEMORY])
    if mem.memory_status()["available_physical_bytes"] < MIN_FREE + MAX_PEAK:
        raise MemoryError("Insufficient free RAM for 1 GiB cap + unchanged 6 GiB reserve")
    if RUN.exists(): raise FileExistsError(f"exclusive measurement already exists: {RUN}")
    RUN.mkdir(parents=True, exist_ok=False)
    out = RUN / "measurement.json"
    receipt = {"status": "STARTED", "source_readset_start": readset,
               "terrain_written": False, "solver_run": False}
    out.write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    guard = Guard(mem, started)
    guard.start()
    try:
        guard.check()
        # Load only the inputs used by this A-only construction and one action.
        with np.load(TERRAIN, allow_pickle=False) as z:
            base = z["heights"].astype(np.float64)
        with np.load(PREP / "bounds.npz", allow_pickle=False) as z:
            variables = z["variables_rc"]
            x0 = z["baseline_values"]
        if base.shape != (2048, 2048) or len(variables) != 2_712_136:
            raise ValueError("pinned global input dimensions differ")
        if not np.array_equal(base[tuple(variables.T)], x0):
            raise ValueError("baseline values do not match pinned terrain")
        source_key = str(SOURCE.resolve())
        opmod = load_pinned(SOURCE, "a_only_verified_operator", readset[source_key])
        fusedmod = load_pinned(FUSED, "a_only_verified_fused", PINNED[FUSED])
        build_start = time.perf_counter()
        op = opmod.build_a_only(base, variables)
        build_s = time.perf_counter()-build_start
        guard.check()
        action = fusedmod.FusedNormalAction(op)
        action_start = time.perf_counter()
        y = action.a_normal(x0)
        action_s = time.perf_counter()-action_start
        if y.shape != x0.shape or not np.isfinite(y).all(): raise RuntimeError("A normal output invalid")
        guard.check()
        final_set = {str(Path(p).resolve()): sha(p) for p in read_paths}
        if final_set != readset: raise RuntimeError("input/source drift")
        receipt.update({"status":"COMPLETE_A_ONLY_MEMORY_MEASUREMENT", "A_rows":op.n_a,
                       "variables":op.n, "anchor_counts":{"xx":len(op.xx_rc),"zz":len(op.zz_rc),"xz":len(op.xz_rc)},
                       "build_seconds":build_s,"one_a_normal_seconds":action_s,
                       "normal_output_l2":float(np.linalg.norm(y)),"source_readset_end":final_set,
                       "source_readset_equal":True})
    except Exception as e:
        receipt.update({"status":"TERMINAL_A_ONLY_MEASUREMENT_FAILURE", "error":f"{type(e).__name__}: {e}"})
    finally:
        guard.close()
        try:
            guard.sample()
            final_set = {str(Path(p).resolve()): sha(p) for p in read_paths}
            guard.sample()
            receipt["source_readset_end"] = final_set
            receipt["source_readset_equal"] = (final_set == readset)
            if final_set != readset:
                receipt.update({"status":"TERMINAL_SOURCE_DRIFT", "error":"input/source readset changed during measurement"})
        except Exception as e:
            receipt.update({"status":"TERMINAL_FINAL_GUARD_FAILURE", "final_error":f"{type(e).__name__}: {e}"})
        receipt.update({"elapsed_seconds":time.perf_counter()-started,
                        "peak_working_set_bytes":max((x["peak_working_set_bytes"] for x in guard.samples),default=None),
                        "minimum_available_physical_bytes":min((x["available_physical_bytes"] for x in guard.samples),default=None),
                        "resource_samples":len(guard.samples),"watchdog_failure":guard.failure})
        if guard.failure and receipt.get("status")=="COMPLETE_A_ONLY_MEMORY_MEASUREMENT":
            receipt.update({"status":"TERMINAL_RESOURCE_GUARD_FAILURE", "error":guard.failure})
        out.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--review-json",required=True,type=Path)
    parser.add_argument("--review-sha256",required=True)
    args=parser.parse_args()
    result=run(args.review_json,args.review_sha256)
    print(json.dumps(result,indent=2),flush=True)
    raise SystemExit(0 if result.get("status")=="COMPLETE_A_ONLY_MEMORY_MEASUREMENT" else 1)
