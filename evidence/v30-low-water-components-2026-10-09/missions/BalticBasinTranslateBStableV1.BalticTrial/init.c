// Sea swell probe for views: the server logs the global sea level and the water surface at three points every
// 250 ms, plus one row per real-time second that ties the server clock to the wall clock of the captures.
// No RPC, player movement or terrain edits.
// APIs: world.c SetDate :51; ensystem.c GetHourMinuteSecond :28; game.c SurfaceGetSeaLevelMin/Max/SeaLevel
// :1174-1176, SurfaceGetSeaWaveMax :1178, GetWaterSurfaceHeightNoFakeWave/WithFakeWave :1185-1187;
// weather.c GetActual :38, Set :49, SetLimits :74, GetWindSpeed :243, SetWindSpeed :251,
// SetWindMaximumSpeed :264, SetWindFunctionParams :280, MissionWeather :383.
void main()
{
    GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);
    GetGame().GetWorld().SetTimeMultiplier(0);
    Weather weather = GetGame().GetWeather();
    weather.MissionWeather(true);
    weather.GetOvercast().SetLimits(0, 1);
    weather.GetOvercast().Set(0.1, 0, 3600);
    weather.GetRain().SetLimits(0, 1);
    weather.GetRain().Set(0, 0, 3600);
    weather.GetFog().SetLimits(0, 0);
    weather.GetFog().Set(0, 0, 3600);
    weather.GetSnowfall().SetLimits(0, 0);
    weather.GetSnowfall().Set(0, 0, 3600);
    weather.SetWindMaximumSpeed(20);
    weather.SetWindFunctionParams(1, 1, 1);
    weather.SetWindSpeed(20);
}


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
  FileHandle logFile=OpenFile("$profile:baltic_basin_translate_Bstable.log",FileMode.APPEND);
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
  FileHandle logFile=OpenFile("$profile:baltic_basin_translate_Bstable.log",FileMode.WRITE);
  if (!logFile) return;
  FPrintln(logFile,"BALTIC_BASIN_TRANSLATE;B;fe0d077a39ecb729933d3c791138c314618ce96e2f4bd21af2b141a021f2377d");CloseFile(logFile);
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
  m_Next=GetGame().GetTime()+60000;
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
