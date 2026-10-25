"""Read-only native WRP tile assignment check for the current Baltic layout."""
from pathlib import Path
import struct,re,json,hashlib
import numpy as np
repo=Path('P:/DayZ_Baltic_12km_dev')
p=repo/'tb/narva_trial/baltic_water_reopened_v1.wrp'; b=p.read_bytes()
magic,tx,tz,nx,nz,cell=struct.unpack_from('<4s4If',b)
assert (magic,tx,tz,nx,nz,cell)==(b'0WZD',1024,1024,2048,2048,12.0)
o=24+nx*nz*4
ind=np.frombuffer(b,dtype='<u2',count=tx*tz,offset=o).reshape(tz,tx);o+=tx*tz*2
n=struct.unpack_from('<I',b,o)[0];o+=4
mats=[]
for _ in range(n):
    names=[]
    while True:
        size=struct.unpack_from('<I',b,o)[0];o+=4
        if size==0:break
        names.append(b[o:o+size].decode('ascii').rstrip('\0'));o+=size
    mats.append(names)
coord=np.zeros((n,2),int)
assert ind.min()>0 and ind.max()<n
for i,ms in enumerate(mats):
    if i==0:continue
    assert len(ms)==1
    found=re.search(r'p_(\d+)-(\d+)',ms[0],re.I)
    coord[i]=[int(found[1]),int(found[2])]
    material=(repo/'tb/narva_trial/data/layers'/ms[0].split('\\')[-1]).read_text()
    sat=re.search(r'class Stage0\s*\{\s*texture="[^"]*s_(\d+)_(\d+)_lco.png"',material,re.I)
    assert sat and [int(sat[1]),int(sat[2])]==coord[i].tolist()
# 512 px * 6 m/px, with 16 px actual overlap. Invariant from the saved frame
# and material transform scale=1/3072; this check does not emulate GPU rendering.
zz,xx=np.mgrid[:tz,:tx]
expected=np.stack((np.floor((xx*cell+cell/2)/2976),np.floor((12288-zz*cell-cell/2)/2976)),axis=-1)
bad=np.any(coord[ind]!=expected,axis=-1)
r={'status':'PASS_NATIVE_TILE_ASSIGNMENT' if not bad.any() else 'FAIL',
   'wrp_sha256':hashlib.sha256(b).hexdigest(),'cells':int(bad.size),
   'wrong_sat_tile_assignments':int(bad.sum()),'materials':n-1,
   'texture_grid':[tx,tz],'texture_cell_m':cell,
   'limit':'Native WRP plus source Stage0 correspondence only, not compiled LOD or rendered output.'}
(repo/'evidence/render-distance/native-tile-assignment.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
raise SystemExit(0 if not bad.any() else 1)
