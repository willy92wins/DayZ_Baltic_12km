// EV89 isolated renderer diagnostic. The host supplies IDs only after its
// exact-executable SHA + label + registry-backlink check. This mission never
// changes the Terrain shadows control.
modded class MissionGameplay
{
 protected bool m_BalticShadowStarted;
 protected bool m_BalticShadowIdsLoaded;
 protected bool m_BalticShadowReady;
 protected bool m_BalticShadowRefused;
 protected bool m_BalticShadowMutated;
 protected bool m_BalticShadowCompleted;
 protected bool m_BalticShadowBaselineLogged;
 protected bool m_BalticShadowDeadmanPendingLogged;
 protected int m_BalticShadowId;
 protected int m_BalticTerrainShadowsId;
 protected int m_BalticShadowOriginal;
 protected int m_BalticTerrainShadowsOriginal;
 protected int m_BalticShadowRequestedPhase;
 protected float m_BalticShadowElapsed;
 protected float m_BalticShadowNextCheck;
 protected float m_BalticShadowDeadline;

 bool BalticShadowLog(string message)
 {
  FileHandle file = OpenFile("$profile:baltic_shadow_probe_v4.log", FileMode.APPEND);
  if (!file) return false;
  FPrintln(file, message);
  CloseFile(file);
  return true;
 }

 void BalticShadowReject(string reason)
 {
  m_BalticShadowRefused = true;
  BalticShadowLog("REFUSED;" + reason + ";time=" + GetGame().GetTime());
 }

 int BalticShadowReadIds()
 {
  FileHandle file;
  string line;
  string digest;
  string proof;
  string shadowIdText;
  string shadowLabel;
  string terrainIdText;
  string terrainLabel;
  string extra;
  int extraRead;
  int shadowId;
  int terrainId;
  file = OpenFile("$profile:baltic_shadow_probe_v4.ids", FileMode.READ);
  if (!file) return 0;
  if (FGets(file, line) <= 0) { CloseFile(file); return -1; }
  digest = line.Trim();
  if (FGets(file, line) <= 0) { CloseFile(file); return -1; }
  proof = line.Trim();
  if (FGets(file, line) <= 0) { CloseFile(file); return -1; }
  shadowIdText = line.Trim();
  if (FGets(file, line) <= 0) { CloseFile(file); return -1; }
  shadowLabel = line.Trim();
  if (FGets(file, line) <= 0) { CloseFile(file); return -1; }
  terrainIdText = line.Trim();
  if (FGets(file, line) <= 0) { CloseFile(file); return -1; }
  terrainLabel = line.Trim();
  extraRead = FGets(file, extra);
  CloseFile(file);
  // FGets returns -1 at EOF (ensystem.c); zero denotes an extra empty line.
  if (extraRead != -1) return -1;
  if (digest != "34f6377be4fd065d104e67263e0c96ac2cb2e348119a4838eba08d2e61b7a69a") return -1;
  if (proof != "READ_ONLY_REGISTRY_CROSSWALK_OK") return -1;
  if (shadowLabel != "Shadows" || terrainLabel != "Terrain shadows") return -1;
  shadowId = shadowIdText.ToInt();
  terrainId = terrainIdText.ToInt();
  if (shadowId < 0 || shadowId >= 4096 || shadowId.ToString() != shadowIdText) return -1;
  if (terrainId < 0 || terrainId >= 4096 || terrainId.ToString() != terrainIdText) return -1;
  if (shadowId == terrainId) return -1;
  m_BalticShadowId = shadowId;
  m_BalticTerrainShadowsId = terrainId;
  m_BalticShadowIdsLoaded = true;
  return 1;
 }

 int BalticShadowReadPhase()
 {
  FileHandle file;
  string line;
  string extra;
  int extraRead;
  file = OpenFile("$profile:baltic_shadow_probe_v4.phase", FileMode.READ);
  if (!file)
  {
   m_BalticShadowRequestedPhase = 0;
   return 1;
  }
  if (FGets(file, line) <= 0) { CloseFile(file); return -1; }
  extraRead = FGets(file, extra);
  CloseFile(file);
  if (extraRead != -1) return -1;
  if (line == "0") { m_BalticShadowRequestedPhase = 0; return 1; }
  if (line == "1") { m_BalticShadowRequestedPhase = 1; return 1; }
  return -1;
 }

 void BalticShadowRestore(string reason)
 {
  int beforeShadow;
  int beforeTerrain;
  int afterShadow;
  int afterTerrain;
  beforeShadow = DiagMenu.GetEngineValue(m_BalticShadowId);
  beforeTerrain = DiagMenu.GetEngineValue(m_BalticTerrainShadowsId);
  DiagMenu.SetEngineValue(m_BalticShadowId, m_BalticShadowOriginal);
  afterShadow = DiagMenu.GetEngineValue(m_BalticShadowId);
  afterTerrain = DiagMenu.GetEngineValue(m_BalticTerrainShadowsId);
  m_BalticShadowMutated = afterShadow != m_BalticShadowOriginal;
  m_BalticShadowCompleted = !m_BalticShadowMutated;
  string logRecord118 = "RESTORE;reason=";
  logRecord118 = logRecord118 + reason;
  logRecord118 = logRecord118 + ";shadow_label=Shadows;shadow_id=";
  logRecord118 = logRecord118 + m_BalticShadowId.ToString();
  logRecord118 = logRecord118 + ";shadow_before=";
  logRecord118 = logRecord118 + beforeShadow.ToString();
  logRecord118 = logRecord118 + ";shadow_original=";
  logRecord118 = logRecord118 + m_BalticShadowOriginal.ToString();
  logRecord118 = logRecord118 + ";shadow_readback=";
  logRecord118 = logRecord118 + afterShadow.ToString();
  logRecord118 = logRecord118 + ";terrain_label=Terrain shadows;terrain_id=";
  logRecord118 = logRecord118 + m_BalticTerrainShadowsId.ToString();
  logRecord118 = logRecord118 + ";terrain_original=";
  logRecord118 = logRecord118 + m_BalticTerrainShadowsOriginal.ToString();
  logRecord118 = logRecord118 + ";terrain_readback=";
  logRecord118 = logRecord118 + afterTerrain.ToString();
  logRecord118 = logRecord118 + ";time=";
  logRecord118 = logRecord118 + GetGame().GetTime();
  BalticShadowLog(logRecord118);
  if (afterShadow != m_BalticShadowOriginal || afterTerrain != m_BalticTerrainShadowsOriginal) m_BalticShadowRefused = true;
 }

 override void OnUpdate(float timeslice)
 {
  string world;
  FileHandle first;
  int idsStatus;
  int phaseStatus;
  int shadowNow;
  int terrainNow;
  int shadowDesired;
  super.OnUpdate(timeslice);
  if (GetGame().IsDedicatedServer()) return;
  m_BalticShadowElapsed = m_BalticShadowElapsed + timeslice;
  m_BalticShadowNextCheck = m_BalticShadowNextCheck - timeslice;
  if (m_BalticShadowNextCheck > 0) return;
  m_BalticShadowNextCheck = 0.25;
  GetGame().GetWorldName(world);
  if (!m_BalticShadowStarted)
  {
   if (world != "BalticTrial") return;
   first = OpenFile("$profile:baltic_shadow_probe_v4.log", FileMode.WRITE);
   if (!first) return;
   FPrintln(first, "BALTIC_SHADOW_PROBE_V4_WAITING_FOR_HOST_IDS");
   CloseFile(first);
   m_BalticShadowStarted = true;
  }
  if (!DiagMenu.IsInitialized())
  {
   if (m_BalticShadowMutated && m_BalticShadowElapsed >= m_BalticShadowDeadline && !m_BalticShadowDeadmanPendingLogged)
   {
    BalticShadowLog("DEADMAN_PENDING;reason=DiagMenu_uninitialized;time=" + GetGame().GetTime());
    m_BalticShadowDeadmanPendingLogged = true;
    m_BalticShadowRefused = true;
   }
   return;
  }
  if (world != "BalticTrial")
  {
   if (m_BalticShadowMutated) BalticShadowRestore("world_changed");
   m_BalticShadowRefused = true;
   return;
  }
  if (!m_BalticShadowIdsLoaded)
  {
   idsStatus = BalticShadowReadIds();
   if (idsStatus == 0) return;
   if (idsStatus < 0) { BalticShadowReject("malformed_or_unverified_ids"); return; }
  }
  if (!m_BalticShadowReady)
  {
   m_BalticShadowOriginal = DiagMenu.GetEngineValue(m_BalticShadowId);
   m_BalticTerrainShadowsOriginal = DiagMenu.GetEngineValue(m_BalticTerrainShadowsId);
   shadowNow = DiagMenu.GetEngineValue(m_BalticShadowId);
   terrainNow = DiagMenu.GetEngineValue(m_BalticTerrainShadowsId);
   BalticShadowLog("IDS;proof=READ_ONLY_REGISTRY_CROSSWALK_OK;exe_sha=34f6377be4fd065d104e67263e0c96ac2cb2e348119a4838eba08d2e61b7a69a;shadow_label=Shadows;shadow_id=" + m_BalticShadowId.ToString() + ";terrain_label=Terrain shadows;terrain_id=" + m_BalticTerrainShadowsId.ToString());
   string logRecord176 = "INITIAL_READBACK;shadow_label=Shadows;shadow_id=";
   logRecord176 = logRecord176 + m_BalticShadowId.ToString();
   logRecord176 = logRecord176 + ";shadow_original=";
   logRecord176 = logRecord176 + m_BalticShadowOriginal.ToString();
   logRecord176 = logRecord176 + ";shadow_readback=";
   logRecord176 = logRecord176 + shadowNow.ToString();
   logRecord176 = logRecord176 + ";terrain_label=Terrain shadows;terrain_id=";
   logRecord176 = logRecord176 + m_BalticTerrainShadowsId.ToString();
   logRecord176 = logRecord176 + ";terrain_original=";
   logRecord176 = logRecord176 + m_BalticTerrainShadowsOriginal.ToString();
   logRecord176 = logRecord176 + ";terrain_readback=";
   logRecord176 = logRecord176 + terrainNow.ToString();
   logRecord176 = logRecord176 + ";time=";
   logRecord176 = logRecord176 + GetGame().GetTime();
   BalticShadowLog(logRecord176);
   if ((m_BalticShadowOriginal != 0 && m_BalticShadowOriginal != 1) || (m_BalticTerrainShadowsOriginal != 0 && m_BalticTerrainShadowsOriginal != 1)) { BalticShadowReject("non_boolean_original"); return; }
   if (shadowNow != m_BalticShadowOriginal || terrainNow != m_BalticTerrainShadowsOriginal) { BalticShadowReject("original_readback_drift"); return; }
   string logRecord179 = "READY;shadow_label=Shadows;shadow_id=";
   logRecord179 = logRecord179 + m_BalticShadowId.ToString();
   logRecord179 = logRecord179 + ";shadow_original=";
   logRecord179 = logRecord179 + m_BalticShadowOriginal.ToString();
   logRecord179 = logRecord179 + ";shadow_readback=";
   logRecord179 = logRecord179 + shadowNow.ToString();
   logRecord179 = logRecord179 + ";terrain_label=Terrain shadows;terrain_id=";
   logRecord179 = logRecord179 + m_BalticTerrainShadowsId.ToString();
   logRecord179 = logRecord179 + ";terrain_original=";
   logRecord179 = logRecord179 + m_BalticTerrainShadowsOriginal.ToString();
   logRecord179 = logRecord179 + ";terrain_readback=";
   logRecord179 = logRecord179 + terrainNow.ToString();
   logRecord179 = logRecord179 + ";time=";
   logRecord179 = logRecord179 + GetGame().GetTime();
   if (!BalticShadowLog(logRecord179)) { m_BalticShadowRefused = true; return; }
   m_BalticShadowReady = true;
  }
  if (m_BalticShadowMutated && m_BalticShadowElapsed >= m_BalticShadowDeadline)
  {
   BalticShadowRestore("deadman_60s");
   m_BalticShadowRefused = true;
   return;
  }
  if (m_BalticShadowRefused || m_BalticShadowCompleted) return;
  shadowNow = DiagMenu.GetEngineValue(m_BalticShadowId);
  terrainNow = DiagMenu.GetEngineValue(m_BalticTerrainShadowsId);
  if (terrainNow != m_BalticTerrainShadowsOriginal)
  {
   string logRecord193 = "ABORT;terrain_control_drift;terrain_label=Terrain shadows;terrain_id=";
   logRecord193 = logRecord193 + m_BalticTerrainShadowsId.ToString();
   logRecord193 = logRecord193 + ";terrain_original=";
   logRecord193 = logRecord193 + m_BalticTerrainShadowsOriginal.ToString();
   logRecord193 = logRecord193 + ";terrain_readback=";
   logRecord193 = logRecord193 + terrainNow.ToString();
   logRecord193 = logRecord193 + ";shadow_readback=";
   logRecord193 = logRecord193 + shadowNow.ToString();
   logRecord193 = logRecord193 + ";time=";
   logRecord193 = logRecord193 + GetGame().GetTime();
   BalticShadowLog(logRecord193);
   if (m_BalticShadowMutated) BalticShadowRestore("terrain_control_drift");
   m_BalticShadowRefused = true;
   return;
  }
  if (!m_BalticShadowBaselineLogged)
  {
   string logRecord200 = "BASELINE;phase=0;shadow_label=Shadows;shadow_id=";
   logRecord200 = logRecord200 + m_BalticShadowId.ToString();
   logRecord200 = logRecord200 + ";shadow_original=";
   logRecord200 = logRecord200 + m_BalticShadowOriginal.ToString();
   logRecord200 = logRecord200 + ";shadow_readback=";
   logRecord200 = logRecord200 + shadowNow.ToString();
   logRecord200 = logRecord200 + ";terrain_label=Terrain shadows;terrain_id=";
   logRecord200 = logRecord200 + m_BalticTerrainShadowsId.ToString();
   logRecord200 = logRecord200 + ";terrain_original=";
   logRecord200 = logRecord200 + m_BalticTerrainShadowsOriginal.ToString();
   logRecord200 = logRecord200 + ";terrain_readback=";
   logRecord200 = logRecord200 + terrainNow.ToString();
   logRecord200 = logRecord200 + ";time=";
   logRecord200 = logRecord200 + GetGame().GetTime();
   if (!BalticShadowLog(logRecord200)) { m_BalticShadowRefused = true; return; }
   m_BalticShadowBaselineLogged = true;
  }
  phaseStatus = BalticShadowReadPhase();
  if (phaseStatus < 0)
  {
   string logRecord206 = "ABORT;malformed_phase;shadow_readback=";
   logRecord206 = logRecord206 + shadowNow.ToString();
   logRecord206 = logRecord206 + ";terrain_readback=";
   logRecord206 = logRecord206 + terrainNow.ToString();
   logRecord206 = logRecord206 + ";time=";
   logRecord206 = logRecord206 + GetGame().GetTime();
   BalticShadowLog(logRecord206);
   if (m_BalticShadowMutated) BalticShadowRestore("malformed_phase_rollback");
   m_BalticShadowRefused = true;
   return;
  }
  if (m_BalticShadowMutated && shadowNow != 1 - m_BalticShadowOriginal)
  {
   string logRecord213 = "ABORT;target_drift;shadow_label=Shadows;shadow_id=";
   logRecord213 = logRecord213 + m_BalticShadowId.ToString();
   logRecord213 = logRecord213 + ";shadow_original=";
   logRecord213 = logRecord213 + m_BalticShadowOriginal.ToString();
   logRecord213 = logRecord213 + ";shadow_readback=";
   logRecord213 = logRecord213 + shadowNow.ToString();
   logRecord213 = logRecord213 + ";terrain_readback=";
   logRecord213 = logRecord213 + terrainNow.ToString();
   logRecord213 = logRecord213 + ";time=";
   logRecord213 = logRecord213 + GetGame().GetTime();
   BalticShadowLog(logRecord213);
   BalticShadowRestore("target_drift_rollback");
   m_BalticShadowRefused = true;
   return;
  }
  if (m_BalticShadowRequestedPhase == 0 && m_BalticShadowMutated)
  {
   BalticShadowRestore("phase0_Aprime");
   return;
  }
  if (m_BalticShadowRequestedPhase == 1 && m_BalticShadowCompleted)
  {
   BalticShadowReject("repeat_toggle_after_restore");
   return;
  }
  if (m_BalticShadowRequestedPhase == 1 && !m_BalticShadowMutated)
  {
   if (shadowNow != m_BalticShadowOriginal) { BalticShadowReject("target_not_at_original_before_B"); return; }
   shadowDesired = 1 - m_BalticShadowOriginal;
   string logRecord232 = "SET_REQUEST;phase=1;shadow_label=Shadows;shadow_id=";
   logRecord232 = logRecord232 + m_BalticShadowId.ToString();
   logRecord232 = logRecord232 + ";from=";
   logRecord232 = logRecord232 + m_BalticShadowOriginal.ToString();
   logRecord232 = logRecord232 + ";to=";
   logRecord232 = logRecord232 + shadowDesired.ToString();
   logRecord232 = logRecord232 + ";terrain_id=";
   logRecord232 = logRecord232 + m_BalticTerrainShadowsId.ToString();
   logRecord232 = logRecord232 + ";terrain_original=";
   logRecord232 = logRecord232 + m_BalticTerrainShadowsOriginal.ToString();
   if (!BalticShadowLog(logRecord232)) { m_BalticShadowRefused = true; return; }
   m_BalticShadowMutated = true;
   m_BalticShadowDeadline = m_BalticShadowElapsed + 60;
   DiagMenu.SetEngineValue(m_BalticShadowId, shadowDesired);
   shadowNow = DiagMenu.GetEngineValue(m_BalticShadowId);
   terrainNow = DiagMenu.GetEngineValue(m_BalticTerrainShadowsId);
   string logRecord238 = "PHASE;1;shadow_label=Shadows;shadow_id=";
   logRecord238 = logRecord238 + m_BalticShadowId.ToString();
   logRecord238 = logRecord238 + ";shadow_desired=";
   logRecord238 = logRecord238 + shadowDesired.ToString();
   logRecord238 = logRecord238 + ";shadow_readback=";
   logRecord238 = logRecord238 + shadowNow.ToString();
   logRecord238 = logRecord238 + ";terrain_label=Terrain shadows;terrain_id=";
   logRecord238 = logRecord238 + m_BalticTerrainShadowsId.ToString();
   logRecord238 = logRecord238 + ";terrain_original=";
   logRecord238 = logRecord238 + m_BalticTerrainShadowsOriginal.ToString();
   logRecord238 = logRecord238 + ";terrain_readback=";
   logRecord238 = logRecord238 + terrainNow.ToString();
   logRecord238 = logRecord238 + ";time=";
   logRecord238 = logRecord238 + GetGame().GetTime();
   if (!BalticShadowLog(logRecord238))
   {
    if (shadowNow != m_BalticShadowOriginal) BalticShadowRestore("post_set_log_failure");
    m_BalticShadowRefused = true;
    return;
   }
   if (shadowNow != shadowDesired || terrainNow != m_BalticTerrainShadowsOriginal)
   {
    if (shadowNow != m_BalticShadowOriginal) BalticShadowRestore("post_set_readback_mismatch");
    m_BalticShadowRefused = true;
    return;
   }
  }
 }
};
