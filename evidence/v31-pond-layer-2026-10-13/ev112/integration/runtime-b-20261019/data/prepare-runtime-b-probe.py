"""Keep every original probe ID, coordinate and expected kind; update only terrain reference heights."""
from pathlib import Path
import numpy as np,json,sys,hashlib,shutil
O=Path(__file__).parent;D=O/'water-fix-b';P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');Q=O/'probe-runtime-b';Q.mkdir(exist_ok=False)
sys.path.insert(0,str(P/'tools/terrain'));from v30_common import tri_sample
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((O/'final-consumers-c/kit/probe/points.json').read_text());new=json.loads((D/'kit/probe/points.json').read_text());assert len(old)==len(new)==3000
changes=[]
for a,b in zip(old,new):
 assert {k:v for k,v in a.items() if k!='ground'}=={k:v for k,v in b.items() if k!='ground'},(a['id'],'probe selection/metadata changed')
 if a.get('ground')!=b.get('ground'):changes.append(a['id'])
h=np.load(D/'terrain.npz')['heights']
for name in ('points.json','bridges-points.json','shores-points.json','dam-points.json'):
 pts=json.loads((O/'probe-c'/name).read_text());items=pts['points'] if isinstance(pts,dict) else pts
 gs=tri_sample(h,[p['x'] for p in items],[p['z'] for p in items])
 for p,g in zip(items,gs):
  if 'ground' in p:p['ground']=float(g)
 (Q/name).write_text(json.dumps(pts,indent=2)+'\n')
for name in ('points.csv','families.json'):shutil.copyfile(O/'probe-c'/name,Q/name)
manifest=dict(status='PREPARED_NOT_RUN',points=4114,inputs={str(D/'terrain.npz'):sha(D/'terrain.npz'),str(O/'fp-ev112-c/footprint.npz'):sha(O/'fp-ev112-c/footprint.npz'),**{str(Q/n):sha(Q/n) for n in ('points.json','points.csv','families.json','dam-points.json')}},original_csv_sha256=sha(O/'probe-c/points.csv'),kit_selection_identical_except_ground=True,kit_reference_ids_with_height_change=changes,scope=__doc__)
assert manifest['original_csv_sha256']==sha(Q/'points.csv');(Q/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
s=(O/'evaluate-runtime-probe-c.py').read_text();pairs=[("Q=O/'probe-c'","Q=O/'probe-runtime-b'"),("O/'final-consumers-c/kit'","O/'water-fix-b/kit'"),("O/'final-consumers-c/kit/gate-g8.json'","O/'water-fix-b/kit/gate-g8.json'"),("O/'terrain-ev112-c.npz'","O/'water-fix-b/terrain.npz'")]
for a,b in pairs:assert a in s,a;s=s.replace(a,b)
target=O/'evaluate-runtime-probe-runtime-b.py';assert not target.exists();target.write_text(s)
print(json.dumps(dict(points=4114,csv_identical=True,kit_height_changes=changes,evaluator=str(target))))
