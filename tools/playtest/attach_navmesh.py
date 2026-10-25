"""Attach a generated .nm using FileBank, preserving every original PBO entry.

The baseline must be the exact PBO whose world fed NavMeshGenerator. This does
not invoke Binarize or AddonBuilder. It rejects an unapproved existing navmesh, raw config,
wrong WRP hash, compressed input, reused staging/output and any post-pack delta
except the specified .nm. FileBank CLI verified from the installed -help.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_pbo(path):
    data = path.read_bytes()
    offset = 0
    table = []
    props = {}

    def string():
        nonlocal offset
        end = data.index(b'\0', offset)
        value = data[offset:end].decode('utf-8')
        offset = end + 1
        return value

    while True:
        name = string()
        mime, original, reserved, timestamp, size = struct.unpack_from('<5I', data, offset)
        offset += 20
        if not name:
            if mime == 0x56657273:
                while True:
                    key = string()
                    if not key:
                        break
                    props[key] = string()
                continue
            break
        if mime != 0:
            raise ValueError(f'Compressed entry requires a decoder: {name}')
        key = name.replace('\\', '/')
        if key.startswith('/') or ':' in key or any(p in ('', '.', '..') for p in key.split('/')):
            raise ValueError(f'Unsafe archive path: {name}')
        table.append((key, size))
    entries = {}
    for name, size in table:
        if name.lower() in {n.lower() for n in entries}:
            raise ValueError(f'Duplicate entry: {name}')
        content = data[offset:offset + size]
        offset += size
        if len(content) != size:
            raise ValueError(f'Truncated entry: {name}')
        entries[name] = content
    return data, props, entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--navmesh', required=True, type=Path)
    parser.add_argument('--wrp-sha256', required=True)
    parser.add_argument('--filebank', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--replace-existing-sha256', help='Explicit hash of the previous own navmesh; omit for first attachment')
    args = parser.parse_args()
    baseline, props, before = read_pbo(args.baseline)
    wrp = before['baltic_trial.wrp']
    if sha(wrp) != args.wrp_sha256.lower() or not wrp.startswith(b'OPRW'):
        raise ValueError('Baseline WRP does not match the generation input')
    if not before['config.bin'].startswith(b'\0raP'):
        raise ValueError('Missing compiled world config')
    nav_entry = 'navmesh/baltic_trial.nm'
    existing_nav = [k for k in before if k.lower().endswith('.nm')]
    replacing = args.replace_existing_sha256 is not None
    if any(k.lower().endswith('.cpp') for k in before):
        raise ValueError('Unexpected raw config in baseline')
    if replacing:
        if existing_nav != [nav_entry] or sha(before[nav_entry]) != args.replace_existing_sha256.lower():
            raise ValueError('Previous own navmesh identity mismatch')
    elif existing_nav:
        raise ValueError('Existing navmesh requires its explicit expected hash')
    if props.get('prefix') != 'dayz_baltic_12km_dev\\tb\\narva_trial':
        raise ValueError('Unexpected baseline prefix')
    nav = args.navmesh.read_bytes()
    if len(nav) < 32:
        raise ValueError('Navmesh absent or too small; inspect generator output')
    if not args.filebank.is_file() or args.output.exists():
        raise ValueError('FileBank must exist and output must be fresh')
    stage = args.output / 'compiled/narva_trial'
    dest = args.output / 'Addons'
    stage.mkdir(parents=True)
    dest.mkdir()
    expected = dict(before)
    expected[nav_entry] = nav
    for name, data in expected.items():
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    argv = [str(args.filebank), '-property', 'prefix=' + props['prefix'], '-property', 'product=dayz ugc', '-dst', str(dest), str(stage)]
    result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    (args.output / 'filebank.log').write_bytes(result.stdout)
    if result.returncode:
        raise RuntimeError(f'FileBank failed: {result.returncode}')
    packed, after_props, after = read_pbo(dest / 'narva_trial.pbo')
    if after != expected or after_props.get('prefix') != props['prefix']:
        raise ValueError('Packed content differs beyond the added navmesh')
    receipt = {
        'status': 'PASS_NAVMESH_PACKED_BYTE_PARITY',
        'baseline_pbo_sha256': sha(baseline),
        'pbo_sha256': sha(packed), 'pbo_bytes': len(packed),
        'wrp_sha256': sha(wrp), 'navmesh_sha256': sha(nav), 'navmesh_bytes': len(nav),
        'original_entries_unchanged': len(before)-int(replacing), 'final_entries': len(after),
        'added_entry': None if replacing else nav_entry,
        'replaced_entry': nav_entry if replacing else None,
        'previous_navmesh_sha256': sha(before[nav_entry]) if replacing else None,
        'binarize_invoked': False,
        'limits': ['Offline packaging only; own navmesh load and useful AI paths require runtime validation.'],
    }
    (args.output / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
