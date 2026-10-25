from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy import ndimage
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-lake-bank-proposal-2026-10-09'
sys.path.insert(0,str(W/'tools/terrain'));from relevel_bodies_v30 import label_bodies
source=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/candidate/terrain.npz');t=dict(np.load(source));h=t['heights'].astype(float);v=h.copy();ids=label_bodies(t['cls'],t['level'])
p=np.load('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
water_support=np.zeros_like(h,dtype=bool)
for dr,dc in ((0,0),(0,1),(1,0),(1,1)):water_support[dr:dr+2047,dc:dc+2047]|=np.isfinite(p)
fixed=np.load('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/constraints.npz')['fixed']|water_support
fixed[:11]=True;fixed[-11:]=True;fixed[:,:11]=True;fixed[:,-11:]=True
allowed=np.zeros_like(fixed);smooth=ndimage.gaussian_filter(h,2.,mode='nearest');reports=[]
def curvature(a,mask):
 xx=(a[1:-1,:-2]-2*a[1:-1,1:-1]+a[1:-1,2:])/36
 zz=(a[:-2,1:-1]-2*a[1:-1,1:-1]+a[2:,1:-1])/36
 xz=(a[2:,2:]-a[2:,:-2]-a[:-2,2:]+a[:-2,:-2])/144
 return float(np.sqrt(np.mean((xx*xx+zz*zz+2*xz*xz)[mask[1:-1,1:-1]])))
for name,x,z in [('southwest',622.4,840),('southeast',10436.5,308.2)]:
 r,c=round((12282-z)/6),round(x/6);body=int(ids[r,c]);mask=ids==body;assert body>0
 dist=ndimage.distance_transform_edt(~mask,sampling=6);dry=t['cls']==0;bank=(dist>0)&(dist<=36)&dry;ring=(dist>12)&(dist<=36)&dry
 level=float(np.median(t['level'][mask]));floor=max(level+.30,float(np.median(h[ring])))
 scope=(dist>0)&(dist<54)&dry&~fixed;allowed|=scope
 fade=np.clip((54-dist)/18,0,1);fade=fade*fade*(3-2*fade)
 target=np.maximum(np.maximum(smooth,floor),h-1.5)
 v[scope]=np.minimum(h[scope],h[scope]+fade[scope]*(target[scope]-h[scope]))
 reports.append(dict(name=name,anchor_xz=[x,z],body=body,level_m=level,target_dry_floor_m=floor,bank_vertices=int(bank.sum()),fixed_bank_vertices=int((bank&fixed).sum()),before_curvature=curvature(h,bank),before_bank_p90=float(np.percentile(h[bank],90)),bank_mask=bank))
v=v.astype(np.float32);changed=v!=t['heights'];max_excess=0.;bad=0
for dr,dc in ((0,1),(1,0)):
 def slope(a):return np.degrees(np.arctan(np.hypot(a[dr:dr+2047,dc:dc+2047]-a[:-1,:-1],a[1:,1:]-a[dr:dr+2047,dc:dc+2047])/6))
 a=slope(h);b=slope(v.astype(float));touch=changed[:-1,:-1]|changed[dr:dr+2047,dc:dc+2047]|changed[1:,1:]
 excess=b-np.maximum(a,35);max_excess=max(max_excess,float(excess[touch].max(initial=0)));bad+=int((touch&(excess>1e-4)).sum())
for q in reports:
 bank=q.pop('bank_mask');q['after_curvature']=curvature(v.astype(float),bank);q['curvature_reduction']=1-q['after_curvature']/q['before_curvature'];q['after_bank_p90']=float(np.percentile(v[bank],90));q['changed_bank_vertices']=int((bank&changed).sum());q['shape_gate']=q['curvature_reduction']>=.10 and q['after_bank_p90']<=q['before_bank_p90']
gates=dict(finite=bool(np.isfinite(v).all()),fixed_exact=not bool((changed&fixed).any()),scope_exact=not bool((changed&~allowed).any()),no_raises=bool(np.all(v<=h+1e-6)),max_lowering=float((h-v).max())<=1.500001,water_support_exact=not bool((changed&water_support).any()),slopes=bad==0,both_lake_shape_gates=all(q['shape_gate'] for q in reports))
candidate=B/'candidate';candidate.mkdir(exist_ok=False);np.savez_compressed(candidate/'terrain.npz',**(t|{'heights':v}))
rr,cc=np.nonzero(changed);np.savez_compressed(E/'terrain-delta.npz',row=rr,col=cc,before=h[rr,cc],after=v[rr,cc])
result=dict(status='PROPOSAL_PASSES_OFFLINE_USER_POLICY_PENDING' if all(gates.values()) else 'PROPOSAL_REJECTED_NOT_FOR_DEPLOYMENT',gates=gates,changed_vertices=len(rr),bad_faces=bad,max_slope_excess_deg=max_excess,lakes=reports,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),candidate_sha256=hashlib.sha256((candidate/'terrain.npz').read_bytes()).hexdigest(),limits=['No level change or promotion.','Water-support vertices exactly fixed, so physical and visible triangle-water intersections are unchanged.','This constrained proposal cannot remove the parts of the bank whose vertices support the waterline.'])
(E/'proposal.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
