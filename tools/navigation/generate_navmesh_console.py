"""Run the installed NavMeshGenerator CLI against an already-owned data server.

Caller must launch/adopt the exact DayZ run through the shared MCP lifecycle and
hold/renew its lease. This script does not obtain ownership, launch/close DayZ,
or validate useful AI paths. Never use the generator's --kill option here.
CLI verified by NavMeshGenerator_x64.exe --console --help on 2026-10-03.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import struct
import subprocess
import uuid


GENERATOR = Path(r'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\NavMeshGenerator\NavMeshGenerator_x64.exe')
GENERATOR_SHA = '5f1e7cd1c19cb4701c4f7a0fa238fe6c1dcb52222c8a8716d7987ac014958b17'
GENERATOR_FORMATS = {
    GENERATOR_SHA: 6,
    # Installed 1.30.164.165: console help reverified 2026-10-25; engine requests v9.
    '66935ce864436892247cd520ea2205c179d661e6390478ec35a2c304aa2ecbb7': 9,
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-id', required=True, type=uuid.UUID)
    ap.add_argument('--world-pbo', required=True, type=Path)
    ap.add_argument('--world-sha256', required=True)
    ap.add_argument('--water-pbo', required=True, type=Path)
    ap.add_argument('--water-sha256', required=True)
    ap.add_argument('--additional-pbo', nargs=2, action='append', default=[], metavar=('PATH','SHA256'))
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--timeout-s', type=int, default=1800)
    a = ap.parse_args()
    if a.out.exists() or not 10 <= a.timeout_s <= 3600:
        raise ValueError('Fresh output directory and bounded timeout required')
    generator_sha = sha(GENERATOR)
    if generator_sha not in GENERATOR_FORMATS:
        raise ValueError('Generator changed; re-read its help before using this wrapper')
    canonical = lambda p: os.path.normcase(str(Path(p).resolve()))
    inputs = {canonical(a.world_pbo): a.world_sha256.lower(), canonical(a.water_pbo): a.water_sha256.lower()}
    for path,digest in a.additional_pbo:
        path = canonical(path)
        if path in inputs:
            raise ValueError('Duplicate additional PBO input')
        inputs[path] = digest.lower()
    if len(inputs) != 2+len(a.additional_pbo) or any(sha(Path(p)) != digest for p, digest in inputs.items()):
        raise ValueError('World/water input identity mismatch')
    a.out.mkdir(parents=True)
    navmesh = a.out.resolve() / 'baltic_trial.nm'
    argv = [str(GENERATOR), '--console', '--server_address', '127.0.0.1',
            '--reconnect', '1', str(navmesh)]
    receipt = dict(status='STARTED', run_id=str(a.run_id), started_utc=now(),
                   generator_sha256=generator_sha, expected_format_version=GENERATOR_FORMATS[generator_sha], argv=argv, inputs=inputs,
                   output=str(navmesh), limits=[
                       'Run identity is supplied by the caller, not attested by this script.',
                       'Caller must hold the MCP lease and prove the deployed mod stack.',
                       'Additional PBOs are caller-supplied; all loaded terrain/collision addons must be bound for reproducible generation.',
                       'File creation is not an AI/path acceptance verdict.'])
    receipt_path = a.out / 'generation.json'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    env = dict(os.environ)
    env['QT_COMMAND_LINE_PARSER_NO_GUI_MESSAGE_BOXES'] = '1'
    with (a.out / 'generator.stdout.log').open('xb') as stdout, (a.out / 'generator.stderr.log').open('xb') as stderr:
        try:
            result = subprocess.run(argv, cwd=a.out, env=env, stdout=stdout, stderr=stderr,
                                    timeout=a.timeout_s, creationflags=subprocess.CREATE_NO_WINDOW)
            receipt['returncode'] = result.returncode
        except subprocess.TimeoutExpired:
            # subprocess terminates only the child it created. It never closes
            # the managed DayZ data server, which remains under MCP lifecycle.
            receipt['returncode'] = None
            receipt['status'] = 'TIMEOUT'
        except OSError as exc:
            receipt['returncode'] = None
            receipt['status'] = 'LAUNCH_FAILED'
            receipt['error'] = str(exc)
    receipt['finished_utc'] = now()
    try:
        receipt['inputs_unchanged'] = all(sha(Path(p)) == digest for p, digest in inputs.items())
    except OSError as exc:
        receipt['inputs_unchanged'] = False
        receipt['status'] = 'POSTCHECK_FAILED'
        receipt['error'] = str(exc)
    receipt['navmesh_exists'] = navmesh.is_file()
    if navmesh.is_file():
        receipt['navmesh_bytes'] = navmesh.stat().st_size
        receipt['navmesh_sha256'] = sha(navmesh)
        with navmesh.open('rb') as stream:
            head = stream.read(48)
        if len(head) == 48:
            receipt['header'] = dict(zip(('magic', 'version', 'count', 'nx', 'nz'), struct.unpack_from('<5I', head)))
    h = receipt.get('header', {})
    header_ok = h.get('magic') == 0x4d534554 and h.get('version') == GENERATOR_FORMATS[generator_sha]
    header_ok = header_ok and h.get('count', 0) > 0 and h.get('count') == h.get('nx', 0) * h.get('nz', 0)
    receipt['header_ok'] = header_ok
    receipt['failure_reasons'] = []
    if receipt['returncode'] != 0:receipt['failure_reasons'].append('generator_exit_not_zero')
    if not receipt['inputs_unchanged']:receipt['failure_reasons'].append('input_drift_or_missing')
    if not header_ok:receipt['failure_reasons'].append('serialized_header_not_verified')
    if receipt['status'] == 'STARTED':
        receipt['status'] = ('GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION'
                             if receipt['returncode'] == 0 and header_ok and receipt['inputs_unchanged']
                             else 'GENERATION_FAILED')
        if receipt['returncode'] == 0 and receipt['inputs_unchanged'] and h.get('magic') == 0x4d534554 and h.get('version') == 9 and not header_ok:
            receipt['status'] = 'GENERATED_FILE_HEADER_LAYOUT_UNVERIFIED'
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('argv', 'inputs', 'limits')}, indent=2))
    return 0 if receipt['status'] == 'GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION' else 1


if __name__ == '__main__':
    raise SystemExit(main())
