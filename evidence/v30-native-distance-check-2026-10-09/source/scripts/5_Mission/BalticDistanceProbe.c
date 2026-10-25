// Transient client diagnostic. Never calls SetPreferredViewDistance.
modded class MissionGameplay
{
 protected bool m_BalticDistanceStarted;
 protected int m_BalticDistancePhase = -1;
 protected int m_BalticDistanceNext;

 void BalticDistanceLog(string message)
 {
  FileHandle file = OpenFile("$profile:baltic_distance_probe_v1.log", FileMode.APPEND);
  if (!file) return;
  FPrintln(file, message);
  CloseFile(file);
 }

 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer() || !GetGame().GetPlayer()) return;
  string world;
  GetGame().GetWorldName(world);
  if (world != "BalticTrial") return;
  int now = GetGame().GetTime();
  if (now < m_BalticDistanceNext) return;
  m_BalticDistanceNext = now + 1000;
  if (!m_BalticDistanceStarted)
  {
   FileHandle first = OpenFile("$profile:baltic_distance_probe_v1.log", FileMode.WRITE);
   if (!first) return;
   FPrintln(first, "BALTIC_DISTANCE_PROBE_V1;EV31;profile1600;candidate5000");
   CloseFile(first);
   m_BalticDistanceStarted = true;
  }
  string requested = "0";
  FileHandle command = OpenFile("$profile:baltic_distance_probe_v1.phase", FileMode.READ);
  if (command)
  {
   string marker;
   FGets(command, marker);
   FGets(command, requested);
   CloseFile(command);
   marker = marker.Trim();
   requested = requested.Trim();
   if (marker != "EV31-20261009") return;
  }
  if (requested != "0" && requested != "1" && requested != "2" && requested != "3") return;
  int desired = requested.ToInt();
  if (desired != m_BalticDistancePhase)
  {
   if (desired == 1) GetGame().GetWorld().SetViewDistance(5000);
   if (desired == 2)
   {
    GetGame().GetWorld().SetViewDistance(5000);
    GetGame().GetWorld().SetObjectViewDistance(5000);
   }
   if (desired == 3)
   {
    GetGame().GetWorld().SetViewDistance(1600);
    GetGame().GetWorld().SetObjectViewDistance(1600);
   }
   m_BalticDistancePhase = desired;
   BalticDistanceLog("PHASE;" + desired + ";" + now);
  }
  vector camera = GetGame().GetCurrentCameraPosition();
  vector direction = GetGame().GetCurrentCameraDirection();
  string row = "FPS;" + m_BalticDistancePhase + ";" + now;
  row = row + ";" + GetGame().GetLastFPS() + ";" + GetGame().GetAvgFPS(64);
  row = row + ";" + GetGame().GetMinFPS(64) + ";" + GetGame().GetMaxFPS(64);
  row = row + ";" + camera.ToString() + ";" + direction.ToString();
  BalticDistanceLog(row);
 }
};
