from pathlib import Path
import hashlib,json,shutil,subprocess,sys,copy
import numpy as np
import rasterio
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-current-physical-consumers-2026-10-09'
sys.path.insert(0,str(W/'tools/navigation'));from waterway_common import sample
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
terrain=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/candidate/terrain.npz')
assert sha(terrain)=='70f74c9334620c458880f728d3ff15cec7867ffe2bd8bd2e9d5135e1692b7ed5'
h=np.load(terrain)['heights'];asc=B/'current-reference.asc'
with asc.open('x',encoding='ascii',newline='\n') as f:
 f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n');np.savetxt(f,h,fmt='%.9g')
with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),h)
mapfiles={str(p):sha(p) for p in Path('P:/Mods/@DayZ_Baltic_TerminalContourV1/Addons').glob('*.pbo')}
assert sorted(mapfiles.values())==sorted(['c06f9b52d0b31d5c6e5cd3ec6c8cb14055abbe3ae40163092403b5ac66ca88fe','3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'])
reports=[]
for kind,refname,missionname in [('boat','v30-bounded-integration-2026-10-08/boat-reference.json','BalticCurrentBoatV1.BalticTrial'),('drive','v30-bug-recheck-2026-10-08/drive-reference.json','BalticCurrentDriveV1.BalticTrial')]:
 old=W/'evidence'/refname;ref=copy.deepcopy(json.loads(old.read_text()))
 for path,digest in ref['mission'].items():assert sha(Path(path))==digest,(path,'source changed')
 source=Path(ref['deployed_mission']);assert source.is_dir()
 for path,digest in ref['mission'].items():assert sha(source/Path(path).name)==digest
 input_path=Path('P:/Mods/@BalticBoatInputProbe/Addons/baltic_boat_input.pbo') if kind=='boat' else Path('P:/Mods/@BalticDriveInputProbe/Addons/baltic_drive_input.pbo')
 assert sha(input_path)==ref['deployment'][str(input_path).replace('\\','/')] if str(input_path).replace('\\','/') in ref['deployment'] else sha(input_path) in ref['deployment'].values()
 newlog='baltic_current_'+kind+'_v1.log';oldlog=ref.get('log',ref.get('log_name'))
 code=(source/'init.c').read_text();assert code.count(oldlog)==1;code=code.replace(oldlog,newlog)
 local=B/'missions'/missionname;local.mkdir(parents=True,exist_ok=False)
 (local/'init.c').write_text(code,encoding='utf-8',newline='\n')
 if kind=='boat':shutil.copyfile(source/'routes.csv',local/'routes.csv')
 else:
  for case in ref['cases']:
   route=np.array(case['route_xyz'],dtype=np.float32);route[:,1]=sample(h,route[:,0].astype(float)+200000,route[:,2].astype(float));case['route_xyz']=route.tolist()
  (local/'routes.csv').write_text(''.join(f"{case['case']};{i};{p[0]:.9g};{p[1]:.9g};{p[2]:.9g}\n" for case in ref['cases'] for i,p in enumerate(case['route_xyz'])),encoding='ascii')
 lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(local)],capture_output=True,text=True)
 parsed=json.loads(lint.stdout);(E/(kind+'-lint.json')).write_text(lint.stdout);assert lint.returncode==0 and parsed['info']['files_scanned']==1 and not parsed['errors']
 deployed=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/missionname;assert not deployed.exists();shutil.copytree(local,deployed)
 ref.update(status='FROZEN_EV16_BEFORE_RUNTIME',terrain=str(asc),terrain_sha256=sha(asc),deployed_mission=str(deployed),mission={str(p):sha(p) for p in local.iterdir()},deployment=mapfiles|{str(input_path):sha(input_path)},inputs={str(old):sha(old),str(terrain):sha(terrain),str(Path(__file__)):sha(Path(__file__))},scope='Fresh consumer on EV16. Historical routes, water levels, controller and thresholds unchanged.')
 if kind=='boat':ref['log']=newlog
 else:ref['log_name']=newlog;ref['route_geometry_historical_only']=ref.pop('route_geometry',None)
 assert ref['criteria']==json.loads(old.read_text())['criteria']
 for p,digest in ref['mission'].items():assert sha(deployed/Path(p).name)==digest
 out=E/(kind+'-reference.json');out.write_text(json.dumps(ref,indent=2)+'\n')
 reports.append(dict(kind=kind,mission=str(deployed),log=newlog,cases=len(ref['cases']),reference_sha256=sha(out),input_pbo_sha256=sha(input_path)))
(B/'preparation.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports,indent=2))
