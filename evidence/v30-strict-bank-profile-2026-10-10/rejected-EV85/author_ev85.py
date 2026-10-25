"""EV85 bounded two-patch SLSQP probe. Writes terrain only after every gate passes."""
from pathlib import Path
import hashlib, json, math, time
import numpy as np
from scipy.optimize import minimize

ROOT = Path(r'E:/DayZ-Baltic-Build')
OUT = ROOT / 'v30-coupled-shore-pilot-20261010'
EV79 = ROOT / 'v30-narva-dry-bank-relief-20261010'
B_DIR = ROOT / 'v30-mixed-bank-incremental-fixed-20261010'
EV83 = ROOT / 'v30-wet-support-shore-pilot-20261010/candidate/terrain.npz'
D4 = ROOT / 'v30-coupled-shore-feasibility-20261010/feasibility.json'
BASE_T = B_DIR / 'candidate/terrain.npz'
ORIG_T = EV79 / 'candidate/terrain.npz'
P_PATH = B_DIR / 'candidate/plane.npy'
F_PATH = B_DIR / 'candidate/visible-field.npy'
N=2048; STEP=6.0; Z0=12282.0; TOL_DEG=1e-4
FOCI=[(1880,191),(1785,366)]
MAX_SECONDS=120.0; MAXITER=150
EXPECTED={'B':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
          'EV79':'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c',
          'P':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
          'F':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()
def load_npz(p):
    with np.load(p,allow_pickle=False) as d:return {k:d[k] for k in d.files}
def write_json(p,d): Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def emit_profiles(base,ev83,cand,status):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows=[]; fig,axs=plt.subplots(2,2,figsize=(10,7),constrained_layout=True)
    for fi,(fr,fc) in enumerate(FOCI):
        panels=[('E-W',[(fr,fc+k) for k in range(-3,4)],[(fc+k)*STEP-fc*STEP for k in range(-3,4)]),
                ('N-S',[(fr+k,fc) for k in range(-3,4)],[-k*STEP for k in range(-3,4)])]
        for ai,(axis,points,dist) in enumerate(panels):
            ax=axs[fi,ai]
            bvals=[float(base[r,c]) for r,c in points]
            evals=[float(ev83[r,c]) for r,c in points]
            cvals=[float(cand[r,c]) for r,c in points]
            ax.plot(dist,bvals,'o-',label='B EV82-B')
            ax.plot(dist,evals,'s--',label='EV83')
            ax.plot(dist,cvals,'^-',label=('EV85' if status.startswith('PASS') else 'EV85 diagnóstico (sin candidato)'))
            ax.set_title(f'{axis}, foco x={fc*STEP} z={Z0-fr*STEP}; tramo 36 m')
            ax.set_xlabel('Distancia desde el foco (m)');ax.set_ylabel('Altura (m)')
            ax.set_xlim(-18,18);ax.grid(True,alpha=.3);ax.set_aspect('equal',adjustable='box')
            if fi==0 and ai==0:ax.legend(fontsize=8)
            for k,(r,c) in enumerate(points):
                rows.append({'focus_world_xz':[fc*STEP,Z0-fr*STEP],'axis':axis,'sample_index':k,
                    'row':r,'col':c,'world_x_m':c*STEP,'world_z_m':Z0-r*STEP,
                    'distance_from_focus_m':dist[k],'height_B_m':bvals[k],
                    'height_EV83_m':evals[k],'height_EV85_diagnostic_m':cvals[k],
                    'delta_vs_B_m':cvals[k]-bvals[k]})
    fig.suptitle(f'Perfiles geométricos 1:1; offline, no captura DayZ — {status}')
    fig.savefig(OUT/'profiles-full-36m-1to1.png',dpi=180);plt.close(fig)
    write_json(OUT/'profiles-full-36m-1to1.json',{'status':status,'units':'metres','axis_aspect':'1:1',
        'scope':'two complete 36m profiles per focus, 7 native vertices each axis',
        'B_sha256':EXPECTED['B'],'EV83_sha256':sha(EV83),'EV85_array_sha256':hashlib.sha256(cand.tobytes()).hexdigest(),
        'rows':rows})

def tri_topology():
    tris=[]; edge_faces={}
    for r in range(-2,2):
        for c in range(-2,2):
            nw,ne,sw,se=(r,c),(r,c+1),(r+1,c),(r+1,c+1)
            tris.extend(((nw,ne,se),(nw,sw,se)))
    for i,t in enumerate(tris):
        for k in range(3):edge_faces.setdefault(tuple(sorted((t[k],t[(k+1)%3]))),[]).append(i)
    inc=[i for i,t in enumerate(tris) if (0,0) in t]
    edges={}
    for i in inc:
        t=tris[i]
        for k in range(3):
            e=tuple(sorted((t[k],t[(k+1)%3])))
            if len(edge_faces[e])!=2:raise RuntimeError('nonmanifold patch fixture')
            edges[e]=tuple(edge_faces[e])
    if len(inc)!=6 or len(edges)!=12:raise RuntimeError('expected 6 faces/12 hinges')
    return tris,inc,[(e,p) for e,p in sorted(edges.items())]
TRIS,INCIDENT,HINGES=tri_topology()

def edge_desc(e):
    (r0,c0),(r1,c1)=e
    if abs(r1-r0)==1 and abs(c1-c0)==1:return ('diagonal',min(r0,r1),min(c0,c1))
    if c0==c1:return ('vertical',min(r0,r1),c0-1)
    return ('horizontal',r0-1,min(c0,c1))
def vertex_hinges(v):
    r,c=v
    return {edge_desc(((r+e[0][0],c+e[0][1]),(r+e[1][0],c+e[1][1]))) for e,_ in HINGES}

def normal(h,r,c,kind):
    if kind=='diagonal': pts=((r,c),(r,c+1),(r+1,c+1))
    elif kind=='vertical': pts=((r,c),(r,c+1),(r+1,c+1))
    elif kind=='horizontal': pts=((r,c),(r+1,c),(r+1,c+1))
    # Caller requests face normals separately through face_normals_at.
    raise AssertionError('use face_normals_at')
def face_normals_at(h,r,c,face):
    if face=='A': idx=((r,c),(r,c+1),(r+1,c+1))
    else: idx=((r,c),(r+1,c),(r+1,c+1))
    xyz=np.asarray([(cc*STEP,float(h[rr,cc]),-rr*STEP) for rr,cc in idx],dtype=np.float64)
    n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0])
    if n[1]<0:n=-n
    return n/np.linalg.norm(n)
def hinge_faces(desc):
    k,r,c=desc
    if k=='diagonal':return ((r,c,'A'),(r,c,'B'))
    if k=='vertical':return ((r,c,'A'),(r,c+1,'B'))
    return ((r,c,'B'),(r+1,c,'A'))
def hinge_angle(h,desc,cache=None):
    faces=hinge_faces(desc); ns=[]
    for r,c,f in faces:
        key=(r,c,f)
        if cache is not None and key in cache:n=cache[key]
        else:
            n=face_normals_at(h,r,c,f)
            if cache is not None:cache[key]=n
        ns.append(n)
    a,b=ns
    return math.degrees(math.atan2(float(np.linalg.norm(np.cross(a,b))),float(np.dot(a,b))))
def face_slope(h,r,c,f):
    n=face_normals_at(h,r,c,f)
    return math.degrees(math.atan2(math.hypot(float(n[0]),float(n[2])),abs(float(n[1]))))
def slope_faces_for_vertices(vertices):
    fs=set()
    for r,c in vertices:
        for cr in (r-1,r):
            for cc in (c-1,c):
                if cr>=0 and cc>=0 and cr<N-1 and cc<N-1:
                    for f,vs in (('A',((cr,cc),(cr,cc+1),(cr+1,cc+1))),('B',((cr,cc),(cr+1,cc),(cr+1,cc+1)))):
                        if any(v in vertices for v in vs):fs.add((cr,cc,f))
    return sorted(fs)

def order_edges(vertices):
    seen=set(); out=[]
    for r,c in vertices:
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if not(dr or dc):continue
                v=(r+dr,c+dc)
                if 0<=v[0]<N and 0<=v[1]<N:
                    e=tuple(sorted(((r,c),v)))
                    if e not in seen:seen.add(e);out.append(e)
    return out
def apply_delta(base, vertices, x):
    h=base.astype(np.float64,copy=True)
    for i,(r,c) in enumerate(vertices):h[r,c]=float(base[r,c])+float(x[i])
    return h
def eval_hinges(h,descs):
    cache={};return np.asarray([hinge_angle(h,d,cache) for d in descs],dtype=np.float64)
def slope_values(h,faces):
    cache={}; vals=[]
    for r,c,f in faces:
        key=(r,c,f)
        if key not in cache: cache[key]=face_normals_at(h,r,c,f)
        n=cache[key]
        vals.append(math.degrees(math.atan2(math.hypot(float(n[0]),float(n[2])),abs(float(n[1])))))
    return np.asarray(vals,dtype=np.float64)
def axial_extrema_window(h,row,col,radius=3):
    out=set()
    for r in range(row-radius,row+radius+1):
        for c in range(col-radius,col+radius+1):
            v=float(h[r,c])
            for axis,a,b in [('EW',float(h[r,c-1]),float(h[r,c+1])),('NS',float(h[r-1,c]),float(h[r+1,c]))]:
                if v>=a and v>=b and (v>a or v>b):out.add((r,c,axis,'max'))
                if v<=a and v<=b and (v<a or v<b):out.add((r,c,axis,'min'))
    return out

def topology_fixture():
    rng=np.random.default_rng(8501); h=rng.normal(size=(12,12)).astype(np.float32)
    # Independently reproduce the consumer's three hinge angle grids.
    nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    ones=np.ones_like(nw); ea=np.stack((6*ones,ne-nw,np.zeros_like(nw)),axis=-1)
    dg=np.stack((6*ones,se-nw,-6*ones),axis=-1); eb=np.stack((np.zeros_like(nw),sw-nw,-6*ones),axis=-1)
    a=np.cross(ea,dg);b=np.cross(dg,eb);a/=np.linalg.norm(a,axis=-1)[...,None];b/=np.linalg.norm(b,axis=-1)[...,None]
    arrays={'diagonal':np.degrees(np.arctan2(np.linalg.norm(np.cross(a,b),axis=-1),np.einsum('...i,...i->...',a,b))),
        'vertical':np.degrees(np.arctan2(np.linalg.norm(np.cross(a[:,:-1],b[:,1:]),axis=-1),np.einsum('...i,...i->...',a[:,:-1],b[:,1:]))),
        'horizontal':np.degrees(np.arctan2(np.linalg.norm(np.cross(b[:-1,:],a[1:,:]),axis=-1),np.einsum('...i,...i->...',b[:-1,:],a[1:,:])))}
    ds=sorted(vertex_hinges((5,5)))
    if len(ds)!=12:raise RuntimeError('hinge descriptor dedup fixture failed')
    got=eval_hinges(h,ds)
    for d,v in zip(ds,got):
        if abs(float(v)-float(arrays[d[0]][d[1],d[2]]))>2e-5:
            raise RuntimeError(f'hinge mapping mismatch {d}: {v} vs {arrays[d[0]][d[1],d[2]]}')
    return {'status':'PASS','focus_hinges':len(ds),'independent_consumer_cross_dot_max_error_deg':float(max(abs(float(v)-float(arrays[d[0]][d[1],d[2]])) for d,v in zip(ds,got)))}

class Deadline(Exception):pass
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    fixture=topology_fixture()
    ids={'B':sha(BASE_T),'EV79':sha(ORIG_T),'P':sha(P_PATH),'F':sha(F_PATH)}
    for k,v in EXPECTED.items():
        if ids[k]!=v:raise RuntimeError(f'identity mismatch {k}: {ids[k]}')
    d4=json.loads(D4.read_text(encoding='utf-8'))
    if d4.get('status')!='FEASIBLE' or d4.get('eligible_node_count_total')!=39 or d4.get('touched_8_neighbor_edges')!=220:
        raise RuntimeError('D4 feasibility provenance/counts mismatch')
    if d4['inputs']['B_terrain']['sha256']!=ids['B'] or d4['inputs']['EV79_terrain']['sha256']!=ids['EV79']:
        raise RuntimeError('D4 report does not match frozen inputs')
    bdata=load_npz(BASE_T); odata=load_npz(ORIG_T)
    B=bdata['heights'].astype(np.float32,copy=False); O=odata['heights'].astype(np.float32,copy=False)
    if B.shape!=(N,N) or O.shape!=B.shape:raise RuntimeError('terrain shape mismatch')
    patches=[]; started=time.monotonic(); solver=[]; candidate=B.copy()
    pinfo=d4['patches']; assert len(pinfo)==2
    all_vars_expected={tuple(v) for patch in pinfo for v in patch['eligible_nodes']}
    if len(all_vars_expected)!=39 or len(order_edges(all_vars_expected))!=220:
        raise RuntimeError('D4 variables/8-neighbor edge count changed')
    ev83_sha=sha(EV83)
    if ev83_sha!='f0e977d8bc2e11529aedc3851bb1d456b45ffee0e2b974af89db6a26fab087f9':
        raise RuntimeError(f'EV83 profile source identity mismatch: {ev83_sha}')
    boundmap={tuple(q['vertex']):tuple(q['delta_bounds']) for q in d4['scalar_delta_bounds']}
    # Single, deterministic solve per focus patch. Each x0 is the directly
    # checked sparse feasibility witness from D4 (no unconstrained start).
    for pi,piinfo in enumerate(pinfo):
        patch_started=time.monotonic()
        verts=[tuple(v) for v in piinfo['eligible_nodes']]
        if piinfo['eligible_mutable_nodes']!=len(verts):raise RuntimeError('D4 variable count mismatch')
        index={v:i for i,v in enumerate(verts)}
        bounds=[boundmap[v] for v in verts]
        if any(lo>hi+1e-10 for lo,hi in bounds):raise RuntimeError('empty D4 scalar bound')
        # Sparse threshold witness; second focus couples to its north neighbor.
        x0=np.zeros(len(verts),dtype=np.float64); focus=FOCI[pi]
        x0[index[focus]]=-0.1
        if pi==1:
            north=(focus[0]-1,focus[1])
            x0[index[north]]=-0.06495246887207032
        if any(x0[i]<bounds[i][0]-1e-8 or x0[i]>bounds[i][1]+1e-8 for i in range(len(verts))):
            raise RuntimeError(f'sparse D4 start outside bounds patch {pi}')
        edges=order_edges(verts)
        def order_ineq(x):
            out=[]
            for u,v in edges:
                du=x[index[u]] if u in index else 0.0
                dv=x[index[v]] if v in index else 0.0
                gap=float(B[u])-float(B[v])
                if gap>0:out.append(gap+du-dv)
                elif gap<0:out.append(-gap+dv-du)
            return np.asarray(out,dtype=np.float64)
        def order_eq(x):
            return np.asarray([(x[index[u]] if u in index else 0.0)-
                               (x[index[v]] if v in index else 0.0)
                               for u,v in edges if float(B[u])==float(B[v])],dtype=np.float64)
        if np.min(order_ineq(x0),initial=0)<-1e-8 or np.max(np.abs(order_eq(x0)),initial=0)>1e-8:
            raise RuntimeError('D4 start violates 8-neighbor order')
        # All affected hinges are deduplicated before any objective/constraint.
        desc=sorted(set().union(*(vertex_hinges(v) for v in verts)))
        focus_desc=sorted(vertex_hinges(focus))
        if len(focus_desc)!=12:raise RuntimeError('focus must touch exactly 12 unique hinges')
        slopefaces=slope_faces_for_vertices(set(verts))
        old_desc=eval_hinges(B,desc); sector_max={}
        for dd,a in zip(desc,old_desc):sector_max.setdefault((dd[1]//64,dd[2]//64),[]).append(float(a))
        caps=np.asarray([min(max(sector_max[(dd[1]//64,dd[2]//64)])+TOL_DEG,
                             30.0+TOL_DEG if old_desc[i]<=30.0+TOL_DEG else math.inf)
                         for i,dd in enumerate(desc)],dtype=np.float64)
        oldslopes=slope_values(B,slopefaces)
        slopecaps=[]
        for r,c,f in slopefaces:
            base_s=face_slope(B,r,c,f);slopecaps.append(max(35.0,base_s))
        slopecaps=np.asarray(slopecaps,dtype=np.float64)
        fidx=[desc.index(dd) for dd in focus_desc]
        focus_energy=float(old_desc[fidx]@old_desc[fidx])
        state_cache={'x':None,'angles':None,'slopes':None}
        def state(x):
            xv=np.asarray(x,dtype=np.float64)
            if state_cache['x'] is None or not np.array_equal(xv,state_cache['x']):
                hh=apply_delta(B,verts,xv)
                state_cache['x']=xv.copy();state_cache['angles']=eval_hinges(hh,desc)
                state_cache['slopes']=slope_values(hh,slopefaces)
            return state_cache['angles'],state_cache['slopes']
        def angles(x):return state(x)[0]
        def slopes(x):return state(x)[1]
        constraints=[{'type':'ineq','fun':order_ineq},
            {'type':'ineq','fun':lambda x: caps-angles(x)},
            {'type':'ineq','fun':lambda x: slopecaps-slopes(x)},
            {'type':'ineq','fun':lambda x: 0.99*focus_energy-float(angles(x)[fidx]@angles(x)[fidx])},
            {'type':'ineq','fun':lambda x: -0.1-float(x[index[focus]])}]
        if len(order_eq(x0)):constraints.append({'type':'eq','fun':order_eq})
        calls={'fun':0,'con':0}; last=[x0.copy()]
        def objective(x):
            calls['fun']+=1
            if time.monotonic()-started>MAX_SECONDS:raise Deadline()
            a=angles(x);return float(a@a)
        def callback(x):
            last[0]=np.array(x,copy=True)
            if time.monotonic()-started>MAX_SECONDS:raise Deadline()
        try:
            res=minimize(objective,x0,method='SLSQP',bounds=bounds,constraints=constraints,
                callback=callback,options={'maxiter':MAXITER,'ftol':1e-10,'disp':False})
            last[0]=np.array(res.x,copy=True)
            st={'patch':pi,'focus':list(focus),'variables':len(verts),'affected_hinges_dedup':len(desc),
                'order_edges':len(edges),'slope_faces':len(slopefaces),'iterations':int(res.nit),
                'success':bool(res.success),'status':int(res.status),'message':str(res.message),
                'objective_initial':float(objective(x0)),'objective_final':float(objective(res.x)),
                'focus_delta':float(res.x[index[focus]]),'focus_energy_before':focus_energy,
                'focus_energy_after':float(angles(res.x)[fidx]@angles(res.x)[fidx]),'max_order_violation':float(max(0,-np.min(order_ineq(res.x),initial=0))),
                'max_order_equality_residual':float(np.max(np.abs(order_eq(res.x)),initial=0)),
                'max_hinge_cap_excess':float(max(0,np.max(angles(res.x)-caps))),
                'max_slope_cap_excess':float(max(0,np.max(slopes(res.x)-slopecaps))),
                'elapsed_solve_seconds':round(time.monotonic()-patch_started,3),
                'elapsed_total_seconds':round(time.monotonic()-started,3),'fun_calls':calls['fun']}
            solver.append(st)
            for i,v in enumerate(verts):candidate[v]=np.float32(float(B[v])+float(res.x[i]))
            patches.append({'verts':verts,'index':index,'descs':desc,'caps':caps,'old_angles':old_desc,
                            'slopefaces':slopefaces,'slopecaps':slopecaps,'focus':focus,'fidx':fidx,'x':res.x.copy()})
        except Deadline:
            solver.append({'patch':pi,'focus':list(focus),'status':'TIMEOUT','variables':len(verts),
                           'maxiter':MAXITER,'elapsed_solve_seconds':round(time.monotonic()-started,3)})
            break
    passed_solver=(len(solver)==2 and all(x.get('success') for x in solver) and time.monotonic()-started<=MAX_SECONDS)
    # Always save the continuous/quantized diagnostic vector on a failed run.
    np.savez_compressed(OUT/'diagnostic-vector.npz',heights=candidate.astype(np.float32),delta=(candidate.astype(np.float64)-B.astype(np.float64)))
    result={'status':'PENDING_POSTSOLVE' if passed_solver else 'SOLVER_FAILED', 'inputs':ids,
            'D4_report_sha256':sha(D4),'D4_solver_script_sha256':sha(ROOT/'v30-coupled-shore-feasibility-20261010/shore_order_feasibility.py'),
            'author_script_sha256':sha(__file__),'scipy_version':__import__('scipy').__version__,
            'scipy_minimize_signature':'verified inspect.signature(minimize) before execution',
            'solver':solver,'elapsed_total_s':round(time.monotonic()-started,3),
            'candidate_written':False,'gates':{},
            'EV83_profile_source_sha256':ev83_sha,
            'plan_p99_count':'EV82-B values: bank p99 4.982070186774692/count 1; interior p99 3.667753611431574/count 112; exact postsolve float32 gate.'}
    if not passed_solver:
        emit_profiles(B,load_npz(EV83)['heights'],candidate,result['status'])
        result['profiles']={'png':str(OUT/'profiles-full-36m-1to1.png'),'json':str(OUT/'profiles-full-36m-1to1.json')}
        write_json(OUT/'authoring-report.json',result);return
    # Verify exact local geometry gates after float32 quantization.
    g={}; all_desc=sorted(set().union(*(set(q['descs']) for q in patches)))
    old_union=eval_hinges(B,all_desc); new_union=eval_hinges(candidate,all_desc)
    g['no_new_over30_local']=not bool(np.any((old_union<=30.0+TOL_DEG)&(new_union>30.0+TOL_DEG)))
    g['union_energy_decreased']=float(new_union@new_union)<float(old_union@old_union)-1e-10
    g['focus_each_reduced_ge_1pct']=all(float(eval_hinges(candidate,q['descs'])[q['fidx']]@eval_hinges(candidate,q['descs'])[q['fidx']]) <= 0.99*float(q['old_angles'][q['fidx']]@q['old_angles'][q['fidx']])+1e-8 for q in patches)
    g['both_focus_lower_at_least_0_1m']=all(float(candidate[q['focus']])-float(B[q['focus']])<=-0.1 for q in patches)
    g['slopes_and_hinge_caps']=all(float(np.max(eval_hinges(candidate,q['descs'])-q['caps']))<=1e-4 and float(np.max(slope_values(candidate,q['slopefaces'])-q['slopecaps']))<=1e-4 for q in patches)
    order_bad=[]
    allvars=set().union(*(set(q['verts']) for q in patches))
    for u,v in order_edges(allvars):
        before=float(B[u])-float(B[v]); after=float(candidate[u])-float(candidate[v])
        if (before>0 and after<0) or (before<0 and after>0) or (before==0 and after!=0):order_bad.append([u,v])
    g['all_8_neighbor_order_float32']=not order_bad
    delta79=candidate.astype(np.float64)-O.astype(np.float64); deltaB=candidate.astype(np.float64)-B.astype(np.float64)
    g['no_height_raise_vs_B']=bool(np.all(deltaB<=0.0))
    g['budget_and_floor']=bool(np.max(np.abs(delta79))<=2.0+1e-7 and np.all(candidate.astype(np.float64)>=np.minimum(O.astype(np.float64),1.8)-1e-7))
    allowed=set().union(*(set(q['verts']) for q in patches))
    changed_set={tuple(map(int,q)) for q in np.argwhere(candidate!=B)}
    g['only_39_vertices_changed']=changed_set.issubset(allowed) and len(changed_set)<=39
    axial_added=[]
    for fr,fc in FOCI:
        axial_added.extend(sorted(axial_extrema_window(candidate,fr,fc)-axial_extrema_window(B,fr,fc)))
    g['no_new_axial_extrema']=len(axial_added)==0
    crossing_bad=[]
    for q in d4['crossing_records']:
        vr,vc=q['vertex'];orow,oc=q['other_fixed']
        lv=float(q['level_at_variable']);lo_=float(q['level_at_other']);length=float(q['edge_length_m'])
        h0=float(q['before_heights'][0]);h1=float(q['before_heights'][1])
        d0=h0-lv;d1=h1-lo_
        n0=float(candidate[vr,vc])-lv;n1=float(candidate[orow,oc])-lo_
        if d0*d1>=0 or n0*n1>=0:crossing_bad.append({'vertex':q['vertex'],'edge':q['other_fixed'],'reason':'sign/topology'})
        else:
            t0=-d0/(d1-d0);t1=-n0/(n1-n0);move=abs(t1-t0)*length
            if move>1.0+1e-8:crossing_bad.append({'vertex':q['vertex'],'edge':q['other_fixed'],'move_m':move})
    g['crossing_topology_and_le_1m']=len(crossing_bad)==0
    # Full-map consumer-equivalent p99/count recalculation (no smooth surrogate).
    report_ref=json.loads((B_DIR/'review-luna/report.json').read_text(encoding='utf-8'))
    if report_ref.get('status')!='PASS_EV82_CONSUMER' or report_ref.get('candidate_sha256')!=EXPECTED['B']:
        raise RuntimeError('EV82-B p99/count report identity/status mismatch')
    # Exact masks copied from consumer definitions; all angles are from natively triangulated faces.
    cls=bdata['cls']; wet=load_npz(EV79/'constraints.npz')['wet_support'].astype(bool)
    eng=(bdata['reserve'].astype(bool)|bdata['platform'].astype(bool))
    dry=(cls==0)&~wet&~eng
    # bank = dry and within 96m of classes 3/5/6; derive distance with scipy as verifier does.
    from scipy.ndimage import distance_transform_edt
    bank=dry&(distance_transform_edt(~np.isin(cls,(3,5,6)),sampling=STEP)<=96.0+1e-9)
    interior=dry&~bank
    def full_stats(h,mask):
        h=np.asarray(h,dtype=np.float64)
        from scipy.ndimage import distance_transform_edt as _unused
        nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
        ones=np.ones_like(nw); ea=np.stack((6*ones,ne-nw,np.zeros_like(nw)),axis=-1)
        dg=np.stack((6*ones,se-nw,-6*ones),axis=-1);eb=np.stack((np.zeros_like(nw),sw-nw,-6*ones),axis=-1)
        a=np.cross(ea,dg);b=np.cross(dg,eb);a/=np.linalg.norm(a,axis=-1)[...,None];b/=np.linalg.norm(b,axis=-1)[...,None]
        vals=[]; masks=[]
        for name,x,y,m in [('diagonal',a,b,mask[:-1,:-1]&mask[:-1,1:]&mask[1:,:-1]&mask[1:,1:]),
            ('vertical',a[:,:-1],b[:,1:],mask[:-1,:-2]&mask[:-1,1:-1]&mask[1:,1:-1]&mask[1:,2:]),
            ('horizontal',b[:-1,:],a[1:,:],mask[:-2,:-1]&mask[1:-1,:-1]&mask[1:-1,1:]&mask[2:,1:])]:
            ang=np.degrees(np.arctan2(np.linalg.norm(np.cross(x,y),axis=-1),np.einsum('...i,...i->...',x,y)))
            vals.append(ang[m].astype(np.float64,copy=False))
            del ang
        q=np.concatenate(vals)
        return {'n':int(q.size),'p99':float(np.percentile(q,99)),'above30':int(np.count_nonzero(q>30.0))}
    st={}
    for name,mask in [('bank',bank),('interior',interior)]:
        base_stats=full_stats(B,mask);got=full_stats(candidate,mask);ref=report_ref['angles']['stats'][name]['candidate']
        if base_stats['n']!=ref['n'] or base_stats['above30']!=ref['above30'] or abs(base_stats['p99']-ref['p99'])>1e-6:
            raise RuntimeError(f'B full-map metric fixture mismatch {name}: {base_stats} vs report {ref}')
        st[name]={'candidate':got,'B_EV82':{k:ref[k] for k in ('n','p99','above30')},
          'pass':got['n']==ref['n'] and got['p99']<=ref['p99']+TOL_DEG and got['above30']<=ref['above30']}
        g[f'{name}_p99_and_count_exact_postsolve']=st[name]['pass']
    result.update({'status':'PASS_AUTHOR_PENDING_INDEPENDENT_CONSUMER' if all(g.values()) else 'FAIL_POSTSOLVE_GATES',
        'gates':g,'distributions':st,'changed_vertices':int(np.count_nonzero(candidate!=B)),
        'changed_vertices_coords':[[int(r),int(c)] for r,c in np.argwhere(candidate!=B)],
        'order_failures':order_bad,'axial_extrema_added':axial_added,'crossing_failures':crossing_bad,
        'postsolve_candidate_sha256':None})
    # Candidate artifact is created only when every post-quantization check passes.
    if all(g.values()):
        arrays=dict(bdata);arrays['heights']=candidate.astype(np.float32,copy=False)
        np.savez_compressed(OUT/'candidate-terrain.npz',**arrays)
        result['candidate_written']=True;result['postsolve_candidate_sha256']=sha(OUT/'candidate-terrain.npz')
    emit_profiles(B,load_npz(EV83)['heights'],candidate,result['status'])
    result['profiles']={'png':str(OUT/'profiles-full-36m-1to1.png'),'json':str(OUT/'profiles-full-36m-1to1.json')}
    write_json(OUT/'authoring-report.json',result)

if __name__=='__main__':
    main()
