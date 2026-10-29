from pathlib import Path
import importlib.util,json,copy,time
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c-local-author-20261029'
s=importlib.util.spec_from_file_location('fixture',D/'test_probe_road_compile_c1c.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
t=m.Tests();t.setUp();rows=[]
try:
 t.receipt['identities']['999']=time.time()-1
 rows.append({'case':'observed_identity_without_image','producer':t.gate(),'observer':m.V.arm_check(t.c,t.phase)['semantic_status'],'expected':'PROBE_INCONCLUSIVE_NOT_OBSERVED'})
 t.receipt['identities'].pop('999');t.receipt['observed_processes'][0]['argv']=['WRONG INPUT'];t.receipt['command']=['WRONG INPUT']
 rows.append({'case':'changed_command_still_accepted','producer':t.gate(),'observer':m.V.arm_check(t.c,t.phase)['semantic_status'],'expected':'ARG_BINDING'})
finally:t.tearDown()
(D/'integration-repro-R0.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows))
