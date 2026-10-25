"""Water polygons consumed independently of their contour/raster construction."""
from pathlib import Path
import argparse,json
import numpy as np
from shapely import STRtree,points
from shapely.geometry import shape
from shapely.ops import unary_union
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
features=json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features']
geos=[shape(f['geometry']) for f in features];levels=np.array([f['properties']['level_m'] for f in features])
ocean=shape(json.loads((EV/'ocean-game.json').read_text())['features'][0]['geometry'])
geos.append(ocean);levels=np.r_[levels,.5]
tree=STRtree(geos)
ap=argparse.ArgumentParser();ap.add_argument('--terrain-version',default='v4');ap.add_argument('--out',type=Path)
args=ap.parse_args()
h=np.load(ROOT/f'tests/regional_foundation_combined_{args.terrain_version}/reference.npz')['candidate']
reports=[]
for feature in json.loads((EV/'fairways-main-game.json').read_text())['features']:
    line=shape(feature['geometry']);s=np.linspace(0,line.length,max(3,int(np.ceil(line.length/2))+1))
    p=np.array([line.interpolate(float(v)).coords[0] for v in s]);delta=np.gradient(p,axis=0)
    normal=np.column_stack([-delta[:,1],delta[:,0]])/np.linalg.norm(delta,axis=1)[:,None]
    q=np.concatenate([p+normal*offset for offset in (-12,-6,0,6,12)])
    q=np.clip(q,.01,12281.99)
    hits=tree.query(points(q),predicate='intersects');water=np.full(len(q),-np.inf)
    np.maximum.at(water,hits[0],levels[hits[1]])
    bottom=sample(h,q[:,0]+200000,q[:,1]);depth=water-bottom
    bad=np.flatnonzero(~np.isfinite(water)|(depth<3))
    reports.append({'river':feature['properties']['river'],'part':feature['properties']['part'],'samples':len(q),
                    'missing':int((~np.isfinite(water)).sum()),'shallow':int((np.isfinite(water)&(depth<3)).sum()),
                    'minimum_depth_m':float(depth[np.isfinite(depth)].min()),
                    'bad_examples':[{'xz':q[i].tolist(),'depth':float(depth[i]) if np.isfinite(depth[i]) else None} for i in bad[:5]]})
islands=json.loads((EV/'protected-islands-game.json').read_text())['features']
water=unary_union(geos[:-1]);overlap=sum(water.intersection(shape(f['geometry'])).area for f in islands)
report={'status':'PASS_OFFLINE_SURFACE_CONSUMER' if not any(r['missing'] or r['shallow'] for r in reports) and overlap<.01 else 'FAIL',
        'protected_island_overlap_m2':overlap,'samples':sum(r['samples'] for r in reports),'rivers':reports,
        'limits':['Source polygons only. Compiled models, native placement and engine classification still required.']}
out=args.out or EV/'contour-water-consumers-v2.json'
if args.out and out.exists():raise ValueError('Preserve prior evidence')
report['terrain_version']=args.terrain_version
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='rivers'},indent=2))
print(json.dumps([r for r in reports if r['missing'] or r['shallow']],indent=2))
raise SystemExit(0 if report['status'].startswith('PASS') else 1)
