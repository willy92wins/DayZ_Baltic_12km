from pathlib import Path
import json,shutil,importlib.util,time
import numpy as np
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'dry-bed-road-mutants-20261028';O.mkdir(exist_ok=False);source=R/'dry-bed-road-candidate-20261028'
sp=importlib.util.spec_from_file_location('consumer',R/'verify_dry_bed_road_candidate_20261028.py');c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
sp=importlib.util.spec_from_file_location('meter',W/'tools/quality/water_constraint_diagnostic_ev112.py');meter=importlib.util.module_from_spec(sp);sp.loader.exec_module(meter);meter.MAX_SECONDS=600;stop=meter.bounded(O)
cases=[('omit_seed','selection_mismatch'),('move_XZ','XZ_or_raised'),('move_fixed_water_support','fixed_point_changed'),('forge_free_mask','free_or_wet_mismatch'),('omit_water_layer','water_inventory_omitted'),('restore_road_obstacle','corridor_still_exposed')];results=[]
try:
 for name,expected in cases:
  raw=O/name;shutil.copytree(source,raw);result=O/(name+'-consumer');result.mkdir()
  inp=c.nz(raw/'kit-118-inputs.npz');candidate=c.nz(raw/'kit-118-candidate.npz');grid=candidate['grid'].reshape(-1,3);baseline=inp['grid'].reshape(-1,3)
  if name=='omit_seed':
   rows=json.loads((raw/'selection.json').read_bytes());next(x for x in rows if x['seed_faces'])['seed_faces']-=1;(raw/'selection.json').write_text(json.dumps(rows))
  elif name=='move_XZ':grid[0,0]+=1/512
  elif name=='move_fixed_water_support':
   vertex=int(inp['triangles'][inp['wet_faces'][0],0]);grid[vertex,1]-=1/512
  elif name=='forge_free_mask':inp['free'][0]=not inp['free'][0]
  elif name=='omit_water_layer':inp['water_refs']=inp['water_refs'][1:]
  elif name=='restore_road_obstacle':
   grid[:]=baseline;vertex=np.flatnonzero(inp['free'])[-1];grid[vertex,1]-=1/512
  np.savez_compressed(raw/'kit-118-inputs.npz',**inp);np.savez_compressed(raw/'kit-118-candidate.npz',**candidate)
  begin=time.monotonic()
  try:c.verify(R,W,raw,result,meter)
  except ValueError as exc:
   actual=str(exc);assert actual==expected,(name,actual,expected);results.append(dict(case=name,rejected=True,reason=actual,seconds=time.monotonic()-begin))
  else:raise AssertionError('MUTANT_SURVIVED:'+name)
  meter.dump(O/'progress.json',results)
 meter.dump(O/'report.json',dict(status='ALL_SIX_MUTANTS_REJECTED',cases=results,measurement=meter.memory()));print(json.dumps(results))
finally:stop.set()
