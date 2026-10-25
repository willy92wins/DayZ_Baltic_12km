"""Diagnostic-only component labels for the unresolved sea/land rendering layer."""
from pathlib import Path
import hashlib,json,subprocess,shutil,sys
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
sys.path.insert(0,str(W/'tools/playtest'));from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=B/'shore-material-probe';src=root/'baltic_shore_readback';(src/'scripts/5_Mission').mkdir(parents=True,exist_ok=True)
(src/'config.cpp').write_text('''class CfgPatches { class BalticShoreReadback { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","BalticTrialWorld"}; }; };
class CfgMods { class BalticShoreReadback { type="mod"; dependencies[]={"Mission"}; class defs { class missionScriptModule { value=""; files[]={"baltic_shore_readback/scripts/5_Mission"}; }; }; }; };
''')
(src/'scripts/5_Mission/BalticShoreReadback.c').write_text('''modded class MissionGameplay
{
 protected bool m_BalticShoreLogged;
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (m_BalticShoreLogged || GetGame().IsDedicatedServer() || GetGame().GetWorldName()!="BalticTrial") return;
  FileHandle file=OpenFile("$profile:baltic_shore_readback_v1.log",FileMode.WRITE);
  if (!file) return;
  FPrintln(file,"BALTIC_SHORE_COMPONENT_READBACK_V1");
  array<string> keys={"seaMaterial","shoreMaterial","shoreFoamMaterial","shoreWetMaterial"};
  for (int i=0;i<keys.Count();i++)
  {
   string value;
   bool found=GetGame().ConfigGetText("CfgWorlds BalticTrial "+keys[i],value);
   FPrintln(file,keys[i]+";"+found+";"+value);
  }
  FPrintln(file,"END");CloseFile(file);m_BalticShoreLogged=true;
 }
};
''')
marker=root/'baltic_shore_marker';marker.mkdir(exist_ok=True)
(marker/'config.cpp').write_text('''class CfgPatches { class BalticShoreMarker { units[]={}; weapons[]={}; requiredVersion=0.1; requiredAddons[]={"DZ_Data","BalticTrialWorld"}; }; };
class CfgMaterials
{
 class Terrain;
 class BalticShoreMagenta: Terrain
 {
  ambient[]={1,0,1,1}; diffuse[]={1,0,1,1}; forcedDiffuse[]={1,0,1,1}; emmisive[]={1,0,1,1}; specular[]={0,0,0,0};
 };
 class BalticShoreWetGreen: Terrain
 {
  ambient[]={0,1,0,1}; diffuse[]={0,1,0,1}; forcedDiffuse[]={0,1,0,1}; emmisive[]={0,1,0,1}; specular[]={0,0,0,0};
 };
};
class CfgWorlds { class CAWorld; class BalticTrial: CAWorld { shoreMaterial="#BalticShoreMagenta"; shoreWetMaterial="#BalticShoreWetGreen"; }; };
''')
cv=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe')
bank=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe');records=[]
for directory,mod in [(src,'@BalticShoreReadback'),(marker,'@BalticShoreMarker')]:
    r=subprocess.run([str(cv),'-bin','-dst',str(directory/'config.bin'),str(directory/'config.cpp')],capture_output=True);assert r.returncode==0
    out=root/(directory.name+'-packed');out.mkdir(exist_ok=True)
    if not (out/(directory.name+'.pbo')).exists():
        r=subprocess.run([str(bank),'-property','prefix='+directory.name,'-dst',str(out),str(directory)],capture_output=True);assert r.returncode==0
    p=out/(directory.name+'.pbo');_,_,entries=read_pbo(p)
    assert entries['config.bin']==(directory/'config.bin').read_bytes() and entries['config.cpp']==(directory/'config.cpp').read_bytes()
    for script in directory.rglob('*.c'):assert entries[str(script.relative_to(directory)).replace('\\','/')]==script.read_bytes()
    dest=Path('P:/Mods')/mod/'Addons';dest.mkdir(parents=True,exist_ok=True)
    if (dest/p.name).exists():assert sha(p)==sha(dest/p.name)
    else:shutil.copyfile(p,dest/p.name)
    assert sha(p)==sha(dest/p.name)
    records.append(dict(mod=str(dest.parent),sha256=sha(p)))
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(src)],capture_output=True,text=True)
result=json.loads(lint.stdout);assert lint.returncode==0 and not result['errors'] and result['info']['files_scanned']==2
(E/'shore-material-lint.json').write_text(lint.stdout)
shutil.copytree(root,E/'shore-material-probe-source',ignore=shutil.ignore_patterns('*.pbo','*.bin','*-packed'))
ref=dict(status='DIAGNOSTIC_ONLY_NOT_FOR_MAP_RELEASE',mods=records,sources=['P:/bin/config.cpp:5198-5201','P:/bin/config.cpp:155-167','P:/scripts/3_game/global/game.c:448'],
    gate=['Same terrain, water models, camera, weather and loaded texture quality.','Baseline must visibly reproduce the residual. Marker must show on a real shoreline positive control before interpreting absent color.','Runtime config readback confirms selected material names, not the renderer consuming them.'],
    limits=['Only the shore and wet-shore materials are relabelled. Ocean/pond geometry and sea physical heights remain exact.','No supported DayZ shore-darkening tuning is inferred from Arma documentation. Markers are diagnostic and must never enter a production map.'])
(E/'shore-material-reference.json').write_text(json.dumps(ref,indent=2)+'\n');print(json.dumps(ref,indent=2))
