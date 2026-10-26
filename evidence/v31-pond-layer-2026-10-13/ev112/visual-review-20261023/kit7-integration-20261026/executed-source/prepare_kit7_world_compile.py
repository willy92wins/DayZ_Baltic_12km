"""Prepare exact isolated compiled pilot dependencies; never deploy or launch."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).parent;O=R/'kit7-world-unit-20261026';P=R/'pilot-kit7-fc-20261026';S=R/'stage-kit7-fc-20261026'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
gate=read(R/'kit7-world-review-20261026/accepted.json');assert gate['status']=='ACCEPTED_TECHNICAL_WORLD_ONLY'
assert all(sha(p)==h for p,h in gate['inputs'].items())
vr=read(R/'package-kit7-fc-pilot-v2-20261026/verification.json');assert vr['status']=='PASS_201_MODELS_BYTE_EXACT_CONFIG_EXTENDED'
packed=R/'package-kit7-fc-pilot-v2-20261026/Addons/baltic_stream_pilot.pbo';assert sha(packed)==vr['pbo_sha256']
_,_,entries=read_pbo(packed)
assert read(R/'kit7-context-unit-20261026/result.json')['status']=='PASS_CONTEXT_GATES_BOUNDARY_PENDING'
source=R/'package-kit7-fc-pilot-v2-20261026/compiled/baltic_stream_pilot';dest=P/'temp/baltic_stream_pilot'
assert not dest.exists() and not (S/'out').exists() and not (S/'temp').exists();O.mkdir(exist_ok=False)
for name,h in vr['models'].items():assert sha(source/name)==h
actual={p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob('*') if p.is_file()};assert actual==entries
shutil.copytree(source,dest)
before={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()};after={str(p.relative_to(dest)):sha(p) for p in dest.rglob('*') if p.is_file()};assert before==after
assert {p.relative_to(dest).as_posix():p.read_bytes() for p in dest.rglob('*') if p.is_file()}==entries
(O/'dependencies.json').write_text(json.dumps(dict(status='EXACT_COMPILED_PILOT_DEPENDENCIES_READY',models=201,files=before,source=str(source),destination=str(dest),limits=['Compiled source dependencies only; no world build accepted.']),indent=2)+'\n')
print('EXACT_COMPILED_PILOT_DEPENDENCIES_READY')
