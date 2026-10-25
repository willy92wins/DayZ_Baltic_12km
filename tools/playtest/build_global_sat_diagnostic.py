"""Isolated Stage0-global experiment. Never edits TB sources or deploys a PBO."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from PIL import Image
from attach_navmesh import read_pbo

BASELINE = '3c3a2f0e649b13e73d483e027f3f3e50db58005848c85beb75321c7a50aa078f'
SAT = 'data/layers/baltic_global_lco.paa'
STAGE0 = re.compile(r'class Stage0\s*\{[^{}]*\};')
GEN3 = re.compile(r'class TexGen3\s*\{\s*uvSource="worldPos";\s*class uvTransform\s*\{(?:[^{}]|\{[^{}]*\})*\};\s*\};')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rest(text):
    """Compare all compiled-consumer fields outside the deliberate edit."""
    if len(STAGE0.findall(text)) != 1 or len(GEN3.findall(text)) != 1:
        raise ValueError('Expected unique satellite Stage0 and TexGen3/worldPos')
    return re.sub(r'\s+', '', GEN3.sub('', STAGE0.sub('', text)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'satellite', 'output', 'imagetopaa', 'cfgconvert', 'binarize', 'filebank'):
        ap.add_argument('--' + name, type=Path, required=True)
    a = ap.parse_args()
    original, props, before = read_pbo(a.baseline)
    if sha(original) != BASELINE or a.output.exists():
        raise ValueError('Exact baseline and fresh output required')
    with Image.open(a.satellite) as im:
        if im.size != (2048, 2048) or im.mode != 'RGB':
            raise ValueError('Expected the existing opaque RGB 2048 square satellite')
    mats = sorted(n for n in before if n.lower().endswith('.rvmat'))
    if len(mats) != 367 or len(before) != 421 or SAT in before:
        raise ValueError('Unexpected baseline contents')
    stage = a.output / 'compiled/narva_trial'
    src = a.output / 'source'
    readback = a.output / 'readback'
    dest = a.output / 'Addons'
    for d in (src, readback, dest):
        d.mkdir(parents=True)
    for name, content in before.items():
        p = stage / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    logs = []

    def run(argv):
        p = subprocess.run([str(x) for x in argv], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logs.append({'argv': [str(x) for x in argv], 'exit': p.returncode,
                     'output': p.stdout.decode('utf-8', errors='replace')})
        if p.returncode:
            (a.output / 'commands.json').write_text(json.dumps(logs, indent=2))
            raise RuntimeError(f'Tool failed: {argv[0]}, exit {p.returncode}')

    run([a.imagetopaa, a.satellite, stage / SAT])
    texpath = props['prefix'] + '\\' + SAT.replace('/', '\\')
    transform = '''class TexGen3
{
    uvSource="worldPos";
    class uvTransform
    {
        aside[]={0.00008138020833333333,0,0};
        up[]={0,0,0.00008138020833333333};
        dir[]={0,-0.00008138020833333333,0};
        pos[]={0,1,0};
    };
};'''
    checks = []
    for name in mats:
        source = src / (Path(name).name + '.cpp')
        baseline_txt = src / (Path(name).name + '.before.cpp')
        final_txt = readback / (Path(name).name + '.cpp')
        run([a.cfgconvert, '-txt', '-dst', baseline_txt, stage / name])
        text = baseline_txt.read_text()
        if not re.fullmatch(r'class Stage0\s*\{\s*texture="[^"]+";\s*texGen=3;\s*\};', STAGE0.findall(text)[0]):
            raise ValueError(f'Unexpected Stage0 contract: {name}')
        old_rest = rest(text)
        new = STAGE0.sub(lambda _: 'class Stage0\n{\n    texture="' + texpath + '";\n    texGen=3;\n};', text)
        new = GEN3.sub(lambda _: transform, new)
        source.write_text(new)
        run([a.cfgconvert, '-bin', '-dst', stage / name, source])
        run([a.cfgconvert, '-txt', '-dst', final_txt, stage / name])
        back = final_txt.read_text()
        if old_rest != rest(back) or texpath not in STAGE0.findall(back)[0]:
            raise ValueError(f'Consumer readback differs outside satellite edit: {name}')
        for path in re.findall(r'texture="([^"]+)"', back):
            if path.startswith('#'):
                continue
            if path.lower().startswith(props['prefix'].lower() + '\\'):
                disk = stage / path[len(props['prefix']) + 1:].replace('\\', '/')
            else:
                disk = Path('P:/') / path.replace('\\', '/')
            if not disk.is_file():
                raise ValueError(f'Missing texture {path}')
        checks.append({'name': name, 'nonsatellite_fields_unchanged': True,
                       'before': sha(before[name]), 'after': sha((stage / name).read_bytes())})
    headers = a.output / 'headers'
    headers.mkdir()
    run([a.binarize, '-texheader', '-silent', stage, headers])
    header = (headers / 'texHeaders.bin').read_bytes()
    if not header:
        raise ValueError('Empty fresh headers')
    (stage / 'texHeaders.bin').write_bytes(header)
    run([a.filebank, '-property', 'prefix=' + props['prefix'], '-property', 'product=dayz ugc', '-dst', dest, stage])
    packed, pp, after = read_pbo(dest / 'narva_trial.pbo')
    changes = [n for n in before if before[n] != after.get(n)]
    if pp != props or set(after) != set(before) | {SAT} or set(changes) != set(mats) | {'texHeaders.bin'}:
        raise ValueError('Packed entry changes outside the experiment')
    report = {'status': 'PASS_OFFLINE_DIAGNOSTIC_ONLY', 'runtime_status': 'NOT_RUN',
              'baseline_sha256': sha(original), 'candidate_sha256': sha(packed),
              'source_satellite_sha256': sha(a.satellite.read_bytes()),
              'entries': len(after), 'unchanged_entries': len(before) - len(changes),
              'changed_materials': len(mats), 'added': SAT,
              'invariants': {n: sha(after[n]) for n in ('baltic_trial.wrp', 'config.bin', 'navmesh/baltic_trial.nm')},
              'material_checks': checks,
              'limit': 'Global Stage0 only; no TB source edits. 6m/px prototype artwork. Requires aerial and close engine validation.'}
    (a.output / 'commands.json').write_text(json.dumps(logs, indent=2) + '\n')
    (a.output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'material_checks'}, indent=2))


if __name__ == '__main__':
    main()
