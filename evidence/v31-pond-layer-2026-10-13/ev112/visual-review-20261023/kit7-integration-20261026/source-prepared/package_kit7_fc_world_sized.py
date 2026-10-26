"""Package a technical candidate; retained boundary uncertainty is never promoted."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/playtest'),str(W/'tools/navigation')]
from package_visual_forest_ev112 import source_arrays,compiled_arrays,compare
from attach_navmesh import read_pbo
from waterway_common import sample
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
S=R/'stage-kit7-fc-20261026';out=R/'package-kit7-fc-world-20261026';assert not out.exists()
gate=json.loads((R/'kit7-world-sized-unit-20261026/accepted.json').read_text());assert gate['status']=='ACCEPTED_TECHNICAL_WORLD_ONLY'
required=[Path(__file__),S/'stage-report.json',S/'forest-support-review-full.json',S/'independent-source-review.json',S/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp',R/'kit7-road-mesh-20261026.json',R/'package-rectangle-f/Addons/narva_trial.pbo',W/'tools/terrain/package_visual_forest_ev112.py',W/'tools/playtest/attach_navmesh.py']
required += [S/'baseline-config.cpp',W/'tools/terrain/compile_visual_pilot_ev112.ps1',Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/AddonBuilder/AddonBuilder.exe'),Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/packages/baltic-road-v29/tools/include.lst'),R/'package-kit7-fc-pilot-v2-20261026/Addons/baltic_stream_pilot.pbo',R/'package-kit7-fc-pilot-v2-20261026/verification.json',R/'kit7-context-unit-20261026/result.json',W/'tools/navigation/waterway_common.py',R/'prepare_kit7_world_compile.py',R/'run_kit7_world_unit.py']
assert all(Path(p).is_absolute() for p in gate['inputs']) and {str(p) for p in required}<=set(gate['inputs'])
assert all(sha(p)==h for p,h in gate['inputs'].items())
compile_receipt=json.loads((R/'kit7-world-sized-unit-20261026/compile.receipt.json').read_text())
assert compile_receipt['returncode']==0 and compile_receipt['inputs_unchanged'] and not compile_receipt['timeout']
assert sha(S/'out-sized/narva_trial.pbo')==compile_receipt['compiled_pbo_sha256']
src=S/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';sr=json.loads((S/'stage-report.json').read_text());fr=json.loads((S/'forest-support-review-full.json').read_text())
assert sha(src)==sr['wrp_sha256']==fr['source_wrp_sha256']
assert fr['status']=='INCONCLUSIVE_BOUNDARY_SUPPORT' and not any(fr['counts'].values()) and fr['boundary_pending']['count']==3727
assert json.loads((S/'independent-source-review.json').read_text())['status']=='PASS_INDEPENDENT_SOURCE_COMPOSITION'
assert json.loads((R/'kit7-road-mesh-20261026.json').read_text())['status']=='OFFLINE_MESH_PASS'
reference_path=Path(sr['forest_reference']['path']);assert sha(reference_path)==sr['forest_reference']['sha256'];reference=json.loads(reference_path.read_text())['models']
s=source_arrays(src,sr['object_count']);s['forest_models']=set(reference)
print('Source objects',len(s['ids']),flush=True)
compiled,_,new=read_pbo(S/'out-sized/narva_trial.pbo');anchor=dict(id=int(s['ids'][0]),name=s['names'][s['mi'][0]],matrix=s['mat'][0])
c,reader=compiled_arrays(new['baltic_trial.wrp'],anchor);parity=compare(s,c);assert parity['pilot_exact']==201
terrain=Path(sr['merged'])/'terrain-buried.npz';assert sha(terrain)==fr['terrain_sha256'];H=np.load(terrain)['heights'].astype(float)
for row in parity['forest_y_rounding']:
    m=np.array(row['compiled']);root=m[9:]-m[:9].reshape(3,3).T@np.array(reference[row['model']]['bc'])
    row['compiled_root_error_m']=float(root[1]-sample(H,np.array([root[0]+200000]),np.array([root[2]]))[0]);assert abs(row['compiled_root_error_m'])<=.005
    assert row['source'][:10]==row['compiled'][:10] and row['source'][11]==row['compiled'][11]
print('Compiled object parity',parity['objects'],parity['pilot_exact'],flush=True)
take=np.arange(min(1000,len(s['ids'])));small={k:(v[take].copy() if k in ('ids','mi','mat') else v) for k,v in s.items()};negatives={}
for test in ('missing','extra','moved'):
    bad={k:(v.copy() if isinstance(v,np.ndarray) else v) for k,v in small.items()}
    if test=='missing':
        for key in ('ids','mi','mat'):bad[key]=bad[key][1:]
    elif test=='extra':
        for key in ('ids','mi','mat'):bad[key]=np.concatenate([bad[key],bad[key][:1]])
        bad['ids'][-1]=int(s['ids'].max())+1
    else:bad['mat'][0,10]+=.1
    try:compare(small,bad)
    except AssertionError:negatives[test]=True
    else:negatives[test]=False
assert all(negatives.values());del s,c
baseline=R/'package-rectangle-f/Addons/narva_trial.pbo';assert sha(baseline)=='4e5f909d2a27e9322299d751d2d54d67f5cc06700499d0498e533b5e1674ef38'
raw,props,before=read_pbo(baseline);out.mkdir();(out/'config.bin').write_bytes(new['config.bin'])
assert new['config.bin']==before['config.bin'],'compiled world config differs from F'
converter='C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe'
p=subprocess.run([converter,'-txt','-dst',str(out/'config.cpp'),str(out/'config.bin')],capture_output=True);(out/'decode.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
updated=(out/'config.cpp').read_text(encoding='utf-8-sig');original=(S/'baseline-config.cpp').read_text(encoding='utf-8-sig');assert updated.count('"Baltic_Stream_Pilot"')==1
assert re.sub(r'\s+','',re.sub(r',\s*"Baltic_Stream_Pilot"','',updated))==re.sub(r'\s+','',original)
expected=dict(before)
expected['baltic_trial.wrp']=new['baltic_trial.wrp']
folder=out/'compiled/narva_trial';folder.mkdir(parents=True);dest=out/'Addons';dest.mkdir()
for name,data in expected.items():
    path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
bank='C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe';argv=[bank]
for key,value in props.items():argv+=['-property',key+'='+value]
p=subprocess.run(argv+['-dst',str(dest),str(folder)],capture_output=True);(out/'filebank.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
packed,finalprops,final=read_pbo(dest/'narva_trial.pbo');assert final==expected and all(finalprops.get(k)==v for k,v in props.items())
assert all(sha(p)==h for p,h in gate['inputs'].items()),'world input drift'
report=dict(status='OBJECTS_AND_PAYLOAD_VERIFIED_BOUNDARY_PENDING',forest_status=fr['status'],boundary_discs_pending=3727,objects=parity,reader=reader,negative_controls=negatives,source_wrp_sha256=sha(src),compiled_pbo_sha256=sha(S/'out-sized/narva_trial.pbo'),pbo_sha256=sha(dest/'narva_trial.pbo'),wrp_sha256=hashlib.sha256(final['baltic_trial.wrp']).hexdigest(),entries_unchanged=len(before)-1,changed_entries=['baltic_trial.wrp'],old_navmesh_preserved_but_not_accepted=True,sources={str(path):sha(path) for path in (Path(__file__),W/'tools/terrain/package_visual_forest_ev112.py',W/'tools/playtest/attach_navmesh.py',W/'tools/navigation/waterway_common.py')},limits=['Technical candidate only. Boundary forest status remains INCONCLUSIVE, not PASS.','OPRW table discovery is heuristic, heights not decoded; motor evidence required.','Native collision/water/forest, visual, regenerated navigation and performance acceptance remain pending.'])
(out/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
