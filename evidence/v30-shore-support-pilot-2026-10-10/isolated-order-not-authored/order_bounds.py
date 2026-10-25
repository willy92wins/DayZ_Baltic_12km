"""No authoring: derive descent bounds and detect EV83 edge-order reversals."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path('E:/DayZ-Baltic-Build'); O=Path(__file__).parent
old=R/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
pilot=R/'v30-wet-support-shore-pilot-20261010/candidate/terrain.npz'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(old)=='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
assert sha(pilot)=='f0e977d8bc2e11529aedc3851bb1d456b45ffee0e2b974af89db6a26fab087f9'
h=np.load(old)['heights'];v=np.load(pilot)['heights'];rows=[]
for r,c in [(1880,191),(1785,366)]:
 center=float(h[r,c]); neighbors=[]
 for dr in (-1,0,1):
  for dc in (-1,0,1):
   if not(dr or dc):continue
   n=float(h[r+dr,c+dc]); a=center-n;b=float(v[r,c])-n
   ok=(b>=0 if a>0 else b<=0 if a<0 else b==0)
   neighbors.append({'row':r+dr,'col':c+dc,'dr':dr,'dc':dc,'height_B':n,'difference_B':a,'difference_EV83':b,'order_preserved_EV83':bool(ok)})
 bound=max(x['height_B'] for x in neighbors if x['height_B']<=center)
 rows.append({'row':r,'col':c,'x':c*6,'z':12282-r*6,'height_B':center,'height_EV83':float(v[r,c]),'order_min_height':bound,'max_descent_m':center-bound,'reversals_EV83':sum(not x['order_preserved_EV83'] for x in neighbors),'neighbors':neighbors})
out={'status':'READ_ONLY_ORDER_BOUNDS','inputs':{str(old):sha(old),str(pilot):sha(pilot)},'script_sha256':sha(Path(__file__)),'foci':rows,'limits':['Necessary bound only; not angular/coverage PASS.','No new terrain created.']}
(O/'order-bounds.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{k:v for k,v in q.items() if k!='neighbors'} for q in rows]))
