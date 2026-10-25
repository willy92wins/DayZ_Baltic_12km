"""DIAGNOSTIC ONLY: first verified native export, no reopen persistence acceptance.

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

ROOT = Path('P:/DayZ_Baltic_12km_dev')
sys.path.insert(0, str(ROOT / 'tools/playtest'))
from verify_texture_grid_change import read

ASC_SHA = '335554a6ea06f8546eeac5444aec7597eaf45df18be0c69b0baab48a573947b2'
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
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--precision-contract', choices=['strict', 'native-v9-micrometre'], default='strict')
    args = parser.parse_args()
    if args.package.exists() or args.evidence.exists():
        raise ValueError('Fresh package and evidence paths required')
    if not args.wrp.is_file():
        raise ValueError('Missing diagnostic native export')
    args.evidence.mkdir(parents=True)
    gates = []
    for tag, path in (('first', args.wrp),):
        output = args.evidence / (tag + '.json')
        result = subprocess.run([
            sys.executable, str(ROOT / 'tools/navigation/verify_foundation_native.py'),
            '--wrp', str(path.resolve()), '--out', str(output.resolve()),
            '--terrain-version', 'v9', '--precision-contract', args.precision_contract], capture_output=True)
        (args.evidence / (tag + '.stdout.log')).write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise ValueError('Native export rejected; see ' + str(args.evidence))
        gate = json.loads(output.read_text())
        if (gate['terrain_only'] or gate['asc_sha256'] != ASC_SHA
                or gate['precision_contract'] != args.precision_contract):
            raise ValueError('Wrong native verification scope')
        gates.append(gate)
    # Reopen persistence is NOT proved or claimed by this diagnostic branch.

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
    shutil.copyfile(args.wrp, stage / 'baltic_trial.wrp')
    shutil.copyfile(bootstrap, stage / 'navmesh/baltic_trial.nm')
    (stage / 'config.cpp').write_text(config, encoding='utf-8')
    expected = dict(before)
    expected.update({'baltic_trial.wrp': gates[0]['wrp_sha256'],
                     'navmesh/baltic_trial.nm': BOOTSTRAP_SHA,
                     'config.cpp': sha(stage / 'config.cpp')})
    if manifest(stage) != expected:
        raise ValueError('Unexpected staged file change')
    shutil.copytree(ROOT / 'packages/baltic-regional-outline-v3/tools', args.package / 'tools')
    (args.package / 'water-addon').mkdir()
    shutil.copyfile(water, args.package / 'water-addon/baltic_water.pbo')
    if sha(args.package / 'water-addon/baltic_water.pbo') != WATER_SHA:
        raise ValueError('Copied water addon changed')
    receipt = {'status': 'DIAGNOSTIC_ONLY_FIRST_EXPORT_STALE_NAV',
               'precision_contract': args.precision_contract,
               'native_exports': gates, 'source_files': expected,
               'water_pbo_sha256': WATER_SHA, 'bootstrap_navmesh_sha256': BOOTSTRAP_SHA,
               'limits': ['Only the first export is staged. Native reopen persistence is still unverified.',
                          'Fresh NM, compiled content and runtime consumers are still required.']}
    (args.package / 'stage-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('source_files', 'native_exports')}, indent=2))


if __name__ == '__main__':
    main()
