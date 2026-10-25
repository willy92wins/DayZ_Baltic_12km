"""Exact water boundary references for TB, including all islands/interior rings.

Use as polylines, never as runtime water or a replacement for GIS polygons.
No simplification, reprojection, buffering or displacement is performed.
"""
from pathlib import Path
import argparse, hashlib, json
import shapefile

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise SystemExit('Refusing to overwrite existing adapter')
    a.out.mkdir(parents=True)
    rings=segments=points=0;max_points=2048
    source=a.repo/'source/vectors/water.shp'
    with shapefile.Reader(str(source),encoding='utf-8') as src, shapefile.Writer(str(a.out/'water_outlines'),shapeType=shapefile.POLYLINE,encoding='utf-8') as wr:
        source_count=len(src)
        for name,size in [('osm_id',40),('src_idx',12),('ring_id',12),('chunk',12),('name',120)]:wr.field(name,'C',size)
        for index,sr in enumerate(src.iterShapeRecords()):
            props=sr.record.as_dict();bounds=list(sr.shape.parts)+[len(sr.shape.points)]
            for ring,(start,end) in enumerate(zip(bounds,bounds[1:])):
                ring_points=[list(p) for p in sr.shape.points[start:end]]
                if len(ring_points)<2:raise ValueError('Degenerate source ring')
                rebuilt=[]
                for chunk,offset in enumerate(range(0,len(ring_points)-1,max_points-1)):
                    section=ring_points[offset:offset+max_points]
                    wr.line([section]);wr.record(props['osm_id'],str(index),str(ring),str(chunk),props['name'])
                    rebuilt.extend(section if chunk==0 else section[1:]);segments+=1
                assert rebuilt==ring_points
                rings+=1;points+=len(ring_points)
    wkt=a.repo/'tb/registration_probe/probe_tb_export.prj'
    (a.out/'water_outlines.prj').write_bytes(wkt.read_bytes())
    (a.out/'water_outlines.cpg').write_text('UTF-8',encoding='ascii')
    manifest={'operation':'Every source polygon ring becomes one or more contiguous line segments; every coordinate preserved',
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_polygons':source_count,
        'source_rings':rings,'source_points_including_ring_closures':points,'output_segments':segments,
        'max_vertices_per_segment':max_points,'rings_reassembled_exactly':True,
        'semantics':'Editor outlines only. Includes exterior shorelines, interior islands, and existing crop edges. GIS polygon source is authoritative for water area and level.',
        'consumer_verdict':'NOT_TESTED',
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.out.iterdir() if p.is_file()}}
    (a.out/'outline-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
