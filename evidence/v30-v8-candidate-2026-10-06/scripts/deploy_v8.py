"""Deploy the v8 candidate PBOs (v7d plus the flowing-water shores and river beds) to P:/Mods/@DayZ_Baltic_V8Candidate/Addons, checked by SHA-256 against the build receipt."""
import hashlib
import json
import shutil
from pathlib import Path

SRC = Path('E:/DayZ-Baltic-Build/v30-v8/package')
DST = Path('P:/Mods/@DayZ_Baltic_V8Candidate/Addons')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()


receipt = json.loads((SRC / 'build-receipt.json').read_text(encoding='utf-8-sig'))
receipt = receipt if isinstance(receipt, list) else [receipt]
assert sorted(r['name'] for r in receipt) == ['baltic_water_v30.pbo', 'narva_trial.pbo'], receipt
assert not DST.parent.exists(), f'fresh mod folder required: {DST.parent}'
DST.mkdir(parents=True)
out = []
for r in receipt:
    src = SRC / 'out' / 'Addons' / r['name']
    assert sha(src) == r['sha256'], f'build output changed since the receipt: {src}'
    dst = DST / r['name']
    shutil.copyfile(src, dst)
    got = sha(dst)
    assert got == r['sha256'] and dst.stat().st_size == r['bytes'], f'copy mismatch: {dst}'
    out.append({'name': r['name'], 'bytes': r['bytes'], 'sha256': got, 'deployed_to': str(dst)})
(SRC.parent / 'deploy-receipt.json').write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
print(json.dumps(out, indent=1))
