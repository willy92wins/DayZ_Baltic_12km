from pathlib import Path
import sys,json,hashlib
import numpy as np
B=Path(__file__).parent;R=B.parent;S=R/'v30-volkhov-stable-derivatives-20261009/candidate'
t=dict(np.load(S/'terrain.npz'));h=t['heights'].astype(float);p=np.load(S/'plane.npy');f=np.load(S/'visible-field.npy')
corners=[(0,0),(0,1),(1,0),(1,1)];hh=np.stack([h[dr:dr+2047,dc:dc+2047] for dr,dc in corners],axis=2)
base=np.fmax(p,.85);F=np.where(np.isfinite(p)[:,:,None],f,.85)
physical=base[:,:,None]-hh;visible=F-hh
wet_face_support=np.zeros(h.shape,bool)
for slots in [[0,1,3],[0,2,3]]:
    wet=np.any(physical[:,:,slots]>1e-7,axis=2)|np.any(visible[:,:,slots]>1e-7,axis=2)
    for j in slots:
        dr,dc=corners[j];wet_face_support[dr:dr+2047,dc:dc+2047]|=wet
engineering=t['reserve']|t['platform'];border=np.zeros(h.shape,bool);border[[0,-1],:]=True;border[:,[0,-1]]=True
fixed=np.load(R/'v30-native-terminal-finish-20261009/constraints.npz')['fixed'];low=(h>.85)&(h<1.79999)&(t['cls']==0)
editable=low&~wet_face_support&~fixed&~engineering&~border
groups=dict(all_low_dry_class_vertices=low,wet_triangle_support=low&wet_face_support,engineering=low&engineering,fixed=low&fixed,border=low&border,editable_strictly_dry=editable,editable_narva=editable&t['narva'])
report=dict(status='READ_ONLY_DOMAIN_CLASSIFICATION',terrain_sha256=hashlib.sha256((S/'terrain.npz').read_bytes()).hexdigest(),counts={k:int(v.sum()) for k,v in groups.items()},max_strict_dry_uplift_m=float(np.max(1.8-h[editable],initial=0)),editable_bounds=None if not editable.any() else [int(np.nonzero(editable)[0].min()),int(np.nonzero(editable)[1].min()),int(np.nonzero(editable)[0].max()),int(np.nonzero(editable)[1].max())],limits=['Strict dry closure freezes every support of every actually wet native face in P, F and the sea crest.','Vertex counts overlap across protected categories and are not a count of rendered defects.'])
np.savez_compressed(B/'domain.npz',editable=editable,wet_face_support=wet_face_support,fixed=fixed,low=low)
(B/'classification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
