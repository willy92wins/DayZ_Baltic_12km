"""Read-only local comparison; no terrain candidate or modified solver."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water')]
from repair_free_shapes_ev112 import fair_native_patch
from continuous_stream_pilot_v31 import fair_energy
import census_pyramids_v31 as P
import census_creases_v31 as C
p=W/'tests/fixtures/feasible-witness-1171-190.npz'
z=np.load(p);f={k:z[k] for k in z.files};base=f['base']
try:
    h,receipt=fair_native_patch(**f,bound_witnesses=True,preserve_satisfied_witnesses=True)
    h=h.astype(np.float32).astype(float);pk,pt,*_=P.prominence(h);oldp,oldt,*_=P.prominence(base)
    a,b=C.angles(base),C.angles(h)
    result=dict(status='DIAGNOSTIC_LOCAL_SOLUTION',solver=receipt,target_m=float(pk[8,8]),
      pure_energy_before=float(fair_energy(base,f['prior'],0)[0]),pure_energy_after=float(fair_energy(h,f['prior'],0)[0]),
      checks=dict(target=bool(pk[8,8]<=.3),fixed=bool(np.array_equal(h[~f['free']],base[~f['free']])),bounds=bool(np.all(h>=f['floor']-2e-6) and np.all(h<=f['ceiling']+2e-6)),
                  prominence=bool(np.all(pk<=np.maximum(oldp,.3)+2e-6) and np.all(pt<=np.maximum(oldt,.3)+2e-6)),creases=all(np.all(b[k]<=np.maximum(a[k],20)+.01) for k in a)))
except ValueError as error:result=dict(status='SOLVER_FAILED',error=str(error))
result['fixture_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
result['scope']='Diagnostic only; no global candidate, water, roads, native or visual acceptance.'
o=R/'kit7-existing-hybrid-rebased-diagnostic.json';assert not o.exists();o.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
