"""Verify a real Terrain Builder SHP export against approved-frame anchors."""
from pathlib import Path
import argparse, hashlib, json, math, shutil
import shapefile

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    manifest_path=a.repo/'derived/tb_vectors_v1/adapter-manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    expected={p['name']:p for p in manifest['anchors']}
    export=a.repo/'tb/baltic_physical/anchors_tb_export.shp'
    rows=[]
    with shapefile.Reader(str(export),encoding='utf-8') as reader:
        fields=reader.fields[1:]
        for sr in reader.iterShapeRecords():
            rec=sr.record.as_dict()
            p=expected.pop(rec['label'])
            x,y=sr.shape.points[0]
            error=math.hypot(x-p['x'],y-p['y'])
            rows.append({'name':p['name'],'expected_xy':[p['x'],p['y']],
                         'exported_xy':[x,y],'error_m':error,
                         'source_lonlat':[p['longitude'],p['latitude']],
                         'exported_lonlat_attributes':[rec['lon'],rec['lat']]})
    passed=not expected and len(rows)==6 and all(r['error_m']<=0.0001 for r in rows)
    report={'verdict':'PASS' if passed else 'FAIL','scope':'Six independent regional control geometries imported into and exported from Terrain Builder',
            'tolerance_m':0.0001,'count':len(rows),'max_error_m':max(r['error_m'] for r in rows),
            'checks':rows,'exported_dbf_fields':fields,
            'attribute_warning':'TB export changed floating-point lon/lat fields to integer numeric fields. Geometry passed; attribute roundtrip failed. Use immutable source for provenance.',
            'not_proven':['Terrain vertex registration correction','Gameplay water','Road objects','Performance']}
    a.out.mkdir(parents=True,exist_ok=True)
    for ext in ['.shp','.shx','.dbf','.prj']:
        src=export.with_suffix(ext);shutil.copy2(src,a.out/src.name)
    shutil.copy2(manifest_path,a.out/manifest_path.name)
    report['export_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.out.glob('anchors_tb_export.*')}
    (a.out/'anchors-roundtrip.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'verdict':report['verdict'],'count':len(rows),'max_error_m':report['max_error_m'],'attribute_roundtrip':'FAIL: numeric decimals lost'}))
    if not passed: raise SystemExit(1)

if __name__=='__main__': main()
