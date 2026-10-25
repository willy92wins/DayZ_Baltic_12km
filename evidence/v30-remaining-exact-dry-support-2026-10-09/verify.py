"""Consumer of saved native triangles: cross products, full slope, fixed water and road gates."""
from pathlib import Path
import csv,json,sys
import numpy as np
from scipy.ndimage import distance_transform_edt
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/terrain'),'E:/DayZ-Baltic-Build/v30-surface-crease-audit-20261009']
from audit_native_surface import sha,incident_all,incident_any
SOURCE=Path('E:/DayZ-Baltic-Build/v30-exact-dry-support-20261009/candidate/terrain.npz')
PLANE=SOURCE.parent/'plane.npy'
from verify_roads_v30 import evaluate

def face_normals(h):
    nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    ones=np.ones_like(nw);zeros=np.zeros_like(nw)
    diagonal=np.stack((6*ones,se-nw,-6*ones),axis=-1)
    ea=np.stack((6*ones,ne-nw,zeros),axis=-1)
    eb=np.stack((zeros,sw-nw,-6*ones),axis=-1)
    a=np.cross(ea,diagonal);b=np.cross(diagonal,eb)
    return a/np.linalg.norm(a,axis=-1)[...,None],b/np.linalg.norm(b,axis=-1)[...,None]

def edges(a,b):
    for name,x,y in [('diagonal',a,b),('vertical',a[:,:-1],b[:,1:]),('horizontal',b[:-1],a[1:])]:
        yield name,np.degrees(np.arctan2(np.linalg.norm(np.cross(x,y),axis=-1),np.einsum('ijk,ijk->ij',x,y)))

def exact_wet_support(h,p):
    f=np.load(SOURCE.parent/'visible-field.npy');corners=[(0,0),(0,1),(1,0),(1,1)]
    hv=[h[dr:dr+2047,dc:dc+2047] for dr,dc in corners]
    nominal=np.fmax(p,.85);visible=np.where(np.isfinite(p)[:,:,None],f,.85)
    support=np.zeros(h.shape,bool)
    for ids in [(0,1,3),(0,2,3)]:
        wet=np.logical_or.reduce([(nominal>hv[i])|(visible[:,:,i]>hv[i]) for i in ids])
        for i in ids:
            dr,dc=corners[i];support[dr:dr+2047,dc:dc+2047]|=wet
    return support

def physical(h,v,t,u,fixed,allowed,p):
    changed=h!=v
    water=exact_wet_support(h,p)
    bad=0;excess=0.
    for mid in ((0,1),(1,0)):
        dr,dc=mid
        def s(a):return np.degrees(np.arctan(np.hypot(a[dr:dr+2047,dc:dc+2047]-a[:-1,:-1],a[1:,1:]-a[dr:dr+2047,dc:dc+2047])/6))
        delta=s(v)-np.maximum(s(h),35);bad+=int((delta>1e-4).sum());excess=max(excess,float(delta.max(initial=0)))
    gates=dict(finite=bool(np.isfinite(v).all()),metadata_exact=all(np.array_equal(t[k],u[k],equal_nan=True) for k in t if k!='heights'),fixed_exact=not bool((changed&fixed).any()),outside_exact=not bool((changed&~allowed).any()),water_faces_exact=not bool((changed&water).any()),road_platform_exact=not bool((changed&(t['reserve']|t['platform'])).any()),dry_floor=bool(np.all(v[allowed]>=np.minimum(h[allowed],1.8)-1e-6)),max_change=float(abs(v-h).max())<=.400001,no_new_steep_faces=bad==0)
    return gates,dict(bad_faces=bad,max_slope_excess_degrees=excess,changed_vertices=int(changed.sum()),water_support_vertices=int(water.sum()))

def controls(h,t,fixed,allowed,p):
    r,c=np.indices((8,8));flat=r*.31+c*.27
    assert max(v.max() for _,v in edges(*face_normals(flat)))<1e-10
    fold=np.maximum(0,c-4)*6
    assert np.isclose(max(v.max() for _,v in edges(*face_normals(fold))),45)
    # Each mutation is passed through the same whole-domain physical consumer.
    results=[]
    masks=[('water_faces_exact',exact_wet_support(h,p),.1),('road_platform_exact',t['reserve'],.1),('outside_exact',~allowed,1.),('no_new_steep_faces',allowed,30.)]
    for key,mask,amount in masks:
        v=h.copy();rr,cc=map(int,np.argwhere(mask)[len(np.argwhere(mask))//2]);v[rr,cc]+=amount
        g,_=physical(h,v,t,t,fixed,allowed,p);assert not g[key],key;results.append(key+'_mutant_rejected')
    return ['inclined_plane_cross_product_zero','45_degree_fold_cross_product',*results]

def summarize(v):
    return dict(n=len(v),mean_sq_degrees=float(np.mean(v*v)),p99_degrees=float(np.percentile(v,99)),max_degrees=float(v.max()),above30=int((v>30).sum()))

def main():
    candidate=B/'candidate/terrain.npz';t=dict(np.load(SOURCE));u=dict(np.load(candidate));h=t['heights'].astype(float);v=u['heights'].astype(float);p=np.load(PLANE);m=dict(np.load(B/'constraints.npz'))
    gates,counts=physical(h,v,t,u,m['fixed'],m['allowed'],p);negative=controls(h,t,m['fixed'],m['allowed'],p)
    gates['all_target_floor_1_8']=bool(np.all(v[m['target']]>=1.8-1e-6))
    gates['no_lowering']=bool(np.all(v>=h-1e-6))
    original=np.load(B.parent/'v30-strict-dry-composition-20261009/candidate/terrain.npz')['heights']
    gates['cumulative_uplift_ev61']=bool(np.all(v<=original.astype(float)+.400001))
    gates['frozen_fields_exact']=all(sha(SOURCE.parent/name)==sha(B/'candidate'/name) for name in ['plane.npy','visible-field.npy'])
    mutated=v.copy();pos=tuple(np.argwhere(m['target'])[0]);mutated[pos]=1.79
    assert not np.all(mutated[m['target']]>=1.8-1e-6)
    negative.append('low_target_mutant_rejected')
    pmax=np.full(h.shape,-np.inf)
    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):np.fmax(pmax[dr:dr+2047,dc:dc+2047],p,out=pmax[dr:dr+2047,dc:dc+2047])
    dry=(h>=pmax)&(h>=.85);distance=distance_transform_edt(dry)*6;natural=dry&~t['reserve']&~t['platform']
    domains=dict(natural_bank=natural&(distance<=54),natural_interior=natural&(distance>54),natural_dry=natural)
    values={key:[[],[]] for key in [*domains,'editable_incident']};sector=[];worst=[]
    old=list(edges(*face_normals(h)));new=list(edges(*face_normals(v)))
    for (kind,before),(kind2,after) in zip(old,new):
        assert kind==kind2
        masks={name:incident_all(mask,kind) for name,mask in domains.items()};masks['editable_incident']=incident_any(m['allowed'],kind)
        for name,mask in masks.items():values[name][0].append(before[mask]);values[name][1].append(after[mask])
        valid=masks['editable_incident'];rr,cc=np.indices(before.shape)
        for sr in range(32):
            for sc in range(32):
                sl=np.s_[sr*64:min((sr+1)*64,before.shape[0]),sc*64:min((sc+1)*64,before.shape[1])];ok=valid[sl]
                if not ok.any():continue
                aa,bb=before[sl][ok],after[sl][ok]
                sector.append(dict(row=sr,col=sc,kind=kind,edges=len(aa),before_sum_sq=float(aa@aa),after_sum_sq=float(bb@bb),before_max=float(aa.max()),after_max=float(bb.max())))
        change=(before-after)*valid;ix=np.argpartition(change.ravel(),-8)[-8:]
        for k in ix:
            r,c=np.unravel_index(k,change.shape);worst.append(dict(kind=kind,x=float((c+.5)*6),z=float(12282-(r+.5)*6),before=float(before[r,c]),after=float(after[r,c]),delta=float(change[r,c])))
    stats={};angle_gates={}
    for name,(a,b) in values.items():
        aa,bb=np.concatenate(a),np.concatenate(b);s0,s1=summarize(aa),summarize(bb);stats[name]=dict(before=s0,after=s1,reduction=1-s1['mean_sq_degrees']/s0['mean_sq_degrees'])
        if name in domains:angle_gates[name+'_p99']=s1['p99_degrees']<=s0['p99_degrees']+1e-5;angle_gates[name+'_over30']=s1['above30']<=s0['above30']
        else:angle_gates['editable_energy_reduction']=stats[name]['reduction']>=0
    grouped={}
    for row in sector:
        key=(row['row'],row['col']);s=grouped.setdefault(key,dict(row=key[0],col=key[1],edges=0,before_sum_sq=0,after_sum_sq=0,before_max=0,after_max=0))
        for k in ('edges','before_sum_sq','after_sum_sq'):s[k]+=row[k]
        for k in ('before_max','after_max'):s[k]=max(s[k],row[k])
    sectors=list(grouped.values());regressed=[x for x in sectors if x['after_sum_sq']>x['before_sum_sq']+1e-6]
    (B/'sectors.json').write_text(json.dumps(sectors,indent=2)+'\n')
    roads=evaluate(v,t['water'].astype(bool));gates|=angle_gates;gates['roads_pass']=roads['status']=='PASS'
    report=dict(status='PASS_STRICT_DRY_FLOOR_SOURCE' if all(gates.values()) else 'FAIL_STRICT_DRY_FLOOR_SOURCE',source_sha256=sha(SOURCE),candidate_sha256=sha(candidate),gates=gates,counts=counts,angles=stats,sectors=len(sectors),regressed_sectors=regressed,largest_improvements=sorted(worst,key=lambda x:x['delta'],reverse=True),roads=roads,negative=negative,limits=['Source geometry verification; native package and loaded views still required.','All actually wet native triangles retain every support vertex exactly; entirely dry corners of finite P cells may rise. Existing river contour/end/residual graphic defects are not fixed by this dry-surface unit.','Per-sector increases retained even when whole-map gates pass; artistic acceptance is not inferred from energy.'])
    (B/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('roads','largest_improvements','regressed_sectors')},indent=2));print('REGRESSED_SECTORS',len(regressed));print('TOP_VIEWS',report['largest_improvements'][:4])

if __name__=='__main__':main()
