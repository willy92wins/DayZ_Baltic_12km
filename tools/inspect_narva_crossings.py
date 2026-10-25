"""Inspect source road classes around the required Narva crossing."""
import json
import osmium
from shapely.geometry import LineString, box, mapping
from geo_common import *

def main():
    area=box(28.185,59.365,28.215,59.387);features={}
    for source in json.loads((EVIDENCE/'source-manifest.json').read_text())['sources']:
        if source['group']!='osm':continue
        stream=osmium.FileProcessor(source['path']).with_locations().with_filter(osmium.filter.EntityFilter(osmium.osm.WAY)).with_filter(osmium.filter.KeyFilter('highway'))
        for way in stream:
            coords=[(n.lon,n.lat) for n in way.nodes if n.location.valid()]
            if len(coords)!=len(way.nodes) or len(coords)<2:continue
            if not any(28.185<=x<=28.215 and 59.365<=y<=59.387 for x,y in coords):continue
            line=LineString(coords)
            if not line.intersects(area):continue
            old=features.get(way.id)
            if old and old['properties']['osm_version']>=way.version:continue
            features[way.id]={'type':'Feature','geometry':mapping(line.intersection(area)),
                'properties':dict(way.tags,osm_id='way/'+str(way.id),osm_version=way.version,source_extract=source['filename'])}
    save_json(DERIVED/'gis/narva_crossing_detail_wgs84.geojson',{'type':'FeatureCollection','features':list(features.values()),'attribution':'© OpenStreetMap contributors; ODbL 1.0'})
    flagged=[f['properties'] for f in features.values() if f['properties'].get('bridge') not in {None,'no'}]
    save_json(EVIDENCE/'narva-crossing-inspection.json',{'features':len(features),'bridge_tagged_ways':flagged,
       'interpretation':'Source tags only; this is neither an independently verified real-world border status nor an approved in-game crossing design.'})
    print(json.dumps(flagged,ensure_ascii=True),flush=True)

if __name__=='__main__':
    main()
