"""Consumer audit of B using frozen engine planes and full native water domains."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,shapely
from shapely.geometry import Polygon,shape
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008');E=W/'evidence/v30-valley-smoothing-2026-10-08'
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import cell_planes,vertex_plane_bounds,grid_xz,tri_sample
from verify_roads_v30 import evaluate
from audit_fairway_triangles_v30 import records
label=sys.argv[1] if len(sys.argv)>1 else 'b'
source=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
if label.startswith('c'):source=B/'candidate-land180/terrain_valley.npz'
candidate=B/f'candidate-{label}/terrain_valley.npz'
t=dict(np.load(source));u=dict(np.load(candidate));h=t['heights'].astype(float);v=u['heights'].astype(float)
mask=np.load(B/f'candidate-{label if label.startswith("c") else "b"}/masks.npz');fixed=mask['fixed'];zone=mask['edited_shore']
plane=cell_planes(t['cls'],t['level']);pmin,pmax=vertex_plane_bounds(plane)
water=np.load('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008/stitched-water/visual_vertex_levels.npy')
x,z=grid_xz();wet=u['cls']>0;dry=~wet;oldwet=t['cls']>0;changed=h!=v;flip=wet!=oldwet
flood=dry&np.isfinite(pmax)&(v<pmax-1e-5)
exposed=wet&np.isfinite(pmin)&(v>pmin-.02+1e-5)
oldflood=~oldwet&np.isfinite(pmax)&(h<pmax-1e-5)
oldexposed=oldwet&np.isfinite(pmin)&(h>pmin-.02+1e-5)
badslopes=0
for dr,dc in ((0,1),(1,0)):
 def angle(a):
  mid=a[dr:dr+2047,dc:dc+2047]
  return np.degrees(np.arctan(np.hypot(mid-a[:-1,:-1],a[1:,1:]-mid)/6))
 touch=dry[:-1,:-1]|dry[dr:dr+2047,dc:dc+2047]|dry[1:,1:]
 badslopes+=int((touch&(angle(v)>np.maximum(angle(h),35)+1e-4)).sum())
paths=[Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson'),W/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson']
corridor=np.zeros_like(wet)
for p in paths:
 for f in json.loads(p.read_text())['features']:
  if f['properties'].get('kind','corridor24m')=='corridor24m':corridor.ravel()[np.unique(records(shape(f['geometry']),plane)['ids'])]=True
def curvature(a,m):
 xx=(a[1:-1,:-2]-2*a[1:-1,1:-1]+a[1:-1,2:])/36
 zz=(a[:-2,1:-1]-2*a[1:-1,1:-1]+a[2:,1:-1])/36
 xz=(a[2:,2:]-a[2:,:-2]-a[:-2,2:]+a[:-2,:-2])/144
 return float(np.sqrt(np.mean((xx*xx+zz*zz+2*xz*xz)[m[1:-1,1:-1]])))
cv={}
for name,m in dict(R3_valley=(x>7170)&(x<7470)&(z>5630)&(z<5920)&~oldwet,general_dry=~oldwet&~t['reserve']&~t['platform']).items():
 a,b=curvature(h,m),curvature(v,m);cv[name]=dict(before=a,after=b,reduction=1-b/a)
# Physical footprint is frozen before authoring. Native clipping, including exact-zero vertices.
domain=shape(json.loads((E/'contour-design.geojson').read_text())['domain'])
core=np.load(B/'contour-design.npz')['core']
cells=[]
rr,cc=np.nonzero(np.isfinite(plane)&(core[:-1,:-1]|core[1:,1:]))
centres=shapely.points(cc*6+3,12282-rr*6-3);inside=shapely.contains(domain,centres)
cells=list(zip(rr[inside],cc[inside]))
def wet_polygon(a):
 polys=[]
 for r,c in cells:
  for dr,dc in ((0,1),(1,0)):
   rc=[(r,c),(r+dr,c+dc),(r+1,c+1)]
   xy=np.array([(j*6,12282-i*6) for i,j in rc]);d=np.array([a[i,j]-water[i,j] for i,j in rc]);pts=[]
   for i,j in ((0,1),(1,2),(2,0)):
    if d[i]<=0:pts.append(xy[i])
    if d[i]*d[j]<0:pts.append(xy[i]+d[i]/(d[i]-d[j])*(xy[j]-xy[i]))
   if len(pts)>=3:polys.append(Polygon(np.round(pts,7)))
 return shapely.union_all(polys,grid_size=1e-6)
before,after=wet_polygon(h),wet_polygon(v)
def component_audit(a,b):
 def parts(g):return [p for p in getattr(g,'geoms',[g]) if p.geom_type=='Polygon' and p.area>=1.]
 old,new=parts(a),parts(b);rows=[]
 for i,p in enumerate(old):
  matches=[q for q in new if p.intersection(q).area>=1.]
  largest=max(matches,key=lambda q:p.intersection(q).area) if matches else None
  rows.append(dict(before_id=i,bounds=list(p.bounds),matches=len(matches),before_area=p.area,after_area=largest.area if largest is not None else 0.,area_ratio=largest.area/p.area if largest is not None else 0.,before_holes=sum(Polygon(r).area>=1 for r in p.interiors),after_holes=sum(Polygon(r).area>=1 for r in largest.interiors) if largest is not None else 0))
 return dict(before_components=len(old),after_components=len(new),components=rows,no_split_or_missing=all(r['matches']==1 for r in rows) and len(old)==len(new),area_preserved=all(r['area_ratio']>=.9 for r in rows),islands_preserved=all(r['after_holes']>=r['before_holes'] for r in rows))
topology=component_audit(before,after)
cut=before.boundary.intersection(domain.boundary.buffer(.001)).buffer(1.)
axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text())
scope={};code=(B/'measure_waterline.py').read_text();exec(code[:code.index('label=sys.argv')],scope)
outlines={};fig,axs=plt.subplots(1,3,figsize=(15,6),layout='constrained')
for ax,(name,a) in zip(axs,axes.items()):
 rc=np.array(a['removed_cells']);rs,cs=rc.T
 box=shapely.box(cs.min()*6-18,12282-(rs.max()+1)*6-18,(cs.max()+1)*6+18,12282-rs.min()*6+18)
 aa=shapely.line_merge(before.boundary.intersection(box).difference(cut))
 bb=shapely.line_merge(after.boundary.intersection(box).difference(cut))
 def lines(g):return [l for l in getattr(g,'geoms',[g]) if l.geom_type=='LineString' and l.length>12]
 la,lb=lines(aa),lines(bb)
 outlines[name]=dict(before=scope['stats'](la),after=scope['stats'](lb),hausdorff_m=float(shapely.hausdorff_distance(aa,bb)))
 for arr,col,title in ((la,'#397dba','Antes'),(lb,'#c74945',label.upper())):
  for j,l in enumerate(arr):ax.plot(*np.array(l.coords).T,color=col,lw=1,label=title if j==0 else None)
 ax.set(xlim=(box.bounds[0],box.bounds[2]),ylim=(box.bounds[1],box.bounds[3]),aspect='equal',title=name);ax.legend()
fig.savefig(E/f'contour-native-{label}.png',dpi=150);plt.close(fig)
roads=evaluate(v,t['water'].astype(bool))
checks=dict(finite=bool(np.isfinite(v).all()),structural_exact=not bool((changed&fixed).any()),corridors_exact=not bool(((changed|flip)&corridor).any()),roads_pass=roads['status']=='PASS',metadata_outside_local_exact=not bool((flip&~zone).any()),no_new_floor_exception=not bool((wet&(v<1.-1e-6)&~(oldwet&(h<1.))).any()),legacy_low_not_excavated=not bool((oldwet&(h<1)&(v<h-1e-6)).any()),no_new_dry_flood=not bool((flood&~oldflood).any()),no_new_wet_exposure=not bool((exposed&~oldexposed).any()),slopes=badslopes==0,R3_curvature=cv['R3_valley']['reduction']>=.15,general_curvature=cv['general_dry']['reduction']>=.1)
for name,a in outlines.items():
 checks[name+'_shore_turns']=a['after']['turn_over30_share']<=a['before']['turn_over30_share'] and a['after']['turn_p90']<=a['before']['turn_p90']
 checks[name+'_shore_distance']=a['hausdorff_m']<=4.1
if label.startswith('c'):
 checks.update(native_components=topology['no_split_or_missing'],component_areas=topology['area_preserved'],islands=topology['islands_preserved'])
np.savez_compressed(B/f'diagnostic-{label}.npz',flood=flood&~oldflood,exposed=exposed&~oldexposed)
report=dict(status='PASS_OFFLINE_VALLEY' if all(checks.values()) else 'FAIL',checks=checks,curvature=cv,outlines=outlines,topology=topology,new_dry_flood=int((flood&~oldflood).sum()),new_wet_exposure=int((exposed&~oldexposed).sum()),bad_faces=badslopes,reclassified_vertices=int(flip.sum()),corridor_vertices=int(corridor.sum()),wet_area_before=before.area,wet_area_after=after.area,roads=roads,terrain_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),limits=['Frozen physical pond planes; class-derived reconstruction is not the deployed water.','Native whole-domain audit corrects removed-cells clipping in the preliminary metric; no game acceptance.'])
(E/f'verification-{label}.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('roads','outlines')},indent=2));print(json.dumps(outlines,indent=2))
