"""Copy the accepted editable only after the V33 independent gates pass."""
from pathlib import Path
import hashlib, json, shutil
ROOT = Path(__file__).resolve().parents[2]
source = ROOT / 'tb/regional_foundation_v10'
target = ROOT / 'tb/regional_outline_smoothing_v33'
candidate = ROOT / 'tests/regional_outline_smoothing_v33'
ev = ROOT / 'evidence/foundation-followup-2026-10-01/outline-v33-native'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not target.exists() and not ev.exists()
asc = candidate / 'baltic_outline_smoothing_v33.asc'
assert sha(asc) == '9d2954fc0600272ec72b61149f5df6b7bbbd347e20979000d96d74bd603b0107'
for filename in ('independent-consumer.json', 'landmarks-controls-physical-contract.json'):
    gate = json.loads((candidate / filename).read_text())
    assert gate['candidate_sha256'] == sha(asc) and all(v is True for v in gate['checks'].values())
assert sha(source / '02_reopened_v10.wrp') == 'cdd6838f522a5b66b729db7c6bda39b0a5a41eb256fb26804eb39f5479ef905a'
items = list(source.rglob('*'))
assert not any(p.is_symlink() or p.is_junction() for p in items)
before = {p.relative_to(source).as_posix(): sha(p) for p in items if p.is_file()}
shutil.copytree(source, target)
for rel, digest in before.items():
    assert sha(source / rel) == digest and sha(target / rel) == digest, rel
shutil.copyfile(asc, target / 'outline_v33.asc')
assert sha(target / 'outline_v33.asc') == sha(asc)
ev.mkdir()
report = dict(status='PASS_COMPLETE_EDITABLE_COPY_NOT_IMPORTED', source=str(source),
              target=str(target), source_files=len(before), source_hashes=before,
              added_asc_sha256=sha(asc))
(ev / 'editor-clone.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'source_hashes'}))
