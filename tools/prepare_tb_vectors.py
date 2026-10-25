"""Copy engineering-coordinate vectors into the empirically tested TB CRS wrapper.

Geometry/attributes/index bytes stay unchanged; only .prj is replaced in a new
consumer directory. This is NOT a real geographical reprojection.
"""
from pathlib import Path
import argparse, hashlib, json, math, shutil
import shapefile

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():
        raise SystemExit('Refusing to overwrite an existing consumer directory')
    wkt_path=a.repo/'tb/registration_probe/probe_tb_export.prj'
    wkt=wkt_path.read_text(encoding='ascii')
    if '"central_meridian",3' not in wkt:
        raise SystemExit('Unexpected Terrain Builder projection wrapper')
    a.out.mkdir(parents=True)
    report={'operation':'Relabel copies only, NO coordinate transformation',
            'crs_warning':'Engineering metres, NOT real EPSG:32631 geography',
            'wrapper_source':str(wkt_path),'wrapper_sha256':sha(wkt_path),'layers':[]}
    for shp in sorted((a.repo/'source/vectors').glob('*.shp')):
        item={'name':shp.stem,'files':[]}
        for ext in ['.shp','.shx','.dbf','.cpg']:
            src=shp.with_suffix(ext)
            if src.exists():
                dst=a.out/src.name
                shutil.copy2(src,dst)
                assert sha(src)==sha(dst)
                item['files'].append({'name':dst.name,'sha256':sha(dst),'source_bytes_identical':True})
        prj=a.out/(shp.stem+'.prj');prj.write_text(wkt,encoding='ascii')
        with shapefile.Reader(str(shp),encoding='utf-8') as r:
            item.update(count=len(r),shape_type=r.shapeType,bounds=list(r.bbox))
        report['layers'].append(item)
    approved=json.loads((a.repo/'evidence/aprobacion.json').read_text(encoding='utf-8'))
    poly=approved['frame_polygon_lonlat_approximate']
    west,east=min(x[0] for x in poly),max(x[0] for x in poly)
    north=max(x[1] for x in poly)
    def merc_y(lat): return math.log(math.tan(math.pi/4+math.radians(lat)/2))
    width=math.radians(east-west)
    controls=json.loads((a.repo/'evidence/validation-report.json').read_text(encoding='utf-8'))['terrain_source_controls'][0]['controls']
    anchors=[]
    with shapefile.Writer(str(a.out/'regional_anchors'),shapeType=shapefile.POINT,encoding='utf-8') as wr:
        wr.field('label','C',40);wr.field('lon','F',20,10);wr.field('lat','F',20,10)
        for c in controls:
            x=200000+12288*math.radians(c['longitude']-west)/width
            y=12288-12288*(merc_y(north)-merc_y(c['latitude']))/width
            wr.point(x,y);wr.record(c['name'],c['longitude'],c['latitude'])
            anchors.append({'name':c['name'],'x':x,'y':y,'longitude':c['longitude'],'latitude':c['latitude']})
    (a.out/'regional_anchors.prj').write_text(wkt,encoding='ascii')
    (a.out/'regional_anchors.cpg').write_text('UTF-8',encoding='ascii')
    report['anchors']=anchors
    (a.out/'adapter-manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'layers':len(report['layers']),'geometry_bytes_unchanged':True,'anchors':anchors},indent=2))

if __name__=='__main__': main()
