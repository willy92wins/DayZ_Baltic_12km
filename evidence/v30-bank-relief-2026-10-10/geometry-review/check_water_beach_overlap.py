import numpy as np,json,sys
from scipy.ndimage import distance_transform_edt
sys.path.insert(0,r'E:/DayZ-Baltic-Build/v30-surface-crease-audit-20261009'); import audit_native_surface as a
P=r'E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009'; C=P+'/candidate'
t=dict(np.load(C+'/terrain.npz')); h=t['heights'].astype(float); d=dict(np.load(P+'/constraints.npz')); r=json.load(open(r'E:/DayZ-Baltic-Build/v30-bank-relief-review-20261010/luna-geometry/report.json')); seed=np.isin(t['cls'],[3,5,6]); belt=distance_transform_edt(~seed,sampling=6)<=96; sup=d['water_support']; bank=belt&(t['cls']==0)&~sup&~t['reserve']&~t['platform']; w=t['water'].astype(bool); b=t['beach'].astype(bool)
print('bank overlaps water/beach:',int((bank&w).sum()),int((bank&b).sum()),'intersection',int((bank&w&b).sum()))
for maskname,mask in [('water',w),('beach',b)]:
 print(maskname)
 for kind,v in a.hinges(h):
  valid=a.incident_all(bank,kind)&a.incident_any(mask,kind)
  print(kind,'total',int(valid.sum()),'>30',int((valid&(v>30)).sum()))
