from pathlib import Path
import hashlib,json,sys,subprocess,shutil,re
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check=json.loads((B/'surface-verification.json').read_text());assert check['status']=='PASS_COMPLETE_SURFACE_SOURCE_COMPILED'
baseline=Path('P:/Mods/@DayZ_Baltic_HingeSmoothV1/Addons/narva_trial.pbo')
assert sha(baseline)=='9eb9f4006c55e3ed3f73461816bed0272e8ab5fdc2f0ca58e214687ef0b82ee5'
raw,props,before=read_pbo(baseline);del raw
stage=B/'package/narva_trial';stage.mkdir(parents=True,exist_ok=False)
changed=[];replaced={'s':0,'m':0}
for name,data in before.items():
    dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True)
    match=re.search(r'(?:^|/)([sm])_\d{3}_\d{3}_lc[oa]\.paa$',name,re.I)
    if match:
        replacement=B/'surface/layers'/Path(name).name.lower();assert replacement.is_file()
        candidate=replacement.read_bytes();replaced[match.group(1).lower()]+=1
        if candidate!=data:changed.append(name)
        dest.write_bytes(candidate)
    else:dest.write_bytes(data)
assert replaced=={'s':1024,'m':1024} and changed
out=B/'packed';out.mkdir(exist_ok=False)
cmd=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
for k,v in props.items():cmd+=['-property',k+'='+v]
done=subprocess.run(cmd+['-dst',str(out),str(stage)],capture_output=True,text=True)
(B/'filebank.log').write_text(done.stdout+'\n'+done.stderr);assert done.returncode==0
pbo=out/'narva_trial.pbo';raw,actualprops,after=read_pbo(pbo);del raw
assert props==actualprops and set(before)==set(after)
actual=sorted(name for name in before if before[name]!=after[name]);assert actual==sorted(changed)
assert all(re.search(r'(?:^|/)[sm]_\d{3}_\d{3}_lc[oa]\.paa$',name,re.I) for name in actual)
water=baseline.parent/'baltic_water_v30.pbo'
assert sha(water)=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
assert hashlib.sha256(after['baltic_trial.wrp']).hexdigest()=='cfcbbd0c70b75a8e82824343905b16c4d43431ecca32b4fe9b722ac802c38fab'
target=Path('P:/Mods/@DayZ_Baltic_CurrentSurfaceV1/Addons');target.mkdir(parents=True,exist_ok=False)
for source in [pbo,water]:
    shutil.copyfile(source,target/source.name);assert sha(source)==sha(target/source.name)
result=dict(status='DEPLOYED_CURRENT_SURFACE_PREVIEW',mod=str(target.parent),files={source.name:sha(source) for source in [pbo,water]},
    baseline_world_sha256=sha(baseline),terrain_sha256='fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6',
    compiled_wrp_sha256=hashlib.sha256(after['baltic_trial.wrp']).hexdigest(),surface_verification_sha256=sha(B/'surface-verification.json'),
    changed_entries=actual,changed_satellites=sum(Path(n).name.startswith('s_') for n in actual),changed_masks=sum(Path(n).name.startswith('m_') for n in actual),
    unchanged_entries=len(before)-len(actual),total_entries=len(before),all_nontexture_entries_exact=True,archive_properties=props,
    limits=['EV25 terrain/objects and water PBO exact; no new physical traversal claimed.','Runtime load and distance checks pending.','No TB/navmesh acceptance or native residual fix claimed.'])
(B/'deploy.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='changed_entries'},indent=2))
