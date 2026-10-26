"""Locate observed norm warnings without changing the reader or its results."""
from pathlib import Path
import hashlib,json,sys,warnings
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/playtest')]
from package_visual_forest_ev112 import source_arrays,compiled_arrays,compare
from attach_navmesh import read_pbo
O=R/'kit7-reader-warning-diagnosis.json';assert not O.exists()
v=json.loads((R/'package-kit7-fc-world-20261026/verification.json').read_text())
p=R/'package-kit7-fc-world-20261026/Addons/narva_trial.pbo'
assert hashlib.sha256(p.read_bytes()).hexdigest()==v['pbo_sha256']
_,_,entries=read_pbo(p);blob=entries['baltic_trial.wrp'];base=np.frombuffer(blob,np.uint8).ctypes.data
s=source_arrays(R/'stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp',2578398)
stage=json.loads((R/'stage-kit7-fc-20261026/stage-report.json').read_text())
s['forest_models']=set(json.loads(Path(stage['forest_reference']['path']).read_text())['models'])
anchor=dict(id=int(s['ids'][0]),name=s['names'][s['mi'][0]],matrix=s['mat'][0]);original=np.linalg.norm;events=[];bad_offsets=[]
def traced_norm(a,*args,**kwargs):
 with warnings.catch_warnings(record=True) as observed:
  warnings.simplefilter('always',RuntimeWarning);value=original(a,*args,**kwargs)
 if observed:
  assert np.shares_memory(a,np.frombuffer(blob,np.uint8))
  invalid=np.flatnonzero(~np.isfinite(value).all(axis=1));assert len(invalid)>0
  offsets=(a.ctypes.data-base-8+invalid*a.strides[0]).tolist();bad_offsets.extend(offsets)
  events.append(dict(messages=[str(w.message) for w in observed],invalid_norm_rows=len(invalid),first_record_byte=offsets[0],last_record_byte=offsets[-1]))
 return value
try:
 np.linalg.norm=traced_norm;c,reader=compiled_arrays(blob,anchor)
finally:np.linalg.norm=original
assert reader==v['reader'];lo,hi=reader['table']
assert events and all(not lo<=offset<hi for offset in bad_offsets)
assert np.isfinite(c['mat']).all()
parity=compare(s,c);assert parity['objects']==2578398 and parity['pilot_exact']==201
result=dict(status='WARNINGS_OUTSIDE_ACCEPTED_OBJECT_TABLE',events=events,accepted_table=reader['table'],accepted_matrices_all_finite=True,full_comparator_replay_pass=True,pbo_sha256=v['pbo_sha256'],reader_sha256=hashlib.sha256((W/'tools/terrain/package_visual_forest_ev112.py').read_bytes()).hexdigest(),limits=['Explains these numeric warnings while scanning adjacent binary bytes; does not certify the heuristic reader for other files or compiled heights.'])
O.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
