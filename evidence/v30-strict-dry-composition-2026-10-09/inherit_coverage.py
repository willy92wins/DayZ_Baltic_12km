from pathlib import Path
import sys,json,hashlib
import numpy as np
B=Path(__file__).parent;R=B.parent;OLD=R/'v30-volkhov-stable-derivatives-20261009'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');sys.path.insert(0,str(W/'tools/terrain'))
from wrp0wzd import read
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
path=Path('package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp');a,b=read(OLD/path),read(B/path)
reference=json.loads((OLD/'compiled-coverage.json').read_text());assert reference['status']=='PASS_GLOBAL_COMPILED_COVERAGE';assert sha(OLD/path)==reference['world_source_sha256']
h=np.load(OLD/'candidate/terrain.npz')['heights'];v=np.load(B/'candidate/terrain.npz')['heights'];assert sha(OLD/'candidate/terrain.npz')==reference['terrain_sha256'];assert np.array_equal(v[::-1],b['heights'])
p=np.load(B/'candidate/plane.npy');support=np.zeros(h.shape,bool)
for dr,dc in [(0,0),(0,1),(1,0),(1,1)]:support[dr:dr+2047,dc:dc+2047]|=np.isfinite(p)
gates=dict(all_water_cell_heights_exact=np.array_equal(h[support],v[support]),all_object_records_exact=[o['bytes'] for o in a['objects']]==[o['bytes'] for o in b['objects']],plane_bytes_exact=sha(OLD/'candidate/plane.npy')==sha(B/'candidate/plane.npy'),visible_field_bytes_exact=sha(OLD/'candidate/visible-field.npy')==sha(B/'candidate/visible-field.npy'),water_package_bytes_exact=sha(Path('P:/Mods/@DayZ_Baltic_TerminalSmoothV1/Addons/baltic_water_v30.pbo'))==reference['water_sha256'])
assert all(gates.values()),gates
report=dict(status='PASS_INHERITED_COMPILED_COVERAGE',gates=gates,source_coverage_sha256=sha(OLD/'compiled-coverage.json'),terrain_sha256=sha(B/'candidate/terrain.npz'),world_source_sha256=sha(B/path),cells=reference['cells'],instances=reference['instances'],models=reference['models'],water_sha256=reference['water_sha256'],uncovered_physical_m2=reference['uncovered_physical_m2'],uncovered_visible_footprint_m2=reference['uncovered_visible_footprint_m2'],water_support_vertices=int(support.sum()),limits=['Coverage inherited only after exact equality of all inputs that determine wet footprints.','Native compiled world and rendered surface still require consumer checks.'])
(B/'compiled-coverage.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
