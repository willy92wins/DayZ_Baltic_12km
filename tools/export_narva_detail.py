"""Export exceptional crossing reference separately from selected major roads."""
import json
from shapely.geometry import shape
from geo_common import DERIVED,tb_geometry
from prepare_prototype import write_shape

def main():
    data=json.loads((DERIVED/'gis/narva_crossing_detail_wgs84.geojson').read_text(encoding='utf-8'))
    write_shape('narva_crossing_detail',[(tb_geometry(shape(f['geometry'])),f['properties']) for f in data['features']],'line')
    print('NARVA REFERENCE EXPORTED '+str(len(data['features'])))

if __name__=='__main__':main()
