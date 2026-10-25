from pathlib import Path
import sys,importlib.util,json,hashlib,time
import numpy as np
B=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
R=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev')
V=Path('E:/DayZ-Baltic-Build/v30-v11')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=W/'tools/terrain/build_v30_water.py';lines=source.read_text().splitlines();cut=[i+1 for i,line in enumerate(lines) if line.strip()=='cls[keep_ground] = 0'];assert len(cut)==1
captured={}
def instrument(frame,event,arg):
 if Path(frame.f_code.co_filename)!=source:return None
 if event=='line' and frame.f_lineno==cut[0]:
  data=frame.f_locals
  assert not captured
  for key in ('cls','level','keep_ground','near_road','v29_dry','zone'):captured[key]=data[key].copy()
 return instrument
args=[str(source),str(V/'design'),str(B/'replayed'),'--border-margin','60','--drop-border-water-km2','0.05','--border-keep-m','45','--contour',str(V/'design/contour_lakes.geojson'),'--round-river-ends','30']
assert not (B/'replay.json').exists()
(B/'replayed').mkdir(exist_ok=False)
sys.argv=args;sys.path.insert(0,str(source.parent));spec=importlib.util.spec_from_file_location('replayed_builder',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
start=time.monotonic();sys.settrace(instrument)
try:module.main()
finally:sys.settrace(None)
assert captured
np.savez_compressed(B/'before-road-cut.npz',**captured)
original=dict(np.load(V/'terrain_v30/water_v30.npz'));result=dict(np.load(B/'replayed/water_v30.npz'));assert set(original)==set(result)
parity={key:bool(np.array_equal(original[key],result[key],equal_nan=True)) for key in original}
removed=captured['keep_ground'];counts=dict(removed_vertices=int(removed.sum()),all_previously_water=bool(np.all(captured['cls'][removed]>0)),all_originally_dry=bool(np.all(captured['v29_dry'][removed])),classes={str(key):int(np.sum(captured['cls'][removed]==key)) for key in np.unique(captured['cls'][removed])})
inputs=[source,W/'tools/terrain/v30_common.py',W/'tools/terrain/verify_roads_v30.py',W/'evidence/v30-v11-candidate-2026-10-06/scripts/chain_v11.sh',V/'design/water_v3.geojson',V/'design/streams_candidates.geojson',V/'design/profiles.npz',V/'design/contour_lakes.geojson',V/'terrain_v30/water_v30.npz',R/'tests/regional_outline_smoothing_v33/reference.npz',R/'tests/regional_road_network_v29/baltic_road_network_v29.asc',R/'tests/regional_foundation_roads_v6/reference.npz',R/'evidence/regional-foundation-v1/road-grade-chains-v6.json']
report=dict(status='EXACT_BUILDER_REPLAY' if all(parity.values()) else 'REPLAY_DIVERGES_DO_NOT_ATTRIBUTE',arrays=parity,cut_line=cut[0],counts=counts,seconds=time.monotonic()-start,arguments=args,inputs={str(p):sha(p) for p in inputs})
(B/'replay.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({key:value for key,value in report.items() if key not in ['inputs','arguments']},indent=2))
assert all(parity.values()),'Cannot attribute historical cuts unless exact builder output reproduced'
