"""Read-only centreline and cross-section consumer of all built design profiles."""
from pathlib import Path
import sys,json,hashlib,csv
import numpy as np
import shapely
from shapely.geometry import shape,LineString,Point,box
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
SOURCE=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')
PFILE=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
FFILE=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009/preserved-field.npy')
DESIGN=Path('E:/DayZ-Baltic-Build/v30-v11/design')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def sample(h,p,f,x,z):
 rx=x/6;rz=(12282-z)/6
 c=np.clip(np.floor(rx).astype(int),0,2046);r=np.clip(np.floor(rz).astype(int),0,2046)
 a=rx-c;b=rz-r
 g=np.where(a>=b,h[r,c]+a*(h[r,c+1]-h[r,c])+b*(h[r+1,c+1]-h[r,c+1]),h[r,c]+b*(h[r+1,c]-h[r,c])+a*(h[r+1,c+1]-h[r+1,c]))
 ff=f[r,c];v=np.where(a>=b,ff[:,0]+a*(ff[:,1]-ff[:,0])+b*(ff[:,3]-ff[:,1]),ff[:,0]+b*(ff[:,2]-ff[:,0])+a*(ff[:,3]-ff[:,2]))
 return g,p[r,c]-g,v-g,r,c
def intervals(mask,s):
 edges=np.diff(np.r_[False,mask,False].astype(int));starts=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)-1
 return [(int(a),int(b),float(s[b]-s[a])) for a,b in zip(starts,ends)]
def main():
 hdata=dict(np.load(SOURCE));h=hdata['heights'];p=np.load(PFILE);f=np.load(FFILE)
 assert sha(SOURCE)=='fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6'
 # Analytic independent plane: native interpolation must reproduce z=2x+3*row+5.
 hh=np.indices((3,3));hh=(12*hh[1]+18*hh[0]+5).astype(float);pp=np.full((2,2),100.);ff=np.repeat(pp[:,:,None],4,axis=2)
 xx=np.array([1.,5.,7.,10.]);row=np.array([5.,1.,2.,11.]);zz=12282-row
 gg,dd,vv,_,_=sample(hh,pp,ff,xx,zz)
 assert np.allclose(gg,2*xx+3*row+5) and np.allclose(dd,100-gg)
 # Gap interval detector has exact metric length and catches an inserted dry interval.
 assert intervals(np.array([False,True,True,True,False]),np.arange(5.))==[(1,3,2.)]
 profiles=np.load(DESIGN/'profiles.npz');water=json.loads((DESIGN/'water_v3.geojson').read_text())['features'];streams=json.loads((DESIGN/'streams_candidates.geojson').read_text())['features']
 feats={q['properties']['id']:q for q in water if q['properties'].get('class')=='river' and q['properties'].get('id')}
 feats.update({q['properties']['id']:q for q in streams if q['properties']['tier_m']>=2500})
 records=[];gaps=[];samples_count=0;excluded=[]
 for key in profiles.files:
  if key not in feats:
   excluded.append(key);continue
  feat=feats[key];geom=shape(feat['geometry']).intersection(box(60,60,12222,12222));a=profiles[key]
  distances=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(a[:,1:3],axis=0),axis=1))];s=np.arange(0.,distances[-1],1.)
  q=np.c_[np.interp(s,distances,a[:,1]),np.interp(s,distances,a[:,2])]
  in_design=shapely.intersects_xy(geom,q[:,0],q[:,1]);valid=in_design&(q[:,0]>=60)&(q[:,0]<=12222)&(q[:,1]>=60)&(q[:,1]<=12222)
  if not valid.any():records.append(dict(id=key,status='NO_PROFILE_INSIDE_CONSTRUCTED_DESIGN',properties=feat['properties']));continue
  s=s[valid];q=q[valid];ground,depth,visible,r,c=sample(h,p,f,q[:,0],q[:,1]);samples_count+=len(q)
  centre_wet=np.isfinite(depth)&(depth>.01);sea=hdata['cls'][r,c]==1;centre_wet|=sea&(ground<.65)
  # Orthogonal cross-sections through the approved centreline; actual outline plus one cell margin.
  tangent=np.gradient(q,axis=0);length=np.linalg.norm(tangent,axis=1);length[length<1e-8]=1.;normal=np.c_[-tangent[:,1],tangent[:,0]]/length[:,None]
  offsets=np.arange(-36.,36.01,1.5);cross=q[:,None,:]+normal[:,None,:]*offsets[None,:,None];flat=cross.reshape(-1,2)
  near=shapely.intersects_xy(geom.buffer(6),flat[:,0],flat[:,1]).reshape(len(q),-1)
  ok=(flat[:,0]>=0)&(flat[:,0]<=12282)&(flat[:,1]>=0)&(flat[:,1]<=12282)
  gh,dh,vh,rr,cc=sample(h,p,f,np.clip(flat[:,0],0,12282),np.clip(flat[:,1],0,12282))
  wet=np.isfinite(dh)&(dh>.01);wet|=(hdata['cls'][rr,cc]==1)&(gh<.65);wet=(wet&ok).reshape(len(q),-1)&near
  any_wet=wet.any(1);max_depth=np.max(np.where(wet,np.nan_to_num(dh,nan=-999.).reshape(len(q),-1),-999.),axis=1)
  breaks=np.r_[False,np.diff(s)>1.01];dry=~any_wet;dry[breaks]=False
  long_gaps=[x for x in intervals(dry,s) if x[2]>=6.]
  row=dict(id=key,properties=feat['properties'],samples=len(q),centre_dry=int((~centre_wet).sum()),cross_section_dry=int(dry.sum()),long_gaps=len(long_gaps),max_dry_run_m=max((x[2] for x in intervals(dry,s)),default=0.),min_centre_depth_m=float(np.nanmin(depth)) if np.isfinite(depth).any() else None,status='HAS_DRY_CROSS_SECTIONS' if long_gaps else 'NO_DRY_CROSS_SECTION_AT_1M')
  records.append(row)
  for lo,hi,length in long_gaps:
   mid=(lo+hi)//2;gaps.append(dict(id=key,start_s=float(s[lo]),end_s=float(s[hi]),length_m=length,start=q[lo].tolist(),end=q[hi].tolist(),mid=q[mid].tolist(),ground=float(ground[mid]),plane=float(p[r[mid],c[mid]]) if np.isfinite(p[r[mid],c[mid]]) else None,cls=int(hdata['cls'][r[mid],c[mid]]),level_metadata=float(hdata['level'][r[mid],c[mid]]) if 'level' in hdata and np.isfinite(hdata['level'][r[mid],c[mid]]) else None))
 report=dict(status='DISCOVERY_REQUIRES_DESIGN_ATTRIBUTION' if gaps else 'CROSS_SECTION_CENSUS_CLEAR',source_sha256=sha(SOURCE),physical_plane_sha256=sha(PFILE),visible_field_sha256=sha(FFILE),profile_sha256=sha(DESIGN/'profiles.npz'),built_profile_count=len(feats),profile_keys=len(profiles.files),sample_count=samples_count,records=records,excluded_profile_ids=excluded,long_dry_gaps=gaps,controls=['analytic_plane_both_triangles','inserted_dry_interval'],limits=['Dry centreline can be shifted within designed width; cross-sections search the polygon plus a single6m cell.','Cross-section presence is not longitudinal connectivity, water depth guarantee or native rendering.','Polygon-only rivers/navigables have no profile and retain their existing domain and navigation checks.','End caps, roads, deliberate joins and disconnected profile parts require attribution before changing terrain.'])
 (B/'census.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k not in ['records','excluded_profile_ids','long_dry_gaps']},indent=2))
 print(json.dumps(sorted(gaps,key=lambda g:-g['length_m'])[:25],indent=2))
if __name__=='__main__':main()
