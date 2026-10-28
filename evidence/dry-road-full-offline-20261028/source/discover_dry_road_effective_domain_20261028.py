"""Bounded read-only surface attribution before defining the full native test."""
from pathlib import Path
import collections,json,sys,time
R=Path(__file__).resolve().parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/quality'),str(W/'tools/water')]
import numpy as np
import shapely
from shapely import Point,Polygon,STRtree
import dry_bed_road_candidate_ev112 as d
import water_constraint_diagnostic_ev112 as meter
O=R/'dry-road-effective-domain-20261028';meter.STARTED=time.monotonic();meter.MAX_SECONDS=120;O.mkdir(exist_ok=False);stop=meter.bounded(O)
pins={}
def pin(p,h=None):
    got=meter.sha(p);meter.require(h is None or got==h,'input_drift:'+str(p));pins[str(p)]=got;return p
def read(p):return json.loads(pin(p).read_bytes())
try:
    old=read(R/'dry-road-native-domain-r2-20261028/report.json')
    for path,h in old['inputs'].items():pin(Path(path),h)
    domain=read(R/'dry-road-native-domain-r2-20261028/points.json');meter.require(len(domain)==2658,'domain_count')
    a=R/'deployed-surface-prototypes-20261028';av=d.nz(a/'surface-prototypes.npz');inst=d.nz(a/'instances.npz');catalog=read(a/'model-catalog.json')
    manifest=read(W/'evidence/deployed-surface-prototypes-20261028/artifact-hashes.json');section_path=a/'model-sections.json';pin(section_path,manifest[section_path.relative_to(R).as_posix()]['sha256']);sections=read(section_path)
    sec={(m['index'],lod['index'],s['index']):s for m in sections for lod in m['lods'] for s in lod['sections']}
    grid=np.load(R/'dry-bed-road-candidate-20261028/kit-118-candidate.npz')['grid'][:21];source=d.nz(R/'pilot-visible-surface-extraction-20261028/models/cs_kit_118_0000.npz')
    q=np.asarray([p['xz'] for p in domain]);meta=av['meta'].copy();meta['kind']=np.where(meta['kind']==0,1,255)
    polys,vertices,refs,instances=d.local_water((av['vertices'],meta,inst,catalog),q.min(0),q.max(0))
    faces=[];faceinfo=[]
    for v,ref in zip(vertices,refs):
        if int(ref[0])==19394363:continue
        m=av['meta'][ref[1]];s=sec[(int(m['model']),int(m['lod']),int(m['section']))]
        faces.append(v[:int(ref[2])]);faceinfo.append(dict(instance=int(ref[0]),prototype_face=int(ref[1]),flags=int(ref[3]),water=s['texture'].endswith('/water_ext.paa'),model=catalog[int(m['model'])]['name']))
    for j,t in enumerate(grid.reshape(-1,3)[source['source_triangles']]):
        faces.append(t);faceinfo.append(dict(instance=19394363,candidate_bed_face=j,flags=0,water=False,model='baltic_stream_pilot/cs_kit_118_0000.p3d'))
    for j,(f,n) in enumerate(zip(source['road_water'],source['road_water_n'])):
        faces.append(f[:n]);faceinfo.append(dict(instance=19394363,preserved_water_face=j,flags=0,water=True,model='baltic_stream_pilot/cs_kit_118_0000.p3d'))
    triangles=[];info=[]
    for f,meta in zip(faces,faceinfo):
        meter.require(len(f) in (3,4),'unsupported_face')
        for j in range(1,len(f)-1):
            t=f[[0,j,j+1]];poly=Polygon(t[:,[0,2]])
            if poly.area==0:
                meter.require(meta['flags']!=0,'unflagged_degenerate');continue
            triangles.append(t);info.append(meta)
    triangles=np.array(triangles);shapes=[Polygon(t[:,[0,2]]) for t in triangles];tree=STRtree(shapes)
    waterids=[i for i,f in enumerate(info) if f['water']];water=shapely.union_all([shapes[i] for i in waterids]);counts=collections.Counter();rows=[];visualdiff=[];foreign=collections.Counter()
    for original,point in zip(domain,q):
        pt=Point(point);hits=[int(i) for i in tree.query(pt,predicate='intersects')]
        heights={i:float(d.solver.barycentric(triangles[i],point[None,:])[0]@triangles[i,:,1]) for i in hits}
        wet=[i for i in hits if info[i]['water']];dry=[i for i in hits if not info[i]['water']]
        wmax=max((heights[i] for i in wet),default=None);bmax=max((heights[i] for i in dry),default=None)
        roadway=max([original['ground'],*heights.values()]);flagged=[i for i in hits if info[i]['flags']]
        distance=float(water.boundary.distance(pt));uncertain=[]
        if distance<=original['float32_half_diagonal']:uncertain.append('water_boundary_numeric')
        if flagged:uncertain.append('flagged_surface')
        if original['bed'] is None:uncertain.append('outside_changed_model_after_roundtrip')
        if wmax is not None and original['water_ext'] is not None:visualdiff.append(original['water_ext']-wmax)
        others=sorted({info[i]['model'] for i in dry if info[i]['instance']!=19394363});foreign.update(others)
        expect='wet' if wmax is not None and wmax>original['ground'] else 'dry'
        counts[expect]+=1
        if uncertain:counts['uncertain']+=1
        if others:counts['foreign_dry_support']+=1
        rows.append(dict(id=original['id'],x=point[0],z=point[1],ground=original['ground'],candidate_bed=original['bed'],effective_bed=bmax,water_ext=wmax,roadway=roadway,expect=expect,uncertain=uncertain,foreign_dry_support=others,sources=original['sources'],roadway_faces=hits,water_faces=wet,water_boundary_distance=distance))
    pin(Path(__file__));pin(W/'plans/ev112-dry-road-native-probe-20261028.md');meter.require(all(meter.sha(p)==h for p,h in pins.items()),'input_drift_end')
    report=dict(status='EFFECTIVE_DOMAIN_DISCOVERY_ONLY',count=len(rows),counts=dict(counts),local_roadway_instances=instances,roadway_triangles=len(triangles),water_triangles=len(waterids),foreign_dry_models=dict(foreign),visual_minus_water_ext_range=None if not visualdiff else [min(visualdiff),max(visualdiff)],visual_water_comparisons=len(visualdiff),inputs=pins,measurement=meter.memory(),limits=['No native acceptance or mission prepared.','Roadway support is not independent Geometry collision proof for foreign models.','Numeric water boundaries remain uncertain; no tolerance changed.'])
    meter.dump(O/'points.json',rows);meter.dump(O/'face-info.json',info);np.savez_compressed(O/'roadway-triangles.npz',triangles=triangles);meter.dump(O/'report.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ('inputs',)},indent=2))
except Exception as exc:meter.dump(O/'failure.json',dict(type=type(exc).__name__,error=str(exc)));raise
finally:stop.set()
