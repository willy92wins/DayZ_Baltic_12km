from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.optimize import minimize_scalar

B=Path(__file__).parent;R=B.parent;O=R/'v30-strict-dry-floor-20261009'
sys.path.insert(0,str(R/'v30-native-hinge-finish-20261009'))
from verify_hinges import face_normals,edges
source=R/'v30-volkhov-stable-derivatives-20261009/candidate/terrain.npz'
t=np.load(source);h=t['heights'].astype(float);d=np.load(O/'constraints.npz');original=dict(edges(*face_normals(h)))
diagnosis=json.loads((O/'bank-diagnosis.json').read_text());threshold=diagnosis['threshold_degrees']
specs={'diagonal':([(0,0),(0,1),(1,0),(1,1)],[0,1,3],[0,2,3]),'vertical':([(0,0),(0,1),(1,1),(1,2)],[0,1,2],[1,2,3]),'horizontal':([(0,0),(1,0),(1,1),(2,1)],[0,1,2],[1,2,3])}
rows=[];error=0.;multi=0
for row in diagnosis['edges']:
    kind=row['kind'];r,c=row['row'],row['col'];offsets,ta,tb=specs[kind]
    coords=[(r+dr,c+dc) for dr,dc in offsets];var=[i for i,rc in enumerate(coords) if d['allowed'][rc]]
    if len(var)!=1:multi+=1;continue
    j=var[0];vals=np.array([h[rc] for rc in coords]);xz=np.array([[dc*6,-dr*6] for dr,dc in offsets]);matrices=[]
    for tri in [ta,tb]:
        coeff=np.linalg.inv(np.column_stack([xz[tri],np.ones(3)]));m=np.zeros((3,4));m[0,tri]=-coeff[0];m[2,tri]=-coeff[1];matrices.append(m)
    def angle(x):
        q=vals.copy();q[j]=x;na=matrices[0]@q;nb=matrices[1]@q;na[1]=nb[1]=1
        return float(np.degrees(np.arctan2(np.linalg.norm(np.cross(na,nb)),na@nb)))
    error=max(error,abs(angle(vals[j])-original[kind][r,c]))
    rc=coords[j];target=bool(d['target'][rc]);lo=max(vals[j],1.8) if target else vals[j];hi=vals[j]+.4
    result=minimize_scalar(angle,bounds=(lo,hi),method='bounded',options={'xatol':1e-12});assert result.success
    points=[(lo,angle(lo)),(hi,angle(hi)),(float(result.x),float(result.fun))];at,value=min(points,key=lambda x:x[1])
    grid=np.linspace(lo,hi,2049);gridminimum=min(map(angle,grid));assert value<=gridminimum+1e-9
    f32=np.float32(at);neighbours=[f32,np.nextafter(f32,np.float32(-np.inf)),np.nextafter(f32,np.float32(np.inf)),np.float32(lo),np.float32(hi)]
    feasible=[(float(x),angle(float(x))) for x in neighbours if float(x)>=lo and float(x)<=hi]
    assert feasible;f_at,f_value=min(feasible,key=lambda x:x[1]);limit=max(float(original[kind][r,c]),threshold)
    vertices=[]
    for rr,cc in coords:
        protections={key:bool(d[key][rr,cc]) for key in ['fixed','water_support','large_lake_banks']}
        protections.update({key:bool(t[key][rr,cc]) for key in ['reserve','platform','beach']})
        vertices.append(dict(row=rr,col=cc,height=float(h[rr,cc]),allowed=bool(d['allowed'][rr,cc]),target=bool(d['target'][rr,cc]),protections=protections))
    rows.append(dict(kind=kind,row=r,col=c,x=c*6,z=12282-r*6,target=target,target_vertex=list(rc),interval=[lo,hi],before=float(original[kind][r,c]),local_limit=limit,minimum_continuous_angle=value,continuous_height=at,minimum_float32_angle=f_value,float32_height=f_at,unavoidable_local_excess=f_value-limit,vertices=vertices))
assert error<1e-9
failed=[x for x in rows if x['unavoidable_local_excess']>1e-5]
out=dict(status='READ_ONLY_BOUNDARY_FEASIBILITY',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),input_edges=len(diagnosis['edges']),single_editable_edges=len(rows),multiple_editable_edges=multi,local_bound_failures=len(failed),unique_targets_requiring_neighbour_change=len(set(tuple(x['target_vertex']) for x in failed)),max_normal_agreement_error_degrees=error,maximum_unavoidable_local_excess=max((x['unavoidable_local_excess'] for x in rows),default=0),edges=rows,limits=['No terrain changes. Examines a sufficient per-edge bound; not proof of global percentile infeasibility.','Continuous scalar minimum checked against endpoints and a dense diagnostic grid; float32 neighbours sampled around that minimum.','Protected water supports and engineering stay fixed. No silent removal of pending targets.'])
(B/'boundary-feasibility.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='edges'},indent=2))
