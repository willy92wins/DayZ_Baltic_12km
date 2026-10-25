from pathlib import Path
import json,hashlib
import numpy as np
B=Path(__file__).parent;R=B.parent;S=R/'v30-strict-dry-composition-20261009/candidate';D=R/'v30-low-flowing-support-scope-20261009';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (B/'authoring.json').exists()
policy=json.loads((D/'volkhov-policy.json').read_text());assert policy['status']=='PASS_LOCAL_REACH_POLICY_NOT_AUTHORED'
row=next(a for a in json.loads((D/'scope.json').read_text())['groups'] if a['group']==349);d=np.load(D/'volkhov-policy-domain.npz');r0,r1,c0,c1=d['box'];sl=np.s_[r0:r1,c0:c1];shift=policy['shift_m']
t=dict(np.load(S/'terrain.npz'));p=np.load(S/'plane.npy');f=np.load(S/'visible-field.npy');h=t['heights'];v=h.copy();v[sl]=d['trial'];q=p.copy();g=f.copy();q[d['cells']]+=shift;g[d['cells']]+=shift
level=t['level'].copy();metadata=d['core']&np.isfinite(level)&(t['cls']>0);level[metadata]+=shift
dest=B/'candidate';dest.mkdir(exist_ok=False);np.savez_compressed(dest/'terrain.npz',**(t|dict(heights=v,level=level)));np.save(dest/'plane.npy',q);np.save(dest/'visible-field.npy',g)
allowed=np.zeros(h.shape,bool);allowed[sl]=d['weight']>0;np.savez_compressed(B/'domain.npz',allowed=allowed,core=d['core'],cells=d['cells'],metadata=metadata,fixed=d['fixed'])
report=dict(status='PREPARED_PROPOSAL_NOT_PROMOTED',source_sha256=sha(S/'terrain.npz'),terrain_sha256=sha(dest/'terrain.npz'),plane_sha256=sha(dest/'plane.npy'),field_sha256=sha(dest/'visible-field.npy'),shift_m=shift,group=349,components=row['all_components'],object_translations={str(oid):shift for oid in row['objects']},changed_vertices=int((v!=h).sum()),metadata_vertices=int(metadata.sum()),level_policy_exception_pending_components=[647,651],policy_reference_sha256=sha(D/'volkhov-policy.json'))
(B/'authoring.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='object_translations'},indent=2))
