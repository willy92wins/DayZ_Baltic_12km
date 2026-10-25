"""Independent read-only audit of deployed EV82-B PBO against EV80 and staged sources."""
from pathlib import Path
import sys, json, hashlib, importlib.util, gc, time

import numpy as np

B = Path(__file__).parents[1]
R = B.parent
EV80 = R / 'v30-mixed-bank-constrained-20261010'
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
OUT = B / 'review-luna/compiled-package-review.json'
MD = B / 'review-luna/compiled-package-review.md'
DEPLOY = B / 'deploy.json'
BASELINE_DEPLOY = EV80 / 'deploy.json'
EXPECTED_CANDIDATE = 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
EXPECTED_EV80 = '0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'
EXPECTED_WATER = '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
EXPECTED_REFERENCE = '358960dd95ef5bd2687190909b033306f8d0e82366a40461af46396f52cc9a8c'
EXPECTED_0WZD_SOURCE = '6b43b82a274bf9d80767f2df4db033a084c1206cc0b0cdab8abde9df0397c064'
EXPECTED_EV80_WRP_PAYLOAD = '3ae8f82cfc7279cec5c58dd8f253b9da79bfbfe52004695ebe02cb5587383680'
EXPECTED_EV80_WORLD_PBO = 'ec3785d1eab89eb18503e358a9f7d786dca35f9eef829301bae45a1ec28d7038'

sys.path.insert(0, str(W / 'tools/playtest'))
sys.path.insert(0, str(W / 'tools/terrain'))
from attach_navmesh import read_pbo
from wrp0wzd import read as read_0wzd


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def blob_sha(blob):
    return hashlib.sha256(blob).hexdigest()


def pbo_inventory(path):
    raw, props, entries = read_pbo(path)
    inventory = {k.replace('\\', '/').lower(): (k, blob_sha(bytes(v))) for k, v in entries.items()}
    result = dict(file_sha256=sha(path), bytes=Path(path).stat().st_size,
                  entry_count=len(entries), properties=props, inventory=inventory,
                  wrp_sha256=blob_sha(entries['baltic_trial.wrp']) if 'baltic_trial.wrp' in entries else None,
                  wrp_magic=bytes(entries.get('baltic_trial.wrp', b''))[:4].decode('ascii', 'replace'))
    del entries, raw
    gc.collect()
    return result


def main():
    started = time.monotonic()
    assert not OUT.exists() and not MD.exists(), 'Preserve prior package review evidence'
    deploy = json.loads(DEPLOY.read_text(encoding='utf-8'))
    base_deploy = json.loads(BASELINE_DEPLOY.read_text(encoding='utf-8'))
    surface = json.loads((B / 'surface-verification.json').read_text(encoding='utf-8'))
    geometry = json.loads((B / 'review-luna/report.json').read_text(encoding='utf-8'))
    reference = json.loads((B / 'reference-inputs.json').read_text(encoding='utf-8'))
    stage = json.loads((B / 'stage.json').read_text(encoding='utf-8'))
    base_stage = json.loads((EV80 / 'stage.json').read_text(encoding='utf-8'))

    assert deploy['status'] == 'DEPLOYED_EV82_PREVIEW_NATIVE_READBACK_PENDING'
    assert base_deploy['status'] == 'DEPLOYED_EV80_PREVIEW_NATIVE_READBACK_PENDING'
    assert geometry['status'] == 'PASS_EV82_CONSUMER' and all(geometry['gates'].values())
    assert surface['status'] == 'PASS_EV82_AFFECTED_SURFACE' and all(surface['gates'].values())
    assert reference['status'] == 'PASS_EV80_COMPOSITE_REFERENCE' and sha(B / 'reference-inputs.json') == EXPECTED_REFERENCE
    assert stage['status'] == 'STAGED_EV82_HEIGHTS_ONLY' and stage['objects'] == 18033 and stage['objects_and_materials_exact']
    assert base_stage['status'] == 'STAGED_EV80_HEIGHTS_ONLY' and base_stage['objects'] == 18033
    assert sha(B / 'candidate/terrain.npz') == EXPECTED_CANDIDATE == deploy['terrain_sha256']
    assert sha(EV80 / 'candidate/terrain.npz') == EXPECTED_EV80 == base_deploy['terrain_sha256']
    assert deploy['total_entries'] == base_deploy['total_entries'] == 6827
    assert len(deploy['changed_entries']) == 92 and len(deploy['changed_texture_entries']) == 91

    baseline_mod = Path(base_deploy['mod']) / 'Addons'
    candidate_mod = Path(deploy['mod']) / 'Addons'
    baseline_pbo = baseline_mod / 'narva_trial.pbo'
    candidate_pbo = candidate_mod / 'narva_trial.pbo'
    baseline_water = baseline_mod / 'baltic_water_v30.pbo'
    candidate_water = candidate_mod / 'baltic_water_v30.pbo'
    packaged_pbo = B / 'packed/narva_trial.pbo'
    compiled_pbo = B / 'package/world/out/narva_trial.pbo'

    assert sha(baseline_pbo) == base_deploy['files']['narva_trial.pbo'] == EXPECTED_EV80_WORLD_PBO
    assert sha(candidate_pbo) == deploy['files']['narva_trial.pbo']
    assert sha(packaged_pbo) == sha(candidate_pbo), 'deployed world PBO differs from staged package artifact'
    assert sha(baseline_water) == sha(candidate_water) == EXPECTED_WATER

    baseline = pbo_inventory(baseline_pbo)
    candidate = pbo_inventory(candidate_pbo)
    compiled = pbo_inventory(compiled_pbo)
    assert baseline['entry_count'] == candidate['entry_count'] == 6827
    assert baseline['properties'] == candidate['properties']
    assert baseline['wrp_magic'] == candidate['wrp_magic'] == compiled['wrp_magic'] == 'OPRW'
    assert candidate['wrp_sha256'] == deploy['compiled_wrp_sha256']
    assert compiled['wrp_sha256'] == candidate['wrp_sha256']
    assert set(baseline['inventory']) == set(candidate['inventory'])

    differences = sorted(k for k in baseline['inventory']
                         if baseline['inventory'][k][1] != candidate['inventory'][k][1])
    expected_differences = sorted(str(k).replace('\\', '/').lower() for k in deploy['changed_entries'])
    assert differences == expected_differences, 'deployed PBO differences differ from deploy manifest'
    assert len(differences) == 92 and differences.count('baltic_trial.wrp') == 1
    diff_paa = [k for k in differences if k.endswith('.paa')]
    assert len(diff_paa) == 91 and set(diff_paa) == {
        str(k).replace('\\', '/').lower() for k in deploy['changed_texture_entries']
    }
    assert set(differences) - {'baltic_trial.wrp'} == set(diff_paa)

    # Every selected generated PAA must be exactly the corresponding payload in
    # the deployed archive; unchanged generated tiles remain byte-identical to EV80.
    tile_payload_checks = []
    texture_index = reference['textures']
    for tile in surface['files']:
        a, b = tile['tile']
        for kind, suffix in (('s', 'lco'), ('m', 'lca')):
            stem = f'{kind}_{a:03d}_{b:03d}_{suffix}'
            item = texture_index[stem]
            pbo_key = item['pbo_entry'].replace('\\', '/').lower()
            expected_paa_sha = tile['files'][kind]['paa_sha256']
            actual_sha = candidate['inventory'][pbo_key][1]
            assert actual_sha == expected_paa_sha, f'deployed PAA differs from verified surface output: {pbo_key}'
            if pbo_key in baseline['inventory']:
                assert (actual_sha != baseline['inventory'][pbo_key][1]) == (pbo_key in diff_paa)
            tile_payload_checks.append(pbo_key)
    assert len(tile_payload_checks) == 924 and len(set(tile_payload_checks)) == 924

    # Read the real staged editable WRP files independently. The parser contract
    # is the repository's wrp0wzd.read; object records are raw serialized bytes.
    base_0wzd = EV80 / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    candidate_0wzd = B / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    assert sha(base_0wzd) == base_stage['staged_wrp_sha256']
    assert sha(candidate_0wzd) == stage['staged_wrp_sha256']
    assert sha(EV80 / 'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp') == EXPECTED_0WZD_SOURCE
    old_wr = read_0wzd(base_0wzd)
    new_wr = read_0wzd(candidate_0wzd)
    baseline_h = np.load(EV80 / 'candidate/terrain.npz', allow_pickle=False)['heights']
    candidate_h = np.load(B / 'candidate/terrain.npz', allow_pickle=False)['heights']
    heights_exact = (np.array_equal(old_wr['heights'], baseline_h[::-1])
                     and np.array_equal(new_wr['heights'], candidate_h[::-1]))
    assert heights_exact
    objects_exact = ([o['bytes'] for o in old_wr['objects']] == [o['bytes'] for o in new_wr['objects']]
                     and len(old_wr['objects']) == len(new_wr['objects']) == 18033)
    assert objects_exact
    header_materials_exact = all(old_wr[k] == new_wr[k] for k in ('header', 'materials', 'terminator'))
    assert header_materials_exact

    checks = {
        'deploy_manifests_match_actual_pbo': True,
        'baseline_and_candidate_pbo_hashes_exact': True,
        'packaged_pbo_equals_deployed': True,
        'water_pbo_identical': True,
        '6827_entries_and_properties_exact': True,
        'only_expected_wrp_and_91_paa_entries_differ': True,
        'all_924_generated_paa_payloads_exact': True,
        'staged_0wzd_heights_match_ev80_and_ev82_candidates': heights_exact,
        'all_18033_staged_object_records_identical': objects_exact,
        'staged_0wzd_header_materials_terminator_identical': header_materials_exact,
        'compiled_wrps_are_oprw_and_payload_hash_matches_manifest': True,
    }
    result = dict(
        status='PASS_EV82B_COMPILED_PACKAGE_REVIEW' if all(checks.values()) else 'FAIL_EV82B_COMPILED_PACKAGE_REVIEW',
        checks=checks,
        candidate_sha256=EXPECTED_CANDIDATE,
        baseline_ev80_pbo_sha256=baseline['file_sha256'], candidate_pbo_sha256=candidate['file_sha256'],
        compiled_output_pbo_sha256=compiled['file_sha256'],
        baseline_world_payload_sha256=baseline['wrp_sha256'], candidate_world_payload_sha256=candidate['wrp_sha256'],
        baseline_water_pbo_sha256=sha(baseline_water), candidate_water_pbo_sha256=sha(candidate_water),
        baseline_properties=baseline['properties'], candidate_properties=candidate['properties'],
        entry_count=candidate['entry_count'], changed_entry_count=len(differences),
        changed_entries=differences, changed_paa_count=len(diff_paa), unchanged_entries=candidate['entry_count']-len(differences),
        expected_paa_payloads_checked=len(tile_payload_checks),
        staged_0wzd=dict(baseline_sha256=sha(base_0wzd), candidate_sha256=sha(candidate_0wzd),
                         baseline_heights_exact=True, candidate_heights_exact=True,
                         baseline_objects=len(old_wr['objects']), candidate_objects=len(new_wr['objects']),
                         object_records_byte_identical=True, header_materials_terminator_identical=True),
        limits=[
            'Independent offline verification of actual deployed PBO bytes and the staged editable 0WZD WRP.',
            'The compiled OPRW payload is hash-anchored and checked for OPRW signature; this audit does not decode native OPRW object records.',
            'No DayZ load, SurfaceY readback, render, mip validation, navigation, or gameplay acceptance is claimed.',
        ],
        seconds=round(time.monotonic()-started, 3),
    )
    OUT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    md = [
        '# EV82-B — auditoría independiente del PBO desplegado', '',
        f"**{result['status']}**. PBO real EV80 y EV82-B comparados contra sus artefactos empaquetados; 6.827 entradas, propiedades PBO y hash de agua verificados.", '',
        f"El PBO EV82-B cambia exactamente {len(differences)} entradas: el WRP y 91 PAA; las otras {candidate['entry_count']-len(differences)} entradas permanecen byte-idénticas a EV80. Los 924 PAA generados para las 462 teselas se compararon con sus cargas desplegadas.", '',
        'El WRP editable 0WZD conserva alturas exactas de las fuentes EV80/EV82-B y sus 18.033 registros de objeto serializados, cabecera, materiales y terminador son idénticos entre versiones.', '',
        'Límite: el OPRW real del PBO se ancla por hash y firma, pero este auditor no decodifica los registros internos del OPRW. Tampoco carga DayZ ni prueba SurfaceY/render/mips/navegación.', '',
        'La superficie se generó y verificó antes del fallo inicial de serialización del informe por clave de conteo. La reanudación omitió regenerar PNG→PAA y comprobó que los hashes PAA y decodificados no cambiaron.', '',
        'Detalle máquina: `compiled-package-review.json`.', '',
    ]
    MD.write_text('\n'.join(md), encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('changed_entries','baseline_properties','candidate_properties')}, indent=2))
    assert all(checks.values())


if __name__ == '__main__':
    main()
