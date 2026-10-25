from pathlib import Path
import hashlib,json,sys
import numpy as np
B=Path(__file__).parent;old=Path('E:/DayZ-Baltic-Build/v30-river-end-tapers-20261009')
source=Path('E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009/candidate-repaired/terrain.npz')
namespace={'__name__':'msta_independent_consumer'}
# Reuse the independent 1 m arc / +/-3 m consumer, not the optimizer objective.
code=(old/'check_msta_turns.py').read_text();exec(code[:code.index('before,after=turns(h),turns(v)')],namespace)
h=np.load(source)['heights'];v=np.load(B/'candidate/terrain.npz')['heights']
before,after=namespace['turns'](h),namespace['turns'](v)
a=namespace['a'];xmin,zmin,xmax,zmax=a['box']
rr=np.arange(2048);cc=np.arange(2048)
mask=((12282-6*rr[:,None]>=zmin-6)&(12282-6*rr[:,None]<=zmax+6)&(6*cc[None,:]>=xmin-6)&(6*cc[None,:]<=xmax+6))
assert np.array_equal(h[mask],v[mask]) and before==after
report=dict(status='UNCHANGED_MSTA_STILL_OPEN',before=before,after=after,box=a['box'],changed_vertices_in_box_and_halo=int(np.sum(h[mask]!=v[mask])),
 method='Independent native contour, 1 m arc samples, 3 m each side, x>=12186; exact EV11 consumer.',
 source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),candidate_sha256=hashlib.sha256((B/'candidate/terrain.npz').read_bytes()).hexdigest(),
 limits=['Rejected EV16 Msta proposal was not applied.','No claim that terminal taper or Msta shape target is complete.'])
(B/'msta-current.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
