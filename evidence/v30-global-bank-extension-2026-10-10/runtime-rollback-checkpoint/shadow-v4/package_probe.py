from pathlib import Path
import sys, subprocess, json, shutil, hashlib
R=Path(__file__).resolve().parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=R/'baltic_shadow_probe_v4';out=R/'packed'
dest=Path('P:/Mods/@BalticShadowProbeV4/Addons')
assert not out.exists() and not dest.exists()
world=Path('P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons/narva_trial.pbo')
water=world.with_name('baltic_water_v30.pbo')
assert sha(world)=='b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c'
assert sha(water)=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
profile=Path('P:/DayZ_MCP_dev/_client/profiles')
for ext in ['ids','phase','log']:
 assert not (profile/f'baltic_shadow_probe_v4.{ext}').exists()
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(source/'scripts')],text=True,capture_output=True,check=True)
(R/'lint-root.json').write_text(lint.stdout,encoding='utf-8')
v=json.loads(lint.stdout);assert v['info']['files_scanned']==1 and not v['errors']
t=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin')
subprocess.run([str(t/'CfgConvert/CfgConvert.exe'),'-bin','-dst',str(source/'config.bin'),str(source/'config.cpp')],check=True,capture_output=True)
out.mkdir()
packed=subprocess.run([str(t/'PboUtils/FileBank.exe'),'-property','prefix=baltic_shadow_probe_v4','-dst',str(out),str(source)],capture_output=True,text=True,check=True)
(R/'filebank.log').write_text(packed.stdout+'\n'+packed.stderr,encoding='utf-8')
pbo=out/'baltic_shadow_probe_v4.pbo';_,props,entries=read_pbo(pbo)
assert props['prefix']=='baltic_shadow_probe_v4'
assert entries['config.bin']==(source/'config.bin').read_bytes()
assert entries['scripts/5_Mission/BalticShadowProbeV4.c']==(source/'scripts/5_Mission/BalticShadowProbeV4.c').read_bytes()
dest.mkdir(parents=True);shutil.copyfile(pbo,dest/pbo.name);assert sha(dest/pbo.name)==sha(pbo)
prior=R/'previous-runtime-files';prior.mkdir()
for base in ['P:/DayZ_MCP_dev/_server/profiles','P:/DayZ_MCP_dev/_client/profiles']:
 p=Path(base)/'baltic_render_layer_v1.log'
 if p.is_file():shutil.copyfile(p,prior/(Path(base).parent.name+'-'+p.name))
mission=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticRenderLayerProbeV1.BalticTrial/init.c')
assert sha(mission)=='1ee48715b476a3cf31684083716b43c8e1b932e12cc1b13d8bb9bc06c5c95be1'
result={'status':'PACKAGED_NOT_RUN','world_sha256':sha(world),'water_sha256':sha(water),'probe_sha256':sha(pbo),'mission_sha256':sha(mission),'source_sha256':{str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},'root_review':['FGets EOF is -1 per ensystem.c; parser corrected before build','ID file create-only','Only target is written; control read-only; 60s deadman']}
(R/'package-receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
