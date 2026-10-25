"""Independently read back EV95's compiled and repacked OPRW identities.

This verifies archive contents and byte provenance, not OPRW semantic decoding
or engine loading. Run only after package.py has produced the isolated preview.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from wide_build_common import (BASE_ADDONS, BASE_COMPILED_WRP_SHA, EV87_BUILD,
    PREVIEW_MOD, W, acceptance_args, load_accepted_inputs, sha,
    verify_baseline_pbos, verify_baseline_reference_inputs)

B = Path(__file__).parent
sys.path.insert(0, str(W / 'tools/playtest'))
from attach_navmesh import read_pbo  # noqa: E402

ATTACH_NAVMESH_SHA = '717b81469e0a799690d1586cd7a4492f079c3b2db626eec7e2815cd15896e062'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_pbo_checked(path: Path):
    if sha(W / 'tools/playtest/attach_navmesh.py') != ATTACH_NAVMESH_SHA:
        raise ValueError('pinned PBO reader source changed')
    return read_pbo(path)


def verify_oprw_identity(compiled: bytes, packed: bytes, deployed: bytes, expected_sha: str) -> str:
    """Prove exact compiled-to-preview byte identity without decoding OPRW."""
    if not all(blob.startswith(b'OPRW') for blob in (compiled, packed, deployed)):
        raise ValueError('compiled, packed, and deployed WRP must all carry OPRW magic')
    hashes = [digest(blob) for blob in (compiled, packed, deployed)]
    if len(set(hashes)) != 1 or hashes[0] != expected_sha:
        raise ValueError('compiled, packed, deployed OPRW bytes or receipt SHA differ')
    return hashes[0]


def changed_entries_between(baseline: dict[str, bytes], packed: dict[str, bytes]) -> list[str]:
    if baseline.keys() != packed.keys():
        raise ValueError('packed PBO entry inventory differs from baseline')
    return sorted(name for name in baseline if baseline[name] != packed[name])


def verify_replacement_scope(packed, changed, expected_sha_by_entry):
    """Regenerated entries can remain byte-identical; every actual change is owned."""
    require('baltic_trial.wrp' in changed, 'compiled WRP is absent from actual delta')
    allowed = set(expected_sha_by_entry) | {'baltic_trial.wrp'}
    require(set(changed) <= allowed, 'PBO changes an entry outside the selected surface footprint')
    for name, wanted in expected_sha_by_entry.items():
        require(name in packed and digest(packed[name]) == wanted,
                f'selected surface entry differs from generated PAA: {name}')


def main() -> None:
    if not __debug__:
        raise RuntimeError('refusing optimized Python for fail-closed PBO identity verification')
    parser = argparse.ArgumentParser(description=__doc__)
    acceptance_args(parser)
    args = parser.parse_args()
    accepted = load_accepted_inputs(args.composition_receipt)
    verify_baseline_pbos()
    reference_path = verify_baseline_reference_inputs()
    reference = json.loads(reference_path.read_text(encoding='utf-8'))
    stage = json.loads((B / 'stage.json').read_text(encoding='utf-8'))
    surface = json.loads((B / 'surface-verification.json').read_text(encoding='utf-8'))
    deploy_path = B / 'deploy.json'
    deploy = json.loads(deploy_path.read_text(encoding='utf-8'))
    require(stage.get('status') == 'STAGED_EV95_WIDE_HEIGHTS_ONLY', 'stage receipt is absent or not PASS')
    require(surface.get('status') == 'PASS_EV95_AFFECTED_SURFACE' and surface.get('gates') and all(value is True for value in surface['gates'].values()), 'surface receipt is absent or not PASS')
    for artifact in (stage, surface, deploy):
        require(artifact.get('terrain_sha256') == accepted['candidate_sha256'], 'artifact candidate identity mismatch')
        require(artifact.get('ev95_composition_receipt_sha256') == accepted['receipt_sha256'], 'artifact selection receipt identity mismatch')
        require(artifact.get('ev95_composition_source_sha256') == accepted['composition_source_sha256'], 'artifact selector source identity mismatch')
        require(artifact.get('ev95_sector_consumer_sha256') == accepted['consumer_source_sha256'], 'artifact consumer source identity mismatch')
    require(deploy.get('status') == 'PACKAGED_EV95_WIDE_PREVIEW_NATIVE_READBACK_PENDING', 'package receipt is absent or unexpected')
    require(Path(deploy.get('mod', '')).resolve() == PREVIEW_MOD.resolve(), 'package receipt points outside the EV95 preview mod')
    require(deploy.get('baseline_world_sha256') == reference['world_sha256'], 'package baseline world identity mismatch')

    baseline_pbo = BASE_ADDONS / 'narva_trial.pbo'
    packed_pbo = B / 'packed/narva_trial.pbo'
    deployed_pbo = PREVIEW_MOD / 'Addons/narva_trial.pbo'
    compiled_pbo = B / 'package/world/out/narva_trial.pbo'
    require(all(path.is_file() for path in (baseline_pbo, packed_pbo, deployed_pbo, compiled_pbo)), 'baseline/compiled/packed/deployed PBO is missing')
    require(sha(packed_pbo) == deploy['files']['narva_trial.pbo'] == sha(deployed_pbo), 'packed/deployed PBO digest differs from package receipt')
    _, baseline_properties, baseline_entries = read_pbo_checked(baseline_pbo)
    _, packed_properties, packed_entries = read_pbo_checked(packed_pbo)
    require(baseline_properties == packed_properties, 'baseline and packed PBO properties differ')
    require(len(baseline_entries) == len(packed_entries) == 6827, 'baseline/packed PBO entry count mismatch')
    require(baseline_entries.keys() == packed_entries.keys(), 'baseline/packed PBO entry inventory mismatch')
    require(digest(baseline_entries['baltic_trial.wrp']) == reference['compiled_wrp_sha256'] == BASE_COMPILED_WRP_SHA, 'baseline compiled WRP identity mismatch')

    packaged_wrp = packed_entries.get('baltic_trial.wrp', b'')
    changed = changed_entries_between(baseline_entries, packed_entries)
    require(changed == deploy.get('changed_entries'), 'package changed-entry list differs from actual PBO delta')
    require(changed.count('baltic_trial.wrp') == 1, 'actual PBO delta must contain exactly one WRP change')
    changed_textures = [name for name in changed if name != 'baltic_trial.wrp']
    require(changed_textures == deploy.get('changed_texture_entries'), 'package changed-texture list differs from actual PBO delta')
    expected_sha_by_entry = {}
    for item in surface['files']:
        a, b = item['tile']
        for kind, suffix in (('s', 'lco'), ('m', 'lca')):
            stem = f'{kind}_{a:03d}_{b:03d}_{suffix}'
            entry = reference['textures'][stem]['pbo_entry']
            require(entry not in expected_sha_by_entry, 'duplicate selected surface entry')
            expected_sha_by_entry[entry] = item['files'][kind]['paa_sha256']
    require(len(expected_sha_by_entry) == 2 * len(surface['tiles']), 'selected surface inventory mismatch')
    verify_replacement_scope(packed_entries, changed, expected_sha_by_entry)
    require(all(packed_entries[name] == (B / 'distribution/narva_trial' / name).read_bytes()
                for name in packed_entries), 'packed PBO entries differ from prepared distribution tree')
    # The deployed PBO file hash was already required to equal the packed PBO
    # hash above, so re-reading a second full payload map would add memory cost
    # without strengthening entry-level identity.
    del baseline_entries, packed_entries

    _, _, compiled_entries = read_pbo_checked(compiled_pbo)
    compiled_wrp = compiled_entries.get('baltic_trial.wrp', b'')
    expected_wrp_sha = deploy.get('compiled_wrp_sha256')
    # The deployed PBO file SHA was checked against the packed file before the
    # entry maps were released, so its WRP payload is byte-identical as well.
    deployed_wrp = packaged_wrp
    wrp_sha = verify_oprw_identity(compiled_wrp, packaged_wrp, deployed_wrp, expected_wrp_sha)
    require(expected_wrp_sha != BASE_COMPILED_WRP_SHA, 'EV95 compiled OPRW unexpectedly equals baseline')
    require(deploy.get('compiled_wrp_sha256') == digest(packaged_wrp), 'package receipt compiled OPRW digest mismatch')
    del compiled_entries
    water_pbo = PREVIEW_MOD / 'Addons/baltic_water_v30.pbo'
    require(sha(water_pbo) == deploy['files']['baltic_water_v30.pbo'], 'preview water PBO differs from package receipt')
    require(sha(water_pbo) == sha(BASE_ADDONS / 'baltic_water_v30.pbo'), 'preview water PBO differs from baseline')

    report = {
        'status': 'PASS_EV95_PACKAGED_OPRW_IDENTITY',
        'candidate_sha256': accepted['candidate_sha256'],
        'composition_report_sha256': accepted['receipt_sha256'],
        'composition_receipt_sha256': accepted['composition_receipt_sha256'],
        'composition_source_sha256': accepted['composition_source_sha256'],
        'sector_consumer_source_sha256': accepted['consumer_source_sha256'],
        'deploy_sha256': sha(deploy_path),
        'pbo_reader_sha256': ATTACH_NAVMESH_SHA,
        'baseline_pbo_sha256': sha(baseline_pbo),
        'packed_pbo_sha256': sha(packed_pbo),
        'deployed_pbo_sha256': sha(deployed_pbo),
        'actual_pbo_sha256': sha(deployed_pbo),
        'compiled_wrp_sha256': wrp_sha,
        'baseline_compiled_wrp_sha256': BASE_COMPILED_WRP_SHA,
        'staged_source_wrp_sha256': stage['staged_wrp_sha256'],
        'compiled_pbo_wrp_equals_packed_and_deployed': True,
        'all_nonchanged_pbo_entries_exact': True,
        'changed_entries': changed,
        'water_pbo_exact_to_baseline': True,
        'limitations': [
            'OPRW is checked as the exact AddonBuilder output carried through FileBank and preview PBO; this does not decode OPRW heights/objects.',
            'No engine load, native terrain readback, or visual acceptance is asserted.'
        ],
    }
    out = B / 'op_rw_verification.json'
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'changed_entries'}, indent=2))


if __name__ == '__main__':
    main()









