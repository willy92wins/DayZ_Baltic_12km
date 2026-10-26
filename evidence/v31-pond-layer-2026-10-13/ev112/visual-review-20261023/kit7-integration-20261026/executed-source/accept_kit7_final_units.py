"""Adjudicate the final read-only review; freeze each unit only when inputs exist."""
from pathlib import Path
import json,hashlib,sys
R=Path(__file__).parent;V=R/'kit7-pilot-v2-review-20261026'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
mode=sys.argv[1];assert mode in ['pilot','world']
review=read(V/'review-response.json');done=read(V/'completion.json');assert done['exit_code']==0 and done['inputs_unchanged'] and not review['is_error'] and 'claude-fable-5-1' in review['modelUsage'] and 'SOUND-with-fixes' in review['result']
assert read(R/'kit7-config-v2-controls.json')['status']=='PASS_REAL_CONFIG_CONTROLS'
frozen=read(R/'kit7-package-review-20261026/accepted.json')['inputs'];assert all(sha(p)==h for p,h in frozen.items())
paths=[R/n for n in ['package_kit7_fc_pilot_v2.py','test_kit7_config_v2.py','kit7-config-v2-controls.json','accept_kit7_final_units.py','river-131-midpoint-c/author-report.json']]
paths += [W/'plans/ev112-kit7-config-registration-amendment-20261026.md']
out=V/'accepted.json';status='ACCEPTED_PILOT_COMPOSITION_ONLY'
if mode=='world':
 O=R/'package-kit7-fc-pilot-v2-20261026';vr=read(O/'verification.json');assert vr['status']=='PASS_201_MODELS_BYTE_EXACT_CONFIG_EXTENDED' and sha(O/'Addons/baltic_stream_pilot.pbo')==vr['pbo_sha256']
 assert read(R/'kit7-context-unit-20261026/result.json')['status']=='PASS_CONTEXT_GATES_BOUNDARY_PENDING'
 paths += [R/n for n in ['package_kit7_fc_world.py','prepare_kit7_world_compile.py','run_kit7_world_unit.py','stage-kit7-fc-20261026/baseline-config.cpp','kit7-road-mesh-20261026.json','kit7-context-unit-20261026/result.json','package-rectangle-f/Addons/narva_trial.pbo','package-kit7-fc-pilot-v2-20261026/verification.json','package-kit7-fc-pilot-v2-20261026/Addons/baltic_stream_pilot.pbo','kit7-pilot-v2-review-20261026/accepted.json']]
 paths += [W/'tools'/n for n in ['terrain/compile_visual_pilot_ev112.ps1','terrain/package_visual_forest_ev112.py','navigation/waterway_common.py']]
 paths += [Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/AddonBuilder/AddonBuilder.exe'),Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/packages/baltic-road-v29/tools/include.lst')]
 paths += list((O/'compiled/baltic_stream_pilot').glob('*'))
 out=R/'kit7-world-review-20261026/accepted.json';status='ACCEPTED_TECHNICAL_WORLD_ONLY'
assert all(p.is_file() for p in paths)
frozen.update({str(p):sha(p) for p in paths})
gate=dict(status=status,inputs=frozen,review_sha256=sha(V/'review-response.json'),fixes=['Frozen exact27old/35missinglegacy/139new config contract, positiveand5negativeactualcfgcontrols.','World required manifest expanded and compiled config byte-exact toF.','TEMP dependency every file compared to actualpackedPBO before/aftercopy and before/aftercompile.','FileBank/CfgConvert timeout writes receipt; failedoutputkept.','Both final review findings and source/forest/roads accepted independently.'],water='Pond plane/field/visible exactF under canonicalmerge,0burychanges; newcustomwater is in139ODOLpilotentries. No nativewaterclaim.',limits=['No deployment, engine heights/collision/navigation/visual acceptance.3727boundarydiscsremainpending.'])
assert not out.exists();out.write_text(json.dumps(gate,indent=2)+'\n',encoding='utf-8');print(status,len(frozen))
