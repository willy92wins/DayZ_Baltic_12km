from pathlib import Path
import ast,hashlib,json,shutil
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-native-water-material-probe-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[]
for p in list(B.glob('*.py'))+list(B.glob('*.json'))+list((B/'baltic_native_water_probe_v1').rglob('*.c'))+list((B/'baltic_native_water_probe_v1').glob('*.cpp'))+list((B/'views').rglob('*.jpg')):
 if p.suffix=='.py':ast.parse(p.read_text())
 q=E/p.relative_to(B);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);assert sha(p)==sha(q);files.append(str(q.relative_to(E)))
p=Path('P:/DayZ_MCP_dev/_client/profiles/baltic_native_water_probe_v1.log');q=E/'runtime.log';shutil.copyfile(p,q);files.append(q.name)
lines=q.read_text().splitlines();assert lines[0]=='BALTIC_NATIVE_WATER_PROBE_V1'
phases=[int(line.split(';')[1]) for line in lines if line.startswith('PHASE;')]
assert phases==[0,1,2,3,9,2,9],phases
assert any('CONTROL_INDEX;glow;BloomIntensity;16;missing;-1'==line for line in lines)
assert all('true' in line or line.endswith(';null') for line in lines if line.startswith('APPLY;'))
result=dict(status='ACTIVE_MATERIAL_RESPONSE_CONFIRMED_RESIDUAL_NOT_RESOLVED',phases=phases,positive_control='NormalPower=0 visibly removes native water normal waves; reset restores them.',
 wetfloor='WetFloor=0 changes legitimate shoreline shading, response is not detectable over natural variation at the calibrated dry residual centre.',
 samplemap='Native material handle null; no mutation on that handle.',
 outcome='No production material change. All values reset before orderly close. This diagnostic route is closed without a fix.',
 limits=['The original residual was not strongly reproduced at its calibrated centre during this series.','Thus no exclusion of every WetFloor contribution at every time or distance.','Three related materials changed together; active individual resource identity not isolated.','No water-phase synchronization or global pixel classifier.'],
 files={name:sha(E/name) for name in files})
(E/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],files=len(files),phases=phases)))
