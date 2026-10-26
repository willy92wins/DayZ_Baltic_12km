"""Read only: stop the real author before its first solve; emit no terrain or meshes."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/terrain')]
import continuous_stream_pilot_v31 as C
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
p=argparse.ArgumentParser();p.add_argument('--site',choices=['kit-7','10.0-0','38.0-0'],required=True);args=p.parse_args()
base=R/'rectangle-pilot-f-merged';out=R/('river-bounds-next-20261026')/args.site
inputs={str(base/'terrain-buried.npz'):'caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc',str(base/'bury-work/fp0/footprint.npz'):'95f7a26304e88c726679ec69ef076bb149ec1f1f8bdf4a6cd1e83e40f3b6be83',str(Path(C.__file__)):'8b340a2ab4e25d69ff9baf46f71c8f843c9da2c02137c32fa356a0bb9deb9169'}
for path,d in inputs.items():assert sha(path)==d,path
class Captured(Exception):pass
captured=False
def probe(initial,prior,free,floor,ceiling):
 global captured
 captured=True
 np.savez_compressed(out/'bounds.npz',initial=initial,prior=prior,free=free,floor=floor,ceiling=ceiling)
 conflict=free&(floor>ceiling)
 rows=[dict(local_rc=[int(r),int(c)],initial=float(initial[r,c]),floor=float(floor[r,c]),ceiling=float(ceiling[r,c]),shortfall=float(floor[r,c]-ceiling[r,c])) for r,c in np.argwhere(conflict)]
 report=dict(status='DIAGNOSTIC_ONLY_NO_CANDIDATE',site=args.site,conflicts=len(rows),free_vertices=int(free.sum()),max_shortfall_m=max((r['shortfall'] for r in rows),default=0.),rows=rows,inputs=inputs,limits=['Real author inputs captured before the first solve; no terrain or mesh output.','No conflict does not prove coupled solve, curvature, water, endpoints, collision or runtime.'])
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 raise Captured()
C.fair_support=probe
sys.argv=[str(C.__file__),str(B),str(out),'--sites',args.site,'--candidate-base',str(base),'--expected-terrain-sha256',inputs[str(base/'terrain-buried.npz')],'--expected-footprint-sha256',inputs[str(base/'bury-work/fp0/footprint.npz')]]
try:C.main()
except Captured:pass
except (AssertionError,ValueError) as exc:
 if captured:raise
 report=dict(status='AUTHOR_PRE_SOLVE_REJECTED',site=args.site,error=str(exc),inputs=inputs,limits=['No solver or geometry was run.'])
 out.mkdir(parents=True,exist_ok=True)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
else:raise AssertionError('Expected no author completion')
for path,d in inputs.items():assert sha(path)==d,path
assert not list(out.rglob('*.p3d')) and not (out/'terrain.npz').exists()
result=json.loads((out/'report.json').read_text())
print(json.dumps({k:v for k,v in result.items() if k not in ('rows','inputs')},indent=2))

