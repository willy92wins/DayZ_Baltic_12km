#!/usr/bin/env python
"""Read-only finite one-ULP neighborhood diagnostic for the failed C_cross rows."""
from __future__ import annotations
import hashlib, itertools, json
from pathlib import Path
import numpy as np
from scipy import sparse

ROOT = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/G/wet-bank-pilot")
PREP = ROOT / "prepared-runs/attempt-08/prepared.npz"
SOL = ROOT / "solve-once/solution.npz"
RESULT = ROOT / "solve-once/solve-result.json"
OUTPUT = ROOT / "postsolve-consumer/quantization-diagnostic.json"
EXPECTED = {
    PREP: "52409a8d074d15ec068bddc6e9265bc3782e84e9d54582b8a6d7b0a6675a787f",
    SOL: "1b7a23ebb3c203427f1c77cb8de6becfca750746e47f5494bba6723b0610eab1",
    RESULT: "35722fa7b8f3235597ed6f82c5263da6320d2d030b3dbef3558728386c4240ca",
}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def csr(z, p):
    return sparse.csr_matrix((z[p+'_data'],z[p+'_indices'],z[p+'_indptr']),shape=tuple(z[p+'_shape']))

def run():
    for p,want in EXPECTED.items():
        got=sha(p)
        if got!=want:raise ValueError(f'input changed: {p} expected {want} got {got}')
    with np.load(PREP,allow_pickle=False) as p, np.load(SOL,allow_pickle=False) as s:
        C=csr(p,'C_cross');D=csr(p,'C_d8');A=csr(p,'A');G=csr(p,'G')
        rc=p['variables_rc'].astype(np.int64); base=np.array([855,1179]); nodes=rc-base
        raw=s['raw_float32_grid'][tuple(nodes.T)]; closed=s['closed_float32_grid'][tuple(nodes.T)]
        cont=s['solution_float64']; lo=p['lo_absolute_float32_inward'];hi=p['hi_absolute_float32_inward']
        d=p['d_C_cross']; c64=np.asarray(C@cont-d).ravel(); c32=np.asarray(C@closed.astype(np.float64)-d).ravel()
        bad=np.flatnonzero(c32<0.0)
        involved=np.unique(np.concatenate([C.getrow(int(i)).indices for i in bad])).astype(int)
        opts=[]
        for j in involved:
            x=np.float32(closed[j]); row=[]
            for direction in (-1,0,1):
                q=x if direction==0 else np.nextafter(x,np.float32(-np.inf if direction<0 else np.inf),dtype=np.float32)
                row.append(None if q<lo[j] or q>hi[j] else float(q))
            opts.append(row)
        choices=[]; count_cross=0; count_all_c_box=0
        for combo in itertools.product(range(3), repeat=len(involved)):
            delta=np.zeros(len(rc),dtype=np.float64)
            for pos,(j,op) in enumerate(zip(involved,combo)):
                v=opts[pos][op]
                if v is None:break
                delta[j]=v-float(closed[j])
            else:
                cc=c32+np.asarray(C@delta).ravel()
                if np.all(cc>=0.0):
                    count_cross+=1
                    xx=closed.astype(np.float64)+delta
                    dd=np.asarray(D@xx-p['d_C_d8']).ravel()
                    in_box=bool(np.all(xx>=lo) and np.all(xx<=hi))
                    if np.all(dd>=0.0) and in_box:
                        count_all_c_box+=1
                    q=(G@xx+p['k_G']).reshape(-1,2)
                    cones=np.linalg.norm(q,axis=1)-p['radii_G']
                    obj=.5*float(np.sum((A@xx-p['rhs_A'])**2))
                    base_obj=.5*float(np.sum((A@closed.astype(float)-p['rhs_A'])**2))
                    steps=[int(op-1) for op in combo]
                    lex=tuple((int(rc[j,0]),int(rc[j,1]),step) for j,step in zip(involved,steps) if step)
                    choices.append({'steps':steps,'rank':(sum(abs(v) for v in steps),
                        float(np.linalg.norm(xx-cont)),lex),
                        'changed_variables':int(np.count_nonzero(delta)),
                        'min_C_cross_slack':float(cc.min()),
                        'min_D8_slack':float(dd.min()),
                        'max_cone_excess':float(cones.max()),
                        'within_box':in_box,'all_C_and_box_pass':bool(np.all(dd>=0.0) and in_box),
                        'objective_delta_from_closed':obj-base_obj})
        choices.sort(key=lambda x:x['rank'])
        all_c_choices=[x for x in choices if x['all_C_and_box_pass']]
        best=all_c_choices[0] if all_c_choices else None
        meta=json.loads(p['crossing_rows_json'].tobytes().decode('utf-8'))[:C.shape[0]]
        rec={
          'schema':'ev94.wet-bank-crossing-quantization-diagnostic.v1',
          'status':'DIAGNOSTIC_ONLY_NO_MUTATION',
          'inputs':{str(path):sha(path) for path in EXPECTED},
          'continuous_float64':{'min_C_cross_slack':float(c64.min()),'negative_rows_exact':int(np.count_nonzero(c64<0.0))},
          'quantized_raw_float32':{'min_C_cross_slack':float(c32.min()),'negative_rows_exact':int(np.count_nonzero(c32<0.0))},
          'closure_equal_raw':bool(np.array_equal(s['raw_float32_grid'].view(np.uint32),s['closed_float32_grid'].view(np.uint32))),
          'negative_row_count':int(len(bad)),
          'involved_variables':[{'index':int(j),'rc':rc[j].tolist(),'closed_f32':float(closed[j]),
             'lo_f32':float(lo[j]),'hi_f32':float(hi[j]),'one_ulp_choices':opts[pos]}
             for pos,j in enumerate(involved)],
          'negative_rows':[{'row':int(i),'slack_f32':float(c32[i]),'slack_float64':float(c64[i]),'metadata':meta[i]}
             for i in bad],
          'individual_row_test':'Every negative C_cross row has at least one single-variable one-ULP neighbor within box that fixes that row; this is not a simultaneous-feasibility claim.',
          'simultaneous_one_ulp_neighborhood':{'variables':int(len(involved)),'assignments_enumerated':int(3**len(involved)),
             'assignments_satisfying_all_C_cross':count_cross,'assignments_satisfying_all_C_and_box':count_all_c_box,
             'choice_order':'minimum L1 ULP steps, then minimum L2 distance to continuous x64, then lexicographic (r,c,step)',
             'best_all_C_and_box_choice':best},
          'interpretation':'No values were written or substituted into the candidate. A successful neighbor would still require all independent gates and a separately authorized workflow; this diagnostic does not repair or create a candidate.'}
    OUTPUT.write_text(json.dumps(rec,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':rec['status'],'continuous_min':rec['continuous_float64']['min_C_cross_slack'],
      'float32_min':rec['quantized_raw_float32']['min_C_cross_slack'],'negative_rows':len(bad),
      'involved_variables':len(involved),'assignments_satisfying_all_C_cross':len(choices),'output':str(OUTPUT)}))

if __name__=='__main__':run()
