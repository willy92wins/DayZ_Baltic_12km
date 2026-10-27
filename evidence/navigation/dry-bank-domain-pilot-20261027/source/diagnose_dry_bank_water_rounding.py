from pathlib import Path
import hashlib,json
import numpy as np
R=Path(__file__).parent;O=R/'dry-bank-water-reference-diagnosis-20261027';O.mkdir(exist_ok=False)
source=R/'river-kit7-a-on-f-20261026/kit-7-surfaces.npz';candidate=R/'dry-bank-domain-pilot-20261027/candidate-surfaces.npz'
a=np.load(source);b=np.load(candidate);old=a['bed'][:,:,1];new=b['bed'][:,:,1]
visual=np.broadcast_to(a['water'][:,0,1,None],old.shape);level=np.broadcast_to(a['level'][:,None],old.shape)
old_visual_dry=old>=visual+.025;old_level_dry=old>=level+.025
bad=old_visual_dry&(new<visual+.025)
qs=np.unique(np.r_[np.arange(-18,19.),-2.25,2.25]);rows=[]
for i,j in np.argwhere(bad):
    rows.append(dict(row=int(i),column=int(j),station=float(a['station'][i]),q=float(qs[j]),
        xyz_before=a['bed'][i,j].tolist(),xyz_after=b['bed'][i,j].tolist(),
        visual_water_y=float(visual[i,j]),unrounded_level=float(level[i,j]),
        before_visual_margin=float(old[i,j]-visual[i,j]),after_visual_margin=float(new[i,j]-visual[i,j]),
        original_classified_dry_by_level=bool(old_level_dry[i,j])))
assert rows and not old_level_dry[bad].any()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(status='REJECTED_OFFLINE_ACTUAL_WATER_FLOOR',source_sha256=sha(source),candidate_sha256=sha(candidate),
    violations=int(bad.sum()),all_violations_misclassified_by_unrounded_level=True,
    minimum_visual_margin_after=float((new-visual)[bad].min()),rows=rows,
    mechanism='Author and checker use level before rounding for was_dry. Saved visual water is independently rounded to1/512. Points at exactly13ticks above visual water can fall below level+.025, disable the dry floor, then be lowered.',
    exact_reference='continuous_stream_pilot_v31.py rounds water before saving it; level stores W unchanged. Fix uses saved water Y for both classification and lower bound, with no tolerance change.',
    old_candidate_retired=True,old_script_rerun_authorized=False)
(O/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
