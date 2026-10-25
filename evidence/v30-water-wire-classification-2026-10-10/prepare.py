from pathlib import Path
import sys,hashlib,json,subprocess,shutil
B=Path(__file__).parent
OLD=Path('E:/DayZ-Baltic-Build/v30-native-render-diagnostic-20261009')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=B/'baltic_render_probe_v2';(src/'scripts/5_Mission').mkdir(parents=True,exist_ok=False)
for rel in ['config.cpp','scripts/5_Mission/BalticRenderProbe.c']:
    old=(OLD/'baltic_render_probe_v1'/rel).read_text()
    new=old.replace('baltic_render_probe_v1','baltic_render_probe_v2').replace('BalticRenderProbeV1','BalticRenderProbeV2').replace('BALTIC_RENDER_PROBE_V1','BALTIC_RENDER_PROBE_V2')
    (src/rel).write_text(new,encoding='utf-8')
    assert new.replace('baltic_render_probe_v2','baltic_render_probe_v1').replace('BalticRenderProbeV2','BalticRenderProbeV1').replace('BALTIC_RENDER_PROBE_V2','BALTIC_RENDER_PROBE_V1')==old
readids=(OLD/'read_live_ids.py').read_text().replace('baltic_render_probe_v1','baltic_render_probe_v2')
(B/'read_live_ids.py').write_text(readids,encoding='utf-8')
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(src/'scripts')],capture_output=True,text=True)
(B/'lint.json').write_text(lint.stdout,encoding='utf-8');v=json.loads(lint.stdout)
assert lint.returncode==0 and v['info']['files_scanned']==1 and not v['errors'],v
t=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools')
subprocess.run([str(t/'Bin/CfgConvert/CfgConvert.exe'),'-bin','-dst',str(src/'config.bin'),str(src/'config.cpp')],check=True,capture_output=True)
out=B/'packed';out.mkdir(exist_ok=False)
subprocess.run([str(t/'Bin/PboUtils/FileBank.exe'),'-property','prefix='+src.name,'-dst',str(out),str(src)],check=True,capture_output=True)
pbo=out/(src.name+'.pbo');_,_,entries=read_pbo(pbo)
assert entries['config.bin']==(src/'config.bin').read_bytes()
k=next(k for k in entries if k.lower().endswith('balticrenderprobe.c'));assert entries[k]==(src/'scripts/5_Mission/BalticRenderProbe.c').read_bytes()
dest=Path('P:/Mods/@BalticRenderProbeV2/Addons');dest.mkdir(parents=True,exist_ok=False)
shutil.copyfile(pbo,dest/pbo.name);assert sha(pbo)==sha(dest/pbo.name)
mapfiles={p.name:sha(p) for p in Path('P:/Mods/@DayZ_Baltic_BaseSurfacePreviewV1/Addons').glob('*.pbo')}
assert set(mapfiles.values())=={'a08b96a1f952edca98e525221ed48790051291b8fcc9db7cc7661ea8bacc1335','3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'}
profile=Path('P:/DayZ_MCP_dev/_client/profiles/Users/Dev/guill_settings.DayZProfile')
for name in ['baltic_render_probe_v2.ids','baltic_render_probe_v2.phase']:
    assert not (Path('P:/DayZ_MCP_dev/_client/profiles')/name).exists()
result=dict(status='DIAGNOSTIC_PREPARED_NOT_RUN',map_files=mapfiles,profile_sha256=sha(profile),pbo_sha256=sha(pbo),source_files={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()},logic_exact_except_isolated_names=True)
(B/'inputs.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
