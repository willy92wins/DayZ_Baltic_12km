"""One-use B1 deploy/gate/consume, with explicit independent-review authorization."""
from pathlib import Path
import sys,json,shutil,time
R=Path(__file__).resolve().parent
W=Path("C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c")
sys.path.insert(0,str(W/'tools/quality'))
import water_query_native_b1_ev112 as b
O=R/'water-query-b1-native-20261028'
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
mode=sys.argv[1]
if mode=='prepare':
    started=time.monotonic()
    M=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticWaterQueryB1.BalticTrial')
    MOD=Path('P:/Mods/@DayZ_Baltic_EV112_WaterB1')
    b.require(not O.exists() and not M.exists() and not MOD.exists(),'fresh_targets')
    approval=R/'water-query-b1-binding-adjudicated-20261028.json';a=b.read(approval)
    b.require(a['status']=='REVIEWED_B1_PREPARATION_READY','review_required');b.verify(a['inputs'])
    F=R/'water-query-b1-final-offline-20261028';f=b.read(F/'report.json');b.verify(f['inputs'])
    b.require(f['status']=='OFFLINE_CONTRACT_VALIDATED_NOT_READY_FOR_DAYZ' and f['tests']==26 and f['lint_files']==1,'offline_gate')
    b.require(b.sha(F/'points.csv')==f['csv_sha256'] and b.sha(F/'points.json')==f['points_sha256'],'offline_data_drift')
    old=b.read(R/'dry-road-full-native-20261028/deployment.json');pre=b.read(R/'dry-road-full-native-20261028/prelaunch.json')
    b.verify(old['deployed']);b.verify({pre['executable']:pre['executable_sha256'],pre['bridge_pbo']:pre['bridge_sha256']})
    O.mkdir();M.mkdir();(MOD/'Addons').mkdir(parents=True)
    packages={}
    for p,h in old['deployed'].items():
        dest=MOD/'Addons'/Path(p).name;shutil.copyfile(p,dest);b.require(b.sha(dest)==h,'copy_drift');packages[str(dest)]=h
    packages[pre['bridge_pbo']]=pre['bridge_sha256']
    shutil.copyfile(W/'missions/BalticWaterQueryB1.BalticTrial/init.c',M/'init.c')
    shutil.copyfile(F/'points.csv',M/'points.csv')
    selected=R/'dry-road-native-discriminators-a-20261028/selected-points.json'
    original=R/'dry-road-full-native-20261028/probe/result.json'
    pins={**a['inputs'],**f['inputs'],**packages}
    for p in [approval,F/'report.json',F/'points.csv',F/'points.json',M/'init.c',M/'points.csv',Path(pre['executable']),Path(__file__).resolve()]:pins[str(p)]=b.sha(p)
    d=dict(status='PREPARED_NOT_ADMITTED',mission=str(M),mod=MOD.name,producer=str(M/'init.c'),csv=str(M/'points.csv'),selected=str(selected),original=str(original),engine=pre['executable'],packages=packages,inputs=pins,seconds=time.monotonic()-started)
    b.check_csv((M/'points.csv').read_text(encoding='ascii'),b.source_points(b.read(selected),b.read(original)))
    b.verify(pins);b.require(d['seconds']<120,'preparation_budget')
    dump(O/'deployment.json',d);print(json.dumps({k:d[k] for k in ('status','mission','mod','seconds')}))
elif mode=='gate':
    print(json.dumps(b.gate(O,sys.argv[2])))
elif mode=='consume':
    result=b.consume_bound(O,sys.argv[2]);dump(O/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('details','inputs','reference_mismatches','confounders')}))
else:raise ValueError('mode')
