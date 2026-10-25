"""Discriminate disconnected raster slivers from the anchored main-river field."""
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import label,distance_transform_edt
from shapely import STRtree
from shapely.geometry import shape
from shapely.ops import unary_union
from rasterio.features import shapes,rasterize
from affine import Affine
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
TX=Affine(6,0,-3,0,-6,12285)
data=np.load(ROOT/'tests/regional_foundation_hydrology_v1/hydraulic-field.npz')
field=data['surfaces'].copy();labels,_=label(data['river'])
orphan=json.loads((EV/'hydraulic-field-v1.json').read_text())['unanchored_components']
mask=np.isin(labels,[r['component'] for r in orphan])&(data['lakes']<0)
field[mask]=np.nan
_,nearest=distance_transform_edt(~np.isfinite(field),return_indices=True)
filled=field[tuple(nearest)]
river=shape(json.loads((EV/'river-engineering-game.json').read_text())['features'][0]['geometry'])
lakes=unary_union([shape(f['geometry']) for f in json.loads((EV/'standing-water-game.json').read_text())['features']])
river=river.difference(lakes.buffer(-.03))
rm=rasterize([(river,1)],out_shape=(2048,2048),transform=TX,dtype='uint8',all_touched=True).astype(bool)
quant=np.rint(filled/.025).astype('int32')
geometries=[];levels=[]
for g,level in shapes(quant,mask=rm,transform=TX):
    part=shape(g).intersection(river)
    if part.area<1e-6:continue
    geometries.append(part);levels.append(level*.025)
tree=STRtree(geometries);pairs=tree.query(geometries,predicate='intersects');keep=pairs[0]<pairs[1]
a,b=pairs[:,keep];delta=abs(np.array(levels)[a]-np.array(levels)[b]);bad=[]
for i in np.where(delta>.05001)[0]:
    g=geometries[a[i]].intersection(geometries[b[i]])
    if g.area>1e-5 or g.length>.02:bad.append({'difference_m':float(delta[i]),'bounds_xz':list(g.bounds)})
out=ROOT/'tests/regional_foundation_hydrology_v1/river-fringe-proposal.npz'
np.savez_compressed(out,field=filled,removed_orphan_vertices=mask)
report={'status':'DISCRIMINATOR_ONLY','orphan_vertices':int(mask.sum()),'bands':len(geometries),'bad_adjacencies':len(bad),
        'max_pair_difference_m':float(delta.max()),'bad':sorted(bad,key=lambda r:-r['difference_m'])}
(EV/'river-fringe-discriminator.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='bad'},indent=2));print(json.dumps(report['bad'][:8],indent=2))
