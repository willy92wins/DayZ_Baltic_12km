"""Validate every changed EV95 texture mip and its native largest-mip decode.

Run after packaging and OPRW identity readback. This does not build, package,
deploy, load DayZ, or claim GPU/engine streaming acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

from wide_build_common import (EV87_BUILD, W, acceptance_args,
                               load_accepted_inputs, sha)

B = Path(__file__).parent
AUDIT_PATH = W / 'evidence/v30-full-mipmap-audit-2026-10-09/audit_mipmaps.py'
AUDIT_SHA256 = '2d7912c8ea4411ec07c1ad9def7c21dfa7bb09c9a3bb44739fb55090cb9f28f2'
PBO_READER_PATH = W / 'tools/playtest/attach_navmesh.py'
PBO_READER_SHA256 = '717b81469e0a799690d1586cd7a4492f079c3b2db626eec7e2815cd15896e062'
PAA_DECODER_PATH = Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-3d-viewer/dayz_3d_viewer/paa_to_png.py')
PAA_DECODER_SHA256 = '0c59c372b21b62cb7c0d7318e8a195e7bd84e3af15558944b41bd5ac05ad812b'
LZO_DECODER_PATH = Path('C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts/lzo_decompress.py')
LZO_DECODER_SHA256 = '5ecb852cca9f38258121e2b5246ff8ba438d672b04390442e2e536bc080b8658'
IMAGE_TO_PAA = Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/ImageToPAA/ImageToPAA.exe')
IMAGE_TO_PAA_SHA256 = '0b786037fc708931bcc85088ba69648bcf57463bcf3b1d3a21a35f29b9c2344a'
EXPECTED_MIP_SIZES = [512, 256, 128, 64, 32, 16, 8, 4]
TEXTURE_RE = re.compile(r'^(?P<kind>[sm])_(?P<a>\d{3})_(?P<b>\d{3})_lc[oa]\.paa$', re.I)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_audit():
    if sha(AUDIT_PATH) != AUDIT_SHA256:
        raise ValueError(f'pinned mip audit source changed: {AUDIT_PATH}')
    if sha(PBO_READER_PATH) != PBO_READER_SHA256:
        raise ValueError(f'pinned PBO reader source changed: {PBO_READER_PATH}')
    if sha(PAA_DECODER_PATH) != PAA_DECODER_SHA256:
        raise ValueError(f'pinned PAA decoder source changed: {PAA_DECODER_PATH}')
    if sha(LZO_DECODER_PATH) != LZO_DECODER_SHA256:
        raise ValueError(f'pinned LZO decoder source changed: {LZO_DECODER_PATH}')
    if sha(IMAGE_TO_PAA) != IMAGE_TO_PAA_SHA256:
        raise ValueError(f'pinned native ImageToPAA tool changed: {IMAGE_TO_PAA}')
    spec = importlib.util.spec_from_file_location('ev95_pinned_audit_mipmaps', AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot load pinned mip audit: {AUDIT_PATH}')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    audit.B = B
    audit.TOOL = IMAGE_TO_PAA
    return audit


def expected_surface_mips(surface: dict) -> dict[str, dict]:
    """Index only the exact generated layer records; reject ambiguity."""
    indexed: dict[str, dict] = {}
    for item in surface.get('files', []):
        tile = item.get('tile')
        files = item.get('files')
        if not isinstance(tile, list) or len(tile) != 2 or not isinstance(files, dict):
            raise ValueError('surface artifact row has an unexpected shape')
        a, b = tile
        for kind, suffix in (('s', 'lco'), ('m', 'lca')):
            record = files.get(kind)
            if not isinstance(record, dict) or not record.get('paa_sha256') or not record.get('decoded_sha256'):
                raise ValueError(f'surface artifact row lacks {kind} PAA/decode hashes')
            name = f'{kind}_{int(a):03d}_{int(b):03d}_{suffix}.paa'
            if name in indexed:
                raise ValueError(f'duplicate generated surface artifact: {name}')
            indexed[name] = record
    if not indexed:
        raise ValueError('surface verification contains no generated PAA artifacts')
    return indexed


def validate_changed_texture_names(names: list[str]) -> list[str]:
    if not names:
        raise ValueError('package declares no changed texture entries')
    normalized = sorted(names)
    if len(normalized) != len(set(normalized)):
        raise ValueError('package changed texture entries contain duplicates')
    for name in normalized:
        base = Path(name).name
        if not TEXTURE_RE.fullmatch(base):
            raise ValueError(f'changed texture entry has unexpected name: {name}')
        if base != name and '/' not in name.replace('\\', '/'):
            raise ValueError(f'changed texture entry path is malformed: {name}')
    kinds = {Path(name).name[0].lower() for name in normalized}
    if not kinds <= {'s', 'm'}:
        raise ValueError('changed texture kinds are outside the supported PAA classes')
    return normalized


def main() -> None:
    if not __debug__:
        raise RuntimeError('refusing optimized Python: the pinned mip decoder uses assertions for binary invariants')
    parser = argparse.ArgumentParser(description=__doc__)
    acceptance_args(parser)
    args = parser.parse_args()
    accepted = load_accepted_inputs(args.composition_receipt)
    audit = load_audit()

    surface_path = B / 'surface-verification.json'
    deploy_path = B / 'deploy.json'
    oprw_path = B / 'op_rw_verification.json'
    surface = json.loads(surface_path.read_text(encoding='utf-8'))
    deploy = json.loads(deploy_path.read_text(encoding='utf-8'))
    oprw = json.loads(oprw_path.read_text(encoding='utf-8'))
    if surface.get('status') != 'PASS_EV95_AFFECTED_SURFACE' or not surface.get('gates') or not all(surface['gates'].values()):
        raise ValueError('surface verification is absent or not PASS')
    if deploy.get('status') != 'PACKAGED_EV95_WIDE_PREVIEW_NATIVE_READBACK_PENDING':
        raise ValueError('package receipt is absent or not the expected EV95 isolated preview')
    if oprw.get('status') != 'PASS_EV95_PACKAGED_OPRW_IDENTITY':
        raise ValueError('packaged OPRW identity readback is absent or not PASS')
    for artifact in (surface, deploy):
        if artifact.get('terrain_sha256') != accepted['candidate_sha256']:
            raise ValueError('artifact candidate identity differs from accepted EV95 candidate')
        if artifact.get('ev95_composition_receipt_sha256') != accepted['receipt_sha256']:
            raise ValueError('artifact receipt identity differs from accepted EV95 receipt')
            raise ValueError('artifact pool identity differs from selected compound pool')
        if artifact.get('ev95_composition_source_sha256') != accepted['composition_source_sha256']:
            raise ValueError('artifact selector source identity differs from reviewed selector')
        if artifact.get('ev95_sector_consumer_sha256') != accepted['consumer_source_sha256']:
            raise ValueError('artifact consumer source identity differs from reviewed consumer')

    pbo = Path(deploy.get('mod', '')).resolve() / 'Addons/narva_trial.pbo'
    if not pbo.is_file() or sha(pbo) != deploy.get('files', {}).get('narva_trial.pbo'):
        raise ValueError('actual isolated preview PBO is missing or differs from deploy receipt')
    if sha(B / 'packed/narva_trial.pbo') != sha(pbo):
        raise ValueError('packed and deployed preview PBO bytes differ')
    if (oprw.get('candidate_sha256') != accepted['candidate_sha256'] or
            oprw.get('composition_report_sha256') != accepted['receipt_sha256'] or
            oprw.get('composition_receipt_sha256') != accepted['composition_receipt_sha256'] or
            oprw.get('composition_source_sha256') != accepted['composition_source_sha256'] or
            oprw.get('sector_consumer_source_sha256') != accepted['consumer_source_sha256'] or
            oprw.get('deploy_sha256') != sha(deploy_path) or
            oprw.get('actual_pbo_sha256') != sha(pbo)):
        raise ValueError('OPRW readback does not cover these exact EV95 package inputs')
    _, _, entries = audit.read_pbo(pbo)

    changed = validate_changed_texture_names(deploy.get('changed_texture_entries', []))
    expected = expected_surface_mips(surface)
    changed_basenames = [Path(name).name for name in changed]
    if len(changed_basenames) != len(set(changed_basenames)) or set(changed_basenames) - set(expected):
        raise ValueError('changed texture entry does not resolve to one generated surface artifact')
    reports = []
    native_controls = []
    controlled_kinds: set[str] = set()
    decoded_dir = B / 'decoded'
    for name in changed:
        if name not in entries:
            raise ValueError(f'changed texture entry missing from actual PBO: {name}')
        base = Path(name).name
        match = TEXTURE_RE.fullmatch(base)
        if match is None:
            raise ValueError(f'changed texture entry has an unsupported basename: {name}')
        kind = match.group('kind').lower()
        blob = entries[name]
        if digest(blob) != expected[base]['paa_sha256']:
            raise ValueError(f'PBO mip bytes do not match generated EV95 PAA: {name}')
        layer = B / 'surface/layers' / base
        if not layer.is_file() or layer.read_bytes() != blob:
            raise ValueError(f'generated layer PAA is absent or differs from actual PBO: {name}')
        decoded = decoded_dir / (Path(base).stem + '.png')
        if not decoded.is_file() or sha(decoded) != expected[base]['decoded_sha256']:
            raise ValueError(f'native largest-mip decode is absent or differs from surface receipt: {name}')
        mip_report = audit.verify_one(blob, kind, decoded)
        if [level['size'] for level in mip_report['levels']] != EXPECTED_MIP_SIZES:
            raise ValueError(f'PAA does not contain the complete expected mip chain: {name}')
        reports.append({'name': name, 'sha256': digest(blob), **mip_report})
        if kind not in controlled_kinds:
            for index in (3, 7):
                native_controls.append(audit.isolate_native(blob, name, index))
            controlled_kinds.add(kind)

    if not controlled_kinds or controlled_kinds != {Path(name).name[0].lower() for name in changed}:
        raise ValueError('native mip controls did not cover every changed texture class')
    first = entries[changed[0]]
    negative = audit.must_reject('truncated_changed_texture_rejected', first[:-12])
    report = {
        'status': 'PASS_EV95_ALL_CHANGED_MIPS',
        'candidate_sha256': accepted['candidate_sha256'],
        'composition_report_sha256': accepted['receipt_sha256'],
        'composition_receipt_sha256': accepted['composition_receipt_sha256'],
        'composition_source_sha256': accepted['composition_source_sha256'],
        'sector_consumer_source_sha256': accepted['consumer_source_sha256'],
        'surface_verification_sha256': sha(surface_path),
        'deploy_sha256': sha(deploy_path),
        'op_rw_verification_sha256': sha(oprw_path),
        'actual_pbo_sha256': sha(pbo),
        'pinned_sources': {
            'audit_mipmaps_sha256': AUDIT_SHA256,
            'pbo_reader_sha256': PBO_READER_SHA256,
            'paa_decoder_sha256': PAA_DECODER_SHA256,
            'lzo_decoder_sha256': LZO_DECODER_SHA256,
            'ImageToPAA_sha256': IMAGE_TO_PAA_SHA256,
        },
        'changed_texture_count': len(reports),
        'decoded_mip_count': sum(len(item['levels']) for item in reports),
        'unchanged_entries_exact': deploy.get('unchanged_entries'),
        'negative_control': negative,
        'native_mip_controls': native_controls,
        'files': reports,
        'limits': [
            'Every package-declared changed PAA is decoded at all eight mip levels; nonchanged PBO entries are checked by verify_packaged_oprw.py.',
            'This is offline native-tool validation and does not prove GPU streaming, engine loading, or visual acceptance.',
        ],
    }
    output = B / 'changed-mips.json'
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'files'}, indent=2))


if __name__ == '__main__':
    main()









