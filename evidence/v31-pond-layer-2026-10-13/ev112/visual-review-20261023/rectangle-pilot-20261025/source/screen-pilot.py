from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/quality'),str(W/'tools/terrain')]
from screen_shapes_ev112 import terrain_screen
tp=R/'rectangle-pilot-f-merged/terrain-buried.npz';fp=R/'rectangle-pilot-f-merged/bury-work/fp0/footprint.npz'
screen,_=terrain_screen(tp,fp)
screen['inputs']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (tp,fp)}
(R/'rectangle-pilot-f/shape-screen.json').write_text(json.dumps(screen,indent=2)+'\n',encoding='utf-8')
print(json.dumps(screen['finding_counts']))
e=np.load(R/'guarded-relief-batch-e-merged/terrain-buried.npz')['heights'];t=np.load(R/'combined-merged/terrain-buried.npz')['heights'];f=np.load(tp)['heights']
assert np.array_equal(f[e!=t],e[e!=t]);print('All prior D/E changed vertices exact')
