"""Fresh river131-only candidate; reference caps come from saved compact P3D."""
from pathlib import Path
import hashlib,io,json,struct,sys,time
import numpy as np
import scipy
if not __debug__:raise RuntimeError('Assertions required')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(__file__).parent
sys.path[:0]=[str(W/'tools/water'),'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
import py3d
import compact_stream_collision_v31 as packing
import midpoint_stream_collision_v31 as midpoint

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def lods(data):
    f=io.BytesIO(data);head=f.read(12);assert struct.unpack('<4sII',head)==(b'MLOD',257,4)
    objects=[];blobs=[]
    for _ in range(4):
        start=f.tell();objects.append(py3d.LOD(f));blobs.append(data[start:f.tell()])
    assert f.tell()==len(data);return head,objects,blobs
def cost(geo):
    assert geo.selections and all(n.startswith('Component') for n in geo.selections)
    selected=[id(f) for s in geo.selections.values() for f in s.faces]
    assert len(selected)==len(set(selected))==len(geo.faces)
    return dict(components=len(geo.selections),faces=len(geo.faces),vertices=len(geo.points),
        max_vertices_per_component=max(len(s.points) for s in geo.selections.values()),
        max_faces_per_component=max(len(s.faces) for s in geo.selections.values()))

old=R/'river-131-a';base=R/'river-131-compact-a';out=R/'river-131-midpoint-a'
assert sha(old/'author-report.json')=='3dbfcf567cbd549c20beda594eda3719b9d4944add2b244a9ffaf2f004317833'
assert sha(base/'author-report.json')=='5139587a85879cb30db476f1b21cc1d3c5adc917ab5f44a81657779cfd88b3c1'
out.mkdir(exist_ok=False);src=out/'source/baltic_stream_pilot';src.mkdir(parents=True);prov=out/'provenance';prov.mkdir()
author=read(old/'author-report.json');baseline={i['model']:i for i in read(base/'author-report.json')['instances']}
assert len(baseline)==len(author['instances'])==27
for path in (Path(__file__),Path(packing.__file__),Path(midpoint.__file__)):(prov/path.name).write_bytes(path.read_bytes())
for folder,name in ((old,'input-author-report.json'),(base,'baseline-author-report.json')):(prov/name).write_bytes((folder/'author-report.json').read_bytes())
for name in ('terrain.npz','envelope.npy','cover.npy','131.0-0-surfaces.npz'):(out/name).write_bytes((old/name).read_bytes())
for name in ('config.cpp','$PBOPREFIX$'):(src/name).write_bytes((old/'source/baltic_stream_pilot'/name).read_bytes())
rows=[]
for inst in author['instances']:
    began=time.monotonic();name=inst['model'].split('\\')[-1]
    source=old/'source'/inst['model'].replace('\\','/');prior=base/'source'/inst['model'].replace('\\','/')
    assert sha(source)==inst['sha256'] and sha(prior)==baseline[inst['model']]['sha256']
    assert inst['origin']==baseline[inst['model']]['origin']
    data=source.read_bytes();head,original,blobs=lods(data);bh,base_lods,base_blobs=lods(prior.read_bytes())
    assert bh==head and all(blobs[i]==base_blobs[i] for i in (0,2,3))
    before=cost(base_lods[1]);assert before['components']==baseline[inst['model']]['collision_components']
    visual=original[0];ids={v.point_index for face in visual.faces if 'water_streambed.rvmat' not in face.material for v in face.vertices};count=max(ids)+1
    assert ids==set(range(count)) and count%39==0
    grid=np.array([p.coords for p in visual.points[:count]]).reshape(-1,39,3)
    try:
        parts,search=midpoint.partition_midpoint(grid,vertical_budget=.03,horizontal_budget=.01,
            max_vertices_per_component=before['max_vertices_per_component'],max_faces_per_component=before['max_faces_per_component'],max_states=20000,timeout_s=60.)
    except midpoint.SearchLimit as exc:
        (out/'search-limit.json').write_text(json.dumps(dict(status='INCONCLUSIVE',model=name,error=str(exc),completed_models=rows),indent=2))
        raise
    geo=py3d.LOD();geo.resolution=1e13;geo.properties.update({'class':'house','damage':'no'});volumes=[];shifts=[]
    for index,part0 in enumerate(parts,1):
        part=dict(part0);part['points']=part0['points'].copy()
        shift=float(np.ceil(max(0.,part['roof_upper_error_bound_m'])/2*512)/512);part['points'][:,1]-=shift
        volumes.append(packing.add_component(py3d,geo,part,index));shifts.append(shift)
    single=py3d.P3D();single.lods.append(geo);temp=prov/(name+'.geometry-lod');single.save(str(temp));geometry=temp.read_bytes()[12:]
    candidate=head+blobs[0]+geometry+blobs[2]+blobs[3];dest=src/name;dest.write_bytes(candidate)
    nh,saved,nb=lods(dest.read_bytes());assert nh==head and all(nb[i]==blobs[i] for i in (0,2,3))
    after=cost(saved[1]);assert after['max_vertices_per_component']<=before['max_vertices_per_component'] and after['max_faces_per_component']<=before['max_faces_per_component']
    row=dict(model=name,original_sha256=sha(source),baseline_sha256=sha(prior),candidate_sha256=sha(dest),before=before,after=after,
        no_cost_regression=all(after[k]<=before[k] for k in before),non_geometry_lods_byte_exact=True,search=search,
        max_centering_shift_m=max(shifts),local_roof_bound_m=max(p['roof_upper_error_bound_m'] for p in parts),seconds=time.monotonic()-began)
    rows.append(row)
    inst.update(source_collision_components=inst['collision_components'],collision_components=len(parts),signed_collision_volume=float(sum(volumes)),sha256=sha(dest))
    print(json.dumps({k:v for k,v in row.items() if k!='search'}),flush=True)
totals={side:{key:(max(r[side][key] for r in rows) if key.startswith('max_') else sum(r[side][key] for r in rows)) for key in rows[0][side]} for side in ('before','after')}
cost_ok=all(r['no_cost_regression'] for r in rows) and totals['after']['components']<totals['before']['components']
report=dict(status='CANDIDATE_GLOBAL_OVERLAY_PENDING' if cost_ok else 'FAIL_COST_REGRESSION',input_author_sha256=sha(old/'author-report.json'),baseline_author_sha256=sha(base/'author-report.json'),
    raw_roof_budget_m=.03,horizontal_budget_m=.01,required_global_vertical_error_m=.02,totals=totals,all_models_cost_nonincreasing=cost_ok,models=rows,
    sources={str(p):sha(p) for p in (Path(__file__),Path(packing.__file__),Path(midpoint.__file__),Path(py3d.__file__))},
    versions=dict(numpy=np.__version__,scipy=scipy.__version__,qhull='Bundled with scipy; independent version not exposed here.'),
    limits=['Saved MLOD overlay, binary and engine acceptance still required.','Midpoint cuts only; no global optimization or FPS claim.','Original F deployed packages are unchanged.'])
author['collision_packing']=report
(out/'author-report.json').write_text(json.dumps(author,indent=2),encoding='utf-8');(out/'packing-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('models','sources')},indent=2))
raise SystemExit(0 if cost_ok else 1)
