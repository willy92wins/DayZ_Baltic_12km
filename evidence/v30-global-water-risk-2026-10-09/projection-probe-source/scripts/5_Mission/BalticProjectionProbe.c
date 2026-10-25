// Read-only native projection. game.c:965,967,1162; no camera creation or GetCurrentCamera().
modded class MissionGameplay
{
 protected int m_BalticProjectionNext;
 protected bool m_BalticProjectionInit;
 protected const string BALTIC_PROJECTION_LOG = "$profile:baltic_projection_probe.log";
 void BalticProjectionLog(string row)
 {
  FileHandle file = OpenFile(BALTIC_PROJECTION_LOG, FileMode.APPEND);
  if (!file) return;
  FPrintln(file,row);
  CloseFile(file);
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer() || GetGame().GetWorldName() != "BalticTrial") return;
  if (!m_BalticProjectionInit)
  {
   FileHandle first = OpenFile(BALTIC_PROJECTION_LOG,FileMode.WRITE);
   if (!first) return;
   FPrintln(first,"BALTIC_NATIVE_PROJECTION_V1");
   CloseFile(first);
   m_BalticProjectionInit = true;
  }
  if (GetGame().GetTime() < m_BalticProjectionNext) return;
  m_BalticProjectionNext = GetGame().GetTime()+1000;
  vector cam = GetGame().GetCurrentCameraPosition();
  BalticProjectionLog("CAM;" + GetGame().GetTime() + ";" + cam);
  for (int x = 2000; x <= 2800; x = x + 200)
  {
   for (int z = 6800; z <= 7400; z = z + 200)
   {
    float height = GetGame().SurfaceY(x,z);
    vector point = Vector(x,height,z);
    vector screen = GetGame().GetScreenPosRelative(point);
    BalticProjectionLog("P;" + GetGame().GetTime() + ";" + x + ";" + height + ";" + z + ";" + screen);
   }
  }
 }
};
