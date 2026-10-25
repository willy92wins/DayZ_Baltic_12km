"""Prepare the proposed global dry box/cones, without solver or terrain output."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import time
import numpy as np

HERE=Path(__file__).resolve().parent
HELPER=HERE/'global-sizing-ev95/audit_rounding_direction.py'
HELPER_SHA='4878c338027e6febd9c2f813dc99c5d009d369bc898c370c7153f74635dd7784'
PLAN=HERE/'GLOBAL_DRY_SOLVE_PLAN.md'
OUT=HERE/'global-dry-solve/prepared-01'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def require(ok,msg):
    if not ok:raise ValueError(msg)

def main():
    require(not OUT.exists(),'Keep existing preparation')
    require(sha(HELPER)==HELPER_SHA,'Correct inward helper changed')
    spec=importlib.util.spec_from_file_location('inward_bounds_audit',HELPER)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    inputs={k:v for k,v in helper.INPUTS.items() if k in ('H','O','P','F','masks')}
    start={str(p):sha(p) for p,_ in inputs.values()}
    start[str(HELPER)]=HELPER_SHA;start[str(PLAN)]=sha(PLAN);start[str(Path(__file__))]=sha(Path(__file__))
    for p,wanted in inputs.values():require(start[str(p)]==wanted,'Input hash mismatch '+str(p))
    tic=time.perf_counter()
    with np.load(inputs['H'][0],allow_pickle=False) as z:H=z['heights'].astype(np.float64)
    with np.load(inputs['O'][0],allow_pickle=False) as z:O=z['heights'].astype(np.float64)
    P=np.load(inputs['P'][0],allow_pickle=False,mmap_mode='r')
    F=np.load(inputs['F'][0],allow_pickle=False,mmap_mode='r')
    require(P.dtype==F.dtype==np.dtype('float64'),'P/F must preserve binary64')
    require(H.shape==O.shape==(2048,2048),'Terrain shape changed')
    with np.load(inputs['masks'][0],allow_pickle=False) as z:
        active=z['ev95_variable'].astype(bool);reason=z['reason_bits']
        masks={k:z[k].astype(bool) for k in ('retained_499_halo2','p9_unknown_nodes','water_bbox_nodes','civil_nodes','water_shore_partial_nodes')}
    require(int(active.sum())==2712136,'Unexpected variable domain')
    overlaps={k:int(np.count_nonzero(v & active)) for k,v in masks.items()}
    require(not any(overlaps.values()),'Variable/guard intersection')
    require(not np.any(reason[active] & np.uint16(2047)),'Variable intersects protected reason bit')
    require(not active[840,370],'Historical focus must remain fixed')
    levels=np.full((2048,2048),.85,np.float64)
    pv=np.nan_to_num(P,nan=.85)
    for i,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
        lev=np.maximum(.85,np.maximum(pv,np.nan_to_num(F[:,:,i],nan=.85)))
        dst=levels[dr:dr+2047,dc:dc+2047];np.maximum(dst,lev,out=dst)
    del pv,lev,dst
    lower_real=np.maximum.reduce((H-2.,np.minimum(O,levels+1e-4),np.minimum(O,1.8),O-2.))
    upper_real=np.minimum(H+2.,O+2.)
    lower=helper.inward(lower_real,True);upper=helper.inward(upper_real,False)
    require(np.all(lower[active].astype(np.float64)>=lower_real[active]),'Lower rounded outside')
    require(np.all(upper[active].astype(np.float64)<=upper_real[active]),'Upper rounded outside')
    require(not np.any(lower[active]>upper[active]),'Infeasible variable box')
    require(not np.any((H[active]<lower[active])|(H[active]>upper[active])),'Baseline not in box')
    violations={'baseline_at_or_below_incident_water':int(np.count_nonzero(active & (H<=levels))),
                'lower_at_or_below_incident_water':int(np.count_nonzero(active & (lower.astype(np.float64)<=levels)))}
    OUT.mkdir(parents=True,exist_ok=False)
    if any(violations.values()):
        report={'status':'FAIL_KNOWN_WATER_CLEARANCE_PREPARATION','violations':violations,
                'first_nodes':np.argwhere(active & ((H<=levels)|(lower.astype(np.float64)<=levels)))[:30].tolist(),
                'readset_start':start,'scope':'No solver, box change or terrain output; proposed domain must be reviewed.'}
        (OUT/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report));return
    rc=np.argwhere(active).astype(np.int32)
    baseline_values=H[tuple(rc.T)]
    lo=lower[tuple(rc.T)];hi=upper[tuple(rc.T)]
    radii=np.empty((2047,2047,2),np.float64)
    flat_radius=6.*math.tan(math.radians(35.))
    for r0 in range(0,2047,128):
        r1=min(2047,r0+128)
        nw=H[r0:r1,:-1];ne=H[r0:r1,1:];sw=H[r0+1:r1+1,:-1];se=H[r0+1:r1+1,1:]
        # Match the reference's sum-of-squares norm evaluation, not a rounded degree threshold.
        r_a=np.sqrt((ne-nw)**2+(ne-se)**2)
        r_b=np.sqrt((se-sw)**2+(nw-sw)**2)
        radii[r0:r1,:,0]=np.maximum(flat_radius,r_a)
        radii[r0:r1,:,1]=np.maximum(flat_radius,r_b)
    dest=OUT/'bounds.npz'
    np.savez_compressed(dest,variables_rc=rc,baseline_values=baseline_values,
                        lower_float32=lo,upper_float32=hi,face_radii=radii.reshape(-1))
    end={p:sha(Path(p)) for p in start}
    require(start==end,'Preparation inputs changed')
    report={'status':'PREPARED_GLOBAL_DRY_BOUNDS_NO_SOLVE','variables':len(rc),'faces':radii.size,
            'artifact':str(dest),'artifact_sha256':sha(dest),'readset_start':start,'readset_end':end,
            'known_water':violations,'minimum_baseline_clearance_m':float(np.min(H[active]-levels[active])),
            'minimum_lower_clearance_m':float(np.min(lo.astype(np.float64)-levels[active])),
            'protected_overlaps':overlaps,'physical_budget':'EV79+-2m intersect EV95+-2m and dry floors; no local B+0.5 cap',
            'rounding':'closest inward float32: lower up, upper down',
            'baseline_feasible':True,'frozen_focus':True,'numeric_elapsed_s':time.perf_counter()-tic,
            'solver_executed':False,'terrain_written':False,
            'limits':'Preparation only. Independent review and driver/resource gates required before one solve.'}
    (OUT/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','variables','faces','artifact_sha256','minimum_baseline_clearance_m','minimum_lower_clearance_m','numeric_elapsed_s')}))

if __name__=='__main__':main()
