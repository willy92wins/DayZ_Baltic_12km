from pathlib import Path
import hashlib,json,shutil,subprocess,sys
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/playtest'));from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=B/'baltic_render_probe_v1'
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(src/'scripts')],capture_output=True,text=True)
parsed=json.loads(lint.stdout);(B/'lint.json').write_text(lint.stdout)
assert lint.returncode==0 and parsed['info']['files_scanned']==1 and not parsed['errors'],parsed
toolroot=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools')
subprocess.run([str(toolroot/'Bin/CfgConvert/CfgConvert.exe'),'-bin','-dst',str(src/'config.bin'),str(src/'config.cpp')],check=True,capture_output=True)
out=B/'packed';out.mkdir(exist_ok=False)
subprocess.run([str(toolroot/'Bin/PboUtils/FileBank.exe'),'-property','prefix='+src.name,'-dst',str(out),str(src)],check=True,capture_output=True)
pbo=out/(src.name+'.pbo');_,_,entries=read_pbo(pbo)
assert entries['config.bin']==(src/'config.bin').read_bytes()
scriptkey=next(k for k in entries if k.lower().endswith('balticrenderprobe.c'))
assert entries[scriptkey]==(src/'scripts/5_Mission/BalticRenderProbe.c').read_bytes()
dest=Path('P:/Mods/@BalticRenderProbeV1/Addons');dest.mkdir(parents=True,exist_ok=False)
shutil.copyfile(pbo,dest/pbo.name);assert sha(pbo)==sha(dest/pbo.name)
mapfiles={p.name:sha(p) for p in Path('P:/Mods/@DayZ_Baltic_TerminalContourV1/Addons').glob('*.pbo')}
assert set(mapfiles.values())=={'c06f9b52d0b31d5c6e5cd3ec6c8cb14055abbe3ae40163092403b5ac66ca88fe','3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'}
for name in ['baltic_render_probe_v1.ids','baltic_render_probe_v1.phase']:
 assert not (Path('P:/DayZ_MCP_dev/_client/profiles')/name).exists()
result=dict(status='ISOLATED_RENDER_DIAGNOSTIC_ONLY',mod=str(dest.parent),pbo_sha256=sha(pbo),lint_files=1,source_files={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()},map_files=mapfiles,limits=['IDs must be read-only verified from the live client registry before any mutation.','No process memory writes, hooks or injected code; only exposed DiagMenu API setters.','Initial phase is untouched; auto-restoration after 1200 seconds.'])
(B/'reference.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
