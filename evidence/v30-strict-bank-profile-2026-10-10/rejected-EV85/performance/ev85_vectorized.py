"""Vectorized, local EV85 geometry evaluator; does not optimize or emit terrain."""
from pathlib import Path
import hashlib, importlib.util, json, math, time
import numpy as np

ROOT=Path(r'E:/DayZ-Baltic-Build')
PILOT=ROOT/'v30-coupled-shore-pilot-20261010'
AUTHOR=PILOT/'author_ev85.py'
B=ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
D4=ROOT/'v30-coupled-shore-feasibility-20261010/feasibility.json'
DIAG=PILOT/'diagnostic-vector.npz'
OUT=PILOT/'performance'
TOL=1e-10

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()
def load_npz(path):
    with np.load(path,allow_pickle=False) as d:return {k:d[k] for k in d.files}

def triangle_vertices(face):
    r,c,f=face
    if f=='A':return ((r,c),(r,c+1),(r+1,c+1)) # NW, NE, SE
    return ((r,c),(r+1,c),(r+1,c+1))           # NW, SW, SE

class PatchEvaluator:
    """Precomputed local face/hinge/slope/order indices; no 4M-height copy per x."""
    def __init__(self,base,vertices,descs,slopefaces,edges):
        self.base=base
        self.vertices=list(vertices);self.vi={v:i for i,v in enumerate(self.vertices)}
        self.descs=list(descs);self.slopefaces=list(slopefaces);self.edges=list(edges)
        self.faces=sorted(set(self.slopefaces).union(*(set(author.hinge_faces(d)) for d in self.descs)))
        self.fi={f:i for i,f in enumerate(self.faces)}
        self.face_var=np.full((len(self.faces),3),-1,dtype=np.int32)
        self.face_h0=np.empty((len(self.faces),3),dtype=np.float64)
        for i,f in enumerate(self.faces):
            for j,v in enumerate(triangle_vertices(f)):
                self.face_h0[i,j]=float(base[v])
                if v in self.vi:self.face_var[i,j]=self.vi[v]
        self.hinge_face_ids=np.asarray([[self.fi[f] for f in author.hinge_faces(d)] for d in self.descs],dtype=np.int32)
        self.slope_face_ids=np.asarray([self.fi[f] for f in self.slopefaces],dtype=np.int32)
        self.order_var=np.full((len(self.edges),2),-1,dtype=np.int32)
        self.order_gap=np.empty(len(self.edges),dtype=np.float64)
        for i,(u,v) in enumerate(self.edges):
            self.order_gap[i]=float(base[u])-float(base[v])
            if u in self.vi:self.order_var[i,0]=self.vi[u]
            if v in self.vi:self.order_var[i,1]=self.vi[v]
        self.order_equal=np.flatnonzero(self.order_gap==0.0)

    def evaluate(self,x):
        x=np.asarray(x,dtype=np.float64)
        if x.shape!=(len(self.vertices),):raise ValueError('x shape does not match patch')
        ix=np.maximum(self.face_var,0)
        hs=self.face_h0+np.where(self.face_var>=0,x[ix],0.0)
        # Exact NW-SE triangle formulas equivalent to cross products of native XYZ.
        # Normalize each normal before the hinge cross/dot, as author_ev85 does.
        raw=np.empty((len(self.faces),3),dtype=np.float64)
        for i,(_,_,f) in enumerate(self.faces):
            if f=='A':
                nw,ne,se=hs[i]
                raw[i]=(-6.0*(ne-nw),36.0,6.0*(se-ne))
            else:
                nw,sw,se=hs[i]
                raw[i]=(6.0*(sw-se),36.0,6.0*(sw-nw))
        normals=raw/np.linalg.norm(raw,axis=1)[:,None]
        a=normals[self.hinge_face_ids[:,0]];b=normals[self.hinge_face_ids[:,1]]
        angles=np.degrees(np.arctan2(np.linalg.norm(np.cross(a,b),axis=1),np.einsum('ij,ij->i',a,b)))
        sn=normals[self.slope_face_ids]
        slopes=np.degrees(np.arctan2(np.hypot(sn[:,0],sn[:,2]),np.abs(sn[:,1])))
        dv=np.where(self.order_var>=0,x[np.maximum(self.order_var,0)],0.0)
        gap=self.order_gap
        # Same signed remaining separation as EV85 order_ineq; equality rows separately.
        order=np.where(gap>0.0,gap+dv[:,0]-dv[:,1],-gap+dv[:,1]-dv[:,0])
        eq=dv[self.order_equal,0]-dv[self.order_equal,1]
        return {'angles':angles,'slopes':slopes,'order_ineq':order,'order_eq':eq}

# Imported only as the frozen scalar reference, not for optimization or writes.
spec=importlib.util.spec_from_file_location('author_ev85_frozen',AUTHOR)
author=importlib.util.module_from_spec(spec);spec.loader.exec_module(author)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    bd=load_npz(B);base=bd['heights'].astype(np.float64,copy=False)
    d4=json.loads(D4.read_text(encoding='utf-8'))
    diag=load_npz(DIAG);diag_delta=diag['delta']
    reports=[];bench=[]
    for pi,p in enumerate(d4['patches']):
        verts=[tuple(map(int,v)) for v in p['eligible_nodes']]
        focus=tuple(map(int,p['focus']))
        desc=sorted(set().union(*(author.vertex_hinges(v) for v in verts)))
        sf=author.slope_faces_for_vertices(set(verts));edges=author.order_edges(verts)
        ev=PatchEvaluator(base,verts,desc,sf,edges)
        bounds={tuple(q['vertex']):tuple(q['delta_bounds']) for q in d4['scalar_delta_bounds']}
        x0=np.zeros(len(verts),dtype=np.float64);x0[ev.vi[focus]]=-0.1
        if pi==1:x0[ev.vi[(focus[0]-1,focus[1])]]=-0.06495246887207032
        xdiag=np.asarray([float(diag_delta[v]) for v in verts],dtype=np.float64)
        rng=np.random.default_rng(8585+pi);random_x=[]
        for _ in range(20):
            x=np.zeros(len(verts),dtype=np.float64)
            for j,v in enumerate(verts):
                lo,hi=bounds[v]
                if hi-lo>1e-12:
                    # Strictly interior deterministic values, independent of feasibility constraints.
                    q=float(rng.uniform(.05,.95));x[j]=lo+q*(hi-lo)
                else:x[j]=(lo+hi)*.5
            random_x.append(x)
        cases=[('B_zero',np.zeros(len(verts),dtype=np.float64)),('x0',x0),('diagnostic',xdiag)]+[(f'interior_{i:02d}',x) for i,x in enumerate(random_x)]
        maxerr={'angles':0.0,'slopes':0.0,'order_ineq':0.0,'order_eq':0.0}; case_rows=[]
        # Reference comparison deliberately uses the frozen full-array scalar implementation.
        for name,x in cases:
            actual=ev.evaluate(x)
            h=author.apply_delta(base,verts,x)
            expected={'angles':author.eval_hinges(h,desc),'slopes':author.slope_values(h,sf)}
            oi=[]
            idx=ev.vi
            for u,v in edges:
                du=float(x[idx[u]]) if u in idx else 0.0;dv=float(x[idx[v]]) if v in idx else 0.0;gap=float(base[u])-float(base[v])
                oi.append(gap+du-dv if gap>0 else -gap+dv-du)
            expected['order_ineq']=np.asarray(oi,dtype=np.float64)
            expected['order_eq']=np.asarray([(float(x[idx[u]]) if u in idx else 0.0)-(float(x[idx[v]]) if v in idx else 0.0) for u,v in edges if float(base[u])==float(base[v])],dtype=np.float64)
            errs={k:float(np.max(np.abs(actual[k]-expected[k]),initial=0.0)) for k in actual}
            for k,v in errs.items():maxerr[k]=max(maxerr[k],v)
            case_rows.append({'case':name,'errors_max_abs':errs})
        if max(maxerr.values())>TOL:raise RuntimeError(f'patch {pi} scalar parity exceeded {TOL}: {maxerr}')
        # Benchmark 100 vectorized calls after precomputation; no optimizer invoked.
        eval_vectors=[cases[i%len(cases)][1] for i in range(100)]
        t0=time.perf_counter()
        for x in eval_vectors:ev.evaluate(x)
        elapsed=time.perf_counter()-t0
        bench.append({'patch':pi,'focus_rc':focus,'variables':len(verts),'dedup_hinges':len(desc),
            'focus_hinges':len(author.vertex_hinges(focus)),'slope_faces':len(sf),'order_edges':len(edges),
            'precompute_face_count':len(ev.faces),'calls':100,'elapsed_seconds':elapsed,
            'milliseconds_per_eval':elapsed*10,'full_4m_copy_per_eval':False})
        reports.append({'patch':pi,'focus_rc':focus,'case_count':len(cases),'max_abs_error':maxerr,'tolerance_deg_or_m':TOL,
            'cases':case_rows,'precomputed':{'faces':len(ev.faces),'dedup_hinges':len(desc),'focus_hinges':len(author.vertex_hinges(focus)),
                'slope_faces':len(sf),'order_edges':len(edges)}})
    result={'status':'PASS_VECTOR_EVALUATOR_FIXTURES','purpose':'implementation parity and performance only; no optimizer/candidate/physical acceptance',
        'inputs':{'frozen_author_sha256':sha(AUTHOR),'B_sha256':sha(B),'D4_sha256':sha(D4),'diagnostic_sha256':sha(DIAG)},
        'method':'local precomputed face->variable indices, vectorized float64 normals/cross/dot/atan2; order edges and base gaps precomputed; no 4M-height copy during evaluate(x)',
        'fixture_vectors':'B zero, EV85 x0, EV85 diagnostic, 20 deterministic box-interior vectors per patch',
        'patches':reports,'benchmarks':bench,
        'limits':['Random interior fixtures are code parity checks, not feasible solutions or physics checks.','No global queue solve, p99/count recomputation, consumer, ODOL, or DayZ validation was performed.']}
    (OUT/'vector-evaluator-report.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'benchmarks':bench,'max_errors':[q['max_abs_error'] for q in reports]},indent=2))
if __name__=='__main__':main()