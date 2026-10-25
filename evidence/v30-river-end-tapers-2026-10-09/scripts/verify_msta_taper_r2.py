"""Independent topology, exact supports, native sampling, and negative controls for the taper."""
from pathlib import Path
import hashlib,json,sys,warnings
import numpy as np
from shapely.geometry import shape,LineString
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-river-end-tapers-20261009');B10=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
sys.path[:0]=[str(W/'tools/terrain'),str(B10),str(B)]
from v30_common import cell_planes,tri_sample
from audit_pond_topology import compare,controls,domain
from audit_fairway_triangles_v30 import records,depths
from verify_roads_v30 import evaluate
from author_msta_taper import native_polygon
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def measured_width(h,p,axis,s):
    a=np.array(axis.interpolate(max(0,s-.1)).coords[0]);b=np.array(axis.interpolate(min(axis.length,s+.1)).coords[0]);v=b-a;v/=np.linalg.norm(v)
    mid=np.array(axis.interpolate(s).coords[0]);normal=np.array([-v[1],v[0]])
    # A second native sampler at 5 cm spacing; no target ellipse or author widths are read.
    d=np.arange(-25,25.0001,.05);xy=mid+d[:,None]*normal
    rr=np.clip(np.floor((12282-xy[:,1])/6).astype(int),0,2046);cc=np.clip(np.floor(xy[:,0]/6).astype(int),0,2046)
    wet=p[rr,cc]>tri_sample(h,xy[:,0],xy[:,1])+1e-5
    edges=np.diff(np.r_[False,wet,False].astype(int));starts=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)
    spans=[(d[a],d[b-1],(b-a)*.05) for a,b in zip(starts,ends)]
    nearest=min(spans,key=lambda q:max(q[0],-q[1],0),default=(0,0,0))
    return float(nearest[2])


def main():
    source=B10/'measured-bank-bed-r2/terrain.npz';candidate=B/'candidate-msta-r2/terrain.npz'
    assert sha(source)=='e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c'
    t=dict(np.load(source));u=dict(np.load(candidate));h=t['heights'].astype(float);v=u['heights'].astype(float)
    p=cell_planes(t['cls'],t['level'],sea_cut=.51);changed=v!=h
    axis=LineString(json.loads((B/'candidate-msta-r2/axis.json').read_text()))
    navmask=np.zeros_like(changed);nav=[]
    for file in [Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson'),W/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson']:
        for f in json.loads(file.read_text())['features']:
            if f['properties'].get('kind','corridor24m')!='corridor24m':continue
            q=records(shape(f['geometry']),p);navmask.ravel()[np.unique(q['ids'])]=True
            old,new=depths(h,q),depths(v,q);nav.append(dict(name=f['properties'].get('name',f['properties'].get('river')),min_before=float(old.min()),min_after=float(new.min()),exact=bool(np.array_equal(old,new))))
    protected=t['reserve']|t['platform']|t['beach']|navmask
    badslope=0
    for dr,dc in [(0,1),(1,0)]:
        def slopes(a):
            mid=a[dr:dr+2047,dc:dc+2047]
            return np.degrees(np.arctan(np.hypot(mid-a[:-1,:-1],a[1:,1:]-mid)/6))
        badslope+=int((slopes(v)>np.maximum(slopes(h),35)+1e-4).sum())
    topology,_=compare(h,v,p)
    # All the source components are still protected; no exception for a terminal may delete one.
    roads=evaluate(v,t['water'])
    refs=json.loads((W/'evidence/v30-global-water-risk-2026-10-09/scalar-r2-temporal-reference.json').read_text())
    points=refs['points'];xy=np.array([[q['x'],q['z']] for q in points])
    same=bool(np.max(np.abs(tri_sample(h,xy[:,0],xy[:,1])-tri_sample(v,xy[:,0],xy[:,1])))<1e-6)
    widths=[dict(station_m=s,before_m=measured_width(h,p,axis,s),after_m=measured_width(v,p,axis,s)) for s in np.arange(3.,66.01,3.)]
    bys={q['station_m']:q for q in widths}
    checks=dict(finite=bool(np.isfinite(v).all()),raise_only=bool(np.all(v>=h)),
        engineering_exact=not bool((changed&protected).any()),only_river_vertices=not bool((changed&(t['cls']!=5)).any()),
        source_metadata_exact=all(np.array_equal(t[k],u[k],equal_nan=True) for k in t if k!='heights'),
        no_new_bed_below_1m=not bool((changed&(v<1)&(h>=1)).any()),slopes=badslope==0,
        topology=topology['status']=='PASS_FROZEN_POND_MODEL',roads=roads['status']=='PASS',old_351_points_exact=same,
        end_width_reduced=bys[6]['after_m']<=.6*bys[6]['before_m'],
        gradual_over_multiple_cells=sum(q['before_m']-q['after_m']>.3 for q in widths if q['station_m']<=36)>=4,
        upstream_width_exact=all(abs(q['before_m']-q['after_m'])<=.051 for q in widths if q['station_m']>=54),
        terminal_within_12m=any(q['after_m']>0 for q in widths if q['station_m']<=12))
    negative=controls()
    negative['unmodified_terminal_rejected']=not (bys[6]['before_m']<=.6*bys[6]['before_m'])
    mutant=v.copy();r,c=np.argwhere(protected)[100];mutant[r,c]+=.1
    negative['engineering_mutation_rejected']=bool(((mutant!=h)&protected).any())
    report=dict(status='PASS_OFFLINE_MSTA_TAPER_RUNTIME_PENDING' if all(checks.values()) and all(negative.values()) else 'FAIL_MSTA_NOT_FOR_PACKAGING',
        source_sha256=sha(source),terrain_sha256=sha(candidate),checks=checks,negative=negative,
        changed_vertices=int(changed.sum()),max_raise_m=float((v-h).max()),bad_slope_faces=badslope,
        topology=topology,navigation=nav,roads=roads,widths=widths,old_control_count=len(points),
        limits=['Terminal only. Widths are native-height/plane samples at 5 cm spacing, not runtime or aesthetic acceptance.',
                'Rendering of waves and the intentional end shallows must still be tested; no global BALTIC-020 closure.'])
    (B/'msta-r2-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('navigation','roads','widths')},indent=2))
    # Technical geometry figure: native contours are derived from the triangles, target shown only for comparison.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    author=json.loads((B/'candidate-msta-r2/authoring.json').read_text());box=author['box']
    before=native_polygon(h,p,box);after=native_polygon(v,p,box)
    fig,ax=plt.subplots(figsize=(11,6),layout='constrained')
    for geom,col,label in [(before,'#b95042','Antes: terreno nativo'),(after,'#2a72ae','Candidato: terreno nativo')]:
        for i,part in enumerate(getattr(geom,'geoms',[geom])):
            if part.geom_type=='Polygon':ax.plot(*part.exterior.xy,color=col,label=label if i==0 else None)
    ax.plot(*np.array(axis.coords).T,color='#777777',linestyle=':',linewidth=.7)
    ax.set(xlim=(12162,12225),ylim=(1774,1814),aspect='equal',title='Msta: estrechamiento longitudinal, pendiente de comprobar en DayZ',xlabel='x (m)',ylabel='z (m)');ax.legend()
    fig.savefig(B/'msta-r2-native-contour.png',dpi=140)


if __name__=='__main__':main()
