"""Independent consumer: reconstruct triangles from final terrain, without author graph."""
from pathlib import Path
import argparse, hashlib, json, sys
import numpy as np
import shapely
from shapely.geometry import Polygon, LineString, box
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

B=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
B9=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
B10=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
B12=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(B12))
from audit_frozen_visual import domain,topology_gate,visible_error,clip,area,UNIT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def geometry(heights,field,cells):
    polygons=[]
    for r,c in cells:
        xy=np.array([[c*6,12282-r*6],[c*6+6,12282-r*6],[c*6,12276-r*6],[c*6+6,12276-r*6]])
        ground=heights[r:r+2,c:c+2].ravel()
        for corners in ([0,1,3],[0,2,3]):
            depth=field[r,c,corners]-ground[corners]; weights=clip(UNIT,depth)
            if len(weights)>2:polygons.append(Polygon(weights@xy[corners]))
    return shapely.union_all(polygons,grid_size=1e-6)


def line_stats(lines):
    angles=[]
    for ln in lines:
        points=np.array([ln.interpolate(d).coords[0] for d in np.arange(0,ln.length,2)])
        if len(points)<10:continue
        a=points[3:-3]-points[:-6];b=points[6:]-points[3:-3]
        theta=np.arctan2(abs(a[:,0]*b[:,1]-a[:,1]*b[:,0]),np.sum(a*b,axis=1))
        angles.extend(np.degrees(theta).tolist())
    if not angles:raise ValueError('No measured contour')
    return dict(lines=len(lines),length_m=float(sum(l.length for l in lines)),samples=len(angles),
                p90_degrees=float(np.percentile(angles,90)),over30_share=float(np.mean(np.array(angles)>30)),max_degrees=float(max(angles)))


def gradient(h,dr,dc):
    rows,cols=np.array(h.shape)-1
    a=h[:-1,:-1];b=h[dr:dr+rows,dc:dc+cols];c=h[1:,1:]
    return np.degrees(np.arctan(np.hypot(b-a,c-b)/6))


def overlap_areas(before,after):
    db,da=before['triangles'],after['triangles'];overlap=np.minimum(before['areas'],after['areas'])
    changed=np.any(db!=da,axis=1)
    mixed=changed&(np.min(db,axis=1)<0)&(np.min(da,axis=1)<0)&(overlap>0)
    for i in np.flatnonzero(mixed):overlap[i]=area(clip(clip(UNIT,db[i]),da[i]))
    return overlap


def basic_gate(h,v,p,f,fixed,allowed):
    rows,cols=p.shape
    changed=v!=h;gates=dict(finite=bool(np.isfinite(v).all()),fixed_exact=not bool((changed&fixed).any()),
                          outside_scope_exact=not bool((changed&~allowed).any()),height_displacement=float(np.max(abs(v-h)))<=2.000001)
    badsign=0;badfloor=0;wetraise=0;drymargin=0;sample=[]
    for slot,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
        a=h[dr:dr+rows,dc:dc+cols];b=v[dr:dr+rows,dc:dc+cols];valid=np.isfinite(p)
        badsign+=int((valid&(np.sign(a-f[:,:,slot])!=np.sign(b-f[:,:,slot]))).sum())
        wet=valid&(a<p);dry=valid&~wet
        badfloor+=int((wet&(b<np.minimum(a,1.)-1e-6)).sum())
        wetraise+=int((wet&(b>a+1e-6)).sum())
        drymargin+=int((dry&(b<np.minimum(a,np.maximum(1.8,p+.0501))-1e-6)).sum())
    badfaces=[];max_slope_excess=0.
    for tri,(dr,dc) in enumerate(((0,1),(1,0))):
        before=gradient(h,dr,dc);after=gradient(v,dr,dc);limit=np.maximum(before,35);delta=after-limit
        touch=changed[:-1,:-1]|changed[dr:dr+rows,dc:dc+cols]|changed[1:,1:]
        max_slope_excess=max(max_slope_excess,float(delta[touch].max(initial=0)))
        for r,c in zip(*np.nonzero(touch&(delta>1e-4))):badfaces.append(dict(row=int(r),col=int(c),tri=tri,before_deg=float(before[r,c]),after_deg=float(after[r,c]),excess_deg=float(delta[r,c])))
    gates.update(visible_signs_exact=badsign==0,bed_floor=badfloor==0,no_wet_raise=wetraise==0,dry_margin=drymargin==0,slopes=len(badfaces)==0)
    return gates,dict(changed_vertices=int(changed.sum()),sign_changes=badsign,floor_violations=badfloor,wet_raises=wetraise,
                      dry_margin_violations=drymargin,max_slope_excess_deg=max_slope_excess,bad_faces=badfaces)


def controls():
    assert area(clip(UNIT,np.ones(3)))==18
    assert abs(area(clip(UNIT,np.array([1.,-1.,-1.])))-4.5)<1e-12
    straight=line_stats([LineString([(0,0),(40,0)])]);bend=line_stats([LineString([(0,0),(20,0),(20,20)])])
    assert straight['max_degrees']==0 and bend['max_degrees']>80
    before=domain(np.zeros((2,2)),np.ones((1,1)));missing=domain(np.full((2,2),2.),np.ones((1,1)))
    assert not topology_gate(before,missing,np.zeros(2))['pass_gate']
    partial=domain(np.array([[0.,2.],[2.,2.]]),np.ones((1,1)))
    assert not topology_gate(before,partial,partial['areas'])['pass_gate']
    # Actual production gates on small independent fixtures, not duplicate inequalities.
    h=np.full((2,2),1.2);p=np.full((1,1),1.5);f=np.full((1,1,4),1.5)
    fixed=np.zeros((2,2),bool);allowed=~fixed
    assert all(basic_gate(h,h,p,f,fixed,allowed)[0].values())
    for gate,value in (('bed_floor',.99),('no_wet_raise',1.3),('visible_signs_exact',1.6)):
        mutant=h.copy();mutant[0,0]=value
        assert not basic_gate(h,mutant,p,f,fixed,allowed)[0][gate],gate
    mutant=h.copy();mutant[0,0]=8
    assert not basic_gate(h,mutant,p,f,fixed,allowed)[0]['slopes']
    dry=np.full((2,2),1.8);mutant=dry.copy();mutant[0,0]=1.6
    assert not basic_gate(dry,mutant,p,f,fixed,allowed)[0]['dry_margin']
    return ['whole_triangle_18m2','quarter_triangle_4.5m2','straight_and_right_angle',
            'missing_body_rejected','area_loss_rejected','unchanged_physical_fixture_passes',
            'bed_floor_mutant_rejected','wet_raise_mutant_rejected','visible_sign_mutant_rejected',
            'steep_face_mutant_rejected','dry_margin_mutant_rejected']


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',default='candidate-native');args=ap.parse_args()
    source=B10/'measured-bank-bed-r2/terrain.npz';path=B/args.candidate/'terrain.npz'
    assert sha(source)=='e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c'
    assert sha(B12/'preserved-field.npy')=='7a5d0900533670a1e533965b36a6dcf28be2715f96f94ccbfbe6a846bdf98e37'
    t=dict(np.load(source));u=dict(np.load(path));h=t['heights'].astype(float);v=u['heights'].astype(float)
    p=np.load(B10/'frozen-field-reference/plane.npy');f=np.load(B12/'preserved-field.npy')
    masks=np.load(B9/'candidate-a/masks.npz');fixed=masks['fixed'].copy()|masks['corridor']
    allowed=np.zeros(h.shape,bool)
    for reach in ('R1','R2'):
        m=np.load(B/(reach+'-constraints.npz'));fixed|=m['fixed'];allowed.ravel()[m['movable']]=True
    gates,physical=basic_gate(h,v,p,f,fixed,allowed)
    gates['metadata_exact']=set(t)==set(u) and all(np.array_equal(t[k],u[k],equal_nan=True) for k in t if k!='heights')
    checks=controls();changed=np.flatnonzero(v!=h)
    # Run the real fixed gate against a changed fixed support; no model-author data involved.
    test=v.copy();index=int(np.flatnonzero(fixed)[100]);test.ravel()[index]+=.1
    assert not basic_gate(h,test,p,f,fixed,allowed)[0]['fixed_exact'];checks.append('fixed_vertex_mutant_rejected')
    del test
    axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text());outlines={}
    fig,axs=plt.subplots(1,2,figsize=(12,8),layout='constrained')
    for ax,reach in zip(axs,('R1','R2')):
        rc=np.array(axes[reach]['removed_cells']);r0,c0=rc.min(0)-3;r1,c1=rc.max(0)+4
        extent=box(c0*6,12282-r1*6,c1*6,12282-r0*6)
        cells=[(r,c) for r in range(r0,r1) for c in range(c0,c1) if np.isfinite(p[r,c])]
        old,new=geometry(h,f,cells),geometry(v,f,cells);lineparts=[]
        for shape,color,title in ((old,'#3070b5','Actual'),(new,'#d94a33','Candidato')):
            line=shapely.line_merge(shape.boundary.difference(extent.boundary.buffer(.001)))
            lines=[l for l in getattr(line,'geoms',[line]) if l.geom_type=='LineString' and l.length>24]
            lineparts.append(lines)
            for j,l in enumerate(lines):ax.plot(*np.array(l.coords).T,color=color,lw=1,label=title if j==0 else None)
        oldstats,newstats=map(line_stats,lineparts);distance=float(shapely.hausdorff_distance(shapely.union_all(lineparts[0]),shapely.union_all(lineparts[1])))
        oldislands=sum(Polygon(r).area>=1 for pg in getattr(old,'geoms',[old]) if pg.geom_type=='Polygon' for r in pg.interiors)
        newislands=sum(Polygon(r).area>=1 for pg in getattr(new,'geoms',[new]) if pg.geom_type=='Polygon' for r in pg.interiors)
        outlines[reach]=dict(before=oldstats,after=newstats,hausdorff_m=distance,islands_before=oldislands,islands_after=newislands)
        gates[reach+'_p90']=newstats['p90_degrees']<=.9*oldstats['p90_degrees']
        gates[reach+'_over30']=newstats['over30_share']<=oldstats['over30_share']+1e-12
        gates[reach+'_max']=newstats['max_degrees']<=oldstats['max_degrees']+1e-5
        gates[reach+'_distance']=distance<=4.1;gates[reach+'_islands']=newislands>=oldislands
        ax.set_aspect('equal');ax.set_title(reach);ax.legend()
    fig.savefig(B/(args.candidate+'-contours.png'),dpi=150);plt.close(fig)
    print(json.dumps(dict(geometry=gates,physical=physical,outlines=outlines),indent=2),flush=True)
    global_results={}
    for label,field in (('physical',None),('visible',f)):
        before,after=domain(h,p,field),domain(v,p,field);overlap=overlap_areas(before,after);topology=topology_gate(before,after,overlap)
        contacts=[dict(axis=axis,new=int(((a<=1e-8)&(b>1e-8)).sum()),lost=int(((a>1e-8)&(b<=1e-8)).sum())) for axis,(a,b) in enumerate(zip(before['contacts'],after['contacts']))]
        rr,cc=before['cells'];classes=np.c_[t['cls'][rr,cc],t['cls'][rr,cc+1],t['cls'][rr+1,cc],t['cls'][rr+1,cc+1]]
        dry=np.stack((np.all(classes[:,[0,1,3]]==0,axis=1),np.all(classes[:,[0,2,3]]==0,axis=1)),axis=1).ravel()
        gain=np.maximum(0,after['areas']-overlap);dry_gain=float(gain[dry].sum())
        gates[label+'_topology']=topology['pass_gate'];gates[label+'_contacts']=not any(c['new'] or c['lost'] for c in contacts);gates[label+'_dry_flood']=dry_gain<=1e-8
        if label=='visible':
            delta=f[rr,cc]-p[rr,cc,None];delta=np.stack((delta[:,[0,1,3]],delta[:,[0,2,3]]),axis=1).reshape(-1,3)
            max_offset=float(visible_error(after['triangles'],delta,after['areas']).max());gates['visible_offset']=max_offset<=.35001
        else:max_offset=None
        global_results[label]=dict(topology=topology,contacts=contacts,gained_area_m2=float(gain.sum()),lost_area_m2=float(np.maximum(0,before['areas']-overlap).sum()),dry_gain_m2=dry_gain,max_visible_offset_m=max_offset)
        print(json.dumps(dict(domain=label,result=global_results[label]),indent=2),flush=True)
    report=dict(status='PASS_SOURCE_TERRAIN' if all(gates.values()) else 'FAIL_SOURCE_TERRAIN',gates=gates,physical=physical,outlines=outlines,global_domains=global_results,
                controls=checks,source_sha256=sha(source),candidate_sha256=sha(path),limits=['Compiled coverage and runtime remain separate.','Solver iteration limit is not a proof of optimality; candidate assessed by independent geometry.'])
    (B/(args.candidate+'-verification.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],failed=[k for k,v in gates.items() if not v])))


if __name__=='__main__':main()
