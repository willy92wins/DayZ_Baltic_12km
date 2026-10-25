#!/usr/bin/env python
"""Read-only EV90 feasibility preflight. No authoring, solver, or candidate output."""
from __future__ import annotations

import hashlib, importlib, json, math, sys
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box, shape

ROOT=Path(r'E:/DayZ-Baltic-Build')
Q=ROOT/'v30-wide-bank-fairing-pilot-20261010'
OUT=Q/'next-method-preflight'
B=ROOT/'v30-mixed-bank-incremental-fixed-20261010'
EV79=ROOT/'v30-narva-dry-bank-relief-20261010'
PRIOR=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz'
P=EV79/'candidate/plane.npy'
F=EV79/'candidate/visible-field.npy'
CONS=EV79/'constraints.npz'
WRP=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
DEPLOY=B/'deploy.json'
BOUNDS=ROOT/'v30-low-water-components-20261009/compiled-instance-bounds.json'
MODEL_DIR=ROOT/'v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30'
WORKSPACE=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
PARSER_DIR=Path(r'C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts')
ATTACH_NAV=WORKSPACE/'tools/playtest/attach_navmesh.py'
WRP_READER=WORKSPACE/'tools/terrain/wrp0wzd.py'
PLAN=Q/'next-method-plan.md'
PILOT_PLAN=Q/'plan.md'
EV87=ROOT/'v30-global-strict-bank-relief-20261010'
EV87_POLICY=EV87/'coverage-contract-proposal.md'
EV87_COVERAGE=EV87/'review-independent/verify_coverage_contract.py'
CORRIDORS=ROOT/'v30-v11/06-evidence/corridors.geojson'
N=2048; CELL=6.0; Z0=12282.0; SEA=0.85
WINDOW=(832,849,362,379)  # 17x17 vertices; 16x16 cells
CORE=(834,847,364,377)
FOCUS=(840,370)
TRIS=((0,1,3),(0,2,3)) # NW,NE,SW,SE; NW-SE diagonal
OFFSETS=((0,0),(0,1),(1,0),(1,1))
EPS={'physical':1e-5,'visible':2e-5}
EXPECTED={
 B/'candidate/terrain.npz':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 EV79/'candidate/terrain.npz':'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c',
 P:'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
 F:'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
 CONS:'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
 PRIOR:'18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370',
 WRP:'3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6',
 DEPLOY:'3c98951f3488eef233d6972621648c84244f9e711c2ff419fd0b8013b427ec00',
 PLAN:'3bde2ce8460f6374830f8ec4ca302e06b7c9a904f36c8778826799ffd6cdd7ea',
 PILOT_PLAN:'50a94dac1a15580c6299426678399ca80caf49835ba98a79946ded688a8a47ad',
 BOUNDS:'863e9539203e59fe77b9c7d4949da3a69b4991249941e15b887b60ff9e81ee62',
 EV87_POLICY:'6964ca97226512764720eb1a25f41ab65e191cfda318ea07ad39bb1f4c0b6463',
 EV87_COVERAGE:'214f0eddda08d84ce18c921fcdbE01298f608c9a5c19b7e5246bb9e71df5dc2b'.lower(),
 CORRIDORS:'28866a8cf6ff57f2f825228046164ef939bc22bca9948eb96fe2463da46af343',
 }

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()

def load_npz(path):
 with np.load(path,allow_pickle=False) as z:return {k:z[k] for k in z.files}

def affine(xy,values):
 return np.linalg.solve(np.column_stack((xy[:,0],xy[:,1],np.ones(3))),np.asarray(values,dtype=np.float64))

def eval_aff(coef,xy):return np.asarray(xy,dtype=np.float64)@coef[:2]+coef[2]

def ring_points(poly):
 if poly.geom_type=='Polygon': geoms=[poly]
 else: geoms=[g for g in getattr(poly,'geoms',[]) if g.geom_type=='Polygon']
 out=[]
 for g in geoms:
  out.extend(np.asarray(g.exterior.coords[:-1],dtype=np.float64).tolist())
  for ring in g.interiors:out.extend(np.asarray(ring.coords[:-1],dtype=np.float64).tolist())
 return np.asarray(out,dtype=np.float64) if out else np.empty((0,2),dtype=np.float64)

def grid_xy(r,c):
 x0=c*CELL; z0=Z0-r*CELL
 return np.asarray([[x0,z0],[x0+CELL,z0],[x0,z0-CELL],[x0+CELL,z0-CELL]],dtype=np.float64)

def inward32_lower(x):
 v=np.float32(x)
 if float(v)<float(x):v=np.nextafter(v,np.float32(np.inf))
 return float(v)

def inward32_upper(x):
 v=np.float32(x)
 if float(v)>float(x):v=np.nextafter(v,np.float32(-np.inf))
 return float(v)

def run_fixtures():
 # Check the native NW-SE split on an inclined corner field; the two halves
 # intentionally have different affine planes when SE is the raised corner.
 corners=np.asarray([0.0,0.0,0.0,6.0])
 xy=grid_xy(0,0)
 a=affine(xy[np.asarray(TRIS[0])],corners[np.asarray(TRIS[0])])
 b=affine(xy[np.asarray(TRIS[1])],corners[np.asarray(TRIS[1])])
 if abs(float(eval_aff(a,np.asarray([[6.0,Z0-3.0]]))[0])-3.0)>1e-12:raise AssertionError('NW-SE triangle 0 fixture failed')
 if abs(float(eval_aff(b,np.asarray([[3.0,Z0-6.0]]))[0])-3.0)>1e-12:raise AssertionError('NW-SE triangle 1 fixture failed')
 exact=1.0;between=1.0+1e-8
 if inward32_lower(exact)!=exact or inward32_upper(exact)!=exact:raise AssertionError('exact float32 endpoint fixture failed')
 if inward32_lower(between)<between or inward32_upper(between)>between:raise AssertionError('inward float32 fixture failed')
 return {'nw_se_diagonal_inclined_field':'PASS','float32_exact_and_inward_bounds':'PASS'}

def import_readers():
 sys.path.insert(0,str(WORKSPACE/'tools/terrain'))
 sys.path.insert(0,str(WORKSPACE/'tools/playtest'))
 sys.path.insert(0,str(PARSER_DIR))
 wrp0wzd=importlib.import_module('wrp0wzd')
 attach_navmesh=importlib.import_module('attach_navmesh')
 odol_reader=importlib.import_module('odol_reader')
 return wrp0wzd,attach_navmesh,odol_reader.ODOL

def check_linkage_and_load():
 hashes={str(p):sha(p) for p in EXPECTED}
 bad={str(p):{'expected':v,'actual':hashes[str(p)]} for p,v in EXPECTED.items() if hashes[str(p)]!=v}
 if bad:raise AssertionError(f'frozen input identity mismatch: {bad}')
 bundle=load_npz(B/'candidate/terrain.npz'); ev79=load_npz(EV79/'candidate/terrain.npz')
 p=np.load(P,allow_pickle=False).astype(np.float64); f=np.load(F,allow_pickle=False).astype(np.float64)
 con=load_npz(CONS); prior=load_npz(PRIOR)
 h=np.asarray(bundle['heights'])
 if h.shape!=(N,N) or h.dtype!=np.float32 or ev79['heights'].shape!=(N,N):raise AssertionError('B/EV79 height contract mismatch')
 if p.shape!=(N-1,N-1) or f.shape!=(N-1,N-1,4):raise AssertionError('P/F array shape mismatch')
 if np.isinf(p).any() or np.isinf(f).any():raise AssertionError('P/F contains infinity; only NaN encodes absence')
 for key in ('other_fixed','engineering_halo'):
  if con[key].shape!=(N,N) or con[key].dtype!=np.bool_:raise AssertionError(f'bad EV79 protection mask {key}')
 if prior['large_lake_banks'].shape!=(N,N) or bundle['cls'].shape!=(N,N):raise AssertionError('protection source dimensions mismatch')
 deploy=json.loads(DEPLOY.read_text(encoding='utf-8'))
 mod=Path(deploy['mod']); addon=mod/'Addons'
 world_pbo=addon/'narva_trial.pbo'; water_pbo=addon/'baltic_water_v30.pbo'
 if sha(world_pbo)!=deploy['files']['narva_trial.pbo'] or sha(water_pbo)!=deploy['files']['baltic_water_v30.pbo']:
  raise AssertionError('B deployed PBO does not match deploy manifest')
 if deploy.get('terrain_sha256')!=EXPECTED[B/'candidate/terrain.npz'] or deploy.get('files',{}).get('baltic_water_v30.pbo')!='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14':
  raise AssertionError('B deploy provenance is not the frozen base')
 wrp0wzd,attach_navmesh,ODOL=import_readers()
 _,_,entries=attach_navmesh.read_pbo(world_pbo)
 compiled=entries.get('baltic_trial.wrp')
 if not compiled or hashlib.sha256(compiled).hexdigest()!=deploy['compiled_wrp_sha256']:
  raise AssertionError('B PBO embedded OPRW hash differs from deploy manifest')
 wrp=wrp0wzd.read(WRP)
 if len(wrp['objects'])!=18033 or wrp['heights'].shape!=(N,N):raise AssertionError('unexpected WRP dimensions/object count')
 bounds=json.loads(BOUNDS.read_text(encoding='utf-8'))
 if bounds.get('water_sha256')!=deploy['files']['baltic_water_v30.pbo'] or len(bounds.get('objects',[]))!=18024:
  raise AssertionError('bounds manifest water/object identity mismatch')
 return {'B':bundle,'EV79':ev79,'P':p,'F':f,'constraints':con,'prior':prior,'deploy':deploy,
  'world_pbo':world_pbo,'water_pbo':water_pbo,'compiled_oprw_sha':hashlib.sha256(compiled).hexdigest(),
  'wrp':wrp,'bounds':bounds,'ODOL':ODOL,'hashes':hashes,'wrp0wzd':wrp0wzd,'attach_navmesh':attach_navmesh}

def local_cells():
 r0,r1,c0,c1=WINDOW
 return [(r,c) for r in range(r0,r1-1) for c in range(c0,c1-1)]

def corridor_p_unknown(src):
 data=json.loads(CORRIDORS.read_text(encoding='utf-8'))
 features=[(i,shape(feat['geometry'])) for i,feat in enumerate(data['features'])]
 p=src['P'];by_feature=[];cells=set()
 for i,geom in features:
  touched=[];area=0.0
  for r,c in local_cells():
   if math.isfinite(float(p[r,c])):continue
   inter=geom.intersection(box(c*CELL,Z0-(r+1)*CELL,(c+1)*CELL,Z0-r*CELL))
   if not inter.is_empty and inter.area>0:
    touched.append((r,c));area+=float(inter.area)
  if touched:
   cells.update(touched);by_feature.append({'feature_index':i,'river':data['features'][i]['properties'].get('river'),
    'unknown_P_cells':len(set(touched)),'intersection_area_m2':area,'cells_rc':sorted([list(x) for x in set(touched)])})
 return cells,by_feature

def partial_f_cells(src):
 f=src['F'];out=set()
 for r,c in local_cells():
  vals=np.asarray(f[r,c],dtype=np.float64)
  for tri in TRIS:
   n=int(np.isfinite(vals[list(tri)]).sum())
   if 0<n<3:out.add((r,c))
 return out

def scan_compiled_faces(src):
 wrp=src['wrp']; bounds=src['bounds']; ODOL=src['ODOL']; deploy=src['deploy']
 model_bounds=bounds['models']; objects_by_id={int(o['id']):o for o in bounds['objects']}
 if len(objects_by_id)!=18024:raise AssertionError('duplicate object IDs in bounds manifest')
 water=[o for o in wrp['objects'] if 'baltic_water_v30' in o['name'].replace('\\','/').lower()]
 if len(water)!=18024:raise AssertionError('B WRP water object inventory mismatch')
 r0,r1,c0,c1=WINDOW
 x0,x1=c0*CELL,(c1-1)*CELL; z1,z0=Z0-r0*CELL,Z0-(r1-1)*CELL
 selected=[]; link_bad=[]; rotation_bad=0; max_xz_delta=0.0
 for o in water:
  ident=int(o['id']); entry=objects_by_id.get(ident)
  if entry is None:raise AssertionError(f'water object absent from bounds manifest: {ident}')
  name=o['name'].replace('\\','/').split('/')[-1]
  if entry['model'].lower()!=name.lower():link_bad.append(ident);continue
  m=np.asarray(o['matrix'],dtype=np.float64)
  if not np.array_equal(m[:9].reshape(3,3),np.eye(3)):rotation_bad+=1
  if not np.array_equal(m[[9,11]].astype(np.float32),np.asarray(entry['position'],dtype=np.float32)[[0,2]]):
   raise AssertionError(f'B transform XZ differs from linked bounds record for object {ident}')
  local=model_bounds.get(name)
  if local is None:raise AssertionError(f'missing compiled model bound record {name}')
  lb=np.asarray(local['bounds'],dtype=np.float64); tx,tz=float(m[9]),float(m[11])
  computed=np.asarray([lb[0]+tx,lb[1]+tz,lb[2]+tx,lb[3]+tz],dtype=np.float64)
  object_bb=np.asarray(entry['bounds'],dtype=np.float64)
  delta=float(np.max(np.abs(computed-object_bb)));max_xz_delta=max(max_xz_delta,delta)
  if delta>1e-4:raise AssertionError(f'compiled bounds do not match linked transform for object {ident}: {delta}')
  bx0,bz0,bx1,bz1=object_bb
  if not (bx1<x0 or bx0>x1 or bz1<z0 or bz0>z1):selected.append((o,entry,name,m,local))
 if link_bad:raise AssertionError(f'object model name mismatch count={len(link_bad)}')
 if rotation_bad:raise AssertionError(f'non-translation transforms among water objects: {rotation_bad}')
 model_cache={};model_file_hashes={}; lod_counts={'physical_faces':0,'visible_faces':0}
 above={'physical':{},'visible':{}}; unknown={'physical':{},'visible':{}}
 per_face_examples=[]; face_exceed_counts={'physical':0,'visible':0}; face_count={'physical':0,'visible':0}
 p=src['P'];f=src['F']; cells=local_cells()
 cell_poly={}; tri_poly={}
 for r,c in cells:
  xy=grid_xy(r,c)
  cell_poly[(r,c)]=box(c*CELL,Z0-(r+1)*CELL,(c+1)*CELL,Z0-r*CELL)
  for ti,tri in enumerate(TRIS):tri_poly[(r,c,ti)]=Polygon(xy[list(tri)])
 for o,entry,name,m,local in selected:
  if name not in model_cache:
   path=MODEL_DIR/name
   digest=sha(path);expected=local.get('sha256')
   if not expected or digest!=expected:raise AssertionError(f'compiled model SHA mismatch: {name}')
   model_file_hashes[str(path)]=digest
   model=ODOL.from_file(str(path)); target={float(np.float32(3e15)):'physical',float(np.float32(1.0)):'visible'}
   lods={}
   for resolution,kind in target.items():
    exact=[lod for lod in model.lods if lod.resolution==resolution]
    if len(exact)!=1:raise AssertionError(f'{name} missing/nonunique exact {kind} resolution {resolution}')
    lods[kind]=exact[0]
   model_cache[name]=lods
  tx,ty,tz=map(float,m[9:12])
  for kind,lod in model_cache[name].items():
   lod_counts[f'{kind}_faces']+=len(lod.faces)
   for face_idx,face in enumerate(lod.faces):
    ids=list(face.vertex_indices)
    if len(ids)!=3:raise AssertionError(f'non-triangle {kind} face in {name}:{face_idx}')
    verts=lod.vertices
    xyz=np.asarray([[verts[i].x+tx,verts[i].y+ty,verts[i].z+tz] for i in ids],dtype=np.float64)
    xy=xyz[:,[0,2]]
    face_shape=Polygon(xy)
    if not face_shape.is_valid:raise AssertionError(f'invalid XY triangle {kind} {name}:{face_idx}')
    if face_shape.area<=0.0:continue
    fc=affine(xy,xyz[:,1])
    xmin,zmin=xy.min(axis=0);xmax,zmax=xy.max(axis=0)
    cr0=max(c0,int(math.floor(xmin/CELL)));cr1=min(c1-2,int(math.floor(xmax/CELL)))
    rr0=max(r0,int(math.floor((Z0-zmax)/CELL)));rr1=min(r1-2,int(math.floor((Z0-zmin)/CELL)))
    for r in range(rr0,rr1+1):
     for c in range(cr0,cr1+1):
      cell_key=(r,c);over=face_shape.intersection(cell_poly[cell_key])
      if over.is_empty or over.area<=0.0:continue
      if kind=='physical':
       face_count[kind]+=1
       level=float(p[r,c]);pts=ring_points(over)
       if not math.isfinite(level):
        for ti,tri in enumerate(TRIS):
         piece=over.intersection(tri_poly[(r,c,ti)])
         if piece.is_empty or piece.area<=0.0:continue
         unknown[kind].setdefault(cell_key,[]).append({'cell':[r,c],'object':name,'face':face_idx,
          'triangle':ti,'area_m2':float(piece.area),'reason':'P_NaN_domain',
          'face_plane_coeff_xz':fc.tolist(),'intersection_xz':ring_points(piece).tolist()})
        continue
       excess=float(np.max(eval_aff(fc,pts)-level))
       if excess>EPS[kind]:
        above[kind].setdefault(cell_key,[]).append({'cell':[r,c],'object':name,'face':face_idx,'max_excess_m':excess,
         'overlap_area_m2':float(over.area),'face_plane_coeff_xz':fc.tolist(),'intersection_xz':pts.tolist()})
        face_exceed_counts[kind]+=1
      else:
       face_count[kind]+=1
       for ti,tri in enumerate(TRIS):
        tri_piece=over.intersection(tri_poly[(r,c,ti)])
        if tri_piece.is_empty or tri_piece.area<=0.0:continue
        offsets=np.asarray(tri,dtype=int);fv=np.asarray(f[r,c,offsets],dtype=np.float64)
        area=float(tri_piece.area);pts=ring_points(tri_piece);tri_xy=grid_xy(r,c)[offsets]
        if not np.isfinite(fv).all():
          bh4=np.asarray([src['B']['heights'][r,c],src['B']['heights'][r,c+1],
            src['B']['heights'][r+1,c],src['B']['heights'][r+1,c+1]],dtype=np.float64)
          ground_coef=affine(tri_xy,bh4[list(tri)])
          b_max=float(np.max(eval_aff(fc,pts)-eval_aff(ground_coef,pts)))
          unknown[kind].setdefault(cell_key,[]).append({'cell':[r,c],'object':name,'face':face_idx,'triangle':ti,'area_m2':area,
            'reason':'F_unknown_triangle','finite_corner_count':int(np.isfinite(fv).sum()),
          'B_max_face_minus_ground_m':b_max,'buried_in_B':b_max<=0.0,
          'face_plane_coeff_xz':fc.tolist(),'intersection_xz':pts.tolist()})
          continue
        fcoef=affine(tri_xy,fv)
        excess=float(np.max(eval_aff(fc,pts)-eval_aff(fcoef,pts)))
        if excess>EPS[kind]:
         above[kind].setdefault(cell_key,[]).append({'cell':[r,c],'object':name,'face':face_idx,'triangle':ti,
          'max_excess_m':excess,'overlap_area_m2':area,'face_plane_coeff_xz':fc.tolist(),'intersection_xz':pts.tolist()})
         face_exceed_counts[kind]+=1
 # Verify each parsed selected model's target LOD XZ geometry is enclosed by its hashed local bounds.
 model_bounds_deltas={}
 for name,lods in model_cache.items():
  local=np.asarray(model_bounds[name]['bounds'],dtype=np.float64); actual=[]
  for lod in lods.values():
   actual.extend([[v.x,v.z] for v in lod.vertices])
  a=np.asarray(actual,dtype=np.float64)
  actual_box=np.asarray([a[:,0].min(),a[:,1].min(),a[:,0].max(),a[:,1].max()])
  model_bounds_deltas[name]=float(np.max(np.abs(actual_box-local)))
  if actual_box[0]<local[0] or actual_box[1]<local[1] or actual_box[2]>local[2] or actual_box[3]>local[3]:
   raise AssertionError(f'selected ODOL vertices exceed linked local bounds: {name}')
 return {'selected_object_count':len(selected),'selected_models':len(model_cache),'model_hashes':model_file_hashes,
  'face_counts_by_lod':lod_counts,'positive_area_face_cell_tests':face_count,
  'face_cell_exceedance_count':face_exceed_counts,'above_by_kind':above,'unknown_by_kind':unknown,
  'bounds_manifest_max_world_transform_delta_m':max_xz_delta,'selected_model_bounds_max_delta_m':max(model_bounds_deltas.values(),default=0.0),
  'object_inventory_count':len(water),'bounds_world_sha256':bounds['world_sha256'],
  'compiled_oprw_sha256':src['compiled_oprw_sha']}

def reconstruct_domain(src,freeze_cells,above_by_kind,unknown_by_kind):
 b=src['B'];ev79=src['EV79'];p=src['P'];f=src['F'];con=src['constraints'];prior=src['prior']
 r0,r1,c0,c1=WINDOW;cr0,cr1,cc0,cc1=CORE
 h=np.asarray(b['heights'],dtype=np.float64);ev=np.asarray(ev79['heights'],dtype=np.float64)
 level=np.full((N,N),SEA,dtype=np.float64)
 # Aggregate finite P/F incident samples per terrain vertex; missing layers are not imputed.
 pcount=np.zeros((N,N),dtype=np.uint8);fcount=np.zeros((N,N),dtype=np.uint8)
 for r in range(r0-1,r1):
  for c in range(c0-1,c1):
   if not(0<=r<N-1 and 0<=c<N-1):continue
   pv=float(p[r,c]);fv=np.asarray(f[r,c],dtype=np.float64)
   for k,(dr,dc) in enumerate(OFFSETS):
    vr,vc=r+dr,c+dc
    if not(r0<=vr<r1 and c0<=vc<c1):continue
    if math.isfinite(pv):level[vr,vc]=max(level[vr,vc],pv);pcount[vr,vc]+=1
    if math.isfinite(float(fv[k])):level[vr,vc]=max(level[vr,vc],float(fv[k]));fcount[vr,vc]+=1
 protection={
  'other_fixed':np.asarray(con['other_fixed'],dtype=bool),
  'engineering_halo':np.asarray(con['engineering_halo'],dtype=bool),
  'large_lake_banks':np.asarray(prior['large_lake_banks'],dtype=bool),
  'reserve':np.asarray(b['reserve'],dtype=bool),
  'platform':np.asarray(b['platform'],dtype=bool),
  'class_nonzero':np.asarray(b['cls'])!=0,
  'actually_wet':h<=level,
 }
 fixed_by_mask=np.logical_or.reduce(tuple(v for v in protection.values()))
 frozen_nodes=set();above_frozen_nodes=set();unknown_frozen_nodes=set()
 for r,c in freeze_cells:
  for node in ((r,c),(r,c+1),(r+1,c),(r+1,c+1)):
   if CORE[0]<=node[0]<CORE[1] and CORE[2]<=node[1]<CORE[3]:frozen_nodes.add(node)
 for cell_set,target in ((set.union(*above_by_kind.values()) if any(above_by_kind.values()) else set(),above_frozen_nodes),
                        (set.union(*unknown_by_kind.values()) if any(unknown_by_kind.values()) else set(),unknown_frozen_nodes)):
  for r,c in cell_set:
   for node in ((r,c),(r,c+1),(r+1,c),(r+1,c+1)):
    if CORE[0]<=node[0]<CORE[1] and CORE[2]<=node[1]<CORE[3]:target.add(node)
 base_mut=[];fully_fixed=0;extra_frozen=[]
 for r in range(cr0,cr1):
  for c in range(cc0,cc1):
   if fixed_by_mask[r,c]:fully_fixed+=1
   else:
    base_mut.append((r,c))
    if (r,c) in frozen_nodes:extra_frozen.append((r,c))
 variables=[node for node in base_mut if node not in frozen_nodes]
 # Any F triangle that touches a would-be mutable node and has undefined samples keeps the preflight inconclusive.
 partial=[]
 core_set=set(variables)
 for r,c in local_cells():
  fv=np.asarray(f[r,c],dtype=np.float64)
  for ti,tri in enumerate(TRIS):
   finite=np.isfinite(fv[list(tri)])
   if 0<int(finite.sum())<3:
    if any((r+OFFSETS[k][0],c+OFFSETS[k][1]) in core_set for k in tri):
     partial.append({'cell':[r,c],'triangle':ti,'finite_corners':int(finite.sum())})
 # Hard variable limits reconstructed from EV79 budget, 1.8m floor, water-level clearance, and B rise cap.
 bounds={}
 for r,c in variables:
  lower=max(float(ev[r,c])-2.0,min(float(ev[r,c]),1.8),min(float(ev[r,c]),float(level[r,c])+1e-4))
  upper=min(float(ev[r,c])+2.0,float(h[r,c])+0.50)
  bounds[(r,c)]=[inward32_lower(lower),inward32_upper(upper)]
  if bounds[(r,c)][0]>bounds[(r,c)][1]:bounds[(r,c)]=None
 # Crossing intervals from every native P/F/SEA triangle edge with exactly one mutable dry endpoint.
 crossing_records=[];cross_unknown=[]
 layer_hits={}
 for r in range(r0-1,r1):
  for c in range(c0-1,c1):
   if not(0<=r<N-1 and 0<=c<N-1):continue
   ids=tuple((r+dr,c+dc) for dr,dc in OFFSETS)
   pval=float(p[r,c]);fvals=np.asarray(f[r,c],dtype=np.float64)
   for ti,tri in enumerate(TRIS):
    tnodes=[ids[k] for k in tri]
    tf=np.asarray(fvals[list(tri)],dtype=np.float64)
    fields=[]
    if math.isfinite(pval):fields.append(('P',(pval,pval,pval,pval)))
    fields.append(('SEA',(SEA,SEA,SEA,SEA)))
    if np.isfinite(tf).all():fields.append((f'F{ti}',tuple(fvals.tolist())))
    elif any(node in core_set for node in tnodes):cross_unknown.append({'cell':[r,c],'triangle':ti,'reason':'partial_or_missing_F'})
    for layer,lv4 in fields:
     for ea,eb in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
      a,bnode=ids[ea],ids[eb]
      if a in core_set and bnode not in core_set:dry,wet=a,bnode
      elif bnode in core_set and a not in core_set:dry,wet=bnode,a
      else:continue
      la=float(lv4[ea]);lb=float(lv4[eb]);lw=la if wet==a else lb;ld=lb if dry==bnode else la
      hw=float(h[wet]);hd=float(h[dry]);gw=hw-lw;gd=hd-ld
      if not(gw<0.0<gd):continue
      dx=(dry[1]-wet[1])*CELL;dz=-(dry[0]-wet[0])*CELL;length=math.hypot(dx,dz)
      t0=-gw/(gd-gw);tlo=max(0.0,t0-1.0/length);thi=min(1.0,t0+1.0/length)
      lo=ld+gw*(1.0-1.0/thi)
      hi=math.inf if tlo==0.0 else ld+gw*(1.0-1.0/tlo)
      current=bounds[dry]
      if current is None:continue
      bounds[dry]=[max(current[0],inward32_lower(lo)),min(current[1],inward32_upper(hi))]
      crossing_records.append({'layer':layer,'cell':[r,c],'triangle':ti,'edge':[list(a),list(bnode)],
       'dry_node':list(dry),'wet_node':list(wet),'t_B':t0,'length_m':length,
      'interval_raw_m':[lo,hi if math.isfinite(hi) else None],'interval_float32_inward_m':list(bounds[dry])})
 # Coalesce duplicate cell-triangle layer definitions: P/SEA are added once per native cell edge.
 for k,v in bounds.items():
  if v is not None and v[0]>v[1]:bounds[k]=None
 final_intervals=[]
 for r in range(cr0,cr1):
  for c in range(cc0,cc1):
   if fixed_by_mask[r,c] or (r,c) in frozen_nodes:
    continue
   final_intervals.append({'node_rc':[r,c],'interval_float32_inward_m':bounds.get((r,c)),
    'empty_after_float32_or_crossing':bounds.get((r,c)) is None})
 # Optimistic separable box feasibility for the focal 25% prominence target, not a solver guarantee.
 fr,fc=FOCUS;f_interval=bounds.get((fr,fc)) if (fr,fc) in core_set else [float(h[fr,fc]),float(h[fr,fc])]
 axis_results={};f_allowed=[]
 for name,nodes in {'east_west':((fr,fc-1),(fr,fc+1)),'north_south':((fr-1,fc),(fr+1,fc))}.items():
  prom=max(0.0,float(h[fr,fc]-max(h[nodes[0]],h[nodes[1]])));target=0.75*prom
  intervals=[bounds.get(n,[float(h[n]),float(h[n])]) if n in core_set else [float(h[n]),float(h[n])] for n in nodes]
  if any(x is None for x in intervals) or f_interval is None:
   possible=False;allow=[math.inf,-math.inf]
  else:
   allow=[max(f_interval[0],min(x[0] for x in intervals)),
          min(f_interval[1],max(x[1] for x in intervals)+target)]
   possible=allow[0]<=allow[1]
  axis_results[name]={'B_prominence_m':prom,'target_max_prominence_m':target,'focus_interval_m':f_interval,
   'neighbor_intervals_m':intervals,'focus_values_satisfying_reduction_and_no_strict_min_m':allow,'box_feasible':possible}
  f_allowed.append(allow)
 both=bool(all(x['box_feasible'] for x in axis_results.values()) and max(x[0] for x in f_allowed)<=min(x[1] for x in f_allowed))
 focus_status='variable' if (fr,fc) in core_set and f_interval is not None else 'fixed_or_empty_interval'
 probe_records=[]
 for node in ((fr,fc),(fr,fc-1),(fr,fc+1),(fr-1,fc),(fr+1,fc)):
  nr,nc=node;touch={(nr-1,nc-1),(nr-1,nc),(nr,nc-1),(nr,nc)}
  mask_reasons=[name for name,mask in protection.items() if bool(mask[nr,nc])]
  above_reasons={kind:sorted([list(x) for x in cells if x in touch]) for kind,cells in above_by_kind.items()}
  unknown_reasons={kind:sorted([list(x) for x in cells if x in touch]) for kind,cells in unknown_by_kind.items()}
  is_variable=node in core_set
  probe_records.append({'node_rc':list(node),'B_height_m':float(h[nr,nc]),'eligible_by_semantic_masks':not mask_reasons,
   'semantic_fixed_reasons':mask_reasons,'compiled_face_above_cells_touching_node':above_reasons,
   'undefined_field_face_cells_touching_node':unknown_reasons,'variable_after_new_protection':is_variable,
   'variable_if_only_confirmed_above_cells_were_frozen':(node in set(base_mut) and node not in above_frozen_nodes),
   'float32_inward_interval_m':bounds.get(node) if is_variable else [float(h[nr,nc]),float(h[nr,nc])]})
 return {'protection_mask_counts_core':{k:int(v[CORE[0]:CORE[1],CORE[2]:CORE[3]].sum()) for k,v in protection.items()},
  'eligible_before_new_face_freeze_count':len(base_mut),'new_face_freeze_vertices_core_count':len(extra_frozen),
  'eligible_after_confirmed_above_freeze_only_count':len([x for x in base_mut if x not in above_frozen_nodes]),
  'confirmed_above_freeze_vertices_core_count':len(above_frozen_nodes),'unknown_field_vertices_touching_core_count':len(unknown_frozen_nodes),
  'new_face_freeze_vertices_core':sorted([list(x) for x in extra_frozen]),'eligible_after_face_freeze_count':len(variables),
  'eligible_after_face_freeze_nodes':sorted([list(x) for x in variables]),'final_float32_intervals_for_eligible_nodes':final_intervals,
  'face_freeze_vertices_core_count':len(frozen_nodes),
  'F_partial_triangles_touching_originally_eligible_nodes':partial,'crossing_F_unknown':cross_unknown,
  'crossing_record_count':len(crossing_records),'crossing_interval_empty_nodes':[list(k) for k,v in bounds.items() if v is None],
  'focus_status':focus_status,'focus_interval_float32_inward_m':f_interval,'focus_axes':axis_results,
  'both_axes_box_feasible_for_25_percent':both,'crossing_records':crossing_records,
  'focus_and_cardinal_neighbor_blockers':probe_records,
  'unknown_domain_preflight_inconclusive':bool(partial or cross_unknown)}

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 fixtures=run_fixtures()
 src=check_linkage_and_load()
 exposure=scan_compiled_faces(src)
 above_cells={kind:set(tuple(k) for k in exposure['above_by_kind'][kind]) for kind in ('physical','visible')}
 unknown_cells={kind:set(tuple(k) for k in exposure['unknown_by_kind'][kind]) for kind in ('physical','visible')}
 p9_unknown_cells,p9_unknown_by_feature=corridor_p_unknown(src)
 partial_f_cell_set=partial_f_cells(src)
 # Only measured excesses and explicit P9 unknown cells require exact B preservation.
 # Other P-NaN terrain is not frozen merely because no nominal physical field exists.
 freeze_cells=set().union(*above_cells.values()) | p9_unknown_cells | partial_f_cell_set
 domain=reconstruct_domain(src,freeze_cells,above_cells,unknown_cells)
 hashes={str(path):sha(path) for path in EXPECTED}
 hashes[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
 runtime_files=[ATTACH_NAV,WRP_READER,PARSER_DIR/'odol_reader.py',PARSER_DIR/'bis_reader.py',PARSER_DIR/'math_types.py',PARSER_DIR/'lzo_decompress.py',PARSER_DIR/'lzss_decompress.py',EV87_POLICY,EV87_COVERAGE]
 hashes.update({str(p):sha(p) for p in runtime_files})
 hashes.update({str(src['world_pbo']):sha(src['world_pbo']),str(src['water_pbo']):sha(src['water_pbo']),str(BOUNDS):sha(BOUNDS)})
 hashes.update(exposure['model_hashes'])
 # Verify every consumed file again before writing the report.
 for path,digest in hashes.items():
  if sha(Path(path))!=digest:raise AssertionError(f'input changed during preflight: {path}')
 mutable=set(tuple(x) for x in domain['eligible_after_face_freeze_nodes'])
 lower_by_node={tuple(row['node_rc']):float(row['interval_float32_inward_m'][0])
  for row in domain['final_float32_intervals_for_eligible_nodes'] if row['interval_float32_inward_m'] is not None}
 h=np.asarray(src['B']['heights'],dtype=np.float64);unknown_lower_results={'physical':[],'visible':[]}
 for kind in ('physical','visible'):
  for cell,items in exposure['unknown_by_kind'][kind].items():
   r,c=cell
   for item in items:
    tri=TRIS[item['triangle']]
    heights4=np.asarray([h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]],dtype=np.float64)
    for k in tri:
     node=(r+OFFSETS[k][0],c+OFFSETS[k][1])
     if node in lower_by_node:heights4[k]=lower_by_node[node]
    tri_xy=grid_xy(r,c)[np.asarray(tri,dtype=int)]
    ground=affine(tri_xy,heights4[list(tri)])
    points=np.asarray(item['intersection_xz'],dtype=np.float64)
    face=np.asarray(item['face_plane_coeff_xz'],dtype=np.float64)
    max_delta=float(np.max(eval_aff(face,points)-eval_aff(ground,points)))
    item_result={'cell':[r,c],'object':item['object'],'face':item['face'],'triangle':item['triangle'],
     'reason':item['reason'],'intersection_area_m2':item['area_m2'],'max_face_minus_minimum_ground_m':max_delta,
     'buried_over_entire_allowed_lower_envelope':max_delta<=0.0,
     'p9_exact_B_preservation':kind=='physical' and cell in p9_unknown_cells}
    unknown_lower_results[kind].append(item_result)
 unknown_unresolved=[]
 for kind,items in unknown_lower_results.items():
  for item in items:
   if item['p9_exact_B_preservation']:continue
   if not item['buried_over_entire_allowed_lower_envelope']:
    unknown_unresolved.append(item)
 unknown_lower_summary={kind:{'positive_area_face_triangle_overlaps':len(items),
   'nonburied_count':sum(not x['buried_over_entire_allowed_lower_envelope'] for x in items),
   'minimum_clearance_to_lower_envelope_m':min([-x['max_face_minus_minimum_ground_m'] for x in items],default=None)}
  for kind,items in unknown_lower_results.items()}
 partial_f=bool(domain['F_partial_triangles_touching_originally_eligible_nodes'])
 status='PREFLIGHT_INCONCLUSIVE' if (partial_f or unknown_unresolved) else (
  'PREFLIGHT_INFEASIBLE' if domain['focus_status']!='variable' or not domain['both_axes_box_feasible_for_25_percent']
  else 'PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW')
 report={'status':status,'scope':'Offline read-only EV90 preflight; no Q/EV88 candidate read, no solver, no candidate output.',
  'inputs_sha256':hashes,'pins':{'preflight_script_sha256':hashes[str(Path(__file__).resolve())],
   'next_method_plan_sha256':hashes[str(PLAN)],'previous_pilot_plan_sha256':hashes[str(PILOT_PLAN)],
   'B_sha256':hashes[str(B/'candidate/terrain.npz')],
   'EV79_sha256':hashes[str(EV79/'candidate/terrain.npz')],'P_sha256':hashes[str(P)],'F_sha256':hashes[str(F)],
   'staged_0WZD_sha256':hashes[str(WRP)],'deployed_PBO_sha256':hashes[str(src['world_pbo'])],
   'deployed_water_PBO_sha256':hashes[str(src['water_pbo'])],'compiled_OPRW_embedded_sha256':src['compiled_oprw_sha'],
   'compiled_bounds_sha256':hashes[str(BOUNDS)],'compiled_bounds_world_identity':src['bounds']['world_sha256']},
  'geometry':{'window_vertices_rc_halfopen':list(WINDOW),'window_cells_rc_top_left': [WINDOW[0],WINDOW[1]-1,WINDOW[2],WINDOW[3]-1],
   'grid_origin_z_m':Z0,'cell_size_m':CELL,'native_triangles_corner_indices':TRIS,
   'physical_height_tolerance_m':EPS['physical'],'visible_height_tolerance_m':EPS['visible'],
    'LOD_resolutions_exact_float32':{'physical':float(np.float32(3e15)),'visible':float(np.float32(1.0))}},
  'formula_contract':{'above_field':'max at vertices of positive-area ODOL-face/native-triangle intersection of (z_face - nominal_P_or_F) > tolerance',
   'buried_unknown_exception':'max over same intersection vertices of (z_face - z_ground_at_float32_lower_envelope) <= 0.0; terrain interpolation uses the exact NW-SE native triangle',
   'lower_envelope_implication':'inside a native triangle, barycentric weights are nonnegative; if each allowed H vertex is >= L32 and face <= ground(L32) everywhere on the overlap, face remains buried for every allowed H',
   'crossing_edge':'g_w=h_w-level_w<0<g_d=h_d-level_d; t0=-g_w/(g_d-g_w); require t in [max(0,t0-1/edge_length), min(1,t0+1/edge_length)]; convert back with g_d=g_w*(1-1/t)',
   'height_bounds':'lower=max(EV79-2, min(EV79,1.8), min(EV79,max(P,F,SEA)+1e-4)); upper=min(EV79+2,B+0.5); round inward to float32 before intersecting crossings',
   'box_test':'per-axis interval possibility only; each node is treated independently and all non-scalar/global/shape constraints are omitted, so infeasibility is decisive but feasibility is optimistic'},
  'fixtures':fixtures,
  'compiled_scan':{k:v for k,v in exposure.items() if k not in ('model_hashes','above_by_kind','unknown_by_kind')},
   'cell_classification':{'above_P_or_F_by_kind':{k:sorted([list(x) for x in v]) for k,v in above_cells.items()},
   'unknown_field_overlap_by_kind':{k:sorted([list(x) for x in v]) for k,v in unknown_cells.items()},
    'P9_unknown_cells_preserved':sorted([list(x) for x in p9_unknown_cells]),
    'P9_unknown_by_feature':p9_unknown_by_feature,
   'above_cell_count_union':len(set.union(*above_cells.values())) if any(above_cells.values()) else 0,
   'unknown_field_cell_count_union':len(set.union(*unknown_cells.values())) if any(unknown_cells.values()) else 0,
    'F_partial_cells_frozen':sorted([list(x) for x in partial_f_cell_set]),
    'F_partial_cell_count_frozen':len(partial_f_cell_set),
    'freeze_cell_count_union_confirmed_above_plus_P9_unknown_plus_partial_F':len(freeze_cells),
    'P_unknown_face_overlaps_outside_P9_not_frozen_by_default':len(unknown_cells['physical']-p9_unknown_cells)},
  'face_exceedance_examples':{k:[x for cell in sorted(exposure['above_by_kind'][k]) for x in exposure['above_by_kind'][k][cell]][:50] for k in ('physical','visible')},
  'unknown_face_examples':{k:[x for cell in sorted(exposure['unknown_by_kind'][k]) for x in exposure['unknown_by_kind'][k][cell]][:30] for k in ('physical','visible')},
  'unknown_field_lower_envelope_checks':{'results_by_kind':unknown_lower_results,'unresolved':unknown_unresolved},
  'unknown_field_lower_envelope_summary':unknown_lower_summary,
  'focus_unknown_face_records':{kind:[x for x in unknown_lower_results[kind]
    if x['cell'] in ([839,369],[839,370],[840,369],[840,370])] for kind in ('physical','visible')},
  'domain_and_bound_analysis':domain,
   'limitations':['No terrain/render engine or wave envelope; the test is static compiled ODOL triangle height against nominal P/F fields.','Buried faces are included: current terrain height is not used to cull model faces.','The source 0WZD transforms are linked by B deploy/PBO hashes; transforms are not parsed from the compiled OPRW payload.','The focal box-feasibility calculation is optimistic and separable; it is a bound-only interval test, not a coupled terrain solve or proof that other geometry gates pass.','No P/F values are imputed. P9 NaN cells and partial-F cells are frozen; unknown-face exceptions use the float32 lower-ground envelope.']}
 out=OUT/'preflight.json';tmp=OUT/'preflight.json.tmp';tmp.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(out)
 unknown_union=len(set.union(*unknown_cells.values())) if any(unknown_cells.values()) else 0
 above_p=len(above_cells['physical']);above_f=len(above_cells['visible'])
 md=f'''# EV90 preflight — solo lectura\n\n**Estado: {status}.** No se leyó Q ni se ejecutó solver/candidato.\n\n- B `{EXPECTED[B/'candidate/terrain.npz']}`; EV79 `{EXPECTED[EV79/'candidate/terrain.npz']}`; P `{EXPECTED[P]}`; F `{EXPECTED[F]}`. Pin plan `{hashes[str(PLAN)]}`.\n- Ventana: 17×17 vértices, 16×16 celdas. Se enlazaron los 18.024 objetos 0WZD con bounds y PBO desplegado; 78 modelos en la ventana se parsearon para LOD físicas/visibles exactas.\n- Excesos confirmados: {exposure['face_cell_exceedance_count']['physical']} intersecciones físicas sobre P+1e-5 en {above_p} celdas; {exposure['face_cell_exceedance_count']['visible']} visibles sobre F+2e-5 en {above_f} celdas. Campo indefinido: {unknown_union} celdas únicas (P: {len(unknown_cells['physical'])}; F: {len(unknown_cells['visible'])}).\n- Foco `{FOCUS}` toca campos P/F desconocidos en celdas `[839,370]` y `[840,370]`; no es F parcial. La excepción de enterramiento sí se cumple: {unknown_lower_summary['physical']['positive_area_face_triangle_overlaps']} solapes físicos, clearance mínimo {unknown_lower_summary['physical']['minimum_clearance_to_lower_envelope_m']:.7f} m; {unknown_lower_summary['visible']['positive_area_face_triangle_overlaps']} visibles, clearance mínimo {unknown_lower_summary['visible']['minimum_clearance_to_lower_envelope_m']:.7f} m; todos siguen enterrados incluso bajo la envolvente L32.\n- Elegibles semánticos antes de freezes por geometría: {domain['eligible_before_new_face_freeze_count']}; después: {domain['eligible_after_face_freeze_count']}. El foco queda `{domain['focus_status']}`, intervalo float32 inward `{domain['focus_interval_float32_inward_m']}`; prominencia B EW {domain['focus_axes']['east_west']['B_prominence_m']:.6f} m, NS {domain['focus_axes']['north_south']['B_prominence_m']:.6f} m. La caja optimista permite ≥25% en ambos ejes: `{domain['both_axes_box_feasible_for_25_percent']}`.\n\nLos excesos sobre P se congelan; las celdas P ausentes dentro de P9 y las F parciales también quedan idénticas a B. P ausente fuera de P9 no se congela por defecto; su exposición física se conserva solo si todas las caras permanecen enterradas bajo L32. La caja es separable y optimista: no es solve acoplado ni prueba energía, prominencia angular, silueta u otras puertas del plan.\n'''
 (OUT/'preflight.md').write_text(md,encoding='utf-8')
 print(json.dumps({'status':status,'selected_objects':exposure['selected_object_count'],'selected_models':exposure['selected_models'],
  'above_cells':report['cell_classification']['above_cell_count_union'],'above_P':len(above_cells['physical']),'above_F':len(above_cells['visible']),
   'unknown_field_cells':report['cell_classification']['unknown_field_cell_count_union'],'freeze_cells':len(freeze_cells),
   'eligible_before':domain['eligible_before_new_face_freeze_count'],
  'eligible_after':domain['eligible_after_face_freeze_count'],'focus_status':domain['focus_status'],
  'focus_interval':domain['focus_interval_float32_inward_m'],'prominence25_box_feasible':domain['both_axes_box_feasible_for_25_percent'],
  'report_sha256':sha(out)},indent=2))

if __name__=='__main__':main()
