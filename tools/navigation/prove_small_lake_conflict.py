"""Geometric certificate: an affine triangle cannot retain a subcell water hole."""
from pathlib import Path
import json,math
from shapely.geometry import shape,Polygon
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1';OUT=ROOT/'tests/regional_outline_smoothing_v27'
fs=json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features'];water=unary_union([shape(f['geometry']) for f in fs]+[shape(json.loads((EV/'ocean-game.json').read_text())['features'][0]['geometry'])]);records=[]
for f in fs:
    g=shape(f['geometry'])
    if not f['properties']['body'].startswith('lake_') or not g.buffer(-4.5).is_empty:continue
    p=g.representative_point();c=int(p.x//6);r=int((12282-p.y)//6);x,z=c*6,12282-r*6;u,v=p.x/6-c,(12282-p.y)/6-r
    coords=[(x,z),(x+6,z),(x+6,z-6)] if v<=u else [(x,z),(x+6,z-6),(x,z-6)]
    tri=Polygon(coords);dry=tri.difference(water);hull=dry.convex_hull;level=f['properties']['level_m']
    records.append(dict(body=f['properties']['body'],point_xz=[p.x,p.y],triangle_xz=coords,source_water_level_m=level,dry_hull_contains_wet_representative=bool(hull.covers(p)),dry_hull=list(hull.exterior.coords) if hull.geom_type=='Polygon' else None,minimum_dry_height_m=level+.35,maximum_wet_height_m=level-.15,contradiction_gap_m=.5))
report=dict(status='EXACT_AFFINE_CONVEX_HULL_DIAGNOSTIC',records=records,mechanism='An affine height at a point inside the convex hull of dry intersection vertices cannot be below every vertex lower bound. No slope or height-delta cap is needed for this contradiction.')
(OUT/'small-lake-geometric-conflict.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
