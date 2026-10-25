"""Pack a bounded temporary Baltic fixture; no deployment or process control."""
from pathlib import Path
import argparse, hashlib, json, subprocess
from attach_navmesh import read_pbo

ap = argparse.ArgumentParser(description=__doc__)
for n in ('source', 'output', 'cfgconvert', 'filebank'):
    ap.add_argument('--' + n, type=Path, required=True)
ap.add_argument('--addon', choices=('baltic_render_probe', 'baltic_walk_probe', 'baltic_visual_ui_probe'), default='baltic_render_probe')
a = ap.parse_args()
if a.output.exists():
    raise ValueError('Fresh output required')
stage = a.output / a.addon
dest = a.output / 'Addons'
stage.mkdir(parents=True)
dest.mkdir()
for p in a.source.rglob('*.c'):
    q = stage / p.relative_to(a.source)
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_bytes(p.read_bytes())
argvs = [
    [a.cfgconvert, '-bin', '-dst', stage / 'config.bin', a.source / 'config.cpp'],
    [a.filebank, '-property', 'prefix=' + a.addon, '-property', 'product=dayz ugc', '-dst', dest, stage],
]
for i, argv in enumerate(argvs):
    p = subprocess.run([str(x) for x in argv], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (a.output / f'command-{i}.log').write_bytes(p.stdout)
    if p.returncode:
        raise RuntimeError(f'Tool failed exit {p.returncode}')
packed, props, entries = read_pbo(dest / (a.addon + '.pbo'))
expected = {p.relative_to(stage).as_posix(): p.read_bytes() for p in stage.rglob('*') if p.is_file()}
if entries != expected or len(entries) != 2 or props['prefix'] != a.addon:
    raise ValueError('Probe packed entries differ')
report = {'status': 'PASS_PACKED_CONTENT_ONLY', 'sha256': hashlib.sha256(packed).hexdigest(),
          'entries': {k: hashlib.sha256(v).hexdigest() for k, v in entries.items()},
          'runtime': 'PENDING_ENGINE_SCRIPT_COMPILATION_AND_FIXTURE_EXECUTION'}
(a.output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
