"""Fail-closed build admission for the REC global dry preview; no native claims."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

G = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
EV82 = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010')
EV95 = G / 'build-wide-slope'
EV87_BUILD = Path(r'E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/build')
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
RECOVERY_RUN = G / 'global-operator-prototype/global-dry-rollback-frozen-recovery/run-01'
RECOVERY_RECEIPT = RECOVERY_RUN / 'receipt.json'
RECOVERY_CANDIDATE = RECOVERY_RUN / 'candidate-terrain.npz'
V2_CONSUMER = G / 'global-operator-prototype/global-dry-rollback/postsolve-consumer/instrumented-v2/verify_global_dry_rollback_v2.py'
V2_RUNS = V2_CONSUMER.parent / 'runs'
EV95_DEPLOY = EV95 / 'deploy.json'
EV95_STAGE = EV95 / 'stage.json'
BASE_ADDONS = Path(r'P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons')
PREVIEW_MOD = Path(r'P:/Mods/@DayZ_Baltic_GlobalDryPreviewV1')

RECOVERY_RECEIPT_SHA = '1b06ba46cfc1a8539cc21ccd8fb1b43c0cb1ed3fbd85cd18dcb9233c376cd866'
RECOVERY_CANDIDATE_SHA = '1bd6b67dc7cfa340c762f878776de157c74c368a7a836484c8f7271c276d1795'
V2_CONSUMER_SHA = '8ab83e18b9e746e0119f3c22f32c8c4332f277d9128a7edb7252dd108f94e72a'
EV95_CANDIDATE = EV95 / 'candidate/terrain.npz'
EV95_CANDIDATE_SHA = '40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a'
EV95_DEPLOY_SHA = 'f5a9c8185812e0b77a804ef9811e0405b5a7969f8ccfc19b85cc29d23cac03ca'
EV95_STAGE_SHA = 'b04b066d99f9c22a4fffd77c66762d3e9e744dfa2bbf20d8508f076845571dda'

BASE_TERRAIN_SHA = 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
BASE_WATER_PLANE_SHA = '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'
BASE_VISIBLE_FIELD_SHA = 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'
BASE_SOURCE_WRP_SHA = '3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6'
BASE_COMPILED_WRP_SHA = '3b12b21d554c6ab75d76c43b5ba902c9a1d49a26516bdd14b16f1a6048ba2539'
BASE_REFERENCE_INPUTS_SHA = 'feb562be42082cdd3749242d470330947a7a299b0c983df26b39b8b436a8216c'
EV82_SURFACE_HELPER_SHA = 'e4cdc3fd50b49ed8d66f32c13e84655cc2796b8d5a52b9c01cbcf5881c245f08'
WORLD_PBO_SHA = 'b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c'
WATER_PBO_SHA = '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'

V2_STATUS = 'PASS_GLOBAL_DRY_ROLLBACK_CANDIDATE'
V2_GATES = {
    'domain_exact', 'physical_bounds_and_water_clearance', 'd8_no_new_minima',
    'face_slope_hinge_sector', 'protected_water_p9_civil_retained',
    'compiled_water_face_support', 'original_objective_strict_improvement',
    'source_readset_start_end_equal',
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def blob_sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError(f'Expected JSON object: {path}')
    return value


def verify_map(mapping: dict, label: str) -> None:
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError(f'{label} must be a non-empty path/SHA map')
    for raw_path, expected in mapping.items():
        path = Path(raw_path)
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f'{label} hash mismatch: {path}')


def require_metadata_exact(candidate: dict, ev95: dict, baseline_b: dict) -> None:
    """Require identical NPZ keys and byte-exact non-height arrays across sources."""
    if set(candidate) != set(ev95) or set(candidate) != set(baseline_b):
        raise ValueError('candidate array schema differs from EV95/EV82 B')
    for name in candidate:
        if name == 'heights':
            continue
        value, prior, base = (np.asarray(candidate[name]), np.asarray(ev95[name]), np.asarray(baseline_b[name]))
        if (value.dtype != prior.dtype or value.shape != prior.shape or value.tobytes() != prior.tobytes() or
                value.dtype != base.dtype or value.shape != base.shape or value.tobytes() != base.tobytes()):
            raise ValueError(f'candidate metadata differs from EV95 or EV82 B: {name}')


def validate_consumer_contract(report: dict, report_sha256: str,
                               supplied_sha256: str) -> dict:
    """Validate V2's emitted contract without trusting any author status."""
    if not supplied_sha256 or report_sha256 != supplied_sha256:
        raise ValueError('explicit consumer report SHA does not match its bytes')
    if report.get('schema') != 'global-dry-rollback.independent-consumer.v1':
        raise ValueError('unexpected V2 consumer report schema')
    if report.get('status') != V2_STATUS:
        raise ValueError('V2 consumer status is not PASS_GLOBAL_DRY_ROLLBACK_CANDIDATE')
    gates = report.get('gates')
    if not isinstance(gates, dict) or set(gates) != V2_GATES or any(value is not True for value in gates.values()):
        raise ValueError('V2 gate set is incomplete, extended, or not all true')
    if Path(report.get('candidate_path', '')).resolve() != RECOVERY_CANDIDATE.resolve():
        raise ValueError('consumer candidate path differs from frozen REC candidate')
    if report.get('candidate_sha256') != RECOVERY_CANDIDATE_SHA:
        raise ValueError('consumer candidate SHA differs from frozen REC candidate')
    if Path(report.get('recovery_receipt_path', '')).resolve() != RECOVERY_RECEIPT.resolve():
        raise ValueError('consumer receipt path differs from frozen REC receipt')
    if report.get('recovery_receipt_sha256') != RECOVERY_RECEIPT_SHA:
        raise ValueError('consumer receipt SHA differs from frozen REC receipt')
    starts, ends = report.get('source_pins_start'), report.get('source_pins_end')
    if not isinstance(starts, dict) or not starts or starts != ends or report.get('source_readset_equal') is not True:
        raise ValueError('consumer source pins do not form a stable start/end readset')
    if starts.get(str(RECOVERY_CANDIDATE.resolve())) != RECOVERY_CANDIDATE_SHA:
        raise ValueError('consumer readset does not pin REC candidate')
    if starts.get(str(RECOVERY_RECEIPT.resolve())) != RECOVERY_RECEIPT_SHA:
        raise ValueError('consumer readset does not pin REC receipt')
    if starts.get(str(V2_CONSUMER.resolve())) != V2_CONSUMER_SHA:
        raise ValueError('consumer readset does not pin approved V2 source')
    if starts.get(str(EV95_CANDIDATE.resolve())) != EV95_CANDIDATE_SHA:
        raise ValueError('consumer readset does not pin EV95 base terrain')
    if starts.get(str(EV95_DEPLOY.resolve())) != EV95_DEPLOY_SHA or starts.get(str(EV95_STAGE.resolve())) != EV95_STAGE_SHA:
        raise ValueError('consumer readset does not pin EV95 deploy/stage lineage')
    instrumentation = report.get('instrumentation')
    if not isinstance(instrumentation, dict) or instrumentation.get('last_phase') != 'complete_source_end_hash':
        raise ValueError('V2 report does not record completion through end-source hashing')
    domain = report.get('domain')
    if not isinstance(domain, dict) or domain.get('pass') is not True:
        raise ValueError('V2 domain result missing or not passing')
    changed_vs_ev95 = domain.get('changed_vertices')
    if type(changed_vs_ev95) is not int or changed_vs_ev95 <= 0:
        raise ValueError('V2 changed-vertex count vs EV95 missing or invalid')
    return {'changed_vertices_vs_ev95': changed_vs_ev95,
            'candidate_path': RECOVERY_CANDIDATE,
            'candidate_sha256': RECOVERY_CANDIDATE_SHA,
            'recovery_receipt_path': RECOVERY_RECEIPT,
            'recovery_receipt_sha256': RECOVERY_RECEIPT_SHA,
            'consumer_source_path': V2_CONSUMER,
            'consumer_source_sha256': V2_CONSUMER_SHA,
            'consumer_report_sha256': supplied_sha256,
            'report': report}


def acceptance_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--consumer-report', type=Path, required=True)
    parser.add_argument('--consumer-sha256', required=True)


def load_accepted_inputs(report_path: Path, report_sha256: str) -> dict:
    report_path = Path(report_path).resolve()
    try:
        relative_report = report_path.relative_to(V2_RUNS.resolve())
    except ValueError as exc:
        raise ValueError('V2 report must live under the instrumented consumer runs directory') from exc
    if len(relative_report.parts) != 2 or relative_report.name != 'report.json':
        raise ValueError('V2 report path must be runs/<attempt>/report.json')
    if not report_path.is_file() or sha(report_path) != report_sha256:
        raise ValueError('explicit V2 consumer report path/SHA mismatch')
    if sha(V2_CONSUMER) != V2_CONSUMER_SHA:
        raise ValueError('V2 consumer source pin changed')
    if sha(RECOVERY_RECEIPT) != RECOVERY_RECEIPT_SHA or sha(RECOVERY_CANDIDATE) != RECOVERY_CANDIDATE_SHA:
        raise ValueError('REC receipt or candidate pin changed')
    receipt = read_json(RECOVERY_RECEIPT)
    if (receipt.get('status') != 'PENDING_INDEPENDENT_CONSUMER' or
            receipt.get('terrain_written') is not True or
            Path(receipt.get('candidate_path', '')).resolve() != RECOVERY_CANDIDATE.resolve() or
            receipt.get('candidate_sha256') != RECOVERY_CANDIDATE_SHA or
            receipt.get('source_readset_equal') is not True or
            receipt.get('source_readset_start') != receipt.get('source_readset_end')):
        raise ValueError('frozen REC receipt is not the expected stable candidate receipt')
    accepted = validate_consumer_contract(read_json(report_path), report_sha256, report_sha256)
    accepted['consumer_report_path'] = report_path
    accepted['receipt'] = receipt
    # Revalidate the complete readset the independent consumer reports before
    # every stage. This catches drift between acceptance and build operations.
    verify_map(accepted['report']['source_pins_start'], 'V2 consumer source readset')
    if sha(report_path) != report_sha256:
        raise ValueError('V2 consumer report changed during admission')
    return accepted


def verify_baseline_pbos() -> None:
    if sha(BASE_ADDONS / 'narva_trial.pbo') != WORLD_PBO_SHA:
        raise ValueError('EV82 baseline world PBO mismatch')
    if sha(BASE_ADDONS / 'baltic_water_v30.pbo') != WATER_PBO_SHA:
        raise ValueError('EV82 baseline water PBO mismatch')


def verify_baseline_reference_inputs() -> Path:
    reference = EV87_BUILD / 'reference-inputs.json'
    if sha(reference) != BASE_REFERENCE_INPUTS_SHA:
        raise ValueError('EV82 baseline reference-inputs hash mismatch')
    value = read_json(reference)
    if not (value.get('status') == 'PASS_EV82_COMPOSITE_REFERENCE' and
            value.get('world_sha256') == WORLD_PBO_SHA and
            value.get('water_sha256') == WATER_PBO_SHA and
            value.get('compiled_wrp_sha256') == BASE_COMPILED_WRP_SHA and
            value.get('source_terrain_sha256') == BASE_TERRAIN_SHA and
            value.get('entries') == 6827):
        raise ValueError('EV82 reference inputs identity mismatch')
    return reference


def add_acceptance_manifest(target: dict, accepted: dict) -> dict:
    target.update({
        'global_dry_consumer_report': str(accepted['consumer_report_path']),
        'global_dry_consumer_report_sha256': accepted['consumer_report_sha256'],
        'global_dry_consumer_source': str(accepted['consumer_source_path']),
        'global_dry_consumer_source_sha256': accepted['consumer_source_sha256'],
        'recovery_receipt': str(accepted['recovery_receipt_path']),
        'recovery_receipt_sha256': accepted['recovery_receipt_sha256'],
        'candidate_terrain': str(accepted['candidate_path']),
        'candidate_terrain_sha256': accepted['candidate_sha256'],
        'changed_vertices_vs_ev95': accepted['changed_vertices_vs_ev95'],
        'baseline_world_pbo_sha256': WORLD_PBO_SHA,
        'baseline_water_pbo_sha256': WATER_PBO_SHA,
        'baseline_terrain_sha256': BASE_TERRAIN_SHA,
        'baseline_water_plane_sha256': BASE_WATER_PLANE_SHA,
        'baseline_visible_field_sha256': BASE_VISIBLE_FIELD_SHA,
        'status_scope': 'isolated global dry rollback preview; no native, visual, or promotion claim',
    })
    return target
