from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.ndimage import distance_transform_edt
B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build');OLD=R/'v30-low-water-components-20261009'
sys.path.insert(0,str(OLD))
from discover_components import connected,area
SOURCE=R/'v30-coupled-native-shore-corrected-20261009/candidate/terrain.npz';P=R/'v30-global-water-risk-20261009/frozen-field-reference/plane.npy';F=R/'v30-frozen-water-stitch-20261009/preserved-field.npy'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def corners(cells):
    out=np.zeros((2048,2048),bool)
    for dr,dc in [(0,0),(0,1),(1,0),(1,1)]:out[dr:dr+2047,dc:dc+2047]|=cells
    return out
def bounds(o,pad=0):
    x0,z0,x1,z1=o['bounds'];return max(0,int(np.floor((12282-z1)/6))-pad),min(2047,int(np.ceil((12282-z0)/6))+pad),max(0,int(np.floor(x0/6))-pad),min(2047,int(np.ceil(x1/6))+pad)
def slope(h):
    h=h.astype(float);nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    return np.array([np.degrees(np.arctan(np.hypot(ne-nw,se-ne)/6)),np.degrees(np.arctan(np.hypot(sw-nw,se-sw)/6))])
def main():
    assert not (B/'authoring.json').exists()
    assert sha(SOURCE)=='12088d96fd04c7291e79037fda73dfed20c3c7b561ddc123155efa1d174e4abb'
    t=dict(np.load(SOURCE));h=t['heights'];p=np.load(P);f=np.load(F);scope=json.loads((R/'v30-isolated-basin-scope-20261009/scope.json').read_text())
    objects={o['id']:o for o in json.loads((OLD/'compiled-instance-bounds.json').read_text())['objects']};support=np.load(OLD/'physical-component-labels.npz')['support_domains']
    engineering=t['reserve']|t['platform']|t['beach'];allwater=corners(np.isfinite(p));items=[];allcore=np.zeros(h.shape,bool)
    for row in scope['groups']:
        if not row['eligible']:continue
        ids=set();corecells=np.zeros(p.shape,bool)
        for oid in row['objects']:
            r0,r1,c0,c1=bounds(objects[oid],1);ids.update(np.unique(support[r0:r1,c0:c1]).tolist())
            r0,r1,c0,c1=bounds(objects[oid]);corecells[r0:r1,c0:c1]=True
        ids.discard(0);cells=np.isin(support,list(ids));corecells|=cells;core=corners(corecells)
        assert int(cells.sum())==row['water_cells'] and int(core.sum())==row['core_vertices']
        assert not (allcore&core).any();allcore|=core
        rr,cc=np.nonzero(core);r0,r1=max(0,rr.min()-12),min(2048,rr.max()+13);c0,c1=max(0,cc.min()-12),min(2048,cc.max()+13)
        items.append(dict(row=row,cells=cells,core=core,box=(r0,r1,c0,c1)))
    displacement=np.zeros(h.shape);q=p.copy();g=f.copy();level=t['level'].copy();records=[];translations={};accepted_core=np.zeros(h.shape,bool);allowed=np.zeros(h.shape,bool);cellshift=np.zeros(p.shape)
    for item in items:
        row,cells,core=item['row'],item['cells'],item['core'];r0,r1,c0,c1=item['box'];sl=np.s_[r0:r1,c0:c1];local=h[sl];localcore=core[sl]
        other=corners(np.isfinite(p)&~cells);fixed=engineering|other|(allcore&~core)
        dist=distance_transform_edt(~localcore,sampling=6);s=np.clip(1-dist/36,0,1);weight=s*s*s*(10+s*(-15+6*s));weight[fixed[sl]]=0
        shift=row['proposed_shift_m'];trial=(local.astype(float)+shift*weight).astype(np.float32)
        ringreports=[]
        for lo,hi in [(12,36),(36,60)]:
            ring=(dist>lo)&(dist<=hi)&(t['cls'][sl]==0)&~allwater[sl]
            old=float(np.median(local[ring])) if ring.any() else None;new=float(np.median(trial[ring])) if ring.any() else None
            lv=float(p[cells].max());ringreports.append(dict(inner=lo,outer=hi,vertices=int(ring.sum()),perched_before=lv-old if old is not None else None,perched_after=lv+shift-new if new is not None else None))
        reasons=[]
        if (core&fixed).any():reasons.append('fixed_support_conflict')
        if np.any(core&np.isin(t['cls'],[1,3,5,6])):reasons.append('nonstanding_metadata')
        if max(float(np.max(a-np.maximum(b,35),initial=0)) for a,b in zip(slope(trial),slope(local)))>1e-4:reasons.append('new_steep_face')
        if any(r['perched_after'] is None or r['perched_after']>max(.3,r['perched_before'])+1e-6 for r in ringreports):reasons.append('perched_policy')
        rec=dict(group=row['group'],target_components=row['target_components'],shift_m=shift,objects=row['objects'],rings=ringreports,accepted=not reasons,reasons=reasons);records.append(rec)
        if reasons:continue
        changed=trial-local;displacement[sl]=np.maximum(displacement[sl],changed);accepted_core|=core;allowed[sl]|=(dist<36)&~fixed[sl]
        q[cells]=(p[cells].astype(float)+shift).astype(p.dtype);g[cells]=(f[cells].astype(float)+shift).astype(f.dtype);cellshift[cells]=shift
        meta=core&np.isfinite(level)&np.isin(t['cls'],[2,7]);level[meta]=(level[meta].astype(float)+shift).astype(level.dtype)
        for oid in row['objects']:assert oid not in translations;translations[oid]=shift
    v=(h.astype(float)+displacement).astype(np.float32);a=connected(h.astype(float),p);b=connected(v.astype(float),q)
    aa=area(a[4].reshape(-1,3));bb=area(b[4].reshape(-1,3));area_diff=float(abs(aa-bb).sum());depth_error=float(abs(a[3]-b[3]).max())
    hd=np.stack([h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]],axis=2);vd=np.stack([v[:-1,:-1],v[:-1,1:],v[1:,:-1],v[1:,1:]],axis=2)
    visual_error=float(abs(((g-vd)-(f-hd))[np.isfinite(f)]).max());changed=v!=h
    gates=dict(accepted_any=any(r['accepted'] for r in records),fixed_exact=np.array_equal(h[engineering],v[engineering]),outside_exact=not(changed&~allowed).any(),physical_depth=depth_error<1e-6,visible_depth=visual_error<1e-6,active_faces=np.array_equal(a[8],b[8]),connections=a[-1]==b[-1],components=a[-2]==b[-2],wet_area=area_diff<=.001,floor=float(v[accepted_core].min())>=1,new_slopes=max(float(np.max(x-np.maximum(y,35),initial=0)) for x,y in zip(slope(v),slope(h)))<=1e-4)
    out=B/'candidate';out.mkdir(exist_ok=False);np.savez_compressed(out/'terrain.npz',**(t|dict(heights=v,level=level)));np.save(out/'plane.npy',q);np.save(out/'visible-field.npy',g);np.savez_compressed(B/'domain.npz',allowed=allowed,core=accepted_core,cellshift=cellshift)
    report=dict(status='PASS_ISOLATED_BASIN_CANDIDATE_SOURCE' if all(gates.values()) else 'FAIL_ISOLATED_BASIN_CANDIDATE_SOURCE',source_sha256=sha(SOURCE),terrain_sha256=sha(out/'terrain.npz'),plane_sha256=sha(out/'plane.npy'),field_sha256=sha(out/'visible-field.npy'),gates={k:bool(v) for k,v in gates.items()},groups=records,accepted_groups=sum(r['accepted'] for r in records),accepted_targets=sum(len(r['target_components']) for r in records if r['accepted']),changed_vertices=int(changed.sum()),object_translations=translations,physical_depth_error=depth_error,visible_depth_error=visual_error,wet_area_error=area_diff,minimum_translated_bed=float(v[accepted_core].min()),limits=['Prepared repair of independent small standing basins; big lakes and flowing/protected groups excluded.','Rigid translation conserves shape, not a global claim about renderer behavior.','Metadata, compiled coverage and consumer readback still require independent validation.'])
    (B/'authoring.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:val for k,val in report.items() if k not in ['groups','object_translations']},indent=2));print(json.dumps([r for r in records if not r['accepted']],indent=2))
if __name__=='__main__':main()
