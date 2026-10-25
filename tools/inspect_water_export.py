"""Inventory the real TB water export after its import error; no source edits."""
from pathlib import Path
from collections import Counter
import argparse, json, hashlib, shutil
import shapefile
from shapely.geometry import shape

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    src=a.repo/'source/vectors/water.shp';dst=a.repo/'tb/regional_refs/water_import_partial.shp'
    with shapefile.Reader(str(src),encoding='utf-8') as r:
        original=[{'index':i,'vertices':len(sr.shape.points),'rings':len(sr.shape.parts),**sr.record.as_dict()} for i,sr in enumerate(r.iterShapeRecords())]
    with shapefile.Reader(str(dst),encoding='utf-8',encodingErrors='replace') as r:
        exported=[sr.record.as_dict() for sr in r.iterShapeRecords()]
        geometry_count=len(r)
    before=Counter(x['osm_id'] for x in original);after=Counter(x['osm_id'] for x in exported)
    missing=before-after;extra=after-before
    report={'source_count':len(original),'tb_export_count':geometry_count,
        'missing_counts':dict(missing),'extra_counts':dict(extra),
        'candidate_source_features_with_missing_ids':[x for x in original if x['osm_id'] in missing],
        'largest_source_features':sorted(original,key=lambda x:x['vertices'],reverse=True)[:10],
        'last_exported_records':exported[-5:],
        'import_error':'Renderer - Too many vertices!; CVectorFormatLoader::Load(727) [AssertNoDlg] area',
        'causal_status':'Input comparison identifies candidates; isolated consumer test needed before claiming cause.'}
    a.out.mkdir(parents=True,exist_ok=True)
    for ext in ['.shp','.shx','.dbf','.prj']:
        p=dst.with_suffix(ext)
        if p.exists():shutil.copy2(p,a.out/p.name)
    report['export_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.out.glob('water_import_partial.*')}
    (a.out/'water-import-diagnostic.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # A measured accepted component: outer ring identical, nine islands lost.
    with shapefile.Reader(str(src),encoding='utf-8') as r:
        control=r.shapeRecord(1199)
        assert control.record.as_dict()['osm_id']=='relation/1318060'
        reference=shape(control.shape)
    with shapefile.Reader(str(dst),encoding='utf-8',encodingErrors='replace') as r:
        matched=[sr for sr in r.iterShapeRecords() if sr.record.as_dict()['osm_id']=='relation/1318060']
    assert len(matched)==1
    actual=shape(matched[0].shape)
    hole_report={'source_index':1199,'osm_id':'relation/1318060','source_holes':len(reference.interiors),
        'exported_holes':len(actual.interiors),'source_area':reference.area,'exported_area':actual.area,
        'outer_boundary_error_m':reference.exterior.hausdorff_distance(actual.exterior),
        'hole_loss_area_m2':actual.area-reference.area,
        'scope':'Actual roundtrip loss; not isolated to import versus internal representation versus export'}
    (a.out/'water-hole-loss.json').write_text(json.dumps(hole_report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['source_count','tb_export_count','missing_counts','extra_counts']},indent=2))

if __name__=='__main__':main()
