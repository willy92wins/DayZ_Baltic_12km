"""Compare every actual TB-exported water line to its immutable GIS source ring."""
from pathlib import Path
import argparse, json, hashlib, shutil
import numpy as np
import shapefile

def normalize(points):
    p=np.asarray(points,dtype='float64')
    if len(p)>1:p=p[np.r_[True,np.any(np.abs(np.diff(p,axis=0))>1e-9,axis=1)]]
    return p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();expected={};ring_count=0
    with shapefile.Reader(str(a.repo/'source/vectors/water.shp'),encoding='utf-8') as r:
        polygons=len(r)
        for index,s in enumerate(r.iterShapes()):
            bounds=list(s.parts)+[len(s.points)]
            for ring,(start,end) in enumerate(zip(bounds,bounds[1:])):
                p=s.points[start:end];ring_count+=1
                for chunk,offset in enumerate(range(0,len(p)-1,2047)):
                    expected[(str(index),str(ring),str(chunk))]=normalize(p[offset:offset+2048])
    path=a.repo/'tb/regional_refs/water_outlines_tb_export.shp'
    errors=[];seen=set();mismatches=[];point_count=0
    with shapefile.Reader(str(path),encoding='utf-8',encodingErrors='replace') as r:
        for sr in r.iterShapeRecords():
            rec=sr.record.as_dict();key=(rec['src_idx'],rec['ring_id'],rec['chunk'])
            if key in seen or key not in expected:raise ValueError('Unexpected/duplicate key: '+repr(key))
            seen.add(key);reference=expected[key];actual=normalize(sr.shape.points)
            if actual.shape!=reference.shape:
                mismatches.append({'key':key,'expected_points':len(reference),'actual_points':len(actual)});continue
            delta=np.linalg.norm(actual-reference,axis=1)
            errors.append(float(delta.max()));point_count+=len(actual)
    missing=set(expected)-seen
    passed=not missing and not mismatches and bool(errors) and max(errors)<=.0001
    report={'verdict':'PASS' if passed else 'FAIL','scope':'All real TB-exported water outlines compared point by point against source polygon rings, including holes',
        'source_polygons':polygons,'source_rings':ring_count,'expected_segments':len(expected),'exported_segments':len(seen),
        'compared_points_after_adjacent_duplicate_removal':point_count,'missing_segments':len(missing),'mismatches':mismatches,
        'max_point_error_m':max(errors) if errors else None,'tolerance_m':.0001,
        'allowed_normalization':'Adjacent repeated identical points only; preserves ordered geometry',
        'not_proven':['Runtime water surfaces','Elevation/depth','Gameplay crossing','Export fidelity of name text']}
    a.out.mkdir(parents=True,exist_ok=True)
    for ext in ['.shp','.shx','.dbf','.prj']:
        p=path.with_suffix(ext)
        if p.exists():shutil.copy2(p,a.out/p.name)
    shutil.copy2(a.repo/'derived/tb_water_outlines_v1/outline-manifest.json',a.out/'outline-manifest.json')
    report['export_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.out.glob('water_outlines_tb_export.*')}
    (a.out/'water-outlines-roundtrip.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
