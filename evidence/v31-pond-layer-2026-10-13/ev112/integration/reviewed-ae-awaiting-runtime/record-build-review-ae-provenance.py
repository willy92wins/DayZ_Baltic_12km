"""Post-review dependency inventory. This does not invent a build-time measurement."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
O=Path(__file__).parent
P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
F=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
D=O/'build-review-ae-provenance';assert not D.exists()
sources={
 'staging-wrp0wzd.py':F/'tools/terrain/wrp0wzd.py',
 'compile-include.lst':F/'packages/baltic-road-v29/tools/include.lst',
 'patch_surface_v31.py':P/'tools/terrain/patch_surface_v31.py',
 'verify_roads_v30.py':P/'tools/terrain/verify_roads_v30.py',
 'stage_bridges_v31.py':P/'tools/terrain/stage_bridges_v31.py',
 'audit-wrp-readback.py':O/'audit-wrp-readback.py',
 'gate_lib.py':O/'surface-gates-b/gate_lib.py'}
assert sha(sources['staging-wrp0wzd.py'])==sha(O/'terrain/wrp0wzd.py')=='8b85cec46ba72851a4ec829c5b0adcc88727ee852c3f699ab7a15e31b50fee2a'
assert sha(sources['patch_surface_v31.py'])==sha(O/'terrain/patch_surface_v31.py')=='00bfecc6e077b0b20402a50a9641866430ebade80836493f4f25440e7c0decf9'
closure=json.loads((O/'forest-review-closure-ae.json').read_text())
assert closure['conditions']['promoted'][str(sources['patch_surface_v31.py'])]==sha(sources['patch_surface_v31.py'])
D.mkdir();rows=[]
for name,source in sources.items():
 target=D/name;shutil.copyfile(source,target);assert sha(target)==sha(source)
 row=dict(path=str(source),sha256=sha(source),snapshot=str(target),mtime_utc=datetime.fromtimestamp(source.stat().st_mtime,timezone.utc).isoformat())
 if source.is_relative_to(P):
  rel=source.relative_to(P).as_posix()
  blob=subprocess.run(['git','show','HEAD:'+rel],cwd=P,capture_output=True,check=True).stdout
  row['current_HEAD_blob_sha256']=hashlib.sha256(blob).hexdigest()
  row['current_HEAD_equal_after_CRLF_normalization']=blob.replace(b'\r\n',b'\n')==source.read_bytes().replace(b'\r\n',b'\n')
 rows.append(row)
out=dict(status='MEASURED_POST_REVIEW',time_utc=datetime.now(timezone.utc).isoformat(),dependencies=rows,
 exact_frozen_matches={'staging-wrp0wzd.py':str(O/'terrain/wrp0wzd.py'),'patch_surface_v31.py':str(O/'terrain/patch_surface_v31.py')},
 original_build_binding_sha256=sha(O/'final-ae-build-binding.json'),surface_manifest_sha256=sha(O/'surface-final-ae/manifest.json'),
 scope='Actual dependency paths read from stage_bridges_v31.py:9, compile_world_ev112_ae.ps1:18, surface-gates-b/gate_lib.py:17-20 and audit-wrp-readback.py:11-12. Current bytes preserved; wrp0wzd and patch_surface match the frozen copies exactly. Existing receipts are unchanged.',
 limits='This inventory was measured after compilation and review, not at import time. It cannot retrospectively prove that an untracked live dependency never changed during the build. Independent compiled-object readback and final surface consumers remain the acceptance evidence; compiled terrain heights were not decoded. The server probe is still pending.')
(D/'provenance.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
