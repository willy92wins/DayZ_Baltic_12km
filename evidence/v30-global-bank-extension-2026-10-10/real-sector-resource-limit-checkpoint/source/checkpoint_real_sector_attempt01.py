"""Archive only the closed first real-sector attempt, without following build trees."""
from pathlib import Path
import hashlib
import json
import shutil

G=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
P=G/'global-operator-prototype'
R=P/'real-sector-preflight'
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
DEST=W/'evidence/v30-global-bank-extension-2026-10-10/real-sector-resource-limit-checkpoint'
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()

files=[P/'PLAN_REAL_SECTOR.md',P/'admm-quantized-pilot/solve.py',P/'prototype.py',
       P/'float32-closure-study/float32_closure.py',G/'constrained-pilot/d8_sparse_pilot.py',
       R/'solve_real_sector.py',R/'prepare_inventory.py',R/'civil_inventory.py',R/'prepare_water_footprint.py',
       R/'verify_real_sector.py',R/'verify_real_sector.preflight-reviewed-dcf3600d1149b278fba9fcb4dc2d0263fb34b90a0cd5083838d229777e251bab.py',
       R/'verify_real_sector.root-reviewed-703f29380b0359df61a3d699573d68c6abdbe7a9688806e5c09867fd787a343e.py',
       R/'ROOT_REVIEW.md',R/'verify_kkt_scale_fixture.py',R/'kkt-scale-fixture.json',
       R/'preflight-independent-review.json',R/'preflight-independent-review-attempt-03.json',
       R/'preflight-independent-review-history.md',R/'preflight-run-01/preflight.json',
       R/'preflight-run-01.log',R/'solve-run-01.log',R/'solve-run-01/solver.started',
       R/'solve-run-01/progress.jsonl',R/'solve-run-01/solve-result.json',
       R/'civil-run-01.json',R/'civil-run-01-receipt.json',R/'inventory-run-02.json/inventory.json',
       R/'water-run-01/water-support-mask.json',Path(__file__).resolve()]
large=[R/'preflight-run-01/prepared.npz',R/'inventory-run-02.json/domain-reasons.npz',
       R/'water-run-01/water-support-mask.npz']
result=json.loads((R/'solve-run-01/solve-result.json').read_text())
assert result['status']=='RESOURCE_LIMIT' and result['candidate_path'] is None and result['solver_state_path'] is None
assert sha(R/'solve-run-01/solve-result.json')=='eedb911f07a4feb3c8ff0e9936dd9c6ad547cd7d92e057ac90de72bc1ae16d5f'
assert sha(R/'solve_real_sector.py')=='9f4fc8e5edc2ad7a8276264d4b6fea05ee8682b777d370cb75a283f0cb4d296e'
assert sha(R/'verify_real_sector.py')=='703f29380b0359df61a3d699573d68c6abdbe7a9688806e5c09867fd787a343e'
assert sha(R/'preflight-run-01/prepared.npz')=='8a8a1cf8e9b6906b1aab8053877383d01a92baa5bd2c18b54b1b9e43c8c37a21'
if DEST.exists():raise FileExistsError(DEST)
items=[]
for src in files:
    if not src.is_file():raise FileNotFoundError(src)
    if src.stat().st_size>8*1024**2:raise RuntimeError(f'Oversized source: {src}')
    items.append((src,sha(src)))
refs=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in large]
DEST.mkdir(parents=True)
copied=[]
for src,want in items:
    rel=src.relative_to(G)
    dst=DEST/'source'/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
    assert sha(src)==want==sha(dst)
    copied.append({'source':str(src),'relative_path':str(rel),'sha256':want,'bytes':dst.stat().st_size})
manifest={'status':'ARCHIVED_RESOURCE_LIMIT_NO_CANDIDATE','copy_count':len(copied),
          'copied_files':copied,'large_references':refs,'result_sha256':sha(R/'solve-run-01/solve-result.json'),
          'scope':'Closed single attempt; no candidate or map acceptance; telemetry hypothesis not included as a proven cause',
          'unavailable_historical_source':'49775a4d7010b15d69c0310245b111ef7f3f33314c93bd77ab637ef8b3efaff4 (old D7BD); final preflight proof uses archived dcf3600d instead'}
(DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':manifest['status'],'copied':len(copied),'references':len(refs),'destination':str(DEST)}))
