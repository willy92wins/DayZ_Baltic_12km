"""One frozen full run after root review; preserve all outcomes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
script=D/'verify_coverage_contract.py'
assert sha(script)=='214f0eddda08d84ce18c921fcdbe01298f608c9a5c19b7e5246bb9e71df5dc2b'
fixtures=D/'coverage-contract-fixtures.json'
f=json.loads(fixtures.read_text())
assert f['status']=='PASS_EV87_REPRESENTATION_FIXTURES'
assert f['verifier_sha256']==sha(script)
assert f['fixtures'] and all(f['fixtures'].values())
policy=D.parent/'coverage-contract-proposal.md'
assert sha(policy)=='6964ca97226512764720eb1a25f41ab65e191cfda318ea07ad39bb1f4c0b6463'
target=D/'coverage-contract-review.json'
receipt=D/'coverage-contract-execution-receipt.json'
assert not target.exists() and not receipt.exists()
started=time.time()
command=[sys.executable,str(script),'--report',str(target)]
start={'status':'STARTED_AFTER_ROOT_REVIEW','started_unix':started,'command':command,
       'verifier_sha256':sha(script),'policy_sha256':sha(policy),'fixtures_sha256':sha(fixtures),
       'scope':'One production run; no candidate edits or tolerance search.'}
receipt.write_text(json.dumps(start,indent=2)+'\n')
with (D/'coverage-contract-run.log').open('w',encoding='utf-8') as log:
    result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
out=json.loads(target.read_text()) if target.exists() else {}
start.update(status=out.get('status','NO_REPORT'),returncode=result.returncode,
             elapsed_seconds=time.time()-started,report_sha256=sha(target) if target.exists() else None,
             verifier_unchanged=sha(script)==start['verifier_sha256'],policy_unchanged=sha(policy)==start['policy_sha256'])
receipt.write_text(json.dumps(start,indent=2)+'\n')
print(json.dumps(start))
assert result.returncode==0 and out.get('status')=='PASS_EV87_REPRESENTATION_CONSUMER', 'Outcome preserved; no build accepted'
