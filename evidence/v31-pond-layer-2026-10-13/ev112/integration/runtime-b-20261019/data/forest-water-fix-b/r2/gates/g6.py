"""G6: determinism. The placer run twice gives byte-identical records.json, report.json and instances.npy.

Usage: python -I g6.py <forest_v31.py> <seed_a> <seed_b> <work_dir>
PASS when the run with seed_a and the run with seed_b produce identical bytes for the three outputs. The gate proper
uses seed_a == seed_b; the negative control passes seed_b = seed_a + 1 and must print FAIL.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gate_common as GC  # noqa: E402

tool, sa, sb, work = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), Path(sys.argv[4])
COVER = GC.E / "ev111-wip/forest/layers.npz"


def run(seed, out):
    args = [sys.executable, "-I", tool, "--terrain", str(GC.TERRAIN), "--footprint", str(GC.FOOTPRINT),
            "--stage-wrp", str(GC.STAGE_WRP), "--pbo", GC.PBO]
    for d in GC.LAYER_DIRS:
        args += ["--layer-dir", d]
    args += ["--cover", str(COVER), "--sectors", str(GC.SECTORS), "--reference", str(GC.REFERENCE), "--seed", str(seed),
             "--out", str(out)]
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode:
        print(p.stdout[-2000:], p.stderr[-2000:])
        raise SystemExit("placer failed")


work.mkdir(parents=True, exist_ok=True)
a, b = work / f"run-a-seed{sa}", work / f"run-b-seed{sb}"
for d in (a, b):
    if d.exists():
        raise SystemExit(f"{d} exists")
run(sa, a)
run(sb, b)
ok = True
for f in ("records.json", "report.json", "instances.npy"):
    ha = hashlib.sha256((a / f).read_bytes()).hexdigest()
    hb = hashlib.sha256((b / f).read_bytes()).hexdigest()
    same = ha == hb and (a / f).stat().st_size > 0
    ok &= same
    print(f"  {f:14s} {ha[:16]} {hb[:16]} {'identical' if same else 'DIFFERENT'}")
print(f"G6 {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
