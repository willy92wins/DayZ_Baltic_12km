// Offline-prepared, server-only readback probe. No world-state edits, RPC, or player control.
void main()
{
}

class BalticEV95SubcellFlagsV1Mission : MissionServer
{
 protected ref array<string> m_Rows = new array<string>;
 protected ref array<string> m_Fields = new array<string>;
 protected FileHandle m_Log;
 protected int m_StartMs;
 protected int m_NextPhaseMs;
 protected int m_PhaseStartMs;
 protected int m_PhaseIndex;
 protected int m_Cursor;
 protected int m_TotalSamples;
 protected bool m_PhaseActive;
 protected bool m_Done;

 void Emit(string row)
 {
  if (!m_Log) { m_Done = true; return; }
  FPrintln(m_Log, row);
 }

 void CloseLog()
 {
  if (m_Log) { CloseFile(m_Log); m_Log = null; }
 }

 void Fail(string reason)
 {
  Emit("FAIL;" + reason + ";" + GetGame().GetTime());
  m_Done = true;
  CloseLog();
 }

 override void OnInit()
 {
  super.OnInit();
  if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial")
  {
   m_Done = true;
   return;
  }
  m_Log = OpenFile("$profile:baltic_ev95_subcell_flags_probe_20261010.log", FileMode.WRITE);
  if (!m_Log) { m_Done = true; return; }
  Emit("BALTIC_EV95_SUBCELL_FLAGS_V1;BalticTrial;40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a;3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14;279;7");
  FileHandle input = OpenFile("$mission:points.csv", FileMode.READ);
  if (!input) { Fail("POINTS_MISSING"); return; }
  string line;
  if (FGets(input, line) < 0 || line != "sample_id;role;group_id;class;row;col;ring_m;dx_m;dz_m;x;z")
  {
   CloseFile(input);
   Fail("POINTS_HEADER");
   return;
  }
  while (FGets(input, line) >= 0)
  {
   if (line == "") continue;
   m_Fields.Clear();
   line.Split(";", m_Fields);
   if (m_Fields.Count() != 11)
   {
    CloseFile(input);
    Fail("POINTS_SCHEMA");
    return;
   }
   m_Rows.Insert(line);
  }
  CloseFile(input);
  if (m_Rows.Count() != 279)
  {
   Fail("POINTS_COUNT_" + m_Rows.Count());
   return;
  }
  m_StartMs = GetGame().GetTime();
  m_NextPhaseMs = m_StartMs;
  m_PhaseIndex = 0;
  m_TotalSamples = 0;
  Emit("BEGIN;" + m_Rows.Count() + ";7;5000;" + m_StartMs);
 }

 void BeginPhase()
 {
  m_PhaseActive = true;
  m_PhaseStartMs = GetGame().GetTime();
  m_Cursor = 0;
  Emit("PHASE_BEGIN;" + m_PhaseIndex + ";" + m_PhaseStartMs + ";" + (m_PhaseStartMs - m_StartMs)
       + ";" + GetGame().SurfaceGetSeaLevel() + ";" + GetGame().SurfaceGetSeaWaveCurrent()
       + ";" + GetGame().SurfaceGetSeaWaveMax() + ";" + GetGame().GetWeather().GetWindSpeed());
 }

 void SamplePoint(int pointIndex)
 {
  m_Fields.Clear();
  m_Rows[pointIndex].Split(";", m_Fields);
  if (m_Fields.Count() != 11) { Fail("POINTS_SCHEMA_DURING_SAMPLE"); return; }

  float x = m_Fields[9].ToFloat();
  float z = m_Fields[10].ToFloat();
  float ground = GetGame().SurfaceY(x, z);
  vector above = Vector(x, ground + 100, z);
  bool sea = GetGame().SurfaceIsSea(x, z);
  bool pond = GetGame().SurfaceIsPond(x, z);
  float noFake = GetGame().GetWaterSurfaceHeightNoFakeWave(above);
  float withFake = GetGame().GetWaterSurfaceHeightWithFakeWave(above);
  float depth = GetGame().GetWaterDepth(Vector(x, ground + 0.01, z));
  int sampleMs = GetGame().GetTime();
  string row = "S;" + m_PhaseIndex + ";" + pointIndex + ";" + m_Fields[0] + ";" + m_Fields[1] + ";" + m_Fields[2];
  row = row + ";" + m_Fields[3] + ";" + m_Fields[4] + ";" + m_Fields[5] + ";" + m_Fields[6];
  row = row + ";" + m_Fields[7] + ";" + m_Fields[8] + ";" + x + ";" + z + ";" + ground;
  row = row + ";" + sea + ";" + pond + ";" + noFake + ";" + withFake + ";" + depth;
  row = row + ";" + sampleMs + ";" + GetGame().SurfaceGetSeaLevel();
  row = row + ";" + GetGame().SurfaceGetSeaWaveCurrent() + ";" + GetGame().SurfaceGetSeaWaveMax();
  row = row + ";" + GetGame().GetWeather().GetWindSpeed();
  Emit(row);
  m_TotalSamples++;
 }

 void EndPhase()
 {
  int actualMs = GetGame().GetTime();
  Emit("PHASE_END;" + m_PhaseIndex + ";" + actualMs + ";" + (actualMs - m_StartMs)
       + ";" + m_Rows.Count() + ";" + GetGame().SurfaceGetSeaLevel()
       + ";" + GetGame().SurfaceGetSeaWaveCurrent() + ";" + GetGame().SurfaceGetSeaWaveMax()
       + ";" + GetGame().GetWeather().GetWindSpeed());
  m_PhaseIndex++;
  m_PhaseActive = false;
  if (m_PhaseIndex >= 7)
  {
   Emit("END;" + m_PhaseIndex + ";" + m_TotalSamples + ";" + (GetGame().GetTime() - m_StartMs));
   m_Done = true;
   CloseLog();
   return;
  }
  m_NextPhaseMs = m_StartMs + m_PhaseIndex * 5000;
 }

 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (m_Done || !GetGame().IsDedicatedServer()) return;
  if (!m_PhaseActive)
  {
   if (GetGame().GetTime() < m_NextPhaseMs) return;
   BeginPhase();
  }
  int batch = 0;
  while (batch < 32 && m_Cursor < m_Rows.Count() && !m_Done)
  {
   SamplePoint(m_Cursor);
   m_Cursor++;
   batch++;
  }
  if (!m_Done && m_Cursor == m_Rows.Count()) EndPhase();
 }
}

Mission CreateCustomMission(string path)
{
 return new BalticEV95SubcellFlagsV1Mission();
}
