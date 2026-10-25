"""One controlled OutsideTerrain material-only config variant; exact PBO parity."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from attach_navmesh import read_pbo, sha


def run(argv, log):
    result = subprocess.run([str(v) for v in argv], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log.write_bytes(result.stdout)
    if result.returncode:
        raise RuntimeError(f'Tool failed: {result.returncode}')


def remove_class(text, name):
    match = re.search(r'\bclass\s+' + re.escape(name) + r'\s*\{', text)
    if not match:
        raise ValueError(f'Missing class {name}')
    depth = 1
    end = match.end()
    while depth:
        if text[end] == '{':
            depth += 1
        elif text[end] == '}':
            depth -= 1
        end += 1
    end = text.index(';', end) + 1
    return text[:match.start()] + text[end:]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'cfgconvert', 'filebank', 'output'):
        ap.add_argument('--' + name, type=Path, required=True)
    ap.add_argument('--baseline-sha256', required=True)
    ap.add_argument('--disable-synth', action='store_true', help='Separate second discriminator, matching the official DayZ Utes sample')
    a = ap.parse_args()
    raw, props, entries = read_pbo(a.baseline)
    if sha(raw) != a.baseline_sha256.lower() or a.output.exists():
        raise ValueError('Expected baseline and fresh output required')
    if any(k.lower().endswith('.cpp') for k in entries):
        raise ValueError('Raw source in baseline')
    a.output.mkdir(parents=True)
    original_bin = a.output / 'baseline-config.bin'
    original_bin.write_bytes(entries['config.bin'])
    original_cpp = a.output / 'baseline-config.cpp'
    run([a.cfgconvert, '-txt', '-dst', original_cpp, original_bin], a.output / 'decode.log')
    source = original_cpp.read_text(encoding='utf-8-sig')
    if 'OutsideTerrain' in source or source.count('class UsedTerrainMaterials') != 1:
        raise ValueError('Unexpected config structure')
    block = r'''class OutsideTerrain
        {
            satellite="DZ\worlds\chernarusplus\data\outside_sat_co.paa";
            class Layers
            {
                class Layer0
                {
                    nopx="DZ\surfaces\data\terrain\cp_grass_nopx.paa";
                    texture="DZ\surfaces\data\terrain\cp_grass_ca.paa";
                };
            };
        };
        '''
    if a.disable_synth:
        block = block.replace('class Layers', 'enableTerrainSynth=0;\n            class Layers')
    candidate_cpp = a.output / 'candidate-config.cpp'
    candidate_cpp.write_text(source.replace('class UsedTerrainMaterials', block + 'class UsedTerrainMaterials'), encoding='utf-8')
    candidate_bin = a.output / 'candidate-config.bin'
    run([a.cfgconvert, '-bin', '-dst', candidate_bin, candidate_cpp], a.output / 'compile.log')
    decoded = a.output / 'candidate-decoded.cpp'
    run([a.cfgconvert, '-txt', '-dst', decoded, candidate_bin], a.output / 'decode-candidate.log')
    candidate_text = decoded.read_text(encoding='utf-8-sig')
    # Config converter canonicalizes whitespace; all original values must remain.
    if re.sub(r'\s+', '', remove_class(candidate_text, 'OutsideTerrain')) != re.sub(r'\s+', '', source):
        raise ValueError('Config changed outside the new material block')
    if not a.disable_synth and 'enableTerrainSynth' in candidate_text:
        raise ValueError('Geometry synthesis is outside this experiment')
    if a.disable_synth and not re.search(r'enableTerrainSynth\s*=\s*0;', candidate_text):
        raise ValueError('Requested exterior synthesis switch missing')
    stage = a.output / 'compiled/narva_trial'
    dest = a.output / 'Addons'
    stage.mkdir(parents=True)
    dest.mkdir()
    expected = dict(entries)
    expected['config.bin'] = candidate_bin.read_bytes()
    for name, content in expected.items():
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    run([a.filebank, '-property', 'prefix=' + props['prefix'], '-property', 'product=dayz ugc', '-dst', dest, stage], a.output / 'filebank.log')
    packed, packed_props, after = read_pbo(dest / 'narva_trial.pbo')
    if after != expected or packed_props.get('prefix') != props['prefix']:
        raise ValueError('Unexpected packed delta')
    report = {'status': 'PASS_CONFIG_ONLY_VARIANT', 'baseline_pbo_sha256': sha(raw),
              'pbo_sha256': sha(packed), 'changed_entries': ['config.bin'],
              'unchanged_entries': len(entries)-1, 'wrp_sha256': sha(after['baltic_trial.wrp']),
              'navmesh_sha256': sha(after['navmesh/baltic_trial.nm']),
              'disable_exterior_synth': a.disable_synth,
              'runtime': 'PENDING_CONTROLLED_VISUAL_COMPARISON'}
    (a.output / 'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
