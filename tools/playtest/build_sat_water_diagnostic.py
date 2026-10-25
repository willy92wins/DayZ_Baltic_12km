"""Build an undeployed diagnostic PBO: paint satellite-water pixels magenta.

Preserves the exact compiled world, materials, masks, configuration and navmesh.
Only S_*.paa and texture headers may differ. This distinguishes painted blue
satellite regions from actual rendered water; it is not an artistic map fix.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from PIL import Image
from attach_navmesh import read_pbo


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'source-layers', 'output', 'imagetopaa', 'binarize', 'filebank'):
        ap.add_argument('--'+name, type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise ValueError('Fresh output required')
    original, props, entries = read_pbo(a.baseline)
    if sha(original) != '3c3a2f0e649b13e73d483e027f3f3e50db58005848c85beb75321c7a50aa078f':
        raise ValueError('Expected current own-navmesh baseline')
    sats = [n for n in entries if re.fullmatch(r'data/layers/S_\d{3}_\d{3}_lco.paa', n)]
    if len(sats) != 25 or 'navmesh/baltic_trial.nm' not in entries:
        raise ValueError('Unexpected baseline content')
    stage = a.output/'compiled/narva_trial'
    source = a.output/'source'
    dest = a.output/'Addons'
    source.mkdir(parents=True)
    dest.mkdir()
    for name, content in entries.items():
        p = stage/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    results = []
    def run(argv, log):
        proc = subprocess.run([str(v) for v in argv], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (a.output/log).write_bytes(proc.stdout)
        if proc.returncode != 0:
            raise RuntimeError(f'{log}: exit {proc.returncode}')
    for name in sorted(sats):
        src = a.source_layers/(Path(name).stem+'.png')
        im = Image.open(src).convert('RGB')
        if im.size != (512, 512):
            raise ValueError('Unexpected satellite size')
        pixels = list(im.getdata())
        changed = sum(v == (103,165,192) for v in pixels)
        im.putdata([(230,35,175) if v == (103,165,192) else v for v in pixels])
        png = source/src.name
        im.save(png)
        run([a.imagetopaa, png, stage/name], 'convert-'+Path(name).stem+'.log')
        results.append({'name':name, 'source_sha256':sha(src.read_bytes()),
                        'painted_water_pixels':changed, 'candidate_sha256':sha((stage/name).read_bytes())})
    headers = a.output/'headers'
    headers.mkdir()
    run([a.binarize, '-texheader', '-silent', stage, headers], 'texheader.log')
    header = headers/'texHeaders.bin'
    if not header.is_file() or not header.stat().st_size:
        raise ValueError('No fresh texture headers')
    (stage/'texHeaders.bin').write_bytes(header.read_bytes())
    run([a.filebank, '-property', 'prefix='+props['prefix'], '-property', 'product=dayz ugc',
         '-dst', dest, stage], 'filebank.log')
    packed, pprops, final = read_pbo(dest/'narva_trial.pbo')
    if final.keys() != entries.keys() or pprops != props:
        raise ValueError('Unexpected entries or properties')
    changes = [n for n in entries if entries[n] != final[n]]
    allowed = set(sats) | {'texHeaders.bin'}
    if not changes or not set(changes) <= allowed:
        raise ValueError('Change outside satellite and headers')
    record = {'status':'PASS_OFFLINE_DIAGNOSTIC_ONLY', 'deployed':False,
              'baseline_sha256':sha(original), 'candidate_sha256':sha(packed),
              'entries':len(final), 'changes':changes, 'satellites':results,
              'invariants':{n:sha(final[n]) for n in ('baltic_trial.wrp','config.bin','navmesh/baltic_trial.nm')},
              'runtime_status':'NOT_RUN',
              'interpretation':{'blue_turns_magenta':'Satellite imagery contributes to the affected region.',
                                'blue_stays_blue':'Rendered water or another channel; verify control visible before interpreting.',
                                'controls_not_visible':'Inconclusive; check loaded artifact, position, opacity and current scene.'},
              'limit':'This does not fix tiling or water geometry; restore exact baseline after the controlled comparison.'}
    (a.output/'verification.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='satellites'},indent=2))


if __name__ == '__main__':
    main()
