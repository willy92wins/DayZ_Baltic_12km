"""Read-only inventory for a future river-bank plan; not an authoring selector."""
from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
from scipy.ndimage import distance_transform_edt

R=Path('E:/DayZ-Baltic-Build'); B=R/'v30-mixed-bank-incremental-fixed-20261010'; O=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B/'candidate/terrain.npz')=='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
paths={'terrain':B/'candidate/terrain.npz','constraints':R/'v30-narva-dry-bank-relief-20261010/constraints.npz','prior':R/'v30-remaining-exact-dry-support-20261009/constraints.npz','consumer':B/'review-luna/verify.py'}
t=np.load(paths['terrain']); k=np.load(paths['constraints']); prior=np.load(paths['prior'])
spec=importlib.util.spec_from_file_location('old_consumer',paths['consumer']); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
h=t['heights'].astype(float); cls=t['cls']; wet=k['wet_support'].astype(bool)
other=k['other_fixed'].astype(bool); eng=k['engineering_halo'].astype(bool); lakes=prior['large_lake_banks'].astype(bool)
dist=distance_transform_edt(~np.isin(cls,(3,5,6)),sampling=6.)
river=(cls==0)&(dist<=96.)
eligible=river&wet&~other&~eng&~lakes
folds=m.selector_from_source(eligible,h)
sectors=[]
for rr in range(0,2048,256):
 for cc in range(0,2048,256):
  q=folds[rr:rr+256,cc:cc+256]
  if q.any():sectors.append({'row_start':rr,'col_start':cc,'vertices_incident_over30':int(q.sum())})
report={'status':'READ_ONLY_DOMAIN_INVENTORY_NOT_AUTHORIZATION','inputs':{n:{'path':str(p),'sha256':sha(p)} for n,p in paths.items()},'script_sha256':sha(Path(__file__)),
 'counts':{'dry_river_band_96m':int(river.sum()),'in_wet_support':int((river&wet).sum()),'other_fixed':int((river&wet&other).sum()),'engineering_halo':int((river&wet&eng).sum()),'large_lake_banks':int((river&wet&lakes).sum()),'wet_support_only_unprotected':int(eligible.sum()),'unprotected_incident_B_hinge_over30':int(folds.sum())},
 'sectors_1536m':sectors,'limits':['Read-only and no global candidate. Pilot has two mutable vertices only.','Counts are terrain geometry, not confirmed visual pyramids.','Reason counts overlap; future eligibility still needs per-cell P/F support, signs, contours, compiled coverage, budget and shape checks.','Large lakes excluded explicitly even if wet_support overlaps their fixed mask.']}
(O/'domain-inventory.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'counts':report['counts'],'sectors':len(sectors)}))
