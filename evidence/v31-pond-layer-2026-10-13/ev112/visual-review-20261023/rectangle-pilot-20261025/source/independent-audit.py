from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
source=(R/'audit_guarded_all_e.py').read_text(encoding='utf-8')
source=source.replace("tp=R/'combined-merged/terrain-buried.npz';cp=R/'guarded-relief-batch-e/terrain.npz'","tp=R/'guarded-relief-batch-e-merged/terrain-buried.npz';cp=R/'rectangle-pilot-f/terrain.npz'")
source=source.replace("R/'combined-merged/envelope.npy'","R/'guarded-relief-batch-e-merged/envelope.npy'").replace("R/'combined-merged/bury-work/fp0/footprint.npz'","R/'guarded-relief-batch-e-merged/bury-work/fp0/footprint.npz'").replace("R/'guarded-relief-discovery/domains.npz'","R/'guarded-relief-batch-e/domains.npz'").replace("R/'guarded-relief-batch-e/all-protected-audit.json'","R/'rectangle-pilot-f/all-protected-audit.json'")
source=source.replace("assert all(provenance.values())", """delta={key:int(np.count_nonzero(value!=stored[key])) for key,value in [('free',free),('shore',shore),('road',road)]}
changed_outside_current_free=int(((v!=h)&~free).sum())
np.savez_compressed(R/'rectangle-pilot-f/rederived-domains.npz',free=free,shore=shore,road=road)
(R/'rectangle-pilot-f/domain-comparison.json').write_text(json.dumps(dict(equal=provenance,different_vertices=delta,changed_outside_current_free=changed_outside_current_free),indent=2)+'\\n')
""")
source=source.replace("status='PASS' if not any(x['violations'] for x in checks) else 'FAIL'", "status='PASS' if not any(x['violations'] for x in checks) and changed_outside_current_free==0 and provenance['shore'] and provenance['road'] else 'FAIL'")
source=source.replace("affected_protected_extrema=len(checks)","changed_outside_current_free=changed_outside_current_free,domain_differences=delta,affected_protected_extrema=len(checks)")
exec(compile(source,str(__file__),'exec'))
