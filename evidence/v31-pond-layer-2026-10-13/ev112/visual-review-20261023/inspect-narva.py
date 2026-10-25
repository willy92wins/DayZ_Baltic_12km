"""Read-only local evidence for VIEW-NARVA-01; does not alter build inputs."""
import hashlib
import json
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
BUILD = Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
WT = Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
CONTRACT = WT / 'evidence/v31-pond-layer-2026-10-13/dam/frozen-exception-narva.json'
REPORT = BUILD / 'dam/dam-report.json'
FINAL = BUILD / 'water-fix-b/terrain.npz'

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

contract = json.loads(CONTRACT.read_text(encoding='utf-8-sig'))
report = json.loads(REPORT.read_text(encoding='utf-8-sig'))
before_path = Path(report['inputs']['terrain'])
env_path = Path(report['inputs']['envelope'])
assert sha(FINAL) == '07054c46ebf2861bc905fe2d68fb3b734d7b8e9ad1d538c73a7ee745edd56d62'
assert sha(CONTRACT) == '28191cce4fe4ec7f240bbaf14cc7a07546748a98fdaa5221661b1649150668a2'
assert sha(before_path) == report['inputs']['terrain_sha256']
assert sha(env_path) == report['inputs']['envelope_sha256']
with np.load(before_path) as z:
    before = z['heights']
with np.load(FINAL) as z:
    final = z['heights']
env_before = np.load(env_path)
env_after = np.load(BUILD / 'dam/envelope-dam.npy')
assert sha(BUILD / 'dam/envelope-dam.npy') == report['outputs']['envelope_sha256']
cells = []
vertices = set()
for cell in contract['cut_cells']:
    r, c = cell['r'], cell['c']
    corners = [(r, c), (r+1, c), (r, c+1), (r+1, c+1)]
    vertices.update(corners)
    hf = np.array([final[y, x] for y, x in corners])
    cells.append(dict(r=r, c=c, x0=cell['x0'], z_north=cell['z_north'],
                      old_water=float(env_before[r, c]), removed=bool(not np.isfinite(env_after[r, c])),
                      corner_min=float(hf.min()), corner_max=float(hf.max()),
                      fully_dry_at_reference_sea_075=bool(np.all(hf >= .75))))
# Bound Narva local comparison to 126 x 108 m; coordinate definitions read from dam_v31.py:367-390.
r0, r1, c0, c1 = 880, 899, 394, 416
diff = final[r0:r1, c0:c1] != before[r0:r1, c0:c1]
changed = [(int(r+r0), int(c+c0)) for r,c in np.argwhere(diff)]
authorized = {(v['r'],v['c']) for v in contract['vertices']}
record = dict(
    schema='ev112-narva-local-diagnostic-v1', defect='VIEW-NARVA-01',
    terrain_sha256=sha(FINAL), contract_sha256=sha(CONTRACT),
    local_bounds_xz=[6*c0, 6*(c1-1), 12282-6*(r1-1), 12282-6*r0],
    cut_cells=len(cells), all_approved_cuts_absent_in_dam_envelope=all(v['removed'] for v in cells),
    cut_cells_fully_dry_at_sea_075=sum(v['fully_dry_at_reference_sea_075'] for v in cells),
    distinct_cut_vertices=len(vertices),
    cut_vertices_unchanged_from_before=sum(bool(final[r,c]==before[r,c]) for r,c in vertices),
    cut_vertices_exactly_1m=sum(bool(final[r,c]==1.0) for r,c in vertices),
    local_changed_vertices=len(changed), local_changed_set_matches_contract=set(changed)==authorized,
    conclusion='The approved cut removes pond water above dry terrain. This explains exposure of the old bed. Rectangular outline attribution to exact rendered features still requires comparing the local contour with the screenshot.',
    limits=['Sea 0.75 m is the source-defined mid-tide reference, not a measured instantaneous tide.',
            'Dam-stage envelope is inspected; this diagnostic alone does not revalidate the final water PBO geometry.',
            'No source, terrain, water, contract or deployed package was changed.'],
    cells=cells)
(OUT/'narva-local-diagnostic.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k!='cells'},indent=2))
