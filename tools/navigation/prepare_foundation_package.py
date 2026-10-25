"""Stage the foundation only after two full native exports pass frozen gates.

The included older NM is explicitly a bootstrap for the data server. Generate a
new NM from this world's compiled WRP before treating the package as playable.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/playtest'))
from verify_texture_grid_change import read

ASC_SHA = '335554a6ea06f8546eeac5444aec7597eaf45df18be0c69b0baab48a573947b2'
V10_ASC_SHA = '8e25fab25e8f0909fdda302ed4ba3db4c43884c523920f5ef3424db90780eb8b'
CONFIG_SHA = 'b9f8aa7d952f4a0d7a4d18051f0059c9facfc834f55918c789344f73fabb6e08'
WATER_SHA = 'f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3'
BOOTSTRAP_SHA = 'eb0f131e5fc0f80d81c60b1f332d8ecfa6396cab9e09ffd36cd1c8504885c496'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(folder):
    paths = list(folder.rglob('*'))
    if any(p.is_symlink() or p.is_junction() for p in paths):
        raise ValueError('Unexpected source reparse point')
    return {p.relative_to(folder).as_posix(): sha(p) for p in paths if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wrp', required=True, type=Path)
    parser.add_argument('--reopened', required=True, type=Path)
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--terrain-version', choices=['v9', 'v10'], default='v9')
    parser.add_argument('--precision-contract', choices=['strict', 'native-v9-micrometre', 'native-v10-frozen'], default='strict')
    args = parser.parse_args()
    if (args.terrain_version == 'v10') != (args.precision_contract == 'native-v10-frozen'):
        raise ValueError('V10 requires its own frozen contract; do not mix V9 and V10 gates')
    expected_asc = V10_ASC_SHA if args.terrain_version == 'v10' else ASC_SHA
    if args.package.exists() or args.evidence.exists():
        raise ValueError('Fresh package and evidence paths required')
    if args.wrp.resolve() == args.reopened.resolve():
        raise ValueError('Two distinct saved exports required')
    for path in (args.wrp, args.reopened):
        if not path.is_file():
            raise ValueError('Missing native export: ' + str(path))
    args.evidence.mkdir(parents=True)
    gates = []
    for tag, path in (('first', args.wrp), ('reopened', args.reopened)):
        output = args.evidence / (tag + '.json')
        if args.terrain_version == 'v10':
            command = [sys.executable, str(ROOT / 'tools/navigation/verify_foundation_v10_native.py'),
                       '--wrp', str(path.resolve()), '--out', str(output.resolve())]
        else:
            command = [sys.executable, str(ROOT / 'tools/navigation/verify_foundation_native.py'),
                       '--wrp', str(path.resolve()), '--out', str(output.resolve()),
                       '--terrain-version', 'v9', '--precision-contract', args.precision_contract]
        result = subprocess.run(command, capture_output=True)
        (args.evidence / (tag + '.stdout.log')).write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise ValueError('Native export rejected; see ' + str(args.evidence))
        gate = json.loads(output.read_text())
        scope_ok = (gate['status'] == 'PASS_NATIVE_V10_CONTENT' and all(gate['checks'].values())) if args.terrain_version == 'v10' else (
            gate['status'] == 'PASS_NATIVE_EXPORT' and not gate['terrain_only']
            and gate['precision_contract'] == args.precision_contract)
        if not scope_ok or gate['asc_sha256'] != expected_asc:
            raise ValueError('Wrong native verification scope')
        gates.append(gate)
    first, reopened = read(args.wrp), read(args.reopened)
    key = lambda obj: (obj['name'].lower(), obj['id'], obj['matrix'])
    if (first['bytes'][:first['objects_start']] != reopened['bytes'][:reopened['objects_start']]
            or sorted(map(key, first['objects'])) != sorted(map(key, reopened['objects']))):
        raise ValueError('Reopening changed terrain, materials or object records')

    source = ROOT / 'packages/baltic-regional-outline-v3/source/BalticTrialWorld'
    config_path = ROOT / 'packages/baltic-regional-v0.3-candidate/world-config.cpp'
    water = ROOT / 'build-output/regional_water_assets_v2/baltic_water.pbo'
    bootstrap = ROOT / 'tb/regional_outline_v3/navmesh/baltic_regional_tile12p5_v1.nm'
    for path, expected in ((config_path, CONFIG_SHA), (water, WATER_SHA), (bootstrap, BOOTSTRAP_SHA)):
        if sha(path) != expected:
            raise ValueError('Frozen dependency changed: ' + str(path))
    before = manifest(source)
    if (sum(p.endswith('.rvmat') for p in before) != 4775
            or sum(p.endswith('.paa') for p in before) != 2048):
        raise ValueError('Expected the accepted SAT1M source palette')
    config = config_path.read_text()
    old = '"DZ_Surfaces"'
    if config.count(old) != 1 or config.count('tileWidth=12.5;') != 1:
        raise ValueError('Unexpected baseline configuration')
    config = config.replace(old, '"DZ_Surfaces",\n\t\t\t"Baltic_Water"')
    stage = args.package / 'source/BalticTrialWorld'
    shutil.copytree(source, stage)
    shutil.copyfile(args.reopened, stage / 'baltic_trial.wrp')
    shutil.copyfile(bootstrap, stage / 'navmesh/baltic_trial.nm')
    (stage / 'config.cpp').write_text(config, encoding='utf-8')
    expected = dict(before)
    expected.update({'baltic_trial.wrp': gates[1]['wrp_sha256'],
                     'navmesh/baltic_trial.nm': BOOTSTRAP_SHA,
                     'config.cpp': sha(stage / 'config.cpp')})
    if manifest(stage) != expected:
        raise ValueError('Unexpected staged file change')
    shutil.copytree(ROOT / 'packages/baltic-regional-outline-v3/tools', args.package / 'tools')
    (args.package / 'water-addon').mkdir()
    shutil.copyfile(water, args.package / 'water-addon/baltic_water.pbo')
    if sha(args.package / 'water-addon/baltic_water.pbo') != WATER_SHA:
        raise ValueError('Copied water addon changed')
    receipt = {'status': 'FOUNDATION_STAGED_WITH_STALE_BOOTSTRAP_NAVIGATION',
               'terrain_version': args.terrain_version,
               'precision_contract': args.precision_contract,
               'exact_native_persistence': True,
               'native_exports': gates, 'source_files': expected,
               'water_pbo_sha256': WATER_SHA, 'bootstrap_navmesh_sha256': BOOTSTRAP_SHA,
               'limits': ['Two files alone do not prove the editor was reopened; retain the UI evidence.',
                          'Fresh NM, compiled content and runtime consumers are still required.']}
    (args.package / 'stage-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('source_files', 'native_exports')}, indent=2))


if __name__ == '__main__':
    main()
