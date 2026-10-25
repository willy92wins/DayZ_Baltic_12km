"""Compile/pack an isolated diagnostic addon; verify actual PBO bytes. Never deploy."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'playtest'))
from attach_navmesh import read_pbo, sha

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[2]
source = root / 'diagnostics/baltic_boat_input'
binroot = Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
cfgconvert = binroot / 'CfgConvert/CfgConvert.exe'
filebank = binroot / 'PboUtils/FileBank.exe'
if not cfgconvert.is_file() or not filebank.is_file():
    raise ValueError('Installed build tools missing')
if a.output.exists():
    raise ValueError('Fresh output required')
prefix = (source / '$PBOPREFIX$').read_text().strip()
if prefix != 'baltic_boat_input':
    raise ValueError('Unexpected addon prefix')
stage = a.output / 'compiled/baltic_boat_input'
dest = a.output / 'Addons'
stage.mkdir(parents=True)
dest.mkdir()
def run(argv, name):
    result = subprocess.run([str(v) for v in argv], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (a.output / name).write_bytes(result.stdout)
    if result.returncode:
        raise RuntimeError(name + ' failed')
run([cfgconvert, '-bin', '-dst', stage / 'config.bin', source / 'config.cpp'], 'cfgconvert.log')
expected = {'config.bin': (stage / 'config.bin').read_bytes()}
if not expected['config.bin'].startswith(b'\0raP'):
    raise ValueError('Config not compiled')
for path in (source / 'scripts').rglob('*.c'):
    name = path.relative_to(source).as_posix()
    expected[name] = path.read_bytes()
    target = stage / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(expected[name])
if len(expected) != 2:
    raise ValueError('Expected one config and one script')
run([filebank, '-property', 'prefix=' + prefix, '-property', 'product=dayz ugc', '-dst', dest, stage], 'filebank.log')
raw, props, entries = read_pbo(dest / 'baltic_boat_input.pbo')
if props.get('prefix') != prefix or entries != expected:
    raise ValueError('Packed byte parity failed')
receipt = {'status': 'PASS_PACKED_BYTE_PARITY', 'pbo_sha256': sha(raw),
           'source_sha256': {str(p.relative_to(source)): sha(p.read_bytes()) for p in source.rglob('*') if p.is_file()},
           'entries': {k: sha(v) for k,v in entries.items()}, 'runtime': 'NOT_TESTED'}
(a.output / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
