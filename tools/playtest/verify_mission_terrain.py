from pathlib import Path
import json, hashlib, argparse
import numpy as np
import rasterio
ap=argparse.ArgumentParser(description='Verify actual Baltic mission samples against the specified native ASC, not an obsolete observation.')
ap.add_argument('--log',type=Path,required=True)
ap.add_argument('--native',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args()
log=a.log; asc=a.native
text=log.read_text()
lines=text.splitlines()
assert lines[0]=='BALTIC_TRIAL_OBSERVER_V1' and lines[-1]=='BALTIC_TRIAL_OBSERVER_COMPLETE'
assert 'world=BalticTrial' in lines
shapes=[l.split('=',1)[1].replace('\\','/').lower() for l in lines if l.startswith('shape=')]
assert shapes.count('dz/structures/roads/bridges/bridge_metal_25.p3d')==1
assert not any('pond_50x50' in s for s in shapes)
def rows(prefix,ncols,count):
    a=np.array([[float(s) for s in l.split(';')[1:]] for l in lines if l.startswith(prefix+';')])
    assert a.shape==(count,ncols) and np.isfinite(a).all()
    return a
with rasterio.open(asc) as ds:
    h=ds.read(1)
assert h.shape==(2048,2048)
def sample(x,z):
    col=x/6; row=(12282-z)/6
    ci=np.floor(col).astype(int); ri=np.floor(row).astype(int)
    a=col-ci; b=row-ri
    return np.where(b<=a,h[ri,ci]*(1-a)+h[ri,ci+1]*(a-b)+h[ri+1,ci+1]*b,
        h[ri,ci]*(1-b)+h[ri+1,ci]*(b-a)+h[ri+1,ci+1]*a)
grid=rows('G',3,289); profile=rows('P',5,289); ends=rows('E',6,34)
assert set(map(tuple,grid[:,:2]))=={(2394+i*3,6864+j*3) for i in range(17) for j in range(17)}
assert np.array_equal(profile[:,0],np.arange(-144,145)*.25)
assert set(map(tuple,ends[:,:2]))=={(d,j*.5) for d in (-12.5,12.5) for j in range(-8,9)}
errs={'G':float(abs(sample(grid[:,0],grid[:,1])-grid[:,2]).max()),
      'P':float(abs(sample(2417.143+.988364361*profile[:,0],6889.885-.152104866*profile[:,0])-profile[:,3]).max()),
      'E':float(abs(sample(2417.143+.988364361*ends[:,0]-.152104866*ends[:,1],6889.885-.152104866*ends[:,0]-.988364361*ends[:,1])-ends[:,4]).max())}
bridge_ok=bool(np.max(abs(ends[:,4:]-2))<=.0051 and np.max(abs(profile[abs(profile[:,0])<=12.25,4]-2))<=.0051)
result={'status':'PASS_CURRENT_ASC' if max(errs.values())<=.0051 and bridge_ok else 'FAIL',
        'samples':612,'error_max_m':errs,'bridge_deck_and_landings_at_2m':bridge_ok,
        'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (log,asc)},
        'limit':'Surface queries at full terrain resolution do not verify distant rendering or traversal.'}
a.out.parent.mkdir(parents=True,exist_ok=True)
assert not a.out.exists(), 'Use a fresh evidence path'
a.out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['status']=='PASS_CURRENT_ASC' else 1)
