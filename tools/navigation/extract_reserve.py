"""Extract named Mshinskoye protected areas from the already approved OSM PBF."""
import hashlib
import json
from pathlib import Path
import sys
import time
import osmium
from shapely import wkb, make_valid
from shapely.geometry import mapping
from pyproj import Geod

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from geo_common import BBOX, tb_geometry


class ReserveExtractor(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.factory = osmium.geom.WKBFactory()
        self.features = []
        self.errors = []

    def area(self, area):
        names = ' '.join(t.v.casefold() for t in area.tags if t.k.startswith('name'))
        if not ('мшинск' in names or 'mshinsk' in names):
            return
        if area.tags.get('boundary') != 'protected_area' and area.tags.get('leisure') != 'nature_reserve':
            return
        try:
            geom = make_valid(wkb.loads(self.factory.create_multipolygon(area), hex=True))
            if not geom.intersects(BBOX):
                return
            clipped = geom.intersection(BBOX)
            real_area, _ = Geod(ellps='WGS84').geometry_area_perimeter(geom)
            props = dict(area.tags)
            props.update(osm_id=('way/' if area.from_way() else 'relation/')+str(area.orig_id()),
                         osm_version=area.version,
                         source_area_km2=abs(real_area)/1e6,
                         game_area_km2=tb_geometry(clipped).area/1e6)
            self.features.append({'type': 'Feature', 'properties': props, 'geometry': mapping(clipped)})
        except (ValueError, RuntimeError) as exc:
            self.errors.append({'id': area.orig_id(), 'error': str(exc)})


def main():
    out = ROOT/'evidence/regional-outline-v1'
    out.mkdir(parents=True, exist_ok=True)
    result_path = out/'reserve_wgs84.geojson'
    if result_path.exists():
        raise ValueError('Reserve extraction already exists; preserve it')
    records = json.loads((ROOT/'evidence/source-manifest.json').read_text())['sources']
    source = next(r for r in records if r['filename'] == 'northwestern-fed-district.osm.pbf')
    path = Path(source['path'])
    with path.open('rb') as handle:
        if hashlib.file_digest(handle, 'sha256').hexdigest() != source['sha256']:
            raise ValueError('Source PBF changed')
    start = time.monotonic()
    handler = ReserveExtractor()
    print('Extracting named protected-area geometry from existing PBF', flush=True)
    handler.apply_file(str(path), locations=True, idx='flex_mem')
    if handler.errors or not handler.features:
        raise ValueError({'errors': handler.errors, 'count': len(handler.features)})
    data = {'type': 'FeatureCollection', 'attribution': '© OpenStreetMap contributors; ODbL 1.0',
            'source_sha256': source['sha256'], 'features': handler.features}
    result_path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    summary = {'status': 'OSM_REFERENCE_EXTRACTED_NOT_LEGAL_SURVEY',
               'source_sha256': source['sha256'], 'seconds': time.monotonic()-start,
               'features': [f['properties'] for f in handler.features],
               'errors': handler.errors}
    (out/'reserve-extraction.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
