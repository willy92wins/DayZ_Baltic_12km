from pathlib import Path
import json,sys
E=Path(__file__).parent;R=E.parent
sys.path.insert(0,r'C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts')
from odol_reader import ODOL
files=[R/'v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30/full_48.p3d',Path('P:/DZ/water/ponds/pond_50x50.p3d'),Path('P:/DZ/water/ponds/lake_50x50.p3d')]
keys=['bounding_sphere','geometry_sphere','view_density','lod_density_coef','draw_importance','auto_center','can_occlude','can_be_occluded','can_blend','property_class','force_not_alpha','special','and_hints','or_hints']
rows=[]
for p in files:
    od=ODOL.from_file(str(p))
    r=dict(path=str(p),model={k:getattr(od.model_info,k,None) for k in keys},lods=[])
    for l in od.lods:
        r['lods'].append(dict(resolution=l.resolution,vertices=len(l.vertices),faces=len(l.faces),properties=l.named_properties,textures=l.textures,materials=[m.material_name for m in l.materials],radius=l.b_radius,special=l.special))
    rows.append(r)
(E/'water-model-metadata.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
