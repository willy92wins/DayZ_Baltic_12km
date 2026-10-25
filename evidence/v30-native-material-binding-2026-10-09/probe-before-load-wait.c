modded class MissionGameplay
{
 protected bool m_BalticBindingStarted;
 protected bool m_BalticBindingRefused;
 protected int m_BalticBindingPhase;
 protected int m_BalticBindingNext;
 protected int m_BalticBindingDeadline;
 protected Material m_BalticMoss;
 protected Material m_BalticClear;
 void BalticBindingLog(string message)
 {
  FileHandle file = OpenFile("$profile:baltic_material_binding_probe_v1.log", FileMode.APPEND);
  if (!file) return;
  FPrintln(file, message);
  CloseFile(file);
 }
 bool BalticBindingCheck(Material mat, string name)
 {
  if (!mat) return false;
  int color = mat.GetParamIndex("Color");
  int reflection = mat.GetParamIndex("ReflectionColor");
  int extinction = mat.GetParamIndex("WaterExtinction");
  int normal = mat.GetParamIndex("NormalPower");
  int absent = mat.GetParamIndex("__baltic_absent_param__");
  BalticBindingLog("INDEX;" + name + ";" + color + ";" + reflection + ";" + extinction + ";" + normal + ";missing;" + absent);
  return color >= 0 && reflection >= 0 && extinction >= 0 && normal >= 0 && absent == -1;
 }
 void BalticBindingRestore(int phase, int now, string reason)
 {
  Material mat = m_BalticMoss;
  if (m_BalticBindingPhase == 3) mat = m_BalticClear;
  mat.ResetParam("Color");
  mat.ResetParam("ReflectionColor");
  mat.ResetParam("WaterExtinction");
  mat.ResetParam("NormalPower");
  m_BalticBindingPhase = phase;
  BalticBindingLog("PHASE;" + phase + ";" + now + ";reset_default;" + reason);
 }
 void BalticBindingMark(int phase, int now)
 {
  Material mat = m_BalticMoss;
  float color[4];
  color[0] = 1; color[1] = 0; color[2] = 1; color[3] = 1;
  if (phase == 3)
  {
   mat = m_BalticClear;
   color[0] = 0; color[1] = 1;
  }
  bool a = mat.SetParam("Color", color);
  bool b = mat.SetParam("ReflectionColor", color);
  bool c = mat.SetParam("WaterExtinction", 100.0);
  bool d = mat.SetParam("NormalPower", 0.0);
  m_BalticBindingPhase = phase;
  m_BalticBindingDeadline = now + 90000;
  BalticBindingLog("PHASE;" + phase + ";" + now + ";marker;returns;" + a + ";" + b + ";" + c + ";" + d);
  if (!a || !b || !c || !d) BalticBindingRestore(9, now, "set_failed");
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer() || !GetGame().GetPlayer() || m_BalticBindingRefused) return;
  string world;
  GetGame().GetWorldName(world);
  if (world != "BalticTrial") return;
  int now = GetGame().GetTime();
  if (now < m_BalticBindingNext) return;
  m_BalticBindingNext = now + 1000;
  if (!m_BalticBindingStarted)
  {
   FileHandle first = OpenFile("$profile:baltic_material_binding_probe_v1.log", FileMode.WRITE);
   if (!first) return;
   FPrintln(first, "BALTIC_MATERIAL_BINDING_PROBE_V1;EV34");
   CloseFile(first);
   m_BalticMoss = GetGame().GetWorld().GetMaterial("graphics/materials/water/pond_moss_1");
   m_BalticClear = GetGame().GetWorld().GetMaterial("graphics/materials/water/pond_clear");
   if (!BalticBindingCheck(m_BalticMoss, "moss") || !BalticBindingCheck(m_BalticClear, "clear"))
   {
    BalticBindingLog("REFUSED;parameter_contract");
    m_BalticBindingRefused = true;
    return;
   }
   m_BalticBindingStarted = true;
   BalticBindingLog("PHASE;0;" + now + ";untouched");
  }
  if ((m_BalticBindingPhase == 1 || m_BalticBindingPhase == 3) && now >= m_BalticBindingDeadline) BalticBindingRestore(9, now, "watchdog");
  FileHandle command = OpenFile("$profile:baltic_material_binding_probe_v1.phase", FileMode.READ);
  if (command)
  {
   string marker;
   string requested;
   FGets(command, marker);
   FGets(command, requested);
   CloseFile(command);
   marker = marker.Trim(); requested = requested.Trim();
   if (marker == "EV34-20261009")
   {
    if ((requested == "1" && m_BalticBindingPhase == 0) || (requested == "3" && m_BalticBindingPhase == 2)) BalticBindingMark(requested.ToInt(), now);
    if (requested == "2" && m_BalticBindingPhase == 1) BalticBindingRestore(2, now, "requested");
    if (requested == "4" && m_BalticBindingPhase == 3) BalticBindingRestore(4, now, "requested");
   }
  }
  vector camera = GetGame().GetCurrentCameraPosition();
  vector direction = GetGame().GetCurrentCameraDirection();
  BalticBindingLog("SAMPLE;" + m_BalticBindingPhase + ";" + now + ";" + GetGame().SurfaceGetSeaLevel() + ";" + camera.ToString() + ";" + direction.ToString());
 }
};
