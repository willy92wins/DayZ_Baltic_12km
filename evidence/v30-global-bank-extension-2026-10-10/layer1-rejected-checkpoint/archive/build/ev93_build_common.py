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
PREVIEW_MOD = Path(r'P:/Mods/@DayZ_Baltic_EV93_GlobalBankPreviewV1')


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
    parser.add_argument('--authoring-receipt', type=Path, required=True,
                        help='EV93 fairing-layer1/authoring.json from the actual run')
    parser.add_argument('--consumer-report', type=Path, required=True,
                        help='independent EV93 global consumer report from the actual run')


def load_accepted_inputs(receipt_path: Path, report_path: Path) -> dict:
    """Require a real EV93 authored candidate and its exact independent PASS."""
    receipt_path, report_path = receipt_path.resolve(), report_path.resolve()
    if not receipt_path.is_file() or not report_path.is_file():
        raise FileNotFoundError('EV93 authoring receipt and consumer report are both required')
    receipt, report = read_json(receipt_path), read_json(report_path)
    if receipt.get('status') != 'AUTHORED_PENDING_GLOBAL_CONSUMER':
        raise ValueError(f"EV93 receipt is not authored: {receipt.get('status')!r}")
    if report.get('status') != 'PASS_INCREMENTAL_NONREGRESSION':
        raise ValueError(f"EV93 independent consumer did not PASS: {report.get('status')!r}")
    gates = report.get('gates')
    if not isinstance(gates, dict) or not gates or not all(value is True for value in gates.values()):
        raise ValueError('EV93 consumer gates are absent or not all true')
    info = report.get('information')
    if not isinstance(info, dict):
        raise ValueError('EV93 consumer information block is missing')
    if info.get('global_contract_status') != 'OPEN_INHERITED_MAP_DEFECTS':
        raise ValueError('EV93 global contract status is unexpected; preview is not a map-completion claim')
    if info.get('candidate_sha256') != receipt.get('candidate_sha256'):
        raise ValueError('consumer candidate SHA does not match author receipt')
    if info.get('prepared_sha256') != receipt.get('prepared_sha256'):
        raise ValueError('consumer prepared SHA does not match author receipt')
    if info.get('authoring_receipt_sha256') != sha(receipt_path):
        raise ValueError('consumer did not read this exact authoring receipt')
    for receipt_key, report_key in (
            ('ledger_sha256', 'ledger_sha256'),
            ('index_manifest_sha256', 'index_manifest_sha256'),
            ('index_verification_sha256', 'index_verification_sha256')):
        if not receipt.get(receipt_key) or info.get(report_key) != receipt.get(receipt_key):
            raise ValueError(f'consumer {report_key} does not match author receipt')
    if int(info.get('changed_vertices', -1)) != int(receipt.get('changed_vertices', -2)):
        raise ValueError('consumer changed-vertex count does not match author receipt')
    candidate = Path(receipt.get('candidate_path', '')).resolve()
    if not candidate.is_file() or sha(candidate) != receipt.get('candidate_sha256'):
        raise ValueError('EV93 candidate path/SHA is absent or mismatched')
    dynamic_inputs = info.get('input_hashes')
    if not isinstance(dynamic_inputs, dict) or not dynamic_inputs:
        raise ValueError('consumer dynamic input hash set is missing')
    for raw_path, expected in dynamic_inputs.items():
        path = Path(raw_path)
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f'EV93 consumer input changed after PASS: {path}')
    return {
        'receipt_path': receipt_path,
        'receipt_sha256': sha(receipt_path),
        'consumer_report_path': report_path,
        'consumer_report_sha256': sha(report_path),
        'candidate_path': candidate,
        'candidate_sha256': receipt['candidate_sha256'],
        'prepared_sha256': receipt['prepared_sha256'],
        'authoring_receipt': receipt,
        'consumer_report': report,
        'changed_vertices': int(info.get('changed_vertices', -1)),
        'input_hashes': dynamic_inputs,
    }


def add_acceptance_manifest(target: dict, accepted: dict) -> dict:
    target.update({
        'ev93_authoring_receipt': str(accepted['receipt_path']),
        'ev93_authoring_receipt_sha256': accepted['receipt_sha256'],
        'ev93_consumer_report': str(accepted['consumer_report_path']),
        'ev93_consumer_report_sha256': accepted['consumer_report_sha256'],
        'ev93_candidate': str(accepted['candidate_path']),
        'ev93_candidate_sha256': accepted['candidate_sha256'],
        'ev93_prepared_sha256': accepted['prepared_sha256'],
        'ev93_changed_vertices': accepted['changed_vertices'],
        'ev93_consumer_input_hashes': accepted['input_hashes'],
        'baseline_world_pbo_sha256': WORLD_PBO_SHA,
        'baseline_water_pbo_sha256': WATER_PBO_SHA,
        'baseline_terrain_sha256': BASE_TERRAIN_SHA,
        'baseline_water_plane_sha256': BASE_WATER_PLANE_SHA,
        'baseline_visible_field_sha256': BASE_VISIBLE_FIELD_SHA,
        'status_scope': 'isolated EV93 preview preparation; not promoted and not map-completion acceptance',
    })
    return target


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

