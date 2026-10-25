// Source-native raster census. SurfaceY and water APIs: 3_game/global/game.c:1162-1188.
void main() {}
class BalticHaloFullWaterMission : MissionServer
{
 protected FileHandle m_Grid;
 protected FileHandle m_Risks;
 protected ref array<string> m_Fields = new array<string>;
 protected int m_Row;
 protected int m_Column;
 protected int m_Total;
 protected int m_Bad;
 protected int m_RowBad;
 protected int m_Dry;
 protected int m_Wet;
 protected int m_DryNominal;
 protected int m_DryDynamic;
 protected int m_WetMissing;
 protected int m_UnflaggedPositive;
 protected float m_RowError;
 protected int m_RiskCount;
 protected int m_Start;
 protected bool m_GridDone;
 protected bool m_Done;
 protected bool m_Negative;
 void Emit(string row)
 {
  FileHandle file=OpenFile("$profile:baltic_halo_fullwater_v3.log",FileMode.APPEND);
  if (!file) { m_Done=true; return; }
  FPrintln(file,row);CloseFile(file);
 }
 void Fail(string reason)
 {
  Emit("FAIL;"+reason);m_Done=true;
  if (m_Grid) { CloseFile(m_Grid);m_Grid=null; }
  if (m_Risks) { CloseFile(m_Risks);m_Risks=null; }
 }
 override void OnInit()
 {
  super.OnInit();
  if (!GetGame().IsDedicatedServer() || GetGame().GetWorldName()!="BalticTrial") { m_Done=true;return; }
  FileHandle first=OpenFile("$profile:baltic_halo_fullwater_v3.log",FileMode.WRITE);
  if (!first) { m_Done=true;return; }
  FPrintln(first,"BALTIC_NATIVE_FULLWATER_V1;BalticTrial;e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c");CloseFile(first);
  m_Grid=OpenFile("$mission:grid.csv",FileMode.READ);
  m_Risks=OpenFile("$mission:risks.csv",FileMode.READ);
  if (!m_Grid || !m_Risks) { Fail("INPUT_MISSING");return; }
  m_Start=GetGame().GetTime();
  Emit("SEA;"+GetGame().SurfaceGetSeaLevelMin()+";"+GetGame().SurfaceGetSeaLevelMax()+";"+GetGame().SurfaceGetSeaLevel()+";"+GetGame().SurfaceGetSeaWaveMax());
 }
 void GridChunk()
 {
  string line;
  if (FGets(m_Grid,line)<0)
  {
   if (m_Row!=2048 || m_Column!=0 || m_Total!=4194304 || !m_Negative) { Fail("GRID_INCOMPLETE");return; }
   CloseFile(m_Grid);m_Grid=null;m_GridDone=true;
   Emit("GRID_END;"+m_Total+";"+m_Bad+";"+m_Negative+";"+(GetGame().GetTime()-m_Start));return;
  }
  m_Fields.Clear();line.Split(";",m_Fields);
  if (m_Fields.Count()!=66 || m_Fields[0].ToInt()!=m_Row || m_Fields[1].ToInt()!=m_Column) { Fail("GRID_SCHEMA_OR_ORDER");return; }
  for (int i=0;i<32;i++)
  {
   int field = 2 + i * 2;
   float expected = m_Fields[field].ToFloat();
   field++;
   int kind = m_Fields[field].ToInt();
   float measured=GetGame().SurfaceY((m_Column+i)*6,12282-m_Row*6);
   float error=Math.AbsFloat(measured-expected);
   if (measured!=measured || measured < -10000 || measured > 10000 || error>0.001) { m_Bad++;m_RowBad++; }
   if (error>m_RowError) m_RowError=error;
   if (m_Row==912 && m_Column+i==453) m_Negative=Math.AbsFloat(measured-(expected+1))>0.5;
   WaterVertex(m_Row, m_Column + i, kind, measured);
   m_Total++;
  }
  m_Column+=32;
  if (m_Column==2048)
  {
   Emit("G;"+m_Row+";2048;"+m_RowBad+";"+m_RowError);
   m_Row++;m_Column=0;m_RowBad=0;m_RowError=0;
  }
 }
 void WaterVertex(int row, int column, int kind, float ground)
 {
  float x = column * 6;
  float z = 12282 - row * 6;
  bool sea = GetGame().SurfaceIsSea(x, z);
  bool pond = GetGame().SurfaceIsPond(x, z);
  float plane = GetGame().GetWaterSurfaceHeightNoFakeWave(Vector(x, ground + 100, z));
  float depth = GetGame().GetWaterDepth(Vector(x, ground + 0.01, z));
  bool nominal = (sea || pond) && plane > ground + 0.03;
  bool dynamic = (sea || pond) && depth > 0.02;
  bool missing = kind > 0 && !sea && !pond;
  if (kind == 0)
  {
   m_Dry++;
   if (nominal) m_DryNominal++;
   if (dynamic) m_DryDynamic++;
  }
  else m_Wet++;
  if (missing) m_WetMissing++;
  // Do not silently discard positive scalar queries when both presence flags are false.
  // These require classification: the height API can also return an object surface.
  if (kind == 0 && !sea && !pond && (plane > ground + 0.03 || depth > 0.02))
  {
   m_UnflaggedPositive++;
   string qrecord = "Q;" + row + ";" + column + ";" + kind;
   qrecord = qrecord + ";" + ground + ";" + sea + ";" + pond;
   qrecord = qrecord + ";" + plane + ";" + depth;
   Emit(qrecord);
  }
  if ((kind == 0 && (nominal || dynamic)) || missing)
  {
   string record = "A;" + row + ";" + column + ";" + kind;
   record = record + ";" + ground + ";" + sea + ";" + pond;
   record = record + ";" + plane + ";" + depth + ";" + GetGame().SurfaceGetSeaLevel();
   Emit(record);
  }
 }
 void RiskPoint()
 {
  string line;
  if (FGets(m_Risks,line)<0)
  {
   CloseFile(m_Risks);m_Risks=null;m_Done=true;
   string summary = "END;" + m_Total + ";" + m_Bad + ";" + m_RiskCount;
   summary = summary + ";" + (GetGame().GetTime()-m_Start) + ";" + m_Dry + ";" + m_Wet;
   summary = summary + ";" + m_DryNominal + ";" + m_DryDynamic + ";" + m_WetMissing;
   Emit("QUERY_END;" + m_UnflaggedPositive);
   Emit(summary);return;
  }
  m_Fields.Clear();line.Split(";",m_Fields);
  if (m_Fields.Count()!=5 || m_Fields[0].ToInt()!=m_RiskCount) { Fail("RISK_SCHEMA_OR_ORDER");return; }
  float x=m_Fields[1].ToFloat();float z=m_Fields[2].ToFloat();
  float ground=GetGame().SurfaceY(x,z);vector above=Vector(x,ground+100,z);
  bool sea=GetGame().SurfaceIsSea(x,z);bool pond=GetGame().SurfaceIsPond(x,z);
  float plane=GetGame().GetWaterSurfaceHeightNoFakeWave(above);
  float depth=GetGame().GetWaterDepth(Vector(x,ground+0.01,z));
  Emit("P;"+m_RiskCount+";"+ground+";"+sea+";"+pond+";"+plane+";"+depth+";"+GetGame().SurfaceGetSeaLevel());
  m_RiskCount++;
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (m_Done || GetGame().GetTime()-m_Start<5000) return;
  int begin=GetGame().GetTime();
  for (int batch=0;batch<64 && !m_Done;batch++)
  {
   if (m_GridDone) RiskPoint();else GridChunk();
   if (GetGame().GetTime()-begin>=20) break;
  }
 }
}
Mission CreateCustomMission(string path) { return new BalticHaloFullWaterMission(); }
