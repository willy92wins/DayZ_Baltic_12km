"""Close actual OT7 R1, preserving raw review and post-review provenance limits."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
raw=O/'review-build-ae-r1.json';review=read(raw.name);run=read('review-build-ae-r1-run.json');deploy=read('deploy.json')
assert run['rc']==0 and review['is_error'] is False
assert review['result'].startswith('## Veredicto: SOUND-with-fixes.')
assert 'No hay hallazgos mayores abiertos que bloqueen la sonda' in review['result']
assert run['binding']['deploy_sha256']==sha(O/'deploy.json')
for key in ('world_sha256','water_sha256','terrain_sha256','footprint_sha256','compiled_wrp_sha256','forest_records_sha256'):
 assert run['binding'][key]==deploy[key]
assert sha(Path(deploy['mod'])/'Addons/narva_trial.pbo')==deploy['world_sha256']
assert sha(Path(deploy['mod'])/'Addons/baltic_water_v30.pbo')==deploy['water_sha256']
assert sha(O/'review-build-ae-r1-prompt.md')==run['prompt_sha256']
mechanical=read('forest-review-closure-ae.json');assert mechanical['verdict']=='MECHANICAL_PASS'
assert all(sha(path)==h for path,h in mechanical['conditions']['promoted'].items())
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=P,text=True).strip()
assert commit=='845295f7b9b0a3ea225ba675755f34efa67a548b'
files=['tools/terrain/patch_surface_v31.py','tools/vegetation/forest_v31.py','tools/vegetation/make_forest_clearings_v31.py','tools/vegetation/streambed_water_v31.py']
committed={}
for name in files:
 blob=subprocess.check_output(['git','show',commit+':'+name],cwd=P)
 assert blob.replace(b'\r\n',b'\n')==(P/name).read_bytes().replace(b'\r\n',b'\n')
 committed[name]=dict(working_sha256=sha(P/name),git_blob_sha256=hashlib.sha256(blob).hexdigest(),equal_after_CRLF_normalization=True)
prov=read('build-review-ae-provenance/provenance.json');assert prov['status']=='MEASURED_POST_REVIEW'
for row in prov['dependencies']:assert sha(row['path'])==sha(row['snapshot'])==row['sha256']
evidence={str(path):sha(path) for path in [raw,O/'review-build-ae-r1-run.json',O/'review-build-ae-r1-binding.json',O/'review-build-ae-r1-prompt.md',O/'forest-review-closure-ae.json',O/'build-review-ae-provenance/provenance.json',O/'forest-ae-control-domain-boundary.json',O/'runtime-preflight-ae.json']}
result=dict(verdict='SOUND-with-fixes',critical_major_open=0,review_round=1,maximum_rounds=2,
 time_utc=datetime.now(timezone.utc).isoformat(),raw_review=str(raw),raw_review_sha256=sha(raw),
 world_sha256=deploy['world_sha256'],water_sha256=deploy['water_sha256'],source_commit=commit,committed_sources=committed,
 review_scope='Independent Claude OT7 review of the actual deployed final build and complete post-S source delta. Read-only review; reviewer did not recalculate hashes or execute tests. Executor rechecked bindings and deployed hashes at closure.',
 minor_responses={
 'staging_and_include_provenance':'Current imported wrp0wzd and include.lst are copied and hashed in build-review-ae-provenance. wrp0wzd exactly matches frozen O/terrain. This is a post-build inventory, not a reconstructed build-time attestation; the historical limitation remains explicit.',
 'promoted_sources_and_patch_hash':'Four production files committed in '+commit+'. Patch hash was already in mechanical conditions.promoted; it is now also explicit in this receipt and the dependency snapshot.',
 'g8_wording':'PASS without per-window exemptions; original structural exclusions for Narva, kit hulls and bridge areas are retained and separately reported. The original mechanical receipt is preserved unchanged; this statement qualifies its abbreviated wording.',
 'live_helpers':'Actual verify_roads_v30 and patch_surface/pbo_index import paths and bytes are copied and hashed. verify_roads matches prior HEAD after CRLF normalization; patch_surface exactly matches the frozen copy. No claim of contemporaneous import-time measurement.'},
 acceptance_limits=[
 'Compiled object readback covers all objects. Compiled terrain heights were not decoded; server sampling is pending.',
 'Global G2/G3 use fixed aggregate/per-metric rules; regional 5/19 failure remains FAIL and is a personal-view target.',
 'G9 C compares 243157 objects20m inside region, all identical. Three diagnostic reed A rows remain FAIL, outside statistical A acceptance by the frozen consumer.',
 '124 WRP translations outside [0,12288) are absent from distribution mutations. Main gates receive the full JSON but retain their spatial filters; no universal gate coverage or engine-boundary acceptance is inferred.',
 '015-45 protected60m remains pending. OT4 .03m bound concerns the accepted central domain only; original outer metrics and superseded historical G7 failures remain visible.',
 'Plan section5 was read by executor: known vanilla concrete-joint water cuts are nonblocking pending work, never a PASS. Actual G8 and all raw runtime failures must still be reported and investigated by cause.',
 'Personal view and FPS remain pending. No runtime acceptance is granted by this review.'
 ],evidence=evidence,ready_for_server_probe=True,server_probe='NOT_RUN',personal_view='PREPARED_NOT_ACCEPTED')
out=O/'build-review-closure-ae.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
print('OT7 SOUND-with-fixes;0 critical/major; sources committed; ready for server probe',out)
