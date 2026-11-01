from pathlib import Path
import importlib.util,tempfile,json,time
D=Path('E:/DayZ-Baltic-Build/shape-repair-20261025/road-c1c1-local-author-20261101');s=importlib.util.spec_from_file_location('v',D/'observe_road_compile_c1c1.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
with tempfile.TemporaryDirectory() as td:
 root=Path(td);(root/'phases').mkdir();start={'phase':'help','state':'STARTED','time':200,'command':['WRONG'],'logger_sha256':'0'*64};entry={'state':'CLOSED','start':start,'receipt':{'command':['RIGHT'],'started':100}};r={'phases':{'help':entry}}
 for name,obj in [('help.started.json',start),('help.closed.json',entry)]:(root/'phases'/name).write_text(json.dumps(obj))
 got=v.phase_state({'root':str(root)},r,'help');assert got=='CLOSED'
 result={'reproduced':True,'observed':got,'expected':'PHASE_BINDING','dimensions':['STARTED command differs from receipt command','STARTED time follows receipt start','logger hash unbound'],'scope':'synthetic journal function; not a native receipt or complete probe'}
 (D/'journal-repro-R0.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
