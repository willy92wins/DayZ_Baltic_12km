"""Read-only empirical vertex-prefix investigation; not a topology decoder."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
R=Path(__file__).parent;O=R/'kit7-nav-tile-diagnostic-20261026';O.mkdir(exist_ok=False)
path=R/'navmesh-kit7-v9-20261026/baltic_trial.nm';data=path.read_bytes()
assert hashlib.sha256(data).hexdigest()=='13e1ab1567740aca2ff94d6607b6f2c6423b9142674878562bf477994597f80b'
_,version,count,nx,nz=struct.unpack_from('<5I',data);assert (version,nx,nz)==(9,983,983)
offsets=struct.unpack_from(f'<{count}I',data,48);base=48+4*count
samples=json.loads((R/'kit7-nav-height-diagnostic-20261026/result.json').read_text())['samples']
targets={(int(s['nav'][0]//12.5),int(s['nav'][2]//12.5)) for s in samples}
rows=[]
for i,off in enumerate(offsets):
    h=base+off+16;ints=struct.unpack_from('<15I',data,h)
    if ints[2:4] not in targets:continue
    end=base+offsets[i+1] if i+1<count else len(data)
    floats=struct.unpack_from('<10f',data,h+60);candidates=[]
    for skip in range(100,161,4):
        v=np.frombuffer(data,dtype='<f4',count=ints[7]*3,offset=h+skip).reshape(-1,3).astype(float)
        if len(v) and np.isfinite(v).all() and np.all(v>=np.array(floats[3:6])-.01) and np.all(v<=np.array(floats[6:9])+.01):
            candidates.append(dict(offset_from_header=skip,vertices=v.tolist()))
    (O/f'tile-{ints[2]}-{ints[3]}.bin').write_bytes(data[h:end])
    rows.append(dict(tile=list(ints[2:4]),header_integers=ints,header_floats=floats,bytes=end-h,plausible_vertex_prefixes=candidates))
assert len(rows)==len(targets)
out=dict(status='READ_ONLY_EMPIRICAL_DISCOVERY',tiles=rows,source_sha256=hashlib.sha256(data).hexdigest(),limits='Plausible vertex offsets based on bounds only. No full layout, polygon topology, engine algorithm or acceptance claim.')
(O/'result.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
