"""Stage the accepted joint road/shore field after native persistence."""
from pathlib import Path
import argparse, json, shutil
from prepare_foundation_package import ROOT, CONFIG_SHA, WATER_SHA, BOOTSTRAP_SHA, sha, manifest
from verify_native_road_terrain import inspect
from canonicalize_road_v29_water_poses import ASC, ASC_SHA, verify_receipt, native_pair, read


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--wrp', type=Path, required=True); p.add_argument('--reopened', type=Path, required=True)
    p.add_argument('--package', type=Path, required=True); p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--object-restoration', type=Path)
    a = p.parse_args(); assert not a.package.exists() and not a.evidence.exists()
    assert a.wrp.resolve() != a.reopened.resolve() and sha(ASC) == ASC_SHA
    statuses = {
        'independent-consumer.json': 'PASS_OFFLINE_EDITABLE_DRY_NETWORK_GEOMETRY',
        'continuous-outline.json': 'PASS_OFFLINE_OUTLINE_GEOMETRY',
        'joint-hydrology.json': 'PASS_OFFLINE_JOINT_HYDROLOGY_AND_PROTECTED_LAND',
        'landmarks-controls-physical-contract.json': 'PASS_OUTLINE_LANDMARKS_AND_CONTROLS',
        'land-controls.json': 'PASS_FULL_NETWORK_POSITIVE_AND_NEGATIVES',
        'joint-hydrology-controls.json': 'PASS_REAL_JOINT_HYDROLOGY_AND_FOUR_NEGATIVES',
    }
    proofs = []
    for name, status in statuses.items():
        path = ASC.parent/name; gate = json.loads(path.read_text())
        assert gate['status'] == status and gate.get('candidate_sha256', gate.get('asc_sha256')) == ASC_SHA
        assert all(value is True for value in gate.get('checks', {}).values())
        proofs.append(dict(path=str(path), sha256=sha(path), status=status))
    restoration = verify_receipt(a.object_restoration) if a.object_restoration else None
    if restoration:
        assert [Path(v['derived']).resolve() for v in restoration['files']] == [a.wrp.resolve(), a.reopened.resolve()]
    gates = [inspect(path, ASC, ASC_SHA) for path in (a.wrp, a.reopened)]
    assert all(all(gate['checks'].values()) for gate in gates), gates
    native_pair(read(a.wrp), read(a.reopened))
    a.evidence.mkdir(parents=True)
    for tag, gate in zip(('first', 'reopened'), gates):
        (a.evidence/(tag+'.json')).write_text(json.dumps(gate, indent=2)+'\n', encoding='utf-8')
    source = ROOT/'packages/baltic-regional-outline-v3/source/BalticTrialWorld'
    config_path = ROOT/'packages/baltic-regional-v0.3-candidate/world-config.cpp'
    water = ROOT/'build-output/regional_water_assets_v2/baltic_water.pbo'
    bootstrap = ROOT/'tb/regional_outline_v3/navmesh/baltic_regional_tile12p5_v1.nm'
    for path, digest in ((config_path, CONFIG_SHA), (water, WATER_SHA), (bootstrap, BOOTSTRAP_SHA)):
        assert sha(path) == digest
    before = manifest(source)
    assert sum(k.endswith('.rvmat') for k in before) == 4775 and sum(k.endswith('.paa') for k in before) == 2048
    config = config_path.read_text()
    assert config.count('"DZ_Surfaces"') == 1 and config.count('tileWidth=12.5;') == 1
    config = config.replace('"DZ_Surfaces"', '"DZ_Surfaces",\n\t\t\t"Baltic_Water"')
    stage = a.package/'source/BalticTrialWorld'; shutil.copytree(source, stage)
    shutil.copyfile(a.reopened, stage/'baltic_trial.wrp'); shutil.copyfile(bootstrap, stage/'navmesh/baltic_trial.nm')
    (stage/'config.cpp').write_text(config)
    expected = {**before, 'baltic_trial.wrp': gates[1]['wrp_sha256'],
                'navmesh/baltic_trial.nm': BOOTSTRAP_SHA, 'config.cpp': sha(stage/'config.cpp')}
    assert manifest(stage) == expected
    shutil.copytree(ROOT/'packages/baltic-regional-outline-v3/tools', a.package/'tools')
    (a.package/'water-addon').mkdir(); shutil.copyfile(water, a.package/'water-addon/baltic_water.pbo')
    assert sha(a.package/'water-addon/baltic_water.pbo') == WATER_SHA
    receipt = dict(status='JOINT_ROAD_V29_STAGED_FOR_DATA_SERVER_WITH_STALE_NAVIGATION',
                   terrain_version='road-v29-on-outline-v33', precision_contract='native-road-v29-frozen',
                   asc=str(ASC), asc_sha256=ASC_SHA, offline_proofs=proofs,
                   exact_native_persistence=True, native_exports=gates, source_files=expected,
                   water_pbo_sha256=WATER_SHA, bootstrap_navmesh_sha256=BOOTSTRAP_SHA,
                   limits=['Actual UI save/close/reopen provenance required.',
                           'Bootstrap navigation is stale. Generate new NM before gameplay.'])
    if restoration:
        receipt['precision_contract'] = 'native-road-v29-canonical-water'
        receipt['build_input_checks'] = receipt.pop('native_exports')
        receipt['object_restoration'] = str(a.object_restoration.resolve())
        receipt['object_restoration_sha256'] = sha(a.object_restoration)
        receipt['literal_native_exports'] = restoration['literal_checks']
        receipt['limits'].append('Build inputs explicitly restore only sub-micrometre water Y; literal files retained separately.')
    (a.package/'stage-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('source_files', 'native_exports', 'literal_native_exports', 'build_input_checks')}), flush=True)


if __name__ == '__main__':
    main()
