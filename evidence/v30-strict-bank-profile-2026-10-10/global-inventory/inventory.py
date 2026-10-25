"""Read-only whole-map triage and non-overlapping bank-patch queue; no authoring."""
from pathlib import Path
import hashlib, importlib.util, json
import numpy as np
from scipy.ndimage import distance_transform_edt

R=Path('E:/DayZ-Baltic-Build'); O=Path(__file__).parent
B=R/'v30-mixed-bank-incremental-fixed-20261010'
paths={'terrain':B/'candidate/terrain.npz',
       'constraints':R/'v30-narva-dry-bank-relief-20261010/constraints.npz',
       'prior':R/'v30-remaining-exact-dry-support-20261009/constraints.npz',
       'geometry_library':B/'review-luna/verify.py'}
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(paths['terrain'])=='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
t=np.load(paths['terrain']); k=np.load(paths['constraints']); prior=np.load(paths['prior'])
h=t['heights'].astype(float); cls=t['cls']; N=h.shape[0]
spec=importlib.util.spec_from_file_location('geometry',paths['geometry_library']); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
max_hinge=np.zeros(h.shape)
offsets={'diagonal':((0,0),(0,1),(1,0),(1,1)),
         'vertical':((0,0),(0,1),(1,1),(1,2)),
         'horizontal':((0,0),(1,0),(1,1),(2,1))}
for kind,a in m.edge_angles(h):
    for dr,dc in offsets[kind]:
        dst=max_hinge[dr:dr+a.shape[0],dc:dc+a.shape[1]]
        np.maximum(dst,a,out=dst)
distance=distance_transform_edt(~np.isin(cls,(3,5,6)),sampling=6.)
dry=cls==0; bank=dry&(distance<=96)
protected=k['other_fixed']|k['engineering_halo']|prior['large_lake_banks']
available=dry&~protected; wet=k['wet_support'].astype(bool)
sharp=max_hinge>30.0001
# Strict axial summit prominence; no assertion that every such vertex is an artistic defect.
ew=np.zeros(h.shape); ns=np.zeros(h.shape)
ew[:,1:-1]=h[:,1:-1]-np.maximum(h[:,:-2],h[:,2:])
ns[1:-1]=h[1:-1]-np.maximum(h[:-2],h[2:])
axial=(ew>.1)|(ns>.1); peak=(ew>.1)&(ns>.1)
domains={'all_dry':dry,'dry_unprotected':available,
         'bank_unprotected':bank&available,
         'bank_unprotected_wet_support':bank&available&wet,
         'bank_unprotected_outside_wet_support':bank&available&~wet,
         'inland_unprotected_beyond96m':available&~bank,
         'dry_protected':dry&protected}
counts={name:{'vertices':int(mask.sum()),'incident_hinge_over30':int((mask&sharp).sum()),
              'axial_peak_over10cm':int((mask&axial).sum()),
              'two_axis_peak_over10cm':int((mask&peak).sum())}
        for name,mask in domains.items()}
# Potential batch only. 11-node separation gives disjoint 9x9 geometry windows,
# leaving room for all faces/hinges touched by the 5x5 variable interior.
eligible=bank&available&wet&sharp
coords=np.argwhere(eligible)
rank=np.lexsort((coords[:,1],coords[:,0],-max_hinge[eligible]))
blocked=np.zeros(h.shape,dtype=bool); queue=[]
for r,c in coords[rank]:
    if blocked[r,c] or min(r,c)<5 or max(r,c)>=N-5: continue
    interior=available[r-2:r+3,c-2:c+3]&bank[r-2:r+3,c-2:c+3]
    queue.append({'row':int(r),'col':int(c),'x':int(c*6),'z':int(12282-r*6),
                  'max_incident_hinge_deg':float(max_hinge[r,c]),
                  'ew_peak_prominence_m':float(ew[r,c]),'ns_peak_prominence_m':float(ns[r,c]),
                  'potential_variable_count':int(interior.sum()),
                  'sector':[int(r//256),int(c//256)]})
    blocked[max(0,r-10):min(N,r+11),max(0,c-10):min(N,c+11)]=True
# A separate peak-first queue avoids forcing an already low point lower just
# because it is incident to a sharp face on a neighbouring summit.
peak_coords=np.argwhere(eligible&axial)
peak_rank=np.lexsort((peak_coords[:,1],peak_coords[:,0],-max_hinge[eligible&axial]))
blocked_peak=np.zeros(h.shape,dtype=bool); peak_queue=[]
for r,c in peak_coords[peak_rank]:
    if blocked_peak[r,c] or min(r,c)<5 or max(r,c)>=N-5: continue
    peak_queue.append({'row':int(r),'col':int(c),'x':int(c*6),'z':int(12282-r*6),
                       'max_incident_hinge_deg':float(max_hinge[r,c]),
                       'ew_peak_prominence_m':float(ew[r,c]),'ns_peak_prominence_m':float(ns[r,c]),
                       'sector':[int(r//256),int(c//256)]})
    blocked_peak[max(0,r-10):min(N,r+11),max(0,c-10):min(N,c+11)]=True
report={'status':'READ_ONLY_TRIAGE_NO_CANDIDATE',
        'inputs':{n:{'path':str(p),'sha256':sha(p)} for n,p in paths.items()},
        'script_sha256':sha(Path(__file__)), 'counts':counts,
        'potential_nonoverlapping_patches':len(queue),
        'sectors_with_patches':len({tuple(q['sector']) for q in queue}),
        'patch_centres':queue,
        'potential_nonoverlapping_crest_patches':len(peak_queue),
        'crest_patch_centres':peak_queue,
        'limits':['Geometry triage, not a visual defect census or authoring approval.',
                  'Queue only addresses dry unprotected river-bank wet support; other categories remain separate.',
                  'Each actual patch still needs P/F eligibility, physical budget, contour bounds, solver and independent coverage/shape gates.',
                  'This diagnostic reuses a frozen geometry library; it is not an independent verifier.']}
(O/'inventory.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({'counts':counts,'patches':len(queue),'crest_patches':len(peak_queue),'sectors':report['sectors_with_patches']}))
