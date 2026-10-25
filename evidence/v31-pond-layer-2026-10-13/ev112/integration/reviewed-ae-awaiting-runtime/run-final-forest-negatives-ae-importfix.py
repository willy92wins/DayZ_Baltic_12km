"""Supply the missing local module search path to the unchanged, frozen negative runner."""
from pathlib import Path
import hashlib, json, runpy, sys
O=Path(__file__).parent;D=O/'forest-final-tools-ae';runner=O/'run-final-forest-negatives-ae.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
frozen=json.loads((O/'forest-ae-frozen.json').read_text())
assert len(frozen['files'])==38 and all(sha(p)==h for p,h in frozen['files'].items())
assert sha(runner)=='2563ed9bfd36bcde2374411f75b32c3bc4375bd2cb8e3bc1aedc987c3657fec4'
sys.path.insert(0,str(D))
import recio
assert Path(recio.__file__).resolve()==(D/'recio.py').resolve()
assert sha(recio.__file__)==frozen['files'][str(D/'recio.py')]=='7e350732f36da9664173679f711c2dbb3a5a7f838656cbcab3ef0be4e81198bc'
receipt=O/'forest-ae-import-repair.json'
if sys.argv[1:]==['--check-import-only']:
 assert not receipt.exists() and not (O/'forest-final-negatives-ae').exists()
 failed=O/'pipeline-ae-package-negatives.log'
 assert "ModuleNotFoundError: No module named 'recio'" in failed.read_text()
 result=dict(status='IMPORT_CHECK_PASS',scope=__doc__,original_runner_sha256=sha(runner),wrapper_sha256=sha(__file__),frozen_manifest_sha256=sha(O/'forest-ae-frozen.json'),module=str(Path(recio.__file__).resolve()),module_sha256=sha(recio.__file__),original_failure_log=str(failed),original_failure_log_sha256=sha(failed),negative_output_not_created=True,production_sources_changed=False,acceptance_rules_changed=False)
 receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(0)
assert sys.argv[1:]==[]
checked=json.loads(receipt.read_text());assert checked['status']=='IMPORT_CHECK_PASS' and checked['wrapper_sha256']==sha(__file__)
assert checked['original_runner_sha256']==sha(runner) and checked['frozen_manifest_sha256']==sha(O/'forest-ae-frozen.json')
try:
 runpy.run_path(str(runner),run_name='__main__')
finally:
 assert all(sha(p)==h for p,h in frozen['files'].items())
