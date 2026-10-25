"""Freeze the actual EV82-B surface composite before EV87 surface authoring.

Read-only against the deployed addon and all previous builds. No candidate,
texture, package or DayZ process is changed by this script.
"""
from pathlib import Path
import hashlib
import json
import sys

OUT = Path(__file__).parent
ROOT = OUT.parent.parent
PREV = ROOT / 'v30-mixed-bank-incremental-fixed-20261010'
WORK = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
MOD = Path('P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons')
sys.path.insert(0, str(WORK / 'tools/playtest'))
from attach_navmesh import read_pbo


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    expected = {
        'terrain': 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
        'world': 'b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c',
        'water': '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14',
        'wrp': '3b12b21d554c6ab75d76c43b5ba902c9a1d49a26516bdd14b16f1a6048ba2539',
        'reference': '358960dd95ef5bd2687190909b033306f8d0e82366a40461af46396f52cc9a8c',
        'consumer': '7406cbb3d103bc09365fb750202614f037b079452a47acad9161581c2ab56c64',
    }
    assert sha(PREV / 'candidate/terrain.npz') == expected['terrain']
    assert sha(PREV / 'reference-inputs.json') == expected['reference']
    assert sha(PREV / 'review-luna/report.json') == expected['consumer']
    receipt = json.loads((PREV / 'deploy.json').read_text())
    surface = json.loads((PREV / 'surface-verification.json').read_text())
    reference = json.loads((PREV / 'reference-inputs.json').read_text())
    assert receipt['files']['narva_trial.pbo'] == expected['world']
    assert surface['status'] == 'PASS_EV82_AFFECTED_SURFACE'
    assert surface['gates'] and all(surface['gates'].values())
    assert surface['terrain_sha256'] == expected['terrain']
    assert len(surface['files']) == 462
    assert reference['status'] == 'PASS_EV80_COMPOSITE_REFERENCE'
    assert sha(MOD / 'narva_trial.pbo') == expected['world']
    assert sha(MOD / 'baltic_water_v30.pbo') == expected['water']
    _, properties, entries = read_pbo(MOD / 'narva_trial.pbo')
    assert len(entries) == 6827
    assert hashlib.sha256(entries['baltic_trial.wrp']).hexdigest() == expected['wrp']
    index = reference['textures'].copy()
    for tile in surface['files']:
        a, b = tile['tile']
        for kind, suffix in [('s', 'lco'), ('m', 'lca')]:
            stem = f'{kind}_{a:03d}_{b:03d}_{suffix}'
            data = tile['files'][kind]
            index[stem] = dict(png=str(PREV / 'surface/layers' / (stem + '.png')),
                               png_sha256=data['png_sha256'], pbo_entry=f'data/layers/{stem}.paa',
                               paa_sha256=data['paa_sha256'])
    assert len(index) == 2048
    for stem, item in index.items():
        assert sha(item['png']) == item['png_sha256'], stem
        assert hashlib.sha256(entries[item['pbo_entry']]).hexdigest() == item['paa_sha256'], stem
    report = dict(status='PASS_EV82_COMPOSITE_REFERENCE', world_sha256=expected['world'],
                  water_sha256=expected['water'], compiled_wrp_sha256=expected['wrp'],
                  source_terrain_sha256=expected['terrain'], entries=len(entries),
                  png_and_deployed_paa_verified=len(index), reference_tiles=1024,
                  ev82_overlay_tiles=len(surface['files']), properties=properties,
                  reference_reports={str(PREV / name): sha(PREV / name) for name in
                                     ('reference-inputs.json', 'surface-verification.json', 'deploy.json', 'review-luna/report.json')},
                  textures=index)
    destination = OUT / 'reference-inputs.json'
    assert not destination.exists(), 'Do not replace a frozen reference'
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'textures'}))


if __name__ == '__main__':
    main()
