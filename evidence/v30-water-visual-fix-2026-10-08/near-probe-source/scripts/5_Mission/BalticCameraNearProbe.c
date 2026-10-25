// A/B/A diagnostic of the owned scripted camera. No Camera.GetCurrentCamera call.
// MCPClientBridge source: :407 class, :504 owned camera, :596 OnTick, :5404 ApplyCameraSet.
// Native Camera GetNearPlane/SetNearPlane: P:/scripts/3_game/entities/camera.c:35,40.
modded class MCPClientBridge
{
 protected Camera m_BalticNearCamera;
 protected int m_BalticNearStart;
 protected int m_BalticNearPhase = -1;
 protected float m_BalticNearOriginal;
 override void OnTick(float timeslice)
 {
  super.OnTick(timeslice);
  if (!m_ActiveCam || !m_ActiveCamOwned) return;
  vector position = m_ActiveCam.GetPosition();
  if (position[0]<2184.9 || position[0]>2185.1 || position[1]<279.9 || position[1]>280.1 || position[2]<7349.9 || position[2]>7350.1) return;
  if (m_BalticNearCamera != m_ActiveCam)
  {
   m_BalticNearCamera = m_ActiveCam;
   m_BalticNearOriginal = m_ActiveCam.GetNearPlane();
   m_BalticNearStart = GetGame().GetTime();
   m_BalticNearPhase = -1;
  }
  int elapsed = GetGame().GetTime()-m_BalticNearStart;
  int phase = 0;
  if (elapsed>=30000) phase=1;
  if (elapsed>=60000) phase=2;
  if (elapsed>=90000) phase=3;
  if (phase == m_BalticNearPhase) return;
  m_BalticNearPhase = phase;
  if (phase==1) m_ActiveCam.SetNearPlane(1);
  else m_ActiveCam.SetNearPlane(m_BalticNearOriginal);
  FileHandle file = OpenFile("$profile:baltic_camera_near_probe.log",FileMode.APPEND);
  if (!file) return;
  FPrintln(file,"NEAR;" + GetGame().GetTime() + ";" + phase + ";" + m_BalticNearOriginal + ";" + m_ActiveCam.GetNearPlane() + ";" + position);
  CloseFile(file);
 }
};
