"""Package EV93 over hash-verified EV82-B into a fresh isolated preview."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys

B = Path(__file__).parent
WORK = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
from ev93_build_common import (BASE_ADDONS as BASE, EV87_BUILD, PREVIEW_MOD, acceptance_args,
    add_acceptance_manifest, load_accepted_inputs, sha, blob_sha, verify_baseline_pbos,
    verify_baseline_reference_inputs)
TARGET = PREVIEW_MOD / 'Addons'
sys.path.insert(0, str(WORK / 'tools/playtest'))
from attach_navmesh import read_pbo


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blob_sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    acceptance_args(parser)
    args = parser.parse_args()
    accepted = load_accepted_inputs(args.authoring_receipt, args.consumer_report)
    if TARGET.exists() or any((B / name).exists() for name in ('distribution', 'packed')):
        raise FileExistsError('EV93 package outputs/preview target must be fresh; refusing overwrite')
    verify_baseline_pbos()
    reference_path = verify_baseline_reference_inputs()
    reference = json.loads(reference_path.read_text(encoding='utf-8'))
    surface = json.loads((B/'surface-verification.json').read_text())
    stage = json.loads((B/'stage.json').read_text())
    assert reference['status'] == 'PASS_EV82_COMPOSITE_REFERENCE'
    assert surface['status'] == 'PASS_EV93_AFFECTED_SURFACE' and surface['gates'] and all(surface['gates'].values())
    assert surface['terrain_sha256'] == stage['terrain_sha256'] == accepted['candidate_sha256']
    assert stage['ev93_authoring_receipt_sha256'] == accepted['receipt_sha256']
    assert stage['ev93_consumer_report_sha256'] == accepted['consumer_report_sha256']
    assert surface['ev93_authoring_receipt_sha256'] == accepted['receipt_sha256']
    assert surface['ev93_consumer_report_sha256'] == accepted['consumer_report_sha256']
    staged = B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    assert sha(staged) == stage['staged_wrp_sha256'] and stage['objects_and_materials_exact']
    assert sha(BASE/'narva_trial.pbo') == reference['world_sha256']
    assert sha(BASE/'baltic_water_v30.pbo') == reference['water_sha256']
    _,properties,entries = read_pbo(BASE/'narva_trial.pbo')
    assert len(entries) == reference['entries'] == 6827
    assert blob_sha(entries['baltic_trial.wrp']) == reference['compiled_wrp_sha256']
    for item in reference['textures'].values():
        assert sha(item['png']) == item['png_sha256']
        assert blob_sha(entries[item['pbo_entry']]) == item['paa_sha256']
    _,_,compiled = read_pbo(B/'package/world/out/narva_trial.pbo')
    wrp = compiled['baltic_trial.wrp']
    assert wrp.startswith(b'OPRW') and wrp != entries['baltic_trial.wrp']
    replacement = {'baltic_trial.wrp':wrp}
    for tile in surface['files']:
        a,b = tile['tile']
        for kind,suffix in [('s','lco'),('m','lca')]:
            stem = f'{kind}_{a:03d}_{b:03d}_{suffix}'
            path = B/'surface/layers'/(stem+'.paa')
            assert sha(path) == tile['files'][kind]['paa_sha256']
            replacement[reference['textures'][stem]['pbo_entry']] = path.read_bytes()
    assert len(replacement) == 1+2*len(surface['tiles'])
    destination = B/'distribution/narva_trial'
    destination.mkdir(parents=True,exist_ok=False)
    for name,data in entries.items():
        path = destination/name
        assert path.resolve().is_relative_to(destination.resolve()), 'Unsafe PBO entry path'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(replacement.get(name,data))
    out = B/'packed'
    out.mkdir(exist_ok=False)
    command = ['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
    for key,value in properties.items():
        command += ['-property',key+'='+value]
    done = subprocess.run(command+['-dst',str(out),str(destination)],capture_output=True,text=True)
    (B/'filebank.log').write_text(done.stdout+'\n'+done.stderr)
    assert done.returncode == 0
    pbo = out/'narva_trial.pbo'
    _,after_properties,after = read_pbo(pbo)
    assert properties == after_properties and entries.keys() == after.keys()
    assert all(after[key] == replacement.get(key,entries[key]) for key in entries)
    changed = sorted(key for key in entries if entries[key] != after[key])
    textures = [key for key in changed if key != 'baltic_trial.wrp']
    assert all(re.search(r'(?:^|/)[sm]_\d{3}_\d{3}_lc[oa]\.paa$',key,re.I) for key in textures)
    TARGET.mkdir(parents=True,exist_ok=False)
    for path in [pbo,BASE/'baltic_water_v30.pbo']:
        shutil.copyfile(path,TARGET/path.name)
        assert sha(path) == sha(TARGET/path.name)
    receipt = dict(status='PACKAGED_EV93_PREVIEW_NATIVE_READBACK_PENDING',mod=str(TARGET.parent),
                   files={path.name:sha(path) for path in [pbo,BASE/'baltic_water_v30.pbo']},
                   terrain_sha256=accepted['candidate_sha256'],compiled_wrp_sha256=blob_sha(wrp),
                   baseline_world_sha256=reference['world_sha256'],changed_entries=changed,
                   changed_texture_entries=textures,unchanged_entries=len(entries)-len(changed),total_entries=len(entries),
                   surface_selected_tiles=len(surface['tiles']),all_expected_entries_exact=True,water_pbo_exact=True,
                   baseline_texture_identities_verified=2048,baseline_png_identities_verified=2048,
                   limits=['Package is isolated EV93 preview only. Native height readback and visual/render/navigation acceptance are pending. No promotion.'])
    add_acceptance_manifest(receipt, accepted)
    (B/'deploy.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in receipt.items() if key not in ('changed_entries','changed_texture_entries')}))


if __name__ == '__main__':
    main()
