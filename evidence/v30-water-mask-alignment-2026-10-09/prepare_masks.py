from pathlib import Path
import sys,json,hashlib,subprocess
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');sys.path.insert(0,str(W/'tools/terrain'));from v30_common import tri_sample
source=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/data/layers')
terrain=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/candidate/terrain.npz');field=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(terrain)=='70f74c9334620c458880f728d3ff15cec7867ffe2bd8bd2e9d5135e1692b7ed5';assert sha(field)=='d59dcdb908b4381a456629fb080a9769147b6fb1a3e321a6423bc931a0fb8803'
h=np.load(terrain)['heights'];p=np.load(field);out=B/'layers';out.mkdir(exist_ok=False);decoded=B/'decoded';decoded.mkdir(exist_ok=False)
tool=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/ImageToPAA/ImageToPAA.exe')
def work(ab):
 a,b=ab;name=f'm_{a:03d}_{b:03d}_lca';before=np.array(Image.open(source/(name+'.png')).convert('RGBA'))
 assert before.shape==(512,512,4)
 uv=np.arange(512)-64+.5;xx,zz=np.meshgrid(a*384+uv,12288-b*384-uv);xc=np.clip(xx,0,12282);zc=np.clip(zz,0,12282)
 rr=np.clip(np.floor((12282-zc)/6).astype(int),0,2046);cc=np.clip(np.floor(xc/6).astype(int),0,2046);level=np.maximum(np.nan_to_num(p[rr,cc],nan=-1e9),.75)
 depth=level-tri_sample(h,xc,zc);wet=depth>1e-6;after=before.copy();after[wet,:3]=0
 assert np.array_equal(before[~wet],after[~wet]) and np.array_equal(before[:,:,3],after[:,:,3]) and np.all(after[wet,:3]==0)
 png=out/(name+'.png');paa=out/(name+'.paa');Image.fromarray(after).save(png)
 cmd=subprocess.run([str(tool),str(png),str(paa)],capture_output=True,text=True);assert cmd.returncode==0 and paa.exists(),(name,cmd.stdout,cmd.stderr)
 check=decoded/(name+'.png');cmd=subprocess.run([str(tool),str(paa),str(check)],capture_output=True,text=True);assert cmd.returncode==0 and check.exists()
 got=np.array(Image.open(check).convert('RGBA'));assert got.shape==before.shape
 core=np.zeros(wet.shape,bool);core[64:448,64:448]=True;core&=(xx<12282)&(zz<12282)&(zz>0)
 deep=core&wet&(distance_transform_edt(wet)>=4)
 bad=deep&(got[:,:,:3].max(axis=2)>8)
 controls=None
 if deep.any():
  r,c=np.argwhere(deep)[0];mutant=got.copy();mutant[r,c,:3]=[255,0,0]
  controls=bool((deep&(mutant[:,:,:3].max(axis=2)>8)).sum()==bad.sum()+1) if not bad[r,c] else None
 return dict(tile=[a,b],changed_source_pixels=int((core&np.any(after!=before,axis=2)).sum()),wet_pixels=int((core&wet).sum()),source_wet_not_gravel=int((core&wet&(after[:,:,:3].max(axis=2)>0)).sum()),compiled_interior_pixels=int(deep.sum()),compiled_interior_non_gravel=int(bad.sum()),compiled_all_wet_non_gravel=int((core&wet&(got[:,:,:3].max(axis=2)>8)).sum()),negative_control=controls,source_sha256=sha(source/(name+'.png')),png_sha256=sha(png),paa_sha256=sha(paa),decoded_sha256=sha(check))
if __name__=='__main__':
 reports=[]
 with ThreadPoolExecutor(max_workers=4) as ex:
  for i,r in enumerate(ex.map(work,[(a,b) for a in range(32) for b in range(32)])):
   reports.append(r)
   if i%128==127:print(f'{i+1}/1024 masks repaired and round-tripped',flush=True)
 # Adjacent 128px overlap must remain bit-identical for every full-resolution source mask.
 overlaps=0
 for a in range(32):
  for b in range(32):
   arr=np.array(Image.open(out/f'm_{a:03d}_{b:03d}_lca.png'))
   if a<31:
    right=np.array(Image.open(out/f'm_{a+1:03d}_{b:03d}_lca.png'));assert np.array_equal(arr[:,384:],right[:,:128]);overlaps+=1
   if b<31:
    below=np.array(Image.open(out/f'm_{a:03d}_{b+1:03d}_lca.png'));assert np.array_equal(arr[384:],below[:128]);overlaps+=1
 counts={k:sum(r[k] for r in reports) for k in ['changed_source_pixels','wet_pixels','source_wet_not_gravel','compiled_interior_pixels','compiled_interior_non_gravel','compiled_all_wet_non_gravel']}
 gates=dict(no_wet_source_mismatch=counts['source_wet_not_gravel']==0,no_compiled_interior_mismatch=counts['compiled_interior_non_gravel']==0,negative_controls=all(r['negative_control'] is not False for r in reports) and any(r['negative_control'] for r in reports),overlaps=overlaps==1984)
 result=dict(status='PASS_MASK_ALIGNMENT_SOURCE_AND_COMPILED_INTERIORS' if all(gates.values()) else 'FAIL_MASK_ALIGNMENT',gates=gates,counts=counts,overlap_pairs=overlaps,dry_source_pixels_changed=0,alpha_preserved=True,inputs={str(f):sha(f) for f in [terrain,field,tool]},tiles=reports)
 (B/'mask-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='tiles'},indent=2));assert all(gates.values())
