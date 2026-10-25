from pathlib import Path
import json,numpy as np
R=Path(__file__).parent;B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
old=np.load(B/'road-merged-20261024-h/terrain-buried.npz');new=np.load(R/'road-candidate-s3/terrain.npz');m=old['heights']!=new['heights']
print(json.dumps({k:int((m&old[k]).sum()) for k in old.files if old[k].dtype==bool and old[k].shape==m.shape},indent=2))
f=json.loads((R/'forest-s3.json').read_text());r=json.loads((R/'candidate-r/forest-staged-g5-g4.json').read_text())
print(json.dumps(dict(boundary_count=f['boundary_pending']['count'],unchanged_boundary_ids=f['boundary_pending']['ids']==r['boundary_pending']['ids'])))
z=np.load(B/'water-fix-b/terrain.npz')
kit=json.loads((B/'water-fix-b/kit/kit-report.json').read_text())
site=next(s for s in kit['sites'] if s.get('site')=='kit-118')
print('kit keys',list(site))
