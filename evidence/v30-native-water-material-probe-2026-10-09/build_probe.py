from pathlib import Path
import hashlib,json,shutil,subprocess,sys
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/playtest'));from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=B/'baltic_native_water_probe_v1'
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(src/'scripts')],capture_output=True,text=True)
parsed=json.loads(lint.stdout);(B/'lint.json').write_text(lint.stdout)
assert lint.returncode==0 and parsed['info']['files_scanned']==1 and not parsed['errors'],parsed
toolroot=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools')
subprocess.run([str(toolroot/'Bin/CfgConvert/CfgConvert.exe'),'-bin','-dst',str(src/'config.bin'),str(src/'config.cpp')],check=True,capture_output=True)
out=B/'packed';out.mkdir(exist_ok=False)
subprocess.run([str(toolroot/'Bin/PboUtils/FileBank.exe'),'-property','prefix='+src.name,'-dst',str(out),str(src)],check=True,capture_output=True)
pbo=out/(src.name+'.pbo');_,_,entries=read_pbo(pbo)
assert entries['config.bin']==(src/'config.bin').read_bytes()
scriptkey=next(k for k in entries if k.lower().endswith('balticnativewaterprobe.c'))
assert entries[scriptkey]==(src/'scripts/5_Mission/BalticNativeWaterProbe.c').read_bytes()
dest=Path('P:/Mods/@BalticNativeWaterProbeV1/Addons');dest.mkdir(parents=True,exist_ok=False)
shutil.copyfile(pbo,dest/pbo.name);assert sha(pbo)==sha(dest/pbo.name)
result=dict(status='DIAGNOSTIC_ONLY_NOT_FOR_MAP_RELEASE',mod=str(dest.parent),pbo_sha256=sha(pbo),lint_files=1,
 source_files={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()},
 map_files={p.name:sha(p) for p in Path('P:/Mods/@DayZ_Baltic_TerminalContourV1/Addons').glob('*.pbo')},
 native_materials={p.name:sha(p) for p in Path('P:/Graphics/Materials/water').glob('oceanold*.emat')},
 limits=['Does not change world config, tide, terrain, ponds or vanilla materials.','Native handles and SetParam success do not prove active rendering.'])
(B/'reference.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
