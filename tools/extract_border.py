"""Recover country boundary membership rather than relying on tags on ways."""
import json
import osmium
from shapely.geometry import LineString,mapping
from geo_common import *

def main():
    source=next(s for s in json.loads((EVIDENCE/'source-manifest.json').read_text())['sources'] if s['filename']=='estonia.osm.pbf')
    path=source['path'];way_ids=set();relations=[]
    for relation in osmium.FileProcessor(path,osmium.osm.RELATION):
        if relation.tags.get('boundary')=='administrative' and relation.tags.get('admin_level')=='2' and relation.tags.get('ISO3166-1')=='EE':
            refs=[m.ref for m in relation.members if m.type=='w' and m.role in {'outer',''}]
            way_ids.update(refs)
            relations.append({'id':relation.id,'version':relation.version,'name':relation.tags.get('name'),'ISO3166-1':'EE','way_members':len(refs)})
    assert way_ids,'Estonia country relation not found'
    print('Border member ways '+str(len(way_ids)),flush=True)
    features=[];missing=[]
    processor=osmium.FileProcessor(path).with_locations().with_filter(osmium.filter.EntityFilter(osmium.osm.WAY)).with_filter(osmium.filter.IdFilter(way_ids))
    for way in processor:
        if not all(n.location.valid() for n in way.nodes):missing.append(way.id);continue
        line=LineString([(n.lon,n.lat) for n in way.nodes])
        if not line.intersects(BBOX):continue
        clipped=line.intersection(BBOX)
        features.append({'type':'Feature','geometry':mapping(clipped),'properties':{'osm_id':f'way/{way.id}','osm_version':way.version,'boundary':'administrative','admin_level':'2','country':'EE','source_relation':relations[0]['id']}})
    assert features and not missing,(len(features),missing)
    save_json(DERIVED/'gis/osm_border_wgs84.geojson',{'type':'FeatureCollection','attribution':'© OpenStreetMap contributors; ODbL 1.0','features':features})
    save_json(EVIDENCE/'border-processing.json',{'relations':relations,'clipped_ways':len(features),'missing_geometry':missing,'method':'Estonia admin_level=2 relation outer members, then nodes and clipping; maritime border may also be present.'})
    print('BORDER COMPLETE '+str(len(features)),flush=True)

if __name__=='__main__':main()
