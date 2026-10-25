from pathlib import Path
import csv, hashlib, json, sys
import numpy as np
from scipy.ndimage import distance_transform_edt, median_filter

OUT=Path(r'E:/DayZ-Baltic-Build/v30-bank-relief-review-20261010/luna-geometry')
C=Path(r'E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009/candidate')
OLD=Path(r'E:/DayZ-Baltic-Build/v30-exact-dry-support-20261009/candidate')
BASE=Path(r'E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009')
AUD=Path(r'E:/DayZ-Baltic-Build/v30-surface-crease-audit-20261009/audit_native_surface.py')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(AUD.parent))
import audit_native_surface as crease

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def normals(h):
    nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    a=np.stack((-(ne-nw)/6,np.ones_like(nw),(se-ne)/6),axis=-1)
    b=np.stack((-(se-sw)/6,np.ones_like(nw),(sw-nw)/6),axis=-1)
    return a/np.linalg.norm(a,axis=-1)[...,None], b/np.linalg.norm(b,axis=-1)[...,None]
def edges(a,b):
    for name,x,y in [('diagonal',a,b),('vertical',a[:,:-1],b[:,1:]),('horizontal',b[:-1],a[1:])]:
        yield name,np.degrees(np.arctan2(np.linalg.norm(np.cross(x,y),axis=-1),np.einsum('ijk,ijk->ij',x,y)))
def calculate_support(h,p,f):
    # Same physical/visible triangle contract as verify.py::exact_wet_support.
    corners=[(0,0),(0,1),(1,0),(1,1)]
    hv=[h[dr:dr+2047,dc:dc+2047] for dr,dc in corners]
    nominal=np.fmax(p,.85);visible=np.where(np.isfinite(p)[:,:,None],f,.85)
    support=np.zeros(h.shape,bool)
    for ids in [(0,1,3),(0,2,3)]:
        wet=np.logical_or.reduce([(nominal>hv[i])|(visible[:,:,i]>hv[i]) for i in ids])
        for i in ids:
            dr,dc=corners[i];support[dr:dr+2047,dc:dc+2047]|=wet
    return support

def edge_vertices(kind,r,c):
    if kind=='diagonal': return [(r,c),(r,c+1),(r+1,c),(r+1,c+1)]
    if kind=='vertical': return [(r,c),(r,c+1),(r+1,c+1),(r+1,c+2)]
    return [(r,c),(r+1,c),(r+1,c+1),(r+2,c+1)]
def xz(kind,r,c):
    if kind=='diagonal': return ((c+.5)*6,12282-(r+.5)*6)
    if kind=='vertical': return ((c+1)*6,12282-(r+.5)*6)
    return ((c+.5)*6,12282-(r+1)*6)
def face_slopes(h,r,c):
    a,b=normals(h)
    aa=float(np.degrees(np.arccos(np.clip(a[r,c,1],-1,1))))
    bb=float(np.degrees(np.arccos(np.clip(b[r,c,1],-1,1))))
    return aa,bb

assert crease.validate()
t=dict(np.load(C/'terrain.npz'));h=t['heights'].astype(np.float64);old=dict(np.load(OLD/'terrain.npz'))['heights'].astype(np.float64)
p=np.load(C/'plane.npy');f=np.load(C/'visible-field.npy');m=dict(np.load(BASE/'constraints.npz'))
assert h.shape==(2048,2048) and p.shape==(2047,2047) and f.shape[:2]==p.shape
support=calculate_support(h,p,f)
assert np.array_equal(support,m['water_support']), 'Calculated actual wet support differs from EV71 stored support'
# Band seeded only by the three river/navigation classes requested; other classes are not distance seeds.
seed=np.isin(t['cls'],[3,5,6]);dist=distance_transform_edt(~seed,sampling=6.0)
belt=dist<=96.0
# A fully eligible dry river-bank vertex must be in belt, land, outside engineering masks,
# outside exact wet support, and outside all already-protected constraints.
base_bank=(belt & (t['cls']==0) & ~support & ~t['water'].astype(bool) & ~t['beach'].astype(bool) & ~t['reserve'].astype(bool) & ~t['platform'].astype(bool))
assert not ((belt & (t['cls']==0) & ~support & ~t['reserve'].astype(bool) & ~t['platform'].astype(bool)) & (t['water'].astype(bool)|t['beach'].astype(bool))).any()
movable=base_bank & ~m['fixed']
fixed=m['fixed'].astype(bool)
# Face pair domain additionally excludes every paired face whose 4 unique vertices touch water or engineering.
face_vertex_domain=base_bank
source_normals=normals(h); old_normals=normals(old); old_edge_map=dict(edges(*old_normals))
stats={}; candidate_rows=[]
for kind,ang in edges(*source_normals):
    # Data rows from a paired hinge have exactly four unique vertices.
    full=crease.incident_all(face_vertex_domain,kind)
    anymov=crease.incident_any(movable,kind)
    # all 4 unique vertices fixed under currently reconstructed protections
    entirely_fixed=full & ~anymov
    may_move=full & anymov
    vals=ang[full];oldang=old_edge_map[kind];oldvals=oldang[full]
    stats[kind]=dict(in_domain=int(full.sum()),above30=int((vals>30).sum()),above45=int((vals>45).sum()),maximum_deg=float(vals.max(initial=0)),p99_deg=float(np.percentile(vals,99)) if vals.size else None,ev70_above30=int((oldvals>30).sum()),ev70_above45=int((oldvals>45).sum()),ev70_maximum_deg=float(oldvals.max(initial=0)),ev70_p99_deg=float(np.percentile(oldvals,99)) if oldvals.size else None,changed_hinges_ev70_to_ev71=int((np.abs(vals-oldvals)>1e-5).sum()),
        folds_over30_all4fixed=int((ang[entirely_fixed]>30).sum()),folds_over30_with_movable_vertex=int((ang[may_move]>30).sum()),
        folds_over45_all4fixed=int((ang[entirely_fixed]>45).sum()),folds_over45_with_movable_vertex=int((ang[may_move]>45).sum()))
    # Candidate list >= 30deg; sort later and pick spatially separated representatives.
    rr,cc=np.nonzero(full & (ang>30))
    for r,c in zip(rr.tolist(),cc.tolist()): candidate_rows.append((float(ang[r,c]),kind,r,c,int(anymov[r,c])))

candidate_rows.sort(reverse=True)
selected=[]
for deg,kind,r,c,nmovflag in candidate_rows:
    xx,zz=xz(kind,r,c)
    if any((xx-s['x_m'])**2+(zz-s['z_m'])**2 < 180.0**2 for s in selected): continue
    verts=edge_vertices(kind,r,c)
    nfree=sum(bool(movable[vr,vc]) for vr,vc in verts)
    nfixed=sum(bool(fixed[vr,vc]) for vr,vc in verts)
    assert all(base_bank[vr,vc] for vr,vc in verts)
    vals=np.array([h[vr,vc] for vr,vc in verts]);oldvals=np.array([old[vr,vc] for vr,vc in verts])
    med=float(median_filter(h,size=3,mode='nearest')[r:r+2,c:c+2].mean())
    # local prominence proxy: largest corner residual from its local 3x3 neighborhood median.
    residual=[]
    med3=median_filter(h,size=3,mode='nearest')
    for vr,vc in verts: residual.append(float(h[vr,vc]-med3[vr,vc]))
    before=next(a for k,a in edges(*old_normals) if k==kind)
    slopea,slopeb=face_slopes(h,r,c)
    oldangle=float(before[r,c])
    cls_dist=float(dist[r,c]);clsnear=int(t['cls'][r,c])
    row=dict(rank=len(selected)+1,kind=kind,row=r,col=c,x_m=xx,z_m=zz,dihedral_deg=deg,ev70_dihedral_deg=oldangle,delta_deg=deg-oldangle,
        paired_face_slopes_deg=[slopea,slopeb],height_range_m=float(vals.max()-vals.min()),corner_heights_m=[float(x) for x in vals],
        local_median_residuals_m=residual,max_abs_local_residual_m=max(abs(x) for x in residual),
        eligible_vertices=int(nfree),fixed_vertices=int(nfixed),nearest_river_seed_distance_m=cls_dist,hinge_cell_class=clsnear)
    selected.append(row)
    if len(selected)>=10: break

# Additional aggregate counts for all qualifying folds across hinge classes.
summary=dict(total_above30=sum(v['above30'] for v in stats.values()),total_above45=sum(v['above45'] for v in stats.values()),
             above30_all4fixed=sum(v['folds_over30_all4fixed'] for v in stats.values()),above30_with_movable_vertex=sum(v['folds_over30_with_movable_vertex'] for v in stats.values()),
             above45_all4fixed=sum(v['folds_over45_all4fixed'] for v in stats.values()),above45_with_movable_vertex=sum(v['folds_over45_with_movable_vertex'] for v in stats.values()),
             qualifying_native_hinges=int(sum(v['in_domain'] for v in stats.values())))
result=dict(status='OFFLINE_GEOMETRY_INVENTORY_ONLY',candidate_terrain_sha256=sha(C/'terrain.npz'),ev70_terrain_sha256=sha(OLD/'terrain.npz'),plane_sha256=sha(C/'plane.npy'),visible_field_sha256=sha(C/'visible-field.npy'),constraints_sha256=sha(BASE/'constraints.npz'),
    exact_support_vertex_count=int(support.sum()),support_matches_ev71_constraint=True,river_seed_vertices=int(seed.sum()),river_belt_vertices=int(belt.sum()),river_belt_limit_m=96,bank_dry_unprotected_vertices=int(base_bank.sum()),potentially_movable_bank_vertices=int(movable.sum()),
    stats_by_hinge_kind=stats,summary=summary,representative_maxima=selected,
    controls=crease.validate(),
    interpretation=['A hinge is a shared edge between two native terrain triangles; the 4 unique vertices of both triangles are the analysis unit.',
      'Dry requires exact physical/visible support exclusion from P/F triangles plus EV71 masks; reserve and platform faces are excluded.',
      'Potentially movable means at least one of the 4 vertices is in the proposed 96 m class-3/5/6 dry bank domain and not in EV71 fixed mask. This is eligibility only, not optimizer feasibility.',
      'Angles >30 degrees follow the already-used inventory gate; >45 is a descriptive severe-fold bin, not a new acceptance threshold.',
      'Height residual to a 3x3 median is a geometric outlier proxy, not a proof of a visually pyramidal silhouette.',
      'Native source triangles do not establish which LOD or normals the game rendered; no runtime, object, or package test was run.'])
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
with (OUT/'representative-maxima.csv').open('w',newline='',encoding='utf-8') as fcsv:
    w=csv.DictWriter(fcsv,fieldnames=list(selected[0]));w.writeheader()
    for row in selected: w.writerow(row)
print(json.dumps({k:result[k] for k in ['status','summary','stats_by_hinge_kind','river_belt_vertices','bank_dry_unprotected_vertices','potentially_movable_bank_vertices']},indent=2))
print('ANCHORS')
for row in selected: print(json.dumps(row))






