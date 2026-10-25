modded class MissionGameplay
{
 protected bool m_BalticFoamStarted;
 protected bool m_BalticFoamRefused;
 protected int m_BalticFoamPhase;
 protected int m_BalticFoamNext;
 protected int m_BalticFoamDeadline;
 protected Material m_BalticMoss;
 protected Material m_BalticClear;
 void BalticFoamLog(string message)
 {
  FileHandle file = OpenFile("$profile:baltic_pond_foam_probe_v1.log", FileMode.APPEND);
  if (!file) return;
  FPrintln(file, message);
  CloseFile(file);
 }
 bool BalticFoamCheck(Material mat, string name)
 {
  if (!mat)
  {
   BalticFoamLog("MISSING;" + name);
   return false;
  }
  int color = mat.GetParamIndex("FoamColor");
  int reflection = mat.GetParamIndex("FoamPower");
  int extinction = mat.GetParamIndex("WaterExtinction");
  int normal = mat.GetParamIndex("NormalPower");
  int absent = mat.GetParamIndex("__baltic_absent_param__");
  BalticFoamLog("INDEX;" + name + ";" + color + ";" + reflection + ";" + extinction + ";" + normal + ";missing;" + absent);
  return color >= 0 && reflection >= 0 && extinction >= 0 && normal >= 0 && absent == -1;
 }
 void BalticFoamRestore(int phase, int now, string reason)
 {
  Material mat = m_BalticMoss;
  if (m_BalticFoamPhase == 3) mat = m_BalticClear;
  if (mat)
  {
   mat.ResetParam("FoamColor");
   mat.ResetParam("FoamPower");
  }
  m_BalticFoamPhase = phase;
  BalticFoamLog("PHASE;" + phase + ";" + now + ";reset_default;" + reason);
 }
 void BalticFoamMark(int phase, int now)
 {
  m_BalticMoss = GetGame().GetWorld().GetMaterial("graphics/materials/water/pond_moss_1");
  m_BalticClear = m_BalticMoss;
  Material mat = m_BalticMoss;
  m_BalticFoamPhase = phase;
  m_BalticFoamDeadline = now + 90000;
  if (!BalticFoamCheck(mat, "moss"))
  {
   BalticFoamLog("CONTROL_REFUSED;" + phase + ";" + now + ";parameter_contract");
   return;
  }
  bool applied;
  string property;
  if (phase == 1)
  {
   float color[4];
   color[0] = 1; color[1] = 0; color[2] = 1; color[3] = 1;
   applied = mat.SetParam("FoamColor", color);
   property = "FoamColor_magenta";
  }
  if (phase == 3)
  {
   applied = mat.SetParam("FoamPower", 0.0);
   property = "FoamPower_zero";
  }
  BalticFoamLog("PHASE;" + phase + ";" + now + ";" + property + ";set_return=" + applied);
  if (!applied) BalticFoamRestore(9, now, "set_failed");
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer() || !GetGame().GetPlayer() || m_BalticFoamRefused) return;
  string world;
  GetGame().GetWorldName(world);
  if (world != "BalticTrial") return;
  int now = GetGame().GetTime();
  if (now < m_BalticFoamNext) return;
  m_BalticFoamNext = now + 1000;
  if (!m_BalticFoamStarted)
  {
   FileHandle first = OpenFile("$profile:baltic_pond_foam_probe_v1.log", FileMode.WRITE);
   if (!first) return;
   FPrintln(first, "BALTIC_POND_FOAM_PROBE_V1;EV35");
   CloseFile(first);
   m_BalticFoamStarted = true;
   BalticFoamLog("PHASE;0;" + now + ";untouched");
  }
  if ((m_BalticFoamPhase == 1 || m_BalticFoamPhase == 3) && now >= m_BalticFoamDeadline) BalticFoamRestore(9, now, "watchdog");
  FileHandle command = OpenFile("$profile:baltic_pond_foam_probe_v1.phase", FileMode.READ);
  if (command)
  {
   string marker;
   string requested;
   FGets(command, marker);
   FGets(command, requested);
   CloseFile(command);
   marker = marker.Trim(); requested = requested.Trim();
   if (marker == "EV35-20261009")
   {
    if ((requested == "1" && m_BalticFoamPhase == 0) || (requested == "3" && m_BalticFoamPhase == 2)) BalticFoamMark(requested.ToInt(), now);
    if (requested == "2" && m_BalticFoamPhase == 1) BalticFoamRestore(2, now, "requested");
    if (requested == "4" && m_BalticFoamPhase == 3) BalticFoamRestore(4, now, "requested");
   }
  }
  vector camera = GetGame().GetCurrentCameraPosition();
  vector direction = GetGame().GetCurrentCameraDirection();
  BalticFoamLog("SAMPLE;" + m_BalticFoamPhase + ";" + now + ";" + GetGame().SurfaceGetSeaLevel() + ";" + camera.ToString() + ";" + direction.ToString());
 }
};
