"""Extract original OSM geometries; never turn individual road segments into assets."""
from collections import Counter
import hashlib,json,time
import osmium
from shapely import wkb,make_valid
from shapely.geometry import Point,LineString,mapping
from geo_common import *

MAJOR={'motorway','trunk','primary','secondary','tertiary','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'}
KEYS=['name','name:en','name:ru','name:et','ref','highway','waterway','natural','water','landuse','place','bridge','tunnel','layer','boundary','admin_level','ele','intermittent','access','surface','lanes','width']

class Extractor(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.factory=osmium.geom.WKBFactory()
        self.layers={key:{} for key in ['roads','rivers','coastline','water','places','border']}
        self.errors=Counter();self.counts=Counter();self.source=''

    def add(self,layer,obj,geom,kind):
        if geom.is_empty or not geom.intersects(BBOX):return
        if not geom.is_valid:geom=make_valid(geom)
        clipped=geom.intersection(BBOX)
        if clipped.is_empty:return
        identity=f'{kind}/{obj.orig_id() if kind=="area" else obj.id}'
        if kind=='area':identity=('way/' if obj.from_way() else 'relation/')+str(obj.orig_id())
        old=self.layers[layer].get(identity)
        if old and old['properties']['osm_version']>=obj.version:return
        props={key:obj.tags[key] for key in KEYS if key in obj.tags}
        props.update(osm_id=identity,osm_version=obj.version,source_extract=self.source)
        self.layers[layer][identity]={'type':'Feature','properties':props,'geometry':mapping(clipped)}

    def node(self,n):
        if n.tags.get('place') not in {'city','town','village','hamlet'}:return
        if n.location.valid():self.add('places',n,Point(n.lon,n.lat),'node')

    def way(self,w):
        highway=w.tags.get('highway')
        target=[]
        if highway in MAJOR:target.append('roads')
        if w.tags.get('waterway') in {'river','canal'}:target.append('rivers')
        if w.tags.get('natural')=='coastline':target.append('coastline')
        if w.tags.get('boundary')=='administrative' and w.tags.get('admin_level')=='2':target.append('border')
        if not target:return
        try:
            # An invalid node is an explicit missing geometry, never silently joined.
            if len(w.nodes)<2 or not all(n.location.valid() for n in w.nodes):
                self.errors['ways_missing_nodes']+=1;return
            coords=[(n.lon,n.lat) for n in w.nodes]
            if max(x for x,y in coords)<WEST or min(x for x,y in coords)>EAST or max(y for x,y in coords)<SOUTH or min(y for x,y in coords)>NORTH:return
            geom=LineString(coords)
            for layer in target:self.add(layer,w,geom,'way')
        except (ValueError,RuntimeError) as exc:self.errors[type(exc).__name__]+=1

    def area(self,a):
        if not (a.tags.get('natural')=='water' or a.tags.get('waterway')=='riverbank' or a.tags.get('landuse')=='reservoir'):return
        try:
            geom=wkb.loads(self.factory.create_multipolygon(a),hex=True)
            self.add('water',a,geom,'area')
        except (ValueError,RuntimeError) as exc:self.errors['area_'+type(exc).__name__]+=1

def main():
    t=time.monotonic();handler=Extractor()
    records=json.loads((EVIDENCE/'source-manifest.json').read_text())['sources']
    headers=[]
    for item in (r for r in records if r['group']=='osm'):
        path=Path(item['path']);assert hashlib.file_digest(path.open('rb'),'sha256').hexdigest()==item['sha256']
        with osmium.io.Reader(str(path)) as reader:
            header=reader.header()
            headers.append({'file':path.name,'generator':header.get('generator'),'osmosis_replication_timestamp':header.get('osmosis_replication_timestamp')})
        handler.source=path.name
        print('READ '+path.name,flush=True)
        handler.apply_file(str(path),locations=True,idx='flex_mem')
        print('COUNTS '+json.dumps({k:len(v) for k,v in handler.layers.items()}),flush=True)
    for name,features in handler.layers.items():
        save_json(DERIVED/f'gis/osm_{name}_wgs84.geojson',{'type':'FeatureCollection',
          'name':name,'attribution':'© OpenStreetMap contributors; ODbL 1.0',
          'features':list(features.values())})
    save_json(EVIDENCE/'osm-processing.json',{'counts':{k:len(v) for k,v in handler.layers.items()},
       'errors':dict(handler.errors),'source_headers':headers,'seconds':round(time.monotonic()-t,1),
       'notes':'Full extracts used for relation/node completeness before clipping; objects deduplicated by type/id and highest version. Errors counted across entire extracts, not automatically in approved frame.'})
    print('VECTORS COMPLETE',flush=True)

if __name__=='__main__':main()
