from pathlib import Path
import hashlib,json,shutil,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/terrain'))
from v30_common import tri_sample
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=ROOT/'missions/BalticBugRecheckWaterV3.BalticTrial'
frozen=json.loads((OUT/'controls-reference.json').read_text())
assert all(sha(source/name)==value for name,value in frozen['files'].items())
mission=ROOT/'missions/BalticJunctionProbeV1.BalticTrial';mission.mkdir()
code=(source/'init.c').read_text().replace('water_v3.log','junction_probe_v1.log').replace('water_order_v3.log','junction_order_v1.log')
code=code.replace('m_Rows.Count() == 18','m_Rows.Count() == 3').replace(';302;2',';62;2').replace('END;302;18','END;62;3').replace('m_Sample == 151','m_Sample == 31').replace('m_Sample == 302','m_Sample == 62')
(mission/'init.c').write_text(code,encoding='utf-8',newline='\n')
points=[(3001,2207.64988128585,7080.7002374283),(3002,2207.5,7080.5),(3003,2210.,7082.)]
(mission/'points.csv').write_text(''.join(f'{i};{x:.9f} 0 {z:.9f}\n' for i,x,z in points),encoding='utf-8')
h=np.load('E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/wave-banks-r1/terrain_wave_banks.npz')['heights'].astype(float)
ref=dict(header=frozen['header'],fields=17,samples=62,interval_s=2,points=[dict(id=i,x=x,z=z,expected_ground_m=float(tri_sample(h,x,z)),role='gap_presence_observer' if i!=3003 else 'adjacent_pond_observer') for i,x,z in points],
         phase_schedule=[dict(name='calm',first=0,count=31),dict(name='storm',first=31,count=31)],
         files={p.name:sha(p) for p in mission.iterdir()},terrain_sha256=frozen['terrain_sha256'],
         limits=['Presence comparison at two gap points and one adjacent pond; depth recorded separately.',
                 'Two weather settings over 62 samples do not define maximum wave envelope.'])
lint=subprocess.run([sys.executable,'-X','utf8','C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(mission)],capture_output=True,text=True)
j=json.loads(lint.stdout);assert lint.returncode==0 and not j['errors'] and j['info']['files_scanned']==1
(OUT/'gap-lint.json').write_text(lint.stdout,encoding='utf-8')
deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/mission.name
shutil.copytree(mission,deployed);assert all(sha(deployed/n)==v for n,v in ref['files'].items())
(OUT/'gap-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
print(json.dumps(ref['points'],indent=1))
