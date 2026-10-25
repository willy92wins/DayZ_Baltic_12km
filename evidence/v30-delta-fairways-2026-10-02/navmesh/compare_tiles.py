"""Read-only old/new TESM6 comparison, using the checked empirical tile reader."""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/navigation'))
from inspect_navmesh_tiles import read


def offmesh_headers(path):
    # Observed Detour header subset: do not parse/rewrite polygon topology.
    data = path.read_bytes()
    count = struct.unpack_from('<I', data, 8)[0]
    offsets = struct.unpack_from(f'<{count}I', data, 48)
    base = 48 + 4 * count
    values = {}
    for offset in offsets:
        header = struct.unpack_from('<15I', data, base + offset + 16)
        values[tuple(header[2:4])] = header[13]
    return values


old_path = Path('E:/DayZ-Baltic-Build/navmesh-v30/baltic_trial.nm')
new_path = Path('E:/DayZ-Baltic-Build/navmesh-v30-delta/baltic_trial.nm')
old = read(old_path, tile_width=12.5)
new = read(new_path, tile_width=12.5)
oc, nc = offmesh_headers(old_path), offmesh_headers(new_path)
assert set(old) == set(new) == set(oc) == set(nc)
assert sum(oc.values()) == 687 and sum(nc.values()) == 121, 'Must match the two saved UI totals'
changed = [k for k in old if old[k]['sha256'] != new[k]['sha256']]
structural = [k for k in changed if any(old[k][f] != new[k][f] for f in ('polygons','vertices','y_bounds'))]
off = [k for k in old if oc[k] != nc[k]]
def bounds(keys):
    return [min(k[0] for k in keys)*12.5,min(k[1] for k in keys)*12.5,
            (max(k[0] for k in keys)+1)*12.5,(max(k[1] for k in keys)+1)*12.5] if keys else None
result = {
    'status':'DIAGNOSTIC_NOT_ACCEPTANCE',
    'old_sha256':hashlib.sha256(old_path.read_bytes()).hexdigest(),
    'new_sha256':hashlib.sha256(new_path.read_bytes()).hexdigest(),
    'tiles':len(new),'byte_changed':len(changed),'structural_changed':len(structural),
    'changed_bounds_xz':bounds(changed),'structural_bounds_xz':bounds(structural),
    'offmesh_old':sum(oc.values()),'offmesh_new':sum(nc.values()),'offmesh_changed_tiles':len(off),
    'offmesh_bounds_xz':bounds(off),
    'offmesh_deltas':[{'tile':k,'old':oc[k],'new':nc[k]} for k in off],
    'limits':['Empirical installed-format header subset, cross-checked against saved UI totals; no complete decoder or causal claim.']}
out = Path(__file__).with_name('tile-comparison.json')
with out.open('x',encoding='utf8') as f:
    json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k != 'offmesh_deltas'},indent=2))
