"""Assemble the reviewed C solver from the B equation and joint-constraint kernels."""
from pathlib import Path
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
text=(B/'build_contour_valley.py').read_text().split("print('SOLVE'")[0]
def replace(old,new):
    global text
    assert text.count(old)==1,old
    text=text.replace(old,new)
replace('"""B: fit the true signed contour, allowing declared local shore reclassification."""','"""C: connected native sign field, joint contour and slope constraints; LAND180 source."""')
replace("Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')","B/'candidate-land180/terrain_valley.npz'")
replace('e0d35db0a7a26f9ec055d57f0c9573a1dd2c27911ec8b084274283f5884cffd1','88914948a3a9a3017b3195642657f0fd4c271475f3dccc1ae751b1f5deb045d1')
replace("out=B/'candidate-b'","out=B/'candidate-c'")
replace("design=np.load(B/'contour-design.npz')","design=np.load(B/'contour-design-c.npz')")
replace('zone=core&interior&~fixed',"""historical=json.loads((W/'evidence/v30-bug-recheck-2026-10-08/wave-fixed-reference.json').read_text())
for p in historical['points']:
 r=int(np.floor((12282-p['z'])/6));c=int(np.floor(p['x']/6));fixed[r:r+2,c:c+2]=True
zone=core&interior&~fixed""")
replace('hi[centre]=np.minimum(hi[centre],h[centre])',"""rails=design['flow_rails']
hi[centre|rails]=np.minimum(hi[centre|rails],h[centre|rails])""")
replace('lo[~newwet]=np.maximum(lo[~newwet],landfloor[~newwet])',"""landfloor=np.maximum(landfloor,np.minimum(h,1.8))
lo[~newwet]=np.maximum(lo[~newwet],landfloor[~newwet])""")
replace('ids=np.flatnonzero(local);',"""outside=np.load(B/'candidate-a1/terrain_valley.npz')['heights'].astype(float)
outside=np.where(t['cls']==0,np.maximum(outside,np.minimum(h,1.8)),outside)
base[~local]=outside[~local];base[fixed]=h[fixed]
ids=np.flatnonzero(local);""")
body=(B/'correct_contour_joint.py').read_text().split('# Every native triangle')[1]
body='# Every native triangle'+body
old="x=np.clip(np.load(B/'candidate-b/terrain_valley.npz')['heights'].ravel()[ids].astype(float),lower,upper)"
assert body.count(old)==1
body=body.replace(old,"x=np.clip(base.ravel()[ids].astype(float),lower,upper)")
body=body.replace("E/'authoring-b1.json'","E/'authoring-c.json'")
body=body.replace("Same B contour and depth bounds, one correction for post-reversion inconsistency.","Connected native C field and no-raising flow rails; independent topology and shape gates required.")
text+='\nfrom scipy.sparse.linalg import factorized\n'+body
(B/'build_connected_valley.py').write_text(text)
print('Generated standalone build_connected_valley.py; source and outputs are isolated C.')
