"""Record human-reviewed native TB observations; not an automatic UI assertion."""
from pathlib import Path
import argparse, json, hashlib

ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
out=ap.parse_args().out
controls=[]
for name,r,c,z in [('NW',8,11,15),('NE',17,112,25),('SW',110,20,35),('SE',101,106,45)]:
    evidence={}
    for suffix in ['shifted-vertex','centre-no-vertex']:
        p=out/f'probe-{name.lower()}-{suffix}.png'
        assert p.is_file()
        evidence[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    controls.append({'name':name,'row':r,'column':c,'source_height_m':z,
        'gis_sample_centre_xy':[200000+(c+.5)*6,768-(r+.5)*6],
        'inferred_tb_vertex_xy':[200000+c*6,768-r*6],
        'observed_positive_selection':{'count':1,'height_m':z},
        'observed_negative_selection_at_gis_centre':{'count':0},
        'evidence_sha256':evidence})
report={'verdict':'OBSERVED_FOUR_CONTROLS','date':'2026-09-29',
    'source':'tests/registration-probe/probe_128_6m.asc',
    'method':'Native Terrain Builder terrain-edit rectangular selection, without editing elevations. One vertex and expected elevation at each displaced location; zero at each original SHP centre. SHP coordinates checked in properties.',
    'evidence_level':'Manually inspected UI screenshots and properties. Vertex coordinates inferred from reference points, selection extents and the 6 m grid, not read from a numeric vertex coordinate property.',
    'observed_offset_from_gis_centres_m':[-3,3],
    'supported_vertex_formula':'X=xllcorner+column*cellsize; Y=yllcorner+nrows*cellsize-row*cellsize',
    'not_proven':['Internal TB implementation','Other TB versions','Arbitrary cell sizes','Right/bottom mesh extension','Production correction'],
    'controls':controls}
(out/'mesh-registration.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('Recorded four positive + four negative native observations; not a production correction.')
