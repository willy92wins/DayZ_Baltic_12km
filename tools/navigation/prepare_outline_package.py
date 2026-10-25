"""Stage a proven outline candidate, preserving literal/derived provenance."""
from pathlib import Path
import argparse,json,shutil,re,sys
from prepare_foundation_package import ROOT,CONFIG_SHA,WATER_SHA,BOOTSTRAP_SHA,sha,manifest
from verify_native_road_terrain import inspect
sys.path.insert(0,str(ROOT/'tools/playtest'))
from verify_texture_grid_change import read
from canonicalize_outline_water_poses import verify_receipt

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',required=True,type=Path);p.add_argument('--wrp',required=True,type=Path);p.add_argument('--reopened',required=True,type=Path);p.add_argument('--package',required=True,type=Path);p.add_argument('--evidence',required=True,type=Path);p.add_argument('--object-restoration',type=Path);a=p.parse_args()
    match=re.fullmatch(r'regional_outline_smoothing_(v[0-9]+)',a.candidate.name);assert match;version=match[1]
    proof=a.candidate/'independent-consumer.json';gate=json.loads(proof.read_text());assert gate['status']=='PASS_OFFLINE_OUTLINE_GEOMETRY' and all(gate['checks'].values())
    assert gate['checks'].get('frozen_v5_runtime_samples') is True,'Legacy geometry-only gate does not preserve accepted runtime points'
    asc=a.candidate/f'baltic_outline_smoothing_{version}.asc';expected=gate['candidate_sha256'];assert sha(asc)==expected
    landmarks=a.candidate/'landmarks-controls-physical-contract.json';landmark_gate=json.loads(landmarks.read_text())
    assert landmark_gate['status']=='PASS_OUTLINE_LANDMARKS_AND_CONTROLS' and all(landmark_gate['checks'].values()) and landmark_gate['candidate_sha256']==expected
    restoration=None
    if a.object_restoration:
        assert version=='v33'
        restoration=verify_receipt(a.object_restoration)
        assert [Path(f['derived']).resolve() for f in restoration['files']]==[a.wrp.resolve(),a.reopened.resolve()]
    assert not a.package.exists() and not a.evidence.exists();assert a.wrp.resolve()!=a.reopened.resolve();a.evidence.mkdir(parents=True)
    gates=[]
    for tag,path in [('first',a.wrp),('reopened',a.reopened)]:
        native=inspect(path,asc,expected);(a.evidence/(tag+'.json')).write_text(json.dumps(native,indent=2)+'\n');assert all(native['checks'].values()),native;gates.append(native)
    first,last=read(a.wrp),read(a.reopened);key=lambda o:(o['name'].lower(),o['id'],o['matrix'])
    assert first['bytes'][:first['objects_start']]==last['bytes'][:last['objects_start']]
    assert sorted(map(key,first['objects']))==sorted(map(key,last['objects']))
    source=ROOT/'packages/baltic-regional-outline-v3/source/BalticTrialWorld';config_path=ROOT/'packages/baltic-regional-v0.3-candidate/world-config.cpp';water=ROOT/'build-output/regional_water_assets_v2/baltic_water.pbo';bootstrap=ROOT/'tb/regional_outline_v3/navmesh/baltic_regional_tile12p5_v1.nm'
    for path,digest in [(config_path,CONFIG_SHA),(water,WATER_SHA),(bootstrap,BOOTSTRAP_SHA)]:assert sha(path)==digest
    before=manifest(source);assert sum(p.endswith('.rvmat') for p in before)==4775 and sum(p.endswith('.paa') for p in before)==2048
    config=config_path.read_text();assert config.count('"DZ_Surfaces"')==1 and config.count('tileWidth=12.5;')==1;config=config.replace('"DZ_Surfaces"','"DZ_Surfaces",\n\t\t\t"Baltic_Water"')
    stage=a.package/'source/BalticTrialWorld';shutil.copytree(source,stage);shutil.copyfile(a.reopened,stage/'baltic_trial.wrp');shutil.copyfile(bootstrap,stage/'navmesh/baltic_trial.nm');(stage/'config.cpp').write_text(config)
    expected_files={**before,**{'baltic_trial.wrp':gates[1]['wrp_sha256'],'navmesh/baltic_trial.nm':BOOTSTRAP_SHA,'config.cpp':sha(stage/'config.cpp')}};assert manifest(stage)==expected_files
    shutil.copytree(ROOT/'packages/baltic-regional-outline-v3/tools',a.package/'tools');(a.package/'water-addon').mkdir();shutil.copyfile(water,a.package/'water-addon/baltic_water.pbo');assert sha(a.package/'water-addon/baltic_water.pbo')==WATER_SHA
    receipt=dict(status='OUTLINE_STAGED_FOR_DATA_SERVER_WITH_STALE_NAVIGATION',terrain_version='outline-'+version,precision_contract='native-outline-frozen',asc=str(asc),asc_sha256=expected,offline_proof=str(proof),offline_proof_sha256=sha(proof),exact_native_persistence=True,native_exports=gates,source_files=expected_files,water_pbo_sha256=WATER_SHA,bootstrap_navmesh_sha256=BOOTSTRAP_SHA,limits=['UI save/close/reopen evidence required in addition to the two exact exports.','Bootstrap NM is stale; generate fresh navigation before gameplay testing.'])
    receipt.update(landmarks_proof=str(landmarks),landmarks_proof_sha256=sha(landmarks))
    if restoration:
        receipt['precision_contract']='native-outline-v33-canonical-water'
        receipt['build_input_checks']=receipt.pop('native_exports')
        receipt['literal_native_exports']=[inspect(Path(f['raw']),asc,expected) for f in restoration['files']]
        receipt['object_restoration']=str(a.object_restoration.resolve())
        receipt['object_restoration_sha256']=sha(a.object_restoration)
        receipt['limits'].append('Build inputs are derived: 670 water Y fields restored to V10. Literal exports retain strict FAIL against V10 but persist exactly across reopen.')
    (a.package/'stage-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ('native_exports','source_files')},indent=2))
if __name__=='__main__':main()
