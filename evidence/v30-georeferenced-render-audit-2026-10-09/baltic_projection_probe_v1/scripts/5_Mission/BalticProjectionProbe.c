// EV43: read-only CLIENT camera/screen evidence. No material, terrain or camera writes.
modded class MissionGameplay
{
 protected bool m_BalticProjectionStarted;
 protected int m_BalticProjectionNext;
 protected int m_BalticProjectionSamples;
 protected ref array<vector> m_BalticProjectionPoints;
 void BalticProjectionPrepare()
 {
  m_BalticProjectionPoints = new array<vector>;
  m_BalticProjectionPoints.Insert("2718.4852496 1.5204567 6812.812874");
  m_BalticProjectionPoints.Insert("2664 1.125 6786");
  m_BalticProjectionPoints.Insert("2688 1.125 6816");
  m_BalticProjectionPoints.Insert("2664 1.125 6816");
  m_BalticProjectionPoints.Insert("2676 1.125 6822");
  m_BalticProjectionPoints.Insert("2688 1.125 6780");
  m_BalticProjectionPoints.Insert("2736 1.125 6816");
  m_BalticProjectionPoints.Insert("2694 1.125 6816");
  m_BalticProjectionPoints.Insert("2736 1.125 6840");
  m_BalticProjectionPoints.Insert("2706 1.125 6822");
  m_BalticProjectionPoints.Insert("2724 1.125 6834");
  m_BalticProjectionPoints.Insert("2712 1.125 6792");
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer() || !GetGame().GetPlayer()) return;
  string world;
  GetGame().GetWorldName(world);
  if (world != "BalticTrial") return;
  if (m_BalticProjectionSamples >= 300) return;
  int now = GetGame().GetTime();
  if (now < m_BalticProjectionNext) return;
  m_BalticProjectionNext = now + 1000;
  FileHandle file;
  if (!m_BalticProjectionStarted)
  {
   BalticProjectionPrepare();
   file = OpenFile("$profile:baltic_projection_probe_v1.log", FileMode.WRITE);
   if (!file) return;
   FPrintln(file, "BALTIC_PROJECTION_PROBE_V1;EV43;CLIENT_READ_ONLY");
   m_BalticProjectionStarted = true;
  }
  else file = OpenFile("$profile:baltic_projection_probe_v1.log", FileMode.APPEND);
  if (!file) return;
  int width;
  int height;
  GetScreenSize(width, height);
  vector camera = GetGame().GetCurrentCameraPosition();
  vector direction = GetGame().GetCurrentCameraDirection();
  float fov = Camera.GetCurrentFOV();
  FPrintln(file, "CAMERA;" + now + ";" + camera.ToString() + ";" + direction.ToString() + ";" + fov + ";" + width + ";" + height + ";" + GetGame().SurfaceGetSeaLevel());
  for (int i = 0; i < m_BalticProjectionPoints.Count(); i++)
  {
   vector point = m_BalticProjectionPoints.Get(i);
   vector pixel = GetGame().GetScreenPos(point);
   vector relative = GetGame().GetScreenPosRelative(point);
   FPrintln(file, "POINT;" + now + ";" + i + ";" + point.ToString() + ";" + pixel.ToString() + ";" + relative.ToString());
  }
  m_BalticProjectionSamples++;
  if (m_BalticProjectionSamples == 300) FPrintln(file, "END;300");
  CloseFile(file);
 }
};
