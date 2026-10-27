"""Create an isolated 8m generation input; preserve all non-config PBO entries.

Only the exact observed 12.5 -> 8 tileWidth experiment is supported. This is
packaging evidence, not navigation acceptance. All source archives stay intact.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'playtest'))
from attach_navmesh import read_pbo


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tokens(text):
    # Preserve quoted values, including their whitespace; ignore only layout.
    return re.findall(r'"(?:\\.|[^"\\])*"|\S', text)


def rewrite_tile_width(text):
    declarations = re.findall(r'\btileWidth\s*=\s*[^;]+;', text)
    if len(declarations) != 1 or not re.fullmatch(r'tileWidth\s*=\s*12\.5\s*;', declarations[0]):
        raise ValueError('Expected one observed tileWidth=12.5 declaration')
    return text.replace(declarations[0], 'tileWidth=8;', 1)


def verify_config_delta(before, after):
    if tokens(after) != tokens(rewrite_tile_width(before)):
        raise ValueError('Compiled configuration changed beyond tileWidth')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--expected-sha256', required=True)
    ap.add_argument('--wrp-sha256', required=True)
    ap.add_argument('--converter', type=Path, required=True)
    ap.add_argument('--filebank', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    raw, props, before = read_pbo(a.baseline)
    if sha(raw) != a.expected_sha256 or sha(before['baltic_trial.wrp']) != a.wrp_sha256:
        raise ValueError('Baseline identity mismatch')
    if props.get('prefix') != 'dayz_baltic_12km_dev\\tb\\narva_trial' or not before['config.bin'].startswith(b'\0raP'):
        raise ValueError('Unexpected world configuration or prefix')
    if a.output.exists() or not a.converter.is_file() or not a.filebank.is_file():
        raise ValueError('Fresh output and real tools required')
    a.output.mkdir(parents=True)

    def run(argv, label):
        p = subprocess.run(list(map(str, argv)), capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        (a.output / (label + '.log')).write_bytes(p.stdout + p.stderr)
        if p.returncode:
            raise RuntimeError(label + ' failed: ' + str(p.returncode))

    original = a.output / 'original.bin'
    original.write_bytes(before['config.bin'])
    decoded = a.output / 'original.cpp'
    run([a.converter, '-txt', '-dst', decoded, original], 'decode-original')
    text = decoded.read_text(encoding='utf-8-sig')
    source = a.output / 'config.cpp'
    source.write_text(rewrite_tile_width(text), encoding='utf-8')
    compiled = a.output / 'config.bin'
    run([a.converter, '-bin', '-dst', compiled, source], 'compile')
    roundtrip = a.output / 'roundtrip.cpp'
    run([a.converter, '-txt', '-dst', roundtrip, compiled], 'decode-candidate')
    verify_config_delta(text, roundtrip.read_text(encoding='utf-8-sig'))
    expected = dict(before)
    expected['config.bin'] = compiled.read_bytes()
    if not expected['config.bin'].startswith(b'\0raP') or expected['config.bin'] == before['config.bin']:
        raise ValueError('Compiled config missing or unchanged')
    stage = a.output / 'compiled/narva_trial'
    dest = a.output / 'Addons'
    stage.mkdir(parents=True)
    dest.mkdir()
    for name, data in expected.items():
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    argv = [a.filebank]
    for key, value in props.items():
        argv += ['-property', key + '=' + value]
    run(argv + ['-dst', dest, stage], 'filebank')
    packed, after_props, after = read_pbo(dest / 'narva_trial.pbo')
    if after != expected or any(after_props.get(k) != v for k, v in props.items()):
        raise ValueError('Packed archive differs beyond verified config')
    if sha(a.baseline.read_bytes()) != a.expected_sha256:
        raise ValueError('Baseline drift during packaging')
    result = dict(status='PASS_ISOLATED_NAV8_CONFIG_PACKAGE', baseline_sha256=sha(raw),
                  pbo_sha256=sha(packed), pbo_bytes=len(packed), tile_width_before=12.5,
                  tile_width_after=8., wrp_sha256=sha(after['baltic_trial.wrp']),
                  changed_entries=['config.bin'], unchanged_entries=len(before)-1,
                  config_sha256=sha(expected['config.bin']),
                  navmesh_sha256=sha(after['navmesh/baltic_trial.nm']),
                  tools={str(p):sha(p.read_bytes()) for p in (a.converter, a.filebank, Path(__file__))},
                  limits=['Generation input only; retained12.5m NM is not the proposed8m result.',
                          'No geometry, terrain, transit, native path or performance acceptance.'])
    (a.output / 'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
