"""Apply only the high navigable floor missed by tiny shore components."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/terrain'))
from v30_common import cell_planes,vertex_plane_bounds
SOURCE=Path('E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/wave-banks-r1/terrain_wave_banks.npz')
OUT=Path('E:/DayZ-Baltic-Build/v30-navigation-contract-20261008')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='b363b79dc8b4374a626644da78f110666139d382ee09a38dc7aade46b2e659dc'
t=dict(np.load(SOURCE));h=t['heights'].astype(float);r,c=np.indices(h.shape)
narva=np.hypot(c*6-2417.1428225906,12282-r*6-6889.8850822322)<=620
axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-v11/24/axes.json').read_text())
reach=np.zeros_like(narva)
for a in axes.values():
 for rr,cc in a['removed_cells']:reach[rr:rr+2,cc:cc+2]=True
target=(t['cls']==3)&(t['level']>=2)&(h<1)&~narva&~reach&(r>1)&(r<2046)&(c>1)&(c<2046)
assert target.sum()==2 and not np.any(target&(t['platform']|t['reserve']))
ids,n=label(np.isin(t['cls'],[3,5,6])&(t['level']>.8),structure=np.ones((3,3)))
sizes=np.bincount(ids.ravel());assert np.all(sizes[ids[target]]==1)
pmin,_=vertex_plane_bounds(cell_planes(t['cls'],t['level'],sea_cut=.51))
assert np.all(pmin[target]-1>.95), 'Not enough water above the chosen floor'
candidate=t['heights'].copy();candidate[target]=1
OUT.mkdir(exist_ok=False)
np.savez_compressed(OUT/'terrain_floor.npz',**dict(t,heights=candidate))
report=dict(status='CANDIDATE_PENDING_CONSUMERS',source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 output_sha256=hashlib.sha256((OUT/'terrain_floor.npz').read_bytes()).hexdigest(),
 changes=[dict(row=int(rr),col=int(cc),x=int(cc*6),z=int(12282-rr*6),before=float(h[rr,cc]),after=1.,
               level=float(t['level'][rr,cc]),component_vertices=int(sizes[ids[rr,cc]])) for rr,cc in zip(*np.nonzero(target))],
 source_mechanism='profile_inland_v30 skips size < min_vertices before setting profiled; the old floor required profiled.')
(OUT/'authoring.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=1))
