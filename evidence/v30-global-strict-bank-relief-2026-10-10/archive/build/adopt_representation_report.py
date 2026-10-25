"""Explicit build contract transition after, and only after, independent PASS.

Raw rejected reports stay immutable. This only adapts unexecuted build scripts.
"""
from pathlib import Path
import ast
import hashlib
import json
import shutil

D=Path(__file__).resolve().parent
R=D.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
report_path=R/'review-independent/coverage-contract-review.json'
report=json.loads(report_path.read_text())
assert report['status']=='PASS_EV87_REPRESENTATION_CONSUMER'
assert report['gates'] and all(value is True for value in report['gates'].values())
for path,digest in report['inputs'].items():
    assert sha(path)==digest, f'Accepted input changed: {path}'
raw=R/'review-independent/ev87-review-p99-sector-corrected.json'
assert sha(raw)=='92aa30ca697547aedb9a515d8441bffebd58b32dae4b1bb179f9ba6adf6987c1'
assert json.loads(raw.read_text())['status']=='FAIL_EV87_GLOBAL_CONSUMER'
assert not (D/'build-inputs.json').exists()
for name in ('surface','package','missions','deploy.json'):
    assert not (D/name).exists(), f'Build already started: {name}'

archive=D/'before-representation-adoption'
archive.mkdir(exist_ok=False)
paths=[D/name for name in ('lock_build_inputs.py','build_surface.py','stage.py','package.py','prepare_probe.py','prepare_native_adapters.py')]
paths.append(R/'plot_result.py')
changes={}
for path in paths:
    old=path.read_text()
    assert 'ev87-review.json' in old and 'PASS_EV87_GLOBAL_CONSUMER' in old
    new=old.replace('ev87-review.json','coverage-contract-review.json').replace('PASS_EV87_GLOBAL_CONSUMER','PASS_EV87_REPRESENTATION_CONSUMER')
    if path.name=='plot_result.py':
        marker="geometries={row['queue_id']:row for row in review['information']['patch_geometry']}"
        assert marker in new
        new=new.replace(marker,"raw_path=B/'review-independent/ev87-review-p99-sector-corrected.json'\nassert hashlib.sha256(raw_path.read_bytes()).hexdigest()==review['raw_geometry_report']['sha256']\nraw=json.loads(raw_path.read_text())\ngeometries={row['queue_id']:row for row in raw['information']['patch_geometry']}")
    if path.name=='lock_build_inputs.py':
        marker="D/'reference-inputs.json',D/'native-adapter-receipt.json',"
        assert marker in new
        new=new.replace(marker,"D/'reference-inputs.json',D/'native-adapter-receipt.json',\n        D/'representation-adoption-receipt.json',R/'coverage-contract-proposal.md',\n        R/'review-independent/verify_coverage_contract.py',R/'review-independent/ev87-review-p99-sector-corrected.json',")
    ast.parse(new)
    backup=archive/path.name
    shutil.copyfile(path,backup)
    before=sha(path)
    path.write_text(new,encoding='utf-8',newline='\n')
    changes[str(path)]={'before_sha256':before,'after_sha256':sha(path),'backup':str(backup)}

receipt_path=D/'native-adapter-receipt.json'
backup=archive/receipt_path.name
shutil.copyfile(receipt_path,backup)
native=json.loads(receipt_path.read_text())
native['supersedes']={'path':str(backup),'sha256':sha(backup)}
native['output']={path:sha(path) for path in native['output']}
native['representation_contract']={'report':str(report_path),'sha256':sha(report_path)}
receipt_path.write_text(json.dumps(native,indent=2)+'\n')
out={'status':'BUILD_GUARDS_EXPLICITLY_ADOPT_REPRESENTATION_PASS',
     'accepted_report':str(report_path),'accepted_report_sha256':sha(report_path),
     'preserved_raw_report':str(raw),'preserved_raw_sha256':sha(raw),
     'changes':changes,'native_adapter_receipt_sha256':sha(receipt_path),
     'limits':'No build executed, no terrain/model edits, no runtime or visual acceptance.'}
(D/'representation-adoption-receipt.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'adapted_scripts':len(changes)}))
