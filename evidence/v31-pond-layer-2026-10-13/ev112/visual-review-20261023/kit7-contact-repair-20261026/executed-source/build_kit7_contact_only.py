"""One isolated candidate using the previously verified local overlap operator."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/water'))
from review_compact_collision_v31 import load,py3d
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,d:p.write_text(json.dumps(d,indent=2)+'\n')
discovery=read(R/'kit7-contact-only-discovery.json')
assert discovery['all_bbox_exact'] and discovery['horizontal_excess_models']==0 and discovery['oversized']==0
gate={'inputs':{str(W/'plans/ev112-kit7-rv-contact-20261026.md'):sha(W/'plans/ev112-kit7-rv-contact-20261026.md'),str(R/'kit7-contact-only-discovery.json'):sha(R/'kit7-contact-only-discovery.json')}}
old=R/'river-kit7-midpoint-a-20261026';out=R/'river-kit7-contact-only-20261026';O=R/'kit7-contact-only-build-20261026'
assert not out.exists()
if O.exists():assert not any(O.iterdir()), 'Only empty preflight output can resume'
else:O.mkdir()
targets=R/'kit7-native-contact-diagnosis-20261026/targets.json';names=sorted(read(targets));assert len(names)==19
paths=[Path(__file__),targets,old/'author-report.json',W/'tools/water/overlap_stream_collision_v31.py',W/'tools/water/review_compact_collision_v31.py',W/'tools/water/compact_stream_collision_v31.py',W/'tools/water/pack_continuous_stream_pilot_v31.ps1',W/'tools/water/verify_compiled_stream_pilot_v31.py']
paths += [Path('C:/temp/moto_lanes/review_g3/tools')/n for n in ('odol_reader.py','bis_reader.py','math_types.py')]
paths += sorted(Path(py3d.__file__).parent.rglob('*.py'))
assert Path(py3d.__file__) in paths
frozen={**gate['inputs'],**{str(p):sha(p) for p in paths}}
for i in read(old/'author-report.json')['instances']:
 p=old/'source'/i['model'].replace('\\','/');assert sha(p)==i['sha256'];frozen[str(p)]=sha(p)
write(O/'inputs.json',frozen)
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def run(label,args,budget):
 start=time.time();timeout=False
 with (O/(label+'.stdout.log')).open('wb') as so,(O/(label+'.stderr.log')).open('wb') as se:
  try:q=subprocess.run(args,cwd=W,env=env,stdout=so,stderr=se,timeout=budget,creationflags=0x08000000|0x00004000);code=q.returncode
  except subprocess.TimeoutExpired:code=None;timeout=True
 same=all(sha(Path(p))==h for p,h in frozen.items());write(O/(label+'.receipt.json'),dict(args=args,returncode=code,timeout=timeout,seconds=time.time()-start,inputs_unchanged=same))
 print(label,code,flush=True);assert code==0 and not timeout and same,label
run('author',[sys.executable,'-I',str(W/'tools/water/overlap_stream_collision_v31.py'),str(old),str(out),'--expected-author-sha256',sha(old/'author-report.json'),'--contact-targets',str(targets),'--contact-only','--models',*names],120)
before={i['model']:i for i in read(old/'author-report.json')['instances']};after=read(out/'author-report.json')
rows=[]
for inst in after['instances']:
 name=inst['model'];a=old/'source'/name.replace('\\','/');b=out/'source'/name.replace('\\','/')
 ah,al,ab=load(a);bh,bl,bb=load(b)
 assert ah==bh and all(ab[k]==bb[k] for k in (0,2,3)) and before[name]['origin']==inst['origin']
 if name.split('\\')[-1] not in names:assert a.read_bytes()==b.read_bytes()
 def cost(g):return dict(components=len(g.selections),faces=len(g.faces),vertices=len(g.points),max_vertices_per_component=max(len(s.points) for s in g.selections.values()),max_faces_per_component=max(len(s.faces) for s in g.selections.values()))
 ca,cb=cost(al[1]),cost(bl[1]);assert ca['components']==cb['components'];assert cb['max_vertices_per_component']<=72 and cb['max_faces_per_component']<=140
 if name.split('\\')[-1] in names:
  import numpy as np
  xyz=(np.array([p.coords for p in bl[1].points])+inst['origin']).astype(np.float32)
  for target in read(targets)[name.split('\\')[-1]]:
   q=np.array([target['x'],target['z']],dtype=np.float32)
   assert not np.any(np.all(xyz[:,[0,2]]==q,axis=1)),('Target remains exact vertex',name,target)
 rows.append(dict(model=name,before=ca,after=cb))
write(O/'costs.json',dict(status='CAPS_PASS',models=rows,totals={s:{k:(max(r[s][k] for r in rows) if k.startswith('max_') else sum(r[s][k] for r in rows)) for k in rows[0][s]} for s in ['before','after']}))
run('overlay',[sys.executable,'-I',str(W/'tools/water/review_compact_collision_v31.py'),str(old),str(out),str(O/'contact.json')],900)
assert read(O/'contact.json')['status']=='SAVED_COLLISION_PASS'
run('compile',['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(W/'tools/water/pack_continuous_stream_pilot_v31.ps1'),'-Pilot',str(out)],900)
run('binary',[sys.executable,'-I',str(W/'tools/water/verify_compiled_stream_pilot_v31.py'),str(out),'--reader-root','C:/temp/moto_lanes/review_g3/tools'],900)
assert read(out/'binary-review.json')['status']=='BINARY_PASS'
assert read(out/'records.json')==read(old/'records.json'),'Compiled poses changed'
write(O/'receipt.json',dict(status='ISOLATED_OVERLAP_BINARY_PASS_PACKED_OVERLAY_PENDING',pbo_sha256=sha(out/'packed/baltic_stream_pilot.pbo'),changed_models=names,all_139_poses_exact=True,inputs_unchanged=True))
print('ISOLATED_OVERLAP_BINARY_PASS_PACKED_OVERLAY_PENDING')

