"""Read and bound every design profile reaching the cut edge; no terrain edits."""
from pathlib import Path
import json,sys
import numpy as np
import shapely
from shapely.geometry import LineString,Point,box
B=Path(__file__).parent
B14=Path('E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009')
B13=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
sys.path.insert(0,str(B13));from discover_native_turns import W,B9,B10,B12,sha,graph
SOURCE=B14/'candidate-repaired/terrain.npz'
assert sha(SOURCE)=='223029dedd7122096bb51c704fc722629b2be549f6c946b9cb89c7d1a8b6d6eb'
t=dict(np.load(SOURCE));h=t['heights'];m=dict(np.load(B9/'candidate-a/masks.npz'))
rr,cc=np.indices(h.shape);x=cc*6;z=12282-rr*6
oldborder=(x<66)|(x>12216)|(z<66)|(z>12216)
outer=(x<24)|(x>12258)|(z<24)|(z>12258)
fixed=(m['fixed']&~oldborder)|outer|t['reserve']|t['platform']|m['corridor']|m['summits']|np.isin(t['cls'],(1,4))|t['beach']|t['narva']
controls=np.zeros(h.shape,bool)
ref=W/'evidence/v30-global-contour-pass-2026-10-09/global-contour-temporal-reference.json'
for point in json.loads(ref.read_text())['points']:
    r=int(np.floor((12282-point['z'])/6));c=int(np.floor(point['x']/6));controls[max(0,r):min(2048,r+2),max(0,c):min(2048,c+2)]=True
fixed|=controls
profiles=Path('E:/DayZ-Baltic-Build/v30-v11/design/profiles.npz');p=np.load(profiles);boundary=box(60,60,12222,12222).boundary
terminals=[];excluded=[]
for name in p.files:
    a=p[name];line=LineString(a[:,1:3])
    for end in (0,-1):
        ex,ez=a[end,1:3]
        if min(ex,ez,12282-ex,12282-ez)>60:continue
        intersections=line.intersection(boundary)
        points=[g for g in getattr(intersections,'geoms',[intersections]) if g.geom_type=='Point']
        if not points:excluded.append(dict(name=name,end=end,reason='no_inner_cut_intersection'));continue
        endpoint=Point(ex,ez);point=min(points,key=lambda q:q.distance(endpoint))
        terminals.append(dict(name=name,end=end,x=point.x,z=point.y,box=[point.x-60,point.y-60,point.x+60,point.y+60]))
merged=shapely.union_all([box(*q['box']) for q in terminals]);jobs=[]
field=np.load(B12/'preserved-field.npy');plane=np.load(B10/'frozen-field-reference/plane.npy')
for component in getattr(merged,'geoms',[merged]):
    xmin,zmin,xmax,zmax=component.bounds
    r0=max(0,int((12282-zmax)//6));r1=min(2047,int(np.ceil((12282-zmin)/6)))
    c0=max(0,int(xmin//6));c1=min(2047,int(np.ceil(xmax/6)))
    names=[q['name']+':'+str(q['end']) for q in terminals if component.covers(Point(q['x'],q['z']))]
    cells=[(r,c) for r in range(max(0,r0-3),min(2047,r1+3)) for c in range(max(0,c0-3),min(2047,c1+3)) if np.isfinite(plane[r,c])]
    g=graph(h,field,cells)
    ids=np.unique(np.array([n['ids'] for n in g['nodes']],dtype=int).ravel());r,c=np.divmod(ids,2048)
    movable=ids[(r>r0)&(r<r1)&(c>c0)&(c<c1)&~fixed.ravel()[ids]]
    jobs.append(dict(box_cells=[r0,c0,r1,c1],features=names,contour_nodes=len(g['nodes']),movable_supports=len(movable)))
report=dict(status='NATIVE_TERMINAL_DISCOVERY',source_sha256=sha(SOURCE),profiles_sha256=sha(profiles),control_reference_sha256=sha(ref),terminals=terminals,excluded=excluded,jobs=jobs,controls=int(controls.sum()),candidate_boxes=len(jobs))
np.savez_compressed(B/'constraints.npz',fixed=fixed,controls=controls,outer=outer)
(B/'discovery.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(terminals=len(terminals),excluded=excluded,jobs=jobs),indent=2))
