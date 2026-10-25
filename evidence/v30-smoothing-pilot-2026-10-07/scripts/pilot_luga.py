"""Two Luga shore pilots on frozen V12; input fields come from the V12 recipe.
No reclassification, level changes or edits to the certified corridor faces.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib
import numpy as np
import shapely
from shapely.geometry import shape
from scipy import ndimage
W=Path(__file__).resolve().parents[3];sys.path.insert(0,str(W/'tools/terrain'))
from profile_inland_v30 import profile
from finish_shores_v30 import protect_corridors,discard_steeper_land_faces
from v30_common import cell_planes,grid_xz,raster_vertices
B=Path('E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007')
R=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev')

def main():
 ref=Path('E:/DayZ-Baltic-Build/v30-v12/inland');rep=json.loads((ref/'report.json').read_text())
 source=Path('E:/DayZ-Baltic-Build/v30-v11/v6/terrain_causeway.npz')
 assert hashlib.sha256(source.read_bytes()).hexdigest()==rep['inputs'][str(source).replace('/','\\')]
 with np.load(source) as f:t=dict(f)
 with np.load(ref/'terrain_inland.npz') as f:base=dict(f)
 assert hashlib.sha256((ref/'terrain_inland.npz').read_bytes()).hexdigest()=='8b3a8c5541403abaf852e14fb4c0651175e6dcaa541f6f8a151f1db04ac7a8a6'
 params=rep['params'];params['slope_by_class']={int(k):v for k,v in params['slope_by_class'].items()}
 a=SimpleNamespace(**params)
 a.ext_sd=np.load(a.outline_sd)['sd'].astype(float)
 corridor,_,_,csources=protect_corridors(cell_planes(base['cls'],base['level'],sea_cut=a.sea_cut))
 axes_path=Path('E:/DayZ-Baltic-Build/v30-v11/24/axes.json');axes=json.loads(axes_path.read_text())
 reach=np.zeros((2048,2048),bool)
 for v in axes.values():
  for r,c in v['removed_cells']:reach[r:r+2,c:c+2]=True
 nature=np.load(R/'tests/regional_outline_v1/reference.npz')['reserve'].astype(bool)
 feats=json.loads(Path('E:/DayZ-Baltic-Build/v30-redesign/design/water_v3.geojson').read_text(encoding='utf-8'))['features']
 luga=next(shape(f['geometry']) for f in feats if f['properties'].get('id')=='Luga_0')
 near_luga=raster_vertices([luga.buffer(24)]).astype(bool)
 x,z=grid_xz();frozen=corridor|nature|base['platform']|base['reserve']|base['narva']|base['beach']|reach|(np.hypot(x-2417.1428225906,z-6889.8850822322)<=620)|(x<66)|(x>12216)|(z<66)|(z>12216)
 nd=ndimage.distance_transform_edt(base['cls']!=3)*6
 allowed=near_luga&~frozen&((base['cls']==3)|((base['cls']==0)&(nd<=18)))
 # Only native shore triangles, not the newly raised main bed.
 shore=ndimage.binary_dilation(base['cls']==0,iterations=3)&ndimage.binary_dilation(base['cls']==3,iterations=3)
 allowed &= shore
 np.savez_compressed(B/'luga-frozen-masks.npz',allowed=allowed,corridor=corridor,frozen=frozen)
 for label in (sys.argv[1:] or ["18", "24"]):
  sigma=int(label.split("-")[0])
  if label.endswith("-vector"):
   a.outline_sd_classes=[2,3,5,6,7]
  a.sigma=float(sigma)
  print('START LUGA',sigma,flush=True)
  out,_,r=profile(t,corridor,reach,a)
  h=base['heights'].astype(float);candidate=h.copy()
  candidate[allowed]=np.clip(out['heights'][allowed],h[allowed]-1.5,h[allowed]+2.0)
  candidate,recovery=discard_steeper_land_faces(candidate,h,base['cls'])
  result=dict(base);result['heights']=candidate.astype(np.float32)
  dest=B/f'luga-{label}';dest.mkdir()
  np.savez_compressed(dest/'terrain_inland.npz',**result)
  d=candidate-h
  report={'status':'PENDING_WATERLINE_GATES','source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'params':{k:v for k,v in vars(a).items() if k!='ext_sd'},'changed_vertices':int(np.count_nonzero(d)),'max_raise_m':float(d.max()),'max_lower_m':float(-d.min()),'fixed_exact':bool(np.array_equal(candidate[~allowed],h[~allowed])),'corridor_exact':bool(np.array_equal(candidate[corridor],h[corridor])),'face_recovery':recovery,'profile_report':r}
  (dest/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
  print('DONE LUGA',sigma,report['changed_vertices'],flush=True)
if __name__=='__main__':main()
