// EV43: read-only CLIENT camera/screen evidence. No material, terrain or camera writes.
modded class MissionGameplay
{
 protected bool m_BalticWaterProjectionV2Started;
 protected int m_BalticWaterProjectionV2Next;
 protected int m_BalticWaterProjectionV2Samples;
 protected ref array<vector> m_BalticWaterProjectionV2Points;
 void BalticWaterProjectionV2Prepare()
 {
  m_BalticWaterProjectionV2Points = new array<vector>;
  m_BalticWaterProjectionV2Points.Insert("2352 2 6810");
  m_BalticWaterProjectionV2Points.Insert("2394 2 6810");
  m_BalticWaterProjectionV2Points.Insert("2436 2 6810");
  m_BalticWaterProjectionV2Points.Insert("2478 2 6810");
  m_BalticWaterProjectionV2Points.Insert("2352 2 6888");
  m_BalticWaterProjectionV2Points.Insert("2394 2 6888");
  m_BalticWaterProjectionV2Points.Insert("2436 2 6888");
  m_BalticWaterProjectionV2Points.Insert("2478 2 6888");
  m_BalticWaterProjectionV2Points.Insert("2352 2 6948");
  m_BalticWaterProjectionV2Points.Insert("2394 2 6948");
  m_BalticWaterProjectionV2Points.Insert("2436 2 6948");
  m_BalticWaterProjectionV2Points.Insert("2478 2 6948");
  m_BalticWaterProjectionV2Points.Insert("2352 2 7020");
  m_BalticWaterProjectionV2Points.Insert("2394 2 7020");
  m_BalticWaterProjectionV2Points.Insert("2436 2 7020");
  m_BalticWaterProjectionV2Points.Insert("2478 2 7020");
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer() || !GetGame().GetPlayer()) return;
  string world;
  GetGame().GetWorldName(world);
  if (world != "BalticTrial") return;
  if (m_BalticWaterProjectionV2Samples >= 300) return;
  int now = GetGame().GetTime();
  if (now < m_BalticWaterProjectionV2Next) return;
  m_BalticWaterProjectionV2Next = now + 1000;
  FileHandle file;
  if (!m_BalticWaterProjectionV2Started)
  {
   BalticWaterProjectionV2Prepare();
   file = OpenFile("$profile:baltic_water_projection_v2.log", FileMode.WRITE);
   if (!file) return;
   FPrintln(file, "BALTIC_WATER_PROJECTION_V2;EV76;CLIENT_READ_ONLY");
   m_BalticWaterProjectionV2Started = true;
  }
  else file = OpenFile("$profile:baltic_water_projection_v2.log", FileMode.APPEND);
  if (!file) return;
  int width;
  int height;
  GetScreenSize(width, height);
  vector camera = GetGame().GetCurrentCameraPosition();
  vector direction = GetGame().GetCurrentCameraDirection();
  float fov = Camera.GetCurrentFOV();
  FPrintln(file, "CAMERA;" + now + ";" + camera.ToString() + ";" + direction.ToString() + ";" + fov + ";" + width + ";" + height + ";" + GetGame().SurfaceGetSeaLevel());
  for (int i = 0; i < m_BalticWaterProjectionV2Points.Count(); i++)
  {
   vector point = m_BalticWaterProjectionV2Points.Get(i);
   vector pixel = GetGame().GetScreenPos(point);
   vector relative = GetGame().GetScreenPosRelative(point);
   FPrintln(file, "POINT;" + now + ";" + i + ";" + point.ToString() + ";" + pixel.ToString() + ";" + relative.ToString());
  }
  m_BalticWaterProjectionV2Samples++;
  if (m_BalticWaterProjectionV2Samples == 300) FPrintln(file, "END;300");
  CloseFile(file);
 }
};
