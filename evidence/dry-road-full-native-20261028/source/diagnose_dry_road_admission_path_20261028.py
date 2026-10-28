from pathlib import Path
import ast,ntpath,unicodedata,json,hashlib
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');S=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_MCP_dev/tools/dayz_mcp/dayz_test_request.py')
source=S.read_text(encoding='utf-8');tree=ast.parse(source)
names={'_bounded_text','_valid_unicode_tree','_valid_local_absolute_path','_path_is_within'}
chosen=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(chosen)==4
scope={'ntpath':ntpath,'unicodedata':unicodedata}
exec(compile(ast.Module(body=chosen,type_ignores=[]),str(S),'exec'),scope)
dep=json.loads((R/'dry-road-full-native-20261028/deployment.json').read_text())
mission=dep['units']['calibration']['mission'];bad=mission.replace('\\','/')
assert not scope['_valid_local_absolute_path'](bad)
assert scope['_valid_local_absolute_path'](mission)
out=R/'dry-road-full-native-20261028/calibration/admission-path-diagnostic.json'
assert not out.exists()
out.write_text(json.dumps(dict(status='CALLER_PATH_TRANSFORMATION_REJECTED',source=str(S),source_sha256=hashlib.sha256(S.read_bytes()).hexdigest(),anchors=dict(valid_local_absolute_path=254,mission_not_allowed=484),sealed_mission=mission,transformed_mission=bad,canonical_accepted=True,transformed_accepted=False,limits=['Actual pure path predicate extracted and executed; no launcher, credential or daemon invoked.','Root membership policy not reconfigured or bypassed.'],correction='Use the exact gate JSON mission field, with no manual reconstruction or slash conversion.'),indent=2)+'\n',encoding='utf-8')
print(out)

