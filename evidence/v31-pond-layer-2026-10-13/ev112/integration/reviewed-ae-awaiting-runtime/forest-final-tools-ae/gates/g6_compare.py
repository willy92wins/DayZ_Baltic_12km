"""G6 determinism: two placer runs with the same inputs, seed, region, tile and halo give byte-identical outputs.

Usage: python -I g6_compare.py <run_a_dir> <run_b_dir>
Compares records.json, report.json, instances.npy and the work rasters (work/*.npy) by SHA-256. PASS when all are
identical and non-empty. The negative control passes two runs with seeds s and s + 1 and must print FAIL."""
import hashlib
import sys
from pathlib import Path

a, b = Path(sys.argv[1]), Path(sys.argv[2])
files = ["records.json", "report.json", "instances.npy"] + sorted("work/" + p.name for p in (a / "work").glob("*.npy"))
ok = True
for f in files:
    pa, pb = a / f, b / f
    ha = hashlib.sha256(pa.read_bytes()).hexdigest() if pa.exists() else None
    hb = hashlib.sha256(pb.read_bytes()).hexdigest() if pb.exists() else None
    same = ha is not None and ha == hb and pa.stat().st_size > 0
    ok &= same
    print(f"  {f:22s} {str(ha)[:16]} {str(hb)[:16]} {'identical' if same else 'DIFFERENT'}")
print(f"G6 {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
