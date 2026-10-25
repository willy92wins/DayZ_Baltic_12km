from pathlib import Path
import hashlib,json,shutil,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/terrain'))
from v30_common import tri_sample
from verify_channel_reaches_v30 import retained_pond_surface
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
oldref=json.loads((ROOT/'evidence/v30-continuation-2026-10-08/gap-reference.json').read_text())
source=ROOT/'missions/BalticJunctionProbeV1.BalticTrial'
assert all(sha(source/n)==v for n,v in oldref['files'].items())
mission=ROOT/'missions/BalticHighBedProbeV1.BalticTrial';mission.mkdir()
code=(source/'init.c').read_text().replace('junction_probe_v1.log','high_bed_probe_v1.log').replace('junction_order_v1.log','high_bed_order_v1.log')
(mission/'init.c').write_text(code,encoding='utf-8',newline='\n')
points=[(4001,1992.,6432.),(4002,1836.,6384.),(4003,2210.,7082.)]
(mission/'points.csv').write_text(''.join(f'{i};{x:.9f} 0 {z:.9f}\n' for i,x,z in points),encoding='utf-8')
terrain=Path('E:/DayZ-Baltic-Build/v30-navigation-contract-20261008/terrain_floor.npz');h=np.load(terrain)['heights'].astype(float)
fit=Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2');manifest=json.loads((fit/'water/pieces.json').read_text())
rows=[]
for i,x,z in points:
    plane,models=retained_pond_surface(fit,manifest,x,z);ground=float(tri_sample(h,x,z))
    assert plane is not None and plane-ground>(.95 if i!=4003 else .5)
    rows.append(dict(id=i,x=x,z=z,expected_ground_m=ground,role='raised_high_bed' if i!=4003 else 'unchanged_pond_control',
                     actual_pond_level_m=plane,models=models))
ref=dict(oldref,points=rows,files={p.name:sha(p) for p in mission.iterdir()},terrain_sha256=sha(terrain),
         limits=['Two repaired high beds and an unchanged pond, 62 samples each; no maximum-wave envelope.'])
lint=subprocess.run([sys.executable,'-X','utf8','C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(mission)],capture_output=True,text=True)
j=json.loads(lint.stdout);assert lint.returncode==0 and not j['errors'] and j['info']['files_scanned']==1
(OUT/'probe-lint.json').write_text(lint.stdout,encoding='utf-8')
deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
shutil.copytree(mission,deployed);assert all(sha(deployed/n)==v for n,v in ref['files'].items())
(OUT/'probe-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
print(json.dumps(rows,indent=1))
