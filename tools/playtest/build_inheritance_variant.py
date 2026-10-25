"""Temporary Chernarus inheritance discriminator; preserve every non-config entry."""
import argparse
import json
from pathlib import Path
import re
from attach_navmesh import read_pbo, sha
from build_outside_material_variant import run

p = argparse.ArgumentParser(description=__doc__)
for key in ('baseline', 'output', 'cfgconvert', 'filebank'):
    p.add_argument('--'+key, type=Path, required=True)
p.add_argument('--baseline-sha256', required=True)
a = p.parse_args()
raw, props, entries = read_pbo(a.baseline)
if sha(raw) != a.baseline_sha256.lower() or a.output.exists():
    raise ValueError('Exact baseline and fresh output required')
a.output.mkdir(parents=True)
original = a.output/'baseline.bin'
original.write_bytes(entries['config.bin'])
cpp = a.output/'baseline.cpp'
run([a.cfgconvert, '-txt', '-dst', cpp, original], a.output/'decode.log')
source = cpp.read_text(encoding='utf-8-sig')
if source.count('class CAWorld;') != 1 or source.count('class BalticTrial: CAWorld') != 1 or source.count('"DZ_Surfaces"') != 1:
    raise ValueError('Unexpected source structure')
candidate = source.replace('class CAWorld;', 'class ChernarusPlus;').replace('class BalticTrial: CAWorld', 'class BalticTrial: ChernarusPlus').replace('"DZ_Surfaces"', '"DZ_Surfaces", "DZ_Worlds_Chernarusplus_World"')
cpp2 = a.output/'candidate.cpp'
cpp2.write_text(candidate, encoding='utf-8')
binary = a.output/'candidate.bin'
run([a.cfgconvert, '-bin', '-dst', binary, cpp2], a.output/'compile.log')
decoded = a.output/'decoded.cpp'
run([a.cfgconvert, '-txt', '-dst', decoded, binary], a.output/'roundtrip.log')
undo = decoded.read_text(encoding='utf-8-sig').replace('class ChernarusPlus;', 'class CAWorld;').replace('class BalticTrial: ChernarusPlus', 'class BalticTrial: CAWorld')
undo = re.sub(r',\s*"DZ_Worlds_Chernarusplus_World"', '', undo)
if re.sub(r'\s+', '', undo) != re.sub(r'\s+', '', source):
    raise ValueError('Unrelated configuration changed')
expected = dict(entries)
expected['config.bin'] = binary.read_bytes()
stage, dest = a.output/'compiled/narva_trial', a.output/'Addons'
stage.mkdir(parents=True)
dest.mkdir()
for key, content in expected.items():
    path = stage/key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
run([a.filebank, '-property', 'prefix='+props['prefix'], '-property', 'product=dayz ugc', '-dst', dest, stage], a.output/'filebank.log')
packed, packed_props, after = read_pbo(dest/'narva_trial.pbo')
if after != expected or packed_props.get('prefix') != props['prefix']:
    raise ValueError('PBO parity failed')
receipt = dict(status='PASS_CONFIG_ONLY_DISCRIMINATOR', temporary=True,
               baseline_sha256=sha(raw), pbo_sha256=sha(packed), unchanged_entries=len(entries)-1,
               wrp_sha256=sha(after['baltic_trial.wrp']), navmesh_sha256=sha(after['navmesh/baltic_trial.nm']),
               runtime='PENDING', forbidden_for_delivery='Foreign names/CE/environment inherited')
(a.output/'verification.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
