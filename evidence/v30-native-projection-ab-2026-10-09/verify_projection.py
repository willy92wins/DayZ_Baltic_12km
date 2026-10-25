from pathlib import Path
import json,re,hashlib
import numpy as np
from PIL import Image
B=Path(__file__).parent
rt=json.loads((B/'runtime-A.json').read_text())
matrix=np.array(rt['camera']['camera']['matrix']).reshape(4,3)
samples={}; tick=None
for line in (B/'projection-A.log').read_text().splitlines():
    parts=line.split(';')
    if parts[0]=='CAMERA':
        tick=int(parts[1]); nums=lambda s:np.array([float(v) for v in re.findall(r'-?\d+\.?\d*',s)])
        pos=nums(parts[2]); size=[int(parts[5]),int(parts[6])]
        if np.max(abs(pos-matrix[3]))<1e-5 and size==[1920,1080]: samples[tick]=[]
    elif parts[0]=='POINT' and tick in samples:
        samples[tick].append((int(parts[2]),nums(parts[3]),nums(parts[4]),nums(parts[5])))
valid=[v for v in samples.values() if len(v)==12]
assert valid
rows=valid[-1]; ids=np.array([r[0] for r in rows]); world=np.stack([r[1] for r in rows]); native=np.stack([r[2] for r in rows]); relative=np.stack([r[3] for r in rows])
q=(world-matrix[3])@matrix[:3].T
uv=np.c_[q[:,0]/q[:,2],-q[:,1]/q[:,2]]
center=np.array([960.,540.]); observed=native[:,:2]-center
inside=(native[:,0]>1)&(native[:,0]<1919)&(native[:,1]>1)&(native[:,1]<1079)&(native[:,2]>0)
train=inside&(ids%2==0); test=inside&~train
f=float(np.sum(uv[train]*observed[train])/np.sum(uv[train]**2))
pred=center+f*uv; error=np.linalg.norm(pred-native[:,:2],axis=1)
rel_error=float(np.max(abs(relative[:,:2]*[1920,1080]-native[:,:2])))
assert error[test].max()<.05
assert rel_error<.003
assert np.max(abs(q[:,2]-native[:,2]))<.002
clamped=np.clip(pred,[0,0],[1920,1080]); assert np.linalg.norm(clamped-native[:,:2],axis=1).max()<.05
estimated=561.0279309536028
captures=rt['captures']; checks=[]
for row in captures:
    a=np.array(Image.open(row['fullres_path']).convert('RGB')).astype(np.int16)
    assert a.shape==(1080,1920,3)
    sky=a[40:300,100:1800]; magenta=(sky[:,:,0]>sky[:,:,1]+65)&(sky[:,:,2]>sky[:,:,1]+65)&(sky[:,:,0]>120)
    checks.append(dict(path=row['fullres_path'],magenta_sky_pixels=int(magenta.sum()),sky_mean=sky.mean(axis=(0,1)).tolist()))
assert all(c['magenta_sky_pixels']==0 for c in checks)
report=dict(status='NATIVE_PROJECTION_CONFIRMED',native_samples=len(valid),native_focal_px=f,archive_estimate_px=estimated,archive_estimate_delta_px=f-estimated,train_ids=ids[train].tolist(),heldout_ids=ids[test].tolist(),heldout_max_error_px=float(error[test].max()),all_clamped_max_error_px=float(np.linalg.norm(clamped-native[:,:2],axis=1).max()),relative_to_pixel_max_error_px=rel_error,camera=rt['camera']['camera'],fov_argument=1.2870022175865687,screen=[1920,1080],capture_baseline=checks,limits=['Native screen positions are clamped at the viewport boundaries; excluded from focal fitting.','Projection confirmation does not identify the material causing dry-land shimmer.'])
(B/'native-projection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['camera','capture_baseline']},indent=2))
