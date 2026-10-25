"""Records I/O for the EV112 forest gates: records.json (a JSON list of {"model", "matrix"}, any layout) to arrays."""
import json
from pathlib import Path

import numpy as np


def load_records(path, bbox=None):
    """Returns (models: sorted list of model paths, midx: uint16 index per record, m: (n, 12) float64 matrices, keys_ok:
    bool per record (exactly the keys model and matrix)). bbox = (x0, z0, x1, z1) keeps the records whose position lies
    inside (the original order is kept). Parsed with one json.loads per record line when the file has one record per
    line, else with json.loads of the whole file."""
    raw = Path(path).read_bytes()
    lines = raw.split(b"\n")
    one_per_line = len(lines) > 2 and lines[0].strip() == b"[" and lines[1].lstrip().startswith(b"{") and lines[1].rstrip().rstrip(b",").endswith(b"}")
    if one_per_line:
        recs = (json.loads(ln.rstrip().rstrip(b",")) for ln in lines[1:] if ln.strip() not in (b"", b"]"))
    else:
        recs = iter(json.loads(raw.decode("ascii")))
    names, mats, keys = [], [], []
    for r in recs:
        names.append(r.get("model"))
        mats.append(r.get("matrix"))
        keys.append(set(r) == {"model", "matrix"})
    m = np.array([x if isinstance(x, list) and len(x) == 12 else [np.nan] * 12 for x in mats], float)
    keys = np.array(keys, bool)
    models = sorted({n for n in names if isinstance(n, str)})
    pos = {n: i for i, n in enumerate(models)}
    midx = np.array([pos.get(n, 65535) if isinstance(n, str) else 65535 for n in names], np.uint32)
    if bbox is not None:
        x0, z0, x1, z1 = bbox
        k = (m[:, 9] >= x0) & (m[:, 9] < x1) & (m[:, 11] >= z0) & (m[:, 11] < z1)
        midx, m, keys = midx[k], m[k], keys[k]
    return models, midx, m, keys


def write_records(path, models, midx, m):
    """The placer's layout: one record per line."""
    with open(path, "wb") as f:
        f.write(b"[\n")
        n = len(midx)
        for k in range(n):
            f.write((json.dumps({"model": models[midx[k]], "matrix": [float(v) for v in m[k]]}) + (",\n" if k + 1 < n else "\n")).encode("ascii"))
        f.write(b"]\n")
