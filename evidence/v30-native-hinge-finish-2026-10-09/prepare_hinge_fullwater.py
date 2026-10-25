"""New full native readback identity for the isolated global contour preview."""
from pathlib import Path
import json,shutil,subprocess,sys
import numpy as np
B=Path(__file__).parent;B13=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
sys.path.insert(0,str(B13));from discover_native_turns import W,sha
sys.path.insert(0,str(W/'tools/terrain'));from v30_common import tri_sample
E=W/'evidence/v30-native-hinge-finish-2026-10-09';E13=W/'evidence/v30-native-turn-optimizer-2026-10-09'
previous_path=E13/'native-contour-fullwater-reference.json';previous=json.loads(previous_path.read_text());old=Path(previous['mission'])
assert all(sha(old/name)==digest for name,digest in previous['files'].items())
deploy=json.loads((B/'deploy.json').read_text());mods=Path(deploy['destination'])/'Addons'
assert all(sha(mods/name)==digest for name,digest in deploy['files'].items())
source=B/'candidate/terrain.npz';assert sha(source)==deploy['terrain_sha256'];t=np.load(source);h=t['heights'];cls=t['cls']
name='BalticHingeSmoothFullWaterV1.BalticTrial';mission=B/'missions'/name;mission.mkdir(parents=True,exist_ok=False)
code=(old/'init.c').read_text().replace('BalticNativeContourFullWaterMission','BalticHingeSmoothFullWaterMission').replace('baltic_native_contour_fullwater_v1','baltic_hinge_smooth_fullwater_v1')
header='BALTIC_NATIVE_CONTOUR_FULLWATER_V1;BalticTrial;'+previous['terrain_sha256'];assert code.count(header)==1
code=code.replace(header,'BALTIC_HINGE_SMOOTH_FULLWATER_V1;BalticTrial;'+sha(source));(mission/'init.c').write_text(code)
with (mission/'grid.csv').open('w',newline='') as stream:
    for r in range(2048):
        for c in range(0,2048,32):
            fields=[]
            for j in range(c,c+32):fields.extend([format(float(h[r,j]),'.9g'),str(int(cls[r,j]))])
            stream.write(f'{r};{c};'+';'.join(fields)+'\n')
assert sha(mission/'grid.csv')!=previous['files']['grid.csv']
shutil.copyfile(old/'risks.csv',mission/'risks.csv')
errors=[abs(float(tri_sample(h,point['x'],point['z']))-point['expected_ground']) for point in previous['points']]
assert max(errors)<1e-7,errors
validator='C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py'
lint=subprocess.run([sys.executable,validator,str(mission)],capture_output=True,text=True);got=json.loads(lint.stdout)
assert lint.returncode==0 and got['info']['files_scanned']==1 and not got['errors'];(B/'native-fullwater-lint.json').write_text(lint.stdout)
destination=old.parent/name;shutil.copytree(mission,destination)
reference=dict(previous,mission=str(destination),terrain_sha256=sha(source),files={p.name:sha(p) for p in mission.iterdir()},
               pbo=deploy['files'],deployed={str(mods/name):digest for name,digest in deploy['files'].items()},
               source_runtime_reference_sha256=sha(previous_path),status='PREPARED_NOT_RUN')
assert all(sha(destination/name)==digest for name,digest in reference['files'].items())
(E/'hinge-smooth-fullwater-reference.json').write_text(json.dumps(reference,indent=2)+'\n')
verifier=(B13/'verify_native_contour_fullwater.py').read_text()
verifier=verifier.replace("E=W/'evidence/v30-native-turn-optimizer-2026-10-09'","E=W/'evidence/v30-native-hinge-finish-2026-10-09'")
verifier=verifier.replace('native-contour-fullwater','hinge-smooth-fullwater').replace('native-contour-physical','hinge-smooth-physical').replace('native-contour-unflagged','hinge-smooth-unflagged')
verifier=verifier.replace('baltic_native_contour_fullwater_v1','baltic_hinge_smooth_fullwater_v1').replace('BALTIC_NATIVE_CONTOUR_FULLWATER_V1','BALTIC_HINGE_SMOOTH_FULLWATER_V1')
oldsource="Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009/candidate-feasible/terrain.npz')";assert verifier.count(oldsource)==1
verifier=verifier.replace(oldsource,f"Path('{source.as_posix()}')")
(B/'verify_hinge_smooth_fullwater.py').write_text(verifier)
print(json.dumps(dict(status='PREPARED_NOT_RUN',mission=str(destination),terrain_sha256=sha(source),files=reference['files'],lint_files=1,protected_points_maximum_change=max(errors)),indent=2))
