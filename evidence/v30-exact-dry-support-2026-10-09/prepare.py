from pathlib import Path
import shutil
B=Path(__file__).parent;R=B.parent
src=R/'v30-strict-dry-floor-20261009/author.py';code=src.read_text()
code=code.replace('v30-volkhov-stable-derivatives-20261009/candidate','v30-strict-dry-composition-20261009/candidate')
old="fixed=prior['fixed']|scope['wet_face_support'];target=scope['editable']&~fixed;assert int(target.sum())==2293"
new="""other_fixed=scope['fixed']|t['water']|t['beach']|(t['cls']!=0)|prior['large_lake_banks']
other_fixed[:11]=True;other_fixed[-11:]=True;other_fixed[:,:11]=True;other_fixed[:,-11:]=True
assert np.array_equal(other_fixed|prior['water_support'],prior['fixed']), 'Every prior non-water protection must be reconstructed exactly'
fixed=other_fixed|scope['wet_face_support']
target=np.load(R/'v30-strict-dry-floor-20261009/constraints.npz')['target']&(original<1.79999)
assert int(target.sum())==2197 and not (target&fixed).any()
assert sha(S/'terrain.npz')=='7bcfae7662acf3f83ff0f52434a3d9c3f1e8af745574b2fdc3ad689db123a990'
released=prior['fixed']&~fixed
assert not (released&(scope['wet_face_support']|other_fixed)).any()
"""
assert old in code;code=code.replace(old,new)
code=code.replace("minimum[target]=1.8;maximum=original+.4;h[target]=1.8","minimum[target]=float(np.float32(1.8));maximum=original+.4;h[target]=float(np.float32(1.8))")
code=code.replace("water_support=prior['water_support']","water_support=scope['wet_face_support'],released_dry= released,other_fixed=other_fixed")
code=code.replace("target_vertices=int(target.sum()),","released_dry_vertices=int((released&allowed).sum()),target_vertices=int(target.sum()),")
code=code.replace("dest.mkdir(exist_ok=False);","dest.mkdir(exist_ok=False);\nfor name in ['plane.npy','visible-field.npy']:shutil.copyfile(S/name,dest/name)\n")
code=code.replace('import sys,json,time,hashlib','import sys,json,time,hashlib,shutil')
(B/'author.py').write_text(code)

code=(R/'v30-strict-dry-composition-20261009/verify.py').read_text()
code=code.replace('v30-volkhov-stable-derivatives-20261009/candidate','v30-strict-dry-composition-20261009/candidate')
needle='def physical(h,v,t,u,fixed,allowed,p):'
insert="""def exact_wet_support(h,p):
    f=np.load(SOURCE.parent/'visible-field.npy');corners=[(0,0),(0,1),(1,0),(1,1)]
    hv=[h[dr:dr+2047,dc:dc+2047] for dr,dc in corners]
    nominal=np.fmax(p,.85);visible=np.where(np.isfinite(p)[:,:,None],f,.85)
    support=np.zeros(h.shape,bool)
    for ids in [(0,1,3),(0,2,3)]:
        wet=np.logical_or.reduce([(nominal>hv[i])|(visible[:,:,i]>hv[i]) for i in ids])
        for i in ids:
            dr,dc=corners[i];support[dr:dr+2047,dc:dc+2047]|=wet
    return support

"""
assert needle in code;code=code.replace(needle,insert+needle)
old="    water=np.zeros(h.shape,bool)\n    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):water[dr:dr+2047,dc:dc+2047]|=np.isfinite(p)"
assert old in code;code=code.replace(old,"    water=exact_wet_support(h,p)")
code=code.replace('water_cells_exact','water_faces_exact')
code=code.replace("('water_faces_exact',np.isfinite(p),.1)","('water_faces_exact',exact_wet_support(h,p),.1)")
code=code.replace("gates['no_lowering']=bool(np.all(v>=h-1e-6))","gates['no_lowering']=bool(np.all(v>=h-1e-6))\n    gates['frozen_fields_exact']=all(sha(SOURCE.parent/name)==sha(B/'candidate'/name) for name in ['plane.npy','visible-field.npy'])")
code=code.replace('Water-support cells are byte-identical.','All actually wet native triangles retain every support vertex exactly; entirely dry corners of finite P cells may rise.')
(B/'verify.py').write_text(code)
print('EV70_AUTHOR_AND_CONSUMER_PREPARED')
