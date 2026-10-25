"""Independent analytic one-triangle pond-over-dry-land fixture for the global auditor."""
from pathlib import Path
import tempfile,json,sys,hashlib
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09';sys.path.insert(0,str(W/'tools/terrain'))
from audit_water_risk_v30 import pond_risks
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/pond-consumer-fixture');B.mkdir(exist_ok=False)
cls=np.zeros((2048,2048),np.uint8);cls[11,10]=7
level=np.full((2048,2048),np.nan,np.float32);level[11,10]=2
h=np.full((2048,2048),3.,np.float32);h[10,11]=1
terrain=dict(heights=h,cls=cls,**{k:np.zeros_like(cls,dtype=bool) for k in ('reserve','platform','beach')})
src=B/'water.npz';np.savez_compressed(src,cls=cls,level=level)
manifest=B/'manifest.json';manifest.write_text('{"sea_cutoff_m":0.51}')
sha=hashlib.sha256(src.read_bytes()).hexdigest()
positive=pond_risks(terrain,src,sha,manifest,B)
assert positive['nominally_submerged_dry_vertices']==1
# Opposite corner is water, so the entirely dry triangle has depths -1,+1,-1: area 18/4.
assert positive['fully_dry_faces_with_pond_area']==1 and abs(positive['pond_area_on_fully_dry_faces_m2']-4.5)<.0001
h[10,11]=3
after=B/'fixed';after.mkdir();negative=pond_risks(terrain,src,sha,manifest,after)
assert negative['nominally_submerged_dry_vertices']==0 and negative['pond_area_on_fully_dry_faces_m2']==0
try:pond_risks(terrain,src,'0'*64,manifest,after)
except ValueError:wrong_hash=True
else:wrong_hash=False
assert wrong_hash
report=dict(status='PASS_ANALYTIC_POND_CONSUMER',one_dry_vertex=1,expected_dry_face_area_m2=4.5,measured_area_m2=positive['pond_area_on_fully_dry_faces_m2'],raised_vertex_removes_risk=True,wrong_source_hash_rejected=wrong_hash)
(E/'pond-risk-consumer-controls.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
