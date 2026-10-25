from pathlib import Path
import json,sys,hashlib
import numpy as np
R=Path('E:/DayZ-Baltic-Build');B=Path(__file__).parent
sys.path[:0]=[str(R/'v30-native-terminal-finish-20261009'),str(R/'v30-low-water-components-20261009')]
from audit_candidate_coverage import wet_shape
from discover_components import connected,area
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    report=json.loads((B/'authoring.json').read_text());a=dict(np.load(R/'v30-coupled-native-shore-corrected-20261009/candidate/terrain.npz'));b=dict(np.load(B/'candidate/terrain.npz'))
    h,v=a['heights'],b['heights'];p=np.load(R/'v30-global-water-risk-20261009/frozen-field-reference/plane.npy');q=np.load(B/'candidate/plane.npy');f=np.load(R/'v30-frozen-water-stitch-20261009/preserved-field.npy');g=np.load(B/'candidate/visible-field.npy')
    shifted=np.isfinite(p)&(q!=p);rr,cc=np.nonzero(shifted);bounds=json.loads((R/'v30-low-water-components-20261009/compiled-instance-bounds.json').read_text())['objects'];shifts={int(k):val for k,val in report['object_translations'].items()};actual=np.zeros(h.shape);covered=np.zeros(h.shape,bool)
    for o in bounds:
        if o['id'] not in shifts:continue
        x0,z0,x1,z1=o['bounds'];r0=max(0,int(np.floor((12282-z1)/6)));r1=min(2047,int(np.ceil((12282-z0)/6)));c0=max(0,int(np.floor(x0/6)));c1=min(2047,int(np.ceil(x1/6)));s=np.s_[r0:r1+1,c0:c1+1]
        assert np.all(~covered[s]|(abs(actual[s]-shifts[o['id']])<1e-9));actual[s]=shifts[o['id']];covered[s]=True
    for r,c in zip(rr,cc):
        assert np.all(covered[r:r+2,c:c+2]);assert np.max(abs(actual[r:r+2,c:c+2]-(q[r,c]-p[r,c])))<1e-6
    meta=covered&np.isfinite(a['level'])&np.isin(a['cls'],[2,7]);expected=a['level'].copy();expected[meta]=(expected[meta].astype(float)+actual[meta]).astype(expected.dtype)
    def metadata_ok(x):return np.array_equal(x,expected,equal_nan=True)
    difference=0.;maximum=0.
    for r,c in zip(rr,cc):
        old=wet_shape(r,c,h,np.repeat(p[r,c],4));new=wet_shape(r,c,v,np.repeat(q[r,c],4));d=float(old.symmetric_difference(new).area);difference+=d;maximum=max(maximum,d)
    old_conn=connected(h.astype(float),p);new_conn=connected(v.astype(float),q)
    aa=area(old_conn[4].reshape(-1,3))[old_conn[5].ravel()];bb=area(new_conn[4].reshape(-1,3))[new_conn[5].ravel()]
    perbody=np.bincount(old_conn[7],weights=bb-aa,minlength=old_conn[-2]);fixed=a['reserve']|a['platform']|a['beach'];allwrong=(v.astype(float)-h.astype(float))[covered]-actual[covered]
    gates=dict(metadata_consistent=metadata_ok(b['level']),metadata_changed=not metadata_ok(a['level']),other_arrays_exact=all(np.array_equal(a[k],b[k],equal_nan=True) for k in a if k not in ('level','heights')),objects_cover_translated_cells=True,rigid_compiled_bounds=np.max(abs(allwrong))<1e-6,geometry_area=difference<.001,each_component_area=np.max(abs(perbody))<.001,same_component_labels=np.array_equal(old_conn[8],new_conn[8]),fixed_exact=np.array_equal(h[fixed],v[fixed]),visible_levels=np.max(abs((g-f)[np.isfinite(f)]-np.repeat((q-p)[:,:,None],4,axis=2)[np.isfinite(f)]))<1e-6)
    mutant=expected.copy();r,c=np.argwhere(meta)[0];mutant[r,c]+=.025
    negative=dict(old_metadata_rejected=not metadata_ok(a['level']),single_wrong_level_rejected=not metadata_ok(mutant),terrain_without_water_shift_rejected=np.max(abs(v[covered]-h[covered]))>1e-6)
    result=dict(status='PASS_INDEPENDENT_BASIN_GEOMETRY' if all(gates.values()) and all(negative.values()) else 'FAIL_INDEPENDENT_BASIN_GEOMETRY',gates={k:bool(v) for k,v in gates.items()},negatives={k:bool(v) for k,v in negative.items()},shifted_cells=len(rr),metadata_vertices=int(meta.sum()),native_wet_symmetric_difference_m2=difference,worst_cell_difference_m2=maximum,maximum_component_area_change_m2=float(abs(perbody).max()),compiled_bounds_vertices=int(covered.sum()),terrain_sha256=sha(B/'candidate/terrain.npz'),plane_sha256=sha(B/'candidate/plane.npy'),field_sha256=sha(B/'candidate/visible-field.npy'),limits=['Independent GEOS clipping, whole-map labels and metadata readback; compiled WRP and runtime remain separate.'])
    (B/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
