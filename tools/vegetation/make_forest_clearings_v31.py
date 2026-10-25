"""Grass-paint mask from placed tree positions and the shipped forest floor.
World coordinates: north-up 1 m, 12288x12288. This changes surface only, never vegetation or gates.
With --moss and its SHA, also repaint the generator's whole 10.75 m tree-free moss
margin where it lies on dry forest floor. The mask must belong to this forest run.
"""
from pathlib import Path
from array import array
import argparse,json,hashlib,time
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('records');ap.add_argument('reference');ap.add_argument('rasters');ap.add_argument('out');ap.add_argument('--moss');ap.add_argument('--moss-sha256');a=ap.parse_args()
 if bool(a.moss)!=bool(a.moss_sha256):ap.error('--moss and --moss-sha256 must be provided together')
 if a.moss and sha(a.moss)!=a.moss_sha256:raise ValueError('moss SHA256 mismatch')
 moss=None
 if a.moss:
  moss=np.load(a.moss,mmap_mode='r',allow_pickle=False)
  if moss.shape!=(12288,12288) or moss.dtype!=bool:raise ValueError('moss must be a north-up 12288x12288 bool raster')
 O=Path(a.out);O.mkdir(exist_ok=False);R=Path(a.rasters);t=time.time()
 ref=json.loads(Path(a.reference).read_text());trees={m for m,v in ref['models'].items() if v['family'] in ('conifer','broadleaf')};positions=array('d');n=0
 with Path(a.records).open(encoding='ascii') as f:
  for line in f:
   line=line.strip().rstrip(',')
   if line in ('[',']',''):continue
   r=json.loads(line);m=r['matrix'];assert len(m)==12 and np.isfinite(m).all()
   if r['model'] in trees:positions.extend((m[9],m[11]))
   else:assert r['model'] in ref['models']
   n+=1
 xy=np.frombuffer(positions,dtype=np.float64).reshape(-1,2);assert len(xy)>0;tree=cKDTree(xy)
 slot=np.load(R/'slot1m.npy',mmap_mode='r');wet=np.load(R/'wsea1m.npy',mmap_mode='r');assert slot.shape==wet.shape==(12288,12288)
 raw=np.zeros(slot.shape,bool)
 for i0 in range(0,12288,128):
  forest=(slot[i0:i0+128]==1)&((wet[i0:i0+128]&1)==0);ii,jj=np.nonzero(forest);q=np.c_[jj+.5,12288-i0-ii-.5];dist=tree.query(q,distance_upper_bound=10.)[0];raw[i0+ii,jj]=dist>=10.
 print('raw',int(raw.sum()),'seconds',time.time()-t,flush=True)
 # Keep genuine patches; a three metre blend margin avoids a dark rim around the clearing.
 lab,num=ndimage.label(raw,structure=np.ones((3,3),bool));sizes=np.bincount(lab.ravel());keep=sizes>=400;keep[0]=False;mask=keep[lab];del lab
 mask=ndimage.binary_dilation(mask,iterations=3)&(slot==1)&((wet&1)==0)
 moss_extra=0
 if a.moss:
  gap=(ndimage.distance_transform_edt(~moss)<=10.75) if moss.any() else np.zeros(mask.shape,bool)
  gap&=(slot==1)&((wet&1)==0);moss_extra=int((gap&~mask).sum());mask|=gap
 np.save(O/'forest-clearings.npy',mask);report=dict(schema='forest-clearings-v31.v1',tool_sha256=sha(__file__),records=a.records,records_sha256=sha(a.records),reference=a.reference,reference_sha256=sha(a.reference),rasters=a.rasters,slot_sha256=sha(R/'slot1m.npy'),water_sha256=sha(R/'wsea1m.npy'),mask=str(O/'forest-clearings.npy'),mask_sha256=sha(O/'forest-clearings.npy'),instances=n,trees=len(xy),raw_clear_pixels=int(raw.sum()),paint_pixels=int(mask.sum()),tree_free_distance_m=10.,minimum_patch_m2=400,blend_margin_m=3.,north_edge_z=12288,seconds=time.time()-t)
 report['moss']=dict(path=a.moss,sha256=a.moss_sha256,tree_free_margin_m=10.75,additional_paint_pixels=moss_extra) if a.moss else None
 (O/'manifest.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(report),flush=True)
if __name__=='__main__':main()
