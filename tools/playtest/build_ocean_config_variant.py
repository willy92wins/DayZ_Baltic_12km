"""Diagnostic explicit vanilla ocean material; config-only PBO delta."""
import argparse
import json
from pathlib import Path
import re
from attach_navmesh import read_pbo, sha
from build_outside_material_variant import run

ap = argparse.ArgumentParser(description=__doc__)
for name in ('baseline', 'cfgconvert', 'filebank', 'output'):
    ap.add_argument('--'+name, type=Path, required=True)
ap.add_argument('--baseline-sha256', required=True)
a = ap.parse_args()
raw, props, entries = read_pbo(a.baseline)
if sha(raw) != a.baseline_sha256.lower() or a.output.exists():
    raise ValueError('Exact baseline and fresh output required')
a.output.mkdir(parents=True)
before_bin = a.output/'baseline-config.bin'
before_bin.write_bytes(entries['config.bin'])
before_cpp = a.output/'baseline-config.cpp'
run([a.cfgconvert, '-txt', '-dst', before_cpp, before_bin], a.output/'decode.log')
source = before_cpp.read_text(encoding='utf-8-sig')
properties = {'oceanMaterial': 'oceanold.emat', 'oceanNiceMaterial': 'oceanold_nice.emat', 'oceanStormMaterial': 'oceanold_storm.emat'}
if any(k in source for k in properties) or source.count('class UsedTerrainMaterials') != 1:
    raise ValueError('Unexpected baseline config')
block = ''
for key, name in properties.items():
    if not (Path('P:/graphics/materials/water')/name).is_file():
        raise ValueError('Vanilla material missing')
    block += key+'="Graphics/materials/water/'+name+'";\n\t\t'
candidate_cpp = a.output/'candidate-config.cpp'
candidate_cpp.write_text(source.replace('class UsedTerrainMaterials', block+'class UsedTerrainMaterials'), encoding='utf-8')
candidate_bin = a.output/'candidate-config.bin'
run([a.cfgconvert, '-bin', '-dst', candidate_bin, candidate_cpp], a.output/'compile.log')
decoded = a.output/'candidate-decoded.cpp'
run([a.cfgconvert, '-txt', '-dst', decoded, candidate_bin], a.output/'candidate-decode.log')
text = decoded.read_text(encoding='utf-8-sig')
for key in properties:
    text, count = re.subn(r'\b'+key+r'\s*=\s*"[^"]*";', '', text)
    if count != 1:
        raise ValueError('Expected exactly one new material property')
if re.sub(r'\s+', '', text) != re.sub(r'\s+', '', source):
    raise ValueError('Unrelated config delta')
expected = dict(entries)
expected['config.bin'] = candidate_bin.read_bytes()
stage, dest = a.output/'compiled/narva_trial', a.output/'Addons'
stage.mkdir(parents=True)
dest.mkdir()
for name, content in expected.items():
    path = stage/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
run([a.filebank, '-property', 'prefix='+props['prefix'], '-property', 'product=dayz ugc', '-dst', dest, stage], a.output/'filebank.log')
packed, packed_props, after = read_pbo(dest/'narva_trial.pbo')
if after != expected or packed_props.get('prefix') != props['prefix']:
    raise ValueError('Unexpected PBO changes')
receipt = {'status':'PASS_OCEAN_CONFIG_ONLY_VARIANT', 'pbo_sha256':sha(packed),
           'baseline_sha256':sha(raw), 'unchanged_entries':len(entries)-1,
           'wrp_sha256':sha(after['baltic_trial.wrp']),
           'navmesh_sha256':sha(after['navmesh/baltic_trial.nm']),
           'runtime':'PENDING_VISUAL_TEST', 'temporary':True}
(a.output/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
