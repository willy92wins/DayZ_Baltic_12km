modded class MissionGameplay
{
 protected bool m_BalticPondStarted;
 protected bool m_BalticPondRefused;
 protected int m_BalticPondPhase;
 protected int m_BalticPondNext;
 protected int m_BalticPondDeadline;
 protected Material m_BalticPondMaterial;
 void BalticPondLog(string message)
 {
  FileHandle file = OpenFile("$profile:baltic_pond_material_probe_v1.log", FileMode.APPEND);
  if (!file) return;
  FPrintln(file, message);
  CloseFile(file);
 }
 void BalticPondRestore(int phase, int now, string reason)
 {
  if (m_BalticPondPhase == 1) m_BalticPondMaterial.ResetParam("WetFloor");
  if (m_BalticPondPhase == 3) m_BalticPondMaterial.ResetParam("NormalPower");
  m_BalticPondPhase = phase;
  BalticPondLog("PHASE;" + phase + ";" + now + ";reset_default;" + reason);
 }
 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer() || !GetGame().GetPlayer() || m_BalticPondRefused) return;
  string world;
  GetGame().GetWorldName(world);
  if (world != "BalticTrial") return;
  int now = GetGame().GetTime();
  if (now < m_BalticPondNext) return;
  m_BalticPondNext = now + 1000;
  if (!m_BalticPondStarted)
  {
   FileHandle first = OpenFile("$profile:baltic_pond_material_probe_v1.log", FileMode.WRITE);
   if (!first) return;
   FPrintln(first, "BALTIC_POND_MATERIAL_PROBE_V1;EV33");
   CloseFile(first);
   m_BalticPondMaterial = GetGame().GetWorld().GetMaterial("graphics/materials/water/pond_moss_1");
   if (!m_BalticPondMaterial)
   {
    BalticPondLog("REFUSED;missing_handle");
    m_BalticPondRefused = true;
    return;
   }
   int wet = m_BalticPondMaterial.GetParamIndex("WetFloor");
   int normal = m_BalticPondMaterial.GetParamIndex("NormalPower");
   int absent = m_BalticPondMaterial.GetParamIndex("__baltic_absent_param__");
   BalticPondLog("INDEX;WetFloor;" + wet + ";NormalPower;" + normal + ";missing;" + absent);
   if (wet < 0 || normal < 0 || absent != -1)
   {
    BalticPondLog("REFUSED;parameter_contract");
    m_BalticPondRefused = true;
    return;
   }
   m_BalticPondStarted = true;
   BalticPondLog("PHASE;0;" + now + ";untouched");
  }
  if ((m_BalticPondPhase == 1 || m_BalticPondPhase == 3) && now >= m_BalticPondDeadline) BalticPondRestore(9, now, "watchdog");
  FileHandle command = OpenFile("$profile:baltic_pond_material_probe_v1.phase", FileMode.READ);
  if (command)
  {
   string marker;
   string requested;
   FGets(command, marker);
   FGets(command, requested);
   CloseFile(command);
   marker = marker.Trim();
   requested = requested.Trim();
   if (marker == "EV33-20261009")
   {
    if ((requested == "1" && m_BalticPondPhase == 0) || (requested == "3" && m_BalticPondPhase == 2))
    {
     string property = "WetFloor";
     if (requested == "3") property = "NormalPower";
     bool applied = m_BalticPondMaterial.SetParam(property, 0.0);
     m_BalticPondPhase = requested.ToInt();
     m_BalticPondDeadline = now + 90000;
     BalticPondLog("PHASE;" + m_BalticPondPhase + ";" + now + ";" + property + ";set_return=" + applied);
     if (!applied) BalticPondRestore(9, now, "set_failed");
    }
    if (requested == "2" && m_BalticPondPhase == 1) BalticPondRestore(2, now, "requested");
    if (requested == "4" && m_BalticPondPhase == 3) BalticPondRestore(4, now, "requested");
   }
  }
  vector camera = GetGame().GetCurrentCameraPosition();
  vector direction = GetGame().GetCurrentCameraDirection();
  BalticPondLog("SAMPLE;" + m_BalticPondPhase + ";" + now + ";" + GetGame().SurfaceGetSeaLevel() + ";" + camera.ToString() + ";" + direction.ToString());
 }
};
