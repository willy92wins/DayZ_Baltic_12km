"""Full verified editable copy, without replacing the V10 editor or deployment."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'tb/regional_foundation_v10';target=ROOT/'tb/regional_outline_smoothing_v26'
assert not target.exists(),'Fresh target required'
items=list(source.rglob('*'));assert not any(p.is_symlink() or p.is_junction() for p in items)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source/'02_reopened_v10.wrp')=='cdd6838f522a5b66b729db7c6bda39b0a5a41eb256fb26804eb39f5479ef905a'
before={p.relative_to(source).as_posix():sha(p) for p in items if p.is_file()}
shutil.copytree(source,target)
for rel,digest in before.items():assert sha(source/rel)==digest and sha(target/rel)==digest,rel
asc=ROOT/'tests/regional_outline_smoothing_v26/baltic_outline_smoothing_v26.asc';assert sha(asc)=='2a5b74be020bb7ad84160adad501bea85af83387a728c0ad488dad445cfa3962'
shutil.copyfile(asc,target/'outline_v26.asc');assert sha(target/'outline_v26.asc')==sha(asc)
ev=ROOT/'evidence/foundation-followup-2026-10-01/outline-v26-native';ev.mkdir()
report=dict(status='PASS_COMPLETE_EDITABLE_COPY_NOT_IMPORTED',source=str(source),target=str(target),source_files=len(before),source_hashes=before,added_asc_sha256=sha(asc))
(ev/'editor-clone.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='source_hashes'}))
