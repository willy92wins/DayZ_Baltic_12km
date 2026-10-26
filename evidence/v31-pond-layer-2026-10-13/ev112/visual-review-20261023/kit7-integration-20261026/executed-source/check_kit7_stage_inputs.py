"""Complete nonempty root binding for this one-shot source unit."""
from pathlib import Path
import hashlib,json
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def validate(gate,rehash=True):
 assert gate['status']=='ACCEPTED_SOURCE_COMPOSITION_ONLY'
 frozen={str(Path(p).resolve()):h for p,h in gate['inputs'].items()}
 required=[R/n for n in ['stage_kit7_fc.py','verify_kit7_fc_stage.py','check_kit7_stage_inputs.py','prepare_kit7_stage_review.py','run_kit7_source_unit.py','stage-rectangle-f/stage-report.json','stage-rectangle-f/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp','rectangle-pilot-f-merged/terrain-buried.npz','river-kit7-merged-byteexact-20261026/terrain-buried.npz','kit7-forest-impact-20261026/result.json','kit7-forest-impact-20261026/inputs.json','river-kit7-midpoint-a-20261026/records.json','collision-overlap-u2/author-report.json','river-131-midpoint-c/author-report.json','river-kit7-midpoint-a-20261026/author-report.json']]
 required += [B/'water-fix-b/kit/kit-records.json',B/'stage-nonforest-c/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp']
 required += [W/'tools'/n for n in ['vegetation/prune_visual_forest_v31.py','terrain/wrp0wzd.py','water/streambed_kit_v31.py','vegetation/review_visual_forest_support_v31.py']]
 assert {str(p.resolve()) for p in required}<=set(frozen),'incomplete root manifest'
 # Read metadata only after these roots are verified; mutable reports cannot redefine membership.
 for p in required:assert sha(p)==frozen[str(p.resolve())],str(p)
 meta=json.loads((R/'stage-rectangle-f/stage-report.json').read_text());ref=Path(meta['forest_reference']['path'])
 assert str(ref.resolve()) in frozen and frozen[str(ref.resolve())]==meta['forest_reference']['sha256']=='813081fa1ef4a8f2f442ebe2811fb2f435bc38b56c9d693477b3b525bfece26c'
 for d in ['collision-overlap-u2','river-131-midpoint-c','river-kit7-midpoint-a-20261026']:
  for inst in json.loads((R/d/'author-report.json').read_text())['instances']:
   p=R/d/'source'/inst['model'].replace('\\','/');assert frozen.get(str(p.resolve()))==inst['sha256']
 expected={'stage-rectangle-f/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp':'6e649b72bf4ec6789a83050f21b7e5597de417e14f251f854728eb20d8b84bd8','rectangle-pilot-f-merged/terrain-buried.npz':'caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc','river-kit7-merged-byteexact-20261026/terrain-buried.npz':'815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40','river-kit7-midpoint-a-20261026/records.json':'3979c1f9838e9acae9b75ebea9b3747926259e44de6dc6a56e310fbbe95faffe','river-kit7-midpoint-a-20261026/author-report.json':'16193c0c96a4b1d127d3706ff698ab928c8139fa534a926a9c61e1bf40320b58'}
 for n,h in expected.items():assert frozen[str((R/n).resolve())]==h
 if rehash:assert all(sha(p)==h for p,h in frozen.items()),'input drift'
 return frozen
