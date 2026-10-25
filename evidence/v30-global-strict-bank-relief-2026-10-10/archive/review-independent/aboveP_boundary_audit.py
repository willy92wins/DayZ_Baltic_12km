from __future__ import annotations
import hashlib, json, math, pathlib, sys
import numpy as np
from shapely.geometry import Polygon

ROOT = pathlib.Path(r'E:\DayZ-Baltic-Build')
OUT = ROOT / 'v30-global-strict-bank-relief-20261010' / 'review-independent'
WORK = pathlib.Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
REPORT = OUT / 'coverage-contract-review.json'
RAW = OUT / 'ev87-review-p99-sector-corrected.json'
WRP = ROOT / 'v30-mixed-bank-incremental-fixed-20261010' / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
P = ROOT / 'v30-narva-dry-bank-relief-20261010/candidate/plane.npy'
B = ROOT / 'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
H = ROOT / 'v30-global-strict-bank-relief-20261010/candidate-terrain.npz'
MODELS = ROOT / 'v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30'
ODOL_READER = pathlib.Path(r'C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts')
PY3D = pathlib.Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\tools\navigation')
WRP_API = WORK / 'tools/terrain/wrp0wzd.py'
LEDGER = ROOT / 'v30-frozen-water-stitch-20261009/authoring-progress.jsonl'
OLD_MLOD_DIR = ROOT / 'v30-continuation-20261008/junction-fix-r2/water/source/baltic_water_v30'
NEW_MLOD_DIR = ROOT / 'v30-frozen-water-stitch-20261009/compile/source/baltic_water_v30'
IDS = {
 16799644: {'cell':[1359,300], 'face':[6,3,0], 'tri':0, 'area_report_B':0.0006941731643448185, 'area_report_H':0.0006941731643448185, 'max_excess_report':0.0249900309199094},
 16800008: {'cell':[1245,371], 'face':[9,7,4], 'tri':1, 'area_report_B':0.0005341462037399597, 'area_report_H':0.000572381854336714, 'max_excess_report':0.0249899735504387},
}
EXPECTED = {
 'coverage_report_sha256':'', # pinned at runtime from parent report
 'raw_geometry_report_sha256':'92aa30ca697547aedb9a515d8441bffebd58b32dae4b1bb179f9ba6adf6987c1',
 'wrp_sha256':'3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6',
 'physical_lod_float32':float(np.float32(3e15)),
 'physical_aboveP_epsilon_m':1e-5,
}

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def clip_ge(poly, coeff):
 # Sutherland-Hodgman affine half-plane clip: coeff dot [x,z,1] >= 0.
 ring=list(np.asarray(poly.exterior.coords[:-1],dtype=np.float64)); out=[]
 def val(p):return float(p[0]*coeff[0]+p[1]*coeff[1]+coeff[2])
 for i,a in enumerate(ring):
  b=ring[(i+1)%len(ring)]; va=val(a); vb=val(b); ina=va>=0; inb=vb>=0
  if ina:out.append(a)
  if ina!=inb:
   den=va-vb
   if abs(den)>1e-18:out.append(a+(b-a)*(va/den))
 if len(out)<3:return Polygon()
 g=Polygon(np.asarray(out))
 return g if g.is_valid else g.buffer(0)

def aff(xy,v):return np.linalg.solve(np.column_stack((xy[:,0],xy[:,1],np.ones(len(xy)))),np.asarray(v,dtype=float))

def read_p3d(path):
 sys.path.insert(0,str(PY3D)); from water_mesh import py3d
 with open(path,'rb') as f:return py3d.P3D(f)

def main():
 # Pin unmodified EV87 reports and inputs.
 report=json.loads(REPORT.read_text(encoding='utf-8')); raw=json.loads(RAW.read_text(encoding='utf-8'))
 rawsha=sha(RAW)
 assert rawsha==EXPECTED['raw_geometry_report_sha256'],rawsha
 receipt=json.loads((OUT/'coverage-contract-execution-receipt.json').read_text(encoding='utf-8'))
 reportsha=sha(REPORT)
 # Use the complementary report's own expected model input hashes.
 report_inputs=report['inputs']; raw_inputs=raw['inputs']
 assert sha(WRP)==EXPECTED['wrp_sha256']
 sys.path.insert(0,str(WORK/'tools/terrain')); import wrp0wzd
 wrp=wrp0wzd.read(WRP); assert len(wrp['objects'])==18033
 p=np.load(P,allow_pickle=False); hb=np.load(B,allow_pickle=False)['heights']; hh=np.load(H,allow_pickle=False)['heights']
 assert p.shape==(2047,2047) and hb.shape==hh.shape==(2048,2048)
 sys.path.insert(0,str(ODOL_READER)); from odol_reader import ODOL
 tris=((0,1,3),(0,2,3)); z0=12282.0; cell=6.0
 ledger={}
 for line in LEDGER.open(encoding='utf-8'):
  x=json.loads(line)
  if int(x.get('object_id',-1)) in IDS:ledger[int(x['object_id'])]=x
 cases=[]
 for ident,spec in IDS.items():
  obj=next(o for o in wrp['objects'] if int(o['id'])==ident)
  assert obj['name'].endswith(f'globalvis_{ident}.p3d')
  m=np.asarray(obj['matrix'],dtype=np.float64); assert np.array_equal(m[:9].reshape(3,3),np.eye(3))
  name=f'globalvis_{ident}.p3d'; odol_path=MODELS/name
  assert odol_path.is_file()
  modelsha=sha(odol_path)
  expected_model=raw_inputs.get(str(odol_path)) or report_inputs.get(str(odol_path))
  assert expected_model==modelsha,(name,modelsha,expected_model)
  model=ODOL.from_file(str(odol_path)); lods=[l for l in model.lods if float(l.resolution)==EXPECTED['physical_lod_float32']]
  assert len(lods)==1
  lod=lods[0]; fidx=next(i for i,f in enumerate(lod.faces) if list(f.vertex_indices)==spec['face'])
  inds=lod.faces[fidx].vertex_indices; verts=np.asarray([[lod.vertices[i].x+m[9],lod.vertices[i].y+m[10],lod.vertices[i].z+m[11]] for i in inds],dtype=float)
  r,c=spec['cell']; x0=c*cell; x1=x0+cell; z1=z0-r*cell; z0c=z1-cell
  corners=np.asarray([[x0,z1],[x1,z1],[x0,z0c],[x1,z0c]],dtype=float)
  tri=tris[spec['tri']]; ids=np.asarray(tri,dtype=int); native=Polygon(corners[ids]); facepoly=Polygon(verts[:,[0,2]])
  overlap=facepoly.intersection(native)
  assert overlap.area>0
  target=float(p[r,c]); h_cell={}
  for label,h in (('B',hb),('H',hh)):
   hv=np.asarray([h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]],dtype=float)[ids]
   ground_coeff=aff(corners[ids],hv)
   # Face is horizontal in these two physical triangles, but use affine fit from decoded ODOL xyz.
   surf_coeff=aff(verts[:,[0,2]],verts[:,1])
   actual=clip_ge(overlap,surf_coeff-ground_coeff)
   above=clip_ge(actual,surf_coeff-np.asarray([0.,0.,target+EXPECTED['physical_aboveP_epsilon_m']]))
   h_cell[label]={'ground_corner_heights_m':hv.tolist(),'exposed_area_m2':float(actual.area),'above_P_area_m2':float(above.area),'above_P_max_excess_m':float(max(0.0,float(np.max(np.asarray(above.exterior.coords[:-1])@surf_coeff[:2]+surf_coeff[2]-target-EXPECTED['physical_aboveP_epsilon_m']))) if not above.is_empty else 0.0)}
  # Neighbor comparison: boundary direction is chosen from z of the actual face.
  def finite_or_none(v): return float(v) if math.isfinite(float(v)) else None
  north=finite_or_none(p[r-1,c]) if r>0 else None; south=finite_or_none(p[r+1,c]) if r<2046 else None
  west=finite_or_none(p[r,c-1]) if c>0 else None; east=finite_or_none(p[r,c+1]) if c<2046 else None
  record=ledger[ident]
  old=OLD_MLOD_DIR/record['old_model']; new=NEW_MLOD_DIR/record['new_model']
  assert sha(old)==record['old_mlod_sha256']; assert sha(new)==record['new_sha256']
  oldp=read_p3d(old); newp=read_p3d(new)
  assert len(oldp.lods)==len(newp.lods)
  old_nonvisual=[i for i,l in enumerate(oldp.lods) if l.resolution>2e15]
  # Old and new non-visual LOD payloads are compared byte-for-byte after parser serialization.
  import io
  compare=[]
  for i in old_nonvisual:
   a=io.BytesIO();b=io.BytesIO();oldp.lods[i].write(a);newp.lods[i].write(b)
   compare.append({'lod_index':i,'resolution':oldp.lods[i].resolution,'bytes_equal':a.getvalue()==b.getvalue(),'serialized_sha256':hashlib.sha256(a.getvalue()).hexdigest()})
  assert all(x['bytes_equal'] for x in compare)
  cases.append({'object_id':ident,'cell':[r,c],'triangle':spec['tri'],'face_index_in_ODOL':fidx,'vertex_ids':inds,
   'physical_lod_resolution':lod.resolution,'odol_model_path':str(odol_path),'odol_sha256':modelsha,'wrp_matrix':m.tolist(),
   'world_vertices_xyz':verts.tolist(),'face_footprint_area_in_cell_triangle_m2':float(overlap.area),
   'cell_bounds_xz':[x0,z0c,x1,z1],'target_P_m':target,'neighbor_P_m':{'north':north,'south':south,'west':west,'east':east},
   'face_y_range_m':[float(verts[:,1].min()),float(verts[:,1].max())], 'surface_minus_target_P_m':float(np.mean(verts[:,1])-target),
   'expected_report_area_B_m2':spec['area_report_B'],'expected_report_area_H_m2':spec['area_report_H'],'expected_report_max_excess_m':spec['max_excess_report'],
   'recomputed_from_ODOL_and_B_H':h_cell,'source_record':{k:record[k] for k in ['old_model','old_mlod_sha256','new_model','new_sha256','origin','old_center','nonvisual_mlod_bytes_exact','max_all_geometry_delta_m','footprint_error_m2']},
   'nonvisual_LODs_exact_after_parser_serialization':compare})
 result={'status':'PASS_LOCAL_ABOVEP_MECHANISM_AUDIT','limitations':['Two targeted examples only; not a census of all aboveP records.','0WZD transforms are used as serialized source inputs, not DayZ runtime readback.','Nonvisual MLOD byte equality is independent source-to-generated-MLOD evidence; it does not prove how the engine rasterizes the seam.','Report-level physical growthoutside totals remain separate and are not attributed entirely to these examples.'],
  'inputs':{'coverage_report_sha256':reportsha,'raw_geometry_report_sha256':rawsha,'wrp_sha256':sha(WRP),'plane_sha256':sha(P),'B_candidate_sha256':sha(B),'H_candidate_sha256':sha(H),'authoring_ledger_sha256':sha(LEDGER),'compiled_ODOL_sha256':{str(x['object_id']):x['odol_sha256'] for x in cases}},'cases':cases,
  'global_raw_context':{'physical_outside_design_growth_B_m2':0.00344908019811354,'physical_outside_design_growth_H_m2':0.00355769761298657,'gate_limit_m2':0.002,'interpretation':'Both B and H fail the raw sum; these two cases establish a plausible inherited neighbor-plane boundary mechanism but do not account for the global excess.'}}
 dest=OUT/'aboveP-boundary-audit.json'; dest.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 print(json.dumps({'status':result['status'],'output':str(dest),'cases':[{k:v for k,v in c.items() if k in ['object_id','cell','triangle','face_index_in_ODOL','face_footprint_area_in_cell_triangle_m2','target_P_m','neighbor_P_m','surface_minus_target_P_m','recomputed_from_ODOL_and_B_H']} for c in cases]},indent=2))

if __name__=='__main__':main()
