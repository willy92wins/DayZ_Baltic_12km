"""One rigid, shape-preserving diagnostic translation of a compiled basin cohort."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.ndimage import distance_transform_edt
from discover_components import SOURCE,PLANE,sha,connected,area
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import tri_sample
FIELD=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009/preserved-field.npy')

def corners(cells):
    out=np.zeros((2048,2048),bool)
    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):out[dr:dr+2047,dc:dc+2047]|=cells
    return out

def depths(h,p):
    r,c=np.nonzero(np.isfinite(p));return p[r,c,None]-np.stack([h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]],axis=1)

def slope(h,dr,dc):
    h=h.astype(float)
    return np.degrees(np.arctan(np.hypot(h[dr:dr+2047,dc:dc+2047]-h[:-1,:-1],h[1:,1:]-h[dr:dr+2047,dc:dc+2047])/6))

def main():
    assert not (B/'translation-authoring.json').exists(),'One candidate budget'
    assert sha(SOURCE)=='fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6'
    assert sha(PLANE)=='d59dcdb908b4381a456629fb080a9769147b6fb1a3e321a6423bc931a0fb8803'
    t=dict(np.load(SOURCE));h=t['heights'];p=np.load(PLANE);f=np.load(FIELD)
    cohort=json.loads((B/'cohort.json').read_text());support=np.load(B/'cohort-support.npz');core=support['vertices'];cells=support['cells']
    shift=float(np.float32(1.125+cohort['quantized_shift_to_1_001m']))-1.125
    affected=np.isfinite(p)&cells;other_water=corners(np.isfinite(p)&~affected)
    protected=other_water|t['reserve']|t['platform']
    assert not (protected&core).any(),'Shared fixed/translated support conflict'
    assert np.all(p[affected]==1.125)
    dist=distance_transform_edt(~core,sampling=6);s=np.clip(1-dist/36,0,1);weight=s*s*s*(10+s*(-15+6*s));weight[protected]=0
    v=(h.astype(float)+shift*weight).astype(np.float32);q=p.copy();q[affected]+=shift;g=f.copy();g[affected]+=shift
    target=B/'translation';target.mkdir(exist_ok=False)
    # Metadata remains the baseline source classification: authoring a new level policy is not part of this diagnostic.
    np.savez_compressed(target/'terrain.npz',**(t|dict(heights=v)))
    np.save(target/'plane.npy',q);np.save(target/'visible-field.npy',g)
    np.savez_compressed(target/'delta.npz',rows=np.nonzero(v!=h)[0],cols=np.nonzero(v!=h)[1],before=h[v!=h],after=v[v!=h])
    changed=v!=h;hd=np.stack([h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]],axis=2);vd=np.stack([v[:-1,:-1],v[:-1,1:],v[1:,:-1],v[1:,1:]],axis=2)
    physical_error=float(abs(depths(v,q)-depths(h,p)).max());visible_error=float(np.max(abs((g-vd)-(f-hd))[np.isfinite(f)]))
    a=connected(h.astype(float),p);b=connected(v.astype(float),q)
    aa=area(a[4].reshape(-1,3));bb=area(b[4].reshape(-1,3));area_error=float(abs(bb-aa).sum())
    slope_excess=max(float((slope(v,dr,dc)-np.maximum(slope(h,dr,dc),35)).max(initial=0)) for dr,dc in ((0,1),(1,0)))
    gates=dict(rigid_core=np.max(abs((v[core].astype(float)-h[core])-shift))<1e-6,engineering_exact=np.array_equal(v[t['reserve']|t['platform']],h[t['reserve']|t['platform']]),outside_exact=not (changed&(dist>=36)).any(),other_water_exact=np.array_equal(v[other_water],h[other_water]),physical_depths=physical_error<1e-6,visible_depths=visible_error<1e-6,wet_faces_and_connections=np.array_equal(a[8],b[8]) and a[-1]==b[-1],wet_area=area_error<=.001,bed_floor=float(v[core].min())>=1,no_new_steep_faces=slope_excess<=1e-4)
    controls=dict(missing_water_shift_rejected=float(abs(depths(v,p)-depths(h,p)).max())>1e-6,old_bed_rejected=float(h[core].min())<1,connectivity_controls=__import__('discover_components').controls())
    result=dict(status='PASS_ISOLATED_TRANSLATION_SOURCE' if all(gates.values()) else 'FAIL_ISOLATED_TRANSLATION_SOURCE',source_sha256=sha(SOURCE),terrain_sha256=sha(target/'terrain.npz'),plane_sha256=sha(target/'plane.npy'),field_sha256=sha(target/'visible-field.npy'),shift_m=shift,object_ids=[o['id'] for o in cohort['objects']],physical_components=cohort['cohort_components'],changed_vertices=int(changed.sum()),core_vertices=int(core.sum()),water_cells=int(affected.sum()),minimum_bed_m=float(v[core].min()),physical_depth_max_error_m=physical_error,visible_depth_max_error_m=visible_error,wet_area_difference_m2=area_error,slope_excess_degrees=slope_excess,calibrated_dry_ground_before=float(tri_sample(h,2718.4852495913565,6812.812873578129)),calibrated_dry_ground_after=float(tri_sample(v,2718.4852495913565,6812.812873578129)),gates=gates,controls=controls,limits=['Diagnostic only; metadata levels are unchanged and must not feed a regeneration.','No nominal/visible shape smoothing or global residual closure.'])
    (B/'translation-authoring.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert all(gates.values()),gates

if __name__=='__main__':main()
