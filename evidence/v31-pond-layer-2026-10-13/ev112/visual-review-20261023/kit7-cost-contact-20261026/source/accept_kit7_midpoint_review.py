from pathlib import Path
import json,hashlib,sys
R=Path(__file__).parent;O=R/'kit7-midpoint-review';W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
import py3d,compact_stream_collision_v31 as packing,midpoint_stream_collision_v31 as midpoint
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
review=json.loads((O/'review-response.json').read_text());complete=json.loads((O/'completion.json').read_text());controls=json.loads((O/'guard-controls.json').read_text())
assert complete['exit_code']==0 and complete['inputs_unchanged'] and not review.get('is_error') and review['result'].startswith('**Verdict: SOUND-with-fixes.')
assert controls['source_sha256']==sha(R/'author_kit7_midpoint_collision.py') and all(c['passed'] for c in controls['cases'])
original=R/'river-kit7-a-on-f-20261026';author=json.loads((original/'author-report.json').read_text())
files=[R/'author_kit7_midpoint_collision.py',R/'run_kit7_midpoint_author.py',R/'kit7-collision-baseline-20261026/result.json',original/'author-report.json',W/'plans/ev112-kit7-collision-budget-20261026.md',Path(packing.__file__),Path(midpoint.__file__),Path(py3d.__file__),W/'tools/water/review_compact_collision_v31.py',W/'tools/water/collision_contact_union_v31.py',W/'tools/water/mesh_quality_v31.py',O/'review-response.json',O/'completion.json',O/'guard-controls.json',R/'test_kit7_author_guards.py',Path(__file__)]
files+=sorted(Path(py3d.__file__).parent.rglob('*.py'))
files+=[original/n for n in ['terrain.npz','envelope.npy','cover.npy','kit-7-surfaces.npz']]
files+=[original/'source/baltic_stream_pilot'/n for n in ['config.cpp','$PBOPREFIX$']]
for inst in author['instances']:
 p=original/'source'/inst['model'].replace('\\','/');assert sha(p)==inst['sha256'];files.append(p)
inputs={str(p):sha(p) for p in files}
result=dict(status='ACCEPTED_FOR_ONE_AUTHOR',review_model='claude-fable-5-1',inputs=inputs,fixes=['Require complete input binding, not an empty/truncated map.','Classify visual/geometry LOD by verified py3d.classify_lod_resolution.','Check actual bed face count and unordered triangle triples against reconstructed grid, plus original prism count.','Clarify inherited metadata and separate aggregate nonincrease from strict component decrease.'],controls='Six real-model/binding cases: positive, missing face, opposite diagonal, wrongLOD, complete/empty binding.',limits=['Wrapper enforces1800s, permodel60s/20000states, one numericalthread and below-normal priority.','Missing author/packing report or timeout is INCONCLUSIVE; never partial acceptance.','Independent savedcost/full-overlay and compiled/native gates pending.'])
out=O/'accepted.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],frozen_inputs=len(inputs))))
