"""Complete the declared dry floor; preserve all protected native heights."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
import rasterio
ROOT=Path(__file__).resolve().parents[2];OLD=ROOT/'tests/regional_outline_smoothing_v25';OUT=ROOT/'tests/regional_outline_smoothing_v26'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not OUT.exists();OUT.mkdir()
assert sha(OLD/'baltic_outline_smoothing_v25.asc')=='f7a220fda8ec33e483dad6e93d113a6c4f98cd09020dd1e15769c13dc93c7055'
ref=np.load(OLD/'reference.npz');h=ref['candidate'].copy();base=ref['parent'];old=np.load(ROOT/'tests/regional_foundation_combined_v9/reference.npz')['candidate']
wet=ref['wet']|ref['ocean'];fixed=ref['fairway_support']|(base!=old);fixed[:2]=fixed[-2:]=True;fixed[:,:2]=fixed[:,-2:]=True
change=(~wet)&(~fixed)&(h<np.float32(1.4));r,c=np.where(change);before=h[change].copy();h[change]=np.float32(1.4)
assert float((h[change]-before).max())<.002
np.savez_compressed(OUT/'floor-delta.npz',row=r,col=c,before=before,after=h[change])
shutil.copyfile(OLD/'pre-solve.json',OUT/'pre-solve.json')
asc=OUT/'baltic_outline_smoothing_v26.asc'
with asc.open('w',newline='\n') as f:
    f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n');np.savetxt(f,h,fmt='%.9g')
with rasterio.open(asc) as ds:assert np.array_equal(h,ds.read(1))
payload={k:ref[k] for k in ref.files};payload.update(candidate=h,changed=h!=base);np.savez_compressed(OUT/'reference.npz',**payload)
report=dict(status='CANDIDATE_REQUIRES_INDEPENDENT_GATES',parent_asc_sha256=sha(OLD/'baltic_outline_smoothing_v25.asc'),asc_sha256=sha(asc),floor_vertices=len(r),maximum_floor_raise_m=float((h[change]-before).max()),delta_sha256=sha(OUT/'floor-delta.npz'),exception='Eight pre-existing low bridge-approach vertices remain exact under the frozen protection rule.')
(OUT/'solve.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
