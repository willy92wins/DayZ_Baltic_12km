"""Read-only local source-band attribution of fourteen archived native waypoints."""
from pathlib import Path
import ast,datetime,hashlib,json,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');O=R/'bank-source-attribution-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def weights_xz(tri,x,z):
 a=np.asarray(tri,float)[:,[0,2]];matrix=np.vstack([a.T,np.ones(3)])
 if abs(np.linalg.det(matrix))<1e-10:return None
 weights=np.linalg.solve(matrix,np.array([x,z,1.]))
 return weights if min(weights)>=-1e-7 else None

def main():
 O.mkdir(exist_ok=False);start=datetime.datetime.now(datetime.timezone.utc);deadline=start+datetime.timedelta(minutes=15)
 (O/'budget.json').write_text(json.dumps(dict(started_utc=start.isoformat(),deadline_utc=deadline.isoformat(),runs=0,generations=0,asset_writes=0),indent=2)+'\n')
 source=R/'river-kit7-a-on-f-20261026/kit-7-surfaces.npz';later=R/'river-kit7-rv-capped-v2-20261026/kit-7-surfaces.npz';author=W/'tools/water/continuous_stream_pilot_v31.py'
 pilot=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Nav12/Addons/baltic_stream_pilot.pbo');geo=R/'kit7-packed-nav-discovery-20261026/geometry.json'
 if sha(source)!=sha(later) or sha(source)!='9d8caf0fb75d2bd34f71b877ecd3f71079898fbc01c28e67ddab0bf8dca50063':raise ValueError('surface identity')
 if sha(author)!='8b340a2ab4e25d69ff9baf46f71c8f843c9da2c02137c32fa356a0bb9deb9169':raise ValueError('historical author identity')
 if sha(pilot)!='3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6' or sha(geo)!='e3c902fd1561804b3b02b68ada18e64c26c3d697f79c9fce8bb0ad62e66d3c5e':raise ValueError('consumer geometry identity')
 native_paths=[R/'kit7-nav-height-diagnostic-20261026/result.json',R/'kit7-nav12-height-diagnostic-20261027/result.json']
 layer_paths=[R/'kit7-nav-layer-diagnostic-20261026-v2/result.json',R/'kit7-nav12-layer-diagnostic-20261027/result.json']
 paths=[Path(__file__),source,later,author,pilot,geo,*native_paths,*layer_paths,W/'plans/ev112-bank-source-attribution-20261027.md']
 before={str(p):sha(p) for p in paths}
 # Use the exact pure topology function from the hash-pinned historical author.
 tree=ast.parse(author.read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='strip_faces')
 namespace={'np':np};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(author),'exec'),namespace)
 sf=namespace['strip_faces'];fixture=[[0,0,0],[2,2,0],[0,4,2]]
 w=weights_xz(fixture,.5,.5);assert np.allclose(w,[.5,.25,.25]) and abs(w@np.array(fixture)[:,1]-1.5)<1e-12
 assert weights_xz(fixture,4,4) is None and weights_xz([[0,0,0],[1,1,1],[2,2,2]],1,1) is None
 assert np.array_equal(sf(2,2),[[0,2,3],[0,3,1]])
 qtest=np.array([0,2,0]);stest=np.array([0,0,2]);assert abs(w@qtest-.5)<1e-12 and abs(w@stest-.5)<1e-12
 a=np.load(source);bed=a['bed'];station=a['station'];level=a['level'];qs=np.unique(np.r_[np.arange(-18,19,dtype=float),-2.25,2.25]);n,m=bed.shape[:2]
 assert m==len(qs) and bed.shape==(len(station),m,3) and np.isfinite(bed).all()
 face=sf(n,m);tri=bed.reshape(-1,3)[face];qflat=np.tile(qs,n);sflat=np.repeat(station,m);wflat=np.repeat(level,m)
 minimum=tri[:,:,[0,2]].min(axis=1);maximum=tri[:,:,[0,2]].max(axis=1)
 # Reuse known PBO reader only to bind the local ODOL files to the exact package.
 sys.path.insert(0,str(W/'tools/playtest'));from attach_navmesh import read_pbo
 _,_,entries=read_pbo(pilot);metadata=read(geo)['models'];rows=[]
 for label,npth,lpth in zip(['nav12p5','nav12'],native_paths,layer_paths):
  native=read(npth)['samples'];layers={(x['query'],x['index']):x for x in read(lpth)['samples']}
  for sample in native:
   assert datetime.datetime.now(datetime.timezone.utc)<deadline
   x,yn,z=sample['nav'];ids=np.flatnonzero(np.all(minimum<=[x+1e-7,z+1e-7],axis=1)&np.all(maximum>=[x-1e-7,z-1e-7],axis=1));hits=[]
   for i in ids:
    weight=weights_xz(tri[i],x,z)
    if weight is None:continue
    ix=face[i];s=float(weight@sflat[ix]);q=float(weight@qflat[ix]);water=float(weight@wflat[ix]);y=float(weight@tri[i,:,1]);band='CAP' if min(s,station[-1]-s)<6 else 'WET_BED' if abs(q)<=2.25 else 'BANK_SLOPE' if abs(q)<=4 else 'OUTER_APRON'
    hits.append(dict(triangle=int(i),station_m=s,q_parameter=q,band=band,source_bed_y=y,visual_water_y=water,water_ext_y=water-.25,weights=weight.tolist(),triangle_vertices=tri[i].tolist()))
   layer=layers[(sample['query'],sample['index'])]
   for item in layer['lods']:
    model=item['model'];path=R/'kit7-packed-nav-discovery-20261026'/model.split('\\')[-1]
    assert sha(path)==metadata[model]['odol_sha256'] and path.read_bytes()==entries[path.name]
   selected=max(hits,key=lambda v:v['source_bed_y']) if hits else None
   native_y=sample['engine_roadway'][1];residual=None if selected is None else selected['source_bed_y']-native_y
   eligible=bool(selected and selected['band']!='CAP' and abs(residual)<=.002 and len({v['band'] for v in hits})==1)
   rows.append(dict(mesh=label,query=sample['query'],index=sample['index'],xz=[x,z],navigation_y=yn,native_roadway_y=native_y,native_terrain_y=sample['terrain'][1],navigation_error_m=sample['error_m'],failed=sample['excess_m']>0,attribution='SOURCE_ATTRIBUTION_ONLY' if eligible else 'INCONCLUSIVE_SOURCE_ATTRIBUTION',source_minus_native_m=residual,candidate_count=len(hits),selected=selected,all_candidates=hits,archived_lods=layer['lods']))
 assert len(rows)==14 and sum(r['failed'] for r in rows)==7
 assert all(sha(Path(k))==v for k,v in before.items())
 result=dict(status='SOURCE_ATTRIBUTION_ONLY' if all(r['attribution']=='SOURCE_ATTRIBUTION_ONLY' for r in rows) else 'INCONCLUSIVE_SOURCE_ATTRIBUTION',cases=14,failed_cases=7,pass_controls=7,rows=rows,inputs=before,inputs_unchanged=True,fixtures_passed=['plane_height','q_station','outside','degenerate','historical_strip_topology'],limits=['Only14 archived native waypoints, not full navigation or source mesh.','Source is bound by exact author/surface hashes and local native/packed comparisons; it does not prove entire generator-to-PBO lineage.','Geometry and Roadway differ slightly by the existing collision cap; separate layers retained.','No modification, performance claim, new engine run, corrective candidate or tolerance change.'])
 (O/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(json.dumps(dict(status=result['status'],rows=[{k:r[k] for k in ['mesh','query','index','failed','source_minus_native_m','candidate_count']}|dict(band=r['selected']['band'],q=r['selected']['q_parameter']) if r['selected'] else r for r in rows]),indent=2))

if __name__=='__main__':main()
