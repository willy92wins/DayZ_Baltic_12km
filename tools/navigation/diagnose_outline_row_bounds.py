"""Check necessary single-row feasibility under the frozen height box."""
from pathlib import Path
import json
import numpy as np
from scipy.sparse import load_npz
ROOT=Path(__file__).resolve().parents[2];F=ROOT/'tests/regional_outline_smoothing_v24a'

def main():
    out=F/'individual-row-bounds.json';assert not out.exists()
    B=load_npz(F/'constraints.npz');data=np.load(F/'variables.npz');rhs=data['rhs'];ix=data['variables'];ref=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz');h=ref['candidate'].ravel()[ix].astype(float);wet=(ref['wet']|ref['ocean']).ravel()[ix];lo=np.where(wet,h-6,np.maximum(h-6,1.4));hi=h+6
    records=[];count=0;worst=[]
    build=json.loads((F/'build.json').read_text());nd=build['category_counts']['dry_plane'];nc=build['category_counts']['lake_core'];counts={}
    for start in range(0,len(rhs),250000):
        A=B[start:start+250000];minimum=A.maximum(0)@lo+A.minimum(0)@hi;bad=np.flatnonzero(minimum>rhs[start:start+len(minimum)]+1e-7)
        for j in bad:
            row=start+int(j);kind='dry_plane' if row<nd else 'lake_core' if row<nd+nc else 'slope';counts[kind]=counts.get(kind,0)+1;worst.append((float(minimum[j]-rhs[row]),row))
    for gap,row in sorted(worst,reverse=True)[:30]:
        v=B.getrow(row);records.append(dict(row=row,category='dry_plane' if row<nd else 'lake_core' if row<nd+nc else 'slope',gap_m=gap,rhs=float(rhs[row]),vertices=[dict(xz=[int(ix[j]%2048*6),int(12282-ix[j]//2048*6)],coefficient=float(c),height=float(h[j]),lo=float(lo[j]),hi=float(hi[j]),wet=bool(wet[j])) for j,c in zip(v.indices,v.data)]))
    result=dict(status='INDIVIDUAL_ROWS_INFEASIBLE' if worst else 'NO_INDIVIDUAL_CONFLICT_COUPLED_DIAGNOSIS_REQUIRED',count=len(worst),categories=counts,worst=records)
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
