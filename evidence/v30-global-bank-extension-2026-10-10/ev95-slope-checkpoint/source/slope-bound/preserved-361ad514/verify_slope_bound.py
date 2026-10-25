#!/usr/bin/env python3
"""Independent EV94 rebase consumer. It never calls the author or solver."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, os, sys
from pathlib import Path
import numpy as np
from scipy import sparse

ROOT=Path(r'E:/DayZ-Baltic-Build'); G=ROOT/'v30-global-bank-extension-20261010'
RS=G/'global-operator-prototype/real-sector-preflight'; HERE=RS/'ev94-rebase'; UNIT=HERE/'slope-bound'
PLAN=UNIT/'PLAN_SLOPE_BOUND.md'; PREP_DRIVER=UNIT/'prepare_slope_bound.py'; SOLVE_DRIVER=HERE/'solve_ev94.py'
PREFLIGHT=UNIT/'preflight-run-01/preflight.json'
ORIGINAL_PLAN=HERE/'PLAN_EV94_REBASE.md'; ORIGINAL_PREP_DRIVER=HERE/'prepare_ev94.py'
ORIGINAL_PREFLIGHT=HERE/'preflight-run-05/preflight.json'; ORIGINAL_PREPARED=HERE/'preflight-run-05/prepared.npz'
SLOPE_REVIEW=HERE/'consumer/full-run-02.json'
SLOPE_DIAGNOSTIC=HERE/'slope-diagnostic.json'
FOCUS_DIR=RS/'focus-unit'; FOCAL=FOCUS_DIR/'author-run-01/candidate-terrain.npz'
FOCAL_REVIEW=FOCUS_DIR/'composition-run-01/review.json'; FOCAL_SUPPLEMENT=FOCUS_DIR/'consumer-run-01/acceptance-supplement.json'
SELECTED_EV93=G/'compound-selection/run-02/candidate-terrain.npz'; SELECTION=G/'compound-selection/run-02/selection.json'
SELECTED_REPORT=G/'crest-extension/selected-consumer-runs/attempt-03/review.json'
FOCAL_CONSUMER=FOCUS_DIR/'verify_focal_composition.py'
OC=RS/'order-closure/verify_order_closure.py'; CONT=RS/'verify_real_sector_continuation.py'
EV87=ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
EV88=ROOT/'v30-wide-bank-fairing-pilot-20261010/review-independent/verify_ev88q.py'
EV91=ROOT/'v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py'
EV82=ROOT/'v30-mixed-bank-incremental-fixed-20261010/author.py'
CIVIL=RS/'civil_inventory.py'; D8=G/'constrained-pilot/d8_sparse_pilot.py'
INVENTORY=RS/'inventory-run-02.json'; DOMAIN_NPZ=INVENTORY/'domain-reasons.npz'
WATER_NPZ=RS/'water-run-01/water-support-mask.npz'; CIVIL_JSON=RS/'civil-run-01.json'
O_EV79=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/terrain.npz'
FOCUS=(840,370); N=2048; SEA=.85; EPS_WATER=1e-4; MAX_DELTA=2.
WINDOW=(712,968,242,498); CONTEXT=(710,970,240,500)
SLOPE_CELL=(899,445); SLOPE_TARGET=(900,446); SLOPE_FIXED=((899,445),(899,446))
PINS={
 PLAN:'5b1ff2818f44975b965958ee89e47a848f381ec94d2611de9def3435f6a43fcb',
 PREP_DRIVER:'b5fa83b96a561bc56edb8eb1b645e45924bd8743ec133a2b7ecfc3329a15b140',
 SOLVE_DRIVER:'ebb53986d69e4ec080356883db15091983fef3bb01715714177d2d504283abf0',
 ORIGINAL_PLAN:'4ba76f70173ac777d3f4b6ad427062d430aabb75a4bb25f70adf04c231b167fd',
 ORIGINAL_PREP_DRIVER:'4f436164fea35e8241ceb50f6090271ca89ac5c2184a693195d2b40334b64124',
 ORIGINAL_PREFLIGHT:'a6ae4b91cf5ebabbfc57352e4f988150eea2a7506b74a610b6aa4ce79a2bf4d7',
 ORIGINAL_PREPARED:'2df4ad67280c656025843f6528147a68c03dfcf6ecdfbe9cce2ee4818e15a2eb',
 SLOPE_REVIEW:'259c87fa01894eb3db409f6087e7cd3b787918e1e08629b4e53ad0fdd2e24030',
 SLOPE_DIAGNOSTIC:'4053a8361a0c4074643e4f9a29d9196ea0b47549d04574fa75c89d08bf16e272',
 FOCAL:'30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1',
 FOCAL_REVIEW:'a5a5aaa1f1f2c06c646bbd54a41ea8fd89d8dee8ffa14d2e59af4d7bc07b05e3',
 FOCAL_SUPPLEMENT:'fab5c76e2f1a7a5935cf70bfaa08dedd4500411e4c2ac11670dc7fccc4b89e7f',
 SELECTED_EV93:'6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d',
 SELECTION:'3b22dcc381b34b8d7c3e6641d3c919658f0fe7377594a859e3d5c064cf92ba0b',
 SELECTED_REPORT:'656e676e38817592ed96d13ddeb1693d2a9bead152770256b0b21e665cedf8ec',
 FOCAL_CONSUMER:'e5228392386606e495579f28b1cfa8ecd6d58aff1eb9f2967f4480e8440aecb2',
 OC:'064f67ef4fcf2f33264853d4301f33e79246e2be3297d9f01b0a64bacf9e4e5e',
 CONT:'5952de0210215275cf8ed67d644dd4a9bd0325b95c1dfda07751510ad9ad821f',
 EV82:'9b7c5374b7c78c3604bb2763ef8b7b4d16dc4bf18fc57091233ad435876cb74b'}
class Reject(RuntimeError): pass
def require(ok,msg):
    if not ok: raise Reject(msg)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def readj(path):
    v=json.loads(Path(path).read_text(encoding='utf-8-sig')); require(isinstance(v,dict),f'not JSON object: {path}'); return v
def load_npz(path):
    with np.load(path,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def load_module(name,path,expected=None):
    if expected:require(sha(path)==expected,f'helper SHA changed: {path}')
    s=importlib.util.spec_from_file_location(name,path);require(s and s.loader,f'cannot load {path}')
    m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def same(a,b,label):
    a=np.asarray(a);b=np.asarray(b)
    require(a.dtype==b.dtype and a.shape==b.shape and np.ascontiguousarray(a).tobytes()==np.ascontiguousarray(b).tobytes(),f'{label}: byte mismatch')
def rehash_map(items,label):
    require(isinstance(items,dict) and items,f'{label}: empty readset')
    out={}
    for raw,want in items.items():
        p=Path(raw).resolve();got=sha(p);require(got==want,f'{label} SHA drift: {p}');out[str(p)]=got
    return dict(sorted(out.items(),key=lambda x:os.path.normcase(x[0])))
def artifact_readset(preflight_path,prepared_path,result_path,state_path,candidate_path,label):
    # Dynamic run artifacts are exactly the five files captured by load_run.
    # The consumer source belongs to the separately checked static readset.
    paths=[Path(p).resolve() for p in (preflight_path,prepared_path,result_path,state_path,candidate_path)]
    require(len(set(paths))==5,f'{label}: duplicate dynamic artifact path')
    return rehash_map({str(p):sha(p) for p in paths},label)
def require_same_readset(start,end,label):
    require(isinstance(start,dict) and isinstance(end,dict),f'{label}: readsets must be mappings')
    require(set(start)==set(end),f'{label}: readset member set changed')
    require(start==end,f'{label}: readset content changed')
def inward_vector(values,side):
    x=np.asarray(values,np.float64);q=x.astype(np.float32)
    if side=='lower': q=np.where(q.astype(np.float64)<x,np.nextafter(q,np.float32(np.inf)),q)
    else:q=np.where(q.astype(np.float64)>x,np.nextafter(q,np.float32(-np.inf)),q)
    return q.astype(np.float32)

def triangle0_slope_deg(nw,ne,se):
    """Independent EV87 NW-NE-SE triangle slope from its two XZ gradients."""
    nw,ne,se=map(float,(nw,ne,se))
    require(all(math.isfinite(x) for x in (nw,ne,se)),'nonfinite slope triangle')
    gx=(ne-nw)/6.0
    gz=(ne-se)/6.0
    return math.degrees(math.atan(math.hypot(gx,gz)))

def scalar_slope_interval(nw,ne,se_base,se_hi):
    """Prove SE>=SE_base controls this face over the whole box interval."""
    vals=tuple(map(float,(nw,ne,se_base,se_hi)))
    require(all(math.isfinite(x) for x in vals),'nonfinite scalar slope interval')
    nw,ne,se_base,se_hi=vals
    require(se_base<=se_hi,'empty scalar slope interval')
    require(se_hi<=ne,'SE upper bound crosses fixed NE; monotonic proof is invalid')
    baseline=triangle0_slope_deg(nw,ne,se_base)
    upper=triangle0_slope_deg(nw,ne,se_hi)
    require(upper<=baseline+1e-12,'slope is not nonincreasing over the derived interval')
    return {'lower_m':se_base,'upper_m':se_hi,'baseline_slope_deg':baseline,
            'worst_allowed_slope_deg':baseline,'slope_at_upper_deg':upper,
            'proof':'NE-SE is nonnegative throughout [SE_base, SE_hi], so its squared gradient component is nonincreasing as SE rises.'}

def slope_bound_fixtures():
    nw,ne,se=7.2344970703125,3.1139774322509766,2.2943551540374756
    proof=scalar_slope_interval(nw,ne,se,2.7943551540374756)
    below=float(np.nextafter(np.float32(se),np.float32(-np.inf)))
    assert triangle0_slope_deg(nw,ne,2.2569596767425537)>proof['baseline_slope_deg']
    assert triangle0_slope_deg(nw,ne,se)<=proof['worst_allowed_slope_deg']
    assert below<se and triangle0_slope_deg(nw,ne,below)>proof['baseline_slope_deg']
    try:scalar_slope_interval(nw,ne,se,ne+1e-5)
    except Reject:pass
    else:raise AssertionError('interval crossing NE must reject')
    try:scalar_slope_interval(nw,ne,math.nan,2.7)
    except Reject:pass
    else:raise AssertionError('nonfinite interval must reject')
    return {'base_interval_monotonic':True,'below_baseline_rejected_by_scalar_contract':True,
            'raised_candidate_slope_failure_detected':True,'crossing_fixed_neighbor_rejected':True,
            'nonfinite_rejected':True,'baseline_slope_deg':proof['baseline_slope_deg'],
            'high_endpoint_slope_deg':proof['slope_at_upper_deg']}

def assert_only_scalar_lo_changed(original,prepared,index,baseline):
    require(set(original)==set(prepared),'prepared array key set changed')
    for key in sorted(original):
        old=np.asarray(original[key]);new=np.asarray(prepared[key])
        if key!='lo':
            same(new,old,f'prepared array changed outside lo: {key}')
            continue
        require(old.dtype==new.dtype and old.shape==new.shape and old.ndim==1 and 0<=index<len(old),'lo layout/index changed')
        expected=old.copy();expected[index]=baseline
        same(new,expected,'lo differs outside the single declared scalar bound')
        require(np.flatnonzero(new!=old).tolist()==[index],'lo changed a non-target entry or did not change target')
    return True

def scalar_slope_local_contract(base_local,fixed_mask,global_nodes,upper_height):
    nodes=np.asarray(global_nodes,np.int32)
    hits=np.flatnonzero(np.all(nodes==np.asarray(SLOPE_TARGET,np.int32),axis=1))
    require(len(hits)==1,'slope target missing or duplicated in mutable nodes')
    ctx=np.asarray((CONTEXT[0],CONTEXT[2]),np.int32)
    target=tuple((np.asarray(SLOPE_TARGET)-ctx).tolist())
    nw=tuple((np.asarray(SLOPE_FIXED[0])-ctx).tolist());ne=tuple((np.asarray(SLOPE_FIXED[1])-ctx).tolist())
    fm=np.asarray(fixed_mask,bool);base=np.asarray(base_local,np.float32)
    require(base.shape==fm.shape,'local fixed mask/base shape mismatch')
    require(not fm[target] and fm[nw] and fm[ne],'slope target/fixed-neighbor ownership differs')
    b=float(base[target]);hnw=float(base[nw]);hne=float(base[ne]);upper=float(upper_height)
    proof=scalar_slope_interval(hnw,hne,b,upper)
    return {'index':int(hits[0]),'target_local':target,'fixed_local':(nw,ne),'base_m':b,
            'nw_m':hnw,'ne_m':hne,'proof':proof}

def scalar_slope_consumer_fixtures():
    idx=1;orig={'lo':np.array([1.,0.,2.],np.float64),'hi':np.array([3.,4.,5.],np.float64),
               'base':np.arange(4,dtype=np.float32)}
    good={k:v.copy() for k,v in orig.items()};good['lo'][idx]=2.0
    assert_only_scalar_lo_changed(orig,good,idx,2.0)
    bad={k:v.copy() for k,v in good.items()};bad['hi'][0]+=1.
    try:assert_only_scalar_lo_changed(orig,bad,idx,2.0)
    except Reject:pass
    else:raise AssertionError('non-lo prepared array mutation must reject')
    bad={k:v.copy() for k,v in good.items()};bad['lo'][2]=3.0
    try:assert_only_scalar_lo_changed(orig,bad,idx,2.0)
    except Reject:pass
    else:raise AssertionError('second lower-bound mutation must reject')
    ctx=np.asarray((CONTEXT[0],CONTEXT[2]),np.int32)
    def local(rc):return tuple((np.asarray(rc)-ctx).tolist())
    b=np.zeros((260,260),np.float32);fixed=np.ones((260,260),bool)
    b[local(SLOPE_FIXED[0])]=np.float32(7.2344970703125);b[local(SLOPE_FIXED[1])]=np.float32(3.1139774322509766)
    b[local(SLOPE_TARGET)]=np.float32(2.2943551540374756)
    nodes=np.asarray([SLOPE_TARGET],np.int32);fixed[local(SLOPE_TARGET)]=False
    valid=scalar_slope_local_contract(b,fixed,nodes,2.7943551540374756)
    assert valid['index']==0 and valid['proof']['slope_at_upper_deg']<valid['proof']['baseline_slope_deg']
    badmask=fixed.copy();badmask[local(SLOPE_FIXED[1])]=False
    try:scalar_slope_local_contract(b,badmask,nodes,2.7943551540374756)
    except Reject:pass
    else:raise AssertionError('mobile fixed neighbor must reject')
    try:scalar_slope_local_contract(b,fixed,np.vstack([nodes,nodes]),2.7943551540374756)
    except Reject:pass
    else:raise AssertionError('duplicate target variable must reject')
    return {'one_lo_entry_only_pass':True,'other_array_mutation_rejected':True,'second_lo_entry_rejected':True,
            'real_target_fixed_neighbor_contract_pass':True,'mobile_fixed_neighbor_rejected':True,'duplicate_target_rejected':True}

def verify_prepared_scalar_delta(pre,prep,base_local,global_nodes):
    """Bind the one changed solver lower-bound entry to original EV94 arrays."""
    require(pre.get('schema')=='ev94.scalar-slope-preflight.v1','wrong scalar-slope preflight schema')
    require(pre.get('original_preflight')=={'path':str(ORIGINAL_PREFLIGHT),'sha256':PINS[ORIGINAL_PREFLIGHT]},
            'original preflight reference differs')
    require(pre.get('original_prepared')=={'path':str(ORIGINAL_PREPARED),'sha256':PINS[ORIGINAL_PREPARED]},
            'original prepared reference differs')
    require(sha(ORIGINAL_PREFLIGHT)==PINS[ORIGINAL_PREFLIGHT]
            and sha(ORIGINAL_PREPARED)==PINS[ORIGINAL_PREPARED],'original EV94 artifacts drifted')
    op=readj(ORIGINAL_PREFLIGHT)
    require(op.get('prepared_artifact',{}).get('path')==str(ORIGINAL_PREPARED)
            and op.get('prepared_artifact',{}).get('sha256')==PINS[ORIGINAL_PREPARED],
            'original preflight does not bind the pinned prepared array')
    orig=load_npz(ORIGINAL_PREPARED)
    hits=np.flatnonzero(np.all(np.asarray(global_nodes)==np.asarray(SLOPE_TARGET),axis=1))
    require(len(hits)==1,'slope target is not exactly one variable')
    idx=int(hits[0]); base=float(base_local[SLOPE_TARGET[0]-CONTEXT[0],SLOPE_TARGET[1]-CONTEXT[2]])
    require(float(orig['lo'][idx])<base,'scalar lower-bound change is not a strict tightening')
    assert_only_scalar_lo_changed(orig,prep,idx,base)
    proof=pre.get('slope_bound')
    require(isinstance(proof,dict),'missing slope_bound proof')
    expected={
      'variable_index':idx,'target_rc':list(SLOPE_TARGET),'face_cell_rc':list(SLOPE_CELL),
      'face_kind':'NW_NE_SE','fixed_neighbors_rc':[list(x) for x in SLOPE_FIXED],
      'previous_lower_m':float(orig['lo'][idx]),'new_lower_m':base,
      'prepared_arrays_changed':['lo'],'changed_entries':1,
      'lower_m':base,'baseline_SE_m':base,'upper_m':float(prep['hi'][idx]),
      'angular_tolerance_consumed':False}
    for key,value in expected.items():
        require(proof.get(key)==value,f'slope proof field differs: {key}')
    require(float(prep['lo'][idx])==base,'effective solver lower bound does not pin exact baseline minimum')
    return {'target_variable_index':idx,'baseline_height_m':base,'previous_solver_lo_m':float(orig['lo'][idx]),
            'new_solver_lo_m':float(prep['lo'][idx]),'only_prepared_array_changed':'lo','only_lo_entry_changed':idx}
def window_halo_mask(shape,windows,halo=2):
    out=np.zeros(shape,bool);h,w=shape
    for win in windows:
        r0,r1,c0,c1=map(int,win);require(r1-r0==17 and c1-c0==17,'not a 17x17 retained window')
        rr0=max(0,r0-halo);rr1=min(h,r1+halo);cc0=max(0,c0-halo);cc1=min(w,c1+halo)
        # NumPy negative slice endpoints wrap from the far edge. A window
        # wholly outside the sector must contribute no mask, not most of it.
        if rr0<rr1 and cc0<cc1:out[rr0:rr1,cc0:cc1]=True
    return out
def fixed_unchanged(base,candidate,mask):
    b=np.asarray(base);h=np.asarray(candidate);m=np.asarray(mask,bool)
    return b.shape==h.shape==m.shape and np.array_equal(b[m],h[m])

def pin_focus(mobile,focus_global,window_global):
    out=np.asarray(mobile,bool).copy();r0,r1,c0,c1=map(int,window_global);r,c=map(int,focus_global)
    require(out.shape==(r1-r0,c1-c0),'focus pin mask/window shape mismatch')
    if r0<=r<r1 and c0<=c<c1:out[r-r0,c-c0]=False
    return out

def corridor_policy(b,h,depth,p9):
    """Separate nominal polygon coverage and P-known depth from inherited P-NaN."""
    rb=b.get('corridors',[]);rh=h.get('corridors',[])
    coverage=len(rb)==19 and len(rh)==19 and all(float(x.get('coverage_error_m2',math.inf))<=1e-5 for x in rb+rh)
    ub=math.fsum(float(x.get('unknown_P_area_m2') or 0.) for x in rb)
    uh=math.fsum(float(x.get('unknown_P_area_m2') or 0.) for x in rh)
    changed=math.fsum(float(x.get('unknown_P_area_changed_between_pair_m2') or 0.) for x in rh)
    exact=math.fsum(float(x.get('unknown_P_area_exact_between_pair_m2') or 0.) for x in rh)
    return {'gates':{'nominal_geometry_coverage':bool(coverage),'affected_known_P_depth':bool(depth.get('pass')),
                     'unknown_P_unchanged':bool(p9.get('pass')) and changed<=1e-12},
            'open_status':'OPEN_INHERITED_P_UNKNOWN' if max(ub,uh)>0 else 'NO_P_UNKNOWN',
            'metrics':{'unknown_P_area_B_m2':ub,'unknown_P_area_H_m2':uh,'unknown_P_area_changed_m2':changed,
                       'unknown_P_area_exact_m2':exact,'legacy_all_covered_B':b.get('all_covered'),
                       'legacy_all_covered_H':h.get('all_covered')}}
def kkt(A,rhs,C,d,lo,hi,state,result):
    x=np.asarray(state['x64'],np.float64);yb=np.asarray(state['y_box'],np.float64);yd=np.asarray(state['y_d8'],np.float64)
    zb=np.asarray(state['z_box'],np.float64);zd=np.asarray(state['z_d8'],np.float64)
    require(x.shape==lo.shape==hi.shape and yb.shape==zb.shape==x.shape and yd.shape==zd.shape==(C.shape[0],),'KKT vector mismatch')
    diag=result.get('diagnostics') or {};rho=float(diag.get('rho',math.nan));require(math.isfinite(rho) and rho>0,'invalid rho')
    inf=lambda a:float(np.max(np.abs(a),initial=0.))
    bp=inf(x-zb);dp=inf(C@x-zd);bf=float(max(np.max(lo-x,initial=0.),np.max(x-hi,initial=0.)));df=float(np.max(d-C@x,initial=0.))
    grad=np.asarray(A.T@(A@x-rhs)).reshape(-1)+yb+np.asarray(C.T@yd).reshape(-1);si=inf(grad)
    ep=1e-10+1e-8*max(inf(x),inf(C@x),inf(zb),inf(zd));ed=1e-10+1e-8*inf(yb+np.asarray(C.T@yd).reshape(-1))
    eps=(math.isclose(float(diag.get('eps_primal',math.nan)),ep,rel_tol=1e-12,abs_tol=1e-18)
         and math.isclose(float(diag.get('eps_dual',math.nan)),ed,rel_tol=1e-12,abs_tol=1e-18))
    signs=int(np.count_nonzero(yd>1e-12));bn=inf(np.clip(zb+yb/rho,lo,hi)-zb);dn=inf(np.maximum(zd+yd/rho,d)-zd)
    ok=(diag.get('status')=='CONVERGED' and eps and bf<=ep and df<=ep and bp<=ep and dp<=ep and si<=ed and signs==0 and bn<=1e-10 and dn<=1e-10)
    return {'pass':bool(ok),'primal_box_inf':bp,'primal_d8_inf':dp,'box_feasibility':bf,'d8_feasibility':df,
      'stationarity_inf':si,'box_normal_cone_inf':bn,'d8_normal_cone_inf':dn,'positive_d8_duals':signs,
      'eps_primal':ep,'eps_dual':ed,'eps_match':eps,'rho':rho}

def bounds_rebuild(base,original,levels,prep):
    b=np.asarray(base,np.float32);o=np.asarray(original,np.float32);lv=np.asarray(levels,np.float64)
    require(b.shape==o.shape==lv.shape==(2048,2048),'bounds shape mismatch')
    require(np.isfinite(b).all() and np.isfinite(o).all() and np.isfinite(lv).all(),'nonfinite bound inputs')
    od=o.astype(np.float64);bd=b.astype(np.float64);floor=np.minimum(od,lv+EPS_WATER)
    lo_raw=np.maximum.reduce((bd-MAX_DELTA,floor,np.minimum(od,1.8),od-MAX_DELTA))
    hi_raw=np.minimum(bd+MAX_DELTA,od+MAX_DELTA)
    lo=inward_vector(lo_raw,'lower');hi=inward_vector(hi_raw,'upper');cap=inward_vector(bd+.5,'upper');hf=np.minimum(hi,cap)
    r0,r1,c0,c1=WINDOW;s=np.s_[r0:r1,c0:c1]
    for key,arr in [('bound_lo_local',lo),('bound_hi_ev79_ev82_local',hi),('bound_hi_ev82_cap_local',cap),('bound_hi_final_local',hf),('floors_local',floor)]:
        same(prep[key],arr[s],key)
    valid=lo[s]<=hf[s];same(prep['bounds_valid'].astype(bool),valid,'bounds_valid')
    return lo,hf,{'empty':int((~valid).sum()),'valid':int(valid.sum()),'floor_min':float(np.min(floor[s])),'upper_max':float(np.max(hf[s]))}

def retained_masks(selection,focal):
    ids=set(selection.get('retained_unit_ids',[]));rows=[x for x in selection.get('units',[]) if x.get('unit_id') in ids]
    require(len(ids)==len(rows)==499,'selection must have 499 retained rows')
    windows=[];origins={'legacy':0,'crest':0};qids=set()
    for row in rows:
        meta,_,_=focal.local_artifact(row,list(FOCUS));qid=int(meta['queue_id'])
        require(qid not in qids,f'duplicate retained qid {qid}');qids.add(qid);origins[meta['origin']]+=1;windows.append(meta['window'])
    require(origins=={'legacy':332,'crest':167},f'origin counts mismatch: {origins}')
    r0,r1,c0,c1=WINDOW;local=[(a-r0,b-r0,c-c0,d-c0) for a,b,c,d in windows]
    return window_halo_mask((256,256),local,2),window_halo_mask((256,256),local,0),{'count':499,'origins':origins,'windows':windows}



def corridor_fixtures():
    good={'all_covered':False,'corridors':[{'coverage_error_m2':0.,'unknown_P_area_m2':8.,
      'unknown_P_area_changed_between_pair_m2':0.,'unknown_P_area_exact_between_pair_m2':8.} for _ in range(19)]}
    report=corridor_policy(good,good,{'pass':True},{'pass':True})
    assert report['gates']['nominal_geometry_coverage'] and report['open_status']=='OPEN_INHERITED_P_UNKNOWN'
    bad=json.loads(json.dumps(good));bad['corridors'][0]['coverage_error_m2']=1.01e-5
    assert not corridor_policy(bad,good,{'pass':True},{'pass':True})['gates']['nominal_geometry_coverage']
    assert not corridor_policy(good,good,{'pass':False},{'pass':True})['gates']['affected_known_P_depth']
    changed=json.loads(json.dumps(good));changed['corridors'][3]['unknown_P_area_changed_between_pair_m2']=.001
    assert not corridor_policy(good,changed,{'pass':True},{'pass':True})['gates']['unknown_P_unchanged']
    return {'geometry_independent_of_all_covered':True,'coverage_hole_rejected':True,
            'known_depth_failure_rejected':True,'unknown_area_change_rejected':True}

def window_fixtures():
    mask=window_halo_mask((64,64),[(20,37,20,37)],2)
    b=np.zeros((64,64),np.float32);h=b.copy();h[18,18]=1
    assert not fixed_unchanged(b,h,mask)
    h[18,18]=0;h[50,50]=1
    assert fixed_unchanged(b,h,mask) and mask.sum()==441
    outside=window_halo_mask((64,64),[(-200,-183,-200,-183)],2)
    assert not outside.any()
    crossing=window_halo_mask((64,64),[(-5,12,10,27)],2)
    assert int(crossing.sum())==14*21
    return {'halo2_tamper_rejected':True,'outside_halo_not_fixed':True,'fixed_vertices':441,
            'far_outside_window_empty':True,'boundary_clip_exact':True}

def kkt_fixtures():
    A=sparse.eye(2,format='csr');rhs=np.zeros(2);C=sparse.csr_matrix([[1.,0.]]);d=np.array([-1.])
    x=np.zeros(2);yb=np.zeros(2);yd=np.zeros(1);zbox=x.copy();zd=C@x
    ep=1e-10;ed=1e-10
    state={'x64':x,'y_box':yb,'y_d8':yd,'z_box':zbox,'z_d8':zd}
    result={'diagnostics':{'rho':4.,'status':'CONVERGED','eps_primal':ep,'eps_dual':ed}}
    assert kkt(A,rhs,C,d,np.full(2,-1.),np.full(2,1.),state,result)['pass']
    bad=dict(state);bad['y_d8']=np.array([1.])
    assert not kkt(A,rhs,C,d,np.full(2,-1.),np.full(2,1.),bad,result)['pass']
    return {'rho4_zero_dual_pass':True,'positive_d8_dual_rejected':True}

def focus_fixtures():
    mobile=np.ones((4,4),bool);result=pin_focus(mobile,(11,21),(10,14,20,24))
    assert result.sum()==15 and not result[1,1] and mobile.all()
    outside=pin_focus(mobile,(99,99),(10,14,20,24));assert outside.all()
    return {'in_domain_focus_explicitly_pinned':True,'outside_focus_mask_unchanged':True}

def self_test():
    return {'status':'PASS','corridor':corridor_fixtures(),'window_halo':window_fixtures(),
            'kkt':kkt_fixtures(),'focus':focus_fixtures(),'slope_bound':slope_bound_fixtures(),
            'slope_prepared_delta':scalar_slope_consumer_fixtures()}

def smoke_read_contract(preflight_path,solve_dir):
    loaded=load_run(preflight_path,solve_dir)
    helper,mods,pre,prep=loaded[:4]
    system=reconstruct_system(helper,mods,pre,prep,loaded[-1])
    source_end=rehash_map(loaded[4],'smoke preflight source end')
    static_end=rehash_map(loaded[5],'smoke consumer static end')
    solve_end=rehash_map(loaded[6],'smoke solver source end')
    dynamic_end=rehash_map(loaded[7],'smoke artifact end')
    require(source_end==loaded[4] and static_end==loaded[5] and solve_end==loaded[6] and dynamic_end==loaded[7],
            'read-contract smoke detected source/artifact drift')
    return {'status':'SMOKE_READ_CONTRACT_PASS','scope':'load_run + reconstruct_system only; no candidate gates or global geometry',
      'consumer_sha256':sha(__file__),'preflight_sha256':sha(preflight_path),'prepared_sha256':sha(pre['prepared_artifact']['path']),
      'solve_result_sha256':sha(loaded[13]),'solver_state_sha256':sha(loaded[11]),'candidate_sha256':sha(loaded[12]),
      'matrix':{'variables':len(system['nodes']),'A_shape':list(system['A'].shape),'A_nnz':int(system['A'].nnz),
        'C_shape':list(system['C'].shape),'C_nnz':int(system['C'].nnz),'witnesses':len(system['witnesses'])},
      'fixed_domain':{'retained_windows':system['winfo']['count'],'retained_origins':system['winfo']['origins'],
        'retained_window_plus_halo2_vertices':int(system['halo'].sum()),'focus':list(FOCUS),
        'focus_explicitly_excluded':not bool(system['domain']['final_local'][FOCUS[0]-WINDOW[0],FOCUS[1]-WINDOW[2]])},
      'selected_seed':system['selected_seed'],'base_dtype':str(system['bundle']['B']['heights'].dtype),
      'readsets':{'preflight':len(loaded[4]),'consumer_static':len(loaded[5]),'solver':len(loaded[6])},
      'source_hashes_start_end_equal':True,'artifact_hashes_start_end_equal':True}

def smoke_preflight(preflight_path):
    """Load and independently reconstruct the new prepared problem, without solve artifacts."""
    helper=load_module('ev94_primitives_smoke',OC,PINS[OC]);mods=load_modules(helper)
    pre=readj(preflight_path)
    require(pre.get('status')=='PREFLIGHT_READY_ONLY','preflight is not READY')
    require(pre.get('schema')=='ev94.scalar-slope-preflight.v1','wrong slope preflight schema')
    require(pre.get('plan_sha256')==PINS[PLAN] and Path(pre.get('plan_path','')).resolve()==PLAN.resolve(),'wrong plan identity')
    require(Path(pre.get('driver_path','')).resolve()==PREP_DRIVER.resolve(),'wrong preflight driver path')
    require(pre.get('driver_sha256_start_end')==[PINS[PREP_DRIVER],PINS[PREP_DRIVER]],'preflight driver is not pinned')
    prep_path=Path(pre['prepared_artifact']['path']).resolve()
    require(prep_path.parent==Path(preflight_path).resolve().parent and sha(prep_path)==pre['prepared_artifact']['sha256'],'prepared path/SHA invalid')
    prep=load_npz(prep_path);rstart=pre.get('source_hashes_start')
    require(rstart and rstart==pre.get('source_hashes_end'),'preflight source readset drift')
    readset_start=rehash_map(rstart,'preflight source')
    static_expected={str(Path(path).resolve()):want for path,want in PINS.items()}
    static_expected[str(Path(__file__).resolve())]=sha(__file__)
    static_start=rehash_map(static_expected,'consumer static source')
    selection=readj(SELECTION)
    require(selection.get('status')=='SELECTED' and selection.get('schema')=='ev93.compound-selection.v1','selection is not accepted')
    system=reconstruct_system(helper,mods,pre,prep,selection)
    readset_end=rehash_map(rstart,'preflight source end');static_end=rehash_map(static_expected,'consumer static end')
    require(readset_end==readset_start and static_end==static_start,'readset drift during preflight reconstruction')
    return {'status':'SMOKE_PREFLIGHT_RECONSTRUCTION_PASS','scope':'prepared load + independent reconstruction only; no solve/candidate/full geometry',
      'consumer_sha256':sha(__file__),'preflight_sha256':sha(preflight_path),'prepared_sha256':sha(prep_path),
      'variables':len(system['nodes']),'A_shape':list(system['A'].shape),'A_nnz':int(system['A'].nnz),
      'C_shape':list(system['C'].shape),'C_nnz':int(system['C'].nnz),'witnesses':len(system['witnesses']),
      'selected_seed':system['selected_seed'],'mutable_nodes':len(system['nodes']),
      'target':{'rc':list(SLOPE_TARGET),'index':system['slope_target_index'],'base_m':float(prep['base_local'][system['slope_target_local']]),
        'physical_lower_m':float(system['lofull'][SLOPE_TARGET]),'solver_lower_m':float(system['lo'][system['slope_target_index']]),
        'solver_upper_m':float(system['hi'][system['slope_target_index']]),'fixed_neighbors_rc':[list(x) for x in SLOPE_FIXED],
        'interval_proof':system['scalar_slope_interval']},
      'prepared_delta':system['scalar_slope_delta'],'readset_counts':{'preflight':len(readset_start),'consumer_static':len(static_start)},
      'readsets_unchanged':True}

def evaluate(preflight_path,solve_dir):
    helper,mods,pre,prep,readset_start,static_start,solve_readset,dynamic_start,result,state,cand,state_path,candidate_path,result_path,selection=load_run(preflight_path,solve_dir)
    system=reconstruct_system(helper,mods,pre,prep,selection)
    A,rhs,C,d=system['A'],system['rhs'],system['C'],system['d'];nodes=system['nodes'];base_local=np.asarray(prep['base_local'],np.float32)
    require(result.get('fresh_start') is True and result.get('continuation') is False,'solve was not one fresh run')
    require(result.get('algorithm_override',{}).get('MAX_ITER')=={'original':10000,'effective':20000},'unexpected solver budget override')
    require(float(result.get('numeric_elapsed_s',math.inf))<=600.,'numeric time budget exceeded')
    memory=result.get('memory_before') or {};after=result.get('memory_after_numeric') or {}
    require(int(memory.get('available_physical_bytes',0))>=3*1024**3,'less than 3 GiB free before solver')
    require(int(after.get('peak_working_set_bytes',2**63-1))<=1536*1024**2,'solver peak exceeds 1.5 GiB')
    k=kkt(A,rhs,C,d,system['lo'],system['hi'],state,result);require(k['pass'],'independent KKT failed')
    same(state['nodes_local'],nodes,'solver node order')
    x=np.asarray(state['x64'],np.float64);raw=base_local.copy();raw[tuple(nodes.T)]=x.astype(np.float32)
    same(state['raw_float32'],raw,'raw cast')
    candidate_local=np.asarray(cand['candidate'],np.float32)
    same(cand['base'],base_local,'candidate source base');same(cand['nodes_local'],nodes,'candidate node order')
    lower=base_local.copy();upper=base_local.copy();lower[tuple(nodes.T)]=system['lo'].astype(np.float32);upper[tuple(nodes.T)]=system['hi'].astype(np.float32)
    edges=helper.order_edges_from_witnesses(system['witnesses'],base_local.shape)
    closure=helper.project_order_closure(raw,lower,upper,edges)
    same(candidate_local,closure['heights'],'independent order projection')
    require(np.array_equal(candidate_local[prep['fixed_mask'].astype(bool)],base_local[prep['fixed_mask'].astype(bool)]),'fixed local context changed')
    require(np.all(candidate_local[tuple(nodes.T)]>=system['lo']) and np.all(candidate_local[tuple(nodes.T)]<=system['hi']),'candidate escaped inward physical bounds')
    slope_idx=system['slope_target_index'];slope_rc=system['slope_target_local']
    slope_base=float(base_local[slope_rc]);slope_candidate=float(candidate_local[slope_rc])
    slope_nw=float(base_local[system['slope_fixed_local'][0]]);slope_ne=float(base_local[system['slope_fixed_local'][1]])
    slope_before=triangle0_slope_deg(slope_nw,slope_ne,slope_base)
    slope_after=triangle0_slope_deg(slope_nw,slope_ne,slope_candidate)
    slope_gate=(slope_candidate>=slope_base and slope_candidate<=float(system['hi'][slope_idx])
                and slope_after<=slope_before+1e-12)
    require(mods['ev91'].check_d8_candidate(candidate_local,system['witnesses']).get('pass') is True,'post-cast D8 failed')
    cost=helper.closure_cost_report(A,rhs,prep['x0'],raw[tuple(nodes.T)],candidate_local[tuple(nodes.T)])
    require(cost['pass'],'objective reduction/closure allowance failed')
    bfull=np.asarray(mods['ev88'].checked_sources()['B']['heights'],np.float32)
    # Re-anchor the in-memory baseline to accepted focal composition, not the old EV82 B.
    focal=load_npz(FOCAL);ev93=load_npz(SELECTED_EV93)
    for key in focal:
        if key=='heights':
            want=np.asarray(ev93[key]).copy();want[FOCUS]=np.float32(3.278029680252075);same(focal[key],want,'focal height provenance')
        else:same(focal[key],ev93[key],f'focal metadata {key}')
    bfull=focal['heights'];hfull=bfull.copy()
    hfull[CONTEXT[0]:CONTEXT[1],CONTEXT[2]:CONTEXT[3]]=candidate_local
    changed=np.argwhere(hfull!=bfull).astype(np.int32);changed_set={tuple(map(int,x)) for x in changed.tolist()}
    changed_expected=system['global_nodes'][candidate_local[tuple(nodes.T)]!=prep['x0']]
    same(changed,changed_expected,'changed full-grid node set')
    require(FOCUS not in changed_set and hfull[FOCUS]==np.float32(3.278029680252075),'explicit focus pin changed')
    fixed_full=np.zeros((N,N),bool);fixed_full[WINDOW[0]:WINDOW[1],WINDOW[2]:WINDOW[3]]=system['halo']
    require(fixed_unchanged(bfull,hfull,fixed_full),'retained 499 windows/halo2 changed')
    domain=system['domain'];water=system['water'];water_cells={(WINDOW[0]-1+int(r),WINDOW[2]-1+int(c)) for r,c in np.argwhere(water['cell_reasons']!=0)}
    protected_cells=water_cells|system['civil_cells']|domain['p9_cells'];protected_nodes=domain['civil_nodes']|domain['p9_nodes']
    protected_changed=changed_set & protected_nodes
    for r,c in changed_set:
        for rr in (r-1,r):
            for cc in (c-1,c):
                if (rr,cc) in protected_cells:protected_changed.add((r,c))
    cell_exact=all(all(bfull[r+dr,c+dc].tobytes()==hfull[r+dr,c+dc].tobytes() for dr,dc in ((0,0),(0,1),(1,0),(1,1))) for r,c in water_cells)
    require(not protected_changed and cell_exact,'water/civil/P9 protected support changed')
    ev87,ev88,ev91=mods['ev87'],mods['ev88'],mods['ev91'];bundle=mods['ev88'].checked_sources()
    bundle['B']=dict(bundle['B']);bundle['B']['heights']=bfull;ev88.bundle=bundle
    changed_cells=set(ev87._ev87_cells(changed.tolist()))
    topology=ev88.topology_check(ev87,bfull.astype(np.float64),hfull.astype(np.float64),bundle['P'],bundle['F'],changed_cells)
    geom=ev88.local_sector_stats(ev87,bfull.astype(np.float64),hfull.astype(np.float64),changed.tolist())
    p99=ev88.p99_population_gate(ev87,geom['angles_b'],geom['angles_h'],bundle)
    wet_diag=ev91.eligible_wet_support_diagnostic(ev88,ev87,bundle,geom['angles_b'],geom['angles_h'])
    corridor_b=ev88.corridor_depth_report(bfull,bundle['P'],bundle['corridors'],comparison=hfull)
    corridor_h=ev88.corridor_depth_report(hfull,bundle['P'],bundle['corridors'],comparison=bfull)
    depth=ev91.affected_corridor_depth_report(ev88,ev87,bundle,hfull,changed.tolist())
    p9=ev91.p9_unknown_preserved(not bool(changed_set & domain['p9_nodes']),corridor_h)
    corridor=corridor_policy(corridor_b,corridor_h,depth,p9)
    bed=ev88.high_bed_floor_report(hfull,bundle['B'])
    minima=mods['cont'].local_new_minima(bfull,hfull,changed.tolist())
    seed=mods['cont'].seed_improved(bfull,hfull,system['selected_seed'],ev87)
    gates={
      'fresh_pending_solve_and_resources':result.get('status')=='LOCAL_CANDIDATE_PENDING_INDEPENDENT_CONSUMER' and int(after.get('peak_working_set_bytes',2**63-1))<=1536*1024**2 and float(result.get('numeric_elapsed_s',math.inf))<=600.,
      'independent_domain_matrices_bounds_rebuilt':True,
      'independent_kkt_closure_objective':bool(k['pass'] and cost['pass']),
      'float32_bounds_and_D8':bool(np.all(candidate_local[tuple(nodes.T)]>=system['lo']) and np.all(candidate_local[tuple(nodes.T)]<=system['hi']) and ev91.check_d8_candidate(candidate_local,system['witnesses']).get('pass')),
      'scalar_slope_face_bounded_from_baseline':bool(slope_gate),
      'retained_499_windows_halo2_and_focus_exact':bool(fixed_unchanged(bfull,hfull,fixed_full) and FOCUS not in changed_set and hfull[FOCUS]==np.float32(3.278029680252075)),
      'water_civil_P9_exact':bool(not protected_changed and cell_exact and p9['pass']),
      'P_F_SEA_signs_crossings_within_1m':bool(topology['signs_preserved'] and topology['crossings_valid_and_within_1m']),
      'no_new_local_minima':bool(minima['no_new_minima']),
      'slope_hinge_global_nonregression':bool(geom['slopes_le_max35_or_B'] and geom['no_new_hinges_over_30_touched'] and geom['affected_sector_max_nonworse']),
      'bank_interior_p99_nonworse':bool(p99.get('pass')),
      'corridor_geometry_covered':bool(corridor['gates']['nominal_geometry_coverage']),
      'known_P_depth_ge_0_95':bool(corridor['gates']['affected_known_P_depth']),
      'unknown_P_preserved':bool(corridor['gates']['unknown_P_unchanged']),
      'high_navigable_bed_floor_1m':bool(bed['high_bed_floor_1m_pass']),
      'seed_improved':bool(seed['pass'])}
    # P-unknown remains openly unresolved even when its footprint is exactly preserved.
    status=('PASS_EV94_REBASE_SECTOR_OFFLINE_OPEN_P_UNKNOWN' if all(gates.values()) and corridor['open_status']=='OPEN_INHERITED_P_UNKNOWN'
            else 'PASS_EV94_REBASE_SECTOR_OFFLINE' if all(gates.values()) else 'FAIL_EV94_REBASE_SECTOR_OFFLINE')
    source_end=rehash_map(readset_start,'preflight source end')
    static_end=rehash_map(static_start,'consumer static source end')
    solve_end=rehash_map(solve_readset,'solve source end')
    artifact_end=artifact_readset(preflight_path,pre['prepared_artifact']['path'],result_path,state_path,candidate_path,'evaluated artifact end')
    require(source_end==readset_start,'source readset changed during evaluation')
    require(static_end==static_start,'consumer static source changed during evaluation')
    require(solve_end==solve_readset,'solve source changed during evaluation')
    require_same_readset(dynamic_start,artifact_end,'preflight/solve artifacts during evaluation')
    require(result.get('source_hashes_start')==result.get('source_hashes_end'),'solver readset changed')
    info={'base_sha256':PINS[FOCAL],'candidate_sha256':sha(candidate_path),'preflight_sha256':sha(preflight_path),
      'prepared_sha256':sha(pre['prepared_artifact']['path']),'variables':len(nodes),'changed_vertices':len(changed),
      'windows':{k:v for k,v in system['winfo'].items() if k!='windows'},'selected_seed':system['selected_seed'],
      'focus_rc':list(FOCUS),'focus_height_m':float(hfull[FOCUS]),'bounds':system['bounds_info'],
      'matrix_counts':{'A_shape':list(A.shape),'A_nnz':int(A.nnz),'C_shape':list(C.shape),'C_nnz':int(C.nnz),'stencils':len(system['stencils']),'witnesses':len(system['witnesses'])},
      'kkt':k,'closure':{k:v for k,v in closure.items() if not isinstance(v,np.ndarray)},'objective':cost,
      'scalar_slope_bound':{'target_rc':list(SLOPE_TARGET),'face_cell_rc':list(SLOPE_CELL),'kind':'NW_NE_SE',
        'fixed_neighbors_rc':[list(x) for x in SLOPE_FIXED],'base_target_m':slope_base,'candidate_target_m':slope_candidate,
        'slope_before_deg':slope_before,'slope_after_deg':slope_after,'interval_proof':system['scalar_slope_interval'],
        'prepared_delta':system['scalar_slope_delta']},
      'topology':{k:v for k,v in topology.items() if not isinstance(v,list)},
      'geometry':{k:v for k,v in geom.items() if k not in ('angles_b','angles_h','new_over30_examples_touched')},
      'p99_bank_interior':p99,'wet_support_diagnostic_not_gate':wet_diag,
      'corridor':{'B':corridor_b,'H':corridor_h,'policy':corridor},'high_bed':bed,'local_minima':minima,'seed':seed,
      'fixed_support':{'retained_windows':499,'water_cells':len(water_cells),'civil_cells':len(system['civil_cells']),
                       'p9_cells':len(domain['p9_cells']),'changed_protected_nodes':len(protected_changed),'water_corners_exact':cell_exact},
      'limitations':['Inherited P-unknown corridor area remains open; preservation is checked, no depth is inferred there.',
                     'Offline sector only: no native runtime/readback, graphical acceptance, or map-wide acceptance.'],
      'source_hashes_start':readset_start,'source_hashes_end':source_end,
      'consumer_static_hashes_start':static_start,'consumer_static_hashes_end':static_end,
      'solve_hashes_start':solve_readset,'solve_hashes_end':solve_end,
      'artifact_hashes_start':dynamic_start,'artifact_hashes_end':artifact_end}
    return {'status':status,'gates':gates,'information':info}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--self-test',action='store_true');ap.add_argument('--smoke-read-contract',action='store_true');ap.add_argument('--smoke-preflight',action='store_true')
    ap.add_argument('--preflight',type=Path,default=PREFLIGHT);ap.add_argument('--solve-dir',type=Path);ap.add_argument('--output',type=Path)
    a=ap.parse_args()
    if a.self_test:
        out=self_test()
        print(json.dumps(out,sort_keys=True));return 0
    if a.smoke_preflight:
        if a.output is None:ap.error('--output is required for --smoke-preflight')
        if a.output.exists():raise FileExistsError(a.output)
        report=smoke_preflight(a.preflight.resolve())
        a.output.parent.mkdir(parents=True,exist_ok=True);tmp=a.output.with_suffix(a.output.suffix+'.tmp')
        tmp.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(a.output)
        print(json.dumps({'status':report['status'],'report':str(a.output),'variables':report['variables'],'target':report['target']},sort_keys=True),flush=True);return 0
    if a.smoke_read_contract:
        if a.solve_dir is None or a.output is None:ap.error('--solve-dir and --output are required for --smoke-read-contract')
        if a.output.exists():raise FileExistsError(a.output)
        report=smoke_read_contract(a.preflight.resolve(),a.solve_dir.resolve())
        a.output.parent.mkdir(parents=True,exist_ok=True);tmp=a.output.with_suffix(a.output.suffix+'.tmp')
        tmp.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(a.output)
        print(json.dumps({'status':report['status'],'report':str(a.output),'matrix':report['matrix']},sort_keys=True),flush=True);return 0
    if a.solve_dir is None or a.output is None:ap.error('--solve-dir and --output are required')
    if a.output.exists():raise FileExistsError(a.output)
    report={'schema':'ev94.scalar-slope.independent-consumer.v1','status':'ERROR_CONSUMER','gates':{},'information':{}}
    code=2
    try:
        report.update(evaluate(a.preflight.resolve(),a.solve_dir.resolve()))
        code=0 if report['status'].startswith('PASS_EV94') else 1
    except Exception as exc:report['error']=repr(exc);code=2
    report['consumer_path']=str(Path(__file__).resolve());report['consumer_sha256']=sha(__file__)
    a.output.parent.mkdir(parents=True,exist_ok=True);tmp=a.output.with_suffix(a.output.suffix+'.tmp')
    tmp.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(a.output)
    print(json.dumps({'status':report['status'],'failed':[k for k,v in report.get('gates',{}).items() if v is not True],'report':str(a.output)},sort_keys=True),flush=True)
    return code
def load_modules(helper):
    ev87=helper.load_module('ev94_ev87',helper.EV87_PATH,helper.PINS[helper.EV87_PATH])
    ev88=helper.load_module('ev94_ev88',helper.EV88_PATH,helper.PINS[helper.EV88_PATH]);ev88.ev=ev87
    ev91=helper.load_module('ev94_ev91',helper.EV91_PATH,helper.PINS[helper.EV91_PATH]);ev91.ev=ev87
    civil=helper.load_module('ev94_civil',helper.CIVIL_PATH,helper.PINS[helper.CIVIL_PATH])
    focal=load_module('ev94_focal_comp',FOCAL_CONSUMER,PINS[FOCAL_CONSUMER])
    cont=load_module('ev94_continuation',CONT,PINS[CONT])
    return {'ev87':ev87,'ev88':ev88,'ev91':ev91,'civil':civil,'focal':focal,'cont':cont}

def load_run(preflight_path,solve_dir):
    helper=load_module('ev94_primitives',OC,PINS[OC])
    mods=load_modules(helper);pre=readj(preflight_path)
    require(pre.get('status')=='PREFLIGHT_READY_ONLY','preflight is not READY')
    require(pre.get('plan_sha256')==PINS[PLAN] and Path(pre.get('plan_path','')).resolve()==PLAN.resolve(),'wrong plan identity')
    require(Path(pre.get('driver_path','')).resolve()==PREP_DRIVER.resolve(),'wrong preflight driver path')
    require(pre.get('driver_sha256_start_end')==[PINS[PREP_DRIVER],PINS[PREP_DRIVER]],'preflight driver is not pinned')
    prep_path=Path(pre['prepared_artifact']['path']).resolve()
    require(prep_path.parent==Path(preflight_path).resolve().parent and sha(prep_path)==pre['prepared_artifact']['sha256'],'prepared path/SHA invalid')
    prep=load_npz(prep_path)
    rstart=pre.get('source_hashes_start');require(rstart and rstart==pre.get('source_hashes_end'),'preflight readset drift')
    readset_start=rehash_map(rstart,'preflight source')
    # The preflight readset is its own declared input set. Its driver identity
    # is bound by driver_path + driver_sha256_start_end above; consumer helpers
    # have a separate pinned readset and are not required to be preflight inputs.
    selection=readj(SELECTION)
    require(selection.get('status')=='SELECTED' and selection.get('schema')=='ev93.compound-selection.v1','selection is not accepted')
    # The accepted focal report is an offline local composition gate, not global acceptance.
    fr=readj(FOCAL_REVIEW);fs=readj(FOCAL_SUPPLEMENT);selected=readj(SELECTED_REPORT)
    require(fr.get('status')=='PASS_FOCAL_COMPOSITION_INCREMENTAL' and fr.get('global_contract_status')=='OPEN_INHERITED_MAP_DEFECTS','focal review status changed')
    require(fs.get('status')=='PASS_FOCAL_DELTA_OFFLINE_COMPLETE_GATESET','focal supplement status changed')
    require(selected.get('status')=='PASS_INCREMENTAL_NONREGRESSION','EV93 selected base report no longer passes')
    require(selection.get('candidate',{}).get('sha256')==sha(SELECTED_EV93)==PINS[SELECTED_EV93],'selected EV93 base identity mismatch')
    require(fr.get('candidate_sha256')==PINS[FOCAL] and fr.get('base_candidate_sha256')==PINS[SELECTED_EV93],'focal report does not bind exact base')
    # Exact solve output identity; no continuation and no inherited PASS.
    solve_dir=Path(solve_dir).resolve();rp=solve_dir/'solve-result.json'
    result=readj(rp);require(result.get('status')=='LOCAL_CANDIDATE_PENDING_INDEPENDENT_CONSUMER','solve result is not pending independent consumer')
    require(Path(result.get('preflight_path','')).resolve()==Path(preflight_path).resolve() and result.get('preflight_sha256')==sha(preflight_path),'solve/preflight link mismatch')
    require(result.get('source_hashes_start')==result.get('source_hashes_end'),'solve source hashes differ')
    solve_readset=rehash_map(result['source_hashes_end'],'solve source')
    require(solve_readset==rehash_map(result['source_hashes_start'],'solve source start'),'solve readset start/end mismatch')
    require(solve_readset.get(str(prep_path))==sha(prep_path),'prepared artifact not bound by solve readset')
    require(solve_readset.get(str(Path(preflight_path).resolve()))==sha(preflight_path),'preflight not bound by solve readset')
    # Pin the consumer's complete static source set independently of the
    # author's preflight/solver readset.
    static_expected={str(Path(path).resolve()):want for path,want in PINS.items()}
    static_expected[str(Path(__file__).resolve())]=sha(__file__)
    static_start=rehash_map(static_expected,'consumer static source')
    sp=Path(result['solver_state_path']).resolve();cp=Path(result['candidate_path']).resolve()
    require(sp.parent==solve_dir and cp.parent==solve_dir,'solver outputs escape run directory')
    require(sha(sp)==result.get('solver_state_sha256') and sha(cp)==result.get('candidate_sha256'),'solver artifacts SHA mismatch')
    state=load_npz(sp);candidate=load_npz(cp)
    dynamic_start=artifact_readset(preflight_path,prep_path,rp,sp,cp,'run artifact')
    return helper,mods,pre,prep,readset_start,static_start,solve_readset,dynamic_start,result,state,candidate,sp,cp,rp,selection

def reconstruct_system(helper,mods,pre,prep,selection):
    ev87,ev91,civil=mods['ev87'],mods['ev91'],mods['civil']
    bundle=mods['ev88'].checked_sources()
    focal=load_npz(FOCAL);ev93=load_npz(SELECTED_EV93)
    require(set(focal)==set(ev93),'focal/EV93 NPZ fields differ')
    for key in focal:
        if key=='heights':
            want=np.asarray(ev93[key]).copy();want[FOCUS]=np.float32(3.278029680252075);same(focal[key],want,'focal single-node delta')
        else:same(focal[key],ev93[key],f'focal field {key}')
    bundle['B']=dict(bundle['B']);bundle['B']['heights']=np.asarray(focal['heights'],np.float32);mods['ev88'].bundle=bundle
    water=load_npz(WATER_NPZ);civil_report=readj(CIVIL_JSON);inv=load_npz(DOMAIN_NPZ)
    domain=helper.reconstruct_static_domain(ev87,bundle,water,civil_report,inv)
    roads,_=civil.road_sample_cells();bridges,bridge_metrics=civil.bridge_face_cells();civil_cells=roads|bridges
    declared={tuple(map(int,xy)) for layer in ('road','bridge') for xy in civil_report[layer]['native_cells_rc_sorted']}
    require(civil_cells==declared,'independently rebuilt road/bridge cells differ from civil inventory')
    halo,rect,winfo=retained_masks(selection,mods['focal'])
    mobile=domain['final_local'].copy() & ~halo
    mobile=pin_focus(mobile,FOCUS,WINDOW)
    expected=np.argwhere(mobile).astype(np.int32)+np.asarray((WINDOW[0],WINDOW[2]),np.int32)
    nodes=np.asarray(prep['nodes_local'],np.int32);global_nodes=nodes+np.asarray((CONTEXT[0],CONTEXT[2]),np.int32)
    require(np.array_equal(global_nodes,expected),'mutable domain/order differs from static+499-window reconstruction')
    require(len(nodes)==int(pre['system']['variables']),'variable count differs from preflight summary')
    base_local=np.asarray(prep['base_local'],np.float32)
    same(base_local,bundle['B']['heights'][CONTEXT[0]:CONTEXT[1],CONTEXT[2]:CONTEXT[3]],'prepared focal context')
    require(prep['focus_explicit_pin'].dtype==np.uint8 and bool(prep['focus_explicit_pin'][FOCUS[0]-WINDOW[0],FOCUS[1]-WINDOW[2]]),'explicit focus pin is missing')
    require(base_local[FOCUS[0]-CONTEXT[0],FOCUS[1]-CONTEXT[2]]==np.float32(3.278029680252075),'focus height mismatch')
    same(prep['retained_window_mask'].astype(bool),halo,'retained windows+halo mask')
    same(prep['retained_rect_mask'].astype(bool),rect,'retained window rectangles')
    A,rhs,stencils=helper.build_objective_matrix(base_local,nodes)
    C,d,witnesses,exempt,centers=helper.build_d8_matrix(ev91,base_local,nodes)
    As=sparse.csr_matrix((prep['A_data'],prep['A_indices'],prep['A_indptr']),shape=tuple(map(int,prep['A_shape'])))
    Cs=sparse.csr_matrix((prep['C_data'],prep['C_indices'],prep['C_indptr']),shape=tuple(map(int,prep['C_shape'])))
    require(A.shape==As.shape and C.shape==Cs.shape and np.array_equal(A.indptr,As.indptr) and np.array_equal(A.indices,As.indices)
      and np.array_equal(A.data,As.data) and np.array_equal(rhs,prep['rhs']),'A/RHS reconstruction mismatch')
    require(np.array_equal(C.indptr,Cs.indptr) and np.array_equal(C.indices,Cs.indices) and np.array_equal(C.data,Cs.data)
      and np.array_equal(d,prep['d']),'C/D8 reconstruction mismatch')
    canon=lambda x:json.loads(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False))
    decode=lambda k:json.loads(np.asarray(prep[k],np.uint8).tobytes().decode('utf-8'))
    for k,v in [('witnesses_json',witnesses),('exempt_json',exempt),('centers_json',centers),('stencils_json',stencils)]:
        require(decode(k)==canon(v),f'{k} differs from independent reconstruction')
    original=load_npz(O_EV79)['heights'];lofull,hifull,binfo=bounds_rebuild(bundle['B']['heights'],original,domain['levels'],prep)
    scalar_delta=verify_prepared_scalar_delta(pre,prep,base_local,global_nodes)
    physical_lo=lofull[tuple(global_nodes.T)].astype(np.float64)
    expected_solver_lo=physical_lo.copy()
    target_hits=np.flatnonzero(np.all(global_nodes==np.asarray(SLOPE_TARGET),axis=1))
    require(len(target_hits)==1,'scalar slope target missing/duplicated in rebuilt domain')
    target_idx=int(target_hits[0])
    slope_contract=scalar_slope_local_contract(base_local,prep['fixed_mask'],global_nodes,float(hifull[SLOPE_TARGET]))
    local_target=slope_contract['target_local'];local_nw,local_ne=slope_contract['fixed_local']
    base_se=slope_contract['base_m'];proof_interval=slope_contract['proof']
    require(physical_lo[target_idx] <= base_se <= hifull[SLOPE_TARGET],
            'baseline slope target is outside physical interval')
    expected_solver_lo[target_idx]=max(expected_solver_lo[target_idx],base_se)
    same(prep['lo'],expected_solver_lo,'physical lower bounds plus exactly one derived slope bound')
    same(prep['hi'],hifull[tuple(global_nodes.T)].astype(np.float64),'upper variable bounds')
    same(prep['x0'],base_local[tuple(nodes.T)].astype(np.float64),'fresh baseline x0')
    selected=helper.choose_seed_independent(readj(helper.QUEUE_PATH),mobile)
    require(selected==pre.get('selected_seed'),'selected seed differs from frozen deterministic policy')
    return {'bundle':bundle,'water':water,'civil_report':civil_report,'domain':domain,'halo':halo,'rect':rect,'winfo':winfo,
      'civil_cells':civil_cells,'bridge_metrics':bridge_metrics,'nodes':nodes,'global_nodes':global_nodes,'A':A,'rhs':rhs,'C':C,'d':d,
      'stencils':stencils,'witnesses':witnesses,'exempt':exempt,'centers':centers,'lo':prep['lo'],'hi':prep['hi'],
      'lofull':lofull,'hifull':hifull,'bounds_info':binfo,'selected_seed':selected,
      'scalar_slope_delta':scalar_delta,'scalar_slope_interval':proof_interval,'slope_target_index':target_idx,
      'slope_target_local':local_target,'slope_fixed_local':(local_nw,local_ne)}

if __name__=='__main__':
    if not __debug__:raise RuntimeError('optimized Python is forbidden')
    raise SystemExit(main())

