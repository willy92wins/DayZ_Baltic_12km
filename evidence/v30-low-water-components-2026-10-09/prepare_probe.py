from pathlib import Path
import json,sys,shutil,subprocess
import numpy as np
from discover_components import SOURCE,PLANE,sha
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import tri_sample
old=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticRenderLayerProbeV1.BalticTrial')
main=(old/'init.c').read_text().split('class BalticRenderLayerProbeV1Mission')[0]
tail='''
class BalticBasinTranslateProbeMission: MissionServer
{
 protected int m_Next;
 protected int m_Sample;
 override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
 {
  pos="2682 0 6850"; pos[1]=GetGame().SurfaceY(pos[0],pos[2])+0.2;
  return super.CreateCharacter(identity,pos,ctx,characterName);
 }
 void Emit(string row)
 {
  FileHandle logFile=OpenFile("$profile:baltic_basin_translate_PHASE.log",FileMode.APPEND);
  if (!logFile) return;
  FPrintln(logFile,row);CloseFile(logFile);
 }
 string Sample(float x,float z)
 {
  float ground=GetGame().SurfaceY(x,z);
  return x.ToString()+";"+z+";"+ground+";"+GetGame().SurfaceIsSea(x,z)+";"+GetGame().SurfaceIsPond(x,z)+";"+GetGame().GetWaterSurfaceHeightNoFakeWave(Vector(x,ground+100,z))+";"+GetGame().GetWaterDepth(Vector(x,ground+0.01,z));
 }
 override void OnInit()
 {
  super.OnInit();
  if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName()!="BalticTrial") return;
  FileHandle logFile=OpenFile("$profile:baltic_basin_translate_PHASE.log",FileMode.WRITE);
  if (!logFile) return;
  FPrintln(logFile,"BALTIC_BASIN_TRANSLATE;PHASE;TERRAIN_HASH");CloseFile(logFile);
  FileHandle input=OpenFile("$mission:points.csv",FileMode.READ);
  if (!input) { Emit("FAIL;missing_input");return; }
  string line;ref array<string> fields=new array<string>;int count;
  while (FGets(input,line)>=0)
  {
   fields.Clear();line.Split(";",fields);
   if (fields.Count()!=2) { Emit("FAIL;point_schema");CloseFile(input);return; }
   Emit("P;"+count+";"+Sample(fields[0].ToFloat(),fields[1].ToFloat()));count++;
  }
  CloseFile(input);Emit("GRID_END;"+count);
  m_Next=GetGame().GetTime()+5000;
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (m_Sample>=64 || GetGame().GetTime()<m_Next) return;
  m_Next=GetGame().GetTime()+250;
  Emit("T;"+m_Sample+";"+GetGame().GetTime()+";"+GetGame().SurfaceGetSeaLevel()+";"+GetGame().GetWeather().GetWindSpeed()+";"+Sample(2718.48525,6812.81287));
  m_Sample++;
  if (m_Sample==64) Emit("END;64");
 }
}
Mission CreateCustomMission(string path) { return new BalticBasinTranslateProbeMission(); }
'''
delta=np.load(B/'translation/delta.npz');r,c=delta['rows'],delta['cols']
grid=[(j*6,12282-i*6) for i in range(int(r.min())-2,int(r.max())+3) for j in range(int(c.min())-2,int(c.max())+3)]
grid.append((2718.48525,6812.81287))
for phase,source,plane in [('A',SOURCE,PLANE),('B',B/'translation/terrain.npz',B/'translation/plane.npy')]:
    name='BalticBasinTranslate'+phase+'V1.BalticTrial';mission=B/'missions'/name;mission.mkdir(parents=True,exist_ok=True)
    h=np.load(source)['heights'];p=np.load(plane)
    code=main+tail.replace('PHASE',phase).replace('TERRAIN_HASH',sha(source));(mission/'init.c').write_text(code)
    (mission/'points.csv').write_text(''.join(f'{x:.8f};{z:.8f}\n' for x,z in grid))
    points=[]
    for x,z in grid:
        ground=float(tri_sample(h,x,z));r0=int(np.floor((12282-z)/6));c0=int(np.floor(x/6));values=[]
        for rr in (r0-1,r0):
            for cc in (c0-1,c0):
                if np.isfinite(p[rr,cc]):values.append(float(p[rr,cc]))
        # Exact native vertices use all incident cells; nonvertex calibration is dry and has no water-level assertion.
        level=max(values,default=None);wet=(x%6==0 and z%6==0 and level is not None and level-ground>.03)
        points.append(dict(x=x,z=z,ground=ground,level=level,assert_wet=bool(wet)))
    validator='C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py'
    done=subprocess.run([sys.executable,validator,str(mission)],capture_output=True,text=True);lint=json.loads(done.stdout)
    assert done.returncode==0 and lint['info']['files_scanned']==1 and not lint['errors'];(B/f'lint-{phase}.json').write_text(done.stdout)
    destination=old.parent/name;shutil.copytree(mission,destination)
    ref=dict(phase=phase,mission=str(destination),terrain_sha256=sha(source),plane_sha256=sha(plane),files={p.name:sha(p) for p in mission.iterdir()},points=points)
    (B/f'probe-{phase}.json').write_text(json.dumps(ref,indent=2)+'\n')
    print(json.dumps(dict(phase=phase,mission=str(destination),points=len(points),assert_wet=sum(p['assert_wet'] for p in points),lint_files=1)))
