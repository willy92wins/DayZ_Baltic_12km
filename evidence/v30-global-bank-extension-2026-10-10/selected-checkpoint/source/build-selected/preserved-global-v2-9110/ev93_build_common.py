"""Fail-closed provenance gates shared by the EV93 preview preparation scripts.

This module only validates existing receipts and source identities. It does not
run a terrain build, pack an addon, deploy files, or create a mission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

G = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
EV82 = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010')
EV87_BUILD = Path(r'E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/build')
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
BASE_ADDONS = Path(r'P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons')
WATER_PBO_SHA = '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
WORLD_PBO_SHA = 'b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c'
BASE_TERRAIN_SHA = 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
BASE_WATER_PLANE_SHA = '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'
BASE_VISIBLE_FIELD_SHA = 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'
BASE_SOURCE_WRP_SHA = '3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6'
BASE_COMPILED_WRP_SHA = '3b12b21d554c6ab75d76c43b5ba902c9a1d49a26516bdd14b16f1a6048ba2539'
BASE_REFERENCE_INPUTS_SHA = 'feb562be42082cdd3749242d470330947a7a299b0c983df26b39b8b436a8216c'
EV82_SURFACE_HELPER_SHA = 'e4cdc3fd50b49ed8d66f32c13e84655cc2796b8d5a52b9c01cbcf5881c245f08'
EV87_NATIVE_V2_VERIFIER_SOURCE_SHA = 'be9a531e9ca1fdd663ebe4064345f821b2fb185d0c2e0479522d834cc1689f0c'
PREVIEW_MOD = Path(r'P:/Mods/@DayZ_Baltic_EV93_SelectedBankPreviewV1')
SELECTOR_SOURCE = G / 'compound-selection/selector.py'
SELECTOR_SOURCE_SHA = '0d29d3979c1f8bc0d3b0b1833edb314a5807fe5b22ba63b43c44080732fe81bc'
SELECTED_LOCAL_CONSUMER_SOURCE = G / 'crest-extension/verify_selected_composite.py'
SELECTED_LOCAL_CONSUMER_SOURCE_SHA = '8cd8f28b7914936bdf86f884b18bd14eb11aeca306f24327851dda340f16a543'
SELECTED_GLOBAL_CONSUMER_SOURCE = G / 'crest-extension/verify_selected_composite_v2.py'
SELECTED_GLOBAL_CONSUMER_SOURCE_SHA = '9110f2aac2d84722e5c48b379aacb51d6983f6a79daf8bf4395090f32dc2ece7'


def sha(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def blob_sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path | str) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def acceptance_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--selection-receipt', type=Path, required=True,
                        help='compound-selection/selection.json from the actual selector run')
    parser.add_argument('--consumer-report', type=Path, required=True,
                        help='independent EV93 global consumer report from the actual run')


def verify_baseline_pbos() -> None:
    world = BASE_ADDONS / 'narva_trial.pbo'
    water = BASE_ADDONS / 'baltic_water_v30.pbo'
    if sha(world) != WORLD_PBO_SHA:
        raise ValueError(f'baseline world PBO identity changed: {world}')
    if sha(water) != WATER_PBO_SHA:
        raise ValueError(f'baseline water PBO identity changed: {water}')


def verify_baseline_reference_inputs() -> Path:
    path = EV87_BUILD / 'reference-inputs.json'
    if sha(path) != BASE_REFERENCE_INPUTS_SHA:
        raise ValueError(f'EV82 composite reference inputs changed: {path}')
    reference = read_json(path)
    expected = (reference.get('status') == 'PASS_EV82_COMPOSITE_REFERENCE' and
                reference.get('world_sha256') == WORLD_PBO_SHA and
                reference.get('water_sha256') == WATER_PBO_SHA and
                reference.get('compiled_wrp_sha256') == BASE_COMPILED_WRP_SHA and
                reference.get('source_terrain_sha256') == BASE_TERRAIN_SHA and
                reference.get('entries') == 6827)
    if not expected:
        raise ValueError('EV82 composite reference identity/shape mismatch')
    return path


def load_accepted_inputs(selection_path: Path, report_path: Path) -> dict:
    """Require an exact SELECTED receipt and its independent consumer PASS."""
    selection_path, report_path = selection_path.resolve(), report_path.resolve()
    if not selection_path.is_file() or not report_path.is_file():
        raise FileNotFoundError('EV93 selection receipt and consumer report are both required')
    selection, report = read_json(selection_path), read_json(report_path)
    if selection.get('schema') != 'ev93.compound-selection.v1' or selection.get('status') != 'SELECTED':
        raise ValueError('selection receipt is not ev93.compound-selection.v1 / SELECTED')

    selector_path = Path(selection.get('selector_source_path', '')).resolve()
    if selector_path != SELECTOR_SOURCE.resolve() or selection.get('selector_sha256') != SELECTOR_SOURCE_SHA:
        raise ValueError('selection selector source path/SHA differs from the reviewed freeze')
    if sha(selector_path) != SELECTOR_SOURCE_SHA:
        raise ValueError('live selector source SHA differs from the reviewed freeze')
    candidate_ref = selection.get('candidate')
    if not isinstance(candidate_ref, dict) or candidate_ref.get('metadata_equal_to_B') is not True:
        raise ValueError('selection has no candidate with exact B metadata')
    candidate = Path(candidate_ref.get('path', '')).resolve()
    candidate_sha = candidate_ref.get('sha256')
    if not candidate.is_file() or not candidate_sha or sha(candidate) != candidate_sha:
        raise ValueError('selected candidate path/SHA is absent or mismatched')
    pool_path = Path(selection.get('compound_pool_path', '')).resolve()
    pool_sha = selection.get('compound_pool_sha256')
    if not pool_path.is_file() or not pool_sha or sha(pool_path) != pool_sha:
        raise ValueError('selected compound pool path/SHA is absent or mismatched')
    base_path = Path(selection.get('base_path', '')).resolve()
    if (base_path != (EV82 / 'candidate/terrain.npz').resolve() or
            selection.get('base_sha256') != BASE_TERRAIN_SHA or sha(base_path) != BASE_TERRAIN_SHA):
        raise ValueError('selection baseline terrain identity differs from pinned B')

    units, retained, excluded = (selection.get('units'), selection.get('retained_unit_ids'),
                                 selection.get('excluded_unit_ids'))
    if not isinstance(units, list) or not isinstance(retained, list) or not isinstance(excluded, list):
        raise ValueError('selection unit rows or retained/excluded lists are missing')
    by_id = {row.get('unit_id'): row for row in units if isinstance(row, dict)}
    all_ids = set(by_id)
    if (len(by_id) != len(units) or len(retained) != len(set(retained)) or
            len(excluded) != len(set(excluded))):
        raise ValueError('selection unit rows or ID lists contain duplicates')
    if set(retained) & set(excluded) or set(retained) | set(excluded) != all_ids:
        raise ValueError('selection retained/excluded IDs do not partition all unit rows')
    row_retained = {uid for uid, row in by_id.items() if row.get('selection_status') == 'retained'}
    retained_crests = [by_id[uid] for uid in retained if uid.startswith('crest:')]
    if (row_retained != set(retained) or not retained_crests or
            not any(int(row.get('changed_vertices', 0)) > 0 for row in retained_crests)):
        raise ValueError('selection rows do not confirm a retained crest unit')

    if report.get('status') != 'PASS_INCREMENTAL_NONREGRESSION':
        raise ValueError(f"selected independent consumer did not PASS: {report.get('status')!r}")
    gates = report.get('gates')
    if not isinstance(gates, dict) or not gates or not all(value is True for value in gates.values()):
        raise ValueError('selected consumer gates are absent or not all true')
    info = report.get('information')
    if not isinstance(info, dict):
        raise ValueError('selected consumer information block is missing')
    if info.get('global_contract_status') != 'OPEN_INHERITED_MAP_DEFECTS':
        raise ValueError('consumer global contract status is unexpected')
    if info.get('selection_sha256') != sha(selection_path):
        raise ValueError('consumer did not read this exact selection receipt')
    if info.get('compound_pool_sha256') != pool_sha:
        raise ValueError('consumer compound pool SHA differs from selection receipt')
    if (info.get('candidate_sha256') != candidate_sha or
            Path(info.get('candidate_path', '')).resolve() != candidate):
        raise ValueError('consumer candidate path/SHA differs from selected candidate')
    consumer_path = Path(info.get('consumer_source_path', '')).resolve()
    if (consumer_path != SELECTED_GLOBAL_CONSUMER_SOURCE.resolve() or
            info.get('consumer_source_sha256') != SELECTED_GLOBAL_CONSUMER_SOURCE_SHA or
            sha(consumer_path) != SELECTED_GLOBAL_CONSUMER_SOURCE_SHA):
        raise ValueError('global consumer source path/SHA differs from reviewed v2 freeze')
    if not isinstance(info.get('input_hashes_expected'), dict) or info['input_hashes_expected'].get(
            str(consumer_path)) != SELECTED_GLOBAL_CONSUMER_SOURCE_SHA:
        raise ValueError('global consumer expected read-set does not bind its v2 source')
    if int(info.get('retained_crest_units', 0)) < 1 or int(info.get('changed_vertices', 0)) < 1:
        raise ValueError('consumer did not confirm a nontrivial candidate and retained crest')

    expected = info.get('input_hashes_expected')
    started = info.get('input_hashes_start')
    ended = info.get('input_hashes_end')
    if not isinstance(expected, dict) or not expected or expected != started or expected != ended:
        raise ValueError('consumer expected/start/end read-set hashes do not match')
    source_read_set = selection.get('source_read_set')
    if not isinstance(source_read_set, dict) or not source_read_set:
        raise ValueError('selection source read-set is missing')
    if (source_read_set.get(str(selector_path)) != SELECTOR_SOURCE_SHA or
            source_read_set.get(str(pool_path)) != pool_sha or
            source_read_set.get(str(base_path)) != BASE_TERRAIN_SHA or
            source_read_set.get(str(SELECTED_LOCAL_CONSUMER_SOURCE.resolve())) != SELECTED_LOCAL_CONSUMER_SOURCE_SHA or
            sha(SELECTED_LOCAL_CONSUMER_SOURCE) != SELECTED_LOCAL_CONSUMER_SOURCE_SHA):
        raise ValueError('selection read-set does not bind selector, pool, baseline, and local verifier identities')
    for raw_path, digest in source_read_set.items():
        canonical = str(Path(raw_path).resolve())
        if expected.get(canonical) != digest:
            raise ValueError(f'global consumer expected read-set omits or disagrees with selection source: {canonical}')
    for raw_path, digest in expected.items():
        path = Path(raw_path)
        if not path.is_file() or sha(path) != digest:
            raise ValueError(f'consumer input changed after PASS: {path}')
    for raw_path, digest in source_read_set.items():
        path = Path(raw_path)
        if not path.is_file() or sha(path) != digest:
            raise ValueError(f'selection source read-set drifted: {path}')

    return {
        'receipt_path': selection_path,
        'receipt_sha256': sha(selection_path),
        'selector_source_path': selector_path,
        'selector_source_sha256': SELECTOR_SOURCE_SHA,
        'consumer_report_path': report_path,
        'consumer_report_sha256': sha(report_path),
        'consumer_source_path': consumer_path,
        'consumer_source_sha256': SELECTED_GLOBAL_CONSUMER_SOURCE_SHA,
        'candidate_path': candidate,
        'candidate_sha256': candidate_sha,
        'selection_receipt': selection,
        'consumer_report': report,
        'changed_vertices': int(info['changed_vertices']),
        'input_hashes': expected,
        'compound_pool_path': pool_path,
        'compound_pool_sha256': pool_sha,
        'retained_crest_units': int(info['retained_crest_units']),
    }


def add_acceptance_manifest(target: dict, accepted: dict) -> dict:
    target.update({
        'ev93_selection_receipt': str(accepted['receipt_path']),
        'ev93_selection_receipt_sha256': accepted['receipt_sha256'],
        'ev93_selector_source': str(accepted['selector_source_path']),
        'ev93_selector_source_sha256': accepted['selector_source_sha256'],
        'ev93_consumer_report': str(accepted['consumer_report_path']),
        'ev93_consumer_report_sha256': accepted['consumer_report_sha256'],
        'ev93_consumer_source': str(accepted['consumer_source_path']),
        'ev93_consumer_source_sha256': accepted['consumer_source_sha256'],
        'ev93_candidate': str(accepted['candidate_path']),
        'ev93_candidate_sha256': accepted['candidate_sha256'],
        'ev93_compound_pool': str(accepted['compound_pool_path']),
        'ev93_compound_pool_sha256': accepted['compound_pool_sha256'],
        'ev93_changed_vertices': accepted['changed_vertices'],
        'ev93_retained_crest_units': accepted['retained_crest_units'],
        'ev93_consumer_input_hashes': accepted['input_hashes'],
        'baseline_world_pbo_sha256': WORLD_PBO_SHA,
        'baseline_water_pbo_sha256': WATER_PBO_SHA,
        'baseline_terrain_sha256': BASE_TERRAIN_SHA,
        'baseline_water_plane_sha256': BASE_WATER_PLANE_SHA,
        'baseline_visible_field_sha256': BASE_VISIBLE_FIELD_SHA,
        'status_scope': 'isolated EV93 selected-bank preview; not promoted and not map-completion acceptance',
    })
    return target

