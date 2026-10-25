"""Stage only a verified regional native export, retaining the SAT1M palette."""
import argparse
import json
import shutil
from pathlib import Path
from prepare_regional_outline import ROOT, sha, save

p = argparse.ArgumentParser()
p.add_argument('--verification', required=True, type=Path)
p.add_argument('--package', required=True, type=Path)
a = p.parse_args()
gate = json.loads(a.verification.read_text())
wrp = Path(gate['wrp'])
if gate['status'] != 'PASS_NATIVE_EXPORT' or sha(wrp) != gate['wrp_sha256']:
    raise ValueError('Native gate does not match actual export')
nm = ROOT/'tb/narva_navigation_v3/navmesh/baltic_navigation_native_v1.nm'
nmsha = '68450401421904660b10bf47563ca069458c722c3b86d3626c1c15fb5e2a3626'
if sha(nm) != nmsha:
    raise ValueError('Bootstrap navigation changed')
source = ROOT/'packages/baltic-navigation-native-v1/source/BalticTrialWorld'
if a.package.exists():
    raise ValueError('Fresh destination required')
items = list(source.rglob('*'))
if any(f.is_symlink() or f.is_junction() for f in items):
    raise ValueError('Unexpected reparse point')
before = {f.relative_to(source).as_posix(): sha(f) for f in items if f.is_file()}
stage = a.package/'source/BalticTrialWorld'
shutil.copytree(source, stage)
shutil.copyfile(wrp, stage/'baltic_trial.wrp')
shutil.copyfile(nm, stage/'navmesh/baltic_trial.nm')
expected = dict(before, **{'baltic_trial.wrp':gate['wrp_sha256'], 'navmesh/baltic_trial.nm':nmsha})
for rel, digest in expected.items():
    if sha(stage/rel) != digest:
        raise ValueError('Unexpected stage content: '+rel)
shutil.copytree(ROOT/'packages/baltic-navigation-native-v1/tools', a.package/'tools')
receipt = {'status':'REGIONAL_NATIVE_STAGED_WITH_STALE_BOOTSTRAP_NAVIGATION',
           'wrp_sha256':gate['wrp_sha256'], 'bootstrap_navmesh_sha256':nmsha,
           'unchanged_files':len(before)-2,
           'limits':['Generate a fresh NM against the compiled WRP before acceptance.']}
save(a.package/'stage-receipt.json', receipt)
print(json.dumps(receipt, indent=2))
