"""Inventory actual native triangle hinges. Read-only discovery, not shape acceptance."""
from pathlib import Path
import csv, hashlib, json, time
import numpy as np
from scipy.ndimage import distance_transform_edt

B=Path(__file__).parent
SOURCE=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/candidate/terrain.npz')
PLANE=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
FIXED=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/constraints.npz')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def normals(h):
    nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    a=np.stack((-(ne-nw)/6,np.ones_like(nw),(se-ne)/6),axis=-1)
    b=np.stack((-(se-sw)/6,np.ones_like(nw),(sw-nw)/6),axis=-1)
    return a/np.linalg.norm(a,axis=-1)[...,None],b/np.linalg.norm(b,axis=-1)[...,None]

def hinges(h):
    a,b=normals(h)
    pairs=[('diagonal',a,b),('vertical',a[:,:-1],b[:,1:]),('horizontal',b[:-1],a[1:])]
    return [(name,np.degrees(np.arctan2(np.linalg.norm(np.cross(x,y),axis=-1),np.einsum('ijk,ijk->ij',x,y)))) for name,x,y in pairs]

def incident_all(mask,kind):
    if kind=='diagonal':return mask[:-1,:-1]&mask[:-1,1:]&mask[1:,:-1]&mask[1:,1:]
    if kind=='vertical':return mask[:-1,:-2]&mask[:-1,1:-1]&mask[1:,1:-1]&mask[1:,2:]
    return mask[:-2,:-1]&mask[1:-1,:-1]&mask[1:-1,1:]&mask[2:,1:]

def incident_any(mask,kind):return ~incident_all(~mask,kind)

def validate():
    r,c=np.indices((32,32));plane=3+c*.72-r*1.13
    assert max(v.max() for _,v in hinges(plane))<1e-10
    ridge=np.maximum(0,c-16)*6.
    vals=dict(hinges(ridge));nz=vals['vertical'][vals['vertical']>1e-8]
    assert len(nz)==31 and np.allclose(nz,45) and vals['diagonal'].max()<1e-8 and vals['horizontal'].max()<1e-8
    # Independent cross-product normal of the actual vertex ordering, not a stencil copy.
    rng=np.random.default_rng(4901);h=rng.normal(size=(32,32));a,b=normals(h)
    for row,col in rng.integers(0,30,size=(30,2)):
        corners=[np.array([col*6,h[row,col],-row*6]),np.array([(col+1)*6,h[row,col+1],-row*6]),np.array([col*6,h[row+1,col],-(row+1)*6]),np.array([(col+1)*6,h[row+1,col+1],-(row+1)*6])]
        for indices,expected in [((0,1,3),a[row,col]),((0,3,2),b[row,col])]:
            p,q,s=[corners[i] for i in indices];n=np.cross(q-p,s-p);n/=np.linalg.norm(n)
            assert np.max(abs(n-expected))<1e-12
    broken=plane.copy();broken[15,15]+=3
    assert max(v.max() for _,v in hinges(broken))>30
    m=np.ones((4,4),bool);m[0,2]=False
    assert incident_all(m,'vertical')[0,0] # unused NE corner of the neighboring cell
    m[1,2]=False
    assert not incident_all(m,'vertical')[0,0] # actual fourth vertex of the two triangles
    return ['inclined_plane_zero','known_45_degree_fold','independent_cross_product_60_faces','raised_vertex_detected','exact_four_incident_vertices']

def main():
    started=time.monotonic();controls=validate()
    assert sha(SOURCE)=='70f74c9334620c458880f728d3ff15cec7867ffe2bd8bd2e9d5135e1692b7ed5'
    assert sha(PLANE)=='d59dcdb908b4381a456629fb080a9769147b6fb1a3e321a6423bc931a0fb8803'
    t=dict(np.load(SOURCE));h=t['heights'].astype(float);p=np.load(PLANE)
    pmax=np.full(h.shape,-np.inf)
    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):
        s=pmax[dr:dr+2047,dc:dc+2047];np.fmax(s,p,out=s)
    wet=(h<pmax)|(h<.85)
    dry=~wet;engineering=t['reserve']|t['platform'];fixed=np.load(FIXED)['fixed']
    distance=distance_transform_edt(dry)*6
    domain=dict(all=np.ones(h.shape,bool),dry=dry,natural_dry=dry&~engineering,natural_bank=dry&~engineering&(distance<=54),natural_interior=dry&~engineering&(distance>54),engineering=engineering)
    out={k:[] for k in domain};top=[];whole=0
    for kind,values in hinges(h):
        whole+=values.size
        for name,mask in domain.items():
            valid=incident_all(mask,kind);v=values[valid]
            out[name].append(v.astype(np.float32))
            if name not in ('natural_bank','natural_interior'):continue
            flat=np.flatnonzero(valid&(values>=10));ix=flat[np.argsort(values.ravel()[flat])[-200:]]
            for index in ix:
                row,col=np.unravel_index(index,values.shape)
                if kind=='diagonal':xx=(col+.5)*6;zz=12282-(row+.5)*6
                elif kind=='vertical':xx=(col+1)*6;zz=12282-(row+.5)*6
                else:xx=(col+.5)*6;zz=12282-(row+1)*6
                top.append(dict(domain=name,kind=kind,row=int(row),col=int(col),x=xx,z=zz,degrees=float(values[row,col]),any_fixed=bool(incident_any(fixed,kind)[row,col])))
    report={}
    for name,parts in out.items():
        v=np.concatenate(parts)
        report[name]=dict(edges=len(v),mean=float(v.mean()) if len(v) else None,p90=float(np.percentile(v,90)) if len(v) else None,p99=float(np.percentile(v,99)) if len(v) else None,maximum=float(v.max()) if len(v) else None,above10=int((v>10).sum()),above20=int((v>20).sum()),above30=int((v>30).sum()))
    top.sort(key=lambda row:row['degrees'],reverse=True)
    with (B/'worst-native-creases.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(top[0]));writer.writeheader();writer.writerows(top)
    result=dict(status='WHOLE_MAP_NATIVE_HINGE_INVENTORY_NOT_ACCEPTANCE',source_sha256=sha(SOURCE),plane_sha256=sha(PLANE),constraints_sha256=sha(FIXED),native_triangles=2*2047**2,internal_edges=whole,domains=report,controls=controls,seconds=time.monotonic()-started,limits=['Dihedral angles measure folds between rendered-source triangles, not artistic intent or actual LOD selection.','Thresholds 10/20/30 degrees are inventory bins, not retroactive acceptance thresholds.','Domain requires all four unique vertices of the actual incident triangles.','Fixed means the previous terminal pass protection, not a new immutable product requirement.'])
    (B/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
