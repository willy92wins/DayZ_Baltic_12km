from pathlib import Path
import ast,json,hashlib,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
import py3d,compact_stream_collision_v31 as packing,midpoint_stream_collision_v31 as midpoint
from review_compact_collision_v31 import load
source=R/'author_kit7_midpoint_collision.py';tree=ast.parse(source.read_text())
scope=dict(np=np,py3d=py3d,packing=packing)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='checked_grid')
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),scope)
old=R/'river-kit7-a-on-f-20261026';report=json.loads((old/'author-report.json').read_text());inst=report['instances'][0]
model=old/'source'/inst['model'].replace('\\','/');cases=[]
for mode in ['positive','missing_face','changed_diagonal','wrong_lod']:
 _,lods,_=load(model)
 if mode=='missing_face':del lods[0].faces[0]
 if mode=='changed_diagonal':
  bedfaces=[f for f in lods[0].faces if 'water_streambed.rvmat' not in f.material]
  assert {tuple(sorted(v.point_index for v in f.vertices)) for f in bedfaces[:2]}=={(0,39,40),(0,1,40)}
  for face,indices in zip(bedfaces[:2],[(0,39,1),(39,40,1)]):
   for v,i in zip(face.vertices,indices):v.point_index=i
 if mode=='wrong_lod':lods[0],lods[1]=lods[1],lods[0]
 rejected=False
 try:grid=scope['checked_grid'](lods,inst['collision_components'])
 except AssertionError:rejected=True
 assert rejected==(mode!='positive'),mode
 cases.append(dict(mode=mode,passed=True,rejected=rejected))
env=dict(Path=Path,__file__=str(source),packing=packing,midpoint=midpoint,py3d=py3d,R=R,W=W,old=old,baseline_path=R/'kit7-collision-baseline-20261026/result.json')
node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='required' for t in n.targets));exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),env)
guard=next(n for n in tree.body if isinstance(n,ast.Assert) and 'Incomplete reviewed input binding' in ast.unparse(n))
for mode,keys in [('complete_binding',env['required']),('empty_binding',set())]:
 env['review']=dict(inputs=dict.fromkeys(keys,'not_a_hash_test'));rejected=False
 try:exec(compile(ast.Module(body=[guard],type_ignores=[]),str(source),'exec'),env)
 except AssertionError:rejected=True
 assert rejected==(mode=='empty_binding');cases.append(dict(mode=mode,passed=True,rejected=rejected))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
result=dict(status='AUTHOR_GUARD_CONTROLS_PASS',source_sha256=sha(source),control_sha256=sha(__file__),model=str(model),model_sha256=sha(model),cases=cases,limits='Real saved model plus in-memory mutations; no author run or geometry write. Hash drift is checked separately by frozen launch manifest.')
out=R/'kit7-midpoint-review/guard-controls.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
