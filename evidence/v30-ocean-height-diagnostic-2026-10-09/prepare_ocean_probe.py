"""One isolated world-config factor, with client native sea readback."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/playtest'));from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=B/'baltic_ocean_height_probe_v1';(src/'scripts/5_Mission').mkdir(parents=True,exist_ok=False)
(src/'config.cpp').write_text('''class CfgPatches { class BalticOceanHeightProbeV1 { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","BalticTrialWorld"}; }; };
class CfgMods { class BalticOceanHeightProbeV1 { type="mod"; dependencies[]={"Mission"}; class defs { class missionScriptModule { value=""; files[]={"baltic_ocean_height_probe_v1/scripts/5_Mission"}; }; }; }; };
class CfgWorlds { class CAWorld; class BalticTrial: CAWorld { MaxTide=0; }; };
''')
(src/'scripts/5_Mission/BalticOceanHeightProbe.c').write_text('''modded class MissionGameplay
{
 protected bool m_BalticOceanStarted;
 protected int m_BalticOceanSample;
 protected float m_BalticOceanNext;
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer() || GetGame().GetWorldName()!="BalticTrial" || m_BalticOceanSample>=90) return;
  if (!m_BalticOceanStarted)
  {
   FileHandle first=OpenFile("$profile:baltic_ocean_height_probe_v1.log",FileMode.WRITE);
   if (!first) return;
   FPrintln(first,"BALTIC_OCEAN_HEIGHT_PROBE_V1");
   FPrintln(first,"CFG;"+GetGame().ConfigGetFloat("CfgWorlds BalticTrial MaxTide")+";"+GetGame().ConfigGetFloat("CfgWorlds BalticTrial MaxWave"));
   CloseFile(first);m_BalticOceanStarted=true;
  }
  m_BalticOceanNext-=timeslice;
  if (m_BalticOceanNext>0) return;
  m_BalticOceanNext=1;
  FileHandle file=OpenFile("$profile:baltic_ocean_height_probe_v1.log",FileMode.APPEND);
  if (!file) return;
  FPrintln(file,"SEA;"+m_BalticOceanSample+";"+GetGame().GetTime()+";"+GetGame().SurfaceGetSeaLevel()+";"+GetGame().SurfaceGetSeaWaveCurrent()+";"+GetGame().SurfaceGetSeaWaveMax());
  m_BalticOceanSample++;
  if (m_BalticOceanSample==90) FPrintln(file,"END;90");
  CloseFile(file);
 }
};
''')
validator='C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py'
lint=subprocess.run([sys.executable,validator,str(src/'scripts')],capture_output=True,text=True);parsed=json.loads(lint.stdout)
assert lint.returncode==0 and parsed['info']['files_scanned']==1 and not parsed['errors'];(B/'lint.json').write_text(lint.stdout)
cv='C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe'
bank='C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe'
subprocess.run([cv,'-bin','-dst',str(src/'config.bin'),str(src/'config.cpp')],check=True,capture_output=True)
out=B/'packed';out.mkdir(exist_ok=False)
subprocess.run([bank,'-property','prefix='+src.name,'-dst',str(out),str(src)],check=True,capture_output=True)
pbo=out/(src.name+'.pbo');_,_,entries=read_pbo(pbo)
assert entries['config.bin']==(src/'config.bin').read_bytes()
scriptkey=next(k for k in entries if k.lower().endswith('balticoceanheightprobe.c'))
assert entries[scriptkey]==(src/'scripts/5_Mission/BalticOceanHeightProbe.c').read_bytes()
dest=Path('P:/Mods/@BalticOceanHeightProbeV1/Addons');dest.mkdir(parents=True,exist_ok=False)
shutil.copyfile(pbo,dest/pbo.name);assert sha(pbo)==sha(dest/pbo.name)
result=dict(status='DIAGNOSTIC_ONLY_NOT_FOR_MAP_RELEASE',mod=str(dest.parent),pbo_sha256=sha(pbo),
            change='CfgWorlds BalticTrial MaxTide only: 1.5 -> 0; MaxWave unchanged.',lint_files=1,
            source_files={str(p.relative_to(src)):sha(p) for p in src.rglob('*') if p.is_file()},
            expected='Observe whether native/client sea level changes; do not assume render causality.',
            limits=['Temporary layer discriminator. No terrain, pond-model, material or production-config edits.'])
(B/'reference.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
