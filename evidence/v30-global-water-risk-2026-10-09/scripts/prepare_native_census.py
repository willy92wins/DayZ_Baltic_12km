from pathlib import Path
import hashlib,json,sys,shutil,subprocess
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');E=W/'evidence/v30-global-water-risk-2026-10-09'
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import tri_sample
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz')
assert sha(source)=='9c3011b8af5279e807630d4e91512d2e95a434463d3523a5b4074e70bc7cc8f6'
t=np.load(source);h=t['heights'];name='BalticNativeCensusV1.BalticTrial'
dst=B/'missions'/name;dst.mkdir(parents=True,exist_ok=False)
shutil.copyfile(B/'BalticNativeCensus.c',dst/'init.c')
with (dst/'grid.csv').open('w',newline='') as f:
    for r in range(2048):
        for c in range(0,2048,32):
            f.write(f'{r};{c};'+';'.join(format(float(v),'.9g') for v in h[r,c:c+32])+'\n')
rr,cc=np.nonzero((t['cls']==0)&(h<1.8-1e-5))
points=[dict(x=int(c*6),z=int(12282-r*6),expected_ground=float(h[r,c]),cls=0,role='low_dry_vertex') for r,c in zip(rr,cc)]
# Independent high controls distributed across the entire map, plus the calibrated user observation.
for r in range(16,2048,64):
    for c in range(16,2048,64):
        if t['cls'][r,c]==0 and h[r,c]>2:
            points.append(dict(x=int(c*6),z=int(12282-r*6),expected_ground=float(h[r,c]),cls=0,role='high_dry_control'))
for p in json.loads((E/'native-projection.json').read_text())['points']:
    x,_,z=p['world'];points.append(dict(x=x,z=z,expected_ground=float(tri_sample(h,x,z)),cls=p['cls'],role=p['name']))
with (dst/'risks.csv').open('w',newline='') as f:
    for i,p in enumerate(points):f.write(f"{i};{p['x']:.8f};{p['z']:.8f};{p['expected_ground']:.9g};{p['cls']}\n")
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(dst)],capture_output=True,text=True)
parsed=json.loads(lint.stdout);assert lint.returncode==0 and not parsed['errors'] and parsed['info']['files_scanned']==1,lint.stdout
(E/'native-census-lint.json').write_text(lint.stdout)
deploy=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/name
shutil.copytree(dst,deploy)
files={p.name:sha(p) for p in dst.iterdir()};assert all(sha(deploy/k)==v for k,v in files.items())
mods=Path('P:/Mods/@DayZ_Baltic_ValleySmoothC1R3P/Addons')
world=mods/'narva_trial.pbo';water=mods/'baltic_water_v30.pbo'
assert sha(world)=='75adb673ed23ab5b656a162063d6a89cbb2e0a0d99aba82263bf2a54a31e8623'
assert sha(water)=='542bd4e85e9f82d9ef373386371168c9b489c0794e3f4bd4773709c680c4b068'
ref=dict(mission=str(deploy),files=files,terrain_sha256=sha(source),vertices=2048**2,points=points,
    pbo={p.name:sha(p) for p in (world,water)},limits=['Server-native height and physical water only; rendering/LOD remains separate.'])
(B/'native-census-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
(E/'native-census-preparation.json').write_text(json.dumps({k:v for k,v in ref.items() if k!='points'},indent=2)+'\n')
shutil.copyfile(dst/'init.c',E/'BalticNativeCensus.c')
print(json.dumps(dict(mission=str(deploy),vertices=ref['vertices'],water_points=len(points),lint_files=1),indent=2))
