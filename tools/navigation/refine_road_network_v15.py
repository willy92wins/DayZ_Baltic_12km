"""One continuous-strip pilot: bounded grading, water protection, no native import."""
from pathlib import Path
from array import array
import subprocess,gc
import hashlib,json,time
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.sparse import coo_matrix,eye,hstack,vstack,save_npz
from scipy.optimize import linprog
from shapely.geometry import Polygon
from fit_road_native_triangles import weights
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'tests/regional_road_network_v15'


def triangle(row,col,side):
    a=row*2048+col;b=a+1;c=a+2048;d=c+1
    if side==0:return np.array([a,b,d]),np.array([-1.,1.,0.])/6,np.array([0.,1.,-1.])/6
    return np.array([a,c,d]),np.array([0.,-1.,1.])/6,np.array([1.,-1.,0.])/6


def touched(poly):
    x0,z0,x1,z1=poly.bounds
    for row in range(max(0,int(np.floor((12282-z1)/6))),min(2047,int(np.floor((12282-z0)/6))+1)):
        for col in range(max(0,int(np.floor(x0/6))),min(2047,int(np.floor(x1/6))+1)):
            for side in [0,1]:
                ix,_,_=triangle(row,col,side)
                tri=Polygon(np.column_stack([ix%2048*6,12282-ix//2048*6]))
                if tri.intersects(poly) and tri.intersection(poly).area>1e-10:yield row,col,side


def main():
    assert not OUT.exists();OUT.mkdir()
    source=ROOT/'tests/regional_foundation_combined_v10/reference.npz';data=np.load(source);h=data['candidate'];prior=h.ravel().astype(float)
    roads=np.load(ROOT/'tests/regional_foundation_roads_v6/reference.npz')
    chains=json.loads((ROOT/'evidence/regional-foundation-v1/road-grade-chains-v6.json').read_text(encoding='utf-8'))['chains'];routes=[]
    for number,indices in enumerate(chains):
        p=roads['xy'][indices]
        if len(p)<4:continue
        station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        if station[-1]<=36:continue
        routes.append(dict(chain=number,station_start_m=18.,station_end_m=float(station[-1]-18),solve_start_m=18.,solve_end_m=float(station[-1]-18),source_polyline=p.tolist()))
    wd=distance_transform_edt(~(data['wet']|data['ocean']))*6;rr,cc=np.mgrid[:2048,:2048]
    allowed=(wd>42)&~data['fairway_support']&~data['bank_support']&~data['island_support_conservative']&(np.hypot(cc*6-2417.1428225906,12282-rr*6-6889.8850822322)>480)
    def dry(p):
        r=np.clip(np.rint((12282-p[:,1])/6).astype(int),0,2047);c=np.clip(np.rint(p[:,0]/6).astype(int),0,2047)
        return (wd[r,c]>48)&(np.linalg.norm(p-[2417.1428225906,6889.8850822322],axis=1)>480)
    radius=np.tan(np.radians(35));facet_limit=radius*np.cos(np.pi/16)
    angle=np.arange(16)*np.pi/8;normals=np.column_stack([np.cos(angle),np.sin(angle)])
    initial=np.column_stack([np.cos(angle+np.pi/16),np.sin(angle+np.pi/16)])*radius
    polygons={};original_constraints={};support=np.zeros(h.shape,bool)
    def clip(poly,normal,limit):
        distance=poly@normal-limit
        if np.max(distance)<=1e-12:return poly
        answer=[]
        for i in range(len(poly)):
            j=(i+1)%len(poly);a=poly[i];b=poly[j];da=distance[i];db=distance[j]
            if da<=0:answer.append(a)
            if (da<=0)!=(db<=0):answer.append(a+(b-a)*(da/(da-db)))
        if not answer:raise ValueError('Empty gradient polygon despite feasible origin')
        return np.asarray(answer)
    def band(tri,normal,tangent):
        key=tuple(tri);poly=polygons.get(key,initial.copy());cons=original_constraints.setdefault(key,{})
        for direction,limit in [(normal,.0032),(tangent,.06)]:
            for sign in [-1,1]:
                v=direction*sign;k=(*np.round(v,14),limit)
                if k not in cons:
                    cons[k]=(v,limit);poly=clip(poly,v,limit)
        polygons[key]=poly;support.ravel()[triangle(*key)[0]]=True

    for route_number,route in enumerate(routes):
        if route_number%10==0:print(json.dumps(dict(stage='build_geometry',route=route_number,total=len(routes))),flush=True)
        p=np.asarray(route['source_polyline']);s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        lo=route['solve_start_m'];hi=route['solve_end_m'];knots=np.r_[lo,s[(s>lo)&(s<hi)],hi]
        q=np.column_stack([np.interp(knots,s,p[:,k]) for k in [0,1]]);eligible=dry(q)
        for i,(a,b) in enumerate(zip(q[:-1],q[1:])):
            if not(eligible[i] and eligible[i+1]):continue
            tangent=(b-a)/np.linalg.norm(b-a);normal=np.array([-tangent[1],tangent[0]])
            poly=Polygon([a+normal*4,b+normal*4,b-normal*4,a-normal*4])
            for tri in touched(poly):band(tri,normal,tangent)
        # All blend normals in a join are bounded by applying incident and
        # bisector directions to every native triangle touching its 4m disk.
        angle=np.arange(16)*np.pi/8;circle=np.column_stack([np.cos(angle),np.sin(angle)])*(4.001/np.cos(np.pi/16))
        for i in range(1,len(q)-1):
            if not np.all(eligible[i-1:i+2]):continue
            directions=[q[i]-q[i-1],q[i+1]-q[i]];directions=[v/np.linalg.norm(v) for v in directions]
            bisector=directions[0]+directions[1]
            if np.linalg.norm(bisector)<1e-6:raise ValueError('Reversing road corner')
            directions.append(bisector/np.linalg.norm(bisector))
            for tri in touched(Polygon(q[i]+circle)):
                for tangent in directions:band(tri,np.array([-tangent[1],tangent[0]]),tangent)
    support=(distance_transform_edt(~support)*6<=12)&allowed
    variables=np.flatnonzero(support);n=len(variables);mapping=np.full(h.size,-1,int);mapping[variables]=np.arange(n)
    rows=array("i");cols=array("i");vals=array("d");rhs=array("d")
    def bound(ix,w,limit):
        row=len(rhs);fixed=float(w@prior[ix]);rhs.append(limit-fixed)
        for j,value in zip(mapping[ix],w):
            if j>=0 and abs(value)>1e-14:rows.append(row);cols.append(j);vals.append(value)
    retained_total=0;original_total=0;maximum_redundancy_residual=0.
    for tri,poly in polygons.items():
        constraints=list(original_constraints[tri].values())+[(v,facet_limit) for v in normals]
        active=[(v,lim) for v,lim in constraints if np.max(poly@v)>=lim-1e-10]
        reduced=initial.copy()
        for v,lim in active:reduced=clip(reduced,v,lim)
        residual=max(float(np.max(reduced@v)-lim) for v,lim in constraints)
        assert residual<1e-9,(tri,residual)
        maximum_redundancy_residual=max(maximum_redundancy_residual,residual)
        ix,gx,gz=triangle(*tri)
        for v,lim in active:bound(ix,gx*v[0]+gz*v[1],lim)
        retained_total+=len(active);original_total+=len(constraints)
    road_constraints=len(rhs)
    affect=support[:-1,:-1]|support[1:,:-1]|support[:-1,1:]|support[1:,1:]
    for row,col in np.argwhere(affect):
        for side in [0,1]:
            tri=(int(row),int(col),side)
            if tri in polygons:continue
            ix,gx,gz=triangle(*tri)
            if np.all(mapping[ix]<0):continue
            for v in normals:bound(ix,gx*v[0]+gz*v[1],facet_limit)
    slope_constraints=len(rhs)-road_constraints
    polygon_count=len(polygons);del polygons,original_constraints;gc.collect()
    for route in routes:
        p=np.asarray(route['source_polyline']);s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        centre=np.arange(route['solve_start_m']+3,route['solve_end_m']-3,.5)
        pts=np.array([np.column_stack([np.interp(centre+delta,s,p[:,k]) for k in [0,1]]) for delta in [-3,0,3]])
        valid=np.logical_and.reduce([dry(v) for v in pts]);ix,w=weights(pts.reshape(-1,2));ix=ix.reshape(3,-1,3);w=w.reshape(3,-1,3)
        for i in np.flatnonzero(valid):
            indices=ix[:,i,:].ravel();coeff=(w[:,i,:]*np.array([-.5,1.,-.5])[:,None]).ravel();bound(indices,coeff,.022);bound(indices,-coeff,.022)
    B=coo_matrix((np.asarray(vals),(np.asarray(rows),np.asarray(cols))),shape=(len(rhs),n)).tocsr();rhs=np.asarray(rhs).copy();del rows,cols,vals;gc.collect();I=eye(n,format='csr')
    floor=np.minimum(prior[variables],1.4)-prior[variables]
    options={'time_limit':600,'threads':1,'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8}
    receipt=dict(status='PLANNED_CONTINUOUS_PILOT',source_npz_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),variables=n,constraints=len(rhs),road_constraints=road_constraints,slope_constraints=slope_constraints,road_triangles=polygon_count,redundant_original_count=original_total,redundant_retained_count=retained_total,redundancy_max_residual=maximum_redundancy_residual,routes=routes,maximum_allowed_delta_m=2.05,lateral_gradient=.0032)
    receipt['status']='PLANNED_FULL_DRY_NETWORK_CANDIDATE'
    save_npz(OUT/'constraints.npz',B)
    np.savez_compressed(OUT/'variables.npz',indices=variables,rhs=rhs,floor=floor,support=support)
    (OUT/'pre-solve.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in receipt.items() if k!='routes'}),flush=True)
    cap=2.05;matrix=vstack([hstack([B,coo_matrix((len(rhs),n))]),hstack([I,-I]),hstack([-I,-I])],format='csr')
    sparse_bytes=matrix.data.nbytes+matrix.indices.nbytes+matrix.indptr.nbytes
    available=int(subprocess.check_output(['powershell','-NoProfile','-Command','(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory'],text=True).strip())*1024
    required=2*1024**3+4*sparse_bytes
    receipt.update(available_memory_bytes=available,required_memory_bytes=required,amplified_sparse_bytes=sparse_bytes)
    if available<required:
        receipt['status']='STOPPED_MEMORY_GUARD_NO_TERRAIN';(OUT/'solve.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in receipt.items() if k!='routes'}));return
    began=time.monotonic();result=linprog(np.r_[np.zeros(n),np.ones(n)],A_ub=matrix,b_ub=np.r_[rhs,np.zeros(2*n)],bounds=[(max(-cap,float(v)),cap) for v in floor]+[(0,None)]*n,method='highs',options=options)
    receipt.update(success=bool(result.success),message=result.message,elapsed_s=time.monotonic()-began,vertex_delta_limit_m=cap,status='SOLVER_ONLY_NOT_ACCEPTED' if result.success else 'STOPPED_NO_CANDIDATE')
    if result.success:
        candidate=h.copy();candidate.ravel()[variables]=(prior[variables]+result.x[:n]).astype('float32');changed=candidate!=h;assert not np.any(changed&~support)
        asc=OUT/'baltic_road_network_v15.asc'
        with asc.open('w',encoding='ascii',newline='\n') as f:
            f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n');np.savetxt(f,candidate,fmt='%.9g')
        with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),candidate)
        arrays={k:data[k] for k in data.files};arrays.update(candidate=candidate,parent=h,changed=candidate!=data['base'],pilot_support=support,pilot_allowed=allowed)
        np.savez_compressed(OUT/'reference.npz',**arrays)
        receipt.update(changed_vertices=int(changed.sum()),max_delta_m=float(abs(candidate-h).max()),asc_sha256=hashlib.sha256(asc.read_bytes()).hexdigest(),constraint_residual_m=float(np.max(B@result.x[:n]-rhs)))
    (OUT/'solve.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in receipt.items() if k!='routes'}))

if __name__=='__main__':main()
