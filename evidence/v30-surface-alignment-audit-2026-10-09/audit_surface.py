from pathlib import Path
import sys,json,hashlib,subprocess,struct,re
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/audit'));from pbo_materials import entries
sys.path.insert(0,str(W/'tools/terrain'));from v30_common import tri_sample
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pbo=Path('P:/Mods/@DayZ_Baltic_TerminalContourV1/Addons/narva_trial.pbo');assert sha(pbo)=='c06f9b52d0b31d5c6e5cd3ec6c8cb14055abbe3ae40163092403b5ac66ca88fe'
terrain=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/candidate/terrain.npz');assert sha(terrain)=='70f74c9334620c458880f728d3ff15cec7867ffe2bd8bd2e9d5135e1692b7ed5'
field=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy');assert sha(field)=='d59dcdb908b4381a456629fb080a9769147b6fb1a3e321a6423bc931a0fb8803'
h=np.load(terrain)['heights'].astype(float);p=np.load(field)
table,offset=entries(pbo);masks=[];materials=[]
rawdir=B/'decoded-masks';rawdir.mkdir(exist_ok=False)
with pbo.open('rb') as f:
 for name,method,size in table:
  match=re.search(r'(?:^|[\\/])m_(\d{3})_(\d{3})_lca\.paa$',name,re.I)
  ismat=bool(re.search(r'layers[\\/]p_.*\.rvmat$',name,re.I))
  if match or ismat:
   assert method==0,(name,method);f.seek(offset);data=f.read(size);assert len(data)==size
   if match:
    a,b=map(int,match.groups());target=rawdir/f'm_{a:03d}_{b:03d}_lca.paa';assert not target.exists();target.write_bytes(data);masks.append((a,b,target))
   else:
    refs=sorted(set(s.lower().decode() for s in re.findall(rb'dz\\surfaces\\data\\terrain\\([a-z0-9_]+?)_(?:ca|nopx|nohq|co)\.paa',data,re.I)))
    materials.append(dict(name=name,surfaces=refs))
  offset+=size
assert len(masks)==1024 and len({(a,b) for a,b,path in masks})==1024
tool=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/ImageToPAA/ImageToPAA.exe')
def work(item):
 a,b,path=item;png=path.with_suffix('.png')
 done=subprocess.run([str(tool),str(path),str(png)],capture_output=True,text=True)
 if done.returncode!=0 or not png.exists():raise RuntimeError((str(path),done.returncode,done.stdout[-600:],done.stderr[-600:]))
 im=np.array(Image.open(png).convert('RGBA'));assert im.shape==(512,512,4),im.shape
 # Unique 384m core per tile; the outer six-metre terrain boundary is excluded.
 uv=np.arange(384)+.5;xx,zz=np.meshgrid(a*384+uv,12288-b*384-uv)
 valid=(xx<12282)&(zz<12282)&(zz>0)
 rr=np.clip(np.floor((12282-zz)/6).astype(int),0,2046);cc=np.clip(np.floor(xx/6).astype(int),0,2046)
 level=np.maximum(np.nan_to_num(p[rr,cc],nan=-1e9),.75);ground=tri_sample(h,xx,zz);depth=level-ground
 water=valid&(depth>1e-6);interior=water&(depth>=.20)
 rgb=im[64:448,64:448,:3];gravel=(rgb.max(axis=2)<=8)
 wrong=water&~gravel;deepwrong=interior&~gravel
 ids=np.argwhere(deepwrong)
 examples=[dict(x=float(xx[r,c]),z=float(zz[r,c]),depth=float(depth[r,c]),rgb=rgb[r,c].tolist()) for r,c in ids[:3]]
 return dict(tile=[a,b],pixels=int(valid.sum()),wet=int(water.sum()),wet_gravel=int((water&gravel).sum()),wet_non_gravel=int(wrong.sum()),deep_wet=int(interior.sum()),deep_wet_non_gravel=int(deepwrong.sum()),examples=examples,paa_sha256=sha(path),decoded_sha256=sha(png))
reports=[]
with ThreadPoolExecutor(max_workers=4) as ex:
 for i,r in enumerate(ex.map(work,sorted(masks))):
  reports.append(r)
  if i%128==127:print(f'{i+1}/1024 masks decoded and audited',flush=True)
sums={k:sum(x[k] for x in reports) for k in ['pixels','wet','wet_gravel','wet_non_gravel','deep_wet','deep_wet_non_gravel']}
assert sums['pixels']==12282**2,sums
# The consumer must reject non-gravel at a wet point; a mask of all gravel cannot fail this narrow invariant.
positive=sums['wet_gravel']>1000000
negative=bool(np.array([255,0,0]).max()>8)
planar=np.add.outer(np.arange(2048)*-12.,np.arange(2048)*6.)+24564
xx=np.array([3.,123.5,5400.25]);zz=np.array([3.,531.5,6200.25]);triangle_control=bool(np.max(abs(tri_sample(planar,xx,zz)-(xx+2*zz)))<1e-8)
result=dict(status='PASS_WET_MASK_INTERIORS' if sums['deep_wet_non_gravel']==0 else 'FAIL_WET_MASK_ALIGNMENT',counts=sums,positive_gravel_water=positive,negative_red_rejected=negative,analytic_triangle_control=triangle_control,materials=len(materials),all_materials_four_surfaces=all(len(m['surfaces'])==4 for m in materials),inputs={str(q):sha(q) for q in [pbo,terrain,field,tool]},tiles=reports,material_inventory=materials,limits=['Uses nominal 0.75m sea and compiled pond level; not an infinite tide envelope.','Mask gravel on dry ground is not necessarily an error.','Per-pixel decoding includes DXT compression; border filtering is reported separately.','No final satellite-color or renderer-distance acceptance.'])
(B/'surface-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['tiles','material_inventory']},indent=2))
assert positive and negative and triangle_control
