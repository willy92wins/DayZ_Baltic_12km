from pathlib import Path
import hashlib,json
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
inputs={}
def bind(p):
 p=Path(p);inputs[str(p)]=sha(p)
def validate(mapping):
 for p,h in mapping.items():
  assert sha(Path(p))==h,p
  inputs[p]=h
for name in ['kit7-contact-only-review-20261026','kit7-binary-comparator-review-20261026']:
 d=R/name;c=read(d/'completion.json');v=read(d/'review-response.json')
 assert c['exit_code']==0 and c['inputs_unchanged']
 assert not v['is_error'] and not v['permission_denials'] and v['terminal_reason']=='completed'
 validate(read(d/'source-hashes.json'))
 for f in ['completion.json','review-response.json','source-hashes.json','review-brief.md']:bind(d/f)
checks=[
 ('river-kit7-contact-only-20261026/binary-review.json','BINARY_PASS'),
 ('river-kit7-contact-only-20261026/compiled-contact-review.json','PACKED_KIT7_OVERLAP_CONTACT_PASS'),
 ('package-kit7-contact-only-20261026/verification.json','NINETEEN_GEOMETRY_DELTA_PACKAGE_PASS'),
 ('kit7-contact-only-negative-controls-20261026/result.json','CONTACT_ONLY_NEGATIVE_CONTROLS_PASS'),
 ('kit7-contact-only-build-20261026/nongeometry-controls-v2.json','NON_GEOMETRY_COMPARATOR_CONTROLS_PASS')]
for rel,status in checks:
 p=R/rel;v=read(p);assert v['status']==status
 if 'inputs' in v:validate(v['inputs'])
 bind(p)
validate(read(R/'kit7-contact-only-build-20261026/inputs.json'))
for rel in ['kit7-contact-only-build-20261026/overlay.receipt.json','kit7-contact-only-build-20261026/compile.receipt.json','kit7-contact-only-build-20261026/binary.receipt.json','kit7-contact-only-build-20261026/packed-contact.receipt.json']:
 v=read(R/rel);assert v['returncode']==0 and not v.get('timeout',False);bind(R/rel)
for rel in ['river-kit7-contact-only-20261026/overlap-report.json','river-kit7-contact-only-20261026/author-report.json','river-kit7-contact-only-20261026/records.json','kit7-contact-only-build-20261026/contact.json','kit7-contact-only-build-20261026/costs.json','kit7-native-contact-diagnosis-20261026/targets.json','kit7-native-contact-diagnosis-20261026/neighbours.json','kit7-contact-only-discovery.json','discover_kit7_contact_only.py','test_kit7_non_geometry_comparator_v2.py','test_kit7_contact_only_refusals.py','package_kit7_contact_only_v2.py','prepare_kit7_contact_only_native.py','finish_kit7_overlap_survey.js','package-kit7-contact-only-20261026/Addons/baltic_stream_pilot.pbo']:
 bind(R/rel)
pbo=R/'package-kit7-contact-only-20261026/Addons/baltic_stream_pilot.pbo';assert sha(pbo)==read(R/'package-kit7-contact-only-20261026/verification.json')['pbo_sha256']
v=dict(status='ACCEPTED_NATIVE_RECHECK',inputs=inputs,adjudication=[
 'Contact-only selection reviewed SOUND. Discovery source and target data now bound by this manifest; no production geometry changes after review.',
 'Comparator reviewed SOUND-with-fixes. Required test fix implemented in separately preserved v2: missing LOD and changed resolution rejected; actual positive and six geometry/surface/stream negatives pass.',
 'Optional preservation of Roadway section count not required: scope is labelled oriented face multiplicity and all other decoded fields, not identical batching. Unknown fields discarded by reader remain explicitly outside decoded comparison.',
 'Native physics not accepted. Recheck same 6801 points and producer with fresh vanilla calibration. No tolerance change.'],
 limits=['No client visual, navigation or global-map acceptance.','Only nineteen Geometry entries replaced;182 others and config byte-exact.'])
out=R/'kit7-contact-only-review-20261026/accepted.json';assert not out.exists();out.write_text(json.dumps(v,indent=2)+'\n')
p=R/'ACTIVE-WORK.md';old=p.read_text(encoding='utf-8-sig');p.write_text('# ACTIVO — kit7 contact-only listo para repetición nativa\n\nBuild y dos revisiones Fable terminados. Paquete3d9550bf:19Geometry cambiadas,182piezas yconfig byteexact. Corrección del testcomparador validada en v2. No DayZ propio activo. Banco ocupado por H2R ajeno. Preparar kit7-overlap-native-20261026 y mantener gate físico pendiente hasta6801+calibración. No relanzar helpers sobre salidas existentes.\n\n## Historia\n'+old,encoding='utf-8')
print(json.dumps(dict(status=v['status'],bound_inputs=len(inputs),pbo_sha256=sha(pbo))))

