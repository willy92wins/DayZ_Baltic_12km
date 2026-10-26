"""Read saved MLODs and run the unchanged full-contact consumer; never build/deploy."""
from pathlib import Path
import subprocess,json,hashlib,sys,time,os
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water')]
from review_compact_collision_v31 import load
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
read=lambda p:json.loads(Path(p).read_text())
write=lambda p,x:Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
original=R/'river-kit7-a-on-f-20261026';candidate=R/'river-kit7-midpoint-a-20261026';O=R/'kit7-midpoint-saved-review-20261026'
receipt=read(R/'kit7-midpoint-author-run-20261026/receipt.json')
assert receipt['returncode']==0 and not receipt['timeout'] and receipt['inputs_unchanged']
gate=read(R/'kit7-midpoint-review/accepted.json');assert all(sha(p)==h for p,h in gate['inputs'].items())
reports=[read(root/'author-report.json') for root in (original,candidate)]
assert reports[1]['collision_packing']['status']=='CANDIDATE_GLOBAL_OVERLAY_PENDING'
paths=[Path(__file__),candidate/'author-report.json',candidate/'packing-report.json',R/'kit7-midpoint-author-run-20261026/receipt.json',R/'kit7-midpoint-review/accepted.json']
paths.extend(candidate/'source'/i['model'].replace('\\','/') for i in reports[1]['instances'])
frozen={**gate['inputs'],**{str(p):sha(p) for p in paths}}
O.mkdir(exist_ok=False);write(O/'inputs.json',frozen)
rows=[]
old={i['model']:i for i in reports[0]['instances']};new={i['model']:i for i in reports[1]['instances']}
assert set(old)==set(new) and len(old)==len(new)==139
for name in old:
 data={}
 for label,root,inst in [('before',original,old[name]),('after',candidate,new[name])]:
  p=root/'source'/name.replace('\\','/');assert sha(p)==inst['sha256']
  header,lods,blobs=load(p);geo=lods[1]
  face_ids=[id(f) for s in geo.selections.values() for f in s.faces]
  assert len(face_ids)==len(set(face_ids))==len(geo.faces) and set(face_ids)=={id(f) for f in geo.faces}
  data[label]=dict(components=len(geo.selections),faces=len(geo.faces),vertices=len(geo.points),max_vertices_per_component=max(len(s.points) for s in geo.selections.values()),max_faces_per_component=max(len(s.faces) for s in geo.selections.values()),bytes=p.stat().st_size)
  if label=='before':old_header,old_blobs=header,blobs
  else:assert header==old_header and all(blobs[k]==old_blobs[k] for k in [0,2,3])
 assert old[name]['origin']==new[name]['origin']
 ok=all(data['after'][k]<=data['before'][k] for k in ['components','faces','vertices']) and data['after']['max_vertices_per_component']<=72 and data['after']['max_faces_per_component']<=140
 rows.append(dict(model=name,**data,non_geometry_lods_byte_exact=True,origin_unchanged=True,cost_pass=ok))
totals={s:{k:(max(r[s][k] for r in rows) if k.startswith('max_') else sum(r[s][k] for r in rows)) for k in rows[0][s]} for s in ['before','after']}
passed=all(r['cost_pass'] for r in rows) and totals['after']['components']<totals['before']['components']
write(O/'costs.json',dict(status='PASS_SAVED_COST_BUDGET' if passed else 'FAIL',totals=totals,models=rows,limits='Per-component maxima rise from6/8; cap72/140 from nativeC only bounds complexity, not performance equivalence.'))
assert passed
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
args=[sys.executable,'-I',str(W/'tools/water/review_compact_collision_v31.py'),str(original),str(candidate),str(O/'contact.json')]
began=time.time();timeout=False
with (O/'consumer.stdout.log').open('wb') as out,(O/'consumer.stderr.log').open('wb') as err:
 try:q=subprocess.run(args,env=env,stdout=out,stderr=err,timeout=1800,creationflags=0x08000000|0x00004000);code=q.returncode
 except subprocess.TimeoutExpired:code=None;timeout=True
same=all(sha(p)==h for p,h in frozen.items())
result=read(O/'contact.json') if (O/'contact.json').exists() else None
passed=code==0 and not timeout and same and result and result['status']=='SAVED_COLLISION_PASS'
write(O/'receipt.json',dict(status='PASS_SAVED_KIT7_COLLISION' if passed else 'INCONCLUSIVE' if timeout or result is None else 'FAIL',returncode=code,timeout=timeout,seconds=time.time()-began,inputs_unchanged=same,contact_sha256=sha(O/'contact.json') if result else None,args=args,limits='Saved MLOD cost/contact only; compilation, ODOL centres, terrain/forest integration, native/visual acceptance remain separate.'))
print(json.dumps(dict(status='PASS_SAVED_KIT7_COLLISION' if passed else 'NOT_ACCEPTED',costs=totals,contact=result['contact']['checks'] if result else None),indent=2))
raise SystemExit(0 if passed else 1)
