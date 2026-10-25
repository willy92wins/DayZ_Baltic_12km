from pathlib import Path
import hashlib,json
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;O=R/'forest-boundary-full-f'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
assert not (O/'deployment.json').exists()
old=read(O/'points.json');p=read(O/'preparation-verification.json')
assert sha(O/'points.json')==p['current_manifest_sha256']=='d3c1b266ca20f8b12192037960c005a7c9d75092e352192b6b92fcd97ad2f356'
assert p['objects']==len(old['objects'])==3727 and p['points']==len(old['points'])==269968
assert old['mod_sha256']['narva_trial.pbo']=='4e5f909d2a27e9322299d751d2d54d67f5cc06700499d0498e533b5e1674ef38'
assert old['mod_sha256']['baltic_stream_pilot.pbo']=='c0be9abc9d36ee19c636325b825dbf09880a9dc31b5dfb8432e0f91d0e1cfa87'
assert old['mod_sha256']['baltic_water_v30.pbo']=='97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'
deployed={str(Path('P:/Mods/@DayZ_Baltic_EV112_RectangleF/Addons')/n):h for n,h in old['mod_sha256'].items()}
inputs={str(O/'points.json'):sha(O/'points.json'),**deployed}
mission=Path(old['mission'])
for name,key in [('init.c','init_sha256'),('points.csv','csv_sha256'),('identity.txt','identity_sha256')]:
    assert sha(mission/name)==old[key];inputs[str(mission/name)]=old[key]
inputs.update({str(W/n):h for n,h in p['source_hashes'].items()})
for path,h in inputs.items():assert sha(path)==h,path
doc=dict(status='PREPARED_NOT_RUN',deployed=deployed,inputs=inputs,mission=str(mission),manifest=str(O/'points.json'),survey_id=old['survey_id'],objects=3727,points=269968,manifest_unchanged=True,navmesh_data_server=True,mod='P:/Mods/@DayZ_Baltic_EV112_RectangleF',wrp_sha256='0139cd1a7ce360436e474fa6448470dfe93bf34a21229b6cf44f4e839af54126',limits=['Bootstrap surface measurement only, no navmesh/AI acceptance; F generation failed before this run.'])
(O/'deployment.json').write_text(json.dumps(doc,indent=2)+'\n')
for src,dst in [('orchestrate_forest_f.js','orchestrate_forest_bootstrap.js'),('finish_forest_f_probe.py','finish_forest_bootstrap.py')]:
    text=(R/src).read_text();text=text.replace('@DayZ_Baltic_EV112_RectangleFNavV9','@DayZ_Baltic_EV112_RectangleF')
    text=text.replace('navmesh_data_server:false','navmesh_data_server:true').replace('navmesh_data_server=False','navmesh_data_server=True').replace("assert not host['navmesh_data_server']", "assert host['navmesh_data_server']")
    text=text.replace('finish_forest_f_probe.py','finish_forest_bootstrap.py')
    assert not (R/dst).exists();(R/dst).write_text(text)
print(json.dumps(dict(status=doc['status'],objects=3727,points=269968,bootstrap=True)))
