from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/terrain')]
import continuous_stream_pilot_v31 as C
base=R/'rectangle-pilot-f-merged';out=R/'river79-bounds-on-f'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Captured(Exception):pass
def probe(initial,prior,free,floor,ceiling):
    np.savez_compressed(out/'bounds.npz',initial=initial,prior=prior,free=free,floor=floor,ceiling=ceiling)
    # The actual author uses ceiling = W-.85 in the wet support.
    conflict=free&(floor>ceiling)
    rows=[dict(local_rc=[int(r),int(c)],initial=float(initial[r,c]),floor=float(floor[r,c]),ceiling=float(ceiling[r,c]),water=float(ceiling[r,c]+.85),nominal_centre_bed=float(ceiling[r,c]+.20),shortfall=float(floor[r,c]-ceiling[r,c])) for r,c in np.argwhere(conflict)]
    report=dict(status='DIAGNOSTIC_ONLY_NO_CANDIDATE',conflicts=len(rows),max_shortfall_m=max((r['shortfall'] for r in rows),default=0),rows=rows,source_sha256=sha(Path(C.__file__)),terrain_sha256=sha(base/'terrain-buried.npz'),footprint_sha256=sha(base/'bury-work/fp0/footprint.npz'),limits=['Captured author inputs before solving, geometry or terrain output.','Nominal centre bed assumes full-depth cross-section; end caps and exact triangle support must be inspected before any change.'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2));raise Captured()
assert sha(base/'terrain-buried.npz')=='caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc'
C.fair_support=probe
sys.argv=[str(C.__file__),str(B),str(out),'--sites','79.0-0','--candidate-base',str(base),'--expected-terrain-sha256',sha(base/'terrain-buried.npz'),'--expected-footprint-sha256',sha(base/'bury-work/fp0/footprint.npz')]
try:C.main()
except Captured:pass
else:raise AssertionError('Expected first solve was not captured')
