"""Read-only interval infeasibility certificates for an already frozen road LP."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
from scipy.sparse import load_npz

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists()
    report=json.loads((a.folder/'solve.json').read_text(encoding='utf-8'))
    data=np.load(a.folder/'variables.npz');B=load_npz(a.folder/'constraints.npz')
    cap=report['maximum_allowed_delta_m'];lo=np.maximum(-cap,data['floor']);hi=np.full(len(lo),cap)
    positive=B.copy();positive.data=np.maximum(0,positive.data)
    negative=B.copy();negative.data=np.minimum(0,negative.data)
    minimum=positive@lo+negative@hi;excess=minimum-data['rhs'];bad=np.flatnonzero(excess>1e-7)
    fixed=np.diff(B.indptr)==0;road=report['road_constraints'];slope=road+report['slope_constraints']
    examples=[]
    for row in bad[np.argsort(excess[bad])[-30:][::-1]]:
        r=B.getrow(row);ids=data['indices'][r.indices]
        examples.append(dict(row=int(row),family='road' if row<road else 'slope' if row<slope else 'chord',excess=float(excess[row]),rhs=float(data['rhs'][row]),nonzero_coefficients=int(len(r.data)),variable_xz=np.column_stack([ids%2048*6,12282-ids//2048*6]).tolist(),coefficients=r.data.tolist()))
    result=dict(status='READ_ONLY_BOUND_CONTRADICTION_DIAGNOSTIC',individually_infeasible=int(len(bad)),fixed_infeasible=int(np.sum(fixed[bad])),by_family=dict(road=int(np.sum(bad<road)),slope=int(np.sum((bad>=road)&(bad<slope))),chord=int(np.sum(bad>=slope))),examples=examples,source_sha256=hashlib.sha256((a.folder/'constraints.npz').read_bytes()).hexdigest())
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':main()
