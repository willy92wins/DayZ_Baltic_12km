"""One bounded opaque-layer recovery experiment; requires the editor closed."""
from pathlib import Path
import datetime, hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source = ROOT / 'tb/regional_foundation_v10'
target = ROOT / 'tb/regional_outline_smoothing_v33'
evidence = ROOT / 'evidence/foundation-followup-2026-10-01/outline-v33-native'
backup = evidence / 'before-object-layer-restore'
assert not backup.exists()
clone = json.loads((evidence / 'editor-clone.json').read_text())
assert all(sha(source / rel) == digest for rel, digest in clone['source_hashes'].items())
old_layer = source / 'narva_trial.Layers/default.tv4l'
new_layer = target / 'outline_v33.Layers/default.tv4l'
assert sha(old_layer) == '9092835794239f30c05c0397dc45bcd07033bb107ecd2209e7a06d7ec7b84119'
assert sha(target / '3.wrp') == 'ce6474590be331fadfdf9f93bfc4c745d7836386cf136a6e553cf0b729984af4'
paths = [p for p in target.rglob('*') if p.is_file()]
assert not any(p.is_junction() or p.is_symlink() for p in target.rglob('*'))
before = {p.relative_to(target).as_posix(): sha(p) for p in paths}
backup.mkdir()
for p in [new_layer, target / 'outline_v33.tv4p', target / 'outline_v33.grid.000.v4w']:
    dest = backup / p.relative_to(target)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)
    assert sha(dest) == before[p.relative_to(target).as_posix()]
assert sha(new_layer) == before['outline_v33.Layers/default.tv4l']
shutil.copyfile(old_layer, new_layer)
after = {p.relative_to(target).as_posix(): sha(p) for p in paths}
changed = [rel for rel in before if before[rel] != after[rel]]
assert changed == ['outline_v33.Layers/default.tv4l']
assert all(sha(source / rel) == digest for rel, digest in clone['source_hashes'].items())
receipt = dict(status='ONE_LAYER_RESTORED_PENDING_NATIVE_EXPORT',
               utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               editor_state='Native UI closed Terrain Builder after Save; no editor window remained.',
               source_sha256=sha(old_layer), changed=changed, before_files=before,
               after_layer_sha256=sha(new_layer), source_v10_files_unchanged=len(clone['source_hashes']),
               limits=['Opaque file copy, not proof of absolute pose semantics or native output.'])
(evidence / 'object-layer-restore.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k:v for k,v in receipt.items() if k != 'before_files'}))
