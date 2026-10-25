"""Audit the small FTT export against copied sources and installed vanilla models.

This is an offline import precheck, not a driving/road-continuity verdict.
CSV contract reference: tools/navigation/verify_regional_water_assets.py:53-58.
"""
from pathlib import Path
import argparse
import copy
import csv
import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse(text, templates):
    result = []
    for number, row in enumerate(csv.reader(text.splitlines(), delimiter=';'), 1):
        if len(row) != 9 or row[-1] != '':
            raise ValueError(f'row {number}: expected 8 columns and terminal delimiter')
        name = row[0]
        if name not in templates:
            raise ValueError(f'row {number}: missing template {name}')
        values = [float(v) for v in row[1:8]]
        if not all(math.isfinite(v) for v in values):
            raise ValueError(f'row {number}: nonfinite')
        easting, northing, yaw, pitch, roll, scale, height = values
        if not (200000 <= easting < 212288 and 0 <= northing < 12288):
            raise ValueError(f'row {number}: outside project mapframe')
        if scale != 1:
            raise ValueError(f'row {number}: pilot requires unscaled vanilla pieces')
        result.append(dict(name=name, easting=easting, northing=northing,
                           yaw=yaw, pitch=pitch, roll=roll, scale=scale, height=height))
    if not result:
        raise ValueError('empty export')
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pilot', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    prep = json.loads((args.pilot / 'preparation.json').read_text())
    unchanged = []
    for entry in prep['files']:
        source_hash, copy_hash = sha(entry['source']), sha(entry['destination'])
        unchanged.append(dict(path=entry['destination'], source_sha256=source_hash,
                              copy_sha256=copy_hash,
                              pass_unchanged=source_hash == copy_hash == entry['sha256']))
    assert all(row['pass_unchanged'] for row in unchanged), 'source/copy changed'
    library_path = args.pilot / 'project/TerrainBuilder/TemplateLibs/dz_structures_roads_parts.tml'
    library = ET.parse(library_path).getroot()
    templates = {t.findtext('Name'): t for t in library.findall('Template')}
    export = args.pilot / 'ftt_roads_pilot.txt'
    text = export.read_text(encoding='utf-8-sig')
    rows = parse(text, templates)
    controls = []
    for name, broken in [
        ('nonfinite', text.replace('205764.511002', 'nan', 1)),
        ('unknown_template', text.replace('asf1_25', 'missing_pilot_model', 1)),
        ('outside_mapframe', text.replace('205764.511002', '764.511002', 1)),
        ('invalid_scale', text.replace(';1.000000;', ';0.000000;', 1)),
        ('missing_height', '"asf1_25";205764;6037;90;0;0;1;'),
    ]:
        assert broken != text
        try:
            parse(broken, templates)
        except ValueError as exc:
            controls.append(dict(name=name, rejected=True, message=str(exc)))
        else:
            raise AssertionError(f'negative control accepted: {name}')
    sys.path.insert(0, r'C:\Users\guill\.agents\skills\dayz-p3d-debinarizer\scripts')
    from odol_reader import ODOL
    models = []
    minimal = ET.Element('Library', dict(library.attrib, name='FTT_Pilot_Roads'))
    for name, count in Counter(r['name'] for r in rows).items():
        template = templates[name]
        model = Path('P:/') / template.findtext('File').replace('\\', '/')
        raw = model.read_bytes()
        parsed = ODOL.from_bytes(raw)
        mi = parsed.model_info
        vec = lambda v: [v.x, v.y, v.z]
        models.append(dict(name=name, count=count, path=str(model), bytes=len(raw),
                           sha256=hashlib.sha256(raw).hexdigest(), odol_version=parsed.version,
                           lod_errors=parsed.lod_errors,
                           bbox_min=vec(mi.bbox_min), bbox_max=vec(mi.bbox_max),
                           bounding_center=vec(mi.bounding_center),
                           tml_radius=float(template.findtext('BBRadius'))))
        minimal.append(copy.deepcopy(template))
    # Consumer trial gets only the exact two needed templates; never writes DZ.
    native = args.pilot / 'native'
    native.mkdir(exist_ok=True)
    ET.ElementTree(minimal).write(native / 'FTT_Pilot_Roads.tml', encoding='utf-8', xml_declaration=True)
    lengths = [math.hypot(b['easting'] - a['easting'], b['northing'] - a['northing'])
               for a, b in zip(rows, rows[1:])]
    report = dict(status='PASS_EXPORT_OFFLINE', created_utc=datetime.now(timezone.utc).isoformat(),
                  app_sha256=sha(args.pilot / 'app/FlynnsTerrainTools.exe'),
                  export_sha256=sha(export), export=str(export), count=len(rows),
                  model_counts=dict(Counter(r['name'] for r in rows)),
                  bounds_local_x=[min(r['easting'] for r in rows)-200000, max(r['easting'] for r in rows)-200000],
                  bounds_local_z=[min(r['northing'] for r in rows), max(r['northing'] for r in rows)],
                  yaw_values=sorted(set(r['yaw'] for r in rows)),
                  height_values=sorted(set(r['height'] for r in rows)),
                  scale_values=sorted(set(r['scale'] for r in rows)),
                  centre_distances_m=lengths, models=models, unchanged_inputs=unchanged,
                  negative_controls=controls,
                  limits=['Height 0 requires relative import; native consumer unverified.',
                          'Shape ground was OFF. No claim of smooth grade or road/ground fit.',
                          'Template BBRadius placeholders are preserved, not evidence of measured geometry.',
                          'Centre spacing/model bounds do not prove joints, drivable surface, collisions or navigation.',
                          'Only this straight segment was exported; no curves, bridges or forest generation.'])
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'export-verification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    (args.out / 'ftt_roads_pilot.txt').write_bytes(export.read_bytes())
    print(json.dumps({k: report[k] for k in ['status','count','model_counts','export_sha256','bounds_local_x','bounds_local_z','height_values','models']}, indent=2))


if __name__ == '__main__':
    main()
