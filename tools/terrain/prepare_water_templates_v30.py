"""Prepare a distinct V30 water template library and absolute import rows.

The XML contract is derived from the native V29 library. All existing hashes,
centres and radii are checked before producing a candidate. Consumer acceptance
still requires a native import/export: this utility does not edit a TB project.
"""
from pathlib import Path
import argparse
import copy
import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

import numpy as np

sys.path.insert(0, r'C:\Users\guill\DayZ-Modding-Knowledge-Pack\tools\py3d')
import py3d
from wrp0wzd import read

BASE = Path('E:/DayZ-Baltic-Build/editor-v30-delta/native-asc/TemplateLibs/Baltic_Water_V2.tml')
WORLD = Path('E:/DayZ-Baltic-Build/v30-shore-finish-package/world/stage/BalticTrialWorld/baltic_trial.wrp')
EXPECTED = '96eb126b7dfb7e2e2e84542b8f1c8776bc30ded210df588349634afafaa32a15'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def name_hash(name):
    value = 0
    for byte in name.encode('ascii'):
        value = (value * 65599 + byte) & 0xffffffff
    return value if value < 2**31 else value - 2**32


def vector(t, key):
    return np.array([float(t.find(key).get(axis)) for axis in 'XYZ'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--world', type=Path, default=WORLD)
    ap.add_argument('--world-sha256', default=EXPECTED)
    ap.add_argument('--models-root', type=Path, default=Path('P:/'))
    ap.add_argument('--object-count', type=int, default=17622)
    ap.add_argument('--model-count', type=int, default=13419)
    ap.add_argument('--name-prefix', default='v30_')
    ap.add_argument('--library-name', default='Baltic_Water_V30')
    ap.add_argument('--pieces-manifest', type=Path)
    args = ap.parse_args()
    if args.out.exists() or sha(args.world) != args.world_sha256.lower():
        raise ValueError('Fresh output and exact staged world required')
    assert args.name_prefix.isascii() and args.name_prefix.replace('_','').isalnum()
    assert args.library_name.isascii() and args.library_name.replace('_','').isalnum()
    manifest=None
    if args.pieces_manifest:
        manifest=json.loads(args.pieces_manifest.read_text(encoding='utf-8'))
        assert manifest['instances']==args.object_count and manifest['models']==args.model_count
        manifest={m['name']:m['sha256'] for m in manifest['model_list']}
    base = ET.parse(BASE).getroot()
    templates = base.findall('Template')
    assert len(templates) == 6187
    old_errors = []
    for t in templates:
        low, high, center = [vector(t, key) for key in ('BoundingMin', 'BoundingMax', 'BoundingCenter')]
        size = high-low
        delta = max(np.max(abs(center-(low+high)/2)), abs(float(t.findtext('BBRadius'))-size[2]/2))
        old_errors.append(float(delta))
        assert name_hash(t.findtext('Name')) == int(t.findtext('Hash'))
        assert delta <= 2e-6 and t.findtext('AutoCenter') == '1'
        # The native UI rectangle stores half its Z span and an X/Z ratio.
        # XML reference values have six decimals; narrow pieces amplify that
        # serialization rounding in the ratio.
        assert np.isclose(float(t.findtext('BBHScale')), size[0]/size[2], rtol=2e-6, atol=1e-6)
    objects = [o for o in read(args.world)['objects'] if o['name'].startswith('baltic_water_v30\\')]
    assert len(objects) == args.object_count
    paths = sorted({o['name'] for o in objects})
    assert len(paths) == args.model_count
    library = ET.Element('Library', dict(base.attrib, name=args.library_name))
    names, model_receipts = {}, []
    for number, relative in enumerate(paths):
        p = args.models_root / relative.replace('\\', '/')
        raw = p.read_bytes()
        assert raw[:4] == b'MLOD'
        if manifest is not None:assert hashlib.sha256(raw).hexdigest()==manifest[p.stem]
        with p.open('rb') as stream:
            model = py3d.P3D(stream)
        points = np.array([(0., 0., 0.)] + [v.coords for lod in model.lods for v in lod.points], dtype=np.float32)
        assert np.isfinite(points).all() and np.all(points[:, 1] == 0)
        low, high = points.min(0), points.max(0)
        center = (low+high)/np.float32(2)
        name = args.name_prefix + p.stem
        names[relative] = name
        t = copy.deepcopy(templates[0])
        t.find('Name').text = name
        t.find('File').text = relative
        t.find('Date').text = 'Sat Oct 03 00:00:00 2026'
        t.find('Hash').text = str(name_hash(name))
        size = high-low
        assert size[2] > 0
        t.find('BBRadius').text = format(float(size[2]/2), '.9g')
        t.find('BBHScale').text = format(float(size[0]/size[2]), '.9g')
        for key, values in [('BoundingMin', low), ('BoundingMax', high), ('BoundingCenter', center)]:
            for axis, value in zip('XYZ', values):
                t.find(key).set(axis, format(float(value), '.9g'))
        library.append(t)
        model_receipts.append(dict(file=relative, template=name, sha256=hashlib.sha256(raw).hexdigest(),
                                   bounding_min=low.tolist(), bounding_max=high.tolist(), center=center.tolist()))
        if number % 2000 == 0:
            print(f'Prepared {number}/{len(paths)} model templates', flush=True)
    assert len(set(names.values())) == len(paths)
    assert len({name_hash(n) for n in names.values()}) == len(paths), 'Hash collision'
    peers = list(BASE.parent.glob('*.tml'))
    peer_hashes = {int(t.findtext('Hash')) for path in peers
                   for t in ET.parse(path).getroot().findall('Template')}
    assert not peer_hashes & {name_hash(n) for n in names.values()}, 'Collision with a loaded native library'
    rows = []
    for o in objects:
        m = o['matrix']
        assert m[:9] == [1.,0.,0.,0.,1.,0.,0.,0.,1.]
        x,y,z = m[9:]
        row = f'"{names[o["name"]]}";{200000+x:.17g};{z:.17g};0;0;0;1;{y:.17g};'
        f = next(csv.reader([row], delimiter=';'))
        assert np.array_equal(np.array([float(f[1])-200000,float(f[7]),float(f[2])],dtype=np.float32), np.array(m[9:],dtype=np.float32))
        rows.append(row)
    args.out.mkdir(parents=True)
    tml, txt = args.out/(args.library_name+'.tml'), args.out/'water_v30_named_absolute.txt'
    ET.indent(library, space='  ')
    ET.ElementTree(library).write(tml, encoding='utf-8', xml_declaration=True)
    txt.write_text('\n'.join(rows)+'\n', encoding='ascii', newline='\n')
    reread = ET.parse(tml).getroot().findall('Template')
    assert len(reread) == len(paths)
    assert set(t.findtext('Name') for t in reread) == set(names.values())
    result = dict(status='PREPARED_NATIVE_CONSUMER_PENDING', templates=len(paths), objects=len(rows),
                  library=str(tml), library_sha256=sha(tml), csv=str(txt), csv_sha256=sha(txt),
                  reference_library_sha256=sha(BASE), staged_world_sha256=sha(args.world),
                  source_models_root=str(args.models_root), name_prefix=args.name_prefix,
                  pieces_manifest_sha256=sha(args.pieces_manifest) if args.pieces_manifest else None,
                  reference_templates_checked=len(templates), reference_max_bbox_relation_error_m=max(old_errors),
                  sources=model_receipts,
                  limits=['Name hash 65599 polynomial verified against all 6187 native reference entries.',
                          'XML schema and placement semantics require native import/export acceptance.',
                          'CSV uses canonical WRP translations, absolute elevation; do not import as relative.',
                          'Old water layer must be replaced in the isolated project; all nine bridges remain.',
                          'Distinct v30_ names avoid basename conflicts with the old native library.'])
    (args.out/'preparation.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'sources'}, indent=2))


if __name__ == '__main__':
    main()
