// Diagnostic client-only material consumer probe. No world config or geometry changes.
modded class MissionGameplay
{
 protected bool m_BalticMaterialStarted;
 protected int m_BalticMaterialPhase = -1;
 protected float m_BalticMaterialNext;
 protected float m_BalticMaterialAge;

 void BalticMaterialLog(string message)
 {
  FileHandle file = OpenFile("$profile:baltic_native_water_probe_v1.log", FileMode.APPEND);
  if (!file) return;
  FPrintln(file, message);
  CloseFile(file);
 }

 void BalticInspectMaterial(string path)
 {
  Material mat = GetGame().GetWorld().GetMaterial(path);
  if (!mat) { BalticMaterialLog("HANDLE;" + path + ";null"); return; }
  BalticMaterialLog("INDEX;" + path + ";NormalPower;" + mat.GetParamIndex("NormalPower") + ";WetFloor;" + mat.GetParamIndex("WetFloor") + ";FoamPower;" + mat.GetParamIndex("FoamPower") + ";missing;" + mat.GetParamIndex("__baltic_absent_param__"));
 }

 void BalticApplyMaterial(string path, int phase)
 {
  Material mat = GetGame().GetWorld().GetMaterial(path);
  if (!mat) { BalticMaterialLog("APPLY;" + phase + ";" + path + ";null"); return; }
  mat.ResetParam("NormalPower");
  mat.ResetParam("WetFloor");
  mat.ResetParam("FoamPower");
  bool applied = true;
  if (phase == 1) applied = mat.SetParam("NormalPower", 0.0);
  if (phase == 2) applied = mat.SetParam("WetFloor", 0.0);
  if (phase == 3) applied = mat.SetParam("FoamPower", 0.0);
  BalticMaterialLog("APPLY;" + phase + ";" + path + ";" + applied);
 }

 override void OnUpdate(float timeslice)
 {
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer()) return;
  string world;
  GetGame().GetWorldName(world);
  if (world != "BalticTrial") return;
  m_BalticMaterialAge += timeslice;
  m_BalticMaterialNext -= timeslice;
  if (m_BalticMaterialNext > 0) return;
  m_BalticMaterialNext = 1;
  if (!m_BalticMaterialStarted)
  {
   FileHandle first = OpenFile("$profile:baltic_native_water_probe_v1.log", FileMode.WRITE);
   if (!first) return;
   FPrintln(first, "BALTIC_NATIVE_WATER_PROBE_V1");
   CloseFile(first);
   BalticInspectMaterial("graphics/materials/water/oceanold");
   BalticInspectMaterial("graphics/materials/water/oceanold_nice");
   BalticInspectMaterial("graphics/materials/water/oceanold_storm");
   BalticInspectMaterial("graphics/materials/water/oceanold_samplemap");
   BalticInspectMaterial("graphics/materials/water/shoreFoam");
   Material glow = GetGame().GetWorld().GetMaterial("graphics/materials/postprocess/glow");
   if (glow) BalticMaterialLog("CONTROL_INDEX;glow;BloomIntensity;" + glow.GetParamIndex("BloomIntensity") + ";missing;" + glow.GetParamIndex("__baltic_absent_param__"));
   m_BalticMaterialStarted = true;
  }
  int desired = 0;
  FileHandle command = OpenFile("$profile:baltic_native_water_probe_v1.phase", FileMode.READ);
  if (command)
  {
   string line;
   FGets(command, line);
   CloseFile(command);
   desired = line.ToInt();
  }
  if (desired < 0 || desired > 3) desired = 9;
  if (m_BalticMaterialAge >= 1200) desired = 9;
  if (desired == m_BalticMaterialPhase) return;
  BalticApplyMaterial("graphics/materials/water/oceanold", desired);
  BalticApplyMaterial("graphics/materials/water/oceanold_nice", desired);
  BalticApplyMaterial("graphics/materials/water/oceanold_storm", desired);
  BalticApplyMaterial("graphics/materials/water/oceanold_samplemap", desired);
  m_BalticMaterialPhase = desired;
  BalticMaterialLog("PHASE;" + desired + ";" + GetGame().GetTime() + ";SEA;" + GetGame().SurfaceGetSeaLevel() + ";WAVE;" + GetGame().SurfaceGetSeaWaveCurrent());
 }
};
