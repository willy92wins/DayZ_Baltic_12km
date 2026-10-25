"""Interpolate level contours before discretization, instead of nearest-cell steps.

ContourPy1.4 OuterOffset layout verified in util/bokeh_util.py:25-39. Preserve
all water outlines; remove arbitrary raster-orphan elevations from the field.
"""
from pathlib import Path
import json,math
import numpy as np
import contourpy
from shapely import STRtree,make_valid
from shapely.geometry import shape,mapping,Polygon,box
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
field=np.load(ROOT/'tests/regional_foundation_hydrology_v1/river-fringe-proposal.npz')['field']
river=shape(json.loads((EV/'river-engineering-game.json').read_text())['features'][0]['geometry'])
standing=json.loads((EV/'standing-water-game.json').read_text())['features']
levels=json.loads((EV/'lake-design-levels.json').read_text())['bodies']
surfaces=[(shape(f['geometry']),levels[i]['design_surface_m'],f'lake_{i:03d}') for i,f in enumerate(standing)]
lakeunion=unary_union([g for g,_,_ in surfaces]);river=river.difference(lakeunion.buffer(-.03))
generator=contourpy.contour_generator(x=np.arange(2048)*6,y=np.arange(2048)*6,z=field[::-1],fill_type='OuterOffset',quad_as_tri=True)
rm=np.load(ROOT/'tests/regional_foundation_hydrology_v1/hydraulic-field.npz')['river']
low=math.floor(float(field[rm].min())/.025)-2;high=math.ceil(float(field[rm].max())/.025)+2
pieces=[]
for k in range(low,high+1):
    lower=(k-.5)*.025;upper=(k+.5)*.025
    xy,rings=generator.filled(lower,upper)
    shapes=[]
    for coords,offsets in zip(xy,rings):
        if coords is None:continue
        poly=Polygon(coords[offsets[0]:offsets[1]],[coords[a:b] for a,b in zip(offsets[1:-1],offsets[2:])])
        if not box(*poly.bounds).intersects(river):continue
        poly=make_valid(poly).intersection(river)
        if poly.area>1e-6:shapes.append(poly)
    if shapes:
        g=unary_union(shapes).buffer(.005).intersection(river)
        pieces.append(g);surfaces.append((g,k*.025,f'river_contour_{k:04d}'))
    if k%30==0:print(f'Contour {k}/{high}',flush=True)
missing=river.difference(unary_union(pieces)).area
assert missing<.01,missing
geos=[g for g,_,_ in surfaces];lev=np.array([v for _,v,_ in surfaces]);pairs=STRtree(geos).query(geos,predicate='intersects')
keep=pairs[0]<pairs[1];a,b=pairs[:,keep];delta=abs(lev[a]-lev[b]);bad=[]
for i in np.flatnonzero(delta>.05001):
    g=geos[a[i]].intersection(geos[b[i]])
    if g.area>1e-5 or g.length>.02:bad.append({'a':surfaces[a[i]][2],'b':surfaces[b[i]][2],'height_difference_m':float(delta[i]),'bounds_xz':list(g.bounds)})
report={'status':'PASS_SOURCE_BANDS_ONLY' if not bad else 'FAIL_JOINT_HEIGHT','bands':len(surfaces),'missing_area_m2':missing,'bad_joints':bad}
(EV/'continuous-water-bands-v2.json').write_text(json.dumps(report,indent=2)+'\n')
(EV/'water-surfaces-contour-v2.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[
    {'type':'Feature','properties':{'body':name,'level_m':v},'geometry':mapping(g)} for g,v,name in surfaces]})+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='bad_joints'},indent=2));print(json.dumps({'bad':len(bad),'examples':bad[:8]},indent=2))
