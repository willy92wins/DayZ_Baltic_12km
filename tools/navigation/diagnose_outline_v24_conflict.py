"""Isolate uniform shore freeboard against small-lake depth, using frozen rows."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.sparse import load_npz
from scipy.optimize import linprog
from shapely.geometry import shape
ROOT=Path(__file__).resolve().parents[2]
F=ROOT/'tests/regional_outline_smoothing_v24a'

def main():
    out=F/'lake217-isolation.json';assert not out.exists()
    A=load_npz(F/'constraints.npz');d=np.load(F/'variables.npz');ix=d['variables'];rhs=d['rhs'];build=json.loads((F/'build.json').read_text())
    f=next(f for f in json.loads((ROOT/'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson').read_text())['features'] if f['properties']['body']=='lake_217')
    x0,z0,x1,z1=shape(f['geometry']).buffer(12).bounds;x=ix%2048*6;z=12282-ix//2048*6
    selection=(x>=x0)&(x<=x1)&(z>=z0)&(z<=z1)
    rows=np.flatnonzero(A[:,selection].getnnz(axis=1));B=A[rows];cols=np.unique(B.indices);B=B[:,cols]
    ref=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz');h=ref['candidate'].ravel()[ix[cols]];wet=(ref['wet']|ref['ocean']).ravel()[ix[cols]]
    bounds=list(zip(np.where(wet,h-6,np.maximum(h-6,1.4)),h+6))
    dry=rows<build['category_counts']['dry_plane'];core=(rows>=build['category_counts']['dry_plane'])&(rows<build['category_counts']['dry_plane']+build['category_counts']['lake_core'])
    records=[]
    for name,keep,adjust in [('original',np.ones(len(rows),bool),0),('shore_without_uniform_35cm',np.ones(len(rows),bool),.35),('no_core_depth',~core,0)]:
        limits=rhs[rows].copy();limits[dry]+=adjust
        r=linprog(np.zeros(len(cols)),A_ub=B[keep],b_ub=limits[keep],bounds=bounds,method='highs',options={'threads':1,'time_limit':60,'primal_feasibility_tolerance':1e-8})
        record=dict(case=name,status=str(r.message),success=bool(r.success),rows=int(keep.sum()))
        if r.success:record['maximum_residual']=float((B[keep]@r.x-limits[keep]).max())
        records.append(record);print(record,flush=True)
    report=dict(status='ISOLATION_DIAGNOSTIC_NOT_TERRAIN',body='lake_217',level=f['properties']['level_m'],bounds_xz=[x0,z0,x1,z1],variables=len(cols),selected_rows=len(rows),row_classes=dict(dry=int(dry.sum()),core=int(core.sum()),slope=int((~(dry|core)).sum())),experiments=records,limits=['Subset of full constraints; infeasibility of the subset proves a conflict in the full model, feasibility does not prove global feasibility.','Uniform shore adjustment is an experiment, not an accepted global terrain change.'])
    out.write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
