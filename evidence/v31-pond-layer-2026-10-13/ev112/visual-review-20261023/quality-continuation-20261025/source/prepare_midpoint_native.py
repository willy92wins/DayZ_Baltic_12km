from pathlib import Path
import hashlib,json,shutil
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;O=R/'runtime-midpoint-b'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
v=read(R/'package-midpoint-b/verification.json');assert v['status']=='PASS_27_MODELS_REPLACED_ALL_OTHER_ENTRIES_EXACT' and v['unchanged_models']==35
source=R/'runtime-rectangle-f/points.json';f=read(source);t=read(R/'probe-combined/points.json');assert len(f['points'])==4749 and len(t['points'])==2823
for p,q in zip(t['points'],f['points']):
    assert {k:z for k,z in p.items() if k!='ground'}=={k:z for k,z in q.items() if k!='ground'},p['id']
assert not O.exists();O.mkdir()
mod=Path('P:/Mods/@DayZ_Baltic_EV112_MidpointB');assert not mod.exists();(mod/'Addons').mkdir(parents=True)
deployed={}
for n,h in [('narva_trial.pbo','4e5f909d2a27e9322299d751d2d54d67f5cc06700499d0498e533b5e1674ef38'),('baltic_water_v30.pbo','97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'),('baltic_stream_pilot.pbo',v['pbo_sha256'])]:
    src=(R/'package-midpoint-b/Addons' if n=='baltic_stream_pilot.pbo' else Path('P:/Mods/@DayZ_Baltic_EV112_RectangleF/Addons'))/n
    assert sha(src)==h;dst=mod/'Addons'/n;shutil.copyfile(src,dst);assert sha(dst)==h;deployed[str(dst)]=h
for kind,oldmission,newmission,count in [('full','BalticRectangleF.BalticTrial','BalticMidpointB.BalticTrial',4749),('grid','BalticShapeRepairTRVGrid.BalticTrial','BalticMidpointBGrid.BalticTrial',300)]:
    out=O/kind;out.mkdir();base=Path('C:/temp/DayZ_MCP_130_dev/mpmissions');mission=base/newmission;assert not mission.exists();mission.mkdir()
    for n in ('init.c','points.csv'):
        shutil.copyfile(base/oldmission/n,mission/n);assert sha(mission/n)==sha(base/oldmission/n)
    inputs={str(mission/n):sha(mission/n) for n in ('init.c','points.csv')};inputs.update(deployed)
    if kind=='full':
        doc={**f,'inherited_inputs':f['inputs'],'inputs':{str(source):sha(source),**inputs}}
        (out/'points.json').write_text(json.dumps(doc,indent=2)+'\n')
    else:
        shutil.copyfile(R/'runtime-t-20261025/rv-grid-points.json',out/'points.json')
        assert len(read(out/'points.json')['points'])==300
    inputs[str(out/'points.json')]=sha(out/'points.json')
    receipt=dict(status='DEPLOYED_ISOLATED_PENDING_RUNTIME',kind=kind,points=count,mission=str(mission),mod=str(mod),deployed=deployed,inputs=inputs,navmesh_data_server=True,original_2823_retained_except_ground=True,limits=['Surface and RV/Bullet measurements only; no navigation, player contact or FPS acceptance.'])
    (out/'deployment.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(status='PREPARED',full=4749,grid=300,mod=str(mod))))
