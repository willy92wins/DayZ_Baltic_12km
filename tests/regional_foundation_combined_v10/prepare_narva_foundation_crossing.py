"""Fit one local crossing to frozen V9; never edit water or change acceptance gates."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy.optimize import linprog
from scipy.interpolate import PchipInterpolator
from scipy.sparse import coo_matrix, csr_matrix, diags, hstack, vstack
from scipy.spatial import cKDTree
from shapely.geometry import LineString
from waterway_common import sample
from fit_road_native_triangles import weights

ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = '335554a6ea06f8546eeac5444aec7597eaf45df18be0c69b0baab48a573947b2'


def routes(centre, u, v, spans):
    """Straight west reserve; east Hermite connection to existing chain71."""
    end = spans * 12.5
    road = np.load(ROOT / 'tests/regional_foundation_roads_v6/reference.npz')
    chains = json.loads((ROOT / 'evidence/regional-foundation-v1/road-grade-chains-v6.json').read_text())['chains']
    chain = road['xy'][chains[71]]
    local = (chain-centre) @ np.stack([u, v]).T
    order = np.argsort(local[:, 0]); chain, local = chain[order], local[order]
    if np.min(np.linalg.norm(chain-centre, axis=1)) > 2:
        raise ValueError('Regional road anchor changed')
    use=(local[:,0]>240)&(local[:,0]<720)
    source=local[use]
    if np.any(np.diff(source[:,0])<=0):raise ValueError('Non-monotonic east road anchor')
    curve_fn=PchipInterpolator(source[:,0],source[:,1])
    target=centre+300*u+float(curve_fn(300))*v
    tangent=u+float(curve_fn.derivative()(300))*v
    tangent /= np.linalg.norm(tangent)
    start = centre+u*end
    length = np.linalg.norm(target-start)
    t = np.linspace(0, 1, int(np.ceil(length))+1)[:, None]
    curve = ((2*t**3-3*t**2+1)*start + (t**3-2*t**2+t)*length*u
             + (-2*t**3+3*t**2)*target + (t**3-t**2)*length*tangent)
    stations=np.arange(301,601,dtype=float)
    further=centre+stations[:,None]*u+curve_fn(stations)[:,None]*v
    return [LineString([centre-u*end, centre-u*420]), LineString(np.vstack([curve, further]))]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--spans', type=int, choices=[7,9], default=7)
    ap.add_argument('--out', required=True, type=Path)
    a=ap.parse_args()
    if a.out.exists(): raise ValueError('Fresh candidate path required')
    source=ROOT/'tests/regional_foundation_combined_v9'
    asc=source/'baltic_regional_foundation_v9.asc'
    if hashlib.sha256(asc.read_bytes()).hexdigest()!=BASE_SHA: raise ValueError('Frozen V9 drift')
    data=np.load(source/'reference.npz');h=data['candidate']
    with rasterio.open(asc) as ds:
        if not np.array_equal(ds.read(1),h): raise ValueError('V9 NPZ differs from ASC')
    f=json.loads((ROOT/'evidence/narva/evidence/narva-fit.json').read_text())
    centre=np.array(f['bridge_centre_tb'])-[200000,0]
    u=np.array(f['axis_east_unit']);v=np.array([u[1],-u[0]])
    paths=routes(centre,u,v,a.spans)
    positions=[];targets=[];groups=[];path_json=[];offset=0
    for side,line in zip(['west','east'],paths):
        station=np.linspace(0,line.length,int(np.ceil(line.length/.5))+1)
        p=np.array([line.interpolate(float(s)).coords[0] for s in station])
        tangent=np.gradient(p,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
        normal=np.column_stack([-tangent[:,1],tangent[:,0]])
        q=np.stack([p+off*normal for off in (-4,-2,0,2,4)],axis=1)
        end_y=float(sample(h,p[-1,0]+200000,p[-1,1]))
        t=np.clip((station-14)/min(300,line.length-25),0,1)
        goal=11+(end_y-11)*(3*t*t-2*t*t*t)
        positions.append(q.reshape(-1,2));targets.append(np.repeat(goal,5))
        groups.append((offset,station));offset+=len(q)*5
        path_json.append({'side':side,'coordinates':np.array(line.coords).tolist(),
                          'length_m':line.length,'end_target_m':end_y})
    positions=np.concatenate(positions);target=np.concatenate(targets)
    rr,cc=np.mgrid[0:2048,0:2048];xx=cc*6;zz=12282-rr*6
    region=(abs(xx-centre[0])<680)&(abs(zz-centre[1])<240)
    roi=np.flatnonzero(region)
    tree=cKDTree(positions[2::5])
    distance=tree.query(np.column_stack([xx.ravel()[roi],zz.ravel()[roi]]))[0]
    protected=(data['wet']|data['ocean']|data['fairway_support']|data['island_support_conservative'])
    variables=roi[(distance<64)&~protected.ravel()[roi]]
    index=np.full(h.size,-1,int);index[variables]=np.arange(len(variables));n=len(variables)
    ix,w=weights(positions)
    road_protected=int(np.count_nonzero(protected.ravel()[np.unique(ix)]))
    a.out.mkdir(parents=True)
    if road_protected:
        report={'status':'FAIL_PROTECTED_ROAD_SUPPORT','spans':a.spans,'protected_support_vertices':road_protected}
        (a.out/'solve.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return 2
    if np.any(index[ix]<0): raise ValueError('Road support missing from local variables')
    A=coo_matrix((w.ravel(),(np.repeat(np.arange(len(positions)),3),index[ix].ravel())),shape=(len(positions),n)).tocsr()
    rows=[];cols=[];values=[];limits=[]
    def bound_sample(c,vv,bound):
        row=len(limits);rows.extend([row]*len(c));cols.extend(c);values.extend(vv);limits.append(bound)
    for start,station in groups:
        for j in range(len(station)):
            mid=start+5*j+2
            for lane in (-2,-1,1,2):bound_sample([mid+lane,mid],[1,-1],.004)
            for lane in range(-2,3):
                k=mid+lane
                if j:
                    ds=station[j]-station[j-1]
                    bound_sample([k,k-5],[1,-1],.057*ds)
                if 0<j<len(station)-1:
                    d1=station[j]-station[j-1];d2=station[j+1]-station[j]
                    bound_sample([k,k-5,k+5],[1,-d2/(d1+d2),-d1/(d1+d2)],.0015)
    D=coo_matrix((values,(rows,cols)),shape=(len(limits),len(positions))).tocsr()
    B=D@A;rhs=np.asarray(limits)
    constraints=[B,-B];bounds=[rhs,rhs]
    # Polygonal conservative bound on both native triangle gradients. The
    # apothem margin keeps the entire polygon inside the 35 degree circle.
    cells=set()
    for vertex in variables:
        row,col=divmod(int(vertex),2048)
        for r in (row-1,row):
            for c in (col-1,col):
                if 0<=r<2047 and 0<=c<2047: cells.add(r*2048+c)
    tr=[];tc=[];tv=[];tb=[]
    angles=np.linspace(0,2*np.pi,16,endpoint=False)
    slope_limit=6*np.tan(np.radians(35))*np.cos(np.pi/16)
    # Road samples alone can miss a narrow steep facet. Bound every triangle
    # of the full8m road, padded by the cell half-diagonal, in all directions.
    cell_list=sorted(cells)
    centres=np.array([[(cell%2048+.5)*6,12282-(cell//2048+.5)*6] for cell in cell_list])
    road_cells=set(np.asarray(cell_list)[tree.query(centres)[0]<9])
    for cell in sorted(cells):
        local_slope_limit=6*.06*np.cos(np.pi/16) if cell in road_cells else slope_limit
        for triangle in ((cell,cell+1,cell+2049),(cell,cell+2048,cell+2049)):
            for angle in angles:
                ca,sa=np.cos(angle),np.sin(angle)
                # upper: dx=b-a, dz=d-b; lower: dx=d-c, dz=c-a
                coeff=(-ca,ca-sa,sa) if triangle[1]==cell+1 else (-sa,sa-ca,ca)
                row=len(tb);fixed=0
                for vert,value in zip(triangle,coeff):
                    k=index[vert]
                    if k>=0:tr.append(row);tc.append(k);tv.append(value)
                    else:fixed+=value*float(h.ravel()[vert])
                tb.append(local_slope_limit-fixed)
    T=coo_matrix((tv,(tr,tc)),shape=(len(tb),n)).tocsr()
    constraints.append(T);bounds.append(np.asarray(tb))
    C=vstack(constraints,format='csr');rhs=np.concatenate(bounds)
    prior=h.ravel()[variables].astype(float)
    soft=vstack([A,diags(np.ones(n))],format='csr');goal=np.r_[target,prior]
    m=len(goal);eye=diags(np.ones(m));zero=csr_matrix((C.shape[0],m))
    lhs=vstack([hstack([soft,-eye]),hstack([-soft,-eye]),hstack([C,zero])],format='csr')
    all_rhs=np.r_[goal,-goal,rhs]
    # All native vertices supporting the first14m of each approach are fixed
    # to deck11; this avoids a seam hidden between road samples.
    pinned={}
    for start,station in groups:
        inds=np.arange(start,start+5*int((station<=14).sum()))
        for k in index[ix[inds]].ravel():pinned[int(k)]=11.
        endpoint=float(target[start+5*(len(station)-1)])
        inds=np.arange(start+5*int((station<station[-1]-14).sum()),start+5*len(station))
        for k in index[ix[inds]].ravel():pinned[int(k)]=endpoint
    var_bounds=[(pinned[i],pinned[i]) if i in pinned else (float(prior[i]-12),float(prior[i]+12)) for i in range(n)]
    objective=np.r_[np.zeros(n),np.full(len(positions),20.),np.full(n,.15)]
    print(f'Solving {a.spans} spans: {n} native variables, {lhs.shape[0]} constraints',flush=True)
    result=linprog(objective,A_ub=lhs,b_ub=all_rhs,bounds=var_bounds+[(0,None)]*m,
                   method='highs',options={'time_limit':180,'primal_feasibility_tolerance':1e-8,'dual_feasibility_tolerance':1e-8})
    report={'status':'SOLVER_ONLY_NOT_ACCEPTED' if result.success else 'FAIL_OR_INCONCLUSIVE_SOLVER',
            'success':bool(result.success),'message':result.message,'solver_status':int(result.status),
            'spans':a.spans,'deck_m':11,'water_design_ceiling_m':3,'source_sha256':BASE_SHA,
            'variables':n,'constraints':lhs.shape[0],'protected_road_support_vertices':road_protected,'routes':path_json}
    if not result.success and result.status==2:
        fixed=prior.copy()
        for k,value in pinned.items():fixed[k]=value
        unpinned=np.array([i for i in range(n) if i not in pinned])
        hard=(T[:,unpinned].getnnz(axis=1)==0)&((T@fixed-np.asarray(tb))>1e-7)
        report['fully_fixed_slope_conflicts']=int(hard.sum())
        if hard.any():
            cell_list=sorted(cells)
            report['fixed_conflict_cells_xz']=sorted(set((int(cell_list[int(k)//32]%2048*6),int(12282-cell_list[int(k)//32]//2048*6)) for k in np.flatnonzero(hard)))
        feasible=linprog(np.zeros(n),A_ub=T,b_ub=np.asarray(tb),bounds=var_bounds,method='highs',options={'time_limit':60})
        report['native_slope_and_pins_only']={'status':int(feasible.status),'success':bool(feasible.success),'message':feasible.message}
    if result.success:
        out=h.copy();out.ravel()[variables]=result.x[:n].astype(np.float32);changed=out!=h
        assert not np.any(changed&protected)
        assert not np.any(changed&~region)
        arrays={k:data[k] for k in data.files};arrays['candidate']=out;arrays['changed']=out!=data['base']
        np.savez_compressed(a.out/'reference.npz',**arrays)
        np.savez_compressed(a.out/'delta-from-v9.npz',row=np.where(changed)[0],col=np.where(changed)[1],before=h[changed],after=out[changed])
        output=a.out/'baltic_regional_foundation_v10.asc'
        with output.open('w',newline='\n') as f:
            f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
            np.savetxt(f,out,fmt='%.9g')
        with rasterio.open(output) as ds:assert np.array_equal(ds.read(1),out)
        report.update(candidate_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),changed_vertices=int(changed.sum()),
                      maximum_adjustment_m=float(abs(out-h).max()),max_road_target_error_m=float(abs(A@result.x[:n]-target).max()))
    (a.out/'solve.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='routes'},indent=2))
    return 0 if result.success else 1


if __name__=='__main__':raise SystemExit(main())
