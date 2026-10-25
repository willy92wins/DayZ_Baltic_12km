from pathlib import Path
import hashlib,json,subprocess,sys,shutil
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;B=R/'river-131-midpoint-b';C=R/'river-131-midpoint-c';U=R/'collision-overlap-u2';O=R/'package-midpoint-c'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/playtest'),str(W/'tools/water')];from attach_navmesh import read_pbo;from review_compact_collision_v31 import load
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def cost(g):return dict(components=len(g.selections),faces=len(g.faces),vertices=len(g.points),max_vertices_per_component=max(len(s.points) for s in g.selections.values()),max_faces_per_component=max(len(s.faces) for s in g.selections.values()))
failed=read(R/'runtime-midpoint-b/full/result.json');grid=read(R/'runtime-midpoint-b/grid/result.json')
assert failed['status']=='FAIL' and failed['failure_count']==1 and failed['failures'][0]['id']==697
assert grid['status']=='FAIL' and grid['failure_count']==13 and {f['original_id'] for f in grid['failures']}=={392}
restored={'cs_131p0_0_0300.p3d','cs_131p0_0_0312.p3d'}
base=Path('P:/Mods/@DayZ_Baltic_EV112_RectangleF/Addons/baltic_stream_pilot.pbo');old=R/'package-midpoint-b/Addons/baltic_stream_pilot.pbo'
assert sha(base)=='c0be9abc9d36ee19c636325b825dbf09880a9dc31b5dfb8432e0f91d0e1cfa87' and sha(old)=='1e2c3f8e130691413b5a5d167fbfdf301792143ef2f21b37713ee96b4aa482f1'
_,props,original=read_pbo(base);_,pb,prior=read_pbo(old);assert props==pb
author=read(B/'author-report.json');u={i['model']:i for i in read(U/'author-report.json')['instances']};baseline={m['model']:m for m in author['collision_packing']['models']}
assert not C.exists() and not O.exists();(C/'source/baltic_stream_pilot').mkdir(parents=True);(C/'temp/baltic_stream_pilot').mkdir(parents=True)
expected=dict(prior);rows=[]
for index,inst in enumerate(author['instances']):
    key=inst['model'];name=key.split('\\')[-1];chosen=u[key] if name in restored else inst
    assert inst['origin']==u[key]['origin'];src=(U if name in restored else B)/'source'/key.replace('\\','/');assert sha(src)==chosen['sha256']
    dest=C/'source'/key.replace('\\','/');shutil.copyfile(src,dest)
    _,a,ab=load(dest);_,b,bb=load(U/'source'/key.replace('\\','/'));assert all(ab[i]==bb[i] for i in (0,2,3))
    after=cost(a[1]);before=cost(b[1]);assert all(after[k]<=before[k] for k in before)
    if name not in restored:assert all(after[k]<=baseline[name]['before'][k] for k in after)
    else:assert dest.read_bytes()==(U/'source'/key.replace('\\','/')).read_bytes();expected[name]=original[name]
    author['instances'][index]=chosen;rows.append(dict(model=name,before=before,after=after,restored_U2=name in restored,source_sha256=sha(dest)))
    (C/'temp/baltic_stream_pilot'/name).write_bytes(expected[name])
assert {n for n in original if original[n]!=expected[n]}=={r['model'] for r in rows if not r['restored_U2']}
totals={side:{k:(max(r[side][k] for r in rows) if k.startswith('max_') else sum(r[side][k] for r in rows)) for k in rows[0][side]} for side in ('before','after')}
assert totals['after']['components']<totals['before']['components']
author['collision_packing']=dict(status='CANDIDATE_GLOBAL_OVERLAY_PENDING',baseline='effective U2 for27; transformed25 also satisfy original compact-a caps',models=rows,totals=totals,restored_U2=sorted(restored),all_models_cost_nonincreasing=True,native_B_rejection_preserved=True)
(C/'author-report.json').write_text(json.dumps(author,indent=2)+'\n');(C/'packing-report.json').write_text(json.dumps(author['collision_packing'],indent=2)+'\n')
shutil.copyfile(B/'f-compiled-poses.json',C/'f-compiled-poses.json')
stage=O/'compiled/baltic_stream_pilot';dest=O/'Addons';stage.mkdir(parents=True);dest.mkdir()
for n,data in expected.items():p=stage/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
fb=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe');assert fb.is_file()
p=subprocess.run([str(fb),'-property','prefix='+props['prefix'],'-property','product=dayz ugc','-dst',str(dest),str(stage)],capture_output=True);(O/'filebank.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
packed=dest/'baltic_stream_pilot.pbo';_,newprops,actual=read_pbo(packed);assert actual==expected and newprops==props
report=dict(status='PASS_25_MODELS_REPLACED_37_U2_EXACT',pbo_sha256=sha(packed),author_sha256=sha(C/'author-report.json'),restored_models=sorted(restored),models=62,changed_models=25,unchanged_models=37,config_byte_exact=True,poses='26 B pose proofs plus restored U2 bytes retain all original F62 poses',cost=totals,sources={str(p):sha(p) for p in (base,old,B/'author-report.json',U/'author-report.json',B/'f-pose-binding.json',R/'runtime-midpoint-b/full/result.json',R/'runtime-midpoint-b/grid/result.json',Path(__file__))},limits=['Mixed package still requires whole packed contact and repeated frozen native tests.'])
(O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
