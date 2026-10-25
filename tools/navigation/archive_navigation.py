"""Preserve the unaccepted pilot and measured evidence outside the live checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from waterway_common import ROOT, BASE, sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): raise ValueError('Fresh archive directory required')
    inputs=[ROOT/'HANDOFF.md',ROOT/'product-spec.md',ROOT/'plans/navigable-rivers.md',
            ROOT/'plans/terrain-first.md',BASE,
            ROOT/'tb/regional_clearance_v1/baltic_regional_objects_restored_v1.wrp',
            ROOT/'packages/baltic-navigation-v3/narva_navigation_derived.wrp',
            ROOT/'packages/baltic-navigation-v3/derived-verification.json',
            ROOT/'packages/baltic-navigation-v3/build/narva_navigation_v3/Addons/narva_trial.pbo',
            ROOT/'packages/baltic-navigation-v3/build/narva_navigation_v3/pbo-verification.json']
    directories=['evidence/navigation','tools/navigation','missions/BalticBoat.BalticTrial',
                 'tests/narva_navigation_v1','tests/narva_navigation_v2','tests/narva_navigation_v3']
    for relative in directories:
        for p in (ROOT/relative).rglob('*'):
            if p.is_symlink() or p.is_junction(): raise ValueError('Unexpected reparse point')
            if p.is_file() and '__pycache__' not in p.parts and not any(x.startswith('storage') for x in p.parts):
                inputs.append(p)
    if len(inputs)!=len(set(inputs)): raise ValueError('Duplicate archive input')
    manifest={'status':'PILOT_ARCHIVE_NOT_FINAL_TERRAIN_OR_NAVMESH',
              'limits':['Native TB import pending; copied native project remains the baseline.',
                        'Packaged navmesh is stale bootstrap, not validated for this WRP.',
                        'See runtime verification for actual measured scope, not an inference from packaging.'],
              'files':[{ 'path':str(p.relative_to(ROOT)).replace('\\','/'),
                         'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(inputs)]}
    args.out.mkdir(parents=True)
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    target=args.out/'baltic-navigation-pilot.zip'
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for p in sorted(inputs): archive.write(p,str(p.relative_to(ROOT)).replace('\\','/'))
        archive.write(args.out/'manifest.json','manifest.json')
    with zipfile.ZipFile(target) as archive:
        if len(archive.namelist())!=len(inputs)+1: raise ValueError('Archive count mismatch')
        for row in manifest['files']:
            content=archive.read(row['path'])
            if len(content)!=row['size'] or hashlib.sha256(content).hexdigest()!=row['sha256']:
                raise ValueError('Archive byte mismatch: '+row['path'])
    report={'status':'PASS_ARCHIVE_CONTENT','zip_sha256':sha(target),'entries':len(inputs)+1,
            'zip_bytes':target.stat().st_size,'zip_path':str(target)}
    (args.out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
