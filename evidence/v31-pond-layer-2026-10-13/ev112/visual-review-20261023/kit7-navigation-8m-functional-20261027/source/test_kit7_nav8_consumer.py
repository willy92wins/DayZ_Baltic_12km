"""Synthetic consumer controls; explicitly NOT evidence of native navigation."""
from pathlib import Path
import copy,hashlib,json,subprocess,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=R/'kit7-nav8-consumer-20261027'
sys.path[:0]=[str(W/'tools/navigation'),str(W/'tools/water')]
from verify_kit7_nav_ev112 import verify,vector,tri_sample
from prepare_visual_probe_v31 import height
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
ref=read(D/'reference.json');geom=read(Path(ref['geometry']));H=np.load(ref['terrain'])['heights'];E=np.load(R/'guarded-relief-batch-e-merged/terrain-buried.npz')['heights']
meshes=np.load(R/'kit7-packed-nav-discovery-20261026/roadway.npz');allroof=np.concatenate([meshes[k] for k in meshes.files if k.endswith('_dry')]);queries={q['name']:q for q in ref['queries']}
old=(R/'patch-nav-c45/runtime.log').read_text(encoding='utf-8-sig').splitlines();assert old[-1]=='END;45'
fmt=lambda v:'<'+', '.join(f'{x:.8f}' for x in v)+'>'
rows=[ref['header']]
paths={}
for row in old[1:-1]:
    f=row.split(';')
    if f[0]=='P':
        nav,ground,road=map(vector,f[3:]);newg=float(tri_sample(H,nav[0],nav[2]));roof=height(allroof,np.array(nav)[[0,2]])
        if roof is not None or abs(newg-ground[1])>1e-9:
            newr=max(newg,roof if roof is not None else newg);nav[1]+=newr-road[1];road[1]=newr;ground[1]=newg
        paths.setdefault(f[1],[]).append([nav,ground,road])
for row in old[1:-1]:
    f=row.split(';')
    if f[0]!='Q':continue
    q=queries[f[1]];p=paths.get(f[1],[]);f[6]=fmt(q['start']);f[7]=fmt(q['end'])
    if f[1]=='changed_bank_13':f[8]=fmt(p[0][0]);f[9]=fmt(p[-1][0])
    rows.append(';'.join(f))
    rows.extend('P;'+f[1]+';'+str(i)+';'+';'.join(fmt(v) for v in triplet) for i,triplet in enumerate(p))
for q in ref['queries'][45:]:
    roof=np.concatenate([meshes[k.split('\\')[-1]+'_dry'] for k in q['allowed_models']]);points=[]
    for x,z in q['centerline']:
        ground=float(tri_sample(H,x,z));surface=height(roof,np.array([x,z]));road=max(ground,ground if surface is None else surface)
        points.append([[x,road+.02,z],[x,ground,z],[x,road,z]])
    rows.append(';'.join(['Q',q['name'],'true','true','true',str(len(points)),fmt(q['start']),fmt(q['end']),fmt(points[0][0]),fmt(points[-1][0])]))
    rows.extend('P;'+q['name']+';'+str(i)+';'+';'.join(fmt(v) for v in p) for i,p in enumerate(points))
rows.append('END;607');text='\n'.join(rows)+'\n';out=D/'synthetic-controls';out.mkdir(exist_ok=False)
(out/'positive-synthetic.log').write_text(text)
results=[]
def control(name,r,t,e=E,expected='REJECT'):
    try:
        v=verify(r,t,H,e,geom);status=v['status']
        if name=='positive':
            (out/'positive-result.json').write_text(json.dumps(v,indent=2)+'\n')
    except (ValueError,KeyError,IndexError,TypeError) as exc:status='REJECTED_EVIDENCE: '+str(exc)
    ok=status=='PASS_KIT7_NATIVE_GRAPH' if expected=='PASS' else status!='PASS_KIT7_NATIVE_GRAPH'
    results.append(dict(name=name,status=status,expected=expected,ok=ok));print(name,status,flush=True)
    assert ok,name
control('positive',ref,text,expected='PASS')
for kind in ('piece','seam','end','cap'):
    name=next(q['name'] for q in ref['queries'] if q['name'].startswith('kit7_'+kind+'_'))
    control('missing_'+kind,ref,'\n'.join(s for s in rows if not s.startswith(('Q;'+name+';','P;'+name+';')))+'\n')
control('truncated',ref,'\n'.join(rows[:-1])+'\n')
control('duplicate',ref,'\n'.join(rows[:-1]+[rows[1],rows[-1]])+'\n')
bad=copy.deepcopy(ref);bad['queries'][0]['start'][0]+=.5;control('regression_xz_mutated',bad,text)
bad=copy.deepcopy(ref);bad['f_local_query_names'][0]='wrong';control('wrong_f_set',bad,text)
control('no_f_delta',ref,text,H)
badrows=list(rows);ix=next(i for i,s in enumerate(rows) if s.startswith('Q;kit7_piece_000_left;'));f=badrows[ix].split(';');f[8]='<nan, 1, 1>';badrows[ix]=';'.join(f);control('nonfinite_sample',ref,'\n'.join(badrows)+'\n')
badrows=list(rows);ix=next(i for i,s in enumerate(rows) if s.startswith('P;kit7_piece_000_left;'));f=badrows[ix].split(';');p=vector(f[3]);p[1]-=2;f[3]=fmt(p);badrows[ix]=';'.join(f);control('below_roadway',ref,'\n'.join(badrows)+'\n')
badrows=list(rows);name='kit7_piece_000_left';inds=[i for i,s in enumerate(rows) if s.startswith('P;'+name+';')];badrows=[s for i,s in enumerate(rows) if i not in inds[1:]];qi=next(i for i,s in enumerate(badrows) if s.startswith('Q;'+name+';'));f=badrows[qi].split(';');f[5]='1';badrows[qi]=';'.join(f);control('partial_path',ref,'\n'.join(badrows)+'\n')
bad=copy.deepcopy(ref);bad['max_waypoint_surface_error_m']=.802;control('relaxed_tolerance',bad,text)
bad=copy.deepcopy(ref);bad['queries'][45]['centerline'][0][0]+=.5;control('changed_centerline',bad,text)
from shapely.geometry import mapping,box
bad=copy.deepcopy(ref);bad['corridors'][0]['exterior']=mapping(box(0,0,10,10));control('fake_exterior',bad,text)
bad=copy.deepcopy(ref);bad['corridors'][0]['corridor']=mapping(box(0,0,10,10));control('fake_corridor',bad,text)
for mode in ('reference','terrain'):
    target=out/('cli-bad-'+mode+'.json')
    args=[sys.executable,'-I',str(W/'tools/navigation/verify_kit7_nav_ev112.py'),'--reference',str(D/'reference.json'),'--reference-sha256','0'*64 if mode=='reference' else hashlib.sha256((D/'reference.json').read_bytes()).hexdigest(),'--log',str(out/'positive-synthetic.log'),'--terrain-e',str(Path(ref['terrain']) if mode=='terrain' else R/'guarded-relief-batch-e-merged/terrain-buried.npz'),'--out',str(target)]
    p=subprocess.run(args,capture_output=True);v=read(target);assert p.returncode==1 and v['status']=='FAIL_KIT7_PROBE_EVIDENCE'
    results.append(dict(name='wrong_'+mode+'_sha',status=v['status'],reason=v['reason'],ok=True))
report=dict(status='SYNTHETIC_CONSUMER_CONTROLS_PASS',controls=results,native_acceptance=False,limits=['Synthetic positive retargets old C45 heights and adds ideal geometric polylines; never consume as runtime evidence.'],sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),W/'tools/navigation/verify_kit7_nav_ev112.py',D/'reference.json',R/'patch-nav-c45/runtime.log']})
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
