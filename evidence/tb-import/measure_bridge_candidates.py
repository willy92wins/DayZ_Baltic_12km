"""Read-only vanilla model dimensions and a geographic Narva crossing comparison."""
from pathlib import Path
import contextlib,hashlib,io,json,struct,sys
import numpy as np
from shapely.geometry import shape
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parent
DEV=Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev')
READER=Path(r'C:\Users\guill\.agents\skills\dayz-p3d-debinarizer\scripts')
sys.path.insert(0,str(READER));sys.path.insert(0,str(DEV/'tools'))
from odol_reader import ODOL
from geo_common import tb_geometry

def xyz(v):return [float(v.x),float(v.y),float(v.z)]
def main():
    models=[]
    source=DEV.parent/'DZ/structures/roads/bridges'
    for p in sorted(source.glob('*.p3d')):
        data=p.read_bytes();assert data[:4]==b'ODOL' and struct.unpack_from('<I',data,4)[0]==54
        log=io.StringIO()
        with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):obj=ODOL.from_file(str(p))
        record={'file':str(p),'sha256':hashlib.sha256(data).hexdigest(),'odol_version':obj.version,'parse_mode':obj.parse_mode,
          'failed_lods':obj.lod_errors,'model_info_min':xyz(obj.model_info.bbox_min),'model_info_max':xyz(obj.model_info.bbox_max),'lods':[]}
        for lod in obj.lods:
            if lod is None:continue
            res=lod.resolution
            if res<100 or any(np.isclose(res,r,rtol=1e-5) for r in [1e13,3e15]):
                verts=np.asarray([xyz(v) for v in lod.vertices]);bc=np.asarray(xyz(obj.model_info.bounding_center))
                if not len(verts):continue
                lo=verts.min(axis=0)+bc;hi=verts.max(axis=0)+bc
                record['lods'].append({'resolution':res,'points':len(verts),'proxy_count':len(lod.proxies),
                    'min':lo.tolist(),'max':hi.tolist(),'size_xyz':(hi-lo).tolist()})
        models.append(record)
        (ROOT/(p.stem+'.parser.log')).write_text(log.getvalue(),encoding='utf-8')
        print(p.stem+' '+str(record['lods'][0]['size_xyz'])+' errors='+str(len(obj.lod_errors)),flush=True)
    features=json.loads((DEV/'derived/gis/narva_crossing_detail_wgs84.geojson').read_text(encoding='utf-8'))['features']
    bridge=[f for f in features if f['properties'].get('name:en')=='Friendship Bridge' and f['properties'].get('bridge')=='yes']
    assert bridge
    merged=unary_union([tb_geometry(shape(f['geometry'])) for f in bridge])
    water=json.loads((DEV/'derived/gis/osm_water_wgs84.geojson').read_text(encoding='utf-8'))['features']
    geo_bridge=unary_union([shape(f['geometry']) for f in bridge]);near=[]
    for f in water:
        g=shape(f['geometry'])
        if g.intersects(geo_bridge):near.append(tb_geometry(g))
    wet=merged.intersection(unary_union(near))
    report={'status':'DIMENSIONS_ONLY_NOT_A_FIT_APPROVAL','models':models,
      'narva_friendship_bridge':{'osm_ways':[f['properties']['osm_id'] for f in bridge],'total_tagged_line_length_game_m':merged.length,
         'wet_intersection_length_game_m':wet.length,'bounds_tb':list(merged.bounds)},
      'source_reader':{'path':str(READER/'odol_reader.py'),'sha256':hashlib.sha256((READER/'odol_reader.py').read_bytes()).hexdigest()},
      'limits':['LOD extents are geometric envelopes, not guaranteed usable deck widths or span/clearance.',
        'No vanilla model was edited or copied into a release. No engine, collision or roadway test was run.',
        'Crossing length is measured along the OSM tagged line inside water polygons after approved global compression. It is not a final bridge-placement design.']}
    (ROOT/'bridge-dimensions.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['narva_friendship_bridge']),flush=True)

if __name__=='__main__':main()
