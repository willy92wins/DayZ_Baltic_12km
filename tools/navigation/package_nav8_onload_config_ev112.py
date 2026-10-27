"""Isolate only Nav8 OnLoad string true -> integer 1; never generate navigation."""
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


TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|[A-Za-z_]\w*|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?|[^\s]')
TARGET = 'filterIsolatedIslandsOnLoad'
TARGET_SCOPE = ('CfgWorlds', 'BalticTrial', 'Navmesh')
BASE_SHA = 'ac088ccbaff34ef7a5cbfe03b6e016fb6941895b9b253786f99b57578cf6d4ff'
NM_SHA = '360a7348b86bb9560352f2aead028fb6ec801f8d3bdd30526f43e0cb7e9efb23'
WRP_SHA = '0da63d3f258923e784a62bcb59bb1d7f2ab99866816f530bfe73cd4211b23254'


def tokens(text):
    return [m.group() for m in TOKEN.finditer(text)]


def scoped_fields(text):
    """Read only the three fixed declarations in CfgConvert's decoded output."""
    ts = tokens(text); stack = []; pending = None; found = {}
    names = (TARGET, 'filterIsolatedIslands', 'tileWidth')
    for i, token in enumerate(ts):
        if token == 'class':
            if i + 1 >= len(ts) or not re.fullmatch(r'[A-Za-z_]\w*', ts[i+1]):
                raise ValueError('Invalid class declaration')
            pending = ts[i+1]
        elif token == '{':
            stack.append(pending); pending = None
        elif token == '}':
            if not stack: raise ValueError('Unbalanced class braces')
            stack.pop()
        elif token == ';': pending = None
        elif token in names and i+1 < len(ts) and ts[i+1] == '=':
            if token in found or i+3 >= len(ts) or ts[i+3] != ';':
                raise ValueError('Duplicate or nonscalar protected declaration')
            found[token] = (tuple(x for x in stack if x), i+2, ts[i+2])
    if stack or set(found) != set(names): raise ValueError('Missing protected declarations')
    for name,scope in ((TARGET,TARGET_SCOPE),('filterIsolatedIslands',TARGET_SCOPE+('GenParams',)),('tileWidth',TARGET_SCOPE+('GenParams',))):
        if found[name][0] != scope: raise ValueError('Wrong class scope: '+name)
    if found['filterIsolatedIslands'][2] != '"true"' or found['tileWidth'][2] != '8':
        raise ValueError('Non-target generation parameters changed')
    return ts,found


def rewrite_onload(text):
    ts,fields=scoped_fields(text);index=fields[TARGET][1]
    if fields[TARGET][2] != '"true"': raise ValueError('Expected original string true')
    span=list(TOKEN.finditer(text))[index].span()
    return text[:span[0]]+'1'+text[span[1]:]


def verify_config_delta(before, after):
    left,lf=scoped_fields(before);right,rf=scoped_fields(after)
    if len(left)!=len(right): raise ValueError('Config token count changed')
    differences=[i for i,(a,b) in enumerate(zip(left,right)) if a!=b]
    if differences != [lf[TARGET][1]] or rf[TARGET][1]!=lf[TARGET][1]:
        raise ValueError('Expected exactly one target value token difference')
    if left[differences[0]]!='"true"' or right[differences[0]]!='1':
        raise ValueError('Expected string true to integer one')


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
    if a.expected_sha256 != BASE_SHA or a.wrp_sha256 != WRP_SHA or sha(raw) != BASE_SHA or sha(before['baltic_trial.wrp']) != WRP_SHA or sha(before['navmesh/baltic_trial.nm']) != NM_SHA:
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
    null_source = a.output / 'noop-source.cpp'
    null_source.write_text(text, encoding='utf-8')
    null_bin = a.output / 'noop.bin'
    run([a.converter, '-bin', '-dst', null_bin, null_source], 'compile-noop')
    null_text = a.output / 'noop.cpp'
    run([a.converter, '-txt', '-dst', null_text, null_bin], 'decode-noop')
    if null_bin.read_bytes() != before['config.bin'] or tokens(null_text.read_text(encoding='utf-8-sig')) != tokens(text):
        raise ValueError('Null compiler roundtrip changed baseline; stop and replan')
    source = a.output / 'config.cpp'
    source.write_text(rewrite_onload(text), encoding='utf-8')
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
    if after != expected or after_props != props:
        raise ValueError('Packed archive differs beyond verified config')
    packed_config = a.output / 'packed-config.bin'
    packed_config.write_bytes(after['config.bin'])
    packed_text = a.output / 'packed-config.cpp'
    run([a.converter, '-txt', '-dst', packed_text, packed_config], 'decode-packed')
    verify_config_delta(text, packed_text.read_text(encoding='utf-8-sig'))
    if sha(a.baseline.read_bytes()) != a.expected_sha256:
        raise ValueError('Baseline drift during packaging')
    result = dict(status='PASS_ISOLATED_NAV8_ONLOAD_CONFIG_PACKAGE', baseline_sha256=sha(raw),
                  pbo_sha256=sha(packed), pbo_bytes=len(packed), onload_before='true',
                  onload_source_literal='1', native_type_verified=False,
                  native_type_gate='Pending engine ConfigGetType==0 plus text 1 and numeric 1',
                  null_roundtrip_byte_equal=True, wrp_sha256=sha(after['baltic_trial.wrp']),
                  changed_entries=['config.bin'], unchanged_entries=len(before)-1,
                  config_sha256=sha(expected['config.bin']),
                  navmesh_sha256=sha(after['navmesh/baltic_trial.nm']),
                  tools={str(p):sha(p.read_bytes()) for p in (a.converter, a.filebank, Path(__file__))},
                  limits=['Same existing Nav8 NM; loader filtering and native607/RAM remain untested.',
                          'No geometry, terrain, transit, native path or performance acceptance.'])
    (a.output / 'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
