from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import tri_sample,cell_planes
t=np.load('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/candidate/terrain.npz');h=t['heights'];p=np.load('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
regenerated=cell_planes(t['cls'],t['level']);field_equal=np.array_equal(regenerated,p,equal_nan=True)
stage=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/data/layers')
reports=[];positive=None
for tile in json.loads((B/'surface-audit.json').read_text())['tiles']:
 if not tile['wet_non_gravel']:continue
 a,b=tile['tile'];uv=np.arange(512)-64+.5;xx,zz=np.meshgrid(a*384+uv,12288-b*384-uv)
 rr=np.clip(np.floor((12282-zz)/6).astype(int),0,2046);cc=np.clip(np.floor(xx/6).astype(int),0,2046);depth=np.maximum(np.nan_to_num(p[rr,cc],nan=-1e9),.75)-tri_sample(h,xx,zz)
 water=(depth>1e-6);valid=(xx<12282)&(xx>0)&(zz<12282)&(zz>0);core=np.zeros(water.shape,bool);core[64:448,64:448]=True;core&=valid
 safe=core&(depth>=.2)&(distance_transform_edt(water)>=2)
 source=np.array(Image.open(stage/f'M_{a:03d}_{b:03d}_lca.png').convert('RGB')).max(axis=2)
 decoded=np.array(Image.open(B/'decoded-masks'/f'm_{a:03d}_{b:03d}_lca.png').convert('RGB')).max(axis=2)
 real=core&water&(source>8);bad=safe&(source>8);strong=safe&(decoded>=64)
 ids=np.argwhere(bad);examples=[dict(x=float(xx[r,c]),z=float(zz[r,c]),depth=float(depth[r,c]),source=int(source[r,c]),decoded=int(decoded[r,c])) for r,c in ids[:2]]
 reports.append(dict(tile=[a,b],uncompressed_wrong=int(real.sum()),safe_uncompressed_wrong=int(bad.sum()),safe_decoded_strong=int(strong.sum()),only_compression=int((core&water&(decoded>8)&(source<=8)).sum()),examples=examples))
 if positive is None and (safe&(source==0)&(decoded<=8)).any():
  r,c=np.argwhere(safe&(source==0)&(decoded<=8))[0];altered=source.copy();altered[r,c]=255
  before=int((safe&(source>8)).sum());after=int((safe&(altered>8)).sum())
  positive=dict(tile=[a,b],rc=[int(r),int(c)],real_before=before,mutant_after=after,negative_corruption_detected=after==before+1)
# A non-planar quad distinguishes the native NW-SE triangulation from bilinear or the other diagonal.
control=np.zeros((2048,2048),np.float32);control[100:102,100:102]=[[1,5],[2,9]]
measured=tri_sample(control,np.array([600+4.5,600+1.5]),np.array([12282-600-1.5,12282-600-4.5]));tri_ok=bool(np.allclose(measured,[5.,3.5],atol=1e-9))
summary={k:sum(r[k] for r in reports) for k in ['uncompressed_wrong','safe_uncompressed_wrong','safe_decoded_strong','only_compression']}
result=dict(status='SOURCE_MISALIGNMENT_CONFIRMED' if summary['safe_uncompressed_wrong'] else 'COMPRESSION_OR_BOUNDARY_ONLY',compiled_field_equals_current_nominal_rule=field_equal,counts=summary,control=positive,nonplanar_native_triangle_control=tri_ok,tiles=reports,limits=['Original EV22 FAIL and all non-gravel counts remain unchanged.','Safe subset is >=0.20m deep and at least2 pixels from a dry pixel; it is classification, not a relaxed acceptance gate.','Stage PNG is the uncompressed provenance; deployment was independently decoded in the first audit.'])
(B/'mismatch-classification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='tiles'},indent=2));assert tri_ok and positive['negative_corruption_detected']
