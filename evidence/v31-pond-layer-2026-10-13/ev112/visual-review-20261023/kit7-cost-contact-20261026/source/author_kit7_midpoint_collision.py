"""Single kit7 candidate, original non-Geometry bytes and frozen native-C caps."""
from pathlib import Path
import hashlib,io,json,struct,sys,time
import numpy as np
import scipy
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
import py3d,compact_stream_collision_v31 as packing,midpoint_stream_collision_v31 as midpoint
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def lods(data):
 f=io.BytesIO(data);head=f.read(12);assert struct.unpack('<4sII',head)==(b'MLOD',257,4)
 objects=[];blobs=[]
 for _ in range(4):
  start=f.tell();objects.append(py3d.LOD(f));blobs.append(data[start:f.tell()])
 assert f.tell()==len(data);return head,objects,blobs
def cost(geo):
 selected=[id(f) for s in geo.selections.values() for f in s.faces]
 assert geo.selections and len(selected)==len(set(selected))==len(geo.faces)
 return dict(components=len(geo.selections),faces=len(geo.faces),vertices=len(geo.points),max_vertices_per_component=max(len(s.points) for s in geo.selections.values()),max_faces_per_component=max(len(s.faces) for s in geo.selections.values()))
def checked_grid(objects,expected_components):
 assert py3d.classify_lod_resolution(objects[0].resolution)=='visual'
 assert py3d.classify_lod_resolution(objects[1].resolution)=='geometry'
 visual=objects[0];faces=[face for face in visual.faces if 'water_streambed.rvmat' not in face.material]
 ids={v.point_index for face in faces for v in face.vertices};count=max(ids)+1
 assert ids==set(range(count)) and count%39==0
 grid=np.array([p.coords for p in visual.points[:count]]).reshape(-1,39,3)
 expected=packing.triangles(grid.shape[0],grid.shape[1])
 assert len(faces)==len(expected)==expected_components
 assert {tuple(sorted(v.point_index for v in f.vertices)) for f in faces}=={tuple(sorted(t)) for t in expected}
 return grid
old=R/'river-kit7-a-on-f-20261026';out=R/'river-kit7-midpoint-a-20261026'
baseline_path=R/'kit7-collision-baseline-20261026/result.json';baseline=json.loads(baseline_path.read_text())
assert baseline['status']=='SAVED_MODEL_BASELINES_MEASURED'
reference=baseline['references']['native_C_reference']['totals'];caps={k:reference[k] for k in ['max_vertices_per_component','max_faces_per_component']};assert caps==dict(max_vertices_per_component=72,max_faces_per_component=140)
original=baseline['references']['kit7_unpacked_candidate'];before_rows={r['model']:r for r in original['rows']}
assert sha(old/'author-report.json')==original['author_sha256']=='5bca325f35bfc1ddabfdc9368eb06ad5898ea8a2d3e4867f174e1e6aab5d152f'
review=json.loads((R/'kit7-midpoint-review/accepted.json').read_text());assert review['status']=='ACCEPTED_FOR_ONE_AUTHOR'
required={str(p) for p in [Path(__file__),Path(packing.__file__),Path(midpoint.__file__),Path(py3d.__file__),baseline_path,old/'author-report.json',W/'plans/ev112-kit7-collision-budget-20261026.md',W/'tools/water/review_compact_collision_v31.py']}
assert required<=set(review['inputs']), 'Incomplete reviewed input binding'
for path,digest in review['inputs'].items():assert sha(path)==digest,path
out.mkdir(exist_ok=False);src=out/'source/baltic_stream_pilot';src.mkdir(parents=True);prov=out/'provenance';prov.mkdir()
author=json.loads((old/'author-report.json').read_text());assert len(author['instances'])==len(before_rows)==139
for path in [Path(__file__),Path(packing.__file__),Path(midpoint.__file__),baseline_path]:(prov/path.name).write_bytes(path.read_bytes())
(prov/'input-author-report.json').write_bytes((old/'author-report.json').read_bytes())
preserved={}
for name in ['terrain.npz','envelope.npy','cover.npy','kit-7-surfaces.npz']:
 (out/name).write_bytes((old/name).read_bytes());preserved[name]=sha(old/name);assert sha(out/name)==preserved[name]
for name in ['config.cpp','$PBOPREFIX$']:(src/name).write_bytes((old/'source/baltic_stream_pilot'/name).read_bytes())
rows=[]
for inst in author['instances']:
 began=time.monotonic();name=inst['model'].split('\\')[-1];source=old/'source'/inst['model'].replace('\\','/')
 assert sha(source)==inst['sha256']==before_rows[name]['sha256'];data=source.read_bytes();head,objects,blobs=lods(data)
 before=cost(objects[1]);assert all(before[k]==before_rows[name][k] for k in before)
 grid=checked_grid(objects,before['components'])
 try:parts,search=midpoint.partition_midpoint(grid,vertical_budget=.03,horizontal_budget=.01,**caps,max_states=20000,timeout_s=60.)
 except midpoint.SearchLimit as exc:
  (out/'search-limit.json').write_text(json.dumps(dict(status='INCONCLUSIVE',model=name,error=str(exc),completed_models=rows),indent=2));raise
 geo=py3d.LOD();geo.resolution=objects[1].resolution;geo.properties.update(objects[1].properties);volumes=[];shifts=[]
 for index,part0 in enumerate(parts,1):
  part=dict(part0);part['points']=part0['points'].copy();shift=float(np.ceil(max(0.,part['roof_upper_error_bound_m'])/2*512)/512);part['points'][:,1]-=shift
  volumes.append(packing.add_component(py3d,geo,part,index));shifts.append(shift)
 single=py3d.P3D();single.lods.append(geo);temp=prov/(name+'.geometry-lod');single.save(str(temp))
 dest=src/name;dest.write_bytes(head+blobs[0]+temp.read_bytes()[12:]+blobs[2]+blobs[3]);nh,saved,nb=lods(dest.read_bytes());assert nh==head and all(nb[i]==blobs[i] for i in [0,2,3])
 after=cost(saved[1]);assert all(after[k]<=caps[k] for k in caps)
 row=dict(model=name,original_sha256=inst['sha256'],candidate_sha256=sha(dest),before=before,after=after,no_aggregate_cost_regression=all(after[k]<=before[k] for k in ['components','faces','vertices']),non_geometry_lods_byte_exact=True,origin_unchanged=inst['origin'],search=search,max_centering_shift_m=max(shifts),local_roof_bound_m=max(p['roof_upper_error_bound_m'] for p in parts),seconds=time.monotonic()-began)
 rows.append(row);inst.update(source_collision_components=inst['collision_components'],collision_components=len(parts),signed_collision_volume=float(sum(volumes)),sha256=sha(dest))
 print(json.dumps({k:v for k,v in row.items() if k not in ['search','origin_unchanged']}),flush=True)
totals={side:{key:(max(r[side][key] for r in rows) if key.startswith('max_') else sum(r[side][key] for r in rows)) for key in rows[0][side]} for side in ['before','after']}
passed=all(r['no_aggregate_cost_regression'] for r in rows) and totals['after']['components']<totals['before']['components']
report=dict(status='CANDIDATE_GLOBAL_OVERLAY_PENDING' if passed else 'FAIL_COST_REGRESSION',input_author_sha256=sha(old/'author-report.json'),baseline_sha256=sha(baseline_path),caps=caps,raw_roof_budget_m=.03,horizontal_budget_m=.01,required_global_vertical_error_m=.02,totals=totals,all_models_aggregate_cost_nonincreasing=all(r['no_aggregate_cost_regression'] for r in rows),strict_total_components_decrease=totals['after']['components']<totals['before']['components'],preserved_inputs=preserved,models=rows,sources={str(p):sha(p) for p in [Path(__file__),Path(packing.__file__),Path(midpoint.__file__),Path(py3d.__file__)]},versions=dict(numpy=np.__version__,scipy=scipy.__version__),limits=['Per-component complexity increases from triangular prisms but is capped by observed native-C maxima; not five-dimensional cost improvement.','Top-level original author metadata is inherited; collision_packing.sources identifies this adapter and its dependencies.','MLOD full overlay, compiled centres/global poses and native contact remain separate gates.','No deployed geometry, PBO or current navigation input is changed.'])
author['collision_packing']=report;(out/'author-report.json').write_text(json.dumps(author,indent=2));(out/'packing-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['models','sources']},indent=2));raise SystemExit(0 if passed else 1)
