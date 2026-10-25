"""Records inside the two EV111 pilot squares (sectors.json polygons' bounding boxes), for the unchanged EV111 r2 gate
scripts (scripts-v3r2/gates: g1, g2_g3, g4, g5, g7_bog), which read every record into memory and judge the
instances inside each polygon. Order kept. Usage: python -I pilot_subset.py <records.json> <out.json>"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import gcfg  # noqa: E402
import recio  # noqa: E402

models, midx, m, _ = recio.load_records(sys.argv[1])
keep = np.zeros(len(midx), bool)
for sec in json.loads(gcfg.SECTORS.read_text(encoding="utf-8"))["sectors"]:
    p = np.asarray(sec["polygon_xz"], float)
    keep |= (m[:, 9] >= p[:, 0].min()) & (m[:, 9] < p[:, 0].max()) & (m[:, 11] >= p[:, 1].min()) & (m[:, 11] < p[:, 1].max())
recio.write_records(sys.argv[2], models, midx[keep], m[keep])
print(f"{int(keep.sum())} of {len(midx)} records in the pilot squares -> {sys.argv[2]}")
