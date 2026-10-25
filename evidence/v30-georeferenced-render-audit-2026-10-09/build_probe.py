from pathlib import Path
import hashlib,json,re,shutil,subprocess,sys
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=B/'baltic_projection_probe_v1'
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(src/'scripts')],capture_output=True,text=True)
(B/'lint.json').write_text(lint.stdout);parsed=json.loads(lint.stdout)
assert lint.returncode==0 and parsed['info']['files_scanned']==1 and not parsed['errors']
tools=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
call=subprocess.run([str(tools/'CfgConvert/CfgConvert.exe'),'-bin','-dst',str(src/'config.bin'),str(src/'config.cpp')],capture_output=True,text=True)
(B/'cfgconvert.log').write_text(call.stdout+'\n'+call.stderr);assert call.returncode==0
out=B/'packed';out.mkdir(exist_ok=False)
call=subprocess.run([str(tools/'PboUtils/FileBank.exe'),'-property','prefix='+src.name,'-dst',str(out),str(src)],capture_output=True,text=True)
(B/'filebank.log').write_text(call.stdout+'\n'+call.stderr);assert call.returncode==0
pbo=out/(src.name+'.pbo');_,_,entries=read_pbo(pbo)
assert entries['config.bin']==(src/'config.bin').read_bytes()
script=next(k for k in entries if k.lower().endswith('balticprojectionprobe.c'))
assert entries[script]==(src/'scripts/5_Mission/BalticProjectionProbe.c').read_bytes()
profile=Path('P:/DayZ_MCP_dev/_client/profiles/Users/Dev/guill_settings.DayZProfile');text=profile.read_text()
settings={key:float(re.search(r'^'+key+r'=([^;]+);',text,re.M).group(1)) for key in ['viewDistance','preferredObjectViewDistance','sceneComplexity','terrainGrid']}
assert settings['viewDistance']==settings['preferredObjectViewDistance']==1600
shutil.copyfile(profile,B/'profile-before.DayZProfile')
dest=Path('P:/Mods/@BalticProjectionProbeV1/Addons');dest.mkdir(parents=True,exist_ok=False)
shutil.copyfile(pbo,dest/pbo.name);assert sha(pbo)==sha(dest/pbo.name)
maps={p.name:sha(p) for p in Path('P:/Mods/@DayZ_Baltic_CurrentSurfaceV1/Addons').glob('*.pbo')}
assert set(maps.values())=={'b69265c5feb99d1bda7a5c9f02282818d0ffe4cd26f89f3a095c128e62d374f3','3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'}
report=dict(status='BUILT_CLIENT_READ_ONLY_PROJECTION_PROBE',mod=str(dest.parent),pbo_sha256=sha(pbo),settings=settings,profile_sha256=sha(profile),map_files=maps,lint_files=1)
(B/'reference.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
