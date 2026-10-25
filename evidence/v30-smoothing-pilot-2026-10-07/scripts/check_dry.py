"""Consumer checks on saved dry candidates, using frozen V12 stations/masks."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy import ndimage
W=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(W/'tools/terrain'))
from verify_roads_v30 import evaluate
from v30_common import grid_xz
B=Path('E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007')
R=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev')
BASE=Path('E:/DayZ-Baltic-Build/v30-v12/inland/terrain_inland.npz')

def steep(h):
 nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
 return [np.degrees(np.arctan(np.hypot(ne-nw,se-ne)/6)),np.degrees(np.arctan(np.hypot(sw-nw,se-sw)/6))]

def curvature(h,m):
 xx=(h[1:-1,:-2]-2*h[1:-1,1:-1]+h[1:-1,2:])/36
 zz=(h[:-2,1:-1]-2*h[1:-1,1:-1]+h[2:,1:-1])/36
 xz=(h[2:,2:]-h[2:,:-2]-h[:-2,2:]+h[:-2,:-2])/144
 v=np.sqrt(xx*xx+zz*zz+2*xz*xz)[m[1:-1,1:-1]]
 return {'points':len(v),'rms':float(np.sqrt(np.mean(v*v))),'p95':float(np.percentile(v,95))}

def invariants(t,u,protected,max_delta=1.00001):
 return {**{f'unchanged_{k}':bool(np.array_equal(t[k],u[k],equal_nan=True)) for k in t if k!='heights'},'protected_exact':bool(np.array_equal(t['heights'][protected],u['heights'][protected])),'finite':bool(np.isfinite(u['heights']).all()),'height_cap':bool(np.max(np.abs(u['heights'].astype(float)-t['heights']))<=max_delta)}

def main():
 with np.load(BASE) as a:t=dict(a)
 h=t['heights'].astype(float); x,z=grid_xz()
 with np.load(R/'tests/regional_outline_v1/reference.npz') as a:nature=a['reserve'].astype(bool)
 with np.load(R/'tests/relief_v30/relief_v30_mix.npz') as a:high=a['high']
 wd=ndimage.distance_transform_edt(~((t['cls']>0)|t['water']))*6
 summits=(high>=.5)&(h==ndimage.maximum_filter(h,size=61,mode='nearest'))
 protected=(wd<=36)|t['platform']|t['reserve']|t['beach']|t['narva']|nature|summits|(h<1.4)|(np.hypot(x-2417.1428225906,z-6889.8850822322)<=620)|(x<66)|(x>12216)|(z<66)|(z>12216)
 evalm=~protected
 oldsteep=steep(h); base_road=evaluate(h,t['water'].astype(bool));reports={}
 # Negative controls must reject altered metadata and one protected terrain vertex.
 idx=tuple(np.argwhere(t['platform'])[0]); wrong=dict(t); wrong['heights']=t['heights'].copy();wrong['heights'][idx]+=0.25
 assert not invariants(t,wrong,protected)['protected_exact']
 wrong=dict(t);wrong['cls']=t['cls'].copy();wrong['cls'][0,0]^=1
 assert not invariants(t,wrong,protected)['unchanged_cls']
 groups={'all':evalm,'uplands':evalm&(high>=.5),'plains':evalm&(high<.5)}
 for sigma in (sys.argv[1:] or ["18", "24"]):
  path=B/f'dry-{sigma}/terrain_dry.npz'
  with np.load(path) as a:u=dict(a)
  hh=u['heights'].astype(float);inv=invariants(t,u,protected)
  slopes=steep(hh); bad=sum(int((new>np.maximum(old,35.)+1e-4).sum()) for old,new in zip(oldsteep,slopes))
  macro=float(np.max(np.abs(ndimage.gaussian_filter(hh-h,30.,mode='nearest'))))
  curve={k:{'before':curvature(h,m),'after':curvature(hh,m)} for k,m in groups.items()}
  for v in curve.values():v['reduction']=1-v['after']['rms']/v['before']['rms']
  road=evaluate(hh,t['water'].astype(bool))
  road_equal=road==base_road
  gates={**inv,'no_worsened_steep_faces':bad==0,'macro_cap':macro<=.10,'curvature_reduction':all(v['reduction']>=.10 for v in curve.values()),'frozen_road_result_identical':road_equal,'road_pass':road['status']=='PASS'}
  reports[str(sigma)]={'status':'PASS_OFFLINE_DRY_ONLY' if all(gates.values()) else 'FAIL','gates':gates,'curvature':curve,'macro_max_change_m':macro,'worsened_steep_faces':bad,'max_change_m':float(np.max(np.abs(hh-h))),'changed_vertices':int(np.count_nonzero(hh!=h)),'road':road,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  print(sigma,{k:v for k,v in reports[str(sigma)].items() if k not in ('road',)},flush=True)
 (B/('dry-independent-'+str(sigma)+'.json') if sys.argv[1:] else B/'dry-independent.json').write_text(json.dumps({'negative_controls':{'protected_edit_rejected':True,'class_edit_rejected':True},'frozen_source':str(BASE),'baseline_road':base_road,'variants':reports},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__': main()
